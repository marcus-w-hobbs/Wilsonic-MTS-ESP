"""MOS-LAT-002 — H-M1 retest on a mixed-tail quadratic-generator corpus.

Registered follow-up to MOS-LAT-001 (LOG.md 2026-07-28 results entry: the
H-M1 null was attributed to the CORPUS — on an all-1s CF tail the spectral
gap |lambda/lambda'| is the constant phi**2 and the remaining descriptors
are near-functions of (N, conj_sep)). Pre-registered in LOG.md
("MOS-LAT-002 pre-registration", 2026-07-29) BEFORE this module was
implemented.

Corpus: quadratic generators [0; preamble, (tail)*] with MIXED periodic
tails — all period-1 and period-2 digit strings over {1, 2, 3} EXCEPT the
pure all-1s tail (MOS-LAT-001's corpus) — and preambles of length <= 3
over {1, 2, 3}, deduplicated by exact generator value. The tail matrix
M = prod [[0, 1], [1, t_i]] now varies by tail cycle, so the spectral gap
|lambda/lambda'| = lambda**2 (|det M| = 1) is genuinely NON-constant:
five values from (1+sqrt2)**2 = 5.83 to (4+sqrt15)**2 = 61.98.

Arithmetic is exact in Q(sqrt d) for squarefree d (class Quad, the Q5 of
moslat001 generalized to arbitrary non-square d). moslat001.py is imported
READ-ONLY: iota, the rank statistics, and the stratified permutation test
are the same code objects, so the two H-M1 runs are comparable by
construction. The frozen triad scorer v1.1.0 is used via score_tempered
(read-only import), epsilon = 2 cents default.

Deterministic: fixed seed 20260725, fixed predictor order, stdlib only.
Run from experiments/lattice/:  python3.12 moslat002.py
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from datetime import date
from functools import total_ordering
from itertools import product as iproduct
from math import floor as ffloor
from math import gcd, isqrt, sqrt
from pathlib import Path

_LATTICE_DIR = Path(__file__).resolve().parent
if str(_LATTICE_DIR) not in sys.path:
    sys.path.insert(0, str(_LATTICE_DIR))

# moslat001 inserts experiments/triads on sys.path and re-exports the
# frozen-scorer entry points; importing it (never editing it) is the
# comparability contract of this follow-up.
from moslat001 import (  # noqa: E402
    MAX_CARD,
    MIN_CARD,
    N_PERMUTATIONS,
    SEED,
    SCORER_VERSION,
    iota,
    partial_spearman,
    stratified_permutation_p,
    score_tempered,
)
from families.mos import MAX_LEVEL, mos_cents, zigzag  # noqa: E402

EXPERIMENT = "MOS-LAT-002"
RESULTS_PATH = _LATTICE_DIR / "results" / "moslat002.json"

#: Mixed periodic tails: every period-1 and period-2 digit string over
#: {1,2,3} except the all-1s tail (that is MOS-LAT-001's corpus). (1,1),
#: (2,2), (3,3) collapse to period-1 strings and are not listed twice.
TAILS: tuple[tuple[int, ...], ...] = (
    (2,), (3,), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2))

MAX_PREAMBLE_DIGIT = 3
MAX_PREAMBLE_LEN = 3


# ---------------------------------------------------------------------------
# exact arithmetic in Q(sqrt d), d squarefree — moslat001.Q5 generalized
# ---------------------------------------------------------------------------


def squarefree_split(n: int) -> tuple[int, int]:
    """n = s*s * d with d squarefree; returns (s, d). n > 0."""
    if n <= 0:
        raise ValueError(f"positive integer required, got {n}")
    s, d = 1, n
    f = 2
    while f * f <= d:
        while d % (f * f) == 0:
            d //= f * f
            s *= f
        f += 1
    return s, d


@total_ordering
@dataclass(frozen=True)
class Quad:
    """Exact (a + b*sqrt(d))/c, c > 0, gcd(a, b, c) = 1, d squarefree and
    non-square (d > 1). Immutable. Mixed-field comparisons are exact:
    distinct squarefree fields intersect only in the rationals."""

    a: int
    b: int
    c: int
    d: int

    def __float__(self) -> float:
        return (self.a + self.b * sqrt(float(self.d))) / self.c

    def conj(self) -> "Quad":
        """Galois conjugate: sqrt(d) -> -sqrt(d)."""
        return quad(self.a, -self.b, self.c, self.d)

    def sign(self) -> int:
        a, b = self.a, self.b  # c > 0 never changes the sign
        if b == 0:
            return (a > 0) - (a < 0)
        if a == 0 or (a > 0) == (b > 0):
            return (b > 0) - (b < 0)
        lhs, rhs = a * a, self.d * b * b  # opposite signs: |a| vs |b|*sqrt(d)
        if a > 0:
            return 1 if lhs > rhs else -1  # equality impossible (d non-square)
        return 1 if rhs > lhs else -1

    def _coerced(self, other: "Quad | int") -> "Quad":
        if isinstance(other, int):
            return quad(other, 0, 1, self.d)
        if other.b == 0:
            return quad(other.a, 0, other.c, self.d)
        if other.d != self.d:
            raise TypeError(
                f"mixed fields: Q(sqrt{self.d}) vs Q(sqrt{other.d})")
        return other

    def __add__(self, other: "Quad | int") -> "Quad":
        o = self._coerced(other)
        return quad(self.a * o.c + o.a * self.c,
                    self.b * o.c + o.b * self.c, self.c * o.c, self.d)

    def __radd__(self, other: int) -> "Quad":
        return self.__add__(other)

    def __neg__(self) -> "Quad":
        return quad(-self.a, -self.b, self.c, self.d)

    def __sub__(self, other: "Quad | int") -> "Quad":
        return self.__add__(-self._coerced(other))

    def __rsub__(self, other: int) -> "Quad":
        return (-self).__add__(other)

    def __mul__(self, other: "Quad | int") -> "Quad":
        o = self._coerced(other)
        return quad(self.a * o.a + self.d * self.b * o.b,
                    self.a * o.b + self.b * o.a, self.c * o.c, self.d)

    def __rmul__(self, other: int) -> "Quad":
        return self.__mul__(other)

    def inv(self) -> "Quad":
        """1/x = c*(a - b*sqrt(d)) / (a**2 - d*b**2)."""
        norm = self.a * self.a - self.d * self.b * self.b
        if norm == 0:
            raise ZeroDivisionError(f"inverse of zero in Q(sqrt{self.d})")
        return quad(self.c * self.a, -self.c * self.b, norm, self.d)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Quad, int)):
            return NotImplemented
        if isinstance(other, Quad) and other.b != 0:
            if self.b == 0:
                return False  # rational != irrational
            if self.d != other.d:
                return False  # distinct squarefree fields meet only in Q
        return (self - other).sign() == 0

    def __lt__(self, other: "Quad | int") -> bool:
        return (self - self._coerced(other)).sign() < 0

    def __hash__(self) -> int:
        return hash((self.a, self.b, self.c, self.d if self.b else 0))

    def floor(self) -> int:
        """Exact floor: float candidate, then exact fix-up (few steps)."""
        f = ffloor(float(self))
        while (self - f).sign() < 0:
            f -= 1
        while (self - (f + 1)).sign() >= 0:
            f += 1
        return f

    def pretty(self) -> str:
        return f"({self.a}{self.b:+d}*sqrt{self.d})/{self.c}"

    def key(self) -> tuple[int, int, int, int]:
        """Canonical dedup key (b == 0 normalizes the field away)."""
        return (self.a, self.b, self.c, self.d if self.b else 0)


def quad(a: int, b: int, c: int, d: int) -> Quad:
    """Normalized constructor: c > 0, gcd(a, b, c) = 1, square part of d
    folded into b (sqrt(12) -> 2*sqrt(3)); a perfect-square d folds into a."""
    if c == 0:
        raise ZeroDivisionError("denominator 0 in Q(sqrt d)")
    if c < 0:
        a, b, c = -a, -b, -c
    if b != 0:
        s, d = squarefree_split(d)
        b *= s
        if d == 1:  # sqrt part was rational after all
            a, b = a + b, 0
    g = gcd(gcd(abs(a), abs(b)), c)
    if g > 1:
        a, b, c = a // g, b // g, c // g
    return Quad(a, b, c, d)


# ---------------------------------------------------------------------------
# generators from CF digit strings: preamble + periodic tail
# ---------------------------------------------------------------------------


def tail_matrix(tail: tuple[int, ...]) -> tuple[int, int, int, int]:
    """Moebius matrix (m11, m12, m21, m22) of x -> [0; t1, ..., tm, x],
    i.e. the product of [[0, 1], [1, t_i]] in digit order."""
    m11, m12, m21, m22 = 1, 0, 0, 1
    for t in tail:
        m11, m12, m21, m22 = m12, m11 + t * m12, m22, m21 + t * m22
    return m11, m12, m21, m22


def tail_fixed_point(tail: tuple[int, ...]) -> Quad:
    """Exact value of the purely periodic CF [0; (t1, ..., tm)*]: the fixed
    point of the tail's Moebius map that lies in (0, 1). Reduced-CF theory
    guarantees exactly one root there (the Galois conjugate is < -1)."""
    m11, m12, m21, m22 = tail_matrix(tail)
    big_a, big_b, big_c = m21, m22 - m11, -m12
    disc = big_b * big_b - 4 * big_a * big_c  # == tr**2 - 4*det
    if isqrt(disc) ** 2 == disc:
        raise ValueError(f"tail {tail}: rational fixed point (square disc)")
    s, d = squarefree_split(disc)
    roots = [quad(-big_b, sigma * s, 2 * big_a, d) for sigma in (1, -1)]
    inside = [r for r in roots if r.sign() > 0 and (1 - r).sign() > 0]
    if len(inside) != 1:
        raise ValueError(f"tail {tail}: expected exactly one root in (0,1)")
    x = inside[0]
    residual = big_a * x * x + big_b * x + big_c
    if residual.sign() != 0:
        raise ArithmeticError(f"tail {tail}: fixed point fails its quadratic")
    return x


def generator_from(preamble: tuple[int, ...], tail: tuple[int, ...]) -> Quad:
    """Exact value of [0; p1, ..., pk, (t1, ..., tm)*]."""
    value = tail_fixed_point(tail)
    for digit in reversed(preamble):
        value = (digit + value).inv()
    return value


def spectral_gap(tail: tuple[int, ...]) -> float:
    """|lambda / lambda'| of the tail matrix. |det| = 1, so this equals
    lambda**2 — a tail-CYCLE invariant (rotations share it)."""
    m11, m12, m21, m22 = tail_matrix(tail)
    tr = m11 + m22
    det = m11 * m22 - m12 * m21
    lam = (tr + sqrt(tr * tr - 4 * det)) / 2.0
    return lam * lam


def tail_cycle(tail: tuple[int, ...]) -> tuple[int, ...]:
    """Canonical representative of the tail's rotation class."""
    rotations = [tail[i:] + tail[:i] for i in range(len(tail))]
    return min(rotations)


def all_preambles(max_digit: int = MAX_PREAMBLE_DIGIT,
                  max_len: int = MAX_PREAMBLE_LEN) -> list[tuple[int, ...]]:
    """All CF preambles with digits <= max_digit, length <= max_len,
    including the empty preamble. 40 at the defaults."""
    out: list[tuple[int, ...]] = [()]
    for length in range(1, max_len + 1):
        out.extend(iproduct(range(1, max_digit + 1), repeat=length))
    return out


def cf_string(preamble: tuple[int, ...], tail: tuple[int, ...]) -> str:
    head = ",".join(map(str, preamble))
    loop = ",".join(map(str, tail))
    return "[0;" + (head + "," if head else "") + "(" + loop + ")*]"


def enumerate_corpus() -> tuple[list[dict], dict]:
    """Deterministic corpus: TAILS x all_preambles, deduplicated by exact
    generator value (first occurrence kept, in enumeration order). Returns
    (generators, census). Duplicates must agree on the tail cycle — the
    eventual CF tail of a quadratic irrational is unique — asserted."""
    by_key: dict[tuple[int, int, int, int], dict] = {}
    n_raw = 0
    duplicates = 0
    for tail in TAILS:
        gap = spectral_gap(tail)
        cycle = tail_cycle(tail)
        for preamble in all_preambles():
            n_raw += 1
            g = generator_from(preamble, tail)
            key = g.key()
            if key in by_key:
                duplicates += 1
                prior = by_key[key]
                if prior["tail_cycle"] != list(cycle):
                    raise AssertionError(
                        f"value collision across tail cycles: "
                        f"{cf_string(preamble, tail)} vs {prior['cf']}")
                continue
            g_conj = g.conj()
            by_key[key] = {
                "cf": cf_string(preamble, tail),
                "preamble": list(preamble),
                "tail": list(tail),
                "tail_cycle": list(cycle),
                "field_d": g.d,
                "value_exact": g.pretty(),
                "conjugate_exact": g_conj.pretty(),
                "g01": float(g),
                "cents": float(g) * 1200.0,
                "conj_sep": abs(float(g - g_conj)),
                "spectral_gap": gap,
                "_g": g,
                "_g_conj": g_conj,
            }
    generators = list(by_key.values())
    census = {
        "n_raw": n_raw,
        "n_distinct": len(generators),
        "duplicates_dropped": duplicates,
        "tails": [list(t) for t in TAILS],
        "preambles": f"digits <= {MAX_PREAMBLE_DIGIT}, "
                     f"length <= {MAX_PREAMBLE_LEN}, empty included",
        "spectral_gap_by_tail": {
            cf_string((), t): spectral_gap(t) for t in TAILS},
    }
    return generators, census


# ---------------------------------------------------------------------------
# rows: frozen scores + conjugate-embedding descriptors
# ---------------------------------------------------------------------------


def run_rows(generators: list[dict]) -> list[dict]:
    """One row per (generator, MOS cardinality in [MIN_CARD, MAX_CARD]) at
    Brun zigzag levels 0..MAX_LEVEL — the moslat001.run_step2_rows recipe,
    plus the spectral-gap descriptor (non-constant on this corpus)."""
    rows = []
    for gen in generators:
        g: Quad = gen["_g"]
        g_conj: Quad = gen["_g_conj"]
        g01 = gen["g01"]
        first_level: dict[int, tuple[int, int]] = {}
        for level, (num, den) in enumerate(zigzag(g01)):
            if den not in first_level:
                first_level[den] = (level, num)
        for den in sorted(first_level):
            if not MIN_CARD <= den <= MAX_CARD:
                continue
            level, num = first_level[den]
            iotas = [iota(b, g, g_conj) for b in range(den)]
            spread = abs(float(max(iotas) - min(iotas)))
            result = score_tempered(mos_cents(g01, den))
            rows.append({
                "cf": gen["cf"],
                "preamble": gen["preamble"],
                "tail": gen["tail"],
                "field_d": gen["field_d"],
                "g01": g01,
                "cents": gen["cents"],
                "cardinality": den,
                "level": level,
                "num": num,
                "P": result.proportional,
                "S": result.subcontrary,
                "G": result.geometric,
                "score_min": result.score_min,
                "P_raw": result.proportional_raw,
                "degenerate_dropped": result.degenerate_dropped,
                "epsilon_cents": result.epsilon_cents,
                "max_span_cents": result.max_span,
                "conj_sep": gen["conj_sep"],
                "window_width": abs(float(den * g_conj - num)),
                "spread": spread,
                "norm_spread": spread / (den * gen["conj_sep"]),
                "spectral_gap": gen["spectral_gap"],
            })
    return rows


#: H-M1 predictor order is FIXED (determinism: one rng consumed in order).
#: MOS-LAT-001's four descriptors plus the now-non-constant spectral gap.
H_M1_PREDICTORS = ("g01_baseline", "conj_sep", "window_width", "spread",
                   "norm_spread", "spectral_gap")


def holm_adjust(pvals: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values (sensitivity report, non-verdict)."""
    items = sorted(pvals.items(), key=lambda kv: (kv[1], kv[0]))
    m = len(items)
    adjusted: dict[str, float] = {}
    running = 0.0
    for i, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[name] = running
    return {name: adjusted[name] for name in pvals}


def run_h_m1(rows: list[dict], n_perm: int = N_PERMUTATIONS) -> dict:
    """The pre-registered H-M1 test — moslat001.run_h_m1's machinery (same
    imported statistics functions, same seed, same verdict rule) with the
    spectral-gap descriptor appended to the fixed predictor order."""
    y = [float(r["P"]) for r in rows]
    z = [float(r["cardinality"]) for r in rows]
    strata = [r["cardinality"] for r in rows]
    predictors = {
        "g01_baseline": [r["g01"] for r in rows],
        "conj_sep": [r["conj_sep"] for r in rows],
        "window_width": [r["window_width"] for r in rows],
        "spread": [r["spread"] for r in rows],
        "norm_spread": [r["norm_spread"] for r in rows],
        "spectral_gap": [r["spectral_gap"] for r in rows],
    }
    rng = random.Random(SEED)
    stats = {}
    for name in H_M1_PREDICTORS:
        x = predictors[name]
        rho = partial_spearman(x, y, z)
        p = stratified_permutation_p(x, y, z, strata, rho, rng, n_perm)
        stats[name] = {"partial_spearman_rho": rho, "permutation_p": p}
    base = abs(stats["g01_baseline"]["partial_spearman_rho"])
    winners = [
        name for name in H_M1_PREDICTORS[1:]
        if stats[name]["permutation_p"] < 0.05
        and abs(stats[name]["partial_spearman_rho"]) > base
    ]
    holm = holm_adjust({name: stats[name]["permutation_p"]
                        for name in H_M1_PREDICTORS[1:]})
    return {
        "outcome": "P (frozen proportional count) controlling for N",
        "n_rows": len(rows),
        "n_generators": len({r["cf"] for r in rows}),
        "seed": SEED,
        "n_permutations": n_perm,
        "permutation_scheme":
            "shuffle predictor within cardinality strata; two-sided; "
            "add-one rule; rng consumed in fixed predictor order",
        "statistics": stats,
        "winners": winners,
        "holm_adjusted_p": holm,
        "holm_survivors": sorted(n for n, p in holm.items() if p < 0.05),
        "verdict": ("SUPPORTED: " + ", ".join(winners)) if winners else
                   "NULL: no descriptor beats the generator-value baseline",
    }


# ---------------------------------------------------------------------------
# descriptor-spread report (the corpus-degeneracy contrast with MOS-LAT-001)
# ---------------------------------------------------------------------------


def descriptor_spread(generators: list[dict], rows: list[dict]) -> dict:
    """Achieved spread of every descriptor — the registered proof that this
    corpus is NOT degenerate the way MOS-LAT-001's was."""

    def stat(values: list[float]) -> dict:
        distinct = len({round(v, 12) for v in values})
        return {"min": min(values), "max": max(values),
                "n_distinct": distinct,
                "max_over_min": (max(values) / min(values))
                if min(values) > 0 else None}

    return {
        "per_generator": {
            "g01": stat([g["g01"] for g in generators]),
            "conj_sep": stat([g["conj_sep"] for g in generators]),
            "spectral_gap": stat([g["spectral_gap"] for g in generators]),
        },
        "per_row": {
            "window_width": stat([r["window_width"] for r in rows]),
            "spread": stat([r["spread"] for r in rows]),
            "norm_spread": stat([r["norm_spread"] for r in rows]),
        },
        "moslat001_contrast": {
            "spectral_gap": "constant phi**2 = 2.618... on the all-1s-tail "
                            "corpus (27 generators, zero information)",
            "receipt": "results/moslat001.json",
        },
    }


def hot_spots(rows: list[dict], top: int = 12) -> list[dict]:
    ordered = sorted(rows, key=lambda r: (-r["P"], r["cf"], r["cardinality"]))
    return [{"cf": r["cf"], "cents": r["cents"], "cardinality":
             r["cardinality"], "P": r["P"], "S": r["S"], "G": r["G"],
             "spectral_gap": r["spectral_gap"], "conj_sep": r["conj_sep"]}
            for r in ordered[:top]]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> dict:
    generators, census = enumerate_corpus()
    rows = run_rows(generators)
    h_m1 = run_h_m1(rows)
    p_eq_s = all(r["P"] == r["S"] for r in rows)
    receipt = {
        "experiment": EXPERIMENT,
        "date": date.today().isoformat(),
        "scorer_version": SCORER_VERSION,
        "max_level": MAX_LEVEL,
        "cardinality_range": [MIN_CARD, MAX_CARD],
        "corpus": {
            **census,
            "generators": [{k: v for k, v in g.items()
                            if not k.startswith("_")} for g in generators],
        },
        "descriptor_spread": descriptor_spread(generators, rows),
        "p_equals_s_everywhere": p_eq_s,
        "rows": rows,
        "h_m1": h_m1,
        "hot_spots": hot_spots(rows),
        "baseline_run": {
            "experiment": "MOS-LAT-001",
            "receipt": "results/moslat001.json",
            "verdict": "NULL: no descriptor beats the generator-value "
                       "baseline (97 rows, 27 all-1s-tail generators)",
        },
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}")
    census = receipt["corpus"]
    print(f"  corpus: {census['n_distinct']} distinct generators "
          f"({census['n_raw']} raw, {census['duplicates_dropped']} dups)")
    for name, st in receipt["descriptor_spread"]["per_generator"].items():
        print(f"    {name:<13} [{st['min']:.6f}, {st['max']:.6f}] "
              f"distinct={st['n_distinct']}")
    for name, st in receipt["descriptor_spread"]["per_row"].items():
        print(f"    {name:<13} [{st['min']:.6f}, {st['max']:.6f}] "
              f"distinct={st['n_distinct']}")
    h = receipt["h_m1"]
    print(f"  rows={h['n_rows']} generators={h['n_generators']} "
          f"P==S everywhere: {receipt['p_equals_s_everywhere']}")
    for name, st in h["statistics"].items():
        print(f"    {name:<14} rho={st['partial_spearman_rho']:+.4f} "
              f"p={st['permutation_p']:.4f}")
    print(f"  holm-adjusted: {h['holm_adjusted_p']}")
    print(f"  H-M1 verdict: {h['verdict']}")
    print("  hot spots:")
    for hs in receipt["hot_spots"][:6]:
        print(f"    {hs['cf']:<22} {hs['cents']:8.2f}c N={hs['cardinality']:2d} "
              f"P={hs['P']}")
    print(f"  receipt: {RESULTS_PATH}")


if __name__ == "__main__":
    _print_summary(main())
