"""MERU-002 — the rho knob of the order lift (LOG.md pre-registration
2026-10-10; committed before this file).

Program A, second knob. MERU-001 lifted the order with (x^k - rho^k) at
rho = 1 only. Here rho runs over an exact rational ladder on three
recurrences chosen for their spread of |lambda2|/G (0.418935: 0.880,
Fibonacci: 0.382, meta-meantone: 0.867), hexany LIFT seeding as MERU-001.
Registered: the lock step follows rho alone (P-R1); the chain step follows
max(rho, |lambda2|) with a plateau below |lambda2| (P-R2); a longer
transient buys no harmony (P-R3); the crossover law re-registered with a
tolerance that scales with the time constant (P-R4); positivity (P-R5).
Predictions are pinned in PREDICTIONS below, verbatim from the LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score, score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)
Shared machinery is imported from meru001.py (not frozen; its rows for
rho = 1 are reproduced here as a cross-check, P-R4).

Receipts: results/meru002.jsonl (one row per recurrence x rho x W x n) +
results/meru002_summary.json; results/scl/meru002/*.scl ear-check stimuli.
Deterministic: stdlib only, exact Fractions, no randomness, no wall-clock
fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 meru002.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from math import log2
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scorer import SCORER_VERSION  # noqa: E402  (frozen v1.1.0, read-only)
from melodic import MELODIC_VERSION  # noqa: E402  (frozen v0.1.0, read-only)
import meru001 as m1  # noqa: E402

MERU002_VERSION = "1.0.0"
EXPERIMENT = "MERU-002"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "meru002.jsonl"
SUMMARY = RESULTS_DIR / "meru002_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "meru002"

CENTS = 1200.0
STEPS = 130
WINDOWS = (7, 12)
EPS_LOCK = 2.0
EPS_CHAIN = (2.0, 0.5)
N_SEED_TONES = 6

RECURRENCES = (
    ("erv418935", 1, 1, 32, 4, "0.418935 H[n-1] + 32 H[n-4] (Erv 16 Jul 97)"),
    ("fib", 1, 1, 1, 2, "0.694242 Fibonacci (Fig 12 #1)"),
    ("metameantone", 2, 3, 2, 4, "0.579692 meta-meantone 2H[n-3] + 2H[n-4]"),
)
RHO_LADDER = tuple(Fraction(s) for s in (
    "1/4", "1/2", "3/4", "1", "5/4", "11/8", "23/16", "3/2", "25/16", "7/4",
    "2", "9/4", "5/2", "21/8"))

PREDICTIONS = {
    "P-R1": {
        "W7": {"erv418935": {"1/4": 12, "1/2": 12, "3/4": 12, "1": 12, "5/4": 12,
                             "3/2": 12, "7/4": 14, "2": 18, "9/4": 28, "5/2": 72},
               "fib": {"1/4": 12, "1/2": 12, "3/4": 12, "1": 14, "5/4": 22, "3/2": 54},
               "metameantone": {"1/4": 12, "1/2": 12, "3/4": 13, "1": 13, "5/4": 23}},
        "W12": {"erv418935": {"1/4": 17, "1/2": 17, "3/4": 17, "1": 17, "5/4": 17,
                              "3/2": 17, "7/4": 17, "2": 18, "9/4": 28, "5/2": 72},
                "fib": {"1/4": 17, "1/2": 17, "3/4": 17, "1": 17, "5/4": 22, "3/2": 54},
                "metameantone": {"1/4": 17, "1/2": 17, "3/4": 17, "1": 17, "5/4": 23}},
        "intercept_bits": (5.5, 8.5), "plateau_margin": 2, "interp_tol": 2,
    },
    "P-R2": {
        "plateau_tol": 4, "law_range": (5.0, 8.5),
        "W7": {"erv418935": {"1/4": 53, "1/2": 53, "3/4": 53, "1": 53, "5/4": 53,
                             "3/2": 53, "7/4": 53, "2": 53, "9/4": 54, "5/2": 94},
               "fib": {"1/4": 16, "1/2": 16, "3/4": 17, "1": 22, "5/4": 31, "11/8": 43,
                       "23/16": 55, "3/2": 75, "25/16": 135},
               "metameantone": {"1/4": 46, "1/2": 44, "3/4": 44, "1": 39, "5/4": 40,
                                "11/8": 71, "23/16": 133}},
    },
    "P-R3": {"jitter": 0.5, "longest_max_P": 2.0, "ir_max": 3.0},
    "P-R4": {"abs_tol": 3, "rel_tol": 0.3},
    "P-R5": {"nonpositive": [("erv418935", "21/8")]},
}


# ---------------------------------------------------------------------------
# the lifted recurrence at rational rho
# ---------------------------------------------------------------------------


def lift_coefs(a: int, i: int, b: int, j: int, k: int, rho: Fraction) -> dict[int, Fraction]:
    """Coefficient map of p(x) * (x^k - rho^k), p(x) = x^j - a x^(j-i) - b."""
    coefs: dict[int, Fraction] = {i: Fraction(a), j: Fraction(b)}
    if k > 0:
        c = rho ** k
        for lag, v in ((k, c), (i + k, -a * c), (j + k, -b * c)):
            coefs[lag] = coefs.get(lag, Fraction(0)) + v
    return coefs


def run_lifted(rec: dict, rho: Fraction, tones: tuple[Fraction, ...],
               steps: int = STEPS) -> tuple[list[Fraction], int | None]:
    """Exact sequence and the index of the first non-positive term (or None)."""
    k = rec["lift_k"]
    coefs = lift_coefs(rec["a"], rec["i"], rec["b"], rec["j"], k, rho)
    seeds = m1.place_seeds(tones, rec["j"] + k, rec["log2G"], "LIFT")
    h = [Fraction(s) for s in seeds]
    for n in range(len(h), len(h) + steps):
        h.append(sum((c * h[n - lag] for lag, c in coefs.items()), Fraction(0)))
    bad = next((n for n, x in enumerate(h) if x <= 0), None)
    return h, bad


def tau_eff(rec: dict, rho: Fraction) -> float | None:
    r = max(rec["lambda2"], float(rho)) / rec["G"]
    return (1.0 / log2(1.0 / r)) if r < 1 else None


# ---------------------------------------------------------------------------
# series
# ---------------------------------------------------------------------------


def run_series(rec: dict, rho: Fraction, tones: tuple[Fraction, ...],
               tone_cents: list[float], classes: tuple[float, ...],
               steps: int = STEPS) -> tuple[list[dict], dict, list[Fraction]]:
    h, bad = run_lifted(rec, rho, tones, steps)
    n_seeds = rec["order_lift"]
    per: dict = {"rho": str(rho), "rho_float": float(rho), "n_seeds": n_seeds,
                 "rate_rho": float(rho) / rec["G"], "tau_eff": tau_eff(rec, rho),
                 "first_nonpositive": bad, "per_w": {}}
    rows: list[dict] = []
    if bad is not None:
        return rows, per, h
    for w in WINDOWS:
        wrows = []
        for n in range(w - 1, len(h)):
            row = m1.window_row(rec, "LIFT", w, n, h, n_seeds, tone_cents, classes)
            row.update({"experiment": EXPERIMENT, "rho": str(rho), "rho_float": float(rho)})
            wrows.append(row)
        rows.extend(wrows)
        post = [r for r in wrows if r["post_seed"]]
        n0 = post[0]["n"]
        n_chain = {str(e): next((r["n"] for r in post if r["chain_error_cents"] <= e), None)
                   for e in EPS_CHAIN}
        n_lock = next((r["n"] for r in post if r["rt"] and r["rt_residual_cents"] <= EPS_LOCK),
                      None)
        n2 = n_chain["2.0"]
        trans = [r for r in post if n2 is None or r["n"] < n2]
        per["per_w"][str(w)] = {
            "n0": n0, "n_lock": n_lock, "n_chain": n_chain,
            "delta_n": (n_chain["0.5"] - n2 if n2 is not None and n_chain["0.5"] is not None
                        else None),
            "transient_windows": len(trans),
            "mean_P_2c_transient": (sum(r["P_2c"] for r in trans) / len(trans)) if trans else None,
            "mean_S_2c_transient": (sum(r["S_2c"] for r in trans) / len(trans)) if trans else None,
            "mean_interval_retention_2c_transient": (
                sum(r["interval_retention_2c"] for r in trans) / len(trans)) if trans else None,
            "echo_windows": sum(1 for r in post if r["P"] > r["rt"]),
            "floor_violations": sum(1 for r in post if r["P"] < r["rt"]),
            "mirror_failures": sum(1 for r in wrows if not r["mirror_ok"]),
            "stationary": {k: wrows[-1][k] for k in (
                "n", "P", "S", "G", "P_2c", "S_2c", "rt", "chain_error_cents",
                "interval_retention_2c", "m1_gap_classes_2c", "m3_propriety")},
        }
    return rows, per, h


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def _ladder(summary: dict, rid: str) -> list[tuple[Fraction, dict]]:
    out = [(Fraction(r), per) for r, per in summary[rid].items()
           if per["first_nonpositive"] is None]
    return sorted(out, key=lambda t: t[0])


def verdict_p_r1(summary: dict, recs: dict) -> dict:
    p = PREDICTIONS["P-R1"]
    lo, hi = p["intercept_bits"]
    fails, checks, intercepts = [], 0, {}
    for rid in recs:
        for w in WINDOWS:
            reg = p[f"W{w}"][rid]
            prev = None
            for rho, per in _ladder(summary, rid):
                pw = per["per_w"][str(w)]
                nl = pw["n_lock"]
                checks += 1
                if nl is None:
                    fails.append(f"{rid} rho={rho} W={w}: no lock")
                    continue
                if prev is not None and nl < prev:
                    fails.append(f"{rid} rho={rho} W={w}: n_lock {nl} < previous {prev}")
                prev = nl
                key = str(rho)
                if key in reg and nl != reg[key]:
                    fails.append(f"{rid} rho={rho} W={w}: n_lock {nl} != registered {reg[key]}")
                if nl > pw["n0"] + p["plateau_margin"]:
                    bits = nl * log2(recs[rid]["G"] / float(rho))
                    intercepts[f"{rid} rho={rho} W={w}"] = bits
                    if not (lo <= bits <= hi):
                        fails.append(f"{rid} rho={rho} W={w}: intercept {bits:.2f} bits outside [{lo}, {hi}]")
    return {"kept": not fails, "checks": checks, "failures": fails, "intercepts_bits": intercepts}


def verdict_p_r2(summary: dict, recs: dict) -> dict:
    p = PREDICTIONS["P-R2"]
    lo, hi = p["law_range"]
    fails, laws = [], {}
    for rid, rec in recs.items():
        reg = p["W7"][rid]
        lam = rec["lambda2"]
        below = [(rho, per) for rho, per in _ladder(summary, rid) if float(rho) < lam]
        above = [(rho, per) for rho, per in _ladder(summary, rid) if float(rho) >= lam]
        vals = [per["per_w"]["7"]["n_chain"]["2.0"] for _, per in below]
        if any(v is None for v in vals):
            fails.append(f"{rid}: a below-lambda2 rho never reaches 2c")
        elif vals and max(vals) - min(vals) > 2 * p["plateau_tol"]:
            fails.append(f"{rid}: plateau spread {min(vals)}..{max(vals)} exceeds +/-{p['plateau_tol']}")
        prev = max(vals) if vals else None
        for rho, per in above:
            v = per["per_w"]["7"]["n_chain"]["2.0"]
            if v is None:
                fails.append(f"{rid} rho={rho}: never reaches 2c")
                continue
            if prev is not None and v <= prev:
                fails.append(f"{rid} rho={rho}: n_chain {v} not increasing above lambda2 (prev {prev})")
            prev = v
        for rho, per in _ladder(summary, rid):
            pw = per["per_w"]["7"]
            key = str(rho)
            if key in reg and pw["n_chain"]["2.0"] != reg[key]:
                fails.append(f"{rid} rho={rho}: n_chain {pw['n_chain']['2.0']} != registered {reg[key]}")
            tau = per["tau_eff"]
            if pw["n_chain"]["2.0"] is not None and tau:
                ratio = (pw["n_chain"]["2.0"] - pw["n0"]) / tau
                laws[f"{rid} rho={rho}"] = ratio
                if not (lo <= ratio <= hi):
                    fails.append(f"{rid} rho={rho}: (n_chain - n0)/tau = {ratio:.2f} outside [{lo}, {hi}]")
    return {"kept": not fails, "failures": fails, "law_ratios": laws}


def verdict_p_r3(summary: dict, recs: dict) -> dict:
    p = PREDICTIONS["P-R3"]
    fails, means = [], {}
    for rid in recs:
        lad = _ladder(summary, rid)
        prev = None
        longest, longest_mean = -1, None
        for rho, per in lad:
            pw = per["per_w"]["7"]
            mp, ir = pw["mean_P_2c_transient"], pw["mean_interval_retention_2c_transient"]
            means[f"{rid} rho={rho}"] = {"mean_P_2c": mp, "mean_ir": ir, "transient": pw["transient_windows"]}
            if mp is None:
                continue
            if rho >= 1 and prev is not None and mp > prev + p["jitter"]:
                fails.append(f"{rid} rho={rho}: mean P@2c {mp:.2f} rose above previous {prev:.2f} + {p['jitter']}")
            if rho >= 1:
                prev = mp
            if ir is not None and ir > p["ir_max"]:
                fails.append(f"{rid} rho={rho}: mean interval retention {ir:.2f} > {p['ir_max']}")
            if pw["echo_windows"]:
                fails.append(f"{rid} rho={rho}: {pw['echo_windows']} exact echo windows")
            if pw["transient_windows"] > longest:
                longest, longest_mean = pw["transient_windows"], mp
        allm = [v["mean_P_2c"] for k, v in means.items() if k.startswith(rid) and v["mean_P_2c"] is not None]
        if longest_mean is not None and (longest_mean > p["longest_max_P"] or longest_mean > min(allm) + 1e-9):
            fails.append(f"{rid}: longest transient mean P@2c {longest_mean:.2f} is not the minimum / exceeds {p['longest_max_P']}")
    return {"kept": not fails, "failures": fails, "means": means}


def verdict_p_r4(summary: dict, recs: dict) -> dict:
    p = PREDICTIONS["P-R4"]
    fails, table = [], {}
    for rid in recs:
        for rho, per in _ladder(summary, rid):
            tau = per["tau_eff"]
            for w in WINDOWS:
                dn = per["per_w"][str(w)]["delta_n"]
                if dn is None or tau is None:
                    continue
                pred = 2 * tau
                tol = max(p["abs_tol"], p["rel_tol"] * pred)
                table[f"{rid} rho={rho} W={w}"] = {"delta_n": dn, "pred": pred, "tol": tol}
                if abs(dn - pred) > tol:
                    fails.append(f"{rid} rho={rho} W={w}: delta_n {dn} vs {pred:.1f} (tol {tol:.1f})")
    return {"kept": not fails, "failures": fails, "table": table}


def verdict_p_r5(summary: dict) -> dict:
    reg = {tuple(x) for x in PREDICTIONS["P-R5"]["nonpositive"]}
    found = {(rid, rho) for rid, lad in summary.items() for rho, per in lad.items()
             if per["first_nonpositive"] is not None}
    return {"kept": found == reg, "registered": sorted(reg), "found": sorted(found),
            "first_index": {f"{rid} rho={rho}": per["first_nonpositive"]
                            for rid, lad in summary.items() for rho, per in lad.items()
                            if per["first_nonpositive"] is not None}}


# ---------------------------------------------------------------------------
# scl + main
# ---------------------------------------------------------------------------

SCL_PICKS = (("erv418935", Fraction(1)), ("erv418935", Fraction(5, 2)))
SCL_STEPS = (12, 40, 100)


def write_scl(rid: str, rho: Fraction, h: list[Fraction], label: str) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    w = 7
    for n in SCL_STEPS:
        cs = [m1.cents_of(x) for x in h[n - w + 1:n + 1]]
        name = f"meru002_{rid}_rho{rho.numerator}-{rho.denominator}_W7_n{n:03d}"
        text = m1.scl_text(name, f"MERU-002 {label}; hexany seeds; rho = {rho}; window of "
                           f"{w} at step {n}; 1/1 = lowest window tone",
                           [c - min(cs) for c in cs])
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def main(steps: int = STEPS) -> dict:
    tones = m1.hexany_tones()
    tone_cents = [m1.cents_of(t) for t in tones]
    classes = m1.interval_classes(tones)
    recs = {r[0]: {**m1.build_recurrence(*r[:5]), "label": r[5]} for r in RECURRENCES}
    all_rows: list[dict] = []
    summary: dict[str, dict] = {}
    scl_files: list[str] = []
    for rid, rec in recs.items():
        summary[rid] = {}
        for rho in RHO_LADDER:
            if float(rho) >= rec["G"]:
                continue
            rows, per, h = run_series(rec, rho, tones, tone_cents, classes, steps)
            all_rows.extend(rows)
            summary[rid][str(rho)] = per
            if (rid, rho) in SCL_PICKS and per["first_nonpositive"] is None and steps >= max(SCL_STEPS):
                scl_files += write_scl(rid, rho, h, rec["label"])
    verdicts = {
        "P-R1": verdict_p_r1(summary, recs),
        "P-R2": verdict_p_r2(summary, recs),
        "P-R3": verdict_p_r3(summary, recs),
        "P-R4": verdict_p_r4(summary, recs),
        "P-R5": verdict_p_r5(summary),
    }
    receipt = {
        "experiment": EXPERIMENT, "runner_version": MERU002_VERSION,
        "meru001_version": m1.MERU001_VERSION,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "steps": steps, "windows": list(WINDOWS),
        "rho_ladder": [str(r) for r in RHO_LADDER],
        "seed_tones": [str(t) for t in tones],
        "recurrences": {rid: {k: v for k, v in rec.items() if k not in ("coefs_exact", "coefs_lift")}
                        for rid, rec in recs.items()},
        "n_rows": len(all_rows),
        "mirror_failures": sum(1 for r in all_rows if not r["mirror_ok"]),
        "per_recurrence": summary, "verdicts": verdicts, "scl_files": scl_files,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  melodic {receipt['melodic_version']}  "
          f"rows={receipt['n_rows']}  mirror failures={receipt['mirror_failures']}")
    for rid, lad in receipt["per_recurrence"].items():
        for rho, per in lad.items():
            if per["first_nonpositive"] is not None:
                print(f"  {rid:13s} rho={rho:5s} NON-POSITIVE at n={per['first_nonpositive']}")
                continue
            w7 = per["per_w"]["7"]
            print(f"  {rid:13s} rho={rho:5s} rate={per['rate_rho']:.3f} n_lock={w7['n_lock']} "
                  f"n_chain={w7['n_chain']} dn={w7['delta_n']} transient={w7['transient_windows']} "
                  f"meanP2c={w7['mean_P_2c_transient'] and round(w7['mean_P_2c_transient'], 2)} "
                  f"meanIR={w7['mean_interval_retention_2c_transient'] and round(w7['mean_interval_retention_2c_transient'], 2)}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}"
              + (f"  {v['failures'][:3]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {len(receipt['scl_files'])}")


if __name__ == "__main__":
    _print_summary(main())
