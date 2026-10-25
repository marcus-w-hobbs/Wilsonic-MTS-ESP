"""Golden-generator palette for the Ear Bench's generator explorer.

Marcus chooses a generator up front, for its melodic character, the way he
chooses a timbre; the bench then shows how well any combination product set
sits on that generator's chains. Erv's optimised generators (0.418935,
0.238186, ...) all lie very close to golden nobles, so the palette is the
dense set of golden nobles (a + phi*c)/(b + phi*d) with |ad - bc| = 1, folded
into (0, 0.5] (g and 1 - g make the same chains), up to a complexity bound
(the larger of the two seed denominators) that gives about 1,024 of them.

The enumeration is GOLD-002's `nobles()`, imported, not reimplemented. The
triad side is not precomputed: the CPS is arbitrary, so the bench places it
on the chains in the browser (docs/ear-bench/generator.js).

    python experiments/ear_bench/palette.py      # writes docs/ear-bench/palette.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LATTICE = REPO / "experiments" / "lattice"
for p in (str(LATTICE), str(REPO / "experiments" / "triads")):
    if p not in sys.path:
        sys.path.insert(0, p)

import gold002  # noqa: E402  (nobles(), GOLD-002)

OUT = REPO / "docs" / "ear-bench" / "palette.json"
PALETTE_VERSION = "1.0.0"
GOLDEN = 1          # metallic mean m = 1: phi
COMPLEXITY_MAX = 58  # 1,028 golden nobles in (0, 0.5]


def build(complexity_max: int = COMPLEXITY_MAX) -> dict:
    nobles = gold002.nobles(GOLDEN, complexity_max)
    return {
        "version": PALETTE_VERSION,
        "family": "golden",
        "complexity_max": complexity_max,
        "count": len(nobles),
        "nobles": [
            {"g": round(g, 12), "cents": round(1200 * g, 6), "seeds": seeds, "complexity": cx}
            for g, seeds, cx in nobles
        ],
    }


def main() -> None:
    palette = build()
    OUT.write_text(json.dumps(palette, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{palette['count']} golden nobles (complexity <= {palette['complexity_max']}) -> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
