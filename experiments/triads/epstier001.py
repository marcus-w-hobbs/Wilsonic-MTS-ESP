"""EPS-TIER-001: three-tier epsilon sweep (lock / 12-ET 5-limit / 12-ET 7-limit).

Question (Marcus, 2026-09-29): should the tempered-path tolerance be set by
what 12-ET has made acceptable for centuries? This sweep scores every MOS
(1-cent generator grid, N = 5..22) and every hexany of HEX-001 (70 odd seed
sets from {1..15}, cents path) at three tiers of the frozen scorer's epsilon:

  LOCK    2.00¢   scorer default; the tier Marcus's ear check validated
  ET5    14.86¢   12-EDO major 0-4-7 vs the arithmetic mean of its outer
                  tones (= 12-EDO minor vs the harmonic mean); ET-001's
                  "cultural epsilon"
  ET7    32.01¢   12-EDO 7-10-12 vs 6:7:8's arithmetic mean, the worst of
                  12-EDO's 7-limit AP chords (5:6:7 as 0-3-6 is 25.86¢)

The tiers are measured, not chosen: tier_anchors() re-derives both 12-ET
numbers from 2**(k/12). Epsilon is a comparison-layer parameter of the
frozen scorer, so nothing in scorer.py changes.

PRE-REGISTERED PREDICTIONS (written before the first run, 2026-09-29):
  E1  P = S holds for every MOS at every tier (inversion theorem rail).
  E2  The degeneracy guard's dropped share grows with epsilon, and at ET7
      exceeds 30% of all labelled triples.
  E3  12-EDO (g = 500¢, N = 12) is outside the top 10 of N = 12 by P at LOCK
      and inside the top 3 at ET5 (the tier is defined by it).
  E4  Tiers measure different things: median over N of the Spearman rank
      correlation of P across generators, LOCK vs ET5, is below 0.5.
  E5  Hexanies: the cents path at LOCK reproduces the exact-rational
      anchored (P, S, G) for all 70 seed sets; at ET5 at least half of the
      hexanies gain triads the exact math does not contain.

Run from experiments/triads/:
    python3.12 epstier001.py
Writes results/epstier001.jsonl and results/epstier001_summary.json.
"""

from __future__ import annotations

import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scorer  # noqa: E402
from families.cps import hexany, odd_seed_sets  # noqa: E402
from families.mos import mos_scales  # noqa: E402

GEN_STEP_CENTS = 1.0
TWELVE_EDO_GEN = 500.0


def _cents(ratio: float) -> float:
    return 1200.0 * math.log2(ratio)


def _edo12(step: int) -> float:
    return 2.0 ** (step / 12.0)


def middle_vs_am_cents(lo: int, mid: int, hi: int) -> float:
    """Signed cents from the arithmetic mean of 12-EDO steps lo, hi to mid."""
    a, x, b = _edo12(lo), _edo12(mid), _edo12(hi)
    return _cents(x / ((a + b) / 2.0))


def tier_anchors() -> dict[str, float]:
    """The three tiers, with the 12-ET two derived from equal temperament."""
    return {
        "LOCK": scorer.DEFAULT_EPSILON_CENTS,
        "ET5": round(abs(middle_vs_am_cents(0, 4, 7)), 2),
        "ET7": round(abs(middle_vs_am_cents(7, 10, 12)), 2),
    }


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rho with average ranks for ties; nan if either is constant."""
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=v.__getitem__)
        out = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2.0
            i = j + 1
        return out
    rx, ry = ranks(xs), ranks(ys)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return float("nan")
    return statistics.correlation(rx, ry)


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _score(cents: tuple[float, ...], eps: float) -> dict:
    r = scorer.score_tempered(cents, eps)
    return {"PSG": [r.proportional, r.subcontrary, r.geometric],
            "raw": [r.proportional_raw, r.subcontrary_raw, r.geometric_raw],
            "dropped": r.degenerate_dropped}


def sweep_mos(tiers: dict[str, float]) -> list[dict]:
    rows = []
    n_gen = int(round(600.0 / GEN_STEP_CENTS))
    for i in range(1, n_gen + 1):
        g = i * GEN_STEP_CENTS
        for card, scale in mos_scales(g / 1200.0).items():
            rows.append({"family": "mos", "generator_cents": g,
                         "cardinality": card,
                         "tiers": {t: _score(scale, e)
                                   for t, e in tiers.items()}})
    return rows


def sweep_hexany(tiers: dict[str, float]) -> list[dict]:
    rows = []
    for seeds in odd_seed_sets(4, 15):
        ratios = hexany(seeds)
        exact = scorer.score(ratios)
        cents = tuple(_cents(float(r)) for r in ratios)
        rows.append({"family": "hexany", "seeds": list(seeds),
                     "exact_PSG": [exact.proportional, exact.subcontrary,
                                   exact.geometric],
                     "tiers": {t: _score(cents, e)
                               for t, e in tiers.items()}})
    return rows


def _rank_of(rows: list[dict], tier: str, g: float) -> int:
    """1-based competition rank of generator g by P (higher is better)."""
    target = next(r for r in rows if r["generator_cents"] == g)
    p = target["tiers"][tier]["PSG"][0]
    return 1 + sum(r["tiers"][tier]["PSG"][0] > p for r in rows)


def summarize(mos: list[dict], hexes: list[dict],
              tiers: dict[str, float]) -> dict:
    names = list(tiers)
    by_n: dict[int, list[dict]] = {}
    for r in mos:
        by_n.setdefault(r["cardinality"], []).append(r)

    ps_violations = sum(r["tiers"][t]["PSG"][0] != r["tiers"][t]["PSG"][1]
                        for r in mos for t in names)

    dropped_share = {}
    for t in names:
        dropped = sum(r["tiers"][t]["dropped"] for r in mos)
        labelled = sum(sum(r["tiers"][t]["raw"]) for r in mos)
        dropped_share[t] = dropped / labelled if labelled else 0.0

    rho = {}
    for a, b in (("LOCK", "ET5"), ("LOCK", "ET7"), ("ET5", "ET7")):
        per_n = {n: spearman([r["tiers"][a]["PSG"][0] for r in rows],
                             [r["tiers"][b]["PSG"][0] for r in rows])
                 for n, rows in sorted(by_n.items())}
        finite = [v for v in per_n.values() if not math.isnan(v)]
        rho[f"{a}_vs_{b}"] = {
            "per_N": {n: round(v, 3) for n, v in per_n.items()},
            "median": round(statistics.median(finite), 3)}

    best = {t: {n: max(rows, key=lambda r: (r["tiers"][t]["PSG"][0],
                                            -r["generator_cents"]))
                for n, rows in sorted(by_n.items())} for t in names}
    best_table = {t: {n: {"g": r["generator_cents"],
                          "PSG": r["tiers"][t]["PSG"]}
                      for n, r in best[t].items()} for t in names}

    edo12_rank = {t: _rank_of(by_n[12], t, TWELVE_EDO_GEN) for t in names}
    edo12_psg = {t: next(r for r in by_n[12]
                         if r["generator_cents"] == TWELVE_EDO_GEN
                         )["tiers"][t]["PSG"] for t in names}

    rail_mismatch = [h["seeds"] for h in hexes
                     if h["tiers"]["LOCK"]["PSG"] != h["exact_PSG"]]
    gains = {t: sum(sum(h["tiers"][t]["PSG"][:2]) > sum(h["exact_PSG"][:2])
                    for h in hexes) for t in names}
    hex_ps_violations = {t: sum(h["tiers"][t]["PSG"][0]
                                != h["tiers"][t]["PSG"][1] for h in hexes)
                         for t in names}
    hex_rho = {f"exact_vs_{t}": round(spearman(
        [h["exact_PSG"][0] + h["exact_PSG"][1] for h in hexes],
        [h["tiers"][t]["PSG"][0] + h["tiers"][t]["PSG"][1] for h in hexes]),
        3) for t in names}
    classic = next(h for h in hexes if h["seeds"] == [1, 3, 5, 7])

    return {
        "tiers": tiers,
        "mos_rows": len(mos), "hexany_rows": len(hexes),
        "E1_mos_ps_violations": ps_violations,
        "E2_dropped_share": {t: round(v, 4) for t, v in dropped_share.items()},
        "E3_12edo_N12_rank_by_P": edo12_rank,
        "E3_12edo_N12_PSG": edo12_psg,
        "E3_N12_field_size": len(by_n[12]),
        "E4_spearman_P": rho,
        "E5_hexany_lock_rail_mismatches": rail_mismatch,
        "E5_hexanies_gaining_triads": gains,
        "hexany_P_ne_S": hex_ps_violations,
        "hexany_spearman_P_plus_S": hex_rho,
        "hexany_1357": {"exact": classic["exact_PSG"],
                        **{t: classic["tiers"][t]["PSG"] for t in names}},
        "best_by_P": best_table,
    }


def main() -> None:
    tiers = tier_anchors()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prov = {"scorer_version": scorer.SCORER_VERSION, "commit": _commit(),
            "timestamp": stamp}
    mos = sweep_mos(tiers)
    hexes = sweep_hexany(tiers)
    out = HERE / "results"
    with (out / "epstier001.jsonl").open("w", encoding="ascii") as fh:
        for r in mos + hexes:
            fh.write(json.dumps({**r, **prov}) + "\n")
    summary = {**summarize(mos, hexes, tiers), **prov}
    (out / "epstier001_summary.json").write_text(
        json.dumps(summary, indent=1) + "\n", encoding="ascii")
    print(json.dumps({k: v for k, v in summary.items()
                      if k != "best_by_P"}, indent=1))


if __name__ == "__main__":
    main()
