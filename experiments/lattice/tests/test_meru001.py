"""Unit tests for meru001.py (MERU-001). Written BEFORE the first experiment
run (LOG.md pre-registration 2026-10-10). Pins: positive roots, the LIFT
polynomial of the playground state, chain-aligned seeds, the law on a
short exact Fibonacci run (frozen scorer as referee), mirror == frozen,
lift residual decay, descriptors on known scales.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import meru001 as m  # noqa: E402


class TestRoots(unittest.TestCase):
    def test_positive_roots(self):
        self.assertAlmostEqual(m.positive_root(4, 1, 1, 32), 2.673880, places=6)
        self.assertAlmostEqual(m.positive_root(2, 1, 1, 1), (1 + 5 ** 0.5) / 2, places=9)
        self.assertAlmostEqual(m.positive_root(3, 2, 1, 1), 1.3247179572, places=9)
        self.assertAlmostEqual(m.positive_root(2, 1, 2, 1), 1 + 2 ** 0.5, places=9)

    def test_root_moduli_fibonacci(self):
        mods = m.root_moduli([1.0, -1.0, -1.0])
        self.assertAlmostEqual(mods[0], 1.6180339887, places=6)
        self.assertAlmostEqual(mods[1], 0.6180339887, places=6)

    def test_generator_cents(self):
        rec = m.build_recurrence("erv418935", 1, 1, 32, 4)
        self.assertAlmostEqual(rec["cents"], 502.72, places=2)
        self.assertAlmostEqual(rec["gen01"], 0.418935, places=6)
        self.assertAlmostEqual(rec["rate"], 0.880, places=3)


class TestLift(unittest.TestCase):
    def test_playground_lift_polynomial(self):
        # H[n] = H[n-1] + H[n-2] - H[n-3] + 32H[n-4] - 32H[n-6]  (k = 2, rho = 1)
        rec = m.build_recurrence("erv418935", 1, 1, 32, 4)
        self.assertEqual(rec["lift_k"], 2)
        self.assertEqual(rec["coefs_lift"], {1: 1, 2: 1, 3: -1, 4: 32, 6: -32})
        self.assertEqual(rec["order_lift"], 6)

    def test_no_lift_for_high_order(self):
        rec = m.build_recurrence("erv415227", 4, 8, 8, 9)
        self.assertEqual(rec["lift_k"], 0)
        self.assertEqual(rec["coefs_lift"], {8: 4, 9: 8})

    def test_law_flags(self):
        self.assertTrue(m.build_recurrence("fib", 1, 1, 1, 2)["law_applies"])
        self.assertFalse(m.build_recurrence("pell", 2, 1, 1, 2)["law_applies"])      # r = 4.83
        self.assertFalse(m.build_recurrence("silver", 8, 9, 7, 10)["law_applies"])  # 7 not 2^q
        self.assertFalse(m.build_recurrence("pelog", 1, 1, 1, 3)["law_applies"])    # r = 2.15


class TestSeeds(unittest.TestCase):
    def test_hexany(self):
        self.assertEqual([str(t) for t in m.hexany_tones()],
                         ["35/32", "5/4", "21/16", "3/2", "7/4", "15/8"])

    def test_chain_aligned_seeds_climb(self):
        rec = m.build_recurrence("erv418935", 1, 1, 32, 4)
        seeds = m.place_seeds(m.hexany_tones(), 6, rec["log2G"], "LIFT")
        self.assertEqual(len(seeds), 6)
        for k, s in enumerate(seeds):
            self.assertEqual(m.reduce_octave(s), m.hexany_tones()[k])
            self.assertLess(abs(m.cents_of(s) - k * rec["log2G"] * 1200), 600.0)

    def test_exact_seeds_are_first_j(self):
        rec = m.build_recurrence("fib", 1, 1, 1, 2)
        coefs, n_seeds = m.seeding_plan(rec, "EXACT")
        self.assertEqual((coefs, n_seeds), ({1: 1, 2: 1}, 2))
        seeds = m.place_seeds(m.hexany_tones(), n_seeds, rec["log2G"], "EXACT")
        self.assertEqual([m.reduce_octave(s) for s in seeds],
                         [Fraction(35, 32), Fraction(5, 4)])

    def test_cycled_seeds_for_order_9(self):
        rec = m.build_recurrence("erv415227", 4, 8, 8, 9)
        seeds = m.place_seeds(m.hexany_tones(), 9, rec["log2G"], "LIFT")
        self.assertEqual(m.reduce_octave(seeds[6]), m.reduce_octave(seeds[0]))


class TestLaw(unittest.TestCase):
    def test_exact_fibonacci_windows_carry_w_minus_2_triads(self):
        rec = m.build_recurrence("fib", 1, 1, 1, 2)
        coefs, n_seeds = m.seeding_plan(rec, "EXACT")
        h = m.run_recurrence(coefs, m.place_seeds(m.hexany_tones(), n_seeds, rec["log2G"], "EXACT"), 40)
        for n in (20, 30, 41):
            win = h[n - 6:n + 1]
            res = m.score(win)                       # frozen exact, referee
            self.assertGreaterEqual(res.proportional, 5)
            self.assertEqual(m.recurrence_triads(rec, n - 6, n), 5)
            self.assertEqual(m.mirror_exact(win), (res.proportional, res.subcontrary, res.geometric))
        self.assertEqual(m.score(h[35:42]).proportional, 5)

    def test_lift_breaks_exactness_and_residual_decays(self):
        rec = m.build_recurrence("erv418935", 1, 1, 32, 4)
        coefs, n_seeds = m.seeding_plan(rec, "LIFT")
        h = m.run_recurrence(coefs, m.place_seeds(m.hexany_tones(), n_seeds, rec["log2G"], "LIFT"), 60)
        r20, r40 = m.lift_residual(h, rec, 20), m.lift_residual(h, rec, 40)
        self.assertGreater(r20, 0.0)
        self.assertLess(r40, r20)
        self.assertLess(r40, 1e-3)
        self.assertEqual(m.score(h[50:57]).proportional, 0)   # exactness gone
        self.assertGreaterEqual(m.score_tempered([m.cents_of(x) for x in h[50:57]], 2.0).proportional, 3)


class TestDescriptors(unittest.TestCase):
    def test_chain_error_of_pure_chain_is_zero(self):
        g = 0.418935
        cs = [k * g * 1200 for k in range(7)]
        last = cs[-1]
        err = max(min(m.circ(c, last - j * g * 1200) for j in range(7)) for c in cs)
        self.assertAlmostEqual(err, 0.0, places=9)

    def test_step_classes(self):
        self.assertEqual(m.step_class_count([0, 200, 400, 600, 800, 1000], 0.5), 1)
        self.assertEqual(m.step_class_count([0, 200, 400, 500, 700, 900, 1100], 0.5), 2)

    def test_interval_classes_and_retention(self):
        tones = m.hexany_tones()
        classes = m.interval_classes(tones)
        self.assertEqual(len(classes), 15)        # 15 dyads, all distinct interval classes
        self.assertEqual(m.interval_retention(list(tones), classes, 2.0), 15)
        self.assertEqual(m.absolute_retention(list(tones), [m.cents_of(t) for t in tones], 2.0), 6)

    def test_scl_text(self):
        txt = m.scl_text("x", "desc", [0.0, 100.0, 700.0])
        self.assertIn(" 3\n", txt)
        self.assertTrue(txt.strip().endswith("1200.000000"))


if __name__ == "__main__":
    unittest.main()
