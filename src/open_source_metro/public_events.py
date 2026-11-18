"""Small, public-only GitHub Events API adapter.

The public Events API is a recent activity stream, NOT a complete contribution
calendar. It contains at most 300 events from the last 30 days. Modern
PushEvent payloads do not expose commit lists, so we do not fabricate commit
counts from a push. No tokens, private endpoints or background requests.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .validation import normalise, safe_label, safe_url, utc_timestamp

USER_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
REPO_RE = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+\Z")
API_VERSION = "2026-03-10"
API_BASE = "https://api.github.com"
MAX_PAGES = 3
MAX_EVENTS = 300
MAX_RESPONSE_BYTES = 3_000_000


def username_valid(username: object) -> bool:
    return isinstance(username, str) and USER_RE.fullmatch(username) is not None


def fetch_public_events(username: str, *, pages: int = MAX_PAGES,
                        per_page: int = 100, opener=None) -> list[dict]:
    """Fetch a bounded, recent, *public-only* activity sample.

    Fetches only https://api.github.com/users/{username}/events/public .
    A transport error raises; it is never silently presented as no activity.
    Tests inject a fake opener and make zero network requests.
    """
    if not username_valid(username):
        raise ValueError("Invalid GitHub username")
    if type(pages) is not int or not 1 <= pages <= MAX_PAGES:
        raise ValueError("pages must be between 1 and 3")
    if type(per_page) is not int or not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")
    transport = opener or urlopen
    result: list[dict] = []
    seen: set[str] = set()
    for page in range(1, pages + 1):
        url = f"{API_BASE}/users/{username}/events/public?per_page={per_page}&page={page}"
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "open-source-metro-public-events/0.1",
        })
        try:
            with transport(request, timeout=12) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            if exc.code in (403, 429):
                raise RuntimeError("GitHub API rate limit or access restriction; retry later") from exc
            raise RuntimeError(f"GitHub API HTTP {exc.code}") from exc
        except (URLError, TimeoutError, HTTPException, OSError) as exc:
            raise RuntimeError("Could not read public GitHub events") from exc
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError("GitHub response exceeds configured safety limit")
        try:
            batch = json.loads(payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid GitHub API JSON response") from exc
        if not isinstance(batch, list):
            raise ValueError("GitHub public events response must be a list")
        for item in batch:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not safe_label(item_id, 160):
                continue
            if item_id not in seen:
                seen.add(item_id)
                result.append(item)
            if len(result) >= MAX_EVENTS:
                return result
        if len(batch) < per_page:
            break
    return result


def convert_events(username: str, events: list[dict], *,
                   generated_at: datetime | None = None, pages_fetched: int | None = None) -> dict:
    """Convert to strict source='github' v1 while recording skipped categories.

    PR 'opened' and merge events, opened issues and published releases map to
    their precise v1 event kinds. Pushes without an explicit *commit list* are
    excluded because counting pushes as commits would be misleading.
    """
    if not username_valid(username):
        raise ValueError("Invalid GitHub username")
    if not isinstance(events, list):
        raise ValueError("Expected a public events list")
    now = generated_at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("generated_at must be timezone-aware UTC")
    now = now.astimezone(timezone.utc)
    earliest = now - timedelta(days=30)
    repositories: dict[str, dict] = {}
    activity: list[dict] = []
    skipped: Counter[str] = Counter()
    seen: set[str] = set()
    for event in events[:MAX_EVENTS]:
        if not isinstance(event, dict):
            skipped["invalid_event"] += 1
            continue
        if event.get("public") is not True:
            skipped["not_explicitly_public"] += 1
            continue
        actor = event.get("actor")
        if not isinstance(actor, dict) or str(actor.get("login", "")).casefold() != username.casefold():
            skipped["different_actor"] += 1
            continue
        repo = event.get("repo")
        repo_name = repo.get("name") if isinstance(repo, dict) else None
        if not isinstance(repo_name, str) or not safe_label(repo_name, 200) or not REPO_RE.fullmatch(repo_name):
            skipped["invalid_repository"] += 1
            continue
        raw_id = event.get("id")
        if not isinstance(raw_id, str) or not safe_label(raw_id, 150):
            skipped["invalid_id"] += 1
            continue
        if raw_id in seen:
            skipped["duplicate"] += 1
            continue
        seen.add(raw_id)
        try:
            occurred = utc_timestamp(event.get("created_at"))
        except ValueError:
            skipped["invalid_timestamp"] += 1
            continue
        if not earliest <= occurred <= now:
            skipped["outside_30_day_window"] += 1
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        kind, count = None, 1
        subtype = event.get("type")
        action = payload.get("action")
        link = None
        if subtype == "PullRequestEvent":
            pr = payload.get("pull_request") if isinstance(payload.get("pull_request"), dict) else {}
            if action == "opened":
                kind = "pr_opened"
            elif action == "merged" or (action == "closed" and pr.get("merged") is True):
                kind = "pr_merged"
            link = pr.get("html_url")
        elif subtype == "IssuesEvent" and action == "opened":
            kind = "issue_opened"
            issue = payload.get("issue") if isinstance(payload.get("issue"), dict) else {}
            link = issue.get("html_url")
        elif subtype == "ReleaseEvent" and action == "published":
            kind = "release"
            release = payload.get("release") if isinstance(payload.get("release"), dict) else {}
            link = release.get("html_url")
        elif subtype == "PushEvent":
            # GitHub API's current documented payload has only before/head, not
            # an enumerated commit list. Never count one push as one commit.
            commits = payload.get("commits")
            if isinstance(commits, list):
                hashes = {c["sha"] for c in commits if isinstance(c, dict)
                          and isinstance(c.get("sha"), str) and
                          re.fullmatch(r"[0-9a-fA-F]{7,40}", c["sha"])}
                if hashes:
                    kind = "commit"
                    count = len(hashes)
            if kind is None:
                skipped["push_without_commit_list"] += 1
                continue
        if kind is None:
            skipped["unsupported_event_or_action"] += 1
            continue
        url = safe_url(link) or f"https://github.com/{repo_name}"
        activity.append({
            "id": f"public-{raw_id}", "kind": kind, "repo_full_name": repo_name,
            "occurred_at": occurred.isoformat().replace("+00:00", "Z"),
            "url": url, "count": count,
        })
        repositories.setdefault(repo_name, {
            "full_name": repo_name, "name": repo_name.split("/", 1)[1],
            "url": f"https://github.com/{repo_name}",
        })
    snapshot = {
        "schema_version": "1", "source": "github",
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "user": {"login": username, "url": f"https://github.com/{username}"},
        "repositories": sorted(repositories.values(), key=lambda x: x["full_name"].casefold()),
        "activity": sorted(activity, key=lambda x: (x["occurred_at"], x["id"])),
        "_coverage": {
            "source": "GitHub public Events API",
            "window": "last 30 days maximum, up to 300 public events",
            "complete_contribution_history": False,
            "api_events_supplied": min(len(events), MAX_EVENTS),
            "mapped_events": len(activity),
            "skipped_by_reason": dict(sorted(skipped.items())),
            "pages_fetched": pages_fetched,
            "possibly_truncated": len(events) >= MAX_EVENTS,
            "notes": [
                "Recent public activity sample, not all GitHub contributions.",
                "A push without a verifiable commit list is NOT counted as commits.",
                "API event delivery may be delayed and repository/activity coverage incomplete.",
                "A blank calendar cell is unobserved, not confirmed inactivity.",
            ],
        },
    }
    # Re-use the same strict validator as all other renderers.
    normalise(snapshot)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public GitHub events into an incomplete v1 source snapshot")
    parser.add_argument("username", help="Public GitHub username")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON (do not commit personal snapshots)")
    parser.add_argument("--pages", type=int, default=3, help="1-3 pages, capped at 300 public API events")
    parser.add_argument("--compact-svg", type=Path, help="Optional compact 53-week source-event SVG")
    args = parser.parse_args()
    events = fetch_public_events(args.username, pages=args.pages)
    snapshot = convert_events(args.username, events, pages_fetched=min(args.pages, (len(events) + 99)//100))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.compact_svg:
        from .compact_profile import render_compact
        args.compact_svg.parent.mkdir(parents=True, exist_ok=True)
        args.compact_svg.write_text(render_compact(snapshot), encoding="utf-8")
    mapped = snapshot["_coverage"]["mapped_events"]
    print(f"Public snapshot: {mapped} mapped events from {len(events)} API records")
    print("WARNING: recent public-event sample only, not complete GitHub contributions.")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
