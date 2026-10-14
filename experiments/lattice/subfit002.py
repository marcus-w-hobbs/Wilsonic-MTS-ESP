"""SUBFIT-002 — SUBFIT-001's subset-playability search with a per-tone cap
in the survival predicate (LOG.md pre-registration 2026-10-14; committed
before this file).

SUBFIT-001 assigned each eikosany tone to its nearest degree inside the
window with no cap on how far that degree could sit from the just pitch,
so below N = 37 its counts were chain coincidences. This runner keeps
SUBFIT-001's objects, search, objective and tie-breaks (subfit001.py)
and changes one thing: a triad survives only when the mirror predicate
holds (|dev| < 2c, separation >= 2c) AND each of its three tones sits
within CAP cents of its just pitch at the assigned degree. Two tiers are
run, CAP = 20 (the CPSFIT-003 cap) and CAP = 10. Predictions P-T20, P-T10,
P-T-A..D are pinned in PREDICTIONS below, verbatim from LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered, via subfit001)

Receipts: results/subfit002.jsonl (one row per cap and N) +
results/subfit002_summary.json; results/scl/subfit002/*.scl. Stdlib only
(multiprocessing over (cap, N)), deterministic, no wall-clock fields; two
runs must be bit-identical.

Run from experiments/lattice/:  python3.12 subfit002.py
"""

from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
import subfit001 as sf  # noqa: E402
from scorer import SCORER_VERSION  # noqa: E402

SUBFIT002_VERSION = "1.0.0"
EXPERIMENT = "SUBFIT-002"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "subfit002.jsonl"
SUMMARY = RESULTS_DIR / "subfit002_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "subfit002"

CENTS = sf.CENTS
CAPS = (20.0, 10.0)
N_MIN, N_MAX = sf.N_MIN, sf.N_MAX
WORKERS = sf.WORKERS
G_TOL = 0.01      # registered generators are exact to 0.01 cents
ERR_TOL = 0.051   # registered errors are given to 0.1 cents

# Registered staircases: (N_lo, N_hi): (g, hex, dek, tet, (triads_lo, triads_hi), err or None)
_T20 = {
    (11, 12): (124.23, 1, 0, 0, (10, 12), 16.2), (13, 13): (350.98, 1, 0, 1, (8, 8), 8.1),
    (14, 15): (351.32, 1, 0, 2, (12, 18), 9.1), (16, 16): (351.32, 2, 0, 2, (21, 21), 9.1),
    (17, 21): (351.32, 3, 0, 3, (24, 24), 9.1), (22, 23): (317.13, 4, 0, 5, (50, 50), 18.1),
    (24, 25): (317.13, 6, 0, 6, (56, 56), 18.1), (26, 29): (350.75, 6, 1, 7, (43, 43), 19.2),
    (30, 31): (350.75, 6, 1, 7, (47, 47), 19.2), (32, 32): (350.75, 6, 1, 7, (55, 55), None),
    (33, 33): (350.75, 7, 1, 8, (56, 56), None), (34, 34): (350.75, 8, 1, 8, (61, 61), None),
    (35, 36): (350.75, 9, 1, 9, (66, 66), 19.2), (37, 37): (350.76, 12, 2, 12, (70, 70), 10.3),
    (38, 48): (351.44, 14, 2, 14, (88, 88), 9.5), (49, 56): (497.77, 16, 2, 16, (76, 76), 4.2),
    (57, 69): (316.78, 18, 2, 18, (96, 96), 8.7), (70, 72): (175.38, 20, 4, 20, (102, 102), 4.6),
}
_T10 = {
    (11, 12): (175.49, 0, 0, 1, (10, 10), 8.1), (13, 13): (350.98, 1, 0, 1, (8, 8), None),
    (14, 15): (351.32, 1, 0, 2, (12, 18), 9.1), (16, 16): (351.32, 2, 0, 2, (21, 21), None),
    (17, 21): (351.32, 3, 0, 3, (24, 24), 9.1), (22, 23): (351.32, 3, 0, 3, (25, 25), None),
    (24, 25): (350.76, 3, 0, 5, (32, 32), 8.3), (26, 29): (350.76, 6, 1, 7, (39, 39), 8.3),
    (30, 31): (350.76, 6, 1, 7, (42, 42), 9.4), (32, 32): (350.76, 6, 1, 7, (49, 49), 9.9),
    (33, 34): (350.76, 7, 1, 8, (52, 52), 9.9), (35, 36): (350.76, 8, 1, 8, (58, 58), 9.9),
    (37, 37): (351.44, 10, 1, 12, (80, 80), 9.5),
    **{k: v for k, v in _T20.items() if k[0] >= 38},   # "38 to 72: identical to cap 20"
}
PREDICTIONS = {
    "P-T20": _T20, "P-T10": _T10,
    "P-T-A": {"identical_from": 38, "differ_at": 37},
    "P-T-B": {"first_dekany": 26, "best_N": 70, "best": (20, 4, 102), "cap10_no_hexany": (11, 12), "cap10_max_hex_before_26": 3},
    "P-T-C": {"levels": {20.0: (17, 41, 53), 10.0: (17, 24, 41, 53)},
              "mos": {41: (351.44, 14, 2, None), 58: (351.44, 14, 2, None), 53: (497.77, 16, 2, None), 72: (483.28, 20, 4, 100),
                      46: (443.13, 12, 2, None), 65: (443.13, 12, 2, None), 31: (116.68, 6, 0, None)}},
    "P-T-D": {14: (41, 9.5), 16: (53, 4.2), 20: (72, 8.0)},
}

_CAP = CAPS[0]


# ---------------------------------------------------------------------------
# the capped predicate
# ---------------------------------------------------------------------------


def evaluate_capped(gc: float, n: int, cap: float | None = None) -> dict:
    """SUBFIT-001's evaluate with the per-tone cap: same windows, same in-window
    nearest assignment, same objective and tie-breaks; a triad counts only when
    all three tones sit within `cap` cents of their just pitch."""
    cap = _CAP if cap is None else cap
    ks = list(range(-(n - 1), n))
    ranked, dist = [], []
    for t in sf.TC:
        ds = {k: sf.circ(k * gc, t) for k in ks}
        ranked.append(sorted(ks, key=lambda k: (ds[k], abs(k))))
        dist.append(ds)
    best = None
    cache: dict[tuple[int, ...], list[bool]] = {}
    for s in range(-(n - 1), 1):
        lo, hi = s, s + n - 1
        assign = tuple(next(k for k in r if lo <= k <= hi) for r in ranked)
        surv = cache.get(assign)
        if surv is None:
            raw = sf.survival(assign, gc)
            ok_tone = [dist[j][assign[j]] <= cap for j in range(len(sf.TC))]
            surv = [raw[i] and all(ok_tone[j] for j, _ in sf.TRI[i][1]) for i in range(len(sf.TRI))]
            cache[assign] = surv
        kept = sum(surv)
        playable = [all(surv[i] for i in inc) for inc in sf.INC]
        hx = sum(p for p, h in zip(playable, sf.IS_HEX) if h)
        dk = sum(p for p, d in zip(playable, sf.IS_DEK) if d)
        tt = sum(p for p, t in zip(playable, sf.IS_TET) if t)
        in_kept = set()
        for i, ok in enumerate(surv):
            if ok:
                in_kept.update(j for j, _ in sf.TRI[i][1])
        err = max((dist[j][assign[j]] for j in in_kept), default=0.0)
        key = (-(hx + dk), -tt, -kept, round(err, sf.KEY_ROUND), -s)
        if best is None or key < best[0]:
            best = (key, {"hex": hx, "dek": dk, "tet": tt, "triads": kept, "mode": -s, "max_err_kept": err,
                          "assign": list(assign), "playable": [sf.NAMES[j] for j, p in enumerate(playable) if p]})
    out = best[1]
    out["g"] = gc
    return out


def search_task(task: tuple[float, int]) -> dict:
    """SUBFIT-001's search_n (grid, refinement, MOS-only variant) under the cap."""
    global _CAP
    cap, n = task
    _CAP = cap
    sf.evaluate = evaluate_capped
    r = sf.search_n(n)
    r["cap"] = cap
    return r


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def _by_cap(rows):
    out = {}
    for r in rows:
        out.setdefault(r["cap"], {})[r["N"]] = r
    return out


def verdict_table(rows, cap: float, table: dict) -> dict:
    by = _by_cap(rows).get(cap, {})
    fails = []
    for (a, b), (g, hx, dk, tt, (t0, t1), err) in sorted(table.items()):
        for n in range(a, b + 1):
            r = by.get(n)
            if r is None:
                fails.append(f"N={n}: missing")
                continue
            f = r["free"]
            if abs(f["g"] - g) > G_TOL:
                fails.append(f"N={n}: g {f['g']:.3f} vs {g}")
            if (f["hex"], f["dek"], f["tet"]) != (hx, dk, tt):
                fails.append(f"N={n}: counts {f['hex']}/{f['dek']}/{f['tet']} vs {hx}/{dk}/{tt}")
            if not t0 <= f["triads"] <= t1:
                fails.append(f"N={n}: triads {f['triads']} vs {t0}-{t1}")
            if err is not None and abs(f["max_err_kept"] - err) > ERR_TOL:
                fails.append(f"N={n}: err {f['max_err_kept']:.1f} vs {err}")
    return {"kept": not fails, "failures": fails}


def _sig(r):
    f = r["free"]
    return (round(f["g"], 3), f["mode"], f["hex"], f["dek"], f["tet"], f["triads"])


def verdict_p_t_a(rows) -> dict:
    by = _by_cap(rows)
    p = PREDICTIONS["P-T-A"]
    fails = []
    for n in range(p["identical_from"], N_MAX + 1):
        a, b = by[CAPS[0]].get(n), by[CAPS[1]].get(n)
        if a is None or b is None or _sig(a) != _sig(b):
            fails.append(f"N={n}: cap20 {a and _sig(a)} vs cap10 {b and _sig(b)}")
    n = p["differ_at"]
    a, b = by[CAPS[0]].get(n), by[CAPS[1]].get(n)
    if a is None or b is None or _sig(a) == _sig(b):
        fails.append(f"N={n}: expected a difference")
    return {"kept": not fails, "failures": fails}


def verdict_p_t_b(rows) -> dict:
    by = _by_cap(rows)
    p = PREDICTIONS["P-T-B"]
    fails = []
    for cap in CAPS:
        rs = by[cap]
        first_dek = min((n for n, r in rs.items() if r["free"]["dek"] > 0), default=None)
        if first_dek != p["first_dekany"]:
            fails.append(f"cap{cap:.0f}: first dekany at N={first_dek}")
        best_sum = max(r["free"]["hex"] + r["free"]["dek"] for r in rs.values())
        best_n = min(n for n, r in rs.items() if r["free"]["hex"] + r["free"]["dek"] == best_sum)
        f = rs[best_n]["free"]
        if (best_n, f["hex"], f["dek"], f["triads"]) != (p["best_N"], *p["best"]):
            fails.append(f"cap{cap:.0f}: best N={best_n} {f['hex']}/{f['dek']}/{f['triads']}")
        if any(r["free"]["hex"] == 30 and r["free"]["dek"] == 12 for r in rs.values()):
            fails.append(f"cap{cap:.0f}: a chain keeps every subset")
    rs = by[CAPS[1]]
    for n in p["cap10_no_hexany"]:
        if rs[n]["free"]["hex"] != 0:
            fails.append(f"cap10 N={n}: {rs[n]['free']['hex']} hexanies")
    for n in range(N_MIN, p["first_dekany"]):
        if rs[n]["free"]["hex"] > p["cap10_max_hex_before_26"]:
            fails.append(f"cap10 N={n}: {rs[n]['free']['hex']} hexanies before 26")
    return {"kept": not fails, "failures": fails}


def verdict_p_t_c(rows) -> dict:
    by = _by_cap(rows)
    p = PREDICTIONS["P-T-C"]
    fails = []
    for cap in CAPS:
        rs = by[cap]
        levels = tuple(n for n in sorted(rs) if rs[n]["free_is_level"])
        if levels != p["levels"][cap]:
            fails.append(f"cap{cap:.0f}: free winner is a level at {levels}")
        for n, (g, hx, dk, tri) in p["mos"].items():
            m = rs[n]["mos"]
            if m is None or abs(m["g"] - g) > G_TOL or (m["hex"], m["dek"]) != (hx, dk) or (tri is not None and m["triads"] != tri):
                fails.append(f"cap{cap:.0f} N={n}: mos {m and (round(m['g'], 2), m['hex'], m['dek'], m['triads'])}")
    return {"kept": not fails, "failures": fails}


def verdict_p_t_d(rows) -> dict:
    by = _by_cap(rows)
    fails = []
    for cap in CAPS:
        rs = by[cap]
        for floor, (n_reg, err_reg) in PREDICTIONS["P-T-D"].items():
            n = min((n for n in sorted(rs) if rs[n]["mos"] and rs[n]["mos"]["hex"] >= floor), default=None)
            if n != n_reg:
                fails.append(f"cap{cap:.0f}: first level with >= {floor} hexanies is N={n}")
            elif rs[n]["mos"]["max_err_kept"] > err_reg + ERR_TOL:
                fails.append(f"cap{cap:.0f} N={n}: level err {rs[n]['mos']['max_err_kept']:.1f} vs {err_reg}")
    return {"kept": not fails, "failures": fails}


# ---------------------------------------------------------------------------
# receipts
# ---------------------------------------------------------------------------

SCL_PICKS = ((20.0, 41, "mos"), (20.0, 72, "mos"), (20.0, 37, "free"))


def write_scl(rows) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    by = _by_cap(rows)
    out = []
    for cap, n, which in SCL_PICKS:
        res = by[cap][n][which]
        if res is None:
            continue
        chain = [((k - res["mode"]) * res["g"]) % CENTS for k in range(n)]
        name = f"subfit002_eikosany_cap{cap:.0f}_N{n:02d}_{which}_g{res['g']:.3f}"
        text = c1.scl_text(name, f"SUBFIT-002 eikosany 1.3.5.7.9.11 in a {n}-note chain of {res['g']:.3f}c ({which}, tone cap {cap:.0f}c), "
                           f"mode {res['mode']}; playable hexanies {res['hex']}/30, dekanies {res['dek']}/12, tetrads {res['tet']}/30, "
                           f"triads {res['triads']}/114 within {sf.EPS_LOCK}c, tones within {res['max_err_kept']:.1f}c; 1/1 = degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def _stair(r):
    f, m = r["free"], r["mos"]
    return {"N": r["N"], "g": f["g"], "mode": f["mode"], "hex": f["hex"], "dek": f["dek"], "tet": f["tet"], "triads": f["triads"],
            "max_err_kept": f["max_err_kept"], "free_is_level": r["free_is_level"],
            "kernel": [k["comma"] for k in r["free_structure"]["kernel"]],
            "mos": m and {"g": m["g"], "hex": m["hex"], "dek": m["dek"], "tet": m["tet"], "triads": m["triads"], "max_err_kept": m["max_err_kept"]}}


def main() -> dict:
    tasks = [(cap, n) for cap in CAPS for n in range(N_MIN, N_MAX + 1)]
    with Pool(WORKERS) as pool:
        rows = pool.map(search_task, tasks, chunksize=1)
    rows.sort(key=lambda r: (-r["cap"], r["N"]))
    for r in rows:
        r["experiment"] = EXPERIMENT
        r["free_structure"] = sf.structure(r["free"], r["N"])
        r["mos_structure"] = sf.structure(r["mos"], r["N"]) if r["mos"] else None
    verdicts = {"P-T20": verdict_table(rows, 20.0, _T20), "P-T10": verdict_table(rows, 10.0, _T10),
                "P-T-A": verdict_p_t_a(rows), "P-T-B": verdict_p_t_b(rows), "P-T-C": verdict_p_t_c(rows), "P-T-D": verdict_p_t_d(rows)}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": SUBFIT002_VERSION, "subfit001_version": sf.SUBFIT001_VERSION,
        "scorer_version": SCORER_VERSION, "epsilon_lock_cents": sf.EPS_LOCK, "caps_cents": list(CAPS),
        "grid_cents": sf.GRID, "refine_step_cents": sf.REFINE_STEP, "N_range": [N_MIN, N_MAX], "seeds": list(sf.SEEDS),
        "n_tones": len(sf.EIK), "n_triads": len(sf.TRI), "n_subsets": len(sf.SUBS),
        "staircase": {f"cap{cap:.0f}": [_stair(r) for r in rows if r["cap"] == cap] for cap in CAPS},
        "verdicts": verdicts, "scl_files": write_scl(rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  caps {receipt['caps_cents']}  N {receipt['N_range']}")
    for cap, stair in receipt["staircase"].items():
        for r in stair:
            m = r["mos"]
            print(f"  {cap} N={r['N']:2d} g={r['g']:8.3f} m{r['mode']:2d} hex {r['hex']:2d} dek {r['dek']} tet {r['tet']:2d} triads {r['triads']:3d} "
                  f"err {r['max_err_kept']:5.1f} level={r['free_is_level']} kernel={r['kernel'][:2]} | mos {m and (round(m['g'], 2), m['hex'], m['dek'], m['triads'], round(m['max_err_kept'], 1))}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
