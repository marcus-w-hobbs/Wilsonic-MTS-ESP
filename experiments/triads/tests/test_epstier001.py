"""EPS-TIER-001 goldens: tier derivation, rank correlation, P = S rail."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import epstier001 as et  # noqa: E402
import scorer  # noqa: E402
from families.mos import mos_scales  # noqa: E402


class TestTiers(unittest.TestCase):
    def test_tiers_are_derived_from_12edo(self):
        self.assertEqual(et.tier_anchors(),
                         {"LOCK": 2.0, "ET5": 14.86, "ET7": 32.01})

    def test_12edo_major_and_minor_miss_their_means_equally(self):
        # 0-4-7 vs AM and 0-3-7 vs HM are inversions of each other
        a, x, b = (et._edo12(k) for k in (0, 3, 7))
        vs_hm = et._cents(x / (2 * a * b / (a + b)))
        self.assertAlmostEqual(abs(vs_hm), abs(et.middle_vs_am_cents(0, 4, 7)),
                               places=9)

    def test_5_6_7_as_12edo_diminished_triad(self):
        self.assertAlmostEqual(et.middle_vs_am_cents(4, 7, 10), -25.86,
                               places=2)


class TestSpearman(unittest.TestCase):
    def test_perfect_and_reversed(self):
        self.assertAlmostEqual(et.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1)
        self.assertAlmostEqual(et.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1)

    def test_ties_and_constant(self):
        self.assertAlmostEqual(et.spearman([1, 1, 2], [1, 1, 2]), 1)
        self.assertTrue(math.isnan(et.spearman([1, 1, 1], [1, 2, 3])))


class TestInversionRail(unittest.TestCase):
    def test_mos_p_equals_s_at_every_tier(self):
        tiers = et.tier_anchors()
        for g in (481.0, 491.0, 500.0, 701.955 - 200.0):
            for scale in mos_scales(g / 1200.0).values():
                for eps in tiers.values():
                    r = scorer.score_tempered(scale, eps)
                    self.assertEqual(r.proportional, r.subcontrary)


if __name__ == "__main__":
    unittest.main()
