"""SUBSET-MEL-000 — machine census of the 72 embedded CPS subsets of an
eikosany (input to the SUBSET-MEL-001 / G-013 brainstorm; gate G-022).

Pre-registered in LOG.md 2026-08-18 BEFORE any run. Deterministic, stdlib
only. For each seed eikosany CPS(6,3) enumerate the 72 index-structural
subsets (6 dekanies fix-IN, 6 dekanies fix-OUT, 30 hexanies one-in/one-out,
15 harmonic tetrads two-in, 15 subharmonic tetrads two-out), score each on
the frozen melodic (v0.1.0) and triad (v1.1.0) scorers plus exact-rational
CS, record Johnson-graph adjacency (shared-tone counts), and report THREE
orderings per seed (melodic-first, harmonic-first, CS-first) — deliberately
not one aggregate.

Notation: canonical CPS(n,k) = n seeds choose k; Erv writes k)n.

Run from experiments/lattice/:  python3.12 subsetmel000.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import log2, prod, sqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import melodic as mel  # noqa: E402
import scorer as triad  # noqa: E402
from cseik001 import cs_check, cs_margin_cents  # noqa: E402  (read-only)
from families.cps import cps_scale, wilsonic_recreation_lines  # noqa: E402
from moslat001 import ranks  # noqa: E402  (read-only rank helper)
from scala import to_scala  # noqa: E402
from scorer import canonical_rational_scale  # noqa: E402
from search import balance_bucket  # noqa: E402  (G-002 buckets)

RESULTS = HERE / "results" / "subsetmel000.jsonl"
SUMMARY = HERE / "results" / "subsetmel000_summary.json"
SCL_DIR = HERE / "results" / "scl" / "subsetmel000"
CSEIK_RESULTS = HERE / "results" / "cseik001.jsonl"

CLASSIC = (1, 3, 5, 7, 9, 11)
FLAGSHIP = (1, 7, 9, 11, 15, 29)
TEMPERED_EPSILONS = (2.0, 3.0)
STEP_WORD_EPSILON_CENTS = mel.DEFAULT_GAP_EPSILON_CENTS

PROPRIETY_RANK = {"strictly_proper": 0, "proper": 1, "improper": 2}
ORDERINGS = ("melodic", "harmonic", "cs")
KINDS = ("dekany_in", "dekany_out", "hexany", "tetrad_in", "tetrad_out")
SPICE_TOP_FRACTION = 1 / 3


# ---------------------------------------------------------------------------
# seed selection
# ---------------------------------------------------------------------------


def further_cs_seeds(path: Path, exclude: tuple[tuple[int, ...], ...],
                     n: int) -> tuple[tuple[int, ...], ...]:
    """Top-n CS-EIK-001 winners by cs_margin_cents desc (ties: seeds asc),
    excluding `exclude`. Pre-registered rule."""
    rows = [json.loads(line) for line in path.open()]
    winners = [r for r in rows if r.get("is_cs")]
    winners.sort(key=lambda r: (-r["cs_margin_cents"], tuple(r["seeds"])))
    out = []
    for r in winners:
        seeds = tuple(r["seeds"])
        if seeds in exclude:
            continue
        out.append(seeds)
        if len(out) == n:
            break
    return tuple(out)


def seed_sets() -> tuple[tuple[int, ...], ...]:
    return (CLASSIC, FLAGSHIP) + further_cs_seeds(
        CSEIK_RESULTS, exclude=(FLAGSHIP,), n=3)


# ---------------------------------------------------------------------------
# subset enumeration (index-structural, Johnson graph J(6,3))
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Subset:
    name: str
    kind: str
    fixed_in: tuple[int, ...]
    fixed_out: tuple[int, ...]
    index_sets: tuple[tuple[int, ...], ...]   # 3-subsets of seed VALUES
    tones: tuple[Fraction, ...]               # canonical (octave-reduced)
    cps_seeds: tuple[int, ...]                # standalone CPS recreation
    cps_k: int


def subset_name(kind: str, fixed_in: tuple[int, ...],
                fixed_out: tuple[int, ...]) -> str:
    fi = "-".join(str(v) for v in fixed_in) or "none"
    fo = "-".join(str(v) for v in fixed_out) or "none"
    return f"{kind}[in={fi},out={fo}]"


def _make(seeds, kind, fixed_in, fixed_out) -> Subset:
    triples = [c for c in combinations(seeds, 3)
               if all(v in c for v in fixed_in)
               and not any(v in c for v in fixed_out)]
    tones = canonical_rational_scale(prod(c) for c in triples)
    rest = tuple(v for v in seeds if v not in fixed_in and v not in fixed_out)
    k = 3 - len(fixed_in)
    return Subset(subset_name(kind, fixed_in, fixed_out), kind,
                  tuple(fixed_in), tuple(fixed_out), tuple(triples), tones,
                  rest, k)


def enumerate_subsets(seeds: tuple[int, ...]) -> list[Subset]:
    seeds = tuple(sorted(seeds))
    out: list[Subset] = []
    for x in seeds:
        out.append(_make(seeds, "dekany_in", (x,), ()))
    for x in seeds:
        out.append(_make(seeds, "dekany_out", (), (x,)))
    for x in seeds:
        for y in seeds:
            if x != y:
                out.append(_make(seeds, "hexany", (x,), (y,)))
    for x, y in combinations(seeds, 2):
        out.append(_make(seeds, "tetrad_in", (x, y), ()))
    for x, y in combinations(seeds, 2):
        out.append(_make(seeds, "tetrad_out", (), (x, y)))
    return out


def shared_tone_matrix(subsets: list[Subset]) -> list[list[int]]:
    sets = [set(s.tones) for s in subsets]
    return [[len(a & b) for b in sets] for a in sets]


# ---------------------------------------------------------------------------
# algebraic identities (H-SM1)
# ---------------------------------------------------------------------------


def relative_scale(tones: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    """Scale relative to its lowest canonical tone (the .scl convention)."""
    root = tones[0]
    return tuple(t / root for t in tones)


def transposition_class(tones: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    """Rotation-invariant form: the lexicographically smallest of the N
    modes (scale relative to each of its tones, octave-reduced, sorted).
    Two subsets that are transpositions of each other share this form."""
    modes = []
    for root in tones:
        modes.append(canonical_rational_scale(t / root for t in tones))
    return min(modes)


def is_inversion_pair(a: tuple[Fraction, ...],
                      b: tuple[Fraction, ...]) -> bool:
    """True iff b is a reflection of a (b == K/a for some constant K),
    up to octave equivalence and transposition."""
    if len(a) != len(b):
        return False
    inv = canonical_rational_scale(1 / t for t in a)
    return transposition_class(inv) == transposition_class(b)


# ---------------------------------------------------------------------------
# per-subset measurement
# ---------------------------------------------------------------------------


def step_word(cents: tuple[float, ...],
              eps: float = STEP_WORD_EPSILON_CENTS) -> str:
    """Circular step pattern with gap classes lettered a<b<c... by size
    (same anchored-minimum clustering convention as melodic.py M1)."""
    scale = mel.canonicalize(cents)
    gaps = mel.circular_gaps(scale)
    ordered = sorted(gaps)
    bounds = mel._cluster_sorted(ordered, eps)
    letter_of: dict[float, str] = {}
    for idx, (start, end) in enumerate(bounds):
        for g in ordered[start:end]:
            letter_of.setdefault(g, chr(ord("a") + idx))
    return "".join(letter_of[g] for g in gaps)


def _harm_row(r: triad.ScoreResult, exact: triad.ScoreResult | None = None,
              eps: float | None = None) -> dict:
    row = {"P": r.proportional, "S": r.subcontrary, "G": r.geometric,
           "P_plus_S": r.proportional + r.subcontrary,
           "balance": balance_bucket(r.proportional, r.subcontrary),
           "scorer_version": r.scorer_version, "path": r.path}
    if eps is not None:
        row["epsilon_cents"] = eps
        # receipt fields (post-hoc addition after run 1, labelled in LOG):
        # the frozen scorer's per-triple degeneracy guard can push tempered
        # counts BELOW exact ones; raw counts and the dropped tally show it.
        row["P_raw"] = r.proportional_raw
        row["S_raw"] = r.subcontrary_raw
        row["degenerate_dropped"] = r.degenerate_dropped
    if exact is not None:
        for lab, t, e in (("P", r.proportional, exact.proportional),
                          ("S", r.subcontrary, exact.subcontrary)):
            row[f"overshoot_{lab}"] = t - e
            row[f"survival_{lab}"] = (t / e) if e else None
    return row


def evaluate_subset(seeds: tuple[int, ...], s: Subset) -> dict:
    m = mel.score_melodic_rational(s.tones)
    m1, m2, m3 = m.gap_entropy, m.constant_structure, m.propriety
    viol, spans = cs_check(s.tones)
    exact_h = triad.score(s.tones)
    cents = mel.ratios_to_cents(s.tones)
    tempered = {}
    for eps in TEMPERED_EPSILONS:
        tempered[f"{eps:.1f}"] = _harm_row(
            triad.score_tempered(cents, eps), exact_h, eps)
    n = len(s.tones)
    return {
        "seed_eikosany": list(seeds),
        "name": s.name,
        "kind": s.kind,
        "fixed_in": list(s.fixed_in),
        "fixed_out": list(s.fixed_out),
        "cps_seeds": list(s.cps_seeds),
        "cps_k": s.cps_k,
        "cardinality": n,
        "tones": [f"{t.numerator}/{t.denominator}" for t in s.tones],
        "relative_scale": [f"{t.numerator}/{t.denominator}"
                           for t in relative_scale(s.tones)],
        "transposition_class": [f"{t.numerator}/{t.denominator}"
                                for t in transposition_class(s.tones)],
        "m1_entropy_bits": round(m1.entropy_bits, 6),
        "m1_gap_classes": m1.gap_class_count,
        "gap_classes_per_n": m1.gap_class_count / n,
        "step_word": step_word(cents),
        "m2_cs_violations": m2.violations,
        "m2_is_cs": m2.is_cs,
        "exact_cs_violations": viol,
        "exact_cs": viol == 0,
        "cs_margin_cents": (round(cs_margin_cents(spans), 6)
                            if viol == 0 else None),
        "m3_class": m3.classification,
        "m3_violations": m3.violating_span_pairs,
        "harmonic_exact": _harm_row(exact_h),
        "harmonic_tempered": tempered,
        "melodic_version": mel.MELODIC_VERSION,
        "scorer_version": triad.SCORER_VERSION,
    }


# ---------------------------------------------------------------------------
# orderings and rank statistics
# ---------------------------------------------------------------------------


def melodic_key(r: dict):
    return (r["gap_classes_per_n"], PROPRIETY_RANK[r["m3_class"]],
            r["m3_violations"], r["exact_cs_violations"], r["name"])


def harmonic_key(r: dict):
    t3 = r["harmonic_tempered"]["3.0"]
    ex = r["harmonic_exact"]
    return (-(t3["P"] + t3["S"]), -(ex["P"] + ex["S"]), -t3["P"], r["name"])


def cs_key(r: dict):
    return (r["exact_cs_violations"], r["gap_classes_per_n"],
            PROPRIETY_RANK[r["m3_class"]], r["m3_violations"], r["name"])


_KEYS = {"melodic": melodic_key, "harmonic": harmonic_key, "cs": cs_key}


def order_rows(rows: list[dict], ordering: str) -> list[dict]:
    return sorted(rows, key=_KEYS[ordering])


def _rank_positions(rows: list[dict], ordering: str) -> list[float]:
    """Average-rank position of each row under an ordering (ties = equal
    non-name key)."""
    key = _KEYS[ordering]
    keys = [key(r)[:-1] for r in rows]           # drop the name tiebreak
    distinct = sorted(set(keys))
    return ranks([float(distinct.index(k)) for k in keys])


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = ranks([float(v) for v in x]), ranks([float(v) for v in y])
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0.0 or syy == 0.0:
        return 0.0
    return sxy / sqrt(sxx * syy)


def rank_disagreement(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        # distinct non-name keys per ordering: 1 means the axis is DEGENERATE
        # (all rows tie) and the Spearman below is 0.0 by convention.
        "n_distinct_keys": {o: len({_KEYS[o](r)[:-1] for r in rows})
                            for o in ORDERINGS},
        "spearman_melodic_vs_harmonic": round(spearman(
            _rank_positions(rows, "melodic"),
            _rank_positions(rows, "harmonic")), 6),
        "spearman_cs_vs_harmonic": round(spearman(
            _rank_positions(rows, "cs"),
            _rank_positions(rows, "harmonic")), 6),
        "spearman_melodic_vs_cs": round(spearman(
            _rank_positions(rows, "melodic"),
            _rank_positions(rows, "cs")), 6),
    }


def brief(r: dict) -> dict:
    t3, ex = r["harmonic_tempered"]["3.0"], r["harmonic_exact"]
    return {"name": r["name"], "cps_seeds": r["cps_seeds"], "k": r["cps_k"],
            "gap_classes": r["m1_gap_classes"],
            "gap_classes_per_n": round(r["gap_classes_per_n"], 4),
            "step_word": r["step_word"], "m3": r["m3_class"],
            "m3_violations": r["m3_violations"],
            "exact_cs_violations": r["exact_cs_violations"],
            "cs_margin_cents": r["cs_margin_cents"],
            "P_exact": ex["P"], "S_exact": ex["S"],
            "P3": t3["P"], "S3": t3["S"], "balance3": t3["balance"]}


def spice_rows(rows: list[dict]) -> list[dict]:
    """Improper subsets in the top third of the harmonic-first order within
    their (seed, kind) group."""
    out = []
    for kind in KINDS:
        group = order_rows([r for r in rows if r["kind"] == kind], "harmonic")
        cut = -(-len(group) * SPICE_TOP_FRACTION // 1)  # ceil
        for i, r in enumerate(group):
            if i < cut and r["m3_class"] == "improper":
                out.append({**brief(r), "harmonic_rank_in_kind": i + 1,
                            "kind": kind})
    return out


# ---------------------------------------------------------------------------
# .scl export
# ---------------------------------------------------------------------------


def _scl_name(seeds, r: dict, tag: str) -> str:
    seed_s = "-".join(str(v) for v in seeds)
    fi = "-".join(str(v) for v in r["fixed_in"]) or "none"
    fo = "-".join(str(v) for v in r["fixed_out"]) or "none"
    return f"sm000_{seed_s}_{r['kind']}_in{fi}_out{fo}_{tag}.scl"


def write_scl(seeds, r: dict, tag: str, subset_tones) -> Path:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    t3, ex = r["harmonic_tempered"]["3.0"], r["harmonic_exact"]
    desc = (f"SUBSET-MEL-000 {r['kind']} of eikosany {list(seeds)}: "
            f"{r['m3_class']}, {r['m1_gap_classes']} gap classes/"
            f"{r['cardinality']}, exact CS viol {r['exact_cs_violations']}, "
            f"P/S exact {ex['P']}/{ex['S']}, 3c {t3['P']}/{t3['S']}")
    prov = [f"parent eikosany CPS(6,3) seeds {list(seeds)} (Erv: 3)6)",
            f"subset {r['name']}: fixed in {r['fixed_in']}, "
            f"fixed out {r['fixed_out']}",
            f"top under ordering(s): {tag}",
            f"step word {r['step_word']}",
            "1/1 = the subset's lowest octave-reduced tone as it sits in "
            "the eikosany (a mode of the standalone CPS below)",
            f"standalone: CPS({len(r['cps_seeds'])},{r['cps_k']}) of "
            f"{r['cps_seeds']} transposed by the fixed-in product",
            ] + wilsonic_recreation_lines(r["cps_seeds"], r["cps_k"]) + [
            "or: EulerGenus 6 design with the parent seeds, select the "
            "subset keyboard"]
    path = SCL_DIR / _scl_name(seeds, r, tag)
    path.write_text(to_scala(desc, subset_tones, prov), encoding="ascii")
    return path


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def census(seeds: tuple[int, ...]) -> tuple[list[dict], list[Subset]]:
    subs = enumerate_subsets(seeds)
    eik = cps_scale(seeds, 3)
    if len(eik) != 20:
        raise ValueError(f"{seeds}: not a true 20-tone eikosany ({len(eik)})")
    rows = [evaluate_subset(seeds, s) for s in subs]
    return rows, subs


def _kind_rows(rows, kind):
    return [r for r in rows if r["kind"] == kind]


def seed_summary(seeds, rows, subs) -> tuple[dict, list[Path]]:
    dek = _kind_rows(rows, "dekany_in") + _kind_rows(rows, "dekany_out")
    hexes = _kind_rows(rows, "hexany")
    tet_in, tet_out = _kind_rows(rows, "tetrad_in"), _kind_rows(rows, "tetrad_out")
    by_name = {r["name"]: r for r in rows}
    tones_by_name = {s.name: s.tones for s in subs}

    # H-SM1: IN/OUT symmetry
    sym = []
    for x in seeds:
        a = by_name[subset_name("dekany_in", (x,), ())]
        b = by_name[subset_name("dekany_out", (), (x,))]
        sym.append({
            "x": x,
            "melodic_identical": all(a[k] == b[k] for k in (
                "m1_gap_classes", "m2_cs_violations", "exact_cs_violations",
                "m3_class", "m3_violations")),
            "step_word_reversed": a["step_word"] == b["step_word"][::-1]
            or sorted(a["step_word"]) == sorted(b["step_word"]),
            "PS_swapped_exact": (a["harmonic_exact"]["P"], a["harmonic_exact"]["S"])
            == (b["harmonic_exact"]["S"], b["harmonic_exact"]["P"]),
            "PS_swapped_3c": (a["harmonic_tempered"]["3.0"]["P"],
                              a["harmonic_tempered"]["3.0"]["S"])
            == (b["harmonic_tempered"]["3.0"]["S"],
                b["harmonic_tempered"]["3.0"]["P"]),
            "in": brief(a), "out": brief(b)})
    tet_sym = []
    for x, y in combinations(seeds, 2):
        a = by_name[subset_name("tetrad_in", (x, y), ())]
        b = by_name[subset_name("tetrad_out", (), (x, y))]
        tet_sym.append({"xy": [x, y],
                        "P_in": a["harmonic_exact"]["P"], "S_in": a["harmonic_exact"]["S"],
                        "P_out": b["harmonic_exact"]["P"], "S_out": b["harmonic_exact"]["S"],
                        "swapped": (a["harmonic_exact"]["P"], a["harmonic_exact"]["S"])
                        == (b["harmonic_exact"]["S"], b["harmonic_exact"]["P"]),
                        "harmonic_P_ge_S": a["harmonic_exact"]["P"] >= a["harmonic_exact"]["S"]})
    hex_pairs = []
    for x, y in combinations(seeds, 2):
        a = by_name[subset_name("hexany", (x,), (y,))]
        b = by_name[subset_name("hexany", (y,), (x,))]
        hex_pairs.append({"xy": [x, y], "identical": all(
            a[k] == b[k] for k in (
                "m1_gap_classes", "exact_cs_violations", "m3_class",
                "m3_violations", "harmonic_exact", "harmonic_tempered",
                "transposition_class"))})

    # orderings
    orderings = {}
    for kind_lab, group in (("dekanies", dek), ("hexanies", hexes)):
        orderings[kind_lab] = {
            o: [brief(r) for r in order_rows(group, o)] for o in ORDERINGS}
        orderings[kind_lab]["rank_disagreement"] = rank_disagreement(group)

    # .scl exports: top dekany per ordering (dedup by relative scale), top 2
    # distinct hexanies under melodic-first
    scl_paths = []
    exported: dict[tuple, list[str]] = {}
    for o in ORDERINGS:
        top = order_rows(dek, o)[0]
        exported.setdefault(tuple(top["relative_scale"]), []).append(o)
    chosen_dek = {}
    for o in ORDERINGS:
        top = order_rows(dek, o)[0]
        chosen_dek[tuple(top["relative_scale"])] = top
    for rel, top in chosen_dek.items():
        tag = "+".join(exported[rel])
        scl_paths.append(write_scl(seeds, top, tag, tones_by_name[top["name"]]))
    seen = set()
    n_hex = 0
    for r in order_rows(hexes, "melodic"):
        rel = tuple(r["transposition_class"])
        if rel in seen:
            continue
        seen.add(rel)
        n_hex += 1
        scl_paths.append(write_scl(seeds, r, f"melodic{n_hex}",
                                   tones_by_name[r["name"]]))
        if n_hex == 2:
            break

    def cs_count(group):
        return sum(1 for r in group if r["exact_cs"])

    def m2_cs_count(group):
        return sum(1 for r in group if r["m2_is_cs"])

    def non_improper(group):
        return sum(1 for r in group if r["m3_class"] != "improper")

    def strictly(group):
        return sum(1 for r in group if r["m3_class"] == "strictly_proper")

    surv = {}
    for eps in TEMPERED_EPSILONS:
        key = f"{eps:.1f}"
        surv[key] = {
            "min_overshoot_P_all": min(r["harmonic_tempered"][key]["overshoot_P"] for r in rows),
            "min_overshoot_S_all": min(r["harmonic_tempered"][key]["overshoot_S"] for r in rows),
            "hexanies_exact_survival_1": sum(
                1 for r in hexes if r["harmonic_tempered"][key]["overshoot_P"] == 0
                and r["harmonic_tempered"][key]["overshoot_S"] == 0),
            "dekanies_exact_survival_1": sum(
                1 for r in dek if r["harmonic_tempered"][key]["overshoot_P"] == 0
                and r["harmonic_tempered"][key]["overshoot_S"] == 0),
            "tetrads_exact_survival_1": sum(
                1 for r in tet_in + tet_out
                if r["harmonic_tempered"][key]["overshoot_P"] == 0
                and r["harmonic_tempered"][key]["overshoot_S"] == 0),
        }
    dek_ps = [r["harmonic_exact"]["P"] + r["harmonic_exact"]["S"] for r in dek]
    return {
        "seed_eikosany": list(seeds),
        "n_subsets": len(rows),
        "kind_counts": {k: len(_kind_rows(rows, k)) for k in KINDS},
        "hsm1_dekany_in_out_pairs": sym,
        "hsm1_tetrad_in_out_pairs": tet_sym,
        "hsm1_hexany_transposition_pairs_identical": sum(
            1 for p in hex_pairs if p["identical"]),
        "hsm2_hexanies_exact_cs": cs_count(hexes),
        "hsm2_hexanies_m2_cs_0p5c": m2_cs_count(hexes),
        "hsm2_hexany_cs_failures": [brief(r) for r in hexes if not r["exact_cs"]],
        "hsm3_dekanies_non_improper": non_improper(dek),
        "hsm3_dekanies_strictly_proper": strictly(dek),
        "hsm3_dekany_classes_non_improper": non_improper(_kind_rows(rows, "dekany_in")),
        "hsm3_dekany_classes_strictly_proper": strictly(_kind_rows(rows, "dekany_in")),
        "hsm3_dekanies_exact_cs": cs_count(dek),
        "hsm3_hexanies_non_improper": non_improper(hexes),
        "hsm3_hexanies_strictly_proper": strictly(hexes),
        "hsm4_survival": surv,
        "hsm4_dekany_P_ne_S": sum(
            1 for r in dek if r["harmonic_exact"]["P"] != r["harmonic_exact"]["S"]),
        "hsm4_dekany_exact_PS_mean": sum(dek_ps) / len(dek_ps),
        "hsm4_dekany_exact_PS_range": [min(dek_ps), max(dek_ps)],
        "hsm4_tetrad_in_P_ge_S": sum(1 for t in tet_sym if t["harmonic_P_ge_S"]),
        "hsm4_tetrad_swapped": sum(1 for t in tet_sym if t["swapped"]),
        "orderings": orderings,
        "spice": spice_rows(rows),
        "scl": [p.name for p in scl_paths],
    }, scl_paths


# ---------------------------------------------------------------------------
# POST-HOC lenses (added after run 1; labelled as such in LOG.md — none of the
# pre-registered verdict fields depend on them)
# ---------------------------------------------------------------------------

#: Coincidence-free control seedings for the "generic dekany fingerprint":
#: does CPS(5,2) of arbitrary well-spread odd seeds reproduce the melodic
#: values the CS-winner dekanies all share?
POSTHOC_CONTROL_DEKANY_SEEDS = ((31, 37, 41, 43, 47), (101, 103, 107, 109, 113),
                                (1, 3, 5, 7, 11), (17, 19, 23, 29, 31))


def posthoc(all_rows: list[dict]) -> dict:
    fingerprints: dict[str, int] = {}
    for r in all_rows:
        if r["kind"] != "dekany_in":
            continue
        fp = (f"gaps={r['m1_gap_classes']} entropy={r['m1_entropy_bits']} "
              f"{r['m3_class']}({r['m3_violations']}) "
              f"exactCS={r['exact_cs_violations']}")
        fingerprints[fp] = fingerprints.get(fp, 0) + 1
    controls = []
    for seeds in POSTHOC_CONTROL_DEKANY_SEEDS:
        sc = cps_scale(seeds, 2)
        m = mel.score_melodic_rational(sc)
        v, _ = cs_check(sc)
        controls.append({"seeds": list(seeds),
                         "gap_classes": m.gap_entropy.gap_class_count,
                         "entropy_bits": round(m.gap_entropy.entropy_bits, 6),
                         "m3": m.propriety.classification,
                         "m3_violations": m.propriety.violating_span_pairs,
                         "exact_cs_violations": v})
    neg = []
    for r in all_rows:
        for eps in ("2.0", "3.0"):
            h = r["harmonic_tempered"][eps]
            if h["overshoot_P"] < 0 or h["overshoot_S"] < 0:
                neg.append({"seed": r["seed_eikosany"], "name": r["name"],
                            "eps": eps, "P_exact": r["harmonic_exact"]["P"],
                            "S_exact": r["harmonic_exact"]["S"],
                            "P": h["P"], "S": h["S"], "P_raw": h["P_raw"],
                            "S_raw": h["S_raw"],
                            "degenerate_dropped": h["degenerate_dropped"]})
    dek_min_cs = min(r["exact_cs_violations"] for r in all_rows
                     if r["kind"].startswith("dekany"))
    return {
        "label": "POST-HOC (after run 1)",
        "dekany_class_melodic_fingerprints": fingerprints,
        "control_dekanies": controls,
        "dekany_min_exact_cs_violations_in_census": dek_min_cs,
        "negative_overshoot_rows": len(neg),
        "negative_overshoot_all_have_dropped_gt_0": all(
            n["degenerate_dropped"] > 0 for n in neg),
        "negative_overshoot_all_raw_ge_exact": all(
            n["P_raw"] >= n["P_exact"] and n["S_raw"] >= n["S_exact"]
            for n in neg),
        "negative_overshoot_examples": neg[:8],
    }


def main() -> None:
    seeds_all = seed_sets()
    all_rows: list[dict] = []
    summaries = []
    generic_adj = None
    adj_identical = {}
    for seeds in seeds_all:
        rows, subs = census(seeds)
        adj = shared_tone_matrix(subs)
        if generic_adj is None:
            generic_adj = adj
        adj_identical["-".join(map(str, seeds))] = adj == generic_adj
        summ, _ = seed_summary(seeds, rows, subs)
        summaries.append(summ)
        all_rows.extend(rows)

    RESULTS.parent.mkdir(exist_ok=True)
    with RESULTS.open("w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")

    dek_all = [r for r in all_rows if r["kind"].startswith("dekany")]
    pooled = rank_disagreement(dek_all)
    subset_names = [s.name for s in enumerate_subsets(CLASSIC)]
    summary = {
        "experiment": "SUBSET-MEL-000",
        "seeds": [list(s) for s in seeds_all],
        "seed_rule": "classic, flagship, then top-3 CS-EIK-001 winners by "
                     "cs_margin_cents desc (ties: seeds asc) excluding flagship",
        "rows": len(all_rows),
        "melodic_version": mel.MELODIC_VERSION,
        "scorer_version": triad.SCORER_VERSION,
        "tempered_epsilons": list(TEMPERED_EPSILONS),
        "orderings": {
            "melodic": "gap_classes/N asc, propriety rank asc, M3 violations asc, exact CS violations asc",
            "harmonic": "P+S at 3c desc, exact P+S desc, P at 3c desc",
            "cs": "exact CS violations asc, gap_classes/N asc, propriety rank asc, M3 violations asc",
        },
        "hsm5_pooled_dekanies": pooled,
        "johnson_adjacency": {
            "subset_names": subset_names,
            "shared_tone_matrix": generic_adj,
            "identical_across_seeds": adj_identical,
        },
        "per_seed": summaries,
        "posthoc": posthoc(all_rows),
    }
    SUMMARY.write_text(json.dumps(summary, indent=1))

    # console verdict digest
    print(f"rows: {len(all_rows)} -> {RESULTS}")
    for s in summaries:
        print(f"\nseed {s['seed_eikosany']}")
        print(f"  H-SM1 IN/OUT melodic identical: "
              f"{sum(p['melodic_identical'] for p in s['hsm1_dekany_in_out_pairs'])}/6, "
              f"PS swapped exact: {sum(p['PS_swapped_exact'] for p in s['hsm1_dekany_in_out_pairs'])}/6, "
              f"3c: {sum(p['PS_swapped_3c'] for p in s['hsm1_dekany_in_out_pairs'])}/6; "
              f"hexany pairs identical {s['hsm1_hexany_transposition_pairs_identical']}/15; "
              f"tetrad swapped {s['hsm4_tetrad_swapped']}/15")
        for p in s["hsm1_dekany_in_out_pairs"]:
            b = p["in"]
            print(f"    drop {p['x']:>2}: CPS(5,2){b['cps_seeds']} gaps {b['gap_classes']}/10 "
                  f"{b['m3']}({b['m3_violations']}) exactCS viol {b['exact_cs_violations']} "
                  f"P/S {b['P_exact']}/{b['S_exact']} 3c {b['P3']}/{b['S3']} word {b['step_word']}")
        print(f"  H-SM2 hexanies exact CS {s['hsm2_hexanies_exact_cs']}/30 "
              f"(M2 0.5c {s['hsm2_hexanies_m2_cs_0p5c']}/30); failures: "
              f"{[f['name'] for f in s['hsm2_hexany_cs_failures']]}")
        print(f"  H-SM3 dekanies non-improper {s['hsm3_dekanies_non_improper']}/12 "
              f"(strict {s['hsm3_dekanies_strictly_proper']}), classes "
              f"{s['hsm3_dekany_classes_non_improper']}/6; dekanies exact CS "
              f"{s['hsm3_dekanies_exact_cs']}/12; hexanies non-improper "
              f"{s['hsm3_hexanies_non_improper']}/30 (strict {s['hsm3_hexanies_strictly_proper']})")
        print(f"  H-SM4 survival {json.dumps(s['hsm4_survival'])}; dekany P!=S "
              f"{s['hsm4_dekany_P_ne_S']}/12; dekany exact P+S mean "
              f"{s['hsm4_dekany_exact_PS_mean']:.1f} range {s['hsm4_dekany_exact_PS_range']}; "
              f"tetrad_in P>=S {s['hsm4_tetrad_in_P_ge_S']}/15")
        print(f"  H-SM5 dekanies {s['orderings']['dekanies']['rank_disagreement']}")
        print(f"        hexanies {s['orderings']['hexanies']['rank_disagreement']}")
        for o in ORDERINGS:
            top = s["orderings"]["dekanies"][o][:3]
            print(f"  dekanies {o:<8}: " + " | ".join(
                f"{t['name']} g{t['gap_classes']} {t['m3'][:6]} cs{t['exact_cs_violations']} "
                f"PS3 {t['P3']}+{t['S3']}" for t in top))
        print(f"  spice ({len(s['spice'])}): " + ", ".join(
            f"{x['name']}[PS3 {x['P3']}+{x['S3']}]" for x in s["spice"][:6]))
        print(f"  scl: {s['scl']}")
    print(f"\nH-SM5 pooled dekanies: {pooled}")
    ph = summary["posthoc"]
    print(f"POST-HOC dekany fingerprints: {ph['dekany_class_melodic_fingerprints']}")
    print(f"POST-HOC controls: {ph['control_dekanies']}")
    print(f"POST-HOC negative overshoot rows {ph['negative_overshoot_rows']}, "
          f"all guard-explained: {ph['negative_overshoot_all_have_dropped_gt_0']} "
          f"raw>=exact: {ph['negative_overshoot_all_raw_ge_exact']}")
    print(f"adjacency identical across seeds: {adj_identical}")


if __name__ == "__main__":
    main()
