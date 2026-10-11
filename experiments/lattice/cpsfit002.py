"""CPSFIT-002 — triad-minimax chain fit of a CPS field (LOG.md
pre-registration 2026-10-10; committed before this file).

Program B, the objective. CPSFIT-001 minimized the largest TONE error of
the lattice to an N-note generator chain and found that triad survival at
the LOCK tier is not monotone in tone error. Here the objective is the
largest deviation of any exact lattice TRIAD re-voiced in the chain (the
mirror's mean-condition deviation), subject to every tone sitting within
20 cents of a chain degree. Candidate assignments are enumerated on a
0.5-cent grid of g, each refined by golden-section search around its best
grid point; ties break toward the smaller tone error. Everything else
(homomorphism, kernel, MOS flag, frozen chain scores, frozen image
survival, nearest recurrences) is CPSFIT-001's machinery, imported.
Predictions P-T1..P-T5 are pinned in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered via cpsfit001)
  experiments/lattice/melodic.py v0.1.0  (score_melodic via cpsfit001)
CPSFIT-001's receipts (results/cpsfit001.jsonl) are read for the
tone-minimax comparison; they are not recomputed.

Receipts: results/cpsfit002.jsonl (one row per lattice x feasible N) +
results/cpsfit002_summary.json; results/scl/cpsfit002/*.scl ear-check
stimuli. Deterministic: stdlib only, no randomness, no wall-clock fields;
two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 cpsfit002.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
from scorer import SCORER_VERSION  # noqa: E402  (frozen v1.1.0, read-only)
from melodic import MELODIC_VERSION  # noqa: E402  (frozen v0.1.0, read-only)

CPSFIT002_VERSION = "1.0.0"
EXPERIMENT = "CPSFIT-002"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "cpsfit002.jsonl"
SUMMARY = RESULTS_DIR / "cpsfit002_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "cpsfit002"
PRIOR = RESULTS_DIR / "cpsfit001.jsonl"

CENTS = 1200.0
N_MIN, N_MAX = 5, 48
TONE_CAP = 20.0
GRID = 0.5
G_MAX = 600.0
GOLDEN_STEPS = 70
EPS_LOCK = 2.0
TIE_EPS = 1e-6

PREDICTIONS = {
    "P-T1": {
        "tol_dev": 0.05, "tol_g": 0.1,
        "hexany": [((11, 11), 17.92, 249.55), ((12, 12), 17.03, 318.93), ((13, 14), 7.95, 490.09),
                   ((15, 15), 5.14, 503.19), ((16, 21), 2.43, 116.59), ((22, 30), 1.156, 193.91),
                   ((31, 47), 0.305, 77.195), ((48, 48), 0.295, 582.45)],
        "ptolemy7": [((7, 11), 10.13, 506.25), ((12, 35), 0.257, 498.25), ((36, 36), 0.112, 565.99)],
        "eg4": [((12, 12), 22.97, 249.74), ((13, 14), 8.60, 490.36), ((15, 15), 7.95, 163.37),
                ((16, 17), 3.91, 116.34), ((18, 22), 3.69, 77.91), ((23, 23), 1.595, 193.31),
                ((24, 30), 1.349, 193.88), ((31, 48), 0.331, 77.191)],
        "infeasible_below": {"hexany": 11, "ptolemy7": 7, "eg4": 12},
    },
    "P-T2": {"first_full": {"hexany": 22, "eg4": 23, "ptolemy7": 12},
             "hexany_22": {"g": 193.908, "tone_err": 2.22, "prior_g": 193.787, "prior_eps": 1.367},
             "eg4_23": {"mapping": (-15, 2, 5), "tone_err": 3.88},
             "dominates_from_N": 15},
    "P-T3": {"hexany": {(11, 11): (-2, -8, -1), (12, 12): (6, 5, 3), (13, 14): (-1, -9, 2),
                        (15, 15): (-1, -4, -10), (16, 21): (6, -7, -2), (22, 30): (16, 2, 5),
                        (31, 47): (-22, 5, -3)},
             "nonhomomorphic": {"hexany": [48]}},
    "P-T4": {"hexany_11_frozen_below": 8, "ptolemy_7_prior_g": 502.346},
    "P-T5": {"N": 15, "min_P_2c": 11, "recurrence": (1, 1, 32, 4)},
}


# ---------------------------------------------------------------------------
# triads and the objective
# ---------------------------------------------------------------------------


def prep_triads(tones: tuple[Fraction, ...]) -> list[tuple[str, list[tuple[int, float]]]]:
    """Each exact lattice triad as (kind, [(tone index, exact cents of the
    voiced member)...]) so the deviation can be re-evaluated cheaply."""
    idx = {c1._reduce(t): i for i, t in enumerate(tones)}
    out = []
    for lab, a, b, m in c1.exact_triads(tones):
        out.append((lab, [(idx[c1._reduce(x)], c1.cents_of(x)) for x in (a, b, m)]))
    return out


def triad_devs(triads, pc: list[float]) -> list[tuple[float, float]]:
    """(deviation, AM-HM separation) in cents for every triad, voiced in the fit."""
    res = []
    for lab, mem in triads:
        v = [pc[i] + CENTS * round((cx - pc[i]) / CENTS) for i, cx in mem]
        fa, fb, fc = (2 ** (x / CENTS) for x in v)
        am, hm = (fa + fc) / 2, 2 * fa * fc / (fa + fc)
        d = abs(c1.cents_of(fb / am)) if lab == "P" else abs(c1.cents_of(fb / hm))
        res.append((d, c1.cents_of(am / hm)))
    return res


def tone_err(tc: list[float], ks: tuple[int, ...], g: float) -> float:
    return max(c1.circ(k * g, t) for k, t in zip(ks, tc))


def objective(triads, tc: list[float], ks: tuple[int, ...], g: float) -> float:
    if tone_err(tc, ks, g) > TONE_CAP:
        return float("inf")
    pc = [c1.wrap(k * g) for k in ks]
    return max(d for d, _ in triad_devs(triads, pc))


def assignments(tc: list[float], n: int, g: float) -> dict[tuple[int, ...], int]:
    """Distinct nearest-degree assignments over every window of N
    consecutive k containing 0, with every tone within TONE_CAP; maps the
    assignment to the smallest window start that produces it."""
    big = n - 1
    cand = [[(k, c1.circ(k * g, t)) for k in range(-big, big + 1) if c1.circ(k * g, t) <= TONE_CAP]
            for t in tc]
    out: dict[tuple[int, ...], int] = {}
    for s in range(-big, 1):
        ks = []
        for lst in cand:
            best = None
            for k, e in lst:
                if s <= k <= s + big and (best is None or e < best[1] or (e == best[1] and abs(k) < abs(best[0]))):
                    best = (k, e)
            if best is None:
                ks = None
                break
            ks.append(best[0])
        if ks and tuple(ks) not in out:
            out[tuple(ks)] = s
    return out


def golden(f, a: float, b: float, steps: int = GOLDEN_STEPS) -> tuple[float, float]:
    r = 0.6180339887498949
    x1, x2 = b - r * (b - a), a + r * (b - a)
    f1, f2 = f(x1), f(x2)
    for _ in range(steps):
        if f1 < f2:
            b, x2, f2 = x2, x1, f1
            x1 = b - r * (b - a)
            f1 = f(x1)
        else:
            a, x1, f1 = x1, x2, f2
            x2 = a + r * (b - a)
            f2 = f(x2)
    x = (a + b) / 2
    return x, f(x)


def fit_triads(tones: tuple[Fraction, ...], n: int) -> dict | None:
    """Triad-minimax fit for one N: the assignment and generator minimizing
    the largest triad deviation under the tone cap; None if infeasible."""
    tc = [c1.cents_of(t) for t in tones]
    triads = prep_triads(tones)
    best_grid: dict[tuple[int, ...], tuple[float, float, int]] = {}
    steps = int(round((G_MAX - 1.0) / GRID))
    for i in range(steps + 1):
        g = 1.0 + i * GRID
        for ks, s in assignments(tc, n, g).items():
            obj = objective(triads, tc, ks, g)
            cur = best_grid.get(ks)
            if cur is None or obj < cur[0]:
                best_grid[ks] = (obj, g, s)
    cands = []
    for ks, (obj0, g0, s) in best_grid.items():
        gx, fx = golden(lambda x, ks=ks: objective(triads, tc, ks, x),
                        max(1e-6, g0 - GRID), min(G_MAX, g0 + GRID))
        if fx == float("inf"):
            continue
        cands.append((fx, tone_err(tc, ks, gx), gx, s, ks))
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1], t[2]))
    fx, te, gx, s, ks = cands[0]
    near = [{"dev": d, "tone_err": e, "g": g, "ks": list(k),
             "homomorphic": c1.homomorphism(tones, list(k), n) is not None}
            for d, e, g, _, k in cands if d - fx <= 0.01]
    return {"N": n, "eps": te, "g": gx, "s": s, "ks": list(ks),
            "errs": [c1.circ(k * gx, t) for k, t in zip(ks, tc)],
            "objective_dev_cents": fx, "n_assignments": len(best_grid),
            "near_optimal": near}


# ---------------------------------------------------------------------------
# rows, prior, verdicts
# ---------------------------------------------------------------------------


def load_prior() -> dict[tuple[str, int], dict]:
    out = {}
    if not PRIOR.exists():
        return out
    with PRIOR.open() as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("kind") == "chain":
                out[(r["lattice"], r["N"])] = r
    return out


def run_lattice(name: str, tones: tuple[Fraction, ...], rr_table: list[dict],
                prior: dict) -> list[dict]:
    rows = []
    for n in range(N_MIN, N_MAX + 1):
        f = fit_triads(tones, n)
        if f is None:
            continue
        row = c1.fit_row(name, tones, [c1.cents_of(t) for t in tones], f, "triad", rr_table)
        row["experiment"] = EXPERIMENT
        row["objective_dev_cents"] = f["objective_dev_cents"]
        row["objective_matches_mirror"] = abs(f["objective_dev_cents"] - row["max_triad_dev_cents"]) < 1e-6
        row["tone_cap_cents"] = TONE_CAP
        row["n_assignments"] = f["n_assignments"]
        row["near_optimal"] = f["near_optimal"]
        p = prior.get((name, n))
        row["prior_tone_minimax"] = None if p is None else {
            "g_cents": p["g_cents"], "eps_star_cents": p["eps_star_cents"],
            "max_triad_dev_cents": p["max_triad_dev_cents"],
            "survival_2c_frozen": p["survival_2c_frozen"], "mapping": p["mapping"]}
        rows.append(row)
    return rows


def _stair_lookup(table, n):
    for (lo, hi), dev, g in table:
        if lo <= n <= hi:
            return dev, g
    return None


def verdict_p_t1(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-T1"]
    fails = []
    for lat, rows in by_lat.items():
        feasible = sorted(r["N"] for r in rows)
        if feasible and feasible[0] != p["infeasible_below"][lat]:
            fails.append(f"{lat}: first feasible N {feasible[0]} != {p['infeasible_below'][lat]}")
        for r in rows:
            reg = _stair_lookup(p[lat], r["N"])
            if reg is None:
                continue
            dev, g = reg
            if abs(r["objective_dev_cents"] - dev) > p["tol_dev"]:
                fails.append(f"{lat} N={r['N']}: dev {r['objective_dev_cents']:.3f} != {dev}")
            if abs(r["g_cents"] - g) > p["tol_g"]:
                fails.append(f"{lat} N={r['N']}: g {r['g_cents']:.3f} != {g}")
    return {"kept": not fails, "failures": fails}


def verdict_p_t2(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-T2"]
    fails, firsts = [], {}
    for lat, rows in by_lat.items():
        full = [r["N"] for r in rows if r["survival_2c_frozen"] == r["exact_triads"]]
        firsts[lat] = full[0] if full else None
        if firsts[lat] != p["first_full"][lat]:
            fails.append(f"{lat}: first full survival N {firsts[lat]} != {p['first_full'][lat]}")
        for r in rows:
            pr = r["prior_tone_minimax"]
            if pr and r["N"] >= p["dominates_from_N"] and r["survival_2c_frozen"] < pr["survival_2c_frozen"]:
                fails.append(f"{lat} N={r['N']}: survival {r['survival_2c_frozen']} < tone-minimax {pr['survival_2c_frozen']}")
    h22 = next((r for r in by_lat.get("hexany", []) if r["N"] == 22), None)
    if h22:
        if abs(h22["g_cents"] - p["hexany_22"]["g"]) > 0.1 or abs(h22["eps_star_cents"] - p["hexany_22"]["tone_err"]) > 0.05:
            fails.append(f"hexany N=22: g {h22['g_cents']:.3f} / tone err {h22['eps_star_cents']:.3f} off registration")
    e23 = next((r for r in by_lat.get("eg4", []) if r["N"] == 23), None)
    if e23 and (tuple(e23["mapping"] or ()) != p["eg4_23"]["mapping"] or abs(e23["eps_star_cents"] - p["eg4_23"]["tone_err"]) > 0.05):
        fails.append(f"eg4 N=23: mapping {e23['mapping']} / tone err {e23['eps_star_cents']:.3f} off registration")
    return {"kept": not fails, "failures": fails, "first_full": firsts}


def verdict_p_t3(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-T3"]
    fails = []
    for r in by_lat.get("hexany", []):
        n = r["N"]
        reg = next((m for (lo, hi), m in p["hexany"].items() if lo <= n <= hi), None)
        if reg is not None:
            if not r["homomorphic"] or tuple(r["mapping"]) != reg:
                fails.append(f"hexany N={n}: mapping {r['mapping']} != {reg}")
        elif n in p["nonhomomorphic"]["hexany"]:
            if r["homomorphic"]:
                fails.append(f"hexany N={n}: registered non-homomorphic, got {r['mapping']}")
    return {"kept": not fails, "failures": fails}


def verdict_p_t4(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-T4"]
    fails = []
    h11 = next((r for r in by_lat.get("hexany", []) if r["N"] == 11), None)
    if h11 is None or h11["survival_2c_frozen"] >= p["hexany_11_frozen_below"]:
        fails.append(f"hexany N=11: frozen survival {h11 and h11['survival_2c_frozen']} not below {p['hexany_11_frozen_below']}")
    p7 = next((r for r in by_lat.get("ptolemy7", []) if r["N"] == 7), None)
    if p7 is None or p7["prior_tone_minimax"] is None or p7["survival_2c_frozen"] >= p7["prior_tone_minimax"]["survival_2c_frozen"]:
        fails.append(f"ptolemy7 N=7: frozen survival {p7 and p7['survival_2c_frozen']} not below tone-minimax {p7 and p7['prior_tone_minimax'] and p7['prior_tone_minimax']['survival_2c_frozen']}")
    return {"kept": not fails, "failures": fails,
            "hexany_11": h11 and {"survival": h11["survival_2c_frozen"], "prior": h11["prior_tone_minimax"]},
            "ptolemy_7": p7 and {"survival": p7["survival_2c_frozen"], "prior": p7["prior_tone_minimax"]}}


def verdict_p_t5(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-T5"]
    r = next((x for x in by_lat.get("hexany", []) if x["N"] == p["N"]), None)
    fails = []
    if r is None:
        fails.append("hexany N=15 missing")
    else:
        if r["chain_P_2c"] < p["min_P_2c"]:
            fails.append(f"hexany N=15: chain P@2c {r['chain_P_2c']} < {p['min_P_2c']}")
        a, i, b, j = p["recurrence"]
        if not any((x["a"], x["i"], x["b"], x["j"]) == (a, i, b, j) and x["pow2"] and x["in_octave"]
                   for x in r["nearest_recurrences"]):
            fails.append("hexany N=15: Erv's recurrence not within 2c of the fit")
    return {"kept": not fails, "failures": fails,
            "row": r and {"g": r["g_cents"], "P_2c": r["chain_P_2c"], "nearest": r["nearest_recurrences"]}}


# ---------------------------------------------------------------------------
# scl + main
# ---------------------------------------------------------------------------


def write_scl(by_lat: dict[str, list[dict]]) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for r in by_lat.get("hexany", []):
        if r["N"] != 22:
            continue
        chain = [c1.wrap(k * r["g_cents"]) for k in range(r["window_start"], r["window_start"] + r["N"])]
        name = f"cpsfit002_hexany_N22_g{r['g_cents']:.3f}"
        text = c1.scl_text(name, f"CPSFIT-002 hexany triad-minimax chain, N = 22, g = {r['g_cents']:.3f}c; "
                           f"all 12 hexany triads within {EPS_LOCK}c; 1/1 = chain degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def main() -> dict:
    rr_table = c1.build_rr_table()
    prior = load_prior()
    by_lat = {name: run_lattice(name, tones, rr_table, prior) for name, tones in c1.LATTICES.items()}
    rows = [r for rows in by_lat.values() for r in rows]
    verdicts = {
        "P-T1": verdict_p_t1(by_lat), "P-T2": verdict_p_t2(by_lat), "P-T3": verdict_p_t3(by_lat),
        "P-T4": verdict_p_t4(by_lat), "P-T5": verdict_p_t5(by_lat),
    }
    receipt = {
        "experiment": EXPERIMENT, "runner_version": CPSFIT002_VERSION,
        "cpsfit001_version": c1.CPSFIT001_VERSION,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "tone_cap_cents": TONE_CAP, "grid_cents": GRID,
        "N_range": [N_MIN, N_MAX], "prior_rows": len(prior),
        "lattices": {k: [str(t) for t in v] for k, v in c1.LATTICES.items()},
        "n_rows": len(rows),
        "objective_mirror_failures": sum(1 for r in rows if not r["objective_matches_mirror"]),
        "staircase": {lat: [{"N": r["N"], "dev": r["objective_dev_cents"], "g": r["g_cents"],
                             "tone_err": r["eps_star_cents"], "mapping": r["mapping"],
                             "mos": r["is_mos"], "survival_2c": r["survival_2c_frozen"],
                             "exact_triads": r["exact_triads"], "chain_P_2c": r["chain_P_2c"],
                             "prior_survival_2c": r["prior_tone_minimax"] and r["prior_tone_minimax"]["survival_2c_frozen"]}
                            for r in rs] for lat, rs in by_lat.items()},
        "verdicts": verdicts, "scl_files": write_scl(by_lat),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  melodic {receipt['melodic_version']}  "
          f"rows={receipt['n_rows']}  objective/mirror failures={receipt['objective_mirror_failures']}")
    for lat, st in receipt["staircase"].items():
        last = None
        for r in st:
            key = (round(r["dev"], 3), round(r["g"], 2))
            if key == last:
                continue
            last = key
            print(f"  {lat:9s} N={r['N']:2d} dev={r['dev']:7.3f} g={r['g']:8.3f} tone={r['tone_err']:6.2f} "
                  f"surv={r['survival_2c']}/{r['exact_triads']} (tone-minimax {r['prior_survival_2c']}) "
                  f"map={r['mapping']} mos={r['mos']} P2c={r['chain_P_2c']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
