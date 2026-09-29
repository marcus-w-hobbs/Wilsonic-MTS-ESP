"""BRIDGE-001b — filtered EG4 bridge design: k2 sweep, tone-set minimax,
two-gap objective (LOG.md pre-registration 2026-08-18, written BEFORE this
file existed).

Same object as BRIDGE-001 (bridge001.py): the {1,3,5,7} Euler Genus (8
distinct tones, hexany CPS(4,2) + both tetranies) carried by rank-2
temperament hosts at N in 7..22, Marcus's monotonicity filter first, strict
MOS-window containment with the murchana anchor sweep, frozen triads
v1.1.0 score_tempered at eps = 2c for survival. Three design filters change:

  H-B3  the implicit second comma k2 is SWEPT over the whole kernel box (not
        argmin-error), rows deduped by (mapping, N, val);
  H-B4  a second tuning per row: pure-octave minimax over the 8 EG4 tone
        images instead of the 3 primes (both tunings measured on every row);
  H-B5  the anchored N-note host window is scored on frozen melodic.py and
        its gap-class count is an OBJECTIVE column, never a filter;
  H-B6  hexany_interval_maxerr (translation-invariant) is recorded to test
        whether absolute-error and survival objectives are aligned.

Rail: rows whose (mapping, val) is the argmin completion of some enumerated
comma (bridge001.choose_completion) are tagged rail; under the prime
tuning they must reproduce BRIDGE-001's contained Pareto front exactly.

All enumeration, val/comma/nullspace/HNF machinery, the monotonicity
filter, host/anchor receipt and scoring conventions are IMPORTED from
bridge001.py (read-only reuse, no re-derivation). Frozen scorers are
imported read-only. python3.12 stdlib only; deterministic.

Run from experiments/lattice/:  python3.12 bridge001b.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from datetime import date
from fractions import Fraction
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "triads"))

import bridge001 as br  # noqa: E402  (BRIDGE-001 machinery, reused)
import scorer as triad  # noqa: E402  (frozen v1.1.0, read-only)
from melodic import MELODIC_VERSION, score_melodic  # noqa: E402  (frozen)

RESULTS = HERE / "results" / "bridge001b.jsonl"
SIDECAR = HERE / "results" / "bridge001b_uncontained.jsonl.gz"
SUMMARY = HERE / "results" / "bridge001b_summary.json"
BRIDGE001_SUMMARY = HERE / "results" / "bridge001_summary.json"

PRIME_MONZOS = ((0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
TONE_MONZOS = tuple(t["monzo"] for t in br.TONES)
TUNINGS = ("prime", "tone_set")
EPS_TEMPERED = br.EPSILON_TEMPERED
EPS_SWEEP = br.EPS_BRIDGE
K2_WITNESSES_KEPT = 4

#: Labels only (resolved from comma pairs at load; unnamed mappings are
#: reported by HNF). Verified against the standard 7-limit lists where the
#: pair is unambiguous; a wrong label changes no number.
NAMED_TEMPERAMENTS = {
    "meantone": ("81/80", "126/125"), "dominant": ("81/80", "64/63"),
    "flattone": ("81/80", "525/512"), "mothra": ("81/80", "1029/1024"),
    "godzilla": ("81/80", "49/48"), "injera": ("81/80", "50/49"),
    "mohajira": ("81/80", "6144/6125"), "miracle": ("225/224", "1029/1024"),
    "orwell": ("225/224", "1728/1715"), "magic": ("225/224", "245/243"),
    "negri": ("225/224", "49/48"), "catakleismic": ("225/224", "4375/4374"),
    "garibaldi": ("32805/32768", "5120/5103"), "pajara": ("50/49", "64/63"),
    "superpyth": ("64/63", "245/243"), "porcupine": ("250/243", "64/63"),
    "keemun": ("49/48", "126/125"), "ennealimmal": ("2401/2400", "4375/4374"),
    "valentine": ("126/125", "1029/1024"), "sensi": ("126/125", "245/243"),
    "rodan": ("245/243", "1029/1024"), "lemba": ("50/49", "525/512"),
    "hedgehog": ("50/49", "245/243"), "augene": ("128/125", "64/63"),
    "blackwood": ("256/243", "64/63"), "diminished": ("648/625", "36/35"),
    "hemififths": ("2401/2400", "5120/5103"), "myna": ("126/125", "1728/1715"),
    "shrutar": ("245/243", "2048/2025"), "beatles": ("64/63", "686/675"),
    "hemiwuerschmidt": ("2401/2400", "3136/3125"),
    "octacot": ("245/243", "2401/2400"), "august": ("128/125", "36/35"),
    "doublewide": ("50/49", "875/864"), "semaphore": ("49/48", "1029/1024"),
}


# ------------------------------------------------------------ tuning -----

def minimax_generator_over(mapping, monzos) -> tuple[float, float]:
    """Pure-octave exact minimax of max |T(m) - cents(m)| over `monzos`
    (period fixed at 1200/x); bridge001.minimax_generator generalized to any
    monzo list. Piecewise-linear crossings + per-line zeros; ties -> smaller
    G. Lines with zero slope and zero offset (1/1) are inert."""
    per = 1200.0 / mapping[0][0]
    lines = []
    for m in monzos:
        a = sum(mm * e for mm, e in zip(mapping[0], m)) * per - br.cents_of(m)
        b = float(sum(mm * e for mm, e in zip(mapping[1], m)))
        if a == 0.0 and b == 0.0:
            continue
        lines.append((a, b))
    cands = []
    for (a1, b1), (a2, b2) in combinations(lines, 2):
        for s in (1.0, -1.0):
            if b1 - s * b2 != 0.0:
                cands.append(-(a1 - s * a2) / (b1 - s * b2))
    for a1, b1 in lines:
        if b1 != 0.0:
            cands.append(-a1 / b1)
    if not cands:
        return 0.0, max(abs(a1) for a1, _ in lines)
    best = min(cands, key=lambda g: (max(abs(a1 + b1 * g)
                                         for a1, b1 in lines), g))
    return best, max(abs(a1 + b1 * best) for a1, b1 in lines)


def tone_set_minimax(mapping) -> tuple[float, float]:
    return minimax_generator_over(mapping, TONE_MONZOS)


def tempered_pitch(mapping, g: float, monzo) -> float:
    per = 1200.0 / mapping[0][0]
    return (sum(mm * e for mm, e in zip(mapping[0], monzo)) * per
            + sum(mm * e for mm, e in zip(mapping[1], monzo)) * g)


def tone_errors(mapping, g: float) -> list[float]:
    return [tempered_pitch(mapping, g, t["monzo"]) - t["cents"]
            for t in br.TONES]


def tone_errors_by_product(mapping, g: float) -> dict[int, float]:
    return {t["product"]: e for t, e in zip(br.TONES, tone_errors(mapping, g))}


def chain_span(mapping) -> int:
    b = [sum(mm * e for mm, e in zip(mapping[1], t["monzo"]))
         for t in br.TONES]
    return max(b) - min(b) + 1


def hexany_interval_maxerr(errs_by_product: dict[int, float]) -> float:
    """Max |e_i - e_j| over the 15 pairwise hexany-image intervals: the
    translation-invariant error the frozen scorer's mean test actually
    sees (H-B6)."""
    e = [errs_by_product[p] for p in br.HEXANY_PRODUCTS]
    return max(abs(a - b) for a, b in combinations(e, 2))


# ---------------------------------------- POST-HOC: triad-identity lens ---
# Added after the first run (LOG 2026-08-18 results): the pre-registered
# survival test (image counts >= base counts) is fooled by grossly detuned
# images whose ACCIDENTAL near-arithmetic triples out-count the hexany's own
# eight faces (rows with 64-155c tone errors reached P = 5-7 at eps = 2 and
# entered the pre-registered fronts). This lens asks the sharper question:
# do the base's OWN triads survive? It uses only frozen-scorer public
# functions (canonical_rational_scale, classify_rational_triple,
# classify_cents_triple) and mirrors score_rational_anchored's window rule.
# It changes no pre-registered field.

def _shift_into_open(pc: Fraction, lo: Fraction, hi: Fraction):
    r = pc
    while r <= lo:
        r *= 2
    while r >= hi:
        r /= 2
    return r if lo < r < hi else None


def base_triads(products) -> list:
    """The base subset's own labelled triads as (label, (prod_a, oct_a),
    (prod_b, 0), (prod_c, oct_c)) under the anchored convention."""
    pcs = {p: br.reduce_rational(Fraction(p)) for p in products}
    out = []
    for pb, b in sorted(pcs.items(), key=lambda kv: kv[1]):
        for pa, apc in pcs.items():
            a = _shift_into_open(apc, b / 2, b)
            if a is None:
                continue
            for pc_, cpc in pcs.items():
                c = _shift_into_open(cpc, b, 2 * b)
                if c is None or c / a > triad.DEFAULT_MAX_SPAN:
                    continue
                label = triad.classify_rational_triple(a, b, c)
                if label in (triad.PROPORTIONAL, triad.SUBCONTRARY):
                    oa = (a / apc).numerator.bit_length() - 1 \
                        if a >= apc else -((apc / a).numerator.bit_length() - 1)
                    oc = (c / cpc).numerator.bit_length() - 1 \
                        if c >= cpc else -((cpc / c).numerator.bit_length() - 1)
                    out.append((label, (pa, oa), (pb, 0), (pc_, oc)))
    return out


HEXANY_TRIADS = base_triads(br.HEXANY_PRODUCTS)


def identity_survival(temp_by_prod: dict, eps: float,
                      triads=HEXANY_TRIADS) -> tuple[int, int]:
    """How many of the base's own (P, S) triads still carry their label in
    the tempered image at eps (same triple, same octave placement)."""
    p = s = 0
    for label, (pa, oa), (pb, ob), (pc_, oc) in triads:
        a = temp_by_prod[pa] + 1200.0 * oa
        b = temp_by_prod[pb] + 1200.0 * ob
        c = temp_by_prod[pc_] + 1200.0 * oc
        if not a < b < c:
            continue
        labels = triad.classify_cents_triple(a, b, c, eps)
        if label in labels:
            if label == triad.PROPORTIONAL:
                p += 1
            else:
                s += 1
    return p, s


# ------------------------------------------------------------- sweep -----

def sweep_temperaments(c, kernel_box, cache: dict) -> dict:
    """H-B3: every rank-2 temperament sat<c, k2> for k2 in the kernel box
    independent of c. Returns {mapping: sorted list of k2 witnesses}."""
    out: dict = {}
    for k2 in kernel_box:
        minors = [c[i] * k2[j] - c[j] * k2[i]
                  for i, j in combinations(range(4), 2)]
        if not any(minors):
            continue
        key = (c, k2)
        if key not in cache:
            basis = br.nullspace_saturated([c, k2])
            cache[key] = (None if len(basis) != 2
                          else br.hnf_mapping(basis))
        mapping = cache[key]
        if mapping is None:
            continue
        out.setdefault(mapping, []).append(k2)
    return {m: sorted(ks, key=lambda k: (br.tenney_log2(k), k))
            for m, ks in out.items()}


def resolve_names() -> dict:
    names = {}
    for name, (a, b) in sorted(NAMED_TEMPERAMENTS.items()):
        mapping = br.hnf_mapping(br.nullspace_saturated(
            [br.monzo_of(Fraction(a)), br.monzo_of(Fraction(b))]))
        names.setdefault(mapping, name)
    return names


# ------------------------------------------------------- host window -----

def window_cents(per: float, g: float, n: int, anchor: int, x: int) -> list:
    """The anchored N-note host window (copied with attribution from
    bridge001.host_receipt's `notes`): npp = n // x generator steps from
    `anchor`, replicated over the x periods."""
    npp = n // x
    return sorted((bi * g) % per + k * per
                  for bi in range(anchor, anchor + npp) for k in range(x))


def melodic_receipt(notes: list) -> dict:
    """H-B5: frozen melodic.py (v0.1.0 defaults) on the host window."""
    ms = score_melodic(notes)
    return {"gap_classes": ms.gap_entropy.gap_class_count,
            "gap_entropy_bits": round(ms.gap_entropy.entropy_bits, 6),
            "gap_sizes": [[round(lo, 4), round(hi, 4), cnt]
                          for lo, hi, cnt in ms.gap_entropy.gap_classes],
            "is_cs": ms.constant_structure.is_cs,
            "cs_violations": ms.constant_structure.violations,
            "propriety": ms.propriety.classification,
            "propriety_violations": ms.propriety.violating_span_pairs,
            "n_notes": len(ms.scale)}


# --------------------------------------------------------- measuring -----

def _subset(products, deg_by_prod, temp_by_prod, n, base) -> dict:
    degs = [deg_by_prod[p] % n for p in products]
    img = triad.score_tempered([temp_by_prod[p] for p in products],
                               epsilon_cents=EPS_TEMPERED)
    return {"P": img.proportional, "S": img.subcontrary, "G": img.geometric,
            "injective_addressing": len(set(degs)) == len(degs),
            "survive": (img.proportional >= base.proportional
                        and img.subcontrary >= base.subcontrary)}


def measure_tuning(mapping, v, n, mono, g, objective_err, contained,
                   anchor, bases) -> dict:
    """One tuning's receipt (mirrors bridge001.measure_candidate's fields,
    same formulas, compact schema)."""
    tempered, errors, deg_by_prod, temp_by_prod = [], [], {}, {}
    for t, d in zip(br.TONES, mono["degrees"]):
        pitch = tempered_pitch(mapping, g, t["monzo"])
        tempered.append(pitch)
        errors.append(pitch - t["cents"])
        deg_by_prod[t["product"]] = d
        temp_by_prod[t["product"]] = pitch
    max_err = max(abs(e) for e in errors)
    n_coll = len(mono["collisions"])
    regimes = ["over-budget" if max_err >= eps else
               ("tempered-merge" if n_coll else "faithful")
               for eps in EPS_SWEEP]
    img = triad.score_tempered(tempered, epsilon_cents=EPS_TEMPERED)
    subsets = {name: _subset(prods, deg_by_prod, temp_by_prod, n, bases[name])
               for name, prods in br.SUBSETS.items()}
    host = br.host_receipt(mapping, g, n, mono["degrees"])
    hex_pitches = [temp_by_prod[p] for p in br.HEXANY_PRODUCTS]
    base = bases["hexany"]
    recovery = None
    for eps in EPS_SWEEP:
        img2 = triad.score_tempered(hex_pitches, epsilon_cents=eps)
        if (img2.proportional >= base.proportional
                and img2.subcontrary >= base.subcontrary):
            recovery = eps
            break
    id_p, id_s = identity_survival(temp_by_prod, EPS_TEMPERED)
    id_recovery = next((eps for eps in EPS_SWEEP
                        if identity_survival(temp_by_prod, eps) == (6, 6)),
                       None)
    per = 1200.0 / mapping[0][0]
    rec = {
        "generator_cents_raw": g, "generator_cents": g % per,
        "objective_error_cents": round(objective_err, 6),
        "tone_errors": [round(e, 6) for e in errors],
        "max_error_cents": round(max_err, 6),
        "mean_error_cents": round(sum(abs(e) for e in errors) / len(errors), 6),
        "hexany_interval_maxerr": round(hexany_interval_maxerr(
            {p: e for p, e in zip((t["product"] for t in br.TONES), errors)}),
            6),
        "image_PSG": [img.proportional, img.subcontrary, img.geometric],
        "hexany": subsets["hexany"], "tetrany_1": subsets["tetrany_1"],
        "tetrany_3": subsets["tetrany_3"],
        "min_faithful_eps": next((e for e, r in zip(EPS_SWEEP, regimes)
                                  if r == "faithful"), None),
        "hexany_full_recovery_eps": recovery,
        "posthoc_identity_P": id_p, "posthoc_identity_S": id_s,
        "posthoc_identity_full_recovery_eps": id_recovery,
        "host_step_classes": host["host_step_classes"],
        "degrees_match_host_ranks": host["degrees_match_host_ranks"],
        "h_b2_pass": (n_coll == 0 and contained and max_err < 15.0
                      and subsets["hexany"]["survive"]),
        "melodic": None,
    }
    if contained:
        notes = window_cents(per, g, n, anchor, mapping[0][0])
        rec["melodic"] = melodic_receipt(notes)
    return rec


_BASES: dict = {}


def bases() -> dict:
    if not _BASES:
        _BASES.update(br.subset_bases())
        hb = _BASES["hexany"]
        assert (hb.proportional, hb.subcontrary) == (6, 6)
    return _BASES


def measure_both(mapping, v, n, mono=None) -> dict:
    """Row for one (mapping, val, N): shared addressing/containment fields
    plus one receipt per tuning objective."""
    mono = mono or br.monotonicity(v)
    assert mono["monotone"]
    combo = br.val_combo(v, mapping)
    assert combo is not None, "val must factor through the temperament"
    g_prime, err_prime = br.minimax_generator(mapping)
    g_tone, err_tone = tone_set_minimax(mapping)
    host = br.host_receipt(mapping, g_prime, n, mono["degrees"])
    merges = []
    for col in mono["collisions"]:
        cm = tuple(col["comma_monzo"])
        gen_steps = sum(mm * e for mm, e in zip(mapping[1], cm))
        per_steps = sum(mm * e for mm, e in zip(mapping[0], cm))
        merges.append({"tones": col["tones"], "degree": col["degree"],
                       "comma": col["comma"],
                       "pitch_merged": gen_steps == 0
                       and per_steps % mapping[0][0] == 0})
    row = {
        "N": n, "val": list(v), "patent_val": list(br.patent_val(n)),
        "mapping": [list(r) for r in mapping],
        "periods_per_octave": mapping[0][0], "alpha": combo[0],
        "generator_degree_beta": combo[1],
        "degrees": mono["degrees"],
        "collisions": merges, "collision_count": len(merges),
        "pitch_merge_count": sum(m["pitch_merged"] for m in merges),
        "injective": not merges,
        "contained": host["contained"], "chain_span": host["chain_span"],
        "chain_positions": host["chain_positions"],
        "notes_per_period_class": host["notes_per_period_class"],
        "anchor_interval": host["anchor_interval"],
        "anchor_used": host["anchor_used"],
        "tunings": {
            "prime": measure_tuning(mapping, v, n, mono, g_prime, err_prime,
                                    host["contained"], host["anchor_used"],
                                    bases()),
            "tone_set": measure_tuning(mapping, v, n, mono, g_tone, err_tone,
                                       host["contained"], host["anchor_used"],
                                       bases())},
    }
    return row


# ------------------------------------------------------------ fronts -----

def dominates(a, b, pkey: str = "hexany_P") -> bool:
    ge = (a[pkey] >= b[pkey]
          and a["collision_count"] <= b["collision_count"]
          and a["max_error_cents"] <= b["max_error_cents"])
    strict = (a[pkey] > b[pkey]
              or a["collision_count"] < b["collision_count"]
              or a["max_error_cents"] < b["max_error_cents"])
    return ge and strict


def front_entry(row, tuning: str) -> dict:
    t = row["tunings"][tuning]
    return {"name": row["name"], "N": row["N"], "val": row["val"],
            "mapping": row["mapping"], "kernel_commas": row["kernel_commas"],
            "rail_commas": row["rail_commas"], "rail_k2": row["rail_k2"],
            "generator_cents": t["generator_cents"],
            "objective_error_cents": t["objective_error_cents"],
            "max_error_cents": t["max_error_cents"],
            "hexany_interval_maxerr": t["hexany_interval_maxerr"],
            "collision_count": row["collision_count"],
            "hexany_P": t["hexany"]["P"], "hexany_S": t["hexany"]["S"],
            "hexany_full_recovery_eps": t["hexany_full_recovery_eps"],
            "posthoc_identity_P": t["posthoc_identity_P"],
            "posthoc_identity_S": t["posthoc_identity_S"],
            "posthoc_identity_full_recovery_eps":
                t["posthoc_identity_full_recovery_eps"],
            "host_step_classes": t["host_step_classes"],
            "gap_classes": t["melodic"]["gap_classes"] if t["melodic"] else None,
            "propriety": t["melodic"]["propriety"] if t["melodic"] else None,
            "is_cs": t["melodic"]["is_cs"] if t["melodic"] else None,
            "anchor_interval": row["anchor_interval"],
            "h_b2_pass": t["h_b2_pass"]}


def pareto(rows, tuning: str, rail_only: bool = False,
           max_error: float | None = None, pkey: str = "hexany_P") -> list:
    """Pre-registered front: contained rows, (P up, collisions down, max tone
    error down). POST-HOC variants (labelled in the summary): max_error caps
    the front to the <= 15c epsilon_bridge regime; pkey = 'posthoc_identity_P'
    swaps the count-based P for the triad-identity lens."""
    cands = [front_entry(r, tuning) for r in rows
             if r["contained"] and (r["rail_commas"] or not rail_only)
             and (max_error is None
                  or r["tunings"][tuning]["max_error_cents"] < max_error)]
    return sorted((a for a in cands
                   if not any(dominates(b, a, pkey) for b in cands)),
                  key=lambda r: (r["max_error_cents"], r["N"], tuple(r["val"])))


def rail_matches_bridge001(rail_front: list, ref_front: list) -> dict:
    """Bit-for-bit comparison of the rail front with BRIDGE-001's summary
    front on the fields BRIDGE-001 recorded."""
    def key(r):
        return (r["N"], tuple(r["val"]))
    ref = {key(r): r for r in ref_front}
    got = {key(r): r for r in rail_front}
    diffs = []
    if set(ref) != set(got):
        diffs.append({"row_sets": {"bridge001": sorted(map(str, ref)),
                                   "rail": sorted(map(str, got))}})
    for k in sorted(set(ref) & set(got)):
        a, b = ref[k], got[k]
        checks = {
            "k2": (a["k2"], b["rail_k2"]),
            "mapping": (a["mapping"], b["mapping"]),
            "generator_cents": (a["generator_cents"], b["generator_cents"]),
            "max_error_cents": (a["max_error_cents"], b["max_error_cents"]),
            "collision_count": (a["collision_count"], b["collision_count"]),
            "hexany_image_P": (a["hexany_image_P"], b["hexany_P"]),
            "posthoc_hexany_full_recovery_eps": (
                a["posthoc_hexany_full_recovery_eps"],
                b["hexany_full_recovery_eps"]),
            "comma_aliases": (a["comma_aliases"], b["rail_commas"]),
        }
        for field, (x, y) in checks.items():
            if x != y:
                diffs.append({"row": list(k), "field": field,
                              "bridge001": x, "rail": y})
    return {"reproduced": not diffs, "diffs": diffs,
            "rows_compared": len(set(ref) & set(got))}


# ------------------------------------------------------------ driver -----

def run() -> tuple[list, dict]:
    commas = br.enumerate_commas()
    names = resolve_names()
    comma_str = {c: br.frac_str(br.ratio_of(c)) for c in commas}
    mono_cache: dict = {}
    box_cache: dict = {}
    map_cache: dict = {}
    temper_cache: dict = {}
    # (mapping, n, v) -> accumulator
    acc: dict = {}
    order: list = []
    n_pairs = n_rejected = 0
    for n in br.N_RANGE:
        for v in br.vals_for(n):
            live = [c for c in commas if br.vdot(v, c) == 0]
            if not live:
                continue
            if v not in mono_cache:
                mono_cache[v] = br.monotonicity(v)
            mono = mono_cache[v]
            n_pairs += len(live)
            if not mono["monotone"]:
                n_rejected += len(live)
                continue
            if v not in box_cache:
                box_cache[v] = br.kernel_box_for(v)
            box = box_cache[v]
            for c in live:
                rail = br.choose_completion(c, v, box, temper_cache)
                rail_map = rail[1] if rail else None
                rail_k2 = rail[0] if rail else None
                for mapping, k2s in sweep_temperaments(c, box, map_cache).items():
                    key = (mapping, n, v)
                    if key not in acc:
                        acc[key] = {"witnesses": set(), "rail_commas": [],
                                    "rail_k2": None, "mono": mono}
                        order.append(key)
                    a = acc[key]
                    a["witnesses"].update(k2s)
                    if rail_map == mapping:
                        a["rail_commas"].append(comma_str[c])
                        if a["rail_k2"] is None:
                            a["rail_k2"] = br.frac_str(br.ratio_of(rail_k2))
    rows = []
    for key in order:
        mapping, n, v = key
        a = acc[key]
        row = measure_both(mapping, v, n, a["mono"])
        wit = sorted(a["witnesses"], key=lambda k: (br.tenney_log2(k), k))
        row.update({
            "name": names.get(mapping),
            "kernel_commas": [comma_str[c] for c in commas
                              if all(br.vdot(r, c) == 0 for r in mapping)],
            "k2_witness_count": len(wit),
            "k2_witnesses": [br.frac_str(br.ratio_of(k))
                             for k in wit[:K2_WITNESSES_KEPT]],
            "rail_commas": a["rail_commas"], "rail_k2": a["rail_k2"],
        })
        rows.append(row)
    meta = {"commas": len(commas), "pairs_total": n_pairs,
            "rejected_monotonicity": n_rejected,
            "monotone_pairs": n_pairs - n_rejected,
            "distinct_rows": len(rows)}
    return rows, meta


def summarize(rows: list, meta: dict) -> dict:
    ref = json.loads(BRIDGE001_SUMMARY.read_text())
    rail_front = pareto(rows, "prime", rail_only=True)
    rail_check = rail_matches_bridge001(rail_front, ref["pareto_front"])
    fronts = {t: pareto(rows, t) for t in TUNINGS}
    contained = [r for r in rows if r["contained"]]
    named_rows = sorted(
        (front_entry(r, t) | {"tuning": t}
         for r in rows if r["name"] for t in TUNINGS),
        key=lambda e: (e["name"], e["tuning"], e["N"], tuple(e["val"])))

    def max_p(rs, t):
        return max((r["tunings"][t]["hexany"]["P"] for r in rs), default=None)

    gap_table = {}
    for t in TUNINGS:
        gap_table[t] = {}
        for r in contained:
            gc = r["tunings"][t]["melodic"]["gap_classes"]
            p = r["tunings"][t]["hexany"]["P"]
            cell = gap_table[t].setdefault(str(gc), {"rows": 0, "max_P": 0,
                                                     "proper_or_strict": 0})
            cell["rows"] += 1
            cell["max_P"] = max(cell["max_P"], p)
            if r["tunings"][t]["melodic"]["propriety"] != "improper":
                cell["proper_or_strict"] += 1
    revived = {t: [front_entry(r, t) for r in rows if r["tunings"][t]["h_b2_pass"]]
               for t in TUNINGS}
    non_225 = {t: [e for e in fronts[t] if "225/224" not in e["kernel_commas"]]
               for t in TUNINGS}
    b1_front_keys = {(r["N"], tuple(r["val"]),
                      tuple(tuple(m) for m in r["mapping"]))
                     for r in ref["pareto_front"]}
    b1_rows = [r for r in rows
               if (r["N"], tuple(r["val"]),
                   tuple(tuple(m) for m in r["mapping"])) in b1_front_keys]
    posthoc = {
        "note": "POST-HOC lenses added after the first run (LOG 2026-08-18 "
                "results): (a) in-budget fronts restrict to max tone error "
                "< 15c (the epsilon_bridge regime, i.e. not over-budget); "
                "(b) identity fronts replace the count-based hexany P by "
                "posthoc_identity_P (the hexany's OWN triads surviving). "
                "Neither changes any pre-registered field or front.",
        "inbudget_fronts": {t: pareto(rows, t, max_error=15.0) for t in TUNINGS},
        "identity_fronts": {t: pareto(rows, t, pkey="posthoc_identity_P")
                            for t in TUNINGS},
        "identity_inbudget_fronts": {
            t: pareto(rows, t, max_error=15.0, pkey="posthoc_identity_P")
            for t in TUNINGS},
        "identity_full_at_eps2_contained": {
            t: [front_entry(r, t) for r in contained
                if r["tunings"][t]["posthoc_identity_P"] == 6
                and r["tunings"][t]["posthoc_identity_S"] == 6]
            for t in TUNINGS},
        "count_vs_identity_disagreements_contained": {
            t: sum(1 for r in contained
                   if (r["tunings"][t]["hexany"]["survive"])
                   != (r["tunings"][t]["posthoc_identity_P"] == 6
                       and r["tunings"][t]["posthoc_identity_S"] == 6))
            for t in TUNINGS},
        "hexany_base_triads": [[lab, list(a), list(b), list(c)]
                               for lab, a, b, c in HEXANY_TRIADS],
    }
    h_b6 = {
        "front_rows": [{
            "name": r["name"], "N": r["N"], "val": r["val"],
            **{f"{t}_{f}": r["tunings"][t][f] for t in TUNINGS
               for f in ("max_error_cents", "hexany_interval_maxerr",
                         "hexany_full_recovery_eps")},
            **{f"{t}_hexany_P": r["tunings"][t]["hexany"]["P"] for t in TUNINGS},
            **{f"{t}_identity_P": r["tunings"][t]["posthoc_identity_P"]
               for t in TUNINGS},
            **{f"{t}_identity_recovery":
               r["tunings"][t]["posthoc_identity_full_recovery_eps"]
               for t in TUNINGS}}
            for r in b1_rows],
        "tone_set_lowers_max_error_everywhere": all(
            r["tunings"]["tone_set"]["max_error_cents"]
            <= r["tunings"]["prime"]["max_error_cents"] + 1e-9 for r in rows),
        "contained_max_P": {t: max_p(contained, t) for t in TUNINGS},
        "some_bridge001_front_row_loses_P": any(
            r["tunings"]["tone_set"]["hexany"]["P"]
            < r["tunings"]["prime"]["hexany"]["P"] for r in b1_rows),
    }
    return {
        "experiment": "BRIDGE-001b", "date": str(date.today()),
        "scorer_version": triad.SCORER_VERSION,
        "melodic_version": MELODIC_VERSION,
        "epsilon_tempered": EPS_TEMPERED,
        "enumeration": meta | {"contained_rows": len(contained),
                               "rail_rows": sum(1 for r in rows if r["rail_commas"]),
                               "named_rows": sum(1 for r in rows if r["name"])},
        "rail": {"front": rail_front, "bridge001_comparison": rail_check},
        "fronts": fronts,
        "h_b3": {"prime_front_equals_rail_front":
                 [(e["N"], e["val"]) for e in fronts["prime"]]
                 == [(e["N"], e["val"]) for e in rail_front],
                 "non_225_224_front_rows": non_225["prime"],
                 "contained_max_hexany_P": max_p(contained, "prime"),
                 "named_contained": [e for e in named_rows
                                     if e["tuning"] == "prime"
                                     and (e["N"], tuple(e["val"])) in
                                     {(r["N"], tuple(r["val"])) for r in contained}]},
        "h_b4": {"front": fronts["tone_set"],
                 "front_flipped": [(e["N"], e["val"]) for e in fronts["prime"]]
                 != [(e["N"], e["val"]) for e in fronts["tone_set"]],
                 "non_225_224_front_rows": non_225["tone_set"],
                 "h_b2_revived_rows": revived["tone_set"],
                 "h_b2_prime_pass_rows": revived["prime"],
                 "named_rows_both_tunings": named_rows},
        "h_b5": {"gap_class_table": gap_table,
                 "front_gap_classes": {t: [(e["name"], e["N"], e["gap_classes"],
                                            e["propriety"], e["is_cs"], e["hexany_P"])
                                           for e in fronts[t]] for t in TUNINGS}},
        "h_b6": h_b6,
        "posthoc": posthoc,
        "bridge000_standard": ref["bridge000_standard"],
    }


COMPACT_TUNING_FIELDS = (
    "generator_cents", "objective_error_cents", "max_error_cents",
    "mean_error_cents", "hexany_interval_maxerr", "image_PSG",
    "min_faithful_eps", "hexany_full_recovery_eps", "posthoc_identity_P",
    "posthoc_identity_S", "posthoc_identity_full_recovery_eps", "h_b2_pass")


def receipt_row(row: dict) -> dict:
    """Receipt schema: FULL row for contained or rail rows (the bridge
    candidates and the BRIDGE-001-comparable set) -> bridge001b.jsonl;
    COMPACT row otherwise (uncontained, non-rail: no bridge can live there)
    -> the gzipped sidecar. The full 33,711-row dump was 77 MB; this keeps
    the repo receipt at BRIDGE-001 scale while every summary field stays
    derivable from the two files together."""
    if row["contained"] or row["rail_commas"]:
        return {"schema": "full", **row}
    return {
        "schema": "compact",
        **{k: row[k] for k in ("N", "val", "mapping", "name",
                                "periods_per_octave", "kernel_commas",
                                "k2_witness_count", "k2_witnesses",
                                "rail_commas", "collision_count",
                                "pitch_merge_count", "injective", "contained",
                                "chain_span", "notes_per_period_class")},
        "tunings": {t: {**{k: row["tunings"][t][k]
                           for k in COMPACT_TUNING_FIELDS},
                        "hexany": row["tunings"][t]["hexany"]}
                    for t in TUNINGS},
    }


def main() -> None:
    rows, meta = run()
    RESULTS.parent.mkdir(exist_ok=True)
    n_full = n_compact = 0
    import io
    with RESULTS.open("w") as fh, gzip.GzipFile(
            SIDECAR, "wb", mtime=0) as gz, io.TextIOWrapper(gz, "utf-8") as side:
        for row in rows:
            rec = receipt_row(row)
            line = json.dumps(rec, separators=(",", ":")) + "\n"
            if rec["schema"] == "full":
                fh.write(line)
                n_full += 1
            else:
                side.write(line)
                n_compact += 1
    summary = summarize(rows, meta)
    SUMMARY.write_text(json.dumps(summary, indent=1))
    sha = hashlib.sha256(RESULTS.read_bytes()).hexdigest()
    summary["receipts"] = {
        "bridge001b_jsonl_rows_full": n_full,
        "bridge001b_uncontained_sidecar_rows_compact": n_compact,
        "sha256_bridge001b_jsonl": sha,
        "sha256_sidecar_gz": hashlib.sha256(SIDECAR.read_bytes()).hexdigest()}
    SUMMARY.write_text(json.dumps(summary, indent=1))
    print(f"rows: {meta}  contained={summary['enumeration']['contained_rows']}"
          f"  full rows={n_full} compact sidecar rows={n_compact}"
          f"  jsonl sha256={sha[:16]}…")
    rc = summary["rail"]["bridge001_comparison"]
    print(f"rail reproduced BRIDGE-001 front: {rc['reproduced']} "
          f"({rc['rows_compared']} rows; diffs={rc['diffs']})")
    for t in TUNINGS:
        print(f"-- {t} front --")
        for e in summary["fronts"][t]:
            print(f"  {e['name'] or e['mapping']} N={e['N']} val={e['val']} "
                  f"g={e['generator_cents']:.4f} err={e['max_error_cents']} "
                  f"P={e['hexany_P']} coll={e['collision_count']} "
                  f"gaps={e['gap_classes']} {e['propriety']} "
                  f"recov={e['hexany_full_recovery_eps']} "
                  f"kernel={e['kernel_commas'][:4]}")
    print("H-B3 prime front == rail front:",
          summary["h_b3"]["prime_front_equals_rail_front"])
    print("H-B4 flipped:", summary["h_b4"]["front_flipped"],
          " revived rows:", len(summary["h_b4"]["h_b2_revived_rows"]))
    print("H-B6:", {k: v for k, v in summary["h_b6"].items()
                   if k != "front_rows"})
    for r in summary["h_b6"]["front_rows"]:
        print("  ", r)
    print("H-B5 gap table:", summary["h_b5"]["gap_class_table"])
    for lens in ("inbudget_fronts", "identity_inbudget_fronts"):
        for t in TUNINGS:
            print(f"-- POST-HOC {lens} {t} --")
            for e in summary["posthoc"][lens][t]:
                print(f"  {e['name'] or e['mapping']} N={e['N']} val={e['val']} "
                      f"err={e['max_error_cents']} P={e['hexany_P']} "
                      f"idP={e['posthoc_identity_P']} coll={e['collision_count']} "
                      f"gaps={e['gap_classes']} {e['propriety']} "
                      f"recov={e['hexany_full_recovery_eps']}/"
                      f"{e['posthoc_identity_full_recovery_eps']}")
    print("identity full (6,6) at eps=2 contained:",
          {t: len(v) for t, v in
           summary["posthoc"]["identity_full_at_eps2_contained"].items()})


if __name__ == "__main__":
    main()
