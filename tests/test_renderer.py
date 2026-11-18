"""Original Open Source Metro Atlas offline data, structure and provenance checks."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from open_source_metro.renderer import COLORS, SERVICE, expand_showcase, generate, metro_track, render

FIXTURE=ROOT/'examples'/'demo-activity.json'

def raw():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))

class AtlasTests(unittest.TestCase):
    def test_both_art_directions_are_valid_accessible_svg(self):
        data=expand_showcase(raw())
        for theme in COLORS:
            with self.subTest(theme=theme):
                svg=render(data,theme)
                root=ET.fromstring(svg)
                self.assertTrue(root.tag.endswith('svg'))
                self.assertTrue(root.find('{http://www.w3.org/2000/svg}title') is not None)
                self.assertTrue(root.find('{http://www.w3.org/2000/svg}desc') is not None)
                self.assertIn('SYNTHETIC DENSITY SHOWCASE',svg)
                self.assertIn('NOT A COMPLETE GITHUB CONTRIBUTION HISTORY',svg)
                self.assertEqual(svg.count('class="terminal"'),5)

    def test_raw_fixture_is_not_augmented_without_showcase(self):
        original=raw();svg=render(original)
        self.assertIn('10 EVENTS',svg)
        self.assertNotIn('illustrative-',svg)
        self.assertIn('SHARED SYNTHETIC FIXTURE',svg)

    def test_demo_expansion_is_deterministic_and_does_not_mutate_input(self):
        input_data=raw();before=copy.deepcopy(input_data)
        first=expand_showcase(input_data);second=expand_showcase(input_data)
        self.assertEqual(input_data,before)
        self.assertEqual(first,second)
        self.assertGreater(first['_illustrative_count'],100)
        self.assertTrue(all(ev['id'].startswith('illustrative-') for ev in first['activity'][10:]))
        self.assertEqual(first['activity'][:10],input_data['activity'])
        self.assertEqual(render(first),render(second))

    def test_showcase_requires_synthetic_source(self):
        source=raw();source['source']='github'
        with self.assertRaises(ValueError):expand_showcase(source)

    def test_public_snapshot_never_masquerades_as_a_synthetic_fixture(self):
        data=raw();data["source"]="github"
        svg=render(data)
        self.assertIn("PUBLIC EVENT SNAPSHOT",svg)
        self.assertIn("incomplete GitHub coverage",svg)
        self.assertNotIn("SHARED SYNTHETIC FIXTURE",svg)

    def test_unfeatured_repositories_are_disclosed_not_silently_mapped(self):
        data=raw()
        data["repositories"].append({"full_name":"sample-dev/sixth","name":"sixth"})
        data["activity"].append({"id":"sixth-event","kind":"commit",
            "repo_full_name":"sample-dev/sixth","occurred_at":"2026-10-08T12:00:00Z","count":3})
        svg=render(data)
        self.assertIn("ONLY 5 OF 6 REPOSITORIES SHOWN",svg)
        self.assertNotIn("sixth-event",svg)
        self.assertEqual(svg.count('class="terminal"'),5)

    def test_five_routes_and_calendar_tiles_are_present(self):
        svg=render(expand_showcase(raw()))
        root=ET.fromstring(svg)
        for kind,code,_ in SERVICE:
            self.assertIn('route-'+kind,svg)
            self.assertIn(code,svg)
        self.assertIn('class="tile-cell f0"',svg)
        self.assertIn('data-units=',svg)
        self.assertIn('CALENDAR DENSITY',svg)
        self.assertGreater(len([e for e in root.iter() if e.get('class','').startswith('tile-cell')]),150)

    def test_escaped_event_identifiers_do_not_inject_markup(self):
        data=raw();data['activity'][0]['id']='<img src=x onerror=alert(1)>'
        svg=render(data)
        ET.fromstring(svg)
        self.assertNotIn('<img src=x',svg)
        self.assertIn('&lt;img',svg)

    def test_empty_and_single_repository_are_supported(self):
        data=raw();data['repositories']=[];data['activity']=[]
        ET.fromstring(render(data));ET.fromstring(render(expand_showcase(data)))
        data=raw();data['repositories']=data['repositories'][:1]
        data['activity']=[x for x in data['activity'] if x['repo_full_name']==data['repositories'][0]['full_name']]
        ET.fromstring(render(data))

    def test_metro_tracks_are_straight_and_use_five_separate_gutters(self):
        svg=render(expand_showcase(raw()))
        root=ET.fromstring(svg)
        tracks=[e for e in root.iter() if e.get('class')=='service-track']
        self.assertEqual(len(tracks),5)
        y_positions=[]
        for path in tracks:
            route=path.attrib['d']
            self.assertRegex(route,r'^M\d+\.\d+ \d+\.\d+ H\d+\.\d+$')
            self.assertNotIn(' L',route)
            self.assertNotIn(' V',route)
            y_positions.append(float(route.split()[1]))
        self.assertEqual(y_positions,sorted(y_positions))
        self.assertEqual([round(y_positions[i+1]-y_positions[i]) for i in range(4)],[21]*4)

    def test_each_weekly_stop_has_observed_events_and_no_synthetic_dates(self):
        raw_data=raw()
        snap=expand_showcase(raw_data)
        svg=ET.fromstring(render(snap))
        stops=[e for e in svg.iter() if e.get('class')=='service-stop']
        from open_source_metro.validation import normalise
        normalized=normalise(snap)
        end=normalized['generated'].date()
        from datetime import timedelta
        start=end-timedelta(days=(end.weekday()+1)%7)-timedelta(weeks=52)
        dates_by_kind={}
        for event in normalized['events']:
            week=(event['date'].date()-start).days//7
            if week>=0 and event['date'].date()<=end:
                dates_by_kind.setdefault((event['kind'],week),0)
                dates_by_kind[(event['kind'],week)]+=1
        self.assertEqual(len(stops),len(dates_by_kind))
        for stop in stops:
            key=stop.get('data-kind'),int(stop.get('data-week'))
            self.assertIn(key,dates_by_kind)
            self.assertEqual(int(stop.get('data-events')), dates_by_kind[key])

    def test_dated_cells_keep_daily_source_type_ticks(self):
        normalized=raw()
        svg=ET.fromstring(render(normalized))
        dots=[e for e in svg.iter() if e.get('class')=='day-service']
        self.assertEqual(len(dots),10)
        self.assertEqual({e.get('data-kind') for e in dots}, {row['kind'] for row in normalized['activity']})

    def test_event_limit_excludes_entire_boundary_day(self):
        data=raw()
        data['activity']=[{'id':f'event-{i:03d}', 'repo_full_name':'sample-dev/aurora',
                           'kind':'commit', 'count':1,
                           'occurred_at':f'2026-10-{1 if i<120 else 2:02d}T{i//60:02d}:{i%60:02d}:00Z'}
                          for i in range(270)]
        svg=render(data)
        self.assertIn('150 EVENTS',svg)
        self.assertIn('120 SOURCE EVENTS NOT SHOWN',svg)
        self.assertNotIn('data-date="2026-10-01"',svg)

    def test_exports_match_local_renderer(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            result=generate(FIXTURE,out)
            self.assertEqual(len(result),3)
            for path in result:
                self.assertEqual(path.read_text(encoding='utf-8'),(ROOT/'assets'/path.name).read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
