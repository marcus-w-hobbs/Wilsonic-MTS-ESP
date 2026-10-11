"""Unit tests for mur001.py (MUR-001) — corpus union, periodic-CF
convergents, exact monotonicity, the anchor-sweep representability census
(fixtures pinned to the MOS-LAT-001 receipt results/moslat001.json,
murchana_analysis fields), the scan-pad drift bound, and the statistics
helpers. Written BEFORE the first experiment run (LOG.md pre-registration,
2026-08-09).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mur001 as mu  # noqa: E402
import moslat001 as ml  # noqa: E402


def _noble(preamble):
    g = ml.noble_from_preamble(preamble)
    return g, g.conj()


def _representable_set(g, g_conj, n):
    sweep = mu.anchor_sweep(g, g_conj, n)
    return [b0 for b0, bit in zip(range(-n, n + 1), sweep["representable"])
            if bit == "1"], sweep


class TestCorpus(unittest.TestCase):
    def test_union_census(self):
        gens = mu.build_corpus()
        self.assertEqual(len(gens), 243)
        self.assertEqual(sum(1 for g in gens if g["corpus"] == "noble"), 27)
        self.assertEqual(sum(1 for g in gens if g["corpus"] == "mixed"), 216)
        values = {round(float(g["g"]), 12) for g in gens}
        self.assertEqual(len(values), 243)  # disjoint by CF-tail uniqueness

    def test_row_counts_match_prior_experiments(self):
        gens = mu.build_corpus()
        noble_rows = sum(len(mu.rows_for(g)) for g in gens
                         if g["corpus"] == "noble")
        mixed_rows = sum(len(mu.rows_for(g)) for g in gens
                         if g["corpus"] == "mixed")
        self.assertEqual(noble_rows, 97)   # MOS-LAT-001 step 2
        self.assertEqual(mixed_rows, 788)  # MOS-LAT-002


class TestConvergents(unittest.TestCase):
    def test_matches_moslat001_on_nobles(self):
        for preamble in ((), (2,), (1, 2), (2, 2)):
            self.assertEqual(
                mu.periodic_cf_convergents(preamble, (1,), 22),
                ml.cf_convergents(preamble, max_den=22))

    def test_silver_ratio(self):
        # [0;(2)*] = sqrt2 - 1: convergents 0/1(excluded), 1/2, 2/5, 5/12...
        conv = mu.periodic_cf_convergents((), (2,), 12)
        self.assertEqual(conv, {(1, 2), (2, 5), (5, 12)})


class TestMonotone(unittest.TestCase):
    def test_exact_criterion(self):
        g, gc = _noble(())      # conj -phi < 0
        self.assertTrue(mu.is_monotone(gc))
        g, gc = _noble((2,))    # conj (3+sqrt5)/2 > 1
        self.assertTrue(mu.is_monotone(gc))
        g, gc = _noble((1, 2))  # conj (5-sqrt5)/10 ~ 0.276 in (0,1)
        self.assertFalse(mu.is_monotone(gc))
        g, gc = _noble((2, 2))  # conj (7-sqrt5)/22 ~ 0.217 in (0,1)
        self.assertFalse(mu.is_monotone(gc))


class TestAnchorSweep(unittest.TestCase):
    """Fixtures pinned to results/moslat001.json murchana_analysis and
    hull_strays (receipts of 2026-07-28, exact arithmetic)."""

    def test_golden_monotone_all_representable(self):
        g, gc = _noble(())
        r_set, sweep = _representable_set(g, gc, 13)
        self.assertEqual(len(r_set), 27)
        self.assertEqual(sweep["intruder_counts"], [0] * 27)

    def test_g3_n11_receipt_pins(self):
        g, gc = _noble((1, 2))
        r_set, sweep = _representable_set(g, gc, 11)
        self.assertEqual(len(r_set), 15)  # receipt representable_count
        # receipt examples are a prefix of the representable set
        prefix = [-11, -9, -8, -6, -5, -4, -2, -1]
        self.assertEqual(r_set[:8], prefix)
        # anchor 0 fails with the single intruder b = 11
        idx0 = 11  # b0 = 0 at index N
        self.assertEqual(sweep["representable"][idx0], "0")
        self.assertNotIn(0, r_set)
        self.assertEqual(sweep["intruder_counts"][idx0], 1)  # single b = 11
        # direct check of the anchor-0 intruder
        seg = [ml.iota(b, g, gc) for b in range(11)]
        lo, hi = min(seg), max(seg)
        v = ml.iota(11, g, gc)
        self.assertTrue(lo <= v and v <= hi)

    def test_g4_n7_receipt_pins(self):
        g, gc = _noble((2, 2))
        r_set, sweep = _representable_set(g, gc, 7)
        self.assertEqual(r_set, [-7, -4, -2, 3, 5])  # receipt examples
        self.assertEqual(sweep["n_representable"], 5)
        self.assertFalse(sweep["contiguous"])
        self.assertEqual(sweep["interior_gap_values"], [2, 3, 5])

    def test_g4_n19_receipt_pins(self):
        g, gc = _noble((2, 2))
        r_set, sweep = _representable_set(g, gc, 19)
        self.assertEqual(len(r_set), 15)  # receipt representable_count
        prefix = [-19, -16, -14, -11, -9, -7, -4, -2]
        self.assertEqual(r_set[:8], prefix)

    def test_scan_pad_sufficient(self):
        """Doubling the pad must not change the census (drift bound)."""
        g, gc = _noble((2, 2))
        base = mu.anchor_sweep(g, gc, 7)
        original = mu.scan_pad
        try:
            mu.scan_pad = lambda cs, n: 2 * original(cs, n)
            wide = mu.anchor_sweep(g, gc, 7)
        finally:
            mu.scan_pad = original
        self.assertEqual(base["representable"], wide["representable"])
        self.assertEqual(base["intruder_counts"], wide["intruder_counts"])


class TestMelodicInvariance(unittest.TestCase):
    def test_golden_n5_triple_constant(self):
        scores = mu.anchor_scores(float(ml.noble_from_preamble(())), 5)
        self.assertTrue(scores["hmu0_ok"])
        self.assertEqual(len(scores["hmu0_distinct_triples"]), 1)
        self.assertEqual(len(scores["P"]["2"]), 11)
        self.assertEqual(len(scores["P"]["3"]), 11)


class TestStatisticsHelpers(unittest.TestCase):
    def test_auc_perfect_and_ties(self):
        self.assertEqual(mu.auc_score([2.0, 3.0], [1.0]), 1.0)
        self.assertEqual(mu.auc_score([1.0], [1.0]), 0.5)
        self.assertEqual(mu.auc_score([1.0, 2.0], [1.5, 3.0]), 0.25)

    def test_hmu3_delta(self):
        rhos = [1.0, 0.0, 0.5, 0.5]
        labels = [False, True, False, True]
        self.assertAlmostEqual(mu.hmu3_delta(rhos, labels), 0.5)

    def test_permutation_p_deterministic(self):
        rhos = [0.9, 0.1, 0.8, 0.2, 0.7, 0.3]
        labels = [False, True, False, True, False, True]
        strata = ["a", "a", "b", "b", "c", "c"]
        obs = mu.hmu3_delta(rhos, labels)
        p1 = mu.hmu3_permutation_p(rhos, labels, strata, obs,
                                   random.Random(mu.SEED), n_perm=199)
        p2 = mu.hmu3_permutation_p(rhos, labels, strata, obs,
                                   random.Random(mu.SEED), n_perm=199)
        self.assertEqual(p1, p2)
        self.assertTrue(0.0 < p1 <= 1.0)


if __name__ == "__main__":
    unittest.main()
