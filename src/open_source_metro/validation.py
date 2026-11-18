"""Source snapshot validation for Open Source Metro.

This is the self-contained v1 data contract shared by the renderer and tests.
No network access, credentials or implicit GitHub API claims.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from urllib.parse import urlsplit

EVENT_KINDS = frozenset({"commit", "pr_opened", "pr_merged", "issue_opened", "release"})


def utc_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Timestamp must be an ISO 8601 UTC string")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid UTC timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError("Only UTC timestamps are supported")
    return timestamp.astimezone(timezone.utc)


def safe_label(value: object, limit: int) -> bool:
    """Reject XML-invalid characters and misleading bidirectional controls."""
    if not isinstance(value, str) or not 1 <= len(value) <= limit:
        return False
    for char in value:
        cp = ord(char)
        if (cp < 32 or 127 <= cp <= 159 or 0xD800 <= cp <= 0xDFFF
                or 0xFDD0 <= cp <= 0xFDEF or cp & 0xFFFE == 0xFFFE
                or 0x202A <= cp <= 0x202E or 0x2066 <= cp <= 0x2069):
            return False
    return True


def safe_url(value: object) -> str | None:
    if not safe_label(value, 2048):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme.lower() == "https" and parsed.hostname == "github.com"
                and not parsed.username and not parsed.password and parsed.port in (None, 443)
                and not parsed.path.startswith("//")):
            return value
    except ValueError:
        pass
    return None


def normalise(source: object) -> dict:
    """Strictly validate, deduplicate and order a v1 demo/public source snapshot."""
    if (not isinstance(source, dict) or source.get("schema_version") != "1"
            or source.get("source") not in ("demo", "github")):
        raise ValueError("Expected v1 demo or github snapshot")
    generated = utc_timestamp(source.get("generated_at"))
    user = source.get("user")
    if not isinstance(user, dict) or not safe_label(user.get("login"), 120):
        raise ValueError("Missing/invalid user.login")
    if not isinstance(source.get("repositories"), list) or not isinstance(source.get("activity"), list):
        raise ValueError("Expected repository and activity lists")
    repos: dict[str, dict] = {}
    for row in source["repositories"]:
        if not isinstance(row, dict):
            raise ValueError("Invalid repository row")
        full = row.get("full_name")
        if not safe_label(full, 200) or not re.fullmatch(r"[^/\s]+/[^/\s]+", full):
            raise ValueError("Invalid repository full_name")
        if full in repos:
            raise ValueError("Duplicate repository")
        name = row.get("name", full.split("/", 1)[1])
        if not safe_label(name, 200):
            raise ValueError("Invalid repository name")
        repos[full] = {"full_name": full, "name": name, "url": safe_url(row.get("url"))}
    events, seen = [], {}
    for row in source["activity"]:
        if not isinstance(row, dict) or not safe_label(row.get("id"), 160):
            raise ValueError("Invalid event ID")
        if row.get("kind") not in EVENT_KINDS or row.get("repo_full_name") not in repos:
            raise ValueError("Unsupported event type or unknown repository")
        count = row.get("count", 1)
        if type(count) is not int or not 1 <= count <= 100000:
            raise ValueError("Event count must be a positive integer")
        record = {"id": row["id"], "kind": row["kind"], "repo": row["repo_full_name"],
                  "date": utc_timestamp(row.get("occurred_at")), "count": count,
                  "url": safe_url(row.get("url"))}
        if record["id"] in seen:
            if seen[record["id"]] != record:
                raise ValueError("Conflicting source records share an event ID")
            continue
        seen[record["id"]] = record
        events.append(record)
    events.sort(key=lambda x: (x["date"], x["id"]))
    first: dict[str, datetime] = {}
    for event in events:
        first.setdefault(event["repo"], event["date"])
    ordered = sorted(repos.values(), key=lambda row: (
        first.get(row["full_name"], datetime.max.replace(tzinfo=timezone.utc)),
        row["full_name"],
    ))
    return {"generated": generated, "source": source["source"], "user": user["login"],
            "repos": ordered, "events": events, "repo_total": len(ordered), "event_total": len(events)}
