"""BRIDGE-002 — the eikosany as bridge payload: EG6 CPS(6,3) on {1,3,5,7,9,11}
inside 11-limit rank-2 temperament hosts (LOG.md pre-registration
2026-10-09, written BEFORE this file existed).

SPEC §BRIDGE-001's EG6 scale-up, unblocked by G-016/G-021 (identity lens
adopted for BRIDGE-002; any front over a sweep must be error-capped or
identity-scored) and by blog 002's closing paragraph (try the eikosany
itself as payload; tune by a tone-set minimax). Same binding design
decisions as BRIDGE-001 (Marcus, SPEC): degrees BY THE VAL, no
nearest-degree rounding; monotonicity filter FIRST; anchoring is a free
design parameter.

What changes at EG6 (all pre-registered):
  * payload = the 20 eikosany tones (no 1/1 — the host root may sit at
    degree 0 or N without that being a payload collision);
  * the kernel has rank 3, so BRIDGE-001b's second-comma sweep is replaced
    by the join-of-vals sweep: temperament = saturated <v, w> for every
    11-limit val w at cardinality 1..46, patent +-1, deduped by (mapping, v);
  * four tunings on contained rows: prime / tone_set / interval minimax
    (exact, piecewise-linear) and a direct `survival` grid argmax of the
    identity count at eps = 2c (the existence oracle);
  * the identity lens (the eikosany's OWN 114 labelled triads) is the
    scored quantity; the count lens (frozen score_tempered) is recorded only.

Linear algebra, the minimax solver and the identity lens generalize
bridge001.py / bridge001b.py to five primes; each generalization is
unit-tested against the 7-limit originals on the BRIDGE-001 fixtures.
Frozen scorers (triads v1.1.0, melodic v0.1.0) are imported read-only.
python3.12 stdlib only; deterministic.

Run from experiments/lattice/:  python3.12 bridge002.py
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import date
from fractions import Fraction
from itertools import combinations, product
from math import gcd, log2, prod
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import scorer as triad  # noqa: E402  (frozen v1.1.0, read-only)
from scorer import canonical_rational_scale, reduce_rational  # noqa: E402
from melodic import MELODIC_VERSION, score_melodic  # noqa: E402  (frozen)

RESULTS = HERE / "results" / "bridge002.jsonl"
SIDECAR = HERE / "results" / "bridge002_sidecar.jsonl.gz"
SUMMARY = HERE / "results" / "bridge002_summary.json"
BRIDGE000 = HERE / "results" / "bridge000.json"
SCL_DIR = HERE / "results" / "scl" / "bridge002"

# ---------------------------------------------------------------- locked --
PRIMES = (2, 3, 5, 7, 11)
NP = len(PRIMES)
LOG2P = tuple(log2(p) for p in PRIMES)
SEEDS = (1, 3, 5, 7, 9, 11)
N_RANGE = range(20, 47)               # host cardinalities
W_RANGE = range(1, 47)                # second-val cardinalities
VAL_OFFSETS = (-1, 0, 1)              # patent +- 1 per odd coordinate
EPS_TEMPERED = 2.0                    # frozen scorer epsilon for the lens
EPS_SWEEP = range(1, 16)              # recovery sweep, cents
EPS_BRIDGE = 15.0                     # error budget (in-budget cap)
SURVIVAL_HALF_WIDTH = 10.0            # survival grid: g_prime +- 10c
SURVIVAL_STEP = 0.02                  # survival grid step, cents
HEXANY_REPORT_EPS = (2, 3, 4)
COMMA_BOX = (8, 5, 4, 3)              # |e3|, |e5|, |e7|, |e11|
COMMA_MAX_CENTS = 60.0
TENNEY_MAX_LOG2 = 40.0
FLOAT_EPS = 1e-6
W_WITNESSES_KEPT = 4
TUNINGS = ("prime", "tone_set", "interval", "survival")
ANALYTIC = ("prime", "tone_set", "interval")

#: Labels only, resolved from standard 11-limit comma triples at load; an
#: unnamed mapping is reported by its HNF. A wrong label changes no number.
NAMED_TEMPERAMENTS = {
    "miracle": ("225/224", "1029/1024", "385/384"),
    "orwell": ("225/224", "1728/1715", "99/98"),
    "magic": ("225/224", "245/243", "100/99"),
    "huygens": ("81/80", "126/125", "99/98"),
    "meanpop": ("81/80", "126/125", "385/384"),
    "mothra": ("81/80", "1029/1024", "99/98"),
    "valentine": ("126/125", "1029/1024", "441/440"),
    "mohajira": ("81/80", "6144/6125", "121/120"),
    "hemififths": ("2401/2400", "5120/5103", "441/440"),
    "garibaldi": ("32805/32768", "5120/5103", "385/384"),
    "pajara": ("50/49", "64/63", "99/98"),
    "porcupine": ("250/243", "64/63", "55/54"),
    "myna": ("126/125", "1728/1715", "176/175"),
    "sensi": ("126/125", "245/243", "385/384"),
    "rodan": ("245/243", "1029/1024", "385/384"),
    "catakleismic": ("225/224", "4375/4374", "385/384"),
    "superpyth": ("64/63", "245/243", "99/98"),
    "lemba": ("50/49", "525/512", "99/98"),
    "injera": ("50/49", "81/80", "99/98"),
    "ennealimmal": ("2401/2400", "4375/4374", "3025/3024"),
    "unidec": ("3025/3024", "5120/5103", "2401/2400"),
}

Monzo = tuple[int, ...]
Mapping = tuple[tuple[int, ...], tuple[int, ...]]


# ---------------------------------------------------------------- monzos --

def monzo_of(fr: Fraction) -> Monzo:
    m = [0] * NP
    n, d = fr.numerator, fr.denominator
    for i, p in enumerate(PRIMES):
        while n % p == 0:
            n //= p
            m[i] += 1
        while d % p == 0:
            d //= p
            m[i] -= 1
    assert n == 1 and d == 1, f"prime outside 11-limit in {fr}"
    return tuple(m)


def ratio_of(m: Monzo) -> Fraction:
    fr = Fraction(1)
    for e, p in zip(m, PRIMES):
        fr *= Fraction(p) ** e
    return fr


def cents_of(m: Monzo) -> float:
    return 1200.0 * sum(e * l for e, l in zip(m, LOG2P))


def tenney_log2(m: Monzo) -> float:
    return sum(abs(e) * l for e, l in zip(m, LOG2P))


def neg(m: Monzo) -> Monzo:
    return tuple(-e for e in m)


def frac_str(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}"


def small_comma_of(a: Fraction, b: Fraction) -> Fraction:
    """Octave-equivalent representative of a/b closest to (and >= ) 1."""
    r = reduce_rational(a / b)
    return 2 / r if r * r > 2 else r


def vdot(v: tuple[int, ...], m: Monzo) -> int:
    return sum(a * b for a, b in zip(v, m))


# --------------------------------------------------------------- payload --

def eikosany_products() -> tuple[int, ...]:
    return tuple(sorted(prod(c) for c in combinations(SEEDS, 3)))


PRODUCTS = eikosany_products()
assert len(PRODUCTS) == 20 and len(set(PRODUCTS)) == 20


def _tone(p: int) -> dict:
    red = reduce_rational(Fraction(p))
    m = monzo_of(red)
    return {"product": p, "ratio": red, "monzo": m, "cents": cents_of(m)}


TONES = sorted((_tone(p) for p in PRODUCTS), key=lambda t: t["cents"])
assert len({t["ratio"] for t in TONES}) == 20, "eikosany tones must be distinct"
TONE_MONZOS = tuple(t["monzo"] for t in TONES)
TONE_BY_PRODUCT = {t["product"]: t for t in TONES}


def _subset_products(fixed_in, fixed_out) -> tuple[int, ...]:
    return tuple(prod(c) for c in combinations(SEEDS, 3)
                 if all(v in c for v in fixed_in)
                 and not any(v in c for v in fixed_out))


def embedded_subsets() -> list[dict]:
    """The 30 hexanies hexany[in=x,out=y] and 12 dekanies of the eikosany,
    in subsetmel000.enumerate_subsets order and naming (re-derived here to
    avoid importing that module's dependency chain; equality is tested)."""
    out = []
    for x in SEEDS:
        out.append({"name": f"dekany_in[in={x},out=none]", "kind": "dekany",
                    "products": _subset_products((x,), ())})
    for x in SEEDS:
        out.append({"name": f"dekany_out[in=none,out={x}]", "kind": "dekany",
                    "products": _subset_products((), (x,))})
    for x in SEEDS:
        for y in SEEDS:
            if x != y:
                out.append({"name": f"hexany[in={x},out={y}]",
                            "kind": "hexany",
                            "products": _subset_products((x,), (y,))})
    for s in out:
        s["base"] = triad.score(canonical_rational_scale(
            Fraction(p) for p in s["products"]))
    return out


# -------------------------------------------------------- identity lens --

def _shift_into_open(pc: Fraction, lo: Fraction, hi: Fraction):
    r = pc
    while r <= lo:
        r *= 2
    while r >= hi:
        r /= 2
    return r if lo < r < hi else None


def base_triads(products) -> list:
    """A product set's own labelled (P/S) triads under the anchored
    convention: (label, (prod_a, oct_a), (prod_b, 0), (prod_c, oct_c)).
    bridge001b.base_triads generalized to any product list."""
    pcs = {p: reduce_rational(Fraction(p)) for p in products}
    out = []
    for pb, b in sorted(pcs.items(), key=lambda kv: kv[1]):
        for pa, apc in pcs.items():
            a = _shift_into_open(apc, b / 2, b)
            if a is None:
                continue
            for pc_, cpc in pcs.items():
                c = _shift_into_open(cpc, b, 2 * b)
                if c is None or c / a > triad.DEFAULT_MAX_SPAN:
                    continue
                label = triad.classify_rational_triple(a, b, c)
                if label in (triad.PROPORTIONAL, triad.SUBCONTRARY):
                    oa = round(log2(a / apc))
                    oc = round(log2(c / cpc))
                    out.append((label, (pa, oa), (pb, 0), (pc_, oc)))
    return out


def identity_survival(temp_by_prod: dict, eps: float, triads) -> tuple[int, int]:
    """How many of the base's own (P, S) triads keep their label in the
    tempered image at eps (same triple, same octave placement)."""
    p = s = 0
    classify = triad.classify_cents_triple
    for label, (pa, oa), (pb, ob), (pc_, oc) in triads:
        a = temp_by_prod[pa] + 1200.0 * oa
        b = temp_by_prod[pb] + 1200.0 * ob
        c = temp_by_prod[pc_] + 1200.0 * oc
        if not a < b < c:
            continue
        if label in classify(a, b, c, eps):
            if label == triad.PROPORTIONAL:
                p += 1
            else:
                s += 1
    return p, s


EIKOSANY_TRIADS = base_triads(PRODUCTS)
EIKOSANY_BASE = triad.score(canonical_rational_scale(
    Fraction(p) for p in PRODUCTS))
FULL = (EIKOSANY_BASE.proportional, EIKOSANY_BASE.subcontrary)
assert FULL == (57, 57), FULL
assert sum(t[0] == triad.PROPORTIONAL for t in EIKOSANY_TRIADS) == 57
assert sum(t[0] == triad.SUBCONTRARY for t in EIKOSANY_TRIADS) == 57

SUBSETS = embedded_subsets()
for _s in SUBSETS:
    _s["triads"] = base_triads(_s["products"])
    assert (len([t for t in _s["triads"] if t[0] == triad.PROPORTIONAL]),
            len([t for t in _s["triads"] if t[0] == triad.SUBCONTRARY])) \
        == (_s["base"].proportional, _s["base"].subcontrary)
    # every subset triad is an eikosany triad (same tones, same placement)
    assert set(_s["triads"]) <= set(EIKOSANY_TRIADS)
HEXANIES = [s for s in SUBSETS if s["kind"] == "hexany"]
DEKANIES = [s for s in SUBSETS if s["kind"] == "dekany"]
assert len(HEXANIES) == 30 and len(DEKANIES) == 12


# ---------------------------------------------------------------- vals ----

def patent_val(n: int) -> tuple[int, ...]:
    return (n,) + tuple(round(n * LOG2P[i]) for i in range(1, NP))


def vals_for(n: int) -> list[tuple[int, ...]]:
    pat = patent_val(n)
    return [(n,) + tuple(pat[i] + o[i - 1] for i in range(1, NP))
            for o in product(VAL_OFFSETS, repeat=NP - 1)]


def monotonicity(v: tuple[int, ...]) -> dict:
    """Marcus's filter on the 20 eikosany tones: unreduced degrees d(t) =
    v.monzo(t) in pitch order must be weakly increasing within [0, N]. The
    payload has no 1/1, so the host root may sit at degree 0 or N; ties
    mod N among payload tones are collisions, strict decreases reject."""
    n = v[0]
    degs = [vdot(v, m) for m in TONE_MONZOS]
    violations = []
    for i in range(len(TONES) - 1):
        if degs[i + 1] < degs[i]:
            violations.append({
                "pair": [frac_str(TONES[i]["ratio"]),
                         frac_str(TONES[i + 1]["ratio"])],
                "degrees": [degs[i], degs[i + 1]]})
    if min(degs) < 0 or max(degs) > n:
        violations.append({"pair": ["1/1", "2/1"],
                           "degrees": [min(degs), max(degs)]})
    collisions = []
    for i, j in combinations(range(len(TONES)), 2):
        if degs[i] % n == degs[j] % n:
            cm = small_comma_of(TONES[j]["ratio"], TONES[i]["ratio"])
            collisions.append({
                "tones": [frac_str(TONES[i]["ratio"]),
                          frac_str(TONES[j]["ratio"])],
                "degree": degs[i] % n, "comma": frac_str(cm),
                "comma_monzo": list(monzo_of(cm))})
    return {"monotone": not violations, "degrees": degs,
            "violations": violations, "collisions": collisions}


# ----------------------------------------------- integer linear algebra --

def nullspace_saturated(rows: list, nc: int) -> list[list[int]]:
    """Saturated basis of {x in Z^nc : r.x = 0 for r in rows} via column
    reduction with a tracked unimodular V (bridge001.nullspace_saturated,
    dimension-generic)."""
    a = [list(r) for r in rows]
    nr = len(a)
    v = [[int(i == j) for j in range(nc)] for i in range(nc)]

    def swapcol(j, k):
        for row in a:
            row[j], row[k] = row[k], row[j]
        for row in v:
            row[j], row[k] = row[k], row[j]

    def addcol(j, k, q):
        for row in a:
            row[j] += q * row[k]
        for row in v:
            row[j] += q * row[k]

    r = 0
    for i in range(nr):
        piv = next((j for j in range(r, nc) if a[i][j] != 0), None)
        if piv is None:
            continue
        swapcol(r, piv)
        while True:
            nz = [j for j in range(r + 1, nc) if a[i][j] != 0]
            if not nz:
                break
            for j in nz:
                q = a[i][j] // a[i][r]
                addcol(j, r, -q)
                if a[i][j] != 0:
                    swapcol(r, j)
        r += 1
    return [[v[i][j] for i in range(nc)] for j in range(r, nc)]


def hnf_mapping(basis: list[list[int]]) -> Mapping:
    """Row-Hermite normal form of a 2 x nc mapping: period row first
    (M[0][0] = periods per octave > 0), generator row with M[1][0] = 0
    (bridge001.hnf_mapping, dimension-generic)."""
    a, b = [list(r) for r in basis]
    nc = len(a)
    if a[0] == 0 and b[0] == 0:
        raise ValueError("mapping has no octave component")
    while b[0] != 0:
        if a[0] == 0:
            a, b = b, a
            continue
        q = b[0] // a[0]
        b = [bi - q * ai for bi, ai in zip(b, a)]
        if b[0] != 0:
            a, b = b, a
    if a[0] < 0:
        a = [-x for x in a]
    j = next((k for k in range(1, nc) if b[k] != 0), None)
    if j is None:
        raise ValueError("degenerate generator row")
    if b[j] < 0:
        b = [-x for x in b]
    q = a[j] // b[j]
    a = [ai - q * bi for ai, bi in zip(a, b)]
    return (tuple(a), tuple(b))


def val_combo(v: tuple[int, ...], m: Mapping):
    """Integers (alpha, beta) with v = alpha*M0 + beta*M1, else None."""
    x = m[0][0]
    if x == 0 or v[0] % x != 0:
        return None
    alpha = v[0] // x
    j = next(k for k in range(1, len(v)) if m[1][k] != 0)
    num = v[j] - alpha * m[0][j]
    if num % m[1][j] != 0:
        return None
    beta = num // m[1][j]
    for k in range(len(v)):
        if alpha * m[0][k] + beta * m[1][k] != v[k]:
            return None
    return alpha, beta


def join_mapping(v: tuple[int, ...], w: tuple[int, ...]):
    """The rank-2 temperament supported by both vals: the saturation of
    span<v, w>, i.e. the vals vanishing on ker v ∩ ker w. None when w is
    dependent on v."""
    kernel = nullspace_saturated([v, w], NP)
    if len(kernel) != NP - 2:
        return None
    basis = nullspace_saturated(kernel, NP)
    if len(basis) != 2:
        return None
    return hnf_mapping(basis)


def mapping_of_commas(commas) -> Mapping:
    return hnf_mapping(nullspace_saturated(
        [monzo_of(Fraction(c)) for c in commas], NP))


def resolve_names() -> dict:
    names = {}
    for name, cs in sorted(NAMED_TEMPERAMENTS.items()):
        names.setdefault(mapping_of_commas(cs), name)
    return names


# --------------------------------------------------------------- commas --

def enumerate_commas() -> list[Monzo]:
    """Primitive 11-limit commas, >1 representative, 0 < cents < 60, odd
    box COMMA_BOX, Tenney height <= 2^40 (for kernel labelling only)."""
    out = set()
    for odd in product(*(range(-b, b + 1) for b in COMMA_BOX)):
        if not any(odd):
            continue
        odd_cents = 1200.0 * sum(e * LOG2P[i + 1] for i, e in enumerate(odd))
        e2 = -round(odd_cents / 1200.0)
        m: Monzo = (e2,) + tuple(odd)
        c = cents_of(m)
        if c < 0:
            m, c = neg(m), -c
        if not (0.0 < c < COMMA_MAX_CENTS):
            continue
        g = 0
        for e in m:
            g = gcd(g, abs(e))
        if g != 1:
            continue
        if tenney_log2(m) > TENNEY_MAX_LOG2:
            continue
        out.add(m)
    return sorted(out, key=lambda m: (tenney_log2(m), m))


def kernel_commas(mapping: Mapping, commas: list[Monzo]) -> list[str]:
    return [frac_str(ratio_of(c)) for c in commas
            if vdot(mapping[0], c) == 0 and vdot(mapping[1], c) == 0]


# --------------------------------------------------------------- tuning --

def tempered_pitch(mapping: Mapping, g: float, monzo: Monzo) -> float:
    per = 1200.0 / mapping[0][0]
    return (vdot(mapping[0], monzo) * per + vdot(mapping[1], monzo) * g)


def lines_for(mapping: Mapping, monzos) -> list[tuple[float, float]]:
    """Error lines e(g) = a + b*g for each monzo (pure octaves)."""
    per = 1200.0 / mapping[0][0]
    out = []
    for m in monzos:
        a = vdot(mapping[0], m) * per - cents_of(m)
        b = float(vdot(mapping[1], m))
        if a == 0.0 and b == 0.0:
            continue
        out.append((a, b))
    return out


def interval_lines(mapping: Mapping, monzos) -> list[tuple[float, float]]:
    """Pairwise-difference lines: the translation-invariant errors."""
    per = 1200.0 / mapping[0][0]
    raw = [(vdot(mapping[0], m) * per - cents_of(m), float(vdot(mapping[1], m)))
           for m in monzos]
    out = []
    for (a1, b1), (a2, b2) in combinations(raw, 2):
        a, b = a1 - a2, b1 - b2
        if a == 0.0 and b == 0.0:
            continue
        out.append((a, b))
    return out


def minimax_exact(lines: list[tuple[float, float]]) -> tuple[float, float]:
    """Exact piecewise-linear minimax of max_i |a_i + b_i g| over pairwise
    crossings and per-line zeros; ties -> smaller g (bridge001b's solver).
    O(L^2) candidates: use for small line sets."""
    cands = []
    for (a1, b1), (a2, b2) in combinations(lines, 2):
        for s in (1.0, -1.0):
            if b1 - s * b2 != 0.0:
                cands.append(-(a1 - s * a2) / (b1 - s * b2))
    for a1, b1 in lines:
        if b1 != 0.0:
            cands.append(-a1 / b1)
    if not cands:
        return 0.0, max(abs(a1) for a1, _ in lines)
    best = min(cands, key=lambda g: (max(abs(a + b * g) for a, b in lines), g))
    return best, max(abs(a + b * best) for a, b in lines)


def minimax_fast(lines: list[tuple[float, float]]) -> tuple[float, float]:
    """Same optimum as minimax_exact for large line sets: bisection on the
    subgradient of the convex function f(g) = max |a + b g| brackets the
    minimizer, then the crossing of the two active lines (and their zeros)
    is solved exactly. Equality with minimax_exact is unit-tested."""
    if not lines:
        return 0.0, 0.0
    if all(b == 0.0 for _, b in lines):
        return 0.0, max(abs(a) for a, _ in lines)

    def f(g):
        return max(abs(a + b * g) for a, b in lines)

    def slope(g):
        a, b = max(lines, key=lambda ab: (abs(ab[0] + ab[1] * g), ab))
        return b if a + b * g >= 0 else -b

    lo, hi = -1e5, 1e5
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if slope(mid) > 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-9:
            break
    g0 = 0.5 * (lo + hi)
    active = sorted(lines, key=lambda ab: -abs(ab[0] + ab[1] * g0))[:4]
    cands = []
    for (a1, b1), (a2, b2) in combinations(active, 2):
        for s in (1.0, -1.0):
            if b1 - s * b2 != 0.0:
                cands.append(-(a1 - s * a2) / (b1 - s * b2))
    for a1, b1 in active:
        if b1 != 0.0:
            cands.append(-a1 / b1)
    cands.append(g0)
    best = min(cands, key=lambda g: (f(g), g))
    return best, f(best)


PRIME_MONZOS = tuple(tuple(int(i == k) for i in range(NP)) for k in range(1, NP))


def prime_minimax(mapping: Mapping) -> tuple[float, float]:
    return minimax_exact(lines_for(mapping, PRIME_MONZOS))


def tone_set_minimax(mapping: Mapping) -> tuple[float, float]:
    return minimax_exact(lines_for(mapping, TONE_MONZOS))


def interval_minimax(mapping: Mapping) -> tuple[float, float]:
    return minimax_fast(interval_lines(mapping, TONE_MONZOS))


def tempered_by_product(mapping: Mapping, g: float) -> dict[int, float]:
    return {t["product"]: tempered_pitch(mapping, g, t["monzo"]) for t in TONES}


def tone_errors(mapping: Mapping, g: float) -> list[float]:
    return [tempered_pitch(mapping, g, t["monzo"]) - t["cents"] for t in TONES]


def survival_grid(mapping: Mapping, g_prime: float, analytic_gs,
                  eps: float = EPS_TEMPERED) -> dict:
    """Direct argmax of identity P+S at eps over g_prime +- HALF_WIDTH at
    STEP, plus the analytic generators; ties -> smaller max tone error,
    then smaller g. The existence oracle for the bridge question."""
    k = int(round(SURVIVAL_HALF_WIDTH / SURVIVAL_STEP))
    grid = [g_prime + i * SURVIVAL_STEP for i in range(-k, k + 1)]
    cands = sorted(set(grid) | set(analytic_gs))
    best = None
    argmax_count = 0
    for g in cands:
        tbp = tempered_by_product(mapping, g)
        p, s = identity_survival(tbp, eps, EIKOSANY_TRIADS)
        err = max(abs(tbp[t["product"]] - t["cents"]) for t in TONES)
        key = (-(p + s), err, g)
        if best is None or key < best[0]:
            best = (key, g, p, s)
            argmax_count = 1
        elif key[0] == best[0][0]:
            argmax_count += 1
    _, g, p, s = best
    return {"g": g, "identity_P": p, "identity_S": s,
            "grid_points": len(cands), "argmax_count": argmax_count}


# ------------------------------------------------------------- host ------

def host_receipt(mapping: Mapping, n: int, degrees: list[int]) -> dict:
    """Structural (tuning-independent) host receipt: chain coordinates,
    span, containment and the murchana anchor interval (bridge001)."""
    x = mapping[0][0]
    npp = n // x
    b = [vdot(mapping[1], m) for m in TONE_MONZOS]
    span = max(b) - min(b) + 1
    contained0 = all(0 <= bi < npp for bi in b)
    anchor_lo = max(b) - npp + 1
    anchor_hi = min(b)
    contained = span <= npp
    anchor = 0 if contained0 else (
        min((a for a in range(anchor_lo, anchor_hi + 1)), key=abs)
        if contained else None)
    return {"periods_per_octave": x, "notes_per_period_class": npp,
            "chain_positions": b, "chain_span": span,
            "contained_at_anchor0": contained0, "contained": contained,
            "anchor_interval": [anchor_lo, anchor_hi] if contained else None,
            "anchor_used": anchor}


def window_cents(per: float, g: float, n: int, anchor: int, x: int) -> list:
    npp = n // x
    return sorted((bi * g) % per + k * per
                  for bi in range(anchor, anchor + npp) for k in range(x))


def host_step_classes(notes: list, n: int) -> int:
    gaps = [notes[i + 1] - notes[i] for i in range(n - 1)]
    gaps.append(1200.0 - notes[-1] + notes[0])
    classes, cluster_min = 0, None
    for gap in sorted(gaps):
        if cluster_min is None or gap - cluster_min > FLOAT_EPS:
            classes += 1
            cluster_min = gap
    return classes


def degrees_match_host_ranks(notes: list, mapping: Mapping, g: float,
                             degrees: list[int], n: int) -> bool:
    ranks = []
    for t in TONES:
        pc = tempered_pitch(mapping, g, t["monzo"]) % 1200.0
        ranks.append(min(range(n), key=lambda i: min(
            abs(notes[i] - pc), 1200.0 - abs(notes[i] - pc))))
    return len({(r - d) % n for r, d in zip(ranks, degrees)}) == 1


def melodic_receipt(notes: list) -> dict:
    ms = score_melodic(notes)
    return {"gap_classes": ms.gap_entropy.gap_class_count,
            "gap_entropy_bits": round(ms.gap_entropy.entropy_bits, 6),
            "gap_sizes": [[round(lo, 4), round(hi, 4), cnt]
                          for lo, hi, cnt in ms.gap_entropy.gap_classes],
            "is_cs": ms.constant_structure.is_cs,
            "cs_violations": ms.constant_structure.violations,
            "propriety": ms.propriety.classification,
            "propriety_violations": ms.propriety.violating_span_pairs,
            "n_notes": len(ms.scale)}


# ------------------------------------------------------------ measuring --

def identity_recovery(tbp: dict, triads, full: tuple[int, int]):
    return next((e for e in EPS_SWEEP
                 if identity_survival(tbp, float(e), triads) == full), None)


def measure_tuning(mapping: Mapping, g: float, objective_err: float, n: int,
                   mono: dict, host: dict, full: bool,
                   lens: bool = True) -> dict:
    """One tuning's receipt. `full` adds the count lens, per-subset
    identity, melodic window and host consistency (full rows only);
    `lens=False` (over-budget compact rows) skips the identity lens, which
    is the only expensive part of a compact row."""
    tbp = tempered_by_product(mapping, g)
    errors = [tbp[t["product"]] - t["cents"] for t in TONES]
    max_err = max(abs(e) for e in errors)
    if lens or full:
        id_p, id_s = identity_survival(tbp, EPS_TEMPERED, EIKOSANY_TRIADS)
        recovery = identity_recovery(tbp, EIKOSANY_TRIADS, FULL)
    else:
        id_p = id_s = recovery = None
    rec = {
        "generator_cents_raw": g,
        "generator_cents": g % (1200.0 / mapping[0][0]),
        "objective_error_cents": round(objective_err, 6),
        "max_error_cents": round(max_err, 6),
        "mean_error_cents": round(sum(abs(e) for e in errors) / len(errors), 6),
        "interval_maxerr": round(max(abs(a - b) for a, b in
                                     combinations(errors, 2)), 6),
        "identity_P": id_p, "identity_S": id_s,
        "identity_full_recovery_eps": recovery,
        "in_budget": max_err < EPS_BRIDGE,
        "h_c1_pass": (not mono["collisions"] and host["contained"]
                      and max_err < EPS_BRIDGE and (id_p, id_s) == FULL),
    }
    if not full:
        return rec
    rec["tone_errors"] = [round(e, 6) for e in errors]
    img = triad.score_tempered([tbp[p] for p in PRODUCTS],
                               epsilon_cents=EPS_TEMPERED)
    rec["image_PSG_count_lens"] = [img.proportional, img.subcontrary,
                                   img.geometric]
    hex_rows, full_at = [], {str(e): 0 for e in HEXANY_REPORT_EPS}
    for h in HEXANIES:
        base = (h["base"].proportional, h["base"].subcontrary)
        p, s = identity_survival(tbp, EPS_TEMPERED, h["triads"])
        hex_rows.append([p, s, base[0], base[1], (p, s) == base])
        for e in HEXANY_REPORT_EPS:
            if identity_survival(tbp, float(e), h["triads"]) == base:
                full_at[str(e)] += 1
    rec["hexanies"] = {"full_at_eps": full_at, "rows": hex_rows}
    rec["dekanies"] = []
    for d in DEKANIES:
        base = (d["base"].proportional, d["base"].subcontrary)
        p, s = identity_survival(tbp, EPS_TEMPERED, d["triads"])
        rec["dekanies"].append([p, s, base[0], base[1], (p, s) == base])
    if host["contained"]:
        per = 1200.0 / mapping[0][0]
        notes = window_cents(per, g, n, host["anchor_used"], mapping[0][0])
        rec["host_step_classes"] = host_step_classes(notes, n)
        rec["degrees_match_host_ranks"] = degrees_match_host_ranks(
            notes, mapping, g, mono["degrees"], n)
        rec["melodic"] = melodic_receipt(notes)
    else:
        rec["host_step_classes"] = None
        rec["degrees_match_host_ranks"] = None
        rec["melodic"] = None
    return rec


def measure_row(mapping: Mapping, v: tuple[int, ...], n: int, mono: dict,
                witnesses: list, name, commas: list[Monzo]) -> dict:
    combo = val_combo(v, mapping)
    assert combo is not None, "val must factor through the temperament"
    host = host_receipt(mapping, n, mono["degrees"])
    merges = []
    for col in mono["collisions"]:
        cm = tuple(col["comma_monzo"])
        merges.append({"tones": col["tones"], "degree": col["degree"],
                       "comma": col["comma"],
                       "pitch_merged": vdot(mapping[1], cm) == 0
                       and vdot(mapping[0], cm) % mapping[0][0] == 0})
    g_prime, e_prime = prime_minimax(mapping)
    prime_max = max(abs(e) for e in tone_errors(mapping, g_prime))
    if host["contained"]:
        g_tone, e_tone = tone_set_minimax(mapping)
        in_budget = e_tone < EPS_BRIDGE
    else:
        g_tone = e_tone = None
        in_budget = prime_max < EPS_BRIDGE
    full = bool(name) or (host["contained"] and in_budget)
    row = {
        "schema": "full" if full else "compact",
        "N": n, "val": list(v), "patent_val": list(patent_val(n)),
        "mapping": [list(r) for r in mapping],
        "periods_per_octave": mapping[0][0],
        "alpha": combo[0], "generator_degree_beta": combo[1],
        "name": name,
        "w_witness_count": len(witnesses),
        "w_witnesses": [list(w) for w in witnesses[:W_WITNESSES_KEPT]],
        "degrees": mono["degrees"],
        "collisions": merges, "collision_count": len(merges),
        "pitch_merge_count": sum(m["pitch_merged"] for m in merges),
        "injective": not merges,
        "contained": host["contained"], "chain_span": host["chain_span"],
        "chain_positions": host["chain_positions"],
        "notes_per_period_class": host["notes_per_period_class"],
        "anchor_interval": host["anchor_interval"],
        "anchor_used": host["anchor_used"],
        "in_budget": in_budget,
        "tunings": {},
    }
    if full:
        row["kernel_commas"] = kernel_commas(mapping, commas)
    tun = row["tunings"]
    tun["prime"] = measure_tuning(mapping, g_prime, e_prime, n, mono, host,
                                  full, lens=in_budget)
    if host["contained"]:
        tun["tone_set"] = measure_tuning(mapping, g_tone, e_tone, n, mono,
                                         host, full, lens=in_budget)
        if in_budget:
            g_int, e_int = interval_minimax(mapping)
            tun["interval"] = measure_tuning(mapping, g_int, e_int, n, mono,
                                             host, full)
            sg = survival_grid(mapping, g_prime, (g_prime, g_tone, g_int))
            tun["survival"] = measure_tuning(mapping, sg["g"], 0.0, n, mono,
                                             host, full)
            tun["survival"]["objective_error_cents"] = None
            tun["survival"]["grid_points"] = sg["grid_points"]
            tun["survival"]["grid_argmax_count"] = sg["argmax_count"]
            assert (tun["survival"]["identity_P"],
                    tun["survival"]["identity_S"]) == (sg["identity_P"],
                                                       sg["identity_S"])
        else:
            tun["interval"] = None
            tun["survival"] = None
    else:
        tun["tone_set"] = tun["interval"] = tun["survival"] = None
    if not full:
        # compact: drop the bulky per-tone fields the summary never needs
        for t in list(tun):
            if tun[t] is not None:
                tun[t] = {k: tun[t][k] for k in (
                    "generator_cents", "max_error_cents", "identity_P",
                    "identity_S", "identity_full_recovery_eps", "in_budget")}
    return row


# -------------------------------------------------------------- fronts ---

def front_entry(row: dict, tuning: str) -> dict:
    t = row["tunings"][tuning]
    hexes = t.get("hexanies")
    mel = t.get("melodic")
    return {"name": row["name"], "N": row["N"], "val": row["val"],
            "mapping": row["mapping"],
            "kernel_commas": row.get("kernel_commas"),
            "tuning": tuning,
            "generator_cents": t["generator_cents"],
            "max_error_cents": t["max_error_cents"],
            "interval_maxerr": t["interval_maxerr"],
            "collision_count": row["collision_count"],
            "identity_P": t["identity_P"], "identity_S": t["identity_S"],
            "identity_full_recovery_eps": t["identity_full_recovery_eps"],
            "hexanies_full_at_eps": hexes["full_at_eps"] if hexes else None,
            "host_step_classes": t.get("host_step_classes"),
            "gap_classes": mel["gap_classes"] if mel else None,
            "propriety": mel["propriety"] if mel else None,
            "is_cs": mel["is_cs"] if mel else None,
            "anchor_interval": row["anchor_interval"],
            "chain_span": row["chain_span"],
            "h_c1_pass": t["h_c1_pass"]}


def dominates(a: dict, b: dict) -> bool:
    ge = (a["identity_P"] >= b["identity_P"]
          and a["collision_count"] <= b["collision_count"]
          and a["max_error_cents"] <= b["max_error_cents"])
    strict = (a["identity_P"] > b["identity_P"]
              or a["collision_count"] < b["collision_count"]
              or a["max_error_cents"] < b["max_error_cents"])
    return ge and strict


def pareto(rows: list, tuning: str, max_error=EPS_BRIDGE) -> list:
    cands = [front_entry(r, tuning) for r in rows
             if r["contained"] and r["tunings"].get(tuning)
             and r["schema"] == "full"
             and (max_error is None
                  or r["tunings"][tuning]["max_error_cents"] < max_error)]
    return sorted((a for a in cands if not any(dominates(b, a) for b in cands)),
                  key=lambda r: (r["max_error_cents"], r["N"], tuple(r["val"])))


# -------------------------------------------------------------- driver ---

def iter_rows(progress=None):
    """Yield every (mapping, val) row in deterministic order, then the
    enumeration meta dict last (as a ("meta", dict) sentinel)."""
    names = resolve_names()
    commas = enumerate_commas()
    w_vals = [w for m in W_RANGE for w in vals_for(m)]
    rows = 0
    mappings: set = set()
    kept_by_n: dict = {}
    offset_patterns: Counter = Counter()
    n_vals = n_mono = n_pairs = 0
    for n in N_RANGE:
        kept_by_n[n] = 0
        for v in vals_for(n):
            n_vals += 1
            mono = monotonicity(v)
            if not mono["monotone"]:
                continue
            n_mono += 1
            kept_by_n[n] += 1
            pat = patent_val(n)
            offset_patterns[tuple(v[i] - pat[i] for i in range(1, NP))] += 1
            seen: dict = {}
            for w in w_vals:
                mapping = join_mapping(v, w)
                if mapping is None:
                    continue
                n_pairs += 1
                seen.setdefault(mapping, []).append(w)
            for mapping in sorted(seen):
                rows += 1
                mappings.add(mapping)
                yield measure_row(mapping, v, n, mono, seen[mapping],
                                  names.get(mapping), commas)
            if progress:
                progress(n, v, rows)
    meta = {"vals_total": n_vals, "vals_monotone": n_mono,
            "vals_rejected": n_vals - n_mono,
            "second_vals": len(w_vals), "independent_pairs": n_pairs,
            "distinct_rows": rows,
            "distinct_mappings": len(mappings),
            "kept_vals_by_N": {str(k): v for k, v in kept_by_n.items()},
            "kept_offset_patterns": [[list(k), c] for k, c in
                                     offset_patterns.most_common()],
            "commas_in_box": len(commas)}
    yield ("meta", meta)


def run(progress=None) -> tuple[list, dict]:
    """Collect every row in memory (tests / small ranges)."""
    rows = []
    for item in iter_rows(progress):
        if isinstance(item, tuple):
            return rows, item[1]
        rows.append(item)
    raise AssertionError("no meta")


def _brief(row: dict, tuning: str) -> dict:
    t = row["tunings"][tuning]
    return {"name": row["name"], "N": row["N"], "val": row["val"],
            "mapping": row["mapping"], "chain_span": row["chain_span"],
            "contained": row["contained"],
            "collision_count": row["collision_count"],
            "max_error_cents": t["max_error_cents"],
            "identity_P": t["identity_P"],
            "identity_full_recovery_eps": t["identity_full_recovery_eps"]}


def summarize(rows: list, meta: dict) -> dict:
    contained = [r for r in rows if r["contained"]]
    full_rows = [r for r in rows if r["schema"] == "full"]
    inb = [r for r in contained if r["in_budget"]]
    fronts = {t: pareto(rows, t) for t in TUNINGS}
    uncapped = {t: pareto(rows, t, max_error=None) for t in TUNINGS}

    def best(rs, t, key):
        vals = [r["tunings"][t] for r in rs if r["tunings"].get(t)]
        vals = [x for x in vals if x[key] is not None]
        return None if not vals else (max if key == "identity_P" else min)(
            x[key] for x in vals)

    # H-C1
    passers = [(_brief(r, t) | {"tuning": t}) for r in contained for t in TUNINGS
               if r["tunings"].get(t) and r["tunings"][t].get("h_c1_pass")]
    h_c1 = {
        "passers": passers,
        "verdict": "REFUTED (bridge exists)" if passers
        else "KEPT (no 2c eikosany bridge at N <= 46)",
        "best_contained_identity_P_at_eps2": {t: best(inb, t, "identity_P")
                                              for t in TUNINGS},
        "min_contained_full_recovery_eps": {
            t: best(inb, t, "identity_full_recovery_eps") for t in TUNINGS},
        "best_rows_by_identity": {
            t: [_brief(r, t) for r in sorted(
                (r for r in inb if r["tunings"].get(t)),
                key=lambda r: (-r["tunings"][t]["identity_P"],
                               r["tunings"][t]["max_error_cents"]))[:5]]
            for t in TUNINGS},
        "best_rows_by_recovery": {
            t: [_brief(r, t) for r in sorted(
                (r for r in inb if r["tunings"].get(t)
                 and r["tunings"][t]["identity_full_recovery_eps"]),
                key=lambda r: (r["tunings"][t]["identity_full_recovery_eps"],
                               -r["tunings"][t]["identity_P"],
                               r["tunings"][t]["max_error_cents"]))[:5]]
            for t in TUNINGS},
    }
    # H-C2: uncontained accuracy
    unc = [r for r in rows if not r["contained"]
           and r["tunings"]["prime"].get("identity_full_recovery_eps") is not None]
    unc_best = sorted(unc, key=lambda r: (
        r["tunings"]["prime"]["identity_full_recovery_eps"],
        r["tunings"]["prime"]["max_error_cents"]))
    h_c2 = {
        "uncontained_rows_with_recovery_le_2": [
            _brief(r, "prime") for r in unc_best
            if r["tunings"]["prime"]["identity_full_recovery_eps"] <= 2],
        "min_uncontained_recovery_eps": (
            unc_best[0]["tunings"]["prime"]["identity_full_recovery_eps"]
            if unc_best else None),
        "min_contained_recovery_eps_prime": best(inb, "prime",
                                                 "identity_full_recovery_eps"),
        "uncontained_best_rows": [_brief(r, "prime") for r in unc_best[:10]],
    }
    # H-C3: tuning objectives
    named_table = []
    for r in sorted(full_rows, key=lambda r: (r["name"] or "~", r["N"],
                                              tuple(r["val"]))):
        if not r["name"]:
            continue
        named_table.append({
            "name": r["name"], "N": r["N"], "val": r["val"],
            "contained": r["contained"], "chain_span": r["chain_span"],
            **{f"{t}_identity_P": (r["tunings"][t]["identity_P"]
                                   if r["tunings"].get(t) else None)
               for t in TUNINGS},
            **{f"{t}_recovery": (r["tunings"][t]["identity_full_recovery_eps"]
                                 if r["tunings"].get(t) else None)
               for t in TUNINGS},
            **{f"{t}_max_error": (r["tunings"][t]["max_error_cents"]
                                  if r["tunings"].get(t) else None)
               for t in TUNINGS}})
    eligible = [r for r in inb if r["tunings"].get("survival")
                and max(r["tunings"][t]["identity_P"] for t in ANALYTIC) >= 10]
    strict = [r for r in eligible
              if r["tunings"]["survival"]["identity_P"]
              > max(r["tunings"][t]["identity_P"] for t in ANALYTIC)]
    tone_lowers = [r for r in inb if r["tunings"]["tone_set"]["identity_P"]
                   < r["tunings"]["prime"]["identity_P"]]
    tone_raises = [r for r in inb if r["tunings"]["tone_set"]["identity_P"]
                   > r["tunings"]["prime"]["identity_P"]]
    front_keys = {t: [(e["N"], tuple(e["val"]), tuple(map(tuple, e["mapping"])))
                      for e in fronts[t]] for t in TUNINGS}
    h_c3 = {
        "named_table": named_table,
        "tone_set_lowers_identity_P_rows": len(tone_lowers),
        "tone_set_raises_identity_P_rows": len(tone_raises),
        "tone_set_lowers_named": sorted({r["name"] for r in tone_lowers
                                         if r["name"]}),
        "analytic_fronts_differ": {
            f"{a}_vs_{b}": front_keys[a] != front_keys[b]
            for a, b in combinations(ANALYTIC, 2)},
        "survival_strictly_exceeds_best_analytic": {
            "eligible_rows": len(eligible), "rows": len(strict),
            "fraction": (len(strict) / len(eligible)) if eligible else None,
            "examples": [_brief(r, "survival") | {
                "analytic_P": [r["tunings"][t]["identity_P"] for t in ANALYTIC]}
                for r in strict[:10]]},
        "survival_ge_each_analytic_everywhere": all(
            r["tunings"]["survival"]["identity_P"]
            + r["tunings"]["survival"]["identity_S"]
            >= r["tunings"][t]["identity_P"] + r["tunings"][t]["identity_S"]
            for r in inb if r["tunings"].get("survival") for t in ANALYTIC),
    }
    # H-C4: Wilson's template
    huy = [r for r in rows if r["val"] == [31, 49, 72, 87, 107]
           and r["name"] == "huygens"]
    h_c4 = {"rows": [{
        **_brief(r, "prime"), "injective": r["injective"],
        "anchor_interval": r["anchor_interval"],
        **{f"{t}_identity_P": r["tunings"][t]["identity_P"]
           for t in TUNINGS if r["tunings"].get(t)},
        **{f"{t}_recovery": r["tunings"][t]["identity_full_recovery_eps"]
           for t in TUNINGS if r["tunings"].get(t)},
        "melodic": r["tunings"]["prime"].get("melodic")} for r in huy],
        "dominated_on_survival_front": all(
            not any(e["val"] == [31, 49, 72, 87, 107] for e in fronts[t])
            for t in TUNINGS)}
    # H-C5: modulus 22
    n22 = [r for r in contained if r["N"] == 22]
    n22_inb = [r for r in n22 if r["in_budget"]]
    h_c5 = {"contained_rows_at_22": len(n22), "in_budget": len(n22_inb),
            "max_identity_P_in_budget": {
                t: best(n22_inb, t, "identity_P") for t in TUNINGS},
            "min_recovery_in_budget": {
                t: best(n22_inb, t, "identity_full_recovery_eps")
                for t in TUNINGS},
            "rows": [_brief(r, "survival" if r["tunings"].get("survival")
                            else "prime") for r in n22_inb[:20]]}
    # H-C6: hexany navigation
    def hex_view(r, t):
        tt = r["tunings"][t]
        return _brief(r, t) | {"hexanies_full_at_eps": tt["hexanies"]["full_at_eps"],
                               "dekanies_full_at_2": sum(
                                   d[4] for d in tt["dekanies"])}
    best_rec = None
    for r in inb:
        for t in TUNINGS:
            tt = r["tunings"].get(t)
            if tt and tt["identity_full_recovery_eps"] is not None:
                key = (tt["identity_full_recovery_eps"], -tt["identity_P"],
                       tt["max_error_cents"], r["N"], tuple(r["val"]), t)
                if best_rec is None or key < best_rec[0]:
                    best_rec = (key, r, t)
    best_p = None
    for r in inb:
        tt = r["tunings"].get("survival")
        if tt:
            key = (-tt["identity_P"], tt["max_error_cents"], r["N"],
                   tuple(r["val"]))
            if best_p is None or key < best_p[0]:
                best_p = (key, r)
    h_c6 = {
        "best_recovery_row": hex_view(best_rec[1], best_rec[2]) if best_rec
        else None,
        "best_survival_row": hex_view(best_p[1], "survival") if best_p else None,
        "hexany_full_implied_by_eikosany_full": True,
    }
    # P-COMMA-6
    small = ("385/384", "441/440")
    p_comma = {t: {"front_kernels": [(e["name"], e["N"], e["kernel_commas"])
                                     for e in fronts[t]],
                   "every_front_row_has_385_or_441": all(
                       any(c in (e["kernel_commas"] or []) for c in small)
                       for e in fronts[t]),
                   "front_rows_with_225_224": sum(
                       "225/224" in (e["kernel_commas"] or [])
                       for e in fronts[t])}
               for t in TUNINGS}
    bridge000 = json.loads(BRIDGE000.read_text())["pareto_standard"]
    return {
        "experiment": "BRIDGE-002", "date": str(date.today()),
        "scorer_version": triad.SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "epsilon_tempered": EPS_TEMPERED, "epsilon_bridge": EPS_BRIDGE,
        "payload": {"seeds": list(SEEDS), "tones": len(TONES),
                    "base_PSG": [EIKOSANY_BASE.proportional,
                                 EIKOSANY_BASE.subcontrary,
                                 EIKOSANY_BASE.geometric],
                    "identity_triads": len(EIKOSANY_TRIADS),
                    "hexanies": len(HEXANIES), "dekanies": len(DEKANIES)},
        "enumeration": meta | {
            "contained_rows": len(contained),
            "contained_mappings": len({tuple(map(tuple, r["mapping"]))
                                       for r in contained}),
            "contained_in_budget_rows": len(inb),
            "full_rows": len(full_rows),
            "named_rows": sum(1 for r in rows if r["name"]),
            "uncontained_in_budget_rows": sum(
                1 for r in rows if not r["contained"] and r["in_budget"]),
            "uncontained_over_budget_rows": meta.get(
                "uncontained_over_budget_counted_only",
                sum(1 for r in rows if not r["contained"] and not r["in_budget"])),
            "contained_over_budget_rows": len(contained) - len(inb)},
        "fronts_capped_15c": fronts,
        "fronts_uncapped_identity": uncapped,
        "h_c1": h_c1, "h_c2": h_c2, "h_c3": h_c3, "h_c4": h_c4,
        "h_c5": h_c5, "h_c6": h_c6, "p_comma_6": p_comma,
        "bridge000_standard": bridge000,
    }


def receipt_row(row: dict) -> dict:
    if row["schema"] == "full":
        return row
    return {k: row[k] for k in (
        "schema", "N", "val", "mapping", "name", "periods_per_octave",
        "w_witness_count", "collision_count", "injective", "contained",
        "chain_span", "notes_per_period_class", "in_budget", "tunings")}


def load_receipts() -> tuple[list, dict]:
    """Rows kept in memory by main() (full + compact contained/in-budget),
    reloaded from the two receipt files, plus meta from the summary."""
    rows = []
    with RESULTS.open() as fh:
        rows.extend(json.loads(line) for line in fh)
    with gzip.open(SIDECAR, "rt", encoding="utf-8") as fh:
        rows.extend(json.loads(line) for line in fh)
    meta = json.loads(SUMMARY.read_text())["enumeration"]
    meta = {k: v for k, v in meta.items() if k not in (
        "contained_rows", "contained_mappings", "contained_in_budget_rows",
        "full_rows", "named_rows", "uncontained_in_budget_rows",
        "uncontained_over_budget_rows", "contained_over_budget_rows")}
    return rows, meta


def resummarize() -> None:
    rows, meta = load_receipts()
    old = json.loads(SUMMARY.read_text())
    summary = summarize(rows, meta)
    summary["receipts"] = old.get("receipts") | {"resummarized": True} \
        if old.get("receipts") else {"resummarized": True}
    SUMMARY.write_text(json.dumps(summary, indent=1))
    print_summary(summary)


# ------------------------------------------------------------ ear check --

def scl_text(name: str, description: list[str], degrees: list[float]) -> str:
    """Scala text in cents (eareps.scl_text's layout): degrees above the
    implicit 1/1, octave last."""
    lines = [f"! {name}.scl", "!"] + [f"! {d}" for d in description] + [
        "!", name, f" {len(degrees)}", "!"]
    lines += [f" {c:.5f}" for c in degrees]
    return "\n".join(lines) + "\n"


def export_scl() -> list[Path]:
    """Standing ear-check exports (GATES protocol: every .scl offered is
    implicitly PENDING): for each row on a capped front, under that
    tuning, (a) the anchored N-note host window and (b) the 20-tone
    eikosany image alone, both in cents with the degree map in the header.
    Reads the receipts; writes nothing else."""
    summary = json.loads(SUMMARY.read_text())
    rows = {}
    with RESULTS.open() as fh:
        for line in fh:
            r = json.loads(line)
            rows[(tuple(map(tuple, r["mapping"])), r["N"], tuple(r["val"]))] = r
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    seen = set()
    for tuning in TUNINGS:
        for e in summary["fronts_capped_15c"][tuning]:
            key = (tuple(map(tuple, e["mapping"])), e["N"], tuple(e["val"]))
            if (key, tuning) in seen:
                continue
            seen.add((key, tuning))
            r = rows[key]
            t = r["tunings"][tuning]
            mapping = key[0]
            g = t["generator_cents_raw"]
            x = mapping[0][0]
            per = 1200.0 / x
            n = r["N"]
            notes = window_cents(per, g, n, r["anchor_used"], x)
            tbp = tempered_by_product(mapping, g)
            label = (r["name"] or "unnamed") + f"-{n}"
            stem = f"b002_{label}_{tuning}"
            root = notes[0]
            degrees = [c - root for c in notes[1:]] + [1200.0]
            scl_deg = {}
            for tt in TONES:
                pc = (tbp[tt["product"]] - root) % 1200.0
                k = min(range(n), key=lambda i: min(
                    abs(([0.0] + degrees)[i] - pc),
                    1200.0 - abs(([0.0] + degrees)[i] - pc)))
                scl_deg[tt["product"]] = k
            deg_map = ", ".join(
                f"{frac_str(tt['ratio'])}->{scl_deg[tt['product']]}"
                for tt in TONES)
            head = [
                f"BRIDGE-002 host window: {label} under the {tuning} tuning",
                f"mapping {list(map(list, mapping))} val {r['val']} "
                f"generator {t['generator_cents']:.4f}c period {per:.4f}c "
                f"anchor {r['anchor_used']} of {r['anchor_interval']}",
                f"eikosany identity survival at 2c: P={t['identity_P']} "
                f"S={t['identity_S']} of 57/57; full recovery at "
                f"{t['identity_full_recovery_eps']}c; max tone error "
                f"{t['max_error_cents']}c; hexanies fully surviving at 2c: "
                f"{t['hexanies']['full_at_eps']['2']}/30",
                f"host: {t['melodic']['gap_classes']} gap classes, "
                f"{t['melodic']['propriety']}, CS={t['melodic']['is_cs']}",
                "1/1 = the window's lowest note (chain position "
                f"{r['anchor_used']}); eikosany tones -> .scl degree: " + deg_map,
                "kernel commas: " + ", ".join(r["kernel_commas"][:8]),
            ]
            path = SCL_DIR / f"{stem}_host{n}.scl"
            path.write_text(scl_text(path.stem, head, degrees))
            written.append(path)
            img = sorted(tbp[p] % 1200.0 for p in PRODUCTS)
            root = img[0]
            img_deg = [c - root for c in img[1:]] + [1200.0]
            head2 = [f"BRIDGE-002 tempered eikosany image alone: {label} under "
                     f"the {tuning} tuning (1/1 = the image's lowest tone, "
                     f"{frac_str(TONES[0]['ratio'])} tempered)",
                     head[1], head[2]]
            path2 = SCL_DIR / f"{stem}_eikosany20.scl"
            path2.write_text(scl_text(path2.stem, head2, img_deg))
            written.append(path2)
    return written


def main() -> None:
    import time
    if "--resummarize" in sys.argv:
        resummarize()
        return
    if "--export-scl" in sys.argv:
        for p in export_scl():
            print(p.relative_to(HERE))
        return
    t0 = time.time()

    def progress(n, v, nrows):
        if v == vals_for(n)[-1] or nrows % 50000 < 100:
            print(f"  N={n} rows={nrows} t={time.time() - t0:.0f}s",
                  file=sys.stderr, flush=True)

    RESULTS.parent.mkdir(exist_ok=True)
    n_full = n_compact = n_counted = 0
    kept: list = []          # full rows + compact rows that are contained
    counted_by_n: Counter = Counter()
    meta = None
    with RESULTS.open("w") as fh, gzip.GzipFile(
            SIDECAR, "wb", mtime=0) as gz, io.TextIOWrapper(gz, "utf-8") as side:
        for item in iter_rows(progress):
            if isinstance(item, tuple):
                meta = item[1]
                break
            row = item
            rec = receipt_row(row)
            line = json.dumps(rec, separators=(",", ":")) + "\n"
            if rec["schema"] == "full":
                fh.write(line)
                n_full += 1
                kept.append(rec)
            elif row["in_budget"] or row["contained"]:
                side.write(line)
                n_compact += 1
                kept.append(rec)
            else:
                n_counted += 1
                counted_by_n[row["N"]] += 1
    meta["counted_only_by_N"] = {str(k): v for k, v in sorted(counted_by_n.items())}
    meta["uncontained_over_budget_counted_only"] = n_counted
    # meta first, so `--resummarize` can rebuild the summary from the
    # receipts if the summary layer ever fails after a complete sweep
    SUMMARY.write_text(json.dumps({"experiment": "BRIDGE-002",
                                   "status": "sweep complete, summary pending",
                                   "enumeration": meta}, indent=1))
    summary = summarize(kept, meta)
    summary["receipts"] = {
        "bridge002_jsonl_rows_full": n_full,
        "bridge002_sidecar_rows_compact": n_compact,
        "rows_counted_only_over_budget": n_counted,
        "sha256_bridge002_jsonl": hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
        "sha256_sidecar_gz": hashlib.sha256(SIDECAR.read_bytes()).hexdigest(),
        "runtime_seconds": round(time.time() - t0, 1)}
    SUMMARY.write_text(json.dumps(summary, indent=1))
    print_summary(summary)


def print_summary(summary: dict) -> None:
    e = summary["enumeration"]
    rc = summary.get("receipts", {})
    print(f"vals {e['vals_total']} monotone {e['vals_monotone']} | rows "
          f"{e['distinct_rows']} mappings {e['distinct_mappings']} | contained "
          f"{e['contained_rows']} (in-budget {e['contained_in_budget_rows']}) | "
          f"full {rc.get('bridge002_jsonl_rows_full')} sidecar "
          f"{rc.get('bridge002_sidecar_rows_compact')} counted "
          f"{rc.get('rows_counted_only_over_budget')} | "
          f"{rc.get('runtime_seconds')}s")
    print("H-C1:", summary["h_c1"]["verdict"],
          summary["h_c1"]["best_contained_identity_P_at_eps2"],
          summary["h_c1"]["min_contained_full_recovery_eps"])
    for t in TUNINGS:
        print(f"-- capped front {t} --")
        for x in summary["fronts_capped_15c"][t]:
            print(f"  {x['name'] or x['mapping']} N={x['N']} val={x['val']} "
                  f"g={x['generator_cents']:.4f} err={x['max_error_cents']} "
                  f"idP={x['identity_P']} coll={x['collision_count']} "
                  f"rec={x['identity_full_recovery_eps']} "
                  f"gaps={x['gap_classes']} {x['propriety']} "
                  f"hex@2={x['hexanies_full_at_eps']}")
    print("H-C2:", {k: v for k, v in summary["h_c2"].items()
                   if k != "uncontained_best_rows"})
    print("H-C3:", {k: v for k, v in summary["h_c3"].items()
                   if k != "named_table"})
    for r in summary["h_c3"]["named_table"]:
        print("  ", r)
    print("H-C4:", summary["h_c4"])
    print("H-C5:", {k: v for k, v in summary["h_c5"].items() if k != "rows"})
    print("H-C6:", summary["h_c6"])
    print("P-COMMA-6:", summary["p_comma_6"])


if __name__ == "__main__":
    main()
