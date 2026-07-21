"""Bit-exact float32 mirror of the plugin's numeric conventions.

Purpose: an executable, independently-reviewable model of what the C++
actually computes — the bridge between the plugin (float32) and the exact
rational scorer. Fidelity is PROVEN, not assumed: crossval001.py compares
every function here against the real compiled C++ (cpp_receipts/) at the
IEEE-754 bit level.

Why this works: Python floats are IEEE binary64. For float32 operands,
computing +, -, *, / in binary64 and rounding the result to binary32 gives
exactly the same bits as native binary32 arithmetic (binary64 has 53 >=
2*24 + 2 significand bits, so no double-rounding hazard). f32() performs
that rounding via ctypes.

Mirrored code, with sources:
- Microtone::octaveReduce float path      (Source/Microtone.cpp:526-556)
- Microtone::octaveReduce rational path   (Source/Microtone.cpp:493-525)
  including Fraction::floatValue = float(num)/float(den) (Fraction.h:34)
- CPSTuningBase::multiplyByCommonTones    (CPSTuningBase.cpp:94-125)
  NOTE: tones multiply in shortDescriptionText string-sort order
  (CPSTuningBase.h:100-104). Float multiplication is bitwise commutative,
  so order is irrelevant for k=2 (hexany); for k>=3 associativity makes
  order matter and the mirror replicates the string sort.
- TuningImp::_analyzeProportionalTriads   (Source/TuningImp.cpp:782-857)
  with each of its three deviations from the exact scorer individually
  toggleable so divergence can be attributed.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional, Sequence

F32_TOLERANCE = 0.0005  # TuningImp.cpp:809 — double, absolute, linear frequency
MAJOR_2ND = None  # set below: float(9.f/8.f)
FOURTH = None  # set below: float(4.f/3.f)


def f32(x: float) -> float:
    """Round a binary64 value to the nearest binary32 (returned as float)."""
    return ctypes.c_float(x).value


MAJOR_2ND = f32(9.0 / 8.0)  # TuningImp.cpp:822
FOURTH = f32(4.0 / 3.0)  # TuningImp.cpp:823


def microtone_octave_reduce_float(f: float, period: float = 2.0) -> float:
    """Mirror of Microtone::octaveReduce, float path, Space::Linear."""
    if f <= 0.0:
        raise ValueError("frequency must be positive")
    f = f32(f)
    period = f32(period)
    while f < 1.0:
        f = f32(f * period)
    while f >= period:
        f = f32(f / period)
    return f


def fraction_float_value(fr: Fraction) -> float:
    """Mirror of Fraction::floatValue: float(num) / float(den)."""
    return f32(f32(float(fr.numerator)) / f32(float(fr.denominator)))


def microtone_octave_reduce_rational(fr: Fraction, period: int = 2) -> Fraction:
    """Mirror of Microtone::octaveReduce, rational path.

    The arithmetic is exact (Fraction mult/div) but the LOOP CONDITIONS
    compare floatValue() — reproducing the plugin's boundary behavior,
    e.g. (2**25-1)/2**24 reduces to 33554431/33554432 < 1 because its
    floatValue rounds to exactly 2.0f (receipt: cpp_receipts case
    r_boundary_2e25).
    """
    if fr <= 0:
        raise ValueError("ratio must be positive")
    period_r = Fraction(period)
    while fraction_float_value(fr) >= float(period):
        fr = fr / period_r
    while fraction_float_value(fr) < 1.0:
        fr = fr * period_r
    return fr


def cps_product_reduce(seeds: Sequence[float]) -> float:
    """Mirror of one CPS tone: multiplyByCommonTones product (float,
    string-sort order) then octave reduction at period 2."""
    ordered = sorted((f32(s) for s in seeds), key=lambda v: str(v))
    f = f32(1.0)
    for s in ordered:
        f = f32(f * s)
    return microtone_octave_reduce_float(f)


def hexany_frequencies_f32(seeds: Sequence[float]) -> tuple[float, ...]:
    """The plugin-canonical hexany: octave-reduced pairwise float products,
    sorted ascending, duplicates KEPT (CPSTuningBase never uniquifies)."""
    if len(seeds) != 4:
        raise ValueError("hexany needs 4 seeds")
    tones = []
    for i in range(4):
        for j in range(i + 1, 4):
            tones.append(cps_product_reduce([seeds[i], seeds[j]]))
    return tuple(sorted(tones))


@dataclass(frozen=True)
class AnalyzerCounts:
    proportional: int
    subcontrary: int


def analyze_proportional_triads(
    frequencies: Sequence[float],
    octave: float = 2.0,
    tolerance: float = F32_TOLERANCE,
    interval_filter: bool = True,
    npo_map_filter: bool = True,
) -> AnalyzerCounts:
    """Mirror of TuningImp::_analyzeProportionalTriads (TuningImp.cpp:767-890
    post paint-split; validated against the REAL compiled analyzer by
    tests/test_tuning on 2026-07-20).

    frequencies: the _processedArray — octave-reduced float frequencies,
    sorted ascending (the analyzer assumes sorted input).

    Plugin semantics mirrored exactly:
    - i (root) over [0, npo); j (fifth) over [i+2, npo+2) wrapping one
      degree past the octave with a single octave factor; k (third)
      strictly between.
    - major = (imf + jmf) / 2; minor = 2*(imf*jmf)/(imf+jmf), all float32.
    - interval filter: mean/root strictly between 9/8 and 4/3 (float32).
    - |mean - kmf| < 0.0005 (absolute, linear frequency, double compare).
    - dedup by unordered WRAPPED index set {i, k%npo, j%npo}, but the
      stored triad keeps the UNWRAPPED (i, k, j) of its FIRST discovery.
    - npo-map filter (TuningImp.cpp:849-858 + MicrotoneArray::npoOverride):
      the final triad lists keep only triads whose stored UNWRAPPED
      indices are all < npo — i.e. EVERY octave-wrapping triad the loop's
      wrap machinery finds is silently dropped. Discovered by executing
      the real analyzer: it reports (1,2) for the 1-3-5-7 hexany where
      the loop itself finds (2,2).

    interval_filter=False disables the 9/8..4/3 gate; npo_map_filter=False
    reports the loop-level counts before the wrap-drop. Both toggles exist
    for divergence attribution; defaults are plugin-exact.
    """
    npo = len(frequencies)
    if npo < 3:
        return AnalyzerCounts(0, 0)
    freqs = [f32(f) for f in frequencies]
    octave = f32(octave)
    pmt: dict[frozenset, tuple[int, int]] = {}
    smt: dict[frozenset, tuple[int, int]] = {}
    for i in range(npo):
        imf = freqs[i]
        for j in range(i + 2, npo + 2):
            ji = j % npo
            jfac = octave if ji < j else f32(1.0)
            jmf = f32(jfac * freqs[ji])
            major = f32(f32(imf + jmf) / f32(2.0))
            minor = f32(f32(2.0 * f32(imf * jmf)) / f32(imf + jmf))
            major_ratio = f32(major / imf)
            minor_ratio = f32(minor / imf)
            major_in = MAJOR_2ND < major_ratio < FOURTH if interval_filter else True
            minor_in = MAJOR_2ND < minor_ratio < FOURTH if interval_filter else True
            for k in range(i + 1, j):
                ki = k % npo
                kfac = octave if ki < k else f32(1.0)
                kmf = f32(kfac * freqs[ki])
                if major_in and abs(f32(major - kmf)) < tolerance:
                    key = frozenset({i, ki, ji})
                    if key not in pmt:
                        pmt[key] = (k, j)
                if minor_in and abs(f32(minor - kmf)) < tolerance:
                    key = frozenset({i, ki, ji})
                    if key not in smt:
                        smt[key] = (k, j)

    def _count(found: dict) -> int:
        if not npo_map_filter:
            return len(found)
        return sum(1 for (k, j) in found.values() if k < npo and j < npo)

    return AnalyzerCounts(_count(pmt), _count(smt))
