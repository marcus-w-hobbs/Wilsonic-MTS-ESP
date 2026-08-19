"""Unit tests for subsetmel000.py (SUBSET-MEL-000) — enumeration of the 72
embedded CPS subsets of an eikosany, their Johnson-graph adjacency, the
inversion/transposition identities pre-registered as H-SM1, the deterministic
seed-selection rule, the ordering keys and the rank statistics. Written BEFORE
the first experiment run (LOG.md pre-registration, 2026-08-18).

Goldens come from LAT-MEL-001 receipts (results/latmel001.jsonl) — the
hexany rows there are the same scales up to transposition.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from itertools import combinations
from math import prod
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import subsetmel000 as sm  # noqa: E402

CLASSIC = (1, 3, 5, 7, 9, 11)
FLAGSHIP = (1, 7, 9, 11, 15, 29)


class TestSeedSelection(unittest.TestCase):
    def test_fixed_seeds(self):
        self.assertEqual(sm.CLASSIC, CLASSIC)
        self.assertEqual(sm.FLAGSHIP, FLAGSHIP)

    def test_further_seeds_rule(self):
        further = sm.further_cs_seeds(sm.CSEIK_RESULTS, exclude=(FLAGSHIP,), n=3)
        self.assertEqual(further, ((13, 17, 21, 23, 25, 27),
                                   (1, 3, 13, 21, 23, 25),
                                   (1, 3, 11, 13, 25, 27)))

    def test_seed_set_is_five_and_ordered(self):
        seeds = sm.seed_sets()
        self.assertEqual(len(seeds), 5)
        self.assertEqual(seeds[0], CLASSIC)
        self.assertEqual(seeds[1], FLAGSHIP)
        self.assertEqual(len(set(seeds)), 5)


class TestEnumeration(unittest.TestCase):
    def setUp(self):
        self.subs = sm.enumerate_subsets(CLASSIC)
        self.by_kind = {}
        for s in self.subs:
            self.by_kind.setdefault(s.kind, []).append(s)

    def test_seventy_two_with_breakdown(self):
        self.assertEqual(len(self.subs), 72)
        counts = {k: len(v) for k, v in self.by_kind.items()}
        self.assertEqual(counts, {"dekany_in": 6, "dekany_out": 6,
                                  "hexany": 30, "tetrad_in": 15,
                                  "tetrad_out": 15})
        self.assertEqual(6 + 6 + 30 + 15 + 15, 72)

    def test_tone_counts(self):
        expected = {"dekany_in": 10, "dekany_out": 10, "hexany": 6,
                    "tetrad_in": 4, "tetrad_out": 4}
        for s in self.subs:
            self.assertEqual(len(s.tones), expected[s.kind], s.name)
            self.assertEqual(len(s.index_sets), expected[s.kind], s.name)

    def test_names_unique_and_deterministic(self):
        names = [s.name for s in self.subs]
        self.assertEqual(len(set(names)), 72)
        again = [s.name for s in sm.enumerate_subsets(CLASSIC)]
        self.assertEqual(names, again)

    def test_dekany_in_is_x_times_cps52(self):
        for s in self.by_kind["dekany_in"]:
            (x,) = s.fixed_in
            rest = tuple(v for v in CLASSIC if v != x)
            expected = sm.canonical_rational_scale(
                x * prod(c) for c in combinations(rest, 2))
            self.assertEqual(s.tones, expected)

    def test_dekany_out_is_cps53_of_rest(self):
        for s in self.by_kind["dekany_out"]:
            (x,) = s.fixed_out
            rest = tuple(v for v in CLASSIC if v != x)
            expected = sm.canonical_rational_scale(
                prod(c) for c in combinations(rest, 3))
            self.assertEqual(s.tones, expected)

    def test_all_tones_are_eikosany_tones(self):
        eik = set(sm.cps_scale(CLASSIC, 3))
        for s in self.subs:
            self.assertTrue(set(s.tones) <= eik, s.name)


class TestJohnsonAdjacency(unittest.TestCase):
    def setUp(self):
        self.subs = sm.enumerate_subsets(CLASSIC)
        self.idx = {s.name: s for s in self.subs}
        self.shared = sm.shared_tone_matrix(self.subs)

    def test_matrix_shape_and_diagonal(self):
        self.assertEqual(len(self.shared), 72)
        for i, s in enumerate(self.subs):
            self.assertEqual(len(self.shared[i]), 72)
            self.assertEqual(self.shared[i][i], len(s.tones))

    def test_in_x_disjoint_from_out_x(self):
        for x in CLASSIC:
            a = set(self.idx[sm.subset_name("dekany_in", (x,), ())].tones)
            b = set(self.idx[sm.subset_name("dekany_out", (), (x,))].tones)
            self.assertEqual(a & b, set())

    def test_in_x_cap_in_y_is_tetrad_in(self):
        for x, y in combinations(CLASSIC, 2):
            a = set(self.idx[sm.subset_name("dekany_in", (x,), ())].tones)
            b = set(self.idx[sm.subset_name("dekany_in", (y,), ())].tones)
            t = set(self.idx[sm.subset_name("tetrad_in", (x, y), ())].tones)
            self.assertEqual(a & b, t)

    def test_in_x_cap_out_y_is_hexany(self):
        for x in CLASSIC:
            for y in CLASSIC:
                if x == y:
                    continue
                a = set(self.idx[sm.subset_name("dekany_in", (x,), ())].tones)
                b = set(self.idx[sm.subset_name("dekany_out", (), (y,))].tones)
                h = set(self.idx[sm.subset_name("hexany", (x,), (y,))].tones)
                self.assertEqual(a & b, h)

    def test_matrix_is_seed_independent(self):
        other = sm.shared_tone_matrix(sm.enumerate_subsets(FLAGSHIP))
        self.assertEqual(self.shared, other)


class TestInversionAndTransposition(unittest.TestCase):
    """The algebra behind H-SM1 (pre-registered symmetry)."""

    def test_dekany_in_out_are_inversions(self):
        for seeds in (CLASSIC, FLAGSHIP):
            subs = {s.name: s for s in sm.enumerate_subsets(seeds)}
            for x in seeds:
                a = subs[sm.subset_name("dekany_in", (x,), ())].tones
                b = subs[sm.subset_name("dekany_out", (), (x,))].tones
                self.assertTrue(sm.is_inversion_pair(a, b), x)

    def test_tetrad_in_out_are_inversions(self):
        subs = {s.name: s for s in sm.enumerate_subsets(CLASSIC)}
        for x, y in combinations(CLASSIC, 2):
            a = subs[sm.subset_name("tetrad_in", (x, y), ())].tones
            b = subs[sm.subset_name("tetrad_out", (), (x, y))].tones
            self.assertTrue(sm.is_inversion_pair(a, b))

    def test_hexany_pairs_are_transpositions(self):
        subs = {s.name: s for s in sm.enumerate_subsets(CLASSIC)}
        for x, y in combinations(CLASSIC, 2):
            a = subs[sm.subset_name("hexany", (x,), (y,))].tones
            b = subs[sm.subset_name("hexany", (y,), (x,))].tones
            self.assertEqual(sm.transposition_class(a), sm.transposition_class(b))
            self.assertNotEqual(a, b)

    def test_is_inversion_pair_negative(self):
        a = sm.canonical_rational_scale([1, Fraction(9, 8), Fraction(5, 4)])
        b = sm.canonical_rational_scale([1, Fraction(9, 8), Fraction(4, 3)])
        self.assertFalse(sm.is_inversion_pair(a, b))


class TestEvaluate(unittest.TestCase):
    """Goldens against LAT-MEL-001 receipts (hexany rows are the same scale
    classes up to transposition; melodic scores and P=S transposition-
    invariant)."""

    def setUp(self):
        self.subs = {s.name: s for s in sm.enumerate_subsets(CLASSIC)}

    def _hex(self, x, y):
        return sm.evaluate_subset(CLASSIC, self.subs[sm.subset_name(
            "hexany", (x,), (y,))])

    def test_hexany_1357_via_9_in_11_out(self):
        row = self._hex(9, 11)  # 9 * CPS(4,2){1,3,5,7}
        self.assertEqual(row["kind"], "hexany")
        self.assertEqual(row["cps_seeds"], [1, 3, 5, 7])
        self.assertEqual(row["m3_class"], "strictly_proper")
        self.assertTrue(row["m2_is_cs"])
        self.assertTrue(row["exact_cs"])
        self.assertEqual(row["m1_gap_classes"], 4)
        self.assertEqual(row["harmonic_exact"]["P"], 6)
        self.assertEqual(row["harmonic_exact"]["S"], 6)
        self.assertEqual(row["cardinality"], 6)
        self.assertAlmostEqual(row["gap_classes_per_n"], 4 / 6)

    def test_hexany_1359_via_7_in_11_out_not_cs(self):
        row = self._hex(7, 11)  # 7 * CPS(4,2){1,3,5,9}
        self.assertEqual(row["cps_seeds"], [1, 3, 5, 9])
        self.assertFalse(row["m2_is_cs"])
        self.assertFalse(row["exact_cs"])
        self.assertEqual(row["m3_class"], "proper")
        self.assertEqual(row["harmonic_exact"]["P"], 9)

    def test_hexany_3_5_7_11_via_1_in_9_out(self):
        row = self._hex(1, 9)
        self.assertEqual(row["cps_seeds"], [3, 5, 7, 11])
        self.assertEqual(row["harmonic_exact"]["P"], 2)
        self.assertEqual(row["m3_class"], "improper")

    def test_tempered_fields_and_survival(self):
        row = self._hex(9, 11)
        for eps in ("2.0", "3.0"):
            h = row["harmonic_tempered"][eps]
            self.assertIn("P", h)
            self.assertIn("balance", h)
            self.assertGreaterEqual(h["survival_P"], 1.0)
        self.assertEqual(row["harmonic_exact"]["balance"], "diagonal")

    def test_step_word_matches_gap_classes(self):
        row = self._hex(9, 11)
        self.assertEqual(len(row["step_word"]), 6)
        self.assertEqual(len(set(row["step_word"])), row["m1_gap_classes"])

    def test_dekany_row_shape(self):
        s = self.subs[sm.subset_name("dekany_in", (9,), ())]
        row = sm.evaluate_subset(CLASSIC, s)
        self.assertEqual(row["cardinality"], 10)
        self.assertEqual(row["cps_seeds"], [1, 3, 5, 7, 11])
        self.assertEqual(row["cps_k"], 2)
        self.assertEqual(len(row["step_word"]), 10)
        self.assertIsInstance(row["exact_cs_violations"], int)


class TestStepWord(unittest.TestCase):
    def test_diatonic(self):
        cents = (0.0, 200.0, 400.0, 500.0, 700.0, 900.0, 1100.0)
        self.assertEqual(sm.step_word(cents), "bbabbba")

    def test_single_class(self):
        cents = tuple(100.0 * i for i in range(12))
        self.assertEqual(sm.step_word(cents), "a" * 12)


class TestOrderingsAndStats(unittest.TestCase):
    def test_spearman_perfect_and_reversed(self):
        self.assertAlmostEqual(sm.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(sm.spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)

    def test_spearman_ties_average_ranks(self):
        # x has a tie; still well-defined and in [-1, 1]
        rho = sm.spearman([1, 1, 2, 3], [1, 2, 3, 4])
        self.assertTrue(-1.0 <= rho <= 1.0)
        self.assertGreater(rho, 0.9)

    def test_spearman_constant_is_zero(self):
        self.assertEqual(sm.spearman([1, 1, 1], [1, 2, 3]), 0.0)

    def test_propriety_rank(self):
        self.assertLess(sm.PROPRIETY_RANK["strictly_proper"],
                        sm.PROPRIETY_RANK["proper"])
        self.assertLess(sm.PROPRIETY_RANK["proper"],
                        sm.PROPRIETY_RANK["improper"])

    def test_ordering_keys_sort_direction(self):
        rows = [
            {"name": "a", "gap_classes_per_n": 0.5, "m3_class": "improper",
             "m3_violations": 2, "exact_cs_violations": 3,
             "harmonic_exact": {"P": 4, "S": 4},
             "harmonic_tempered": {"3.0": {"P": 5, "S": 5}}},
            {"name": "b", "gap_classes_per_n": 0.4, "m3_class": "proper",
             "m3_violations": 0, "exact_cs_violations": 0,
             "harmonic_exact": {"P": 1, "S": 1},
             "harmonic_tempered": {"3.0": {"P": 1, "S": 1}}},
        ]
        self.assertEqual([r["name"] for r in sm.order_rows(rows, "melodic")],
                         ["b", "a"])
        self.assertEqual([r["name"] for r in sm.order_rows(rows, "harmonic")],
                         ["a", "b"])
        self.assertEqual([r["name"] for r in sm.order_rows(rows, "cs")],
                         ["b", "a"])

    def test_orderings_registry(self):
        self.assertEqual(tuple(sm.ORDERINGS), ("melodic", "harmonic", "cs"))


if __name__ == "__main__":
    unittest.main()
