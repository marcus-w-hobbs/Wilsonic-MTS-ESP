"""Unit tests for gold001.py (GOLD-001). Written BEFORE the first run
(LOG.md pre-registration 2026-10-13). Pins: the exact level intervals
against the scale-tree walk, the lattice list (3 + 42 subsets), the
best-window count on registered hexany cases (golden 193.993 at N = 22
keeps 12), the MOS-only count fit at hexany N = 25 (>= 12) and N = 15
(>= 8), and the verdict helpers on synthetic rows.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cpsfit001 as c1  # noqa: E402
import cpsfit002 as c2  # noqa: E402
import gold001 as g1  # noqa: E402
import gold002 as g2  # noqa: E402


class TestLevels(unittest.TestCase):
    def test_level_intervals_match_scale_tree(self):
        for n in (5, 7, 12, 19, 22, 25):
            ivs = g1.level_intervals(n)
            for k in range(1, 400):
                g = k / 800.0 + 1e-7   # off the rationals: on a boundary the walk and the open intervals differ
                inside = any(lo < g < hi for lo, hi in ivs)
                self.assertEqual(inside, n in g2.levels_of(g, max_n=n), f"N={n} g={g}")

    def test_known_levels(self):
        self.assertTrue(g1.is_level(7, 0.58))     # a fifth has a 7-note level
        self.assertTrue(g1.is_level(12, 0.58))
        self.assertFalse(g1.is_level(8, 0.58))
        self.assertTrue(g1.is_level(25, 193.993 / 1200))


class TestLattices(unittest.TestCase):
    def test_list(self):
        lats = g1.lattices()
        self.assertEqual(len(lats), 45)
        self.assertEqual([l[0] for l in lats[:3]], ["hexany", "eg4", "dek52"])
        kinds = [l[1] for l in lats[3:]]
        self.assertEqual(kinds.count("hexany"), 30)
        self.assertEqual(kinds.count("dekany_in"), 6)
        self.assertEqual(kinds.count("dekany_out"), 6)


class TestCounts(unittest.TestCase):
    def setUp(self):
        self.tones = c1.LATTICES["hexany"]
        self.tc = [c1.cents_of(t) for t in self.tones]
        self.triads = c2.prep_triads(self.tones)

    def test_best_window_registered_cases(self):
        cnt, te, s, ks = g1.best_window(self.tc, self.triads, 193.993, 22)
        self.assertEqual(cnt, 12)
        self.assertLess(te, 4.0)
        cnt2, *_ = g1.best_window(self.tc, self.triads, 317.17, 15)
        self.assertEqual(cnt2, 8)
        self.assertIsNone(g1.best_window(self.tc, self.triads, 100.0, 5))

    def test_free_mos_hexany(self):
        fm25 = g1.fit_count_mos(self.tones, 25)
        self.assertIsNotNone(fm25)
        self.assertGreaterEqual(fm25["count"], 12)
        self.assertTrue(g1.is_level(25, g2.fold(fm25["g"] / 1200)))
        fm15 = g1.fit_count_mos(self.tones, 15)
        self.assertGreaterEqual(fm15["count"], 8)
        self.assertTrue(g1.is_level(15, g2.fold(fm15["g"] / 1200)))


def _row(lat, kind, n, free, exact, g60, g20, s60, s20, lv60=None, lv20=None, mos=None):
    rec = lambda c: None if c is None else {"count": c, "g": 100.0, "tone_err": 1.0, "mode": 0, "seeds": "", "complexity": 1, "is_level": True}
    return {"lattice": lat, "kind": kind, "N": n, "exact_triads": exact,
            "free": None if free is None else {"count": free, "g": 317.175, "source": "x"},
            "free_effective_count": free, "free_beaten_by_noble": None,
            "free_mos": None if mos is None else {"count": mos, "g": 100.0},
            "golden_by_Q": {"8": rec(g20), "12": rec(g20), "20": rec(g20), "30": rec(g60), "60": rec(g60)},
            "golden_level_only_by_Q": {"8": rec(lv20), "12": rec(lv20), "20": rec(lv20), "30": rec(lv60), "60": rec(lv60)},
            "silver_by_Q": {"8": rec(s20), "12": rec(s20), "20": rec(s20), "30": rec(s60), "60": rec(s60)},
            "silver_level_only_by_Q": {q: None for q in ("8", "12", "20", "30", "60")},
            "golden_nearest_to_free_by_Q": {q: {"count": g60, "dist_cents": 0.05, "complexity": 11} for q in ("8", "12", "20", "30", "60")}}


class TestVerdicts(unittest.TestCase):
    def test_aggregate(self):
        rows = [_row("h1", "hexany", 12, 4, 6, 4, 2, 4, 4), _row("h2", "hexany", 12, 6, 6, 6, 6, 6, 6),
                _row("d1", "dekany_in", 14, 10, 20, 8, 2, 10, 4), _row("x", "main", 12, 4, 12, 4, 4, 4, 4)]
        a = g1._aggregate(rows, ("hexany",))
        self.assertEqual((a["cells"], a["golden60"], a["golden20"], a["silver60"], a["silver20_ge_golden20"], a["full_free"]), (2, 2, 1, 2, 2, 1))
        d = g1._aggregate(rows, ("dekany_in", "dekany_out"))
        self.assertEqual((d["cells"], d["golden60"]), (1, 0))
        # a zero count on both sides is a match, not a missing candidate
        z = [_row("h0", "hexany", 11, 0, 2, 0, 0, 0, 0)]
        a0 = g1._aggregate(z, ("hexany",))
        self.assertEqual((a0["golden60"], a0["golden20"], a0["silver20_ge_golden20"]), (1, 1, 1))

    def test_p_g1_8_shape(self):
        rows = []
        for n in range(11, 37):
            for lat in ("hexany", "eg4", "dek52"):
                rows.append(_row(lat, "main", n, 12, 12, 12, 8, 12, 10, mos=8))
        self.assertTrue(g1.verdict_p_g1_8(rows)["kept"])
        for r in rows:
            r["golden_by_Q"]["20"]["count"] = 12
        self.assertFalse(g1.verdict_p_g1_8(rows)["kept"])


if __name__ == "__main__":
    unittest.main()
