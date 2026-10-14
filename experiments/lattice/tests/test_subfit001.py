"""Unit tests for subfit001.py (SUBFIT-001). Written BEFORE the first run
(LOG.md pre-registration 2026-10-14). Pins: the eikosany (20 tones, 114
triads, 72 subsets with every subset triad among the 114), the per-window
assignment (inside the window, nearest), the registered N = 70 winner
(175.378 cents keeps at least 20 hexanies and 4 dekanies with at least
102 triads), the N = 17 winner (351.32 keeps at least 3 hexanies), the
structure helper on a known chain, and the verdict helpers.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import subfit001 as sf  # noqa: E402


class TestObjects(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(sf.EIK), 20)
        self.assertEqual(len(sf.TRI), 114)
        self.assertEqual(len(sf.SUBS), 72)
        self.assertEqual((sum(sf.IS_HEX), sum(sf.IS_DEK), sum(sf.IS_TET)), (30, 12, 30))
        self.assertTrue(all(len(i) >= 1 for i in sf.INC))
        self.assertTrue(all(0 <= j < 114 for i in sf.INC for j in i))


class TestEvaluate(unittest.TestCase):
    def test_assignment_inside_window(self):
        r = sf.evaluate(351.32, 17)
        s = -r["mode"]
        self.assertTrue(all(s <= k <= s + 16 for k in r["assign"]))
        self.assertGreaterEqual(r["hex"], 3)

    def test_registered_n70(self):
        r = sf.evaluate(175.378, 70)
        self.assertGreaterEqual(r["hex"], 20)
        self.assertGreaterEqual(r["dek"], 4)
        self.assertGreaterEqual(r["triads"], 102)
        self.assertLessEqual(r["max_err_kept"], 5.0)

    def test_structure_on_n26(self):
        r = sf.evaluate(350.756, 26)
        st = sf.structure(r, 26)
        self.assertIn("image_frozen_PS_2c", st)
        self.assertGreaterEqual(st["image_frozen_PS_2c"], r["triads"] - 10)
        self.assertEqual(st["step_classes"] >= 2, True)


def _row(n, g, hx, dk, tt, tri, err=4.5, level=False, mos=None):
    free = {"g": g, "hex": hx, "dek": dk, "tet": tt, "triads": tri, "max_err_kept": err, "mode": 0, "assign": [], "playable": []}
    return {"N": n, "free": free, "free_is_level": level, "mos": mos}


class TestVerdicts(unittest.TestCase):
    def test_p_s2_and_s5(self):
        rows = [_row(n, 351.32, 3, 0, 3, 26, err=27.9 if n <= 20 else 9.1) for n in range(11, 25)]
        rows += [_row(n, 350.76, 6, 1, 7, 40, err=9.0) for n in range(25, 40)]
        rows += [_row(n, 497.77, 16, 2, 16, 76, err=4.2) for n in range(40, 70)]
        rows += [_row(n, 175.38, 20, 4, 20, 102, err=4.6) for n in range(70, 73)]
        rows[14]["free"]["dek"] = 0   # N=25 keeps no dekany
        v = sf.verdict_p_s2(rows)
        self.assertEqual(v["failures"], [])
        self.assertTrue(sf.verdict_p_s5(rows)["kept"])
        rows[5]["free"]["max_err_kept"] = 1.0   # N=16 sits in the 27-28.5 band
        self.assertFalse(sf.verdict_p_s5(rows)["kept"])

    def test_p_s4_level_logic(self):
        mos = {"g": 339.4, "hex": 12, "dek": 0, "tet": 12, "triads": 82, "max_err_kept": 5.0, "mode": 0, "assign": [], "playable": []}
        rows = [_row(46, 339.404, 12, 2, 12, 84, level=True, mos=mos)]
        v = sf.verdict_p_s4(rows)
        self.assertFalse(any("N=46" in f for f in v["failures"]))
        rows[0]["free_is_level"] = False
        v = sf.verdict_p_s4(rows)
        self.assertTrue(any("N=46" in f for f in v["failures"]))


if __name__ == "__main__":
    unittest.main()
