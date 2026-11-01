"""EPS-TIER-002 (G-027): the tolerance tiers re-run with Marcus's own ear.

G-026 held every tier above LOCK until EAR-eps gave Marcus's lock-loss
thresholds, and asked for a report-layer filter that collapses pitches
closer than epsilon. G-025 passed on 2026-11-01; this runner reads its
receipt and derives the tiers from it:

  LOCK  (2.00, 2.00)   scorer default
  EAR   (P, S)         stricter side of the major third (P) and of the
                       minor third (S), sitting 2: 8.43 / 7.43 (primary)
  EAR5  (F, F)         stricter side of the fifth, 4.0: sensitivity only,
                       because the P class also holds 2:3:4 shapes
  ET5, ET7             EPS-TIER-001's tiers, for continuity

Part A re-runs EPS-TIER-001's sweep (MOS on the 1c grid, N = 5..22, and the
70 HEX-001 hexanies) at every tier, raw and collapsed. Part B scores the
audition scales of the seven gates waiting on Marcus's ear as whole scales.
Predictions F1-F5 are in LOG.md (2026-11-01, before this file existed).

Stdlib only, deterministic, no wall-clock fields. scorer.py is untouched;
epsilon and the collapse filter live in this report layer.

Run from experiments/triads/:
    python3.12 epstier002.py
Writes results/epstier002.jsonl and results/epstier002_summary.json.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import epstier001 as et1  # noqa: E402
import scorer  # noqa: E402
from families.cps import hexany, odd_seed_sets  # noqa: E402
from families.mos import mos_scales  # noqa: E402

VERSION = "1.0.0"
EAREPS = HERE.parent / "lattice" / "results" / "eareps_results.json"
SCL_ROOT = HERE.parent / "lattice" / "results" / "scl"
GATE_FOLDERS = {"G-028": "meru001", "G-030": "meru002", "G-033": "rank3001", "G-035": "gold001",
                "G-036": "subfit001", "G-037": "subfit002", "G-039": "dynmos001"}
ORDER = ("LOCK", "EAR", "EAR5", "ET5", "ET7")
ET1_LOCK_VS_ET5_MEDIAN = 0.155     # EPS-TIER-001 receipt, F2's line


def _stricter(th: dict, fam: str) -> float:
    sides = [th[f"{fam}-{s}"]["T"] for s in ("sharp", "flat")]
    finite = [t for t in sides if t is not None]
    if not finite:
        raise ValueError(f"family {fam} has no finite threshold")
    return min(finite)


def tiers(path: Path = EAREPS) -> dict[str, tuple[float, float]]:
    th = json.loads(Path(path).read_text())["thresholds"]
    anchors = et1.tier_anchors()
    p, s, f = _stricter(th, "A"), _stricter(th, "C"), _stricter(th, "B")
    return {"LOCK": (anchors["LOCK"], anchors["LOCK"]), "EAR": (p, s), "EAR5": (f, f),
            "ET5": (anchors["ET5"], anchors["ET5"]), "ET7": (anchors["ET7"], anchors["ET7"])}


def collapse(cents: tuple[float, ...], eps: float) -> tuple[float, ...]:
    """Merge pitch classes closer than eps (single linkage, across the octave
    wrap); keep each cluster's lowest member, and 0 for the root's cluster."""
    pcs = sorted({c % 1200.0 for c in cents})
    if len(pcs) < 2:
        return tuple(pcs)
    clusters = [[pcs[0]]]
    for c in pcs[1:]:
        if c - clusters[-1][-1] < eps:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    if len(clusters) > 1 and (1200.0 - clusters[-1][-1]) + clusters[0][0] < eps:
        clusters[0] = clusters.pop() + clusters[0]
    reps = [0.0 if 0.0 in cl else cl[0] for cl in clusters]
    return tuple(sorted(reps))


def min_step(cents: tuple[float, ...]) -> float:
    pcs = sorted({c % 1200.0 for c in cents})
    return min([b - a for a, b in zip(pcs, pcs[1:])] + [1200.0 - pcs[-1] + pcs[0]])


def score_tier(cents: tuple[float, ...], tier: tuple[float, float], collapsed: bool) -> dict:
    """P at eps_P and S at eps_S (G read from the eps_P call)."""
    out, runs = {}, {}
    for cls, eps in (("P", tier[0]), ("S", tier[1])):
        scale = collapse(cents, eps) if collapsed else tuple(cents)
        key = (eps, scale)
        if key not in runs:
            runs[key] = scorer.score_tempered(scale, eps)
        out[cls] = (runs[key], len(scale))
    (rp, np_), (rs, ns) = out["P"], out["S"]
    return {"PSG": [rp.proportional, rs.subcontrary, rp.geometric], "N_eff": [np_, ns]}


def score_all(cents: tuple[float, ...], ts: dict) -> dict:
    return {t: {"raw": score_tier(cents, ts[t], False), "collapsed": score_tier(cents, ts[t], True)}
            for t in ORDER}


def read_scl(path: Path) -> tuple[float, ...]:
    lines = [ln.strip() for ln in Path(path).read_text().splitlines() if not ln.strip().startswith("!")]
    count = int(lines[1].split()[0])
    vals = []
    for ln in lines[2:2 + count]:
        tok = ln.split()[0]
        vals.append(float(tok) if "." in tok else 1200.0 * math.log2(float(Fraction(tok))))
    # degree 0 is implicit; the last listed value is the period
    return tuple([0.0] + [v % 1200.0 for v in vals[:-1]])


def gate_files(gate: str) -> list[Path]:
    return sorted((SCL_ROOT / GATE_FOLDERS[gate]).glob("*.scl"))


def part_a(ts: dict) -> tuple[list[dict], list[dict]]:
    mos = []
    for i in range(1, int(round(600.0 / et1.GEN_STEP_CENTS)) + 1):
        g = i * et1.GEN_STEP_CENTS
        for card, scale in mos_scales(g / 1200.0).items():
            mos.append({"family": "mos", "generator_cents": g, "cardinality": card,
                        "min_step": round(min_step(scale), 6), "tiers": score_all(scale, ts)})
    hexes = []
    for seeds in odd_seed_sets(4, 15):
        ratios = hexany(seeds)
        exact = scorer.score(ratios)
        cents = tuple(1200.0 * math.log2(float(r)) for r in ratios)
        hexes.append({"family": "hexany", "seeds": list(seeds),
                      "exact_PSG": [exact.proportional, exact.subcontrary, exact.geometric],
                      "min_step": round(min_step(cents), 6), "tiers": score_all(cents, ts)})
    return mos, hexes


def part_b(ts: dict) -> list[dict]:
    rows = []
    for gate in GATE_FOLDERS:
        for f in gate_files(gate):
            cents = read_scl(f)
            rows.append({"family": "audition", "gate": gate, "file": f.name, "N": len(cents),
                         "min_step": round(min_step(cents), 6),
                         "tiers": {t: score_all(cents, ts)[t] for t in ("LOCK", "EAR", "EAR5")}})
    return rows


def _ps(row: dict, tier: str, mode: str) -> int:
    psg = row["tiers"][tier][mode]["PSG"]
    return psg[0] + psg[1]


def _winners(rows: list[dict], tier: str, mode: str) -> dict[int, float]:
    by_n: dict[int, list[dict]] = {}
    for r in rows:
        by_n.setdefault(r["cardinality"], []).append(r)
    return {n: max(rs, key=lambda r: (r["tiers"][tier][mode]["PSG"][0], -r["generator_cents"]))["generator_cents"]
            for n, rs in sorted(by_n.items())}


def summarize(mos: list[dict], hexes: list[dict], aud: list[dict], ts: dict) -> dict:
    by_n: dict[int, list[dict]] = {}
    for r in mos:
        by_n.setdefault(r["cardinality"], []).append(r)
    w_raw, w_col = _winners(mos, "ET7", "raw"), _winners(mos, "ET7", "collapsed")
    f1 = sum(w_raw[n] != w_col[n] for n in w_raw)
    rho = {}
    for b in ("EAR", "EAR5", "ET5", "ET7"):
        per_n = {n: et1.spearman([r["tiers"]["LOCK"]["raw"]["PSG"][0] for r in rs],
                                 [r["tiers"][b]["collapsed"]["PSG"][0] for r in rs]) for n, rs in sorted(by_n.items())}
        finite = [v for v in per_n.values() if not math.isnan(v)]
        rho[f"LOCK_vs_{b}_collapsed"] = {"per_N": {n: round(v, 3) for n, v in per_n.items()},
                                         "median": round(statistics.median(finite), 3)}
    eps_p = ts["EAR"][0]
    f3_rows = sum(r["min_step"] < eps_p for r in mos)
    gains = {t: {m: sum(_ps(h, t, m) > h["exact_PSG"][0] + h["exact_PSG"][1] for h in hexes)
                 for m in ("raw", "collapsed")} for t in ORDER}
    collapsed_share = {t: round(sum(r["tiers"][t]["collapsed"]["N_eff"][0] < r["cardinality"] for r in mos) / len(mos), 4)
                       for t in ORDER}
    edo = next(r for r in by_n[12] if r["generator_cents"] == et1.TWELVE_EDO_GEN)

    gates = {}
    for gate in GATE_FOLDERS:
        rows = [r for r in aud if r["gate"] == gate]
        def top(tier, mode):
            return max(rows, key=lambda r: (_ps(r, tier, mode), r["file"]))["file"]
        gates[gate] = {
            "top_LOCK": top("LOCK", "raw"), "top_EAR_collapsed": top("EAR", "collapsed"),
            "changed": top("LOCK", "raw") != top("EAR", "collapsed"),
            "scales": [{"file": r["file"], "N": r["N"], "min_step": r["min_step"],
                        "LOCK": r["tiers"]["LOCK"]["raw"]["PSG"],
                        "EAR_raw": r["tiers"]["EAR"]["raw"]["PSG"],
                        "EAR_collapsed": r["tiers"]["EAR"]["collapsed"]["PSG"],
                        "EAR_N_eff": r["tiers"]["EAR"]["collapsed"]["N_eff"],
                        "EAR5_collapsed": r["tiers"]["EAR5"]["collapsed"]["PSG"]} for r in rows],
        }
    f5 = sum(g["changed"] for g in gates.values())

    return {
        "experiment": "EPS-TIER-002", "version": VERSION, "gate": "G-027",
        "scorer_version": scorer.SCORER_VERSION,
        "scorer_sha256": (HERE / "scorer.sha256").read_text().split()[0],
        "tiers": {t: list(ts[t]) for t in ORDER},
        "rows": {"mos": len(mos), "hexany": len(hexes), "audition": len(aud)},
        "predictions": {
            "F1": {"verdict": "KEPT" if f1 >= 14 else "REFUTED", "ET7_winners_changed_by_collapse": f1, "of": len(w_raw)},
            "F2": {"verdict": "KEPT" if rho["LOCK_vs_EAR_collapsed"]["median"] > ET1_LOCK_VS_ET5_MEDIAN else "REFUTED",
                   "median_rho_LOCK_vs_EAR": rho["LOCK_vs_EAR_collapsed"]["median"], "line": ET1_LOCK_VS_ET5_MEDIAN},
            "F3": {"verdict": "KEPT" if f3_rows / len(mos) < 0.10 else "REFUTED",
                   "mos_rows_with_step_below_eps_P": f3_rows, "share": round(f3_rows / len(mos), 4)},
            "F4": {"verdict": "KEPT" if gains["EAR"]["collapsed"] <= 20 else "REFUTED",
                   "hexanies_gaining_at_EAR_collapsed": gains["EAR"]["collapsed"]},
            "F5": {"verdict": "KEPT" if f5 >= 2 else "REFUTED", "gates_whose_top_changed": f5},
        },
        "spearman_P": rho,
        "collapsed_share_mos": collapsed_share,
        "hexanies_gaining_triads": gains,
        "hexany_1357": {t: next(h for h in hexes if h["seeds"] == [1, 3, 5, 7])["tiers"][t]["collapsed"]["PSG"] for t in ORDER},
        "edo12_N12": {t: {m: edo["tiers"][t][m]["PSG"] for m in ("raw", "collapsed")} for t in ORDER},
        "ET7_winners": {"raw": w_raw, "collapsed": w_col},
        "EAR_winners_collapsed": _winners(mos, "EAR", "collapsed"),
        "LOCK_winners": _winners(mos, "LOCK", "raw"),
        "gates": gates,
    }


def main() -> None:
    ts = tiers()
    mos, hexes = part_a(ts)
    aud = part_b(ts)
    out = HERE / "results"
    with (out / "epstier002.jsonl").open("w", encoding="ascii") as fh:
        for r in mos + hexes + aud:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    summary = summarize(mos, hexes, aud, ts)
    (out / "epstier002_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({"tiers": summary["tiers"], "predictions": summary["predictions"]}, indent=1))


if __name__ == "__main__":
    main()
