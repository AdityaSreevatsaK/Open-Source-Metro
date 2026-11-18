"""Portrait 16-week source-data and SVG validation."""
from __future__ import annotations
import copy
from datetime import date, timedelta
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from open_source_metro.mobile_profile import mobile_plan, render_mobile, WEEKS, WIDTH, HEIGHT
from open_source_metro.living_network import demo_story

DATA = Path(__file__).resolve().parents[1]/"examples"/"demo-activity.json"


def fixture():
    return json.loads(DATA.read_text(encoding="utf-8"))


class MobileProfileTests(unittest.TestCase):
    def test_portrait_size_and_16_week_scope(self):
        self.assertLess(WIDTH, HEIGHT)
        self.assertEqual(WEEKS, 16)
        plan = mobile_plan(fixture())
        self.assertEqual(plan["window_weeks"], 16)
        self.assertEqual((plan["today"]-plan["start"]).days//7, 15)

    def test_both_themes_generate_valid_svg(self):
        for theme in ("midnight","paper"):
            with self.subTest(theme=theme):
                root=ET.fromstring(render_mobile(fixture(),theme=theme))
                self.assertTrue(root.tag.endswith("svg"))
                self.assertEqual(root.attrib["width"], str(WIDTH))
                self.assertEqual(root.attrib["height"], str(HEIGHT))
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))

    def test_all_stations_have_actual_source_events(self):
        plan=mobile_plan(demo_story(fixture()))
        ids={e["id"] for e in plan["events"]}
        for route in plan["routes"]:
            for s in route["stations"]:
                self.assertTrue(s["ids"])
                self.assertTrue(set(s["ids"]).issubset(ids))
                self.assertGreaterEqual(s["week"],0)
                self.assertLess(s["week"],16)

    def test_no_extra_demo_events_when_not_requested(self):
        original=mobile_plan(fixture())
        self.assertLessEqual(len(original["events"]),10)
        self.assertNotIn("DESIGN SHOWCASE",render_mobile(fixture()))
        full=render_mobile(demo_story(fixture()))
        self.assertIn("SYNTHETIC DESIGN SHOWCASE",full)
        self.assertNotEqual(full,render_mobile(fixture()))

    def test_no_real_activity_fabrication(self):
        data=fixture();data["source"]="github"
        svg=render_mobile(data)
        self.assertIn("PUBLIC EVENTS",svg)
        self.assertIn("PUBLIC SOURCE MAY COVER ONLY 30 DAYS",svg)
        self.assertNotIn("SYNTHETIC DESIGN SHOWCASE",svg)
        with self.assertRaises(ValueError):
            render_mobile(demo_story(data))

    def test_invalid_text_escapes_rejected(self):
        data=fixture()
        data["repositories"][0]["name"]="<script>alert(1)</script>"
        svg=render_mobile(data)
        self.assertNotIn("<script>",svg)
        self.assertIn("&lt;script&gt;",svg)

    def test_empty_snapshot_is_explicit(self):
        data=fixture();data["repositories"]=[];data["activity"]=[]
        result=render_mobile(data)
        self.assertIn("0 EVENTS",result)
        self.assertEqual(mobile_plan(data)["routes"],[])

    def test_month_and_day_coordinates_are_not_future_dates(self):
        p=mobile_plan(fixture())
        svg=render_mobile(fixture())
        root=ET.fromstring(svg)
        cells=root.findall(".//{http://www.w3.org/2000/svg}rect[@class='mobile-day']")
        self.assertEqual(len(cells),(p["today"]-p["start"]).days+1)
        self.assertLessEqual(len(cells),112)

    def test_rejects_unrecognised_theme(self):
        with self.assertRaises(ValueError):
            render_mobile(fixture(),theme="hot-pink")

    def test_deterministic_output(self):
        sample=demo_story(fixture())
        self.assertEqual(render_mobile(sample),render_mobile(sample))

if __name__=="__main__":
    unittest.main()
