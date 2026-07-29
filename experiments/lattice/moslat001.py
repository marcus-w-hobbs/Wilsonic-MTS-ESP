"""MOS-LAT-001 — lattices from noble generators: cut-and-project round trip.

SPEC.md §MOS-LAT-001. Pre-registered in LOG.md ("MOS-LAT-001
pre-registration", 2026-07-28) BEFORE this module was implemented.

Construction. Every generator here has continued-fraction tail all 1s
(noble), so the tail recurrence is Fibonacci, M = [[1, 1], [1, 0]] with
eigenvalues phi and -1/phi, and every generator lies in Q(sqrt5). The
preamble digits are the GL(2,Z) Moebius mask; conjugation preserves
eigenvalues, so the spectral gap |lambda|/|lambda'| = phi**2 is CONSTANT
over this corpus (recorded once, replaced as a descriptor by the conjugate
separation |g - g'|). Eigen-embedding, exact in Q(sqrt5): lattice point
(octaves a, generator-steps b) has physical coordinate x = a + b*g
(log-pitch, octaves) and internal coordinate iota = a + b*g' (Galois
conjugate, sqrt5 -> -sqrt5). Octave reduction x in [0, 1) fixes
a = -floor(b*g), so admissible points are parametrized by b with
iota(b) = b*g' - floor(b*g).

Step 1 verifies, per (generator, Brun level 0-9), that the window-selected
set {b : iota(b) in W_L} is exactly {0..q-1} for the level's zigzag
fraction (p, q) from families/mos.py (the Brun.cpp:269 semiconvergent
path), under BOTH the a-priori window (0 closed to iota(q) open, derived
from the zigzag fraction) and the closed hull window; and that the
projection matches mos_cents at 1e-6 cents. Step 2 scores every MOS
cardinality 5-22 of the 27-generator digit-string corpus with the FROZEN
triad scorer v1.1.0 (score_tempered, read-only import) and runs the
pre-registered H-M1 partial-Spearman + stratified-permutation test.

Deterministic: fixed seed 20260725, fixed predictor order, stdlib only.
Run from experiments/lattice/:  python3.12 moslat001.py
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
from math import gcd, sqrt
from pathlib import Path

_LATTICE_DIR = Path(__file__).resolve().parent
_TRIADS_DIR = _LATTICE_DIR.parent / "triads"
if str(_TRIADS_DIR) not in sys.path:
    sys.path.insert(0, str(_TRIADS_DIR))

from scorer import (  # noqa: E402
    SCORER_VERSION,
    canonical_cents_scale,
    score_tempered,
)
from families.mos import MAX_LEVEL, mos_cents, zigzag  # noqa: E402

EXPERIMENT = "MOS-LAT-001"
SEED = 20260725
N_PERMUTATIONS = 9999
CENTS_TOLERANCE = 1e-6
MIN_CARD, MAX_CARD = 5, 22
RESULTS_PATH = _LATTICE_DIR / "results" / "moslat001.json"

#: Step-1 generators (SPEC: golden ratio + 2-3 other nobles). CF preambles
#: before the all-1s tail; exact values derived in LOG.md pre-registration.
STEP1_PREAMBLES: tuple[tuple[int, ...], ...] = ((), (2,), (1, 2), (2, 2))

#: Constant over the all-1s-tail corpus (Fibonacci tail matrix): phi**2.
SPECTRAL_GAP_ALL_ONES_TAIL = ((1 + sqrt(5.0)) / 2) ** 2


# ---------------------------------------------------------------------------
# exact arithmetic in Q(sqrt5)
# ---------------------------------------------------------------------------


@total_ordering
@dataclass(frozen=True)
class Q5:
    """Exact (a + b*sqrt5)/c with c > 0 and gcd(a, b, c) = 1. Immutable."""

    a: int
    b: int
    c: int

    def __float__(self) -> float:
        return (self.a + self.b * sqrt(5.0)) / self.c

    def conj(self) -> "Q5":
        """Galois conjugate: sqrt5 -> -sqrt5."""
        return q5(self.a, -self.b, self.c)

    def sign(self) -> int:
        a, b = self.a, self.b  # c > 0 never changes the sign
        if b == 0:
            return (a > 0) - (a < 0)
        if a == 0 or (a > 0) == (b > 0):
            return (b > 0) - (b < 0)
        lhs, rhs = a * a, 5 * b * b  # opposite signs: |a| vs |b|*sqrt5
        if a > 0:
            return 1 if lhs > rhs else -1  # equality impossible (sqrt5 irr.)
        return 1 if rhs > lhs else -1

    def __add__(self, other: "Q5 | int") -> "Q5":
        o = _as_q5(other)
        return q5(self.a * o.c + o.a * self.c,
                  self.b * o.c + o.b * self.c, self.c * o.c)

    def __radd__(self, other: int) -> "Q5":
        return self.__add__(other)

    def __neg__(self) -> "Q5":
        return q5(-self.a, -self.b, self.c)

    def __sub__(self, other: "Q5 | int") -> "Q5":
        return self.__add__(-_as_q5(other))

    def __rsub__(self, other: int) -> "Q5":
        return (-self).__add__(other)

    def __mul__(self, other: "Q5 | int") -> "Q5":
        o = _as_q5(other)
        return q5(self.a * o.a + 5 * self.b * o.b,
                  self.a * o.b + self.b * o.a, self.c * o.c)

    def __rmul__(self, other: int) -> "Q5":
        return self.__mul__(other)

    def inv(self) -> "Q5":
        """1/x = c*(a - b*sqrt5) / (a**2 - 5*b**2)."""
        norm = self.a * self.a - 5 * self.b * self.b
        if norm == 0:
            raise ZeroDivisionError("inverse of zero in Q(sqrt5)")
        return q5(self.c * self.a, -self.c * self.b, norm)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Q5, int)):
            return NotImplemented
        return (self - _as_q5(other)).sign() == 0

    def __lt__(self, other: "Q5 | int") -> bool:
        return (self - _as_q5(other)).sign() < 0

    def __hash__(self) -> int:
        return hash((self.a, self.b, self.c))

    def floor(self) -> int:
        """Exact floor: float candidate, then exact fix-up (few steps)."""
        f = ffloor(float(self))
        while (self - f).sign() < 0:
            f -= 1
        while (self - (f + 1)).sign() >= 0:
            f += 1
        return f

    def pretty(self) -> str:
        return f"({self.a}{self.b:+d}*sqrt5)/{self.c}"


def q5(a: int, b: int, c: int = 1) -> Q5:
    """Normalized constructor: c > 0, gcd(a, b, c) = 1."""
    if c == 0:
        raise ZeroDivisionError("denominator 0 in Q(sqrt5)")
    if c < 0:
        a, b, c = -a, -b, -c
    g = gcd(gcd(abs(a), abs(b)), c)
    return Q5(a // g, b // g, c // g) if g > 1 else Q5(a, b, c)


def _as_q5(x: "Q5 | int") -> Q5:
    return x if isinstance(x, Q5) else q5(int(x), 0, 1)


#: 1/phi = (-1 + sqrt5)/2 — the all-1s continued fraction [0; 1, 1, 1, ...].
PHI_INV = q5(-1, 1, 2)


def noble_from_preamble(preamble: tuple[int, ...]) -> Q5:
    """Exact value of [0; d1, ..., dk, 1, 1, 1, ...] in Q(sqrt5)."""
    value = PHI_INV
    for digit in reversed(preamble):
        value = (_as_q5(digit) + value).inv()
    return value


def canonical_preambles(max_digit: int = 3,
                        max_len: int = 3) -> list[tuple[int, ...]]:
    """All CF preambles with digits <= max_digit, length <= max_len, before
    the all-1s tail — canonicalized: a preamble ending in 1 equals the
    shorter preamble ((..., 1) + tail == (...) + tail), so only the empty
    preamble may 'end' in 1. 27 generators at the defaults."""
    out: list[tuple[int, ...]] = [()]
    for length in range(1, max_len + 1):
        for tup in iproduct(range(1, max_digit + 1), repeat=length):
            if tup[-1] != 1:
                out.append(tup)
    return out


def cf_convergents(preamble: tuple[int, ...],
                   max_den: int, tail_ones: int = 60) -> set[tuple[int, int]]:
    """Convergents (p, q) of [0; preamble, 1, 1, ...] with q <= max_den."""
    digits = list(preamble) + [1] * tail_ones
    out: set[tuple[int, int]] = set()
    h_prev, h_prev2 = 0, 1  # h_0 = a0 = 0, h_{-1} = 1
    k_prev, k_prev2 = 1, 0
    for d in digits:
        h_cur = d * h_prev + h_prev2
        k_cur = d * k_prev + k_prev2
        if k_cur > max_den:
            break
        out.add((h_cur, k_cur))
        h_prev2, h_prev = h_prev, h_cur
        k_prev2, k_prev = k_prev, k_cur
    return out


# ---------------------------------------------------------------------------
# step 1 — cut-and-project verification against the Brun zigzag
# ---------------------------------------------------------------------------


def iota(b: int, g: Q5, g_conj: Q5) -> Q5:
    """Internal coordinate of the octave-reduced lattice point for b
    generator steps: iota(b) = b*g' - floor(b*g)."""
    return b * g_conj - (b * g).floor()


def verify_level(g: Q5, g_conj: Q5, g01: float,
                 level: int, num: int, den: int) -> dict:
    """One (generator, level) verification record. Exact arithmetic for the
    selection; floats only for the receipt and the mos.py comparison."""
    iotas_in = [iota(b, g, g_conj) for b in range(den)]
    hull_lo = min(iotas_in)
    hull_hi = max(iotas_in)
    argmin = iotas_in.index(hull_lo)
    argmax = iotas_in.index(hull_hi)

    scan_pad = 5 * den + 100  # drift bound: N + 2/|g-g'| would suffice
    scan = range(-scan_pad, den + scan_pad + 1)
    iotas_all = {b: iota(b, g, g_conj) for b in scan}

    hull_selected = [b for b in scan
                     if hull_lo <= iotas_all[b] <= hull_hi]
    hull_bit = hull_selected == list(range(den))

    iota_q = iota(den, g, g_conj)  # a-priori window edge from the fraction
    if iota_q.sign() > 0:
        ap_selected = [b for b in scan
                       if iotas_all[b].sign() >= 0 and iotas_all[b] < iota_q]
    else:
        ap_selected = [b for b in scan
                       if iota_q < iotas_all[b] and iotas_all[b].sign() <= 0]
    ap_bit = ap_selected == list(range(den))

    projected = canonical_cents_scale(
        (b * g01 * 1200.0) % 1200.0 for b in range(den))
    expected = mos_cents(g01, den)
    if len(projected) == len(expected):
        cents_diff = max((abs(p - e) for p, e in zip(projected, expected)),
                         default=0.0)
    else:
        cents_diff = float("inf")
    cents_bit = cents_diff <= CENTS_TOLERANCE

    u_defect = float(den * g - num)          # physical defect q*g - p
    w_internal = float(den * g_conj - num)   # internal length q*g' - p

    def _stray(selected: list[int]) -> dict:
        inside = set(selected)
        return {
            "intruders": sorted(b for b in inside if not 0 <= b < den),
            "excluded": sorted(b for b in range(den) if b not in inside),
        }

    # Investigation fields (LOG.md pre-registration commissions documenting
    # WHY a level fails): where the next chain point iota(q) sits relative
    # to the hull, and — when the murchana-0 segment [0, q) fails — whether
    # OTHER contiguous chain segments [b0, b0+q) are window-representable
    # (the same MOS up to transposition/murchana).
    if iota_q < hull_lo:
        iota_q_vs_hull = "below"
    elif iota_q > hull_hi:
        iota_q_vs_hull = "above"
    elif iota_q == hull_lo or iota_q == hull_hi:
        iota_q_vs_hull = "on_edge"
    else:
        iota_q_vs_hull = "inside"

    murchana = None
    if not hull_bit:
        wide = {b: iota(b, g, g_conj)
                for b in range(-3 * den - 100, 4 * den + 101)}
        representable = []
        for b0 in range(-den, den + 1):
            seg = [wide[b0 + j] for j in range(den)]
            seg_lo, seg_hi = min(seg), max(seg)
            sel = [b for b in range(b0 - den - 60, b0 + 2 * den + 61)
                   if seg_lo <= wide[b] <= seg_hi]
            if sel == list(range(b0, b0 + den)):
                representable.append(b0)
        murchana = {
            "shifts_tested": [-den, den],
            "representable_count": len(representable),
            "representable_examples": representable[:8],
        }

    return {
        "level": level,
        "num": num,
        "den": den,
        "u_defect": u_defect,
        "u_sign": (u_defect > 0) - (u_defect < 0),
        "w_internal": w_internal,
        "iota_q": float(iota_q),
        "iota_q_vs_hull": iota_q_vs_hull,
        "murchana_analysis": murchana,
        "hull": [float(hull_lo), float(hull_hi)],
        "hull_argmin_b": argmin,
        "hull_argmax_b": argmax,
        "hull_window_bit": hull_bit,
        "ap_window_bit": ap_bit,
        "hull_strays": _stray(hull_selected),
        "ap_strays": _stray(ap_selected),
        "cents_max_abs_diff": cents_diff,
        "cents_bit": cents_bit,
        "verified": hull_bit and ap_bit and cents_bit,
    }


def run_step1() -> list[dict]:
    records = []
    for preamble in STEP1_PREAMBLES:
        g = noble_from_preamble(preamble)
        g_conj = g.conj()
        g01 = float(g)
        conj_sep = abs(float(g - g_conj))
        monotone = conj_sep > 1.0  # |iota step| >= |g'-g| - 1 > 0
        zz = zigzag(g01)
        convergents = cf_convergents(preamble, max_den=max(d for _, d in zz))
        levels = []
        for level, (num, den) in enumerate(zz):
            rec = verify_level(g, g_conj, g01, level, num, den)
            rec["is_cf_convergent"] = (num, den) in convergents or den == 1
            levels.append(rec)
        records.append({
            "preamble": list(preamble),
            "cf": "[0;" + ",".join(map(str, preamble)) + ",(1)*]",
            "value_exact": g.pretty(),
            "conjugate_exact": g_conj.pretty(),
            "g01": g01,
            "cents": g01 * 1200.0,
            "conj_separation": conj_sep,
            "internal_monotone": monotone,
            "levels": levels,
            "all_levels_verified": all(r["verified"] for r in levels),
        })
    return records


# ---------------------------------------------------------------------------
# step 2 — frozen scores + conjugate-embedding descriptors, H-M1
# ---------------------------------------------------------------------------


def run_step2_rows() -> list[dict]:
    rows = []
    for preamble in canonical_preambles():
        g = noble_from_preamble(preamble)
        g_conj = g.conj()
        g01 = float(g)
        conj_sep = abs(float(g - g_conj))
        zz = zigzag(g01)
        first_level = {}
        for level, (num, den) in enumerate(zz):
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
                "preamble": list(preamble),
                "g01": g01,
                "cents": g01 * 1200.0,
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
                "conj_sep": conj_sep,
                "window_width": abs(float(den * g_conj - num)),
                "spread": spread,
                "norm_spread": spread / (den * conj_sep),
            })
    return rows


# --- rank statistics (stdlib only, deterministic) --------------------------


def ranks(values: list[float]) -> list[float]:
    """Average ranks (1-based) with ties shared."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    out = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0.0 or syy == 0.0:
        return 0.0
    return sxy / sqrt(sxx * syy)


def residualize(y: list[float], z: list[float]) -> list[float]:
    """Least-squares residual of y on z (with intercept)."""
    n = len(y)
    mz, my = sum(z) / n, sum(y) / n
    szz = sum((c - mz) ** 2 for c in z)
    beta = 0.0 if szz == 0.0 else sum(
        (c - mz) * (d - my) for c, d in zip(z, y)) / szz
    return [d - (my + beta * (c - mz)) for c, d in zip(z, y)]


def partial_spearman(x: list[float], y: list[float],
                     z: list[float]) -> float:
    """Spearman correlation of x and y with z ranked out of both."""
    rx, ry, rz = ranks(x), ranks(y), ranks(z)
    return pearson(residualize(rx, rz), residualize(ry, rz))


def stratified_permutation_p(x: list[float], y: list[float], z: list[float],
                             strata: list[int], observed: float,
                             rng: random.Random,
                             n_perm: int = N_PERMUTATIONS) -> float:
    """Two-sided permutation p for partial_spearman(x, y | z), shuffling x
    only within strata (here: cardinality classes). Add-one rule."""
    by_stratum: dict[int, list[int]] = {}
    for idx, s in enumerate(strata):
        by_stratum.setdefault(s, []).append(idx)
    groups = [idx_list for _, idx_list in sorted(by_stratum.items())]
    hits = 0
    threshold = abs(observed) - 1e-12
    for _ in range(n_perm):
        xp = list(x)
        for idx_list in groups:
            vals = [x[i] for i in idx_list]
            rng.shuffle(vals)
            for i, v in zip(idx_list, vals):
                xp[i] = v
        if abs(partial_spearman(xp, y, z)) >= threshold:
            hits += 1
    return (hits + 1) / (n_perm + 1)


#: H-M1 predictor order is FIXED (determinism: one rng consumed in order).
H_M1_PREDICTORS = ("g01_baseline", "conj_sep", "window_width", "spread",
                   "norm_spread")


def run_h_m1(rows: list[dict], n_perm: int = N_PERMUTATIONS) -> dict:
    y = [float(r["P"]) for r in rows]
    z = [float(r["cardinality"]) for r in rows]
    strata = [r["cardinality"] for r in rows]
    predictors = {
        "g01_baseline": [r["g01"] for r in rows],
        "conj_sep": [r["conj_sep"] for r in rows],
        "window_width": [r["window_width"] for r in rows],
        "spread": [r["spread"] for r in rows],
        "norm_spread": [r["norm_spread"] for r in rows],
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
    return {
        "outcome": "P (frozen proportional count) controlling for N",
        "n_rows": len(rows),
        "n_generators": len({tuple(r["preamble"]) for r in rows}),
        "seed": SEED,
        "n_permutations": n_perm,
        "permutation_scheme":
            "shuffle predictor within cardinality strata; two-sided; "
            "add-one rule; rng consumed in fixed predictor order",
        "statistics": stats,
        "winners": winners,
        "verdict": ("SUPPORTED: " + ", ".join(winners)) if winners else
                   "NULL: no descriptor beats the generator-value baseline",
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> dict:
    step1 = run_step1()
    rows = run_step2_rows()
    h_m1 = run_h_m1(rows)
    p_eq_s = all(r["P"] == r["S"] for r in rows)
    receipt = {
        "experiment": EXPERIMENT,
        "date": date.today().isoformat(),
        "scorer_version": SCORER_VERSION,
        "max_level": MAX_LEVEL,
        "cents_tolerance": CENTS_TOLERANCE,
        "spectral_gap_note": (
            "all-1s-tail corpus: |lambda|/|lambda'| = phi**2 = "
            f"{SPECTRAL_GAP_ALL_ONES_TAIL!r} for EVERY generator "
            "(preamble acts by GL(2,Z) conjugation) — zero information "
            "here; conj_separation |g - g'| replaces it (LOG.md)."),
        "step1": {
            "generators": step1,
            "summary": {
                g["cf"]: [lv["verified"] for lv in g["levels"]]
                for g in step1
            },
        },
        "step2": {
            "enumeration": (
                "CF digit strings, digits <= 3, preamble length <= 3, "
                "all-1s tail; preambles ending in 1 canonicalized away "
                "(identical value); 27 generators; cardinalities "
                f"{MIN_CARD}-{MAX_CARD} at Brun levels 0-{MAX_LEVEL}"),
            "p_equals_s_everywhere": p_eq_s,
            "rows": rows,
            "h_m1": h_m1,
        },
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}")
    for gen in receipt["step1"]["generators"]:
        bits = "".join("1" if lv["verified"] else "0"
                       for lv in gen["levels"])
        print(f"  step1 {gen['cf']:<18} levels 0-9: {bits}  "
              f"(monotone={gen['internal_monotone']})")
    h = receipt["step2"]["h_m1"]
    print(f"  step2 rows={h['n_rows']} generators={h['n_generators']} "
          f"P==S everywhere: {receipt['step2']['p_equals_s_everywhere']}")
    for name, st in h["statistics"].items():
        print(f"    {name:<14} rho={st['partial_spearman_rho']:+.4f} "
              f"p={st['permutation_p']:.4f}")
    print(f"  H-M1 verdict: {h['verdict']}")
    print(f"  receipt: {RESULTS_PATH}")


if __name__ == "__main__":
    _print_summary(main())
