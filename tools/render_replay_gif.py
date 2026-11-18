"""Optional GIF exporter for the source-backed Living Network storyboard.

Requires Pillow and CairoSVG *only* for this optional asset build. Never part
of the core renderer or CI test dependency. Reuses the exact SVG engine.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

# Works from a fresh editable project install or a source checkout.
try:
    from open_source_metro.living_network import (DX,CAL_X,CELL,
      demo_story,render_svg)
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from open_source_metro.living_network import (DX,CAL_X,CELL,
      demo_story,render_svg)


def frame_weeks(count: int) -> list[int]:
    if not 5 <= count <= 53:
        raise ValueError('Frame count must be between 5 and 53')
    return sorted({round(i*52/(count-1)) for i in range(count)} | {52})


def make_frame(source_svg: str, week: int, *, width: int):
    try:
        import cairosvg
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError('Optional animation requires Pillow and CairoSVG; pip install -e ".[animation]"') from exc
    root=ET.fromstring(source_svg)
    for el in root.iter():
        k=el.attrib.get('data-week')
        if k is not None:
            el.set('opacity','0.04' if int(k)>week else '1')
        if el.attrib.get('id')=='route-reveal-width':
            el.set('width',str(15+week*DX))
        if el.attrib.get('id')=='scan-cursor':
            x=CAL_X+week*DX+CELL/2
            el.set('x1',str(x));el.set('x2',str(x))
            el.set('opacity','0.9')
    svg_bytes=ET.tostring(root,encoding='utf-8',xml_declaration=False)
    png=cairosvg.svg2png(bytestring=svg_bytes,output_width=width)
    return Image.open(BytesIO(png)).convert('RGB')


def render_gif(raw: dict, target: Path, *, showcase: bool=False,
               theme: str='midnight', frames: int=28, width: int=950,
               duration_ms: int=135) -> Path:
    if not 600 <= width <= 1500:
        raise ValueError('Width must be between 600 and 1500 pixels')
    if not 60 <= duration_ms <= 2000:
        raise ValueError('Frame duration must be 60-2000 ms')
    weeklist=frame_weeks(frames)
    if showcase:
        raw=demo_story(raw)  # raises for real-source snapshots
    original=render_svg(raw,theme=theme)
    images=[make_frame(original,week,width=width) for week in weeklist]
    # Shared palette avoids colour flicker as stations are progressively revealed.
    from PIL import Image
    base=images[-1].quantize(colors=96,method=Image.Quantize.FASTOCTREE)
    prepared=[im.quantize(palette=base,dither=Image.Dither.NONE) for im in images]
    # End-state hold permits viewers to inspect actual stations/milestones.
    durations=[duration_ms]*len(prepared)
    durations[-1]=max(duration_ms,1400)
    target.parent.mkdir(parents=True,exist_ok=True)
    prepared[0].save(target,format='GIF',save_all=True,
                     append_images=prepared[1:],duration=durations,
                     loop=0,disposal=2,optimize=True)
    return target


def main() -> None:
    parser=argparse.ArgumentParser(description='Build an optional chronological Metro GIF preview')
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--showcase',action='store_true',help='Only for explicit demo-source illustration')
    parser.add_argument('--theme',choices=('midnight','paper'),default='midnight')
    parser.add_argument('--frames',type=int,default=28)
    parser.add_argument('--width',type=int,default=950)
    parser.add_argument('--duration-ms',type=int,default=135)
    args=parser.parse_args()
    out=render_gif(json.loads(args.input.read_text(encoding='utf-8')),
        args.output,showcase=args.showcase,theme=args.theme,
        frames=args.frames,width=args.width,duration_ms=args.duration_ms)
    print(f'Created {out} ({out.stat().st_size:,} bytes)')


if __name__=='__main__':main()
