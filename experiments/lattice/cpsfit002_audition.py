"""CPSFIT-002 audition files for G-032 (post-hoc, Ear Bench).

G-032 asks whether ten of the hexany's twelve triads with one tone out at
about 5 cents (CPSFIT-003's count chains) sound better than six at 4.8
cents (CPSFIT-002's worst-triad chains at the same N). CPSFIT-002 exported
only its N = 22 chain, so the worst-triad chains at N = 16 and N = 18 were
never playable. This script writes them as .scl straight from the recorded
rows in results/cpsfit002.jsonl, with the same chain construction and Scala
writer as the runner. Nothing is re-run or re-fitted, and no registered
result changes.

    python experiments/lattice/cpsfit002_audition.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402

ROWS = _HERE / "results" / "cpsfit002.jsonl"
SCL_DIR = _HERE / "results" / "scl" / "cpsfit002"
AUDITION_N = (16, 18)


def audition_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("lattice") == "hexany" and r.get("kind") == "triad" and r.get("N") in AUDITION_N]


def chain_cents(row: dict) -> list[float]:
    start = row["window_start"]
    return [c1.wrap(k * row["g_cents"]) for k in range(start, start + row["N"])]


def scl_for(row: dict) -> tuple[str, str]:
    name = f"cpsfit002_hexany_N{row['N']}_g{row['g_cents']:.3f}"
    tone = max(abs(e) for e in row["tone_errors_cents"])
    desc = (f"CPSFIT-002 hexany triad-minimax chain, N = {row['N']}, g = {row['g_cents']:.3f}c; "
            f"{row['survival_2c_frozen']} of 12 hexany triads within 2.0c, worst tone {tone:.2f}c; "
            f"1/1 = chain degree 0; post-hoc audition file for G-032 (cpsfit002_audition.py)")
    return name, c1.scl_text(name, desc, chain_cents(row))


def main() -> None:
    rows = [json.loads(line) for line in ROWS.read_text(encoding="utf-8").splitlines() if line.strip()]
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    for row in audition_rows(rows):
        name, text = scl_for(row)
        (SCL_DIR / f"{name}.scl").write_text(text, encoding="utf-8")
        print(f"wrote results/scl/cpsfit002/{name}.scl")


if __name__ == "__main__":
    main()
