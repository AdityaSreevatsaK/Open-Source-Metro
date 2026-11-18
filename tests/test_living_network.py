"""Living Network prototype: source-event grounding, accessibility and replay."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# Works before editable installation, and through regular CI discovery.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from open_source_metro.living_network import (W,H,ROUTE_COLOURS,build_plan,
    browser_html,demo_story,first_sunday,generate,render_svg)

FIXTURE=Path(__file__).resolve().parents[1] / 'examples/demo-activity.json'
SVGTAG='{http://www.w3.org/2000/svg}'


def raw():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


class LivingNetworkTests(unittest.TestCase):
    def test_original_sample_remains_exact_ten_events(self):
        p=build_plan(raw())
        self.assertEqual(len(p['events']), 10)
        self.assertEqual(p['omitted_events'],0)
        self.assertEqual(p['omitted_repos'],0)
        self.assertEqual(len(p['featured']),5)

    def test_all_dates_are_on_sunday_first_53_week_grid(self):
        p=build_plan(raw())
        self.assertEqual(p['start'].weekday(),6)
        self.assertEqual(len(p['positions']),371)
        self.assertEqual(p['positions'][p['start']],(0,0))
        self.assertEqual(p['positions'][p['start']+timedelta(days=370)],(52,6))
        self.assertEqual(p['today'].isoformat(),'2026-11-16')

    def test_demo_only_story_and_determinism(self):
        a=demo_story(raw());b=demo_story(raw())
        self.assertEqual(a,b)
        self.assertGreater(a['_synthetic_added'],70)
        self.assertEqual(len(a['activity']),10+a['_synthetic_added'])
        self.assertEqual(raw()['activity'][0]['id'],'demo-001')
        a['source']='github'
        with self.assertRaises(ValueError): demo_story(a)

    def test_observed_week_stations_provenance(self):
        doc=ET.fromstring(render_svg(raw()))
        stops=[el for el in doc.iter() if el.attrib.get('class')=='stop station']
        p=build_plan(raw())
        expected=sum(len({p['positions'][e['date'].date()][0] for e in p['events'] if e['repo']==r['full_name']}) for r in p['featured'])
        self.assertEqual(len(stops),expected)
        for e in p['events']:
            self.assertTrue(any(e['id'] in ''.join(s.itertext()) for s in stops))

    def test_rendered_repository_routes_are_source_backed(self):
        doc=ET.fromstring(render_svg(raw()))
        journeys=[el for el in doc.iter() if el.attrib.get('class')=='journey']
        self.assertEqual(len(journeys),len(build_plan(raw())['featured']))
        self.assertEqual(len({j.attrib['data-repo-index'] for j in journeys}),len(journeys))
        self.assertEqual(len([el for el in doc.iter() if el.attrib.get('class')=='passport-card']),3)

    def test_blank_days_not_labelled_zero_github_contributions(self):
        svg=render_svg(raw())
        self.assertIn('BLANK ≠ VERIFIED ZERO',svg)
        self.assertIn('not confirmed zero GitHub contributions',svg)
        self.assertNotIn('OFFICIAL GITHUB TOTALS',svg)

    def test_non_demo_render_never_claims_synthetic_additions(self):
        inp=raw();inp['source']='github'
        svg=render_svg(inp)
        self.assertIn('PUBLIC EVENT SNAPSHOT',svg)
        self.assertNotIn('DEMO ONLY',svg)
        self.assertIn('COVERAGE INCOMPLETE',svg)

    def test_passport_milestones_hide_until_their_observed_week(self):
        source=demo_story(raw())
        p=build_plan(source)
        doc=ET.fromstring(render_svg(source))
        milestones={e['id']:p['positions'][e['date'].date()][0] for e in p['events']
                    if e['kind'] in ('release','pr_merged')}
        cards=[el for el in doc.iter() if el.attrib.get('class')=='passport-card']
        self.assertEqual(len(cards),4)
        for card in cards:
            text=''.join(card.itertext())
            self.assertIn('data-week',card.attrib)
            self.assertIn(int(card.attrib['data-week']),range(53))
            self.assertTrue(any(source_id in text and week==int(card.attrib['data-week'])
                                for source_id,week in milestones.items()))

    def test_all_outputs_are_valid_accessible_svg(self):
        for theme in ('midnight','paper'):
            with self.subTest(theme=theme):
                doc=ET.fromstring(render_svg(demo_story(raw()),theme=theme))
                self.assertEqual(doc.tag,SVGTAG+'svg')
                self.assertEqual(doc.attrib['viewBox'],f'0 0 {W} {H}')
                self.assertIsNotNone(doc.find(SVGTAG+'title'))
                self.assertIsNotNone(doc.find(SVGTAG+'desc'))
                self.assertIsNotNone(next((x for x in doc.iter() if x.attrib.get('id')=='route-reveal-width'),None))

    def test_event_types_not_equated_with_commits(self):
        svg=render_svg(raw())
        self.assertIn('MERGES / RELEASES',svg)
        self.assertIn('03 / MILESTONE PASSPORT',svg)
        self.assertIn('PR MERGED',svg)
        self.assertIn('RELEASE',svg)

    def test_no_made_up_journey_for_empty_snapshot(self):
        data=raw();data['repositories']=[];data['activity']=[]
        doc=ET.fromstring(render_svg(data))
        self.assertFalse([el for el in doc.iter() if el.attrib.get('class')=='journey'])
        self.assertIn('No recorded merge or release milestones',render_svg(data))
        self.assertEqual(demo_story(data)['_synthetic_added'],0)

    def test_one_repo_and_same_day_events(self):
        data=raw();data['repositories']=data['repositories'][:1]
        data['activity']=[data['activity'][0],data['activity'][6]]
        data['activity'][1]['occurred_at']=data['activity'][0]['occurred_at']
        p=build_plan(data)
        self.assertEqual(len(p['featured']),1)
        doc=ET.fromstring(render_svg(data))
        self.assertEqual(len([x for x in doc.iter() if x.attrib.get('class')=='stop station']),1)

    def test_future_observations_never_marked_as_observed(self):
        data=raw();event=copy.deepcopy(data['activity'][0]);event['id']='impossible-future';event['occurred_at']='2026-11-16T12:00:00Z';data['activity'].append(event)
        p=build_plan(data)
        self.assertEqual(p['omitted_events'],1)
        self.assertNotIn('impossible-future',render_svg(data))

    def test_outside_window_and_oversized_repo_directory_disclosed(self):
        data=raw()
        data['repositories'].extend({'full_name':f'unknown/repo{i}', 'name':f'repo{i}'} for i in range(3))
        data['activity'].append({**data['activity'][0],'id':'ancient','occurred_at':'2020-01-01T00:00:00Z'})
        p=build_plan(data)
        self.assertEqual(len(p['featured']),5)
        self.assertEqual(p['omitted_repos'],3)
        self.assertEqual(p['omitted_events'],1)
        self.assertIn('OMITTED 3 REPOS / 1 EVENTS',render_svg(data))

    def test_event_cap_never_splits_a_day(self):
        data=raw()
        data['activity']=[{'id':f'e-{i}', 'kind':'commit','repo_full_name':'sample-dev/aurora','count':1,
            'occurred_at':f'2026-10-01T{i//60:02d}:{i%60:02d}:00Z'} for i in range(241)]
        p=build_plan(data)
        self.assertEqual(len(p['events']),0)
        self.assertEqual(p['omitted_events'],241)

    def test_interchanges_only_where_multiple_projects_share_a_week(self):
        p=build_plan(demo_story(raw()))
        doc=ET.fromstring(render_svg(demo_story(raw())))
        for item in [x for x in doc.iter() if x.attrib.get('class')=='interchange']:
            week=int(item.attrib['data-week'])
            self.assertGreaterEqual(len(p['coactive'][week]),2)
            self.assertIn('Same-week repository activity', ''.join(item.itertext()))

    def test_xml_and_js_escaped_untrusted_event_id(self):
        inp=raw();bad='</script><img src=x onerror=alert(1)>'
        inp['activity'][0]['id']=bad
        svg=render_svg(inp)
        self.assertIn('&lt;/script&gt;',svg)
        ET.fromstring(svg)
        html=browser_html(inp,svg)
        self.assertNotIn('"id":"</script>',html)
        self.assertIn(r'\u003c/script\u003e',html)

    def test_offline_html_contains_working_replay_hooks(self):
        inp=raw();html=browser_html(inp,render_svg(inp))
        for part in ('id="play"','id="week"','id="routes"','id="event-list"',
                     "requestAnimationFrame(frame)","getElementById('route-reveal-width')",
                     "<meta http-equiv=\"Content-Security-Policy\"",'No network requests'):
            self.assertIn(part,html)
        self.assertNotIn('https://cdn.',html)

    def test_generated_demo_assets_repeat_byte_for_byte(self):
        inp=raw()
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            p=generate(inp,Path(a),showcase=True)
            q=generate(inp,Path(b),showcase=True)
            self.assertEqual([x.read_bytes() for x in p],[x.read_bytes() for x in q])
            self.assertEqual(len(p),2)
            self.assertIn('SYNTHETIC STORY SHOWCASE',p[0].read_text(encoding='utf-8'))

    def test_two_themes_have_distinct_valid_colours(self):
        a=render_svg(raw(),theme='midnight');b=render_svg(raw(),theme='paper')
        self.assertNotEqual(a,b)
        self.assertIn('#59F0BD',a)
        self.assertIn('#168B69',b)
        with self.assertRaises(ValueError):render_svg(raw(),theme='illegitimate')


if __name__=='__main__':unittest.main()
