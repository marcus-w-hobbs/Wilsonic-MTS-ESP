"""HEX-003 + EIK-001: dual-swap verification and eikosany calibration.

HEX-003: score the period-space dual of all 70 odd-seed hexanies; verify
the exact P<->S swap under both conventions.

EIK-001: score CPS(6,3) eikosanies on the exact path — Marcus's
calibration set {1,45,135,225,19,377} plus all C(8,6)=28 seed sets from
odds <= 15 — and test the P = S diagonal prediction (anchored).

Run from experiments/triads/:  python3.12 hex003_eik001.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scorer  # noqa: E402
from families.cps import cps_products, cps_scale, odd_seed_sets  # noqa: E402
from scala import write_scl  # noqa: E402

MARCUS_EIKOSANY = (1, 45, 135, 225, 19, 377)


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def hex003() -> dict:
    swap_failures = []
    for seeds in odd_seed_sets(4, 15):
        products = cps_products(seeds, 2)
        dual = scorer.invert_rational_scale(products)
        for score_fn in (scorer.score_rational, scorer.score_rational_anchored):
            fwd = score_fn(products)
            rev = score_fn(dual)
            if (rev.proportional, rev.subcontrary, rev.geometric) != (
                    fwd.subcontrary, fwd.proportional, fwd.geometric):
                swap_failures.append({
                    "seeds": list(seeds), "convention": fwd.convention,
                    "fwd": [fwd.proportional, fwd.subcontrary],
                    "dual": [rev.proportional, rev.subcontrary],
                })
    return {"scales": 70, "swap_failures": swap_failures}


def eik001() -> dict:
    rows = []
    seed_sets = [MARCUS_EIKOSANY] + list(odd_seed_sets(6, 15))
    for seeds in seed_sets:
        products = cps_products(seeds, 3)
        anc = scorer.score_rational_anchored(products)
        win = scorer.score_rational(products)
        rows.append({
            "seeds": list(seeds),
            "cardinality": len(anc.scale),
            "anchored": [anc.proportional, anc.subcontrary, anc.geometric],
            "window": [win.proportional, win.subcontrary, win.geometric],
            "on_diagonal_anchored": anc.proportional == anc.subcontrary,
        })
    return {"rows": rows}


def main() -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    h = hex003()
    print(f"HEX-003: {h['scales']} duals scored under both conventions; "
          f"{len(h['swap_failures'])} swap failures")

    e = eik001()
    off_diag = [r for r in e["rows"] if not r["on_diagonal_anchored"]]
    print(f"EIK-001: {len(e['rows'])} eikosanies; "
          f"{len(off_diag)} off the P=S diagonal (anchored)")
    ranked = sorted(e["rows"], key=lambda r: (-min(r["anchored"][0], r["anchored"][1]),
                                              r["seeds"]))
    for r in ranked[:8]:
        marker = "  <-- Marcus calibration" if tuple(r["seeds"]) == MARCUS_EIKOSANY else ""
        print(f"  seeds {r['seeds']}: card={r['cardinality']} "
              f"anchored P,S,G={r['anchored']} window={r['window']}{marker}")
    cal = next(r for r in e["rows"] if tuple(r["seeds"]) == MARCUS_EIKOSANY)
    rank = 1 + sum(1 for r in e["rows"]
                   if min(r["anchored"][0], r["anchored"][1])
                   > min(cal["anchored"][0], cal["anchored"][1]))
    print(f"  calibration set rank by anchored min(P,S): {rank}/{len(e['rows'])}")

    scl_dir = HERE / "results" / "scl"
    scl_dir.mkdir(parents=True, exist_ok=True)
    top = ranked[0]
    for r in (top, cal):
        tag = "-".join(str(s) for s in r["seeds"])
        desc = (f"eikosany {tag}  anchored P={r['anchored'][0]} "
                f"S={r['anchored'][1]} (scorer {scorer.SCORER_VERSION}, "
                f"{_commit()[:8]})")
        write_scl(scl_dir / f"eik_{tag}.scl", desc,
                  cps_products(tuple(r["seeds"]), 3))

    out = HERE / "results" / "hex003_eik001.json"
    out.write_text(json.dumps({
        "hex003": h, "eik001": e, "scorer_version": scorer.SCORER_VERSION,
        "commit": _commit(), "timestamp": stamp,
    }, indent=1), encoding="ascii")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
