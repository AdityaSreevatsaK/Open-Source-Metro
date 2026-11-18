"""Self-service selection and export smoke tests. No live API or profile writes."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

from open_source_metro.profile_cli import export_profile, select_repositories
from open_source_metro.validation import normalise

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/demo-activity.json"


def fixture():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class ProfileExportTests(unittest.TestCase):
    def test_both_layouts_export_valid_static_svg_without_live_api(self):
        original = fixture()
        with TemporaryDirectory() as tmp:
            files = export_profile(original, Path(tmp), layout="both")
            names = {p.name for p in files}
            self.assertEqual(names, {"profile-compact.svg", "profile-mobile.svg",
                                     "source-snapshot.json", "README_SNIPPET.md"})
            for filename in ("profile-compact.svg", "profile-mobile.svg"):
                root = ET.parse(Path(tmp) / filename).getroot()
                self.assertTrue(root.tag.endswith("svg"))
            self.assertIn("Synthetic demonstration data", (Path(tmp)/"README_SNIPPET.md").read_text())
            self.assertEqual(len(normalise(json.loads((Path(tmp)/"source-snapshot.json").read_text()))["events"]),10)

    def test_featured_selection_keeps_only_requested_real_repositories(self):
        raw = fixture()
        repo = raw["repositories"][0]["full_name"]
        before = copy.deepcopy(raw)
        selection = select_repositories(raw,[repo])
        self.assertEqual([r["full_name"] for r in selection["repositories"]],[repo])
        self.assertTrue(all(e["repo_full_name"] == repo for e in selection["activity"]))
        self.assertEqual(raw,before) # no in-place modification
        self.assertEqual(selection["_selection"]["omitted_repositories"],4)

    def test_rejects_unknown_duplicate_or_empty_featured_selection(self):
        raw=fixture()
        valid=raw["repositories"][0]["full_name"]
        for entries in ([],[valid,valid],["other/not-in-fixture"],["../bad"],[valid]*6):
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    select_repositories(raw,entries)

    def test_unchanged_source_if_no_featured_restriction(self):
        raw=fixture()
        self.assertIs(select_repositories(raw,None),raw)

    def test_real_source_is_never_augmented_with_demo_events(self):
        raw=fixture();raw["source"]="github"
        with TemporaryDirectory() as tmp:
            paths=export_profile(raw,Path(tmp),theme="paper",layout="mobile")
            self.assertEqual(len(paths),3)
            content=(Path(tmp)/"profile-mobile.svg").read_text()
            self.assertIn("PUBLIC EVENTS",content)
            self.assertNotIn("SYNTHETIC DESIGN SHOWCASE",content)
            self.assertIn("Partial public repository-history snapshot",
                          (Path(tmp)/"README_SNIPPET.md").read_text())

    def test_stable_export_bytes(self):
        raw=fixture()
        with TemporaryDirectory() as first,TemporaryDirectory() as second:
            export_profile(raw,Path(first))
            export_profile(raw,Path(second))
            for name in ("profile-compact.svg","profile-mobile.svg","source-snapshot.json","README_SNIPPET.md"):
                self.assertEqual((Path(first)/name).read_bytes(),(Path(second)/name).read_bytes())

    def test_invalid_layout_and_theme(self):
        raw=fixture()
        with TemporaryDirectory() as out:
            with self.assertRaises(ValueError):
                export_profile(raw,Path(out),layout="animated-snake")
            with self.assertRaises(ValueError):
                export_profile(raw,Path(out),theme="rainbow")

    def test_export_preserves_coverage_and_selection_manifest(self):
        raw=fixture()
        raw["source"]="github"
        raw["_coverage"]={"complete_contribution_history":False,"source":"unit-test"}
        repo=raw["repositories"][0]["full_name"]
        with TemporaryDirectory() as tmp:
            export_profile(raw,Path(tmp),featured=[repo],layout="compact")
            exported=json.loads((Path(tmp)/"source-snapshot.json").read_text())
            self.assertFalse(exported["_coverage"]["complete_contribution_history"])
            self.assertEqual(exported["_selection"]["featured_repositories"],[repo])
            self.assertEqual(len(exported["repositories"]),1)

if __name__=="__main__":
    unittest.main()
