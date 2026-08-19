"""Unit tests for mur002.py (MUR-002) — corpus integrity of the
LatticingRagaScales transcription (S22, the 18 ragas, the grāmas), the
53-degree map against the figure's own numbers, rotation (mūrchanā),
tonic-anchored m4_proto, śruti-spelling snap, chain/EDO fit helpers, and
the transposition-invariance rail of the frozen anchored triad scorer.
Written BEFORE the first experiment run (LOG.md pre-registration,
2026-08-18). No hypothesis value is pinned here — tests check code, the
receipts adjudicate the predictions.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mur002 as mu  # noqa: E402


class TestCorpus(unittest.TestCase):
    def test_s22_is_sorted_22_with_unison(self):
        self.assertEqual(len(mu.S22), 22)
        self.assertEqual(mu.S22[0], F(1))
        self.assertEqual(list(mu.S22), sorted(mu.S22))
        self.assertEqual(len(set(mu.S22)), 22)
        for r in mu.S22:
            self.assertTrue(1 <= r < 2)

    def test_s22_rows(self):
        rows = {}
        for r in mu.S22:
            e3, e5 = mu.monzo35(r)
            rows.setdefault(e5, []).append(e3)
        self.assertEqual(sorted(rows[0]), list(range(-5, 7)))
        self.assertEqual(sorted(rows[1]), list(range(-2, 3)))
        self.assertEqual(sorted(rows[-1]), list(range(-1, 4)))

    def test_eighteen_ragas_seven_tones_with_sa(self):
        self.assertEqual(len(mu.RAGAS), 18)
        nums = sorted(r["num"] for r in mu.RAGAS)
        self.assertEqual(nums, list(range(1, 19)))
        for raga in mu.RAGAS:
            tones = raga["tones"]
            self.assertEqual(len(tones), 7, raga["name"])
            ratios = [t[1] for t in tones]
            self.assertIn(F(1), ratios)
            self.assertEqual(len(set(ratios)), 7)
            self.assertTrue(2 <= raga["page"] <= 19)

    def test_ratios_are_5_limit(self):
        for raga in mu.RAGAS:
            for _, r, _ in raga["tones"]:
                mu.monzo35(r)  # raises if not 3^a 5^b 2^c
        for r in mu.S22 + list(mu.SA) + list(mu.MA):
            mu.monzo35(r)

    def test_gramas(self):
        self.assertEqual(mu.SA, (F(1), F(10, 9), F(32, 27), F(4, 3),
                                 F(3, 2), F(5, 3), F(16, 9)))
        self.assertEqual(mu.MA, (F(1), F(10, 9), F(32, 27), F(4, 3),
                                 F(40, 27), F(5, 3), F(16, 9)))
        old_kafi = next(r for r in mu.RAGAS if r["name"] == "Old Kafi")
        self.assertEqual(mu.canonical(t[1] for t in old_kafi["tones"]),
                         mu.SA)

    def test_deg53_matches_transcribed_degrees(self):
        # the figure's own 53-degree numbers, read off the hexes
        for raga in mu.RAGAS:
            for label, r, deg in raga["tones"]:
                self.assertEqual(mu.deg53(r), deg, f"{raga['name']} {label}")
        for r, deg in mu.S22_DEG53:
            self.assertEqual(mu.deg53(r), deg)
        self.assertEqual(mu.deg53(F(135, 128)), 4)
        self.assertEqual(mu.deg53(F(405, 256)), 35)
        self.assertEqual(mu.deg53(F(1215, 1024)), 13)
        self.assertEqual(mu.deg53(F(3645, 2048)), 44)

    def test_s22_degrees_distinct(self):
        degs = [mu.deg53(r) for r in mu.S22]
        self.assertEqual(len(set(degs)), 22)
        self.assertEqual(degs, sorted(degs))  # 53 order = JI order


class TestRotation(unittest.TestCase):
    def test_rotate_identity_and_cycle(self):
        self.assertEqual(mu.rotate(mu.SA, 0), mu.SA)
        self.assertEqual(mu.rotate(mu.SA, 7), mu.SA)
        for k in range(7):
            rot = mu.rotate(mu.SA, k)
            self.assertEqual(rot[0], F(1))
            self.assertEqual(len(rot), 7)
            self.assertEqual(list(rot), sorted(rot))

    def test_rotate_ni_of_sa(self):
        # hand derivation in the pre-registration
        rot = mu.rotate(mu.SA, 6)
        self.assertEqual(rot, (F(1), F(9, 8), F(5, 4), F(4, 3), F(3, 2),
                               F(27, 16), F(15, 8)))

    def test_step_words(self):
        steps = mu.step_word(mu.SA)
        self.assertEqual(steps, (F(10, 9), F(16, 15), F(9, 8), F(9, 8),
                                 F(10, 9), F(16, 15), F(9, 8)))
        self.assertEqual(mu.coarse_word(steps), "TsTTTsT")
        self.assertEqual(mu.coarse_word(mu.step_word(mu.rotate(mu.SA, 6))),
                         "TTsTTTs")

    def test_word_rotation_membership(self):
        w = mu.coarse_word(mu.step_word(mu.SA))
        self.assertEqual(mu.word_rotation_index(w, "TTsTTTs"), 6)
        self.assertEqual(mu.word_rotation_index(w, "TsTTTsT"), 0)
        self.assertIsNone(mu.word_rotation_index(w, "TTTTTss"))


class TestM4Proto(unittest.TestCase):
    def test_tonic_consonances(self):
        proto = mu.m4_proto(mu.SA)
        # 4/3, 3/2, 5/3 are exact consonances with 1/1; 10/9, 32/27, 16/9 not
        self.assertEqual(proto["tonic_consonance_count"], 3)
        self.assertEqual(proto["coarse_word"], "TsTTTsT")
        self.assertEqual(len(proto["from_tonic"]), 7)
        self.assertEqual(proto["from_tonic"][0]["ratio"], "1")

    def test_all_rotations_distinct_words(self):
        words = {mu.m4_proto(mu.rotate(mu.SA, k))["step_word"]
                 for k in range(7)}
        self.assertEqual(len(words), 7)


class TestSpelling(unittest.TestCase):
    def test_sruti_snap(self):
        todi = next(r for r in mu.RAGAS if r["name"] == "Todi")
        drawn = mu.canonical(t[1] for t in todi["tones"])
        snapped = mu.sruti_spelled(drawn)
        self.assertIn(F(256, 243), snapped)
        self.assertNotIn(F(135, 128), snapped)
        self.assertTrue(set(snapped) <= set(mu.S22))
        self.assertEqual([mu.deg53(r) for r in snapped],
                         [mu.deg53(r) for r in drawn])

    def test_snap_is_identity_on_s22_subsets(self):
        self.assertEqual(mu.sruti_spelled(mu.SA), mu.SA)


class TestFitHelpers(unittest.TestCase):
    def test_best_offset_match_self(self):
        cents = mu.cents_of(mu.S22)
        self.assertEqual(mu.best_offset_match(cents, cents, 5.0), 22)

    def test_best_offset_match_shifted(self):
        a = (0.0, 100.0, 300.0)
        b = (50.0, 150.0, 350.0, 700.0)
        self.assertEqual(mu.best_offset_match(a, b, 1.0), 3)
        self.assertEqual(mu.best_offset_match(a, (0.0, 600.0), 1.0), 1)

    def test_edo_and_chain(self):
        self.assertEqual(len(mu.edo_cents(22)), 22)
        chain = mu.chain_cents(701.955, 22, -10)
        self.assertEqual(len(chain), 22)
        self.assertEqual(len(mu.edo_image(mu.S22, 53)), 22)

    def test_three_gap_identity(self):
        # a genuine rank-1 3-gap set satisfies L = M + S
        chain = mu.chain_cents(701.955000865, 22, -10)
        gaps = mu.gap_classes(chain, 0.5)
        self.assertEqual(len(gaps), 3)
        self.assertTrue(mu.three_gap_identity(gaps, 0.01))
        # S22 has 3 gap classes but the identity fails by a schisma
        gaps22 = mu.gap_classes(mu.cents_of(mu.S22), 0.5)
        self.assertEqual(len(gaps22), 3)
        self.assertFalse(mu.three_gap_identity(gaps22, 0.01))
        self.assertTrue(mu.three_gap_identity(gaps22, 2.0))


class TestScorerRail(unittest.TestCase):
    """Transposition invariance of the frozen anchored scorer (a theorem
    of the convention; the runner relies on it for H-R3)."""

    def test_exact_and_tempered_invariance_on_synthetic(self):
        scale = (F(1), F(9, 8), F(5, 4), F(4, 3), F(3, 2), F(5, 3), F(15, 8))
        base_exact = mu.triad_counts_exact(scale)
        base_temp = mu.triad_counts_tempered(mu.cents_of(scale), 3.0)
        for k in range(1, 7):
            rot = mu.rotate(scale, k)
            self.assertEqual(mu.triad_counts_exact(rot), base_exact)
            self.assertEqual(
                mu.triad_counts_tempered(mu.cents_of(rot), 3.0), base_temp)


class TestDeterminism(unittest.TestCase):
    def test_scale_row_is_json_stable(self):
        import json
        r1 = json.dumps(mu.scale_row("SA", "sa_grama", mu.SA, 0,
                                     epsilons=(2.0,)), sort_keys=True)
        r2 = json.dumps(mu.scale_row("SA", "sa_grama", mu.SA, 0,
                                     epsilons=(2.0,)), sort_keys=True)
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
