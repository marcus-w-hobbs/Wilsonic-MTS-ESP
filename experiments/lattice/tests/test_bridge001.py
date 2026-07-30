"""Unit tests for bridge001.py (BRIDGE-001) — EG4 tesseract construction,
comma enumeration, monotonicity filter, integer nullspace/HNF machinery,
minimax tuning, and the murchana anchor sweep. Written BEFORE the first
experiment run (LOG.md pre-registration, 2026-07-29).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bridge001 as br  # noqa: E402


class TestEG4(unittest.TestCase):
    def test_sixteen_formal_vertices(self):
        self.assertEqual(len(br.VERTICES), 16)

    def test_eight_distinct_tones_are_divisors_of_105(self):
        products = sorted(t["product"] for t in br.TONES)
        self.assertEqual(products, [1, 3, 5, 7, 15, 21, 35, 105])

    def test_pitch_order(self):
        ratios = [br.frac_str(t["ratio"]) for t in br.TONES]
        self.assertEqual(ratios, ["1/1", "35/32", "5/4", "21/16",
                                  "3/2", "105/64", "7/4", "15/8"])

    def test_every_vertex_product_is_a_distinct_tone(self):
        keys = {t["product"] for t in br.TONES}
        for v in br.VERTICES:
            self.assertIn(v["product"], keys)


class TestCommaEnumeration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.commas = br.enumerate_commas()

    def test_named_commas_included(self):
        got = set(self.commas)
        for s in br.NAMED_COMMAS:
            self.assertIn(br.monzo_of(Fraction(s)), got)

    def test_all_in_bounds_and_primitive(self):
        from math import gcd
        for m in self.commas:
            c = br.cents_of(m)
            self.assertGreater(c, 0.0)
            self.assertLess(c, br.COMMA_MAX_CENTS)
            self.assertLessEqual(br.tenney_log2(m), br.TENNEY_MAX_LOG2)
            g = gcd(gcd(abs(m[0]), abs(m[1])), gcd(abs(m[2]), abs(m[3])))
            self.assertEqual(g, 1)

    def test_larger_than_named_list(self):
        self.assertGreater(len(self.commas), 9)


class TestVals(unittest.TestCase):
    def test_patent_12(self):
        self.assertEqual(br.patent_val(12), (12, 19, 28, 34))

    def test_patent_31_matches_wilson(self):
        self.assertEqual(br.patent_val(31), (31, 49, 72, 87))

    def test_meantone_comma_killed_by_12_patent(self):
        c = br.monzo_of(Fraction(81, 80))
        self.assertEqual(br.vdot(br.patent_val(12), c), 0)

    def test_neighborhood_size(self):
        self.assertEqual(len(br.vals_for(12)), 27)


class TestMonotonicity(unittest.TestCase):
    def test_12_patent_monotone_injective(self):
        mono = br.monotonicity((12, 19, 28, 34))
        self.assertTrue(mono["monotone"])
        self.assertEqual(mono["degrees"], [0, 2, 4, 5, 7, 9, 10, 11])
        self.assertEqual(mono["collisions"], [])

    def test_9_patent_ties_21_20(self):
        # v(21/20) = 0 at the 9-patent: 5/4 and 21/16 share a degree
        mono = br.monotonicity((9, 14, 21, 25))
        self.assertTrue(mono["monotone"])
        commas = {c["comma"] for c in mono["collisions"]}
        self.assertIn("21/20", commas)

    def test_inversion_rejected(self):
        # a5 = patent+1 at N=9 makes v(21/20) = -1: 21/16 below 5/4
        mono = br.monotonicity((9, 14, 22, 25))
        self.assertFalse(mono["monotone"])
        pairs = [v["pair"] for v in mono["violations"]]
        self.assertIn(["5/4", "21/16"], pairs)


class TestLinearAlgebra(unittest.TestCase):
    def test_meantone_mapping(self):
        c = br.monzo_of(Fraction(81, 80))
        k = br.monzo_of(Fraction(126, 125))
        basis = br.nullspace_saturated([c, k])
        self.assertEqual(len(basis), 2)
        m = br.hnf_mapping(basis)
        for row in m:
            self.assertEqual(sum(a * b for a, b in zip(row, c)), 0)
            self.assertEqual(sum(a * b for a, b in zip(row, k)), 0)
        self.assertEqual(m[0][0], 1)       # octave period
        self.assertEqual(m[1][0], 0)       # generator is 2-free
        combo = br.val_combo((12, 19, 28, 34), m)
        self.assertIsNotNone(combo)
        alpha, _beta = combo
        self.assertEqual(alpha, 12)

    def test_miracle_mapping_and_combo(self):
        c = br.monzo_of(Fraction(225, 224))
        k = br.monzo_of(Fraction(1029, 1024))
        m = br.hnf_mapping(br.nullspace_saturated([c, k]))
        combo = br.val_combo((21, 33, 49, 59), m)
        self.assertIsNotNone(combo)
        self.assertEqual(combo[0] * m[0][0], 21)

    def test_val_combo_rejects_unsupported(self):
        c = br.monzo_of(Fraction(81, 80))
        k = br.monzo_of(Fraction(126, 125))
        m = br.hnf_mapping(br.nullspace_saturated([c, k]))
        # 22-patent does not support meantone (v(81/80) = 1)
        self.assertIsNone(br.val_combo((22, 35, 51, 62), m))


class TestMinimax(unittest.TestCase):
    def test_meantone_error_band(self):
        c = br.monzo_of(Fraction(81, 80))
        k = br.monzo_of(Fraction(126, 125))
        mm = br.hnf_mapping(br.nullspace_saturated([c, k]))
        _g, err = br.minimax_generator(mm)
        # septimal meantone, pure octaves: a few cents, deterministic
        self.assertLess(err, 7.0)
        self.assertGreater(err, 1.0)

    def test_miracle_value(self):
        # hand-derived pre-run: minimax at the e3 = e5 crossing,
        # G = 1515.6413/13 = 116.5878c-equivalent, max error 2.428c
        c = br.monzo_of(Fraction(225, 224))
        k = br.monzo_of(Fraction(1029, 1024))
        mm = br.hnf_mapping(br.nullspace_saturated([c, k]))
        g, err = br.minimax_generator(mm)
        self.assertAlmostEqual(err, 2.4284, places=3)
        self.assertAlmostEqual(g % (1200.0 / mm[0][0]), 116.5878, places=3)


class TestHostReceipt(unittest.TestCase):
    def test_miracle_21_anchor_sweep(self):
        c = br.monzo_of(Fraction(225, 224))
        k = br.monzo_of(Fraction(1029, 1024))
        mm = br.hnf_mapping(br.nullspace_saturated([c, k]))
        g, _ = br.minimax_generator(mm)
        mono = br.monotonicity((21, 33, 49, 59))
        host = br.host_receipt(mm, g, 21, mono["degrees"])
        self.assertEqual(host["chain_span"], 16)
        self.assertFalse(host["contained_at_anchor0"])
        self.assertTrue(host["contained"])
        lo, hi = host["anchor_interval"]
        self.assertLessEqual(lo, host["anchor_used"])
        self.assertLessEqual(host["anchor_used"], hi)
        self.assertIn(host["host_step_classes"], (1, 2, 3))

    def test_meantone_12_not_contained(self):
        # 35/32 needs 14 fifths: the EG4 chain span (16) exceeds 12
        c = br.monzo_of(Fraction(81, 80))
        k = br.monzo_of(Fraction(126, 125))
        mm = br.hnf_mapping(br.nullspace_saturated([c, k]))
        g, _ = br.minimax_generator(mm)
        mono = br.monotonicity((12, 19, 28, 34))
        host = br.host_receipt(mm, g, 12, mono["degrees"])
        self.assertEqual(host["chain_span"], 16)
        self.assertFalse(host["contained"])


class TestBases(unittest.TestCase):
    def test_hexany_base_is_v110_six_six(self):
        bases = br.subset_bases()
        self.assertEqual((bases["hexany"].proportional,
                          bases["hexany"].subcontrary), (6, 6))


if __name__ == "__main__":
    unittest.main()
