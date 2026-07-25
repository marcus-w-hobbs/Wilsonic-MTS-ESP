"""Melodic scorers M1-M3 for the lattice module (SPEC.md §"Melodic scorers").

Version 0.1.0 — NOT yet frozen. Freeze (hash-pin pattern, mirroring
triads/scorer.py) happens after Marcus reviews LAT-MEL-001. Until then this
file may change, but every result record carries MELODIC_VERSION so receipts
from different versions never get compared by accident.

This module is a sibling of experiments/triads/ and imports the FROZEN triad
scorer READ-ONLY (canonicalization helpers only) so the two axes share one
canonical form. It must never modify triads/scorer.py (v1.1.0, CI-enforced).

Three independent scores, all pure functions of a pitch-class multiset given
in cents (any real values; reduced mod 1200 into [0, 1200) and deduplicated
at a logged epsilon before scoring). Each returns a frozen dataclass: a
scalar plus receipts, with every epsilon it was scored under.

M1 — gap entropy (gap_entropy).
    Circular gaps of the deduped scale, clustered into size classes at
    eps_gap (default 0.5c, matching the frozen scorer's smallest epsilon
    regime), Shannon entropy of the gap-instance distribution IN BITS
    (base 2). A MOS has 2 gap classes, hence entropy <= 1 bit (= log 2 nats,
    the SPEC's phrasing); rank-1 projections have <= 3 classes (three-gap
    theorem); random scales approach log2(N) bits.

M2 — constant structure (constant_structure + best_val_kendall_tau).
    Wilson's criterion: a scale is CS iff every interval size subtends the
    SAME number of steps wherever it occurs. All N*(N-1) circular intervals
    (span k in 1..N-1) are clustered by size at eps_cs (default 0.5c);
    a size class occurring at two different spans is a violation. Score =
    number of violating size classes (0 = CS).
    Separately, for EXACT rational scales, best_val_kendall_tau measures
    epimorphy: over the patent val <N, round(N log2 3), ...> for the scale's
    actual prime limit, with +-1 perturbations per odd-prime coordinate
    (full product, logged search size), the Kendall-tau distance (discordant
    pair count) between pitch order and val order; the minimum is reported
    with its argmin val. tau = 0 means some val orders the scale exactly.

M3 — Rothenberg propriety (propriety). Reference: Rothenberg 1978,
    "A model for pattern perception with musical applications".
    Proper iff max(spectrum at span k) <= min(spectrum at span k+1) for all
    k; strictly proper if < holds everywhere. Comparisons use eps_prop
    (default 1e-9c) purely as a float-noise guard — equality within eps_prop
    is "equal" (blocks strictness, not propriety). Classification in
    {strictly_proper, proper, improper} + count of violating span pairs.

Clustering convention (M1 and M2): values are sorted; a value joins the
current cluster iff (value - cluster_minimum) <= epsilon, else it starts a
new cluster. Anchoring to the cluster MINIMUM (not the previous value)
prevents unbounded chaining; the convention is deterministic and identical
in both scorers. Dedup in canonicalization is the frozen scorer's own rule
(anchored the same way) with eps_dedup default 0.01c per SPEC.

Machine-checked corrections to SPEC.md §"Melodic scorers" test parentheticals
(discovered while pinning goldens, 2026-07-25; see LOG.md):
- the 12-EDO diatonic is NOT a constant structure: the 600c tritone subtends
  3 steps (F-B) and 4 steps (B-F'), one violating class. It IS proper (the
  equality max-span-3 = min-span-4 = 600c makes it proper, not strict).
- Pythagorean [wolf] 12 is STRICTLY PROPER (apotome/limma steps never stack
  enough to cross spans). The known IMPROPER scale is the Pythagorean
  DIATONIC (7): aug4 611.73c at 3 steps > dim5 588.27c at 4 steps — the
  classic Rothenberg example. Tests pin the true behavior.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from math import log2
from pathlib import Path
from typing import Iterable, Union

# Frozen triad scorer, imported READ-ONLY for the shared canonical forms.
_TRIADS_DIR = Path(__file__).resolve().parent.parent / "triads"
if str(_TRIADS_DIR) not in sys.path:
    sys.path.insert(0, str(_TRIADS_DIR))

from scorer import (  # noqa: E402
    SCORER_VERSION as FROZEN_SCORER_VERSION,
    canonical_cents_scale,
    canonical_rational_scale,
)

MELODIC_VERSION = "0.1.0"

#: SPEC defaults. eps_dedup collapses float-identical tones; eps_gap and
#: eps_cs match the frozen scorer's tightest epsilon regime (0.5c).
DEFAULT_DEDUP_EPSILON_CENTS = 0.01
DEFAULT_GAP_EPSILON_CENTS = 0.5
DEFAULT_CS_EPSILON_CENTS = 0.5
#: Float-noise guard only — NOT a musical tolerance. Rothenberg propriety is
#: classically exact; 1e-9c absorbs binary-representation noise and nothing
#: audible.
DEFAULT_PROPRIETY_EPSILON_CENTS = 1e-9

STRICTLY_PROPER = "strictly_proper"
PROPER = "proper"
IMPROPER = "improper"

RationalLike = Union[Fraction, int, str]


# ---------------------------------------------------------------------------
# canonical form and shared geometry
# ---------------------------------------------------------------------------


def canonicalize(
    cents: Iterable[float],
    dedup_epsilon_cents: float = DEFAULT_DEDUP_EPSILON_CENTS,
) -> tuple[float, ...]:
    """Reduce mod 1200 into [0, 1200), sort, dedup at eps (wrap-aware).

    Delegates to the frozen scorer's canonical_cents_scale so the melodic and
    harmonic axes agree exactly on what "the scale" is; only the dedup
    epsilon default differs (0.01c per SPEC vs the scorer's 1e-6c).
    """
    return canonical_cents_scale(cents, dedup_epsilon_cents)


def ratios_to_cents(ratios: Iterable[RationalLike]) -> tuple[float, ...]:
    """Exact-dedup a rational scale (frozen scorer's canonical form), then
    convert to cents in [0, 1200). Use this to run M1-M3 on JI scales."""
    scale = canonical_rational_scale(ratios)
    return tuple(1200.0 * log2(float(r)) for r in scale)


def circular_gaps(scale: tuple[float, ...]) -> tuple[float, ...]:
    """The N circular steps of a canonical scale, in scale order (the last
    entry wraps through the octave). Gaps sum to 1200 exactly up to float."""
    n = len(scale)
    if n == 0:
        raise ValueError("scale must contain at least one degree")
    if n == 1:
        return (1200.0,)
    inner = tuple(scale[i + 1] - scale[i] for i in range(n - 1))
    return inner + (1200.0 - scale[-1] + scale[0],)


def interval_spectrum(scale: tuple[float, ...]) -> dict[int, tuple[float, ...]]:
    """All circular interval sizes by span: spectrum[k] = sorted sizes of the
    N intervals subtending k steps, for k in 1..N-1 (mod-1200 ascending)."""
    n = len(scale)
    return {
        k: tuple(sorted((scale[(i + k) % n] - scale[i]) % 1200.0
                        for i in range(n)))
        for k in range(1, n)
    }


def _cluster_sorted(
    values: tuple[float, ...], epsilon: float
) -> tuple[tuple[int, int], ...]:
    """Cluster an ASCENDING tuple into runs anchored at each cluster minimum:
    v joins the open cluster iff v - cluster_min <= epsilon. Returns
    (start, end) index pairs, end exclusive. Deterministic, no chaining."""
    if not values:
        return ()
    bounds: list[tuple[int, int]] = []
    start = 0
    for i in range(1, len(values)):
        if values[i] - values[start] > epsilon:
            bounds.append((start, i))
            start = i
    bounds.append((start, len(values)))
    return tuple(bounds)


# ---------------------------------------------------------------------------
# M1 — gap entropy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GapEntropyResult:
    """M1 receipts. gap_classes rows are (size_min, size_max, count)."""

    entropy_bits: float
    gap_count: int
    gap_class_count: int
    gap_classes: tuple
    scale: tuple
    dedup_epsilon_cents: float
    gap_epsilon_cents: float
    melodic_version: str


def gap_entropy(
    cents: Iterable[float],
    dedup_epsilon_cents: float = DEFAULT_DEDUP_EPSILON_CENTS,
    gap_epsilon_cents: float = DEFAULT_GAP_EPSILON_CENTS,
) -> GapEntropyResult:
    """M1: Shannon entropy (bits) of the circular gap-size distribution.

    Each of the N gaps is one observation; probabilities are class counts
    over N. MOS => 2 classes => entropy <= 1 bit; 1-class scales (EDO subsets
    of one step size) score exactly 0.
    """
    scale = canonicalize(cents, dedup_epsilon_cents)
    gaps = tuple(sorted(circular_gaps(scale)))
    bounds = _cluster_sorted(gaps, gap_epsilon_cents)
    n = len(gaps)
    entropy = -sum(
        ((end - start) / n) * log2((end - start) / n)
        for start, end in bounds
        if end > start
    )
    classes = tuple(
        (gaps[start], gaps[end - 1], end - start) for start, end in bounds
    )
    return GapEntropyResult(
        entropy_bits=entropy,
        gap_count=n,
        gap_class_count=len(bounds),
        gap_classes=classes,
        scale=scale,
        dedup_epsilon_cents=dedup_epsilon_cents,
        gap_epsilon_cents=gap_epsilon_cents,
        melodic_version=MELODIC_VERSION,
    )


# ---------------------------------------------------------------------------
# M2 — constant structure + best-val Kendall tau
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConstantStructureResult:
    """M2 (machine check) receipts. violating_classes rows are
    (size_min, size_max, spans) — an interval-size class subtended by more
    than one step count. violations == 0 means the scale IS a CS."""

    violations: int
    is_cs: bool
    interval_class_count: int
    violating_classes: tuple
    scale: tuple
    dedup_epsilon_cents: float
    cs_epsilon_cents: float
    melodic_version: str


def constant_structure(
    cents: Iterable[float],
    dedup_epsilon_cents: float = DEFAULT_DEDUP_EPSILON_CENTS,
    cs_epsilon_cents: float = DEFAULT_CS_EPSILON_CENTS,
) -> ConstantStructureResult:
    """M2: count interval-size classes that occur at >= 2 distinct spans."""
    scale = canonicalize(cents, dedup_epsilon_cents)
    n = len(scale)
    pairs = tuple(sorted(
        ((scale[(i + k) % n] - scale[i]) % 1200.0, k)
        for k in range(1, n)
        for i in range(n)
    ))
    sizes = tuple(size for size, _ in pairs)
    bounds = _cluster_sorted(sizes, cs_epsilon_cents)
    violating = tuple(
        (pairs[start][0], pairs[end - 1][0],
         tuple(sorted({span for _, span in pairs[start:end]})))
        for start, end in bounds
        if len({span for _, span in pairs[start:end]}) > 1
    )
    return ConstantStructureResult(
        violations=len(violating),
        is_cs=not violating,
        interval_class_count=len(bounds),
        violating_classes=violating,
        scale=scale,
        dedup_epsilon_cents=dedup_epsilon_cents,
        cs_epsilon_cents=cs_epsilon_cents,
        melodic_version=MELODIC_VERSION,
    )


def _factorize(n: int) -> dict[int, int]:
    """Prime factorization by trial division (positive integers)."""
    if n < 1:
        raise ValueError(f"expected positive integer, got {n}")
    factors: dict[int, int] = {}
    remaining = n
    p = 2
    while p * p <= remaining:
        while remaining % p == 0:
            factors[p] = factors.get(p, 0) + 1
            remaining //= p
        p += 1 if p == 2 else 2
    if remaining > 1:
        factors[remaining] = factors.get(remaining, 0) + 1
    return factors


def _monzo(ratio: Fraction, primes: tuple[int, ...]) -> tuple[int, ...]:
    """Exponent vector of ratio over the given prime basis."""
    num = _factorize(ratio.numerator)
    den = _factorize(ratio.denominator)
    return tuple(num.get(p, 0) - den.get(p, 0) for p in primes)


@dataclass(frozen=True)
class ValTauResult:
    """M2 (val part) receipts. best_val coordinates follow `primes` (which
    always starts with 2; the 2-coordinate is fixed at N). min_tau is the
    Kendall-tau distance = discordant pair count (val strictly decreasing
    where pitch increases); ties (equal val degrees) are counted separately
    and do NOT contribute to tau."""

    min_tau: int
    best_val: tuple
    tie_pairs_at_best: int
    primes: tuple
    vals_searched: int
    pair_count: int
    patent_val: tuple
    scale: tuple
    melodic_version: str


def best_val_kendall_tau(ratios: Iterable[RationalLike]) -> ValTauResult:
    """Minimum Kendall-tau distance between pitch order and val order, over
    the patent val for the scale's actual prime limit plus +-1 perturbations
    per odd-prime coordinate (full product; the 2-coordinate stays N).

    Exact rationals only — this is the epimorphy/monotonicity lens on M2.
    Search order is deterministic (itertools.product over ascending primes,
    offsets -1, 0, +1), and the first minimum wins ties for best_val.
    """
    scale = canonical_rational_scale(ratios)
    n = len(scale)
    prime_set = {
        p
        for r in scale
        for part in (r.numerator, r.denominator)
        for p in _factorize(part)
    }
    primes = (2,) + tuple(sorted(prime_set - {2}))
    monzos = tuple(_monzo(r, primes) for r in scale)
    patent = (n,) + tuple(round(n * log2(p)) for p in primes[1:])
    pair_count = n * (n - 1) // 2

    best_tau = best_ties = None
    best_val: tuple[int, ...] = patent
    searched = 0
    for offsets in product((-1, 0, 1), repeat=len(primes) - 1):
        val = (n,) + tuple(v + o for v, o in zip(patent[1:], offsets))
        degrees = tuple(
            sum(v * m for v, m in zip(val, monzo)) for monzo in monzos
        )
        tau = sum(
            1 for i, j in combinations(range(n), 2) if degrees[i] > degrees[j]
        )
        ties = sum(
            1 for i, j in combinations(range(n), 2) if degrees[i] == degrees[j]
        )
        searched += 1
        if best_tau is None or tau < best_tau:
            best_tau, best_ties, best_val = tau, ties, val
    return ValTauResult(
        min_tau=best_tau,
        best_val=best_val,
        tie_pairs_at_best=best_ties,
        primes=primes,
        vals_searched=searched,
        pair_count=pair_count,
        patent_val=patent,
        scale=scale,
        melodic_version=MELODIC_VERSION,
    )


# ---------------------------------------------------------------------------
# M3 — Rothenberg propriety
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProprietyResult:
    """M3 receipts. violations rows are (span, max_at_span, min_at_next):
    span pairs where max exceeds the next span's min by more than eps_prop.
    equal_span_pairs counts boundary contacts (equality within eps_prop) —
    zero violations with zero equalities is strict propriety. Scales with
    fewer than 3 tones have no span pairs and are strictly proper vacuously."""

    classification: str
    violating_span_pairs: int
    violations: tuple
    equal_span_pairs: int
    scale: tuple
    dedup_epsilon_cents: float
    propriety_epsilon_cents: float
    melodic_version: str


def propriety(
    cents: Iterable[float],
    dedup_epsilon_cents: float = DEFAULT_DEDUP_EPSILON_CENTS,
    propriety_epsilon_cents: float = DEFAULT_PROPRIETY_EPSILON_CENTS,
) -> ProprietyResult:
    """M3: Rothenberg propriety over the circular interval spectrum."""
    scale = canonicalize(cents, dedup_epsilon_cents)
    spectrum = interval_spectrum(scale)
    violations = []
    equalities = 0
    for k in range(1, len(scale) - 1):
        widest, narrowest = spectrum[k][-1], spectrum[k + 1][0]
        if widest > narrowest + propriety_epsilon_cents:
            violations.append((k, widest, narrowest))
        elif abs(widest - narrowest) <= propriety_epsilon_cents:
            equalities += 1
    if violations:
        classification = IMPROPER
    elif equalities:
        classification = PROPER
    else:
        classification = STRICTLY_PROPER
    return ProprietyResult(
        classification=classification,
        violating_span_pairs=len(violations),
        violations=tuple(violations),
        equal_span_pairs=equalities,
        scale=scale,
        dedup_epsilon_cents=dedup_epsilon_cents,
        propriety_epsilon_cents=propriety_epsilon_cents,
        melodic_version=MELODIC_VERSION,
    )


# ---------------------------------------------------------------------------
# combined entry point
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MelodicScore:
    """M1 + M2 (machine check) + M3 on one canonical scale, with provenance.
    The val lens (best_val_kendall_tau) is separate because it needs exact
    rationals; LAT-MEL-001 records it alongside when the source is JI."""

    gap_entropy: GapEntropyResult
    constant_structure: ConstantStructureResult
    propriety: ProprietyResult
    scale: tuple
    melodic_version: str
    frozen_scorer_version: str


def score_melodic(
    cents: Iterable[float],
    dedup_epsilon_cents: float = DEFAULT_DEDUP_EPSILON_CENTS,
    gap_epsilon_cents: float = DEFAULT_GAP_EPSILON_CENTS,
    cs_epsilon_cents: float = DEFAULT_CS_EPSILON_CENTS,
    propriety_epsilon_cents: float = DEFAULT_PROPRIETY_EPSILON_CENTS,
) -> MelodicScore:
    """Run all three melodic scorers on one scale (cents in, canonical form
    shared across the three via one dedup pass)."""
    scale = canonicalize(cents, dedup_epsilon_cents)
    return MelodicScore(
        gap_entropy=gap_entropy(scale, dedup_epsilon_cents, gap_epsilon_cents),
        constant_structure=constant_structure(
            scale, dedup_epsilon_cents, cs_epsilon_cents),
        propriety=propriety(scale, dedup_epsilon_cents, propriety_epsilon_cents),
        scale=scale,
        melodic_version=MELODIC_VERSION,
        frozen_scorer_version=FROZEN_SCORER_VERSION,
    )


def score_melodic_rational(
    ratios: Iterable[RationalLike],
    dedup_epsilon_cents: float = DEFAULT_DEDUP_EPSILON_CENTS,
    gap_epsilon_cents: float = DEFAULT_GAP_EPSILON_CENTS,
    cs_epsilon_cents: float = DEFAULT_CS_EPSILON_CENTS,
    propriety_epsilon_cents: float = DEFAULT_PROPRIETY_EPSILON_CENTS,
) -> MelodicScore:
    """Convenience: exact-dedup a JI scale, convert to cents, run M1-M3."""
    return score_melodic(
        ratios_to_cents(ratios),
        dedup_epsilon_cents,
        gap_epsilon_cents,
        cs_epsilon_cents,
        propriety_epsilon_cents,
    )
