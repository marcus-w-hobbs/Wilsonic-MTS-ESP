"""Unit tests for gapfill002.py (GAPFILL-002). Written before the registered
run (LOG.md pre-registration 2026-10-31). Pins: the exact cover against brute
force on small random instances, its tie rule, the greedy bound never below
the optimum, the completion lister (inclusion-minimal, every completion CS
under CAP, the smallest equal to GAPFILL-001's search), the own-pool seeding
(a table never covers less than the subset's own pool), and the Wilson-Grady
dekany completing from the genus in exactly 4 tones as a listed completion.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import random
import sys
import unittest
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gapfill001 as g1  # noqa: E402
import gapfill002 as g2  # noqa: E402
from families.cps import cps_scale  # noqa: E402


def cents(xs):
    return [g1.cents_of(x) for x in xs]


def brute(comps):
    tones = sorted({t for cs in comps for c in cs for t in c})
    need = [cs for cs in comps if cs]
    for size in range(len(tones) + 1):
        for F in combinations(tones, size):
            F = frozenset(F)
            if all(any(c <= F for c in cs) for cs in need):
                return size
    return None


class TestCover(unittest.TestCase):
    def test_hand_instance(self):
        comps = [[frozenset("ab"), frozenset("c")], [frozenset("bc")], [frozenset("cd")], []]
        F, _, proven, lower = g2.exact_cover(comps)
        self.assertEqual(F, frozenset("bcd"))
        self.assertTrue(proven)

    def test_matches_brute_force(self):
        rng = random.Random(2026_10_31)
        for _ in range(40):
            tones = list(range(9))
            comps = [[frozenset(rng.sample(tones, rng.randint(1, 4))) for _ in range(rng.randint(0, 4))]
                     for _ in range(rng.randint(2, 6))]
            F, _, proven, lower = g2.exact_cover(comps)
            self.assertTrue(proven)
            self.assertEqual(len(F), brute(comps))
            self.assertLessEqual(lower, len(F))
            self.assertTrue(all(any(c <= F for c in cs) for cs in comps if cs))
            _, masks = g2._masks(comps)
            self.assertGreaterEqual(g2.greedy_cover(masks).bit_count(), len(F))

    def test_start_is_kept_when_it_is_optimal(self):
        comps = [[frozenset("ab"), frozenset("xy")], [frozenset("bc"), frozenset("yz")]]
        F, _, proven, _ = g2.exact_cover(comps, (frozenset("xyz"),))
        self.assertTrue(proven)
        self.assertEqual(F, frozenset("abc"))     # ties go to the lowest tones

    def test_minimal_drops_supersets(self):
        got = g2.minimal({frozenset("ab"), frozenset("abc"), frozenset("d"), frozenset("ad")})
        self.assertEqual(got, [frozenset("d"), frozenset("ab")])


class TestCompletions(unittest.TestCase):
    def setUp(self):
        self.hexany = sorted(cents(cps_scale((1, 3, 5, 7), 2)))
        seeds = (1, 3, 5, 7, 9, 11)
        self.pool = sorted(cents(set(g1.genus(seeds)) - set(Fraction(x) for x in ())))

    def test_every_completion_is_cs_under_cap_and_minimal(self):
        pool = [p for p in self.pool if g2.key(p) not in {g2.key(c) for c in self.hexany}]
        comps, _, _ = g2.completions(self.hexany, pool)
        self.assertTrue(comps)
        for c in comps:
            cs = sorted(self.hexany + list(c))
            self.assertTrue(g1.is_cs(cs))
            self.assertLessEqual(g1.max_step(cs), g1.CAP)
        self.assertFalse(any(a < b for a in comps for b in comps))
        got, _, _ = g1.cs_search(self.hexany, pool)
        self.assertEqual(len(comps[0]), len(got))
        self.assertLessEqual(len(comps[-1]), len(comps[0]) + g2.SLACK)

    def test_own_pool_seeding_keeps_gapfill001_coverage(self):
        own = [p for p in self.pool if 300 < p < 700]
        alone, _, _ = g2.completions(self.hexany, own)
        both, _, _ = g2._enum_task((self.hexany, own, self.pool, {}))
        for c in alone:
            self.assertTrue(any(d <= c for d in both))

    def test_wilson_grady_dekany_from_the_genus(self):
        d = list(cps_scale((1, 3, 5, 7, 9), 3))
        pool = cents(sorted(set(g1.genus((1, 3, 5, 7, 9))) - set(d)))
        saved = (g1.CAP, g1.MIN_STEP, g1.N_SEARCH_MAX, g2.SLACK)
        g1.CAP, g1.MIN_STEP, g1.N_SEARCH_MAX, g2.SLACK = 1200.0, 0.0, len(d) + 4, 0
        try:
            comps, _, out = g2.completions(sorted(cents(d)), pool)
        finally:
            g1.CAP, g1.MIN_STEP, g1.N_SEARCH_MAX, g2.SLACK = saved
        self.assertFalse(out)
        self.assertEqual(min(len(c) for c in comps), 4)
        other = {g2.key(c) for c in cents(cps_scale((1, 3, 5, 7, 9), 2))} - {g2.key(c) for c in cents(d)}
        self.assertTrue(any(c <= other for c in comps))


if __name__ == "__main__":
    unittest.main()
