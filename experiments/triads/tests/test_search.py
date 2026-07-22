"""Goldens for the LOOP-001 batch search helpers (search.py).

The search itself is stochastic beyond its exhaustive phase, so what gets
pinned here is the deterministic machinery: descriptors, elite ordering,
mutation invariants, and the two structural facts the search relies on
(duality of CPS(n,k) vs CPS(n,n-k), and the diagonal for k = n/2).
"""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import scorer as sc  # noqa: E402
import search  # noqa: E402
from families.cps import cps_scale  # noqa: E402


class TestPrimeLimit(unittest.TestCase):
    def test_known_limits(self):
        self.assertEqual(search.prime_limit([1, 3, 5, 7]), 7)
        self.assertEqual(search.prime_limit([1, 3, 9, 27]), 3)
        self.assertEqual(search.prime_limit([1, 45, 135, 225, 19, 377]), 29)
        self.assertEqual(search.prime_limit([1]), 1)


class TestBalanceBucket(unittest.TestCase):
    def test_diagonal_and_sides(self):
        self.assertEqual(search.balance_bucket(8, 8), "diagonal")
        self.assertEqual(search.balance_bucket(31, 18), "strong_P")
        self.assertEqual(search.balance_bucket(18, 31), "strong_S")
        self.assertEqual(search.balance_bucket(21, 20), "near_P")
        self.assertEqual(search.balance_bucket(25, 20), "skew_P")

    def test_zero_side_is_degenerate(self):
        self.assertEqual(search.balance_bucket(46, 0), "degenerate_P")
        self.assertEqual(search.balance_bucket(0, 46), "degenerate_S")


class TestEliteOrdering(unittest.TestCase):
    def _rec(self, **kw):
        base = {"score_min": 5, "score_product": 25, "G": 0, "seeds": [1, 3, 5, 7]}
        return {**base, **kw}

    def test_min_score_dominates(self):
        self.assertTrue(search.is_better(self._rec(score_min=6),
                                         self._rec(score_min=5)))

    def test_product_breaks_min_ties(self):
        self.assertTrue(search.is_better(
            self._rec(score_product=30), self._rec(score_product=25)))

    def test_simpler_seeds_win_all_else_equal(self):
        simple = self._rec(seeds=[1, 3, 5, 7])
        gnarly = self._rec(seeds=[1, 3, 5, 377])
        self.assertTrue(search.is_better(simple, gnarly))
        self.assertFalse(search.is_better(gnarly, simple))


class TestMutationInvariants(unittest.TestCase):
    def test_seeds_stay_distinct_positive_and_sized(self):
        rng = random.Random(12345)
        cand = search.Candidate((1, 3, 5, 7, 9), 2)
        for _ in range(500):
            cand = search.mutate(cand, rng)
            self.assertEqual(len(cand.seeds), 5)
            self.assertEqual(len(set(cand.seeds)), 5, "seeds must stay distinct")
            self.assertTrue(all(s >= 1 for s in cand.seeds))
            self.assertEqual(list(cand.seeds), sorted(cand.seeds))


class TestStructuralFactsTheSearchRelieson(unittest.TestCase):
    """These are why the search covers asymmetric families at all."""

    def test_symmetric_family_sits_on_the_diagonal(self):
        # CPS(6,3): k == n/2, so it is self-inverse -> P == S exactly.
        r = sc.score(cps_scale((1, 3, 5, 7, 9, 11), 3))
        self.assertEqual(r.proportional, r.subcontrary)

    def test_asymmetric_pair_swaps_p_and_s_exactly(self):
        # CPS(n,k) inverts to CPS(n,n-k): the counts must swap exactly.
        for seeds, n, k in (((1, 3, 5, 7, 9), 5, 2),
                            ((1, 3, 5, 7, 9, 11), 6, 2)):
            with self.subTest(seeds=seeds, k=k):
                a = sc.score(cps_scale(seeds, k))
                b = sc.score(cps_scale(seeds, n - k))
                self.assertEqual((a.proportional, a.subcontrary),
                                 (b.subcontrary, b.proportional))
                self.assertNotEqual(a.proportional, a.subcontrary,
                                    "this pair should be OFF the diagonal")


class TestEvaluate(unittest.TestCase):
    def test_record_shape_and_provenance(self):
        rec = search.evaluate(search.Candidate((1, 3, 5, 7), 2))
        self.assertEqual(rec["family"], "CPS(4,2)")
        self.assertEqual(rec["cardinality"], 6)
        self.assertEqual((rec["P"], rec["S"]), (6, 6))  # v1.1.0 octave limit
        self.assertEqual(rec["balance"], "diagonal")
        self.assertEqual(rec["scorer_version"], sc.SCORER_VERSION)
        self.assertEqual(rec["convention"], sc.PRIMARY_CONVENTION)

    def test_degenerate_candidate_rejected(self):
        # k out of range yields no scale rather than an exception escaping.
        self.assertIsNone(search.evaluate(search.Candidate((1, 3), 5)))


if __name__ == "__main__":
    unittest.main()


class TestGeometricAxis(unittest.TestCase):
    """G is a diversity axis, not just a reported number (2026-07-21).

    Without it, a G-heavy scale shares a cell with a P/S-heavier one and is
    evicted by the min(P,S)-first elite rule before any report can see it.
    """

    def test_buckets(self):
        self.assertEqual(search.geometric_bucket(9, 9, 0), "G0")
        self.assertEqual(search.geometric_bucket(9, 9, 2), "G_low")
        self.assertEqual(search.geometric_bucket(5, 5, 3), "G_mid")
        self.assertEqual(search.geometric_bucket(5, 5, 4), "G_high")  # 0.4 is the edge
        self.assertEqual(search.geometric_bucket(5, 5, 6), "G_high")
        self.assertEqual(search.geometric_bucket(0, 0, 3), "G_only")

    def test_g_heavy_scale_gets_its_own_cell(self):
        rich = search.evaluate(search.Candidate((1, 3, 5, 9), 2))     # G-light
        geo = search.evaluate(search.Candidate((1, 3, 9, 81), 2))     # G-heavy
        self.assertGreater(geo["G"], rich["G"])
        self.assertNotEqual(search.bin_key(rich), search.bin_key(geo),
                            "G-heavy scales must not share a cell with "
                            "P/S-heavy ones, or they get evicted unseen")
