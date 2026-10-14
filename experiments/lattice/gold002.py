"""GOLD-002 — Erv's hand-found generators against the nearest golden and
silver generators, with a null model (LOG.md pre-registration 2026-10-13;
committed before this file).

Is "optimize proportional and subcontrary triads and you land near a noble
number" a law? Nobles are dense, so nearness is measured against the
nearness of a random generator at the same complexity. A golden generator
is (a + phi c)/(b + phi d) for a unimodular pair a/b, c/d (|bc - ad| = 1),
silver uses 1 + sqrt(2); its COMPLEXITY is the smallest max(b, d) over the
pairs that generate it. Ladder Q = 8, 12, 20, 30, 60. Null: 20000 uniform
generators on (0, 0.5], seed 20261013. Generators: MERU-001's sixteen
recurrence roots plus phi. Chain triads: frozen P + S at 2 cents of the
N-chain of each generator and of its nearest golden (Q = 60) at that
golden generator's MOS levels up to 41. Predictions P-G2-1..P-G2-4 are
pinned in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)

Receipts: results/gold002.jsonl (one row per generator) +
results/gold002_summary.json. Stdlib only, deterministic (seeded random),
no wall-clock fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 gold002.py
"""

from __future__ import annotations

import json
import random
import sys
from bisect import bisect_left
from math import gcd, log2
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
import meru001 as m1  # noqa: E402
from scorer import SCORER_VERSION, score_tempered  # noqa: E402

GOLD002_VERSION = "1.0.0"
EXPERIMENT = "GOLD-002"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "gold002.jsonl"
SUMMARY = RESULTS_DIR / "gold002_summary.json"

CENTS = 1200.0
EPS_LOCK = 2.0
Q_LADDER = (8, 12, 20, 30, 60)
Q_MAX = 60
NULL_N = 20000
NULL_SEED = 20261013
TAIL = 0.10
LEVEL_MAX = 41
LEVEL_MIN = 5
PHI = (1 + 5 ** 0.5) / 2

PREDICTIONS = {
    "tol_cents": 0.01,
    "P-G2-1": {"golden_median": {8: 8.58, 12: 4.21, 20: 1.52, 30: 0.71, 60: 0.18},
               "golden_p10": {8: 1.35, 12: 0.66, 20: 0.24, 30: 0.11, 60: 0.027},
               "silver_median": {8: 5.54, 12: 2.69, 20: 0.97, 30: 0.45, 60: 0.11}, "tol": 0.02},
    "P-G2-2": {"golden_tail": {8: ["erv418935", "metameantone", "silver414", "fib", "phi"],
                               12: ["metameantone", "fib", "metapelog", "fit351", "phi"],
                               20: ["erv418935", "silver414", "erv773743"],
                               30: ["metaslendro", "erv773743"],
                               60: ["metaslendro", "metaptolemy", "erv773743", "pell"]},
               "silver_tail_counts": {8: 4, 12: 5, 20: 6, 30: 4, 60: 4},
               "max_tail": 6},
    "P-G2-3": {20: {"erv418935": -0.12, "erv238186": -1.23, "fig12_12": -10.58, "erv415227": -1.02,
                    "metameantone": -0.58, "silver414": 0.16, "fib": -0.65, "metapelog": 0.31,
                    "metaslendro": 2.74, "metaptolemy": 3.60, "erv59178": -0.30, "llsls": -2.74,
                    "metaslendro2": -2.72, "erv773743": 0.00, "pell": -1.92, "fit351": -0.45, "phi": -0.65},
               60: {"erv418935": 0.09, "erv238186": 0.61, "fig12_12": -0.17, "erv415227": 0.07,
                    "metameantone": 0.11, "silver414": -0.08, "fib": 0.07, "metapelog": 0.12,
                    "metaslendro": 0.02, "metaptolemy": -0.02, "erv59178": 0.17, "llsls": -0.19,
                    "metaslendro2": -0.05, "erv773743": 0.00, "pell": -0.01, "fit351": 0.11, "phi": 0.07},
               "erv418935_Q60_seeds": "18/43,13/31"},
    "P-G2-4": {"erv_wins": {"erv418935": (31, 212, 190), "erv238186": (25, 138, 94), "fig12_12": (40, 364, 314),
                            "metameantone": (31, 156, 140), "fib": (36, 366, 264), "metaslendro": (37, 404, 380),
                            "metaptolemy": (38, 400, 354), "llsls": (38, 396, 390), "phi": (36, 366, 264)},
               "golden_wins": {"erv415227": (41, 492, 494), "silver414": (41, 302, 372), "metapelog": (29, 100, 152),
                               "erv59178": (27, 128, 154), "metaslendro2": (36, 308, 326), "fit351": (41, 634, 652)},
               "ties": {"erv773743": 31, "pell": 37}, "tie_level_max": 12},
}


# ---------------------------------------------------------------------------
# nobles
# ---------------------------------------------------------------------------


def metallic(m: int) -> float:
    return (m + (m * m + 4) ** 0.5) / 2


def nobles(m: int, Q: int = Q_MAX) -> list[tuple[float, str, int]]:
    """(g, seeds, complexity) for every noble with complexity <= Q, g folded to
    (0, 0.5] (g and 1 - g make the same chains), sorted by g."""
    mu = metallic(m)
    out: dict[float, tuple[float, str, int]] = {}
    for b in range(1, Q + 1):
        for d in range(1, Q + 1):
            for a in range(0, b + 1):
                if gcd(a, b) != 1:
                    continue
                for sgn in (1, -1):
                    num = a * d + sgn
                    if num % b:
                        continue
                    c = num // b
                    if c < 0 or c > d or gcd(c, d) != 1:
                        continue
                    for (x0, x1), (y0, y1) in (((a, b), (c, d)), ((c, d), (a, b))):
                        g = (x0 + mu * y0) / (x1 + mu * y1)
                        if g > 0.5:
                            g = 1 - g
                        if g <= 0 or g > 0.5:
                            continue
                        key = round(g, 9)
                        cx = max(x1, y1)
                        if key not in out or cx < out[key][2]:
                            out[key] = (g, f"{x0}/{x1},{y0}/{y1}", cx)
    return sorted(out.values())


def levels_of(g: float, max_n: int = LEVEL_MAX) -> list[int]:
    lo, hi = (0, 1), (1, 1)
    out = []
    for _ in range(200):
        m = (lo[0] + hi[0], lo[1] + hi[1])
        if m[1] > max_n:
            break
        out.append(m[1])
        if g < m[0] / m[1]:
            hi = m
        else:
            lo = m
    return out


def fold(g: float) -> float:
    return g if g <= 0.5 else 1.0 - g


def nearest(cands: list[tuple[float, str, int]], g: float, Q: int) -> tuple[float, str, int]:
    return min((c for c in cands if c[2] <= Q), key=lambda c: abs(c[0] - g))


# ---------------------------------------------------------------------------
# null model
# ---------------------------------------------------------------------------


def null_distances(cands: list[tuple[float, str, int]], Q: int, gs: list[float]) -> list[float]:
    xs = sorted(c[0] for c in cands if c[2] <= Q)
    out = []
    for g in gs:
        i = bisect_left(xs, g)
        out.append(min(abs(g - xs[j]) for j in (i - 1, i) if 0 <= j < len(xs)) * CENTS)
    out.sort()
    return out


def percentile(sorted_ds: list[float], d: float) -> float:
    return bisect_left(sorted_ds, abs(d)) / len(sorted_ds)


# ---------------------------------------------------------------------------
# generators and chains
# ---------------------------------------------------------------------------


def erv_generators() -> list[dict]:
    out = []
    for rid, a, i, b, j, label in m1.RECURRENCES:
        big_g = c1.positive_root(j, i, a, b)
        out.append({"id": rid, "g01": log2(big_g) % 1.0, "label": label,
                    "source": f"MERU-001 table: H[n] = {a}H[n-{i}] + {b}H[n-{j}]"})
    out.append({"id": "phi", "g01": 0.694241913631, "label": "phi 0.694242 (Fig 12 entry 1)",
                "source": "MOS-fit playground GEN_PRESETS"})
    return out


def chain_ps(gc: float, n: int) -> int:
    r = score_tempered([c1.wrap(k * gc) for k in range(n)], EPS_LOCK)
    return r.proportional + r.subcontrary


def run() -> tuple[list[dict], dict]:
    fams = {"golden": nobles(1), "silver": nobles(2)}
    rng = random.Random(NULL_SEED)
    null_g = [rng.uniform(1e-6, 0.5) for _ in range(NULL_N)]
    null = {(fam, q): null_distances(c, q, null_g) for fam, c in fams.items() for q in Q_LADDER}
    null_summary = {f"{fam}_Q{q}": {"n_candidates": sum(1 for c in fams[fam] if c[2] <= q),
                                    "median_dist_cents": null[(fam, q)][NULL_N // 2],
                                    "p10_dist_cents": null[(fam, q)][NULL_N // 10]}
                    for fam in fams for q in Q_LADDER}
    rows = []
    for gen in erv_generators():
        f = fold(gen["g01"])
        row = {"experiment": EXPERIMENT, **gen, "g_cents": gen["g01"] * CENTS, "folded01": f,
               "levels": levels_of(f)}
        for fam, cands in fams.items():
            ladder = {}
            for q in Q_LADDER:
                ng, seeds, cx = nearest(cands, f, q)
                d = (ng - f) * CENTS
                ladder[str(q)] = {"g_cents": ng * CENTS, "seeds": seeds, "complexity": cx, "dist_cents": d,
                                  "null_percentile": percentile(null[(fam, q)], d), "in_tail": percentile(null[(fam, q)], d) <= TAIL}
            ng, seeds, cx = nearest(cands, f, Q_MAX)
            lv = [n for n in levels_of(ng) if n >= LEVEL_MIN]
            comp = [{"N": n, "erv_PS_2c": chain_ps(f * CENTS, n), "noble_PS_2c": chain_ps(ng * CENTS, n)} for n in lv]
            row[fam] = {"by_Q": ladder, "nearest_Q60": {"g_cents": ng * CENTS, "seeds": seeds, "complexity": cx,
                                                          "dist_cents": (ng - f) * CENTS},
                        "levels": lv, "chain_PS_2c": comp}
        rows.append(row)
    return rows, null_summary


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def verdict_p_g2_1(null_summary: dict) -> dict:
    p = PREDICTIONS["P-G2-1"]
    fails = []
    for q in Q_LADDER:
        g = null_summary[f"golden_Q{q}"]
        s = null_summary[f"silver_Q{q}"]
        if abs(g["median_dist_cents"] - p["golden_median"][q]) > p["tol"]:
            fails.append(f"golden Q{q} median {g['median_dist_cents']:.3f} != {p['golden_median'][q]}")
        if abs(g["p10_dist_cents"] - p["golden_p10"][q]) > p["tol"]:
            fails.append(f"golden Q{q} p10 {g['p10_dist_cents']:.3f} != {p['golden_p10'][q]}")
        if abs(s["median_dist_cents"] - p["silver_median"][q]) > p["tol"]:
            fails.append(f"silver Q{q} median {s['median_dist_cents']:.3f} != {p['silver_median'][q]}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g2_2(rows: list[dict]) -> dict:
    p = PREDICTIONS["P-G2-2"]
    fails, tails = [], {}
    for q in Q_LADDER:
        gt = [r["id"] for r in rows if r["golden"]["by_Q"][str(q)]["in_tail"]]
        st = [r["id"] for r in rows if r["silver"]["by_Q"][str(q)]["in_tail"]]
        tails[q] = {"golden": gt, "silver": st}
        if gt != p["golden_tail"][q]:
            fails.append(f"golden Q{q} tail {gt} != {p['golden_tail'][q]}")
        if len(st) != p["silver_tail_counts"][q]:
            fails.append(f"silver Q{q} tail count {len(st)} != {p['silver_tail_counts'][q]}")
        if max(len(gt), len(st)) > p["max_tail"]:
            fails.append(f"Q{q}: more than {p['max_tail']} in the tail")
    strong_law = any(len(t["golden"]) > len(rows) / 2 or len(t["silver"]) > len(rows) / 2 for t in tails.values())
    return {"kept": not fails, "failures": fails, "tails": tails, "strong_law_holds": strong_law}


def verdict_p_g2_3(rows: list[dict]) -> dict:
    p = PREDICTIONS["P-G2-3"]
    tol = PREDICTIONS["tol_cents"]
    fails = []
    for r in rows:
        for q in (20, 60):
            d = r["golden"]["by_Q"][str(q)]["dist_cents"]
            if abs(d - p[q][r["id"]]) > tol:
                fails.append(f"{r['id']} Q{q}: {d:+.3f} != {p[q][r['id']]:+.2f}")
    r = next(x for x in rows if x["id"] == "erv418935")
    if r["golden"]["nearest_Q60"]["seeds"] != p["erv418935_Q60_seeds"]:
        fails.append(f"erv418935 Q60 seeds {r['golden']['nearest_Q60']['seeds']}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g2_4(rows: list[dict]) -> dict:
    p = PREDICTIONS["P-G2-4"]
    fails = []
    for r in rows:
        comp = r["golden"]["chain_PS_2c"]
        deepest = comp[-1]
        got = (deepest["N"], deepest["erv_PS_2c"], deepest["noble_PS_2c"])
        if r["id"] in p["erv_wins"]:
            want = p["erv_wins"][r["id"]]
            if got != want or not got[1] > got[2]:
                fails.append(f"{r['id']}: {got} != erv win {want}")
        elif r["id"] in p["golden_wins"]:
            want = p["golden_wins"][r["id"]]
            if got != want or not got[1] < got[2]:
                fails.append(f"{r['id']}: {got} != golden win {want}")
        elif r["id"] in p["ties"]:
            if got[0] != p["ties"][r["id"]] or got[1] != got[2]:
                fails.append(f"{r['id']}: {got} != tie at {p['ties'][r['id']]}")
        else:
            fails.append(f"{r['id']}: unregistered")
        for c in comp:
            if c["N"] <= p["tie_level_max"] and c["erv_PS_2c"] != c["noble_PS_2c"]:
                fails.append(f"{r['id']} N={c['N']}: shallow level not a tie")
    return {"kept": not fails, "failures": fails}


def main() -> dict:
    rows, null_summary = run()
    verdicts = {"P-G2-1": verdict_p_g2_1(null_summary), "P-G2-2": verdict_p_g2_2(rows),
                "P-G2-3": verdict_p_g2_3(rows), "P-G2-4": verdict_p_g2_4(rows)}
    receipt = {"experiment": EXPERIMENT, "runner_version": GOLD002_VERSION, "scorer_version": SCORER_VERSION,
               "epsilon_lock_cents": EPS_LOCK, "Q_ladder": list(Q_LADDER), "null_n": NULL_N, "null_seed": NULL_SEED,
               "tail": TAIL, "n_generators": len(rows), "null": null_summary,
               "table": [{"id": r["id"], "g_cents": r["g_cents"],
                          "golden_by_Q": {q: (v["dist_cents"], v["null_percentile"]) for q, v in r["golden"]["by_Q"].items()},
                          "silver_by_Q": {q: (v["dist_cents"], v["null_percentile"]) for q, v in r["silver"]["by_Q"].items()},
                          "deepest_golden_level": r["golden"]["chain_PS_2c"][-1]} for r in rows],
               "verdicts": verdicts}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  generators={receipt['n_generators']}")
    for q in Q_LADDER:
        n = receipt["null"][f"golden_Q{q}"]
        print(f"  null golden Q{q}: {n['n_candidates']} candidates, median {n['median_dist_cents']:.2f}c, p10 {n['p10_dist_cents']:.3f}c")
    for t in receipt["table"]:
        print(f"  {t['id']:13s} {t['g_cents']:8.3f}  " + "  ".join(f"Q{q}:{t['golden_by_Q'][str(q)][0]:+6.2f}/p{t['golden_by_Q'][str(q)][1]:.2f}" for q in Q_LADDER)
              + f"  deepest {t['deepest_golden_level']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  strong law holds: {receipt['verdicts']['P-G2-2']['strong_law_holds']}")
    print(f"  receipts: {RESULTS}, {SUMMARY}")


if __name__ == "__main__":
    _print_summary(main())
