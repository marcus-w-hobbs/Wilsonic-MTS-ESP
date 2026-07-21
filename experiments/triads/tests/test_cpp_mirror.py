"""Pin the float32 mirror's behavior (hermetic — no compiler needed).

The mirror's fidelity to the real C++ is established by crossval001.py,
which compiles and runs the plugin's actual Microtone.cpp/Fraction.cpp and
asserts bit-level agreement (27/27 cases, 2026-07-20, results/
crossval001.json). These unit tests freeze the mirror itself so any drift
is caught without needing g++.
"""

from __future__ import annotations

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
    """Golden counts from the 2026-07-20 crossval run (results/
    crossval001.json). NOTE: analyzer-mirror fidelity to TuningImp.cpp is
    established by line-by-line reading, not yet by execution — see
    VERIFICATION.md."""

    def test_hexany_1357_plugin_counts(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        counts = cm.analyze_proportional_triads(freqs)
        self.assertEqual((counts.proportional, counts.subcontrary), (2, 2))

    def test_hexany_1357_without_interval_filter(self):
        freqs = cm.hexany_frequencies_f32([1.0, 3.0, 5.0, 7.0])
        counts = cm.analyze_proportional_triads(freqs, interval_filter=False)
        self.assertEqual((counts.proportional, counts.subcontrary), (4, 2))

    def test_segment_plugin_counts(self):
        seg = sorted(cm.f32(h / 8.0) for h in range(8, 16))  # canonical, no dup 2
        counts = cm.analyze_proportional_triads(seg)
        self.assertEqual((counts.proportional, counts.subcontrary), (8, 1))

    def test_fewer_than_three_tones(self):
        counts = cm.analyze_proportional_triads([1.0, 1.5])
        self.assertEqual((counts.proportional, counts.subcontrary), (0, 0))


if __name__ == "__main__":
    unittest.main()
