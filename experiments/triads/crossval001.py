"""CROSSVAL-001: chain-of-custody validation.

Link 1 (bit-exact): the real compiled C++ (cpp_receipts/, which builds the
plugin's actual Microtone.cpp/Fraction.cpp) vs cpp_mirror.py. Every case
must agree at the IEEE-754 bit level; any mismatch exits nonzero.

Link 2 (attributed divergence): the plugin's triad analyzer (bit-exact
mirror) vs the exact rational scorer, across all 70 odd-seed hexanies and
the harmonic segment. The analyzer's three deviations (absolute linear
tolerance, 9/8..4/3 interval filter, one-octave+wrap domain) are reported
so no count difference is ever mysterious.

Run from experiments/triads/:
    python3.12 crossval001.py
"""

from __future__ import annotations

import json
import struct
import subprocess
import sys
from fractions import Fraction
from math import log2
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cpp_mirror as cm  # noqa: E402
import scorer  # noqa: E402
from families.cps import cps_products, odd_seed_sets  # noqa: E402


def float_bits(x: float) -> str:
    return format(struct.unpack("<I", struct.pack("<f", x))[0], "08x")


# --------------------------------------------------------------------------
# Link 1: real C++ vs mirror, bit level
# --------------------------------------------------------------------------

JB2 = cm.f32(2.0 - 2.0 ** -23)  # nextafterf(2, 1)
JA2 = cm.f32(2.0 + 2.0 ** -22)  # nextafterf(2, 3)
JB1 = cm.f32(1.0 - 2.0 ** -24)  # nextafterf(1, 0)
JB4 = cm.f32(4.0 - 2.0 ** -22)  # nextafterf(4, 1)

MIRROR_CASES = {
    "one": lambda: cm.microtone_octave_reduce_float(1.0),
    "two": lambda: cm.microtone_octave_reduce_float(2.0),
    "three": lambda: cm.microtone_octave_reduce_float(3.0),
    "three_point_five": lambda: cm.microtone_octave_reduce_float(3.5),
    "zero_point_three": lambda: cm.microtone_octave_reduce_float(cm.f32(0.3)),
    "tiny": lambda: cm.microtone_octave_reduce_float(cm.f32(1e-6)),
    "huge": lambda: cm.microtone_octave_reduce_float(cm.f32(1e6)),
    "just_below_two": lambda: cm.microtone_octave_reduce_float(JB2),
    "just_above_two": lambda: cm.microtone_octave_reduce_float(JA2),
    "just_below_one": lambda: cm.microtone_octave_reduce_float(JB1),
    "just_below_four": lambda: cm.microtone_octave_reduce_float(JB4),
    "cps_1x3": lambda: cm.cps_product_reduce([1.0, 3.0]),
    "cps_1x5": lambda: cm.cps_product_reduce([1.0, 5.0]),
    "cps_1x7": lambda: cm.cps_product_reduce([1.0, 7.0]),
    "cps_3x5": lambda: cm.cps_product_reduce([3.0, 5.0]),
    "cps_3x7": lambda: cm.cps_product_reduce([3.0, 7.0]),
    "cps_5x7": lambda: cm.cps_product_reduce([5.0, 7.0]),
    "cps_1p3x2p6": lambda: cm.cps_product_reduce([cm.f32(1.3), cm.f32(2.6)]),
}

RATIONAL_CASES = {
    "r_35_16": Fraction(35, 16),
    "r_3_1": Fraction(3, 1),
    "r_1_3": Fraction(1, 3),
    "r_2_1": Fraction(2, 1),
    "r_1_1": Fraction(1, 1),
    "r_45_8": Fraction(45, 8),
    "r_135_64": Fraction(135, 64),
    "r_boundary_2e25": Fraction(2 ** 25 - 1, 2 ** 24),
    "r_boundary_2e24": Fraction(2 ** 24 - 1, 2 ** 23),
}


def run_cpp_harness() -> list[dict]:
    build = subprocess.run(
        ["make", "run"], cwd=HERE / "cpp_receipts",
        capture_output=True, text=True,
    )
    if build.returncode != 0:
        print(build.stdout)
        print(build.stderr, file=sys.stderr)
        raise RuntimeError("cpp_receipts build/run failed")
    json_text = build.stdout[build.stdout.index("["):]
    return json.loads(json_text)


def validate_link1(records: list[dict]) -> list[dict]:
    failures = []
    rows = []
    for rec in records:
        label = rec["label"]
        if rec["kind"] in ("float_reduce", "cps_product_reduce"):
            mirror_value = MIRROR_CASES[label]()
            ok = float_bits(mirror_value) == rec["bits"]
            rows.append({"label": label, "cpp_bits": rec["bits"],
                         "mirror_bits": float_bits(mirror_value), "match": ok})
        elif rec["kind"] == "rational_reduce":
            reduced = cm.microtone_octave_reduce_rational(RATIONAL_CASES[label])
            fv = cm.fraction_float_value(reduced)
            ok = (reduced.numerator == rec["num"]
                  and reduced.denominator == rec["den"]
                  and float_bits(fv) == rec["bits"])
            rows.append({"label": label,
                         "cpp": f"{rec['num']}/{rec['den']}",
                         "mirror": f"{reduced.numerator}/{reduced.denominator}",
                         "cpp_bits": rec["bits"], "mirror_bits": float_bits(fv),
                         "match": ok})
        else:
            raise ValueError(f"unknown kind {rec['kind']}")
        if not rows[-1]["match"]:
            failures.append(rows[-1])
    print(f"link 1: {len(rows)} cases, {len(rows) - len(failures)} bit-exact, "
          f"{len(failures)} mismatches")
    for f in failures:
        print("  MISMATCH:", f)
    if failures:
        raise SystemExit(1)
    return rows


# --------------------------------------------------------------------------
# Link 2: plugin analyzer (mirror) vs exact scorer, attributed
# --------------------------------------------------------------------------


def analyzer_vs_exact() -> dict:
    corpus = {}
    for seeds in odd_seed_sets(4, 15):
        freqs = cm.hexany_frequencies_f32([float(s) for s in seeds])
        products = cps_products(seeds, 2)
        corpus[f"hexany {'-'.join(map(str, seeds))}"] = (freqs, products)
    seg = [Fraction(h, 8) for h in range(8, 17)]
    seg_scale = scorer.canonical_rational_scale(seg)
    corpus["segment 8..16"] = (
        tuple(sorted(cm.f32(float(x)) for x in seg_scale)), seg)

    rows = []
    for name, (freqs, exact_ratios) in corpus.items():
        plugin = cm.analyze_proportional_triads(freqs)
        no_filter = cm.analyze_proportional_triads(freqs, interval_filter=False)
        exact_win = scorer.score_rational(exact_ratios)
        exact_anc = scorer.score_rational_anchored(exact_ratios)
        rows.append({
            "scale": name,
            "plugin_P": plugin.proportional, "plugin_S": plugin.subcontrary,
            "nofilter_P": no_filter.proportional, "nofilter_S": no_filter.subcontrary,
            "window_P": exact_win.proportional, "window_S": exact_win.subcontrary,
            "anchored_P": exact_anc.proportional, "anchored_S": exact_anc.subcontrary,
        })
    return {"rows": rows}


def tolerance_register_table() -> list[dict]:
    """The plugin tolerance is 0.0005 in ABSOLUTE linear frequency, so its
    width in cents depends on register within the octave."""
    table = []
    for f in (1.0, 1.25, 1.5, 1.75, 1.999):
        cents = 1200.0 * log2((f + cm.F32_TOLERANCE) / f)
        table.append({"frequency": f, "tolerance_cents": round(cents, 4)})
    return table


def main() -> None:
    records = run_cpp_harness()
    link1 = validate_link1(records)

    link2 = analyzer_vs_exact()
    tol = tolerance_register_table()

    print("\ntolerance 0.0005 absolute -> cents by register:")
    for row in tol:
        print(f"  f={row['frequency']:<6} {row['tolerance_cents']:.3f} cents")

    rows = link2["rows"]
    hex_rows = [r for r in rows if r["scale"].startswith("hexany")]
    agree_plugin_window = sum(
        1 for r in hex_rows
        if (r["plugin_P"], r["plugin_S"]) == (r["window_P"], r["window_S"]))
    print(f"\nlink 2: hexanies where plugin-mirror == exact window counts: "
          f"{agree_plugin_window}/{len(hex_rows)}")
    print("sample rows (plugin | no-filter | exact-window | exact-anchored):")
    for r in rows[:6] + [r for r in rows if r["scale"] == "segment 8..16"]:
        print(f"  {r['scale']:24s} "
              f"({r['plugin_P']:3d},{r['plugin_S']:3d}) | "
              f"({r['nofilter_P']:3d},{r['nofilter_S']:3d}) | "
              f"({r['window_P']:3d},{r['window_S']:3d}) | "
              f"({r['anchored_P']:3d},{r['anchored_S']:3d})")

    out = HERE / "results" / "crossval001.json"
    out.parent.mkdir(exist_ok=True)
    payload = {
        "link1_bit_exact_cases": link1,
        "link2_analyzer_vs_exact": rows,
        "tolerance_register_table": tol,
        "scorer_version": scorer.SCORER_VERSION,
    }
    out.write_text(json.dumps(payload, indent=1), encoding="ascii")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
