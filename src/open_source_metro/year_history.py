"""Bounded, public-repository history collection across a real year.

Not GitHub's official contribution calendar. Only default-branch commits and
selected public repository events are collected. All limits and omissions are
recorded in an explicit coverage manifest. No authentication is required;
GITHUB_TOKEN is optional for rate limits and is never logged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .public_events import API_BASE, API_VERSION, username_valid
from .validation import normalise, safe_url, utc_timestamp

_REPOSITORY = re.compile(r"[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}\Z")
_COMMIT = re.compile(r"[0-9a-fA-F]{40}\Z")
MAX_REQUEST_BYTES = 3_000_000
MAX_REPOS = 20
MAX_PAGES = 5
PER_PAGE = 100
EVENT_TYPES = ("commits", "pulls", "issues", "releases")


def repository_valid(name: object) -> bool:
    return isinstance(name, str) and len(name) <= 140 and _REPOSITORY.fullmatch(name) is not None


def utc_z(stamp: datetime) -> str:
    return stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp(value: object) -> datetime | None:
    try:
        return utc_timestamp(value)
    except ValueError:
        return None


def _same_user(row: object, username: str) -> bool:
    return isinstance(row, dict) and isinstance(row.get("login"), str) and row["login"].casefold() == username.casefold()


class PublicGitHub:
    """Read-only fixed-host client with bounded pages, responses and timeouts."""

    def __init__(self, *, opener=None, token: str | None = None, timeout: int = 12):
        self.opener = opener or urlopen
        self.token = token
        self.timeout = timeout
        self.requests = 0

    def get(self, path: str, query: dict | None = None, *, allow_empty: bool = False):
        if not path.startswith("/") or ".." in path or any(c in path for c in ("?", "#", "\\", "\n", "\r")):
            raise ValueError("Invalid fixed GitHub API path")
        url = API_BASE + path
        if query:
            url += "?" + urlencode(query)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "open-source-metro-year-history/0.1",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(url, headers=headers)
        self.requests += 1
        try:
            with self.opener(request, timeout=self.timeout) as response:
                payload = response.read(MAX_REQUEST_BYTES + 1)
        except HTTPError as exc:
            if allow_empty and exc.code == 409:
                return []
            if exc.code in (403, 429):
                raise RuntimeError("GitHub rate limit or access restriction. Try a read-only GITHUB_TOKEN.") from None
            raise RuntimeError("GitHub public API returned HTTP " + str(exc.code)) from None
        except (URLError, HTTPException, TimeoutError, OSError):
            raise RuntimeError("Unable to retrieve public GitHub API data") from None
        if len(payload) > MAX_REQUEST_BYTES:
            raise ValueError("Public API response exceeds allowed size")
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("GitHub API returned invalid JSON") from exc

    def pages(self, path: str, query: dict | None = None, *, max_pages: int = 2,
              allow_empty: bool = False) -> tuple[list[dict], bool]:
        if type(max_pages) is not int or not 1 <= max_pages <= MAX_PAGES:
            raise ValueError("max_pages must be 1-5")
        rows: list[dict] = []
        capped = False
        for page in range(1, max_pages + 1):
            args = dict(query or {})
            args.update({"per_page": PER_PAGE, "page": page})
            result = self.get(path, args, allow_empty=allow_empty)
            if not isinstance(result, list):
                raise ValueError("Expected a JSON list from GitHub")
            rows.extend(r for r in result if isinstance(r, dict))
            if len(result) < PER_PAGE:
                return rows, capped
            if page == max_pages:
                capped = True  # Full final page may have more records.
        return rows, capped


def collect_year(username: str, *, repos: list[str] | None = None, days: int = 365,
                 max_repos: int = 5, pages: int = 2, include_forks: bool = False,
                 generated_at: datetime | None = None, client: PublicGitHub | None = None) -> dict:
    """Collect public, observed activity for owned/explicit repositories.

    Uses the current default branch's /commits?author=... data and public PR,
    issues and release lists. Does NOT invent events, fetch private repositories,
    or claim complete contributions to all forks and organisations.
    """
    if not username_valid(username):
        raise ValueError("Invalid GitHub username")
    if type(days) is not int or not 30 <= days <= 370:
        raise ValueError("days must be 30-370")
    if type(max_repos) is not int or not 1 <= max_repos <= MAX_REPOS:
        raise ValueError("max_repos must be 1-20")
    if type(pages) is not int or not 1 <= pages <= MAX_PAGES:
        raise ValueError("pages must be 1-5")
    moment = generated_at or datetime.now(timezone.utc)
    if moment.tzinfo is None or moment.utcoffset() != timedelta(0):
        raise ValueError("generated_at must be in UTC")
    moment = moment.astimezone(timezone.utc)
    since = moment - timedelta(days=days)
    api = client or PublicGitHub(token=os.getenv("GITHUB_TOKEN"))
    explicit = repos is not None
    names: list[str] = []
    manifests: dict[str, dict] = {}
    repo_cap = False
    if explicit:
        if not repos or len(repos) > max_repos:
            raise ValueError("Explicit repositories must contain 1-max_repos names")
        for value in repos:
            if not repository_valid(value):
                raise ValueError("Invalid repository name")
            if value.casefold() not in {n.casefold() for n in names}:
                names.append(value)
        for name in names:
            response = api.get("/repos/" + name)
            if not isinstance(response, dict) or response.get("private") is not False:
                raise ValueError("Selected repository is not confirmed public")
            actual = response.get("full_name")
            if not repository_valid(actual) or actual.casefold() != name.casefold():
                raise ValueError("Repository identity mismatch")
    else:
        owned, discover_capped = api.pages(
            "/users/" + username + "/repos",
            {"type": "owner", "sort": "pushed", "direction": "desc"},
            max_pages=pages)
        seen: set[str] = set()
        for row in owned:
            name = row.get("full_name")
            if row.get("private") is not False or not repository_valid(name):
                continue
            if row.get("fork") and not include_forks:
                continue
            owner = row.get("owner")
            if not _same_user(owner, username):
                continue
            if name.casefold() not in seen:
                seen.add(name.casefold())
                names.append(name)
        repo_cap = discover_capped or len(names) > max_repos
        names = names[:max_repos]

    collected_repos = []
    events: dict[str, dict] = {}
    for name in names:
        if not repository_valid(name):
            raise ValueError("Invalid repository name")
        endpoint = "/repos/" + name
        individual: dict[str, dict] = {}
        counts = {}
        for item_type in EVENT_TYPES:
            query = {}
            if item_type == "commits":
                query = {"author": username, "since": utc_z(since), "until": utc_z(moment)}
            elif item_type == "pulls":
                query = {"state": "all", "sort": "created", "direction": "desc"}
            elif item_type == "issues":
                query = {"state": "all", "creator": username, "sort": "created", "direction": "desc"}
            responses, truncated = api.pages(endpoint + "/" + item_type, query,
                                             max_pages=pages, allow_empty=item_type == "commits")
            individual[item_type] = {"rows": responses, "possibly_truncated": truncated}
            counts[item_type] = len(responses)
        manifests[name] = {"fetched": counts,
                           "possibly_truncated": [kind for kind, meta in individual.items()
                                                  if meta["possibly_truncated"]],
                           "default_branch_only_commits": True}
        observed: list[dict] = []

        def record(kind: str, event_id: str, stamp: object, raw_url: object):
            time = _timestamp(stamp)
            if time is None or not since <= time <= moment:
                return
            if event_id in events:
                return
            url = safe_url(raw_url) or f"https://github.com/{name}"
            events[event_id] = {
                "id": event_id, "kind": kind, "repo_full_name": name,
                "occurred_at": utc_z(time), "count": 1, "url": url,
            }
            observed.append(events[event_id])

        for commit in individual["commits"]["rows"]:
            sha = commit.get("sha")
            if not isinstance(sha, str) or not _COMMIT.fullmatch(sha):
                continue
            # Repository commits endpoint was scoped by author=username.
            author = commit.get("author")
            if isinstance(author, dict) and not _same_user(author, username):
                continue
            detail = commit.get("commit")
            authored = detail.get("author") if isinstance(detail, dict) else None
            if not isinstance(authored, dict):
                continue
            record("commit", "commit:" + name + ":" + sha.lower(),
                   authored.get("date"), commit.get("html_url"))

        for pull in individual["pulls"]["rows"]:
            if not _same_user(pull.get("user"), username):
                continue
            number = pull.get("number")
            if type(number) is not int or number <= 0:
                continue
            stem = "pr:" + name + ":" + str(number)
            url = pull.get("html_url")
            record("pr_opened", stem + ":opened", pull.get("created_at"), url)
            # Only a PR authored by this user counts as their merged PR.
            if pull.get("merged_at"):
                record("pr_merged", stem + ":merged", pull["merged_at"], url)

        for issue in individual["issues"]["rows"]:
            if "pull_request" in issue or not _same_user(issue.get("user"), username):
                continue
            number = issue.get("number")
            if type(number) is not int or number <= 0:
                continue
            record("issue_opened", "issue:" + name + ":" + str(number),
                   issue.get("created_at"), issue.get("html_url"))

        for release in individual["releases"]["rows"]:
            if not _same_user(release.get("author"), username):
                continue
            key = release.get("id")
            if type(key) is not int or key <= 0:
                continue
            record("release", "release:" + name + ":" + str(key),
                   release.get("published_at"), release.get("html_url"))
        collected_repos.append({"full_name": name, "name": name.split("/", 1)[1],
                                "url": "https://github.com/" + name})
        manifests[name]["mapped"] = len(observed)

    snapshot = {
        "schema_version": "1", "source": "github", "generated_at": utc_z(moment),
        "user": {"login": username, "url": "https://github.com/" + username},
        "repositories": collected_repos,
        "activity": sorted(events.values(), key=lambda event: (event["occurred_at"], event["id"])),
        "_coverage": {
            "collector": "public-repository-history-v1",
            "window_start": utc_z(since), "window_end": utc_z(moment),
            "days_requested": days, "complete_contribution_history": False,
            "public_repositories_only": True,
            "selection": "explicit" if explicit else "owned_public_repositories",
            "included_repositories": names,
            "repository_discovery_possibly_truncated": repo_cap,
            "requests": api.requests,
            "pages_per_endpoint_maximum": pages,
            "per_repository": manifests,
            "possible_history_truncation": repo_cap or any(
                entry["possibly_truncated"] for entry in manifests.values()),
            "limitations": [
                "Observed public repository history, not GitHub's official contribution totals.",
                "Commits are from current default branch and use the GitHub author filter.",
                "Repository list excludes organisations and contributed-to repositories unless selected.",
                "PR and issue lists may be truncated or miss events created before the requested window.",
                "Only pull requests authored by this user have merge milestones.",
                "No review comments, discussions, private activity, or deleted repositories.",
                "A blank day means unobserved, not proven inactivity.",
            ],
        },
    }
    normalise(snapshot)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch bounded, incomplete, public year-scale repository history")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--output", type=Path, required=True, help="Local v1 JSON snapshot")
    parser.add_argument("--repos", help="Comma-separated public repositories; includes contributed-to repositories")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--max-repos", type=int, default=5)
    parser.add_argument("--pages", type=int, default=2, help="1-5 pages per endpoint per repository")
    parser.add_argument("--include-forks", action="store_true")
    args = parser.parse_args()
    names = [s.strip() for s in args.repos.split(",")] if args.repos is not None else None
    snapshot = collect_year(args.username, repos=names, days=args.days,
                            max_repos=args.max_repos, pages=args.pages,
                            include_forks=args.include_forks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(snapshot['activity'])} observed events across {len(snapshot['repositories'])} public repositories")
    print("IMPORTANT: not a complete GitHub contribution calendar.")
    if snapshot["_coverage"]["possible_history_truncation"]:
        print("WARNING: at least one repository or API page limit may omit additional activity.")


if __name__ == "__main__":
    main()
