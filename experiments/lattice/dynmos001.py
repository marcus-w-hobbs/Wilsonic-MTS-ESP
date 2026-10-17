"""DYNMOS-001 — Fork B, the dynamic MOS: one fixed generator, and for every
Euler-genus subset the smallest MOS level and the window that keep every
exact triad of the subset (LOG.md pre-registration 2026-10-17; committed
before this file).

Objects: two seed sets (canonical 1.3.5.7.9.11 and Marcus's
1.45.135.225.19.377), the SUBSET-MEL-000 census of 72 subsets each with
its own exact triads; a subset with no exact triad is VACUOUS and is
excluded from coverage. Twelve fixed generators. Predicate: for each
level N of g (Farey levels, 5..72) and each window of N consecutive
degrees, tones go to the nearest in-window degree; the window keeps the
subset when every tone is within CAP of its degree and every exact triad
survives the mirror predicate (|dev| < 2c, separation >= 2c). N* is the
smallest keeping level; the window minimises the largest tone error, then
the mode number. Referee: every N from 5 to 72. Transitions: for dekany
pairs with levels, common tones KEPT (same chain degree) vs RETUNED.

Frozen inputs (read-only): subsetmel000.enumerate_subsets, cpsfit001/002
helpers, gold002.levels_of.

Receipts: results/dynmos001.jsonl (one row per generator x seed set) +
results/dynmos001_summary.json; results/scl/dynmos001/*.scl. Stdlib only,
deterministic, no wall-clock fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 dynmos001.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
import cpsfit002 as c2  # noqa: E402
import gold002 as g2  # noqa: E402
import subsetmel000 as sm  # noqa: E402
from families.cps import cps_scale  # noqa: E402
from scorer import SCORER_VERSION  # noqa: E402

DYNMOS001_VERSION = "1.0.0"
EXPERIMENT = "DYNMOS-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "dynmos001.jsonl"
SUMMARY = RESULTS_DIR / "dynmos001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "dynmos001"

CENTS = 1200.0
EPS_LOCK = 2.0
CAP = 20.0
N_MIN, N_MAX = 5, 72
WORKERS = 8

GENERATORS = {
    "marcus238186": 285.823, "marcus418935": 502.722, "gold503786": 503.786, "gold317170": 317.170,
    "sub351444": 351.444, "sub497774": 497.774, "sub443128": 443.128, "sub483278": 483.278,
    "sub175378": 175.378, "sub316778": 316.778, "miracle116676": 116.676, "breed193908": 193.908,
}
SEEDSETS = {"canonical": (1, 3, 5, 7, 9, 11), "marcus": (1, 45, 135, 225, 19, 377)}

# Registered predictions (LOG 2026-10-17). Coverage rows: (hex, dek, tet, incidences).
PREDICTIONS = {
    "P-D1": {"marcus238186": {"canonical": (0, 0), "marcus": (0, 0)},     # (level hexanies, any-N hexanies)
             "marcus418935": {"canonical": (0, 1), "marcus": (4, None)}, "marcus418935_marcus_hexN": 43, "marcus418935_marcus_dek": 0},
    "P-D2": {"gold503786": (2, 0, 2, 12), "gold317170": (8, 0, 10, 120), "sub351444": (14, 2, 14, 292), "sub497774": (16, 2, 16, 220),
             "sub443128": (12, 2, 12, 222), "sub483278": (20, 4, 20, 310), "sub175378": (12, 0, 22, 220), "sub316778": (18, 2, 19, 311),
             "miracle116676": (12, 0, 15, 123), "breed193908": (12, 2, 15, 279), "err": {"sub351444": 9.5, "sub497774": 4.2},
             "total": 684},
    "P-D3": {"min_hex": (17, "sub351444"), "min_dek": (41, ("sub351444", "sub497774")),
             "hexN": {"sub351444": {17: 3, 24: 3, 41: 8}, "sub497774": {29: 6, 41: 6, 53: 4}, "sub316778": {19: 1, 34: 6, 53: 11},
                      "sub443128": {19: 2, 27: 1, 46: 9}, "sub483278": {32: 1, 37: 1, 42: 5, 52: 3, 57: 6, 62: 2, 67: 2}, "miracle116676": {31: 9, 41: 3}},
             "dekN": {"sub351444": {41: 2}, "sub497774": {41: 2}, "sub443128": {46: 2}, "sub316778": {53: 2}, "sub483278": {62: 2, 67: 2}, "breed193908": {68: 2}}},
    "P-D4": {"vacuous": {"hexany": 12, "tetrad": 12}, "denominators": (18, 12, 18, 228), "exact_triads": 30,
             "sub316778": (14, 7, 18, 193), "gold317170": (14, 6, 18, 178), "breed193908": (15, 6, 17, 179), "sub443128": (12, 6, 15, 171),
             "sub483278": (16, 5, 17, 169), "sub351444": (12, 4, 17, 149), "miracle116676": (12, 5, 12, 75), "sub175378": (6, 2, 16, 76),
             "sub497774": (7, 2, 11, 55), "gold503786": (6, 4, 6, 30), "min_dek": (15, "sub316778"), "min_hex": (11, ("sub316778", "gold317170"))},
    "P-D5": {"canonical": {"sub483278": (4, 0, 20, 2), "sub351444": (0, 0, 0, 1), "sub497774": (0, 0, 0, 1), "sub443128": (0, 0, 0, 1),
                           "sub316778": (0, 0, 0, 1), "breed193908": (0, 0, 0, 1)},   # (affinity pairs, retuned, common, contrast pairs)
             "marcus": {"sub316778": (18, 36, 90, 3), "gold317170": (12, 20, 60, None), "sub443128": (12, 25, 60, None), "breed193908": (12, 21, 60, None),
                        "sub483278": (8, 11, 40, None), "miracle116676": (8, 9, 40, None), "sub351444": (4, 9, 20, None), "gold503786": (4, 3, 20, None)},
             "sub483278_levels": (62, 67)},
    "P-D6": {"same": ("sub497774", "sub443128", "sub483278", "sub316778", "miracle116676", "breed193908", "marcus238186"),
             "differ": {"marcus418935": (0, 1), "gold503786": (2, 4), "gold317170": (8, 12), "sub351444": (14, 16), "sub175378": (12, 22)},
             "sub175378_dek": (0, 4)},
}


# ---------------------------------------------------------------------------
# objects
# ---------------------------------------------------------------------------


def circ(a: float, b: float) -> float:
    d = abs((a - b) % CENTS)
    return min(d, CENTS - d)


def prep(seeds: tuple[int, ...]) -> list[dict]:
    """The census subsets of a seed set with cents and exact triads; vacuous flagged."""
    out = []
    for s in sm.enumerate_subsets(seeds):
        tri = c2.prep_triads(s.tones)
        out.append({"name": s.name, "kind": s.kind, "tones": [str(t) for t in s.tones],
                    "tc": [c1.cents_of(t) for t in s.tones], "tri": tri, "ntri": len(tri), "vacuous": len(tri) == 0})
    return out


def genus_facts(seeds: tuple[int, ...]) -> dict:
    eik = cps_scale(seeds, 3)
    tc = sorted(c1.cents_of(t) for t in eik)
    steps = sorted((b - a) for a, b in zip(tc, tc[1:] + [tc[0] + CENTS]))
    return {"n_tones": len(eik), "distinct_pc": len({round(c, 6) for c in tc}), "exact_triads": len(c1.exact_triads(eik)),
            "min_step_cents": steps[0], "max_step_cents": steps[-1]}


# ---------------------------------------------------------------------------
# the predicate
# ---------------------------------------------------------------------------


def best_window(tc: list[float], tri, gc: float, n: int) -> dict | None:
    """Smallest-error window of the n-note chain of gc that keeps every triad, or None."""
    ks = list(range(-(n - 1), n))
    ranked, dist = [], []
    for t in tc:
        ds = {k: circ(k * gc, t) for k in ks}
        ranked.append(sorted(ks, key=lambda k: (ds[k], abs(k))))
        dist.append(ds)
    best = None
    for s in range(-(n - 1), 1):
        lo, hi = s, s + n - 1
        assign = tuple(next(k for k in r if lo <= k <= hi) for r in ranked)
        errs = [dist[j][assign[j]] for j in range(len(tc))]
        if max(errs) > CAP:
            continue
        pc = [(k * gc) % CENTS for k in assign]
        if not all(d < EPS_LOCK and sp >= EPS_LOCK for d, sp in c2.triad_devs(tri, pc)):
            continue
        key = (max(errs), -s)
        if best is None or key < best[0]:
            best = (key, {"mode": -s, "assign": list(assign), "err": max(errs)})
    return best and best[1]


def levels(gc: float) -> list[int]:
    return [n for n in g2.levels_of(gc / CENTS, N_MAX) if n >= N_MIN]


def first_level(sub: dict, gc: float, ns) -> dict | None:
    for n in ns:
        w = best_window(sub["tc"], sub["tri"], gc, n)
        if w:
            return {"N": n, **w}
    return None


def transitions(subs: list[dict], rows: list[dict]) -> list[dict]:
    deks = [(s, r) for s, r in zip(subs, rows) if s["kind"].startswith("dekany") and r["level"]]
    out = []
    for i in range(len(deks)):
        for j in range(i + 1, len(deks)):
            (sa, ra), (sb, rb) = deks[i], deks[j]
            ka = dict(zip(sa["tones"], ra["level"]["assign"]))
            kb = dict(zip(sb["tones"], rb["level"]["assign"]))
            common = [t for t in sa["tones"] if t in kb]
            kept = sum(ka[t] == kb[t] for t in common)
            out.append({"a": sa["name"], "b": sb["name"], "common": len(common), "kept": kept, "retuned": len(common) - kept,
                        "Na": ra["level"]["N"], "Nb": rb["level"]["N"], "dN": abs(ra["level"]["N"] - rb["level"]["N"])})
    return out


def run_pair(task: tuple[str, str]) -> dict:
    gname, sname = task
    gc, seeds = GENERATORS[gname], SEEDSETS[sname]
    subs = prep(seeds)
    ns = levels(gc)
    rows = []
    for s in subs:
        if s["vacuous"]:
            rows.append({"name": s["name"], "kind": s["kind"], "ntri": 0, "vacuous": True, "level": None, "any": None})
            continue
        rows.append({"name": s["name"], "kind": s["kind"], "ntri": s["ntri"], "vacuous": False,
                     "level": first_level(s, gc, ns), "any": first_level(s, gc, range(N_MIN, N_MAX + 1))})
    return {"experiment": EXPERIMENT, "generator": gname, "g_cents": gc, "seeds": sname, "seed_values": list(seeds),
            "levels": ns, "subsets": rows, "transitions": transitions(subs, rows)}


# ---------------------------------------------------------------------------
# summaries and verdicts
# ---------------------------------------------------------------------------


def coverage(r: dict, key: str = "level") -> dict:
    rows = [x for x in r["subsets"] if not x["vacuous"]]
    out = {}
    for kind in ("hexany", "dekany", "tetrad"):
        rs = [x for x in rows if x["kind"].startswith(kind)]
        out[kind] = (sum(1 for x in rs if x[key]), len(rs))
    out["incidences"] = (sum(x["ntri"] for x in rows if x[key]), sum(x["ntri"] for x in rows))
    errs = [x[key]["err"] for x in rows if x[key]]
    out["max_err"] = max(errs) if errs else None
    out["hexN"] = dict(sorted(Counter(x[key]["N"] for x in rows if x["kind"] == "hexany" and x[key]).items()))
    out["dekN"] = dict(sorted(Counter(x[key]["N"] for x in rows if x["kind"].startswith("dekany") and x[key]).items()))
    return out


def trans_summary(r: dict) -> dict:
    tr = r["transitions"]
    aff = [t for t in tr if t["common"] > 0]
    return {"affinity_pairs": len(aff), "retuned": sum(t["retuned"] for t in aff), "common": sum(t["common"] for t in aff),
            "contrast_pairs": sum(1 for t in tr if t["common"] == 0), "levels_used": sorted({t["Na"] for t in tr} | {t["Nb"] for t in tr})}


def _by(rows):
    return {(r["generator"], r["seeds"]): r for r in rows}


def _cov4(c):
    return (c["hexany"][0], c["dekany"][0], c["tetrad"][0], c["incidences"][0])


def verdict_p_d1(rows) -> dict:
    by = _by(rows); p = PREDICTIONS["P-D1"]; fails = []
    for g in ("marcus238186", "marcus418935"):
        for s in SEEDSETS:
            lv, an = p[g][s]
            c, ca = coverage(by[(g, s)]), coverage(by[(g, s)], "any")
            if c["hexany"][0] != lv:
                fails.append(f"{g} {s}: level hexanies {c['hexany'][0]} vs {lv}")
            if an is not None and ca["hexany"][0] != an:
                fails.append(f"{g} {s}: any-N hexanies {ca['hexany'][0]} vs {an}")
            if g == "marcus238186" and (any(x["level"] or x["any"] for x in by[(g, s)]["subsets"])):
                fails.append(f"{g} {s}: keeps a subset")
    c = coverage(by[("marcus418935", "marcus")])
    if set(c["hexN"]) != {p["marcus418935_marcus_hexN"]} or c["dekany"][0] != p["marcus418935_marcus_dek"]:
        fails.append(f"marcus418935 marcus: hexN {c['hexN']} dek {c['dekany'][0]}")
    return {"kept": not fails, "failures": fails}


def _verdict_cov(rows, key, seeds) -> dict:
    by = _by(rows); p = PREDICTIONS[key]; fails = []
    for g, want in p.items():
        if not isinstance(want, tuple) or len(want) != 4 or g not in GENERATORS:
            continue
        c = coverage(by[(g, seeds)])
        if _cov4(c) != want:
            fails.append(f"{g}: {_cov4(c)} vs {want}")
    if key == "P-D2":
        for g, e in p["err"].items():
            if coverage(by[(g, seeds)])["max_err"] > e + 0.051:
                fails.append(f"{g}: max err {coverage(by[(g, seeds)])['max_err']:.1f} vs {e}")
        if coverage(by[("sub483278", seeds)])["incidences"][1] != p["total"]:
            fails.append("incidence total")
    return {"kept": not fails, "failures": fails}


def verdict_p_d2(rows) -> dict:
    return _verdict_cov(rows, "P-D2", "canonical")


def verdict_p_d3(rows) -> dict:
    by = _by(rows); p = PREDICTIONS["P-D3"]; fails = []
    covs = {g: coverage(by[(g, "canonical")]) for g in GENERATORS}
    min_hex = min((min(c["hexN"]), g) for g, c in covs.items() if c["hexN"])
    min_dek = min(min(c["dekN"]) for c in covs.values() if c["dekN"])
    dek_at = tuple(sorted(g for g, c in covs.items() if c["dekN"] and min(c["dekN"]) == min_dek))
    if min_hex != p["min_hex"]:
        fails.append(f"min hexany level {min_hex}")
    if (min_dek, dek_at) != p["min_dek"]:
        fails.append(f"min dekany level {min_dek} at {dek_at}")
    for g, want in p["hexN"].items():
        if covs[g]["hexN"] != want:
            fails.append(f"{g} hexN {covs[g]['hexN']} vs {want}")
    for g, want in p["dekN"].items():
        if covs[g]["dekN"] != want:
            fails.append(f"{g} dekN {covs[g]['dekN']} vs {want}")
    return {"kept": not fails, "failures": fails}


def verdict_p_d4(rows) -> dict:
    by = _by(rows); p = PREDICTIONS["P-D4"]; fails = []
    r0 = by[("sub316778", "marcus")]
    vac = Counter(x["kind"].split("_")[0] for x in r0["subsets"] if x["vacuous"])
    if (vac.get("hexany", 0), vac.get("tetrad", 0), vac.get("dekany", 0)) != (p["vacuous"]["hexany"], p["vacuous"]["tetrad"], 0):
        fails.append(f"vacuous {dict(vac)}")
    c0 = coverage(r0)
    if (c0["hexany"][1], c0["dekany"][1], c0["tetrad"][1], c0["incidences"][1]) != p["denominators"]:
        fails.append("denominators")
    if r0["genus"]["exact_triads"] != p["exact_triads"]:
        fails.append(f"exact triads {r0['genus']['exact_triads']}")
    v = _verdict_cov(rows, "P-D4", "marcus")
    fails += v["failures"]
    covs = {g: coverage(by[(g, "marcus")]) for g in GENERATORS}
    min_dek = min((min(c["dekN"]), g) for g, c in covs.items() if c["dekN"])
    if min_dek != p["min_dek"]:
        fails.append(f"min dekany level {min_dek}")
    min_hex = min(min(c["hexN"]) for c in covs.values() if c["hexN"])
    hex_at = tuple(sorted(g for g, c in covs.items() if c["hexN"] and min(c["hexN"]) == min_hex))
    if (min_hex, hex_at) != p["min_hex"]:
        fails.append(f"min hexany level {min_hex} at {hex_at}")
    return {"kept": not fails, "failures": fails}


def verdict_p_d5(rows) -> dict:
    by = _by(rows); p = PREDICTIONS["P-D5"]; fails = []
    for seeds in ("canonical", "marcus"):
        for g, (aff, ret, com, con) in p[seeds].items():
            t = trans_summary(by[(g, seeds)])
            if (t["affinity_pairs"], t["retuned"], t["common"]) != (aff, ret, com) or (con is not None and t["contrast_pairs"] != con):
                fails.append(f"{seeds} {g}: {t}")
    others = [g for g in GENERATORS if g not in p["canonical"]]
    for g in others:
        if trans_summary(by[(g, "canonical")])["affinity_pairs"]:
            fails.append(f"canonical {g} has affinity pairs")
    if tuple(trans_summary(by[("sub483278", "canonical")])["levels_used"]) != p["sub483278_levels"]:
        fails.append("sub483278 levels")
    return {"kept": not fails, "failures": fails}


def verdict_p_d6(rows) -> dict:
    by = _by(rows); p = PREDICTIONS["P-D6"]; fails = []
    for g in p["same"]:
        c, ca = coverage(by[(g, "canonical")]), coverage(by[(g, "canonical")], "any")
        if c["hexany"][0] != ca["hexany"][0]:
            fails.append(f"{g}: level {c['hexany'][0]} vs any {ca['hexany'][0]}")
    for g, (lv, an) in p["differ"].items():
        c, ca = coverage(by[(g, "canonical")]), coverage(by[(g, "canonical")], "any")
        if (c["hexany"][0], ca["hexany"][0]) != (lv, an):
            fails.append(f"{g}: ({c['hexany'][0]}, {ca['hexany'][0]}) vs {(lv, an)}")
    c, ca = coverage(by[("sub175378", "canonical")]), coverage(by[("sub175378", "canonical")], "any")
    if (c["dekany"][0], ca["dekany"][0]) != p["sub175378_dek"]:
        fails.append("sub175378 dekanies")
    return {"kept": not fails, "failures": fails}


# ---------------------------------------------------------------------------
# receipts
# ---------------------------------------------------------------------------

SCL_PICKS = (("sub351444", "canonical", "hexany", 17), ("sub497774", "canonical", "hexany", 29), ("sub316778", "marcus", "dekany", 15))


def write_scl(rows) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    by = _by(rows)
    out = []
    for g, seeds, kind, n in SCL_PICKS:
        r = by[(g, seeds)]
        picks = [x for x in r["subsets"] if x["kind"].startswith(kind) and x["level"] and x["level"]["N"] == n]
        if not picks:
            continue
        x = sorted(picks, key=lambda x: (x["level"]["err"], x["name"]))[0]
        lv = x["level"]
        chain = [((k - lv["mode"]) * r["g_cents"]) % CENTS for k in range(n)]
        name = f"dynmos001_{seeds}_{g}_N{n:02d}_{x['name']}"
        text = c1.scl_text(name, f"DYNMOS-001 {seeds} seeds {r['seed_values']}: {n}-note level of {r['g_cents']:.3f}c, mode {lv['mode']}, "
                           f"keeps {x['kind']} {x['name']} ({x['ntri']} exact triads within {EPS_LOCK}c, tones within {lv['err']:.1f}c); "
                           f"subset degrees {sorted(k - lv['mode'] for k in lv['assign'])}; 1/1 = degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def main() -> dict:
    tasks = [(g, s) for g in GENERATORS for s in SEEDSETS]
    with Pool(WORKERS) as pool:
        rows = pool.map(run_pair, tasks, chunksize=1)
    facts = {s: genus_facts(v) for s, v in SEEDSETS.items()}
    for r in rows:
        r["genus"] = facts[r["seeds"]]
        r["coverage_level"] = coverage(r)
        r["coverage_any"] = coverage(r, "any")
        r["transition_summary"] = trans_summary(r)
    verdicts = {"P-D1": verdict_p_d1(rows), "P-D2": verdict_p_d2(rows), "P-D3": verdict_p_d3(rows),
                "P-D4": verdict_p_d4(rows), "P-D5": verdict_p_d5(rows), "P-D6": verdict_p_d6(rows)}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": DYNMOS001_VERSION, "scorer_version": SCORER_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "tone_cap_cents": CAP, "N_range": [N_MIN, N_MAX],
        "generators": GENERATORS, "seedsets": {k: list(v) for k, v in SEEDSETS.items()}, "genus": facts,
        "table": [{"generator": r["generator"], "g_cents": r["g_cents"], "seeds": r["seeds"], "levels": r["levels"],
                   "level": r["coverage_level"], "any": r["coverage_any"], "transitions": r["transition_summary"]} for r in rows],
        "verdicts": verdicts, "scl_files": write_scl(rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  cap {receipt['tone_cap_cents']}c  genus {receipt['genus']}")
    for r in receipt["table"]:
        c, a, t = r["level"], r["any"], r["transitions"]
        print(f"  {r['seeds']:9s} {r['generator']:14s} {r['g_cents']:8.3f} L={r['levels']}\n"
              f"     hex {c['hexany'][0]}/{c['hexany'][1]} (any {a['hexany'][0]}) dek {c['dekany'][0]}/{c['dekany'][1]} (any {a['dekany'][0]}) "
              f"tet {c['tetrad'][0]}/{c['tetrad'][1]} inc {c['incidences'][0]}/{c['incidences'][1]} err {c['max_err']} hexN {c['hexN']} dekN {c['dekN']} | "
              f"affinity {t['affinity_pairs']} retuned {t['retuned']}/{t['common']} contrast {t['contrast_pairs']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
