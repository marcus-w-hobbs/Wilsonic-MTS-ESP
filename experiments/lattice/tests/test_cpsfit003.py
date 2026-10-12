"""Unit tests for cpsfit003.py (CPSFIT-003). Written BEFORE the first run
(LOG.md pre-registration 2026-10-11). Pins: the five lattices and their
exact triad counts, the voiced-deviation function against cpsfit001's
mirror, the shared survival predicate, the basin, survival intervals and
segment counting on a known chain, the window range, the transposed-val
test, the registered hexany fits at N = 11, 16 and 22, EG4 infeasibility
at N = 11, and the verdict helpers.

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
import cpsfit003 as c3  # noqa: E402
from scorer import score  # noqa: E402


class TestLattices(unittest.TestCase):
    def test_exact_triad_counts(self):
        want = {"hexany": (6, 6), "eg4": (12, 12), "dek52": (25, 16), "dek52refl": (16, 25), "dek53": (16, 25)}
        for name, (p, s) in want.items():
            tri = c1.exact_triads(c3.LATTICES[name])
            self.assertEqual((sum(1 for t in tri if t[0] == "P"), sum(1 for t in tri if t[0] == "S")), (p, s), name)
            r = score(c3.LATTICES[name])
            self.assertEqual((r.proportional, r.subcontrary), (p, s), name + " frozen")

    def test_reflection_is_exact_inverse(self):
        inv = {c1._reduce(1 / t) for t in c3.LATTICES["dek52"]}
        self.assertEqual(inv, set(c3.LATTICES["dek52refl"]))


class TestDeviation(unittest.TestCase):
    def setUp(self):
        self.tones = c1.LATTICES["hexany"]
        self.tc = [c1.cents_of(t) for t in self.tones]
        self.triads = c2.prep_triads(self.tones)
        self.ks = (7, 2, 21, 16, 5, 18)   # the (16, 2, 5) val at N = 22
        self.g = 193.908

    def test_matches_mirror(self):
        voiced = c3.voiced_offsets(self.triads, self.tc, self.ks, self.g)
        pc = [c1.wrap(k * self.g) for k in self.ks]
        slow = c1.triad_deviations(self.tones, pc)
        for (lab, v), d in zip(voiced, slow):
            dev, sep = c3.signed_dev(lab, v, self.g)
            self.assertAlmostEqual(abs(dev), d["dev_cents"], places=9)
            self.assertAlmostEqual(sep, d["sep_cents"], places=9)

    def test_offsets_are_linear_in_g(self):
        voiced = c3.voiced_offsets(self.triads, self.tc, self.ks, self.g)
        again = c3.voiced_offsets(self.triads, self.tc, self.ks, self.g + 0.05)
        for (_, v1), (_, v2) in zip(voiced, again):
            for (k1, o1), (k2, o2) in zip(v1, v2):
                self.assertEqual(k1, k2)
                self.assertAlmostEqual(o1, o2, places=9)

    def test_alive_matches_fit_row_predicate(self):
        voiced = c3.voiced_offsets(self.triads, self.tc, self.ks, self.g)
        pc = [c1.wrap(k * self.g) for k in self.ks]
        mirror = [d["dev_cents"] <= 2.0 and d["sep_cents"] >= 2.0 for d in c1.triad_deviations(self.tones, pc)]
        self.assertEqual([c3.alive(lab, v, self.g) for lab, v in voiced], mirror)
        self.assertTrue(all(mirror))


class TestSearchPieces(unittest.TestCase):
    def setUp(self):
        self.tones = c1.LATTICES["hexany"]
        self.tc = [c1.cents_of(t) for t in self.tones]
        self.triads = c2.prep_triads(self.tones)
        self.ks = (7, 2, 21, 16, 5, 18)

    def test_basin_contains_g0_and_respects_cap(self):
        lo, hi = c3.basin(self.tc, self.ks, 193.908)
        self.assertLess(lo, 193.908)
        self.assertGreater(hi, 193.908)
        for g in (lo + 1e-6, hi - 1e-6):
            self.assertLessEqual(c2.tone_err(self.tc, self.ks, g), c3.TONE_CAP + 1e-6)
        self.assertGreater(c2.tone_err(self.tc, self.ks, hi + 0.01), c3.TONE_CAP)

    def test_survival_intervals_and_segments(self):
        lo, hi = c3.basin(self.tc, self.ks, 193.908)
        voiced = c3.voiced_offsets(self.triads, self.tc, self.ks, (lo + hi) / 2)
        dead_at_194_5 = 0
        for lab, v in voiced:
            ivs = c3.survival_intervals(lab, v, lo, hi)
            self.assertTrue(any(a <= 193.908 <= b for a, b in ivs))
            self.assertEqual(any(a <= 194.5 <= b for a, b in ivs), c3.alive(lab, v, 194.5))
            dead_at_194_5 += not c3.alive(lab, v, 194.5)
        self.assertGreater(dead_at_194_5, 0)   # a shared prime cancels in some triads, not all
        segs = c3.count_segments(voiced, lo, hi)
        top = max(segs, key=lambda s: s[0])
        self.assertEqual(top[0], 12)
        self.assertLess(top[1], 193.908)
        self.assertGreater(top[2], 193.908)
        self.assertAlmostEqual(top[1], 193.797, places=2)
        self.assertAlmostEqual(top[2], 193.997, places=2)

    def test_representative_is_cpsfit002_minimax_when_all_survive(self):
        lo, hi = c3.basin(self.tc, self.ks, 193.908)
        voiced = c3.voiced_offsets(self.triads, self.tc, self.ks, (lo + hi) / 2)
        segs = c3.count_segments(voiced, lo, hi)
        c, a, b = max(segs, key=lambda s: s[0])
        g, margin = c3.representative(voiced, a, b)
        self.assertAlmostEqual(g, 193.908, places=2)
        self.assertAlmostEqual(2.0 - margin, 1.156, places=2)

    def test_window_range(self):
        self.assertEqual(c3.window_range((7, 2, 21, 16, 5, 18), 22), (0, 0))
        self.assertEqual(c3.window_range((-9, -8, -3, -2, -1, -10), 11), (-10, -10))
        self.assertEqual(c3.window_range((1, 2, 3), 10), (-6, 0))

    def test_transposed_val(self):
        tones = self.tones
        self.assertEqual(c3.transposed_val(tones, list(self.ks), 22), ((16, 2, 5), 0))
        shifted = [k - 31 for k in self.ks]
        self.assertEqual(c3.transposed_val(tones, shifted, 31), ((16, 2, 5), -31))
        self.assertEqual(c3.transposed_val(tones, [0, 1, 2, 3, 4, 5], 22), (None, 0))


class TestFits(unittest.TestCase):
    def test_hexany_n22_registered(self):
        f = c3.fit_count(c1.LATTICES["hexany"], 22)
        self.assertEqual(f["count"], 12)
        self.assertAlmostEqual(f["g"], 193.908, places=2)
        self.assertEqual(f["s_range"], [0, 0])

    def test_hexany_n16_registered(self):
        f = c3.fit_count(c1.LATTICES["hexany"], 16)
        self.assertEqual(f["count"], 10)
        self.assertAlmostEqual(f["g"], 116.676, places=2)
        self.assertEqual(c1.homomorphism(c1.LATTICES["hexany"], f["ks"], 16), (6, -7, -2))

    def test_hexany_n11_registered(self):
        f = c3.fit_count(c1.LATTICES["hexany"], 11)
        self.assertEqual(f["count"], 6)
        self.assertAlmostEqual(f["g"], 249.211, places=2)
        self.assertAlmostEqual(f["eps"], 20.0, places=3)

    def test_eg4_n11_infeasible(self):
        self.assertIsNone(c3.fit_count(c1.LATTICES["eg4"], 11))


def _row(lat, n, count, exact, frozen, g, mapping, tone=None, triad=None, P=None, S=None, s=0, srange=None,
         dev=1.0, margin=0.5, tv=None):
    prior = {}
    if tone is not None:
        prior["tone"] = {"g_cents": tone[0], "frozen": tone[1], "exact_count": tone[1]}
    if triad is not None:
        prior["triad"] = {"g_cents": triad[0], "frozen": triad[1], "exact_count": triad[2] if len(triad) > 2 else triad[1]}
    return {"lattice": lat, "N": n, "count_exact": count, "exact_triads": exact, "survival_2c_frozen": frozen,
            "g_cents": g, "mapping": mapping, "eps_star_cents": 1.0, "transposed_val": tv, "prior": prior,
            "image_P": {"2.0": P if P is not None else count // 2}, "image_S": {"2.0": S if S is not None else count - count // 2},
            "window_start": s, "window_range": srange or [s, s], "max_triad_dev_cents": dev, "margin_cents": margin}


class TestVerdicts(unittest.TestCase):
    def test_p_c3_exceptions(self):
        rows = {"dek52": [_row("dek52", 18, 14, 41, 14, 497.514, None, tone=(497.5, 10), triad=(503.939, 15, 12))]}
        self.assertTrue(c3.verdict_p_c3(rows)["kept"])
        rows["dek52"][0]["prior"]["triad"]["frozen"] = 13
        self.assertFalse(c3.verdict_p_c3(rows)["kept"])

    def test_p_c5_reflection(self):
        a = _row("dek52", 26, 32, 41, 32, 498.066, (-1, 8, 14), P=19, S=13, s=-3, srange=[-3, -3])
        b = _row("dek52refl", 26, 32, 41, 32, 498.066, (-1, 8, 14), P=13, S=19, s=-22, srange=[-22, -22])
        c = _row("dek53", 26, 32, 41, 32, 498.066, (-1, 8, 14), P=13, S=19, s=-3)
        rows = {"dek52": [a], "dek52refl": [b], "dek53": [c]}
        v = c3.verdict_p_c5(rows)
        self.assertEqual(v["cps53_agree_N"], [26])
        self.assertFalse(any("reflection" in f for f in v["failures"]))
        b["image_P"]["2.0"], b["image_S"]["2.0"] = 19, 13
        self.assertTrue(any("P/S not swapped" in f for f in c3.verdict_p_c5(rows)["failures"]))

    def test_p_c7_created(self):
        rows = {"hexany": [_row("hexany", 11, 6, 12, 8, 249.211, (-2, -8, -1)),
                           _row("hexany", 22, 12, 12, 12, 193.908, (16, 2, 5))]}
        self.assertTrue(c3.verdict_p_c7(rows)["kept"])
        rows["hexany"][1]["survival_2c_frozen"] = 13
        self.assertFalse(c3.verdict_p_c7(rows)["kept"])


if __name__ == "__main__":
    unittest.main()
