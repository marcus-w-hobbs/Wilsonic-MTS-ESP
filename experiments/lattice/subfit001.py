"""SUBFIT-001 — one generator chain scored by the eikosany subsets it keeps
fully playable (LOG.md pre-registration 2026-10-14; committed before this
file).

The classic eikosany CPS(6,3){1,3,5,7,9,11} has 20 tones, 114 exact triads
and 72 embedded subsets (SUBSET-MEL-000 census: 30 hexanies, 12 dekanies,
30 tetrads), every subset triad being one of the 114. For each N in 11..72
and each generator g on a 0.1 cent grid (then a 0.002 cent refinement of
the best twelve), every window of N consecutive degrees: each tone goes to
its nearest degree INSIDE the window (no tone cap), a triad survives by the
mirror predicate (|dev| < 2c, separation >= 2c), a subset is playable when
all its triads survive. Objective per N: most playable hexanies + dekanies,
then tetrads, then triads kept, then the smaller largest error among tones
in kept triads. The MOS-only variant restricts g to the exact level
intervals of N (gold001.level_intervals). Predictions P-S1..P-S5 are
pinned in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)

Receipts: results/subfit001.jsonl (one row per N) +
results/subfit001_summary.json; results/scl/subfit001/*.scl. Stdlib only
(multiprocessing over N), deterministic, no wall-clock fields; two runs
must be bit-identical.

Run from experiments/lattice/:  python3.12 subfit001.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from math import log2
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
import cpsfit002 as c2  # noqa: E402
import gold001 as g1  # noqa: E402
import rank3001 as r3  # noqa: E402  (11-limit monzo, int_solve)
import subsetmel000 as sm  # noqa: E402
from scorer import SCORER_VERSION, score_tempered  # noqa: E402
from families.cps import cps_scale  # noqa: E402

SUBFIT001_VERSION = "1.0.0"
EXPERIMENT = "SUBFIT-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "subfit001.jsonl"
SUMMARY = RESULTS_DIR / "subfit001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "subfit001"

CENTS = 1200.0
EPS_LOCK = 2.0
SEEDS = (1, 3, 5, 7, 9, 11)
N_MIN, N_MAX = 11, 72
GRID = 0.1
G_MAX = 600.0
REFINE_TOP = 12
REFINE_STEP = GRID / 50
REFINE_HALF = GRID
WORKERS = 8
KEY_ROUND = 6

PREDICTIONS = {
    "tol_g": 0.05,
    "P-S1": [((11, 11), (1, 0, 1), (16, 16), 500.04), ((12, 12), (1, 0, 1), (17, 17), 566.33),
             ((13, 13), (2, 0, 1), (16, 16), 350.98), ((14, 16), (2, 0, 2), (20, 26), 351.32),
             ((17, 23), (3, 0, 3), (24, 30), 351.32), ((24, 24), (3, 0, 5), (32, 32), 350.76),
             ((25, 25), (4, 0, 4), (52, 52), 271.61), ((26, 34), (6, 1, 7), (39, 43), 350.76),
             ((35, 36), (7, 1, 7), (48, 48), 350.76), ((37, 38), (9, 0, 9), (59, 59), 116.73),
             ((39, 39), (7, 1, 8), (52, 52), 350.76), ((40, 40), (7, 1, 9), (50, 50), 497.77),
             ((41, 44), (8, 1, 10), (73, 73), 339.40), ((45, 48), (12, 2, 12), (84, 84), 339.40),
             ((49, 69), (16, 2, 16), (76, 76), 497.77), ((70, 72), (20, 4, 20), (102, 102), 175.38)],
    "P-S2": {"best_hex": 20, "best_dek": 4, "best_N": 70, "best_triads": 102, "first_dekany_N": 26, "max_hex_before_25": 3},
    "P-S3": {"neutral_third_N": (14, 36), "neutral_third_except": [25], "miracle_N": [37, 38], "miracle_g": 116.73},
    "P-S4": {"levels": {46: (339.40, 12, 0, 82), 53: (497.77, 16, 2, 76), 31: (116.7, 5, None, None), 68: (193.8, 8, 1, None)},
             "free_is_level_N": [46, 53]},
    "P-S5": {"err_14_20": (27.0, 28.5), "err_21_39": (8.0, 10.0), "err_40_up": (4.0, 5.0)},
}


# ---------------------------------------------------------------------------
# the eikosany, its triads and subsets
# ---------------------------------------------------------------------------


def build():
    eik = cps_scale(SEEDS, 3)
    tc = [c1.cents_of(t) for t in eik]
    tri = c2.prep_triads(eik)              # (lab, [(idx, exact cents) * 3])
    key = lambda t: (t[0], c1._reduce(t[1]), c1._reduce(t[2]), c1._reduce(t[3]))
    idx = {key(t): i for i, t in enumerate(c1.exact_triads(eik))}
    subs = sm.enumerate_subsets(SEEDS)
    inc = []
    for s in subs:
        inc.append(sorted(idx[key(t)] for t in c1.exact_triads(s.tones)))
    return eik, tc, tri, subs, inc


EIK, TC, TRI, SUBS, INC = build()
KIND = [s.kind for s in SUBS]
NAMES = [s.name for s in SUBS]
IS_HEX = [k == "hexany" for k in KIND]
IS_DEK = [k in ("dekany_in", "dekany_out") for k in KIND]
IS_TET = [k in ("tetrad_in", "tetrad_out") for k in KIND]


def circ(a: float, b: float) -> float:
    d = abs((a - b) % CENTS)
    return min(d, CENTS - d)


def survival(assign: tuple[int, ...], gc: float) -> list[bool]:
    """Mirror predicate per exact triad, tones voiced at their assigned degrees."""
    pc = [(k * gc) % CENTS for k in assign]
    return [d < EPS_LOCK and sp >= EPS_LOCK for d, sp in c2.triad_devs(TRI, pc)]


def evaluate(gc: float, n: int) -> dict:
    """Best window at (g, N) by the registered lexicographic objective."""
    ks = list(range(-(n - 1), n))
    # per tone: degrees ranked by circular distance (ties: smaller |k|)
    ranked = []
    dist = []
    for t in TC:
        ds = {k: circ(k * gc, t) for k in ks}
        ranked.append(sorted(ks, key=lambda k: (ds[k], abs(k))))
        dist.append(ds)
    best = None
    cache: dict[tuple[int, ...], list[bool]] = {}
    for s in range(-(n - 1), 1):
        lo, hi = s, s + n - 1
        assign = []
        for r in ranked:
            for k in r:
                if lo <= k <= hi:
                    assign.append(k)
                    break
        assign = tuple(assign)
        surv = cache.get(assign)
        if surv is None:
            surv = survival(assign, gc)
            cache[assign] = surv
        kept = sum(surv)
        playable = [all(surv[i] for i in inc) for inc in INC]
        hx = sum(p for p, h in zip(playable, IS_HEX) if h)
        dk = sum(p for p, d in zip(playable, IS_DEK) if d)
        tt = sum(p for p, t in zip(playable, IS_TET) if t)
        in_kept = set()
        for i, ok in enumerate(surv):
            if ok:
                in_kept.update(j for j, _ in TRI[i][1])
        err = max((dist[j][assign[j]] for j in in_kept), default=0.0)
        key = (-(hx + dk), -tt, -kept, round(err, KEY_ROUND), -s)
        if best is None or key < best[0]:
            best = (key, {"hex": hx, "dek": dk, "tet": tt, "triads": kept, "mode": -s, "max_err_kept": err,
                          "assign": list(assign), "playable": [NAMES[j] for j, p in enumerate(playable) if p]})
    out = best[1]
    out["g"] = gc
    return out


def rank_key(r: dict):
    return (-(r["hex"] + r["dek"]), -r["tet"], -r["triads"], round(r["max_err_kept"], KEY_ROUND), round(r["g"], KEY_ROUND))


def search_n(n: int) -> dict:
    ivs = g1.level_intervals(n)
    in_level = lambda gc: any(lo < gc / CENTS < hi for lo, hi in ivs) or any(lo < 1 - gc / CENTS < hi for lo, hi in ivs)
    grid = []
    steps = int(round(G_MAX / GRID))
    for i in range(1, steps + 1):
        gc = i * GRID
        r = evaluate(gc, n)
        grid.append(r)
    grid.sort(key=rank_key)
    seen, tops = set(), []
    for r in grid:
        if len(tops) >= REFINE_TOP:
            break
        if round(r["g"], 1) in seen:
            continue
        seen.add(round(r["g"], 1))
        best = r
        g = r["g"] - REFINE_HALF
        while g <= r["g"] + REFINE_HALF + 1e-9:
            if g > 0:
                q = evaluate(g, n)
                if rank_key(q) < rank_key(best):
                    best = q
            g += REFINE_STEP
        tops.append(best)
    tops.sort(key=rank_key)
    free = tops[0]
    mos_grid = [r for r in grid if in_level(r["g"])]
    mos = None
    if mos_grid:
        m = mos_grid[0]
        best = m
        g = m["g"] - REFINE_HALF
        while g <= m["g"] + REFINE_HALF + 1e-9:
            if g > 0 and in_level(g):
                q = evaluate(g, n)
                if rank_key(q) < rank_key(best):
                    best = q
            g += REFINE_STEP
        mos = best
    return {"N": n, "free": free, "mos": mos, "free_is_level": in_level(free["g"]),
            "runners": [{"g": t["g"], "hex": t["hex"], "dek": t["dek"], "tet": t["tet"], "triads": t["triads"]} for t in tops[1:4]]}


# ---------------------------------------------------------------------------
# structure of a winner: frozen image, val, kernel
# ---------------------------------------------------------------------------


def structure(res: dict, n: int) -> dict:
    gc, assign = res["g"], res["assign"]
    pcs = [(k * gc) % CENTS for k in assign]
    fr = score_tempered(pcs, EPS_LOCK)
    chain = [((k - res["mode"]) * gc) % CENTS for k in range(n)]   # the window starts at degree -mode
    ch = score_tempered(chain, EPS_LOCK)
    # val: octave row and generator row by exact integer solve on 11-limit monzos
    mz = [r3.monzo(t) for t in EIK]
    used = [i for i in range(len(r3.PRIMES)) if any(m[1][i] for m in mz)]
    rows = [[m[1][i] for i in used] for m in mz]
    # pitch(t) = k*gc + 1200*m_t, so the octave row satisfies e2 + sum e_p o_p = m_t
    m_t = [round((t - k * gc) / CENTS) for t, k in zip(TC, assign)]
    gen = r3.int_solve(rows, list(assign))
    oct_row = r3.int_solve(rows, [m - e2 for (e2, _), m in zip(mz, m_t)])
    val = None
    if gen is not None and oct_row is not None:
        val = {"primes": [r3.PRIMES[i] for i in used], "octave": oct_row, "g0": gen, "g1": [0] * len(used)}
    ker = r3.kernel_of(val) if val else []
    return {"image_frozen_PS_2c": fr.proportional + fr.subcontrary, "chain_P_2c": ch.proportional, "chain_S_2c": ch.subcontrary,
            "homomorphic": val is not None, "val": val and {"primes": val["primes"], "octave": val["octave"], "generator": val["g0"]},
            "kernel": ker[:4], "step_classes": c1.step_class_count(chain, 0.01)}


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def verdict_p_s1(rows):
    p = PREDICTIONS["P-S1"]
    fails = []
    by = {r["N"]: r for r in rows}
    for (lo, hi), (hx, dk, tt), (tmin, tmax), g in p:
        for n in range(lo, hi + 1):
            f = by[n]["free"]
            if f["hex"] < hx or f["dek"] < dk or f["tet"] < tt:
                fails.append(f"N={n}: {f['hex']}/{f['dek']}/{f['tet']} below {hx}/{dk}/{tt}")
            if not (tmin <= f["triads"] <= tmax + 2):
                fails.append(f"N={n}: triads {f['triads']} outside {tmin}..{tmax}")
            if abs(f["g"] - g) > PREDICTIONS["tol_g"]:
                fails.append(f"N={n}: g {f['g']:.3f} != {g}")
    return {"kept": not fails, "failures": fails}


def verdict_p_s2(rows):
    p = PREDICTIONS["P-S2"]
    fails = []
    best = max(rows, key=lambda r: (r["free"]["hex"] + r["free"]["dek"], r["free"]["triads"], -r["N"]))
    if best["free"]["hex"] != p["best_hex"] or best["free"]["dek"] != p["best_dek"] or best["N"] != p["best_N"] or best["free"]["triads"] != p["best_triads"]:
        fails.append(f"best {best['N']}: {best['free']['hex']}/{best['free']['dek']} triads {best['free']['triads']}")
    if any(r["free"]["hex"] == 30 and r["free"]["dek"] == 12 for r in rows):
        fails.append("a chain keeps every subset")
    first_dek = min((r["N"] for r in rows if r["free"]["dek"] > 0), default=None)
    if first_dek != p["first_dekany_N"]:
        fails.append(f"first dekany at {first_dek}")
    if max(r["free"]["hex"] for r in rows if r["N"] < 25) > p["max_hex_before_25"]:
        fails.append("more than 3 hexanies before N=25")
    return {"kept": not fails, "failures": fails}


def verdict_p_s3(rows):
    p = PREDICTIONS["P-S3"]
    fails = []
    by = {r["N"]: r for r in rows}
    for n in range(p["neutral_third_N"][0], p["neutral_third_N"][1] + 1):
        g = by[n]["free"]["g"]
        if n in p["neutral_third_except"]:
            if abs(g - 271.61) > PREDICTIONS["tol_g"]:
                fails.append(f"N={n}: g {g:.2f} != 271.61")
        elif not (350.6 <= g <= 351.5):
            fails.append(f"N={n}: g {g:.2f} not a neutral third")
    for n in p["miracle_N"]:
        if abs(by[n]["free"]["g"] - p["miracle_g"]) > PREDICTIONS["tol_g"]:
            fails.append(f"N={n}: g {by[n]['free']['g']:.2f} != miracle")
    miracle_elsewhere = [n for n, r in by.items() if abs(r["free"]["g"] - p["miracle_g"]) <= PREDICTIONS["tol_g"] and n not in p["miracle_N"]]
    if miracle_elsewhere:
        fails.append(f"miracle wins elsewhere: {miracle_elsewhere}")
    return {"kept": not fails, "failures": fails}


def verdict_p_s4(rows):
    p = PREDICTIONS["P-S4"]
    fails = []
    by = {r["N"]: r for r in rows}
    for n, (g, hx, dk, tri) in p["levels"].items():
        if n not in by:
            fails.append(f"N={n}: no row")
            continue
        m = by[n]["mos"]
        if m is None or abs(m["g"] - g) > 0.15 or m["hex"] < hx or (dk is not None and m["dek"] < dk):
            fails.append(f"N={n} level-only {m and (round(m['g'], 2), m['hex'], m['dek'], m['triads'])} != {(g, hx, dk, tri)}")
    for n, r in by.items():
        if r["free_is_level"]:
            if n not in p["free_is_level_N"]:
                fails.append(f"N={n}: free winner is a level (unregistered)")
        else:
            if r["mos"] is not None and r["mos"]["hex"] >= r["free"]["hex"]:
                fails.append(f"N={n}: level-only hexanies {r['mos']['hex']} not below free {r['free']['hex']}")
    for n in p["free_is_level_N"]:
        if n in by and not by[n]["free_is_level"]:
            fails.append(f"N={n}: free winner is not a level")
    return {"kept": not fails, "failures": fails}


def verdict_p_s5(rows):
    p = PREDICTIONS["P-S5"]
    fails = []
    for r in rows:
        n, e = r["N"], r["free"]["max_err_kept"]
        band = p["err_14_20"] if 14 <= n <= 20 else p["err_21_39"] if 21 <= n <= 39 else p["err_40_up"] if n >= 40 else None
        if band and not (band[0] <= e <= band[1]):
            fails.append(f"N={n}: max error in kept triads {e:.1f} outside {band}")
    return {"kept": not fails, "failures": fails}


# ---------------------------------------------------------------------------
# scl + main
# ---------------------------------------------------------------------------

SCL_PICKS = ((26, "free"), (45, "free"), (49, "free"), (70, "free"), (46, "mos"), (53, "mos"))


def write_scl(rows) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    by = {r["N"]: r for r in rows}
    out = []
    for n, which in SCL_PICKS:
        res = by[n][which]
        if res is None:
            continue
        chain = [((k - res["mode"]) * res["g"]) % CENTS for k in range(n)]
        name = f"subfit001_eikosany_N{n:02d}_{which}_g{res['g']:.3f}"
        text = c1.scl_text(name, f"SUBFIT-001 eikosany 1.3.5.7.9.11 in a {n}-note chain of {res['g']:.3f}c ({which}), "
                           f"mode {res['mode']}; playable hexanies {res['hex']}/30, dekanies {res['dek']}/12, tetrads {res['tet']}/30, "
                           f"triads {res['triads']}/114 within {EPS_LOCK}c; 1/1 = degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def main() -> dict:
    with Pool(WORKERS) as pool:
        rows = pool.map(search_n, range(N_MIN, N_MAX + 1), chunksize=1)
    rows.sort(key=lambda r: r["N"])
    for r in rows:
        r["experiment"] = EXPERIMENT
        r["free_structure"] = structure(r["free"], r["N"])
        r["mos_structure"] = structure(r["mos"], r["N"]) if r["mos"] else None
    verdicts = {"P-S1": verdict_p_s1(rows), "P-S2": verdict_p_s2(rows), "P-S3": verdict_p_s3(rows),
                "P-S4": verdict_p_s4(rows), "P-S5": verdict_p_s5(rows)}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": SUBFIT001_VERSION, "scorer_version": SCORER_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "grid_cents": GRID, "refine_step_cents": REFINE_STEP, "N_range": [N_MIN, N_MAX],
        "seeds": list(SEEDS), "n_tones": len(EIK), "n_triads": len(TRI), "n_subsets": len(SUBS),
        "subset_kinds": {k: KIND.count(k) for k in sorted(set(KIND))},
        "staircase": [{"N": r["N"], "g": r["free"]["g"], "mode": r["free"]["mode"], "hex": r["free"]["hex"], "dek": r["free"]["dek"],
                       "tet": r["free"]["tet"], "triads": r["free"]["triads"], "max_err_kept": r["free"]["max_err_kept"],
                       "free_is_level": r["free_is_level"], "kernel": [k["comma"] for k in r["free_structure"]["kernel"]],
                       "mos": r["mos"] and {"g": r["mos"]["g"], "hex": r["mos"]["hex"], "dek": r["mos"]["dek"], "tet": r["mos"]["tet"], "triads": r["mos"]["triads"]}}
                      for r in rows],
        "verdicts": verdicts, "scl_files": write_scl(rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  N {receipt['N_range']}  subsets {receipt['subset_kinds']}")
    for r in receipt["staircase"]:
        m = r["mos"]
        print(f"  N={r['N']:2d} g={r['g']:8.3f} m{r['mode']:2d} hex {r['hex']:2d} dek {r['dek']} tet {r['tet']:2d} triads {r['triads']:3d} "
              f"err {r['max_err_kept']:5.1f} level={r['free_is_level']} kernel={r['kernel'][:2]} | mos {m and (round(m['g'], 2), m['hex'], m['dek'], m['triads'])}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
