"""Generator-family goldens: CPS and MOS (families/)."""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from families.cps import cps_products, cps_scale, hexany, odd_seed_sets  # noqa: E402
from families.mos import mos_cardinalities, mos_cents, zigzag  # noqa: E402


class TestCps(unittest.TestCase):
    def test_hexany_1357(self):
        self.assertEqual(
            hexany([1, 3, 5, 7]),
            (F(35, 32), F(5, 4), F(21, 16), F(3, 2), F(7, 4), F(15, 8)))

    def test_eikosany_is_20_tones(self):
        self.assertEqual(len(cps_scale((1, 3, 5, 7, 9, 11), 3)), 20)

    def test_products_multiset_kept(self):
        # seeds 1,3,5,15: pairwise products collide (15 = 1*15 = 3*5)
        self.assertEqual(len(cps_products((1, 3, 5, 15), 2)), 6)
        self.assertEqual(len(cps_scale((1, 3, 5, 15), 2)), 5)

    def test_odd_seed_sets_counts(self):
        self.assertEqual(len(odd_seed_sets(4, 15)), 70)
        self.assertEqual(len(odd_seed_sets(6, 15)), 28)


class TestMos(unittest.TestCase):
    # Golden zigzag for the fifth, EXECUTED against the real C++
    # (tests/test_tuning testBrunZigzag + crossval002, 2026-07-21).
    FIFTH = 701.955 / 1200.0

    def test_zigzag_fifth_denominators(self):
        dens = [den for _, den in zigzag(self.FIFTH)]
        self.assertEqual(dens, [1, 2, 3, 5, 7, 12, 17, 29, 41, 53])

    def test_zigzag_fifth_numerators(self):
        nums = [num for num, _ in zigzag(self.FIFTH)]
        self.assertEqual(nums, [1, 1, 2, 3, 4, 7, 10, 17, 24, 31])

    def test_cardinalities_deduped_ascending(self):
        self.assertEqual(mos_cardinalities(self.FIFTH),
                         [1, 2, 3, 5, 7, 12, 17, 29, 41, 53])

    def test_mos_cents_pentatonic(self):
        scale = mos_cents(self.FIFTH, 5)
        self.assertEqual(len(scale), 5)
        self.assertEqual(scale[0], 0.0)
        # degree*g mod 1200, sorted: 2*701.955-1200 = 203.91
        self.assertAlmostEqual(scale[1], 203.91, places=6)
        self.assertAlmostEqual(scale[-1], 905.865, places=6)

    def test_generator_bounds(self):
        with self.assertRaises(ValueError):
            zigzag(1.5)


if __name__ == "__main__":
    unittest.main()
