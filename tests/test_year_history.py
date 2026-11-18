"""Mock-only year-scale public repository history and provenance checks."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from open_source_metro.year_history import PublicGitHub, collect_year, repository_valid
from open_source_metro.validation import normalise

AT = datetime(2026, 11, 18, 10, tzinfo=timezone.utc)
DATE = "2026-10-03T11:00:00Z"
OLD = "2025-08-04T11:00:00Z"


class Response:
    def __init__(self, data):
        self.body = BytesIO(json.dumps(data).encode("utf-8"))
    def read(self, n=-1):
        return self.body.read(n)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


def commit(sha="a"*40, date=DATE, author="demo-dev"):
    return {"sha": sha, "html_url": "https://github.com/demo-dev/aurora/commit/" + sha,
            "author": {"login": author}, "commit": {"author": {"date": date}}}


def pull(number=3, author="demo-dev", merged_at=DATE, created=DATE):
    return {"number": number, "user": {"login": author},
            "created_at": created, "merged_at": merged_at,
            "html_url": f"https://github.com/demo-dev/aurora/pull/{number}"}


def issue(number=2, author="demo-dev"):
    return {"number": number, "user": {"login": author},
            "created_at": DATE, "html_url": f"https://github.com/demo-dev/aurora/issues/{number}"}


def release(number=7, author="demo-dev"):
    return {"id": number, "author": {"login": author},
            "published_at": DATE, "html_url": f"https://github.com/demo-dev/aurora/releases/tag/v{number}"}


class FakeAPI:
    """Mock URI router that exercises real request construction and sanitising."""
    def __init__(self, overrides=None):
        self.urls = []
        self.headers = []
        self.overrides = overrides or {}

    def __call__(self, request, timeout=12):
        self.urls.append(request.full_url)
        self.headers.append(dict(request.header_items()))
        url = urlsplit(request.full_url)
        path, q = url.path, parse_qs(url.query)
        if path in self.overrides:
            output = self.overrides[path]
        elif path == "/users/demo-dev/repos":
            output = [
                {"full_name": "demo-dev/aurora", "private": False, "fork": False,
                 "owner": {"login": "demo-dev"}},
                {"full_name": "demo-dev/forked", "private": False, "fork": True,
                 "owner": {"login": "demo-dev"}},
                {"full_name": "demo-dev/private", "private": True, "fork": False,
                 "owner": {"login": "demo-dev"}},
                {"full_name": "elsewhere/other", "private": False, "fork": False,
                 "owner": {"login": "elsewhere"}},
            ]
        elif path in ("/repos/demo-dev/aurora", "/repos/elsewhere/project"):
            output = {"full_name": path.removeprefix("/repos/"), "private": False}
        elif path.endswith("/commits"):
            output = [commit(), commit(sha="b"*40, date=OLD)]
        elif path.endswith("/pulls"):
            output = [pull(), pull(number=17, author="elsewhere")]
        elif path.endswith("/issues"):
            output = [issue(), dict(issue(number=77), pull_request={"url":"https://github.com/demo-dev/aurora/pull/77"})]
        elif path.endswith("/releases"):
            output = [release()]
        else:
            raise AssertionError("Unexpected API request: " + request.full_url)
        return Response(output)


class YearHistoryTests(unittest.TestCase):
    def test_validated_repo_names_never_allow_url_injection(self):
        self.assertTrue(repository_valid("demo-dev/aurora"))
        for name in ("demo-dev", "demo-dev/a/b", "../evil", "x/a?token=abc",
                     "x/%2e", "x/a b", "x/a#x", "x/"):
            self.assertFalse(repository_valid(name))

    def test_owned_public_excludes_private_forks_and_other_owners(self):
        transport = FakeAPI()
        snapshot = collect_year("demo-dev", generated_at=AT,
                                client=PublicGitHub(opener=transport))
        self.assertEqual([r["full_name"] for r in snapshot["repositories"]], ["demo-dev/aurora"])
        self.assertEqual(len(snapshot["activity"]), 5)
        self.assertEqual({x["kind"] for x in snapshot["activity"]},
                         {"commit", "pr_opened", "pr_merged", "issue_opened", "release"})
        self.assertEqual(len(normalise(snapshot)["events"]), 5)
        self.assertFalse(snapshot["_coverage"]["complete_contribution_history"])
        self.assertEqual(snapshot["_coverage"]["days_requested"], 365)

    def test_endpoint_requests_are_bounded_pagination_and_fixed_host(self):
        fake = FakeAPI()
        client = PublicGitHub(opener=fake, token="test-private-token")
        snapshot = collect_year("demo-dev", generated_at=AT, client=client)
        self.assertEqual(snapshot["_coverage"]["requests"], 5)
        self.assertEqual(len(fake.urls), 5)
        self.assertTrue(all(url.startswith("https://api.github.com/") for url in fake.urls))
        self.assertTrue(any("author=demo-dev" in url for url in fake.urls))
        self.assertTrue(all("test-private-token" not in url for url in fake.urls))
        self.assertTrue(all("per_page=100" in url and "page=1" in url for url in fake.urls))
        self.assertIn("Authorization",str(fake.headers))

    def test_explicit_contributed_to_repository_is_supported(self):
        fake = FakeAPI()
        snapshot = collect_year("demo-dev", repos=["elsewhere/project"], generated_at=AT,
                                client=PublicGitHub(opener=fake))
        self.assertEqual(snapshot["_coverage"]["selection"], "explicit")
        self.assertEqual(snapshot["repositories"][0]["full_name"], "elsewhere/project")
        self.assertTrue(any("/repos/elsewhere/project" in u for u in fake.urls))

    def test_authored_pr_merges_and_created_issue_only(self):
        fake = FakeAPI()
        snapshot = collect_year("demo-dev", generated_at=AT,
                                client=PublicGitHub(opener=fake))
        ids = [e["id"] for e in snapshot["activity"]]
        self.assertTrue(any(x.endswith(":opened") for x in ids))
        self.assertTrue(any(x.endswith(":merged") for x in ids))
        self.assertFalse(any("77" in x for x in ids)) # issue API PR is not an issue
        self.assertFalse(any("17" in x for x in ids)) # other author's PR

    def test_page_cap_is_reported_not_silently_treated_as_complete(self):
        fake = FakeAPI(overrides={"/repos/demo-dev/aurora/commits":[commit(sha=f"{i:040x}") for i in range(100)]})
        snapshot = collect_year("demo-dev", generated_at=AT, pages=1,
                                client=PublicGitHub(opener=fake))
        self.assertTrue(snapshot["_coverage"]["possible_history_truncation"])
        self.assertIn("commits",snapshot["_coverage"]["per_repository"]["demo-dev/aurora"]["possibly_truncated"])

    def test_empty_or_invalid_repositories_are_not_fetched(self):
        fake = FakeAPI(overrides={"/users/demo-dev/repos":[]})
        snapshot = collect_year("demo-dev", generated_at=AT,
                                client=PublicGitHub(opener=fake))
        self.assertEqual(snapshot["repositories"], [])
        self.assertEqual(snapshot["activity"], [])
        with self.assertRaises(ValueError):
            collect_year("demo-dev", repos=["../etc/passwd"], generated_at=AT, client=PublicGitHub(opener=fake))
        with self.assertRaises(ValueError):
            collect_year("demo-dev", days=999, generated_at=AT, client=PublicGitHub(opener=fake))

    def test_selected_private_repo_fails_closed(self):
        fake = FakeAPI(overrides={"/repos/demo-dev/secret":{"full_name":"demo-dev/secret","private":True}})
        with self.assertRaisesRegex(ValueError,"public"):
            collect_year("demo-dev", repos=["demo-dev/secret"], generated_at=AT,
                         client=PublicGitHub(opener=fake))

    def test_unsafe_location_and_response_are_rejected(self):
        fake=FakeAPI()
        api=PublicGitHub(opener=fake)
        for path in ("https://evil.example", "/users/../secrets", "/a?x=y", "/a#frag"):
            with self.assertRaises(ValueError):
                api.get(path)
        bad=FakeAPI(overrides={"/users/demo-dev/repos":{"not":"a list"}})
        with self.assertRaisesRegex(ValueError,"JSON list"):
            collect_year("demo-dev",generated_at=AT,client=PublicGitHub(opener=bad))

    def test_rate_limit_is_error_not_zero_contributions(self):
        def blocked(request,timeout=12):
            raise HTTPError(request.full_url, 403, "rate limit", {}, None)
        with self.assertRaisesRegex(RuntimeError,"rate limit"):
            collect_year("demo-dev",generated_at=AT,client=PublicGitHub(opener=blocked))

    def test_invalid_utc_generation_and_config(self):
        with self.assertRaisesRegex(ValueError,"UTC"):
            collect_year("demo-dev",generated_at=datetime(2026,11,18))
        for cfg in ({"pages":0},{"max_repos":0},{"days":1}):
            with self.subTest(cfg=cfg):
                with self.assertRaises(ValueError):
                    collect_year("demo-dev",generated_at=AT,**cfg)

    def test_duplicate_repo_selections_are_idempotent(self):
        fake=FakeAPI()
        snapshot=collect_year("demo-dev",repos=["demo-dev/aurora","DEMO-DEV/AURORA"],
                              generated_at=AT,client=PublicGitHub(opener=fake))
        self.assertEqual(len(snapshot["repositories"]),1)
        self.assertEqual(len(snapshot["activity"]),5)


if __name__=="__main__":
    unittest.main()
