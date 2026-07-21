"""CROSSVAL-002: corpus-level validation against the REAL plugin code.

Runs every odd-seed hexany (70) and a MOS sweep through tests/research_cli
(the plugin's actual Microtone/MicrotoneArray/TuningImp/Brun sources) and
checks, per scale:

1. hexany scale degrees match the float32 mirror BIT-FOR-BIT;
2. MOS scale degrees match a float32 simulation of Brun's log-space
   construction within 1 ulp (the pow() conversion is libm, the only
   place bit equality cannot be demanded);
3. the analyzer counts reported by the real C++ equal the mirror's
   plugin-exact counts when fed the C++'s own reported scale.

Any failure exits nonzero. Run from experiments/triads/:
    python3.12 crossval002.py
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cpp_bridge  # noqa: E402
import cpp_mirror as cm  # noqa: E402
from families.cps import odd_seed_sets  # noqa: E402


def float_bits(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0]


def mos_frequencies_f32(generator: float, level: int) -> list[float]:
    """Float32 simulation of Brun::_microtoneArrayBrun at murchana 0
    (Brun.cpp:308-357) + the LogPeriod processing pipeline:
    p = degree*g mod 1 (float32), frequency = pow(2, p) truncated to
    float32 (Microtone.cpp:299)."""
    g = cm.f32(generator)
    num_degrees = {0: 1, 1: 2, 2: 3, 3: 5, 4: 7, 5: 12, 6: 17, 7: 29, 8: 41, 9: 53}
    # cardinality from the real zigzag, re-derived per generator
    n = zigzag_denominator(g, level)
    pitches = []
    for degree in range(n):
        p = cm.f32(float(degree) * g)
        while p < 0.0:
            p = cm.f32(p + 1.0)
        while p > 1.0:
            p = cm.f32(p - 1.0)
        # _update's octaveReduce in LogPeriod space: fmod into [0, 1)
        if p < 0.0:
            p = cm.f32(p + 1.0)
        p = cm.f32(math.fmod(p, 1.0))
        pitches.append(p)
    freqs = sorted(cm.f32(2.0 ** p) for p in pitches)
    del num_degrees
    return freqs


def zigzag_denominator(g: float, level: int) -> int:
    """The Brun zigzag (Brun.cpp:269-299), float32-faithful."""
    mos_a, mos_b = cm.f32(1.0), cm.f32(g)
    x1, x2, y1, y2 = 1, 0, 0, 1
    num = den = 1
    for _ in range(level):
        num = 2 * y1 + y2
        den = 2 * x1 + x2
        mos_a = cm.f32(mos_a - mos_b)
        x2 = x1 + x2
        y2 = y1 + y2
        if mos_b > mos_a:
            mos_a, mos_b = mos_b, mos_a
            x1, x2 = x2, x1
            y1, y2 = y2, y1
    return den


def main() -> None:
    cpp_bridge.build_cli()
    failures = 0
    hex_rows = []

    for seeds in odd_seed_sets(4, 15):
        cpp = cpp_bridge.hexany([float(s) for s in seeds])
        mirror_scale = cm.hexany_frequencies_f32([float(s) for s in seeds])
        cpp_bits = [r["bits"] for r in cpp["scale"]]
        mirror_bits = [format(float_bits(f), "08x") for f in mirror_scale]
        counts = cm.analyze_proportional_triads([r["float"] for r in cpp["scale"]])
        ok_scale = cpp_bits == mirror_bits
        ok_counts = (cpp["proportional"], cpp["subcontrary"]) == (
            counts.proportional, counts.subcontrary)
        if not (ok_scale and ok_counts):
            failures += 1
            print(f"MISMATCH hexany {seeds}: scale_ok={ok_scale} "
                  f"cpp=({cpp['proportional']},{cpp['subcontrary']}) "
                  f"mirror=({counts.proportional},{counts.subcontrary})")
        hex_rows.append({
            "seeds": list(seeds),
            "cpp_P": cpp["proportional"], "cpp_S": cpp["subcontrary"],
            "scale_bit_exact": ok_scale, "counts_match": ok_counts,
        })

    mos_rows = []
    for g in (0.5849625, 0.41805, 0.32):
        for level in range(3, 8):
            cpp = cpp_bridge.mos(g, level)
            sim = mos_frequencies_f32(g, level)
            cpp_floats = [r["float"] for r in cpp["scale"]]
            ok_card = len(cpp_floats) == len(sim)
            max_ulp = 0
            if ok_card:
                for a, b in zip(cpp_floats, sim):
                    max_ulp = max(max_ulp, abs(float_bits(a) - float_bits(b)))
            counts = cm.analyze_proportional_triads(cpp_floats)
            ok_counts = (cpp["proportional"], cpp["subcontrary"]) == (
                counts.proportional, counts.subcontrary)
            ok = ok_card and max_ulp <= 1 and ok_counts
            if not ok:
                failures += 1
                print(f"MISMATCH mos g={g} level={level}: card_ok={ok_card} "
                      f"max_ulp={max_ulp} counts_ok={ok_counts}")
            mos_rows.append({
                "generator": g, "level": level, "cardinality": len(cpp_floats),
                "cpp_P": cpp["proportional"], "cpp_S": cpp["subcontrary"],
                "max_ulp": max_ulp, "ok": ok,
            })

    out = HERE / "results" / "crossval002.json"
    out.write_text(json.dumps({"hexanies": hex_rows, "mos": mos_rows}, indent=1),
                   encoding="ascii")
    n_hex = len(hex_rows)
    n_mos = len(mos_rows)
    print(f"crossval002: {n_hex} hexanies + {n_mos} MOS scales through the "
          f"real C++; {failures} mismatches")
    print(f"wrote {out}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
