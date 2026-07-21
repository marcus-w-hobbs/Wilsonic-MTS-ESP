"""Frozen triad scorer for the Wilson triad-optimization harness.

This module is the FROZEN VERIFIER of the experiment loop described in
plans/triad-optimization-loop.md. After human approval of its initial
version, agent-loop commits must never modify this file; desired changes
are flagged to Marcus instead. Every archived result records
SCORER_VERSION and (for the tempered path) the epsilon it was scored under.

Design rules (see plan §1):
- All triad math happens in FREQUENCY-RATIO space. An arithmetic mean of
  frequencies is not a cents midpoint.
- JI path: exact rationals (fractions.Fraction) end to end. Zero floats.
- Tempered path: degrees in cents; frequencies reconstructed as
  f = 2**(cents/1200); the single hyperparameter epsilon (cents) appears
  only in the comparison layer.
- Octave reduction is half-open [1, 2), matching the plugin's
  Microtone::octaveReduce (Source/Microtone.cpp:475-556).
- Loss: score_min = min(P, S) primary; score_product = P * S secondary;
  raw (P, S, G) always recorded. Geometric triads are counted but NEVER
  contribute to either loss (plan §1.3, §6).

Triad definitions, for frequencies a < b < c (plan §1.2):
- proportional (arithmetic mean, major prototype 4:5:6):  2b = a + c
- subcontrary (harmonic mean, minor prototype 10:12:15):  b(a+c) = 2ac
- geometric (b is geometric mean):                        b^2 = ac

For exact rationals the three conditions are mutually exclusive when
a < b < c (any two together force a = c).

TWO SAMPLING CONVENTIONS (decision pending before freeze — see LOG.md):

1. "two-octave-window" (score_rational / score_cents): the sample is
   T = S U 2S, all C(|T|, 3) triples classified. This is the convention
   written in plan §1.1. Verified caveats, discovered 2026-07-20:
   - The pipeline duality swap (invert scale -> re-reduce -> rescore) is
     exact ONLY for scales not containing 1/1. When 1/1 is a degree, the
     inverted sample is the reflection 4/T with the boundary element 4
     replaced by 1, and counts through the boundary differ. The underlying
     AM<->HM theorem is exact for every scale: classifying the reflected
     multiset 4/T always swaps P and S exactly.
   - NOT transposition-invariant: multiplying every degree by a constant
     and re-canonicalizing rotates the pitch circle and changes which
     cross-boundary triads land inside the [1, 4) window.

2. "middle-anchored" (score_rational_anchored / score_cents_anchored):
   for every scale degree b (the triad middle) in the canonical octave,
   the outer tones are the unique octave-shifted representatives of scale
   pitch classes inside the open windows a in (b/2, b), c in (b, 2b).
   Verified 2026-07-20 to be BOTH exactly self-dual for every scale
   (including those containing 1/1) AND exactly transposition-invariant.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import log2
from typing import Iterable, Optional, Union

SCORER_VERSION = "0.1.0"
DEFAULT_EPSILON_CENTS = 2.0

PROPORTIONAL = "proportional"
SUBCONTRARY = "subcontrary"
GEOMETRIC = "geometric"

RationalLike = Union[Fraction, int, str]

# ---------------------------------------------------------------------------
# rational (JI) path — exact arithmetic only
# ---------------------------------------------------------------------------


def reduce_rational(ratio: RationalLike) -> Fraction:
    """Octave-reduce a positive rational to the half-open interval [1, 2)."""
    r = Fraction(ratio)
    if r <= 0:
        raise ValueError(f"ratio must be positive, got {r}")
    while r < 1:
        r *= 2
    while r >= 2:
        r /= 2
    return r


def canonical_rational_scale(ratios: Iterable[RationalLike]) -> tuple[Fraction, ...]:
    """Octave-reduce to [1, 2), deduplicate exactly, sort ascending.

    Note: the scorer's canonical form is a set (duplicates removed). The
    plugin's CPS classes keep duplicates (CPSTuningBase.cpp:18); the
    plugin-canonical multiset belongs in archive metadata, not here.
    """
    reduced = {reduce_rational(r) for r in ratios}
    if not reduced:
        raise ValueError("scale must contain at least one ratio")
    return tuple(sorted(reduced))


def invert_rational_scale(ratios: Iterable[RationalLike]) -> tuple[Fraction, ...]:
    """Reciprocal of every degree, re-reduced: the period-space dual."""
    return canonical_rational_scale(1 / Fraction(r) for r in ratios)


def two_octave_sample_rational(scale: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    """T = S U 2S for a canonical scale S in [1, 2). Strictly ascending."""
    return scale + tuple(2 * s for s in scale)


def classify_rational_triple(
    a: RationalLike, b: RationalLike, c: RationalLike
) -> Optional[str]:
    """Classify an exact triple with a < b < c; None if no mean relation."""
    fa, fb, fc = Fraction(a), Fraction(b), Fraction(c)
    if not fa < fb < fc:
        raise ValueError(f"require a < b < c, got {fa}, {fb}, {fc}")
    if 2 * fb == fa + fc:
        return PROPORTIONAL
    if fb * (fa + fc) == 2 * fa * fc:
        return SUBCONTRARY
    if fb * fb == fa * fc:
        return GEOMETRIC
    return None


# ---------------------------------------------------------------------------
# tempered (cents) path — epsilon appears here and only here
# ---------------------------------------------------------------------------


def reduce_cents(cents: float) -> float:
    """Reduce a cents value mod 1200 into [0, 1200)."""
    return float(cents) % 1200.0


def canonical_cents_scale(
    cents: Iterable[float], dedup_epsilon_cents: float = 1e-6
) -> tuple[float, ...]:
    """Reduce mod 1200, sort, collapse duplicates closer than dedup epsilon."""
    reduced = sorted(reduce_cents(c) for c in cents)
    if not reduced:
        raise ValueError("scale must contain at least one degree")
    out: list[float] = []
    for c in reduced:
        if not out or c - out[-1] > dedup_epsilon_cents:
            out.append(c)
    # 0 and ~1200 are the same pitch class across the wrap
    if len(out) > 1 and (1200.0 - out[-1]) <= dedup_epsilon_cents and out[0] <= dedup_epsilon_cents:
        out.pop()
    return tuple(out)


def invert_cents_scale(
    cents: Iterable[float], dedup_epsilon_cents: float = 1e-6
) -> tuple[float, ...]:
    """Negate every degree, re-reduce: the period-space dual in cents."""
    return canonical_cents_scale((-c for c in cents), dedup_epsilon_cents)


def two_octave_sample_cents(scale: tuple[float, ...]) -> tuple[float, ...]:
    """T = S U (S + 1200) for a canonical scale S in [0, 1200)."""
    return scale + tuple(c + 1200.0 for c in scale)


def classify_cents_triple(
    a_cents: float,
    b_cents: float,
    c_cents: float,
    epsilon_cents: float = DEFAULT_EPSILON_CENTS,
) -> frozenset[str]:
    """Classify a tempered triple with a < b < c (cents).

    Frequencies are reconstructed as f = 2**(cents/1200); each mean
    condition is checked as a deviation in cents against epsilon. Returns a
    frozenset because near-degenerate triples can satisfy more than one
    condition within epsilon (unlike the exact path).
    """
    if not a_cents < b_cents < c_cents:
        raise ValueError(f"require a < b < c, got {a_cents}, {b_cents}, {c_cents}")
    fa = 2.0 ** (a_cents / 1200.0)
    fb = 2.0 ** (b_cents / 1200.0)
    fc = 2.0 ** (c_cents / 1200.0)
    labels = set()
    if abs(1200.0 * log2((fa + fc) / (2.0 * fb))) < epsilon_cents:
        labels.add(PROPORTIONAL)
    if abs(1200.0 * log2(fb * (fa + fc) / (2.0 * fa * fc))) < epsilon_cents:
        labels.add(SUBCONTRARY)
    if abs(1200.0 * log2((fa * fc) / (fb * fb))) < epsilon_cents:
        labels.add(GEOMETRIC)
    return frozenset(labels)


# ---------------------------------------------------------------------------
# scoring records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreResult:
    """Immutable scoring record. Everything needed for provenance except
    the generating parameters, which the archive layer records alongside."""

    proportional: int
    subcontrary: int
    geometric: int
    score_min: int
    score_product: int
    path: str  # "rational" | "cents"
    convention: str  # "two-octave-window" | "middle-anchored"
    epsilon_cents: Optional[float]  # None on the rational path
    scorer_version: str
    scale: tuple
    sample_size: int


def _result(p: int, s: int, g: int, *, path: str, convention: str,
            epsilon_cents: Optional[float], scale: tuple,
            sample_size: int) -> ScoreResult:
    return ScoreResult(
        proportional=p,
        subcontrary=s,
        geometric=g,
        score_min=min(p, s),
        score_product=p * s,
        path=path,
        convention=convention,
        epsilon_cents=epsilon_cents,
        scorer_version=SCORER_VERSION,
        scale=scale,
        sample_size=sample_size,
    )


# ---------------------------------------------------------------------------
# convention 1: two-octave window (plan §1.1 as written)
# ---------------------------------------------------------------------------


def score_rational(ratios: Iterable[RationalLike]) -> ScoreResult:
    """Score a JI scale with exact arithmetic over its two-octave sample."""
    scale = canonical_rational_scale(ratios)
    sample = two_octave_sample_rational(scale)
    p = s = g = 0
    for a, b, c in combinations(sample, 3):
        label = classify_rational_triple(a, b, c)
        if label == PROPORTIONAL:
            p += 1
        elif label == SUBCONTRARY:
            s += 1
        elif label == GEOMETRIC:
            g += 1
    return _result(p, s, g, path="rational", convention="two-octave-window",
                   epsilon_cents=None, scale=scale, sample_size=len(sample))


def score_cents(
    cents: Iterable[float],
    epsilon_cents: float = DEFAULT_EPSILON_CENTS,
) -> ScoreResult:
    """Score a tempered scale (degrees in cents) over its two-octave sample."""
    scale = canonical_cents_scale(cents)
    sample = two_octave_sample_cents(scale)
    p = s = g = 0
    for a, b, c in combinations(sample, 3):
        labels = classify_cents_triple(a, b, c, epsilon_cents)
        if PROPORTIONAL in labels:
            p += 1
        if SUBCONTRARY in labels:
            s += 1
        if GEOMETRIC in labels:
            g += 1
    return _result(p, s, g, path="cents", convention="two-octave-window",
                   epsilon_cents=epsilon_cents, scale=scale,
                   sample_size=len(sample))


# ---------------------------------------------------------------------------
# convention 2: middle-anchored octave windows
# (exactly self-dual and transposition-invariant; candidate primary)
# ---------------------------------------------------------------------------


def _shift_rational_into_open(x: Fraction, lo: Fraction, hi: Fraction) -> Optional[Fraction]:
    """Unique 2**k * x inside the open octave window (lo, hi), hi == 2*lo.

    Returns None when x's pitch class lands exactly on the boundary
    (x * 2**k == lo), i.e. when x is octave-equivalent to lo.
    """
    r = x
    while r <= lo:
        r *= 2
    while r >= hi:
        r /= 2
    return r if lo < r < hi else None


def score_rational_anchored(ratios: Iterable[RationalLike]) -> ScoreResult:
    """Middle-anchored exact scoring: for each degree b in the canonical
    octave, classify (a, b, c) where a and c are the unique representatives
    of every scale pitch class in (b/2, b) and (b, 2b) respectively."""
    scale = canonical_rational_scale(ratios)
    p = s = g = 0
    for b in scale:
        half_b = b / 2
        two_b = 2 * b
        lows = [r for pc in scale
                if (r := _shift_rational_into_open(pc, half_b, b)) is not None]
        highs = [r for pc in scale
                 if (r := _shift_rational_into_open(pc, b, two_b)) is not None]
        for a in lows:
            for c in highs:
                label = classify_rational_triple(a, b, c)
                if label == PROPORTIONAL:
                    p += 1
                elif label == SUBCONTRARY:
                    s += 1
                elif label == GEOMETRIC:
                    g += 1
    return _result(p, s, g, path="rational", convention="middle-anchored",
                   epsilon_cents=None, scale=scale,
                   sample_size=len(scale))


def _cents_rep_below(pitch_class: float, b: float) -> Optional[float]:
    """Unique representative of pitch_class in the open window (b-1200, b)."""
    offset = (pitch_class - b) % 1200.0
    if offset == 0.0:
        return None  # octave-equivalent to b: boundary
    return b - 1200.0 + offset


def _cents_rep_above(pitch_class: float, b: float) -> Optional[float]:
    """Unique representative of pitch_class in the open window (b, b+1200)."""
    offset = (pitch_class - b) % 1200.0
    if offset == 0.0:
        return None
    return b + offset


def score_cents_anchored(
    cents: Iterable[float],
    epsilon_cents: float = DEFAULT_EPSILON_CENTS,
) -> ScoreResult:
    """Middle-anchored tempered scoring; see score_rational_anchored."""
    scale = canonical_cents_scale(cents)
    p = s = g = 0
    for b in scale:
        lows = [r for pc in scale if (r := _cents_rep_below(pc, b)) is not None]
        highs = [r for pc in scale if (r := _cents_rep_above(pc, b)) is not None]
        for a in lows:
            for c in highs:
                labels = classify_cents_triple(a, b, c, epsilon_cents)
                if PROPORTIONAL in labels:
                    p += 1
                if SUBCONTRARY in labels:
                    s += 1
                if GEOMETRIC in labels:
                    g += 1
    return _result(p, s, g, path="cents", convention="middle-anchored",
                   epsilon_cents=epsilon_cents, scale=scale,
                   sample_size=len(scale))
