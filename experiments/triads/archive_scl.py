"""Export the per-(family, cardinality) archive winners as .scl files.

Companion to search.py: the archive is the museum, this makes the exhibits
playable in Wilsonic. Winners are taken WITHIN cardinality bins (plan §1.3)
and written alongside their landmark peers so an ear check is a direct A/B
rather than a hunt through the JSONL.

Usage (from experiments/triads/):
    python3.12 archive_scl.py                      # top 1 per bin
    python3.12 archive_scl.py --top 2 --min-score 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from families.cps import cps_scale, wilsonic_recreation_lines  # noqa: E402
from scala import write_scl  # noqa: E402
from search import load  # noqa: E402


def slug(rec: dict) -> str:
    seeds = "-".join(str(s) for s in rec["seeds"])
    fam = rec["family"].replace("(", "_").replace(")", "").replace(",", "_")
    return f"{fam}_N{rec['cardinality']}_{seeds}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path,
                    default=HERE / "results" / "archive.jsonl")
    ap.add_argument("--outdir", type=Path,
                    default=HERE / "results" / "scl")
    ap.add_argument("--top", type=int, default=1)
    ap.add_argument("--min-score", type=int, default=1)
    args = ap.parse_args()

    archive, meta = load(args.archive)
    args.outdir.mkdir(parents=True, exist_ok=True)

    # Landmarks come from the run metadata, NOT from the archive: MAP-Elites
    # evicts a landmark as soon as something better occupies its cell, so
    # reading them out of the archive silently drops exactly the reference
    # tunings an ear check needs for its A/B (observed: the classic
    # pentadekany 1-3-5-7-9-11 went missing from the export this way).
    records = list(archive.values())
    known = {(tuple(r["seeds"]), r["k"]) for r in records}
    for lm in meta.get("landmarks", []):
        if (tuple(lm["seeds"]), lm["k"]) not in known:
            records.append(lm)

    by_bin: dict[tuple, list[dict]] = {}
    for rec in records:
        by_bin.setdefault((rec["family"], rec["cardinality"]), []).append(rec)

    written = 0
    for key in sorted(by_bin):
        rows = sorted(by_bin[key],
                      key=lambda r: (-r["score_min"], -r["score_product"]))
        chosen = [r for r in rows[:args.top] if r["score_min"] >= args.min_score]
        # always include landmarks in the bin, for A/B against the winner
        chosen += [r for r in rows if "landmark" in r and r not in chosen]
        for rec in chosen:
            scale = cps_scale(rec["seeds"], rec["k"])
            desc = (f"{rec['family']} seeds {'-'.join(map(str, rec['seeds']))} "
                    f"N={rec['cardinality']} P={rec['P']} S={rec['S']} "
                    f"G={rec['G']} min={rec['score_min']} "
                    f"{rec['prime_limit']}-limit "
                    f"[scorer {rec['scorer_version']} {rec['convention']}]")
            prov = wilsonic_recreation_lines(rec["seeds"], rec["k"]) + [
                f"SCORE: P={rec['P']} S={rec['S']} G={rec['G']} "
                f"min(P,S)={rec['score_min']}  N={rec['cardinality']}  "
                f"{rec['prime_limit']}-limit  [{rec['convention']}]",
                f"PROVENANCE: scorer {rec['scorer_version']}, "
                f"LOOP-001 batch search, archive origin "
                f"'{rec.get('origin', 'unknown')}'"
                + (f", landmark '{rec['landmark']}'" if "landmark" in rec
                   else ""),
            ]
            write_scl(args.outdir / f"{slug(rec)}.scl", desc, scale, prov)
            written += 1

    print(f"wrote {written} .scl files to {args.outdir}")
    print(f"archive: {meta.get('evaluated')} candidates, "
          f"{meta.get('cells_filled')} cells, scorer "
          f"{meta.get('scorer_version')}")


if __name__ == "__main__":
    main()
