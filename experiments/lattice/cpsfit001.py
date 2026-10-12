"""CPSFIT-001 — exact minimax chain fit of a CPS field (LOG.md
pre-registration 2026-10-10; committed before this file).

Program B (Marcus, 2026-10-08): find a generator and note count whose MOS
field approximates a CPS field, ET-approximation style, within 2 cents.
For each lattice (hexany CPS(4,2){1,3,5,7}; the EG4 tesseract's 8 distinct
tones; Ptolemy's just major as control) and each N in 5..48, the generator
g* in (0, 600c] minimizing the largest circular error of any lattice tone to
a degree of the N-note chain {k*g : k in [s, s+N-1]}, s <= 0 <= s+N-1 (the
chain contains 1/1) — solved exactly by an interval sweep + bisection on
the tolerance, then a ternary refinement of g for the found assignment.

Then per fit: the k-assignment's homomorphism test (an integer mapping
(k3, k5, k7) with k(tone) = sum e_p k_p — the fit is a val, not an
accident), the kernel of that mapping (period = octave; 7-limit commas in
BRIDGE-001's box), whether the chain is a 2-step MOS, frozen triads v1.1.0
(score_tempered, eps = 2c) and frozen melodic v0.1.0 of the full chain,
the lattice IMAGE (fitted tones only) under the frozen tempered scorer at
eps in {1, 2, 3, 5}c (triad survival at LOCK), the mirror's per-triad
deviation and the smallest eps recovering every exact triad, equal
temperaments N = 5..72 the same way, and the nearest two-term recurrences
within 2c of g* flagged power-of-two / in-octave per the MERU-001 law.
Predictions P-F1..P-F5 are pinned in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score, score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)

Receipts: results/cpsfit001.jsonl (one row per lattice x N, plus ET rows)
+ results/cpsfit001_summary.json; results/scl/cpsfit001/*.scl ear-check
stimuli. Deterministic: stdlib only, no randomness, no wall-clock fields;
two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 cpsfit001.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import combinations
from math import gcd, log2, prod
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scorer import (  # noqa: E402  (frozen v1.1.0, read-only)
    SCORER_VERSION,
    canonical_rational_scale,
    score,
    score_tempered,
)
from melodic import (  # noqa: E402  (frozen v0.1.0, read-only)
    MELODIC_VERSION,
    score_melodic,
)
from families.cps import cps_scale  # noqa: E402

CPSFIT001_VERSION = "1.0.0"
EXPERIMENT = "CPSFIT-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "cpsfit001.jsonl"
SUMMARY = RESULTS_DIR / "cpsfit001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "cpsfit001"

CENTS = 1200.0
N_MIN, N_MAX = 5, 48
ET_MIN, ET_MAX = 5, 72
EPS_LOCK = 2.0
EPS_IMAGE = (1.0, 2.0, 3.0, 5.0)
EPS_HI = 60.0
BISECT_STEPS = 14
TERNARY_STEPS = 200
G_MAX = 600.0
PRIMES = (3, 5, 7)
KERNEL_BOX = (12, 6, 5)       # |e3|, |e5|, |e7| (BRIDGE-001 box)
KERNEL_CENTS_MAX = 60.0
KERNEL_HEIGHT_MAX = 2 ** 40
RR_COEFS = (1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 64, 128)
RR_MAX_ORDER = 12
RR_TOL = 2.0

#: Registered predictions, verbatim from LOG.md 2026-10-10.
PREDICTIONS = {
    "P-F1_hexany_staircase": {  # N -> (eps*, g*)
        6: (42.23, 257.15), 7: (40.76, 465.30), 8: (28.52, 357.79),
        9: (24.41, 361.90), 10: (23.30, 118.69), 11: (18.85, 249.36),
        12: (13.73, 318.36), 13: (13.73, 318.36), 14: (13.73, 318.36),
        15: (4.815, 502.86), 16: (4.771, 116.50), 17: (4.771, 116.50),
        18: (3.275, 77.92), 19: (2.571, 271.42), 20: (2.571, 271.42),
        21: (2.571, 271.42), 22: (1.367, 193.79), 30: (1.367, 193.79),
        31: (0.743, 77.20), 48: (0.743, 77.20),
    },
    "P-F1_min_N": {"hexany": {"2.0": 22, "1.0": 31, "5.0": 15, "15.0": 12},
                   "eg4": {"2.0": 24}, "ptolemy7": {"2.0": 12, "10.0": 7}},
    "P-F2_hexany_nonhomomorphic_N": (7, 10),
    "P-F2_mappings": {15: (-1, -4, -10), 16: (6, -7, -2), 19: (7, -3, 8),
                      22: (16, 2, 5), 31: (-22, 5, -3)},
    "P-F3_hexany_survival_2c": {15: 2, 16: 6, 19: 8, 22: 10, 31: 12},
    "P-F3_hexany_full_recovery_eps": {15: 7.25, 16: 2.94, 19: 3.42, 22: 2.08, 31: 0.32},
    "P-F3_eg4_survival_2c": {16: 4, 19: 16, 24: 20},
    "P-F4_law_floor": {("hexany", 15): 11, ("ptolemy7", 7): 3},
}

STAIR_TOL_EPS = 0.01   # cents, comparing eps* to the registered staircase
STAIR_TOL_G = 0.01     # cents, comparing g* to the registered staircase


# ---------------------------------------------------------------------------
# lattices and pure math
# ---------------------------------------------------------------------------


def cents_of(x: Fraction | float) -> float:
    return CENTS * log2(float(x))


def wrap(c: float) -> float:
    return c % CENTS


def circ(a: float, b: float) -> float:
    d = abs(wrap(a) - wrap(b))
    return min(d, CENTS - d)


def eg4_tones() -> tuple[Fraction, ...]:
    factors = (1, 3, 5, 7)
    prods = [Fraction(prod(c)) for r in range(0, 5) for c in combinations(factors, r)]
    return canonical_rational_scale(prods)


LATTICES: dict[str, tuple[Fraction, ...]] = {
    "hexany": cps_scale((1, 3, 5, 7), 2),
    "eg4": eg4_tones(),
    "ptolemy7": canonical_rational_scale([Fraction(1), Fraction(9, 8), Fraction(5, 4),
                                          Fraction(4, 3), Fraction(3, 2), Fraction(5, 3),
                                          Fraction(15, 8)]),
}


def monzo(fr: Fraction) -> tuple[int, tuple[int, ...]]:
    """(e2, (e3, e5, e7)); raises if a prime > 7 appears."""
    n, d = fr.numerator, fr.denominator
    e2 = 0
    while n % 2 == 0:
        n //= 2
        e2 += 1
    while d % 2 == 0:
        d //= 2
        e2 -= 1
    out = []
    for p in PRIMES:
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        while d % p == 0:
            d //= p
            e -= 1
        out.append(e)
    if n != 1 or d != 1:
        raise ValueError(f"{fr} is not 7-limit")
    return e2, tuple(out)


# ---------------------------------------------------------------------------
# the exact fit
# ---------------------------------------------------------------------------


def feasible(tone_cents: list[float], n: int, eps: float) -> tuple[float, int] | None:
    """First g (ascending) at which some window of N consecutive chain
    degrees containing 0 lands every tone within eps; (g, s) or None."""
    big_k = n - 1
    t_count = len(tone_cents)
    always = [circ(0.0, c) <= eps for c in tone_cents]
    events: list[tuple[float, int, int, int]] = []
    for t, c in enumerate(tone_cents):
        for k in range(-big_k, big_k + 1):
            if k == 0:
                continue
            for m in range(-big_k - 2, big_k + 3):
                center = (c + CENTS * m) / k
                lo, hi = center - eps / abs(k), center + eps / abs(k)
                if hi <= 1e-9 or lo > G_MAX:
                    continue
                events.append((max(lo, 1e-9), 0, t, k))
                events.append((min(hi, G_MAX), 1, t, k))
    events.sort()
    active: list[set[int]] = [set() for _ in range(t_count)]

    def check() -> int | None:
        cand: list[list[int]] | None = None
        for t in range(t_count):
            if always[t]:
                continue
            ks = sorted(active[t])
            if not ks:
                return None
            ivs: list[list[int]] = []
            for k in ks:
                a, b = k - big_k, k
                if ivs and a <= ivs[-1][1]:
                    ivs[-1][1] = max(ivs[-1][1], b)
                else:
                    ivs.append([a, b])
            cand = ivs if cand is None else [
                [max(a, c), min(b, d)] for a, b in cand for c, d in ivs
                if max(a, c) <= min(b, d)]
            if not cand:
                return None
        if cand is None:
            return -big_k
        for a, b in cand:
            a2, b2 = max(a, -big_k), min(b, 0)
            if a2 <= b2:
                return a2
        return None

    for g, typ, t, k in events:
        if typ == 0:
            active[t].add(k)
            s = check()
            if s is not None:
                return g, s
        else:
            active[t].discard(k)
    return None


def assign(tone_cents: list[float], n: int, g: float, s: int) -> list[int]:
    out = []
    for c in tone_cents:
        best = min(range(s, s + n), key=lambda k: (circ(k * g, c), abs(k)))
        out.append(best)
    return out


def fit(tone_cents: list[float], n: int, eps_hi: float = EPS_HI) -> dict | None:
    res = feasible(tone_cents, n, eps_hi)
    if res is None:
        return None
    lo, hi = 0.0, eps_hi
    for _ in range(BISECT_STEPS):
        mid = (lo + hi) / 2
        r = feasible(tone_cents, n, mid)
        if r is None:
            lo = mid
        else:
            hi = mid
            res = r
    g, s = res
    ks = assign(tone_cents, n, g, s)

    def err(x: float) -> float:
        return max(circ(k * x, c) for c, k in zip(tone_cents, ks))

    a, b = g - 0.05, g + 0.05
    for _ in range(TERNARY_STEPS):
        m1, m2 = a + (b - a) / 3, b - (b - a) / 3
        if err(m1) < err(m2):
            b = m2
        else:
            a = m1
    g_star = (a + b) / 2
    return {"N": n, "eps": err(g_star), "g": g_star, "s": s, "ks": ks,
            "errs": [circ(k * g_star, c) for c, k in zip(tone_cents, ks)]}


def et_fit(tone_cents: list[float], n: int) -> dict:
    step = CENTS / n
    errs = [abs(c - round(c / step) * step) for c in tone_cents]
    ks = [round(c / step) % n for c in tone_cents]
    return {"N": n, "eps": max(errs), "g": step, "s": 0, "ks": ks, "errs": errs}


# ---------------------------------------------------------------------------
# structure of a fit
# ---------------------------------------------------------------------------


def homomorphism(tones: tuple[Fraction, ...], ks: list[int], n: int) -> tuple[int, ...] | None:
    """Integer (k3, k5, k7) with k(tone) = e3 k3 + e5 k5 + e7 k7 for every
    tone, searched over [-n, n]^3 with unused primes pinned to 0."""
    mz = [monzo(t)[1] for t in tones]
    used = [any(m[p] for m in mz) for p in range(3)]
    rng = [range(-n, n + 1) if u else range(0, 1) for u in used]
    for k3 in rng[0]:
        for k5 in rng[1]:
            for k7 in rng[2]:
                if all(m[0] * k3 + m[1] * k5 + m[2] * k7 == k for m, k in zip(mz, ks)):
                    return (k3, k5, k7)
    return None


def kernel(mapping: tuple[int, ...], g: float) -> list[dict]:
    """7-limit commas (< KERNEL_CENTS_MAX, Tenney height <= 2**40, box
    KERNEL_BOX) killed by the rank-2 mapping [octave row; generator row]."""
    gen = dict(zip(PRIMES, mapping))
    octv = {p: round((cents_of(p) - gen[p] * g) / CENTS) for p in PRIMES}
    out = []
    b3, b5, b7 = KERNEL_BOX
    for e3 in range(-b3, b3 + 1):
        for e5 in range(-b5, b5 + 1):
            for e7 in range(-b7, b7 + 1):
                if (e3, e5, e7) == (0, 0, 0):
                    continue
                if e3 * gen[3] + e5 * gen[5] + e7 * gen[7] != 0:
                    continue
                e2 = -(e3 * octv[3] + e5 * octv[5] + e7 * octv[7])
                r = Fraction(2) ** e2 * Fraction(3) ** e3 * Fraction(5) ** e5 * Fraction(7) ** e7
                if r < 1:
                    continue
                c = cents_of(r)
                if c >= KERNEL_CENTS_MAX or r.numerator * r.denominator > KERNEL_HEIGHT_MAX:
                    continue
                out.append({"comma": f"{r.numerator}/{r.denominator}", "cents": c,
                            "monzo": [e2, e3, e5, e7]})
    out.sort(key=lambda d: d["cents"])
    return out[:6]


def step_class_count(cs: list[float], tol: float) -> int:
    pcs = sorted({round(wrap(c), 9) for c in cs})
    steps = sorted((pcs[k + 1] - pcs[k]) if k + 1 < len(pcs)
                   else pcs[0] + CENTS - pcs[k] for k in range(len(pcs)))
    classes: list[float] = []
    for st in steps:
        if not classes or st - classes[-1] > tol:
            classes.append(st)
    return len(classes)


def _shift_open(x: Fraction, lo: Fraction, hi: Fraction) -> Fraction | None:
    r = x
    while r <= lo:
        r *= 2
    while r >= hi:
        r /= 2
    return r if lo < r < hi else None


def exact_triads(tones: tuple[Fraction, ...]) -> list[tuple[str, Fraction, Fraction, Fraction]]:
    """Mirror of the anchored exact classification (span <= 2/1)."""
    out = []
    for b in tones:
        lows = [r for pc in tones if (r := _shift_open(pc, b / 2, b)) is not None]
        highs = [r for pc in tones if (r := _shift_open(pc, b, 2 * b)) is not None]
        for a in lows:
            for c in highs:
                if c / a > 2:
                    continue
                if 2 * b == a + c:
                    out.append(("P", a, b, c))
                elif b * (a + c) == 2 * a * c:
                    out.append(("S", a, b, c))
    return out


def _reduce(x: Fraction) -> Fraction:
    while x < 1:
        x *= 2
    while x >= 2:
        x /= 2
    return x


def triad_deviations(tones: tuple[Fraction, ...], fitted_pc: list[float]) -> list[dict]:
    """Each exact lattice triad re-voiced in the fit: deviation of the mean
    condition (cents) and the AM-HM separation (the guard quantity)."""
    fitted = {_reduce(t): f for t, f in zip(tones, fitted_pc)}
    out = []
    for lab, a, b, c in exact_triads(tones):
        voiced = []
        for x in (a, b, c):
            pc = fitted[_reduce(x)]
            voiced.append(pc + CENTS * round((cents_of(x) - pc) / CENTS))
        fa, fb, fc = (2 ** (v / CENTS) for v in voiced)
        am, hm = (fa + fc) / 2, 2 * fa * fc / (fa + fc)
        dev = abs(cents_of(fb / am)) if lab == "P" else abs(cents_of(fb / hm))
        out.append({"kind": lab, "triad": f"{a}:{b}:{c}", "dev_cents": dev,
                    "sep_cents": cents_of(am / hm)})
    return out


def positive_root(j: int, i: int, a: int, b: int) -> float:
    def f(x: float) -> float:
        return x ** j - a * x ** (j - i) - b
    lo, hi = 1e-9, 1.0
    while f(hi) < 0:
        hi *= 2
    for _ in range(300):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def build_rr_table() -> list[dict]:
    rows = []
    for j in range(2, RR_MAX_ORDER + 1):
        for i in range(1, j):
            if gcd(i, j) != 1:
                continue
            for a in RR_COEFS:
                for b in RR_COEFS:
                    big_g = positive_root(j, i, a, b)
                    r = a * big_g ** (j - i) / b
                    rows.append({"a": a, "i": i, "b": b, "j": j, "gen01": log2(big_g) % 1.0,
                                 "pow2": (a & (a - 1) == 0) and (b & (b - 1) == 0),
                                 "in_octave": 0.5 < r < 2.0})
    return rows


def nearest_recurrences(table: list[dict], gen01: float, tol: float = RR_TOL,
                        limit: int = 4) -> list[dict]:
    hits = []
    for r in table:
        for mode, gg in (("direct", r["gen01"]), ("complement", 1.0 - r["gen01"])):
            e = (gg - gen01) * CENTS
            if abs(e) <= tol:
                hits.append({**r, "mode": mode, "err_cents": e})
    hits.sort(key=lambda h: (h["j"], abs(h["err_cents"])))
    seen, out = set(), []
    for h in hits:
        if h["j"] in seen:
            continue
        seen.add(h["j"])
        out.append({k: h[k] for k in ("a", "i", "b", "j", "mode", "err_cents", "pow2", "in_octave")})
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------


def fit_row(name: str, tones: tuple[Fraction, ...], tone_cents: list[float],
            f: dict, kind: str, rr_table: list[dict]) -> dict:
    n, g, s, ks = f["N"], f["g"], f["s"], f["ks"]
    chain = [wrap(k * g) for k in range(s, s + n)]
    fitted_pc = [wrap(k * g) for k in ks]
    hom = None if kind == "ET" else homomorphism(tones, ks, n)
    ker = kernel(hom, g) if hom else []
    full = score_tempered(chain, EPS_LOCK)
    mel = score_melodic(chain)
    image = {str(e): score_tempered(fitted_pc, e) for e in EPS_IMAGE}
    devs = triad_deviations(tones, fitted_pc)
    exact_count = len(devs)
    survive_mirror = sum(1 for d in devs if d["dev_cents"] <= EPS_LOCK and d["sep_cents"] >= EPS_LOCK)
    return {
        "experiment": EXPERIMENT, "lattice": name, "kind": kind, "N": n,
        "eps_star_cents": f["eps"], "g_cents": g, "g01": g / CENTS,
        "window_start": s, "ks": ks, "tone_errors_cents": f["errs"],
        "homomorphic": hom is not None, "mapping": list(hom) if hom else None,
        "kernel": ker, "is_mos": step_class_count(chain, 0.01) == 2,
        "step_classes": step_class_count(chain, 0.01),
        "chain_P_2c": full.proportional, "chain_S_2c": full.subcontrary,
        "chain_G_2c": full.geometric, "chain_dropped_2c": full.degenerate_dropped,
        "chain_m1_gap_classes": mel.gap_entropy.gap_class_count,
        "chain_m2_cs_violations": mel.constant_structure.violations,
        "chain_m3_propriety": mel.propriety.classification,
        "image_P": {e: r.proportional for e, r in image.items()},
        "image_S": {e: r.subcontrary for e, r in image.items()},
        "image_dropped": {e: r.degenerate_dropped for e, r in image.items()},
        "exact_triads": exact_count,
        "survival_2c_frozen": image["2.0"].proportional + image["2.0"].subcontrary,
        "survival_2c_mirror": survive_mirror,
        "max_triad_dev_cents": max((d["dev_cents"] for d in devs), default=0.0),
        "triad_deviations": devs,
        "nearest_recurrences": nearest_recurrences(rr_table, g / CENTS),
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_cents": EPS_LOCK,
    }


def run_lattice(name: str, tones: tuple[Fraction, ...], rr_table: list[dict]) -> list[dict]:
    tone_cents = [cents_of(t) for t in tones]
    rows = []
    eps_hi = EPS_HI
    for n in range(N_MIN, N_MAX + 1):
        f = fit(tone_cents, n, eps_hi)
        if f is None:
            continue
        eps_hi = min(EPS_HI, f["eps"] + 0.02)   # eps*(N) is non-increasing
        rows.append(fit_row(name, tones, tone_cents, f, "chain", rr_table))
    for n in range(ET_MIN, ET_MAX + 1):
        rows.append(fit_row(name, tones, tone_cents, et_fit(tone_cents, n), "ET", rr_table))
    return rows


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def min_n_within(rows: list[dict], eps: float, kind: str = "chain") -> int | None:
    return next((r["N"] for r in rows if r["kind"] == kind and r["eps_star_cents"] <= eps), None)


def verdict_p_f1(by_lat: dict[str, list[dict]]) -> dict:
    pred = PREDICTIONS["P-F1_hexany_staircase"]
    hx = {r["N"]: r for r in by_lat["hexany"] if r["kind"] == "chain"}
    mism = []
    for n, (pe, pg) in pred.items():
        r = hx.get(n)
        if r is None or abs(r["eps_star_cents"] - pe) > STAIR_TOL_EPS or abs(r["g_cents"] - pg) > STAIR_TOL_G:
            mism.append({"N": n, "predicted": (pe, pg),
                         "got": None if r is None else (r["eps_star_cents"], r["g_cents"])})
    minn = {lat: {e: min_n_within(by_lat[lat], float(e)) for e in d}
            for lat, d in PREDICTIONS["P-F1_min_N"].items()}
    minn_mism = [(lat, e, minn[lat][e], want) for lat, d in PREDICTIONS["P-F1_min_N"].items()
                 for e, want in d.items() if minn[lat][e] != want]
    return {"kept": not mism and not minn_mism, "staircase_mismatches": mism,
            "min_N": minn, "min_N_mismatches": minn_mism}


def verdict_p_f2(by_lat: dict[str, list[dict]]) -> dict:
    hx = {r["N"]: r for r in by_lat["hexany"] if r["kind"] == "chain"}
    nonhom = tuple(n for n, r in sorted(hx.items()) if not r["homomorphic"])
    map_mism = [(n, m, hx[n]["mapping"]) for n, m in PREDICTIONS["P-F2_mappings"].items()
                if tuple(hx[n]["mapping"] or ()) != m]
    return {"kept": nonhom == PREDICTIONS["P-F2_hexany_nonhomomorphic_N"] and not map_mism,
            "hexany_nonhomomorphic_N": nonhom, "mapping_mismatches": map_mism,
            "kernels": {n: [c["comma"] for c in hx[n]["kernel"]] for n in PREDICTIONS["P-F2_mappings"]}}


def verdict_p_f3(by_lat: dict[str, list[dict]]) -> dict:
    hx = {r["N"]: r for r in by_lat["hexany"] if r["kind"] == "chain"}
    eg = {r["N"]: r for r in by_lat["eg4"] if r["kind"] == "chain"}
    mism, mirror_mism = [], []
    for n, want in PREDICTIONS["P-F3_hexany_survival_2c"].items():
        if hx[n]["survival_2c_frozen"] != want:
            mism.append(("hexany", n, want, hx[n]["survival_2c_frozen"]))
        if hx[n]["survival_2c_frozen"] != hx[n]["survival_2c_mirror"]:
            mirror_mism.append(("hexany", n, hx[n]["survival_2c_frozen"], hx[n]["survival_2c_mirror"]))
    for n, want in PREDICTIONS["P-F3_eg4_survival_2c"].items():
        if eg[n]["survival_2c_frozen"] != want:
            mism.append(("eg4", n, want, eg[n]["survival_2c_frozen"]))
    rec_mism = [(n, want, hx[n]["max_triad_dev_cents"])
                for n, want in PREDICTIONS["P-F3_hexany_full_recovery_eps"].items()
                if abs(hx[n]["max_triad_dev_cents"] - want) > 0.01]
    return {"kept": not mism and not rec_mism, "survival_mismatches": mism,
            "frozen_vs_mirror_mismatches": mirror_mism, "recovery_eps_mismatches": rec_mism,
            "hexany_survival_table": {n: (hx[n]["survival_2c_frozen"], hx[n]["exact_triads"],
                                          hx[n]["max_triad_dev_cents"]) for n in sorted(hx)}}


def verdict_p_f4(by_lat: dict[str, list[dict]]) -> dict:
    got, bad = {}, []
    for (lat, n), floor in PREDICTIONS["P-F4_law_floor"].items():
        r = next(x for x in by_lat[lat] if x["kind"] == "chain" and x["N"] == n)
        got[f"{lat}/N{n}"] = {"P_2c": r["chain_P_2c"], "floor": floor,
                              "nearest": r["nearest_recurrences"][:1]}
        if r["chain_P_2c"] < floor:
            bad.append(f"{lat}/N{n}")
    return {"kept": not bad, "rows": got, "below_floor": bad}


def verdict_p_f5(by_lat: dict[str, list[dict]]) -> dict:
    hx = by_lat["hexany"]
    first = min_n_within(hx, EPS_LOCK, "ET")
    le41 = [r["N"] for r in hx if r["kind"] == "ET" and r["N"] <= 41 and r["eps_star_cents"] <= EPS_LOCK]
    return {"kept": not le41, "first_ET_within_2c": first, "ET_le_41_within_2c": le41,
            "best_ET_le_41": min(((r["eps_star_cents"], r["N"]) for r in hx
                                  if r["kind"] == "ET" and r["N"] <= 41))}


# ---------------------------------------------------------------------------
# .scl
# ---------------------------------------------------------------------------


def scl_text(name: str, description: str, cs: list[float]) -> str:
    pcs = sorted({round(wrap(c), 6) for c in cs})
    degrees = [c for c in pcs if c > 1e-9] + [CENTS]
    lines = [f"! {name}.scl", "!", description, f" {len(degrees)}", "!"]
    lines += [f" {d:.6f}" for d in degrees]
    return "\n".join(lines) + "\n"


def write_scl(rows: list[dict]) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for n in (15, 22):
        r = next(x for x in rows if x["lattice"] == "hexany" and x["kind"] == "chain" and x["N"] == n)
        chain = [wrap(k * r["g_cents"]) for k in range(r["window_start"], r["window_start"] + n)]
        name = f"cpsfit001_hexany_N{n:02d}_g{r['g_cents']:.2f}"
        text = scl_text(name, f"CPSFIT-001 hexany 1.3.5.7 inside a {n}-note chain of "
                        f"{r['g_cents']:.4f} cents (max tone error {r['eps_star_cents']:.3f} c); "
                        f"1/1 = chain degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> dict:
    rr_table = build_rr_table()
    by_lat = {name: run_lattice(name, tones, rr_table) for name, tones in LATTICES.items()}
    rows = [r for name in LATTICES for r in by_lat[name]]
    verdicts = {"P-F1": verdict_p_f1(by_lat), "P-F2": verdict_p_f2(by_lat),
                "P-F3": verdict_p_f3(by_lat), "P-F4": verdict_p_f4(by_lat),
                "P-F5": verdict_p_f5(by_lat)}
    staircase = {name: [{"N": r["N"], "eps": r["eps_star_cents"], "g": r["g_cents"],
                         "mapping": r["mapping"], "mos": r["is_mos"],
                         "P_2c": r["chain_P_2c"], "survival_2c": r["survival_2c_frozen"],
                         "exact_triads": r["exact_triads"]}
                        for r in by_lat[name] if r["kind"] == "chain"]
                 for name in LATTICES}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": CPSFIT001_VERSION,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "N_range": [N_MIN, N_MAX], "ET_range": [ET_MIN, ET_MAX],
        "lattices": {name: [str(t) for t in tones] for name, tones in LATTICES.items()},
        "rr_table_size": len(rr_table), "n_rows": len(rows),
        "staircase": staircase, "verdicts": verdicts,
        "scl_files": write_scl(rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  melodic {receipt['melodic_version']}  rows={receipt['n_rows']}")
    for name, st in receipt["staircase"].items():
        print(f"  {name}:")
        last = None
        for r in st:
            key = (round(r["eps"], 3), round(r["g"], 2))
            if key == last:
                continue
            last = key
            print(f"    N={r['N']:2d} eps*={r['eps']:7.3f} g*={r['g']:8.3f}c map={r['mapping']} "
                  f"mos={r['mos']} P2c={r['P_2c']} survive={r['survival_2c']}/{r['exact_triads']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}")
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
