"""Report over a MOS sweep JSONL: per-cardinality rankings with an
epsilon-degeneracy guard applied at the REPORT layer (scorer untouched).

A tempered scale is flagged epsilon-degenerate when its smallest step is
<= GUARD_FACTOR * epsilon: near-equal steps make AM/GM/HM coincide within
epsilon, so triples multi-count as P, S, and G and min(P,S) inflates
(observed: a 1-cent generator tops N=5..10; ~599c near-2-EDO tops
N=15/17). GUARD_FACTOR is a report-layer choice, clearly printed — the
scorer records raw counts either way, so re-filtering is free.

Usage: python3.12 mos_report.py results/mos001_fine.jsonl [--eps 2.0]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from families.mos import mos_cents  # noqa: E402

GUARD_FACTOR = 4.0


def min_step_cents(generator_cents: float, cardinality: int) -> float:
    scale = mos_cents(generator_cents / 1200.0, cardinality)
    steps = [b - a for a, b in zip(scale, scale[1:])]
    steps.append(1200.0 - scale[-1] + scale[0])
    return min(steps)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    eps_key = str(args.eps)
    guard = GUARD_FACTOR * args.eps
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

    print(f"epsilon={args.eps}c, degeneracy guard: min step > {guard}c "
          f"(= {GUARD_FACTOR} * epsilon, report-layer choice)")
    for card in sorted(by_card):
        rows = by_card[card]
        guarded = []
        degenerate = 0
        for r in rows:
            if min_step_cents(r["g"], card) > guard:
                guarded.append(r)
            else:
                degenerate += 1
        guarded.sort(key=lambda r: (-r["min"], r["g"]))
        print(f"\nN={card}: {len(rows)} generators, {degenerate} "
              f"epsilon-degenerate excluded")
        for r in guarded[:args.top]:
            print(f"  g={r['g']:7.1f}c  P={r['P']:3d} S={r['S']:3d} "
                  f"G={r['G']:3d}  min={r['min']:3d}")


if __name__ == "__main__":
    main()
