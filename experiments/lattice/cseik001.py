"""CS-EIK-001 — search for a constant-structure eikosany (G-007 amendment).

Pre-registered in LOG.md 2026-07-28 BEFORE first run. Exhaustive over
6-subsets of odd integers <= 31 (escalation to <= 45 pre-registered if no CS
found). Exact arithmetic for generation and the CS criterion; frozen scorers
(triad v1.1.0, melodic v0.1.0) for the winner panel.

Run from experiments/lattice/:  python3.12 cseik001.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import combinations
from math import log2
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import melodic as mel  # noqa: E402
import scorer as triad  # noqa: E402
from families.cps import cps_scale  # noqa: E402
from scorer import canonical_rational_scale  # noqa: E402

RESULTS = HERE / "results" / "cseik001.jsonl"
CORE_BOUND = 31
ESCALATION_BOUND = 45
NEAR_MISS_MAX_VIOLATIONS = 2


def interval_span_map(scale: tuple[Fraction, ...]) -> dict[Fraction, set[int]]:
    """Exact circular interval -> set of spans (steps) it subtends."""
    n = len(scale)
    spans: dict[Fraction, set[int]] = {}
    for k in range(1, n):
        for i in range(n):
            j = (i + k) % n
            iv = scale[j] / scale[i] * (2 if j < i else 1)
            spans.setdefault(iv, set()).add(k)
    return spans


def cs_check(scale: tuple[Fraction, ...]) -> tuple[int, dict[Fraction, set[int]]]:
    """Number of exact interval-size classes at >= 2 spans (0 = CS)."""
    spans = interval_span_map(scale)
    return sum(1 for s in spans.values() if len(s) > 1), spans


def cs_margin_cents(spans: dict[Fraction, set[int]]) -> float:
    """For an exact-CS scale: min cents distance between two interval sizes
    at DIFFERENT spans — the epsilon up to which the scale stays CS."""
    sized = sorted((1200.0 * log2(float(iv)), next(iter(sp)))
                   for iv, sp in spans.items())
    margin = float("inf")
    for (c1, k1), (c2, k2) in zip(sized, sized[1:]):
        if k1 != k2:
            margin = min(margin, c2 - c1)
    return margin


def _factorize(n: int) -> dict[int, int]:
    out: dict[int, int] = {}
    m, p = n, 2
    while p * p <= m:
        while m % p == 0:
            out[p] = out.get(p, 0) + 1
            m //= p
        p += 1 if p == 2 else 2
    if m > 1:
        out[m] = out.get(m, 0) + 1
    return out


def epimorphy_check(scale: tuple[Fraction, ...]) -> dict:
    """Solve v . monzo(t_i) = i exactly over Q with v(2) = len(scale).

    Returns {'epimorphic': bool, 'val': [...] or None, 'reason': str}.
    Epimorphic iff the linear system is consistent AND the solved odd-prime
    coordinates are integers (a val is an integer covector).
    """
    n = len(scale)
    primes = sorted({p for t in scale
                     for part in (t.numerator, t.denominator)
                     for p in _factorize(part)} - {2})
    rows = []
    for i, t in enumerate(scale):
        num, den = _factorize(t.numerator), _factorize(t.denominator)
        m2 = num.get(2, 0) - den.get(2, 0)
        coeffs = [Fraction(num.get(p, 0) - den.get(p, 0)) for p in primes]
        rhs = Fraction(i - n * m2)
        rows.append((coeffs, rhs))
    # Gaussian elimination over Q on [coeffs | rhs]
    cols = len(primes)
    mat = [row[0] + [row[1]] for row in rows]
    pivot_row = 0
    pivots = []
    for c in range(cols):
        r = next((r for r in range(pivot_row, len(mat)) if mat[r][c] != 0), None)
        if r is None:
            continue
        mat[pivot_row], mat[r] = mat[r], mat[pivot_row]
        pv = mat[pivot_row][c]
        mat[pivot_row] = [x / pv for x in mat[pivot_row]]
        for rr in range(len(mat)):
            if rr != pivot_row and mat[rr][c] != 0:
                f = mat[rr][c]
                mat[rr] = [a - f * b for a, b in zip(mat[rr], mat[pivot_row])]
        pivots.append(c)
        pivot_row += 1
    for r in range(pivot_row, len(mat)):
        if mat[r][cols] != 0:
            return {"epimorphic": False, "val": None, "reason": "inconsistent"}
    if len(pivots) < cols:
        return {"epimorphic": False, "val": None, "reason": "underdetermined"}
    sol = [Fraction(0)] * cols
    for r, c in enumerate(pivots):
        sol[c] = mat[r][cols]
    if any(s.denominator != 1 for s in sol):
        return {"epimorphic": False, "val": None, "reason": "non-integer val"}
    return {"epimorphic": True,
            "val": [n] + [int(s) for s in sol],
            "reason": f"primes {[2] + primes}"}


def seed_features(seeds: tuple[int, ...]) -> dict:
    factored = {s: _factorize(s) for s in seeds}
    composites = [s for s in seeds if s > 1 and len(_factorize(s)) > 1
                  or (s > 1 and sum(_factorize(s).values()) > 1)]
    shared = []
    for a, b in combinations(seeds, 2):
        common = set(factored[a]) & set(factored[b])
        if a > 1 and b > 1 and common:
            shared.append((a, b, sorted(common)))
    return {"composite_seeds": composites,
            "sharing_pairs": len(shared),
            "all_prime": not composites}


def full_panel(seeds: tuple[int, ...], scale) -> dict:
    h = triad.score(scale)
    m = mel.score_melodic_rational(scale)
    tau = mel.best_val_kendall_tau(scale)
    epi = epimorphy_check(canonical_rational_scale(scale))
    return {"harmonic": {"P": h.proportional, "S": h.subcontrary,
                         "G": h.geometric, "scorer_version": h.scorer_version},
            "m1_entropy_bits": round(m.gap_entropy.entropy_bits, 6),
            "m1_gap_classes": m.gap_entropy.gap_class_count,
            "m3_class": m.propriety.classification,
            "val_min_tau": tau.min_tau,
            "val_ties": tau.tie_pairs_at_best,
            "epimorphy": epi,
            "melodic_version": mel.MELODIC_VERSION}


def sweep(bound: int, skip_below: int = 0) -> tuple[list[dict], int, int]:
    odds = [n for n in range(1, bound + 1, 2)]
    rows, cs_found, degenerate = [], 0, 0
    for seeds in combinations(odds, 6):
        if max(seeds) <= skip_below:
            continue  # already covered by the core sweep
        raw = cps_scale(seeds, 3)
        scale = canonical_rational_scale(raw)
        if len(scale) != 20:
            degenerate += 1
            rows.append({"seeds": list(seeds), "distinct_tones": len(scale),
                         "degenerate": True})
            continue
        violations, spans = cs_check(scale)
        row = {"seeds": list(seeds), "distinct_tones": 20,
               "cs_violations": violations, "is_cs": violations == 0,
               **seed_features(seeds)}
        if violations == 0:
            cs_found += 1
            row["cs_margin_cents"] = round(cs_margin_cents(spans), 6)
            row.update(full_panel(seeds, raw))
        elif violations <= NEAR_MISS_MAX_VIOLATIONS:
            row.update(full_panel(seeds, raw))
        rows.append(row)
    return rows, cs_found, degenerate


def main() -> None:
    rows, cs_found, degenerate = sweep(CORE_BOUND)
    bound = CORE_BOUND
    if cs_found == 0:
        print(f"odds <= {CORE_BOUND}: no CS eikosany — escalating to "
              f"{ESCALATION_BOUND} (pre-registered)")
        more, cs_found, deg2 = sweep(ESCALATION_BOUND, skip_below=CORE_BOUND)
        rows += more
        degenerate += deg2
        bound = ESCALATION_BOUND

    RESULTS.parent.mkdir(exist_ok=True)
    with RESULTS.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    proper = [r for r in rows if not r.get("degenerate")]
    winners = [r for r in proper if r.get("is_cs")]
    near = [r for r in proper
            if not r.get("is_cs") and r.get("cs_violations", 99) <= NEAR_MISS_MAX_VIOLATIONS]
    print(f"\nswept odds <= {bound}: {len(rows)} seedings "
          f"({len(proper)} true 20-tone, {degenerate} degenerate)")
    print(f"P1  CS eikosanies found: {len(winners)}")
    for w in sorted(winners, key=lambda r: -r.get("cs_margin_cents", 0))[:12]:
        print(f"    {w['seeds']} margin={w['cs_margin_cents']}c "
              f"P={w['harmonic']['P']} m3={w['m3_class']} "
              f"epimorphic={w['epimorphy']['epimorphic']} "
              f"val={w['epimorphy']['val']}")
    all_prime_cs = [w for w in winners if w["all_prime"]]
    print(f"P2  all-prime CS winners: {len(all_prime_cs)} "
          f"(prediction: 0); winners with sharing pairs: "
          f"{sum(1 for w in winners if w['sharing_pairs'] > 0)}/{len(winners)}")
    epi_mismatch = [w["seeds"] for w in winners
                    if not w["epimorphy"]["epimorphic"]]
    print(f"P3  CS-but-not-epimorphic: {len(epi_mismatch)} {epi_mismatch[:5]}")
    print(f"near-misses (<= {NEAR_MISS_MAX_VIOLATIONS} violations): {len(near)}")
    vio = sorted(r.get("cs_violations", 0) for r in proper)
    print(f"violation distribution: min={vio[0]} median={vio[len(vio)//2]} "
          f"max={vio[-1]}")


if __name__ == "__main__":
    main()
