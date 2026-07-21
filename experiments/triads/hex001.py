"""HEX-001: exhaustive hexany calibration sweep.

Enumerates all C(8,4) = 70 seed sets from the odds {1,3,...,15}, scores
every hexany on the exact-rational path under BOTH sampling conventions,
ranks within cardinality bins by min(P,S) then P*S, and reports where the
classic 1-3-5-7 hexany lands. Writes:

  results/hex001.jsonl          one full-provenance record per seed set
  results/scl/hex_*.scl         top hexanies by anchored min(P,S), 6-note bin

Run from experiments/triads/:
    python3.12 hex001.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scorer  # noqa: E402
from families.cps import cps_products, odd_seed_sets  # noqa: E402
from scala import write_scl  # noqa: E402

TOP_N_SCL = 10


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=HERE, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"warning: could not resolve git commit: {exc}", file=sys.stderr)
        return "unknown"


def _score_block(result: scorer.ScoreResult) -> dict:
    return {
        "P": result.proportional,
        "S": result.subcontrary,
        "G": result.geometric,
        "score_min": result.score_min,
        "score_product": result.score_product,
        "convention": result.convention,
    }


def evaluate_all() -> list[dict]:
    commit = _git_commit()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records = []
    for seeds in odd_seed_sets(4, 15):
        products = cps_products(seeds, 2)
        window = scorer.score_rational(products)
        anchored = scorer.score_rational_anchored(products)
        records.append({
            "family": "cps",
            "n": 4,
            "k": 2,
            "seeds": list(seeds),
            "products": [str(p) for p in products],
            "scale": [str(x) for x in anchored.scale],
            "cardinality": len(anchored.scale),
            "window": _score_block(window),
            "anchored": _score_block(anchored),
            "scorer_version": scorer.SCORER_VERSION,
            "epsilon_cents": None,
            "commit": commit,
            "timestamp": stamp,
        })
    return records


def rank_key(convention: str):
    def key(rec: dict):
        block = rec[convention]
        return (-block["score_min"], -block["score_product"], rec["seeds"])
    return key


def report(records: list[dict]) -> str:
    lines = []
    bins: dict[int, list[dict]] = {}
    for rec in records:
        bins.setdefault(rec["cardinality"], []).append(rec)

    for card in sorted(bins, reverse=True):
        group = bins[card]
        lines.append(f"\n== cardinality {card} ({len(group)} seed sets) ==")
        for convention in ("anchored", "window"):
            ranked = sorted(group, key=rank_key(convention))
            lines.append(f"-- ranked by {convention} min(P,S), then P*S --")
            for i, rec in enumerate(ranked[:12], start=1):
                b = rec[convention]
                marker = "  <-- 1-3-5-7" if rec["seeds"] == [1, 3, 5, 7] else ""
                lines.append(
                    f"  {i:2d}. seeds {rec['seeds']}  "
                    f"P={b['P']:3d} S={b['S']:3d} G={b['G']:2d}  "
                    f"min={b['score_min']:3d} prod={b['score_product']:4d}{marker}"
                )
            classic = next(
                (i for i, rec in enumerate(ranked, start=1)
                 if rec["seeds"] == [1, 3, 5, 7]), None)
            if classic is not None:
                lines.append(f"  [1,3,5,7] rank under {convention}: "
                             f"{classic}/{len(ranked)}")
    return "\n".join(lines)


def main() -> None:
    records = evaluate_all()

    results_dir = HERE / "results"
    scl_dir = results_dir / "scl"
    scl_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = results_dir / "hex001.jsonl"
    with jsonl_path.open("w", encoding="ascii") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    print(f"scored {len(records)} hexanies -> {jsonl_path}")
    print(report(records))

    six_note = [r for r in records if r["cardinality"] == 6]
    top = sorted(six_note, key=rank_key("anchored"))[:TOP_N_SCL]
    for rec in top:
        tag = "-".join(str(s) for s in rec["seeds"])
        b = rec["anchored"]
        desc = (f"hexany {tag}  P={b['P']} S={b['S']} "
                f"min={b['score_min']} (anchored, scorer "
                f"{rec['scorer_version']}, {rec['commit'][:8]})")
        path = write_scl(scl_dir / f"hex_{tag}.scl", desc, rec["products"])
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
