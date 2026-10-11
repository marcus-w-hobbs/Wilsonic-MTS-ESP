"""MUR-002 — grāma/mūrchanā calibration against Wilson's LatticingRagaScales.

Pre-registered in LOG.md ("MUR-002 pre-registration", 2026-08-18) BEFORE
this module was implemented. Primary source (read in place, never copied):
`~/Documents/scans by Kraig/2010_02_24/Hanson/LatticingRagaScales.pdf` —
Figure 1, "Major-Minor Triadic Lattice for 53 (redrawn from 1942
original)" (Hanson's 5-limit hex lattice with 53-EDO degrees), eighteen
ragas as red-dot subsets (pp. 2–19), and the 22-śruti "theoretical scale
of 22 steps, of modern India" outlined in red (p.20). Derived
transcription with page citations: MUR002_TRANSCRIPTION.md.

Under the frozen scorers (triads v1.1.0, melodic v0.1.0 — both imported
READ-ONLY) the experiment measures: H-R1 grāma structure and which
mūrchanā of the ṣaḍja-grāma is Bilawal/Khamaj/…; H-R2 the 22-śruti set
as a housing (MOS? proper? CS? P/S; single-generator chain? 22-EDO /
orwell-22 / 53-EDO fit; raga containment exact vs mod-53); H-R3 the
rotation-invariance rail of P on lattice subsets; H-R4 the ṣaḍja →
madhyama shift as a comma perturbation; H-R5 the schisma as a
constant-structure phase transition in ε_CS. m4_proto — a tonic-anchored
descriptor (step word, interval-from-tonic set, tonic-consonance count) —
is computed HERE, not added to melodic.py.

Deterministic: stdlib only, fixed corpus order, no randomness.
Run from experiments/lattice/:  python3.12 mur002.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from fractions import Fraction as F
from math import log2
from pathlib import Path
from typing import Iterable, Optional

_LATTICE_DIR = Path(__file__).resolve().parent
_TRIADS_DIR = _LATTICE_DIR.parent / "triads"
for _p in (_LATTICE_DIR, _TRIADS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scorer import SCORER_VERSION, score, score_tempered  # noqa: E402
from melodic import (  # noqa: E402
    MELODIC_VERSION,
    best_val_kendall_tau,
    constant_structure,
    score_melodic,
)

EXPERIMENT = "MUR-002"
JSONL_PATH = _LATTICE_DIR / "results" / "mur002.jsonl"
SUMMARY_PATH = _LATTICE_DIR / "results" / "mur002_summary.json"
SOURCE = "scans by Kraig/2010_02_24/Hanson/LatticingRagaScales.pdf"

#: locked constants (LOG.md pre-registration)
TRIAD_EPSILONS = (2.0, 3.0, 5.0, 15.0)
CS_SWEEP = (0.5, 1.0, 1.5, 1.9, 2.0, 2.5, 3.0, 5.0)
FIT_TOLERANCES = (5.0, 2.0)
COARSE_T_THRESHOLD = 150.0
ORWELL_GENERATOR = 271.385          # BRIDGE-001's orwell-22 host, cents
FIFTH_CENTS = 1200.0 * log2(1.5)
CONSONANCES = (F(3, 2), F(4, 3), F(5, 4), F(6, 5), F(5, 3), F(8, 5))
SCHISMA_CENTS = 1200.0 * log2(32805 / 32768)


# ---------------------------------------------------------------------------
# corpus — transcription of LatticingRagaScales.pdf (derived data only)
# ---------------------------------------------------------------------------

#: p.20 — the 22-śruti set outlined in red, with the figure's 53-degree
#: numbers; śruti index = sorted rank (0 = Sa).
S22_DEG53 = (
    (F(1), 0), (F(256, 243), 4), (F(16, 15), 5), (F(10, 9), 8),
    (F(9, 8), 9), (F(32, 27), 13), (F(6, 5), 14), (F(5, 4), 17),
    (F(81, 64), 18), (F(4, 3), 22), (F(27, 20), 23), (F(45, 32), 26),
    (F(729, 512), 27), (F(3, 2), 31), (F(128, 81), 35), (F(8, 5), 36),
    (F(5, 3), 39), (F(27, 16), 40), (F(16, 9), 44), (F(9, 5), 45),
    (F(15, 8), 48), (F(243, 128), 49),
)
S22 = [r for r, _ in S22_DEG53]

#: pp. 2–19 — ragas as red dots: (lattice label, ratio, 53-degree).
_C = ("C", F(1), 0)
_D = ("D", F(9, 8), 9)
_E = ("E", F(5, 4), 17)
_Fn = ("F", F(4, 3), 22)
_G = ("G", F(3, 2), 31)
_A = ("A", F(5, 3), 39)
_B = ("B", F(15, 8), 48)
_uA = ("/A", F(27, 16), 40)
_uFs = ("/F#", F(45, 32), 26)
_uCs = ("/C#", F(135, 128), 4)
_uGs = ("/G#", F(405, 256), 35)
_uDs = ("/D#", F(1215, 1024), 13)
_uuAs = ("//A#", F(3645, 2048), 44)
_dD = ("\\D", F(10, 9), 8)
_dDb = ("\\Db", F(256, 243), 4)
_dEb = ("\\Eb", F(32, 27), 13)
_dAb = ("\\Ab", F(128, 81), 35)
_dBb = ("\\Bb", F(16, 9), 44)

RAGAS = (
    {"num": 18, "name": "Nat Bhairav", "page": 2,
     "tones": (_C, _D, _E, _Fn, _G, _uGs, _B)},
    {"num": 17, "name": "Madhubanti", "page": 3,
     "tones": (_C, _D, _uDs, _uFs, _G, _uA, _B)},
    {"num": 16, "name": "Jogiya Todi", "page": 4,
     "tones": (_C, _uCs, _uDs, _Fn, _G, _uGs, _B)},
    {"num": 15, "name": "Bhairav", "page": 5,
     "tones": (_C, _uCs, _E, _Fn, _G, _uGs, _B)},
    {"num": 14, "name": "Anand Bhairav", "page": 6,
     "tones": (_C, _uCs, _E, _Fn, _G, _A, _B)},
    {"num": 13, "name": "No Name", "page": 7,
     "tones": (_C, _uCs, _uDs, _uFs, _G, _uGs, _uuAs)},
    {"num": 12, "name": "Lalit", "page": 8,
     "tones": (_C, _uCs, _E, _Fn, _uFs, _uGs, _B)},
    {"num": 11, "name": "Todi", "page": 9,
     "tones": (_C, _uCs, _uDs, _uFs, _G, _uGs, _B)},
    {"num": 10, "name": "Lalit 2", "page": 10,
     "tones": (_C, _uCs, _E, _Fn, _uFs, _A, _B)},
    {"num": 9, "name": "Purvi", "page": 11,
     "tones": (_C, _uCs, _E, _uFs, _G, _uGs, _B)},
    {"num": 8, "name": "Marwa", "page": 12,
     "tones": (_C, _uCs, _E, _uFs, _G, _A, _B)},
    {"num": 7, "name": "Bhairavi", "page": 13,
     "tones": (_C, _dDb, _dEb, _Fn, _G, _dAb, _dBb)},
    {"num": 6, "name": "Asawari", "page": 14,
     "tones": (_C, _D, _dEb, _Fn, _G, _dAb, _dBb)},
    {"num": 5, "name": "Kafi", "page": 15,
     "tones": (_C, _D, _dEb, _Fn, _G, _uA, _dBb)},
    {"num": 4, "name": "Old Kafi", "page": 16,
     "tones": (_C, _dD, _dEb, _Fn, _G, _A, _dBb)},
    {"num": 3, "name": "Khamaj", "page": 17,
     "tones": (_C, _D, _E, _Fn, _G, _A, _dBb)},
    {"num": 2, "name": "Bilawal", "page": 18,
     "tones": (_C, _D, _E, _Fn, _G, _uA, _B)},
    {"num": 1, "name": "Kalyan", "page": 19,
     "tones": (_C, _D, _E, _uFs, _G, _A, _B)},
)

#: ṣaḍja-grāma = Wilson's "Old Kafi" (p.16); madhyama-grāma DERIVED
#: (Pa lowered one śruti, 3/2 → 40/27) — not drawn by Wilson.
SA = (F(1), F(10, 9), F(32, 27), F(4, 3), F(3, 2), F(5, 3), F(16, 9))
MA = (F(1), F(10, 9), F(32, 27), F(4, 3), F(40, 27), F(5, 3), F(16, 9))

#: modern thaat coarse words (T = step > 150¢) used for the H-R1 lookup
THAAT_WORDS = {
    "Bilawal": "TTsTTTs", "Khamaj": "TTsTTsT", "Kafi": "TsTTTsT",
    "Kalyan": "TTTsTTs", "Asawari": "TsTTsTT", "Bhairavi": "sTTTsTT",
}


# ---------------------------------------------------------------------------
# arithmetic helpers
# ---------------------------------------------------------------------------


def monzo35(r: F) -> tuple[int, int]:
    """(e3, e5) of a 5-limit ratio; raises if any other odd prime appears."""
    e3 = e5 = 0
    n, d = r.numerator, r.denominator
    for prime, sign in ((n, 1), (d, -1)):
        while prime % 2 == 0:
            prime //= 2
        while prime % 3 == 0:
            prime //= 3
            e3 += sign
        while prime % 5 == 0:
            prime //= 5
            e5 += sign
        if prime != 1:
            raise ValueError(f"not 5-limit: {r}")
    return e3, e5


def deg53(r: F) -> int:
    """53-EDO degree of a 5-limit ratio, the figure's numbering
    (schismatic patent val ⟨53, 84, 123⟩: fifth 31, third 17)."""
    e3, e5 = monzo35(r)
    return (31 * e3 + 17 * e5) % 53


def reduce_octave(r: F) -> F:
    while r >= 2:
        r /= 2
    while r < 1:
        r *= 2
    return r


def canonical(ratios: Iterable[F]) -> tuple[F, ...]:
    return tuple(sorted({reduce_octave(F(r)) for r in ratios}))


def cents(r: F) -> float:
    return 1200.0 * log2(r.numerator / r.denominator)


def cents_of(scale: Iterable[F]) -> tuple[float, ...]:
    return tuple(cents(r) for r in scale)


def rotate(scale: tuple[F, ...], k: int) -> tuple[F, ...]:
    """Mūrchanā: re-tonicize the scale on its k-th tone."""
    tonic = scale[k % len(scale)]
    return canonical(r / tonic for r in scale)


def step_word(scale: tuple[F, ...]) -> tuple[F, ...]:
    n = len(scale)
    return tuple(reduce_octave(scale[(i + 1) % n] / scale[i]) if i + 1 < n
                 else F(2) / scale[i] for i in range(n))


def coarse_word(steps: Iterable[F]) -> str:
    return "".join("T" if cents(s) > COARSE_T_THRESHOLD else "s"
                   for s in steps)


def word_rotation_index(word: str, target: str) -> Optional[int]:
    """Smallest k with rotate(word, k) == target, else None."""
    if len(word) != len(target):
        return None
    for k in range(len(word)):
        if word[k:] + word[:k] == target:
            return k
    return None


def m4_proto(scale: tuple[F, ...]) -> dict:
    """Tonic-anchored descriptor (runner-local; NOT part of melodic.py)."""
    steps = step_word(scale)
    return {
        "step_word": tuple(str(s) for s in steps),
        "step_word_cents": tuple(round(cents(s), 3) for s in steps),
        "coarse_word": coarse_word(steps),
        "from_tonic": tuple({"ratio": str(r), "cents": round(cents(r), 3)}
                            for r in scale),
        "tonic_consonance_count": sum(1 for r in scale if r in CONSONANCES),
    }


def sruti_spelled(scale: tuple[F, ...]) -> tuple[F, ...]:
    """Snap each tone to the S22 tone with the same 53-degree."""
    by_deg = {deg53(r): r for r in S22}
    return canonical(by_deg[deg53(r)] for r in scale)


def edo_image(scale: tuple[F, ...], n: int) -> tuple[float, ...]:
    if n != 53:
        raise ValueError("only the 53-degree map is defined for the lattice")
    return tuple(sorted(1200.0 * deg53(r) / 53 for r in scale))


def edo_cents(n: int) -> tuple[float, ...]:
    return tuple(1200.0 * k / n for k in range(n))


def chain_cents(generator: float, n: int, anchor: int) -> tuple[float, ...]:
    return tuple(sorted((k * generator) % 1200.0
                        for k in range(anchor, anchor + n)))


def _circ_dist(a: float, b: float) -> float:
    d = abs(a - b) % 1200.0
    return min(d, 1200.0 - d)


def matches_within(a: Iterable[float], b: Iterable[float], tol: float,
                   offset: float = 0.0) -> int:
    """Number of tones of a with some tone of b + offset within tol."""
    bs = tuple(b)
    return sum(1 for x in a
               if any(_circ_dist(x, y + offset) <= tol for y in bs))


def best_offset_match(a: Iterable[float], b: Iterable[float],
                      tol: float) -> int:
    """max over offsets of matches_within (candidates: every a_i − b_j)."""
    a, b = tuple(a), tuple(b)
    best = 0
    for x in a:
        for y in b:
            best = max(best, matches_within(a, b, tol, offset=x - y))
    return best


def gap_classes(cents_scale: Iterable[float], eps: float) -> tuple[float, ...]:
    """Distinct circular gap sizes (cluster minima), ascending."""
    s = sorted(c % 1200.0 for c in cents_scale)
    gaps = sorted(((s[(i + 1) % len(s)] - s[i]) % 1200.0) or 1200.0
                  for i in range(len(s)))
    classes, cur = [], None
    for g in gaps:
        if cur is None or g - cur > eps:
            cur = g
            classes.append(g)
    return tuple(classes)


def three_gap_identity(gaps: tuple[float, ...], tol: float) -> bool:
    """Rank-1 three-gap sets satisfy L = M + S (three-distance theorem)."""
    if len(gaps) != 3:
        return False
    s, m, l = gaps
    return abs(l - (m + s)) <= tol


# ---------------------------------------------------------------------------
# frozen-scorer wrappers (read-only imports)
# ---------------------------------------------------------------------------


def triad_counts_exact(scale: tuple[F, ...]) -> tuple[int, int, int]:
    r = score(scale)
    return (r.proportional, r.subcontrary, r.geometric)


def triad_counts_tempered(cents_scale: Iterable[float],
                          eps: float) -> tuple[int, int, int]:
    r = score_tempered(cents_scale, eps)
    return (r.proportional, r.subcontrary, r.geometric)


def melodic_triple(cents_scale: Iterable[float]) -> dict:
    m = score_melodic(cents_scale)
    return {
        "propriety": m.propriety.classification,
        "propriety_violations": m.propriety.violating_span_pairs,
        "propriety_equalities": m.propriety.equal_span_pairs,
        "cs_violations": m.constant_structure.violations,
        "is_cs": m.constant_structure.is_cs,
        "gap_class_count": m.gap_entropy.gap_class_count,
        "gap_entropy_bits": round(m.gap_entropy.entropy_bits, 6),
        "gap_classes": [(round(a, 3), round(b, 3), n)
                        for a, b, n in m.gap_entropy.gap_classes],
    }


def cs_sweep(cents_scale: Iterable[float]) -> dict:
    cs = tuple(cents_scale)
    return {str(e): constant_structure(cs, cs_epsilon_cents=e).violations
            for e in CS_SWEEP}


def scale_row(scale_id: str, family: str, scale: tuple[F, ...], rotation: int,
              epsilons: tuple[float, ...] = TRIAD_EPSILONS,
              tempered_only: Optional[tuple[float, ...]] = None,
              extra: Optional[dict] = None) -> dict:
    """One receipt row for one (scale, rotation). If tempered_only is
    given (a cents scale, e.g. a 53-EDO image) the exact path is skipped."""
    if tempered_only is None:
        cs = cents_of(scale)
        exact = triad_counts_exact(scale)
        val = best_val_kendall_tau(scale)
        val_row = {"min_tau": val.min_tau, "best_val": list(val.best_val),
                   "tie_pairs_at_best": val.tie_pairs_at_best}
        ratios = [str(r) for r in scale]
        proto = m4_proto(scale)
    else:
        cs = tuple(tempered_only)
        exact = None
        val_row = None
        ratios = None
        proto = None
    row = {
        "experiment": EXPERIMENT,
        "scale_id": scale_id,
        "family": family,
        "rotation": rotation,
        "n": len(cs),
        "ratios": ratios,
        "cents": [round(c, 4) for c in cs],
        "melodic": melodic_triple(cs),
        "val": val_row,
        "triads_exact": exact,
        "triads_tempered": {str(e): triad_counts_tempered(cs, e)
                            for e in epsilons},
        "m4_proto": proto,
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
    }
    if extra:
        row.update(extra)
    return row


# ---------------------------------------------------------------------------
# experiment
# ---------------------------------------------------------------------------


def raga_scale(raga: dict) -> tuple[F, ...]:
    return canonical(t[1] for t in raga["tones"])


def rotation_rows(scale_id: str, family: str, scale: tuple[F, ...],
                  extra: Optional[dict] = None) -> list[dict]:
    return [scale_row(scale_id, family, rotate(scale, k), k, extra=extra)
            for k in range(len(scale))]


def rows_invariant(rows: list[dict], key: str) -> bool:
    return len({json.dumps(r[key], sort_keys=True) for r in rows}) == 1


def run_rows() -> list[dict]:
    rows: list[dict] = []
    # S22 — 22 rotations (rail) — and its 53-EDO image
    for k in range(22):
        rows.append(scale_row("S22", "sruti22", rotate(tuple(S22), k), k,
                              extra={"page": 20}))
    rows.append(scale_row("S22_53edo", "sruti22_53edo", tuple(S22), 0,
                          tempered_only=edo_image(tuple(S22), 53),
                          extra={"page": 20}))
    # grāmas
    rows += rotation_rows("SA", "sadja_grama", SA,
                          extra={"page": 16, "note": "Old Kafi"})
    rows += rotation_rows("MA", "madhyama_grama", MA,
                          extra={"page": None, "note": "derived, not drawn"})
    # ragas: as drawn (7 rotations), śruti-spelled (rotation 0), 53-EDO image
    for raga in RAGAS:
        sid = f"R{raga['num']:02d}"
        drawn = raga_scale(raga)
        extra = {"page": raga["page"], "name": raga["name"],
                 "labels": [t[0] for t in raga["tones"]]}
        rows += rotation_rows(sid, "raga_drawn", drawn, extra=extra)
        rows.append(scale_row(sid + "_sruti", "raga_sruti",
                              sruti_spelled(drawn), 0, extra=extra))
        rows.append(scale_row(sid + "_53edo", "raga_53edo", drawn, 0,
                              tempered_only=edo_image(drawn, 53),
                              extra=extra))
    return rows


def _by(rows: list[dict], scale_id: str, family: Optional[str] = None
        ) -> list[dict]:
    return [r for r in rows if r["scale_id"] == scale_id
            and (family is None or r["family"] == family)]


def verdict_hr1(rows: list[dict]) -> dict:
    sa0 = _by(rows, "SA")[0]
    ma0 = _by(rows, "MA")[0]
    sa_rots = _by(rows, "SA")
    ma_rots = _by(rows, "MA")
    sa_sets = {k: rotate(SA, k) for k in range(7)}
    ma_sets = {k: rotate(MA, k) for k in range(7)}
    thaats = {}
    for name, word in THAAT_WORDS.items():
        raga = next(r for r in RAGAS if r["name"] == name)
        target = raga_scale(raga)
        exact_sa = [k for k, s in sa_sets.items() if s == target]
        exact_ma = [k for k, s in ma_sets.items() if s == target]
        k_word = word_rotation_index(coarse_word(step_word(SA)), word)
        drawn_word = coarse_word(step_word(target))
        diff = None
        if k_word is not None:
            diff = len(set(target) - set(sa_sets[k_word]))
        thaats[name] = {
            "wilson_ratios": [str(r) for r in target],
            "wilson_coarse_word": drawn_word,
            "modern_word": word,
            "exact_match_sa_rotation": exact_sa,
            "exact_match_ma_rotation": exact_ma,
            "coarse_match_sa_rotation": k_word,
            "tones_differing_from_coarse_sa_match": diff,
        }
    m_ok = (sa0["melodic"]["propriety"] == "strictly_proper"
            and ma0["melodic"]["propriety"] == "strictly_proper"
            and sa0["melodic"]["is_cs"] and ma0["melodic"]["is_cs"])
    exact_ok = (thaats["Bilawal"]["exact_match_sa_rotation"] == [6]
                and thaats["Khamaj"]["exact_match_sa_rotation"] == [3])
    return {
        "sa_melodic": sa0["melodic"], "ma_melodic": ma0["melodic"],
        "sa_rotations_melodic_invariant": rows_invariant(sa_rots, "melodic"),
        "ma_rotations_melodic_invariant": rows_invariant(ma_rots, "melodic"),
        "sa_distinct_step_words": len({r["m4_proto"]["step_word"]
                                       for r in sa_rots}),
        "ma_distinct_step_words": len({r["m4_proto"]["step_word"]
                                       for r in ma_rots}),
        "sa_rotation_words": {str(r["rotation"]): r["m4_proto"]["coarse_word"]
                              for r in sa_rots},
        "thaats": thaats,
        "predicted": {"propriety": "strictly_proper x2, CS x2",
                      "Bilawal": "SA@6", "Khamaj": "SA@3"},
        "verdict": "KEPT" if (m_ok and exact_ok) else "REFUTED",
    }


def verdict_hr2(rows: list[dict]) -> dict:
    s22 = _by(rows, "S22")[0]
    s22c = cents_of(tuple(S22))
    gaps = gap_classes(s22c, 0.5)
    degs = sorted(deg53(r) for r in S22)
    fifth_chain_53 = sorted((31 * k) % 53 for k in range(-10, 12))
    pyth = chain_cents(FIFTH_CENTS, 22, -10)
    fits = {}
    for name, cand in (("22edo", edo_cents(22)),
                       ("orwell22", chain_cents(ORWELL_GENERATOR, 22, 0)),
                       ("53edo", edo_cents(53)),
                       ("pyth22_anchor-10", pyth)):
        fits[name] = {str(t): best_offset_match(s22c, cand, t)
                      for t in FIT_TOLERANCES}
    fits["pyth22_anchor-10"]["aligned_5"] = matches_within(s22c, pyth, 5.0)
    fits["pyth22_anchor-10"]["aligned_2"] = matches_within(s22c, pyth, 2.0)
    fits["pyth22_anchor-10"]["max_dev_aligned"] = round(max(
        min(_circ_dist(x, y) for y in pyth) for x in s22c), 4)
    housing = {}
    s22set, s22deg = set(S22), set(degs)
    for raga in RAGAS:
        sc = raga_scale(raga)
        housing[raga["name"]] = {
            "exact_subset": set(sc) <= s22set,
            "mod53_subset": {deg53(r) for r in sc} <= s22deg,
        }
    n_exact = sum(1 for h in housing.values() if h["exact_subset"])
    n_mod = sum(1 for h in housing.values() if h["mod53_subset"])
    mel = s22["melodic"]
    a_ok = (mel["gap_class_count"] == 3 and mel["propriety"] == "improper"
            and mel["is_cs"] and s22["triads_exact"][0] == 45
            and s22["triads_exact"][1] == 45)
    b_ok = (not three_gap_identity(gaps, 0.01)
            and degs == fifth_chain_53
            and fits["pyth22_anchor-10"]["5.0"] == 22
            and fits["22edo"]["5.0"] <= 10 and fits["orwell22"]["5.0"] <= 10
            and fits["53edo"]["2.0"] == 22)
    c_ok = (n_mod == 18 and n_exact == 7)
    return {
        "melodic": mel, "triads_exact": s22["triads_exact"],
        "triads_tempered": s22["triads_tempered"],
        "gap_classes_cents": [round(g, 3) for g in gaps],
        "three_gap_identity_0.01c": three_gap_identity(gaps, 0.01),
        "three_gap_identity_2c": three_gap_identity(gaps, 2.0),
        "three_gap_defect_cents": round(gaps[2] - gaps[1] - gaps[0], 4)
        if len(gaps) == 3 else None,
        "degrees53": degs, "fifth_chain_53_-10..11": fifth_chain_53,
        "degrees_equal_fifth_chain": degs == fifth_chain_53,
        "fits": fits, "housing": housing,
        "housing_exact_count": n_exact, "housing_mod53_count": n_mod,
        "clauses": {"a": a_ok, "b": b_ok, "c": c_ok},
        "verdict": "KEPT" if (a_ok and b_ok and c_ok) else "REFUTED",
    }


def verdict_hr3(rows: list[dict]) -> dict:
    ids = ["SA", "MA"] + [f"R{r['num']:02d}" for r in RAGAS] + ["S22"]
    violations = []
    for sid in ids:
        rs = [r for r in _by(rows, sid)
              if r["family"] in ("sadja_grama", "madhyama_grama",
                                 "raga_drawn", "sruti22")]
        for key in ("triads_exact", "triads_tempered"):
            if not rows_invariant(rs, key):
                violations.append((sid, key))
    return {"scales_checked": len(ids), "violations": violations,
            "predicted_violations": 0,
            "verdict": "KEPT" if not violations else "REFUTED"}


def verdict_hr4(rows: list[dict]) -> dict:
    sa0, ma0 = _by(rows, "SA")[0], _by(rows, "MA")[0]
    sa_word = coarse_word(step_word(SA))
    ma_word = coarse_word(step_word(MA))
    inv_sa = canonical(F(1) / r for r in SA)
    is_rotation = any(rotate(SA, k) == MA for k in range(7))
    is_inv_rotation = any(rotate(inv_sa, k) == MA for k in range(7))
    same_melodic = (json.dumps(sa0["melodic"], sort_keys=True)
                    == json.dumps(ma0["melodic"], sort_keys=True))
    ex = (tuple(sa0["triads_exact"][:2]), tuple(ma0["triads_exact"][:2]))
    ok = same_melodic and ex == ((11, 7), (13, 9))
    return {
        "sa_word": sa_word, "ma_word": ma_word,
        "ma_is_rotation_of_sa": is_rotation,
        "ma_is_rotation_of_inverted_sa": is_inv_rotation,
        "same_melodic_triple": same_melodic,
        "sa_exact_PS": ex[0], "ma_exact_PS": ex[1],
        "sa_tempered": sa0["triads_tempered"],
        "ma_tempered": ma0["triads_tempered"],
        "predicted": {"sa": (11, 7), "ma": (13, 9), "melodic": "identical"},
        "verdict": "KEPT" if ok else "REFUTED",
    }


def verdict_hr5(rows: list[dict]) -> dict:
    s22c = cents_of(tuple(S22))
    sweep = cs_sweep(s22c)
    img = edo_image(tuple(S22), 53)
    cs53 = constant_structure(img, cs_epsilon_cents=0.5)
    fifth53 = 1200.0 * 31 / 53
    fifth_violation = any(abs(lo - fifth53) <= 0.5 and {12, 13} <= set(spans)
                          for lo, hi, spans in cs53.violating_classes)
    below = all(sweep[str(e)] == 0 for e in CS_SWEEP if e < SCHISMA_CENTS)
    above = all(sweep[str(e)] > 0 for e in CS_SWEEP if e > SCHISMA_CENTS)
    return {
        "schisma_cents": round(SCHISMA_CENTS, 4),
        "cs_violations_by_epsilon": sweep,
        "cs53_violations": cs53.violations,
        "cs53_violating_classes": [(round(lo, 3), round(hi, 3), list(sp))
                                   for lo, hi, sp in cs53.violating_classes],
        "cs53_fifth_at_12_and_13_steps": fifth_violation,
        "verdict": "KEPT" if (below and above and cs53.violations > 0
                              and fifth_violation) else "REFUTED",
    }


def descriptive(rows: list[dict]) -> dict:
    out = {}
    for raga in RAGAS:
        sid = f"R{raga['num']:02d}"
        d = _by(rows, sid, "raga_drawn")[0]
        s = _by(rows, sid + "_sruti")[0]
        e = _by(rows, sid + "_53edo")[0]
        out[raga["name"]] = {
            "page": raga["page"], "num": raga["num"],
            "ratios": d["ratios"],
            "propriety": d["melodic"]["propriety"],
            "cs_drawn": d["melodic"]["is_cs"],
            "cs_sruti": s["melodic"]["is_cs"],
            "cs_53edo": e["melodic"]["is_cs"],
            "gap_classes": d["melodic"]["gap_class_count"],
            "exact_PS_drawn": d["triads_exact"][:2],
            "exact_PS_sruti": s["triads_exact"][:2],
            "tempered_drawn": d["triads_tempered"],
            "tempered_sruti": s["triads_tempered"],
            "tempered_53edo": e["triads_tempered"],
            "coarse_word": d["m4_proto"]["coarse_word"],
            "tonic_consonances": d["m4_proto"]["tonic_consonance_count"],
        }
    props = {}
    for v in out.values():
        props[v["propriety"]] = props.get(v["propriety"], 0) + 1
    return {"ragas": out, "propriety_histogram": props,
            "cs_counts": {
                "drawn_0.5c": sum(v["cs_drawn"] for v in out.values()),
                "sruti_0.5c": sum(v["cs_sruti"] for v in out.values()),
                "53edo_0.5c": sum(v["cs_53edo"] for v in out.values())}}


def run_verdicts(rows: list[dict]) -> dict:
    return {
        "experiment": EXPERIMENT,
        "date": str(date.today()),
        "source": SOURCE,
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "constants": {"triad_epsilons": TRIAD_EPSILONS, "cs_sweep": CS_SWEEP,
                      "fit_tolerances": FIT_TOLERANCES,
                      "coarse_T_threshold": COARSE_T_THRESHOLD,
                      "orwell_generator": ORWELL_GENERATOR},
        "n_rows": len(rows),
        "H-R1": verdict_hr1(rows),
        "H-R2": verdict_hr2(rows),
        "H-R3": verdict_hr3(rows),
        "H-R4": verdict_hr4(rows),
        "H-R5": verdict_hr5(rows),
        "descriptive": descriptive(rows),
    }


def main() -> dict:
    rows = run_rows()
    summary = run_verdicts(rows)
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    with SUMMARY_PATH.open("w") as fh:
        json.dump(summary, fh, sort_keys=True, indent=1)
        fh.write("\n")
    _print_summary(summary)
    return summary


def _print_summary(s: dict) -> None:
    print(f"{EXPERIMENT}: {s['n_rows']} rows")
    for h in ("H-R1", "H-R2", "H-R3", "H-R4", "H-R5"):
        print(f"  {h}: {s[h]['verdict']}")
    print("  H-R2 fits:", s["H-R2"]["fits"])
    print("  H-R2 housing exact/mod53:", s["H-R2"]["housing_exact_count"],
          s["H-R2"]["housing_mod53_count"])
    print("  H-R4 exact:", s["H-R4"]["sa_exact_PS"], s["H-R4"]["ma_exact_PS"])
    print("  H-R5 sweep:", s["H-R5"]["cs_violations_by_epsilon"])
    print("  propriety histogram:", s["descriptive"]["propriety_histogram"])


if __name__ == "__main__":
    main()
