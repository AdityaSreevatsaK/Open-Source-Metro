"""GitHub GraphQL profile day counts and independent public-route provenance."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

from open_source_metro.contribution_calendar import (
    fetch_contribution_calendar, parse_calendar, normalise_calendar_for_snapshot
)
from open_source_metro.compact_profile import render_compact
from open_source_metro.mobile_profile import render_mobile
from open_source_metro.profile_cli import export_profile, select_repositories

FIXTURE = Path(__file__).resolve().parents[1]/"examples"/"demo-activity.json"
NOW = datetime(2026,11,16,0,0,tzinfo=timezone.utc)


def fixture():
    raw=json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["source"]="github"
    return raw


def graphql_result(username="sample-dev"):
    return {"data":{"user":{"login":username,"contributionsCollection":{
        "contributionCalendar":{"totalContributions":11,"weeks":[
            {"contributionDays":[
                {"date":"2026-08-15","contributionCount":8},
                {"date":"2026-10-08","contributionCount":3},
            ]}
        ]}}}}}


def calendar():
    obj=parse_calendar(graphql_result(),"sample-dev")
    obj["window_from"]="2025-11-16T00:00:00Z"
    obj["window_to"]="2026-11-16T00:00:00Z"
    return obj


class Response:
    def __init__(self, content):
        self.content=BytesIO(json.dumps(content).encode("utf-8"))
    def read(self,count=-1):return self.content.read(count)
    def __enter__(self):return self
    def __exit__(self,*args):return False


class OfficialCalendarTests(unittest.TestCase):
    def test_parses_source_backed_official_days(self):
        result=calendar()
        self.assertEqual(result["total_contributions"],11)
        self.assertEqual(len(result["days"]),2)
        self.assertEqual(result["provider"],"github-graphql")

    def test_fixed_host_authenticated_post_and_no_token_leak(self):
        requests=[]
        def transport(request,timeout):
            requests.append(request)
            return Response(graphql_result())
        result=fetch_contribution_calendar("sample-dev",generated_at=NOW,
                                           token="local-only-test-token",opener=transport)
        self.assertEqual(len(requests),1)
        self.assertEqual(requests[0].full_url,"https://api.github.com/graphql")
        self.assertEqual(requests[0].get_method(),"POST")
        self.assertIn("Authorization",str(dict(requests[0].header_items())))
        self.assertNotIn("local-only-test-token",json.dumps(result))
        self.assertEqual(result["total_contributions"],11)

    def test_invalid_or_conflicting_calendar_days_rejected(self):
        wrong=graphql_result("someone-else")
        with self.assertRaises(ValueError):
            parse_calendar(wrong,"sample-dev")
        bad=graphql_result()
        bad["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"][0]["contributionDays"].append(
            {"date":"2026-08-15","contributionCount":1})
        with self.assertRaises(ValueError):
            parse_calendar(bad,"sample-dev")
        bad2=graphql_result()
        bad2["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"][0]["contributionDays"][0]["contributionCount"]=True
        with self.assertRaises(ValueError):
            parse_calendar(bad2,"sample-dev")

    def test_no_token_fails_clearly(self):
        with self.assertRaises(RuntimeError):
            fetch_contribution_calendar("sample-dev",generated_at=NOW,token="")

    def test_calendar_cannot_be_attached_to_demo_or_wrong_user(self):
        sample=fixture()
        sample["_calendar"]=calendar()
        self.assertEqual(normalise_calendar_for_snapshot(sample, {} )[
            datetime(2026,8,15).date()],8)
        sample["source"]="demo"
        with self.assertRaises(ValueError):
            render_compact(sample)
        sample["source"]="github"
        sample["_calendar"]["username"]="another-user"
        with self.assertRaises(ValueError):
            render_mobile(sample)

    def test_rich_github_grid_does_not_fabricate_route_events(self):
        sample=fixture()
        sample["_calendar"]=calendar()
        desktop=ET.fromstring(render_compact(sample))
        squares=[n for n in desktop.iter() if n.get("class")=="calendar-day"]
        self.assertEqual(sum(int(x.get("data-count","0")) for x in squares),11)
        self.assertEqual(sum(int(x.get("data-source-count","0")) for x in squares),10)
        self.assertIn("GITHUB CALENDAR",render_compact(sample))
        self.assertIn("11 GitHub contributions",render_compact(sample))
        self.assertIn("01 / GITHUB PROFILE CONTRIBUTIONS",render_compact(sample))
        self.assertEqual(len(sample["activity"]),10)

    def test_profile_intensity_has_four_observation_based_levels(self):
        from open_source_metro.contribution_calendar import contribution_intensity
        samples = [1, 3, 5, 9, 15, 30, 60, 100]
        self.assertEqual(contribution_intensity(0, samples),0)
        self.assertEqual(contribution_intensity(1, samples),1)
        self.assertEqual(contribution_intensity(100, samples),4)
        self.assertLess(contribution_intensity(3, samples),
                        contribution_intensity(60, samples))

    def test_mobile_and_profile_pack_keep_calendar_independent(self):
        sample=fixture();sample["_calendar"]=calendar()
        mobile=ET.fromstring(render_mobile(sample))
        squares=[n for n in mobile.iter() if n.get("class")=="mobile-day"]
        self.assertEqual(sum(int(x.get("data-count","0")) for x in squares),11)
        self.assertIn("GITHUB PROFILE",render_mobile(sample))
        with TemporaryDirectory() as folder:
            export_profile(sample,Path(folder))
            note=(Path(folder)/"README_SNIPPET.md").read_text(encoding="utf-8")
            self.assertIn("GitHub profile calendar",note)
            self.assertIn("11 displayed GitHub contribution units",note)
            self.assertIn("public repository events",note.lower())

    def test_featured_repo_selection_does_not_reshape_official_calendar(self):
        sample=fixture();sample["_calendar"]=calendar()
        repo=sample["repositories"][0]["full_name"]
        selected=select_repositories(sample,[repo])
        self.assertEqual(selected["_calendar"],sample["_calendar"])
        self.assertEqual(sum(normalise_calendar_for_snapshot(selected,{}).values()),11)
        self.assertEqual(len(selected["repositories"]),1)

    def test_untrusted_calendar_rejects_non_numeric_and_duplicate_date(self):
        sample=fixture();sample["_calendar"]=calendar()
        sample["_calendar"]["days"].append({"date":"2026-08-15","count":10})
        with self.assertRaises(ValueError):render_compact(sample)
        sample["_calendar"]["days"]=calendar()["days"]
        sample["_calendar"]["username"]=88
        with self.assertRaises(ValueError):render_mobile(sample)


if __name__=="__main__":
    unittest.main()
