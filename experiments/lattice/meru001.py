"""MERU-001 — CPS seeds bent toward a generator (LOG.md pre-registration
2026-10-10; committed before this file).

Program A (Marcus, 2026-10-08): seed a generator's two-term recurrence
H[n] = a*H[n-i] + b*H[n-j] with the tones of the hexany CPS(4,2){1,3,5,7}
and watch pure harmony bend into pure melody; compare sixteen generators
(Erv's presets from meruthree.pdf plus the playground's direction-2 pick)
on identical seeds. Two seedings: LIFT (all six tones; order lifted by
(x^k - rho^k), k = 6 - j, rho = 1 — the playground's state) and EXACT (the
first j tones, unlifted, so every term satisfies the recurrence exactly).

The registered law: for power-of-two coefficients, H[n]/2 is the arithmetic
mean of a*H[n-i] and b*H[n-j], so (H[n-i], H[n], H[n-j]) is an exact
proportional triad whenever the two addends lie within an octave
(r = a*G^(j-i)/b in (1/2, 2)). Each W-window after the seeds then carries
at least W - j such triads (P-M1); the lift breaks exactness and the
tempered tier recovers it at a predictable step (P-M2); the melodic
crossover obeys Delta n = 2 / log2(G/|lambda2|) (P-M3); interval retention
is structural, absolute retention is rotation (P-M4); melody arrives
(P-M5). Predictions are pinned in PREDICTIONS below, verbatim from the LOG.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score, score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)
A MIRROR of the anchored exact classification (independent code, span
<= 2/1) is compared with the frozen exact result on every window; any
disagreement is recorded as a verification failure, never patched.

Receipts: results/meru001.jsonl (one row per recurrence x seeding x W x n)
+ results/meru001_summary.json; results/scl/meru001/*.scl ear-check
stimuli. Deterministic: stdlib only, exact Fractions for the sequence, no
randomness, no wall-clock fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 meru001.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import combinations
from math import cos, gcd, hypot, log, log2, pi, sin
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scorer import (  # noqa: E402  (frozen v1.1.0, read-only)
    SCORER_VERSION,
    score,
    score_tempered,
)
from melodic import (  # noqa: E402  (frozen v0.1.0, read-only)
    MELODIC_VERSION,
    score_melodic,
)
from families.cps import cps_scale  # noqa: E402

MERU001_VERSION = "1.0.0"
EXPERIMENT = "MERU-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "meru001.jsonl"
SUMMARY = RESULTS_DIR / "meru001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "meru001"

CENTS = 1200.0
STEPS = 130               # generated terms after the seeds
WINDOWS = (7, 12)
EPS_LOCK = 2.0            # the LOCK tier (G-026: the only reporting tier)
EPS_CHAIN = (2.0, 0.5)    # chain-error thresholds for the crossover law
EPS_RETAIN = 2.0
GAP_EPS_LOGGED = 2.0      # M1 also scored at this gap epsilon (logged)
SEED_FACTORS = (1, 3, 5, 7)
N_SEED_TONES = 6
CROSSOVER_TOL = 3         # |Delta n - predicted| <= this (P-M3)

#: (id, a, i, b, j, label). Order fixed; the receipt lists it.
RECURRENCES: tuple[tuple[str, int, int, int, int, str], ...] = (
    ("erv418935", 1, 1, 32, 4, "Erv 0.418935: H[n-1] + 32H[n-4] (2L^4 = L^3 + 4)"),
    ("erv238186", 1, 1, 2, 3, "Erv 0.238186 (complement): H[n-1] + 2H[n-3]"),
    ("fig12_12", 1, 1, 1, 7, "Fig 12 #12: H[n-1] + H[n-7]"),
    ("erv415227", 4, 8, 8, 9, "Erv 0.415227: 4H[n-8] + 8H[n-9]"),
    ("metameantone", 2, 3, 2, 4, "meta-meantone: 2H[n-3] + 2H[n-4]"),
    ("silver414", 8, 9, 7, 10, "nearest to sqrt2 - 1: 8H[n-9] + 7H[n-10] (control)"),
    ("fib", 1, 1, 1, 2, "Fibonacci: H[n-1] + H[n-2]"),
    ("metapelog", 1, 1, 1, 3, "meta-pelog: H[n-1] + H[n-3]"),
    ("metaslendro", 1, 2, 1, 3, "meta-slendro: H[n-2] + H[n-3]"),
    ("metaptolemy", 1, 3, 1, 4, "meta-Ptolemy: H[n-3] + H[n-4]"),
    ("erv59178", 16, 8, 16, 9, "Erv 0.591780: 16H[n-8] + 16H[n-9]"),
    ("llsls", 1, 2, 2, 3, "LLSLS: H[n-2] + 2H[n-3]"),
    ("metaslendro2", 1, 1, 4, 4, "meta-slendro 2: H[n-1] + 4H[n-4]"),
    ("erv773743", 2, 3, 128, 10, "Erv 0.773743: 2H[n-3] + 128H[n-10]"),
    ("pell", 2, 1, 1, 2, "Pell: 2H[n-1] + H[n-2]"),
    ("fit351", 1, 1, 128, 6, "playground direction-2 pick: H[n-1] + 128H[n-6]"),
)
SLOW = ("erv415227", "silver414", "erv59178", "erv773743")
OUT_OF_OCTAVE = ("fig12_12", "metapelog", "pell")

#: Registered predictions, verbatim from LOG.md 2026-10-10 (mirror numbers).
PREDICTIONS = {
    "P-M1_stationary_P": {  # EXACT seeding, last window, W=7 / W=12
        "erv418935": (3, 8), "erv238186": (4, 9), "metameantone": (3, 8),
        "fib": (5, 10), "metaslendro": (4, 9), "metaptolemy": (3, 8),
        "llsls": (4, 9), "metaslendro2": (3, 8), "fit351": (1, 6),
        "erv415227": (0, 3), "erv59178": (0, 3), "erv773743": (0, 2),
        "fig12_12": (0, 0), "metapelog": (0, 0), "pell": (0, 0),
        "silver414": (0, 0),
    },
    "P-M1_echo_windows": {  # EXACT seeding, windows with P > rt, W=7 / W=12
        "erv415227": (14, 28), "erv59178": (14, 23), "erv773743": (1, 2),
        "metameantone": (4, 6), "fib": (1, 1), "metaslendro": (1, 2),
        "metaptolemy": (2, 3), "metapelog": (0, 3),
    },
    "P-M2_n_lock": {  # LIFT seeding, W=7 / W=12
        "erv418935": (12, 17), "erv238186": (18, 23), "metameantone": (21, 26),
        "fib": (18, 23), "metaslendro": (26, 31), "metaptolemy": (36, 41),
        "llsls": (20, 25), "metaslendro2": (17, 22),
    },
    "P-M3_delta_n": {  # predicted 2/log2(G/lambda2) (mirror LIFT W=7 in LOG)
        "erv418935": 10.8, "erv238186": 3.1, "fig12_12": 7.8,
        "metameantone": 9.7, "fib": 2.9, "metapelog": 3.6, "metaslendro": 4.9,
        "metaptolemy": 10.0, "llsls": 4.9, "metaslendro2": 5.7, "pell": 1.6,
        "fit351": 24.0,
    },
    "P-M4_interval_retention": {  # stationary, W=7 / W=12
        "erv418935": (1, 6), "fib": (3, 8), "metaslendro2": (6, 11),
        "pell": (5, 15), "fit351": (5, 13), "erv773743": (2, 5),
        "erv415227": (0, 2), "silver414": (0, 2), "erv59178": (0, 2),
        "metapelog": (0, 2), "erv238186": (0, 0), "fig12_12": (0, 0),
        "metameantone": (0, 0), "metaslendro": (0, 0), "metaptolemy": (0, 0),
        "llsls": (0, 0),
    },
}


# ---------------------------------------------------------------------------
# pure math
# ---------------------------------------------------------------------------


def cents_of(x: Fraction | float) -> float:
    return CENTS * log2(float(x))


def wrap(c: float) -> float:
    return c % CENTS


def circ(a: float, b: float) -> float:
    d = abs(wrap(a) - wrap(b))
    return min(d, CENTS - d)


def reduce_octave(x: Fraction) -> Fraction:
    while x < 1:
        x *= 2
    while x >= 2:
        x /= 2
    return x


def is_power_of_two(n: int) -> bool:
    return n > 0 and n & (n - 1) == 0


def positive_root(j: int, i: int, a: int, b: int) -> float:
    """The unique positive root of x^j - a x^(j-i) - b (bisection)."""
    def f(x: float) -> float:
        return x ** j - a * x ** (j - i) - b
    lo, hi = 1e-9, 1.0
    while f(hi) < 0:
        hi *= 2
    for _ in range(300):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def root_moduli(coefs: list[float]) -> list[float]:
    """Moduli of the roots of the monic polynomial sum coefs[k] x^(n-k),
    coefs[0] = 1 (Durand-Kerner, deterministic start), sorted descending."""
    n = len(coefs) - 1
    re = [1.3 * cos(2 * pi * k / n + 0.4) for k in range(n)]
    im = [1.3 * sin(2 * pi * k / n + 0.4) for k in range(n)]

    def poly(x: float, y: float) -> tuple[float, float]:
        pr = pi_ = 0.0
        for c in coefs:
            pr, pi_ = pr * x - pi_ * y + c, pr * y + pi_ * x
        return pr, pi_

    for _ in range(800):
        for p in range(n):
            pr, pi_ = poly(re[p], im[p])
            dr, di = 1.0, 0.0
            for q in range(n):
                if q == p:
                    continue
                ar, ai = re[p] - re[q], im[p] - im[q]
                dr, di = dr * ar - di * ai, dr * ai + di * ar
            den = dr * dr + di * di or 1e-30
            re[p] -= (pr * dr + pi_ * di) / den
            im[p] -= (pi_ * dr - pr * di) / den
    return sorted((hypot(r, i) for r, i in zip(re, im)), reverse=True)


def build_recurrence(rid: str, a: int, i: int, b: int, j: int,
                     n_tones: int = N_SEED_TONES) -> dict:
    """Generator data plus the LIFT coefficient map (rho = 1)."""
    big_g = positive_root(j, i, a, b)
    base = [0.0] * (j + 1)
    base[0], base[i], base[j] = 1.0, -float(a), -float(b)
    lam2 = root_moduli(base)[1]
    k = max(0, n_tones - j)
    lift: dict[int, int] = {i: a, j: b}
    if k:
        lift[k] = lift.get(k, 0) + 1
        lift[i + k] = lift.get(i + k, 0) - a
        lift[j + k] = lift.get(j + k, 0) - b
    rate = max(lam2, 1.0 if k else 0.0) / big_g
    r = a * big_g ** (j - i) / b
    in_octave = 0.5 < r < 2.0
    pow2 = is_power_of_two(a) and is_power_of_two(b)
    return {
        "id": rid, "a": a, "i": i, "b": b, "j": j,
        "G": big_g, "log2G": log2(big_g), "gen01": log2(big_g) % 1.0,
        "cents": (log2(big_g) % 1.0) * CENTS, "lambda2": lam2,
        "rate": rate, "lift_k": k, "order_lift": j + k,
        "coefs_exact": {i: a, j: b}, "coefs_lift": lift,
        "r": r, "in_octave": in_octave, "pow2": pow2,
        "law_applies": in_octave and pow2,
        "pred_delta_n": (log(4.0) / log(1.0 / rate)) if rate < 1 else None,
    }


# ---------------------------------------------------------------------------
# seeds and sequences (exact)
# ---------------------------------------------------------------------------


def hexany_tones() -> tuple[Fraction, ...]:
    return cps_scale(SEED_FACTORS, 2)


def chain_align(base: Fraction, m: int, log2g: float) -> Fraction:
    """Octave copy of base nearest G^m in pitch."""
    e = round(m * log2g - log2(float(base)))
    return base * (Fraction(2) ** e if e >= 0 else Fraction(1, 2 ** (-e)))


def place_seeds(tones: tuple[Fraction, ...], order: int, log2g: float,
                mode: str) -> list[Fraction]:
    """LIFT: cycle all tones (octave copies) to fill `order` seeds.
    EXACT: the first `order` tones in pitch order (order <= len(tones))."""
    if mode == "EXACT" and order <= len(tones):
        return [chain_align(tones[m], m, log2g) for m in range(order)]
    return [chain_align(tones[m % len(tones)], m, log2g) for m in range(order)]


def run_recurrence(coefs: dict[int, int], seeds: list[Fraction],
                   steps: int) -> list[Fraction]:
    h = list(seeds)
    for n in range(len(seeds), len(seeds) + steps):
        h.append(sum((Fraction(c) * h[n - lag] for lag, c in coefs.items()),
                     Fraction(0)))
    return h


def seeding_plan(rec: dict, mode: str) -> tuple[dict[int, int], int]:
    """(coefficient map, number of seeds) for a seeding mode."""
    if mode == "LIFT":
        return rec["coefs_lift"], rec["order_lift"]
    if rec["j"] < N_SEED_TONES:
        return rec["coefs_exact"], rec["j"]
    return rec["coefs_lift"], rec["order_lift"]  # j >= 6: EXACT == LIFT


# ---------------------------------------------------------------------------
# mirror of the frozen anchored exact classification (independent code)
# ---------------------------------------------------------------------------


def _shift_open(x: Fraction, lo: Fraction, hi: Fraction) -> Fraction | None:
    r = x
    while r <= lo:
        r *= 2
    while r >= hi:
        r /= 2
    return r if lo < r < hi else None


def mirror_exact(values: list[Fraction]) -> tuple[int, int, int]:
    scale = sorted({reduce_octave(x) for x in values})
    p = s = g = 0
    for b in scale:
        lows = [r for pc in scale if (r := _shift_open(pc, b / 2, b)) is not None]
        highs = [r for pc in scale if (r := _shift_open(pc, b, 2 * b)) is not None]
        for a in lows:
            for c in highs:
                if c / a > 2:
                    continue
                if 2 * b == a + c:
                    p += 1
                elif b * (a + c) == 2 * a * c:
                    s += 1
                elif b * b == a * c:
                    g += 1
    return p, s, g


# ---------------------------------------------------------------------------
# descriptors
# ---------------------------------------------------------------------------


def chain_error(window: list[Fraction], log2g: float) -> float:
    last = cents_of(window[-1])
    return max(min(circ(cents_of(x), last - m * log2g * CENTS)
                   for m in range(len(window))) for x in window)


def step_class_count(cs: list[float], tol: float) -> int:
    pcs = sorted({round(wrap(c), 6) for c in cs})
    if len(pcs) < 2:
        return len(pcs)
    steps = sorted((pcs[k + 1] - pcs[k]) if k + 1 < len(pcs)
                   else pcs[0] + CENTS - pcs[k] for k in range(len(pcs)))
    classes: list[float] = []
    for st in steps:
        if not classes or st - classes[-1] > tol:
            classes.append(st)
    return len(classes)


def interval_classes(tones: tuple[Fraction, ...]) -> tuple[float, ...]:
    cs = [cents_of(t) for t in tones]
    return tuple(sorted({circ(a, b) for a, b in combinations(cs, 2)}))


def interval_retention(window: list[Fraction], classes: tuple[float, ...],
                       tol: float) -> int:
    cs = [cents_of(x) for x in window]
    return sum(1 for a, b in combinations(cs, 2)
               if min(abs(circ(a, b) - v) for v in classes) <= tol)


def absolute_retention(window: list[Fraction], tone_cents: list[float],
                       tol: float) -> int:
    return sum(1 for x in window
               if min(circ(cents_of(x), t) for t in tone_cents) <= tol)


def recurrence_triads(rec: dict, lo: int, hi: int) -> int:
    """Windows [lo, hi]: generated terms n with n - j >= lo (the law)."""
    if not rec["law_applies"]:
        return 0
    return max(0, hi - (lo + rec["j"]) + 1)


def lift_residual(h: list[Fraction], rec: dict, n: int) -> float:
    a, i, b, j = rec["a"], rec["i"], rec["b"], rec["j"]
    return abs(cents_of(h[n] / (a * h[n - i] + b * h[n - j])))


# ---------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------


def window_row(rec: dict, mode: str, w: int, n: int, h: list[Fraction],
               n_seeds: int, tone_cents: list[float],
               classes: tuple[float, ...]) -> dict:
    lo = n - w + 1
    window = h[lo:n + 1]
    cs = [cents_of(x) for x in window]
    exact = score(window)
    temp = score_tempered(cs, EPS_LOCK)
    mel = score_melodic(cs)
    mel2 = score_melodic(cs, gap_epsilon_cents=GAP_EPS_LOGGED)
    mp, ms, mg = mirror_exact(window)
    rt = recurrence_triads(rec, lo, n)
    rtdev = max((lift_residual(h, rec, m) for m in range(lo + rec["j"], n + 1)),
                default=0.0) if rt else 0.0
    return {
        "experiment": EXPERIMENT, "recurrence": rec["id"], "seeding": mode,
        "W": w, "n": n, "post_seed": n >= n_seeds + w - 1,
        "size": exact.sample_size,
        "P": exact.proportional, "S": exact.subcontrary, "G": exact.geometric,
        "mirror_P": mp, "mirror_S": ms, "mirror_G": mg,
        "mirror_ok": (mp, ms, mg) == (exact.proportional, exact.subcontrary,
                                      exact.geometric),
        "P_2c": temp.proportional, "S_2c": temp.subcontrary,
        "G_2c": temp.geometric, "dropped_2c": temp.degenerate_dropped,
        "rt": rt, "rt_residual_cents": rtdev,
        "ratio_dev_cents": cents_of(h[n] / h[n - 1]) - rec["log2G"] * CENTS,
        "chain_error_cents": chain_error(window, rec["log2G"]),
        "step_classes_2c": step_class_count(cs, 2.0),
        "interval_retention_2c": interval_retention(window, classes, EPS_RETAIN),
        "absolute_retention_2c": absolute_retention(window, tone_cents, EPS_RETAIN),
        "m1_gap_classes": mel.gap_entropy.gap_class_count,
        "m1_entropy_bits": mel.gap_entropy.entropy_bits,
        "m1_gap_classes_2c": mel2.gap_entropy.gap_class_count,
        "m2_cs_violations": mel.constant_structure.violations,
        "m3_propriety": mel.propriety.classification,
        "m3_violations": mel.propriety.violating_span_pairs,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_cents": EPS_LOCK,
    }


def pure_chain_propriety(gen01: float, w: int) -> str:
    cs = [wrap(k * gen01 * CENTS) for k in range(w)]
    return score_melodic(cs).propriety.classification


def run_series(rec: dict, mode: str, tones: tuple[Fraction, ...],
               tone_cents: list[float], classes: tuple[float, ...]) -> tuple[list[dict], dict]:
    coefs, n_seeds = seeding_plan(rec, mode)
    seeds = place_seeds(tones, n_seeds, rec["log2G"], mode)
    h = run_recurrence(coefs, seeds, STEPS)
    rows: list[dict] = []
    per_w: dict[str, dict] = {}
    for w in WINDOWS:
        wrows = [window_row(rec, mode, w, n, h, n_seeds, tone_cents, classes)
                 for n in range(w - 1, len(h))]
        rows.extend(wrows)
        post = [r for r in wrows if r["post_seed"]]
        last = wrows[-1]
        n_chain = {str(e): next((r["n"] for r in post if r["chain_error_cents"] <= e), None)
                   for e in EPS_CHAIN}
        n_lock = next((r["n"] for r in post if r["rt"] and r["rt_residual_cents"] <= EPS_LOCK),
                      None)
        per_w[str(w)] = {
            "n_seeds": n_seeds, "n_windows_post_seed": len(post),
            "stationary": {k: last[k] for k in (
                "n", "size", "P", "S", "G", "P_2c", "S_2c", "G_2c", "rt",
                "chain_error_cents", "interval_retention_2c",
                "m1_gap_classes", "m1_gap_classes_2c", "m3_propriety")},
            "pure_chain_propriety": pure_chain_propriety(rec["gen01"], w),
            "floor_violations": sum(1 for r in post if r["P"] < r["rt"]),
            "echo_windows": sum(1 for r in post if r["P"] > r["rt"]),
            "echo_window_ns": [r["n"] for r in post if r["P"] > r["rt"]][:12],
            "exact_P_nonzero_windows": sum(1 for r in post if r["P"] > 0),
            "n_lock": n_lock,
            "tempered_floor_violations_from_lock": (
                sum(1 for r in post if n_lock is not None and r["n"] >= n_lock
                    and r["P_2c"] < r["rt"])),
            "n_chain": n_chain,
            "delta_n": (n_chain["0.5"] - n_chain["2.0"]
                        if n_chain["0.5"] is not None and n_chain["2.0"] is not None
                        else None),
            "absolute_retention_fraction": (
                sum(1 for r in post if r["absolute_retention_2c"] > 0) / len(post)),
            "mirror_failures": sum(1 for r in wrows if not r["mirror_ok"]),
            "seeds": [str(s) for s in seeds],
        }
    return rows, per_w


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def verdict_p_m1(summary: dict) -> dict:
    pred = PREDICTIONS["P-M1_stationary_P"]
    echo_pred = PREDICTIONS["P-M1_echo_windows"]
    mism, floor, echo_mism = [], [], []
    for rid, per in summary.items():
        ex = per["EXACT"]
        got = (ex["7"]["stationary"]["P"], ex["12"]["stationary"]["P"])
        if got != pred[rid]:
            mism.append({"recurrence": rid, "predicted": pred[rid], "got": got})
        if ex["7"]["floor_violations"] or ex["12"]["floor_violations"]:
            floor.append(rid)
        if ex["7"]["stationary"]["S"] or ex["12"]["stationary"]["S"] \
                or ex["7"]["stationary"]["G"] or ex["12"]["stationary"]["G"]:
            floor.append(rid + ":S/G")
        got_e = (ex["7"]["echo_windows"], ex["12"]["echo_windows"])
        if got_e != echo_pred.get(rid, (0, 0)):
            echo_mism.append({"recurrence": rid, "predicted": echo_pred.get(rid, (0, 0)),
                              "got": got_e})
    kept = not mism and not floor
    return {"kept": kept, "stationary_mismatches": mism, "floor_or_SG_violations": floor,
            "echo_mismatches": echo_mism}


def verdict_p_m2(summary: dict) -> dict:
    pred = PREDICTIONS["P-M2_n_lock"]
    lock_mism, exact_nonzero, temp_floor = [], [], []
    for rid, per in summary.items():
        li = per["LIFT"]
        rec_k = [r for r in RECURRENCES if r[0] == rid][0]
        if N_SEED_TONES - rec_k[4] <= 0:
            continue  # unlifted
        got = (li["7"]["n_lock"], li["12"]["n_lock"])
        if rid in pred and got != pred[rid]:
            lock_mism.append({"recurrence": rid, "predicted": pred[rid], "got": got})
        for w in ("7", "12"):
            if li[w]["tempered_floor_violations_from_lock"]:
                temp_floor.append(f"{rid}/W{w}")
            exact_nonzero.append({"recurrence": rid, "W": int(w),
                                  "windows": li[w]["exact_P_nonzero_windows"],
                                  "ns": li[w]["echo_window_ns"]})
    return {"kept": not lock_mism and not temp_floor, "n_lock_mismatches": lock_mism,
            "tempered_floor_violations": temp_floor,
            "lift_exact_P_nonzero_windows": exact_nonzero}


def verdict_p_m3(summary: dict, recs: dict) -> dict:
    pred = PREDICTIONS["P-M3_delta_n"]
    out, bad, slow_bad = [], [], []
    for rid, per in summary.items():
        for mode in ("LIFT", "EXACT"):
            for w in ("7", "12"):
                dn = per[mode][w]["delta_n"]
                nc = per[mode][w]["n_chain"]
                if rid in SLOW:
                    if nc["2.0"] is not None:
                        slow_bad.append(f"{rid}/{mode}/W{w}")
                    continue
                p = pred[rid]
                ok = dn is not None and abs(dn - p) <= CROSSOVER_TOL
                out.append({"recurrence": rid, "seeding": mode, "W": int(w),
                            "delta_n": dn, "predicted": p, "within_tol": ok})
                if not ok:
                    bad.append(f"{rid}/{mode}/W{w}")
    return {"kept": not bad and not slow_bad, "tolerance_steps": CROSSOVER_TOL,
            "rows": out, "outside_tolerance": bad,
            "slow_reached_2c_unexpectedly": slow_bad}


def verdict_p_m4(summary: dict) -> dict:
    pred = PREDICTIONS["P-M4_interval_retention"]
    mism, rot = [], {}
    for rid, per in summary.items():
        li = per["LIFT"]
        got = (li["7"]["stationary"]["interval_retention_2c"],
               li["12"]["stationary"]["interval_retention_2c"])
        if got != pred[rid]:
            mism.append({"recurrence": rid, "predicted": pred[rid], "got": got})
        rot[rid] = {w: li[w]["absolute_retention_fraction"] for w in ("7", "12")}
    return {"kept": not mism, "mismatches": mism,
            "absolute_retention_fraction_of_post_seed_windows": rot}


def verdict_p_m5(summary: dict) -> dict:
    bad_gap, bad_prop, lift_vs_exact = [], [], []
    for rid, per in summary.items():
        if rid in SLOW:
            continue
        for w in ("7", "12"):
            st = per["LIFT"][w]["stationary"]
            if st["m1_gap_classes_2c"] > 3:
                bad_gap.append(f"{rid}/W{w}:{st['m1_gap_classes_2c']}")
            if st["m3_propriety"] != per["LIFT"][w]["pure_chain_propriety"]:
                bad_prop.append(f"{rid}/W{w}:{st['m3_propriety']}!="
                                f"{per['LIFT'][w]['pure_chain_propriety']}")
            a = per["LIFT"][w]["stationary"]
            b = per["EXACT"][w]["stationary"]
            keys = ("P_2c", "S_2c", "m1_gap_classes_2c", "m3_propriety",
                    "interval_retention_2c")
            if any(a[k] != b[k] for k in keys):
                lift_vs_exact.append(f"{rid}/W{w}")
    return {"kept": not bad_gap and not bad_prop, "gap_classes_over_3": bad_gap,
            "propriety_mismatch_vs_pure_chain": bad_prop,
            "lift_vs_exact_stationary_differences": lift_vs_exact}


# ---------------------------------------------------------------------------
# .scl ear-check exports
# ---------------------------------------------------------------------------

SCL_PICKS = ("erv418935", "fib", "metameantone")


def scl_text(name: str, description: str, cs: list[float]) -> str:
    pcs = sorted({round(wrap(c), 6) for c in cs})
    degrees = [c for c in pcs if c > 1e-9] + [CENTS]
    lines = [f"! {name}.scl", "!", description, f" {len(degrees)}", "!"]
    lines += [f" {d:.6f}" for d in degrees]
    return "\n".join(lines) + "\n"


def write_scl(rec: dict, series: dict, h_by_mode: dict) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    w = 7
    h = h_by_mode["LIFT"]
    n_seeds = series["LIFT"]["7"]["n_seeds"]
    picks = {"seed": n_seeds + w - 2,
             "lock": series["LIFT"]["7"]["n_lock"],
             "last": len(h) - 1}
    for tag, n in picks.items():
        if n is None:
            continue
        cs = [cents_of(x) for x in h[n - w + 1:n + 1]]
        name = f"meru001_{rec['id']}_LIFT_W7_n{n:03d}_{tag}"
        text = scl_text(name, f"MERU-001 {rec['label']}; hexany seeds; window of "
                        f"{w} at step {n} ({tag}); 1/1 = lowest window tone",
                        [c - min(cs) for c in cs])
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> dict:
    tones = hexany_tones()
    tone_cents = [cents_of(t) for t in tones]
    classes = interval_classes(tones)
    recs = {r[0]: {**build_recurrence(*r[:5]), "label": r[5]} for r in RECURRENCES}
    all_rows: list[dict] = []
    summary: dict[str, dict] = {}
    scl_files: list[str] = []
    for rid, rec in recs.items():
        per: dict[str, dict] = {}
        h_by_mode: dict[str, list[Fraction]] = {}
        for mode in ("LIFT", "EXACT"):
            rows, per_w = run_series(rec, mode, tones, tone_cents, classes)
            all_rows.extend(rows)
            per[mode] = per_w
            coefs, n_seeds = seeding_plan(rec, mode)
            h_by_mode[mode] = run_recurrence(
                coefs, place_seeds(tones, n_seeds, rec["log2G"], mode), STEPS)
        summary[rid] = per
        if rid in SCL_PICKS:
            scl_files += write_scl(rec, per, h_by_mode)
    mirror_failures = sum(1 for r in all_rows if not r["mirror_ok"])
    verdicts = {
        "P-M1": verdict_p_m1(summary),
        "P-M2": verdict_p_m2(summary),
        "P-M3": verdict_p_m3(summary, recs),
        "P-M4": verdict_p_m4(summary),
        "P-M5": verdict_p_m5(summary),
    }
    receipt = {
        "experiment": EXPERIMENT, "runner_version": MERU001_VERSION,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "steps": STEPS, "windows": list(WINDOWS),
        "seed_tones": [str(t) for t in tones], "seed_cents": tone_cents,
        "hexany_interval_classes_cents": list(classes),
        "recurrences": {rid: {k: v for k, v in rec.items()
                              if k not in ("coefs_exact", "coefs_lift")}
                        | {"coefs_lift": {str(k): v for k, v in rec["coefs_lift"].items()}}
                        for rid, rec in recs.items()},
        "n_rows": len(all_rows), "mirror_failures": mirror_failures,
        "per_recurrence": summary, "verdicts": verdicts,
        "scl_files": scl_files,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  melodic "
          f"{receipt['melodic_version']}  rows={receipt['n_rows']}  "
          f"mirror failures={receipt['mirror_failures']}")
    for rid, per in receipt["per_recurrence"].items():
        ex7, ex12 = per["EXACT"]["7"], per["EXACT"]["12"]
        li7 = per["LIFT"]["7"]
        print(f"  {rid:13s} EXACT stat P {ex7['stationary']['P']}/{ex12['stationary']['P']} "
              f"rt {ex7['stationary']['rt']}/{ex12['stationary']['rt']} "
              f"echo {ex7['echo_windows']}/{ex12['echo_windows']} | LIFT W7 n_lock "
              f"{li7['n_lock']} P2c@last {li7['stationary']['P_2c']} "
              f"n_chain {li7['n_chain']} dn {li7['delta_n']} ir {li7['stationary']['interval_retention_2c']} "
              f"m1@2c {li7['stationary']['m1_gap_classes_2c']} {li7['stationary']['m3_propriety']}")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}")
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {len(receipt['scl_files'])}")


if __name__ == "__main__":
    _print_summary(main())
