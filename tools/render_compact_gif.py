"""Optional compact GitHub README GIF: replay observed-week arrivals."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

try:
    from open_source_metro.compact_profile import (
        X0, XSTEP, DAY_SIZE, LANE_Y, LANE_STEP, COLOURS, compact_plan, render_compact,
    )
    from open_source_metro.living_network import demo_story
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from open_source_metro.compact_profile import (
        X0, XSTEP, DAY_SIZE, LANE_Y, LANE_STEP, COLOURS, compact_plan, render_compact,
    )
    from open_source_metro.living_network import demo_story

SVG='{http://www.w3.org/2000/svg}'


def frame_weeks(count: int) -> list[int]:
    if not 8 <= count <= 53:
        raise ValueError('Expected 8-53 chronological frames')
    return sorted({round(i*52/(count-1)) for i in range(count)} | {52})


def frame_svg(svg: str, plan: dict, week: int, *, theme: str='midnight') -> bytes:
    """Reveal source events only; the train rests at a recorded station."""
    if theme not in COLOURS or not 0 <= week <= 52:
        raise ValueError('Invalid replay week or theme')
    root=ET.fromstring(svg)
    if root.tag!=SVG+'svg':
        raise ValueError('Expected SVG root')
    colors=COLOURS[theme]
    for node in root.iter():
        index=node.attrib.get('data-week')
        if index is not None and int(index)>week:
            node.set('opacity','0.12')
        if node.attrib.get('id')=='compact-reveal-width':
            node.set('width',str(14+week*XSTEP))
        if node.attrib.get('id')=='compact-cursor':
            x=X0+week*XSTEP+DAY_SIZE/2
            node.set('x1',f'{x:.2f}');node.set('x2',f'{x:.2f}')
            node.set('opacity','0' if week==52 else '.48')
    for route in plan['routes']:
        stops=[stop for stop in route['stations'] if stop['week']<=week]
        if not stops:
            continue
        recent=stops[-1]
        i=route['index'];x=X0+recent['week']*XSTEP+DAY_SIZE/2
        y=LANE_Y+i*LANE_STEP
        colour=colors['routes'][i]
        g=ET.SubElement(root,SVG+'g',{'class':'replay-train','data-repo':route['repo']['full_name'],
                                     'data-stop-week':str(recent['week'])})
        ET.SubElement(g,SVG+'circle',{'cx':f'{x:.2f}','cy':f'{y:.2f}','r':'8.5',
                                    'fill':colors['surface'],'stroke':colour,'stroke-width':'2.5'})
        ET.SubElement(g,SVG+'rect',{'x':f'{x-4.1:.2f}','y':f'{y-2.7:.2f}',
                                  'width':'8.2','height':'5.4','rx':'1.6','fill':colour})
        for dx in (-2.7,.8):
            ET.SubElement(g,SVG+'rect',{'x':f'{x+dx:.2f}','y':f'{y-1.7:.2f}',
                                      'width':'1.8','height':'1.7','rx':'.3',
                                      'fill':colors['surface']})
    ET.SubElement(root,SVG+'text',{
        'x':'682','y':'443','fill':colors['muted'],'font-size':'10',
        'font-family':'DejaVu Sans,Arial,sans-serif','font-weight':'700',
        'text-anchor':'middle'
    }).text=f'{week+1:02d} / 53 WEEKS' if week<52 else 'FULL NETWORK · SOURCE-BACKED STOPS'
    return ET.tostring(root,encoding='utf-8',xml_declaration=False)


def render_gif(raw: dict, target: Path, *, showcase: bool=False,
               theme: str='midnight', frames: int=26,width: int=850,
               duration_ms: int=140) -> Path:
    if not 640<=width<=1360:
        raise ValueError('Width must be between 640 and 1360 pixels')
    if not 65<=duration_ms<=1000:
        raise ValueError('Frame duration must be 65-1000ms')
    try:
        import cairosvg
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError('Optional animation requires pip install -e ".[animation]"') from exc
    if showcase:
        raw=demo_story(raw)
    plan=compact_plan(raw)
    svg=render_compact(raw,theme=theme)
    images=[]
    for week in frame_weeks(frames):
        png=cairosvg.svg2png(bytestring=frame_svg(svg,plan,week,theme=theme),output_width=width)
        images.append(Image.open(BytesIO(png)).convert('RGB'))
    base=images[-1].quantize(colors=96,method=Image.Quantize.FASTOCTREE)
    prepared=[image.quantize(palette=base,dither=Image.Dither.NONE) for image in images]
    durations=[duration_ms]*len(prepared)
    durations[-1]=2200
    target.parent.mkdir(parents=True,exist_ok=True)
    prepared[0].save(target,format='GIF',save_all=True,append_images=prepared[1:],
                     duration=durations,loop=0,disposal=2,optimize=True)
    return target


def main() -> None:
    parser=argparse.ArgumentParser(description='Render compact source-backed Metro replay GIF')
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--theme',choices=tuple(COLOURS),default='midnight')
    parser.add_argument('--showcase',action='store_true')
    parser.add_argument('--frames',type=int,default=26)
    parser.add_argument('--width',type=int,default=850)
    parser.add_argument('--duration-ms',type=int,default=140)
    args=parser.parse_args()
    raw=json.loads(args.input.read_text(encoding='utf-8'))
    out=render_gif(raw,args.output,showcase=args.showcase,theme=args.theme,
                   frames=args.frames,width=args.width,duration_ms=args.duration_ms)
    print(f'Created {out} ({out.stat().st_size:,} bytes)')


if __name__=='__main__':
    main()
