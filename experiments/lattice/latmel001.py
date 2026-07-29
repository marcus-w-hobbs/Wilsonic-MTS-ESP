"""LAT-MEL-001 — melodic scoring of the harmonic corpus (SPEC §LAT-MEL-001).

Pre-registered in LOG.md 2026-07-25 BEFORE first run. Deterministic, stdlib
only. Writes results/latmel001.jsonl (one row per scale) and prints the
H-L1/H-L2 summary used for the verdict.

Run from experiments/lattice/:
    python3.12 latmel001.py
"""

from __future__ import annotations

import json
import random
import sys
from fractions import Fraction
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import melodic as mel  # noqa: E402
import scorer as triad  # noqa: E402
from families.cps import cps_scale, odd_seed_sets  # noqa: E402
from families.mos import mos_scales  # noqa: E402
from scorer import canonical_cents_scale  # noqa: E402

RESULTS = HERE / "results" / "latmel001.jsonl"
RANDOM_SEED = 20260725
TEMPERED_EPSILON = 2.0

#: MOS control generators (cents): mos001 hot spots + the fifth/fourth pair
#: + one noble (1/phi). See LOG.md pre-registration.
MOS_GENERATORS_CENTS = (701.955, 498.045, 571.6, 416.2, 741.6383)

#: hex003_eik001 calibration set (ranks last 29/29 by min(P,S); a deliberate
#: rank-1-geometric outlier inside the eikosany family).
CALIBRATION_EIK = (1, 45, 135, 225, 19, 377)


def melodic_row(score: mel.MelodicScore) -> dict:
    """Flatten a MelodicScore into JSON-safe receipt fields."""
    m1, m2, m3 = score.gap_entropy, score.constant_structure, score.propriety
    return {
        "m1_entropy_bits": round(m1.entropy_bits, 6),
        "m1_gap_classes": m1.gap_class_count,
        "m2_cs_violations": m2.violations,
        "m2_is_cs": m2.is_cs,
        "m3_class": m3.classification,
        "m3_violations": m3.violating_span_pairs,
        "cardinality": len(score.scale),
        "melodic_version": score.melodic_version,
    }


def harmonic_row_rational(ratios) -> dict:
    r = triad.score(ratios)
    return {"P": r.proportional, "S": r.subcontrary, "G": r.geometric,
            "scorer_version": r.scorer_version, "path": r.path}


def harmonic_row_cents(cents) -> dict:
    r = triad.score_tempered(cents, TEMPERED_EPSILON)
    return {"P": r.proportional, "S": r.subcontrary, "G": r.geometric,
            "scorer_version": r.scorer_version, "path": r.path,
            "epsilon_cents": TEMPERED_EPSILON}


def ji_rows():
    for seeds in odd_seed_sets(4, 15):
        yield {"family": "hexany", "seeds": list(seeds)}, cps_scale(seeds, 2)
    eik_seed_sets = list(odd_seed_sets(6, 15)) + [CALIBRATION_EIK]
    for seeds in eik_seed_sets:
        fam = "eikosany_cal" if tuple(seeds) == CALIBRATION_EIK else "eikosany"
        yield {"family": fam, "seeds": list(seeds)}, cps_scale(seeds, 3)


def control_rows():
    for g in MOS_GENERATORS_CENTS:
        g01 = g / 1200.0
        for n, scale in sorted(mos_scales(g01).items()):
            yield {"family": "mos", "generator_cents": g}, scale
        for n in (6, 20):
            chain = canonical_cents_scale(
                (k * g) % 1200.0 for k in range(n))
            yield {"family": "chain", "generator_cents": g,
                   "chain_n": n}, chain
    rng = random.Random(RANDOM_SEED)
    for n in (6, 20):
        for i in range(20):
            scale = canonical_cents_scale(
                rng.uniform(0.0, 1200.0) for _ in range(n))
            yield {"family": "random", "n": n, "index": i}, scale


def main() -> None:
    rows = []
    for meta, ratios in ji_rows():
        score = mel.score_melodic_rational(ratios)
        tau = mel.best_val_kendall_tau(ratios)
        rows.append({
            **meta,
            **melodic_row(score),
            "val_min_tau": tau.min_tau,
            "val_best": list(tau.best_val),
            "val_primes": list(tau.primes),
            "harmonic": harmonic_row_rational(ratios),
        })
    for meta, cents in control_rows():
        score = mel.score_melodic(cents)
        rows.append({
            **meta,
            **melodic_row(score),
            "harmonic": harmonic_row_cents(cents),
        })

    RESULTS.parent.mkdir(exist_ok=True)
    with RESULTS.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    # ---- summary for the pre-registered verdicts ---------------------------
    by = lambda fam: [r for r in rows if r["family"] == fam]  # noqa: E731
    hexanies, eiks = by("hexany"), by("eikosany") + by("eikosany_cal")
    mos, chains, rand = by("mos"), by("chain"), by("random")

    eik_wilson = next(r for r in eiks if r.get("seeds") == [1, 3, 5, 7, 9, 11])
    print(f"rows: {len(rows)} -> {RESULTS}")
    print("\nH-L1  eikosany {1,3,5,7,9,11}:"
          f" cs_violations={eik_wilson['m2_cs_violations']}"
          f" is_cs={eik_wilson['m2_is_cs']}"
          f" propriety={eik_wilson['m3_class']}"
          f" gap_classes={eik_wilson['m1_gap_classes']}"
          f" val_tau={eik_wilson['val_min_tau']}")

    def frac_improper(rs):
        return sum(r["m3_class"] == "improper" for r in rs) / len(rs)

    def frac_proper_or_strict(rs):
        return sum(r["m3_class"] != "improper" for r in rs) / len(rs)

    print("\nH-L2a  improper fraction: "
          f"hexanies {frac_improper(hexanies):.2f}, "
          f"eikosanies {frac_improper(eiks):.2f}; "
          f"MOS proper-or-strict {frac_proper_or_strict(mos):.2f} "
          f"(n={len(mos)})")
    mos6 = [r for r in mos + chains if r["cardinality"] == 6]
    mos20 = [r for r in mos + chains if r["cardinality"] == 20]
    print("H-L2b  mean gap classes: "
          f"hexany {mean(r['m1_gap_classes'] for r in hexanies):.2f} vs "
          f"rank-1 N=6 {mean(r['m1_gap_classes'] for r in mos6):.2f}; "
          f"eikosany {mean(r['m1_gap_classes'] for r in eiks):.2f} vs "
          f"rank-1 N=20 {mean(r['m1_gap_classes'] for r in mos20):.2f}")
    hx_ent = sorted(r["m1_entropy_bits"] for r in hexanies)
    hx_m3 = sorted(r["m3_violations"] for r in hexanies)
    print("H-L2c  within-hexany spread: entropy "
          f"[{hx_ent[0]:.3f}..{hx_ent[-1]:.3f}], "
          f"propriety violations [{hx_m3[0]}..{hx_m3[-1]}], "
          f"distinct entropy values={len(set(hx_ent))}/70")
    print("controls  random improper fraction: "
          f"{frac_improper(rand):.2f}; random mean gap classes "
          f"N=6 {mean(r['m1_gap_classes'] for r in rand if r['n'] == 6):.2f}, "
          f"N=20 {mean(r['m1_gap_classes'] for r in rand if r['n'] == 20):.2f}")
    cs_ji = [r for r in hexanies + eiks if r["m2_is_cs"]]
    print(f"CS holds for {len(cs_ji)}/{len(hexanies) + len(eiks)} JI scales")


if __name__ == "__main__":
    main()
