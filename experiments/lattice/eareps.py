"""EAR-ε — detuning-ladder stimuli + blinded protocol for the lock-loss
threshold (LOG.md pre-registration 2026-08-19; committed before this file).

ET-001 fixed the machine side of the cultural epsilon: 12-EDO first
supports the full patent 4:5:6/10:12:15 pair at ε = 14.859022¢ and locks
its power chord at 1.955001¢ (= its fifth error, exactly). EAR-ε builds
the human side: 44 minimal blinded .scl stimuli — four families, each rung
a triad with ONE tone detuned by a pre-registered δ — so Marcus can locate
his own lock-loss thresholds in one sitting (gate G-025). This module only
GENERATES stimuli and machine receipts; no listening result lives here.

Families (LOG.md, locked):
  A  major prototype 4:5:6, third detuned      δ ∈ {0, ±2, ±5, ±8, ±11,
                                                    ±14.86, ±18, ±22}¢
  B  power chord 2:3:4, fifth detuned          δ ∈ {0, ±1, ±1.955001,
                                                    ±3, ±5, ±8}¢
  C  subcontrary prototype 10:12:15, third     same ladder as A
  D  the literal 12-EDO major / minor / power  (anchors, no δ)

Scorer rails (frozen triads v1.1.0 is the referee, read-only): in A/B/C
the detuned tone is exactly the mean tone of its class, so the frozen
classifier's deviation equals |δ| EXACTLY; every rung is verified by
classify_cents_triple at |δ| ± 1e−6 and by a +1 count jump in
score_tempered across the same threshold. Family D deviations must equal
ET-001's numbers (14.859022 / 14.859022 / 1.955001¢).

Blinding: filenames are opaque presentation-order ids (shuffle seed
20260819, pre-registered); .scl headers carry no provenance; the δ
assignment lives only in the SEALED results/eareps_key.json, the technical
record in the SEALED results/eareps_manifest.json.

Deterministic: python3.12 stdlib only, no wall-clock fields; two runs must
be bit-identical on every output.

Run from experiments/lattice/:  python3.12 eareps.py
"""

from __future__ import annotations

import json
import random
import sys
from math import log2
from pathlib import Path
from typing import NamedTuple, Optional

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scorer import (  # noqa: E402  (frozen v1.1.0, read-only)
    GEOMETRIC,
    PROPORTIONAL,
    SCORER_VERSION,
    SUBCONTRARY,
    classify_cents_triple,
    mean_separation_cents,
    score_tempered,
)

EAREPS_VERSION = "1.0.0"

# --- constants, locked in the LOG.md pre-registration (2026-08-19) ---------
SEED = 20260819                      # the one rng use: per-family shuffles
RAIL_DELTA_CENTS = 1e-6              # scorer verification offset
EPS_GRID = (1.0, 2.0, 3.0, 5.0, 10.0, 14.86, 20.0)   # ET-001 grid, joinable

M3_CENTS = 1200.0 * log2(5.0 / 4.0)      # 386.313714
m3_CENTS = 1200.0 * log2(6.0 / 5.0)      # 315.641287
P5_CENTS = 1200.0 * log2(3.0 / 2.0)      # 701.955001
DELTA_PC_CENTS = 1200.0 * log2(3.0) - 1900.0   # 1.955001 = 12-EDO 5th error

LADDER_THIRD_MAGS = (2.0, 5.0, 8.0, 11.0, 14.86, 18.0, 22.0)
LADDER_FIFTH_MAGS = (1.0, DELTA_PC_CENTS, 3.0, 5.0, 8.0)

#: Presentation-block order (LOG.md): fifths first (easiest percept,
#: calibrates the task), then major, minor, 12-EDO anchors.
BLOCK_ORDER = ("B", "A", "C", "D")

KNIFE_EDGE_MAG = 14.86   # rungs at ±14.86 sit on the 14.86 grid point

OUT_SCL = _HERE / "results" / "scl" / "eareps"
OUT_MANIFEST = _HERE / "results" / "eareps_manifest.json"
OUT_KEY = _HERE / "results" / "eareps_key.json"
OUT_TEMPLATE = _HERE / "results" / "eareps_responses.template.json"

SEALED_WARNING = (
    "SEALED -- do not open this file (or its PR diff) until your "
    "responses are saved to results/eareps_responses.json. See "
    "EAREPS_PROTOCOL.md."
)


class Rung(NamedTuple):
    """One stimulus, pre-shuffle. `triple` is the sounding triad (cents,
    a < b < c); `degrees` are the .scl degrees above the implicit 1/1,
    ending with the octave. `target_triples` pairs each target scorer
    class with the triple that carries it — for family B the subcontrary
    label lives on the 3:4:6 fifth-below voicing (P5+δ−1200, 0, P5+δ),
    the octave-dual of the sounding 2:3:4, not on the sounding triple
    itself. Every target deviation is |delta| exactly (family D: the
    ET-001 number)."""

    family: str
    delta_cents: Optional[float]     # None for family D anchors
    description: str                 # sealed provenance (key file only)
    triple: tuple[float, float, float]
    degrees: tuple[float, ...]
    target_triples: tuple[tuple[str, tuple[float, float, float]], ...]

    @property
    def targets(self) -> tuple[str, ...]:
        return tuple(cls for cls, _ in self.target_triples)


def ladder(mags: tuple[float, ...]) -> tuple[float, ...]:
    """0 then ±each magnitude, canonical pre-shuffle order."""
    out = [0.0]
    for m in mags:
        out.extend((m, -m))
    return tuple(out)


def build_rungs() -> dict[str, tuple[Rung, ...]]:
    """All 44 rungs in canonical (pre-shuffle) order, keyed by family."""
    fams: dict[str, list[Rung]] = {"A": [], "B": [], "C": [], "D": []}
    for d in ladder(LADDER_THIRD_MAGS):
        maj = (0.0, M3_CENTS + d, P5_CENTS)
        fams["A"].append(Rung(
            "A", d, f"4:5:6 major, third {d:+.6f}c from just",
            maj, (M3_CENTS + d, P5_CENTS, 1200.0),
            ((PROPORTIONAL, maj),)))
        mnr = (0.0, m3_CENTS + d, P5_CENTS)
        fams["C"].append(Rung(
            "C", d, f"10:12:15 minor, third {d:+.6f}c from just",
            mnr, (m3_CENTS + d, P5_CENTS, 1200.0),
            ((SUBCONTRARY, mnr),)))
    for d in ladder(LADDER_FIFTH_MAGS):
        pc = (0.0, P5_CENTS + d, 1200.0)                 # sounding 2:3:4
        dual = (P5_CENTS + d - 1200.0, 0.0, P5_CENTS + d)  # 3:4:6 voicing
        fams["B"].append(Rung(
            "B", d, f"2:3:4 power chord, fifth {d:+.6f}c from just",
            pc, (P5_CENTS + d, 1200.0),
            ((PROPORTIONAL, pc), (SUBCONTRARY, dual))))
    d_maj = (0.0, 400.0, 700.0)
    d_mnr = (0.0, 300.0, 700.0)
    d_pc = (0.0, 700.0, 1200.0)
    fams["D"] = [
        Rung("D", None, "12-EDO major triad 0-400-700",
             d_maj, (400.0, 700.0, 1200.0), ((PROPORTIONAL, d_maj),)),
        Rung("D", None, "12-EDO minor triad 0-300-700",
             d_mnr, (300.0, 700.0, 1200.0), ((SUBCONTRARY, d_mnr),)),
        Rung("D", None, "12-EDO power chord 0-700-1200",
             d_pc, (700.0, 1200.0), ((PROPORTIONAL, d_pc),)),
    ]
    return {f: tuple(v) for f, v in fams.items()}


# --- analytic mirror (independent one-liners; the scorer is the referee) ---

def deviation_cents(triple: tuple[float, float, float], cls: str) -> float:
    """Mean-condition deviation of a cents triple for one class."""
    a, b, c = triple
    fa, fb, fc = (2.0 ** (x / 1200.0) for x in (a, b, c))
    if cls == PROPORTIONAL:
        return abs(1200.0 * log2((fa + fc) / (2.0 * fb)))
    if cls == SUBCONTRARY:
        return abs(1200.0 * log2(fb * (fa + fc) / (2.0 * fa * fc)))
    if cls == GEOMETRIC:
        return abs(1200.0 * log2((fa * fc) / (fb * fb)))
    raise ValueError(f"unknown class {cls!r}")


def target_deviation(rung: Rung) -> float:
    """Max over the rung's target (class, triple) pairs — the deviations
    agree (= |delta|) for family B's two readings."""
    return max(deviation_cents(triple, cls)
               for cls, triple in rung.target_triples)


def scale_cents(rung: Rung) -> tuple[float, ...]:
    """The rung's full scale for score_tempered (degree 0 + degrees)."""
    return (0.0,) + rung.degrees


# --- rails ------------------------------------------------------------------

def rail_check(rung: Rung) -> dict:
    """Verify, against the FROZEN scorer, that the rung's target class(es)
    flip exactly at the analytic deviation d: absent at d − 1e−6, present
    at d + 1e−6 (δ = 0 and family-D-exact rungs: present at 1e−6), and
    that the full-scale count of each target class jumps by exactly +1
    across the same threshold. Records everything; patches nothing."""
    d = target_deviation(rung)
    lo_eps = d - RAIL_DELTA_CENTS
    hi_eps = d + RAIL_DELTA_CENTS
    result: dict = {"deviation_cents": d}
    if lo_eps > 0.0:
        flips_ok = True
        classify_low: dict[str, list[str]] = {}
        classify_high: dict[str, list[str]] = {}
        for cls, triple in rung.target_triples:
            lo = classify_cents_triple(*triple, lo_eps)
            hi = classify_cents_triple(*triple, hi_eps)
            classify_low[cls] = sorted(lo)
            classify_high[cls] = sorted(hi)
            flips_ok = flips_ok and (cls not in lo and cls in hi)
        result["classify_low"] = classify_low
        result["classify_high"] = classify_high
        result["classify_flip_ok"] = flips_ok
        counts_lo = score_tempered(scale_cents(rung), lo_eps)
        counts_hi = score_tempered(scale_cents(rung), hi_eps)
        jumps = {
            PROPORTIONAL: counts_hi.proportional - counts_lo.proportional,
            SUBCONTRARY: counts_hi.subcontrary - counts_lo.subcontrary,
        }
        result["scale_jump"] = {cls: jumps[cls] for cls in rung.targets}
        result["scale_jump_ok"] = all(jumps[cls] == 1 for cls in rung.targets)
    else:   # δ = 0: deviation is (float-)zero; presence at 1e−6 is the rail
        classify_high = {
            cls: sorted(classify_cents_triple(*triple, RAIL_DELTA_CENTS))
            for cls, triple in rung.target_triples}
        result["classify_high"] = classify_high
        result["classify_flip_ok"] = all(
            cls in classify_high[cls] for cls in rung.targets)
        result["scale_jump_ok"] = None   # no jump rail at δ = 0 (LOG.md)
    result["separation_cents"] = {
        cls: mean_separation_cents(triple[0], triple[2])
        for cls, triple in rung.target_triples}
    result["rail_ok"] = bool(result["classify_flip_ok"]) and (
        result["scale_jump_ok"] in (True, None))
    return result


def grid_classification(rung: Rung) -> dict:
    """Frozen-scorer record at every ET-001 grid ε: the target triple's
    label set and the full scale's guarded P/S/G counts."""
    grid = {}
    for eps in EPS_GRID:
        labels = classify_cents_triple(*rung.triple, eps)
        counts = score_tempered(scale_cents(rung), eps)
        grid[f"{eps:g}"] = {
            "triple_labels": sorted(labels),
            "scale_P": counts.proportional,
            "scale_S": counts.subcontrary,
            "scale_G": counts.geometric,
        }
    return grid


# --- blinding ----------------------------------------------------------------

def presentation() -> dict[str, tuple[Rung, ...]]:
    """Per-family presentation order: canonical rungs shuffled by the
    pre-registered seed, rng consumed in block order B, A, C, D."""
    fams = build_rungs()
    rng = random.Random(SEED)
    out = {}
    for fam in BLOCK_ORDER:
        order = list(fams[fam])
        rng.shuffle(order)
        out[fam] = tuple(order)
    return out


def rung_id(family: str, position: int) -> str:
    """Opaque id: presentation position within the family block."""
    return f"eareps_{family}_{position:02d}"


def scl_text(rid: str, degrees: tuple[float, ...]) -> str:
    """Minimal blinded Scala text: opaque description, degrees above the
    implicit 1/1, octave last, NO provenance (the delta is the secret)."""
    lines = [
        f"! {rid}.scl",
        "!",
        "! EAR-eps blinded stimulus -- key sealed"
        " (results/eareps_key.json)",
        "!",
        rid,
        f" {len(degrees)}",
        "!",
    ]
    lines += [f" {c:.5f}" for c in degrees]
    return "\n".join(lines) + "\n"


# --- assembly ----------------------------------------------------------------

def build_all() -> tuple[dict, dict, dict, dict[str, str]]:
    """(manifest, key, responses_template, {filename: scl_text})."""
    pres = presentation()
    manifest_rungs = {}
    key_rungs = {}
    template_rungs = {}
    files: dict[str, str] = {}
    rail_failures = 0
    for fam in BLOCK_ORDER:
        for i, rung in enumerate(pres[fam], start=1):
            rid = rung_id(fam, i)
            fname = f"{rid}.scl"
            files[fname] = scl_text(rid, rung.degrees)
            rails = rail_check(rung)
            if not rails["rail_ok"]:
                rail_failures += 1
            knife_edge = (rung.delta_cents is not None
                          and abs(abs(rung.delta_cents) - KNIFE_EDGE_MAG)
                          < 1e-12)
            manifest_rungs[rid] = {
                "family": fam,
                "file": f"scl/eareps/{fname}",
                "delta_cents": rung.delta_cents,
                "description": rung.description,
                "triple_cents": list(rung.triple),
                "scl_degrees_cents": list(rung.degrees),
                "target_classes": list(rung.targets),
                "rails": rails,
                "grid": grid_classification(rung),
                "knife_edge_at_14.86": knife_edge,
            }
            key_rungs[rid] = {
                "family": fam,
                "delta_cents": rung.delta_cents,
                "description": rung.description,
            }
            template_rungs[rid] = {
                "verdict": "",          # locked | beating | broken
                "fusion_1to5": None,    # optional, 5 = perfectly fused
                "notes": "",
            }
    manifest = {
        "_warning": SEALED_WARNING,
        "experiment": "EAR-eps",
        "version": EAREPS_VERSION,
        "seed": SEED,
        "scorer_version": SCORER_VERSION,
        "eps_grid_cents": list(EPS_GRID),
        "rail_delta_cents": RAIL_DELTA_CENTS,
        "block_order": list(BLOCK_ORDER),
        "rail_failures": rail_failures,
        "n_stimuli": len(manifest_rungs),
        "rungs": manifest_rungs,
    }
    key = {
        "_warning": SEALED_WARNING,
        "experiment": "EAR-eps",
        "version": EAREPS_VERSION,
        "seed": SEED,
        "rungs": key_rungs,
    }
    template = {
        "_instructions": (
            "Copy this file to results/eareps_responses.json and fill it "
            "in while listening, block by block, in the order the rungs "
            "appear here. verdict: locked | beating | broken. Do not open "
            "eareps_key.json or eareps_manifest.json until this file is "
            "saved. See EAREPS_PROTOCOL.md."),
        "sitting_date": "",
        "synth_patch": "",
        "playback_chain": "",
        "responses": template_rungs,
    }
    return manifest, key, template, files


def main() -> None:
    manifest, key, template, files = build_all()
    OUT_SCL.mkdir(parents=True, exist_ok=True)
    for fname, text in files.items():
        (OUT_SCL / fname).write_text(text, encoding="ascii")
    OUT_MANIFEST.write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="ascii")
    OUT_KEY.write_text(json.dumps(key, indent=1) + "\n", encoding="ascii")
    OUT_TEMPLATE.write_text(
        json.dumps(template, indent=1) + "\n", encoding="ascii")
    n = len(files)
    print(f"{n} .scl stimuli -> {OUT_SCL}")
    print(f"manifest (SEALED) -> {OUT_MANIFEST}")
    print(f"key (SEALED) -> {OUT_KEY}")
    print(f"responses template -> {OUT_TEMPLATE}")
    print(f"rail failures: {manifest['rail_failures']}")


if __name__ == "__main__":
    main()
