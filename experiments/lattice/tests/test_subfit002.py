"""Unit tests for subfit002.py (SUBFIT-002). Written BEFORE the first run
(LOG.md pre-registration 2026-10-14). Pins: the capped predicate reduces
to SUBFIT-001's evaluate when the cap is huge and never counts more than
it; the cap-20 N = 11 chain coincidence (124.23 cents keeps one hexany
with tones 16 cents off) disappears under cap 10; the registered N = 41
level (351.444 keeps 14 hexanies and 2 dekanies within 9.5 cents under
both caps); the search task tags its cap; the verdict helpers on
synthetic rows.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import subfit001 as sf  # noqa: E402
import subfit002 as s2  # noqa: E402


class TestPredicate(unittest.TestCase):
    def test_huge_cap_equals_subfit001(self):
        for gc, n in ((351.32, 17), (124.23, 11)):
            a = sf.evaluate(gc, n)
            b = s2.evaluate_capped(gc, n, 1e9)
            self.assertEqual((a["hex"], a["dek"], a["tet"], a["triads"], a["mode"]), (b["hex"], b["dek"], b["tet"], b["triads"], b["mode"]))

    def test_cap_never_counts_more(self):
        for gc, n in ((350.756, 26), (317.126, 24)):
            a = sf.evaluate(gc, n)
            for cap in (20.0, 10.0):
                b = s2.evaluate_capped(gc, n, cap)
                self.assertLessEqual(b["hex"] + b["dek"], a["hex"] + a["dek"])
                self.assertLessEqual(b["max_err_kept"], cap)

    def test_n11_coincidence_dies_under_cap10(self):
        a = s2.evaluate_capped(124.23, 11, 20.0)
        b = s2.evaluate_capped(124.23, 11, 10.0)
        self.assertEqual(a["hex"], 1)
        self.assertGreater(a["max_err_kept"], 10.0)
        self.assertEqual(b["hex"], 0)

    def test_registered_n41_level(self):
        for cap in (20.0, 10.0):
            r = s2.evaluate_capped(351.444, 41, cap)
            self.assertEqual((r["hex"], r["dek"]), (14, 2))
            self.assertLessEqual(r["max_err_kept"], 9.55)


class TestSearchTask(unittest.TestCase):
    def test_tags_cap_and_uses_it(self):
        r = s2.search_task((10.0, 11))
        self.assertEqual(r["cap"], 10.0)
        self.assertEqual(r["N"], 11)
        self.assertLessEqual(r["free"]["max_err_kept"], 10.0)
        self.assertIn("mos", r)


def _row(cap, n, g, hx, dk, tt, tri, err=4.5, level=False, mos=None, mode=0):
    free = {"g": g, "hex": hx, "dek": dk, "tet": tt, "triads": tri, "max_err_kept": err, "mode": mode, "assign": [], "playable": []}
    return {"cap": cap, "N": n, "free": free, "free_is_level": level, "mos": mos}


def _mos(g, hx, dk, tri, err=5.0):
    return {"g": g, "hex": hx, "dek": dk, "tet": hx, "triads": tri, "max_err_kept": err, "mode": 0, "assign": [], "playable": []}


def _staircase(cap, table):
    rows = []
    for (a, b), (g, hx, dk, tt, (t0, t1), err) in sorted(table.items()):
        for n in range(a, b + 1):
            rows.append(_row(cap, n, g, hx, dk, tt, t0, err=err if err is not None else 5.0))
    return rows


class TestVerdicts(unittest.TestCase):
    def test_tables(self):
        rows = _staircase(20.0, s2._T20) + _staircase(10.0, s2._T10)
        self.assertTrue(s2.verdict_table(rows, 20.0, s2._T20)["kept"])
        self.assertTrue(s2.verdict_table(rows, 10.0, s2._T10)["kept"])
        rows[0]["free"]["g"] += 0.02
        v = s2.verdict_table(rows, 20.0, s2._T20)
        self.assertFalse(v["kept"])
        self.assertTrue(any("N=11" in f for f in v["failures"]))

    def test_p_t_a(self):
        rows = _staircase(20.0, s2._T20) + _staircase(10.0, s2._T10)
        self.assertTrue(s2.verdict_p_t_a(rows)["kept"])
        by = s2._by_cap(rows)
        by[10.0][37]["free"]["hex"] = 12   # cap 10 at N=37 now matches cap 20: the difference is gone
        by[10.0][37]["free"]["dek"] = 2
        by[10.0][37]["free"]["g"] = 350.76
        by[10.0][37]["free"]["tet"] = 12
        by[10.0][37]["free"]["triads"] = 70
        self.assertFalse(s2.verdict_p_t_a(rows)["kept"])

    def test_p_t_b(self):
        rows = _staircase(20.0, s2._T20) + _staircase(10.0, s2._T10)
        self.assertTrue(s2.verdict_p_t_b(rows)["kept"])
        s2._by_cap(rows)[10.0][20]["free"]["hex"] = 4
        v = s2.verdict_p_t_b(rows)
        self.assertFalse(v["kept"])
        self.assertTrue(any("before 26" in f for f in v["failures"]))

    def test_p_t_c_and_d(self):
        rows = []
        for cap in s2.CAPS:
            for n in range(11, 73):
                mos = None
                if n == 31:
                    mos = _mos(116.68, 6, 0, 64)
                elif n in (41, 58):
                    mos = _mos(351.44, 14, 2, 88, 9.5)
                elif n in (46, 65):
                    mos = _mos(443.13, 12, 2, 70)
                elif n == 53:
                    mos = _mos(497.77, 16, 2, 76, 4.2)
                elif n == 72:
                    mos = _mos(483.28, 20, 4, 100, 8.0)
                level = n in s2.PREDICTIONS["P-T-C"]["levels"][cap]
                rows.append(_row(cap, n, 351.44, 14, 2, 14, 88, level=level, mos=mos))
        self.assertTrue(s2.verdict_p_t_c(rows)["kept"])
        self.assertTrue(s2.verdict_p_t_d(rows)["kept"])
        s2._by_cap(rows)[20.0][40]["mos"] = _mos(351.44, 14, 2, 88, 9.5)   # a 40-note level now beats the floor
        self.assertFalse(s2.verdict_p_t_d(rows)["kept"])
        s2._by_cap(rows)[10.0][24]["free_is_level"] = False
        self.assertFalse(s2.verdict_p_t_c(rows)["kept"])


if __name__ == "__main__":
    unittest.main()
