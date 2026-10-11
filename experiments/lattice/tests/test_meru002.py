"""Unit tests for meru002.py (MERU-002). Written BEFORE the first run
(LOG.md pre-registration 2026-10-10). Pins: the rational lift polynomial
(rho = 1 reproduces MERU-001's integer lift; rho = 3/2 the registered
coefficients), the rho = 1 sequence equals MERU-001's LIFT sequence term by
term, tau_eff, positivity on a short run, the ladder filter, and the verdict
helpers on a synthetic summary.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import meru001 as m1  # noqa: E402
import meru002 as m2  # noqa: E402


class TestLift(unittest.TestCase):
    def test_rho_one_matches_meru001(self):
        rec = m1.build_recurrence("erv418935", 1, 1, 32, 4)
        c = m2.lift_coefs(1, 1, 32, 4, rec["lift_k"], Fraction(1))
        self.assertEqual({k: int(v) for k, v in c.items()}, rec["coefs_lift"])

    def test_rho_three_halves(self):
        # (x^4 - x^3 - 32)(x^2 - 9/4) = x^6 - x^5 - 9/4 x^4 + 9/4 x^3 - 32 x^2 + 72
        c = m2.lift_coefs(1, 1, 32, 4, 2, Fraction(3, 2))
        self.assertEqual(c, {1: Fraction(1), 2: Fraction(9, 4), 3: Fraction(-9, 4),
                             4: Fraction(32), 6: Fraction(-72)})

    def test_no_lift_when_k_zero(self):
        self.assertEqual(m2.lift_coefs(4, 8, 8, 9, 0, Fraction(2)), {8: Fraction(4), 9: Fraction(8)})

    def test_rho_one_sequence_equals_meru001_lift(self):
        rec = m1.build_recurrence("fib", 1, 1, 1, 2)
        tones = m1.hexany_tones()
        h2, bad = m2.run_lifted(rec, Fraction(1), tones, steps=40)
        coefs, n_seeds = m1.seeding_plan(rec, "LIFT")
        h1 = m1.run_recurrence(coefs, m1.place_seeds(tones, n_seeds, rec["log2G"], "LIFT"), 40)
        self.assertIsNone(bad)
        self.assertEqual(h1, h2)

    def test_positivity_short_run(self):
        rec = m1.build_recurrence("erv418935", 1, 1, 32, 4)
        _, bad = m2.run_lifted(rec, Fraction(5, 2), m1.hexany_tones(), steps=30)
        self.assertIsNone(bad)


class TestDescriptors(unittest.TestCase):
    def test_tau_eff_plateau_below_lambda2(self):
        rec = m1.build_recurrence("erv418935", 1, 1, 32, 4)
        self.assertAlmostEqual(m2.tau_eff(rec, Fraction(1)), m2.tau_eff(rec, Fraction(2)), places=9)
        self.assertGreater(m2.tau_eff(rec, Fraction(5, 2)), m2.tau_eff(rec, Fraction(2)))
        self.assertAlmostEqual(m2.tau_eff(rec, Fraction(5, 2)), 10.309, places=2)

    def test_ladder_filters_by_G(self):
        fib = m1.build_recurrence("fib", 1, 1, 1, 2)
        kept = [r for r in m2.RHO_LADDER if float(r) < fib["G"]]
        self.assertEqual(len(kept), 9)
        self.assertEqual(kept[-1], Fraction(25, 16))


def _per(n0, n_lock, n2, n05, mean_p, ir, echo=0, bad=None, tau=5.0, rho="1"):
    return {"rho": rho, "rho_float": float(Fraction(rho)), "first_nonpositive": bad, "tau_eff": tau,
            "rate_rho": 0.3, "n_seeds": 6,
            "per_w": {str(w): {"n0": n0 + (w - 7), "n_lock": n_lock, "n_chain": {"2.0": n2, "0.5": n05},
                               "delta_n": (n05 - n2) if n2 and n05 else None,
                               "transient_windows": (n2 - n0) if n2 else 0,
                               "mean_P_2c_transient": mean_p, "mean_S_2c_transient": 1.0,
                               "mean_interval_retention_2c_transient": ir,
                               "echo_windows": echo, "floor_violations": 0, "mirror_failures": 0,
                               "stationary": {}} for w in m2.WINDOWS}}


class TestVerdicts(unittest.TestCase):
    def test_p_r5_detects_registered_pair_only(self):
        summary = {"erv418935": {"21/8": _per(12, None, None, None, None, None, bad=9, rho="21/8"),
                                 "1": _per(12, 12, 53, 62, 4.0, 1.4)},
                   "fib": {"1": _per(12, 14, 22, 23, 3.6, 1.8)}}
        self.assertTrue(m2.verdict_p_r5(summary)["kept"])
        summary["fib"]["1"]["first_nonpositive"] = 3
        self.assertFalse(m2.verdict_p_r5(summary)["kept"])

    def test_p_r4_tolerance_scales(self):
        recs = {"fib": m1.build_recurrence("fib", 1, 1, 1, 2)}
        summary = {"fib": {"3/2": _per(12, 54, 75, 95, 1.7, 1.1, tau=9.151, rho="3/2")}}
        self.assertTrue(m2.verdict_p_r4(summary, recs)["kept"])      # 20 vs 18.3, tol 5.5
        summary["fib"]["3/2"]["per_w"]["7"]["delta_n"] = 25
        self.assertFalse(m2.verdict_p_r4(summary, recs)["kept"])     # 25 vs 18.3


if __name__ == "__main__":
    unittest.main()
