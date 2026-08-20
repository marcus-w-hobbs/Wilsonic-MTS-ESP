"""ET-003 — the comma-kernel history of 12-EDO under the frozen scorers
(LOG.md pre-registration 2026-08-19; committed before this file).

The 11-limit patent val V12 = <12,19,28,34,42> has a kernel; European
practice walked INTO that kernel one comma at a time. Four fixed stages
share the SAME val/addressing (12 degrees, fifth = 7 steps) and differ only
in the lift (tuning map):

  S1  Pythagorean 12        chain of pure fifths, positions -5..+6
  S2  1/4-comma meantone 12 fifth = 300*log2(5), chain -5..+6
  S3  Werckmeister III      C-G, G-D, D-A, B-F# narrowed by PC/4, rest pure
                            (Werckmeister, Musicalische Temperatur, 1691;
                            cents table matches Barbour 1951)
  S4  12-EDO                k*100 cents

Measured per stage: frozen triad scorer (v1.1.0, score_tempered, PRIMARY
anchored convention, default max_span 1200c) at the ET-001 epsilon grid;
frozen melodic scorers (v0.1.0); full P/S lock spectra <= 20c, each
distinct lock value verified against the frozen scorer at +-delta;
major/minor address censuses (best-voicing deviations); plus the V12
kernel census at the 5-, 7- and 11-limits (comma enumeration adapted from
bridge001.py, copy-with-attribution, generalized to per-limit prime lists).

Analytic MIRROR (never a substitute for the scorer): an independent
reimplementation of the anchored classification math (ET-001 method,
extended off-EDO) enumerating all anchored triples of each 12-tone scale;
a triple counts at eps exactly on the half-open interval (dev, sep].
Mirror-vs-scorer disagreement anywhere is recorded as a verification
failure, never patched over.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)

Receipts: results/et003.jsonl (7 rows: 3 kernel-census rows + 4 stage
rows) + results/et003_summary.json. Deterministic: stdlib only, no
randomness, no wall-clock fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 et003.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import product
from math import gcd, log2
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scorer import (  # noqa: E402  (frozen v1.1.0, read-only)
    DEFAULT_MAX_SPAN_CENTS,
    SCORER_VERSION,
    score_tempered,
)
from melodic import (  # noqa: E402  (frozen v0.1.0, read-only)
    MELODIC_VERSION,
    score_melodic,
)

ET003_VERSION = "1.0.0"

# --- constants, locked in the LOG.md pre-registration (2026-08-19) ---------
EPS_GRID = (1.0, 2.0, 3.0, 5.0, 10.0, 14.86, 20.0)
DELTA = 1e-6          # lock verification: scorer queried at dev +- DELTA
TIE_TOL = 1e-9        # lock-value tie clustering
LOCK_LIMIT = 20.0     # spectra recorded and verified up to this deviation
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "et003.jsonl"
SUMMARY = RESULTS_DIR / "et003_summary.json"

PURE_FIFTH = 1200.0 * log2(1.5)                    # 701.955001 c
PYTH_COMMA = 1200.0 * (12.0 * log2(1.5) - 7.0)     # 23.460010 c
MEANTONE_FIFTH = 300.0 * log2(5.0)                 # 696.578428 c
WERCK_TEMPERED = PURE_FIFTH - PYTH_COMMA / 4.0     # 696.089998 c
# Werckmeister III circle-of-fifths word from C (T = tempered by PC/4):
# C-G, G-D, D-A tempered; A-E, E-B pure; B-F# tempered; the rest pure.
WERCK_WORD = "TTTPPTPPPPPP"

# --- V12 kernel census (H-K1) -----------------------------------------------
# Enumeration adapted from bridge001.py::enumerate_commas (2026-07-29),
# generalized to a per-limit prime list and the ET-003 box: |e3| <= 12
# (widened from BRIDGE's 8 solely to admit the Pythagorean comma),
# |e5| <= 5, |e7| <= 4, |e11| <= 3, 0 < cents < 60, primitive,
# Tenney height n*d <= 2^40.
PRIMES = (2, 3, 5, 7, 11)
LOG2P = tuple(log2(p) for p in PRIMES)
ODD_BOX_11 = (12, 5, 4, 3)
COMMA_MAX_CENTS = 60.0
TENNEY_MAX_LOG2 = 40.0
V12 = (12, 19, 28, 34, 42)


def cents_of(monzo: tuple[int, ...]) -> float:
    return 1200.0 * sum(e * l for e, l in zip(monzo, LOG2P))


def ratio_of(monzo: tuple[int, ...]) -> Fraction:
    fr = Fraction(1)
    for e, p in zip(monzo, PRIMES):
        fr *= Fraction(p) ** e
    return fr


def tenney_log2(monzo: tuple[int, ...]) -> float:
    return sum(abs(e) * l for e, l in zip(monzo, LOG2P))


def vdot(val: tuple[int, ...], monzo: tuple[int, ...]) -> int:
    return sum(a * b for a, b in zip(val, monzo))


def enumerate_kernel(n_odd_primes: int) -> list[dict]:
    """V12 kernel members within the ET-003 box at the given prime limit
    (n_odd_primes = 2 -> 5-limit, 3 -> 7-limit, 4 -> 11-limit)."""
    box = ODD_BOX_11[:n_odd_primes]
    val = V12[: n_odd_primes + 1]
    out = {}
    for odd in product(*[range(-b, b + 1) for b in box]):
        if all(e == 0 for e in odd):
            continue
        odd_cents = 1200.0 * sum(e * LOG2P[i + 1] for i, e in enumerate(odd))
        e2 = -round(odd_cents / 1200.0)
        m = (e2,) + tuple(odd)
        c = cents_of(m + (0,) * (5 - len(m)))
        if c < 0:
            m = tuple(-x for x in m)
            c = -c
        if not (0.0 < c < COMMA_MAX_CENTS):
            continue
        g = 0
        for x in m:
            g = gcd(g, abs(x))
        if g != 1:
            continue
        padded = m + (0,) * (5 - len(m))
        if tenney_log2(padded) > TENNEY_MAX_LOG2:
            continue
        if vdot(val, m) != 0:
            continue
        fr = ratio_of(padded)
        out[m] = {
            "ratio": f"{fr.numerator}/{fr.denominator}",
            "monzo": list(m),
            "cents": round(c, 6),
            "tenney_height_log2": round(tenney_log2(padded), 6),
        }
    return sorted(
        out.values(),
        key=lambda d: (d["tenney_height_log2"], tuple(d["monzo"])),
    )


# --- stage construction ------------------------------------------------------


def chain_scale(fifth: float, lo: int = -5, hi: int = 6) -> tuple[float, ...]:
    """Octave-reduced chain of one fifth size, chain positions lo..hi."""
    return tuple(sorted((k * fifth) % 1200.0 for k in range(lo, hi + 1)))


def werck3_scale() -> tuple[float, ...]:
    """Werckmeister III degrees from the circle-of-fifths word."""
    sizes = {"T": WERCK_TEMPERED, "P": PURE_FIFTH}
    degs = [0.0]
    cur = 0.0
    for ch in WERCK_WORD[:-1]:
        cur = (cur + sizes[ch]) % 1200.0
        degs.append(cur)
    return tuple(sorted(degs))


STAGES: tuple[tuple[str, str], ...] = (
    ("S1_pythagorean", "chain of pure fifths 701.955001c, positions -5..+6"),
    ("S2_meantone", "chain of 1/4-comma fifths 696.578428c, positions -5..+6"),
    ("S3_werckmeister3", "Werckmeister III (1691): word TTTPPTPPPPPP from C"),
    ("S4_12edo", "12-EDO, degrees k*100c"),
)


def stage_scale(stage: str) -> tuple[float, ...]:
    if stage == "S1_pythagorean":
        return chain_scale(PURE_FIFTH)
    if stage == "S2_meantone":
        return chain_scale(MEANTONE_FIFTH)
    if stage == "S3_werckmeister3":
        return werck3_scale()
    if stage == "S4_12edo":
        return tuple(k * 100.0 for k in range(12))
    raise ValueError(f"unknown stage {stage}")


# --- analytic mirror (independent algebra; the scorer is the referee) -------


def _rep_below(pc: float, b: float) -> float | None:
    off = (pc - b) % 1200.0
    return None if off == 0.0 else b - 1200.0 + off


def _rep_above(pc: float, b: float) -> float | None:
    off = (pc - b) % 1200.0
    return None if off == 0.0 else b + off


def anchored_triples(scale: tuple[float, ...]):
    """All anchored triples (a, b, c) with span <= 1200c, mirroring the
    frozen score_cents_anchored sampling."""
    for b in scale:
        lows = [r for pc in scale if (r := _rep_below(pc, b)) is not None]
        highs = [r for pc in scale if (r := _rep_above(pc, b)) is not None]
        for a in lows:
            for c in highs:
                if c - a > DEFAULT_MAX_SPAN_CENTS:
                    continue
                yield a, b, c


def triple_devs(a: float, b: float, c: float) -> tuple[float, float, float, float]:
    """(dev_P, dev_S, dev_G, sep) of an anchored triple, mirroring the frozen
    classify_cents_triple / mean_separation_cents math."""
    fa = 2.0 ** (a / 1200.0)
    fb = 2.0 ** (b / 1200.0)
    fc = 2.0 ** (c / 1200.0)
    am = (fa + fc) / 2.0
    hm = 2.0 * fa * fc / (fa + fc)
    dev_p = abs(1200.0 * log2(am / fb))
    dev_s = abs(1200.0 * log2(fb / hm))
    dev_g = abs(1200.0 * log2(fa * fc / (fb * fb)))
    sep = abs(1200.0 * log2(am / hm))
    return dev_p, dev_s, dev_g, sep


def mirror_counts(scale: tuple[float, ...], eps: float) -> tuple[int, int, int]:
    """Guarded (P, S, G) exactly as the frozen scorer counts them: a triple
    counts iff dev < eps (strict) AND sep >= eps."""
    p = s = g = 0
    for a, b, c in anchored_triples(scale):
        dev_p, dev_s, dev_g, sep = triple_devs(a, b, c)
        if sep < eps:
            continue
        if dev_p < eps:
            p += 1
        if dev_s < eps:
            s += 1
        if dev_g < eps:
            g += 1
    return p, s, g


def lock_spectrum(scale: tuple[float, ...], kind: str) -> list[dict]:
    """Distinct P- or S-deviation values <= LOCK_LIMIT, tie-clustered at
    TIE_TOL, with counts, separations and interval patterns."""
    rows = []
    for a, b, c in anchored_triples(scale):
        dev_p, dev_s, _, sep = triple_devs(a, b, c)
        dev = dev_p if kind == "P" else dev_s
        if dev <= LOCK_LIMIT:
            rows.append((dev, sep, round(a - b, 4), round(c - b, 4)))
    rows.sort()
    clusters: list[dict] = []
    for dev, sep, lo, hi in rows:
        if clusters and dev - clusters[-1]["_anchor"] <= TIE_TOL:
            cl = clusters[-1]
        else:
            cl = {"_anchor": dev, "dev": None, "count": 0,
                  "sep_min": sep, "sep_max": sep, "patterns": {}}
            clusters.append(cl)
        cl["count"] += 1
        cl["sep_min"] = min(cl["sep_min"], sep)
        cl["sep_max"] = max(cl["sep_max"], sep)
        key = f"({lo},{hi})"
        cl["patterns"][key] = cl["patterns"].get(key, 0) + 1
    for cl in clusters:
        cl["dev"] = round(cl.pop("_anchor"), 6)
        cl["sep_min"] = round(cl["sep_min"], 6)
        cl["sep_max"] = round(cl["sep_max"], 6)
        cl["inert"] = cl["dev"] > cl["sep_max"]  # empty (dev, sep] interval
    return clusters


def verify_locks(scale: tuple[float, ...], spectra: dict[str, list[dict]]) -> dict:
    """For every distinct lock value d, compare frozen-scorer P and S at
    d +- DELTA against the mirror at the same epsilons. The scorer is the
    referee; any mismatch is recorded, never patched."""
    eps_points = set()
    for clusters in spectra.values():
        for cl in clusters:
            d = cl["dev"]
            if d > DELTA:
                eps_points.add(round(d - DELTA, 9))
            eps_points.add(round(d + DELTA, 9))
    checked = 0
    failures = []
    for eps in sorted(eps_points):
        res = score_tempered(scale, epsilon_cents=eps)
        mp, ms, mg = mirror_counts(scale, eps)
        checked += 1
        if (res.proportional, res.subcontrary, res.geometric) != (mp, ms, mg):
            failures.append({
                "eps": eps,
                "scorer": [res.proportional, res.subcontrary, res.geometric],
                "mirror": [mp, ms, mg],
            })
    return {"epsilon_points_checked": checked, "failures": failures}


# --- address censuses (H-K4/H-K5) -------------------------------------------


def address_table(scale: tuple[float, ...], third_steps: int,
                  fifth_steps: int, kind: str) -> list[dict]:
    """Per root address r: the triad {r, r+third_steps, r+fifth_steps} (in
    shared Z12 addressing) with the deviation of every anchored voicing of
    its 3 pitch classes; kind 'P' for major (proportional), 'S' for minor
    (subcontrary)."""
    n = len(scale)
    out = []
    for r in range(n):
        pcs = sorted({scale[r], scale[(r + third_steps) % n],
                      scale[(r + fifth_steps) % n]})
        voicings = []
        # triad voicings only: anchor b = one pc, a and c the unique octave
        # representatives of the OTHER TWO pcs (both assignments) -- the
        # 2-pc power-chord voicings (a, c from the same class) belong to the
        # full-scale spectra, not to the per-address triad census
        for b in pcs:
            others = [pc for pc in pcs if pc != b]
            if len(others) != 2:
                continue  # degenerate address (pc collision)
            for x, y in ((others[0], others[1]), (others[1], others[0])):
                a = _rep_below(x, b)
                c = _rep_above(y, b)
                if a is None or c is None or c - a > DEFAULT_MAX_SPAN_CENTS:
                    continue
                dev_p, dev_s, _, sep = triple_devs(a, b, c)
                dev = dev_p if kind == "P" else dev_s
                voicings.append({
                    "dev": round(dev, 6), "sep": round(sep, 6),
                    "a_rel": round(a - b, 4), "c_rel": round(c - b, 4),
                })
        voicings.sort(key=lambda v: (v["dev"], v["a_rel"]))
        # each pc-triple appears once per anchor scale-degree occurrence;
        # dedup identical (dev, a_rel, c_rel) rows, keeping a count
        dedup: list[dict] = []
        for v in voicings:
            if dedup and (dedup[-1]["dev"], dedup[-1]["a_rel"],
                          dedup[-1]["c_rel"]) == (v["dev"], v["a_rel"],
                                                  v["c_rel"]):
                dedup[-1]["multiplicity"] += 1
            else:
                v = dict(v)
                v["multiplicity"] = 1
                dedup.append(v)
        out.append({
            "root_index": r,
            "third_cents": round((scale[(r + third_steps) % n] - scale[r])
                                 % 1200.0, 6),
            "fifth_cents": round((scale[(r + fifth_steps) % n] - scale[r])
                                 % 1200.0, 6),
            "voicings": dedup,
        })
    return out


def coverage(table: list[dict], eps: float) -> int:
    """Addresses with at least one voicing counting at eps (dev < eps <= sep)."""
    return sum(
        1 for row in table
        if any(v["dev"] < eps <= v["sep"] for v in row["voicings"])
    )


# --- receipts ----------------------------------------------------------------


def melodic_receipt(scale: tuple[float, ...]) -> dict:
    m = score_melodic(scale)
    return {
        "propriety": m.propriety.classification,
        "propriety_violations": m.propriety.violating_span_pairs,
        "is_cs": m.constant_structure.is_cs,
        "cs_violations": m.constant_structure.violations,
        "gap_class_count": m.gap_entropy.gap_class_count,
        "gap_classes": [
            [round(lo, 6), round(hi, 6), count]
            for lo, hi, count in m.gap_entropy.gap_classes
        ],
        "entropy_bits": round(m.gap_entropy.entropy_bits, 6),
        "melodic_version": MELODIC_VERSION,
    }


def stage_row(stage: str, description: str) -> dict:
    scale = stage_scale(stage)
    grid = {"eps": list(EPS_GRID), "P": [], "S": [], "G": [],
            "P_raw": [], "S_raw": [], "G_raw": []}
    mirror_grid = {"P": [], "S": [], "G": []}
    for eps in EPS_GRID:
        res = score_tempered(scale, epsilon_cents=eps)
        grid["P"].append(res.proportional)
        grid["S"].append(res.subcontrary)
        grid["G"].append(res.geometric)
        grid["P_raw"].append(res.proportional_raw)
        grid["S_raw"].append(res.subcontrary_raw)
        grid["G_raw"].append(res.geometric_raw)
        mp, ms, mg = mirror_counts(scale, eps)
        mirror_grid["P"].append(mp)
        mirror_grid["S"].append(ms)
        mirror_grid["G"].append(mg)
    mirror_agrees_grid = (grid["P"] == mirror_grid["P"]
                          and grid["S"] == mirror_grid["S"]
                          and grid["G"] == mirror_grid["G"])
    spectra = {"P": lock_spectrum(scale, "P"), "S": lock_spectrum(scale, "S")}
    verification = verify_locks(scale, spectra)
    maj = address_table(scale, 4, 7, "P")
    mino = address_table(scale, 3, 7, "S")
    cov_eps = (2.0, 3.0, 5.0, 10.0, 14.86, 20.0)
    return {
        "row_type": "stage",
        "stage": stage,
        "description": description,
        "scale_cents": [round(c, 6) for c in scale],
        "grid": grid,
        "mirror_grid": mirror_grid,
        "mirror_agrees_grid": mirror_agrees_grid,
        "lock_spectrum_P": [
            {k: v for k, v in cl.items()} for cl in spectra["P"]],
        "lock_spectrum_S": [
            {k: v for k, v in cl.items()} for cl in spectra["S"]],
        "lock_verification": verification,
        "melodic": melodic_receipt(scale),
        "major_addresses": maj,
        "minor_addresses": mino,
        "coverage_major": {str(e): coverage(maj, e) for e in cov_eps},
        "coverage_minor": {str(e): coverage(mino, e) for e in cov_eps},
        "scorer_version": SCORER_VERSION,
        "et003_version": ET003_VERSION,
    }


# --- pre-registered predictions (transcribed from LOG.md 2026-08-19) --------

PRED_GRID = {
    "S1_pythagorean": {"P": [11, 19, 21, 19, 20, 37, 46],
                       "S": [11, 19, 21, 19, 20, 37, 46],
                       "G": [30, 30, 30, 28, 28, 28, 28]},
    "S2_meantone": {"P": [2, 2, 10, 28, 39, 47, 48],
                    "S": [2, 2, 10, 28, 39, 47, 48],
                    "G": [30, 30, 30, 30, 28, 28, 28]},
    "S3_werckmeister3": {"P": [10, 10, 14, 18, 28, 40, 48],
                         "S": [9, 9, 14, 19, 28, 40, 46],
                         "G": [20, 20, 20, 20, 39, 55, 58]},
    "S4_12edo": {"P": [0, 12, 24, 24, 24, 48, 48],
                 "S": [0, 12, 24, 24, 24, 48, 48],
                 "G": [72, 72, 72, 72, 60, 60, 60]},
}

PRED_MELODIC = {
    "S1_pythagorean": ("strictly_proper", True, 2, 0.979869),
    "S2_meantone": ("strictly_proper", True, 2, 0.979869),
    "S3_werckmeister3": ("strictly_proper", True, 4, 1.918296),
    "S4_12edo": ("strictly_proper", True, 1, 0.0),
}

PRED_COVERAGE_MAJOR = {
    "S1_pythagorean": {"2.0": 3, "3.0": 3, "5.0": 3, "10.0": 4,
                       "14.86": 12, "20.0": 12},
    "S2_meantone": {"2.0": 0, "3.0": 8, "5.0": 8, "10.0": 8,
                    "14.86": 8, "20.0": 9},
    "S3_werckmeister3": {"2.0": 1, "3.0": 2, "5.0": 4, "10.0": 9,
                         "14.86": 12, "20.0": 12},
    "S4_12edo": {"2.0": 0, "3.0": 0, "5.0": 0, "10.0": 12,
                 "14.86": 12, "20.0": 12},
}

PRED_CENSUS_COUNTS = {"5": 5, "7": 29, "11": 122}
PRED_5LIMIT_MEMBERS = ["81/80", "128/125", "2048/2025", "32805/32768",
                       "531441/524288"]

# first-lock (dev rounded 4dp, count) heads per stage, P side
PRED_FIRST_LOCKS_P = {
    "S1_pythagorean": (0.0, 11),
    "S2_meantone": (0.7394, 2),
    "S3_werckmeister3": (0.0, 8),
    "S4_12edo": (1.955, 12),
}

# W-III per-root best-voicing major dev multiset (rounded 4dp)
PRED_WERCK_KEY_COLOR = sorted([0.2516, 2.4456, 3.9273, 3.9273, 6.1166,
                               7.6077, 9.7924, 9.7924, 9.7924, 13.4727,
                               13.4727, 13.4727])


def verdicts(stage_rows: dict[str, dict], census_rows: dict[str, dict]) -> dict:
    """Per-hypothesis machine verdicts against the pre-registered numbers."""
    v: dict = {}
    # H-K1
    counts_ok = all(
        census_rows[lim]["count"] == PRED_CENSUS_COUNTS[lim]
        for lim in ("5", "7", "11"))
    members5 = [m["ratio"] for m in census_rows["5"]["members"]]
    v["H-K1"] = {
        "counts_predicted": PRED_CENSUS_COUNTS,
        "counts_measured": {lim: census_rows[lim]["count"]
                            for lim in ("5", "7", "11")},
        "five_limit_members_predicted": sorted(PRED_5LIMIT_MEMBERS),
        "five_limit_members_measured": sorted(members5),
        "kept": counts_ok and sorted(members5) == sorted(PRED_5LIMIT_MEMBERS),
    }
    # H-K2
    grid_ok = {}
    for stage in PRED_GRID:
        g = stage_rows[stage]["grid"]
        grid_ok[stage] = (g["P"] == PRED_GRID[stage]["P"]
                          and g["S"] == PRED_GRID[stage]["S"]
                          and g["G"] == PRED_GRID[stage]["G"])
    first_ok = {}
    for stage, (dev, count) in PRED_FIRST_LOCKS_P.items():
        head = stage_rows[stage]["lock_spectrum_P"][0]
        first_ok[stage] = (round(head["dev"], 4) == dev
                           and head["count"] == count)
    verif_ok = all(not stage_rows[s]["lock_verification"]["failures"]
                   for s in PRED_GRID)
    mirror_ok = all(stage_rows[s]["mirror_agrees_grid"] for s in PRED_GRID)
    v["H-K2"] = {
        "grid_matches_prediction": grid_ok,
        "first_locks_match": first_ok,
        "lock_verification_clean": verif_ok,
        "mirror_agrees_grid": mirror_ok,
        "kept": (all(grid_ok.values()) and all(first_ok.values())
                 and verif_ok and mirror_ok),
    }
    # H-K3
    mel_ok = {}
    for stage, (prop, cs, gc, ent) in PRED_MELODIC.items():
        m = stage_rows[stage]["melodic"]
        mel_ok[stage] = (m["propriety"] == prop and m["is_cs"] == cs
                         and m["gap_class_count"] == gc
                         and abs(m["entropy_bits"] - ent) < 5e-7)
    gc_walk = [stage_rows[s]["melodic"]["gap_class_count"]
               for s, _ in STAGES]
    v["H-K3"] = {
        "per_stage_matches": mel_ok,
        "gap_class_walk": gc_walk,
        "monotone_uniformity": all(
            gc_walk[i] >= gc_walk[i + 1] for i in range(len(gc_walk) - 1)),
        "kept": all(mel_ok.values()),
        "note": "prediction: monotone_uniformity False (the walk is a hump"
                " peaking at Werckmeister III), with every stage strictly"
                " proper and CS",
    }
    # H-K4
    cov_ok = {}
    for stage in PRED_COVERAGE_MAJOR:
        cov_ok[stage] = (
            stage_rows[stage]["coverage_major"] == PRED_COVERAGE_MAJOR[stage])
    minor_eq = all(stage_rows[s]["coverage_minor"]
                   == stage_rows[s]["coverage_major"] for s in PRED_GRID)
    v["H-K4"] = {
        "coverage_major_matches": cov_ok,
        "minor_equals_major": minor_eq,
        "meantone_never_full_below_20": max(
            stage_rows["S2_meantone"]["coverage_major"][k]
            for k in ("2.0", "3.0", "5.0", "10.0", "14.86")) == 8,
        "kept": all(cov_ok.values()) and minor_eq,
        "note": "81/80 alone buys 8 of 12 major addresses (predicted NO to"
                " 'all'); 128/125 buys the 4 wrapped addresses + the 12th"
                " power chord; comma dev identities pinned in tests",
    }
    # H-K5
    werck_devs = sorted(
        round(min(vv["dev"] for vv in row["voicings"]), 4)
        for row in stage_rows["S3_werckmeister3"]["major_addresses"])
    chirality = [
        (p, s) for p, s in zip(stage_rows["S3_werckmeister3"]["grid"]["P"],
                               stage_rows["S3_werckmeister3"]["grid"]["S"])]
    v["H-K5"] = {
        "werck_key_color_predicted": PRED_WERCK_KEY_COLOR,
        "werck_key_color_measured": werck_devs,
        "werck_P_neq_S_at": [EPS_GRID[i] for i, (p, s) in enumerate(chirality)
                             if p != s],
        "kept": werck_devs == PRED_WERCK_KEY_COLOR,
        "note": "chirality prediction: P != S exactly at eps 1, 2, 5, 20",
    }
    return v


def main() -> None:
    census_rows = {}
    rows = []
    for limit, n_odd in (("5", 2), ("7", 3), ("11", 4)):
        members = enumerate_kernel(n_odd)
        row = {
            "row_type": "kernel_census",
            "limit": limit,
            "val": list(V12[: n_odd + 1]),
            "box": {"e3": 12, "e5": 5, "e7": 4, "e11": 3},
            "count": len(members),
            "members": members,
            "et003_version": ET003_VERSION,
        }
        census_rows[limit] = row
        rows.append(row)
    stage_rows = {}
    for stage, description in STAGES:
        row = stage_row(stage, description)
        stage_rows[stage] = row
        rows.append(row)
    summary = {
        "experiment": "ET-003",
        "et003_version": ET003_VERSION,
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "eps_grid": list(EPS_GRID),
        "stages": [s for s, _ in STAGES],
        "constants": {
            "pure_fifth_cents": round(PURE_FIFTH, 6),
            "pythagorean_comma_cents": round(PYTH_COMMA, 6),
            "meantone_fifth_cents": round(MEANTONE_FIFTH, 6),
            "werckmeister_tempered_fifth_cents": round(WERCK_TEMPERED, 6),
            "werckmeister_word": WERCK_WORD,
            "delta": DELTA,
            "tie_tol": TIE_TOL,
        },
        "grid_tables": {s: stage_rows[s]["grid"] for s, _ in STAGES},
        "coverage_major": {s: stage_rows[s]["coverage_major"]
                           for s, _ in STAGES},
        "coverage_minor": {s: stage_rows[s]["coverage_minor"]
                           for s, _ in STAGES},
        "melodic": {s: stage_rows[s]["melodic"] for s, _ in STAGES},
        "kernel_census_counts": {lim: census_rows[lim]["count"]
                                 for lim in ("5", "7", "11")},
        "verdicts": verdicts(stage_rows, census_rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(f"wrote {RESULTS} ({len(rows)} rows) and {SUMMARY}")
    for h, vv in summary["verdicts"].items():
        print(f"  {h}: kept={vv['kept']}")


if __name__ == "__main__":
    main()
