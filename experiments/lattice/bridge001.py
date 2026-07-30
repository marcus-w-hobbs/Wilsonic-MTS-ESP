"""BRIDGE-001 — EG4 CPS structure inside an MOS host (SPEC §BRIDGE-001).

Pre-registered in LOG.md 2026-07-29 BEFORE implementation. Scope: the
{1,3,5,7} Euler Genus (Marcus's 2026-07-22 EG4-first decision) carried by
rank-2 temperament hosts at cardinality N in 7..22, judged against the
BRIDGE-000 D'Alessandro calibration standard (results/bridge000.json).

Binding design decisions (Marcus, SPEC §BRIDGE-001):
1. NO nearest-degree rounding: degree assignment is BY THE VAL. The only
   structural filter is monotonicity (val order == pitch order on the EG4
   tones), applied FIRST; violations are rejected and logged.
2. Anchoring is a free design parameter (MOS-LAT-001 corollary): if the
   host MOS fails to contain the image at anchor 0, sweep anchors before
   rejecting.

Rank accounting (SPEC soft spot, resolved in the pre-registration): a
linear MOS host is rank 2 in the full 2.3.5.7 group, so the kernel has
rank 2 — the SPEC's "exactly ONE comma" undercounts by the val's worth.
Candidates are pairs (comma c, val v) with v(c) = 0: c names the planar
temperament, v is the degree assignment, and the implicit second kernel
generator k2 is chosen by the pre-registered completion rule: the
primitive kernel-box element independent of c minimizing the pure-octave
minimax {3,5,7} error of sat<c, k2> (ties: Tenney height, then lex).

Tesseract counting (pre-registered): the EG4 tesseract has 16 formal
vertices (subsets of {1,3,5,7}) but seed 1 pairs S with S+{1} at the same
product, so there are exactly 8 distinct pitch classes — the divisors of
105, octave-reduced (the BRIDGE-000 convention: EG6's 64 subsets = 32
tones). Collisions and injectivity are evaluated on the 8 distinct tones.

Run from experiments/lattice/:  python3.12 bridge001.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from fractions import Fraction
from itertools import combinations, product
from math import gcd, log2
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import scorer as triad  # noqa: E402  (frozen v1.1.0, read-only)
from scorer import canonical_rational_scale, reduce_rational  # noqa: E402
from melodic import MELODIC_VERSION  # noqa: E402  (provenance only)

RESULTS = HERE / "results" / "bridge001.jsonl"
SUMMARY = HERE / "results" / "bridge001_summary.json"
BRIDGE000 = HERE / "results" / "bridge000.json"

PRIMES = (2, 3, 5, 7)
LOG2P = tuple(log2(p) for p in PRIMES)
N_RANGE = range(7, 23)
ODD_BOX = (8, 5, 4)               # |e3|, |e5|, |e7| bounds
COMMA_MAX_CENTS = 60.0
TENNEY_MAX_LOG2 = 40.0
EPSILON_TEMPERED = 2.0            # frozen scorer score_tempered epsilon
EPS_BRIDGE = range(1, 16)         # faithful/merge regime sweep, cents
FLOAT_EPS = 1e-6

NAMED_COMMAS = ("81/80", "64/63", "126/125", "225/224", "245/243",
                "1029/1024", "2401/2400", "3125/3087", "4375/4374")

Monzo = tuple[int, int, int, int]


# ---------------------------------------------------------------- monzos ---

def monzo_of(fr: Fraction) -> Monzo:
    m = [0, 0, 0, 0]
    n, d = fr.numerator, fr.denominator
    for i, p in enumerate(PRIMES):
        while n % p == 0:
            n //= p
            m[i] += 1
        while d % p == 0:
            d //= p
            m[i] -= 1
    assert n == 1 and d == 1, f"prime outside 7-limit in {fr}"
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
    """Octave-equivalent representative of a/b closest to (and >=) 1."""
    r = reduce_rational(a / b)
    return 2 / r if r * r > 2 else r


# --------------------------------------------------------- EG4 tesseract ---

SEEDS = (1, 3, 5, 7)


def eg4_vertices() -> list[dict]:
    """All 16 formal tesseract vertices (subsets of {1,3,5,7})."""
    out = []
    for r in range(5):
        for combo in combinations(SEEDS, r):
            prod = 1
            for f in combo:
                prod *= f
            out.append({"subset": list(combo), "product": prod})
    return out


def eg4_distinct() -> list[dict]:
    """The 8 distinct pitch classes (divisors of 105), sorted by cents."""
    tones = {}
    for v in eg4_vertices():
        p = v["product"]
        if p not in tones:
            red = reduce_rational(Fraction(p))
            tones[p] = {"product": p, "ratio": red,
                        "monzo": monzo_of(red), "cents": cents_of(monzo_of(red))}
    return sorted(tones.values(), key=lambda t: t["cents"])


VERTICES = eg4_vertices()
TONES = eg4_distinct()
HEXANY_PRODUCTS = (3, 5, 7, 15, 21, 35)           # CPS(4,2) products
TET1_PRODUCTS = (1, 3, 5, 7)                      # CPS(4,1)
TET3_PRODUCTS = (15, 21, 35, 105)                 # CPS(4,3)
SUBSETS = {"hexany": HEXANY_PRODUCTS, "tetrany_1": TET1_PRODUCTS,
           "tetrany_3": TET3_PRODUCTS}


# ------------------------------------------------------ comma enumeration ---

def enumerate_commas() -> list[Monzo]:
    """Primitive 7-limit commas, >1 representative, 0 < cents < 60,
    odd box |e3|<=8 |e5|<=5 |e7|<=4, Tenney height n*d <= 2^40."""
    out = set()
    b3, b5, b7 = ODD_BOX
    for e3 in range(-b3, b3 + 1):
        for e5 in range(-b5, b5 + 1):
            for e7 in range(-b7, b7 + 1):
                if e3 == e5 == e7 == 0:
                    continue
                odd_cents = 1200.0 * (e3 * LOG2P[1] + e5 * LOG2P[2]
                                      + e7 * LOG2P[3])
                e2 = -round(odd_cents / 1200.0)
                m: Monzo = (e2, e3, e5, e7)
                c = cents_of(m)
                if c < 0:
                    m, c = neg(m), -c
                if not (0.0 < c < COMMA_MAX_CENTS):
                    continue
                if gcd(gcd(abs(m[0]), abs(m[1])),
                       gcd(abs(m[2]), abs(m[3]))) != 1:
                    continue
                if tenney_log2(m) > TENNEY_MAX_LOG2:
                    continue
                out.add(m)
    commas = sorted(out, key=lambda m: (tenney_log2(m), m))
    named = {monzo_of(Fraction(s)) for s in NAMED_COMMAS}
    missing = named - set(commas)
    assert not missing, f"named commas outside enumeration: {missing}"
    return commas


# ------------------------------------------------------------------- vals ---

def patent_val(n: int) -> tuple[int, ...]:
    return (n,) + tuple(round(n * LOG2P[i]) for i in (1, 2, 3))


def vals_for(n: int) -> list[tuple[int, ...]]:
    pat = patent_val(n)
    return [(n, pat[1] + o3, pat[2] + o5, pat[3] + o7)
            for o3, o5, o7 in product((-1, 0, 1), repeat=3)]


def vdot(v: tuple[int, ...], m: Monzo) -> int:
    return sum(a * b for a, b in zip(v, m))


def monotonicity(v: tuple[int, ...]) -> dict:
    """Marcus filter: val order == pitch order on the 8 distinct EG4 tones.
    Unreduced degrees d(t) in [0, N]; weak increase required; ties (incl.
    d = N against the octave) are collisions, strict decreases reject."""
    n = v[0]
    degs = [vdot(v, t["monzo"]) for t in TONES]
    violations = []
    for i in range(len(TONES) - 1):
        if degs[i + 1] < degs[i]:
            violations.append({
                "pair": [frac_str(TONES[i]["ratio"]),
                         frac_str(TONES[i + 1]["ratio"])],
                "degrees": [degs[i], degs[i + 1]]})
    if degs[0] != 0 or degs[-1] > n or min(degs) < 0:
        violations.append({"pair": ["1/1", "2/1"],
                           "degrees": [degs[0], degs[-1]]})
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


# --------------------------------------------- integer linear algebra ------

def nullspace_saturated(rows: list[Monzo]) -> list[list[int]]:
    """Saturated basis of {x in Z^4 : r.x = 0 for r in rows} via column
    reduction with a tracked unimodular V (Smith-style, deterministic)."""
    a = [list(r) for r in rows]
    nr, nc = len(a), 4
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


def hnf_mapping(basis: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Row-Hermite normal form of the 2x4 mapping: period row first
    (M[0][0] = periods per octave > 0), generator row with M[1][0] = 0."""
    a, b = [list(r) for r in basis]
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
    j = next((k for k in range(1, 4) if b[k] != 0), None)
    if j is None:
        raise ValueError("degenerate generator row")
    if b[j] < 0:
        b = [-x for x in b]
    q = a[j] // b[j]
    a = [ai - q * bi for ai, bi in zip(a, b)]
    return (tuple(a), tuple(b))


def val_combo(v: tuple[int, ...], m: tuple[tuple[int, ...], ...]):
    """Integers (alpha, beta) with v = alpha*M0 + beta*M1, else None."""
    x = m[0][0]
    if x == 0 or v[0] % x != 0:
        return None
    alpha = v[0] // x
    j = next(k for k in range(1, 4) if m[1][k] != 0)
    num = v[j] - alpha * m[0][j]
    if num % m[1][j] != 0:
        return None
    beta = num // m[1][j]
    for k in range(4):
        if alpha * m[0][k] + beta * m[1][k] != v[k]:
            return None
    return alpha, beta


# ------------------------------------------------------------------ tuning ---

def minimax_generator(m: tuple[tuple[int, ...], ...]) -> tuple[float, float]:
    """Pure-octave minimax over {3,5,7}: period fixed at 1200/M[0][0];
    returns (G, max_error). Exact piecewise-linear minimax over pairwise
    crossings and per-line zeros; ties broken toward smaller G."""
    per = 1200.0 / m[0][0]
    lines = []
    for idx in (1, 2, 3):
        lines.append((m[0][idx] * per - 1200.0 * LOG2P[idx], float(m[1][idx])))
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
    best = min(cands, key=lambda g: (max(abs(a1 + b1 * g)
                                         for a1, b1 in lines), g))
    return best, max(abs(a1 + b1 * best) for a1, b1 in lines)


def choose_completion(c: Monzo, v: tuple[int, ...],
                      kernel_box: list[Monzo], cache: dict):
    """Pre-registered completion: k2 = argmin over primitive kernel-box
    monzos independent of c of the minimax error of sat<c,k2>;
    ties -> smaller Tenney height, then lex. Returns
    (k2, mapping, generator, err) or None."""
    best = None
    for k2 in kernel_box:
        minors = [c[i] * k2[j] - c[j] * k2[i]
                  for i, j in combinations(range(4), 2)]
        if not any(minors):
            continue  # dependent on c
        key = (c, k2)
        if key not in cache:
            basis = nullspace_saturated([c, k2])
            if len(basis) != 2:
                cache[key] = None
            else:
                mapping = hnf_mapping(basis)
                g, err = minimax_generator(mapping)
                cache[key] = (mapping, g, err)
        entry = cache[key]
        if entry is None:
            continue
        mapping, g, err = entry
        rank = (err, tenney_log2(k2), k2)
        if best is None or rank < best[0]:
            best = (rank, k2, mapping, g, err)
    if best is None:
        return None
    return best[1], best[2], best[3], best[4]


def kernel_box_for(v: tuple[int, ...]) -> list[Monzo]:
    """Primitive monzos in the odd box with v(m) = 0 (e2 from
    divisibility), deterministic order."""
    n = v[0]
    out = []
    b3, b5, b7 = ODD_BOX
    for e3 in range(-b3, b3 + 1):
        for e5 in range(-b5, b5 + 1):
            for e7 in range(-b7, b7 + 1):
                if e3 == e5 == e7 == 0:
                    continue
                num = v[1] * e3 + v[2] * e5 + v[3] * e7
                if num % n != 0:
                    continue
                m: Monzo = (-num // n, e3, e5, e7)
                if gcd(gcd(abs(m[0]), abs(m[1])),
                       gcd(abs(m[2]), abs(m[3]))) != 1:
                    continue
                out.append(m)
    return out


# ------------------------------------------------------------- host / MOS ---

def host_receipt(mapping, g: float, n: int, degrees: list[int]) -> dict:
    """Chain coordinates, murchana anchor sweep, host step classes and the
    degrees-match-host-ranks consistency bit."""
    x = mapping[0][0]
    per = 1200.0 / x
    npp = n // x
    b = [sum(mm * e for mm, e in zip(mapping[1], t["monzo"])) for t in TONES]
    span = max(b) - min(b) + 1
    contained0 = all(0 <= bi < npp for bi in b)
    anchor_lo = max(b) - npp + 1
    anchor_hi = min(b)
    contained = span <= npp
    anchor = 0 if contained0 else (
        min((a for a in range(anchor_lo, anchor_hi + 1)), key=abs)
        if contained else None)
    receipt = {"periods_per_octave": x, "notes_per_period_class": npp,
               "chain_positions": b, "chain_span": span,
               "contained_at_anchor0": contained0, "contained": contained,
               "anchor_interval": [anchor_lo, anchor_hi] if contained
               else None, "anchor_used": anchor}
    if not contained:
        receipt["host_step_classes"] = None
        receipt["degrees_match_host_ranks"] = None
        return receipt
    notes = sorted((bi * g) % per + k * per
                   for bi in range(anchor, anchor + npp) for k in range(x))
    gaps = [notes[i + 1] - notes[i] for i in range(n - 1)]
    gaps.append(1200.0 - notes[-1] + notes[0])
    classes, cluster_min = 0, None
    for gap in sorted(gaps):
        if cluster_min is None or gap - cluster_min > FLOAT_EPS:
            classes += 1
            cluster_min = gap
    tone_pitch = [sum(mm * e for mm, e in zip(mapping[0], t["monzo"])) * per
                  + bi * g for t, bi in zip(TONES, b)]
    ranks = []
    for p in tone_pitch:
        pc = p % 1200.0
        ranks.append(min(range(n), key=lambda i: min(
            abs(notes[i] - pc), 1200.0 - abs(notes[i] - pc))))
    offsets = {(r - d) % n for r, d in zip(ranks, degrees)}
    receipt["host_step_classes"] = classes
    receipt["degrees_match_host_ranks"] = len(offsets) == 1
    return receipt


# ------------------------------------------------------------- scoring -----

def subset_receipt(products, degrees_by_product, tempered_by_product,
                   n: int, base) -> dict:
    degs = [degrees_by_product[p] % n for p in products]
    img = triad.score_tempered([tempered_by_product[p] for p in products],
                               epsilon_cents=EPSILON_TEMPERED)
    return {"degrees": sorted(degs),
            "injective_addressing": len(set(degs)) == len(degs),
            "image_P": img.proportional, "image_S": img.subcontrary,
            "image_G": img.geometric,
            "base_P": base.proportional, "base_S": base.subcontrary,
            "triads_survive": (img.proportional >= base.proportional
                               and img.subcontrary >= base.subcontrary)}


def measure_candidate(c: Monzo, v: tuple[int, ...], n: int, mono: dict,
                      k2: Monzo, mapping, g: float, minimax_err: float,
                      bases) -> dict:
    per = 1200.0 / mapping[0][0]
    combo = val_combo(v, mapping)
    assert combo is not None, "val must factor through the temperament"
    alpha, beta = combo
    tempered, errors, deg_by_prod, temp_by_prod = [], [], {}, {}
    for t, d in zip(TONES, mono["degrees"]):
        pitch = (sum(mm * e for mm, e in zip(mapping[0], t["monzo"])) * per
                 + sum(mm * e for mm, e in zip(mapping[1], t["monzo"])) * g)
        tempered.append(pitch)
        errors.append(pitch - t["cents"])
        deg_by_prod[t["product"]] = d
        temp_by_prod[t["product"]] = pitch
    max_err = max(abs(e) for e in errors)
    merges = []
    for col in mono["collisions"]:
        cm = tuple(col["comma_monzo"])
        gen_steps = sum(mm * e for mm, e in zip(mapping[1], cm))
        per_steps = sum(mm * e for mm, e in zip(mapping[0], cm))
        merges.append({**col, "pitch_merged": gen_steps == 0
                       and per_steps % mapping[0][0] == 0})
    n_coll = len(mono["collisions"])
    injective = n_coll == 0
    regimes = []
    for eps in EPS_BRIDGE:
        if max_err >= eps:
            regimes.append("over-budget")
        elif n_coll:
            regimes.append("tempered-merge")
        else:
            regimes.append("faithful")
    img = triad.score_tempered(tempered, epsilon_cents=EPSILON_TEMPERED)
    subsets = {name: subset_receipt(prods, deg_by_prod, temp_by_prod, n,
                                    bases[name])
               for name, prods in SUBSETS.items()}
    host = host_receipt(mapping, g, n, mono["degrees"])
    row = {
        "status": "scored", "comma": frac_str(ratio_of(c)),
        "comma_monzo": list(c), "comma_cents": round(cents_of(c), 6),
        "val": list(v), "N": n, "patent_val": list(patent_val(n)),
        "k2": frac_str(ratio_of(k2)), "k2_monzo": list(k2),
        "mapping": [list(r) for r in mapping],
        "period_cents": per, "generator_cents_raw": g,
        "generator_cents": g % per, "generator_degree_beta": beta,
        "alpha": alpha, "minimax_error_cents": minimax_err,
        "tesseract": {"formal_vertices": len(VERTICES),
                      "distinct_tones": len(TONES), "trivial_1_pairs": 8},
        "tones": [{"ratio": frac_str(t["ratio"]), "just_cents":
                   round(t["cents"], 6), "degree": d,
                   "degree_mod_N": d % n, "chain_b": b,
                   "tempered_cents": round(tc, 6),
                   "error_cents": round(tc - t["cents"], 6)}
                  for t, d, b, tc in zip(TONES, mono["degrees"],
                                         host["chain_positions"], tempered)],
        "vertex_degrees": [{"subset": vx["subset"], "product": vx["product"],
                            "degree_mod_N": deg_by_prod[vx["product"]] % n}
                           for vx in VERTICES],
        "collisions": merges, "collision_count": n_coll,
        "pitch_merge_count": sum(m["pitch_merged"] for m in merges),
        "injective": injective,
        "max_error_cents": round(max_err, 6),
        "mean_error_cents": round(sum(abs(e) for e in errors)
                                  / len(errors), 6),
        "image_score_tempered_eps2": {"P": img.proportional,
                                      "S": img.subcontrary,
                                      "G": img.geometric},
        "subsets": subsets, "host": host,
        "eps_bridge_regimes": regimes,
        "min_faithful_eps": next((e for e, r in zip(EPS_BRIDGE, regimes)
                                  if r == "faithful"), None),
        "h_b2_pass": (injective and host["contained"] and max_err < 15.0
                      and subsets["hexany"]["triads_survive"]),
    }
    if host["contained"]:
        # POST-HOC lens (added after first inspection, logged in LOG.md):
        # the smallest integer epsilon at which the tempered hexany image
        # recovers its full base count under the frozen scorer. Changes no
        # pre-registered field; every epsilon is recorded with its score.
        hex_pitches = [temp_by_prod[p] for p in HEXANY_PRODUCTS]
        base = bases["hexany"]
        recovery = None
        for eps in EPS_BRIDGE:
            img2 = triad.score_tempered(hex_pitches, epsilon_cents=eps)
            if (img2.proportional >= base.proportional
                    and img2.subcontrary >= base.subcontrary):
                recovery = eps
                break
        row["posthoc_hexany_full_recovery_eps"] = recovery
    return row


# ---------------------------------------------------------------- driver ---

def subset_bases() -> dict:
    return {name: triad.score(canonical_rational_scale(
        [Fraction(p) for p in prods]))
        for name, prods in SUBSETS.items()}


def main() -> None:
    commas = enumerate_commas()
    bases = subset_bases()
    full_base = triad.score(canonical_rational_scale(
        [t["ratio"] for t in TONES]))
    assert (bases["hexany"].proportional, bases["hexany"].subcontrary) \
        == (6, 6), "hexany base must be the v1.1.0 (6,6), not SPEC's (8,8)"

    mono_cache: dict = {}
    box_cache: dict = {}
    temper_cache: dict = {}
    rows, rejected = [], []
    per_comma: dict[Monzo, dict] = {
        c: {"pairs": 0, "rejected": 0, "scored": 0} for c in commas}

    for n in N_RANGE:
        for v in vals_for(n):
            live = [c for c in commas if vdot(v, c) == 0]
            if not live:
                continue
            if v not in mono_cache:
                mono_cache[v] = monotonicity(v)
            mono = mono_cache[v]
            for c in live:
                per_comma[c]["pairs"] += 1
                if not mono["monotone"]:
                    per_comma[c]["rejected"] += 1
                    rejected.append({
                        "status": "rejected_monotonicity",
                        "comma": frac_str(ratio_of(c)),
                        "comma_monzo": list(c), "val": list(v), "N": n,
                        "violations": mono["violations"]})
                    continue
                if v not in box_cache:
                    box_cache[v] = kernel_box_for(v)
                completion = choose_completion(c, v, box_cache[v],
                                               temper_cache)
                if completion is None:
                    rejected.append({
                        "status": "rejected_no_completion",
                        "comma": frac_str(ratio_of(c)),
                        "val": list(v), "N": n})
                    continue
                k2, mapping, g, err = completion
                per_comma[c]["scored"] += 1
                rows.append(measure_candidate(c, v, n, mono, k2, mapping,
                                              g, err, bases))

    # ---- receipts -----------------------------------------------------
    RESULTS.parent.mkdir(exist_ok=True)
    with RESULTS.open("w") as fh:
        for row in rows + rejected:
            fh.write(json.dumps(row) + "\n")

    # ---- Pareto front vs BRIDGE-000 -----------------------------------
    dedup: dict = {}
    for row in rows:
        if not row["host"]["contained"]:
            continue
        key = (tuple(tuple(r) for r in row["mapping"]), row["N"],
               tuple(row["val"]))
        if key not in dedup:
            dedup[key] = {**{k: row[k] for k in (
                "val", "N", "k2", "mapping", "generator_cents",
                "max_error_cents", "collision_count",
                "image_score_tempered_eps2", "h_b2_pass",
                "posthoc_hexany_full_recovery_eps")},
                "hexany_image_P": row["subsets"]["hexany"]["image_P"],
                "hexany_survives": row["subsets"]["hexany"]
                ["triads_survive"],
                "host_step_classes": row["host"]["host_step_classes"],
                "comma_aliases": []}
        dedup[key]["comma_aliases"].append(row["comma"])

    cands = list(dedup.values())

    def dominates(a, b):
        ge = (a["hexany_image_P"] >= b["hexany_image_P"]
              and a["collision_count"] <= b["collision_count"]
              and a["max_error_cents"] <= b["max_error_cents"])
        strict = (a["hexany_image_P"] > b["hexany_image_P"]
                  or a["collision_count"] < b["collision_count"]
                  or a["max_error_cents"] < b["max_error_cents"])
        return ge and strict

    front = sorted(
        (a for a in cands if not any(dominates(b, a) for b in cands)),
        key=lambda r: r["max_error_cents"])

    passers = [r for r in rows if r["h_b2_pass"]]
    flagship = min(passers, key=lambda r: (r["max_error_cents"],
                                           -r["subsets"]["hexany"]["image_P"],
                                           r["N"], tuple(r["val"]))) \
        if passers else None
    # POST-HOC reading (logged): the pre-registered H-B2 sentence was
    # ambiguous about MOS containment; the strict reading (the MOS carries
    # the image — the program's meaning of "carries") is the headline.
    # The addressing-only reading is reported alongside for honesty.
    loose = [r for r in rows if r["injective"]
             and r["max_error_cents"] < 15.0
             and r["subsets"]["hexany"]["triads_survive"]]
    loose_best = min(loose, key=lambda r: (r["max_error_cents"], r["N"],
                                           tuple(r["val"]))) if loose else None

    killed = sorted(frac_str(ratio_of(c)) for c, s in per_comma.items()
                    if s["pairs"] > 0 and s["scored"] == 0)
    named_set = set(NAMED_COMMAS)
    bridge000 = json.loads(BRIDGE000.read_text())["pareto_standard"]

    summary = {
        "experiment": "BRIDGE-001", "date": str(date.today()),
        "scorer_version": triad.SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "epsilon_tempered": EPSILON_TEMPERED,
        "comma_enumeration": {
            "count": len(commas),
            "named_included": sorted(named_set),
            "list": [{"comma": frac_str(ratio_of(c)), "monzo": list(c),
                      "cents": round(cents_of(c), 4)} for c in commas]},
        "bases": {name: {"P": b.proportional, "S": b.subcontrary,
                         "G": b.geometric}
                  for name, b in bases.items()},
        "full_eg4_base": {"P": full_base.proportional,
                          "S": full_base.subcontrary,
                          "G": full_base.geometric},
        "candidates": {
            "pairs_total": sum(s["pairs"] for s in per_comma.values()),
            "rejected_monotonicity": sum(
                1 for r in rejected
                if r["status"] == "rejected_monotonicity"),
            "scored": len(rows),
            "contained_distinct_temperaments": len(cands)},
        "monotonicity_kills": {
            "fully_killed_commas": killed,
            "fully_killed_count": len(killed),
            "named_killed": sorted(named_set & set(killed)),
            "per_comma": {frac_str(ratio_of(c)): s
                          for c, s in sorted(per_comma.items())
                          if s["pairs"] > 0}},
        "pareto_front": front,
        "h_b2": {"passers": len(passers),
                 "verdict": "PASS" if passers else "FAIL",
                 "flagship": flagship,
                 "posthoc_addressing_only_reading": {
                     "passers": len(loose),
                     "best": None if loose_best is None else {
                         "comma": loose_best["comma"],
                         "k2": loose_best["k2"],
                         "val": loose_best["val"], "N": loose_best["N"],
                         "max_error_cents":
                             loose_best["max_error_cents"],
                         "contained": loose_best["host"]["contained"],
                         "chain_span": loose_best["host"]["chain_span"],
                         "notes_per_period_class":
                             loose_best["host"]
                             ["notes_per_period_class"]}}},
        "bridge000_standard": {
            "hexany_survival": bridge000["harmonic_wealth"]
            ["hexanies_injectively_addressed"],
            "collisions": bridge000["addressing_cost"]["collision_count"],
            "cents_error": bridge000["cents_error"]},
        "notes_for_marcus": [
            "Rank accounting: a linear MOS host is rank 2 in 2.3.5.7, so "
            "the kernel is rank 2 (two commas), not the SPEC's 'exactly "
            "ONE'; resolved as (comma, val) pairs with the pre-registered "
            "min-error completion rule for the implicit second comma.",
            "The 16-tone tesseract has 16 formal vertices but 8 distinct "
            "pitch classes (divisors of 105) because seed 1 pairs each "
            "subset with its 1-augmented twin — the BRIDGE-000 convention "
            "(EG6: 64 subsets = 32 tones). Injectivity is on the 8."],
    }
    SUMMARY.write_text(json.dumps(summary, indent=1))

    print(f"commas enumerated: {len(commas)} (all 9 named included)")
    print(f"candidates: {summary['candidates']['pairs_total']} pairs, "
          f"{summary['candidates']['rejected_monotonicity']} rejected by "
          f"monotonicity, {len(rows)} scored")
    print(f"fully killed commas: {len(killed)} "
          f"(named killed: {summary['monotonicity_kills']['named_killed']})")
    print(f"distinct contained temperaments: {len(cands)}; Pareto front: "
          f"{len(front)}")
    for r in front:
        print(f"  N={r['N']} val={r['val']} k2={r['k2']} "
              f"g={r['generator_cents']:.2f}c err={r['max_error_cents']}c "
              f"coll={r['collision_count']} hexP={r['hexany_image_P']} "
              f"aliases={r['comma_aliases']}")
    print(f"H-B2: {summary['h_b2']['verdict']} ({len(passers)} passers)")
    if flagship:
        print(f"flagship: comma={flagship['comma']} k2={flagship['k2']} "
              f"N={flagship['N']} val={flagship['val']} "
              f"g={flagship['generator_cents']:.3f}c "
              f"err={flagship['max_error_cents']}c "
              f"hex={flagship['subsets']['hexany']['image_P']},"
              f"{flagship['subsets']['hexany']['image_S']}")


if __name__ == "__main__":
    main()
