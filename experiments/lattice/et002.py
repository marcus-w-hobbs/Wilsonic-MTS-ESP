"""ET-002 — the subset census of 12-EDO under the frozen scorers
(LOG.md pre-registration 2026-08-18; committed before this file).

Every non-empty pitch-class set of Z12 up to TRANSPOSITION (351 classes,
Pólya) is scored on the melodic side with frozen melodic.py v0.1.0 and on
the harmonic side with frozen triads/scorer.py v1.1.0 (score_tempered,
PRIMARY anchored convention, default max_span 1200c) at the ET-001 epsilon
grid {1, 2, 3, 5, 10, 14.86, 20}c. Per (class, eps): P, S, G, raw counts and
the G-002 balance bucket (verbatim copy of triads/search.py::balance_bucket,
cross-checked by a test) -- NOT a min(P,S) ranking.

Analytic MIRROR (never a substitute for the scorer): inside 12-EDO every
anchored triple is one of ET-001's 12-EDO types (p, q); a class's count is
the number of embedded patterns {b-p, b, b+q} summed over the types that
qualify at eps (dev < eps <= sep, the (dev, sep] half-open interval of
ET-001). Type deviations are imported from et001.mirror_type (read-only).
The melodic mirror is exact integer arithmetic on step vectors. Both are
recorded per row as mirror_agrees flags; disagreement is a verification
failure, never patched over.

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)

Receipts: results/et002.jsonl (one row per class, 351) +
results/et002_summary.json. Deterministic: stdlib only, no randomness, no
wall-clock fields; two runs must produce bit-identical receipts.

Run from experiments/lattice/:  python3.12 et002.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import combinations
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
from et001 import (  # noqa: E402  (ET-001 analytic mirror, reused read-only)
    EPS_GRID,
    ET001_VERSION,
    mirror_type,
    triple_types,
)

ET002_VERSION = "1.0.0"

# --- constants, locked in the LOG.md pre-registration (2026-08-18) ---------
N_EDO = 12
STEP_CENTS = 100.0
EPS_FRONTIER = 14.86
RESULTS_DIR = _HERE / "results"

#: Named classes (tags are by T-class membership; looked up, not searched).
TAGS: dict[str, tuple[int, ...]] = {
    "power_chord": (0, 7),
    "tritone": (0, 6),
    "major_triad": (0, 4, 7),
    "minor_triad": (0, 3, 7),
    "augmented_triad": (0, 4, 8),
    "diminished_triad": (0, 3, 6),
    "sus_trichord": (0, 2, 7),
    "dominant_seventh": (0, 4, 7, 10),
    "diminished_seventh": (0, 3, 6, 9),
    "pentatonic": (0, 2, 4, 7, 9),
    "whole_tone": (0, 2, 4, 6, 8, 10),
    "hexatonic": (0, 1, 4, 5, 8, 9),
    "guidonian_hexachord": (0, 2, 4, 5, 7, 9),
    "diatonic": (0, 2, 4, 5, 7, 9, 11),
    "melodic_minor": (0, 2, 3, 5, 7, 9, 11),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "harmonic_major": (0, 2, 4, 5, 7, 8, 11),
    "octatonic": (0, 1, 3, 4, 6, 7, 9, 10),
    "messiaen_3": (0, 2, 3, 4, 6, 7, 8, 10, 11),
    "messiaen_4": (0, 1, 2, 5, 6, 7, 8, 11),
    "messiaen_5": (0, 1, 5, 6, 7, 11),
    "messiaen_6": (0, 2, 4, 5, 6, 8, 10, 11),
    "messiaen_7": (0, 1, 2, 3, 5, 6, 7, 8, 9, 11),
    "chromatic": tuple(range(12)),
}
#: Aliases sharing a class with a primary tag (Messiaen 1 = whole-tone,
#: Messiaen 2 = octatonic; also known as the augmented scale / bebop names).
TAG_ALIASES: dict[str, str] = {
    "messiaen_1": "whole_tone",
    "messiaen_2": "octatonic",
    "augmented_scale": "hexatonic",
}


# ---------------------------------------------------------------------------
# enumeration and canonical forms
# ---------------------------------------------------------------------------


def transpositions(pcs) -> tuple[tuple[int, ...], ...]:
    """The 12 transpositions of a pitch-class set, each as a sorted tuple."""
    s = tuple(pcs)
    return tuple(
        tuple(sorted((x + t) % N_EDO for x in s)) for t in range(N_EDO)
    )


def canonical_t(pcs) -> tuple[int, ...]:
    """T-class representative: lexicographically smallest transposition."""
    return min(transpositions(pcs))


def inversion(pcs) -> tuple[int, ...]:
    return tuple(sorted((-x) % N_EDO for x in pcs))


def canonical_ti(pcs) -> tuple[int, ...]:
    """T/I-class key: lexmin over transpositions of the set and its
    inversion (deterministic join key; not necessarily Forte's prime form)."""
    return min(canonical_t(pcs), canonical_t(inversion(pcs)))


def rahn_prime_form(pcs) -> tuple[int, ...]:
    """Rahn prime form: over all rotations of the set and its inversion,
    transposed to start at 0, choose the most compact -- minimize the
    tuple read from the largest span downward (t[n-1], t[n-2], ..., t[1])."""
    s = sorted(set(pcs))
    n = len(s)
    if n == 0:
        return ()
    cands = []
    for base in (s, sorted(inversion(s))):
        for i in range(n):
            rot = base[i:] + base[:i]
            norm = tuple((x - rot[0]) % N_EDO for x in rot)
            cands.append((tuple(reversed(norm[1:])), norm))
    return min(cands)[1]


def is_inversionally_symmetric(pcs) -> bool:
    return canonical_t(pcs) == canonical_t(inversion(pcs))


def transposition_period(pcs) -> int:
    """Smallest d | 12 with T_d(S) = S (12 = no limited transposition)."""
    s = set(pcs)
    for d in (1, 2, 3, 4, 6, 12):
        if {(x + d) % N_EDO for x in s} == s:
            return d
    raise AssertionError("unreachable: 12 always fixes the set")


def enumerate_t_classes() -> tuple[tuple[int, ...], ...]:
    """All 351 non-empty T-classes, sorted by (size, canonical tuple)."""
    seen: set[tuple[int, ...]] = set()
    for n in range(1, N_EDO + 1):
        for c in combinations(range(N_EDO), n):
            seen.add(canonical_t(c))
    return tuple(sorted(seen, key=lambda c: (len(c), c)))


def size_histogram(classes) -> dict[int, int]:
    return dict(sorted(Counter(len(c) for c in classes).items()))


def circular_steps(pcs) -> tuple[int, ...]:
    s = sorted(pcs)
    n = len(s)
    return tuple(
        ((s[(i + 1) % n] - s[i]) % N_EDO) or N_EDO for i in range(n)
    )


def _digit(x: int) -> str:
    return str(x) if x < 10 else chr(ord("a") + x - 10)


def step_word(pcs) -> str:
    """Necklace representative of the step pattern: the lexicographically
    smallest rotation of the circular step sequence (12 encoded as 'c')."""
    steps = circular_steps(pcs)
    n = len(steps)
    rots = [steps[i:] + steps[:i] for i in range(n)]
    return "".join(_digit(x) for x in min(rots))


def interval_vector(pcs) -> tuple[int, ...]:
    v = [0] * 7
    for a, b in combinations(sorted(pcs), 2):
        d = (b - a) % N_EDO
        v[min(d, N_EDO - d)] += 1
    return tuple(v[1:])


def cents(pcs) -> tuple[float, ...]:
    return tuple(STEP_CENTS * x for x in sorted(pcs))


# ---------------------------------------------------------------------------
# analytic mirror
# ---------------------------------------------------------------------------

_TYPES_12 = triple_types(N_EDO)


def qualifying_types(eps: float, cls: str) -> tuple[tuple[int, int], ...]:
    """12-EDO types (p, q) counted for class cls at eps: dev < eps <= sep."""
    out = []
    for t in _TYPES_12:
        dev = {"P": t.dev_p, "S": t.dev_s, "G": t.dev_g}[cls]
        if dev < eps <= t.sep:
            out.append((t.p, t.q))
    return tuple(sorted(out))


def pattern_count(pcs, p: int, q: int) -> int:
    """#{b in S : b - p in S and b + q in S} (mod 12)."""
    s = set(pcs)
    return sum(1 for b in s if (b - p) % N_EDO in s and (b + q) % N_EDO in s)


def mirror_counts(pcs, eps: float) -> tuple[int, int, int]:
    """(P, S, G) predicted by the pattern-count mirror at eps."""
    return tuple(
        sum(pattern_count(pcs, p, q) for p, q in qualifying_types(eps, cls))
        for cls in ("P", "S", "G")
    )


def _spectrum(pcs) -> dict[int, list[int]]:
    s = sorted(pcs)
    n = len(s)
    return {
        k: sorted((s[(i + k) % n] - s[i]) % N_EDO for i in range(n))
        for k in range(1, n)
    }


def mirror_melodic(pcs) -> dict:
    """Exact integer Rothenberg propriety, CS and gap classes."""
    sp = _spectrum(pcs)
    n = len(pcs)
    viol = eq = 0
    for k in range(1, n - 1):
        widest, narrowest = sp[k][-1], sp[k + 1][0]
        if widest > narrowest:
            viol += 1
        elif widest == narrowest:
            eq += 1
    prop = "improper" if viol else ("proper" if eq else "strictly_proper")
    spans_by_size: dict[int, set[int]] = {}
    for k, sizes in sp.items():
        for x in sizes:
            spans_by_size.setdefault(x, set()).add(k)
    cs_viol = sum(1 for v in spans_by_size.values() if len(v) > 1)
    return {
        "propriety": prop,
        "propriety_violations": viol,
        "is_cs": cs_viol == 0,
        "cs_violations": cs_viol,
        "gap_class_count": len(set(circular_steps(pcs))),
    }


# ---------------------------------------------------------------------------
# reporting contract pieces
# ---------------------------------------------------------------------------


def balance_bucket(p: int, s: int) -> str:
    """Verbatim copy of triads/search.py::balance_bucket (G-002 reporting
    contract); tests assert equality with the original on a grid."""
    if p == s:
        return "diagonal"
    lo, hi = (s, p) if p > s else (p, s)
    if lo == 0:
        return "degenerate_P" if p > s else "degenerate_S"
    ratio = hi / lo
    side = "P" if p > s else "S"
    if ratio < 1.1:
        return f"near_{side}"
    if ratio < 1.5:
        return f"skew_{side}"
    return f"strong_{side}"


_TAG_BY_CLASS: dict[tuple[int, ...], list[str]] = {}
for _name, _pcs in TAGS.items():
    _TAG_BY_CLASS.setdefault(canonical_t(_pcs), []).append(_name)
for _alias, _primary in TAG_ALIASES.items():
    _TAG_BY_CLASS[canonical_t(TAGS[_primary])].append(_alias)


def tags_for(canonical: tuple[int, ...]) -> list[str]:
    return list(_TAG_BY_CLASS.get(canonical, []))


def pareto_front(rows: list[dict], proper_only: bool = False) -> list:
    """Per-cardinality frontier on (gc minimize, ps maximize). Rows are
    dicts with keys canonical, n, gc, ps, improper. Weak dominance: a row is
    dropped iff some same-N row is <= on gc and >= on ps with one strict."""
    pool = [r for r in rows if not (proper_only and r["improper"])]
    front = []
    for r in pool:
        same = [o for o in pool if o["n"] == r["n"]]
        dominated = any(
            o["gc"] <= r["gc"] and o["ps"] >= r["ps"]
            and (o["gc"] < r["gc"] or o["ps"] > r["ps"])
            for o in same
        )
        if not dominated:
            front.append(r["canonical"])
    return front


# ---------------------------------------------------------------------------
# per-class row
# ---------------------------------------------------------------------------


def _eps_key(eps: float) -> str:
    return f"{eps:g}"


def build_row(canonical: tuple[int, ...]) -> dict:
    n = len(canonical)
    scale = cents(canonical)

    grid = {}
    harmonic_ok = True
    for eps in EPS_GRID:
        r = score_tempered(scale, eps)
        mp, ms, mg = mirror_counts(canonical, eps)
        agrees = (r.proportional, r.subcontrary, r.geometric) == (mp, ms, mg)
        harmonic_ok = harmonic_ok and agrees
        grid[_eps_key(eps)] = {
            "P": r.proportional,
            "S": r.subcontrary,
            "G": r.geometric,
            "P_raw": r.proportional_raw,
            "S_raw": r.subcontrary_raw,
            "G_raw": r.geometric_raw,
            "degenerate_dropped": r.degenerate_dropped,
            "balance": balance_bucket(r.proportional, r.subcontrary),
            "mirror": {"P": mp, "S": ms, "G": mg},
            "mirror_agrees": agrees,
        }

    m = score_melodic(scale)
    melodic = {
        "propriety": m.propriety.classification,
        "propriety_violations": m.propriety.violating_span_pairs,
        "is_cs": m.constant_structure.is_cs,
        "cs_violations": m.constant_structure.violations,
        "gap_class_count": m.gap_entropy.gap_class_count,
        "entropy_bits": m.gap_entropy.entropy_bits,
        "gap_classes_over_n": m.gap_entropy.gap_class_count / n,
    }
    mm = mirror_melodic(canonical)
    melodic_ok = all(melodic[k] == mm[k] for k in mm)

    # derived from the frozen scorer's own grid (pre-registered identities):
    # P@2 = ic5; Maj = P@10 - P@2; Min = S@10 - S@2; WT3 = P@14.86 - P@10 - Maj
    g2, g10, g14 = grid["2"], grid["10"], grid[_eps_key(EPS_FRONTIER)]
    maj = g10["P"] - g2["P"]
    mn = g10["S"] - g2["S"]
    derived = {
        "ic5_from_scorer": g2["P"],
        "major_triads": maj,
        "minor_triads": mn,
        "whole_tone_trichords": g14["P"] - g10["P"] - maj,
        "chromatic_trichord_middles": grid["5"]["P"] - g2["P"],
        "ps_total_frontier_eps": g14["P"] + g14["S"],
    }

    return {
        "experiment": "ET-002",
        "canonical": list(canonical),
        "n": n,
        "step_word": step_word(canonical),
        "steps": list(circular_steps(canonical)),
        "cents": list(scale),
        "ti_key": list(canonical_ti(canonical)),
        "prime_form_rahn": list(rahn_prime_form(canonical)),
        "is_inversionally_symmetric": is_inversionally_symmetric(canonical),
        "transposition_period": transposition_period(canonical),
        "limited_transposition": transposition_period(canonical) < N_EDO,
        "interval_vector": list(interval_vector(canonical)),
        "tags": tags_for(canonical),
        "melodic": melodic,
        "melodic_mirror": mm,
        "grid": grid,
        "derived": derived,
        "mirror_agrees": {"harmonic": harmonic_ok, "melodic": melodic_ok},
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "et001_version": ET001_VERSION,
        "et002_version": ET002_VERSION,
    }


# ---------------------------------------------------------------------------
# verdicts (pre-registered criteria, LOG.md 2026-08-18)
# ---------------------------------------------------------------------------


def _by_tag(rows: dict, tag: str) -> dict:
    for r in rows.values():
        if tag in r["tags"]:
            return r
    raise KeyError(tag)


def _p(r: dict, eps: float) -> int:
    return r["grid"][_eps_key(eps)]["P"]


def _s(r: dict, eps: float) -> int:
    return r["grid"][_eps_key(eps)]["S"]


def _verdict_ht1(rows: dict) -> dict:
    counts_p_pos = {
        _eps_key(e): sum(1 for r in rows.values() if _p(r, e) > 0)
        for e in EPS_GRID
    }
    counts_ps_eq = {
        _eps_key(e): sum(1 for r in rows.values() if _p(r, e) == _s(r, e))
        for e in EPS_GRID
    }
    ic5_rule = all(
        _p(r, 2.0) == r["interval_vector"][4] == _s(r, 2.0)
        for r in rows.values()
    )
    fifthfree_cluster = sorted(
        tuple(r["canonical"]) for r in rows.values()
        if _p(r, 5.0) > 0 and r["interval_vector"][4] == 0
    )
    r12 = rows[tuple(range(12))]
    grid12 = [_p(r12, e) for e in EPS_GRID]
    grid12_s = [_s(r12, e) for e in EPS_GRID]
    nonmono = sum(1 for r in rows.values() if _p(r, 10.0) < _p(r, 5.0))
    buckets = dict(sorted(Counter(
        r["grid"][_eps_key(EPS_FRONTIER)]["balance"] for r in rows.values()
    ).items()))
    expected_p_pos = {"1": 0, "2": 321, "3": 327, "5": 327, "10": 321,
                      "14.86": 330, "20": 330}
    expected_eq = {"1": 351, "2": 351, "3": 351, "5": 351, "10": 231,
                   "14.86": 231, "20": 231}
    expected_cluster = [
        (0, 1, 2), (0, 1, 2, 3), (0, 1, 2, 4), (0, 1, 2, 10),
        (0, 1, 2, 3, 4), (0, 1, 2, 4, 10),
    ]
    ok = (
        counts_p_pos == expected_p_pos
        and counts_ps_eq == expected_eq
        and ic5_rule
        and fifthfree_cluster == expected_cluster
        and grid12 == [0, 12, 24, 24, 24, 48, 48]
        and grid12_s == grid12
        and nonmono == 105
    )
    return {
        "hypothesis": "H-T1 cultural epsilon inherited: P=0 below 1.955c "
                      "everywhere; P@2 = ic5; cluster classes at 3/5c; "
                      "N=12 row = ET-001 rail",
        "classes_with_P_positive": counts_p_pos,
        "classes_with_P_equal_S": counts_ps_eq,
        "P2_equals_ic5_all_classes": ic5_rule,
        "fifth_free_classes_with_P_at_5": [list(c) for c in fifthfree_cluster],
        "n12_grid_P": grid12,
        "n12_grid_S": grid12_s,
        "classes_P10_below_P5": nonmono,
        "balance_buckets_at_frontier_eps": buckets,
        "verdict": "KEPT" if ok else "REFUTED",
    }


def _verdict_ht2(rows: dict) -> dict:
    d = _by_tag(rows, "diatonic")
    sevens = [r for r in rows.values() if r["n"] == 7]
    d_ps = d["derived"]["ps_total_frontier_eps"]
    ties_or_beats = [
        tuple(r["canonical"]) for r in sevens
        if r["derived"]["ps_total_frontier_eps"] >= d_ps
        and tuple(r["canonical"]) != tuple(d["canonical"])
    ]
    p_max = max(_p(r, EPS_FRONTIER) for r in sevens)
    p_at_max = [tuple(r["canonical"]) for r in sevens
                if _p(r, EPS_FRONTIER) == p_max]
    raw = sorted(
        ((r["derived"]["major_triads"] + r["derived"]["minor_triads"],
          tuple(r["canonical"])) for r in sevens), reverse=True
    )
    raw_max = raw[0][0]
    raw_winners = [c for v, c in raw if v == raw_max]
    d_raw = d["derived"]["major_triads"] + d["derived"]["minor_triads"]
    scorer_ok = (
        d["melodic"]["is_cs"] is False
        and d["melodic"]["cs_violations"] == 1
        and d["melodic"]["propriety"] == "proper"
        and _p(d, EPS_FRONTIER) == 15 and _s(d, EPS_FRONTIER) == 15
        and [_p(d, e) for e in EPS_GRID] == [0, 6, 6, 6, 9, 15, 15]
        and d["derived"]["major_triads"] == 3
        and d["derived"]["minor_triads"] == 3
        and d["derived"]["whole_tone_trichords"] == 3
        and ties_or_beats == []
        and p_at_max == [tuple(d["canonical"])]
    )
    raw_refuted_as_predicted = (
        raw_max == 7 and d_raw == 6
        and sorted(raw_winners) == [(0, 1, 2, 4, 5, 8, 9),
                                    (0, 1, 2, 5, 6, 9, 10)]
    )
    return {
        "hypothesis": "H-T2 diatonic distinction: not CS, proper not strict, "
                      "P=S=15 at 14.86c and unique 7-note max of P+S / P / "
                      "S; literal raw Maj+Min maximum predicted REFUTED "
                      "(hexatonic+1 classes carry 7)",
        "diatonic_canonical": d["canonical"],
        "diatonic_melodic": d["melodic"],
        "diatonic_grid_P": [_p(d, e) for e in EPS_GRID],
        "diatonic_grid_S": [_s(d, e) for e in EPS_GRID],
        "diatonic_derived": d["derived"],
        "seven_note_ties_or_beats_on_PS": [list(c) for c in ties_or_beats],
        "seven_note_max_P": p_max,
        "seven_note_P_max_classes": [list(c) for c in p_at_max],
        "seven_note_raw_MajMin_max": raw_max,
        "seven_note_raw_MajMin_winners": [list(c) for c in raw_winners],
        "diatonic_raw_MajMin": d_raw,
        "verdict_scorer_sense": "KEPT" if scorer_ok else "REFUTED",
        "verdict_raw_triad_sense": (
            "REFUTED (as predicted)" if raw_refuted_as_predicted
            else "see fields"
        ),
        "verdict": (
            "KEPT (scorer P+S/P/S unique max; raw Maj+Min refuted as "
            "predicted)" if scorer_ok and raw_refuted_as_predicted
            else "see fields"
        ),
    }


def _verdict_ht3(rows: dict) -> dict:
    prop = Counter(r["melodic"]["propriety"] for r in rows.values())
    cs = sum(1 for r in rows.values() if r["melodic"]["is_cs"])
    per_n = {}
    for n in range(1, N_EDO + 1):
        rr = [r for r in rows.values() if r["n"] == n]
        c = Counter(r["melodic"]["propriety"] for r in rr)
        per_n[str(n)] = {
            "classes": len(rr),
            "strictly_proper": c["strictly_proper"],
            "proper": c["proper"],
            "improper": c["improper"],
            "cs": sum(1 for r in rr if r["melodic"]["is_cs"]),
        }
    strictly = sorted(tuple(r["canonical"]) for r in rows.values()
                      if r["melodic"]["propriety"] == "strictly_proper")
    expected_strict = sorted([
        (0,), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (0, 2, 7), (0, 3, 7), (0, 3, 8), (0, 4, 8),
        (0, 1, 5, 8), (0, 1, 6, 7), (0, 2, 5, 8), (0, 2, 5, 9), (0, 2, 6, 8),
        (0, 2, 6, 9), (0, 3, 6, 9),
        (0, 2, 4, 7, 9), (0, 1, 4, 5, 8, 9), (0, 2, 4, 6, 8, 10),
        (0, 1, 3, 4, 6, 7, 9, 10), tuple(range(12)),
    ])
    max_gcn = max(r["melodic"]["gap_classes_over_n"] for r in rows.values())
    at_max = sum(1 for r in rows.values()
                 if r["melodic"]["gap_classes_over_n"] == max_gcn)
    max_gcn_ge5 = max(r["melodic"]["gap_classes_over_n"]
                      for r in rows.values() if r["n"] >= 5)
    mirror_ok = all(r["mirror_agrees"]["melodic"] for r in rows.values())
    ok = (
        prop["strictly_proper"] == 23 and prop["proper"] == 46
        and prop["improper"] == 282 and cs == 51
        and strictly == expected_strict
        and max_gcn == 1.0 and at_max == 32
        and abs(max_gcn_ge5 - 0.8) < 1e-12
        and mirror_ok
    )
    return {
        "hypothesis": "H-T3 propriety census: 23/46/282 strictly/proper/"
                      "improper, 51 CS, max gap_classes/N = 1.0 (32 classes)",
        "propriety_counts": dict(prop),
        "propriety_fractions": {k: v / len(rows) for k, v in prop.items()},
        "cs_count": cs,
        "cs_fraction": cs / len(rows),
        "per_n": per_n,
        "strictly_proper_classes": [list(c) for c in strictly],
        "max_gap_classes_over_n": max_gcn,
        "classes_at_max": at_max,
        "max_gap_classes_over_n_for_n_ge_5": max_gcn_ge5,
        "melodic_mirror_agrees_all": mirror_ok,
        "verdict": "KEPT" if ok else "REFUTED",
    }


def _frontier_rows(rows: dict) -> list[dict]:
    return [
        {
            "canonical": tuple(r["canonical"]),
            "n": r["n"],
            "gc": r["melodic"]["gap_class_count"],
            "ps": r["derived"]["ps_total_frontier_eps"],
            "improper": r["melodic"]["propriety"] == "improper",
        }
        for r in rows.values()
    ]


def _verdict_ht4(rows: dict) -> dict:
    fr = _frontier_rows(rows)
    front = pareto_front(fr)
    front_proper = pareto_front(fr, proper_only=True)
    front_set = set(front)

    def has(tag: str) -> bool:
        return tuple(_by_tag(rows, tag)["canonical"]) in front_set

    improper_on = sorted(
        c for c in front if rows[c]["melodic"]["propriety"] == "improper"
    )
    expected_improper = sorted([
        (0, 1, 2, 7), (0, 2, 4, 6), (0, 2, 4, 7), (0, 2, 4, 9),
        (0, 1, 2, 3, 5, 7, 8, 10), (0, 1, 2, 3, 4, 5, 6, 8, 9, 10),
    ])
    ok = (
        len(front) == 24 and len(front_proper) == 19
        and has("diatonic") and has("pentatonic") and has("whole_tone")
        and has("hexatonic") and has("guidonian_hexachord")
        and has("messiaen_3") and has("chromatic") and has("sus_trichord")
        and has("augmented_triad")
        and not has("major_triad") and not has("minor_triad")
        and not has("octatonic")
        and improper_on == expected_improper
    )
    members = []
    for c in sorted(front, key=lambda c: (len(c), c)):
        r = rows[c]
        members.append({
            "canonical": list(c), "n": r["n"], "step_word": r["step_word"],
            "gap_class_count": r["melodic"]["gap_class_count"],
            "P": _p(r, EPS_FRONTIER), "S": _s(r, EPS_FRONTIER),
            "P_plus_S": r["derived"]["ps_total_frontier_eps"],
            "propriety": r["melodic"]["propriety"],
            "is_cs": r["melodic"]["is_cs"],
            "balance": r["grid"][_eps_key(EPS_FRONTIER)]["balance"],
            "tags": r["tags"],
        })
    return {
        "hypothesis": "H-T4 Pareto (per-N frontier on gap classes vs P+S at "
                      "14.86c): 24 members incl. diatonic/pentatonic/whole-"
                      "tone/hexatonic/Guidonian/Messiaen-3/chromatic; major, "
                      "minor triads and octatonic NOT on it; 6 improper "
                      "members",
        "frontier_size": len(front),
        "frontier_proper_only_size": len(front_proper),
        "frontier": members,
        "frontier_proper_only": [list(c) for c in sorted(
            front_proper, key=lambda c: (len(c), c))],
        "improper_on_frontier": [list(c) for c in improper_on],
        "named_membership": {
            t: has(t) for t in (
                "diatonic", "pentatonic", "whole_tone", "hexatonic",
                "guidonian_hexachord", "messiaen_3", "chromatic",
                "sus_trichord", "augmented_triad", "major_triad",
                "minor_triad", "octatonic", "melodic_minor",
                "harmonic_minor", "harmonic_major")
        },
        "verdict": "KEPT" if ok else "REFUTED",
    }


def _verdict_rails(rows: dict) -> dict:
    sym_bad = [
        list(r["canonical"]) for r in rows.values()
        if r["is_inversionally_symmetric"]
        and any(_p(r, e) != _s(r, e) for e in EPS_GRID)
    ]
    dual_bad = []
    for c, r in rows.items():
        inv = canonical_t(inversion(c))
        ri = rows[inv]
        if any(_p(r, e) != _s(ri, e) for e in EPS_GRID):
            dual_bad.append(list(c))
    harm_bad = [list(r["canonical"]) for r in rows.values()
                if not r["mirror_agrees"]["harmonic"]]
    mel_bad = [list(r["canonical"]) for r in rows.values()
               if not r["mirror_agrees"]["melodic"]]
    sym_count = sum(1 for r in rows.values() if r["is_inversionally_symmetric"])
    return {
        "R_DUAL_symmetric": {
            "symmetric_classes": sym_count, "failing": sym_bad,
            "verdict": "KEPT" if not sym_bad and sym_count == 95 else "REFUTED",
        },
        "R_DUAL_pairs": {
            "failing": dual_bad,
            "verdict": "KEPT" if not dual_bad else "REFUTED",
        },
        "R_MIRROR_harmonic": {
            "failing": harm_bad,
            "verdict": "KEPT" if not harm_bad else "REFUTED",
        },
        "R_MIRROR_melodic": {
            "failing": mel_bad,
            "verdict": "KEPT" if not mel_bad else "REFUTED",
        },
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def run(results_dir: Path = RESULTS_DIR) -> dict:
    classes = enumerate_t_classes()
    rows = {c: build_row(c) for c in classes}

    hist = size_histogram(classes)
    per_n_tables = {}
    for n in range(1, N_EDO + 1):
        rr = [r for r in rows.values() if r["n"] == n]
        per_n_tables[str(n)] = {
            "classes": len(rr),
            "max_P_plus_S_at_frontier_eps": max(
                r["derived"]["ps_total_frontier_eps"] for r in rr),
            "mean_P_plus_S_at_frontier_eps": sum(
                r["derived"]["ps_total_frontier_eps"] for r in rr) / len(rr),
            "strictly_proper": sum(
                1 for r in rr if r["melodic"]["propriety"] == "strictly_proper"),
            "proper": sum(1 for r in rr if r["melodic"]["propriety"] == "proper"),
            "improper": sum(
                1 for r in rr if r["melodic"]["propriety"] == "improper"),
            "cs": sum(1 for r in rr if r["melodic"]["is_cs"]),
            "inversionally_symmetric": sum(
                1 for r in rr if r["is_inversionally_symmetric"]),
        }

    tagged = {}
    for c, r in rows.items():
        for t in r["tags"]:
            tagged[t] = {
                "canonical": list(c), "n": r["n"], "step_word": r["step_word"],
                "melodic": r["melodic"],
                "grid_P": [_p(r, e) for e in EPS_GRID],
                "grid_S": [_s(r, e) for e in EPS_GRID],
                "grid_G": [r["grid"][_eps_key(e)]["G"] for e in EPS_GRID],
                "balance_at_frontier_eps":
                    r["grid"][_eps_key(EPS_FRONTIER)]["balance"],
                "derived": r["derived"],
            }

    summary = {
        "experiment": "ET-002",
        "preregistration": "experiments/lattice/LOG.md 2026-08-18",
        "corpus": {
            "family": "non-empty pitch-class sets of Z12 up to transposition",
            "classes": len(rows),
            "ti_classes": len({tuple(r["ti_key"]) for r in rows.values()}),
            "size_histogram": {str(k): v for k, v in hist.items()},
            "limited_transposition_classes": sum(
                1 for r in rows.values() if r["limited_transposition"]),
        },
        "constants": {
            "eps_grid": list(EPS_GRID),
            "eps_frontier": EPS_FRONTIER,
            "max_span_cents": DEFAULT_MAX_SPAN_CENTS,
            "step_cents": STEP_CENTS,
            "canonical_form": "lexmin transposition; step_word = necklace-min "
                              "rotation of circular steps (12 -> 'c')",
            "frontier_lens": "per cardinality N: minimize gap_class_count, "
                             "maximize P+S at eps_frontier (weak dominance)",
        },
        "epsilon_semantics": (
            "score_tempered eps is a per-mean-condition deviation in cents "
            "(strict <) with the degeneracy guard sep(a,c) >= eps; a triple "
            "counts on the half-open interval (dev, sep]. NOT the plugin's "
            "register-dependent linear-frequency 0.0005."
        ),
        "verdicts": {
            "H-T1": _verdict_ht1(rows),
            "H-T2": _verdict_ht2(rows),
            "H-T3": _verdict_ht3(rows),
            "H-T4": _verdict_ht4(rows),
            **_verdict_rails(rows),
        },
        "per_n": per_n_tables,
        "tagged": dict(sorted(tagged.items())),
        "scorer_calls": len(rows) * len(EPS_GRID),
        "melodic_calls": len(rows),
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "et001_version": ET001_VERSION,
        "et002_version": ET002_VERSION,
        "python": "3.12",
    }

    results_dir.mkdir(parents=True, exist_ok=True)
    with (results_dir / "et002.jsonl").open("w") as f:
        for c in classes:
            f.write(json.dumps(rows[c], sort_keys=True) + "\n")
    (results_dir / "et002_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return summary


def main() -> None:
    summary = run()
    v = summary["verdicts"]
    print(f"ET-002 complete: {summary['corpus']['classes']} classes, "
          f"{summary['scorer_calls']} scorer calls")
    for key in ("H-T1", "H-T2", "H-T3", "H-T4", "R_DUAL_symmetric",
                "R_DUAL_pairs", "R_MIRROR_harmonic", "R_MIRROR_melodic"):
        print(f"  {key}: {v[key]['verdict']}")
    print(f"  frontier size: {v['H-T4']['frontier_size']} "
          f"(proper-only {v['H-T4']['frontier_proper_only_size']})")
    print(f"  propriety: {v['H-T3']['propriety_counts']}, "
          f"CS {v['H-T3']['cs_count']}")


if __name__ == "__main__":
    main()
