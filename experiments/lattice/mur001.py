"""MUR-001 — murchana window-regularity census.

Pre-registered in LOG.md ("MUR-001 pre-registration", 2026-08-09) BEFORE
this module was implemented. Quantifies the MOS-LAT-001 "murchana rescue"
at corpus scale: for every (generator, MOS cardinality N) row of the
MOS-LAT-001 noble corpus ∪ MOS-LAT-002 mixed-tail corpus, sweep every
anchor b0 ∈ [−N, N] and record whether the chain segment [b0, b0+N) is
EXACTLY the set selected by its own internal-coordinate hull
(cut-and-project window-representability), plus the frozen melodic triple
(anchor-INVARIANT by the transposition argument — the H-MU0 null rail)
and the frozen anchored triad count P at ε ∈ {2, 3}¢ (anchor-dependent by
convention; descriptive lens only).

Anchor-dependence enters through ι(b) = b·g′ − ⌊b·g⌋ =
b·(g′ − g) + frac(b·g): a line of slope ±|g − g′| plus a sawtooth driven
by the Sturmian floor word of g. The hull/intruder census depends on the
word factor AT the anchor — not on the projected scale's interval
structure, which is a transposition of the anchor-0 scale and therefore
constant over the sweep.

Frozen verifiers imported READ-ONLY: triads scorer v1.1.0 (via moslat001's
re-export of score_tempered) and melodic v0.1.0 (score_melodic).
moslat001.py / moslat002.py are imported read-only for the corpus objects,
exact ℚ(√d) arithmetic, and iota — the comparability contract.

Deterministic: stdlib only, seed 20260725, fixed row order.
Run from experiments/lattice/:  python3.12 mur001.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date
from math import ceil
from pathlib import Path

_LATTICE_DIR = Path(__file__).resolve().parent
if str(_LATTICE_DIR) not in sys.path:
    sys.path.insert(0, str(_LATTICE_DIR))

# Read-only imports; moslat001 puts experiments/triads on sys.path and
# re-exports the frozen scorer entry points.
from moslat001 import (  # noqa: E402
    MAX_CARD,
    MIN_CARD,
    N_PERMUTATIONS,
    SEED,
    SCORER_VERSION,
    canonical_preambles,
    iota,
    noble_from_preamble,
    score_tempered,
)
from moslat002 import enumerate_corpus  # noqa: E402
from melodic import MELODIC_VERSION, score_melodic  # noqa: E402
from families.mos import MAX_LEVEL, zigzag  # noqa: E402

EXPERIMENT = "MUR-001"
JSONL_PATH = _LATTICE_DIR / "results" / "mur001.jsonl"
SUMMARY_PATH = _LATTICE_DIR / "results" / "mur001_summary.json"

#: Triad-scorer epsilons for the descriptive per-anchor P lens (locked).
TRIAD_EPSILONS = (2.0, 3.0)
#: Float fast-path ambiguity band for in-hull tests; ι float error is
#: ≤ ~1e-12 at census magnitudes, comparisons inside the band re-run exact.
FLOAT_GUARD = 1e-9
#: H-MU4 band constants (locked in the pre-registration).
HMU4_T_ZERO_RESCUE_MAX = 2.0
HMU4_T_ALWAYS_RESCUE_MIN = 4.0
HMU4_AUC_THRESHOLD = 0.95


# ---------------------------------------------------------------------------
# corpus: MOS-LAT-001 nobles ∪ MOS-LAT-002 mixed-tail quadratics
# ---------------------------------------------------------------------------


def noble_cf_string(preamble: tuple[int, ...]) -> str:
    return "[0;" + ",".join(map(str, preamble)) + ",(1)*]"


def build_corpus() -> list[dict]:
    """243 generators in fixed enumeration order: 27 nobles (moslat001
    canonical preambles, all-1s tail) then 216 mixed-tail quadratics
    (moslat002 enumerate_corpus). Exact values kept as Q5/Quad objects."""
    gens: list[dict] = []
    for preamble in canonical_preambles():
        g = noble_from_preamble(preamble)
        gens.append({
            "corpus": "noble",
            "cf": noble_cf_string(preamble),
            "preamble": list(preamble),
            "tail": [1],
            "g": g,
            "g_conj": g.conj(),
        })
    mixed, _census = enumerate_corpus()
    for gen in mixed:
        gens.append({
            "corpus": "mixed",
            "cf": gen["cf"],
            "preamble": gen["preamble"],
            "tail": gen["tail"],
            "g": gen["_g"],
            "g_conj": gen["_g_conj"],
        })
    return gens


def periodic_cf_convergents(preamble: tuple[int, ...],
                            tail: tuple[int, ...],
                            max_den: int) -> set[tuple[int, int]]:
    """Convergents (p, q), q <= max_den, of [0; preamble, (tail)*]. All
    digits are >= 1, so the digit string IS the canonical CF and the
    convergents are representation-independent."""
    out: set[tuple[int, int]] = set()
    h_prev, h_prev2 = 0, 1  # h_0 = a0 = 0, h_{-1} = 1
    k_prev, k_prev2 = 1, 0
    digits = list(preamble)
    idx = 0
    for _ in range(200):  # ample: denominators grow at least like Fibonacci
        if idx >= len(digits):
            digits.extend(tail)
        d = digits[idx]
        idx += 1
        h_cur = d * h_prev + h_prev2
        k_cur = d * k_prev + k_prev2
        if k_cur > max_den:
            break
        out.add((h_cur, k_cur))
        h_prev2, h_prev = h_prev, h_cur
        k_prev2, k_prev = k_prev, k_cur
    return out


def is_monotone(g_conj) -> bool:
    """Exact monotonicity of ι in b: steps are g′ and g′ − 1, same sign
    iff g′ ∉ (0, 1). (g′ is a quadratic irrational: never 0 or 1.)"""
    return g_conj.sign() < 0 or (g_conj - 1).sign() > 0


def scan_pad(conj_sep: float, n: int) -> int:
    """Registered drift bound: hull width W <= (n−1)·cs + 1 and
    |ι(b) − ι(endpoint)| >= m·cs − 1 at distance m, so intruders need
    m <= (W+1)/cs <= n + 2/cs. Pad 2n + ceil(2/cs) + 8 strictly exceeds
    the bound."""
    return 2 * n + ceil(2.0 / conj_sep) + 8


# ---------------------------------------------------------------------------
# per-(generator, N) census
# ---------------------------------------------------------------------------


def rows_for(gen: dict) -> list[tuple[int, int, int]]:
    """(N, level, num) at the FIRST zigzag level attaining each distinct
    cardinality N in [MIN_CARD, MAX_CARD] — the moslat001.run_step2_rows /
    moslat002.run_rows recipe."""
    g01 = float(gen["g"])
    first: dict[int, tuple[int, int]] = {}
    for level, (num, den) in enumerate(zigzag(g01)):
        if den not in first:
            first[den] = (level, num)
    return [(den, first[den][0], first[den][1])
            for den in sorted(first) if MIN_CARD <= den <= MAX_CARD]


def anchor_sweep(g, g_conj, n: int) -> dict:
    """Representability census over anchors b0 ∈ [−n, n]. Exact quadratic
    arithmetic for hulls and (inside the float ambiguity band) membership;
    float fast-path outside the band."""
    conj_sep = abs(float(g - g_conj))
    pad = scan_pad(conj_sep, n)
    lo_b, hi_b = -n - pad, 2 * n - 1 + pad
    iotas = {b: iota(b, g, g_conj) for b in range(lo_b, hi_b + 1)}
    fiotas = {b: float(v) for b, v in iotas.items()}

    representable_bits: list[str] = []
    intruder_counts: list[int] = []
    first_failing_anchor = None
    first_failing_intruders: list[int] = []
    for b0 in range(-n, n + 1):
        seg = range(b0, b0 + n)
        hull_lo = min(iotas[b] for b in seg)
        hull_hi = max(iotas[b] for b in seg)
        flo, fhi = float(hull_lo), float(hull_hi)
        intruders = []
        for b in range(b0 - pad, b0 + n + pad):
            if b0 <= b < b0 + n:
                continue
            fv = fiotas[b]
            if fv < flo - FLOAT_GUARD or fv > fhi + FLOAT_GUARD:
                continue
            v = iotas[b]
            if hull_lo <= v and v <= hull_hi:
                intruders.append(b)
        intruder_counts.append(len(intruders))
        representable_bits.append("1" if not intruders else "0")
        if intruders and first_failing_anchor is None:
            first_failing_anchor = b0
            first_failing_intruders = intruders[:12]

    r_set = [b0 for b0, bit in zip(range(-n, n + 1), representable_bits)
             if bit == "1"]
    if len(r_set) >= 2:
        contiguous = r_set == list(range(r_set[0], r_set[-1] + 1))
        gap_values = sorted({b - a for a, b in zip(r_set, r_set[1:])})
    else:
        contiguous = None
        gap_values = []
    return {
        "conj_sep": conj_sep,
        "scan_pad": pad,
        "representable": "".join(representable_bits),
        "intruder_counts": intruder_counts,
        "n_representable": len(r_set),
        "rho": len(r_set) / (2 * n + 1),
        "contiguous": contiguous,
        "interior_gap_values": gap_values,
        "first_failing_anchor": first_failing_anchor,
        "first_failing_intruders": first_failing_intruders,
    }


def anchor_scores(g01: float, n: int) -> dict:
    """Frozen melodic triple and anchored triad P per anchor. Melodic
    invariance across anchors is the H-MU0 null rail."""
    triples = []
    p_by_eps: dict[str, list[int]] = {f"{e:g}": [] for e in TRIAD_EPSILONS}
    for b0 in range(-n, n + 1):
        cents = [((b0 + j) * g01 * 1200.0) % 1200.0 for j in range(n)]
        ms = score_melodic(cents)
        triples.append((
            ms.propriety.classification,
            ms.constant_structure.violations,
            ms.gap_entropy.gap_class_count,
        ))
        for e in TRIAD_EPSILONS:
            p_by_eps[f"{e:g}"].append(
                score_tempered(cents, epsilon_cents=e).proportional)
    anchor0 = triples[n]  # b0 = 0, the plugin's anchor
    return {
        "melodic": {
            "propriety": anchor0[0],
            "cs_violations": anchor0[1],
            "gap_classes": anchor0[2],
        },
        "hmu0_ok": all(t == anchor0 for t in triples),
        "hmu0_distinct_triples": sorted({str(t) for t in triples}),
        "P": p_by_eps,
    }


def census_row(gen: dict, n: int, level: int, num: int,
               convergents: set[tuple[int, int]],
               with_scores: bool = True) -> dict:
    g, g_conj = gen["g"], gen["g_conj"]
    g01 = float(g)
    sweep = anchor_sweep(g, g_conj, n)
    row = {
        "corpus": gen["corpus"],
        "cf": gen["cf"],
        "preamble": gen["preamble"],
        "tail": gen["tail"],
        "g01": g01,
        "cents": g01 * 1200.0,
        "N": n,
        "level": level,
        "num": num,
        "is_cf_convergent": (num, n) in convergents,
        "monotone": is_monotone(g_conj),
        "T": n * sweep["conj_sep"],
        "anchors": [-n, n],
        **sweep,
    }
    if with_scores:
        row.update(anchor_scores(g01, n))
    return row


# ---------------------------------------------------------------------------
# statistics helpers (deterministic, stdlib only)
# ---------------------------------------------------------------------------


def auc_score(positive: list[float], negative: list[float]) -> float:
    """Mann-Whitney AUC of a score separating positive from negative
    (ties count 0.5). Caller guards non-empty classes."""
    total = 0.0
    for p in positive:
        for q in negative:
            if p > q:
                total += 1.0
            elif p == q:
                total += 0.5
    return total / (len(positive) * len(negative))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def hmu3_delta(rhos: list[float], labels: list[bool]) -> float:
    """Δ = mean ρ(non-convergent) − mean ρ(convergent)."""
    conv = [r for r, c in zip(rhos, labels) if c]
    nonconv = [r for r, c in zip(rhos, labels) if not c]
    return mean(nonconv) - mean(conv)


def hmu3_permutation_p(rhos: list[float], labels: list[bool],
                       strata: list[str], observed: float,
                       rng: random.Random,
                       n_perm: int = N_PERMUTATIONS) -> float:
    """One-sided permutation p for Δ, shuffling convergent labels WITHIN
    generator strata. Add-one rule."""
    by_stratum: dict[str, list[int]] = {}
    for idx, s in enumerate(strata):
        by_stratum.setdefault(s, []).append(idx)
    groups = [idx_list for _, idx_list in sorted(by_stratum.items())]
    hits = 0
    threshold = observed - 1e-12
    for _ in range(n_perm):
        perm = list(labels)
        for idx_list in groups:
            vals = [labels[i] for i in idx_list]
            rng.shuffle(vals)
            for i, v in zip(idx_list, vals):
                perm[i] = v
        if hmu3_delta(rhos, perm) >= threshold:
            hits += 1
    return (hits + 1) / (n_perm + 1)


# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------


def run_verdicts(rows: list[dict]) -> dict:
    zero_rescue = [r for r in rows if r["n_representable"] == 0]
    failing = [r for r in rows if "0" in r["representable"]]
    partial = [r for r in rows
               if 0 < r["n_representable"] < 2 * r["N"] + 1]
    hmu0_bad = [r for r in rows if not r["hmu0_ok"]]

    # H-MU2 / H-MU2b
    partial2 = [r for r in partial if r["n_representable"] >= 2]
    noncontig = [r for r in partial2 if r["contiguous"] is False]
    gap_rows = [r for r in rows if r["n_representable"] >= 3]
    hmu2b_bad = [r for r in gap_rows if len(r["interior_gap_values"]) > 3]

    # H-MU3 (non-monotone rows only)
    nm = [r for r in rows if not r["monotone"]]
    rhos = [r["rho"] for r in nm]
    labels = [r["is_cf_convergent"] for r in nm]
    strata = [r["cf"] for r in nm]
    if any(labels) and not all(labels):
        delta = hmu3_delta(rhos, labels)
        rng = random.Random(SEED)
        p = hmu3_permutation_p(rhos, labels, strata, delta, rng)
        hmu3 = {
            "n_rows": len(nm),
            "n_convergent": sum(labels),
            "mean_rho_convergent": mean(
                [r for r, c in zip(rhos, labels) if c]),
            "mean_rho_nonconvergent": mean(
                [r for r, c in zip(rhos, labels) if not c]),
            "delta": delta,
            "permutation_p_one_sided": p,
            "seed": SEED,
            "n_permutations": N_PERMUTATIONS,
            "verdict": "SUPPORTED" if (delta > 0 and p < 0.05)
                       else "NULL",
        }
    else:
        hmu3 = {"n_rows": len(nm), "verdict": "VACUOUS: one stratum empty"}

    # H-MU4
    mono_bad = [r for r in rows
                if r["monotone"] and r["n_representable"] != 2 * r["N"] + 1]
    nm_pos = [r["T"] for r in nm if r["n_representable"] > 0]
    nm_neg = [r["T"] for r in nm if r["n_representable"] == 0]
    auc = auc_score(nm_pos, nm_neg) if nm_pos and nm_neg else None
    band_zero = ([r["T"] for r in zero_rescue] or [0.0])
    band_c1 = max(band_zero) < HMU4_T_ZERO_RESCUE_MAX if zero_rescue else None
    high_t_bad = [r for r in nm
                  if r["T"] > HMU4_T_ALWAYS_RESCUE_MIN
                  and r["n_representable"] == 0]
    hmu4 = {
        "a_monotone_rail_violations": len(mono_bad),
        "b_zero_rescue_rows": len(zero_rescue),
        "b_rescue_possible_rows": len(nm_pos),
        "b_auc_T": auc,
        "c_max_T_zero_rescue": max(band_zero) if zero_rescue else None,
        "c_min_T_rescue_possible_nonmono": min(nm_pos) if nm_pos else None,
        "c_zero_rescue_all_T_below_2": band_c1,
        "c_high_T_no_rescue_violations": len(high_t_bad),
        "verdict_a": "KEPT" if not mono_bad else f"VIOLATED ({len(mono_bad)})",
        "verdict_b": (
            "KEPT" if (auc is not None and auc >= HMU4_AUC_THRESHOLD)
            else ("VACUOUS: a class is empty" if auc is None
                  else f"REFUTED: AUC {auc:.4f} < {HMU4_AUC_THRESHOLD}")),
        "verdict_c": (
            "KEPT" if (band_c1 is True and not high_t_bad)
            else ("VACUOUS: no zero-rescue rows" if band_c1 is None
                  and not high_t_bad else "REFUTED")),
    }

    return {
        "h_mu0": {
            "violations": len(hmu0_bad),
            "violating_rows": [[r["cf"], r["N"]] for r in hmu0_bad][:20],
            "verdict": "KEPT (null rail): melodic triple anchor-invariant "
                       "on every row" if not hmu0_bad else
                       "VIOLATED — implementation bug, run halted",
        },
        "h_mu1": {
            "failing_rows": len(failing),
            "zero_rescue_rows": len(zero_rescue),
            "zero_rescue_examples": [
                [r["cf"], r["N"], round(r["T"], 4)]
                for r in zero_rescue[:12]],
            "verdict": "KEPT: every failing row has a rescuing anchor"
                       if not zero_rescue else
                       f"REFUTED: {len(zero_rescue)} zero-rescue rows "
                       "(as the registered H-MU4(b) tension predicted)",
        },
        "h_mu2": {
            "partial_rows_ge2": len(partial2),
            "non_contiguous": len(noncontig),
            "contiguous_fraction": (
                (len(partial2) - len(noncontig)) / len(partial2)
                if partial2 else None),
            "verdict": (
                "REFUTED (as registered): representable-anchor sets are "
                "not generically contiguous" if noncontig else
                "KEPT (contrary to the registered prediction)"),
        },
        "h_mu2b": {
            "rows_ge3": len(gap_rows),
            "violations": len(hmu2b_bad),
            "violating_examples": [
                [r["cf"], r["N"], r["interior_gap_values"]]
                for r in hmu2b_bad[:12]],
            "verdict": "KEPT: interior anchor-gap values <= 3 everywhere"
                       if not hmu2b_bad else
                       f"REFUTED: {len(hmu2b_bad)} rows exceed 3 gap values",
        },
        "h_mu3": hmu3,
        "h_mu4": hmu4,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def run_rows(with_scores: bool = True) -> list[dict]:
    gens = build_corpus()
    rows: list[dict] = []
    for gen in gens:
        convergents = periodic_cf_convergents(
            tuple(gen["preamble"]), tuple(gen["tail"]), MAX_CARD)
        for n, level, num in rows_for(gen):
            rows.append(census_row(gen, n, level, num, convergents,
                                   with_scores=with_scores))
    return rows


def main() -> dict:
    rows = run_rows(with_scores=True)
    verdicts = run_verdicts(rows)
    p2_varying = sum(
        1 for r in rows if len(set(r["P"]["2"])) > 1)
    summary = {
        "experiment": EXPERIMENT,
        "date": date.today().isoformat(),
        "scorer_version": SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "max_level": MAX_LEVEL,
        "cardinality_range": [MIN_CARD, MAX_CARD],
        "triad_epsilons": list(TRIAD_EPSILONS),
        "anchor_range": "[-N, N]",
        "corpus": {
            "n_generators": len({r["cf"] for r in rows}),
            "n_rows": len(rows),
            "n_rows_noble": sum(1 for r in rows if r["corpus"] == "noble"),
            "n_rows_mixed": sum(1 for r in rows if r["corpus"] == "mixed"),
            "n_rows_monotone": sum(1 for r in rows if r["monotone"]),
        },
        "descriptive_p_lens": {
            "note": "anchored triad P is anchor-dependent BY CONVENTION "
                    "(octave wrap under transposition); no hypothesis",
            "rows_with_varying_P_eps2": p2_varying,
            "fraction": p2_varying / len(rows),
        },
        "verdicts": verdicts,
    }
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def _print_summary(summary: dict) -> None:
    print(f"{EXPERIMENT}  scorer {summary['scorer_version']} "
          f"melodic {summary['melodic_version']}")
    c = summary["corpus"]
    print(f"  corpus: {c['n_generators']} generators, {c['n_rows']} rows "
          f"({c['n_rows_noble']} noble + {c['n_rows_mixed']} mixed), "
          f"{c['n_rows_monotone']} monotone")
    v = summary["verdicts"]
    for name in ("h_mu0", "h_mu1", "h_mu2", "h_mu2b"):
        print(f"  {name}: {v[name]['verdict']}")
    h3 = v["h_mu3"]
    if "delta" in h3:
        print(f"  h_mu3: delta={h3['delta']:+.4f} "
              f"p={h3['permutation_p_one_sided']:.4f} — {h3['verdict']}")
    else:
        print(f"  h_mu3: {h3['verdict']}")
    h4 = v["h_mu4"]
    print(f"  h_mu4: a={h4['verdict_a']}  b={h4['verdict_b']} "
          f"(AUC={h4['b_auc_T']})  c={h4['verdict_c']}")
    print(f"  receipts: {JSONL_PATH}  {SUMMARY_PATH}")


if __name__ == "__main__":
    summary = main()
    _print_summary(summary)
    if summary["verdicts"]["h_mu0"]["violations"]:
        print("H-MU0 VIOLATED — halting for investigation "
              "(pre-registered bug rail)", file=sys.stderr)
        sys.exit(1)
