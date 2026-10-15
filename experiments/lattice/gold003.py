"""GOLD-003 arm A — do CPSFIT-003's count-optimal survival segments contain
golden / silver nobles of complexity <= Q more often than randomly placed
segments of the same widths? (LOG.md pre-registration 2026-10-14; committed
before this file.)

Principle served (Marcus, 2026-10-14): nobility does not predict harmony,
there is no mechanism. The testable form of Erv's practice is "the noble
lies INSIDE the survival segment", never "the optimum is near a noble".

Objects: the distinct count-optimal segments of results/cpsfit003.jsonl
(distinct by rounded end points; 22 expected) and the overlap-merged set
(15 expected). Nobles from gold002.nobles(m, 60), folded to (0, 600]
cents, Q ladder 8/12/20/30/60. Statistic: segments containing at least
one noble of complexity <= Q. Null: NULL_N draws, each segment keeps its
width and is placed uniformly on (0, 600). Decision rule: signal at
p <= 0.005, hint in (0.005, 0.05], nothing above.

Frozen inputs (read-only): results/cpsfit003.jsonl (receipt of a frozen
runner), gold002.nobles (unchanged module).

Receipts: results/gold003.jsonl (one row per segment set x family x Q) +
results/gold003_summary.json. Stdlib only, seeded, deterministic; two runs
must be bit-identical.

Run from experiments/lattice/:  python3.12 gold003.py
"""

from __future__ import annotations

import bisect
import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gold002 as g2  # noqa: E402

GOLD003_VERSION = "1.0.0"
EXPERIMENT = "GOLD-003"
RESULTS_DIR = _HERE / "results"
CPSFIT003 = RESULTS_DIR / "cpsfit003.jsonl"
RESULTS = RESULTS_DIR / "gold003.jsonl"
SUMMARY = RESULTS_DIR / "gold003_summary.json"

CENTS = 1200.0
HALF = 600.0
Q_LADDER = (8, 12, 20, 30, 60)
Q_MAX = 60
NULL_N = 20000
NULL_SEED = 20261014
FAMILIES = ((1, "golden"), (2, "silver"))
SIGNAL_P = 0.005
HINT_P = 0.05
ROUND = 4

# Registered predictions (LOG 2026-10-14): counts by Q, null means, p-values.
PREDICTIONS = {
    "P-G3-1": {"set": "distinct", "family": "golden", "n_segments": 22, "contained": (1, 3, 3, 4, 7),
               "null_mean": (0.12, 0.24, 0.68, 1.47, 5.12), "p": (0.11, 0.0012, 0.028, 0.054, 0.22), "signal_Q": (12,)},
    "P-G3-2": {"set": "distinct", "family": "silver", "n_segments": 22, "contained": (1, 1, 3, 3, 14),
               "null_mean": (0.17, 0.37, 1.02, 2.17, 6.90), "p": (0.16, 0.31, 0.077, 0.37, 0.0007), "signal_Q": (60,)},
    "P-G3-3": {"set": "merged", "n_segments": 15,
               "golden": {"contained": (1, 2, 2, 3, 6), "p": (0.075, 0.0095, 0.070, 0.068, 0.090)},
               "silver": {"contained": (1, 1, 3, 3, 9), "p": (0.11, 0.22, 0.024, 0.16, 0.011)}, "signal_Q": ()},
    "P-G3-4": {"golden_Q12": {317.170: "3/11,1/4", 503.786: "2/3,1/2"},
               "silver_Q20": {351.472: "0/1,1/1", 316.827: "4/15,5/19", 77.850: "1/13,0/1"}},
    "P-G3-5": {"expect": "hint at most: distinct golden Q=12 is a signal, merged golden Q=12 is a hint, nothing else"},
}
P_TOL = 0.5      # a registered p is kept when the measured p is within a factor of 1.5 (null draws are seeded but the scratch RNG stream differs)
MEAN_TOL = 0.15


# ---------------------------------------------------------------------------
# segments
# ---------------------------------------------------------------------------


def load_segments(path: Path = CPSFIT003) -> list[dict]:
    """Distinct count-optimal segments of CPSFIT-003, by rounded end points."""
    rows = [json.loads(line) for line in path.open()]
    segs: dict[tuple[float, float], dict] = {}
    for r in rows:
        lo, hi = r["segment_cents"]
        key = (round(lo, ROUND), round(hi, ROUND))
        s = segs.setdefault(key, {"lo": lo, "hi": hi, "w": hi - lo, "g": r["g_cents"], "count": r["count_exact"],
                                  "lattices": [], "Ns": []})
        lat = r["lattice"].replace("refl", "")
        if lat not in s["lattices"]:
            s["lattices"].append(lat)
        s["Ns"].append(r["N"])
    out = sorted(segs.values(), key=lambda s: s["lo"])
    for s in out:
        s["Ns"] = sorted(set(s["Ns"]))
    return out


def merge_segments(segs: list[dict]) -> list[dict]:
    """Union of overlapping segments across lattices (sorted by lo)."""
    out: list[dict] = []
    for s in sorted(segs, key=lambda s: s["lo"]):
        if out and s["lo"] <= out[-1]["hi"]:
            m = out[-1]
            m["hi"] = max(m["hi"], s["hi"])
            m["w"] = m["hi"] - m["lo"]
            m["lattices"] = sorted(set(m["lattices"]) | set(s["lattices"]))
            m["Ns"] = sorted(set(m["Ns"]) | set(s["Ns"]))
        else:
            out.append({"lo": s["lo"], "hi": s["hi"], "w": s["w"], "g": s["g"], "count": s["count"],
                        "lattices": list(s["lattices"]), "Ns": list(s["Ns"])})
    return out


# ---------------------------------------------------------------------------
# containment and null
# ---------------------------------------------------------------------------


def noble_cents(m: int, Q: int) -> list[tuple[float, str, int]]:
    """Nobles of complexity <= Q as (cents in (0, 600], seeds, complexity), sorted."""
    return sorted((c[0] * CENTS, c[1], c[2]) for c in g2.nobles(m, Q_MAX) if c[2] <= Q)


def contained(cs: list[float], lo: float, hi: float) -> int | None:
    """Index of the first noble in [lo, hi], or None."""
    i = bisect.bisect_left(cs, lo)
    return i if i < len(cs) and cs[i] <= hi else None


def observed(cs: list[float], segs: list[dict]) -> list[int | None]:
    return [contained(cs, s["lo"], s["hi"]) for s in segs]


def null_counts(cs: list[float], widths: list[float], n: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        k = 0
        for w in widths:
            lo = rng.uniform(0.0, HALF - w)
            if contained(cs, lo, lo + w) is not None:
                k += 1
        out.append(k)
    return out


def test_row(set_name: str, segs: list[dict], m: int, family: str, Q: int, seed: int) -> dict:
    nobles = noble_cents(m, Q)
    cs = [c[0] for c in nobles]
    obs = observed(cs, segs)
    n_obs = sum(i is not None for i in obs)
    null = null_counts(cs, [s["w"] for s in segs], NULL_N, seed)
    p = sum(k >= n_obs for k in null) / NULL_N
    verdict = "signal" if p <= SIGNAL_P else "hint" if p <= HINT_P else "nothing"
    hits = [{"lo": s["lo"], "hi": s["hi"], "w": s["w"], "g": s["g"], "count": s["count"], "lattices": s["lattices"], "Ns": s["Ns"],
             "noble_cents": nobles[i][0], "seeds": nobles[i][1], "complexity": nobles[i][2]}
            for s, i in zip(segs, obs) if i is not None]
    return {"experiment": EXPERIMENT, "set": set_name, "family": family, "m": m, "Q": Q, "n_nobles": len(cs), "n_segments": len(segs),
            "contained": n_obs, "null_mean": sum(null) / NULL_N, "null_n": NULL_N, "null_seed": seed, "p_ge": p, "verdict": verdict, "hits": hits}


def run() -> list[dict]:
    distinct = load_segments()
    merged = merge_segments(distinct)
    rows = []
    seed = NULL_SEED
    for set_name, segs in (("distinct", distinct), ("merged", merged)):
        for m, family in FAMILIES:
            for Q in Q_LADDER:
                rows.append(test_row(set_name, segs, m, family, Q, seed))
                seed += 1
    return rows


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def _rows_for(rows, set_name, family):
    return {r["Q"]: r for r in rows if r["set"] == set_name and r["family"] == family}


def _p_ok(measured: float, registered: float) -> bool:
    if registered <= SIGNAL_P or measured <= SIGNAL_P:
        return (measured <= SIGNAL_P) == (registered <= SIGNAL_P)
    return abs(measured - registered) <= P_TOL * registered


def verdict_counts(rows, key: str) -> dict:
    p = PREDICTIONS[key]
    fails = []
    by = _rows_for(rows, p["set"], p["family"])
    if by and next(iter(by.values()))["n_segments"] != p["n_segments"]:
        fails.append(f"n_segments {next(iter(by.values()))['n_segments']} vs {p['n_segments']}")
    for Q, c, mu, pr in zip(Q_LADDER, p["contained"], p["null_mean"], p["p"]):
        r = by.get(Q)
        if r is None:
            fails.append(f"Q={Q} missing")
            continue
        if r["contained"] != c:
            fails.append(f"Q={Q} contained {r['contained']} vs {c}")
        if abs(r["null_mean"] - mu) > MEAN_TOL * max(mu, 0.1):
            fails.append(f"Q={Q} null mean {r['null_mean']:.2f} vs {mu}")
        if not _p_ok(r["p_ge"], pr):
            fails.append(f"Q={Q} p {r['p_ge']:.4f} vs {pr}")
        if (r["p_ge"] <= SIGNAL_P) != (Q in p["signal_Q"]):
            fails.append(f"Q={Q} signal status {r['verdict']}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g3_3(rows) -> dict:
    p = PREDICTIONS["P-G3-3"]
    fails = []
    for family in ("golden", "silver"):
        by = _rows_for(rows, "merged", family)
        for Q, c, pr in zip(Q_LADDER, p[family]["contained"], p[family]["p"]):
            r = by.get(Q)
            if r is None:
                fails.append(f"{family} Q={Q} missing")
                continue
            if r["n_segments"] != p["n_segments"]:
                fails.append(f"{family} n_segments {r['n_segments']} vs {p['n_segments']}")
            if r["contained"] != c:
                fails.append(f"{family} Q={Q} contained {r['contained']} vs {c}")
            if not _p_ok(r["p_ge"], pr):
                fails.append(f"{family} Q={Q} p {r['p_ge']:.4f} vs {pr}")
            if r["p_ge"] <= SIGNAL_P:
                fails.append(f"{family} Q={Q} reached signal level")
    return {"kept": not fails, "failures": fails}


def verdict_p_g3_4(rows) -> dict:
    p = PREDICTIONS["P-G3-4"]
    fails = []
    for (family, Q, key) in (("golden", 12, "golden_Q12"), ("silver", 20, "silver_Q20")):
        r = _rows_for(rows, "distinct", family).get(Q)
        got = {round(h["noble_cents"], 3): h["seeds"] for h in (r["hits"] if r else [])}
        want = {round(k, 3): v for k, v in p[key].items()}
        if got != want:
            fails.append(f"{key}: {got} vs {want}")
    return {"kept": not fails, "failures": fails}


def verdict_p_g3_5(rows) -> dict:
    signals = sorted((r["set"], r["family"], r["Q"]) for r in rows if r["verdict"] == "signal")
    want = [("distinct", "golden", 12), ("distinct", "silver", 60)]
    merged_g12 = _rows_for(rows, "merged", "golden").get(12)
    fails = []
    if signals != want:
        fails.append(f"signals {signals} vs {want}")
    if merged_g12 is None or merged_g12["verdict"] != "hint":
        fails.append(f"merged golden Q=12 is {merged_g12 and merged_g12['verdict']}")
    return {"kept": not fails, "failures": fails}


# ---------------------------------------------------------------------------
# receipts
# ---------------------------------------------------------------------------


def main() -> dict:
    rows = run()
    verdicts = {"P-G3-1": verdict_counts(rows, "P-G3-1"), "P-G3-2": verdict_counts(rows, "P-G3-2"),
                "P-G3-3": verdict_p_g3_3(rows), "P-G3-4": verdict_p_g3_4(rows), "P-G3-5": verdict_p_g3_5(rows)}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": GOLD003_VERSION, "source": CPSFIT003.name, "Q_ladder": list(Q_LADDER),
        "null_n": NULL_N, "null_seed": NULL_SEED, "signal_p": SIGNAL_P, "hint_p": HINT_P,
        "n_distinct_segments": rows[0]["n_segments"], "n_merged_segments": next(r["n_segments"] for r in rows if r["set"] == "merged"),
        "table": [{k: r[k] for k in ("set", "family", "Q", "n_nobles", "n_segments", "contained", "null_mean", "p_ge", "verdict")} for r in rows],
        "verdicts": verdicts,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  segments distinct {receipt['n_distinct_segments']} merged {receipt['n_merged_segments']}  null {receipt['null_n']}")
    for r in receipt["table"]:
        print(f"  {r['set']:8s} {r['family']:6s} Q={r['Q']:2d} nobles={r['n_nobles']:4d} contained={r['contained']:2d}/{r['n_segments']} "
              f"null={r['null_mean']:5.2f} p={r['p_ge']:.4f} {r['verdict']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}")


if __name__ == "__main__":
    _print_summary(main())
