"""Unit tests for moslat002.py (MOS-LAT-002) — exact Q(sqrt d) arithmetic,
mixed-tail generator construction, corpus census, spectral-gap values, and
the reuse contract with moslat001's rank statistics. Written BEFORE the
first experiment run (LOG.md pre-registration, 2026-07-29).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from math import sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import moslat001 as ml1  # noqa: E402
import moslat002 as ml  # noqa: E402


def cf_eval(preamble: tuple[int, ...], tail: tuple[int, ...],
            reps: int = 200) -> float:
    """Independent numeric evaluation of [0; preamble, (tail)*] by exact
    rational truncation — cross-check for the algebraic construction."""
    digits = list(preamble) + list(tail) * reps
    value = Fraction(0)
    for d in reversed(digits):
        value = Fraction(1, 1) / (d + value)
    return float(value)


class TestSquarefree(unittest.TestCase):
    def test_split(self):
        self.assertEqual(ml.squarefree_split(12), (2, 3))
        self.assertEqual(ml.squarefree_split(45), (3, 5))
        self.assertEqual(ml.squarefree_split(117), (3, 13))
        self.assertEqual(ml.squarefree_split(5), (1, 5))
        self.assertEqual(ml.squarefree_split(16), (4, 1))


class TestQuad(unittest.TestCase):
    def test_normalization(self):
        x = ml.quad(2, 4, -6, 5)  # -> (-1 - 2*sqrt5)/3
        self.assertEqual((x.a, x.b, x.c, x.d), (-1, -2, 3, 5))

    def test_square_part_folds_into_b(self):
        self.assertEqual(ml.quad(0, 1, 1, 12), ml.quad(0, 2, 1, 3))

    def test_perfect_square_d_folds_into_a(self):
        self.assertEqual(ml.quad(1, 3, 2, 4), ml.quad(7, 0, 2, 2))

    def test_sign_mixed(self):
        self.assertEqual(ml.quad(-1, 1, 1, 2).sign(), 1)   # sqrt2 - 1 > 0
        self.assertEqual(ml.quad(-2, 1, 1, 2).sign(), -1)  # sqrt2 - 2 < 0
        self.assertEqual(ml.quad(4, -1, 1, 13).sign(), 1)  # 4 - sqrt13 > 0
        self.assertEqual(ml.quad(3, -1, 1, 13).sign(), -1)

    def test_floor_exact(self):
        self.assertEqual(ml.quad(1, 1, 1, 2).floor(), 2)     # 2.414
        self.assertEqual(ml.quad(-1, -1, 1, 2).floor(), -3)  # -2.414
        self.assertEqual(ml.quad(4, 0, 2, 3).floor(), 2)     # exact integer

    def test_inverse(self):
        g = ml.generator_from((2, 2), (2, 3))
        self.assertEqual(g * g.inv(), ml.quad(1, 0, 1, g.d))

    def test_conjugate_is_involution(self):
        g = ml.generator_from((1, 2), (3,))
        self.assertEqual(g.conj().conj(), g)

    def test_quadratic_identity_silver(self):
        # [0;(2)*] = sqrt2 - 1 satisfies x**2 + 2x - 1 = 0 exactly.
        x = ml.tail_fixed_point((2,))
        self.assertEqual(x * x + 2 * x - 1, ml.quad(0, 0, 1, 2))

    def test_mixed_field_arithmetic_raises(self):
        with self.assertRaises(TypeError):
            _ = ml.quad(0, 1, 1, 2) + ml.quad(0, 1, 1, 3)

    def test_mixed_field_equality_is_false(self):
        self.assertNotEqual(ml.quad(0, 1, 1, 2), ml.quad(0, 1, 1, 3))
        self.assertNotEqual(ml.quad(1, 0, 2, 2), ml.quad(0, 1, 1, 3))

    def test_rational_quads_compare_across_fields(self):
        self.assertEqual(ml.quad(1, 0, 2, 2), ml.quad(2, 0, 4, 13))
        self.assertEqual(hash(ml.quad(1, 0, 2, 2)),
                         hash(ml.quad(2, 0, 4, 13)))


class TestTailFixedPoints(unittest.TestCase):
    """Exact values hand-derived in the LOG.md pre-registration entry."""

    def test_known_values(self):
        self.assertEqual(ml.tail_fixed_point((2,)),
                         ml.quad(-1, 1, 1, 2))       # sqrt2 - 1
        self.assertEqual(ml.tail_fixed_point((3,)),
                         ml.quad(-3, 1, 2, 13))      # (sqrt13 - 3)/2
        self.assertEqual(ml.tail_fixed_point((1, 2)),
                         ml.quad(-1, 1, 1, 3))       # sqrt3 - 1
        self.assertEqual(ml.tail_fixed_point((2, 1)),
                         ml.quad(-1, 1, 2, 3))       # (sqrt3 - 1)/2

    def test_all_tails_in_unit_interval_and_verified(self):
        for tail in ml.TAILS:
            x = ml.tail_fixed_point(tail)
            self.assertTrue(0.0 < float(x) < 1.0, tail)
            self.assertAlmostEqual(float(x), cf_eval((), tail), places=12)

    def test_all_ones_tail_matches_moslat001(self):
        # The construction generalizes moslat001: same value for (1)*.
        self.assertAlmostEqual(float(ml.tail_fixed_point((1,))),
                               float(ml1.PHI_INV), places=14)


class TestGeneratorConstruction(unittest.TestCase):
    def test_preamble_application(self):
        # [0;1,(2)*] = 1/(1 + sqrt2 - 1) = sqrt2/2.
        self.assertEqual(ml.generator_from((1,), (2,)), ml.quad(0, 1, 2, 2))

    def test_rotation_absorption(self):
        # [0;1,(2,1)*] has digit sequence 1,2,1,2,... == [0;(1,2)*].
        self.assertEqual(ml.generator_from((1,), (2, 1)),
                         ml.generator_from((), (1, 2)))
        # [0;2,(2)*] == [0;(2)*] shifted: sequence 2,2,2,... identical.
        self.assertEqual(ml.generator_from((2,), (2,)),
                         ml.generator_from((), (2,)))

    def test_numeric_cross_check(self):
        for preamble, tail in (((3, 1, 2), (2, 3)), ((1,), (3, 1)),
                               ((2, 2, 2), (3,)), ((), (3, 2))):
            g = ml.generator_from(preamble, tail)
            self.assertAlmostEqual(float(g), cf_eval(preamble, tail),
                                   places=12)

    def test_iota_zero_is_zero(self):
        g = ml.generator_from((2,), (2, 3))
        self.assertEqual(ml1.iota(0, g, g.conj()), ml.quad(0, 0, 1, g.d))


class TestSpectralGap(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(ml.spectral_gap((2,)),
                               (1 + sqrt(2)) ** 2, places=10)
        self.assertAlmostEqual(ml.spectral_gap((3,)),
                               ((3 + sqrt(13)) / 2) ** 2, places=10)
        self.assertAlmostEqual(ml.spectral_gap((1, 2)),
                               (2 + sqrt(3)) ** 2, places=10)
        self.assertAlmostEqual(ml.spectral_gap((1, 3)),
                               ((5 + sqrt(21)) / 2) ** 2, places=10)
        self.assertAlmostEqual(ml.spectral_gap((2, 3)),
                               (4 + sqrt(15)) ** 2, places=10)

    def test_rotation_invariance(self):
        self.assertAlmostEqual(ml.spectral_gap((1, 2)),
                               ml.spectral_gap((2, 1)), places=12)
        self.assertAlmostEqual(ml.spectral_gap((2, 3)),
                               ml.spectral_gap((3, 2)), places=12)

    def test_nobles_would_be_constant(self):
        # The MOS-LAT-001 degeneracy this corpus exists to break.
        phi_sq = ((1 + sqrt(5)) / 2) ** 2
        self.assertAlmostEqual(ml.spectral_gap((1,)), phi_sq, places=12)


class TestCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generators, cls.census = ml.enumerate_corpus()

    def test_census(self):
        # Pre-registered: 8 tails x 40 preambles = 320 raw, 27 canonical
        # per tail = 216 distinct (preamble-last-digit == tail-last-digit
        # absorbs into a rotation).
        self.assertEqual(self.census["n_raw"], 320)
        self.assertEqual(self.census["n_distinct"], 216)
        self.assertEqual(self.census["duplicates_dropped"], 104)

    def test_values_distinct_and_in_unit_interval(self):
        floats = [g["g01"] for g in self.generators]
        self.assertEqual(len(set(floats)), len(floats))
        for v in floats:
            self.assertTrue(0.0 < v < 1.0)

    def test_no_noble_generators(self):
        # No all-1s tail: every tail cycle contains a digit > 1.
        for g in self.generators:
            self.assertTrue(any(t > 1 for t in g["tail_cycle"]), g["cf"])

    def test_spectral_gap_takes_five_values(self):
        gaps = {round(g["spectral_gap"], 9) for g in self.generators}
        self.assertEqual(len(gaps), 5)
        expected = {(1 + sqrt(2)) ** 2, ((3 + sqrt(13)) / 2) ** 2,
                    (2 + sqrt(3)) ** 2, ((5 + sqrt(21)) / 2) ** 2,
                    (4 + sqrt(15)) ** 2}
        self.assertEqual(gaps, {round(v, 9) for v in expected})

    def test_meets_registered_floor(self):
        self.assertGreaterEqual(self.census["n_distinct"], 40)


class TestStatisticsReuse(unittest.TestCase):
    """The comparability contract: MOS-LAT-002 runs MOS-LAT-001's own
    statistics code objects, not lookalikes."""

    def test_same_code_objects(self):
        self.assertIs(ml.partial_spearman, ml1.partial_spearman)
        self.assertIs(ml.stratified_permutation_p,
                      ml1.stratified_permutation_p)
        self.assertIs(ml.iota, ml1.iota)
        self.assertIs(ml.score_tempered, ml1.score_tempered)

    def test_seed_and_bounds_shared(self):
        self.assertEqual(ml.SEED, 20260725)
        self.assertEqual((ml.MIN_CARD, ml.MAX_CARD), (5, 22))

    def test_predictor_order(self):
        self.assertEqual(
            ml.H_M1_PREDICTORS,
            ("g01_baseline", "conj_sep", "window_width", "spread",
             "norm_spread", "spectral_gap"))


class TestHolm(unittest.TestCase):
    def test_holm_adjust(self):
        adj = ml.holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adj["a"], 0.03)
        self.assertAlmostEqual(adj["c"], 0.06)
        self.assertAlmostEqual(adj["b"], 0.06)  # monotone step-down

    def test_holm_caps_at_one(self):
        adj = ml.holm_adjust({"a": 0.9, "b": 0.5})
        self.assertEqual(adj["a"], 1.0)


class TestHM1Determinism(unittest.TestCase):
    def _synthetic_rows(self) -> list[dict]:
        rows = []
        for i, gen in enumerate(("[0;(2)*]", "[0;(3)*]", "[0;(1,2)*]")):
            for j, card in enumerate((5, 7, 12, 17)):
                rows.append({
                    "cf": gen, "g01": 0.3 + 0.1 * i, "cardinality": card,
                    "P": (i * 5 + j * 3) % 11,
                    "conj_sep": 1.0 + i, "window_width": 0.1 * (j + 1),
                    "spread": 0.5 + 0.2 * j, "norm_spread": 0.05 * (i + j),
                    "spectral_gap": (5.8, 10.9, 13.9)[i],
                })
        return rows

    def test_repeat_runs_identical(self):
        rows = self._synthetic_rows()
        first = ml.run_h_m1(rows, n_perm=199)
        second = ml.run_h_m1(rows, n_perm=199)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
