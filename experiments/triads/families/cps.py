"""Combination product set (CPS) generators — exact rational path.

Mirrors the plugin's construction (CPSTuningBase::multiplyByCommonTones +
TuningImp::_update): scale = octave-reduced products of all k-subsets of
the seed multiset. The plugin computes in floats and keeps duplicate
products (CPSTuningBase.cpp:18); here we compute exact rationals and the
canonical scale is deduplicated (scorer convention). cps_products()
returns the raw multiset for round-tripping to the plugin's form.

CPS(n, k) notation: n seeds choose k. Hexany = CPS(4, 2).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from math import prod
from typing import Iterable, Sequence

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import RationalLike, canonical_rational_scale  # noqa: E402


def cps_products(seeds: Sequence[RationalLike], k: int) -> tuple[Fraction, ...]:
    """Raw k-subset products, un-reduced, in combination order (multiset)."""
    if k < 1 or k > len(seeds):
        raise ValueError(f"k={k} out of range for {len(seeds)} seeds")
    fr = [Fraction(s) for s in seeds]
    if any(s <= 0 for s in fr):
        raise ValueError("seeds must be positive")
    return tuple(prod(combo) for combo in combinations(fr, k))


def cps_scale(seeds: Sequence[RationalLike], k: int) -> tuple[Fraction, ...]:
    """Canonical (octave-reduced, deduped, sorted) CPS(n, k) scale."""
    return canonical_rational_scale(cps_products(seeds, k))


def hexany(seeds: Sequence[RationalLike]) -> tuple[Fraction, ...]:
    """CPS(4, 2): the hexany of four seeds."""
    if len(seeds) != 4:
        raise ValueError(f"hexany needs exactly 4 seeds, got {len(seeds)}")
    return cps_scale(seeds, 2)


def odd_seed_sets(n_seeds: int, odd_max: int) -> tuple[tuple[int, ...], ...]:
    """All ascending n_seeds-subsets of the odd integers in [1, odd_max]."""
    odds = range(1, odd_max + 1, 2)
    return tuple(combinations(odds, n_seeds))
