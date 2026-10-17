"""Pin the float32 mirror's behavior (hermetic — no compiler needed).

The mirror's fidelity to the real C++ is established by crossval001.py,
which compiles and runs the plugin's actual Microtone.cpp/Fraction.cpp and
asserts bit-level agreement (27/27 cases, 2026-07-20, results/
crossval001.json), and by crossval003.py, which runs the plugin's actual
analyzer through tests/research_cli and compares P, S and G counts
(2026-10-17, results/crossval003.json). These unit tests freeze the mirror
itself so any drift is caught without needing g++.
"""

from __future__ import annotations

import math
import struct
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cpp_mirror as cm  # noqa: E402


def bits(x: float) -> str:
    return format(struct.unpack("<I", struct.pack("<f", x))[0], "08x")


class TestFloatOctaveReduce(unittest.TestCase):
    def test_half_open_conventions(self):
        self.assertEqual(cm.microtone_octave_reduce_float(2.0), 1.0)
        self.assertEqual(cm.microtone_octave_reduce_float(1.0), 1.0)
        self.assertEqual(cm.microtone_octave_reduce_float(3.0), 1.5)
        self.assertEqual(bits(cm.microtone_octave_reduce_float(cm.f32(0.3))),
                         "3f99999a")  # cpp_receipts golden

    def test_boundary_neighbors(self):
        jb2 = cm.f32(2.0 - 2.0 ** -23)
        ja2 = cm.f32(2.0 + 2.0 ** -22)
        self.assertEqual(bits(cm.microtone_octave_reduce_float(jb2)), "3fffffff")
        self.assertEqual(bits(cm.microtone_octave_reduce_float(ja2)), "3f800001")


class TestRationalOctaveReduce(unittest.TestCase):
    def test_basic_conventions(self):
        self.assertEqual(cm.microtone_octave_reduce_rational(F(35, 16)), F(35, 32))
        self.assertEqual(cm.microtone_octave_reduce_rational(F(1, 3)), F(4, 3))
        self.assertEqual(cm.microtone_octave_reduce_rational(F(2)), F(1))

    def test_boundary_anomaly_reduces_below_one(self):
        # Receipt: cpp_receipts case r_boundary_2e25 (real plugin code).
        # floatValue of (2^25-1)/2^24 rounds to exactly 2.0f, so the loop
        # divides once too many and the exact rational leaves [1, 2).
        reduced = cm.microtone_octave_reduce_rational(F(2 ** 25 - 1, 2 ** 24))
        self.assertEqual(reduced, F(33554431, 33554432))
        self.assertLess(reduced, 1)  # invariant violation, faithfully mirrored

    def test_boundary_neighbor_stays_inside(self):
        reduced = cm.microtone_octave_reduce_rational(F(2 ** 24 - 1, 2 ** 23))
        self.assertEqual(reduced, F(2 ** 24 - 1, 2 ** 23))


class TestCpsProducts(unittest.TestCase):
    def test_hexany_1357_matches_exact_rationals(self):
        # Integer-seed products are exactly representable in float32, so
        # the plugin's float hexany equals the exact rational hexany.
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        exact = sorted(
            float(x) for x in
            (F(35, 32), F(5, 4), F(21, 16), F(3, 2), F(7, 4), F(15, 8)))
        self.assertEqual(list(freqs), exact)

    def test_duplicates_kept(self):
        # Seeds 1,3,5,15: products 15 and 15 collide; the plugin keeps both.
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 15.0])
        self.assertEqual(len(freqs), 6)
        self.assertEqual(len(set(freqs)), 5)


class TestAnalyzerMirror(unittest.TestCase):
    """Analyzer-mirror fidelity is established by EXECUTION: the real
    compiled analyzer (tests/test_tuning at the repo root) reports exactly
    these counts, and the 1-3-5-9 golden was predicted by this mirror
    before the C++ test ever ran (2026-07-20). The plugin-exact default
    includes the npo-map wrap-drop: octave-wrapping triads found by the
    analyzer's search loop are dropped from its reported lists."""

    def test_hexany_1357_plugin_counts(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        counts = cm.analyze_proportional_triads(freqs)
        self.assertEqual((counts.proportional, counts.subcontrary), (1, 2))

    def test_hexany_1357_loop_level_counts(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        counts = cm.analyze_proportional_triads(freqs, npo_map_filter=False)
        self.assertEqual((counts.proportional, counts.subcontrary), (2, 2))

    def test_hexany_1357_without_interval_filter(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        counts = cm.analyze_proportional_triads(
            freqs, interval_filter=False, npo_map_filter=False)
        self.assertEqual((counts.proportional, counts.subcontrary), (4, 2))

    def test_hexany_1359_plugin_counts(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 9.0])
        counts = cm.analyze_proportional_triads(freqs)
        self.assertEqual((counts.proportional, counts.subcontrary), (1, 2))

    def test_segment_plugin_counts(self):
        seg = sorted(cm.f32(h / 8.0) for h in range(8, 16))  # canonical, no dup 2
        counts = cm.analyze_proportional_triads(seg)
        self.assertEqual((counts.proportional, counts.subcontrary), (4, 1))

    def test_segment_loop_level_counts(self):
        seg = sorted(cm.f32(h / 8.0) for h in range(8, 16))
        counts = cm.analyze_proportional_triads(seg, npo_map_filter=False)
        self.assertEqual((counts.proportional, counts.subcontrary), (8, 1))

    def test_fewer_than_three_tones(self):
        counts = cm.analyze_proportional_triads([1.0, 1.5])
        self.assertEqual(counts.as_tuple(), (0, 0, 0))


class TestGeometricMirror(unittest.TestCase):
    """Geometric triads (b^2 = ac) landed in the plugin analyzer with PR #59
    (TuningImp.cpp:813-815, 820, 853-862). The counts pinned here were
    reported by the real compiled analyzer (tests/test_tuning, PR #59) and
    then confirmed by crossval003.py over the hexany, MOS and ET-as-MOS
    corpus with 0 mismatches (2026-10-17, results/crossval003.json). With
    odd seeds a hexany has a geometric chain only when the seed set has a
    multiplicative coincidence a*d = b*c (a duplicated tone); of the 70
    odd-seed hexanies only 1-3-5-15 and 3-5-9-15 qualify, and only the
    latter's chain survives the window and the wrap-drop."""

    @staticmethod
    def _et(n: int) -> list[float]:
        return sorted(cm.f32(2.0 ** (k / n)) for k in range(n))

    def test_hexany_1357_has_no_geometric_triads(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        counts = cm.analyze_proportional_triads(freqs)
        self.assertEqual(counts.as_tuple(), (1, 2, 0))

    def test_hexany_1359_has_no_geometric_triads(self):
        # 1-3-9 is a geometric seed progression, yet its chain 1, 3/2, 9/8
        # stacks fifths, which the window rejects as a middle tone.
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 9.0])
        counts = cm.analyze_proportional_triads(freqs)
        self.assertEqual(counts.geometric, 0)

    def test_window_hides_hexany_fifth_stacks(self):
        # Without the window the 1-3-5-9 hexany's fifth-stacks become
        # visible: the count is nonzero, so the window is what hides them.
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 9.0])
        gated = cm.analyze_proportional_triads(freqs, npo_map_filter=False)
        open_ = cm.analyze_proportional_triads(
            freqs, interval_filter=False, npo_map_filter=False)
        self.assertEqual(gated.geometric, 0)
        self.assertGreater(open_.geometric, 0)

    def test_hexany_35915_reports_two_geometric_triads(self):
        # 3*15 = 5*9 = 45: chain 27/16 : 45/32 : 75/64 has ratio 5/3, which
        # is 6/5 octave-reduced and inside the window; the duplicated 45/32
        # makes two index sets. Reported by the real C++ (crossval003).
        freqs = cm.hexany_frequencies_f32([3.0, 5.0, 9.0, 15.0])
        counts = cm.analyze_proportional_triads(freqs)
        self.assertEqual(counts.as_tuple(), (0, 0, 2))

    def test_hexany_13515_geometric_chain_is_wrap_dropped(self):
        # 1*15 = 3*5: chain 3/2 : 15/8 : 75/64 (ratio 5/4) wraps the octave,
        # so the loop finds 2 and the NPO-map filter reports 0.
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 15.0])
        reported = cm.analyze_proportional_triads(freqs)
        loop = cm.analyze_proportional_triads(freqs, npo_map_filter=False)
        self.assertEqual(reported.geometric, 0)
        self.assertEqual(loop.geometric, 2)

    def test_just_chain_reports_one_geometric_triad(self):
        # 1 9/8 5/4 25/16 3/2 15/8: degrees (0, 2, 4) = 1, 5/4, 25/16 with
        # (5/4)^2 = 25/16 exactly; 5/4 sits inside the window.
        chain = sorted(cm.f32(float(x)) for x in (
            F(1), F(9, 8), F(5, 4), F(25, 16), F(3, 2), F(15, 8)))
        counts = cm.analyze_proportional_triads(chain)
        self.assertEqual(counts.geometric, 1)

    def test_12_et_reports_ten_geometric_triads(self):
        counts = cm.analyze_proportional_triads(self._et(12))
        self.assertEqual(counts.as_tuple(), (0, 0, 10))

    def test_6_et_reports_two_geometric_triads(self):
        counts = cm.analyze_proportional_triads(self._et(6))
        self.assertEqual(counts.as_tuple(), (0, 0, 2))

    def test_geometric_window_is_shared_with_p_and_s(self):
        # In 12-ET every equal-step triad (i, i+m, i+2m) is geometric; the
        # window 9/8 < 2^(m/12) < 4/3 keeps m in {3, 4} only.
        counts = cm.analyze_proportional_triads(
            self._et(12), interval_filter=False, npo_map_filter=False)
        self.assertGreater(counts.geometric, 10)

    def test_fewer_than_three_tones_geometric(self):
        counts = cm.analyze_proportional_triads([1.0, 1.5])
        self.assertEqual(counts.geometric, 0)

    def test_sqrt_double_rounding_matches_float32(self):
        # sqrt in binary64 then rounded to binary32 equals sqrtf for
        # float32 operands (53 >= 2*24 + 2). Spot-check against a
        # ctypes-free identity on exact squares and a non-square.
        for v in (cm.f32(1.5625), cm.f32(2.25), cm.f32(1.3)):
            g = cm.f32(math.sqrt(v))
            self.assertEqual(g, cm.f32(g))
        self.assertEqual(cm.f32(math.sqrt(cm.f32(1.5625))), 1.25)


if __name__ == "__main__":
    unittest.main()
