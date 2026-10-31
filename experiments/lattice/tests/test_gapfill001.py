"""Unit tests for gapfill001.py (GAPFILL-001). Written before the registered
run (LOG.md pre-registration 2026-10-27). Pins: Archytas's enharmonic as a
two-step mediant cascade, the epimoric facts the EPI pool rests on, the
arithmetic split making a proportional triad and depending only on the gap
ratio, the CS search reproducing Wilson and Grady's 14-tone 1-3-5-7-9
dekany (exactly 4 genus tones, one of them the other dekany) and Kraig's
1-3-7-9-15 dekany (no genus fill of 4 or fewer), the unique 12-tone parent
completion of the canonical dekany in 1, and the AM/HM inversion mirror.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gapfill001 as gf  # noqa: E402
from families.cps import cps_scale  # noqa: E402


def cents(xs):
    return [gf.cents_of(x) for x in xs]


class TestEpimoric(unittest.TestCase):
    def test_archytas_enharmonic_is_a_mediant_cascade(self):
        m1 = gf.split_point(F(1), F(4, 3), "MED")
        m2 = gf.split_point(m1, F(4, 3), "MED")
        self.assertEqual((m1, m2), (F(5, 4), F(9, 7)))
        self.assertEqual((m1, m2 / m1, F(4, 3) / m2), (F(5, 4), F(36, 35), F(28, 27)))

    def test_farey_neighbours_differ_by_an_epimore(self):
        for a, b in ((F(1), F(5, 4)), (F(5, 4), F(9, 7)), (F(9, 7), F(4, 3))):
            self.assertEqual(b.numerator * a.denominator - a.numerator * b.denominator, 1)
            r = b / a
            self.assertEqual(r.numerator - r.denominator, 1)

    def test_no_epimore_is_a_square_ratio(self):
        sq = lambda n: isqrt(n) ** 2 == n
        self.assertEqual([n for n in range(1, 200_000) if sq(n) and sq(n + 1)], [])

    def test_arithmetic_split_is_a_proportional_triad_and_ratio_only(self):
        for a, r in ((F(5, 4), F(8, 7)), (F(21, 16), F(8, 7)), (F(1), F(7, 6))):
            m = gf.split_point(a, a * r, "AM")
            self.assertEqual(m, (a + a * r) / 2)
            self.assertEqual(m / a, (1 + r) / 2)        # depends only on the gap ratio
            h = gf.split_point(a, a * r, "HM")
            self.assertEqual(h / a, 2 * r / (1 + r))    # the mirror of the AM split

    def test_epi_fill_brings_every_step_under_cap(self):
        hexany = list(cps_scale((1, 3, 5, 7), 2))
        for rule in ("AM", "HM"):
            added = gf.epi_fill(hexany, rule)
            self.assertIsNotNone(added)
            self.assertLessEqual(gf.max_step(sorted(cents(hexany + added))), gf.CAP)


class TestSearch(unittest.TestCase):
    def test_is_cs(self):
        self.assertTrue(gf.is_cs(sorted(cents(cps_scale((1, 3, 5, 7), 2)))))
        self.assertFalse(gf.is_cs([0.0, 200.0, 400.0, 500.0, 700.0, 900.0, 1100.0, 600.0]))

    def _min_genus_fill(self, seeds, k, max_add):
        d = list(cps_scale(seeds, k))
        pool = sorted(set(gf.genus(seeds)) - set(d))
        saved = (gf.CAP, gf.MIN_STEP, gf.N_SEARCH_MAX)
        gf.CAP, gf.MIN_STEP, gf.N_SEARCH_MAX = 1200.0, 0.0, len(d) + max_add
        try:
            got, _, out = gf.cs_search(cents(d), cents(pool))
        finally:
            gf.CAP, gf.MIN_STEP, gf.N_SEARCH_MAX = saved
        return d, got, out

    def test_wilson_grady_double_dekany(self):
        d, got, out = self._min_genus_fill((1, 3, 5, 7, 9), 3, 4)
        self.assertFalse(out)
        self.assertEqual(len(got), 4)
        union = sorted(set(cps_scale((1, 3, 5, 7, 9), 2)) | set(d))
        self.assertEqual(len(union), 14)
        self.assertTrue(gf.is_cs(sorted(cents(union))))

    def test_kraig_dekany_has_no_small_genus_fill(self):
        _, got, out = self._min_genus_fill((1, 3, 7, 9, 15), 2, 4)
        self.assertFalse(out)
        self.assertIsNone(got)

    def test_canonical_dekany_in_1_parent_completion(self):
        rows = gf.run_subset(("canonical", 0))
        r = next(r for r in rows if r["method"] == "PARENT-CS")
        self.assertEqual((r["subset"], r["ok"], r["n"], r["cs"]), ("dekany_in[in=1,out=none]", True, 12, True))
        self.assertEqual(r["in_eikosany"], 2)


class TestMirror(unittest.TestCase):
    def test_partner(self):
        self.assertEqual(gf.partner("hexany[in=9,out=11]"), "hexany[in=11,out=9]")
        self.assertEqual(gf.partner("dekany_in[in=1,out=none]"), "dekany_out[in=none,out=1]")
        self.assertEqual(gf.partner("dekany_out[in=none,out=1]"), "dekany_in[in=1,out=none]")

    def test_am_fill_mirrors_hm_fill_of_partner(self):
        rows = gf.run_subset(("canonical", 12)) + gf.run_subset(("canonical", 17))
        s = gf.mirror_check(rows)
        self.assertEqual((s["pairs"], s["steps_mirrored"], s["P_S_swapped_cs_propriety_equal"]), (2, 2, 2))


if __name__ == "__main__":
    unittest.main()
