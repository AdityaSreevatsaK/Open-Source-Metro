"""Replay trains may only occupy source-backed, observed repository weeks."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from open_source_metro.compact_profile import compact_plan,render_compact
from open_source_metro.living_network import demo_story

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('compact_gif',ROOT/'tools/render_compact_gif.py')
assert SPEC and SPEC.loader
gif=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gif)


def fixture():
    return json.loads((ROOT/'examples/demo-activity.json').read_text(encoding='utf-8'))


class CompactGifTests(unittest.TestCase):
    def test_sampling_covers_start_and_end(self):
        for n in (8,14,26,53):
            weeks=gif.frame_weeks(n)
            self.assertEqual((weeks[0],weeks[-1]),(0,52))
            self.assertEqual(len(weeks),n)
        with self.assertRaises(ValueError):
            gif.frame_weeks(7)

    def test_no_vehicle_appears_at_an_unobserved_stop(self):
        raw=demo_story(fixture());plan=compact_plan(raw)
        svg=render_compact(raw)
        for week in (0,10,25,52):
            root=ET.fromstring(gif.frame_svg(svg,plan,week))
            trains=[n for n in root.iter() if n.get('class')=='replay-train']
            for train in trains:
                repo=train.get('data-repo');at=int(train.get('data-stop-week'))
                self.assertLessEqual(at,week)
                self.assertIn((repo,at),plan['by_week_repo'])
            self.assertEqual(len(trains),sum(any(s['week']<=week for s in r['stations'])
                                            for r in plan['routes']))

    def test_future_activity_is_dimmed_and_frame_reveal_is_exact(self):
        raw=demo_story(fixture());plan=compact_plan(raw)
        root=ET.fromstring(gif.frame_svg(render_compact(raw),plan,12))
        later=[n for n in root.iter() if n.get('class')=='calendar-day' and int(n.get('data-week'))>12]
        self.assertTrue(later)
        self.assertTrue(all(n.get('opacity')=='0.12' for n in later))
        reveal=next(n for n in root.iter() if n.get('id')=='compact-reveal-width')
        self.assertAlmostEqual(float(reveal.get('width')),14+12*gif.XSTEP)

    def test_end_frame_has_readable_completion_and_no_cursor(self):
        raw=demo_story(fixture());plan=compact_plan(raw)
        root=ET.fromstring(gif.frame_svg(render_compact(raw),plan,52))
        self.assertIn('FULL NETWORK',''.join(root.itertext()))
        cursor=next(n for n in root.iter() if n.get('id')=='compact-cursor')
        self.assertEqual(cursor.get('opacity'),'0')

    def test_invalid_week_and_colour_rejected(self):
        svg=render_compact(fixture());plan=compact_plan(fixture())
        with self.assertRaises(ValueError):gif.frame_svg(svg,plan,-1)
        with self.assertRaises(ValueError):gif.frame_svg(svg,plan,52,theme='invalid')


if __name__=='__main__':
    unittest.main()
