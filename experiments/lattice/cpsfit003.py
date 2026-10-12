"""CPSFIT-003 — count-objective chain fit of a CPS field (LOG.md
pre-registration 2026-10-11; committed before this file).

Program B, the third objective. CPSFIT-001 minimized the largest TONE
error, CPSFIT-002 the largest TRIAD deviation. Here the objective is the
NUMBER of exact lattice triads that survive at the LOCK tier (2 cents)
when the lattice is voiced in an N-note generator chain, every tone within
20 cents of its degree. For a fixed assignment the voiced members are
linear in g, so each triad's survival set in g is a union of intervals.
The count is piecewise constant in g. Segments narrower than W_MIN are
discarded. The representative inside the best segment maximizes the
smallest margin eps - |dev| over the surviving triads (CPSFIT-002's
minimax when every triad survives), then the smaller tone error, then the
smaller g. The frozen tempered scorer of the image is the referee. The
tone-minimax (cpsfit001.fit) and triad-minimax (cpsfit002.fit_triads)
fits are recomputed per row for the comparison. Predictions P-C1..P-C7
are pinned in PREDICTIONS below, verbatim from LOG.

Lattices: hexany, EG4 (from cpsfit001), dekany CPS(5,2){1,3,5,7,9}, its
exact reflection 1/CPS(5,2), and dekany CPS(5,3){1,3,5,7,9}.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered via cpsfit001)
  experiments/lattice/melodic.py v0.1.0  (score_melodic via cpsfit001)

Receipts: results/cpsfit003.jsonl (one row per lattice x feasible N) +
results/cpsfit003_summary.json; results/scl/cpsfit003/*.scl ear-check
stimuli. Deterministic: stdlib only, no randomness, no wall-clock fields;
two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 cpsfit003.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpsfit001 as c1  # noqa: E402
import cpsfit002 as c2  # noqa: E402
from scorer import SCORER_VERSION, invert_rational_scale, score_tempered  # noqa: E402
from melodic import MELODIC_VERSION  # noqa: E402  (frozen v0.1.0, read-only)
from families.cps import cps_scale  # noqa: E402

CPSFIT003_VERSION = "1.0.0"
EXPERIMENT = "CPSFIT-003"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "cpsfit003.jsonl"
SUMMARY = RESULTS_DIR / "cpsfit003_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "cpsfit003"
PRIOR_001 = RESULTS_DIR / "cpsfit001.jsonl"
PRIOR_002 = RESULTS_DIR / "cpsfit002.jsonl"

CENTS = 1200.0
N_MIN, N_MAX = 11, 36
EPS_LOCK = 2.0
TONE_CAP = 20.0
GRID = 0.5
G_MAX = 600.0
W_MIN = 0.01          # a registered count must survive g +- 0.005 c
SAMPLE_STEP = 0.1     # largest sample step over a basin, cents
BISECT_STEPS = 40
REP_SAMPLES = 24
REP_GOLDEN_STEPS = 50
KEY_ROUND = 6

LATTICES: dict[str, tuple[Fraction, ...]] = {
    "hexany": c1.LATTICES["hexany"],
    "eg4": c1.LATTICES["eg4"],
    "dek52": cps_scale((1, 3, 5, 7, 9), 2),
    "dek52refl": invert_rational_scale(cps_scale((1, 3, 5, 7, 9), 2)),
    "dek53": cps_scale((1, 3, 5, 7, 9), 3),
}

#: Registered predictions, verbatim from LOG.md 2026-10-11.
PREDICTIONS = {
    "tol_g": 0.02, "tol_cents": 0.05,
    "P-C1": {  # lattice -> [((N_lo, N_hi), count, g, mapping or None, tone_err)]
        "hexany": [((11, 11), 6, 249.211, (-2, -8, -1), 20.00), ((12, 15), 8, 317.175, (6, 5, 3), 17.74),
                   ((16, 17), 10, 116.676, (6, -7, -2), 5.22), ((18, 21), 10, 77.818, (9, 5, -3), 3.87),
                   ((22, 30), 12, 193.908, (16, 2, 5), 2.22), ((31, 36), 12, 77.195, (-22, 5, -3), 0.75)],
        "eg4": [((12, 14), 10, 249.211, (-2, -8, -1), 20.00), ((15, 15), 16, 317.175, (6, 5, 3), 17.74),
                ((16, 17), 18, 116.676, (6, -7, -2), 7.12), ((18, 22), 20, 77.791, (9, 5, -3), 4.03),
                ((23, 23), 24, 193.309, (-15, 2, 5), 3.87), ((24, 30), 24, 193.883, (16, 2, 5), 2.21),
                ((31, 36), 24, 77.191, (-22, 5, -3), 0.92)],
        "dek52": [((15, 17), 12, 503.939, (-1, -4, -10), 20.00), ((18, 18), 14, 497.514, None, 20.00),
                  ((19, 24), 25, 317.049, (6, 5, 3), 18.75), ((25, 25), 26, 234.429, (3, 17, -1), 4.28),
                  ((26, 32), 32, 498.066, (-1, 8, 14), 4.10), ((33, 34), 34, 351.484, None, 9.59),
                  ((35, 36), 37, 316.825, (6, 5, 22), 4.21)],
        "dek53": [((17, 21), 13, 497.381, None, 20.00), ((22, 22), 17, 233.453, (3, 12, -1), 13.53),
                  ((23, 23), 22, 350.827, None, 20.00), ((24, 25), 25, 317.049, (6, 5, 3), 18.75),
                  ((26, 32), 32, 498.066, (-1, 8, 14), 4.08), ((33, 34), 34, 351.484, None, 9.59),
                  ((35, 36), 35, 497.399, None, 6.47)],
        "first_feasible": {"hexany": 11, "eg4": 12, "dek52": 15, "dek52refl": 15, "dek53": 17},
    },
    "P-C2": {"N_hi": 22, "near_c": 0.05,
             "near_tone": {"hexany": [], "eg4": [], "dek52": [], "dek53": []},
             "near_triad": {"hexany": [22], "eg4": [], "dek52": [15, 16, 17], "dek53": []},
             "hexany_16": {"mapping": (6, -7, -2), "g": 116.676, "count": 10, "prior_count": 6}},
    "P-C3": {"exceptions_triad": [("dek52", 18)], "exceptions_tone": [],
             "dek52_18": {"count_frozen": 14, "triad_frozen": 15, "count_exact": 14, "triad_exact": 12}},
    "P-C4": {"first_full": {"hexany": 22, "eg4": 23, "dek52": None, "dek53": None},
             "best_partial": {"dek52": (37, 35), "dek53": (35, 35)}},
    "P-C5": {"differ_N": list(range(17, 26)) + [35, 36], "agree_N": list(range(26, 35)), "g_tol": 0.001},
    "P-C6": {"hexany_18_21": {"count": 10, "mapping": (9, 5, -3), "g": 77.818},
             "hexany_16_17": {"count": 10, "mapping": (6, -7, -2)}},
    "P-C7": {"hexany": {11: (8, 6)},
             "eg4": {12: (12, 10), 13: (12, 10), 14: (12, 10), 15: (18, 16)},
             "dek52": {15: (15, 12), 16: (15, 12), 17: (15, 12), 19: (27, 25), 20: (27, 25), 21: (27, 25),
                       22: (27, 25), 23: (27, 25), 24: (27, 25)},
             "dek53": {17: (17, 13), 18: (17, 13), 19: (17, 13), 20: (17, 13), 21: (17, 13), 22: (19, 17),
                       23: (23, 22), 24: (27, 25), 25: (27, 25)}},
}


# ---------------------------------------------------------------------------
# triads voiced in a chain: deviation as a function of g
# ---------------------------------------------------------------------------


def voiced_offsets(triads, tone_cents: list[float], ks: tuple[int, ...], g: float):
    """Each triad's members as (k, offset) so that the voiced pitch is
    k*g + offset for every g in the assignment's basin (the octave of each
    member is fixed at this g, nearest the exact pitch)."""
    out = []
    for lab, mem in triads:
        v = []
        for i, cx in mem:
            pc = c1.wrap(ks[i] * g)
            m = round((cx - pc) / CENTS)
            v.append((ks[i], pc + CENTS * m - ks[i] * g))
        out.append((lab, v))
    return out


def signed_dev(lab: str, v, g: float) -> tuple[float, float]:
    """(signed mean-condition deviation, AM-HM separation) in cents."""
    va, vb, vc = (k * g + off for k, off in v)
    fa, fb, fc = (2 ** (x / CENTS) for x in (va, vb, vc))
    am, hm = (fa + fc) / 2, 2 * fa * fc / (fa + fc)
    d = c1.cents_of(fb / am) if lab == "P" else c1.cents_of(fb / hm)
    return d, c1.cents_of(am / hm)


def alive(lab: str, v, g: float, eps: float = EPS_LOCK) -> bool:
    """The shared survival predicate: |dev| < eps and separation >= eps."""
    d, sep = signed_dev(lab, v, g)
    return abs(d) < eps and sep >= eps


def basin(tone_cents: list[float], ks: tuple[int, ...], g0: float) -> tuple[float, float] | None:
    """The g-interval on which every tone sits within TONE_CAP of its
    assigned degree, in the octave arrangement valid at g0."""
    lo, hi = 1e-6, G_MAX
    for k, t in zip(ks, tone_cents):
        if k == 0:
            if c1.circ(0.0, t) > TONE_CAP:
                return None
            continue
        m = round((k * g0 - t) / CENTS)
        center = (t + CENTS * m) / k
        lo, hi = max(lo, center - TONE_CAP / abs(k)), min(hi, center + TONE_CAP / abs(k))
    return (lo, hi) if lo < hi else None


def _cross(lab, v, a: float, b: float) -> float:
    """Boundary between a (not alive) and b (alive): the first alive g."""
    for _ in range(BISECT_STEPS):
        m = (a + b) / 2
        if alive(lab, v, m):
            b = m
        else:
            a = m
    return b


def survival_intervals(lab: str, v, lo: float, hi: float) -> list[tuple[float, float]]:
    """The g-intervals in [lo, hi] on which the triad survives."""
    n = max(16, int((hi - lo) / SAMPLE_STEP) + 2)
    xs = [lo + (hi - lo) * i / n for i in range(n + 1)]
    st = [alive(lab, v, x) for x in xs]
    ds = [signed_dev(lab, v, x)[0] for x in xs]
    out = []
    i = 0
    while i <= n:
        if st[i]:
            a = xs[i] if i == 0 else _cross(lab, v, xs[i - 1], xs[i])
            j = i
            while j + 1 <= n and st[j + 1]:
                j += 1
            b = xs[j] if j == n else _cross(lab, v, xs[j + 1], xs[j])
            out.append((a, b))
            i = j + 1
            continue
        if i + 1 <= n and not st[i + 1] and ds[i] * ds[i + 1] < 0:
            a, b = xs[i], xs[i + 1]
            for _ in range(BISECT_STEPS):
                m = (a + b) / 2
                if signed_dev(lab, v, m)[0] * signed_dev(lab, v, a)[0] < 0:
                    b = m
                else:
                    a = m
            z = (a + b) / 2
            if alive(lab, v, z):
                out.append((_cross(lab, v, xs[i], z), _cross(lab, v, xs[i + 1], z)))
        i += 1
    return out


def count_segments(voiced, lo: float, hi: float) -> list[tuple[int, float, float]]:
    """(count, a, b): the g-segments of constant survival count, from the
    sorted interval endpoints; segments narrower than W_MIN dropped."""
    events = []
    for lab, v in voiced:
        for a, b in survival_intervals(lab, v, lo, hi):
            events.append((a, 1))
            events.append((b, -1))
    events.sort()
    cur, segs = 0, []
    for idx, (x, d) in enumerate(events):
        cur += d
        if d == 1 and idx + 1 < len(events):
            segs.append((cur, x, events[idx + 1][0]))
    wide = [(c, a, b) for c, a, b in segs if b - a >= W_MIN]
    return wide or [(0, lo, hi)]


def representative(voiced, a: float, b: float) -> tuple[float, float]:
    """The g in [a, b] maximizing the smallest margin eps - |dev| over the
    triads alive at the midpoint; returns (g, margin)."""
    mid = (a + b) / 2
    live = [(lab, v) for lab, v in voiced if alive(lab, v, mid)]
    if not live:
        return mid, 0.0

    def neg_margin(x: float) -> float:
        return -min(EPS_LOCK - abs(signed_dev(lab, v, x)[0]) for lab, v in live)

    xs = [a + (b - a) * (i + 0.5) / REP_SAMPLES for i in range(REP_SAMPLES)]
    x0 = min(xs, key=neg_margin)
    w = (b - a) / REP_SAMPLES
    gx, fneg = c2.golden(neg_margin, max(a, x0 - w), min(b, x0 + w), REP_GOLDEN_STEPS)
    return gx, -fneg


def window_range(ks: tuple[int, ...], n: int) -> tuple[int, int]:
    """All window starts s with s <= 0 <= s+N-1 holding every k of ks."""
    return max(-(n - 1), max(ks) - (n - 1)), min(0, min(ks))


def transposed_val(tones, ks: list[int], n: int) -> tuple[tuple[int, ...] | None, int]:
    """(mapping, shift j): k = j + sum e_p k_p; shift 0 is the plain val."""
    hom = c1.homomorphism(tones, ks, n)
    if hom is not None:
        return hom, 0
    for j in range(-n, n + 1):
        if j == 0:
            continue
        h = c1.homomorphism(tones, [k - j for k in ks], n)
        if h is not None:
            return h, j
    return None, 0


def fit_count(tones: tuple[Fraction, ...], n: int) -> dict | None:
    """The count-objective fit for one N; None if no assignment is
    feasible under the tone cap."""
    tc = [c1.cents_of(t) for t in tones]
    triads = c2.prep_triads(tones)
    seen: dict[tuple[int, ...], float] = {}
    steps = int(round((G_MAX - 1.0) / GRID))
    for i in range(steps + 1):
        g = 1.0 + i * GRID
        for ks in c2.assignments(tc, n, g):
            seen.setdefault(ks, g)
    best = None
    for ks, g0 in seen.items():
        b = basin(tc, ks, g0)
        if b is None:
            continue
        lo, hi = b
        voiced = voiced_offsets(triads, tc, ks, (lo + hi) / 2)
        segs = count_segments(voiced, lo, hi)
        top = max(c for c, _, _ in segs)
        for c, a, bb in segs:
            if c != top:
                continue
            gx, margin = representative(voiced, a, bb)
            te = c2.tone_err(tc, ks, gx)
            key = (-c, -round(margin, KEY_ROUND), round(te, KEY_ROUND), round(gx, KEY_ROUND))
            if best is None or key < best[0]:
                best = (key, c, margin, te, gx, ks, (a, bb))
    if best is None:
        return None
    _, c, margin, te, gx, ks, seg = best
    s_lo, s_hi = window_range(ks, n)
    voiced = voiced_offsets(triads, tc, ks, gx)
    return {"N": n, "eps": te, "g": gx, "s": s_lo, "s_range": [s_lo, s_hi], "ks": list(ks),
            "errs": [c1.circ(k * gx, t) for k, t in zip(ks, tc)],
            "count": c, "margin": margin, "segment": list(seg),
            "max_dev": max(abs(signed_dev(lab, v, gx)[0]) for lab, v in voiced),
            "n_candidates": len(seen)}


# ---------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------


def image_frozen(tones, ks: list[int], g: float) -> dict:
    pc = [c1.wrap(k * g) for k in ks]
    r = score_tempered(pc, EPS_LOCK)
    devs = c1.triad_deviations(tones, pc)
    exact = sum(1 for d in devs if d["dev_cents"] < EPS_LOCK and d["sep_cents"] >= EPS_LOCK)
    return {"frozen": r.proportional + r.subcontrary, "P": r.proportional, "S": r.subcontrary,
            "exact_count": exact, "max_dev": max(d["dev_cents"] for d in devs)}


def prior_fits(tones, tone_cents: list[float], n: int) -> dict:
    """Tone-minimax and triad-minimax fits recomputed at this N."""
    out = {}
    f = c1.fit(tone_cents, n)
    if f is not None:
        hom = c1.homomorphism(tones, f["ks"], n)
        out["tone"] = {"g_cents": f["g"], "eps_star_cents": f["eps"], "window_start": f["s"],
                       "mapping": list(hom) if hom else None, **image_frozen(tones, f["ks"], f["g"])}
    ft = c2.fit_triads(tones, n)
    if ft is not None:
        hom = c1.homomorphism(tones, ft["ks"], n)
        out["triad"] = {"g_cents": ft["g"], "eps_star_cents": ft["eps"], "window_start": ft["s"],
                        "objective_dev_cents": ft["objective_dev_cents"],
                        "mapping": list(hom) if hom else None, **image_frozen(tones, ft["ks"], ft["g"])}
    return out


def run_lattice(name: str, tones: tuple[Fraction, ...], rr_table: list[dict]) -> list[dict]:
    tc = [c1.cents_of(t) for t in tones]
    rows = []
    for n in range(N_MIN, N_MAX + 1):
        f = fit_count(tones, n)
        if f is None:
            continue
        row = c1.fit_row(name, tones, tc, f, "count", rr_table)
        row["experiment"] = EXPERIMENT
        row["count_exact"] = f["count"]
        row["margin_cents"] = f["margin"]
        row["segment_cents"] = f["segment"]
        row["window_range"] = f["s_range"]
        row["n_candidates"] = f["n_candidates"]
        row["tone_cap_cents"] = TONE_CAP
        mapping, shift = transposed_val(tones, f["ks"], n)
        row["transposed_val"] = None if shift == 0 else {"mapping": list(mapping), "shift": shift}
        row["objective_matches_mirror"] = f["count"] == row["survival_2c_mirror"]
        row["prior"] = prior_fits(tones, tc, n)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def _stair(table, n):
    for (lo, hi), cnt, g, mapping, te in table:
        if lo <= n <= hi:
            return cnt, g, mapping, te
    return None


def verdict_p_c1(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C1"]
    fails = []
    for lat, rows in by_lat.items():
        first = min((r["N"] for r in rows), default=None)
        if first != p["first_feasible"][lat]:
            fails.append(f"{lat}: first feasible N {first} != {p['first_feasible'][lat]}")
        if lat not in p:
            continue
        for r in rows:
            reg = _stair(p[lat], r["N"])
            if reg is None:
                fails.append(f"{lat} N={r['N']}: no registered rung")
                continue
            cnt, g, mapping, te = reg
            if r["count_exact"] != cnt:
                fails.append(f"{lat} N={r['N']}: count {r['count_exact']} != {cnt}")
            if abs(r["g_cents"] - g) > PREDICTIONS["tol_g"]:
                fails.append(f"{lat} N={r['N']}: g {r['g_cents']:.3f} != {g}")
            if abs(r["eps_star_cents"] - te) > PREDICTIONS["tol_cents"]:
                fails.append(f"{lat} N={r['N']}: tone err {r['eps_star_cents']:.2f} != {te}")
            got = tuple(r["mapping"]) if r["mapping"] else None
            if got != mapping or (mapping is None and r["transposed_val"] is not None):
                fails.append(f"{lat} N={r['N']}: mapping {got} / transposed {r['transposed_val']} != {mapping}")
    return {"kept": not fails, "failures": fails}


def verdict_p_c2(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C2"]
    fails, near = [], {}
    for lat in ("hexany", "eg4", "dek52", "dek53"):
        nt, nr = [], []
        for r in by_lat.get(lat, []):
            if r["N"] > p["N_hi"]:
                continue
            pr = r["prior"]
            if "tone" in pr and abs(pr["tone"]["g_cents"] - r["g_cents"]) < p["near_c"]:
                nt.append(r["N"])
            if "triad" in pr and abs(pr["triad"]["g_cents"] - r["g_cents"]) < p["near_c"]:
                nr.append(r["N"])
        near[lat] = {"tone": nt, "triad": nr}
        if nt != p["near_tone"][lat]:
            fails.append(f"{lat}: near tone-minimax at {nt} != {p['near_tone'][lat]}")
        if nr != p["near_triad"][lat]:
            fails.append(f"{lat}: near triad-minimax at {nr} != {p['near_triad'][lat]}")
    h16 = next((r for r in by_lat.get("hexany", []) if r["N"] == 16), None)
    q = p["hexany_16"]
    if h16 is None or tuple(h16["mapping"] or ()) != q["mapping"] or h16["count_exact"] != q["count"] \
            or h16["prior"]["triad"]["frozen"] != q["prior_count"]:
        fails.append("hexany N=16: miracle val / 10 vs 6 not reproduced")
    return {"kept": not fails, "failures": fails, "near": near}


def verdict_p_c3(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C3"]
    viol_tone, viol_triad = [], []
    for lat, rows in by_lat.items():
        for r in rows:
            pr = r["prior"]
            if "tone" in pr and r["survival_2c_frozen"] < pr["tone"]["frozen"]:
                viol_tone.append((lat, r["N"]))
            if "triad" in pr and r["survival_2c_frozen"] < pr["triad"]["frozen"]:
                viol_triad.append((lat, r["N"]))
    fails = []
    if viol_tone != [tuple(x) for x in p["exceptions_tone"]]:
        fails.append(f"tone-minimax exceptions {viol_tone} != {p['exceptions_tone']}")
    if viol_triad != [tuple(x) for x in p["exceptions_triad"]]:
        fails.append(f"triad-minimax exceptions {viol_triad} != {p['exceptions_triad']}")
    d18 = next((r for r in by_lat.get("dek52", []) if r["N"] == 18), None)
    q = p["dek52_18"]
    if d18 is None or (d18["survival_2c_frozen"], d18["prior"]["triad"]["frozen"], d18["count_exact"],
                       d18["prior"]["triad"]["exact_count"]) != (q["count_frozen"], q["triad_frozen"],
                                                                 q["count_exact"], q["triad_exact"]):
        fails.append("dek52 N=18 referee numbers off registration")
    return {"kept": not fails, "failures": fails, "violations_tone": viol_tone, "violations_triad": viol_triad}


def verdict_p_c4(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C4"]
    fails, first, best = [], {}, {}
    for lat in ("hexany", "eg4", "dek52", "dek53"):
        rows = by_lat.get(lat, [])
        full = [r["N"] for r in rows if r["count_exact"] == r["exact_triads"]]
        first[lat] = full[0] if full else None
        if first[lat] != p["first_full"][lat]:
            fails.append(f"{lat}: first full N {first[lat]} != {p['first_full'][lat]}")
        if lat in p["best_partial"]:
            top = max(rows, key=lambda r: (r["count_exact"], -r["N"]))
            best[lat] = (top["count_exact"], top["N"])
            if best[lat] != p["best_partial"][lat]:
                fails.append(f"{lat}: best partial {best[lat]} != {p['best_partial'][lat]}")
        for r in rows:
            pr = r["prior"].get("triad")
            if r["count_exact"] == r["exact_triads"] and pr and pr["exact_count"] != r["exact_triads"]:
                fails.append(f"{lat} N={r['N']}: count full but triad-minimax not full")
    return {"kept": not fails, "failures": fails, "first_full": first, "best_partial": best}


def verdict_p_c5(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C5"]
    a = {r["N"]: r for r in by_lat.get("dek52", [])}
    b = {r["N"]: r for r in by_lat.get("dek52refl", [])}
    c = {r["N"]: r for r in by_lat.get("dek53", [])}
    fails = []
    if set(a) != set(b):
        fails.append("reflection: different feasible N")
    for n, ra in a.items():
        rb = b.get(n)
        if rb is None:
            continue
        if ra["count_exact"] != rb["count_exact"] or abs(ra["g_cents"] - rb["g_cents"]) > p["g_tol"] \
                or abs(ra["max_triad_dev_cents"] - rb["max_triad_dev_cents"]) > p["g_tol"] \
                or abs(ra["margin_cents"] - rb["margin_cents"]) > p["g_tol"]:
            fails.append(f"reflection N={n}: count/g/dev/margin differ")
        if (ra["image_P"]["2.0"], ra["image_S"]["2.0"]) != (rb["image_S"]["2.0"], rb["image_P"]["2.0"]):
            fails.append(f"reflection N={n}: P/S not swapped")
        mirror = -(ra["window_start"] + n - 1)
        if not (rb["window_range"][0] <= mirror <= rb["window_range"][1]):
            fails.append(f"reflection N={n}: mirrored window {mirror} not in {rb['window_range']}")
    differ, agree = [], []
    for n in sorted(set(a) | set(c)):
        ra, rc = a.get(n), c.get(n)
        same = ra is not None and rc is not None and ra["count_exact"] == rc["count_exact"] \
            and abs(ra["g_cents"] - rc["g_cents"]) <= p["g_tol"]
        (agree if same else differ).append(n)
    if differ != p["differ_N"] or agree != p["agree_N"]:
        fails.append(f"CPS(5,3) differ {differ} / agree {agree} != registered")
    return {"kept": not fails, "failures": fails, "cps53_differ_N": differ, "cps53_agree_N": agree}


def verdict_p_c6(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C6"]
    fails = []
    for n in range(18, 22):
        r = next((x for x in by_lat.get("hexany", []) if x["N"] == n), None)
        q = p["hexany_18_21"]
        if r is None or r["count_exact"] != q["count"] or tuple(r["mapping"] or ()) != q["mapping"] \
                or abs(r["g_cents"] - q["g"]) > PREDICTIONS["tol_g"]:
            fails.append(f"hexany N={n}: not {q}")
    for n in (16, 17):
        r = next((x for x in by_lat.get("hexany", []) if x["N"] == n), None)
        q = p["hexany_16_17"]
        if r is None or r["count_exact"] != q["count"] or tuple(r["mapping"] or ()) != q["mapping"]:
            fails.append(f"hexany N={n}: not {q}")
    return {"kept": not fails, "failures": fails}


def verdict_p_c7(by_lat: dict[str, list[dict]]) -> dict:
    p = PREDICTIONS["P-C7"]
    fails, created = [], {}
    for lat, rows in by_lat.items():
        reg = p.get(lat, {})
        for r in rows:
            n = r["N"]
            got = (r["survival_2c_frozen"], r["count_exact"])
            if got[0] > got[1]:
                created.setdefault(lat, {})[n] = got
            if n in reg:
                if got != reg[n]:
                    fails.append(f"{lat} N={n}: frozen/exact {got} != {reg[n]}")
            elif got[0] != got[1]:
                fails.append(f"{lat} N={n}: unregistered created triads {got}")
    return {"kept": not fails, "failures": fails, "created": created}


# ---------------------------------------------------------------------------
# scl + main
# ---------------------------------------------------------------------------

SCL_PICKS = (("hexany", 16), ("hexany", 18), ("dek52", 26))


def write_scl(by_lat: dict[str, list[dict]]) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for lat, n in SCL_PICKS:
        r = next((x for x in by_lat.get(lat, []) if x["N"] == n), None)
        if r is None:
            continue
        chain = [c1.wrap(k * r["g_cents"]) for k in range(r["window_start"], r["window_start"] + n)]
        name = f"cpsfit003_{lat}_N{n:02d}_g{r['g_cents']:.3f}"
        text = c1.scl_text(name, f"CPSFIT-003 {lat} count-objective chain, N = {n}, g = {r['g_cents']:.3f}c; "
                           f"{r['count_exact']} of {r['exact_triads']} exact triads within {EPS_LOCK}c; "
                           f"1/1 = chain degree 0", chain)
        (SCL_DIR / f"{name}.scl").write_text(text)
        out.append(name + ".scl")
    return out


def prior_receipt_check(by_lat: dict[str, list[dict]]) -> dict:
    """The recomputed tone/triad fits must match the CPSFIT-001/002
    receipts on the hexany and EG4 (g within 0.01c, same frozen survival)."""
    mism = []
    if PRIOR_001.exists():
        r1 = {(r["lattice"], r["N"]): r for r in map(json.loads, PRIOR_001.open()) if r["kind"] == "chain"}
        for lat in ("hexany", "eg4"):
            for r in by_lat.get(lat, []):
                p, q = r1.get((lat, r["N"])), r["prior"].get("tone")
                if p and q and (abs(p["g_cents"] - q["g_cents"]) > 0.01 or p["survival_2c_frozen"] != q["frozen"]):
                    mism.append(("cpsfit001", lat, r["N"]))
    if PRIOR_002.exists():
        r2 = {(r["lattice"], r["N"]): r for r in map(json.loads, PRIOR_002.open())}
        for lat in ("hexany", "eg4"):
            for r in by_lat.get(lat, []):
                p, q = r2.get((lat, r["N"])), r["prior"].get("triad")
                if p and q and (abs(p["g_cents"] - q["g_cents"]) > 0.01 or p["survival_2c_frozen"] != q["frozen"]):
                    mism.append(("cpsfit002", lat, r["N"]))
    return {"ok": not mism, "mismatches": mism}


def main() -> dict:
    rr_table = c1.build_rr_table()
    by_lat = {name: run_lattice(name, tones, rr_table) for name, tones in LATTICES.items()}
    rows = [r for rs in by_lat.values() for r in rs]
    verdicts = {"P-C1": verdict_p_c1(by_lat), "P-C2": verdict_p_c2(by_lat), "P-C3": verdict_p_c3(by_lat),
                "P-C4": verdict_p_c4(by_lat), "P-C5": verdict_p_c5(by_lat), "P-C6": verdict_p_c6(by_lat),
                "P-C7": verdict_p_c7(by_lat)}
    receipt = {
        "experiment": EXPERIMENT, "runner_version": CPSFIT003_VERSION,
        "cpsfit001_version": c1.CPSFIT001_VERSION, "cpsfit002_version": c2.CPSFIT002_VERSION,
        "scorer_version": SCORER_VERSION, "melodic_version": MELODIC_VERSION,
        "epsilon_lock_cents": EPS_LOCK, "tone_cap_cents": TONE_CAP, "grid_cents": GRID,
        "min_segment_cents": W_MIN, "N_range": [N_MIN, N_MAX],
        "lattices": {k: [str(t) for t in v] for k, v in LATTICES.items()},
        "n_rows": len(rows),
        "objective_mirror_failures": sum(1 for r in rows if not r["objective_matches_mirror"]),
        "prior_receipt_check": prior_receipt_check(by_lat),
        "staircase": {lat: [{"N": r["N"], "count": r["count_exact"], "frozen": r["survival_2c_frozen"],
                             "exact_triads": r["exact_triads"], "g": r["g_cents"], "tone_err": r["eps_star_cents"],
                             "max_dev": r["max_triad_dev_cents"], "margin": r["margin_cents"],
                             "mapping": r["mapping"], "transposed_val": r["transposed_val"],
                             "window_range": r["window_range"], "mos": r["is_mos"], "chain_P_2c": r["chain_P_2c"],
                             "tone_frozen": r["prior"].get("tone", {}).get("frozen"),
                             "triad_frozen": r["prior"].get("triad", {}).get("frozen")}
                            for r in rs] for lat, rs in by_lat.items()},
        "verdicts": verdicts, "scl_files": write_scl(by_lat),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{EXPERIMENT}  scorer {receipt['scorer_version']}  melodic {receipt['melodic_version']}  "
          f"rows={receipt['n_rows']}  objective/mirror failures={receipt['objective_mirror_failures']}  "
          f"prior receipts ok={receipt['prior_receipt_check']['ok']}")
    for lat, st in receipt["staircase"].items():
        last = None
        for r in st:
            key = (r["count"], round(r["g"], 2))
            if key == last:
                continue
            last = key
            print(f"  {lat:9s} N={r['N']:2d} count={r['count']:2d}/{r['exact_triads']} frozen={r['frozen']:2d} "
                  f"g={r['g']:8.3f} tone={r['tone_err']:6.2f} dev={r['max_dev']:6.2f} margin={r['margin']:.3f} "
                  f"map={r['mapping']} tv={r['transposed_val']} (tone {r['tone_frozen']}, triad {r['triad_frozen']})")
    for k, v in receipt["verdicts"].items():
        print(f"  {k}: {'KEPT' if v['kept'] else 'REFUTED'}" + (f"  {v['failures'][:4]}" if v.get("failures") else ""))
    print(f"  receipts: {RESULTS}, {SUMMARY}; scl: {receipt['scl_files']}")


if __name__ == "__main__":
    _print_summary(main())
