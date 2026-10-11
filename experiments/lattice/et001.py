"""ET-001 — the (N, ε) phase diagram of equal temperaments under the frozen
scorers (LOG.md pre-registration 2026-08-09; committed before this file).

For every EDO N = 2..60, score the FULL N-EDO scale with the frozen triad
scorer's tempered path (v1.1.0, PRIMARY middle-anchored convention, default
max_span 1200¢) and the frozen melodic scorers (v0.1.0). Chart, as a
function of the triad-scorer tolerance ε, when proportional and subcontrary
triads first lock and how counts grow at a standard ε grid.

Method: in N-EDO the anchored sample factors into triple TYPES (p, q) =
steps below/above the middle, 1 ≤ p, q ≤ N−1, p + q ≤ N, each contributing
exactly N counted triples (transposition invariance). An analytic MIRROR
computes each type's per-class deviation and its degeneracy-guard
separation; a type is counted at ε exactly on the half-open interval
(deviation, separation]. Lock thresholds are the mirror's minima, then
VERIFIED against the frozen scorer at threshold ± δ — the scorer is the
referee, the mirror is not. Mirror-vs-scorer disagreement anywhere is
recorded as a verification failure, never patched over.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)

Receipts: results/et001.jsonl (one row per N) + results/et001_summary.json.
Deterministic: stdlib only, no randomness, no wall-clock fields; two runs
must produce bit-identical receipts.

Run from experiments/lattice/:  python3.12 et001.py
"""

from __future__ import annotations

import json
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
    DEFAULT_MAX_SPAN_CENTS,
    SCORER_VERSION,
    mean_separation_cents,
    score_tempered,
)
from melodic import (  # noqa: E402  (frozen v0.1.0, read-only)
    MELODIC_VERSION,
    score_melodic,
)

ET001_VERSION = "1.0.0"

# --- constants, locked in the LOG.md pre-registration (2026-08-09) ---------
N_MIN = 2
N_MAX = 60
EPS_GRID = (1.0, 2.0, 3.0, 5.0, 10.0, 14.86, 20.0)
EPS_G0 = 1e-6            # rail epsilon: geometric floor / P=S=0 check
VERIFY_DELTA = 1e-6      # lock verification: scorer queried at eps* ± delta
TIE_TOL = 1e-9           # analytic tie tolerance on lock thresholds
NAIVE_TOP5 = (53, 41, 29, 58, 12)   # H-E3 cultural hypothesis (fifth error)
CULTURE_SET = (12, 19, 22, 31, 34, 41, 53)
RESULTS_DIR = _HERE / "results"

LOG2_3_2 = log2(1.5)
LOG2_5_4 = log2(1.25)
LOG2_6_5 = log2(1.2)


# ---------------------------------------------------------------------------
# corpus
# ---------------------------------------------------------------------------


def edo_scale(n: int) -> tuple[float, ...]:
    """Degrees of N-EDO in cents: k * 1200/N for k = 0..N-1."""
    if n < 1:
        raise ValueError(f"need n >= 1, got {n}")
    return tuple(k * 1200.0 / n for k in range(n))


# ---------------------------------------------------------------------------
# analytic mirror (independent algebra; never a substitute for the scorer)
# ---------------------------------------------------------------------------


class TripleType(NamedTuple):
    """Anchored triple type (p, q): p steps below the middle, q above."""

    p: int
    q: int
    span_steps: int
    span_cents: float
    dev_p: float
    dev_s: float
    dev_g: float
    sep: float  # degeneracy-guard separation |1200*log2(AM/HM)| of outers


def mirror_type(n: int, p: int, q: int) -> TripleType:
    """Per-class deviations and guard separation for type (p, q) in N-EDO.

    Mirrors the frozen classify_cents_triple / is_informative_triple math
    with b = 0 (transposition invariance makes every anchor identical).
    """
    s = 1200.0 / n
    fa = 2.0 ** (-p * s / 1200.0)
    fc = 2.0 ** (q * s / 1200.0)
    dev_p = abs(1200.0 * log2((fa + fc) / 2.0))
    dev_s = abs(1200.0 * log2((fa + fc) / (2.0 * fa * fc)))
    dev_g = abs(1200.0 * log2(fa * fc))
    am = (fa + fc) / 2.0
    hm = 2.0 * fa * fc / (fa + fc)
    sep = abs(1200.0 * log2(am / hm))
    return TripleType(p, q, p + q, (p + q) * s, dev_p, dev_s, dev_g, sep)


def triple_types(n: int) -> tuple[TripleType, ...]:
    """All admissible types: 1 <= p, q <= N-1, p + q <= N (span <= 1200)."""
    return tuple(
        mirror_type(n, p, q)
        for p in range(1, n)
        for q in range(1, n - p + 1)
    )


def _dev_of(t: TripleType, cls: str) -> float:
    return {"P": t.dev_p, "S": t.dev_s, "G": t.dev_g}[cls]


def lock_candidates(
    types: tuple[TripleType, ...], cls: str, asymmetric_only: bool = False
) -> list[tuple[float, int, int]]:
    """(deviation, p, q) of every type that ever counts for class cls
    (deviation < separation), sorted ascending by deviation."""
    out = [
        (_dev_of(t, cls), t.p, t.q)
        for t in types
        if _dev_of(t, cls) < t.sep and not (asymmetric_only and t.p == t.q)
    ]
    return sorted(out)


def entry_multiplicity(
    types: tuple[TripleType, ...], cls: str, eps_star: float, window: float
) -> int:
    """Number of types whose class-cls deviation lies within `window` of
    eps_star and which qualify (dev < sep) — the expected count jump / N."""
    return sum(
        1
        for t in types
        if abs(_dev_of(t, cls) - eps_star) <= window and _dev_of(t, cls) < t.sep
    )


def sep_interference(
    types: tuple[TripleType, ...], eps_star: float, window: float
) -> bool:
    """True if any qualifying type's guard separation falls inside the
    verification window — a count EXIT that would pollute the jump."""
    return any(
        abs(t.sep - eps_star) <= window
        and min(t.dev_p, t.dev_s, t.dev_g) < t.sep
        for t in types
    )


# ---------------------------------------------------------------------------
# patent (nearest-degree) landmarks
# ---------------------------------------------------------------------------


def patent_fifth(n: int) -> tuple[int, float]:
    """(steps, |error|) of the patent fifth round(N*log2(3/2))."""
    steps = round(n * LOG2_3_2)
    return steps, abs(1200.0 * LOG2_3_2 - steps * 1200.0 / n)


def patent_major_pq(n: int) -> tuple[int, int]:
    """Anchored type of the patent 4:5:6: p = round(N*log2(5/4)) steps below
    the middle (the major third), q = round(N*log2(6/5)) above."""
    return round(n * LOG2_5_4), round(n * LOG2_6_5)


# ---------------------------------------------------------------------------
# frozen-scorer access (cached; the referee)
# ---------------------------------------------------------------------------


class ScorerCache:
    """Memoizes score_tempered calls per (n, eps). Read-only use of the
    frozen scorer at its default max_span (1200c)."""

    def __init__(self) -> None:
        self._cache: dict[tuple[int, float], object] = {}
        self.calls = 0

    def counts(self, n: int, eps: float):
        key = (n, eps)
        if key not in self._cache:
            self._cache[key] = score_tempered(edo_scale(n), eps)
            self.calls += 1
        return self._cache[key]

    def count(self, n: int, eps: float, cls: str) -> int:
        r = self.counts(n, eps)
        return {"P": r.proportional, "S": r.subcontrary, "G": r.geometric}[cls]


def verify_jump(
    cache: ScorerCache,
    n: int,
    types: tuple[TripleType, ...],
    cls: str,
    eps_star: float,
    expect_below_zero: bool,
) -> dict:
    """Referee check of an analytic threshold: scorer counts at eps* ± δ.

    The expected jump is N * (number of types entering at eps*); the window
    must be free of guard-separation exits (asserted analytically and
    recorded). If expect_below_zero, the below-count must be exactly 0
    (first lock); otherwise the jump alone is checked."""
    mult = entry_multiplicity(types, cls, eps_star, VERIFY_DELTA)
    interference = sep_interference(types, eps_star, VERIFY_DELTA)
    below = cache.count(n, eps_star - VERIFY_DELTA, cls)
    above = cache.count(n, eps_star + VERIFY_DELTA, cls)
    ok = (
        not interference
        and mult >= 1
        and above - below == n * mult
        and (below == 0 or not expect_below_zero)
    )
    return {
        "eps_star": eps_star,
        "count_below": below,
        "count_above": above,
        "expected_jump": n * mult,
        "entry_multiplicity": mult,
        "sep_interference": interference,
        "verified": ok,
    }


# ---------------------------------------------------------------------------
# per-N row
# ---------------------------------------------------------------------------


def melodic_row(n: int) -> dict:
    """Frozen melodic scorers (v0.1.0 defaults) on the full N-EDO scale."""
    m = score_melodic(edo_scale(n))
    return {
        "propriety": m.propriety.classification,
        "propriety_violations": m.propriety.violating_span_pairs,
        "gap_class_count": m.gap_entropy.gap_class_count,
        "entropy_bits": m.gap_entropy.entropy_bits,
        "is_cs": m.constant_structure.is_cs,
        "cs_violations": m.constant_structure.violations,
        "gap_classes_over_n": m.gap_entropy.gap_class_count / n,
    }


def _lock_block(
    cache: ScorerCache,
    n: int,
    types: tuple[TripleType, ...],
    cls: str,
) -> dict:
    """First lock of class cls: analytic minimum + scorer verification."""
    cands = lock_candidates(types, cls)
    dev, p, q = cands[0]
    ver = verify_jump(cache, n, types, cls, dev, expect_below_zero=True)
    return {
        "eps_star": dev,
        "witness_pq": [p, q],
        "witness_span_steps": p + q,
        "is_power_chord": p + q == n,
        "is_symmetric_cluster": p == q,
        "candidate_count": len(cands),
        "verification": ver,
    }


def build_row(n: int, cache: ScorerCache) -> dict:
    types = triple_types(n)
    scale = edo_scale(n)

    # --- grid counts (the joinable table for ET-002 / EAR-ε) --------------
    grid = {}
    for eps in EPS_GRID:
        r = cache.counts(n, eps)
        grid[f"{eps:g}"] = {
            "P": r.proportional,
            "S": r.subcontrary,
            "G": r.geometric,
            "P_raw": r.proportional_raw,
            "S_raw": r.subcontrary_raw,
            "G_raw": r.geometric_raw,
            "degenerate_dropped": r.degenerate_dropped,
        }

    # --- R-G0 rail ---------------------------------------------------------
    r0 = cache.counts(n, EPS_G0)
    rail_g0 = {
        "eps": EPS_G0,
        "P": r0.proportional,
        "S": r0.subcontrary,
        "G": r0.geometric,
        "expected_g": n * (n // 2),
        "ok": (
            r0.proportional == 0
            and r0.subcontrary == 0
            and r0.geometric == n * (n // 2)
        ),
    }

    # --- locks -------------------------------------------------------------
    lock_p = _lock_block(cache, n, types, "P")
    lock_s = _lock_block(cache, n, types, "S")

    # asymmetric-only P lock (excludes the 1/N^2 symmetric cluster family);
    # verified by count jump when it differs from the raw lock.
    asym = lock_candidates(types, "P", asymmetric_only=True)
    asym_block: Optional[dict] = None
    if asym:
        a_dev, a_p, a_q = asym[0]
        a_block = {
            "eps_star": a_dev,
            "witness_pq": [a_p, a_q],
            "witness_span_steps": a_p + a_q,
            "is_power_chord": a_p + a_q == n,
            "same_as_raw_lock": abs(a_dev - lock_p["eps_star"]) <= TIE_TOL,
        }
        if not a_block["same_as_raw_lock"]:
            a_block["verification"] = verify_jump(
                cache, n, types, "P", a_dev, expect_below_zero=False
            )
        asym_block = a_block

    # --- patent landmarks (cultural-epsilon column) ------------------------
    fifth_steps, fifth_err = patent_fifth(n)
    mp, mq = patent_major_pq(n)
    major: Optional[dict] = None
    if 1 <= mp <= n - 1 and 1 <= mq <= n - 1 and mp + mq <= n:
        t = mirror_type(n, mp, mq)
        major = {
            "pq": [mp, mq],
            "dev_cents": t.dev_p,
            "qualifies": t.dev_p < t.sep,
            "minor_dual_dev_cents": mirror_type(n, mq, mp).dev_s,
        }
        if major["qualifies"]:
            major["verification"] = verify_jump(
                cache, n, types, "P", t.dev_p, expect_below_zero=False
            )

    # --- duality rail over everything measured for this N ------------------
    duality_diffs = [
        abs(cache.counts(n, e).proportional - cache.counts(n, e).subcontrary)
        for e in list(EPS_GRID) + [EPS_G0]
    ]

    return {
        "experiment": "ET-001",
        "n": n,
        "step_cents": 1200.0 / n,
        "scale_size": len(scale),
        "triple_type_count": len(types),
        "melodic": melodic_row(n),
        "patent": {
            "fifth_steps": fifth_steps,
            "fifth_error_cents": fifth_err,
            "major": major,
        },
        "locks": {"P": lock_p, "S": lock_s, "P_asymmetric": asym_block},
        "rail_g0": rail_g0,
        "grid": grid,
        "duality_max_abs_diff": max(duality_diffs),
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "et001_version": ET001_VERSION,
    }


# ---------------------------------------------------------------------------
# verdicts (pre-registered criteria, LOG.md 2026-08-09)
# ---------------------------------------------------------------------------


def _verdict_he1(rows: dict[int, dict]) -> dict:
    r12 = rows[12]
    major = r12["patent"]["major"]
    ver = major.get("verification", {})
    analytic = major["dev_cents"]
    ok = (
        major["pq"] == [4, 3]
        and abs(analytic - 14.859022) < 5e-4
        and round(analytic, 2) == 14.86
        and ver.get("verified", False)
        and ver.get("count_below") == 36
        and ver.get("count_above") == 48
        and abs(major["minor_dual_dev_cents"] - analytic) <= TIE_TOL
    )
    return {
        "hypothesis": "H-E1 cultural epsilon: 12-EDO full major+minor at "
                      "~14.86c (predicted 14.8590)",
        "measured_eps": analytic,
        "measured_eps_2dp": round(analytic, 2),
        "p_jump": [ver.get("count_below"), ver.get("count_above")],
        "verdict": "KEPT" if ok else "REFUTED",
    }


def _verdict_he2(rows: dict[int, dict]) -> dict:
    lp = rows[12]["locks"]["P"]
    ok = (
        lp["is_power_chord"]
        and lp["witness_pq"] == [7, 5]
        and abs(lp["eps_star"] - 1.955001) < 5e-4
        and lp["verification"]["verified"]
        and lp["verification"]["count_below"] == 0
        and lp["verification"]["count_above"] == 12
    )
    return {
        "hypothesis": "H-E2 power chords: scorer counts 2:3:4 (span-1200 "
                      "inclusive); 12-EDO first P lock = fifth error 1.9550c",
        "structurally_counted": True,
        "measured_eps": lp["eps_star"],
        "witness": lp["witness_pq"],
        "verdict": "KEPT" if ok else "REFUTED",
    }


def _verdict_he3(rows: dict[int, dict]) -> dict:
    ranking = sorted(
        (r["locks"]["P"]["eps_star"], n) for n, r in rows.items()
    )
    top5 = tuple(n for _, n in ranking[:5])
    naive_refuted = top5 != NAIVE_TOP5
    champions_near_top = 53 in top5 and 41 in top5
    mirror_top5_confirmed = top5 == (50, 41, 49, 39, 53)
    return {
        "hypothesis": "H-E3 ranking: naive fifth-error top5 "
                      f"{list(NAIVE_TOP5)} predicted REFUTED; mirror top5 "
                      "[50, 41, 49, 39, 53] predicted",
        "measured_top5": list(top5),
        "naive_top5_refuted": naive_refuted,
        "mirror_top5_confirmed": mirror_top5_confirmed,
        "champions_53_41_in_top5": champions_near_top,
        "verdict": (
            "REFUTED (naive), mirror KEPT"
            if naive_refuted and mirror_top5_confirmed
            else "see fields"
        ),
    }


def _verdict_he4(rows: dict[int, dict]) -> dict:
    bad = [
        n
        for n, r in rows.items()
        if not (
            r["melodic"]["propriety"] == "strictly_proper"
            and r["melodic"]["gap_class_count"] == 1
            and r["melodic"]["entropy_bits"] == 0.0
            and r["melodic"]["is_cs"]
        )
    ]
    return {
        "hypothesis": "H-E4 melodic rails: every N-EDO strictly proper, CS, "
                      "1 gap class, 0 bits",
        "failing_n": bad,
        "verdict": "KEPT" if not bad else "REFUTED",
    }


def _verdict_rails(rows: dict[int, dict]) -> dict:
    dual_bad = [n for n, r in rows.items() if r["duality_max_abs_diff"] != 0]
    g0_bad = [n for n, r in rows.items() if not r["rail_g0"]["ok"]]
    grid12 = [rows[12]["grid"][f"{e:g}"]["P"] for e in EPS_GRID]
    grid12_ok = grid12 == [0, 12, 24, 24, 24, 48, 48]
    locks_bad = [
        n
        for n, r in rows.items()
        if not (
            r["locks"]["P"]["verification"]["verified"]
            and r["locks"]["S"]["verification"]["verified"]
        )
    ]
    return {
        "R_DUAL": {"failing_n": dual_bad,
                   "verdict": "KEPT" if not dual_bad else "REFUTED"},
        "R_G0": {"failing_n": g0_bad,
                 "verdict": "KEPT" if not g0_bad else "REFUTED"},
        "GRID12_PIN": {"measured_P": grid12,
                       "verdict": "KEPT" if grid12_ok else "REFUTED"},
        "ALL_LOCKS_VERIFIED": {"failing_n": locks_bad,
                               "verdict": "KEPT" if not locks_bad else
                               "REFUTED"},
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def run(results_dir: Path = RESULTS_DIR) -> dict:
    cache = ScorerCache()
    rows = {n: build_row(n, cache) for n in range(N_MIN, N_MAX + 1)}

    ranking = sorted(
        (r["locks"]["P"]["eps_star"], n,
         r["locks"]["P"]["witness_pq"],
         r["locks"]["P"]["is_power_chord"],
         r["locks"]["P"]["is_symmetric_cluster"])
        for n, r in rows.items()
    )
    summary = {
        "experiment": "ET-001",
        "preregistration": "experiments/lattice/LOG.md 2026-08-09",
        "corpus": {
            "family": "full N-EDO scales",
            "n_range": [N_MIN, N_MAX],
            "rows": len(rows),
        },
        "constants": {
            "eps_grid": list(EPS_GRID),
            "eps_g0": EPS_G0,
            "verify_delta": VERIFY_DELTA,
            "tie_tol": TIE_TOL,
            "max_span_cents": DEFAULT_MAX_SPAN_CENTS,
            "naive_top5": list(NAIVE_TOP5),
        },
        "epsilon_semantics": (
            "score_tempered eps is a per-mean-condition deviation in cents "
            "(strict <) with the degeneracy guard sep(a,c) >= eps; a triple "
            "counts on the half-open interval (dev, sep]. NOT the plugin's "
            "register-dependent linear-frequency 0.0005."
        ),
        "verdicts": {
            "H-E1": _verdict_he1(rows),
            "H-E2": _verdict_he2(rows),
            "H-E3": _verdict_he3(rows),
            "H-E4": _verdict_he4(rows),
            **_verdict_rails(rows),
        },
        "first_lock_ranking_top10": [
            {"rank": i + 1, "n": n, "eps_star": e, "witness_pq": pq,
             "is_power_chord": pc, "is_symmetric_cluster": sym}
            for i, (e, n, pq, pc, sym) in enumerate(ranking[:10])
        ],
        "first_lock_ranking_full": [
            {"n": n, "eps_star": e} for e, n, _, _, _ in ranking
        ],
        "culture_set_major_eps": {
            str(n): rows[n]["patent"]["major"]["dev_cents"]
            for n in CULTURE_SET
            if rows[n]["patent"]["major"] is not None
        },
        "scorer_calls": cache.calls,
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "et001_version": ET001_VERSION,
        "python": "3.12",
    }

    results_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = results_dir / "et001.jsonl"
    with jsonl_path.open("w") as f:
        for n in sorted(rows):
            f.write(json.dumps(rows[n], sort_keys=True) + "\n")
    summary_path = results_dir / "et001_summary.json"
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2)
                            + "\n")
    return summary


def main() -> None:
    summary = run()
    v = summary["verdicts"]
    print(f"ET-001 complete: {summary['corpus']['rows']} rows, "
          f"{summary['scorer_calls']} scorer calls")
    for key in ("H-E1", "H-E2", "H-E3", "H-E4",
                "R_DUAL", "R_G0", "GRID12_PIN", "ALL_LOCKS_VERIFIED"):
        print(f"  {key}: {v[key]['verdict']}")
    top = summary["first_lock_ranking_top10"]
    print("  top5 first-lock: "
          + ", ".join(f"N={t['n']} @ {t['eps_star']:.6f}c" for t in top[:5]))
    print(f"  cultural epsilon (12-EDO major): "
          f"{v['H-E1']['measured_eps']:.6f}c")


if __name__ == "__main__":
    main()
