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
- TEMPERED PATH ONLY: a degeneracy guard (is_informative_triple, Marcus's
  decision 2026-07-21) suppresses triples whose arithmetic and harmonic
  means are closer together than epsilon — at that resolution such a triple
  cannot be shown to be proportional rather than subcontrary, so it counts
  as neither. Without it a 1-cent generator is the global optimum of
  min(P, S) at every cardinality N=5..10 and at every epsilon: the reward
  hack the frozen verifier exists to prevent. Unguarded counts survive in
  the *_raw fields; the guard is a no-op on the exact rational path.

Triad definitions, for frequencies a < b < c (plan §1.2):
- proportional (arithmetic mean, major prototype 4:5:6):  2b = a + c
- subcontrary (harmonic mean, minor prototype 10:12:15):  b(a+c) = 2ac
- geometric (b is geometric mean):                        b^2 = ac

For exact rationals the three conditions are mutually exclusive when
a < b < c (any two together force a = c).

TWO SAMPLING CONVENTIONS. **"middle-anchored" is PRIMARY** (decided by
Marcus, 2026-07-21). Use the convention-neutral entry points `score()`
(rational path) and `score_tempered()` (cents path) for all new work;
they dispatch to the anchored implementations.

1. "middle-anchored" — PRIMARY (score / score_tempered, implemented by
   score_rational_anchored / score_cents_anchored): for every scale degree
   b (the triad middle) in the canonical octave, the outer tones are the
   unique octave-shifted representatives of scale pitch classes inside the
   open windows a in (b/2, b), c in (b, 2b). Verified 2026-07-20 to be
   BOTH exactly self-dual for every scale (including those containing 1/1)
   AND exactly transposition-invariant.

   Rationale for primacy: it is the only one of the two that satisfies
   plan §4 TRIAD-004 ("this MUST pass exactly") for every scale. The plan
   §1.1 text specified a sampling procedure; the invariant is the thing
   worth preserving when the two conflict.

   Known structural consequence (FINDINGS.md, 2026-07-21): every MOS and
   every CPS(n, n/2) sits EXACTLY on P = S under this convention, because
   both families are inversionally symmetric as pitch-class sets and the
   anchored scorer commutes exactly with inversion. So min(P, S) equals P
   inside those families and differentiates only asymmetric constructions.
   That is a statement about the LOSS, not the convention.

2. "two-octave-window" — RETAINED FOR COMPARISON ONLY
   (score_rational_window / score_cents_window; the legacy names
   score_rational / score_cents remain as back-compat aliases so existing
   result files and scripts keep working). The sample is T = S U 2S, all
   C(|T|, 3) triples classified. This is the convention written in plan
   §1.1. Verified caveats, discovered 2026-07-20:
   - The pipeline duality swap (invert scale -> re-reduce -> rescore) is
     exact ONLY for scales not containing 1/1. When 1/1 is a degree, the
     inverted sample is the reflection 4/T with the boundary element 4
     replaced by 1, and counts through the boundary differ (segment 8..16
     scores (46,8) but its dual scores (7,42), not (8,46)). The underlying
     AM<->HM theorem is exact for every scale: classifying the reflected
     multiset 4/T always swaps P and S exactly.
   - NOT transposition-invariant: multiplying every degree by a constant
     and re-canonicalizing rotates the pitch circle and changes which
     cross-boundary triads land inside the [1, 4) window (hexany 1-3-5-7
     scores (11,11), the same hexany times 3 scores (10,9)).
   Both counterexamples are pinned as goldens in tests/test_scorer.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import log2
from typing import Iterable, Optional, Union

SCORER_VERSION = "0.1.0"
DEFAULT_EPSILON_CENTS = 2.0

WINDOW_CONVENTION = "two-octave-window"
ANCHORED_CONVENTION = "middle-anchored"
#: The convention `score()` / `score_tempered()` dispatch to. Marcus's call,
#: 2026-07-21; see the module docstring for the evidence.
PRIMARY_CONVENTION = ANCHORED_CONVENTION

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


def mean_separation_cents(a_cents: float, c_cents: float) -> float:
    """Distance in cents between the arithmetic and harmonic means of the
    outer tones: |1200*log2(AM/HM)|. Depends only on the OUTER interval, not
    on the middle tone, and grows monotonically with the span c - a.

    This is the resolving power available to a triple: if it is smaller than
    epsilon, no middle tone can be shown to be arithmetic rather than
    harmonic. See is_informative_triple.
    """
    fa = 2.0 ** (a_cents / 1200.0)
    fc = 2.0 ** (c_cents / 1200.0)
    am = (fa + fc) / 2.0
    hm = 2.0 * fa * fc / (fa + fc)
    return abs(1200.0 * log2(am / hm))


def is_informative_triple(
    a_cents: float,
    c_cents: float,
    epsilon_cents: float = DEFAULT_EPSILON_CENTS,
) -> bool:
    """DEGENERACY GUARD (Marcus's decision, 2026-07-21; plan §1.4).

    A tempered triple is informative only when its arithmetic and harmonic
    means are themselves distinguishable at the scoring resolution:

        |1200*log2(AM/HM)| >= epsilon

    Below that threshold the two mean conditions are the same condition, so
    labelling the triple "proportional" asserts nothing about proportionality
    — the identical triple is equally "subcontrary". Uninformative triples
    contribute to NO count (P, S, or G); raw unguarded counts are recorded
    alongside so the archive loses nothing.

    Equivalent framing: a span cutoff. Triples spanning less than ~58.8c
    (eps=0.5), ~83.2c (eps=1), ~117.7c (eps=2) or ~186.1c (eps=5) are
    uninformative, whatever the scale.

    Why this rule and not the alternatives (all measured over the coarse MOS
    sweep, 3006 records x 4 epsilon, before adoption):
    - "discount triples that are also geometric": FAILS. Narrow triples match
      P and S but usually not G — G fires only when the middle tone happens
      to sit near the cents-midpoint. 1-3c generators still won N=5..10.
    - "discount triples labelled both P and S": clears eps=2 and 5 but FAILS
      at eps=0.5, where near-misses split on a knife edge (triple 0-2-3c has
      AM and HM 0.0013c apart, both ~0.5c from the middle, so one lands
      inside epsilon and one outside and it counts as a PURE proportional).
    - "minimum-step guard on the scale": a scale-shape prior inside the
      verifier, and demonstrably under-filters (the report-layer version
      admits 2.1/4.1/8.1c generators).

    NOT applied on the rational path: for exact rationals with a < b < c the
    three conditions are already mutually exclusive and there is no epsilon,
    so the guard is a no-op there by construction. Every exact-path result
    (hexanies, eikosanies, duality goldens) is unaffected.
    """
    return mean_separation_cents(a_cents, c_cents) >= epsilon_cents


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
    # Unguarded counts: what the scorer would report with the degeneracy
    # guard disabled. On the rational path the guard is a no-op, so these
    # always equal the guarded counts and degenerate_dropped is 0.
    proportional_raw: int
    subcontrary_raw: int
    geometric_raw: int
    degenerate_dropped: int  # label-hits suppressed by the guard


def _result(p: int, s: int, g: int, *, path: str, convention: str,
            epsilon_cents: Optional[float], scale: tuple,
            sample_size: int,
            p_raw: Optional[int] = None, s_raw: Optional[int] = None,
            g_raw: Optional[int] = None,
            degenerate_dropped: int = 0) -> ScoreResult:
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
        proportional_raw=p if p_raw is None else p_raw,
        subcontrary_raw=s if s_raw is None else s_raw,
        geometric_raw=g if g_raw is None else g_raw,
        degenerate_dropped=degenerate_dropped,
    )


# ---------------------------------------------------------------------------
# secondary convention: two-octave window (plan §1.1 as written)
# retained for comparison only — NOT self-dual, NOT transposition-invariant
# ---------------------------------------------------------------------------


def score_rational_window(ratios: Iterable[RationalLike]) -> ScoreResult:
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
    return _result(p, s, g, path="rational", convention=WINDOW_CONVENTION,
                   epsilon_cents=None, scale=scale, sample_size=len(sample))


def score_cents_window(
    cents: Iterable[float],
    epsilon_cents: float = DEFAULT_EPSILON_CENTS,
) -> ScoreResult:
    """Score a tempered scale (degrees in cents) over its two-octave sample.

    The degeneracy guard (is_informative_triple) applies, as on every
    tempered path."""
    scale = canonical_cents_scale(cents)
    sample = two_octave_sample_cents(scale)
    p = s = g = p_raw = s_raw = g_raw = dropped = 0
    for a, b, c in combinations(sample, 3):
        labels = classify_cents_triple(a, b, c, epsilon_cents)
        if not labels:
            continue
        informative = is_informative_triple(a, c, epsilon_cents)
        if PROPORTIONAL in labels:
            p_raw += 1
            p += informative
        if SUBCONTRARY in labels:
            s_raw += 1
            s += informative
        if GEOMETRIC in labels:
            g_raw += 1
            g += informative
        if not informative:
            dropped += len(labels)
    return _result(p, s, g, path="cents", convention=WINDOW_CONVENTION,
                   epsilon_cents=epsilon_cents, scale=scale,
                   sample_size=len(sample),
                   p_raw=p_raw, s_raw=s_raw, g_raw=g_raw,
                   degenerate_dropped=dropped)


#: Back-compat aliases. Pre-2026-07-21 scripts and result files were written
#: against these names; they still mean the WINDOW convention, never the
#: primary one. New code calls score() / score_tempered() instead.
score_rational = score_rational_window
score_cents = score_cents_window


# ---------------------------------------------------------------------------
# PRIMARY convention: middle-anchored octave windows
# (exactly self-dual and transposition-invariant)
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
    return _result(p, s, g, path="rational", convention=ANCHORED_CONVENTION,
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
    """Middle-anchored tempered scoring; see score_rational_anchored.

    The degeneracy guard (is_informative_triple) applies: triples whose AM
    and HM are closer than epsilon contribute to no count. Unguarded counts
    are recorded in the *_raw fields."""
    scale = canonical_cents_scale(cents)
    p = s = g = p_raw = s_raw = g_raw = dropped = 0
    for b in scale:
        lows = [r for pc in scale if (r := _cents_rep_below(pc, b)) is not None]
        highs = [r for pc in scale if (r := _cents_rep_above(pc, b)) is not None]
        for a in lows:
            for c in highs:
                labels = classify_cents_triple(a, b, c, epsilon_cents)
                if not labels:
                    continue
                informative = is_informative_triple(a, c, epsilon_cents)
                if PROPORTIONAL in labels:
                    p_raw += 1
                    p += informative
                if SUBCONTRARY in labels:
                    s_raw += 1
                    s += informative
                if GEOMETRIC in labels:
                    g_raw += 1
                    g += informative
                if not informative:
                    dropped += len(labels)
    return _result(p, s, g, path="cents", convention=ANCHORED_CONVENTION,
                   epsilon_cents=epsilon_cents, scale=scale,
                   sample_size=len(scale),
                   p_raw=p_raw, s_raw=s_raw, g_raw=g_raw,
                   degenerate_dropped=dropped)


# ---------------------------------------------------------------------------
# canonical entry points — call these, not the convention-specific functions
# ---------------------------------------------------------------------------


def score(ratios: Iterable[RationalLike]) -> ScoreResult:
    """Score a JI scale under the PRIMARY convention (middle-anchored).

    This is the entry point all new work should use; the result records
    `convention` so archives stay unambiguous if the primary ever changes.
    """
    return score_rational_anchored(ratios)


def score_tempered(
    cents: Iterable[float],
    epsilon_cents: float = DEFAULT_EPSILON_CENTS,
) -> ScoreResult:
    """Score a tempered scale (cents) under the PRIMARY convention."""
    return score_cents_anchored(cents, epsilon_cents)
