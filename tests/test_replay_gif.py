"""Minimal, dependency-free assertions for optional chronological GIF generator."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
SCRIPT=ROOT/'tools/render_replay_gif.py'
spec=importlib.util.spec_from_file_location('_metro_optional_gif',SCRIPT)
assert spec and spec.loader
gif=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gif)


class ReplayGifTests(unittest.TestCase):
    def test_frame_weeks_include_first_and_last(self):
        for count in (5,10,24,53):
            with self.subTest(count=count):
                weeks=gif.frame_weeks(count)
                self.assertEqual((weeks[0],weeks[-1]),(0,52))
                self.assertEqual(weeks,sorted(set(weeks)))
                self.assertLessEqual(len(weeks),53)

    def test_frame_count_out_of_bounds(self):
        for count in (0,4,54,200):
            with self.assertRaises(ValueError):gif.frame_weeks(count)

    def test_checked_in_gif_signature_and_size(self):
        path=ROOT/'assets/living-network-replay.gif'
        data=path.read_bytes()
        self.assertTrue(data.startswith(b'GIF89a'),data[:8])
        self.assertLess(len(data),2_000_000)


if __name__=='__main__':unittest.main()
