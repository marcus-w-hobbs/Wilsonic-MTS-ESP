"""MOS-001/002: generator sweep with epsilon sensitivity.

Sweeps g in (0, 600] cents at a given resolution; for each generator,
scores every MOS cardinality in [5, 22] on the tempered path (anchored
convention primary, window logged) at each epsilon. Emits JSONL with full
provenance plus a per-cardinality top table.

Symmetry note: generators g and 1200-g produce mirror-inverted scales, so
P and S swap between them; min(P,S) is invariant, which is why sweeping
only (0, 600] loses nothing (plan §2.2).

Usage (from experiments/triads/):
    python3.12 mos001.py --step 1.0 --out results/mos001_coarse.jsonl
    python3.12 mos001.py --step 0.1 --out results/mos001_fine.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scorer  # noqa: E402
from families.mos import mos_scales  # noqa: E402

EPSILONS = (0.5, 1.0, 2.0, 5.0)
PRIMARY_EPSILON = 2.0

LANDMARKS = {
    "fifth_702_complement_498": 498.045,   # 1200 - 701.955 (pure 3/2)
    "meantone_696_complement_504": 503.42,  # 1200 - 696.58 (1/4-comma)
    "noble_phi_moslike_466": 466.18,        # 1200/phi^2-flavored zigzag noble
    "twelve_edo_500": 500.0,
    "bohlen_pierce_ish_585": 585.0,
}


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def sweep(step_cents: float, out_path: Path,
          epsilons: tuple[float, ...] = EPSILONS) -> None:
    commit = _commit()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    n_gen = int(round(600.0 / step_cents))
    best: dict[int, dict] = {}
    count = 0
    with out_path.open("w", encoding="ascii") as fh:
        for i in range(1, n_gen + 1):
            g_cents = i * step_cents
            g01 = g_cents / 1200.0
            for card, scale in mos_scales(g01).items():
                rec = {
                    "family": "mos", "generator_cents": round(g_cents, 4),
                    "cardinality": card, "scores": {},
                    "scorer_version": scorer.SCORER_VERSION,
                    "commit": commit, "timestamp": stamp,
                }
                for eps in epsilons:
                    anc = scorer.score_cents_anchored(scale, eps)
                    win = scorer.score_cents(scale, eps)
                    rec["scores"][str(eps)] = {
                        "anchored": [anc.proportional, anc.subcontrary,
                                     anc.geometric],
                        "window": [win.proportional, win.subcontrary,
                                   win.geometric],
                    }
                fh.write(json.dumps(rec) + "\n")
                count += 1
                primary = rec["scores"][str(PRIMARY_EPSILON)]["anchored"]
                score = min(primary[0], primary[1])
                cur = best.get(card)
                if cur is None or score > cur["score"]:
                    best[card] = {"score": score, "generator_cents": g_cents,
                                  "PSG": primary}
    print(f"scored {count} (generator, cardinality) pairs at step "
          f"{step_cents} cents -> {out_path}")
    print(f"per-cardinality best by anchored min(P,S) at eps={PRIMARY_EPSILON}:")
    for card in sorted(best):
        b = best[card]
        print(f"  N={card:2d}: min={b['score']:3d} PSG={b['PSG']} "
              f"at g={b['generator_cents']:.1f}c")
    print("landmarks (anchored PSG at eps=2, nearest grid point):")
    for name, cents in LANDMARKS.items():
        g01 = cents / 1200.0
        for card, scale in sorted(mos_scales(g01).items()):
            anc = scorer.score_cents_anchored(scale, PRIMARY_EPSILON)
            print(f"  {name} N={card:2d}: "
                  f"({anc.proportional},{anc.subcontrary},{anc.geometric})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--out", type=Path,
                    default=HERE / "results" / "mos001_coarse.jsonl")
    args = ap.parse_args()
    args.out.parent.mkdir(exist_ok=True)
    sweep(args.step, args.out)


if __name__ == "__main__":
    main()
