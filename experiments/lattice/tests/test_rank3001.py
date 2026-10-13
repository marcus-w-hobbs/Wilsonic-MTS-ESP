"""Unit tests for rank3001.py (RANK3-001). Written BEFORE the first run
(LOG.md pre-registration 2026-10-12). Pins: 11-limit monzos, the mode-error
routine against brute force, the structure constraints at and across a
Brun3 boundary, the Chebyshev vertex solver on a known problem, the integer
solver, and the exact refinement of the two registered hexany winners
(N = 21 breed at 0.12 cents, N = 19 at 0.61 cents) from their grid seeds.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brun3  # noqa: E402
import cpsfit001 as c1  # noqa: E402
import rank3001 as r3  # noqa: E402


class TestHelpers(unittest.TestCase):
    def test_monzo_11_limit(self):
        self.assertEqual(r3.monzo(Fraction(11, 8)), (-3, (0, 0, 0, 1)))
        self.assertEqual(r3.monzo(Fraction(63, 32)), (-5, (2, 0, 1, 0)))
        with self.assertRaises(ValueError):
            r3.monzo(Fraction(13, 8))

    def test_mode_errors_matches_brute_force(self):
        tones = [c1.cents_of(t) for t in c1.LATTICES["hexany"]]
        steps = brun3.brun3_levels(1.0, 0.58, 0.32, "AB")[5]
        pcs = brun3.scale_cents(steps, 1.0, 0.58, 0.32, 0)
        fast = r3.mode_errors(pcs, tones)
        for worst, m in fast:
            rot = [(p - pcs[m]) % 1200.0 for p in pcs]
            brute = max(min(r3.circ(t, q) for q in rot) for t in tones)
            self.assertAlmostEqual(worst, brute, places=9)

    def test_structure_constraints_hold_at_point_and_detect_change(self):
        g0, g1, calc, L = 0.58, 0.32, "AB", 6
        cons = r3.structure_constraints(1.0, g0, g1, calc, L)
        self.assertTrue(all(a + b * g0 + c * g1 >= -1e-12 for a, b, c in cons))
        steps = brun3.brun3_levels(1.0, g0, g1, calc)[L]
        # walk until the structure changes; the constraints must fail there
        x = g0
        while brun3.brun3_levels(1.0, x, g1, calc)[L] == steps and x < 0.99:
            x += 0.002
        self.assertNotEqual(brun3.brun3_levels(1.0, x, g1, calc)[L], steps)
        self.assertTrue(any(a + b * x + c * g1 < 0 for a, b, c in cons))

    def test_chebyshev_known(self):
        # minimize eps s.t. |x - 1| <= eps, |x - 3| <= eps, y free in box: eps = 1 at x = 2
        rows = [(-1.0, 1.0, 0.0), (-3.0, 1.0, 0.0)]
        sol = r3.solve_chebyshev(rows, [], (0.0, 10.0, 0.0, 10.0))
        self.assertIsNotNone(sol)
        self.assertAlmostEqual(sol[0], 1.0, places=9)
        self.assertAlmostEqual(sol[1], 2.0, places=9)

    def test_int_solve(self):
        self.assertEqual(r3.int_solve([[1, 0], [0, 1], [1, 1]], [2, -3, -1]), [2, -3])
        self.assertIsNone(r3.int_solve([[1, 0], [0, 1], [1, 1]], [2, -3, 0]))
        self.assertIsNone(r3.int_solve([[2, 0], [0, 1]], [1, 1]))


class TestRefine(unittest.TestCase):
    def setUp(self):
        self.tones = c1.LATTICES["hexany"]
        self.tc = [c1.cents_of(t) for t in self.tones]

    def _refine_from(self, g0c, g1c, calc, L):
        steps = brun3.brun3_levels(1.0, g0c / 1200, g1c / 1200, calc)[L]
        pcs = brun3.scale_cents(steps, 1.0, g0c / 1200, g1c / 1200, 0)
        e, m = min(r3.mode_errors(pcs, self.tc))
        return r3.refine(self.tc, (e, g0c, g1c, calc, L, m))

    def test_hexany_n21_breed(self):
        f = self._refine_from(850.0, 232.0, "AB", 7)
        self.assertIsNotNone(f)
        self.assertEqual(len(f["steps"]), 21)
        self.assertLessEqual(f["eps"], 0.12 + 0.05)
        val = r3.val_of(self.tones, f["assign"])
        self.assertIsNotNone(val)
        self.assertEqual(r3.kernel_of(val)[0]["comma"], "2401/2400")

    def test_hexany_n19(self):
        f = self._refine_from(1004.0, 386.0, "AB", 7)
        self.assertIsNotNone(f)
        self.assertEqual(len(f["steps"]), 19)
        self.assertLessEqual(f["eps"], 0.61 + 0.05)
        val = r3.val_of(self.tones, f["assign"])
        self.assertEqual(r3.kernel_of(val)[0]["comma"], "65625/65536")

    def test_refined_errors_are_consistent(self):
        f = self._refine_from(850.0, 232.0, "AB", 7)
        row = r3.fit_row("hexany", self.tones, self.tc, f, None)
        self.assertEqual(row["N"], 21)
        self.assertAlmostEqual(row["eps_star_cents"], max(row["tone_errors_cents"]), places=9)
        self.assertEqual(row["survival_2c_frozen"], 12)
        self.assertEqual(row["survival_2c_mirror"], 12)


class TestGridColumn(unittest.TestCase):
    def test_one_column_has_small_n_entries(self):
        tc = [c1.cents_of(t) for t in c1.LATTICES["hexany"]]
        part = r3.grid_column((850.0, tc))
        self.assertIn(21, part)
        for n, lst in part.items():
            self.assertLessEqual(len(lst), r3.TOPK)
            self.assertEqual(lst, sorted(lst))


if __name__ == "__main__":
    unittest.main()
