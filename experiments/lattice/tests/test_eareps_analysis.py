"""Unit tests for eareps_analysis.py (G-025). Pins the registered rule from
LOG.md 2026-08-19: T = midpoint of max-locked and min-broken, the delta = 0
rung as locked territory, right- and left-censoring, the non-monotone flag
(broken below locked), the catch-trial validity rule, and the P-E1/P-E2/
P-E3 decision lines.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import eareps_analysis as ea  # noqa: E402


class TestThreshold(unittest.TestCase):
    def test_midpoint_of_last_locked_and_first_broken(self):
        t = ea.threshold([(0, "locked"), (2, "locked"), (5, "beating"), (8, "broken"), (11, "broken")])
        self.assertEqual((t["L"], t["K"], t["T"], t["censored"]), (2, 8, 5, None))
        self.assertEqual(t["transition_band"], [5])
        self.assertFalse(t["non_monotone"])

    def test_zero_rung_is_locked_territory(self):
        t = ea.threshold([(0, "locked"), (2, "beating"), (5, "broken")])
        self.assertEqual((t["L"], t["T"]), (0, 2.5))

    def test_right_censored_when_nothing_breaks(self):
        t = ea.threshold([(0, "locked"), (1, "locked"), (3, "beating"), (8, "beating")])
        self.assertIsNone(t["T"])
        self.assertEqual(t["censored"], "T > 8")

    def test_left_censored_when_smallest_rung_breaks(self):
        t = ea.threshold([(0, "locked"), (2, "broken"), (5, "broken")])
        self.assertEqual((t["T"], t["censored"]), (1, "T < 2"))

    def test_broken_below_locked_is_flagged_not_corrected(self):
        t = ea.threshold([(0, "locked"), (2, "broken"), (5, "locked"), (8, "broken")])
        self.assertTrue(t["non_monotone"])
        self.assertEqual(t["T"], 3.5)       # still max-locked 5 and min-broken 2

    def test_locked_above_beating_is_not_non_monotone(self):
        t = ea.threshold([(0, "locked"), (2, "beating"), (8, "locked"), (18, "broken")])
        self.assertFalse(t["non_monotone"])
        self.assertEqual(t["T"], 13)


def sitting(verdicts):
    key = {rid: {"family": f, "delta_cents": d, "description": rid} for rid, (f, d, _) in verdicts.items()}
    resp = {rid: {"verdict": v} for rid, (_, _, v) in verdicts.items()}
    return key, {"responses": resp}


class TestPredictions(unittest.TestCase):
    def base(self, a, b, c="beating"):
        rows = {"a0": ("A", 0.0, "locked"), "b0": ("B", 0.0, "locked"), "c0": ("C", 0.0, "locked"),
                "c+": ("C", 5.0, c), "c-": ("C", -5.0, c), "d": ("D", None, "broken")}
        rows.update(a)
        rows.update(b)
        return sitting(rows)

    def test_band_kept_and_fifths_kept(self):
        key, s = self.base({"a+5": ("A", 5.0, "locked"), "a+11": ("A", 11.0, "broken"),
                            "a-5": ("A", -5.0, "locked"), "a-8": ("A", -8.0, "broken")},
                           {"b+1": ("B", 1.0, "locked"), "b+2": ("B", ea.PC, "beating"), "b+3": ("B", 3.0, "broken"),
                            "b-1": ("B", -1.0, "locked"), "b-2": ("B", -ea.PC, "beating"), "b-3": ("B", -3.0, "broken")})
        p = ea.analyse(key, s)["predictions"]
        self.assertEqual(p["P-E1"]["verdict"], "KEPT")            # T = 8, 6.5
        self.assertEqual(p["P-E2"]["verdict"], "KEPT")            # T = 2, 2
        self.assertEqual(p["P-E2b"]["verdict"], "KEPT")
        self.assertEqual(p["P-E3"]["verdict"], "KEPT")            # 8 - 6.5 = 1.5

    def test_censored_fifth_refutes_and_out_of_band_is_weak(self):
        key, s = self.base({"a+8": ("A", 8.0, "locked"), "a+18": ("A", 18.0, "broken"),
                            "a-5": ("A", -5.0, "locked"), "a-14": ("A", -14.86, "broken")},
                           {"b+8": ("B", 8.0, "beating"), "b-8": ("B", -8.0, "beating")})
        p = ea.analyse(key, s)["predictions"]
        self.assertEqual(p["P-E1"]["verdict"], "WEAK-KEPT")       # T = 13, 9.93
        self.assertEqual(p["P-E2"]["verdict"], "REFUTED")         # T > 8 both ways
        self.assertEqual(p["P-E3"]["verdict"], "KEPT")

    def test_catch_trial_broken_invalidates_family(self):
        key, s = self.base({"a+5": ("A", 5.0, "broken")}, {"b+5": ("B", 5.0, "broken")})
        s["responses"]["a0"]["verdict"] = "broken"
        self.assertFalse(ea.analyse(key, s)["catch_trials"]["A"]["valid"])

    def test_missing_verdict_is_an_error(self):
        key, s = self.base({}, {})
        s["responses"]["d"]["verdict"] = ""
        with self.assertRaises(ValueError):
            ea.analyse(key, s)


if __name__ == "__main__":
    unittest.main()
