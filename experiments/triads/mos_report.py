"""Report over a MOS sweep JSONL: per-cardinality rankings.

The epsilon-degeneracy problem now lives in the SCORER, per Marcus's
decision of 2026-07-21: a triple counts only when its arithmetic and
harmonic means are distinguishable at epsilon
(scorer.is_informative_triple). Sweep records written after that decision
carry guarded counts under "anchored", so this report needs no guard of
its own and GUARD_FACTOR defaults to 0 (off).

The old report-layer min-step guard is retained behind --guard-factor for
comparison against pre-decision runs. It was always a scale-shape prior
rather than a scoring fact, and it under-filtered: at eps=0.5/1 it still
admitted 2-4c micro-generators, which topped the N=5..10 bins.

Usage: python3.12 mos_report.py results/mos001_fine.jsonl [--eps 2.0]
                                [--guard-factor 4.0]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from families.mos import mos_cents  # noqa: E402

GUARD_FACTOR = 0.0  # report-layer guard off; the scorer guards per triple


def min_step_cents(generator_cents: float, cardinality: int) -> float:
    scale = mos_cents(generator_cents / 1200.0, cardinality)
    steps = [b - a for a, b in zip(scale, scale[1:])]
    steps.append(1200.0 - scale[-1] + scale[0])
    return min(steps)


def epsilon_table(path: Path, top: int = 1) -> None:
    """MOS-002: per-cardinality best generator at each epsilon in the file.

    Reproduces results/mos002_epsilon_sensitivity.txt, which was previously
    generated ad hoc.
    """
    by_eps: dict[str, dict[int, tuple]] = {}
    with path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            for eps_key, sc in rec["scores"].items():
                p, s, _ = sc["anchored"]
                cur = by_eps.setdefault(eps_key, {}).get(rec["cardinality"])
                if cur is None or min(p, s) > cur[0]:
                    by_eps[eps_key][rec["cardinality"]] = (
                        min(p, s), rec["generator_cents"]
                    )
    eps_keys = sorted(by_eps, key=float)
    print("MOS-002: per-cardinality best generator by anchored min(P,S), "
          "by epsilon")
    print("degeneracy guard: in the SCORER (per-triad AM/HM separation >= "
          "epsilon); no report-layer filter")
    print("  N | " + " | ".join(f"eps={k:<5}" for k in eps_keys))
    cards = sorted({c for v in by_eps.values() for c in v})
    for card in cards:
        cells = []
        for k in eps_keys:
            hit = by_eps[k].get(card)
            cells.append(f"{hit[1]:7.1f}c m={hit[0]:<4d}" if hit else " " * 16)
        print(f"{card:3d} | " + " | ".join(cells))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--guard-factor", type=float, default=GUARD_FACTOR,
                    help="legacy report-layer min-step guard; 0 disables "
                         "(the scorer's per-triple guard supersedes it)")
    ap.add_argument("--epsilon-table", action="store_true",
                    help="emit the MOS-002 epsilon sensitivity table instead")
    args = ap.parse_args()

    if args.epsilon_table:
        epsilon_table(args.jsonl)
        return

    eps_key = str(args.eps)
    guard = args.guard_factor * args.eps
    by_card: dict[int, list[dict]] = {}
    with args.jsonl.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if eps_key not in rec["scores"]:
                continue
            p, s, g = rec["scores"][eps_key]["anchored"]
            by_card.setdefault(rec["cardinality"], []).append({
                "g": rec["generator_cents"], "P": p, "S": s, "G": g,
                "min": min(p, s),
            })

    if guard > 0:
        print(f"epsilon={args.eps}c, LEGACY report-layer guard: min step > "
              f"{guard}c (= {args.guard_factor} * epsilon)")
    else:
        print(f"epsilon={args.eps}c, degeneracy handled in the scorer "
              f"(per-triad AM/HM separation >= epsilon); no report guard")
    for card in sorted(by_card):
        rows = by_card[card]
        guarded = []
        degenerate = 0
        for r in rows:
            if guard <= 0 or min_step_cents(r["g"], card) > guard:
                guarded.append(r)
            else:
                degenerate += 1
        guarded.sort(key=lambda r: (-r["min"], r["g"]))
        print(f"\nN={card}: {len(rows)} generators, {degenerate} "
              f"excluded by the legacy report guard")
        for r in guarded[:args.top]:
            print(f"  g={r['g']:7.1f}c  P={r['P']:3d} S={r['S']:3d} "
                  f"G={r['G']:3d}  min={r['min']:3d}")


if __name__ == "__main__":
    main()
