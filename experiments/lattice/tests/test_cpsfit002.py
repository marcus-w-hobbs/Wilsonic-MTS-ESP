"""Unit tests for cpsfit002.py (CPSFIT-002). Written BEFORE the first run
(LOG.md pre-registration 2026-10-10). Pins: the triad table sizes, zero
deviation on an identity voicing, agreement with cpsfit001's
triad_deviations, assignment enumeration on a Pythagorean triple, the
golden search on a quadratic, the N = 7 Ptolemy and N = 15 hexany
triad-minimax fits (registered numbers), and the verdict helpers.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cpsfit001 as c1  # noqa: E402
import cpsfit002 as c2  # noqa: E402


class TestTriads(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(c2.prep_triads(c1.LATTICES["hexany"])), 12)
        self.assertEqual(len(c2.prep_triads(c1.LATTICES["eg4"])), 24)
        self.assertEqual(len(c2.prep_triads(c1.LATTICES["ptolemy7"])), 23)

    def test_identity_voicing_has_zero_deviation(self):
        tones = c1.LATTICES["hexany"]
        pc = [c1.wrap(c1.cents_of(t)) for t in tones]
        devs = c2.triad_devs(c2.prep_triads(tones), pc)
        self.assertTrue(all(d < 1e-9 for d, _ in devs))

    def test_matches_cpsfit001_triad_deviations(self):
        tones = c1.LATTICES["hexany"]
        g = 193.787
        ks = [-3, 2, 5, 16, 7, 18]
        pc = [c1.wrap(k * g) for k in ks]
        fast = [d for d, _ in c2.triad_devs(c2.prep_triads(tones), pc)]
        slow = [d["dev_cents"] for d in c1.triad_deviations(tones, pc)]
        for a, b in zip(fast, slow):
            self.assertAlmostEqual(a, b, places=9)


class TestSearch(unittest.TestCase):
    def test_assignments_pythagorean(self):
        tc = [c1.cents_of(Fraction(x)) for x in (Fraction(1), Fraction(3, 2), Fraction(9, 8))]
        found = c2.assignments(tc, 3, 498.045)
        self.assertIn((0, -1, -2), found)

    def test_golden_quadratic(self):
        x, fx = c2.golden(lambda t: (t - 2.5) ** 2 + 1.0, 0.0, 5.0)
        self.assertAlmostEqual(x, 2.5, places=6)
        self.assertAlmostEqual(fx, 1.0, places=9)

    def test_ptolemy_n7_registered(self):
        f = c2.fit_triads(c1.LATTICES["ptolemy7"], 7)
        self.assertIsNotNone(f)
        self.assertAlmostEqual(f["objective_dev_cents"], 10.13, places=1)
        self.assertAlmostEqual(f["g"], 506.25, places=1)

    def test_hexany_n15_registered(self):
        f = c2.fit_triads(c1.LATTICES["hexany"], 15)
        self.assertAlmostEqual(f["objective_dev_cents"], 5.14, places=1)
        self.assertAlmostEqual(f["g"], 503.19, places=1)
        self.assertEqual(c1.homomorphism(c1.LATTICES["hexany"], f["ks"], 15), (-1, -4, -10))

    def test_infeasible_small_n(self):
        self.assertIsNone(c2.fit_triads(c1.LATTICES["hexany"], 6))


def _row(lat, n, dev, g, surv, exact, mapping, prior_surv=None, P2c=0, tone=1.0):
    return {"lattice": lat, "N": n, "objective_dev_cents": dev, "g_cents": g, "eps_star_cents": tone,
            "survival_2c_frozen": surv, "exact_triads": exact, "mapping": mapping,
            "homomorphic": mapping is not None, "chain_P_2c": P2c,
            "nearest_recurrences": [{"a": 1, "i": 1, "b": 32, "j": 4, "pow2": True, "in_octave": True}],
            "prior_tone_minimax": None if prior_surv is None else {"survival_2c_frozen": prior_surv}}


class TestVerdicts(unittest.TestCase):
    def test_p_t3_mapping_table(self):
        rows = {"hexany": [_row("hexany", 22, 1.156, 193.908, 12, 12, (16, 2, 5)),
                           _row("hexany", 48, 0.295, 582.45, 12, 12, None)]}
        self.assertTrue(c2.verdict_p_t3(rows)["kept"])
        rows["hexany"][1]["mapping"] = (-22, 5, -3)
        rows["hexany"][1]["homomorphic"] = True
        self.assertFalse(c2.verdict_p_t3(rows)["kept"])

    def test_p_t5_floor(self):
        rows = {"hexany": [_row("hexany", 15, 5.14, 503.185, 4, 12, (-1, -4, -10), P2c=12)]}
        self.assertTrue(c2.verdict_p_t5(rows)["kept"])
        rows["hexany"][0]["chain_P_2c"] = 9
        self.assertFalse(c2.verdict_p_t5(rows)["kept"])


if __name__ == "__main__":
    unittest.main()
