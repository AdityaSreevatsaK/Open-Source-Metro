"""GitHub's profile-visible contribution calendar, kept separate from repo events.

The GraphQL daily calendar is GitHub's account-level visible contribution count,
NOT a repository event ledger. A route stop can only use independently observed
public repository events. Any visible private/restricted aggregate remains
unattributed; no private repository metadata is ever requested or stored.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .public_events import username_valid

GRAPHQL_URL = "https://api.github.com/graphql"
MAX_BYTES = 1_500_000
MAX_DAYS = 380
QUERY = """query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    login
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def parse_calendar(value: object, username: str) -> dict:
    """Fail closed on invalid or misattributed GitHub profile-calendar data."""
    if not username_valid(username) or not isinstance(value, dict):
        raise ValueError("Invalid GitHub contribution calendar")
    user = (value.get("data") or {}).get("user") if isinstance(value.get("data"), dict) else None
    if not isinstance(user, dict) or not isinstance(user.get("login"), str) or user["login"].casefold() != username.casefold():
        raise ValueError("GitHub contribution calendar user identity mismatch")
    collection = user.get("contributionsCollection")
    calendar = collection.get("contributionCalendar") if isinstance(collection, dict) else None
    if not isinstance(calendar, dict):
        raise ValueError("Missing GitHub contribution calendar")
    total = calendar.get("totalContributions")
    if type(total) is not int or not 0 <= total <= 1_000_000_000:
        raise ValueError("Invalid GitHub contribution count")
    weeks = calendar.get("weeks")
    if not isinstance(weeks, list) or not 1 <= len(weeks) <= 55:
        raise ValueError("Invalid contribution calendar weeks")
    days = []
    seen = set()
    for week in weeks:
        rows = week.get("contributionDays") if isinstance(week, dict) else None
        if not isinstance(rows, list) or len(rows) > 7:
            raise ValueError("Invalid contribution calendar week")
        for item in rows:
            if not isinstance(item, dict) or type(item.get("contributionCount")) is not int:
                raise ValueError("Invalid contribution day")
            count = item["contributionCount"]
            stamp = item.get("date")
            if type(count) is not int or not 0 <= count <= 1_000_000 or not isinstance(stamp, str):
                raise ValueError("Invalid contribution day count or date")
            try:
                parsed = date.fromisoformat(stamp)
            except ValueError as exc:
                raise ValueError("Invalid contribution day date") from exc
            if parsed.isoformat() != stamp or stamp in seen:
                raise ValueError("Duplicate or noncanonical contribution date")
            seen.add(stamp)
            days.append({"date": stamp, "count": count})
    if len(days) > MAX_DAYS:
        raise ValueError("Contribution calendar exceeds expected date range")
    days.sort(key=lambda d: d["date"])
    return {
        "provider": "github-graphql",
        "kind": "github-profile-visible-contributions",
        "username": user["login"],
        "total_contributions": total,
        "days": days,
        "scope_note": (
            "GitHub profile-visible daily contribution totals. Some accounts may "
            "show anonymous restricted/private contribution counts. Repository "
            "routes are independently observed public records, not a breakdown "
            "of these totals."
        ),
    }


def fetch_contribution_calendar(username: str, *, generated_at: datetime | None = None,
                                token: str | None = None, opener=None) -> dict:
    """Fetch official GitHub GraphQL day counts with a single fixed-host POST.

    Requires a GitHub API token, which stays in the request header and is not
    written into the returned calendar JSON or generated SVG.
    """
    if not username_valid(username):
        raise ValueError("Invalid GitHub username")
    secret = token if token is not None else os.getenv("GITHUB_TOKEN")
    if not secret:
        raise RuntimeError("A read-only GITHUB_TOKEN is required for the GitHub GraphQL calendar")
    now = generated_at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("Calendar timestamp must be UTC")
    now = now.astimezone(timezone.utc)
    begin = now - timedelta(days=365)
    payload = {
        "query": QUERY,
        "variables": {"login": username, "from": begin.isoformat(),
                      "to": now.isoformat()},
    }
    request = Request(
        GRAPHQL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": "Bearer " + secret,
                 "User-Agent": "open-source-metro-profile-calendar/0.1"},
        method="POST",
    )
    try:
        with (opener or urlopen)(request, timeout=20) as response:
            raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError):
        raise RuntimeError("GitHub GraphQL contribution-calendar request failed") from None
    if len(raw) > MAX_BYTES:
        raise ValueError("GitHub contribution-calendar response too large")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Malformed GraphQL calendar response") from exc
    if not isinstance(decoded, dict) or decoded.get("errors"):
        raise RuntimeError("GitHub GraphQL contribution-calendar query was rejected")
    result = parse_calendar(decoded, username)
    result["window_from"] = begin.isoformat().replace("+00:00", "Z")
    result["window_to"] = now.isoformat().replace("+00:00", "Z")
    return result


def normalise_calendar_for_snapshot(raw: dict, snapshot: dict) -> dict[date, int] | None:
    """Validate optional independent calendar before rendering untrusted input."""
    value = raw.get("_calendar")
    if value is None:
        return None
    if not isinstance(value, dict) or value.get("provider") != "github-graphql":
        raise ValueError("Unrecognised GitHub calendar source")
    if raw.get("source") != "github":
        raise ValueError("A GitHub contribution calendar is not a synthetic fixture")
    user = raw.get("user")
    login = user.get("login") if isinstance(user, dict) else None
    if not isinstance(login, str) or value.get("username", "").casefold() != login.casefold():
        raise ValueError("Calendar account mismatch")
    total = value.get("total_contributions")
    if type(total) is not int or not 0 <= total <= 1_000_000_000:
        raise ValueError("Invalid calendar total")
    days = value.get("days")
    if not isinstance(days, list) or len(days) > MAX_DAYS:
        raise ValueError("Invalid calendar days")
    result: dict[date, int] = {}
    for item in days:
        if not isinstance(item, dict) or type(item.get("count")) is not int:
            raise ValueError("Invalid calendar day")
        stamp = item.get("date")
        amount = item["count"]
        if not isinstance(stamp, str) or not 0 <= amount <= 1_000_000:
            raise ValueError("Invalid calendar count or date")
        try:
            day = date.fromisoformat(stamp)
        except ValueError as exc:
            raise ValueError("Invalid calendar date") from exc
        if day.isoformat() != stamp or day in result:
            raise ValueError("Duplicate or noncanonical calendar date")
        result[day] = amount
    return result
