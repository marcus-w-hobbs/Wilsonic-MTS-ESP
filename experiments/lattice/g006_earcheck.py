"""G-006 ear-check kit: blind .scl pairs testing whether M3 (Rothenberg
propriety) ranks scales the way Marcus's ear does.

Design (blind, sealed-key): each pair holds one NON-IMPROPER and one
IMPROPER scale of the same cardinality, in randomized a/b order (fixed
seed). Filenames are neutral; the assignment lives only in
results/scl/g006/g006_key_SEALED.json — DO NOT open it until the listening
notes are written down. Provenance comments inside each .scl name the
scale precisely (they are visible in Scala-aware editors; avoid reading
file contents while listening).

Pairs 1-6: hexanies (from latmel001.jsonl; non-improper vs most-improper).
Pairs 7-8: true MOS, noble phi (strictly proper) vs 571.6c hot-spot
(improper), at matched cardinality.

Run from experiments/lattice/:  python3.12 g006_earcheck.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import melodic as mel  # noqa: E402
from families.cps import cps_scale  # noqa: E402
from families.mos import mos_cardinalities, mos_cents  # noqa: E402
from scala import to_scala  # noqa: E402

OUT = HERE / "results" / "scl" / "g006"
SEED = 20260725
NOBLE_PHI = 741.6383 / 1200.0
HOTSPOT = 571.6 / 1200.0


def cents_scl(description: str, cents: tuple[float, ...],
              provenance: list[str]) -> str:
    """Scala text for a cents scale (degree 0 implicit, octave appended)."""
    rel = [c - cents[0] for c in cents[1:]] + [1200.0]
    lines = [f"! {description}", "!"]
    lines += [f"! {p}" for p in provenance] + ["!"]
    lines += [description, f" {len(rel)}", "!"]
    lines += [f" {c:.5f}" for c in rel]
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = [json.loads(l) for l in (HERE / "results" / "latmel001.jsonl").open()]
    hexes = [r for r in rows if r["family"] == "hexany"]
    non_improper = sorted((r for r in hexes if r["m3_class"] != "improper"),
                          key=lambda r: r["seeds"])
    improper = sorted((r for r in hexes if r["m3_class"] == "improper"),
                      key=lambda r: (-r["m3_violations"], r["seeds"]))
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    key = {"seed": SEED, "pairs": {}}

    for i in range(6):
        good, bad = non_improper[i], improper[i]
        entries = [("proper", good), ("improper", bad)]
        rng.shuffle(entries)
        for slot, (label, row) in zip("ab", entries):
            seeds = row["seeds"]
            name = f"g006_p{i + 1}_{slot}.scl"
            scale = cps_scale(tuple(seeds), 2)
            (OUT / name).write_text(to_scala(
                f"g006 pair {i + 1}{slot}", scale,
                [f"hexany CPS(4,2) seeds {seeds}",
                 "Wilsonic: CPS design, 4 factors, choose 2",
                 "G-006 blind ear check -- key sealed"]), encoding="ascii")
            key["pairs"][f"p{i + 1}"] = key["pairs"].get(f"p{i + 1}", {})
            key["pairs"][f"p{i + 1}"][slot] = {
                "m3": row["m3_class"], "seeds": seeds,
                "m3_violations": row["m3_violations"],
                "m2_is_cs": row["m2_is_cs"]}

    shared = sorted(set(mos_cardinalities(NOBLE_PHI))
                    & set(mos_cardinalities(HOTSPOT)))
    shared = [n for n in shared if 5 <= n <= 22][:2]
    for j, n in enumerate(shared):
        pair_id = f"p{7 + j}"
        entries = [("noble_phi_strictly_proper", NOBLE_PHI, 741.6383),
                   ("hotspot_improper", HOTSPOT, 571.6)]
        rng.shuffle(entries)
        for slot, (label, g01, g_cents) in zip("ab", entries):
            cents = mos_cents(g01, n)
            m3 = mel.propriety(cents)
            name = f"g006_{pair_id}_{slot}.scl"
            (OUT / name).write_text(cents_scl(
                f"g006 pair {7 + j}{slot}", cents,
                [f"MOS generator {g_cents}c, cardinality {n}, murchana 0",
                 "Wilsonic: MOS (Brun) design",
                 "G-006 blind ear check -- key sealed"]), encoding="ascii")
            key["pairs"][pair_id] = key["pairs"].get(pair_id, {})
            key["pairs"][pair_id][slot] = {
                "label": label, "generator_cents": g_cents,
                "cardinality": n, "m3": m3.classification}

    (OUT / "g006_key_SEALED.json").write_text(json.dumps(key, indent=1))
    n_files = len(list(OUT.glob("g006_p*.scl")))
    print(f"{n_files} .scl files + sealed key -> {OUT}")
    print("MOS pairs at cardinalities:", shared)


if __name__ == "__main__":
    main()
