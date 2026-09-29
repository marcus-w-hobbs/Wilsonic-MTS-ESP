"""Unit tests for ET-003 (the comma-kernel history of 12-EDO).

Written and green BEFORE the first receipts run (harness rule). Pins:
- stage construction (chains, Werckmeister III table, exact closure);
- the V12 kernel census (counts 5/29/122, the 5-limit member list, named
  7-limit members, 33/32 and 121/120 EXCLUDED with V12 image 1);
- the lattice rank rail: cross(81/80, 128/125) = -<12,19,28>, so the pair
  generates the SATURATED 5-limit kernel; integer combination identities;
- exact deviation identities (root ditone major = syntonic comma;
  schismatic major = schisma; dim5+ditone = diaschisma; 2nd-inv ditone =
  129/128; meantone wrapped third = 128/125; wolf power chords);
- prototype Fraction identities behind the meantone septimal lock
  ((75/64)/(7/6) = 225/224, (144/125)/(8/7) = 126/125);
- the analytic mirror against the frozen scorer on 12-EDO (ET-001 rail)
  and the Werckmeister chirality (P != S at eps = 1);
- frozen melodic pins for all four stages.
"""

import sys
import unittest
from fractions import Fraction
from math import log2
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_TRIADS = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import et003  # noqa: E402
from et003 import (  # noqa: E402
    MEANTONE_FIFTH,
    PURE_FIFTH,
    PYTH_COMMA,
    V12,
    WERCK_TEMPERED,
    address_table,
    chain_scale,
    coverage,
    enumerate_kernel,
    lock_spectrum,
    mirror_counts,
    stage_scale,
    triple_devs,
    vdot,
    werck3_scale,
)
from scorer import score_tempered  # noqa: E402  (frozen v1.1.0)
from melodic import score_melodic  # noqa: E402  (frozen v0.1.0)

CENTS = lambda fr: 1200.0 * log2(float(fr))  # noqa: E731


class TestStageConstruction(unittest.TestCase):
    def test_pythagorean_scale(self):
        s = stage_scale("S1_pythagorean")
        self.assertEqual(len(s), 12)
        self.assertAlmostEqual(s[0], 0.0, places=9)
        self.assertAlmostEqual(s[1], 90.225, places=3)     # limma
        self.assertAlmostEqual(s[6], 611.73, places=2)     # aug4 (+6 fifths)
        self.assertAlmostEqual(s[7], PURE_FIFTH, places=9)

    def test_meantone_scale(self):
        s = stage_scale("S2_meantone")
        self.assertAlmostEqual(s[4], 1200.0 * log2(1.25), places=9)  # 5/4 exact
        self.assertAlmostEqual(s[7], MEANTONE_FIFTH, places=9)
        # wolf G#-Eb: 8400 - 11 fifths
        wolf = 8400.0 - 11.0 * MEANTONE_FIFTH
        self.assertAlmostEqual(wolf, 737.637287, places=5)

    def test_werckmeister_table(self):
        s = werck3_scale()
        expected = [0.0, 90.225, 192.180, 294.135, 390.225, 498.045,
                    588.270, 696.090, 792.180, 888.270, 996.090, 1092.180]
        for got, want in zip(s, expected):
            self.assertAlmostEqual(got, want, places=3)

    def test_werckmeister_circle_closes_exactly(self):
        # 8 pure + 4 tempered fifths = 7 octaves, exact by construction
        total = 8.0 * PURE_FIFTH + 4.0 * WERCK_TEMPERED
        self.assertAlmostEqual(total, 8400.0, places=9)

    def test_pythagorean_wolf_is_pure_minus_comma(self):
        wolf = 8400.0 - 11.0 * PURE_FIFTH
        self.assertAlmostEqual(wolf, PURE_FIFTH - PYTH_COMMA, places=9)


class TestKernelCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.k5 = enumerate_kernel(2)
        cls.k7 = enumerate_kernel(3)
        cls.k11 = enumerate_kernel(4)

    def test_counts(self):
        self.assertEqual(len(self.k5), 5)
        self.assertEqual(len(self.k7), 29)
        self.assertEqual(len(self.k11), 122)

    def test_five_limit_members(self):
        self.assertEqual(
            sorted(m["ratio"] for m in self.k5),
            sorted(["81/80", "128/125", "2048/2025", "32805/32768",
                    "531441/524288"]))

    def test_named_seven_limit_members_present(self):
        ratios = {m["ratio"] for m in self.k7}
        for named in ("36/35", "50/49", "64/63", "126/125", "225/224"):
            self.assertIn(named, ratios)

    def test_33_32_and_121_120_are_not_kernel_members(self):
        # both map to ONE step of 12-EDO, not zero: V12(33/32) = V12(121/120) = 1
        self.assertEqual(vdot(V12, (-5, 1, 0, 0, 1)), 1)    # 33/32
        self.assertEqual(vdot(V12, (-3, -1, -1, 0, 2)), 1)  # 121/120
        ratios = {m["ratio"] for m in self.k11}
        self.assertNotIn("33/32", ratios)
        self.assertNotIn("121/120", ratios)

    def test_members_are_killed_and_in_box(self):
        for members, n_odd in ((self.k5, 2), (self.k7, 3), (self.k11, 4)):
            box = (12, 5, 4, 3)[:n_odd]
            val = V12[: n_odd + 1]
            for m in members:
                monzo = tuple(m["monzo"])
                self.assertEqual(vdot(val, monzo), 0, m["ratio"])
                self.assertTrue(0.0 < m["cents"] < 60.0, m["ratio"])
                for e, b in zip(monzo[1:], box):
                    self.assertLessEqual(abs(e), b, m["ratio"])

    def test_cross_product_rail(self):
        # cross(81/80, 128/125) = -<12,19,28>: the two commas' monzos span
        # the SATURATED 5-limit kernel of the patent val (minor gcd 1).
        a = (-4, 4, -1)   # 81/80
        b = (7, 0, -3)    # 128/125
        cross = (a[1] * b[2] - a[2] * b[1],
                 a[2] * b[0] - a[0] * b[2],
                 a[0] * b[1] - a[1] * b[0])
        self.assertEqual(cross, (-12, -19, -28))

    def test_integer_combination_identities(self):
        c81 = Fraction(81, 80)
        c128 = Fraction(128, 125)
        self.assertEqual(c81 ** 3 / c128, Fraction(531441, 524288))  # PC
        self.assertEqual(c128 / c81, Fraction(2048, 2025))           # diaschisma
        self.assertEqual(c81 ** 2 / c128, Fraction(32805, 32768))    # schisma


class TestExactDevIdentities(unittest.TestCase):
    """The comma->triad attribution identities (H-K4), to 1e-9 cents."""

    def test_pythagorean_root_ditone_major_is_syntonic_comma(self):
        b = (4.0 * PURE_FIFTH) % 1200.0   # ditone 81/64
        dev_p, _, _, _ = triple_devs(0.0, b, PURE_FIFTH)
        self.assertAlmostEqual(dev_p, CENTS(Fraction(81, 80)), places=9)

    def test_schismatic_major_root_dev_is_schisma(self):
        b = (-8.0 * PURE_FIFTH) % 1200.0  # dim4 8192/6561
        dev_p, _, _, _ = triple_devs(0.0, b, PURE_FIFTH)
        self.assertAlmostEqual(dev_p, CENTS(Fraction(32805, 32768)), places=9)

    def test_dim5_ditone_dev_is_diaschisma(self):
        a = -((-6.0 * PURE_FIFTH) % 1200.0)  # dim5 1024/729 below
        c = (4.0 * PURE_FIFTH) % 1200.0
        dev_p, _, _, _ = triple_devs(a, 0.0, c)
        self.assertAlmostEqual(dev_p, CENTS(Fraction(2048, 2025)), places=9)

    def test_second_inversion_ditone_dev_is_129_128(self):
        a = PURE_FIFTH - 1200.0
        c = (4.0 * PURE_FIFTH) % 1200.0
        dev_p, _, _, _ = triple_devs(a, 0.0, c)
        self.assertAlmostEqual(dev_p, CENTS(Fraction(129, 128)), places=9)

    def test_meantone_wrapped_third_error_is_diesis(self):
        d4 = (-8.0 * MEANTONE_FIFTH) % 1200.0
        m3 = (4.0 * MEANTONE_FIFTH) % 1200.0
        self.assertAlmostEqual(d4 - m3, CENTS(Fraction(128, 125)), places=9)
        # and the wrapped third is exactly 32/25 in 1/4-comma meantone
        self.assertAlmostEqual(d4, CENTS(Fraction(32, 25)), places=9)

    def test_wolf_power_chord_devs(self):
        pyth_wolf = 8400.0 - 11.0 * PURE_FIFTH
        dev_p, _, _, _ = triple_devs(0.0, pyth_wolf, 1200.0)
        self.assertAlmostEqual(dev_p, PYTH_COMMA, places=9)
        mt_dev, _, _, _ = triple_devs(0.0, MEANTONE_FIFTH, 1200.0)
        self.assertAlmostEqual(mt_dev, CENTS(Fraction(81, 80)) / 4.0, places=9)

    def test_septimal_prototype_fraction_identities(self):
        # the meantone 6:7:8 lock: A2 (just 75/64) ~ 7/6 via 225/224,
        # d3 (just 144/125) ~ 8/7 via 126/125 -- both V12 kernel members
        self.assertEqual(Fraction(75, 64) / Fraction(7, 6),
                         Fraction(225, 224))
        self.assertEqual(Fraction(144, 125) / Fraction(8, 7),
                         Fraction(126, 125))


class TestMirrorAgainstFrozenScorer(unittest.TestCase):
    def test_12edo_grid_reproduces_et001_rail(self):
        s = stage_scale("S4_12edo")
        for eps, want in zip(et003.EPS_GRID, [0, 12, 24, 24, 24, 48, 48]):
            p, sub, _ = mirror_counts(s, eps)
            self.assertEqual((p, sub), (want, want), f"eps={eps}")
            res = score_tempered(s, epsilon_cents=eps)
            self.assertEqual((res.proportional, res.subcontrary),
                             (want, want), f"scorer eps={eps}")

    def test_12edo_geometric_rail(self):
        s = stage_scale("S4_12edo")
        for eps, want in zip(et003.EPS_GRID, [72, 72, 72, 72, 60, 60, 60]):
            self.assertEqual(mirror_counts(s, eps)[2], want)
            self.assertEqual(score_tempered(s, epsilon_cents=eps).geometric,
                             want)

    def test_mirror_equals_scorer_on_all_stages_at_2c(self):
        for stage, _ in et003.STAGES:
            s = stage_scale(stage)
            res = score_tempered(s, epsilon_cents=2.0)
            self.assertEqual(
                mirror_counts(s, 2.0),
                (res.proportional, res.subcontrary, res.geometric), stage)

    def test_werckmeister_chirality_at_1c(self):
        # W-III's fifth word TTTPPTPPPPPP is chirally asymmetric: P != S
        res = score_tempered(stage_scale("S3_werckmeister3"),
                             epsilon_cents=1.0)
        self.assertEqual((res.proportional, res.subcontrary), (10, 9))

    def test_meantone_first_lock_is_septimal(self):
        # 1/4-comma meantone-12's first proportional lock is the 6:7:8
        # (A2 + d3) at 0.7394c, count 2 -- BELOW 1 cent, while 12-EDO has 0
        head = lock_spectrum(stage_scale("S2_meantone"), "P")[0]
        self.assertAlmostEqual(head["dev"], 0.7394, places=4)
        self.assertEqual(head["count"], 2)
        self.assertEqual(
            score_tempered(stage_scale("S2_meantone"),
                           epsilon_cents=1.0).proportional, 2)
        self.assertEqual(
            score_tempered(stage_scale("S4_12edo"),
                           epsilon_cents=1.0).proportional, 0)

    def test_pythagorean_pure_fifth_locks_at_zero(self):
        head = lock_spectrum(stage_scale("S1_pythagorean"), "P")[0]
        self.assertLess(head["dev"], 1e-9)
        self.assertEqual(head["count"], 11)

    def test_inert_clusters_flagged(self):
        # S1's apotome-below/limma-above cluster: dev 8.73 > sep 6.00, so its
        # (dev, sep] counting interval is empty -- flagged inert
        spec = lock_spectrum(stage_scale("S1_pythagorean"), "P")
        inert = [cl for cl in spec if cl["inert"]]
        self.assertTrue(any(abs(cl["dev"] - 8.7296) < 1e-3 for cl in inert))


class TestMelodicPins(unittest.TestCase):
    """Frozen melodic v0.1.0 on the four stages (H-K3 rails)."""

    def check(self, stage, gap_classes, entropy):
        m = score_melodic(stage_scale(stage))
        self.assertEqual(m.propriety.classification, "strictly_proper", stage)
        self.assertTrue(m.constant_structure.is_cs, stage)
        self.assertEqual(m.gap_entropy.gap_class_count, gap_classes, stage)
        self.assertAlmostEqual(m.gap_entropy.entropy_bits, entropy, places=6)

    def test_pythagorean(self):
        h = -(7 / 12) * log2(7 / 12) - (5 / 12) * log2(5 / 12)
        self.check("S1_pythagorean", 2, h)

    def test_meantone(self):
        h = -(7 / 12) * log2(7 / 12) - (5 / 12) * log2(5 / 12)
        self.check("S2_meantone", 2, h)

    def test_werckmeister(self):
        h = -2 * (2 / 12) * log2(2 / 12) - 2 * (4 / 12) * log2(4 / 12)
        self.check("S3_werckmeister3", 4, h)

    def test_12edo(self):
        self.check("S4_12edo", 1, 0.0)

    def test_werckmeister_step_multiset(self):
        m = score_melodic(stage_scale("S3_werckmeister3"))
        counts = sorted(c for _, _, c in m.gap_entropy.gap_classes)
        self.assertEqual(counts, [2, 2, 4, 4])


class TestAddressCensus(unittest.TestCase):
    def test_12edo_major_coverage(self):
        table = address_table(stage_scale("S4_12edo"), 4, 7, "P")
        self.assertEqual(coverage(table, 5.0), 0)
        self.assertEqual(coverage(table, 14.86), 12)

    def test_meantone_major_coverage_caps_at_8_below_20(self):
        table = address_table(stage_scale("S2_meantone"), 4, 7, "P")
        self.assertEqual(coverage(table, 14.86), 8)
        self.assertEqual(coverage(table, 20.0), 9)  # the G# double-wolf

    def test_pythagorean_schismatic_majors(self):
        table = address_table(stage_scale("S1_pythagorean"), 4, 7, "P")
        self.assertEqual(coverage(table, 2.0), 3)   # schisma triads
        self.assertEqual(coverage(table, 14.86), 12)

    def test_werckmeister_key_color_extremes(self):
        table = address_table(stage_scale("S3_werckmeister3"), 4, 7, "P")
        best = sorted(min(v["dev"] for v in row["voicings"]) for row in table)
        self.assertAlmostEqual(best[0], 0.2516, places=4)    # C major
        self.assertAlmostEqual(best[-1], 13.4727, places=4)  # C#/F#/G#
        self.assertAlmostEqual(best[-1], CENTS(Fraction(129, 128)), places=4)


if __name__ == "__main__":
    unittest.main()
