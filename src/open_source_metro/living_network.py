"""Living Network: source-backed calendar and repository journeys.

An independent, experimental Open Source Metro design. The default renderer
never synthesises source data; a separate --showcase flag creates an explicitly
labelled, repeatable *demo-only* illustration. No network or paid dependencies.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import random

from .validation import normalise

W, H = 1460, 938
CAL_X, CAL_Y, DX, DY, CELL = 206, 232, 21.05, 19.15, 14.5
ROUTE_BASE, ROUTE_GAP = 494, 48
ROUTE_COLOURS = ('#59F0BD', '#BEA2FF', '#FF988A', '#FFD17B', '#7BC9FF')
KIND_NAMES = {
    'commit': 'Commits', 'pr_opened': 'PRs opened',
    'pr_merged': 'PRs merged', 'issue_opened': 'Issues opened',
    'release': 'Releases',
}
THEMES = {
    'midnight': dict(background='#070D16', canvas='#0C1725', panel='#101F30',
                     ink='#F1F7FE', secondary='#ADC0D2', quiet='#748EA4',
                     stroke='#2B4357', empty='#1B2D3C',
                     greens=('#245B4F', '#26866C', '#32B98A', '#76EFB8')),
    'paper': dict(background='#EAE4D7', canvas='#FAF4EA', panel='#F4EDE1',
                  ink='#263B43', secondary='#506774', quiet='#667A80',
                  stroke='#C9C9BD', empty='#E2DED0',
                  greens=('#B5D5BB', '#87BA9C', '#5F9F81', '#28775C')),
}


def xml(value: object) -> str:
    return escape(str(value), quote=True)


def label(x: float, y: float, value: object, klass: str, *, anchor: str = 'start') -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">{xml(value)}</text>'


def first_sunday(snapshot_date):
    last_sunday = snapshot_date - timedelta(days=(snapshot_date.weekday() + 1) % 7)
    return last_sunday - timedelta(weeks=52)


def build_plan(raw: dict) -> dict:
    """Select a calendar and up to five *real observed* source repositories."""
    snap = normalise(raw)
    today = snap['generated'].date()
    start = first_sunday(today)
    eligible = [e for e in snap['events']
                if start <= e['date'].date() <= today and e['date'] <= snap['generated']]
    sizes = Counter(e['repo'] for e in eligible)
    first_seen = {}
    for e in eligible:
        first_seen.setdefault(e['repo'], e['date'])
    # Prefer active repos, not old/inactive or large synthetic 'count' weights.
    featured = sorted(snap['repos'], key=lambda r: (-sizes[r['full_name']],
          first_seen.get(r['full_name'], datetime.max.replace(tzinfo=timezone.utc)),
          r['full_name']))[:5]
    repo_names = {r['full_name'] for r in featured}
    chosen = [e for e in eligible if e['repo'] in repo_names]
    trimmed = chosen[-240:]
    if len(chosen) > 240 and trimmed and chosen[-241]['date'].date() == trimmed[0]['date'].date():
        boundary = trimmed[0]['date'].date()
        trimmed = [e for e in trimmed if e['date'].date() != boundary]
    positions = {start+timedelta(days=k):(k//7,k%7) for k in range(371)}
    by_day = defaultdict(list)
    by_week_repo = defaultdict(list)
    for e in trimmed:
        by_day[e['date'].date()].append(e)
        by_week_repo[(e['repo'], positions[e['date'].date()][0])].append(e)
    # This is only *same-week co-activity*, never evidence of a dependency.
    shared = defaultdict(set)
    for (repo, week), events in by_week_repo.items():
        if events:
            shared[week].add(repo)
    return dict(snap=snap, start=start, today=today, featured=featured,
                events=trimmed, positions=positions, by_day=by_day,
                by_week_repo=by_week_repo, coactive=shared,
                omitted_events=snap['event_total']-len(trimmed),
                omitted_repos=snap['repo_total']-len(featured))


def demo_story(raw: dict) -> dict:
    """Generate a deliberately fictional, deterministic project-lifecycle exhibit."""
    if raw.get('source') != 'demo':
        raise ValueError('Synthetic network journeys require source="demo"')
    data = json.loads(json.dumps(raw))
    if not data['repositories']:
        data['_synthetic_added'] = 0
        return data
    end = datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00')).date()
    start = first_sunday(end)
    rng = random.Random(6283)
    arcs = ((0, 29), (8, 41), (15, 51), (27, 51), (33, 52))
    added = []
    for index, repo in enumerate(data['repositories'][:5]):
        begin, finish = arcs[index]
        for week in range(begin, finish+1):
            # A recognisable narrative: launch, concentrated build, then handover.
            probability = 0.63 if week < finish-4 else 0.82
            if rng.random() > probability:
                continue
            weekday = (index*2 + week*3 + rng.randrange(7)) % 7
            when = start+timedelta(days=week*7+weekday)
            if when > end:
                continue
            chance = rng.random()
            kind = ('commit' if chance < .61 else 'pr_opened' if chance < .78
                    else 'pr_merged' if chance < .93 else 'issue_opened')
            if (week-begin) in (11, 22) and week < finish-3:
                kind = 'pr_merged'
            if week >= finish-1:
                kind = 'release' if week == finish else 'commit'
            count = rng.randrange(1, 5) if kind == 'commit' else 1
            added.append({'id': f'illustration-project-{index+1}-week-{week:02d}',
                          'repo_full_name': repo['full_name'], 'kind': kind,
                          'count':count,'occurred_at':when.isoformat()+'T12:00:00Z'})
    data['activity'].extend(added)
    data['_synthetic_added'] = len(added)
    return data


def _density(units: int) -> int:
    return 0 if not units else 1 if units < 3 else 2 if units < 6 else 3 if units < 10 else 4


def render_svg(raw: dict, *, theme: str = 'midnight') -> str:
    """Return standalone accessible SVG; no scripts, external URLs or fake events."""
    if theme not in THEMES:
        raise ValueError('Unknown colour theme')
    p = build_plan(raw)
    t = THEMES[theme]
    dark = theme == 'midnight'
    demo = p['snap']['source'] == 'demo'
    exhibition = demo and bool(raw.get('_synthetic_added'))
    tag = ('SYNTHETIC STORY SHOWCASE' if exhibition else
           'SHARED SYNTHETIC FIXTURE' if demo else
           'PUBLIC EVENT SNAPSHOT • COVERAGE INCOMPLETE')
    user = p['snap']['user']
    counts = Counter(e['kind'] for e in p['events'])
    total_units = sum(e['count'] for e in p['events'])
    featured = p['featured']
    colors = ROUTE_COLOURS if dark else ('#168B69','#7759B8','#BC5A58','#9C711C','#317CA9')
    bg = t['background']; ink=t['ink']; panel=t['panel']; canvas=t['canvas']
    c = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
         f'<title id="title">Open Source Metro | Living Network | {xml(tag)}</title>',
         '<desc id="desc">A 53-week Sunday-to-Saturday GitHub-style event calendar above up to five horizontal repository journeys. Each coloured line is a specific repository. Small stops represent weeks with recorded source events; larger rings show recorded merged pull requests or releases. Thin interchange bars mean only that projects had source events in the same week, not dependencies. Blank calendar dates are unobserved, not confirmed zero GitHub contributions. This image does not claim a complete GitHub contributions history.</desc>',
         '<defs><style><![CDATA[',
         '.hero{font-family:DejaVu Sans,Arial,sans-serif;font-size:38px;font-weight:800;letter-spacing:-1.65px}',
         '.tag{font-family:DejaVu Sans,Arial,sans-serif;font-size:10px;font-weight:700;letter-spacing:1.6px}',
         '.sub{font:500 13px system-ui,Segoe UI,sans-serif}',
         '.meta{font-family:DejaVu Sans,Arial,sans-serif;font-size:11px;font-weight:650;letter-spacing:.35px}',
         '.month{font:700 11px system-ui,Segoe UI,sans-serif}',
         '.route{font:800 13px system-ui,Segoe UI,sans-serif}',
         '.tiny{font:600 9px system-ui,Segoe UI,sans-serif}',
         '.num{font:850 11px system-ui,Segoe UI,sans-serif}',
         '.station text{pointer-events:none}',
         '.stop{transition:opacity .15s ease}',
         '.scan-cursor{pointer-events:none}',
         '@media(prefers-reduced-motion:reduce){.stop{transition:none}}',
         ']]></style><clipPath id="route-reveal"><rect id="route-reveal-width" x="196" y="458" width="1129" height="260"/></clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="{bg}"/>',
         f'<rect x="22" y="21" width="1416" height="896" rx="26" fill="{canvas}" stroke="{t["stroke"]}" stroke-width="1.1"/>',
         f'<rect x="48" y="44" width="7" height="66" rx="3.5" fill="{colors[0]}"/>',
         f'<g fill="{ink}">',label(74,84,'PROJECTS IN MOTION','hero'),'</g>',
         f'<g fill="{t["secondary"]}">',label(76,108,'One year. Five project journeys. Every stop has a source.','sub'),'</g>',
         f'<rect x="1056" y="57" width="346" height="39" rx="19" fill="{panel}" stroke="{t["stroke"]}"/>',
         f'<circle cx="1077" cy="76" r="5" fill="{colors[0]}"/>',
         f'<g fill="{ink}">',label(1092,80,tag,'tag'),'</g>',
         f'<rect x="65" y="125" width="1329" height="54" rx="12" fill="{panel}" stroke="{t["stroke"]}"/>',
         f'<g fill="{t["secondary"]}">',label(84,146,'SOURCE EVENTS','tiny'),label(277,146,'OBSERVED UNITS','tiny'),label(478,146,'FEATURED ROUTES','tiny'),label(692,146,'MERGES / RELEASES','tiny'),label(952,146,'WINDOW','tiny'),'</g>',
         f'<g fill="{ink}">',label(84,167,str(len(p['events'])),'route'),label(277,167,str(total_units),'route'),label(478,167,str(len(featured)),'route'),label(692,167,f"{counts['pr_merged']} / {counts['release']}",'route'),label(952,167,f'{p["start"].isoformat()} – {p["today"].isoformat()}','meta'),'</g>',
         f'<rect x="65" y="189" width="1329" height="214" rx="15" fill="{panel}" stroke="{t["stroke"]}"/>',
         f'<g fill="{t["secondary"]}">',label(88,212,'01 / CONTRIBUTION CALENDAR','tag'),label(1366,212,'OBSERVED EVENT UNITS • UTC','meta',anchor='end'),'</g>']
    # Month labels and calendar lanes.
    for k in range(53):
        d=p['start']+timedelta(weeks=k)
        if k == 0 or d.month != (d-timedelta(weeks=1)).month:
            c += [f'<g fill="{t["quiet"]}">',label(CAL_X+k*DX,226,d.strftime('%b').upper(),'month'),'</g>']
        if k%13==0 and k>0:
            x=CAL_X+k*DX-7
            c.append(f'<line x1="{x:.1f}" y1="237" x2="{x:.1f}" y2="375" stroke="{t["stroke"]}" stroke-dasharray="2 5" opacity=".6"/>')
    for row,name in ((0,'SUN'),(2,'TUE'),(4,'THU'),(6,'SAT')):
        c += [f'<g fill="{t["quiet"]}">',label(184,CAL_Y+row*DY+11,name,'tiny',anchor='end'),'</g>']
    for k in range(371):
        week,weekday=divmod(k,7)
        day=p['start']+timedelta(days=k)
        if day>p['today']:
            continue
        events=p['by_day'].get(day,())
        units=sum(e['count'] for e in events)
        level=_density(units)
        fill=t['greens'][level-1] if level else t['empty']
        x=CAL_X+week*DX;y=CAL_Y+weekday*DY
        title=f'{day.isoformat()}: {len(events)} source events, {units} observed units' if events else f'{day.isoformat()}: no observation in supplied snapshot'
        c.append(f'<rect class="calendar-day" data-week="{week}" data-date="{day.isoformat()}" data-count="{len(events)}" x="{x:.2f}" y="{y:.2f}" width="{CELL}" height="{CELL}" rx="3" fill="{fill}"><title>{xml(title)}</title></rect>')
    c.extend([f'<g fill="{t["secondary"]}">',label(91,395,'BLANK ≠ VERIFIED ZERO','tiny'),label(1145,395,'LESS','tiny'),'</g>'])
    for i in range(5):
        c.append(f'<rect x="{1183+i*27}" y="386" width="13" height="13" rx="2.5" fill="{t["empty"] if not i else t["greens"][i-1]}"/>')
    c += [f'<g fill="{t["secondary"]}">',label(1355,395,'MORE','tiny',anchor='end'),'</g>']
    # Repository journeys, not activity-type rails.
    c += [f'<rect x="65" y="417" width="1329" height="333" rx="15" fill="{panel}" stroke="{t["stroke"]}"/>',
          f'<g fill="{t["secondary"]}">',label(88,441,'02 / THE REPOSITORY NETWORK','tag'),
          label(1364,441,'ROUTES = REPOSITORIES • STOPS = ACTIVE WEEKS','meta',anchor='end'),'</g>']
    # Week guides connect both panels visually without placing fake calendar marks.
    for week in range(0,53,4):
        x=CAL_X+week*DX+CELL/2
        c.append(f'<line x1="{x:.1f}" y1="463" x2="{x:.1f}" y2="705" stroke="{t["stroke"]}" opacity=".43" stroke-dasharray="2 7"/>')
    # Connections represent coactivity during the *same* source week, capped.
    repo_ids=[r['full_name'] for r in featured]
    shared=[]
    for week,names in p['coactive'].items():
        indexes=sorted(repo_ids.index(name) for name in names if name in repo_ids)
        if len(indexes)>1 and (max(indexes)-min(indexes))<=3:
            important=any(e['kind'] in ('pr_merged','release') for r in names for e in p['by_week_repo'].get((r,week),()))
            shared.append((not important,-len(indexes),week,min(indexes),max(indexes)))
    for _,_,week,a,b in sorted(shared)[:9]:
        x=CAL_X+week*DX+CELL/2
        top=ROUTE_BASE+a*ROUTE_GAP;bottom=ROUTE_BASE+b*ROUTE_GAP
        c.append(f'<g data-week="{week}" class="interchange" clip-path="url(#route-reveal)"><line x1="{x:.1f}" y1="{top:.1f}" x2="{x:.1f}" y2="{bottom:.1f}" stroke="{t["quiet"]}" stroke-width="1.25" stroke-dasharray="3 4" opacity=".68"><title>Same-week repository activity only, not a dependency</title></line></g>')
    for i,r in enumerate(featured):
        full=r['full_name'];name=r['name'];color=colors[i]; y=ROUTE_BASE+i*ROUTE_GAP
        weeks=sorted(w for (repo,w) in p['by_week_repo'] if repo==full)
        source_events=[e for e in p['events'] if e['repo']==full]
        c.append(f'<g class="journey" data-repo-index="{i}">')
        c.append(f'<rect x="80" y="{y-18}" width="29" height="29" rx="10" fill="{color}"/>')
        c.append(f'<text x="94.5" y="{y+2}" font-size="12" font-weight="850" font-family="system-ui,sans-serif" fill="{bg}" text-anchor="middle">{i+1:02}</text>')
        shortened = name if len(name)<=11 else name[:10]+'…'
        c.append(f'<g fill="{ink}">{label(119,y-3,shortened,"route")}</g>')
        c.append(f'<g fill="{t["quiet"]}">{label(119,y+12,f"{len(weeks)} active weeks","tiny")}</g>')
        c.append('<g class="network-track" clip-path="url(#route-reveal)">')
        left=CAL_X+CELL/2
        right=CAL_X+52*DX+CELL/2
        c.append(f'<line x1="{left:.1f}" y1="{y}" x2="{right:.1f}" y2="{y}" stroke="{t["stroke"]}" stroke-width="2" stroke-dasharray="2 7"/>')
        if weeks:
            x1=CAL_X+weeks[0]*DX+CELL/2;x2=CAL_X+weeks[-1]*DX+CELL/2
            if x1==x2:x1-=7;x2+=7
            c.append(f'<line class="route-line" x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" stroke="{color}" stroke-width="4.5" stroke-linecap="round" opacity=".86"/>')
        for week in weeks:
            es=p['by_week_repo'][(full,week)]
            units=sum(e['count'] for e in es)
            milestone='release' if any(e['kind']=='release' for e in es) else 'merge' if any(e['kind']=='pr_merged' for e in es) else 'event'
            x=CAL_X+week*DX+CELL/2
            tooltip=f'{name}, week {week+1}: '+', '.join(f'{e["id"]} ({e["kind"]}, {e["count"]} units)' for e in es)
            radius = 10 if milestone=='release' else 8 if milestone=='merge' else 4.75
            c.append(f'<g class="stop station" data-week="{week}" data-repo-index="{i}" data-event-kind="{milestone}"><title>{xml(tooltip)}</title>')
            if milestone!='event':
                c.append(f'<circle cx="{x:.1f}" cy="{y}" r="{radius+5}" fill="{color}" opacity=".12"/>')
            c.append(f'<circle cx="{x:.1f}" cy="{y}" r="{radius}" fill="{panel}" stroke="{color}" stroke-width="{2.6 if milestone!="event" else 2}"/>')
            if milestone=='release':
                c.append(f'<path d="M{x-4:.1f} {y}L{x:.1f} {y-4}L{x+4:.1f} {y}L{x:.1f} {y+4}Z" fill="{color}"/>')
            elif milestone=='merge':
                c.append(f'<circle cx="{x:.1f}" cy="{y}" r="3.0" fill="{color}"/>')
            elif units>4:
                c.append(f'<circle cx="{x:.1f}" cy="{y}" r="1.8" fill="{color}"/>')
            c.append('</g>')
        c.append('</g>')  # close timeline clip; keep the repository label always visible
        c.append(f'<g fill="{t["quiet"]}">{label(1380,y+5,f"{len(source_events)} EVENTS", "meta",anchor="end")}</g>')
        c.append('</g>')
    # A compact milestone passport is the narrative payoff, never invented labels.
    # Use actual source IDs and dates; a demo showcase remains labelled synthetic.
    milestones = [e for e in p['events'] if e['kind'] in ('release', 'pr_merged')]
    chosen_milestones = []
    if milestones:
        if len(milestones) <= 4:
            chosen_milestones = milestones
        else:
            idxs = sorted({round(i*(len(milestones)-1)/3) for i in range(4)})
            chosen_milestones = [milestones[i] for i in idxs]
    c.extend([f'<rect x="65" y="757" width="1329" height="136" rx="15" fill="{panel}" stroke="{t["stroke"]}"/>',
              f'<g fill="{t["secondary"]}">',label(88,778,'03 / MILESTONE PASSPORT','tag'),
              label(1364,778,'RECORDED SOURCE EVENTS • NO INVENTED MILESTONE TITLES','meta',anchor='end'),'</g>'])
    if not chosen_milestones:
        c.append(f'<g fill="{t["quiet"]}">{label(92,836,"No recorded merge or release milestones in this snapshot.","sub")}</g>')
    for i, event in enumerate(chosen_milestones):
        repo_idx = next((j for j,r in enumerate(featured) if r['full_name']==event['repo']),0)
        colour=colors[repo_idx]
        x=86+i*327
        short_repo=event['repo'].split('/')[-1][:18]
        when=event['date'].strftime('%d %b %Y')
        kind_name='RELEASE' if event['kind']=='release' else 'PR MERGED'
        milestone_week=p['positions'][event['date'].date()][0]
        c.append(f'<g class="passport-card" data-week="{milestone_week}"><title>{xml(event["id"])}: {xml(event["repo"])} / {xml(event["kind"])} / {when}</title>')
        c.append(f'<rect x="{x}" y="789" width="311" height="89" rx="10" fill="{canvas}" stroke="{t["stroke"]}"/>')
        c.append(f'<rect x="{x}" y="789" width="5" height="89" rx="2.5" fill="{colour}"/>')
        c.append(f'<circle cx="{x+26}" cy="809" r="7" fill="none" stroke="{colour}" stroke-width="2.2"/>')
        c.append(f'<g fill="{t["secondary"]}">{label(x+41,813,kind_name,"tiny")}{label(x+295,813,when,"tiny",anchor="end")}</g>')
        c.append(f'<g fill="{ink}">{label(x+18,840,short_repo,"route")}</g>')
        c.append(f'<g fill="{t["quiet"]}">{label(x+18,860,event["id"][:35],"tiny")}</g>')
        c.append('</g>')
    # Embedded replay scan line, hidden in stills but activated by browser JS.
    c.append(f'<line class="scan-cursor" id="scan-cursor" x1="{CAL_X+52*DX+CELL/2:.1f}" y1="229" x2="{CAL_X+52*DX+CELL/2:.1f}" y2="714" stroke="{colors[0]}" stroke-width="1.6" stroke-dasharray="5 5" opacity="0"/>')
    c += [f'<g fill="{t["secondary"]}">',
          label(90,732,'● ACTIVE WEEK','tiny'),label(282,732,'◉ MERGED PR','tiny'),label(459,732,'◆ RELEASE','tiny'),label(619,732,'┊ SAME-WEEK CO-ACTIVITY','tiny'),
          label(1015,732,f"OMITTED {p['omitted_repos']} REPOS / {p['omitted_events']} EVENTS",'tiny'),'</g>',
          f'<g fill="{t["quiet"]}">',
          label(70,922,('DEMO ONLY • +'+str(raw.get('_synthetic_added',0))+' INVENTED SHOWCASE EVENTS' if exhibition else
                          'SYNTHETIC FIXTURE • NO EXTRA EVENTS' if demo else
                          'PUBLIC SOURCE EVENTS ONLY • COVERAGE NOT COMPLETE'), 'tag'),
          label(1390,922,'CALENDAR = SOURCE OBSERVATIONS, NOT VERIFIED GITHUB TOTALS','tiny',anchor='end'),'</g>',
          '</svg>']
    return '\n'.join(c)+'\n'


def browser_html(raw: dict, svg: str, *, theme: str = 'midnight') -> str:
    """Offline, self-contained interactive replay of the exact rendered events."""
    p=build_plan(raw)
    # JSON escapes '<' and other script terminators; event labels are untrusted.
    event_payload=[{'week':p['positions'][e['date'].date()][0],
                    'date':e['date'].date().isoformat(),'kind':e['kind'],
                    'repo':e['repo'],'units':e['count'],'id':e['id']}
                   for e in p['events']]
    safe_json=json.dumps(event_payload,ensure_ascii=True,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    routes=json.dumps([r['full_name'] for r in p['featured']],ensure_ascii=True)
    dark=theme=='midnight'; bg='#070d16' if dark else '#eae4d7';ink='#f1f7fe' if dark else '#263b43';muted='#9db7c8' if dark else '#506774';panel='#102033' if dark else '#faf4ea';rule='#34516a' if dark else '#c1c5b7'
    provenance='SYNTHETIC DESIGN SHOWCASE' if raw.get('_synthetic_added') else 'SYNTHETIC FIXTURE' if raw.get('source')=='demo' else 'PUBLIC SOURCE SNAPSHOT • INCOMPLETE COVERAGE'
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Open Source Metro | Living Network replay</title>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<style>:root{{--bg:{bg};--ink:{ink};--muted:{muted};--panel:{panel};--rule:{rule};font:15px system-ui,Segoe UI,sans-serif;color:var(--ink);background:var(--bg)}}*{{box-sizing:border-box}}body{{margin:0;padding:24px}}main{{max-width:1520px;margin:auto}}h1{{font-size:clamp(1.45rem,3vw,2.2rem);margin:0 0 4px}}p{{color:var(--muted);line-height:1.5}}.eyebrow{{font-weight:800;letter-spacing:.14em;font-size:.73rem;color:var(--muted)}}.tools{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;padding:16px;margin:18px 0;border:1px solid var(--rule);border-radius:16px;background:var(--panel)}}button,select{{border:1px solid var(--rule);border-radius:9px;padding:11px 15px;font:700 14px system-ui;color:var(--ink);background:transparent;cursor:pointer}}button:focus-visible,select:focus-visible,input:focus-visible{{outline:2px solid #58edbc;outline-offset:2px}}button[aria-pressed=true]{{background:#206a5d;color:#fff}}input[type=range]{{flex:1;min-width:160px;accent-color:#59f0bd}}.viewport{{overflow-x:auto;border:1px solid var(--rule);border-radius:18px;background:var(--panel)}}.viewport svg{{width:100%;height:auto;display:block;min-width:950px}}.status{{font-weight:700;min-width:152px}}.routes{{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}}.routes button{{border-radius:999px;padding:9px 13px;font-size:13px}}.legend{{font-size:.88rem}}.ledger{{margin-top:20px;padding:16px;border:1px solid var(--rule);border-radius:16px}}.ledger ol{{margin:12px 0;padding-left:22px;max-height:240px;overflow:auto}}.ledger li{{padding:5px 2px;color:var(--muted)}}.footer{{font-size:.8rem}}@media(max-width:680px){{body{{padding:10px}}.viewport svg{{min-width:1100px}}.tools{{gap:10px}}.status{{min-width:auto}}}}</style></head>
<body><main><div class="eyebrow">OPEN SOURCE METRO / INTERACTIVE LAB / {xml(provenance)}</div><h1>Watch the network grow</h1><p>Choose a repository route, drag through the year or play the chronology. Every stop is traceable to an event in this supplied snapshot. The demonstration is not a complete GitHub contributions record.</p>
<section class="tools" aria-label="Chronological network playback"><button id="play" type="button" aria-label="Play chronological replay">▶ Play</button><button id="restart" type="button">↺ Restart</button><label for="week">Week</label><input id="week" type="range" min="0" max="52" value="52" step="1" aria-label="Timeline week"><output id="status" class="status" for="week" aria-live="polite">Week 53 / 53</output><label for="speed">Speed</label><select id="speed"><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></section>
<div class="routes" id="routes" role="group" aria-label="Filter repository journeys"></div>
<div class="viewport" role="region" aria-label="Scroll horizontally to explore the metro network" tabindex="0">{svg}</div>
<section class="ledger" aria-labelledby="ledger-title"><h2 id="ledger-title">Source events at this stop</h2><div id="summary" aria-live="polite"></div><ol id="event-list"></ol></section>
<p class="footer">Stops are observed active weeks. Route spans do not imply activity on unmarked days; dashed interchanges mean overlapping weeks, not repository dependencies. No network requests, cookies, tracking or external scripts.</p>
<script>"use strict";
const events={safe_json};const repos={routes};const input=document.getElementById('week');const status=document.getElementById('status');const summary=document.getElementById('summary');const list=document.getElementById('event-list');const play=document.getElementById('play');const speed=document.getElementById('speed');const routes=document.getElementById('routes');const svg=document.querySelector('.viewport svg');const cursor=document.getElementById('scan-cursor');const reveal=document.getElementById('route-reveal-width');const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let chosen=-1,playing=false,last=0,elapsed=0;
const buttons=[];repos.forEach((repo,i)=>{{const b=document.createElement('button');b.textContent=('0'+(i+1)).slice(-2)+' '+repo.split('/').pop();b.dataset.index=i;b.setAttribute('aria-pressed','false');b.addEventListener('click',()=>{{chosen=chosen===i?-1:i;update();}});routes.appendChild(b);buttons.push(b);}});
function update(){{const week=Number(input.value);const until=events.filter(e=>e.week<=week&&(chosen<0||e.repo===repos[chosen]));const thisWeek=events.filter(e=>e.week===week&&(chosen<0||e.repo===repos[chosen]));status.textContent='Week '+(week+1)+' / 53';summary.textContent=until.length+' observed events through this week; '+thisWeek.length+' in the selected week'+(chosen<0?'':' for '+repos[chosen])+'.';list.replaceChildren();for(const e of thisWeek.slice(0,32)){{const li=document.createElement('li');li.textContent=e.date+' · '+e.repo+' · '+e.kind+' · '+e.units+' source units ('+e.id+')';list.appendChild(li);}}if(!thisWeek.length){{const li=document.createElement('li');li.textContent='No source event in the selected week and route.';list.appendChild(li);}}
svg.querySelectorAll('[data-week]').forEach(el=>{{el.style.opacity=Number(el.dataset.week)>week?'.06':'';}});svg.querySelectorAll('.journey').forEach(el=>{{el.style.opacity=chosen>=0&&Number(el.dataset.repoIndex)!==chosen?'.13':'';}});buttons.forEach((b,i)=>b.setAttribute('aria-pressed',String(i===chosen)));cursor.setAttribute('x1',String({CAL_X}+week*{DX}+{CELL}/2));cursor.setAttribute('x2',String({CAL_X}+week*{DX}+{CELL}/2));cursor.setAttribute('opacity','0.8');reveal.setAttribute('width',String(15+(week*{DX})));}}
function stop(){{playing=false;play.textContent='▶ Play';play.setAttribute('aria-label','Play chronological replay');}}
function frame(ts){{if(!playing)return;if(!last)last=ts;elapsed+=Math.min(100,ts-last);last=ts;const step=410/Number(speed.value);if(elapsed>=step){{const ticks=Math.floor(elapsed/step);elapsed-=ticks*step;input.value=Math.min(52,Number(input.value)+ticks);update();if(Number(input.value)===52){{stop();return;}}}}requestAnimationFrame(frame);}}
play.addEventListener('click',()=>{{if(playing){{stop();return;}}if(Number(input.value)===52)input.value=0;playing=true;elapsed=0;last=0;play.textContent='Ⅱ Pause';play.setAttribute('aria-label','Pause chronological replay');update();requestAnimationFrame(frame);}});
input.addEventListener('input',()=>{{stop();update();}});document.getElementById('restart').addEventListener('click',()=>{{stop();input.value=0;update();}});if(reduced){{play.title='Motion preference detected: playback starts only on demand';}}update();
</script></main></body></html>'''


def generate(raw: dict, output: Path, *, showcase: bool = False, theme: str = 'midnight') -> list[Path]:
    if showcase:
        raw = demo_story(raw)
    output.mkdir(parents=True,exist_ok=True)
    svg=render_svg(raw,theme=theme)
    # Stable names and provenance separate faithful from invented demo views.
    stem='living-network-showcase' if showcase else 'living-network-snapshot'
    svg_path=output/(stem+'.svg')
    html_path=output/(stem+'.html')
    svg_path.write_text(svg,encoding='utf-8')
    html_path.write_text(browser_html(raw,svg,theme=theme),encoding='utf-8')
    return [svg_path,html_path]


def main() -> None:
    parser=argparse.ArgumentParser(description='Build the Open Source Metro Living Network experiment')
    parser.add_argument('--input',type=Path,required=True,help='v1 normalised snapshot JSON')
    parser.add_argument('--output',type=Path,default=Path('output/living-network'))
    parser.add_argument('--theme',choices=tuple(THEMES),default='midnight')
    parser.add_argument('--showcase',action='store_true',help='Add clearly invented event data (demo source only)')
    args=parser.parse_args()
    raw=json.loads(args.input.read_text(encoding='utf-8'))
    for path in generate(raw,args.output,showcase=args.showcase,theme=args.theme):
        print(path)

if __name__=='__main__':
    main()
