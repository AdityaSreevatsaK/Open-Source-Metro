"""Regression checks for untrusted snapshot input and provenance rules."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from open_source_metro.validation import normalise, safe_url, safe_label
from open_source_metro.renderer import render, expand_showcase

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/demo-activity.json'


def fixture():
    return json.loads(EXAMPLE.read_text(encoding='utf-8'))


class ValidationTests(unittest.TestCase):
    def test_v1_snapshot_has_expected_counts(self):
        snapshot = normalise(fixture())
        self.assertEqual(snapshot['repo_total'], 5)
        self.assertEqual(snapshot['event_total'], 10)

    def test_unsafe_event_id_is_rejected(self):
        data = fixture()
        data['activity'][0]['id'] = '\x00'
        with self.assertRaisesRegex(ValueError, 'event ID'):
            normalise(data)

    def test_incorrect_event_type_rejected(self):
        data = fixture()
        data['activity'][0]['kind'] = 'fake_contribution'
        with self.assertRaisesRegex(ValueError, 'Unsupported event'):
            normalise(data)

    def test_conflicting_duplicate_event_id_is_rejected(self):
        data = fixture()
        altered = copy.deepcopy(data['activity'][0])
        altered['count'] = 99
        data['activity'].append(altered)
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            normalise(data)

    def test_identical_duplicate_event_id_is_deduplicated(self):
        data = fixture()
        data['activity'].append(copy.deepcopy(data['activity'][0]))
        self.assertEqual(normalise(data)['event_total'], 10)

    def test_unverified_url_is_silently_dropped(self):
        self.assertIsNone(safe_url('javascript:alert(1)'))
        self.assertIsNone(safe_url('https://github.com.evil.example/org/repo'))
        self.assertEqual(safe_url('https://github.com/openai/openai'), 'https://github.com/openai/openai')

    def test_bidirectional_override_and_xml_controls_are_rejected(self):
        for value in ('bad\u202etag', 'bad\x01tag', 'bad\ud800tag'):
            self.assertFalse(safe_label(value, 100))

    def test_only_demo_inputs_may_be_augmented(self):
        data = fixture()
        data['source'] = 'github'
        with self.assertRaisesRegex(ValueError, 'demo'):
            expand_showcase(data)

    def test_public_svg_explicitly_disclaims_completeness(self):
        data = fixture()
        data['source'] = 'github'
        result = render(data)
        self.assertIn('PUBLIC EVENT SNAPSHOT', result)
        self.assertIn('NOT A COMPLETE GITHUB CONTRIBUTION HISTORY', result)
        self.assertNotIn('SYNTHETIC DENSITY SHOWCASE', result)


if __name__ == '__main__':
    unittest.main()
