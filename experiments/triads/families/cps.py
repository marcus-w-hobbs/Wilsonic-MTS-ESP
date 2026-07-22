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


# ---------------------------------------------------------------------------
# Wilsonic UI recreation
# ---------------------------------------------------------------------------

#: Scale-selector values in the plugin's CPS design, indexed as "n_k".
#: Source: CPSModel::__scaleNames (Source/CPSModel.cpp:16-32). The dropdown
#: shows these strings verbatim; index 5 ("Mandala") is the stellated hexany
#: and has no plain (n, k) form.
UI_SCALE_NAMES: dict[tuple[int, int], str] = {
    (3, 1): "3_1", (3, 2): "3_2",
    (4, 1): "4_1", (4, 2): "4_2", (4, 3): "4_3",
    (5, 1): "5_1", (5, 2): "5_2", (5, 3): "5_3", (5, 4): "5_4",
    (6, 1): "6_1", (6, 2): "6_2", (6, 3): "6_3", (6, 4): "6_4", (6, 5): "6_5",
}

#: Seed parameter letters in UI order, and their APVTS parameter IDs
#: (CPSModel.h:73-84). Seeds map to A, B, C, ... in ascending order.
UI_SEED_LETTERS = ("A", "B", "C", "D", "E", "F")

#: Common names, for the human reading the .scl comment.
UI_COMMON_NAMES: dict[tuple[int, int], str] = {
    (4, 2): "Hexany (6 tones)",
    (5, 2): "Dekany (10 tones)",
    (5, 3): "Dekany (10 tones)",
    (6, 2): "Pentadekany (15 tones)",
    (6, 3): "Eikosany (20 tones)",
    (6, 4): "Pentadekany (15 tones)",
}


def wilsonic_recreation_lines(seeds: Sequence[int], k: int) -> list[str]:
    """Comment lines telling a reader how to rebuild this CPS in Wilsonic.

    Everything needed to reproduce the tuning from the UI: which design to
    pick, which scale/subset, and every seed value. Also records Erv's own
    notation, which REVERSES the canonical order -- Erv writes k)n for what
    this codebase calls CPS(n, k) -- so nobody has to guess which convention
    a given file used.
    """
    n = len(seeds)
    key = (n, k)
    ui_scale = UI_SCALE_NAMES.get(key)
    common = UI_COMMON_NAMES.get(key)
    ordered = sorted(int(s) for s in seeds)
    if n > len(UI_SEED_LETTERS):
        raise ValueError(f"CPS UI supports at most 6 seeds, got {n}")

    lines = [
        "RECREATE IN WILSONIC:",
        "  Design: Combination Product Sets",
    ]
    if ui_scale is None:
        lines.append(f"  Scale: (no plain n_k selector for CPS({n},{k}))")
    else:
        lines.append(f"  Scale: {ui_scale}"
                     + (f"   [{common}]" if common else ""))
    for letter, value in zip(UI_SEED_LETTERS, ordered):
        lines.append(f"  {letter} = {value}")
    if n < len(UI_SEED_LETTERS):
        unused = ", ".join(UI_SEED_LETTERS[n:])
        lines.append(f"  ({unused} unused at this scale selection)")
    lines += [
        f"  APVTS: CPSCALE={ui_scale or '?'}, "
        + ", ".join(f"CPS{l}={v}"
                    for l, v in zip(UI_SEED_LETTERS, ordered)),
        f"  Notation: canonical CPS({n},{k}) = {n} seeds choose {k}; "
        f"Erv writes this {k}){n}.",
    ]
    return lines
