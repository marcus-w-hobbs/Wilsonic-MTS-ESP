"""Unit tests for moslat001.py (MOS-LAT-001) — exact Q(sqrt5) arithmetic,
noble generator construction, the monotone-case window theorem, and the
rank-statistics helpers. Written BEFORE the first experiment run (LOG.md
pre-registration, 2026-07-28).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from math import sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import moslat001 as ml  # noqa: E402

PHI = (1 + sqrt(5.0)) / 2


class TestQ5(unittest.TestCase):
    def test_phi_inv_value(self):
        self.assertAlmostEqual(float(ml.PHI_INV), 1 / PHI, places=12)

    def test_normalization(self):
        x = ml.q5(2, 4, -6)  # -> (-1 - 2*sqrt5)/3
        self.assertEqual((x.a, x.b, x.c), (-1, -2, 3))

    def test_quadratic_identity(self):
        # 1/phi satisfies x**2 + x - 1 = 0 exactly.
        g = ml.PHI_INV
        self.assertEqual(g * g + g - 1, ml.q5(0, 0, 1))

    def test_sign_mixed(self):
        self.assertEqual(ml.q5(-2, 1, 1).sign(), 1)   # sqrt5 - 2 > 0
        self.assertEqual(ml.q5(-3, 1, 1).sign(), -1)  # sqrt5 - 3 < 0
        self.assertEqual(ml.q5(3, -1, 1).sign(), 1)
        self.assertEqual(ml.q5(2, -1, 1).sign(), -1)

    def test_floor_exact(self):
        self.assertEqual(ml.q5(1, 1, 1).floor(), 3)     # 3.236
        self.assertEqual(ml.q5(-1, -1, 1).floor(), -4)  # -3.236
        self.assertEqual(ml.PHI_INV.conj().floor(), -2)  # -1.618
        self.assertEqual(ml.q5(4, 0, 2).floor(), 2)     # exact integer 2
        self.assertEqual((ml.q5(3, 1, 1) * 0).floor(), 0)

    def test_inverse(self):
        g = ml.noble_from_preamble((2, 2))
        self.assertEqual(g * g.inv(), ml.q5(1, 0, 1))

    def test_conjugate_is_involution(self):
        g = ml.noble_from_preamble((1, 2))
        self.assertEqual(g.conj().conj(), g)


class TestNobleConstruction(unittest.TestCase):
    """Exact values hand-derived in the LOG.md pre-registration entry."""

    def test_known_values(self):
        self.assertEqual(ml.noble_from_preamble(()), ml.q5(-1, 1, 2))
        self.assertEqual(ml.noble_from_preamble((2,)), ml.q5(3, -1, 2))
        self.assertEqual(ml.noble_from_preamble((1, 2)), ml.q5(5, 1, 10))
        self.assertEqual(ml.noble_from_preamble((2, 2)), ml.q5(7, 1, 22))

    def test_preamble_ending_in_one_collapses(self):
        self.assertEqual(ml.noble_from_preamble((1,)),
                         ml.noble_from_preamble(()))
        self.assertEqual(ml.noble_from_preamble((2, 1)),
                         ml.noble_from_preamble((2,)))

    def test_canonical_preambles(self):
        pre = ml.canonical_preambles()
        self.assertEqual(len(pre), 27)  # 1 + 2 + 6 + 18
        self.assertNotIn((1,), pre)
        self.assertNotIn((2, 1), pre)
        values = [float(ml.noble_from_preamble(p)) for p in pre]
        self.assertEqual(len(set(values)), 27)  # all distinct
        for v in values:
            self.assertTrue(0.0 < v < 1.0)

    def test_cf_convergents_golden(self):
        conv = ml.cf_convergents((), max_den=21)
        # Fibonacci convergents of 1/phi: 1/1, 1/2, 2/3, 3/5, 5/8, 8/13, 13/21
        self.assertEqual(conv, {(1, 1), (1, 2), (2, 3), (3, 5), (5, 8),
                                (8, 13), (13, 21)})


class TestWindowTheorem(unittest.TestCase):
    """For |g - g'| > 1 the internal coordinate is strictly monotone in b,
    so both windows MUST verify — a theorem the implementation must pass."""

    def test_golden_generator_early_levels(self):
        g = ml.noble_from_preamble(())
        gc = g.conj()
        g01 = float(g)
        from families.mos import zigzag
        for level, (num, den) in enumerate(zigzag(g01)[:6]):
            rec = ml.verify_level(g, gc, g01, level, num, den)
            self.assertTrue(rec["verified"],
                            f"level {level} (num={num}, den={den}): {rec}")

    def test_iota_zero_is_zero(self):
        g = ml.noble_from_preamble((2,))
        self.assertEqual(ml.iota(0, g, g.conj()), ml.q5(0, 0, 1))


class TestRankStatistics(unittest.TestCase):
    def test_ranks_with_ties(self):
        self.assertEqual(ml.ranks([10.0, 20.0, 20.0, 30.0]),
                         [1.0, 2.5, 2.5, 4.0])

    def test_pearson_perfect(self):
        self.assertAlmostEqual(ml.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(ml.pearson([1, 2, 3], [6, 4, 2]), -1.0)

    def test_pearson_degenerate_is_zero(self):
        self.assertEqual(ml.pearson([1.0, 1.0, 1.0], [1, 2, 3]), 0.0)

    def test_partial_spearman_removes_confounder(self):
        # x and y are both driven by z alone -> partial rho ~ 0.
        z = [float(i) for i in range(12)]
        x = list(z)
        y = list(z)
        self.assertAlmostEqual(ml.partial_spearman(x, y, z), 0.0, places=9)

    def test_permutation_p_deterministic(self):
        import random
        x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        y = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0]
        z = [1.0] * 6
        strata = [0, 0, 0, 1, 1, 1]
        rho = ml.partial_spearman(x, y, z)
        p1 = ml.stratified_permutation_p(
            x, y, z, strata, rho, random.Random(ml.SEED), n_perm=199)
        p2 = ml.stratified_permutation_p(
            x, y, z, strata, rho, random.Random(ml.SEED), n_perm=199)
        self.assertEqual(p1, p2)
        self.assertTrue(0.0 < p1 <= 1.0)


if __name__ == "__main__":
    unittest.main()
