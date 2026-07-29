"""Unit tests for the SHADOW-001 harness helpers (shadow001.py).

Fast, deterministic — no full sweep here. The pure helpers are pinned
(collision skips, displacement, factorization/sharing, comma spectrum,
tone survival) plus one end-to-end evaluate_scale() on the classic hexany
against the SPEC-quoted baseline (exact (P,S) = (8,8) under scorer v1.1.0).
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from math import log2
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import shadow001  # noqa: E402


class TestPerturbationVariants(unittest.TestCase):
    def test_hexany_collision_skip(self):
        variants = list(shadow001.perturbation_variants((1, 3, 5, 7)))
        # pos 0 (n=1), k=3, sign -1 -> m=7 collides with factor 7: skipped
        keys = {(pos, k, sign) for pos, _, k, sign, _, _ in variants}
        self.assertNotIn((0, 3, -1), keys)
        self.assertIn((0, 3, 1), keys)  # m=9 does not collide
        self.assertEqual(len(variants), 4 * 14 * 2 - 1)  # 111

    def test_eikosany_collision_skips(self):
        variants = list(
            shadow001.perturbation_variants((1, 3, 5, 7, 9, 11)))
        keys = {(pos, k, sign) for pos, _, k, sign, _, _ in variants}
        self.assertNotIn((0, 3, 1), keys)   # m=9 collides
        self.assertNotIn((0, 3, -1), keys)  # m=7 collides
        self.assertEqual(len(variants), 6 * 14 * 2 - 2)  # 166

    def test_replacement_value_and_seed_order(self):
        variants = {
            (pos, k, sign): (m, new_seeds)
            for pos, _, k, sign, m, new_seeds
            in shadow001.perturbation_variants((1, 3, 5, 7))
        }
        m, new_seeds = variants[(0, 8, 1)]
        self.assertEqual(m, 257)
        self.assertEqual(new_seeds, (257, 3, 5, 7))
        m, new_seeds = variants[(2, 4, -1)]
        self.assertEqual(m, 79)
        self.assertEqual(new_seeds, (1, 3, 79, 7))


class TestDisplacement(unittest.TestCase):
    def test_known_values(self):
        # 257/256 = 6.7585 cents; 255/256 = 6.7849 cents
        self.assertAlmostEqual(
            shadow001.displacement_cents(1, 8, 1),
            1200.0 * log2(257 / 256), places=9)
        self.assertAlmostEqual(
            shadow001.displacement_cents(1, 8, -1),
            abs(1200.0 * log2(255 / 256)), places=9)

    def test_halves_per_k_step(self):
        d_prev = shadow001.displacement_cents(3, 8, 1)
        d_next = shadow001.displacement_cents(3, 9, 1)
        self.assertAlmostEqual(d_prev / d_next, 2.0, places=2)


class TestFactorization(unittest.TestCase):
    def test_factorize(self):
        self.assertEqual(shadow001.factorize(255), {3: 1, 5: 1, 17: 1})
        self.assertEqual(shadow001.factorize(1), {})
        self.assertEqual(shadow001.factorize(4095), {3: 2, 5: 1, 7: 1, 13: 1})

    def test_is_prime(self):
        self.assertTrue(shadow001.is_prime(257))
        self.assertFalse(shadow001.is_prime(255))
        self.assertFalse(shadow001.is_prime(1))

    def test_shared_factors(self):
        # 255 = 3*5*17 shares 3 and 5 with remaining {3,5,7}
        self.assertEqual(shadow001.shared_factors(255, (3, 5, 7)), (3, 5))
        self.assertEqual(shadow001.shared_factors(257, (3, 5, 7)), ())
        # 9 in the remaining set exposes prime 3
        self.assertEqual(shadow001.shared_factors(33, (5, 7, 9, 11)), (3, 11))


class TestCommaSpectrumAndSurvival(unittest.TestCase):
    def test_wrap_aware_distance(self):
        # 1/1 and 255/128 are 6.7849 cents apart THROUGH the octave wrap
        scale = shadow001.scorer.canonical_rational_scale(
            [1, Fraction(255, 128), Fraction(3, 2)])
        spectrum = shadow001.comma_spectrum(scale)
        self.assertEqual(len(spectrum), 1)
        self.assertAlmostEqual(
            spectrum[0]["cents"], abs(1200.0 * log2(255 / 256)), places=9)
        self.assertEqual(spectrum[0]["ratio"], "255/128")

    def test_tone_survival_collapse(self):
        # two tones 0.3 cents apart: distinct at 0.01/0.1, merged at 0.5/2
        cents = (0.0, 700.0, 700.3)
        survival = shadow001.tone_survival(cents)
        self.assertEqual(survival["0.01"], 3)
        self.assertEqual(survival["0.1"], 3)
        self.assertEqual(survival["0.5"], 2)
        self.assertEqual(survival["2.0"], 2)


class TestEvaluateScale(unittest.TestCase):
    def test_hexany_baseline(self):
        row = shadow001.evaluate_scale((1, 3, 5, 7), 2)
        self.assertEqual(row["tone_count_exact"], 6)
        # (6,6) under v1.1.0 (within-octave span), matching the anchored
        # block of triads/results/hex001.jsonl. SPEC §BRIDGE-001's "(8,8)"
        # is the v1.0.0 number (all 8 octahedron faces, no span limit;
        # verified: score(s, max_span=None) gives (8,8)).
        self.assertEqual(row["exact"]["P"], 6)
        self.assertEqual(row["exact"]["S"], 6)
        self.assertEqual(row["tempered"]["epsilon_cents"], 2.0)

    def test_perturbed_p_equals_s(self):
        # CPS(4,2) inversional symmetry is seed-value independent
        row = shadow001.evaluate_scale((257, 3, 5, 7), 2)
        self.assertEqual(row["exact"]["P"], row["exact"]["S"])
        self.assertEqual(row["tempered"]["P"], row["tempered"]["S"])


if __name__ == "__main__":
    unittest.main()
