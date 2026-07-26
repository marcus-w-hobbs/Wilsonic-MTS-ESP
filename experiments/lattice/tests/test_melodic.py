"""Golden tests for melodic.py v0.1.0 (M1 gap entropy, M2 constant
structure + best-val tau, M3 Rothenberg propriety).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v

Fixture facts were hand-derived on 2026-07-25 (see LOG.md, "melodic.py
v0.1.0" entry). Two SPEC.md parentheticals are CORRECTED here, with the
machine-checked truth pinned:
- 12-EDO diatonic is NOT CS (600c tritone subtends 3 and 4 steps); it is
  proper but not strictly (max span-3 = min span-4 = 600c).
- Pythagorean 12 is STRICTLY PROPER; the known-improper fixture is the
  Pythagorean DIATONIC 7 (aug4 611.73c/3 steps > dim5 588.27c/4 steps),
  Rothenberg's classic example.
"""

from __future__ import annotations

import random
import sys
import unittest
from fractions import Fraction as F
from math import log2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import melodic as m  # noqa: E402

# Named fixtures ------------------------------------------------------------

DIATONIC_12EDO = [0.0, 200.0, 400.0, 500.0, 700.0, 900.0, 1100.0]
WHOLE_TONE_12EDO = [200.0 * i for i in range(6)]

# Pythagorean diatonic: chain 3^-1 .. 3^5, octave-reduced (F C G D A E B).
PYTH_7 = [F(3) ** k for k in range(-1, 6)]
# Pythagorean chromatic with wolf: chain 3^0 .. 3^11.
PYTH_12 = [F(3) ** k for k in range(12)]

# Plugin-canonical hexany 1-3-5-7 (matches triads tests fixture).
HEXANY_1357 = ["35/32", "5/4", "21/16", "3/2", "7/4", "15/8"]


def _rand6():
    """Deterministic 'random' 6-note scale (fixed seed, pinned in LOG.md).

    Sorted gaps ~ [98.3, 145.4, 150.8, 182.4, 243.1, 379.9]c: all six
    distinct at eps_gap = 0.5c (closest pair is 5.4c apart)."""
    rng = random.Random(20260725)
    return [rng.uniform(0.0, 1200.0) for _ in range(6)]


class TestCanonicalization(unittest.TestCase):
    def test_reduces_sorts_and_dedups(self):
        self.assertEqual(m.canonicalize([1300.0, 0.0, 100.0, -100.0]),
                         (0.0, 100.0, 1100.0))

    def test_dedup_epsilon_collapses_near_duplicates(self):
        self.assertEqual(m.canonicalize([0.0, 0.005, 100.0]), (0.0, 100.0))
        self.assertEqual(m.canonicalize([0.0, 0.005, 100.0],
                                        dedup_epsilon_cents=1e-6),
                         (0.0, 0.005, 100.0))

    def test_dedup_is_wrap_aware(self):
        self.assertEqual(m.canonicalize([0.0, 1199.999]), (0.0,))

    def test_ratios_to_cents_octave_reduces(self):
        cents = m.ratios_to_cents([1, 3, F(1, 3)])
        self.assertEqual(len(cents), 3)
        self.assertAlmostEqual(cents[0], 0.0)
        self.assertAlmostEqual(cents[1], 498.045, places=3)
        self.assertAlmostEqual(cents[2], 701.955, places=3)


class TestM1GapEntropy(unittest.TestCase):
    def test_diatonic_two_gap_classes(self):
        r = m.gap_entropy(DIATONIC_12EDO)
        self.assertEqual(r.gap_count, 7)
        self.assertEqual(r.gap_class_count, 2)
        self.assertEqual(r.gap_classes, ((100.0, 100.0, 2), (200.0, 200.0, 5)))
        # H(2/7, 5/7) in bits; <= 1 bit is the MOS bound from SPEC.
        self.assertAlmostEqual(r.entropy_bits, 0.863120568566631, places=12)
        self.assertLessEqual(r.entropy_bits, 1.0)

    def test_whole_tone_single_gap_class_zero_entropy(self):
        r = m.gap_entropy(WHOLE_TONE_12EDO)
        self.assertEqual(r.gap_class_count, 1)
        self.assertEqual(r.entropy_bits, 0.0)

    def test_pythagorean_diatonic_is_mos_shaped(self):
        # 5 tones (203.91c) + 2 limmas (90.22c): same distribution as the
        # 12-EDO diatonic, so identical entropy.
        r = m.gap_entropy(m.ratios_to_cents(PYTH_7))
        self.assertEqual(r.gap_class_count, 2)
        self.assertAlmostEqual(r.entropy_bits, 0.863120568566631, places=12)

    def test_random_six_note_scale_has_high_entropy(self):
        r = m.gap_entropy(_rand6())
        self.assertEqual(r.gap_class_count, 6)  # all gaps distinct
        self.assertAlmostEqual(r.entropy_bits, log2(6), places=12)

    def test_single_note_scale(self):
        r = m.gap_entropy([0.0])
        self.assertEqual(r.gap_classes, ((1200.0, 1200.0, 1),))
        self.assertEqual(r.entropy_bits, 0.0)

    def test_gaps_sum_to_octave(self):
        gaps = m.circular_gaps(m.canonicalize(_rand6()))
        self.assertAlmostEqual(sum(gaps), 1200.0, places=9)


class TestM2ConstantStructure(unittest.TestCase):
    def test_whole_tone_is_cs(self):
        r = m.constant_structure(WHOLE_TONE_12EDO)
        self.assertTrue(r.is_cs)
        self.assertEqual(r.violations, 0)

    def test_12edo_diatonic_is_not_cs_tritone(self):
        # SPEC parenthetical CORRECTED (LOG.md 2026-07-25): the 600c tritone
        # subtends 3 steps (F-B) and 4 (B-F'), exactly one violating class.
        r = m.constant_structure(DIATONIC_12EDO)
        self.assertFalse(r.is_cs)
        self.assertEqual(r.violations, 1)
        self.assertEqual(r.violating_classes, ((600.0, 600.0, (3, 4)),))

    def test_pythagorean_diatonic_is_cs(self):
        # aug4 (611.73c) and dim5 (588.27c) are distinct at eps_cs = 0.5c,
        # so unlike 12-EDO the Pythagorean diatonic IS a constant structure.
        r = m.constant_structure(m.ratios_to_cents(PYTH_7))
        self.assertTrue(r.is_cs)

    def test_pythagorean_12_is_cs(self):
        r = m.constant_structure(m.ratios_to_cents(PYTH_12))
        self.assertTrue(r.is_cs)

    def test_random_scale_is_trivially_cs(self):
        # Generic scales have no repeated interval sizes at all.
        r = m.constant_structure(_rand6())
        self.assertTrue(r.is_cs)

    def test_best_val_tau_pythagorean_diatonic(self):
        r = m.best_val_kendall_tau(PYTH_7)
        self.assertEqual(r.primes, (2, 3))
        self.assertEqual(r.patent_val, (7, 11))  # round(7*log2(3)) = 11
        self.assertEqual(r.vals_searched, 3)     # one odd coord: {10, 11, 12}
        self.assertEqual(r.min_tau, 0)           # patent val orders it exactly
        self.assertEqual(r.best_val, (7, 11))
        self.assertEqual(r.tie_pairs_at_best, 0)
        self.assertEqual(r.pair_count, 21)

    def test_best_val_tau_hexany(self):
        # 7-limit, 6 tones: patent val <6, 10, 14, 17>, 27 vals searched.
        r = m.best_val_kendall_tau(HEXANY_1357)
        self.assertEqual(r.primes, (2, 3, 5, 7))
        self.assertEqual(r.patent_val,
                         (6, round(6 * log2(3)), round(6 * log2(5)),
                          round(6 * log2(7))))
        self.assertEqual(r.vals_searched, 27)
        self.assertEqual(r.pair_count, 15)
        self.assertGreaterEqual(r.min_tau, 0)


class TestM3Propriety(unittest.TestCase):
    def test_12edo_diatonic_proper_not_strict(self):
        # max span-3 (600c tritone) == min span-4 (600c): proper, not strict.
        r = m.propriety(DIATONIC_12EDO)
        self.assertEqual(r.classification, m.PROPER)
        self.assertEqual(r.violating_span_pairs, 0)
        self.assertEqual(r.equal_span_pairs, 1)

    def test_whole_tone_strictly_proper(self):
        r = m.propriety(WHOLE_TONE_12EDO)
        self.assertEqual(r.classification, m.STRICTLY_PROPER)
        self.assertEqual(r.violating_span_pairs, 0)
        self.assertEqual(r.equal_span_pairs, 0)

    def test_pythagorean_diatonic_improper(self):
        # Rothenberg's classic improper scale: aug4 at 3 steps exceeds dim5
        # at 4 steps. (This is the SPEC's "known improper" fixture; the
        # SPEC's own example, Pythagorean 12, is strictly proper — below.)
        r = m.propriety(m.ratios_to_cents(PYTH_7))
        self.assertEqual(r.classification, m.IMPROPER)
        self.assertEqual(r.violating_span_pairs, 1)
        span, widest, narrowest = r.violations[0]
        self.assertEqual(span, 3)
        self.assertAlmostEqual(widest, 611.730, places=3)    # aug4
        self.assertAlmostEqual(narrowest, 588.270, places=3)  # dim5

    def test_pythagorean_12_strictly_proper(self):
        # SPEC parenthetical CORRECTED (LOG.md 2026-07-25): apotome/limma
        # steps never stack across spans; the machine check finds zero
        # violations and zero equalities.
        r = m.propriety(m.ratios_to_cents(PYTH_12))
        self.assertEqual(r.classification, m.STRICTLY_PROPER)

    def test_two_note_scale_vacuously_strict(self):
        r = m.propriety([0.0, 700.0])
        self.assertEqual(r.classification, m.STRICTLY_PROPER)
        self.assertEqual(r.violating_span_pairs, 0)


class TestCombinedEntryPoint(unittest.TestCase):
    def test_versions_and_provenance(self):
        r = m.score_melodic(DIATONIC_12EDO)
        self.assertEqual(r.melodic_version, m.MELODIC_VERSION)
        self.assertEqual(r.frozen_scorer_version, m.FROZEN_SCORER_VERSION)
        self.assertEqual(r.gap_entropy.melodic_version, m.MELODIC_VERSION)
        self.assertEqual(r.scale, tuple(DIATONIC_12EDO))

    def test_epsilons_recorded_in_receipts(self):
        r = m.score_melodic(DIATONIC_12EDO)
        self.assertEqual(r.gap_entropy.dedup_epsilon_cents, 0.01)
        self.assertEqual(r.gap_entropy.gap_epsilon_cents, 0.5)
        self.assertEqual(r.constant_structure.cs_epsilon_cents, 0.5)
        self.assertEqual(r.propriety.propriety_epsilon_cents, 1e-9)

    def test_hexany_rational_entry(self):
        r = m.score_melodic_rational(HEXANY_1357)
        self.assertEqual(len(r.scale), 6)
        # Gap classes: 84.47, 119.44, 2 x 231.17, 2 x 266.87 (cents).
        self.assertEqual(r.gap_entropy.gap_class_count, 4)
        expected = 2 * (1 / 6) * log2(6) + 2 * (1 / 3) * log2(3)
        self.assertAlmostEqual(r.gap_entropy.entropy_bits, expected, places=12)


if __name__ == "__main__":
    unittest.main()
