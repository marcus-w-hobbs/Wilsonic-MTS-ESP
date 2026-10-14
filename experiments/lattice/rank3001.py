"""RANK3-001 — two-generator (Brun3) fits of CPS lattices (LOG.md
pre-registration 2026-10-12; committed before this file).

For each lattice and each note count N, the smallest largest-tone-error at
which a Brun3 scale (octave + two generators, Viggo Brun's three-term
algorithm as implemented in the iOS Wilsonic, ported in brun3.py) holds
the lattice with its 1/1 on a scale degree. Stage 1 enumerates (g0, g1) on
a 2 cent grid, both calc types, levels 1..7, every mode, and keeps the best
candidates per N. Stage 2 refines each candidate exactly: with the scale's
step structure, mode and nearest-degree assignment held fixed, the minimax
over (g0, g1) is a Chebyshev linear program in two unknowns, solved by
vertex enumeration under the ordering constraints that keep the structure
valid; the assignment is re-derived and the solve repeated until stable.
Per fit: three-row val (exact integer solve), kernel comma, frozen image
survival at 2 cents, mirror deviations, step-size count, frozen melodic.
Predictions P-R1..P-R6 are pinned in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered via cpsfit001)
  experiments/lattice/melodic.py v0.1.0  (score_melodic via cpsfit001)

Receipts: results/rank3001.jsonl + results/rank3001_summary.json;
results/scl/rank3001/*.scl. Stdlib only (multiprocessing), deterministic,
no wall-clock fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 rank3001.py
"""

from __future__ import annotations

import json
import sys
from bisect import bisect_left
from fractions import Fraction
from itertools import combinations
from math import log2
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import brun3  # noqa: E402
import cpsfit001 as c1  # noqa: E402
from scorer import SCORER_VERSION, score_tempered  # noqa: E402
from melodic import MELODIC_VERSION, score_melodic  # noqa: E402
from families.cps import cps_scale  # noqa: E402

RANK3001_VERSION = "1.0.0"
EXPERIMENT = "RANK3-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "rank3001.jsonl"
SUMMARY = RESULTS_DIR / "rank3001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "rank3001"

CENTS = 1200.0
GRID = 2.0
LEVELS = tuple(range(1, brun3.MAX_LEVEL + 1))
TOPK = 8
EPS_LOCK = 2.0
EPS_IMAGE = (1.0, 2.0, 3.0, 5.0)
PRIMES = (3, 5, 7, 11)
KERNEL_BOX = {3: 12, 5: 6, 7: 5, 11: 4}
KERNEL_CENTS_MAX = 60.0
KERNEL_HEIGHT_MAX = 2 ** 40
LP_TOL = 1e-9
REASSIGN_ROUNDS = 6
WORKERS = 8

LATTICES: dict[str, tuple[Fraction, ...]] = {
    "hexany": c1.LATTICES["hexany"],
    "eg4": c1.LATTICES["eg4"],
    "dek52": cps_scale((1, 3, 5, 7, 9), 2),
    "eikosany": cps_scale((1, 3, 5, 7, 9, 11), 3),
}

#: Registered predictions, verbatim from LOG.md 2026-10-12. Errors are upper bounds (+0.05c).
PREDICTIONS = {
    "tol_cents": 0.05,
    "P-R1": {10: (2.57, "225/224", 4), 15: (2.81, "1029/1024", 10), 19: (0.61, "65625/65536", 12),
             20: (2.57, "225/224", 10), 21: (0.12, "2401/2400", 12), 24: (0.46, "32805/32768", 12),
             27: (0.12, "2401/2400", 12), 29: (0.25, "32805/32768", 12),
             "first_within_2c": 19, "first_full": 19},
    "P-R2": {10: (2.57, "225/224", 8), 15: (2.81, "1029/1024", 18), 19: (0.47, "65625/65536", 24),
             21: (0.12, "2401/2400", 24), 24: (0.46, "32805/32768", 24), "first_full": 19},
    "P-R3": {21: (3.27, "1728/1715", 25), 29: (0.66, "32805/32768", 41),
             "N29_g0": 701.73, "N29_g1": 64.0, "g_tol": 0.5},
    "P-R4": {"min_err_floor": 10.0, "best_err_about": 12.0, "best_err_tol": 1.5, "best_N": 31,
             "survival_max": 29, "N_max": 34},
    "P-R6": {"within_3c_level": 7, "calc_at": {10: "AC", 24: "AC", 15: "AB", 19: "AB", 21: "AB", 27: "AB", 29: "AB"}},
}


# ---------------------------------------------------------------------------
# lattice helpers (11-limit monzos; cpsfit001's are 7-limit)
# ---------------------------------------------------------------------------


def monzo(fr: Fraction) -> tuple[int, tuple[int, ...]]:
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
        raise ValueError(f"{fr} is not 11-limit")
    return e2, tuple(out)


def circ(a: float, b: float) -> float:
    d = abs((a - b) % CENTS)
    return min(d, CENTS - d)


# ---------------------------------------------------------------------------
# stage 1: the grid
# ---------------------------------------------------------------------------


def mode_errors(pcs: list[float], tones: list[float]) -> list[tuple[float, int]]:
    """For each mode m: the largest error of any tone to the scale rotated so
    that degree m is 1/1. pcs are the unrotated pitch classes (cents)."""
    srt = sorted(pcs)
    ext = srt + [x + CENTS for x in srt]
    out = []
    for m, pm in enumerate(pcs):
        worst = 0.0
        for t in tones:
            x = (t + pm) % CENTS
            i = bisect_left(srt, x)
            lo = ext[i - 1] if i > 0 else srt[-1] - CENTS
            hi = ext[i]
            e = min(x - lo, hi - x)
            if e > worst:
                worst = e
        out.append((worst, m))
    return out


def grid_column(args) -> dict[int, list]:
    """All g1 for one g0 (cents). Returns N -> candidate list."""
    g0c, tones = args
    g0 = g0c / CENTS
    best: dict[int, list] = {}
    j = GRID
    while j < g0c:
        g1 = j / CENTS
        for calc in brun3.CALCS:
            try:
                lv = brun3.brun3_levels(1.0, g0, g1, calc)
            except RuntimeError:
                # commensurable pair: the rank collapses and Brun3 runs out of intervals to split
                best.setdefault(-1, []).append((0.0, g0c, j, calc, 0, 0))
                continue
            for L in LEVELS:
                steps = lv[L]
                pcs = brun3.scale_cents(steps, 1.0, g0, g1, 0)
                n = len(pcs)
                me = mode_errors(pcs, tones)
                e, m = min(me)
                lst = best.setdefault(n, [])
                lst.append((e, g0c, j, calc, L, m))
        j += GRID
    for n, lst in best.items():
        if n == -1:
            continue
        lst.sort()
        del lst[TOPK:]
    return best


def stage1(tones: list[float]) -> dict[int, list]:
    cols = [(g0c, tones) for g0c in _frange(2 * GRID, CENTS - GRID, GRID)]
    merged: dict[int, list] = {}
    skipped = 0
    with Pool(WORKERS) as pool:
        for part in pool.imap(grid_column, cols, chunksize=4):
            for n, lst in part.items():
                if n == -1:
                    skipped += len(lst)
                    continue
                merged.setdefault(n, []).extend(lst)
    for n, lst in merged.items():
        lst.sort()
        del lst[TOPK:]
    merged[-1] = skipped
    return merged


def _frange(a: float, b: float, step: float) -> list[float]:
    out = []
    k = 0
    while True:
        v = a + k * step
        if v > b:
            break
        out.append(v)
        k += 1
    return out


# ---------------------------------------------------------------------------
# stage 2: exact Chebyshev refinement
# ---------------------------------------------------------------------------


def structure_constraints(O: float, g0: float, g1: float, calc: str, L: int) -> list[tuple[int, int, int]]:
    """Linear forms (a, b, c) with a*O + b*g0 + c*g1 >= 0 that keep the Brun3
    ordering decisions of this (g0, g1) unchanged through level L."""
    H = [[O, (1, 0, 0)], [g0, (0, 1, 0)], [g1, (0, 0, 1)]]
    H.sort(key=lambda h: -h[0])
    cons = []

    def add_order():
        cons.append(tuple(x - y for x, y in zip(H[0][1], H[1][1])))
        cons.append(tuple(x - y for x, y in zip(H[1][1], H[2][1])))
        cons.append(H[2][1])   # smallest interval stays positive

    add_order()
    j = 1 if calc == "AB" else 2
    for _ in range(L):
        newco = tuple(x - y for x, y in zip(H[0][1], H[j][1]))
        H[0] = [H[0][0] - H[j][0], newco]
        H.sort(key=lambda h: -h[0])
        add_order()
    return cons


def assignment(pcs_rot: list[tuple[float, tuple[int, int, int]]], tones: list[float],
               g0c: float, g1c: float):
    """Nearest degree per tone in the rotated scale: (octave shift a, triple co)
    with pitch(tone) = (co[0] + a)*1200 + co[1]*g0c + co[2]*g1c."""
    out = []
    for t in tones:
        best = None
        for pc, co in pcs_rot:
            e = circ(pc, t)
            if best is None or e < best[0]:
                best = (e, pc, co)
        _, pc, co = best
        raw = co[0] * CENTS + co[1] * g0c + co[2] * g1c
        a = round((t - raw) / CENTS)
        out.append((a, co))
    return out


def rotated_degrees(steps, g0: float, g1: float, mode: int):
    cos = brun3.degrees(steps)
    base = cos[mode]
    rel = [tuple(x - y for x, y in zip(c, base)) for c in cos]
    pcs = [((c[0] * 1.0 + c[1] * g0 + c[2] * g1) * CENTS) % CENTS for c in rel]
    # express each degree as (reduced pitch, relative triple) where triple*(O,g0,g1) may differ from pc by octaves
    return [(pc, co) for pc, co in zip(pcs, rel)]


def solve_chebyshev(rows: list[tuple[float, float, float]], cons: list[tuple[float, float, float]],
                    box: tuple[float, float, float, float]) -> tuple[float, float, float] | None:
    """min eps s.t. |k0 + k1*x + k2*y| <= eps for rows, c0 + c1*x + c2*y >= 0 for cons,
    box = (xlo, xhi, ylo, yhi). Vertex enumeration in (x, y, eps). Returns (eps, x, y)."""
    # half-planes in (x, y, eps): A*(x,y,eps) <= b form -> we use generic planes p·(x,y,eps) = q
    planes = []
    for k0, k1, k2 in rows:
        planes.append((k1, k2, -1.0, -k0))     # k0+k1x+k2y - eps <= 0
        planes.append((-k1, -k2, -1.0, k0))    # -(k0+k1x+k2y) - eps <= 0
    for c0, c1, c2 in cons:
        planes.append((-c1, -c2, 0.0, c0))     # -(c0+c1x+c2y) <= 0
    xlo, xhi, ylo, yhi = box
    planes += [(-1.0, 0.0, 0.0, -xlo), (1.0, 0.0, 0.0, xhi), (0.0, -1.0, 0.0, -ylo), (0.0, 1.0, 0.0, yhi)]

    def feasible(x, y, e):
        return all(p[0] * x + p[1] * y + p[2] * e <= p[3] + 1e-7 for p in planes)

    best = None
    for (a1, b1, c1_, d1), (a2, b2, c2_, d2), (a3, b3, c3_, d3) in combinations(planes, 3):
        det = (a1 * (b2 * c3_ - c2_ * b3) - b1 * (a2 * c3_ - c2_ * a3) + c1_ * (a2 * b3 - b2 * a3))
        if abs(det) < 1e-12:
            continue
        x = (d1 * (b2 * c3_ - c2_ * b3) - b1 * (d2 * c3_ - c2_ * d3) + c1_ * (d2 * b3 - b2 * d3)) / det
        y = (a1 * (d2 * c3_ - c2_ * d3) - d1 * (a2 * c3_ - c2_ * a3) + c1_ * (a2 * d3 - d2 * a3)) / det
        e = (a1 * (b2 * d3 - d2 * b3) - b1 * (a2 * d3 - d2 * a3) + d1 * (a2 * b3 - b2 * a3)) / det
        if e < 0:
            continue
        if best is not None and e >= best[0] - 1e-12:
            continue
        if feasible(x, y, e):
            best = (e, x, y)
    return best


def refine(tones: list[float], cand) -> dict | None:
    e0, g0c, g1c, calc, L, mode = cand
    g0, g1 = g0c / CENTS, g1c / CENTS
    try:
        steps = brun3.brun3_levels(1.0, g0, g1, calc)[L]
    except RuntimeError:
        return None
    cons = structure_constraints(1.0, g0, g1, calc, L)
    cons_c = [(a * CENTS, b, c) for a, b, c in cons]     # in cents with x=g0c, y=g1c
    cur = (g0c, g1c)
    assign = None
    for _ in range(REASSIGN_ROUNDS):
        rot = rotated_degrees(steps, cur[0] / CENTS, cur[1] / CENTS, mode)
        new_assign = assignment(rot, tones, cur[0], cur[1])
        if new_assign == assign:
            break
        assign = new_assign
        rows = []
        for t, (a, co) in zip(tones, assign):
            # pitch(t) = (co0 + a)*1200 + co1*g0c + co2*g1c ; error = pitch - t
            rows.append(((co[0] + a) * CENTS - t, float(co[1]), float(co[2])))
        sol = solve_chebyshev(rows, cons_c, (GRID / 4, CENTS - GRID / 4, GRID / 4, CENTS - GRID / 4))
        if sol is None:
            return None
        eps, x, y = sol
        if not (0 < y < x < CENTS):
            return None
        cur = (x, y)
    x, y = cur
    # validate the structure at the solution
    try:
        steps2 = brun3.brun3_levels(1.0, x / CENTS, y / CENTS, calc)[L]
    except RuntimeError:
        return None
    if steps2 != steps:
        return None
    rot = rotated_degrees(steps, x / CENTS, y / CENTS, mode)
    assign = assignment(rot, tones, x, y)
    errs = [abs(((co[0] + a) * CENTS + co[1] * x + co[2] * y) - t) for t, (a, co) in zip(tones, assign)]
    return {"eps": max(errs), "g0_cents": x, "g1_cents": y, "calc": calc, "level": L, "mode": mode,
            "steps": steps, "assign": assign, "errs": errs, "grid_eps": e0}


# ---------------------------------------------------------------------------
# structure of a fit: val, kernel, scores
# ---------------------------------------------------------------------------


def int_solve(rows: list[list[int]], rhs: list[int]) -> list[int] | None:
    """Unique integer solution x of rows·x = rhs (Fraction elimination), or None."""
    m, n = len(rows), len(rows[0])
    A = [[Fraction(v) for v in r] + [Fraction(b)] for r, b in zip(rows, rhs)]
    rank, piv = 0, []
    for c in range(n):
        p = next((r for r in range(rank, m) if A[r][c] != 0), None)
        if p is None:
            continue
        A[rank], A[p] = A[p], A[rank]
        pv = A[rank][c]
        A[rank] = [v / pv for v in A[rank]]
        for r in range(m):
            if r != rank and A[r][c] != 0:
                f = A[r][c]
                A[r] = [a - f * b for a, b in zip(A[r], A[rank])]
        piv.append(c)
        rank += 1
    if any(A[r][n] != 0 for r in range(rank, m)) or rank < n:
        return None
    x = [Fraction(0)] * n
    for i, c in enumerate(piv):
        x[c] = A[i][n]
    if any(v.denominator != 1 for v in x):
        return None
    return [int(v) for v in x]


def val_of(tones: tuple[Fraction, ...], assign) -> dict | None:
    mz = [monzo(t) for t in tones]
    used = [i for i in range(len(PRIMES)) if any(m[1][i] for m in mz)]
    rows = [[m[1][i] for i in used] for m in mz]
    out = {}
    for name, idx in (("octave", 0), ("g0", 1), ("g1", 2)):
        rhs = []
        for (e2, _), (a, co) in zip(mz, assign):
            v = (co[0] + a) if idx == 0 else co[idx]
            rhs.append(v - e2 if idx == 0 else v)
        sol = int_solve(rows, rhs)
        if sol is None:
            return None
        out[name] = sol
    return {"primes": [PRIMES[i] for i in used], **out}


def kernel_of(val: dict) -> list[dict]:
    primes = val["primes"]
    box = [KERNEL_BOX[p] for p in primes]
    out = []

    def rec(i, es):
        if i == len(primes):
            if all(e == 0 for e in es):
                return
            if sum(e * v for e, v in zip(es, val["g0"])) or sum(e * v for e, v in zip(es, val["g1"])):
                return
            e2 = -sum(e * v for e, v in zip(es, val["octave"]))
            r = Fraction(2) ** e2
            for e, p in zip(es, primes):
                r *= Fraction(p) ** e
            if r < 1:
                return
            c = CENTS * log2(r)
            if c >= KERNEL_CENTS_MAX or r.numerator * r.denominator > KERNEL_HEIGHT_MAX:
                return
            out.append({"comma": f"{r.numerator}/{r.denominator}", "cents": c, "monzo": [e2] + list(es)})
            return
        for e in range(-box[i], box[i] + 1):
            rec(i + 1, es + [e])

    rec(0, [])
    out.sort(key=lambda d: d["cents"])
    return out[:6]


def fit_row(name: str, tones: tuple[Fraction, ...], tc: list[float], f: dict, rr_table) -> dict:
    x, y = f["g0_cents"], f["g1_cents"]
    rot = rotated_degrees(f["steps"], x / CENTS, y / CENTS, f["mode"])
    scale = sorted(pc for pc, _ in rot)
    fitted_pc = [((co[0] + a) * CENTS + co[1] * x + co[2] * y) % CENTS for a, co in f["assign"]]
    val = val_of(tones, f["assign"])
    ker = kernel_of(val) if val else []
    full = score_tempered(scale, EPS_LOCK)
    mel = score_melodic(scale)
    image = {str(e): score_tempered(fitted_pc, e) for e in EPS_IMAGE}
    devs = c1.triad_deviations(tones, fitted_pc)
    sizes = brun3.step_sizes(f["steps"], 1.0, x / CENTS, y / CENTS, tol=1e-6)
    return {
        "experiment": EXPERIMENT, "lattice": name, "N": len(scale),
        "eps_star_cents": f["eps"], "grid_eps_cents": f["grid_eps"],
        "g0_cents": x, "g1_cents": y, "calc": f["calc"], "level": f["level"], "mode": f["mode"],
        "steps": [list(s) for s in f["steps"]], "step_sizes_cents": sizes, "step_classes": len(sizes),
        "assignment": [[a, list(co)] for a, co in f["assign"]], "tone_errors_cents": f["errs"],
        "homomorphic": val is not None, "val": val, "kernel": ker,
        "chain_P_2c": full.proportional, "chain_S_2c": full.subcontrary, "chain_G_2c": full.geometric,
        "chain_m1_gap_classes": mel.gap_entropy.gap_class_count,
        "chain_m2_cs_violations": mel.constant_structure.violations,
        "chain_m3_propriety": mel.propriety.classification,
        "image_P": {e: r.proportional for e, r in image.items()},
        "image_S": {e: r.subcontrary for e, r in image.items()},
        "exact_triads": len(devs),
        "survival_2c_frozen": image["2.0"].proportional + image["2.0"].subcontrary,
        "survival_2c_mirror": sum(1 for d in devs if d["dev_cents"] < EPS_LOCK and d["sep_cents"] >= EPS_LOCK),
        "max_triad_dev_cents": max((d["dev_cents"] for d in devs), default=0.0),
        "triad_deviations": devs,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION, "epsilon_cents": EPS_LOCK,
    }


def run_lattice(name: str, tones: tuple[Fraction, ...], rr_table) -> list[dict]:
    tc = [c1.cents_of(t) for t in tones]
    cands = stage1(tc)
    skipped = cands.pop(-1, 0)
    rows = []
    for n in sorted(cands):
        fits = []
        for cand in cands[n]:
            f = refine(tc, cand)
            if f is not None:
                fits.append(f)
        if not fits:
            continue
        fits.sort(key=lambda f: (round(f["eps"], 9), f["g0_cents"], f["g1_cents"], f["calc"], f["level"], f["mode"]))
        best = fits[0]
        row = fit_row(name, tones, tc, best, rr_table)
        row["n_candidates"] = len(cands[n])
        row["n_refined"] = len(fits)
        row["grid_pairs_skipped_degenerate"] = skipped
        row["runners_up"] = [{"eps": f["eps"], "g0_cents": f["g0_cents"], "g1_cents": f["g1_cents"],
                              "calc": f["calc"], "level": f["level"], "mode": f["mode"]} for f in fits[1:4]]
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def _by_n(rows):
    return {r["N"]: r for r in rows}


def _check_table(rows, table, label):
    tol = PREDICTIONS["tol_cents"]
    by = _by_n(rows)
    fails = []
    for n, v in table.items():
        if not isinstance(n, int):
            continue
        err, comma, surv = v
        r = by.get(n)
        if r is None:
            fails.append(f"{label} N={n}: no fit")
            continue
        if r["eps_star_cents"] > err + tol:
            fails.append(f"{label} N={n}: eps {r['eps_star_cents']:.3f} > {err}")
        if not r["kernel"] or r["kernel"][0]["comma"] != comma:
            fails.append(f"{label} N={n}: comma {r['kernel'][0]['comma'] if r['kernel'] else None} != {comma}")
        if r["survival_2c_frozen"] < surv:
            fails.append(f"{label} N={n}: survival {r['survival_2c_frozen']} < {surv}")
    return fails


def verdict_p_r1(by_lat):
    p = PREDICTIONS["P-R1"]
    rows = by_lat["hexany"]
    fails = _check_table(rows, p, "hexany")
    within = [r["N"] for r in rows if r["eps_star_cents"] <= 2.0]
    full = [r["N"] for r in rows if r["survival_2c_frozen"] == r["exact_triads"]]
    if (within[0] if within else None) != p["first_within_2c"]:
        fails.append(f"hexany first within 2c {within[:1]} != {p['first_within_2c']}")
    if (full[0] if full else None) != p["first_full"]:
        fails.append(f"hexany first full {full[:1]} != {p['first_full']}")
    return {"kept": not fails, "failures": fails, "first_within_2c": within[:1], "first_full": full[:1]}


def verdict_p_r2(by_lat):
    p = PREDICTIONS["P-R2"]
    rows = by_lat["eg4"]
    fails = _check_table(rows, p, "eg4")
    full = [r["N"] for r in rows if r["survival_2c_frozen"] == r["exact_triads"]]
    if (full[0] if full else None) != p["first_full"]:
        fails.append(f"eg4 first full {full[:1]} != {p['first_full']}")
    return {"kept": not fails, "failures": fails, "first_full": full[:1]}


def verdict_p_r3(by_lat):
    p = PREDICTIONS["P-R3"]
    rows = by_lat["dek52"]
    fails = _check_table(rows, p, "dek52")
    r = _by_n(rows).get(29)
    if r is None or abs(r["g0_cents"] - p["N29_g0"]) > p["g_tol"] or abs(r["g1_cents"] - p["N29_g1"]) > p["g_tol"]:
        fails.append(f"dek52 N=29 generators off registration: {r and (r['g0_cents'], r['g1_cents'])}")
    return {"kept": not fails, "failures": fails}


def verdict_p_r4(by_lat):
    p = PREDICTIONS["P-R4"]
    rows = [r for r in by_lat["eikosany"] if r["N"] <= p["N_max"]]
    fails = []
    best = min(rows, key=lambda r: r["eps_star_cents"]) if rows else None
    if any(r["eps_star_cents"] <= p["min_err_floor"] for r in rows):
        fails.append("eikosany: some scale within 10c")
    if best is None or abs(best["eps_star_cents"] - p["best_err_about"]) > p["best_err_tol"] or best["N"] != p["best_N"]:
        fails.append(f"eikosany best {best and (best['N'], round(best['eps_star_cents'], 2))} != (31, ~12)")
    if any(r["survival_2c_frozen"] > p["survival_max"] for r in rows):
        fails.append("eikosany: survival above 29")
    return {"kept": not fails, "failures": fails,
            "best": best and {"N": best["N"], "eps": best["eps_star_cents"], "survival": best["survival_2c_frozen"]}}


def verdict_p_r5(by_lat):
    fails = []
    for lat, key in (("hexany", "P-R1"), ("eg4", "P-R2"), ("dek52", "P-R3")):
        by = _by_n(by_lat[lat])
        for n in [k for k in PREDICTIONS[key] if isinstance(k, int)]:
            r = by.get(n)
            if r is None:
                continue
            if not r["homomorphic"]:
                fails.append(f"{lat} N={n}: not a val")
            elif len(r["kernel"]) != 1:
                fails.append(f"{lat} N={n}: {len(r['kernel'])} kernel commas in the box, expected 1")
    return {"kept": not fails, "failures": fails}


def verdict_p_r6(by_lat):
    p = PREDICTIONS["P-R6"]
    fails = []
    by = _by_n(by_lat["hexany"])
    for r in by_lat["hexany"]:
        if r["eps_star_cents"] <= 3.0 and r["level"] != p["within_3c_level"]:
            fails.append(f"hexany N={r['N']}: within 3c at level {r['level']}")
    for n, calc in p["calc_at"].items():
        r = by.get(n)
        if r is None or r["calc"] != calc:
            fails.append(f"hexany N={n}: calc {r and r['calc']} != {calc}")
    return {"kept": not fails, "failures": fails}


# ---------------------------------------------------------------------------
# scl + main
# ---------------------------------------------------------------------------

SCL_PICKS = (("hexany", 19), ("hexany", 21), ("dek52", 29))


def write_scl(by_lat) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for lat, n in SCL_PICKS:
        r = _by_n(by_lat.get(lat, [])).get(n)
        if r is None:
            continue
        rot = rotated_degrees([tuple(s) for s in r["steps"]], r["g0_cents"] / CENTS, r["g1_cents"] / CENTS, r["mode"])
        name = f"rank3001_{lat}_N{n:02d}_g{r['g0_cents']:.2f}_{r['g1_cents']:.2f}"
        text = c1.scl_text(name, f"RANK3-001 {lat} Brun3 scale {r['calc']} level {r['level']} mode {r['mode']}, "
                           f"G0 = {r['g0_cents']:.3f}c, G1 = {r['g1_cents']:.3f}c; largest tone error "
                           f"{r['eps_star_cents']:.3f}c; 1/1 = degree 0", [pc for pc, _ in rot])
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def main() -> dict:
    by_lat = {name: run_lattice(name, tones, None) for name, tones in LATTICES.items()}
    rows = [r for rs in by_lat.values() for r in rs]
    verdicts = {"P-R1": verdict_p_r1(by_lat), "P-R2": verdict_p_r2(by_lat), "P-R3": verdict_p_r3(by_lat),
                "P-R4": verdict_p_r4(by_lat), "P-R5": verdict_p_r5(by_lat), "P-R6": verdict_p_r6(by_lat)}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": RANK3001_VERSION,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "grid_cents": GRID, "levels": list(LEVELS), "topk": TOPK, "epsilon_lock_cents": EPS_LOCK,
        "lattices": {k: [str(t) for t in v] for k, v in LATTICES.items()},
        "n_rows": len(rows),
        "staircase": {lat: [{"N": r["N"], "eps": r["eps_star_cents"], "g0": r["g0_cents"], "g1": r["g1_cents"],
                             "calc": r["calc"], "level": r["level"], "mode": r["mode"],
                             "comma": r["kernel"][0]["comma"] if r["kernel"] else None,
                             "survival_2c": r["survival_2c_frozen"], "exact_triads": r["exact_triads"],
                             "step_classes": r["step_classes"]} for r in rs] for lat, rs in by_lat.items()},
        "verdicts": verdicts, "scl_files": write_scl(by_lat),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  melodic {receipt['melodic_version']}  rows={receipt['n_rows']}")
    for lat, st in receipt["staircase"].items():
        for r in st:
            print(f"  {lat:8s} N={r['N']:2d} eps={r['eps']:6.2f} g0={r['g0']:8.3f} g1={r['g1']:8.3f} {r['calc']} L{r['level']} "
                  f"m{r['mode']:2d} comma={r['comma']} surv={r['survival_2c']}/{r['exact_triads']} steps={r['step_classes']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
