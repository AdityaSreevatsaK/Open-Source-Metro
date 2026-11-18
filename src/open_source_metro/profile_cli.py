"""Self-service profile SVG exports from public history or local v1 snapshots.

Works offline with --input. The live path is public-only and bounded. No
profile repository is modified, and no demonstration events are fabricated.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

from .compact_profile import render_compact
from .mobile_profile import render_mobile
from .validation import normalise
from .contribution_calendar import fetch_contribution_calendar, normalise_calendar_for_snapshot
from .year_history import collect_year, repository_valid


def select_repositories(snapshot: dict, featured: list[str] | None) -> dict:
    """Create a non-mutating, explicit subset of already validated v1 data."""
    normalise(snapshot)
    if featured is None:
        return snapshot
    if not featured or len(featured) > 5 or any(not repository_valid(x) for x in featured):
        raise ValueError("Select between one and five valid repository names")
    canonical = {r["full_name"].casefold(): r["full_name"]
                 for r in snapshot["repositories"]}
    desired = [x.casefold() for x in featured]
    if len(set(desired)) != len(desired) or any(x not in canonical for x in desired):
        raise ValueError("Featured repositories must be unique and exist in the snapshot")
    names = {canonical[x] for x in desired}
    selected = dict(snapshot)
    selected["repositories"] = [r for r in snapshot["repositories"] if r["full_name"] in names]
    selected["activity"] = [e for e in snapshot["activity"] if e["repo_full_name"] in names]
    selected["_selection"] = {
        "featured_repositories": [canonical[x] for x in desired],
        "omitted_repositories": len(snapshot["repositories"]) - len(selected["repositories"]),
        "omitted_events": len(snapshot["activity"]) - len(selected["activity"]),
    }
    normalise(selected)
    return selected


def export_profile(snapshot: dict, output: Path, *, layout: str = "both",
                   theme: str = "midnight", featured: list[str] | None = None) -> list[Path]:
    """Generate static SVGs and honest embed instructions, without online access."""
    if layout not in ("compact", "mobile", "both"):
        raise ValueError("layout must be compact, mobile or both")
    if theme not in ("midnight", "paper"):
        raise ValueError("theme must be midnight or paper")
    data = select_repositories(snapshot, featured)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    produced = []
    svg_files = []
    if layout in ("compact", "both"):
        path = output / "profile-compact.svg"
        path.write_text(render_compact(data, theme=theme), encoding="utf-8")
        svg_files.append(path)
        produced.append(path)
    if layout in ("mobile", "both"):
        path = output / "profile-mobile.svg"
        path.write_text(render_mobile(data, theme=theme), encoding="utf-8")
        svg_files.append(path)
        produced.append(path)
    snapshot_path = output / "source-snapshot.json"
    snapshot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    produced.append(snapshot_path)
    status = ("Synthetic demonstration data" if data["source"] == "demo"
              else "Partial public GitHub event snapshot")
    snap = normalise(data)
    calendar = normalise_calendar_for_snapshot(data, snap)
    generated = snap["generated"].date()
    last_sunday = generated - timedelta(days=(generated.weekday() + 1) % 7)
    window_start = last_sunday - timedelta(weeks=52)
    observed = [e["date"].date() for e in snap["events"]
                if window_start <= e["date"].date() <= generated
                and e["date"] <= snap["generated"]]
    if calendar is not None:
        observed_days = sorted(day for day, amount in calendar.items()
                               if window_start <= day <= generated and amount > 0)
        calendar_total = sum(amount for day, amount in calendar.items()
                             if window_start <= day <= generated)
    else:
        observed_days = sorted(set(observed))
        calendar_total = None
    observed_weeks = {(day - window_start).days // 7 for day in observed_days}
    observed_range = (f"{observed_days[0].isoformat()} to {observed_days[-1].isoformat()}"
                      if observed_days else "No events in the displayed annual window")
    text = [
        "# Open Source Metro | Generated profile assets",
        "",
        f"**Source:** {status}. This is not GitHub's official complete contribution calendar.",
        "",
        f"**Actually observed dates:** {observed_range}.",
        (f"**GitHub profile calendar:** {calendar_total} displayed GitHub contribution units on {len(observed_days)} days in {len(observed_weeks)} of 53 weeks."
         if calendar is not None else
         f"**Source event coverage:** {len(observed)} observed public events on {len(observed_days)} days in {len(observed_weeks)} of 53 weeks."),
        (f"**Public project routes:** {len(observed)} recorded public repository events; project routes are not a breakdown of the GitHub contribution totals."
         if calendar is not None else
         "Up to five featured project routes; all validated events contribute to the source-event calendar."),
        ("**Sparse history warning:** The selected source data covers fewer than eight active weeks; "
         "a nearly blank year is expected. Add older public repositories using --repos, "
         "or view the separate 16-week mobile layout." if data["source"] == "github"
         and len(observed_weeks) < 8 else ""),
        "",
        "Upload the chosen SVG to your own profile repository and update its README **manually**.",
        "This tool does not open PRs, commit to a profile, publish any token or change GitHub settings.",
        "",
    ]
    for svg in svg_files:
        text.append(f"![{status} | {svg.stem}](./{svg.name})")
        text.append("")
    text.extend([
        "**Coverage:** Blank squares are unobserved activity, not confirmed zero contributions.",
        "For public data, refer to source-snapshot.json → _coverage for API, pagination and omissions.",
        "Portrait image intentionally shows only the most recent 16 weeks.",
        "",
    ])
    instructions = output / "README_SNIPPET.md"
    instructions.write_text("\n".join(text), encoding="utf-8")
    produced.append(instructions)
    return produced


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a source-backed Open Source Metro profile pack")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--username", help="Collect public history for this GitHub account")
    sources.add_argument("--input", type=Path, help="Use an existing local v1 JSON snapshot (offline)")
    parser.add_argument("--output", type=Path, default=Path("output/profile"))
    parser.add_argument("--repos", help="Comma-separated public repository collection scope (live only)")
    parser.add_argument("--featured", help="Comma-separated repository names to include in the generated card")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--max-repos", type=int, default=10)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--include-forks", action="store_true")
    parser.add_argument("--layout", choices=("compact", "mobile", "both"), default="both")
    parser.add_argument("--theme", choices=("midnight", "paper"), default="midnight")
    args = parser.parse_args()
    if args.input:
        if args.repos or args.include_forks:
            parser.error("--repos and --include-forks require --username")
        data = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        repos = [name.strip() for name in args.repos.split(",")] if args.repos is not None else None
        data = collect_year(args.username, repos=repos, days=args.days,
                            max_repos=args.max_repos, pages=args.pages,
                            include_forks=args.include_forks)
        if os.getenv("GITHUB_TOKEN"):
            # Official GitHub profile daily totals complement, never replace,
            # the separately verified public repository event ledger.
            recorded = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
            data["_calendar"] = fetch_contribution_calendar(args.username, generated_at=recorded)
        else:
            print("NOTE: No GITHUB_TOKEN: calendar shows only sampled public repository events.")
    featured = ([name.strip() for name in args.featured.split(",")]
                if args.featured is not None else None)
    files = export_profile(data, args.output, layout=args.layout,
                           theme=args.theme, featured=featured)
    for file in files:
        print(file)
    print("This is a source-backed event illustration, NOT a complete GitHub contribution calendar.")


if __name__ == "__main__":
    main()
