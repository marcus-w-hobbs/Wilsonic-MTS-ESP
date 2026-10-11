"""Unit tests for cpsfit001.py (CPSFIT-001). Written BEFORE the first run
(LOG.md pre-registration 2026-10-10). Pins: the lattices, an exact fit on a
Pythagorean triple (eps* = 0 at the pure fifth), the hexany N = 15 fit
(Erv's generator), homomorphism and kernel solvers, ET fits, triad
deviations of an identity fit, the recurrence table.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cpsfit001 as c  # noqa: E402


class TestLattices(unittest.TestCase):
    def test_tones(self):
        self.assertEqual([str(t) for t in c.LATTICES["hexany"]],
                         ["35/32", "5/4", "21/16", "3/2", "7/4", "15/8"])
        self.assertEqual([str(t) for t in c.LATTICES["eg4"]],
                         ["1", "35/32", "5/4", "21/16", "3/2", "105/64", "7/4", "15/8"])
        self.assertEqual(len(c.LATTICES["ptolemy7"]), 7)

    def test_monzo(self):
        self.assertEqual(c.monzo(Fraction(35, 32)), (-5, (0, 1, 1)))
        self.assertEqual(c.monzo(Fraction(3, 2)), (-1, (1, 0, 0)))
        with self.assertRaises(ValueError):
            c.monzo(Fraction(11, 8))


class TestFit(unittest.TestCase):
    def test_pythagorean_triple_fits_exactly(self):
        tones = [Fraction(1), Fraction(3, 2), Fraction(9, 8)]
        tc = [c.cents_of(t) for t in tones]
        f = c.fit(tc, 3)
        self.assertIsNotNone(f)
        self.assertLess(f["eps"], 1e-6)
        # the pure fifth (701.955) exceeds G_MAX, so the fit is its complement 498.045 with k = -1, -2
        self.assertAlmostEqual(f["g"], 498.0449991, places=5)
        self.assertEqual(sorted(f["ks"]), [-2, -1, 0])

    def test_hexany_n15_is_ervs_generator(self):
        tc = [c.cents_of(t) for t in c.LATTICES["hexany"]]
        f = c.fit(tc, 15)
        self.assertAlmostEqual(f["eps"], 4.8154, places=3)
        self.assertAlmostEqual(f["g"], 502.86, places=1)
        self.assertEqual(c.homomorphism(c.LATTICES["hexany"], f["ks"], 15), (-1, -4, -10))

    def test_eps_non_increasing_in_n(self):
        tc = [c.cents_of(t) for t in c.LATTICES["hexany"]]
        e8, e9 = c.fit(tc, 8)["eps"], c.fit(tc, 9)["eps"]
        self.assertGreaterEqual(e8, e9)

    def test_et_fit(self):
        tc = [c.cents_of(t) for t in c.LATTICES["ptolemy7"]]
        f = c.et_fit(tc, 12)
        self.assertAlmostEqual(f["eps"], 15.641, places=2)   # 5/3 vs 900: 884.36
        self.assertEqual(f["ks"], [0, 2, 4, 5, 7, 9, 11])


class TestStructure(unittest.TestCase):
    def test_homomorphism_rejects_accident(self):
        self.assertIsNone(c.homomorphism(c.LATTICES["hexany"], [0, 1, 2, 3, 4, 5], 10))

    def test_kernel_of_hemi_mapping_contains_2401_2400(self):
        commas = [k["comma"] for k in c.kernel((16, 2, 5), 193.7867)]
        self.assertIn("2401/2400", commas)
        self.assertIn("3136/3125", commas)

    def test_kernel_meantone(self):
        commas = [k["comma"] for k in c.kernel((-1, -4, -10), 502.8604)]
        self.assertIn("81/80", commas)
        self.assertIn("126/125", commas)

    def test_exact_triads_of_hexany(self):
        tri = c.exact_triads(c.LATTICES["hexany"])
        self.assertEqual(sum(1 for t in tri if t[0] == "P"), 6)
        self.assertEqual(sum(1 for t in tri if t[0] == "S"), 6)
        res = c.score(c.LATTICES["hexany"])
        self.assertEqual((res.proportional, res.subcontrary), (6, 6))

    def test_identity_fit_has_zero_deviation(self):
        tones = c.LATTICES["hexany"]
        devs = c.triad_deviations(tones, [c.wrap(c.cents_of(t)) for t in tones])
        self.assertEqual(len(devs), 12)
        self.assertTrue(all(d["dev_cents"] < 1e-9 for d in devs))

    def test_step_classes(self):
        self.assertEqual(c.step_class_count([k * 100.0 for k in range(12)], 0.01), 1)
        self.assertEqual(c.step_class_count([c.wrap(k * 701.955) for k in range(7)], 0.01), 2)

    def test_rr_table(self):
        table = c.build_rr_table()
        hits = c.nearest_recurrences(table, 0.418935, 0.5)
        self.assertTrue(any(h["a"] == 1 and h["i"] == 1 and h["b"] == 32 and h["j"] == 4
                            and h["pow2"] and h["in_octave"] for h in hits))


if __name__ == "__main__":
    unittest.main()
