"""Compact profile-sized Living Network. Keeps the large renderer untouched.

Every coloured stop is an observed activity week in one repository; stretches
of rail between stops are a schematic time axis, not invented contributions.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
from html import escape
import json
from pathlib import Path

from .living_network import build_plan, demo_story, _density
from .contribution_calendar import normalise_calendar_for_snapshot, contribution_intensity

WIDTH, HEIGHT = 1360, 462
X0, XSTEP, DAY_SIZE = 202.0, 19.45, 12.8
DAY_Y, DAY_STEP = 151.0, 15.3
LANE_Y, LANE_STEP = 317.0, 22.5

COLOURS = {
    'midnight': dict(bg='#070C15', panel='#101B2B', surface='#132235',
        text='#EDF6FF', muted='#9BB2C7', rule='#294057', empty='#233246',
        greens=('#236049','#268F6D','#3EC995','#7FF8C0'),
        routes=('#5AEFC0','#BFABFF','#FF9C89','#FFD37E','#81CBFF')),
    'paper': dict(bg='#EAE3D3', panel='#F8F1E5', surface='#F0E8D9',
        text='#2A3C42', muted='#526876', rule='#C5C7BB', empty='#E0DCD0',
        greens=('#B3D2B9','#8BBCA0','#589D7D','#28795C'),
        routes=('#147B60','#6E55AE','#B75552','#95691B','#317CAC')),
}


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def txt(x: float, y: float, value: object, cls: str, anchor: str = 'start') -> str:
    return f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" text-anchor="{anchor}">{esc(value)}</text>'


def compact_plan(raw: dict) -> dict:
    """Expose source-backed, testable week and milestone semantics."""
    p = build_plan(raw)
    routes = []
    for i, repo in enumerate(p['featured']):
        full = repo['full_name']
        weeks = sorted(week for name, week in p['by_week_repo'] if name == full)
        events = [e for e in p['events'] if e['repo'] == full]
        stops = []
        for week in weeks:
            es = p['by_week_repo'][(full, week)]
            kind = ('release' if any(e['kind']=='release' for e in es) else
                    'pr_merged' if any(e['kind']=='pr_merged' for e in es) else 'event')
            stops.append(dict(week=week, kind=kind, ids=[e['id'] for e in es],
                              events=len(es), units=sum(e['count'] for e in es)))
        routes.append(dict(repo=repo,index=i,weeks=weeks,stations=stops,events=len(events)))
    p['routes'] = routes
    p['milestones'] = sum(e['kind'] in ('release','pr_merged') for e in p['events'])
    return p


def render_compact(raw: dict, *, theme: str = 'midnight') -> str:
    """Source-verified static GitHub README SVG, no scripts or external assets."""
    if theme not in COLOURS:
        raise ValueError('Unknown theme')
    p = compact_plan(raw)
    official = normalise_calendar_for_snapshot(raw, p['snap'])
    t = COLOURS[theme]
    routes = p['routes']
    colors = t['routes']
    demo = p['snap']['source'] == 'demo'
    synthetic = demo and bool(raw.get('_synthetic_added'))
    provenance = ('GITHUB CALENDAR · PARTIAL ROUTES' if official is not None else
                  'SYNTHETIC DESIGN SHOWCASE' if synthetic else
                  'SHARED SYNTHETIC FIXTURE' if demo else
                  'PUBLIC EVENTS · INCOMPLETE COVERAGE')
    years = f"{p['start'].year}–{p['today'].year}"
    metrics = (f"{sum(amount for day, amount in official.items() if p['start'] <= day <= p['today']):,} GitHub contributions · {len(p['events'])} public events"
               if official is not None else
               f"{len(p['events'])} events · {len(routes)} routes · {p['milestones']} milestones")
    active_days = (sorted(day for day, amount in official.items()
                          if p['start'] <= day <= p['today'] and amount > 0)
                   if official is not None else sorted(p['by_day']))
    active_weeks = {p['positions'][day][0] for day in active_days}
    intensity_samples = (sorted(value for day,value in official.items()
                                if p['start'] <= day <= p['today'] and value > 0)
                         if official is not None else [])
    if not demo:
        if active_days:
            date_range = f"{active_days[0]:%d %b %Y} to {active_days[-1]:%d %b %Y}"
            subtitle = (f"GitHub profile contributions on {len(active_days)} days · {date_range}" if official is not None
                        else f"Observed {len(active_days)} active days · {date_range}")
        else:
            subtitle = ("No GitHub profile contributions in selected dates" if official is not None
                        else "No source events observed in selected repositories")
    else:
        subtitle = "A year of source-backed project journeys"
    items = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="metro-title metro-desc">',
        f'<title id="metro-title">Open Source Metro / Project journeys / {esc(provenance)}</title>',
        (('<desc id="metro-desc">GitHub GraphQL profile-visible contribution counts form the annual day squares. Separate public repository history supports the five schematic project routes; routes do not account for all calendar totals. A blank square means zero in this GitHub profile calendar, which may reflect privacy settings. Individual project events are not a complete GitHub contribution record.</desc>')
         if official is not None else
         '<desc id="metro-desc">A compact 53-week Sunday-to-Saturday GitHub-style event calendar with up to five repository journeys aligned to the same week positions. Stops are observed events; merges are rings, releases diamonds. Rails between stops are schematic and do not mean continuous contributions. Blank days are unobserved, not verified zero contributions. This is not GitHub’s official contributions chart.</desc>'),
        '<defs><style><![CDATA[',
        '.display{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:27px;font-weight:850;letter-spacing:-1px}',
        '.small{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:10px;font-weight:600}',
        '.tag{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:9px;font-weight:800;letter-spacing:1px}',
        '.month{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:9px;font-weight:700}',
        '.route{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:12px;font-weight:700}',
        '.count{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:11px;font-weight:750}',
        '.index{font-family:DejaVu Sans,Segoe UI,Arial,sans-serif;font-size:10px;font-weight:850}',
        ']]></style>',
        '<clipPath id="compact-reveal"><rect id="compact-reveal-width" x="192" y="293" width="1068" height="130"/></clipPath>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="1334" height="436" rx="22" fill="{t["panel"]}" stroke="{t["rule"]}" stroke-width="1"/>',
        f'<rect x="36" y="33" width="5" height="47" rx="2.5" fill="{colors[0]}"/>',
        f'<g fill="{t["text"]}">{txt(53,59,"OPEN SOURCE METRO","display")}</g>',
        f'<g fill="{t["muted"]}">{txt(55,79,subtitle,"small")}</g>',
        f'<rect x="994" y="34" width="323" height="25" rx="12.5" fill="{t["surface"]}" stroke="{t["rule"]}"/>',
        f'<circle cx="1008" cy="46.5" r="3.3" fill="{colors[0]}"/>',
        f'<g fill="{t["text"]}">{txt(1019,50,provenance,"tag")}</g>',
        f'<g fill="{t["muted"]}">{txt(1310,82,metrics,"small",anchor="end")}</g>',
        f'<rect x="35" y="94" width="1290" height="175" rx="13" fill="{t["surface"]}" stroke="{t["rule"]}"/>',
        f'<g fill="{t["muted"]}">{txt(53,113,("01 / GITHUB PROFILE CONTRIBUTIONS" if official is not None else "01 / SOURCE ACTIVITY"),"tag")}',
        txt(1305,113,(f"GITHUB CALENDAR · {len(active_weeks)} ACTIVE WEEKS" if official is not None else
                         f"OBSERVED {len(active_weeks)}/53 WEEKS  ·  UTC" if not demo else
                         '53 WEEKS  ·  SUN–SAT  ·  UTC'),'tag',anchor='end'),'</g>',
    ]
    # Source-observed contribution-style calendar. No blank day means a verified zero.
    for w in range(53):
        d = p['start']+timedelta(weeks=w)
        if w==0 or d.month != (d-timedelta(weeks=1)).month:
            items.append(f'<g fill="{t["muted"]}">{txt(X0+w*XSTEP,143,d.strftime("%b").upper(),"month")}</g>')
    for row,day in ((0,'S'),(2,'T'),(4,'T'),(6,'S')):
        items.append(f'<g fill="{t["muted"]}">{txt(187,DAY_Y+row*DAY_STEP+10,day,"small",anchor="end")}</g>')
    for offset in range(371):
        day = p['start']+timedelta(days=offset)
        if day > p['today']:
            continue
        week,row = divmod(offset,7)
        observed = p['by_day'].get(day,())
        units = official.get(day, 0) if official is not None else sum(e['count'] for e in observed)
        level = (contribution_intensity(units, intensity_samples)
                 if official is not None else _density(units))
        fill = t['greens'][level-1] if level else t['empty']
        x = X0+week*XSTEP
        y = DAY_Y+row*DAY_STEP
        desc = (f'{day.isoformat()}: not returned in GitHub profile calendar query'
                if official is not None and day not in official else
                f'{day.isoformat()}: {units} GitHub profile contributions, {len(observed)} observed public repository events'
                if official is not None else
                f'{day.isoformat()}: {len(observed)} source events, {units} observed units' if observed else
                f'{day.isoformat()}: unobserved in supplied snapshot')
        source_attribute = (f' data-source-count="{len(observed)}"' if official is not None else '')
        items.append(f'<rect class="calendar-day" data-week="{week}" data-date="{day.isoformat()}" data-count="{units if official is not None else len(observed)}"{source_attribute} x="{x:.2f}" y="{y:.2f}" width="{DAY_SIZE}" height="{DAY_SIZE}" rx="2.4" fill="{fill}"><title>{esc(desc)}</title></rect>')
        if any(e['kind']=='release' for e in observed):
            items.append(f'<path class="calendar-milestone" data-week="{week}" data-kind="release" d="M{x+DAY_SIZE/2:.2f} {y-2.8:.2f}l3.2 3.2 -3.2 3.2 -3.2 -3.2Z" fill="{colors[3]}"><title>Recorded release on {day.isoformat()}</title></path>')
    items += [
        f'<g fill="{t["muted"]}">{txt(54,260,("DAY SQUARES = GITHUB PROFILE · ROUTES = PARTIAL PUBLIC REPOSITORY HISTORY" if official is not None else "BLANK = NO OBSERVATION, NOT CONFIRMED INACTIVITY"),"tag")}</g>',
        f'<rect x="35" y="281" width="1290" height="141" rx="13" fill="{t["surface"]}" stroke="{t["rule"]}"/>',
        f'<g fill="{t["muted"]}">{txt(53,299,"02 / PROJECT ROUTES","tag")}',
        txt(1306,299,"◉ MERGE  ·  ◆ RELEASE","tag",anchor='end'),'</g>',
    ]
    for route in routes:
        i=route['index']
        y=LANE_Y+i*LANE_STEP
        full=route['repo']['full_name']
        name=route['repo']['name']
        colour=colors[i]
        short=name if len(name)<=13 else name[:12]+'…'
        items.append(f'<g class="compact-journey" data-repo="{esc(full)}">')
        if not demo:
            items.append(f'<title>{esc(full)} · {len(route["weeks"])} weeks with observed activity</title>')
        items.append(f'<rect x="52" y="{y-9:.1f}" width="23" height="18" rx="6" fill="{colour}"/>')
        items.append(f'<text x="63.5" y="{y+3.7:.1f}" class="index" text-anchor="middle" fill="{t["bg"]}">{i+1:02}</text>')
        items.append(f'<g fill="{t["text"]}">{txt(84,y+4,short,"route")}</g>')
        items.append('<g clip-path="url(#compact-reveal)">')
        for week in range(0,53,4):
            x=X0+week*XSTEP+DAY_SIZE/2
            items.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.15" fill="{t["muted"]}" opacity=".35"/>')
        if route['weeks']:
            x1=X0+route['weeks'][0]*XSTEP+DAY_SIZE/2
            x2=X0+route['weeks'][-1]*XSTEP+DAY_SIZE/2
            if x1==x2:
                x1-=4;x2+=4
            items.append(f'<line class="compact-track" x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" stroke="{colour}" stroke-width="4.4" stroke-linecap="round" opacity=".91"/>')
            for stop in route['stations']:
                x=X0+stop['week']*XSTEP+DAY_SIZE/2
                kind=stop['kind']
                radius=7.5 if kind=='release' else 6.3 if kind=='pr_merged' else 3.5
                desc=f'{full}: {stop["events"]} source events in week {stop["week"]+1}: '+', '.join(stop['ids'])
                items.append(f'<g class="compact-station" data-week="{stop["week"]}" data-kind="{kind}" data-repo="{esc(full)}"><title>{esc(desc)}</title>')
                if kind!='event':
                    items.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius+3}" fill="{colour}" opacity=".13"/>')
                items.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.1f}" fill="{t["surface"]}" stroke="{colour}" stroke-width="2.2"/>')
                if kind=='release':
                    items.append(f'<path d="M{x:.2f} {y-3.6:.2f}l3.6 3.6 -3.6 3.6 -3.6 -3.6Z" fill="{colour}"/>')
                elif kind=='pr_merged':
                    items.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.3" fill="{colour}"/>')
                items.append('</g>')
        items.append('</g>')
        items.append(f'<g fill="{t["muted"]}">{txt(1293,y+3.7,str(len(route["weeks"]))+"w","count",anchor="end")}</g>')
        items.append('</g>')
    end=X0+52*XSTEP+DAY_SIZE/2
    items.append(f'<line id="compact-cursor" x1="{end:.2f}" x2="{end:.2f}" y1="147" y2="411" stroke="{colors[0]}" stroke-width="1.6" stroke-dasharray="4 5" opacity="0"/>')
    footer=('GITHUB PROFILE CALENDAR · ROUTE EVENTS INCOMPLETE' if official is not None else
            'DEMO ONLY · '+str(raw.get('_synthetic_added',0))+' INVENTED ILLUSTRATION EVENTS' if synthetic else
            'SYNTHETIC EXAMPLE · NO EXTRA EVENTS' if demo else
            'PUBLIC EVENTS ONLY · COVERAGE NOT COMPLETE')
    coverage_footer = (f"UNROUTED {p['omitted_repos']} REPOS · OUTSIDE YEAR {p['omitted_events']} EVENTS   |   {years}"
                       if not demo else
                       f"OMITTED {p['omitted_repos']} REPOS · {p['omitted_events']} EVENTS   |   {years}")
    items += [f'<g fill="{t["muted"]}">',
              txt(52,443,footer,'tag'),
              txt(1308,443,coverage_footer,'tag',anchor='end'),
              '</g>','</svg>']
    return '\n'.join(items)+'\n'


def main() -> None:
    parser=argparse.ArgumentParser(description='Compact GitHub profile Metro SVG: source-backed project journeys')
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--theme',choices=tuple(COLOURS),default='midnight')
    parser.add_argument('--showcase',action='store_true',help='Synthetic example only; rejects real source snapshots')
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding='utf-8'))
    if args.showcase:
        data=demo_story(data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render_compact(data,theme=args.theme),encoding='utf-8')
    print(f'Created {args.output} ({args.output.stat().st_size:,} bytes)')


if __name__=='__main__':
    main()
