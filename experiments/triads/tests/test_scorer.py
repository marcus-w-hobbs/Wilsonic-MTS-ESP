"""Golden tests TRIAD-001..004 for the frozen triad scorer.

Run from experiments/triads/:
    python3.12 -m unittest discover -s tests -v

Every golden number in this file was hand-verified or derived from a run
whose individual triads were hand-checked on 2026-07-20 (see LOG.md).
These numbers define the scorer's behavior; if a change moves them, the
change is a scorer-version bump requiring Marcus's approval.
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scorer as sc  # noqa: E402

# Named fixtures ------------------------------------------------------------

# Plugin-canonical hexany 1-3-5-7 (verified against CPSTuningBase behavior:
# octave-reduced raw pairwise products, no 1/1 present).
HEXANY_1357 = ["35/32", "5/4", "21/16", "3/2", "7/4", "15/8"]

# Harmonic segment 8:9:...:16 octave-reduced (contains 1/1; 16 dedups to 1).
SEGMENT_8_16 = [F(h, 8) for h in range(8, 17)]

MAJOR_TRIAD_SCALE = ["1", "5/4", "3/2"]

ASYM_SCALE = ["1", "9/8", "21/16", "3/2", "7/4"]

TWELVE_EDO = [100.0 * i for i in range(12)]


def _count_raw_rational(sample):
    """Classify every triple of an arbitrary ascending rational multiset."""
    p = s = g = 0
    for a, b, c in combinations(sorted(sample), 3):
        label = sc.classify_rational_triple(a, b, c)
        if label == sc.PROPORTIONAL:
            p += 1
        elif label == sc.SUBCONTRARY:
            s += 1
        elif label == sc.GEOMETRIC:
            g += 1
    return p, s, g


def _psg(result):
    return (result.proportional, result.subcontrary, result.geometric)


class TestTriad001RationalMechanics(unittest.TestCase):
    """TRIAD-001: exact-rational scoring over the two-octave sample."""

    def test_octave_reduction_half_open(self):
        self.assertEqual(sc.reduce_rational(1), F(1))
        self.assertEqual(sc.reduce_rational(2), F(1))  # 2 -> [1,2) lower edge
        self.assertEqual(sc.reduce_rational(3), F(3, 2))
        self.assertEqual(sc.reduce_rational(F(1, 3)), F(4, 3))
        self.assertEqual(sc.reduce_rational(7), F(7, 4))
        self.assertEqual(sc.reduce_rational("35/2"), F(35, 32))

    def test_reduction_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            sc.reduce_rational(0)
        with self.assertRaises(ValueError):
            sc.reduce_rational(-3)

    def test_canonical_scale_dedups_and_sorts(self):
        scale = sc.canonical_rational_scale([F(3), F(3, 2), F(6), F(1), F(2)])
        self.assertEqual(scale, (F(1), F(3, 2)))

    def test_hexany_canonical_matches_plugin_form(self):
        seeds = [1, 3, 5, 7]
        products = [F(a * b) for a, b in combinations(seeds, 2)]
        scale = sc.canonical_rational_scale(products)
        self.assertEqual(
            scale,
            (F(35, 32), F(5, 4), F(21, 16), F(3, 2), F(7, 4), F(15, 8)),
        )

    def test_two_octave_sample(self):
        scale = sc.canonical_rational_scale(MAJOR_TRIAD_SCALE)
        sample = sc.two_octave_sample_rational(scale)
        self.assertEqual(sample, (F(1), F(5, 4), F(3, 2), F(2), F(5, 2), F(3)))

    def test_major_triad_scale_window_counts(self):
        # Hand-verified triads: P = {(1,5/4,3/2), (1,3/2,2), (1,2,3),
        # (3/2,2,5/2), (2,5/2,3)}; S = {(1,3/2,3), (3/2,2,3)}.
        r = sc.score_rational(MAJOR_TRIAD_SCALE)
        self.assertEqual(_psg(r), (5, 2, 0))
        self.assertEqual(r.score_min, 2)
        self.assertEqual(r.score_product, 10)
        self.assertEqual(r.sample_size, 6)

    def test_major_triad_scale_anchored_counts(self):
        # Hand-verified: P = {(3/4,1,5/4), (1,5/4,3/2), (1,3/2,2)};
        # S = {(3/4,1,3/2)}.
        r = sc.score_rational_anchored(MAJOR_TRIAD_SCALE)
        self.assertEqual(_psg(r), (3, 1, 0))


class TestTriad002GoldenTriads(unittest.TestCase):
    """TRIAD-002: prototype sonorities classify correctly; segment controls."""

    def test_major_prototype_4_5_6(self):
        self.assertEqual(sc.classify_rational_triple(4, 5, 6), sc.PROPORTIONAL)

    def test_root_position_major_equals_4_5_6(self):
        self.assertEqual(
            sc.classify_rational_triple(F(1), F(5, 4), F(3, 2)), sc.PROPORTIONAL
        )

    def test_minor_prototype_10_12_15(self):
        self.assertEqual(sc.classify_rational_triple(10, 12, 15), sc.SUBCONTRARY)

    def test_geometric_prototype_4_6_9(self):
        self.assertEqual(sc.classify_rational_triple(4, 6, 9), sc.GEOMETRIC)

    def test_no_relation(self):
        self.assertIsNone(sc.classify_rational_triple(F(1), F(9, 8), F(3, 2)))

    def test_harmonic_segment_p_heavy(self):
        r = sc.score_rational(SEGMENT_8_16)
        self.assertEqual(_psg(r), (46, 8, 2))
        self.assertGreater(r.proportional, 5 * r.subcontrary)

    def test_harmonic_segment_anchored_p_heavy(self):
        r = sc.score_rational_anchored(SEGMENT_8_16)
        self.assertEqual(_psg(r), (32, 5, 2))

    def test_subharmonic_dual_s_heavy(self):
        dual = sc.invert_rational_scale(SEGMENT_8_16)
        r = sc.score_rational_anchored(dual)
        self.assertEqual(_psg(r), (5, 32, 2))  # exact mirror, anchored


class TestTriad003TemperedPath(unittest.TestCase):
    """TRIAD-003: epsilon layer; 12-EDO calibration facts."""

    def test_12edo_major_triad_not_proportional_at_musical_precision(self):
        # Exact deviation is -14.859 cents; the plan's original epsilon=14
        # threshold was corrected to 15 after computing the true value.
        self.assertEqual(sc.classify_cents_triple(0.0, 400.0, 700.0, 2.0), frozenset())
        self.assertEqual(sc.classify_cents_triple(0.0, 400.0, 700.0, 14.0), frozenset())
        self.assertEqual(
            sc.classify_cents_triple(0.0, 400.0, 700.0, 15.0),
            frozenset({sc.PROPORTIONAL}),
        )

    def test_12edo_window_counts(self):
        r = sc.score_cents(TWELVE_EDO, 2.0)
        self.assertEqual(_psg(r), (17, 17, 132))
        self.assertEqual(r.epsilon_cents, 2.0)

    def test_12edo_anchored_counts(self):
        r = sc.score_cents_anchored(TWELVE_EDO, 2.0)
        self.assertEqual(_psg(r), (12, 12, 132))

    def test_12edo_p_equals_s_by_inversion_symmetry(self):
        # 12-EDO is inversionally symmetric, so P == S at any epsilon.
        for eps in (0.5, 2.0, 15.0):
            r = sc.score_cents(TWELVE_EDO, eps)
            self.assertEqual(r.proportional, r.subcontrary)

    def test_cents_reduction_wrap_dedup(self):
        scale = sc.canonical_cents_scale([0.0, 1200.0, 700.0, 1900.0])
        self.assertEqual(scale, (0.0, 700.0))


class TestTriad004Duality(unittest.TestCase):
    """TRIAD-004: inversion swaps P and S. Three layers, all exact-rational.

    (a) Theorem layer: reflecting the two-octave sample (x -> 4/x) swaps
        P and S exactly for EVERY scale. This validates the classifier.
    (b) Pipeline layer, anchored convention: score(invert(S)) swaps
        exactly for every scale, including scales containing 1/1.
    (c) Pipeline layer, window convention: exact swap holds only for
        scales without 1/1; the segment counterexample is frozen below.
    """

    ALL_SCALES = {
        "hexany": HEXANY_1357,
        "segment": SEGMENT_8_16,
        "triad": MAJOR_TRIAD_SCALE,
        "asym": ASYM_SCALE,
    }

    def test_004a_reflected_sample_swaps_exactly_for_all_scales(self):
        for name, ratios in self.ALL_SCALES.items():
            with self.subTest(scale=name):
                scale = sc.canonical_rational_scale(ratios)
                sample = sc.two_octave_sample_rational(scale)
                p, s, g = _count_raw_rational(sample)
                rp, rs, rg = _count_raw_rational([4 / F(x) for x in sample])
                self.assertEqual((rp, rs, rg), (s, p, g))

    def test_004b_anchored_pipeline_swaps_exactly_for_all_scales(self):
        for name, ratios in self.ALL_SCALES.items():
            with self.subTest(scale=name):
                fwd = sc.score_rational_anchored(ratios)
                dual = sc.score_rational_anchored(sc.invert_rational_scale(ratios))
                self.assertEqual(
                    _psg(dual),
                    (fwd.subcontrary, fwd.proportional, fwd.geometric),
                )

    def test_004c_window_pipeline_swaps_exactly_without_unity(self):
        # Scales whose canonical form excludes 1/1 (all odd-seeded CPS
        # qualify: odd products are never powers of two).
        for name in ("hexany",):
            with self.subTest(scale=name):
                ratios = self.ALL_SCALES[name]
                fwd = sc.score_rational(ratios)
                dual = sc.score_rational(sc.invert_rational_scale(ratios))
                self.assertEqual(
                    _psg(dual),
                    (fwd.subcontrary, fwd.proportional, fwd.geometric),
                )

    def test_004c_window_boundary_counterexample_frozen(self):
        # Known, documented behavior: with 1/1 in the scale the window
        # convention's pipeline swap is inexact (boundary of [1,4)).
        fwd = sc.score_rational(SEGMENT_8_16)
        dual = sc.score_rational(sc.invert_rational_scale(SEGMENT_8_16))
        self.assertEqual(_psg(fwd), (46, 8, 2))
        self.assertEqual(_psg(dual), (7, 42, 2))  # NOT (8, 46, 2)


class TestTranspositionInvariance(unittest.TestCase):
    """Anchored scoring is invariant under transposition; window is not."""

    def test_anchored_invariant_under_transposition(self):
        base = sc.score_rational_anchored(HEXANY_1357)
        for k in (F(3), F(5, 4), F(7, 5)):
            with self.subTest(factor=k):
                moved = sc.score_rational_anchored(
                    [F(x) * k for x in map(F, HEXANY_1357)]
                )
                self.assertEqual(_psg(moved), _psg(base))

    def test_hexany_anchored_sits_on_diagonal(self):
        # CPS inversion-symmetry hypothesis (plan §1.3): the 1-3-5-7 hexany
        # lands exactly on P == S under the anchored convention.
        r = sc.score_rational_anchored(HEXANY_1357)
        self.assertEqual(_psg(r), (8, 8, 0))

    def test_window_transposition_caveat_frozen(self):
        # Documented limitation of the window convention.
        base = sc.score_rational(HEXANY_1357)
        moved = sc.score_rational([F(x) * 3 for x in map(F, HEXANY_1357)])
        self.assertEqual(_psg(base), (10, 9, 0))
        self.assertEqual(_psg(moved), (11, 11, 0))


class TestProvenanceFields(unittest.TestCase):
    def test_rational_result_records_provenance(self):
        r = sc.score_rational(HEXANY_1357)
        self.assertEqual(r.scorer_version, sc.SCORER_VERSION)
        self.assertEqual(r.path, "rational")
        self.assertEqual(r.convention, "two-octave-window")
        self.assertIsNone(r.epsilon_cents)
        self.assertEqual(len(r.scale), 6)

    def test_cents_result_records_epsilon(self):
        r = sc.score_cents_anchored(TWELVE_EDO, 3.5)
        self.assertEqual(r.epsilon_cents, 3.5)
        self.assertEqual(r.convention, "middle-anchored")


class TestPrimaryConvention(unittest.TestCase):
    """The anchored convention is primary (Marcus, 2026-07-21). These pin the
    dispatch so a future edit cannot silently repoint it."""

    def test_primary_is_anchored(self):
        self.assertEqual(sc.PRIMARY_CONVENTION, sc.ANCHORED_CONVENTION)
        self.assertEqual(sc.PRIMARY_CONVENTION, "middle-anchored")

    def test_score_dispatches_to_anchored(self):
        r = sc.score(HEXANY_1357)
        self.assertEqual(r.convention, sc.PRIMARY_CONVENTION)
        self.assertEqual(_psg(r), _psg(sc.score_rational_anchored(HEXANY_1357)))

    def test_score_tempered_dispatches_to_anchored(self):
        r = sc.score_tempered(TWELVE_EDO, 3.5)
        self.assertEqual(r.convention, sc.PRIMARY_CONVENTION)
        self.assertEqual(r.epsilon_cents, 3.5)
        self.assertEqual(
            _psg(r), _psg(sc.score_cents_anchored(TWELVE_EDO, 3.5))
        )

    def test_legacy_names_still_mean_window(self):
        # Pre-2026-07-21 scripts and result files depend on these.
        self.assertIs(sc.score_rational, sc.score_rational_window)
        self.assertIs(sc.score_cents, sc.score_cents_window)
        self.assertEqual(
            sc.score_rational_window(HEXANY_1357).convention,
            sc.WINDOW_CONVENTION,
        )


if __name__ == "__main__":
    unittest.main()
