"""GOLD-001 — golden and silver generator families scored by triad survival
against the free count optimum, per note count, on a complexity ladder,
with and without the MOS-level constraint (LOG.md pre-registration
2026-10-13; committed before this file).

For each lattice (hexany, EG4, dekany CPS(5,2){1,3,5,7,9}, and the
eikosany's 42 embedded subsets from SUBSET-MEL-000) and each N: the free
count optimum (CPSFIT-003 receipt, or cpsfit003.fit_count for subsets),
the free optimum restricted to MOS levels (CPSFIT-003's count segments
intersected with the exact level intervals of N), the best golden and
silver candidate by count at each complexity Q (any N, and level-only),
and the nearest candidate to the free generator at each Q with its count.
Candidates and complexity come from gold002.nobles. Survival is the mirror
predicate (|dev| < 2c, separation >= 2c); the frozen score_tempered count
of the image is reported beside it. Predictions P-G1-1..P-G1-8 are pinned
in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)
  experiments/lattice/melodic.py v0.1.0  (not used here)

Receipts: results/gold001.jsonl (one row per lattice x N) +
results/gold001_summary.json; results/scl/gold001/*.scl. Stdlib only
(multiprocessing), deterministic, no wall-clock fields; two runs must be
bit-identical.

Run from experiments/lattice/:  python3.12 gold001.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from math import gcd
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
import cpsfit002 as c2  # noqa: E402
import cpsfit003 as c3  # noqa: E402
import gold002 as g2  # noqa: E402
import subsetmel000 as sm  # noqa: E402
from scorer import SCORER_VERSION, score_tempered  # noqa: E402
from families.cps import cps_scale  # noqa: E402

GOLD001_VERSION = "1.0.0"
EXPERIMENT = "GOLD-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "gold001.jsonl"
SUMMARY = RESULTS_DIR / "gold001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "gold001"
PRIOR_003 = RESULTS_DIR / "cpsfit003.jsonl"

CENTS = 1200.0
EPS_LOCK = 2.0
TONE_CAP = c3.TONE_CAP
Q_LADDER = g2.Q_LADDER
Q_MAX = g2.Q_MAX
N_RANGE_MAIN = (11, 36)
N_RANGE_SUBSET = (11, 24)
EIKOSANY_SEEDS = (1, 3, 5, 7, 9, 11)
SUBSET_KINDS = ("hexany", "dekany_in", "dekany_out")
WORKERS = 8
KEY_ROUND = 6

PREDICTIONS = {
    "P-G1-1": {"golden60_equals_free_except": [16, 17], "golden60_at_16_17": 8,
               "golden_le20_value": 8, "golden_le20_from_N": 12,
               "golden8": {(15, 31): 4, (32, 36): 5},
               "free_12_15": {"g": 317.175, "count": 8, "complexity": 11, "seeds": "3/11,1/4", "dist_tol": 0.01}},
    "P-G1-2": {"silver20_10_N": (18, 28), "silver20_12_from": 29, "silver60_12_from": 22, "silver_beats_golden_le20_from": 16},
    "P-G1-3": {"golden_level_12_N": [25, 31], "golden_level_12_g": 193.993, "golden_level_le20_max": 8,
               "free_mos_lower": {15: 8, 19: 8, 25: 12, 31: 12}},
    "P-G1-4": {"q60_keeps_free_N": (11, 30), "q60_dist_max": 0.1, "q60_31_36_count": 4, "q20_keeps_free_N": (12, 15)},
    "P-G1-5": {"golden60_equals_free_N": [12, 13, 14, 15, 36],
               "golden60_values": {(16, 22): 16, (23, 23): 20, (24, 35): 22},
               "silver60_equals_free_N": [12, 13, 14, 15] + list(range(24, 37)),
               "golden_level_22_N": [25, 31], "golden_level_never": 24},
    "P-G1-6": {"beaten_N": (13, 18), "beaten_count": 16, "golden60_values": {(19, 24): 22, (25, 25): 25, (26, 30): 27, (31, 32): 29, (33, 34): 34, (35, 36): 34},
               "silver20_values": {(23, 24): 25, (33, 34): 34, (35, 36): 37}, "silver20_26_32_min": 27, "silver20_ge_golden60_from": 23},
    "P-G1-7": {"hexany": {"cells": 408, "golden60": 339, "silver60": 369, "golden20": 172, "silver20_ge_golden20": 354,
                          "full_free": 165, "full_golden60": 128, "full_silver20": 85},
               "dekany": {"cells": 124, "golden60": 59, "golden20": 11, "silver20_ge_golden20": 97}, "tol": 3},
}


# ---------------------------------------------------------------------------
# lattices
# ---------------------------------------------------------------------------


def lattices() -> list[tuple[str, str, tuple[Fraction, ...], tuple[int, int]]]:
    out = [("hexany", "main", c1.LATTICES["hexany"], N_RANGE_MAIN),
           ("eg4", "main", c1.LATTICES["eg4"], N_RANGE_MAIN),
           ("dek52", "main", cps_scale((1, 3, 5, 7, 9), 2), N_RANGE_MAIN)]
    for s in sm.enumerate_subsets(EIKOSANY_SEEDS):
        if s.kind in SUBSET_KINDS:
            out.append((s.name, s.kind, s.tones, N_RANGE_SUBSET))
    return out


def load_prior() -> dict[tuple[str, int], dict]:
    out = {}
    if PRIOR_003.exists():
        for line in PRIOR_003.open():
            r = json.loads(line)
            out[(r["lattice"], r["N"])] = r
    return out


# ---------------------------------------------------------------------------
# levels: the exact g-intervals on which N is a scale-tree level
# ---------------------------------------------------------------------------


def level_intervals(n: int) -> list[tuple[float, float]]:
    """Open intervals (in octaves, within (0, 0.5]) of g for which N is a level:
    between Farey neighbours p/q < p'/q' with q + q' = N, folded to (0, 0.5]."""
    fr = sorted({(p, q) for q in range(1, n) for p in range(0, q + 1) if gcd(p, q) == 1},
                key=lambda x: Fraction(x[0], x[1]))
    out = []
    for (p, q), (p2, q2) in zip(fr, fr[1:]):
        if q + q2 != n:
            continue
        a, b = p / q, p2 / q2
        for lo, hi in ((a, b), (1 - b, 1 - a)):
            lo2, hi2 = max(lo, 0.0), min(hi, 0.5)
            if lo2 < hi2:
                out.append((lo2, hi2))
    out.sort()
    return out


def is_level(n: int, g01: float) -> bool:
    return n in g2.levels_of(g01, max_n=max(n, 2))


# ---------------------------------------------------------------------------
# counts
# ---------------------------------------------------------------------------


def best_window(tc: list[float], triads, gc: float, n: int):
    """Best window of the N-chain of gc: (count, tone_err, s, ks) or None (cap)."""
    best = None
    for s in range(-(n - 1), 1):
        ks, errs = [], []
        ok = True
        for t in tc:
            k = min(range(s, s + n), key=lambda k: (c1.circ(k * gc, t), abs(k)))
            e = c1.circ(k * gc, t)
            if e > TONE_CAP:
                ok = False
                break
            ks.append(k)
            errs.append(e)
        if not ok:
            continue
        pc = [c1.wrap(k * gc) for k in ks]
        cnt = sum(1 for d, sp in c2.triad_devs(triads, pc) if d < EPS_LOCK and sp >= EPS_LOCK)
        key = (-cnt, round(max(errs), KEY_ROUND), s)
        if best is None or key < best[0]:
            best = (key, cnt, max(errs), s, ks)
    return None if best is None else best[1:]


def frozen_image(ks, gc: float) -> int:
    r = score_tempered([c1.wrap(k * gc) for k in ks], EPS_LOCK)
    return r.proportional + r.subcontrary


def fit_count_mos(tones: tuple[Fraction, ...], n: int) -> dict | None:
    """CPSFIT-003's count fit restricted to generators for which N is a level."""
    tc = [c1.cents_of(t) for t in tones]
    triads = c2.prep_triads(tones)
    ivs = [(lo * CENTS, hi * CENTS) for lo, hi in level_intervals(n)]
    seen: dict[tuple[int, ...], float] = {}
    steps = int(round((c3.G_MAX - 1.0) / c3.GRID))
    for i in range(steps + 1):
        g = 1.0 + i * c3.GRID
        for ks in c2.assignments(tc, n, g):
            seen.setdefault(ks, g)
    best = None
    for ks, g0 in seen.items():
        b = c3.basin(tc, ks, g0)
        if b is None:
            continue
        lo, hi = b
        voiced = c3.voiced_offsets(triads, tc, ks, (lo + hi) / 2)
        for c, a, bb in c3.count_segments(voiced, lo, hi):
            for ilo, ihi in ivs:
                a2, b2 = max(a, ilo), min(bb, ihi)
                if b2 - a2 < c3.W_MIN:
                    continue
                gx, margin = c3.representative(voiced, a2, b2)
                te = c2.tone_err(tc, ks, gx)
                key = (-c, -round(margin, KEY_ROUND), round(te, KEY_ROUND), round(gx, KEY_ROUND))
                if best is None or key < best[0]:
                    best = (key, c, margin, te, gx, ks)
    if best is None:
        return None
    _, c, margin, te, gx, ks = best
    return {"count": c, "margin": margin, "tone_err": te, "g": gx, "ks": list(ks),
            "mode": -c3.window_range(ks, n)[0], "frozen": frozen_image(ks, gx)}


# ---------------------------------------------------------------------------
# one (lattice, N) row
# ---------------------------------------------------------------------------

_FAMS: dict[str, list] = {}


def _fams():
    if not _FAMS:
        _FAMS["golden"] = g2.nobles(1)
        _FAMS["silver"] = g2.nobles(2)
    return _FAMS


def row_task(args) -> dict:
    name, kind, tones, n, prior = args
    tc = [c1.cents_of(t) for t in tones]
    triads = c2.prep_triads(tones)
    fams = _fams()
    row = {"experiment": EXPERIMENT, "lattice": name, "kind": kind, "N": n, "exact_triads": len(triads),
           "tones": [str(t) for t in tones]}
    # free optimum
    if prior is not None:
        free = {"count": prior["count_exact"], "g": prior["g_cents"], "source": "cpsfit003 receipt",
                "frozen": prior["survival_2c_frozen"]}
    else:
        f = c3.fit_count(tones, n)
        free = None if f is None else {"count": f["count"], "g": f["g"], "source": "fit_count",
                                       "frozen": frozen_image(f["ks"], f["g"])}
    row["free"] = free
    fm = fit_count_mos(tones, n)
    row["free_mos"] = fm
    best_noble = None
    for fam, cands in fams.items():
        best = {q: None for q in Q_LADDER}
        best_lv = {q: None for q in Q_LADDER}
        for g, seeds, cx in cands:
            gc = g * CENTS
            r = best_window(tc, triads, gc, n)
            if r is None:
                continue
            cnt, te, s, ks = r
            lv = is_level(n, g)
            key = (-cnt, round(te, KEY_ROUND), round(gc, KEY_ROUND))
            rec = {"count": cnt, "tone_err": te, "g": gc, "seeds": seeds, "complexity": cx, "mode": -s,
                   "is_level": lv, "ks": list(ks)}
            for q in Q_LADDER:
                if cx > q:
                    continue
                if best[q] is None or key < best[q][0]:
                    best[q] = (key, rec)
                if lv and (best_lv[q] is None or key < best_lv[q][0]):
                    best_lv[q] = (key, rec)
            if best_noble is None or key < best_noble[0]:
                best_noble = (key, rec)
        for q in Q_LADDER:
            for d in (best, best_lv):
                if d[q] is not None:
                    d[q][1]["frozen"] = frozen_image(d[q][1]["ks"], d[q][1]["g"])
        row[fam + "_by_Q"] = {str(q): (best[q][1] if best[q] else None) for q in Q_LADDER}
        row[fam + "_level_only_by_Q"] = {str(q): (best_lv[q][1] if best_lv[q] else None) for q in Q_LADDER}
        if free is not None:
            fg01 = g2.fold(free["g"] / CENTS)
            near = {}
            for q in Q_LADDER:
                g, seeds, cx = g2.nearest(cands, fg01, q)
                r = best_window(tc, triads, g * CENTS, n)
                near[str(q)] = {"g": g * CENTS, "dist_cents": (g - fg01) * CENTS, "seeds": seeds, "complexity": cx,
                                "count": r[0] if r else None, "tone_err": r[1] if r else None}
            row[fam + "_nearest_to_free_by_Q"] = near
    if free is not None and best_noble is not None and best_noble[1]["count"] > free["count"]:
        row["free_beaten_by_noble"] = {"count": best_noble[1]["count"], "g": best_noble[1]["g"],
                                       "receipt_count": free["count"]}
        row["free_effective_count"] = best_noble[1]["count"]
    else:
        row["free_beaten_by_noble"] = None
        row["free_effective_count"] = None if free is None else free["count"]
    return row


def run_all() -> list[dict]:
    prior = load_prior()
    tasks = []
    for name, kind, tones, (lo, hi) in lattices():
        for n in range(lo, hi + 1):
            tasks.append((name, kind, tones, n, prior.get((name, n))))
    with Pool(WORKERS) as pool:
        rows = pool.map(row_task, tasks, chunksize=2)
    return rows


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def _by(rows, name):
    return {r["N"]: r for r in rows if r["lattice"] == name}


def _cnt(x):
    return None if x is None else x["count"]


def _in(table, n):
    for (lo, hi), v in table.items():
        if lo <= n <= hi:
            return v
    return None


def verdict_p_g1_1(rows):
    p = PREDICTIONS["P-G1-1"]
    by = _by(rows, "hexany")
    fails = []
    for n, r in by.items():
        f = r["free_effective_count"]
        g60 = _cnt(r["golden_by_Q"]["60"])
        if n in p["golden60_equals_free_except"]:
            if g60 != p["golden60_at_16_17"] or g60 == f:
                fails.append(f"N={n}: golden60 {g60} vs free {f}")
        elif g60 != f:
            fails.append(f"N={n}: golden60 {g60} != free {f}")
        if n >= p["golden_le20_from_N"] and _cnt(r["golden_by_Q"]["20"]) != p["golden_le20_value"]:
            fails.append(f"N={n}: golden20 {_cnt(r['golden_by_Q']['20'])} != {p['golden_le20_value']}")
        want8 = _in(p["golden8"], n)
        if want8 is not None and _cnt(r["golden_by_Q"]["8"]) != want8:
            fails.append(f"N={n}: golden8 {_cnt(r['golden_by_Q']['8'])} != {want8}")
    q = p["free_12_15"]
    for n in range(12, 16):
        r = by[n]
        near = r["golden_nearest_to_free_by_Q"]["12"]
        if abs(r["free"]["g"] - q["g"]) > 0.01 or r["free"]["count"] != q["count"] \
                or abs(near["dist_cents"]) > q["dist_tol"] or near["complexity"] != q["complexity"]:
            fails.append(f"N={n}: free optimum not the complexity-11 golden ({near})")
    return {"kept": not fails, "failures": fails}


def verdict_p_g1_2(rows):
    p = PREDICTIONS["P-G1-2"]
    by = _by(rows, "hexany")
    fails = []
    for n, r in by.items():
        s20, g20, s60 = _cnt(r["silver_by_Q"]["20"]), _cnt(r["golden_by_Q"]["20"]), _cnt(r["silver_by_Q"]["60"])
        if p["silver20_10_N"][0] <= n <= p["silver20_10_N"][1] and s20 != 10:
            fails.append(f"N={n}: silver20 {s20} != 10")
        if n >= p["silver20_12_from"] and s20 != 12:
            fails.append(f"N={n}: silver20 {s20} != 12")
        if n >= p["silver60_12_from"] and s60 != 12:
            fails.append(f"N={n}: silver60 {s60} != 12")
        if n >= p["silver_beats_golden_le20_from"] and not (s20 or 0) > (g20 or 0):
            fails.append(f"N={n}: silver20 {s20} does not beat golden20 {g20}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g1_3(rows):
    p = PREDICTIONS["P-G1-3"]
    by = _by(rows, "hexany")
    fails = []
    twelve = [n for n, r in by.items() if _cnt(r["golden_level_only_by_Q"]["60"]) == 12]
    if twelve != p["golden_level_12_N"]:
        fails.append(f"golden level-only 12 at {twelve} != {p['golden_level_12_N']}")
    for n in p["golden_level_12_N"]:
        g = by[n]["golden_level_only_by_Q"]["60"]
        if g is None or abs(g["g"] - p["golden_level_12_g"]) > 0.02:
            fails.append(f"N={n}: golden level-only g {g and g['g']} != {p['golden_level_12_g']}")
    for n, r in by.items():
        if (_cnt(r["golden_level_only_by_Q"]["20"]) or 0) > p["golden_level_le20_max"]:
            fails.append(f"N={n}: golden level-only Q20 above {p['golden_level_le20_max']}")
    for n, lower in p["free_mos_lower"].items():
        fm = by[n]["free_mos"]
        if fm is None or fm["count"] < lower:
            fails.append(f"N={n}: free MOS-only {fm and fm['count']} < {lower}")
    return {"kept": not fails, "failures": fails,
            "free_mos": {n: (r["free_mos"] and (r["free_mos"]["count"], round(r["free_mos"]["g"], 3))) for n, r in by.items()}}


def verdict_p_g1_4(rows):
    p = PREDICTIONS["P-G1-4"]
    by = _by(rows, "hexany")
    fails = []
    for n, r in by.items():
        f = r["free_effective_count"]
        n60 = r["golden_nearest_to_free_by_Q"]["60"]
        n20 = r["golden_nearest_to_free_by_Q"]["20"]
        if p["q60_keeps_free_N"][0] <= n <= p["q60_keeps_free_N"][1]:
            if n60["count"] != f or abs(n60["dist_cents"]) > p["q60_dist_max"]:
                fails.append(f"N={n}: nearest golden Q60 {n60['count']} at {n60['dist_cents']:+.3f}c")
        elif n60["count"] != p["q60_31_36_count"]:
            fails.append(f"N={n}: nearest golden Q60 count {n60['count']} != {p['q60_31_36_count']}")
        keeps20 = n20["count"] == f
        if keeps20 != (p["q20_keeps_free_N"][0] <= n <= p["q20_keeps_free_N"][1]):
            fails.append(f"N={n}: nearest golden Q20 keeps free = {keeps20}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g1_5(rows):
    p = PREDICTIONS["P-G1-5"]
    by = _by(rows, "eg4")
    fails = []
    eq60 = [n for n, r in by.items() if _cnt(r["golden_by_Q"]["60"]) == r["free_effective_count"]]
    if eq60 != p["golden60_equals_free_N"]:
        fails.append(f"golden60 equals free at {eq60}")
    for n, r in by.items():
        want = _in(p["golden60_values"], n)
        if want is not None and _cnt(r["golden_by_Q"]["60"]) != want:
            fails.append(f"N={n}: golden60 {_cnt(r['golden_by_Q']['60'])} != {want}")
    eqs = [n for n, r in by.items() if _cnt(r["silver_by_Q"]["60"]) == r["free_effective_count"]]
    if eqs != p["silver60_equals_free_N"]:
        fails.append(f"silver60 equals free at {eqs}")
    lv22 = [n for n, r in by.items() if _cnt(r["golden_level_only_by_Q"]["60"]) == 22]
    if lv22 != p["golden_level_22_N"] or any(_cnt(r["golden_level_only_by_Q"]["60"]) == p["golden_level_never"] for r in by.values()):
        fails.append(f"golden level-only 22 at {lv22}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g1_6(rows):
    p = PREDICTIONS["P-G1-6"]
    by = _by(rows, "dek52")
    fails = []
    for n in range(p["beaten_N"][0], p["beaten_N"][1] + 1):
        r = by[n]
        if r["free_effective_count"] < p["beaten_count"] or (r["free"] is not None and r["free_beaten_by_noble"] is None and r["free"]["count"] < p["beaten_count"]):
            fails.append(f"N={n}: free effective {r['free_effective_count']} < {p['beaten_count']}")
    for n, r in by.items():
        want = _in(p["golden60_values"], n)
        if want is not None and _cnt(r["golden_by_Q"]["60"]) != want:
            fails.append(f"N={n}: golden60 {_cnt(r['golden_by_Q']['60'])} != {want}")
        want = _in(p["silver20_values"], n)
        if want is not None and _cnt(r["silver_by_Q"]["20"]) != want:
            fails.append(f"N={n}: silver20 {_cnt(r['silver_by_Q']['20'])} != {want}")
        if 26 <= n <= 32 and (_cnt(r["silver_by_Q"]["20"]) or 0) < p["silver20_26_32_min"]:
            fails.append(f"N={n}: silver20 below {p['silver20_26_32_min']}")
        if n >= p["silver20_ge_golden60_from"] and (_cnt(r["silver_by_Q"]["20"]) or 0) < (_cnt(r["golden_by_Q"]["60"]) or 0):
            fails.append(f"N={n}: silver20 < golden60")
    return {"kept": not fails, "failures": fails}


def _aggregate(rows, kinds):
    agg = {"cells": 0, "golden60": 0, "silver60": 0, "golden20": 0, "silver20_ge_golden20": 0,
           "full_free": 0, "full_golden60": 0, "full_silver20": 0}
    for r in rows:
        if r["kind"] not in kinds or r["free"] is None:
            continue
        f = r["free_effective_count"]
        agg["cells"] += 1
        g60, s60, g20, s20 = (_cnt(r["golden_by_Q"]["60"]), _cnt(r["silver_by_Q"]["60"]),
                              _cnt(r["golden_by_Q"]["20"]), _cnt(r["silver_by_Q"]["20"]))
        agg["golden60"] += (g60 or -1) >= f
        agg["silver60"] += (s60 or -1) >= f
        agg["golden20"] += (g20 or -1) >= f
        agg["silver20_ge_golden20"] += (s20 if s20 is not None else -1) >= (g20 if g20 is not None else -1)
        agg["full_free"] += f == r["exact_triads"]
        agg["full_golden60"] += g60 == r["exact_triads"]
        agg["full_silver20"] += s20 == r["exact_triads"]
    return agg


def verdict_p_g1_7(rows):
    p = PREDICTIONS["P-G1-7"]
    fails = []
    hx = _aggregate(rows, ("hexany",))
    dk = _aggregate(rows, ("dekany_in", "dekany_out"))
    for key, want in p["hexany"].items():
        if abs(hx[key] - want) > p["tol"]:
            fails.append(f"hexany subsets {key} {hx[key]} != {want}")
    for key, want in p["dekany"].items():
        if abs(dk[key] - want) > p["tol"]:
            fails.append(f"dekany subsets {key} {dk[key]} != {want}")
    return {"kept": not fails, "failures": fails, "hexany_subsets": hx, "dekany_subsets": dk}


def verdict_p_g1_8(rows):
    fails = []
    for lat in ("hexany", "eg4", "dek52"):
        by = _by(rows, lat)
        ns = [n for n, r in by.items() if r["free"] is not None]
        g20_loses = sum(1 for n in ns if (_cnt(by[n]["golden_by_Q"]["20"]) or 0) < by[n]["free_effective_count"])
        s_ge_g = sum(1 for n in ns if (_cnt(by[n]["silver_by_Q"]["20"]) or 0) >= (_cnt(by[n]["golden_by_Q"]["20"]) or 0))
        mos_lt = sum(1 for n in ns if by[n]["free_mos"] is None or by[n]["free_mos"]["count"] < by[n]["free_effective_count"])
        if not g20_loses > len(ns) / 2:
            fails.append(f"{lat}: golden Q20 loses at only {g20_loses}/{len(ns)}")
        if not s_ge_g > len(ns) / 2:
            fails.append(f"{lat}: silver Q20 >= golden Q20 at only {s_ge_g}/{len(ns)}")
        if not mos_lt > len(ns) / 2:
            fails.append(f"{lat}: MOS-only free below free at only {mos_lt}/{len(ns)}")
    return {"kept": not fails, "failures": fails}


# ---------------------------------------------------------------------------
# scl + main
# ---------------------------------------------------------------------------


def write_scl(rows) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    by = _by(rows, "hexany")
    picks = []
    r15 = by.get(15)
    if r15 and r15["golden_by_Q"]["12"]:
        picks.append(("golden_c11_N15", r15["golden_by_Q"]["12"], 15, "golden complexity-11 generator (3/11, 1/4), 15-note level"))
    r29 = by.get(29)
    if r29 and r29["silver_by_Q"]["20"]:
        picks.append(("silver_Q20_N29", r29["silver_by_Q"]["20"], 29, "silver generator of complexity <= 20, 29-note chain"))
    for tag, rec, n, desc in picks:
        s = -rec["mode"]
        chain = [c1.wrap(k * rec["g"]) for k in range(s, s + n)]
        name = f"gold001_hexany_{tag}_g{rec['g']:.3f}"
        text = c1.scl_text(name, f"GOLD-001 hexany, {desc}, g = {rec['g']:.3f}c, mode {rec['mode']}, "
                           f"{rec['count']} of 12 triads within {EPS_LOCK}c, tone error {rec['tone_err']:.2f}c; 1/1 = degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def main() -> dict:
    rows = run_all()
    rows.sort(key=lambda r: (r["kind"] != "main", r["lattice"], r["N"]))
    verdicts = {"P-G1-1": verdict_p_g1_1(rows), "P-G1-2": verdict_p_g1_2(rows), "P-G1-3": verdict_p_g1_3(rows),
                "P-G1-4": verdict_p_g1_4(rows), "P-G1-5": verdict_p_g1_5(rows), "P-G1-6": verdict_p_g1_6(rows),
                "P-G1-7": verdict_p_g1_7(rows), "P-G1-8": verdict_p_g1_8(rows)}
    beaten = [{"lattice": r["lattice"], "N": r["N"], **r["free_beaten_by_noble"]} for r in rows if r["free_beaten_by_noble"]]
    receipt = {
        "experiment": EXPERIMENT, "runner_version": GOLD001_VERSION, "scorer_version": SCORER_VERSION,
        "cpsfit003_version": c3.CPSFIT003_VERSION, "gold002_version": g2.GOLD002_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "tone_cap_cents": TONE_CAP, "Q_ladder": list(Q_LADDER),
        "n_rows": len(rows), "n_lattices": len({r["lattice"] for r in rows}),
        "receipts_beaten": beaten,
        "staircase": {lat: [{"N": r["N"], "free": r["free_effective_count"], "free_g": r["free"] and r["free"]["g"],
                             "free_mos": r["free_mos"] and r["free_mos"]["count"],
                             "golden_by_Q": {q: _cnt(v) for q, v in r["golden_by_Q"].items()},
                             "golden_level_by_Q": {q: _cnt(v) for q, v in r["golden_level_only_by_Q"].items()},
                             "silver_by_Q": {q: _cnt(v) for q, v in r["silver_by_Q"].items()}}
                            for r in rows if r["lattice"] == lat] for lat in ("hexany", "eg4", "dek52")},
        "subset_aggregates": {"hexany": verdicts["P-G1-7"]["hexany_subsets"], "dekany": verdicts["P-G1-7"]["dekany_subsets"]},
        "verdicts": verdicts, "scl_files": write_scl(rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  rows={receipt['n_rows']}  lattices={receipt['n_lattices']}  "
          f"receipts beaten={len(receipt['receipts_beaten'])}")
    for lat, st in receipt["staircase"].items():
        for r in st:
            print(f"  {lat:7s} N={r['N']:2d} free={r['free']} mos={r['free_mos']} golden {list(r['golden_by_Q'].values())} "
                  f"goldenMOS {list(r['golden_level_by_Q'].values())} silver {list(r['silver_by_Q'].values())}")
    print("  subsets:", receipt["subset_aggregates"])
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
