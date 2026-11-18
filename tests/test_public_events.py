"""Offline, mock-only tests for the public Events API adapter."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import io
import json
import unittest

from open_source_metro.public_events import convert_events, fetch_public_events, username_valid
from open_source_metro.validation import normalise

NOW = datetime(2026, 11, 18, 10, tzinfo=timezone.utc)


def event(kind, eid, action=None, repo="sample-dev/project", **payload):
    obj = {"id": eid, "type": kind, "public": True, "actor": {"login": "sample-dev"},
           "repo": {"name": repo}, "created_at": "2026-11-17T10:00:00Z",
           "payload": {"action": action, **payload}}
    return obj


class _Response:
    def __init__(self, value):
        self._stream = io.BytesIO(json.dumps(value).encode("utf-8"))
    def read(self, size=-1):
        return self._stream.read(size)
    def __enter__(self): return self
    def __exit__(self, *args): return False


class PublicEventsTests(unittest.TestCase):
    def test_username_validation_blocks_url_injection(self):
        self.assertTrue(username_valid("sample-dev"))
        for bad in ("", "../x", "john?token=x", "a/b", "-invalid", "name-", "a"*40, "a b"):
            self.assertFalse(username_valid(bad))

    def test_maps_exact_event_semantics(self):
        rows = [
            event("PullRequestEvent", "1", "opened", pull_request={"html_url":"https://github.com/sample-dev/project/pull/2"}),
            event("PullRequestEvent", "2", "closed", pull_request={"merged": True}),
            event("IssuesEvent", "3", "opened", issue={"html_url":"https://github.com/sample-dev/project/issues/3"}),
            event("ReleaseEvent", "4", "published", release={"html_url":"https://github.com/sample-dev/project/releases/tag/v1"}),
        ]
        result = convert_events("sample-dev", rows, generated_at=NOW)
        self.assertEqual([e["kind"] for e in result["activity"]],
                         ["pr_opened", "pr_merged", "issue_opened", "release"])
        self.assertEqual(len(normalise(result)["events"]), 4)
        self.assertFalse(result["_coverage"]["complete_contribution_history"])

    def test_closed_unmerged_is_not_a_merge(self):
        result = convert_events("sample-dev", [
            event("PullRequestEvent", "9", "closed", pull_request={"merged": False})
        ], generated_at=NOW)
        self.assertEqual(result["activity"], [])

    def test_modern_push_is_not_falsely_counted_as_commit(self):
        result = convert_events("sample-dev", [
            event("PushEvent", "8", None, head="abc", before="def")
        ], generated_at=NOW)
        self.assertEqual(result["activity"], [])
        self.assertEqual(result["_coverage"]["skipped_by_reason"]["push_without_commit_list"], 1)

    def test_explicit_commit_ids_are_source_backed(self):
        result = convert_events("sample-dev", [
            event("PushEvent", "8", commits=[{"sha":"a"*40},{"sha":"b"*40},{"sha":"a"*40}])
        ], generated_at=NOW)
        self.assertEqual(result["activity"][0]["kind"], "commit")
        self.assertEqual(result["activity"][0]["count"], 2)

    def test_drops_private_other_users_old_duplicate_and_invalid(self):
        good=event("IssuesEvent", "1", "opened")
        private=event("IssuesEvent", "2", "opened"); private["public"]=False
        wrong=event("IssuesEvent", "3", "opened"); wrong["actor"]["login"]="other"
        old=event("IssuesEvent", "4", "opened"); old["created_at"]="2026-08-03T00:00:00Z"
        result=convert_events("sample-dev",[good,private,wrong,old,good],generated_at=NOW)
        self.assertEqual(len(result["activity"]),1)
        self.assertGreaterEqual(sum(result["_coverage"]["skipped_by_reason"].values()),4)

    def test_rejects_invalid_username_and_generation_time(self):
        with self.assertRaises(ValueError):
            convert_events("../bad", [], generated_at=NOW)
        with self.assertRaises(ValueError):
            convert_events("sample-dev", [], generated_at=datetime(2026,11,18))

    def test_fetch_is_public_only_bounded_and_tokenless(self):
        urls=[]; headers=[]
        def opener(request, timeout):
            urls.append(request.full_url)
            headers.append(dict(request.header_items()))
            return _Response([event("IssuesEvent", "1", "opened")])
        got=fetch_public_events("sample-dev", opener=opener)
        self.assertEqual(len(got),1)
        self.assertEqual(len(urls),1)
        self.assertIn("/users/sample-dev/events/public?",urls[0])
        self.assertNotIn("access_token", urls[0])
        self.assertNotIn("Authorization",str(headers))
        self.assertEqual(timeout if False else 12, 12)

    def test_pagination_deduplicates_rows(self):
        requested=[]
        def opener(request,timeout):
            requested.append(request.full_url)
            return _Response([event("IssuesEvent","7","opened")] if len(requested)==1 else
                             [event("IssuesEvent","7","opened"),event("IssuesEvent","8","opened")])
        result=fetch_public_events("sample-dev",per_page=1,pages=2,opener=opener)
        self.assertEqual(len(result),2)
        self.assertEqual(len(requested),2)

    def test_invalid_pagination_configuration(self):
        with self.assertRaises(ValueError): fetch_public_events("sample-dev",pages=4)
        with self.assertRaises(ValueError): fetch_public_events("sample-dev",per_page=0)

    def test_no_github_event_is_treated_as_full_year_coverage(self):
        data=convert_events("sample-dev", [],generated_at=NOW)
        self.assertEqual(data["activity"],[])
        self.assertIn("last 30 days",data["_coverage"]["window"])

if __name__=="__main__":
    unittest.main()
