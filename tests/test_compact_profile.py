"""Compact profile calendar semantics, provenance, rendering and basic safety."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from open_source_metro.compact_profile import render_compact,compact_plan,WIDTH,HEIGHT
from open_source_metro.living_network import demo_story

ROOT=Path(__file__).resolve().parents[1]
SVG='{http://www.w3.org/2000/svg}'


def fixture():
    return json.loads((ROOT/'examples/demo-activity.json').read_text(encoding='utf-8'))


class CompactProfileTests(unittest.TestCase):
    def test_real_fixture_remains_ten_source_events(self):
        p=compact_plan(fixture())
        self.assertEqual(len(p['events']),10)
        self.assertEqual(len(p['routes']),5)

    def test_every_station_matches_an_observed_repo_week(self):
        raw=demo_story(fixture());plan=compact_plan(raw)
        root=ET.fromstring(render_compact(raw))
        stations=[x for x in root.iter() if x.get('class')=='compact-station']
        expected={(r['repo']['full_name'],s['week'],s['kind'])
                  for r in plan['routes'] for s in r['stations']}
        actual={(x.get('data-repo'),int(x.get('data-week')),x.get('data-kind')) for x in stations}
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual),len(stations))

    def test_53_week_alignment_and_source_dates(self):
        plan=compact_plan(fixture())
        root=ET.fromstring(render_compact(fixture()))
        days=[n for n in root.iter() if n.get('class')=='calendar-day']
        indexed={n.get('data-date'):n for n in days}
        self.assertEqual(plan['start'].weekday(),6)
        self.assertIn(plan['start'].isoformat(),indexed)
        self.assertIn(plan['today'].isoformat(),indexed)
        self.assertEqual(indexed['2026-11-13'].get('data-count'),'1')
        self.assertEqual(max(int(x.get('data-week')) for x in days),52)

    def test_release_and_merge_markers_are_source_backed(self):
        root=ET.fromstring(render_compact(fixture()))
        release=[n for n in root.iter() if n.get('class')=='compact-station' and n.get('data-kind')=='release']
        merged=[n for n in root.iter() if n.get('class')=='compact-station' and n.get('data-kind')=='pr_merged']
        self.assertEqual(len(release),1)
        self.assertEqual(len(merged),2)
        self.assertEqual(sum(n.get('class')=='calendar-milestone' for n in root.iter()),1)

    def test_two_themes_are_standalone_accessible_and_small(self):
        for theme in ('midnight','paper'):
            with self.subTest(theme=theme):
                svg=render_compact(demo_story(fixture()),theme=theme)
                root=ET.fromstring(svg)
                self.assertEqual(root.get('viewBox'),f'0 0 {WIDTH} {HEIGHT}')
                self.assertIsNotNone(root.find(SVG+'title'))
                self.assertIsNotNone(root.find(SVG+'desc'))
                self.assertNotIn('<script',svg)
                self.assertLess(len(svg.encode('utf-8')),220000)
                self.assertIn('SYNTHETIC DESIGN SHOWCASE',svg)

    def test_empty_and_single_repository(self):
        raw=fixture();raw['activity']=[];raw['repositories']=[]
        root=ET.fromstring(render_compact(raw))
        self.assertFalse([x for x in root.iter() if x.get('class')=='compact-journey'])
        raw=fixture();raw['repositories']=raw['repositories'][:1];raw['activity']=raw['activity'][:1]
        root=ET.fromstring(render_compact(raw))
        self.assertEqual(sum(x.get('class')=='compact-journey' for x in root.iter()),1)

    def test_no_fabrication_or_false_real_account_claim(self):
        inp=fixture()
        self.assertEqual(render_compact(demo_story(inp)),render_compact(demo_story(inp)))
        pub=copy.deepcopy(inp);pub['source']='github'
        with self.assertRaises(ValueError):demo_story(pub)
        self.assertIn('PUBLIC EVENTS',render_compact(pub))
        self.assertNotIn('SYNTHETIC DESIGN SHOWCASE',render_compact(pub))

    def test_real_snapshot_explains_observed_date_range_and_week_count(self):
        sample = fixture()
        sample['source'] = 'github'
        svg = render_compact(sample)
        self.assertIn('Observed ', svg)
        self.assertIn('/53 WEEKS', svg)
        self.assertIn('OUTSIDE YEAR', svg)
        self.assertIn('REPOS', svg)

    def test_real_dense_events_are_counted_without_240_cap(self):
        sample = fixture()
        sample['source'] = 'github'
        sample['activity'] = [
            dict(id=f'busy-{i}', kind='commit', repo_full_name='sample-dev/aurora',
                 occurred_at=f'2026-10-01T{i//60:02d}:{i%60:02d}:00Z', count=1)
            for i in range(502)]
        svg = render_compact(sample)
        self.assertIn('502 events', svg)
        self.assertIn('0 WEEKS' if False else 'OBSERVED', svg)
        self.assertIn('data-count="502"', svg)

    def test_untrusted_labels_escaped_and_invalid_values_rejected(self):
        raw=fixture();raw['activity'][0]['id']='<script>bad</script>'
        svg=render_compact(raw)
        ET.fromstring(svg)
        self.assertIn('&lt;script&gt;',svg)
        self.assertNotIn('<script>',svg)
        with self.assertRaises(ValueError):render_compact(raw,theme='nonexistent')
        raw['activity'][0]['count']=-1
        with self.assertRaises(ValueError):render_compact(raw)


if __name__=='__main__':
    unittest.main()
