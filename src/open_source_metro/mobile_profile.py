"""Portrait-format 16-week GitHub activity/metro view for narrow screens.

A distinct *recent window*, NOT a squashed 53-week chart. It reads the same
strict v1 source snapshot as the large and compact renderers and never
synthesises activity outside the explicitly labelled demo-only --showcase.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import timedelta
from html import escape
import json
from pathlib import Path

from .compact_profile import COLOURS
from .living_network import demo_story, _density
from .validation import normalise
from .contribution_calendar import normalise_calendar_for_snapshot

WIDTH, HEIGHT = 460, 808
WEEKS = 16
X0, XSTEP, CELL = 88.0, 21.5, 16.5
DAY_Y, DAY_STEP = 181.0, 18.0
LANE_Y, LANE_STEP = 389.0, 61.0


def _esc(value: object) -> str:
    return escape(str(value), quote=True)


def _txt(x: float, y: float, value: object, cls: str, anchor: str = "start") -> str:
    return f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" text-anchor="{anchor}">{_esc(value)}</text>'


def mobile_plan(raw: dict) -> dict:
    """One source-backed 16-week window with at most five recent active routes."""
    snapshot = normalise(raw)
    today = snapshot["generated"].date()
    final_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    start = final_sunday - timedelta(weeks=WEEKS - 1)
    visible = [e for e in snapshot["events"]
               if start <= e["date"].date() <= today and e["date"] <= snapshot["generated"]]
    activity_count = Counter(e["repo"] for e in visible)
    first = {}
    for e in visible:
        first.setdefault(e["repo"], e["date"])
    featured = sorted([r for r in snapshot["repos"] if activity_count[r["full_name"]]],
                      key=lambda r: (-activity_count[r["full_name"]], first[r["full_name"]],
                                     r["full_name"]))[:5]
    names = {r["full_name"] for r in featured}
    chosen = [e for e in visible if e["repo"] in names]
    # Do not silently truncate dense real activity at 240 events. Calendar
    # cells include every source-observed event, including unfeatured repos.
    retained = visible
    by_day = defaultdict(list)
    by_repo_week = defaultdict(list)
    for event in retained:
        d = event["date"].date()
        week = (d - start).days // 7
        by_day[d].append(event)
        if event["repo"] in names:
            by_repo_week[(event["repo"], week)].append(event)
    routes = []
    for index, repo in enumerate(featured):
        name = repo["full_name"]
        weeks = sorted(w for (r, w) in by_repo_week if r == name)
        stations = []
        for week in weeks:
            events = by_repo_week[(name, week)]
            kind = ("release" if any(e["kind"] == "release" for e in events)
                    else "pr_merged" if any(e["kind"] == "pr_merged" for e in events)
                    else "event")
            stations.append({"week": week, "kind": kind,
                             "ids": [e["id"] for e in events], "events": len(events)})
        routes.append({"repo": repo, "index": index, "stations": stations, "weeks": weeks})
    return {
        "snap": snapshot, "start": start, "today": today,
        "routes": routes, "events": retained, "by_day": by_day,
        "omitted_repos": snapshot["repo_total"] - len(featured),
        "omitted_events": snapshot["event_total"] - len(retained),
        "window_weeks": WEEKS,
    }


def render_mobile(raw: dict, *, theme: str = "midnight") -> str:
    """Accessible, static 460px portrait SVG, with truthful time scope."""
    if theme not in COLOURS:
        raise ValueError("Unknown colour theme")
    p = mobile_plan(raw)
    official = normalise_calendar_for_snapshot(raw, p["snap"])
    c = COLOURS[theme]
    demo = p["snap"]["source"] == "demo"
    synthetic = demo and bool(raw.get("_synthetic_added"))
    provenance = ("GITHUB PROFILE · PUBLIC ROUTES PARTIAL" if official is not None else
                  "SYNTHETIC DESIGN SHOWCASE" if synthetic else
                  "SHARED SYNTHETIC FIXTURE" if demo else
                  "PUBLIC EVENTS · PARTIAL HISTORY")
    coverage = raw.get("_coverage", {}) if isinstance(raw.get("_coverage"), dict) else {}
    mode = coverage.get("collector")
    scope = (("GITHUB DAY COUNTS · PUBLIC ROUTES PARTIAL" if official is not None else
              "PUBLIC REPOSITORY HISTORY · COVERAGE PARTIAL" if mode == "public-repository-history-v1"
              else "PUBLIC EVENT SNAPSHOT · COVERAGE PARTIAL") if not demo else
             "ILLUSTRATIVE DATA, NOT REAL GITHUB HISTORY")
    if (p["events"] or official is not None) and not demo:
        observed_days = (sorted(day for day, amount in official.items()
                                if p["start"] <= day <= p["today"] and amount > 0)
                         if official is not None else sorted(p["by_day"]))
        range_label = (f"OBSERVED {len(observed_days)} DAYS · "
                       f"{observed_days[0]:%d %b}–{observed_days[-1]:%d %b %Y}"
                       if observed_days else "NO VISIBLE CONTRIBUTIONS IN THIS WINDOW")
    elif not demo:
        range_label = "NO SOURCE EVENTS OBSERVED IN THIS WINDOW"
    else:
        range_label = "BLANK SQUARES = UNOBSERVED"
    items = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="mobile-title mobile-desc">',
        f'<title id="mobile-title">Open Source Metro mobile / {provenance}</title>',
        ('<desc id="mobile-desc">The most recent sixteen-week portrait uses GitHub profile-visible contribution counts for daily squares. Repository routes use a separate, incomplete public event ledger; these counts are not a per-project breakdown and may include anonymous restricted contributions depending on profile privacy settings.</desc>'
         if official is not None else
         '<desc id="mobile-desc">A dedicated portrait view of the most recent sixteen Sunday-to-Saturday weeks. Date squares show observed source-event units; each line is one active repository, with stops only on observed weeks. Ring stations denote merged pull requests and diamond stations denote releases. The rail between stops is schematic, not continuous activity. Blank means unobserved, not zero GitHub contributions. This is not the official GitHub contributions chart.</desc>'),
        '<defs><style><![CDATA[',
        '.heading{font:800 27px Arial,Segoe UI,sans-serif;letter-spacing:-1px}',
        '.subtitle{font:600 11px Arial,Segoe UI,sans-serif}',
        '.tag{font:800 10px Arial,Segoe UI,sans-serif;letter-spacing:.5px}',
        '.small{font:600 10px Arial,Segoe UI,sans-serif}',
        '.route{font:700 13px Arial,Segoe UI,sans-serif}',
        '.station-index{font:800 10px Arial,Segoe UI,sans-serif}',
        ']]></style></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{c["bg"]}"/>',
        f'<rect x="12" y="12" width="436" height="784" rx="22" fill="{c["panel"]}" stroke="{c["rule"]}"/>',
        f'<rect x="27" y="28" width="5" height="51" rx="2" fill="{c["routes"][0]}"/>',
        f'<g fill="{c["text"]}">{_txt(43,57,"OPEN SOURCE METRO","heading")}</g>',
        f'<g fill="{c["muted"]}">{_txt(43,77,"A recent snapshot of project journeys","subtitle")}</g>',
        f'<rect x="28" y="94" width="404" height="29" rx="10" fill="{c["surface"]}"/>',
        f'<g fill="{c["text"]}">{_txt(42,113,provenance,"tag")}</g>',
        f'<rect x="28" y="135" width="404" height="187" rx="14" fill="{c["surface"]}" stroke="{c["rule"]}"/>',
        f'<g fill="{c["muted"]}">{_txt(42,155,("01 / GITHUB CONTRIBUTIONS" if official is not None else "01 / SOURCE ACTIVITY"),"tag")}',
        _txt(417,155,"LATEST 16 WEEKS","tag","end"),'</g>',
    ]
    for w in range(WEEKS):
        d = p["start"] + timedelta(weeks=w)
        if w == 0 or d.month != (d-timedelta(weeks=1)).month:
            items.append(f'<g fill="{c["muted"]}">{_txt(X0+w*XSTEP,174,d.strftime("%b").upper(),"small")}</g>')
    for row, day in [(0, "Sun"), (2, "Tue"), (4, "Thu"), (6, "Sat")]:
        items.append(f'<g fill="{c["muted"]}">{_txt(77,DAY_Y+row*DAY_STEP+11,day,"small","end")}</g>')
    for offset in range(WEEKS*7):
        d = p["start"]+timedelta(days=offset)
        if d>p["today"]:
            continue
        week, row = divmod(offset, 7)
        records = p["by_day"].get(d, ())
        units = official.get(d, 0) if official is not None else sum(e["count"] for e in records)
        level = _density(units)
        fill = c["greens"][level-1] if level else c["empty"]
        x = X0 + week*XSTEP
        y = DAY_Y + row*DAY_STEP
        message = (f"{d.isoformat()}: not returned by GitHub profile calendar query"
                   if official is not None and d not in official else
                   f"{d.isoformat()}: {units} GitHub profile contributions, {len(records)} public repository events"
                   if official is not None else
                   f"{d.isoformat()}: {len(records)} observed events, {units} units" if records
                   else f"{d.isoformat()}: not observed in supplied snapshot")
        src_count = (f' data-source-count="{len(records)}"' if official is not None else '')
        items.append(f'<rect class="mobile-day" data-date="{d.isoformat()}" data-week="{week}" data-count="{units if official is not None else len(records)}"{src_count} x="{x:.2f}" y="{y:.2f}" width="{CELL}" height="{CELL}" rx="3" fill="{fill}"><title>{_esc(message)}</title></rect>')
    items.extend([
        f'<g fill="{c["muted"]}">{_txt(42,311,range_label,"small")}</g>',
        f'<rect x="28" y="336" width="404" height="346" rx="14" fill="{c["surface"]}" stroke="{c["rule"]}"/>',
        f'<g fill="{c["muted"]}">{_txt(42,358,"02 / REPOSITORY JOURNEYS","tag")}',
        _txt(416,358,"◉ MERGE · ◆ RELEASE","small","end"),'</g>',
    ])
    for route in p["routes"]:
        idx = route["index"]
        label_y = LANE_Y + idx*LANE_STEP
        track_y = label_y+21
        colour = c["routes"][idx]
        fullname = route["repo"]["full_name"]
        name = route["repo"]["name"]
        name = name if len(name) <= 25 else name[:24] + "…"
        items.append(f'<g class="mobile-route" data-repo="{_esc(fullname)}">')
        items.append(f'<rect x="43" y="{label_y-13:.2f}" width="27" height="23" rx="6" fill="{colour}"/>')
        items.append(f'<text x="56.5" y="{label_y+2.7:.2f}" text-anchor="middle" class="station-index" fill="{c["bg"]}">{idx+1:02d}</text>')
        items.append(f'<g fill="{c["text"]}">{_txt(80,label_y+3,name,"route")}</g>')
        items.append(f'<g fill="{c["muted"]}">{_txt(415,label_y+3,str(len(route["weeks"]))+" active weeks","small","end")}</g>')
        items.append(f'<line x1="{X0+CELL/2:.2f}" x2="{X0+(WEEKS-1)*XSTEP+CELL/2:.2f}" y1="{track_y:.2f}" y2="{track_y:.2f}" stroke="{c["rule"]}" stroke-width="2.3" stroke-dasharray="3 7"/>')
        if route["weeks"]:
            start_x = X0+route["weeks"][0]*XSTEP+CELL/2
            end_x = X0+route["weeks"][-1]*XSTEP+CELL/2
            if start_x == end_x:
                start_x -= 4; end_x += 4
            items.append(f'<line class="mobile-track" x1="{start_x:.2f}" x2="{end_x:.2f}" y1="{track_y:.2f}" y2="{track_y:.2f}" stroke="{colour}" stroke-width="4.2" stroke-linecap="round"/>')
            for station in route["stations"]:
                week = station["week"]
                x = X0+week*XSTEP+CELL/2
                kind = station["kind"]
                radius = 7.4 if kind == "release" else 6.4 if kind == "pr_merged" else 4.2
                items.append(f'<g class="mobile-station" data-week="{week}" data-kind="{kind}" data-repo="{_esc(fullname)}"><title>{_esc(fullname)}: {station["events"]} observed events; IDs: {_esc(", ".join(station["ids"]))}</title>')
                items.append(f'<circle cx="{x:.2f}" cy="{track_y:.2f}" r="{radius}" stroke="{colour}" stroke-width="2.2" fill="{c["surface"]}"/>')
                if kind == "release":
                    items.append(f'<path d="M{x:.2f} {track_y-3.6:.2f}l3.6 3.6 -3.6 3.6 -3.6 -3.6Z" fill="{colour}"/>')
                elif kind == "pr_merged":
                    items.append(f'<circle cx="{x:.2f}" cy="{track_y:.2f}" r="2.4" fill="{colour}"/>')
                items.append('</g>')
        items.append('</g>')
    summary = (f"{sum(v for day, v in official.items() if p['start'] <= day <= p['today']):,} GITHUB CONTRIBUTIONS · {len(p['routes'])} ROUTES"
               if official is not None else
               f"{len(p['events'])} EVENTS  ·  {len(p['routes'])} ROUTES  ·  16 WEEKS")
    items.extend([
        f'<rect x="28" y="696" width="404" height="80" rx="12" fill="{c["surface"]}" stroke="{c["rule"]}"/>',
        f'<g fill="{c["text"]}">{_txt(43,717,summary,"tag")}</g>',
        f'<g fill="{c["muted"]}">{_txt(43,736,scope,"small")}',
        _txt(43,752,"BLANK IS NOT PROOF OF ZERO CONTRIBUTIONS","small"),
        _txt(43,767,f"EXCLUDED {p['omitted_repos']} REPOS · {p['omitted_events']} EVENTS","small"),'</g>',
        '</svg>',
    ])
    return "\n".join(items)+"\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a source-backed portrait Open Source Metro card")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--theme", choices=tuple(COLOURS), default="midnight")
    parser.add_argument("--showcase", action="store_true", help="Add explicitly synthetic fixture-only events")
    options = parser.parse_args()
    raw = json.loads(options.input.read_text(encoding="utf-8"))
    if options.showcase:
        raw = demo_story(raw)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(render_mobile(raw, theme=options.theme), encoding="utf-8")
    print(f"Wrote {options.output}")


if __name__ == "__main__":
    main()
