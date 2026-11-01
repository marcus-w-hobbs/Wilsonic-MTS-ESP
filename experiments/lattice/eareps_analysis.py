"""EAR-eps analysis (gate G-025): Marcus's lock-loss thresholds, scored
exactly as pre-registered in LOG.md (2026-08-19, "EAR-ε pre-registration",
analysis plan and predictions P-E1/P-E2/P-E3). Nothing here was chosen
after the sitting except the code that executes the registered rule.

Rule, per family-direction (A/B/C x sharp/flat), rungs ordered by |delta|:
L = max |delta| judged "locked" (the delta = 0 rung counts as locked
territory, so L >= 0), K = min |delta| judged "broken", T = (L + K) / 2.
No "broken" rung -> right-censored (T > max rung). Even the smallest
nonzero rung "broken" -> T < that rung (the midpoint rule still gives the
number). A "broken" below a "locked" is flagged, not corrected. Validity:
a family whose delta = 0 catch trial is "broken" is invalid.

Inputs: results/eareps_responses.json (Marcus's sitting) and the unsealed
results/eareps_key.json. Output: results/eareps_results.json.
Stdlib only, deterministic, no wall-clock fields.

Run from experiments/lattice/ (sitting 1 is on record as
results/eareps_responses_sitting1.json -> results/eareps_results_sitting1.json):
    python3.12 eareps_analysis.py [responses.json] [results.json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
VERSION = "1.0.0"
VERDICTS = ("locked", "beating", "broken")
CULTURAL_EPS = 14.86        # P-E1's line, as registered
BAND = (6.0, 12.0)          # P-E1's committed band
FIFTH_LIMIT = 3.0           # P-E2
ASYM_MIN = 1.5              # P-E3
PC = 1.955001               # the 12-EDO fifth error, the P-E2b rungs


def threshold(rungs: list[tuple[float, str]]) -> dict:
    """rungs: (|delta|, verdict) for one family-direction, the delta = 0
    catch trial included. Returns the registered threshold record."""
    rungs = sorted(rungs)
    locked = [d for d, v in rungs if v == "locked"]
    broken = [d for d, v in rungs if v == "broken"]
    L = max(locked + [0.0])
    nonzero = [d for d, _ in rungs if d > 0]
    out = {"rungs": [{"abs_delta": round(d, 6), "verdict": v} for d, v in rungs],
           "L": round(L, 6), "K": None, "T": None, "censored": None,
           "non_monotone": bool(broken) and min(broken) < L,
           "transition_band": [round(d, 6) for d, v in rungs if v == "beating" and d > 0
                               and (not broken or d < min(broken))]}
    if not nonzero:
        out["censored"] = "no detuned rungs"
        return out
    broken = [d for d in broken if d > 0]
    if not broken:
        out["censored"] = f"T > {max(nonzero):g}"
        return out
    K = min(broken)
    out["K"] = round(K, 6)
    out["T"] = round((L + K) / 2, 6)
    if K == min(nonzero) and L == 0:
        out["censored"] = f"T < {K:g}"
    return out


def family_directions(key: dict, responses: dict) -> dict:
    """{'A-sharp': [...], ...} with the delta = 0 rung in both directions."""
    groups: dict[str, list[tuple[float, str]]] = {}
    for rid, k in key.items():
        if k["family"] not in ("A", "B", "C"):
            continue
        d, v = k["delta_cents"], responses[rid]["verdict"]
        dirs = ("sharp", "flat") if d == 0 else (("sharp",) if d > 0 else ("flat",))
        for side in dirs:
            groups.setdefault(f"{k['family']}-{side}", []).append((abs(d), v))
    return dict(sorted(groups.items()))


def catch_trials(key: dict, responses: dict) -> dict:
    return {k["family"]: {"rung": rid, "verdict": responses[rid]["verdict"],
                          "valid": responses[rid]["verdict"] != "broken"}
            for rid, k in sorted(key.items()) if k["family"] in ("A", "B", "C") and k["delta_cents"] == 0}


def below(t: dict, line: float) -> bool | None:
    """Is the threshold strictly below `line`? None when censoring leaves it open."""
    if t["T"] is not None:
        return t["T"] < line
    return False if t["censored"].startswith("T >") and float(t["censored"][4:]) >= line else None


def predictions(th: dict, key: dict, responses: dict) -> dict:
    a_s, a_f = th["A-sharp"], th["A-flat"]
    b_s, b_f = th["B-sharp"], th["B-flat"]
    # P-E1: both major-third thresholds below 14.86, committed band [6, 12].
    sides = [below(a_s, CULTURAL_EPS), below(a_f, CULTURAL_EPS)]
    in_band = all(t["T"] is not None and BAND[0] <= t["T"] <= BAND[1] for t in (a_s, a_f))
    pe1 = ("REFUTED" if False in sides else "OPEN (censored)" if None in sides
           else "KEPT" if in_band else "WEAK-KEPT")
    # P-E2: both fifth thresholds <= 3; a right-censored T > 3 refutes.
    def fifth_ok(t):
        if t["T"] is not None:
            return t["T"] <= FIFTH_LIMIT
        return t["censored"].startswith("T <")
    pe2 = "KEPT" if fifth_ok(b_s) and fifth_ok(b_f) else "REFUTED"
    # P-E2b: the +-1.955001 rungs are not "broken".
    pc = {rid: responses[rid]["verdict"] for rid, k in key.items()
          if k["family"] == "B" and abs(abs(k["delta_cents"]) - PC) < 1e-5}
    pe2b = "KEPT" if all(v != "broken" for v in pc.values()) else "REFUTED"
    # P-E3: T_A(sharp) - T_A(flat) >= 1.5.
    gap = None if a_s["T"] is None or a_f["T"] is None else round(a_s["T"] - a_f["T"], 6)
    pe3 = "OPEN (censored)" if gap is None else "KEPT" if gap >= ASYM_MIN else "REFUTED"
    return {
        "P-E1": {"verdict": pe1, "T_A_sharp": a_s["T"], "T_A_flat": a_f["T"], "band": list(BAND), "line": CULTURAL_EPS},
        "P-E2": {"verdict": pe2, "T_B_sharp": b_s["T"] or b_s["censored"], "T_B_flat": b_f["T"] or b_f["censored"], "limit": FIFTH_LIMIT},
        "P-E2b": {"verdict": pe2b, "rungs": dict(sorted(pc.items()))},
        "P-E3": {"verdict": pe3, "gap_sharp_minus_flat": gap, "min": ASYM_MIN},
    }


def pacing(responses: dict) -> dict:
    """Seconds between successive commits, in sitting order (descriptive)."""
    from datetime import datetime
    ts = sorted(datetime.fromisoformat(r["committedAt"].replace("Z", "+00:00"))
                for r in responses.values() if r.get("committedAt"))
    gaps = [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]
    if not gaps:
        return {}
    return {"rungs_timed": len(ts), "sitting_seconds": round((ts[-1] - ts[0]).total_seconds(), 1),
            "median_gap_seconds": round(median(gaps), 2), "min_gap_seconds": round(min(gaps), 2),
            "gaps_under_10s": sum(g < 10 for g in gaps), "gaps": len(gaps)}


def analyse(key: dict, sitting: dict) -> dict:
    responses = sitting["responses"]
    missing = [rid for rid in key if responses.get(rid, {}).get("verdict") not in VERDICTS]
    if missing:
        raise ValueError(f"no valid verdict for {missing}")
    th = {name: threshold(r) for name, r in family_directions(key, responses).items()}
    anchors = {k["description"]: responses[rid]["verdict"] for rid, k in sorted(key.items()) if k["family"] == "D"}
    c = {s: th[f"C-{s}"] for s in ("sharp", "flat")}
    return {
        "experiment": "EAR-eps", "analysis_version": VERSION, "gate": "G-025",
        "sitting": {k: sitting.get(k) for k in ("sitting_date", "synth_patch", "playback_chain")},
        "catch_trials": catch_trials(key, responses),
        "thresholds": th,
        "predictions": predictions(th, key, responses),
        "exploratory": {
            "T_C_sharp": c["sharp"]["T"] or c["sharp"]["censored"],
            "T_C_flat": c["flat"]["T"] or c["flat"]["censored"],
            "family_D": anchors,
        },
        "pacing": pacing(responses),
    }


def main() -> None:
    key = json.loads((RESULTS / "eareps_key.json").read_text())["rungs"]
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS / "eareps_responses.json"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else RESULTS / "eareps_results.json"
    sitting = json.loads(src.read_text())
    out = analyse(key, sitting)
    dst.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    for name, t in out["thresholds"].items():
        print(f"{name:8s} L={t['L']:<7g} K={t['K']!s:<7} T={t['T'] if t['T'] is not None else t['censored']}"
              f"{'  NON-MONOTONE' if t['non_monotone'] else ''}")
    for name, p in out["predictions"].items():
        print(f"{name:6s} {p['verdict']}")


if __name__ == "__main__":
    main()
