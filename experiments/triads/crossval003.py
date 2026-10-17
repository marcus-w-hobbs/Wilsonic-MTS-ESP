"""CROSSVAL-003: geometric triads, mirror vs the REAL plugin analyzer.

PR #59 (plugin lane, branch plugin/geometric-triads) made
TuningImp::_analyzeProportionalTriads compute geometric triads
(sqrtf(imf*jmf) tested against each inner degree under the same 9/8..4/3
window and 0.0005 linear tolerance as P and S) and made tests/research_cli
emit a "geometric" JSON key. cpp_mirror.py now mirrors that path. This
script runs every scale the CLI can express through the plugin's actual
Microtone/MicrotoneArray/TuningImp/Brun sources and checks, per scale:

1. hexany scale degrees match the float32 mirror BIT-FOR-BIT (as in
   crossval002); MOS degrees are recorded with their max ulp distance
   from the float32 Brun simulation (pow() is libm, so 1 ulp is allowed);
2. the analyzer counts reported by the real C++ — proportional,
   subcontrary AND geometric — equal the mirror's plugin-exact counts when
   the mirror is fed the C++'s own reported scale (counts are integers, so
   "match" means exact equality; the scale fed in is bit-identical).

Corpus: the 70 odd-seed hexanies (seeds <= 15), the crossval002 MOS sweep
(three generators x levels 3..7), and ET-like inputs. The CLI has no ET
command, but the plugin's own Brun MOS with a rational generator p/N at
the level whose zigzag denominator is N IS the plugin's N-ET (float32
degree*g, pow(2, p)), so 5/6/7/12/19/31-ET are expressed that way. The
just chain 1 9/8 5/4 25/16 3/2 15/8 (G = 1 at degrees 0,2,4) cannot be
expressed through the CLI and lives in tests/test_cpp_mirror.py only.

Expectations carried from PR #59's own C++ tests are re-checked here and
fail the run if broken: 12-ET reports 10, 6-ET reports 2, and the 12-tone
Pythagorean MOS (generator 0.5849625, level 5) reports 6.

PR #59 also stated that every CPS scale reports G = 0 under the window.
The first run of this script (2026-10-17) showed that is too strong: the
hexany 3-5-9-15 reports G = 2 in the real C++ and in the mirror alike.
With odd seeds a hexany's pair-products p1, p2, p3 form a geometric chain
(p1*p3 = p2^2) only when the seed set has a multiplicative coincidence
a*d = b*c; then a*d is a duplicated tone, the two chains {ab, ad, cd} and
{ac, ad, bd} have ratios d/b and d/c, and each window-passing chain yields
two index sets through the duplicate. 3*15 = 5*9 gives 27:45:75 with
ratio 5/3 (6/5 reduced, inside the window), hence G = 2. 1*15 = 3*5 gives
3:15:75 with ratio 5/4, also inside the window, but that chain wraps the
octave and the NPO-map filter drops it, so 1-3-5-15 reports G = 0 while
its search loop finds 2. The check enforced here is the refined claim:
a hexany reports G > 0 only if its seed set has a duplicated product.

Any failure exits nonzero. Run from experiments/triads/:
    python3.12 crossval003.py
"""

from __future__ import annotations

import itertools
import json
import struct
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cpp_bridge  # noqa: E402
import cpp_mirror as cm  # noqa: E402
import scorer  # noqa: E402
from crossval002 import mos_frequencies_f32  # noqa: E402
from families.cps import odd_seed_sets  # noqa: E402

MOS_SWEEP = [(g, level) for g in (0.5849625, 0.41805, 0.32)
             for level in range(3, 8)]

# (N, p, level): generator p/N reaches cardinality N at this Brun level
ET_AS_MOS = [(5, 2, 3), (6, 1, 5), (7, 3, 4), (12, 7, 5), (19, 11, 6),
             (31, 18, 7)]

EXPECTED_G = {"et 12": 10, "et 6": 2, "mos 0.5849625 L5": 6}


def float_bits(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0]


def cpp_counts(cpp: dict) -> tuple[int, int, int]:
    return (cpp["proportional"], cpp["subcontrary"], cpp["geometric"])


def has_duplicate_product(seeds: tuple[int, ...]) -> bool:
    products = [a * b for a, b in itertools.combinations(seeds, 2)]
    return len(set(products)) < len(products)


def git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True,
            text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def check_hexanies() -> tuple[list[dict], int]:
    rows, failures = [], 0
    for seeds in odd_seed_sets(4, 15):
        cpp = cpp_bridge.hexany([float(s) for s in seeds])
        mirror_scale = cm.hexany_frequencies_f32([float(s) for s in seeds])
        cpp_bits = [r["bits"] for r in cpp["scale"]]
        mirror_bits = [format(float_bits(f), "08x") for f in mirror_scale]
        counts = cm.analyze_proportional_triads([r["float"] for r in cpp["scale"]])
        ok_scale = cpp_bits == mirror_bits
        ok_counts = cpp_counts(cpp) == counts.as_tuple()
        dup = has_duplicate_product(tuple(seeds))
        loop = cm.analyze_proportional_triads(
            [r["float"] for r in cpp["scale"]], npo_map_filter=False)
        ok_g_rule = cpp["geometric"] == 0 or dup
        ok = ok_scale and ok_counts and ok_g_rule
        if not ok:
            failures += 1
            print(f"MISMATCH hexany {seeds}: scale_ok={ok_scale} "
                  f"cpp={cpp_counts(cpp)} mirror={counts.as_tuple()} "
                  f"duplicate_product={dup}")
        rows.append({
            "seeds": list(seeds),
            "cpp_P": cpp["proportional"], "cpp_S": cpp["subcontrary"],
            "cpp_G": cpp["geometric"],
            "mirror_P": counts.proportional, "mirror_S": counts.subcontrary,
            "mirror_G": counts.geometric,
            "mirror_loop_G": loop.geometric,
            "duplicate_product": dup,
            "scale_bit_exact": ok_scale, "counts_match": ok_counts,
            "ok": ok,
        })
    return rows, failures


def check_mos(label: str, g: float, level: int, expected_g: int | None) -> tuple[dict, bool]:
    cpp = cpp_bridge.mos(g, level)
    sim = mos_frequencies_f32(g, level)
    cpp_floats = [r["float"] for r in cpp["scale"]]
    ok_card = len(cpp_floats) == len(sim)
    max_ulp = 0
    if ok_card:
        for a, b in zip(cpp_floats, sim):
            max_ulp = max(max_ulp, abs(float_bits(a) - float_bits(b)))
    counts = cm.analyze_proportional_triads(cpp_floats)
    ok_counts = cpp_counts(cpp) == counts.as_tuple()
    ok_expect = expected_g is None or cpp["geometric"] == expected_g
    ok = ok_card and max_ulp <= 1 and ok_counts and ok_expect
    if not ok:
        print(f"MISMATCH {label}: card_ok={ok_card} max_ulp={max_ulp} "
              f"cpp={cpp_counts(cpp)} mirror={counts.as_tuple()} "
              f"expected_G={expected_g}")
    row = {
        "label": label, "generator": g, "level": level,
        "cardinality": len(cpp_floats),
        "cpp_P": cpp["proportional"], "cpp_S": cpp["subcontrary"],
        "cpp_G": cpp["geometric"],
        "mirror_P": counts.proportional, "mirror_S": counts.subcontrary,
        "mirror_G": counts.geometric,
        "max_ulp": max_ulp, "counts_match": ok_counts,
        "expected_G": expected_g, "ok": ok,
    }
    return row, ok


def main() -> None:
    cpp_bridge.build_cli()
    hex_rows, failures = check_hexanies()

    mos_rows = []
    for g, level in MOS_SWEEP:
        label = f"mos {g} L{level}"
        row, ok = check_mos(label, g, level, EXPECTED_G.get(label))
        mos_rows.append(row)
        failures += 0 if ok else 1

    et_rows = []
    for n, p, level in ET_AS_MOS:
        label = f"et {n}"
        row, ok = check_mos(label, p / n, level, EXPECTED_G.get(label))
        row["edo"] = n
        row["generator_steps"] = p
        et_rows.append(row)
        failures += 0 if ok else 1

    def tally(rows: list[dict], key: str) -> int:
        return sum(1 for r in rows if not r[key])

    all_rows = hex_rows + mos_rows + et_rows
    summary = {
        "date": date.today().isoformat(),
        "scorer_version": scorer.SCORER_VERSION,
        "cli_source_commit": git_head(),
        "scales": len(all_rows),
        "hexanies": len(hex_rows), "mos": len(mos_rows), "et_as_mos": len(et_rows),
        "count_mismatches": tally(all_rows, "counts_match"),
        "hexany_scale_bit_mismatches": tally(hex_rows, "scale_bit_exact"),
        "mos_max_ulp": max(r["max_ulp"] for r in mos_rows + et_rows),
        "hexanies_with_geometric": [r["seeds"] for r in hex_rows if r["cpp_G"]],
        "hexanies_with_loop_level_geometric": [
            r["seeds"] for r in hex_rows if r["mirror_loop_G"]],
        "hexanies_with_duplicate_product": [
            r["seeds"] for r in hex_rows if r["duplicate_product"]],
        "expectations": {k: next(r["cpp_G"] for r in mos_rows + et_rows
                                 if r["label"] == k) for k in EXPECTED_G},
        "failures": failures,
    }
    out = HERE / "results" / "crossval003.json"
    out.write_text(json.dumps({"summary": summary, "hexanies": hex_rows,
                               "mos": mos_rows, "et_as_mos": et_rows},
                              indent=1), encoding="ascii")
    print(f"crossval003: {len(hex_rows)} hexanies + {len(mos_rows)} MOS + "
          f"{len(et_rows)} ET-as-MOS scales through the real C++; "
          f"{summary['count_mismatches']} P/S/G count mismatches, "
          f"{failures} failures")
    print(f"geometric expectations: {summary['expectations']}")
    print(f"wrote {out}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
