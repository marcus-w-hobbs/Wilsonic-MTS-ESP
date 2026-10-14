"""Tests for brun3.py, pinned to the iOS Brun3.h example (2/1, 3/2, 5/4).
Run from experiments/lattice/:  python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brun3  # noqa: E402

O, G0, G1 = 1.0, math.log2(1.5), math.log2(1.25)


def _cents_set(steps, mode=0):
    return sorted(round(c, 3) for c in brun3.scale_cents(steps, O, G0, G1, mode))


class TestExample(unittest.TestCase):
    def test_ab_level_sizes(self):
        lv = brun3.brun3_levels(O, G0, G1, "AB")
        self.assertEqual([len(l) for l in lv], [1, 2, 3, 5, 7, 10, 15, 22])

    def test_ac_level_sizes(self):
        lv = brun3.brun3_levels(O, G0, G1, "AC")
        self.assertEqual([len(l) for l in lv], [1, 2, 3, 4, 6, 7, 9, 10])

    def test_ab_level3_is_the_just_pentatonic(self):
        lv = brun3.brun3_levels(O, G0, G1, "AB")
        want = sorted(round(1200 * math.log2(r), 3) for r in (1, 5 / 4, 4 / 3, 3 / 2, 15 / 8))
        self.assertEqual(_cents_set(lv[3]), want)

    def test_ac_level5_is_the_just_heptatonic(self):
        lv = brun3.brun3_levels(O, G0, G1, "AC")
        want = sorted(round(1200 * math.log2(r), 3) for r in (1, 16 / 15, 5 / 4, 4 / 3, 3 / 2, 8 / 5, 15 / 8))
        self.assertEqual(_cents_set(lv[5]), want)

    def test_steps_sum_to_octave_and_three_sizes(self):
        for calc in brun3.CALCS:
            for L, steps in enumerate(brun3.brun3_levels(O, G0, G1, calc)):
                total = sum(brun3._value(s, O, G0, G1) for s in steps)
                self.assertAlmostEqual(total, O, places=12, msg=f"{calc} L{L}")
                self.assertLessEqual(len(brun3.step_sizes(steps, O, G0, G1)), 3)

    def test_degrees_are_integer_combinations(self):
        lv = brun3.brun3_levels(O, G0, G1, "AB")
        cos = brun3.degrees(lv[7])
        self.assertEqual(len(cos), 22)
        self.assertEqual(cos[0], (0, 0, 0))
        self.assertIn((0, 1, 0), cos)   # the fifth itself
        self.assertIn((0, 0, 1), cos)   # the third itself

    def test_mode_rotation(self):
        lv = brun3.brun3_levels(O, G0, G1, "AB")
        base = brun3.scale_cents(lv[4], O, G0, G1, 0)
        rot = brun3.scale_cents(lv[4], O, G0, G1, 2)
        self.assertEqual(rot[2], 0.0)
        self.assertEqual(sorted(round(x, 6) for x in rot),
                         sorted(round((x - base[2]) % 1200, 6) for x in base))

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            brun3.brun3_levels(1.0, 0.3, 0.5)
        with self.assertRaises(ValueError):
            brun3.brun3_levels(1.0, 0.5, 0.3, "XY")


if __name__ == "__main__":
    unittest.main()
