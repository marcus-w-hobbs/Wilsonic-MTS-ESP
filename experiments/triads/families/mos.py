"""MOS (moment of symmetry) generator — Brun/scale-tree zigzag.

Mirrors the plugin's construction, cross-validated against the real C++
on 2026-07-21 (crossval002: 15 scales, cardinality-exact, degrees within
1 ulp): cardinality at a level is the denominator of the level-th zigzag
fraction (Brun.cpp:269-299), and scale degrees are generator multiples
mod 1 in log-octave space at murchana 0 (Brun.cpp:308-357).

This module computes in float64 for research precision; the float32
plugin-faithful path lives in cpp_mirror/crossval002. Generators are
expressed as a fraction of the period in [0, 1] (g01); cents = 1200*g01.
"""

from __future__ import annotations

from typing import Iterable

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import canonical_cents_scale  # noqa: E402

MIN_LEVEL = 0
MAX_LEVEL = 9  # Brun.h:43-44


def zigzag(g01: float, max_level: int = MAX_LEVEL) -> list[tuple[int, int]]:
    """The scale-tree zigzag fractions (num, den) for levels 0..max_level.

    den at index L is the MOS cardinality at level L; num is the number
    of periods spanned by the generator chain (num/den approximates g01).
    """
    if not 0.0 <= g01 <= 1.0:
        raise ValueError(f"g01 must be in [0, 1], got {g01}")
    mos_a, mos_b = 1.0, g01
    x1, x2, y1, y2 = 1, 0, 0, 1
    num = den = 1
    out = [(1, 1)]
    for _ in range(max_level):
        num = 2 * y1 + y2
        den = 2 * x1 + x2
        mos_a = mos_a - mos_b
        x2 = x1 + x2
        y2 = y1 + y2
        if mos_b > mos_a:
            mos_a, mos_b = mos_b, mos_a
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        out.append((num, den))
    return out


def mos_cardinalities(g01: float, max_level: int = MAX_LEVEL) -> list[int]:
    """Distinct MOS cardinalities for a generator, ascending."""
    seen = []
    for _, den in zigzag(g01, max_level):
        if den not in seen:
            seen.append(den)
    return seen


def mos_cents(g01: float, cardinality: int) -> tuple[float, ...]:
    """The MOS scale of the given cardinality: degree*g mod 1 in
    log-octave space (murchana 0), canonicalized to sorted cents."""
    return canonical_cents_scale(
        (degree * g01 * 1200.0) % 1200.0 for degree in range(cardinality))


def mos_scales(g01: float, min_card: int = 5, max_card: int = 22,
               max_level: int = MAX_LEVEL) -> dict[int, tuple[float, ...]]:
    """All MOS scales for a generator with cardinality in [min_card,
    max_card], keyed by cardinality."""
    return {
        n: mos_cents(g01, n)
        for n in mos_cardinalities(g01, max_level)
        if min_card <= n <= max_card
    }
