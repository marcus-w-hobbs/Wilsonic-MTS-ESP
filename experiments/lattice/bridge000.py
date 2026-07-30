"""BRIDGE-000 — D'Alessandro as calibration standard (SPEC §BRIDGE-000).

Pre-registered in LOG.md 2026-07-29 BEFORE the scan was opened. Encodes
Wilson's fig-24 D'Alessandro (issued 1975, (c) 1989): the 1.3.5.7.9.11
Combination-Product Set series mapped to modulus 31 and the Bosanquet
keyboard, both lifts (+18 huygens / -13 meanpop inverted, figs 26-27).
Verification anchors transcribed from dal.PDF are in
BRIDGE000_TRANSCRIPTION.md; this module must reproduce every one.

Construction (fig 24 template):
- factor chain positions (fifths): 1->0, 3->+1, 9->+2, 5->+4, 7->+10,
  11->+18 (huygens) / 11->-13 (meanpop). Degree(p) = 18*p mod 31.
- EG6 = all 32 subset products of {3,9,5,7,11}; positions are subset sums.
- 6 pigtails fill the holes and extend the ends: -1 = 3*5*7*9/11,
  +8 = 3^4*5, +9 = 7/3, +26 = 3^4*5*11, +27 = 7*11/3, +36 = 11^2.
  (Huygens chain -1..+36 is then CONSECUTIVE: 38 tones, 38 slots.)

Run from experiments/lattice/:  python3.12 bridge000.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import scorer as triad  # noqa: E402
from scorer import canonical_rational_scale, reduce_rational  # noqa: E402

RESULTS = HERE / "results" / "bridge000.json"
MODULUS = 31
GEN_DEG = 18  # degree of one chain step (3/2 -> 18\31)

FACTORS = (3, 9, 5, 7, 11)
POS_HUYGENS = {3: 1, 9: 2, 5: 4, 7: 10, 11: 18}
POS_MEANPOP = {**POS_HUYGENS, 11: -13}

#: fig 24 pigtails: chain position -> exact ratio (pre-octave-reduction)
PIGTAILS = {
    -1: Fraction(3 * 5 * 7 * 9, 11),
    8: Fraction(3**4 * 5),
    9: Fraction(7, 3),
    26: Fraction(3**4 * 5 * 11),
    27: Fraction(7 * 11, 3),
    36: Fraction(11**2),
}

#: Wilson's template as an integer val on primes (2,3,5,7,11); huygens.
WILSON_VAL = (31, 49, 72, 87, 107)

#: Anchors transcribed by eye from dal.PDF fig 24 / figs 26-27 (see
#: BRIDGE000_TRANSCRIPTION.md). The code must reproduce every entry.
FIG24_TEMPLATE_ANCHORS = {1: (0, 0), 3: (1, 18), 9: (2, 5), 5: (4, 10),
                          7: (10, 25), 11: (18, 14)}
FIG24_DUP_DEGREES = {0, 5, 10, 13, 18, 23, 28}
FIG24_COMMAS = {"385/384": 3, "2079/2048": 2, "121/120": 2}


def eg6_tones() -> dict[int, Fraction]:
    """32 EG6 tones keyed by huygens chain position (subset sums)."""
    tones: dict[int, Fraction] = {}
    for r in range(len(FACTORS) + 1):
        for combo in combinations(FACTORS, r):
            pos = sum(POS_HUYGENS[f] for f in combo)
            val = Fraction(1)
            for f in combo:
                val *= f
            assert pos not in tones, f"position collision at {pos}"
            tones[pos] = val
    return tones


def dalessandro() -> dict[int, Fraction]:
    """All 38 tones keyed by huygens chain position (-1..36 consecutive)."""
    tones = eg6_tones()
    for pos, ratio in PIGTAILS.items():
        assert pos not in tones, f"pigtail {pos} overlaps EG6"
        tones[pos] = ratio
    return tones


def factor_monzo(ratio: Fraction) -> tuple[int, ...]:
    """Monzo over primes (2,3,5,7,11) — sufficient for this tone set."""
    m = [0, 0, 0, 0, 0]
    primes = (2, 3, 5, 7, 11)
    n, d = ratio.numerator, ratio.denominator
    for i, p in enumerate(primes):
        while n % p == 0:
            n //= p
            m[i] += 1
        while d % p == 0:
            d //= p
            m[i] -= 1
    assert n == 1 and d == 1, f"prime outside 11-limit in {ratio}"
    return tuple(m)


def val_degree(val: tuple[int, ...], ratio: Fraction) -> int:
    """v . monzo(ratio) mod 31 — the keyboard address."""
    return sum(v * m for v, m in zip(val, factor_monzo(ratio))) % MODULUS


def collisions(tones: dict[int, Fraction], val=WILSON_VAL):
    """Degree -> list of (position, ratio); only degrees with >= 2 tones."""
    by_deg: dict[int, list] = {}
    for pos, ratio in sorted(tones.items()):
        by_deg.setdefault(val_degree(val, ratio), []).append((pos, ratio))
    return {d: v for d, v in by_deg.items() if len(v) > 1}


def comma_of(a: Fraction, b: Fraction) -> Fraction:
    """The comma between two colliding tones: the octave-equivalent
    representative of a/b closest to (and >= ) 1."""
    r = reduce_rational(a / b)
    return 2 / r if r * r > 2 else r


def tie_pairs(tones: dict[int, Fraction], val) -> tuple[int, int]:
    """(#pairs sharing a degree, #degrees hosting 3+ tones) for a val."""
    counts: dict[int, int] = {}
    for ratio in tones.values():
        d = val_degree(val, ratio)
        counts[d] = counts.get(d, 0) + 1
    pairs = sum(c * (c - 1) // 2 for c in counts.values())
    triples = sum(1 for c in counts.values() if c >= 3)
    return pairs, triples


def main() -> None:
    tones = dalessandro()

    # ---- verification against fig 24 anchors -------------------------------
    positions = sorted(tones)
    assert positions == list(range(-1, 37)), "chain not consecutive -1..36"
    for f, (pos, deg) in FIG24_TEMPLATE_ANCHORS.items():
        assert POS_HUYGENS.get(f, 0) == pos or f == 1
        assert (GEN_DEG * pos) % MODULUS == deg, f"template degree {f}"
        assert val_degree(WILSON_VAL, Fraction(f)) == deg, f"val degree {f}"

    col = collisions(tones)
    assert set(col) == FIG24_DUP_DEGREES, f"dup degrees {sorted(col)}"
    comma_census: dict[str, int] = {}
    collision_rows = []
    for deg, members in sorted(col.items()):
        assert len(members) == 2, f"degree {deg} hosts {len(members)} tones"
        (p1, r1), (p2, r2) = members
        c = comma_of(r1, r2)
        key = f"{c.numerator}/{c.denominator}"
        comma_census[key] = comma_census.get(key, 0) + 1
        collision_rows.append({"degree": deg, "positions": [p1, p2],
                               "tones": [str(r1), str(r2)], "comma": key})
    assert comma_census == FIG24_COMMAS, f"comma census {comma_census}"

    # meanpop (inverted, figs 26-27): same degrees, shrunken chain
    pos_meanpop = {}
    for pos, ratio in tones.items():
        m = factor_monzo(ratio)
        p_inv = m[1] * 1 + m[2] * 4 + m[3] * 10 + m[4] * (-13)
        # 9's exponent is inside m[1] (3^2) — linear treatment is automatic
        pos_meanpop[pos] = p_inv
    inv_positions = sorted(pos_meanpop.values())
    inv_span = (min(inv_positions), max(inv_positions))
    inv_unisons = len(inv_positions) - len(set(inv_positions))

    # ---- Pareto pair: harmonic wealth --------------------------------------
    scale = canonical_rational_scale(tones.values())
    full = triad.score(scale)
    hexanies = []
    for quad in combinations((1, 3, 5, 7, 9, 11), 4):
        hex_tones = [Fraction(a * b) for a, b in combinations(quad, 2)]
        degs = [val_degree(WILSON_VAL, t) for t in hex_tones]
        hx = triad.score(hex_tones)
        hexanies.append({
            "seeds": list(quad),
            "P": hx.proportional, "S": hx.subcontrary, "G": hx.geometric,
            "degrees": sorted(degs),
            "injective_addressing": len(set(degs)) == len(degs),
        })
    injective = sum(h["injective_addressing"] for h in hexanies)

    # ---- H-B1: tie-optimality of Wilson's val ------------------------------
    wilson_pairs, wilson_triples = tie_pairs(tones, WILSON_VAL)
    sweep = []
    better = equal = 0
    for offs in product((-1, 0, 1), repeat=4):
        val = (31,) + tuple(v + o for v, o in zip(WILSON_VAL[1:], offs))
        pairs, triples = tie_pairs(tones, val)
        sweep.append({"val": list(val), "tie_pairs": pairs,
                      "degrees_with_3plus": triples})
        if val != WILSON_VAL:
            if pairs < wilson_pairs:
                better += 1
            elif pairs == wilson_pairs:
                equal += 1

    result = {
        "experiment": "BRIDGE-000", "date": "2026-07-29",
        "scorer_version": full.scorer_version,
        "source": "dal.PDF fig 24 (huygens) + figs 26-27 (meanpop); "
                  "anchors in BRIDGE000_TRANSCRIPTION.md",
        "verification": {
            "chain_consecutive_-1..36": True,
            "template_anchors": "all reproduced",
            "duplicated_degrees": sorted(col),
            "collisions": collision_rows,
            "comma_census": comma_census,
            "meanpop": {"span": inv_span,
                        "position_unisons": inv_unisons},
        },
        "pareto_standard": {
            "harmonic_wealth": {
                "full_38_tone": {"P": full.proportional,
                                 "S": full.subcontrary,
                                 "G": full.geometric,
                                 "cardinality": len(scale)},
                "embedded_hexanies": hexanies,
                "hexanies_injectively_addressed": f"{injective}/15",
            },
            "addressing_cost": {
                "collision_count": len(col),
                "pigeonhole_floor": 38 - MODULUS,
                "at_floor": len(col) == 38 - MODULUS,
                "commas": comma_census,
            },
            "cents_error": 0.0,  # regime iii: pitch-just by construction
        },
        "h_b1": {
            "wilson_val": list(WILSON_VAL),
            "wilson_tie_pairs": wilson_pairs,
            "wilson_degrees_with_3plus": wilson_triples,
            "neighbors_strictly_better": better,
            "neighbors_equal": equal,
            "neighborhood_size": len(sweep) - 1,
            "sweep": sweep,
        },
    }
    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(result, indent=1))

    print(f"38 tones, chain -1..36 consecutive: OK; {len(scale)} distinct "
          f"pitch classes")
    print(f"collisions at degrees {sorted(col)}; commas {comma_census}")
    print(f"meanpop chain span {inv_span}, position unisons {inv_unisons}")
    print(f"full-set frozen score: P={full.proportional} "
          f"S={full.subcontrary} G={full.geometric}")
    print(f"hexanies injectively addressed: {injective}/15")
    print(f"H-B1: Wilson val ties={wilson_pairs} (floor "
          f"{38 - MODULUS}), triples={wilson_triples}; neighbors better: "
          f"{better}, equal: {equal} of {len(sweep) - 1}")


if __name__ == "__main__":
    main()
