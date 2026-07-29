"""SHADOW-001: comma perturbation of CPS factors (SPEC.md §SHADOW-001).

Replace one factor n of a CPS seed set with m = 2^k·n ± 1 (always odd,
co-prime to the octave), sweep k = 3..16 and both signs over every factor
position of the hexany (1,3,5,7) and eikosany (1,3,5,7,9,11). Per variant:

- frozen triad scorer v1.1.0 on BOTH paths: `score()` (exact rational,
  the control — exact coincidences should drop and stay dropped) and
  `score_tempered(cents, epsilon_cents=2.0)` (H-S1's recovery prediction);
- tone survival: `canonical_cents_scale` dedup at
  eps_dedup in {0.01, 0.1, 0.5, 2} cents;
- comma spectrum: all pairwise circular intervals < 20 cents;
- prime factorization of the replacement m (is_prime, primes shared with
  the remaining factors);
- melodic M1-M3 via melodic.score_melodic_rational (v0.1.0 defaults);
- displacement_cents = 1200*|log2(m/(2^k*n))|.

Hypotheses H-S1/H-S2/H-S3 are pre-registered in LOG.md (2026-07-28 entry)
with concrete numeric predictions; this script prints the verdict tables
the LOG results entry quotes.

Deterministic: stdlib only, fixed constants, no randomness. Timestamps and
git commit are provenance, not inputs.

Run from experiments/lattice/:
    python3.12 shadow001.py

Writes:
    results/shadow001.jsonl           one row per variant (+ 2 baselines)
    results/shadow001_verdicts.json   hypothesis verdict summary
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from math import log2
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
TRIADS = HERE.parent / "triads"
for _p in (str(HERE), str(TRIADS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scorer  # noqa: E402  (frozen v1.1.0, read-only)
from families.cps import cps_scale  # noqa: E402
import melodic  # noqa: E402

EXPERIMENT = "SHADOW-001"
SCORER_EPSILON_CENTS = 2.0
DEDUP_EPSILONS_CENTS = (0.01, 0.1, 0.5, 2.0)
COMMA_LIMIT_CENTS = 20.0
K_MIN, K_MAX = 3, 16
SIGNS = (1, -1)
#: (name, seeds, choose-k). Hexany = CPS(4,2), eikosany = CPS(6,3).
BASES = (
    ("hexany", (1, 3, 5, 7), 2),
    ("eikosany", (1, 3, 5, 7, 9, 11), 3),
)
#: Small-k window for H-S1's exact-drop claim and the k probing no-recovery.
SMALL_K = tuple(range(3, 8))
NO_RECOVERY_K = 16

RESULTS = HERE / "results"
RECEIPT_PATH = RESULTS / "shadow001.jsonl"
VERDICT_PATH = RESULTS / "shadow001_verdicts.json"


# ---------------------------------------------------------------------------
# pure helpers (unit-tested in tests/test_shadow001.py)
# ---------------------------------------------------------------------------


def factorize(n: int) -> dict[int, int]:
    """Prime factorization by trial division; {} for n == 1."""
    if n < 1:
        raise ValueError(f"expected positive integer, got {n}")
    factors: dict[int, int] = {}
    remaining = n
    p = 2
    while p * p <= remaining:
        while remaining % p == 0:
            factors[p] = factors.get(p, 0) + 1
            remaining //= p
        p += 1 if p == 2 else 2
    if remaining > 1:
        factors[remaining] = factors.get(remaining, 0) + 1
    return factors


def is_prime(n: int) -> bool:
    return factorize(n) == {n: 1} if n > 1 else False


def shared_factors(m: int, remaining_seeds: tuple[int, ...]) -> tuple[int, ...]:
    """Primes of m also dividing at least one of the surviving factors.

    Seed value 1 contributes nothing. m = 2^k*n +- 1 is odd and co-prime
    to n by construction, so sharing can only be with the OTHER factors."""
    remaining_primes = {
        p for s in remaining_seeds if s > 1 for p in factorize(s)
    }
    return tuple(sorted(set(factorize(m)) & remaining_primes))


def displacement_cents(n: int, k: int, sign: int) -> float:
    """1200*|log2((2^k*n + sign)/(2^k*n))| — the perturbed tone's shift."""
    base = (2 ** k) * n
    return abs(1200.0 * log2(Fraction(base + sign, base)))


def perturbation_variants(seeds: tuple[int, ...]):
    """Yield (pos, n, k, sign, m, new_seeds) for the full sweep, skipping
    collisions (m equal to a surviving factor). Deterministic order:
    position, then k, then sign (+ before -)."""
    for pos, n in enumerate(seeds):
        others = seeds[:pos] + seeds[pos + 1:]
        for k in range(K_MIN, K_MAX + 1):
            for sign in SIGNS:
                m = (2 ** k) * n + sign
                if m in others:
                    continue
                new_seeds = seeds[:pos] + (m,) + seeds[pos + 1:]
                yield pos, n, k, sign, m, new_seeds


def scale_cents(scale: tuple[Fraction, ...]) -> tuple[float, ...]:
    """Cents in [0, 1200) of an exact canonical scale."""
    return tuple(1200.0 * log2(float(r)) for r in scale)


def comma_spectrum(scale: tuple[Fraction, ...],
                   limit_cents: float = COMMA_LIMIT_CENTS) -> list[dict]:
    """All unordered pairs at circular distance < limit_cents.

    Distance is min(d, 1200-d) over the cents of the exact scale; the
    interval ratio is recorded octave-reduced (its cents equal either d
    or 1200-d, whichever direction the ratio runs)."""
    cents = scale_cents(scale)
    out = []
    for i in range(len(scale)):
        for j in range(i + 1, len(scale)):
            d = (cents[j] - cents[i]) % 1200.0
            dist = min(d, 1200.0 - d)
            if dist < limit_cents:
                ratio = scorer.reduce_rational(scale[j] / scale[i])
                out.append({
                    "tones": [str(scale[i]), str(scale[j])],
                    "ratio": str(ratio),
                    "cents": dist,
                })
    out.sort(key=lambda row: row["cents"])
    return out


def tone_survival(cents: tuple[float, ...]) -> dict[str, int]:
    """Deduped tone count at each pre-registered eps_dedup."""
    return {
        str(eps): len(scorer.canonical_cents_scale(cents, eps))
        for eps in DEDUP_EPSILONS_CENTS
    }


# ---------------------------------------------------------------------------
# per-variant evaluation
# ---------------------------------------------------------------------------


def _exact_block(res: scorer.ScoreResult) -> dict:
    return {
        "P": res.proportional, "S": res.subcontrary, "G": res.geometric,
        "score_min": res.score_min, "score_product": res.score_product,
        "convention": res.convention, "max_span": str(res.max_span),
    }


def _tempered_block(res: scorer.ScoreResult) -> dict:
    return {
        "P": res.proportional, "S": res.subcontrary, "G": res.geometric,
        "score_min": res.score_min, "score_product": res.score_product,
        "P_raw": res.proportional_raw, "S_raw": res.subcontrary_raw,
        "G_raw": res.geometric_raw,
        "degenerate_dropped": res.degenerate_dropped,
        "epsilon_cents": res.epsilon_cents,
        "convention": res.convention, "max_span": res.max_span,
    }


def _melodic_block(ms: melodic.MelodicScore) -> dict:
    return {
        "m1_entropy_bits": ms.gap_entropy.entropy_bits,
        "m1_gap_count": ms.gap_entropy.gap_count,
        "m1_gap_class_count": ms.gap_entropy.gap_class_count,
        "m2_violations": ms.constant_structure.violations,
        "m2_is_cs": ms.constant_structure.is_cs,
        "m2_interval_class_count": ms.constant_structure.interval_class_count,
        "m3_classification": ms.propriety.classification,
        "m3_violating_span_pairs": ms.propriety.violating_span_pairs,
        "epsilons": {
            "dedup": melodic.DEFAULT_DEDUP_EPSILON_CENTS,
            "gap": melodic.DEFAULT_GAP_EPSILON_CENTS,
            "cs": melodic.DEFAULT_CS_EPSILON_CENTS,
            "propriety": melodic.DEFAULT_PROPRIETY_EPSILON_CENTS,
        },
    }


def evaluate_scale(seeds: tuple[int, ...], choose_k: int) -> dict:
    """Score one seed set on every pre-registered axis."""
    scale = cps_scale(seeds, choose_k)
    cents = scale_cents(scale)
    exact = scorer.score(scale)
    tempered = scorer.score_tempered(cents, SCORER_EPSILON_CENTS)
    mel = melodic.score_melodic_rational(scale)
    return {
        "seeds": list(seeds),
        "tone_count_exact": len(scale),
        "tone_survival": tone_survival(cents),
        "comma_spectrum": comma_spectrum(scale),
        "exact": _exact_block(exact),
        "tempered": _tempered_block(tempered),
        "melodic": _melodic_block(mel),
    }


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=HERE, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"warning: could not resolve git commit: {exc}", file=sys.stderr)
        return "unknown"


def run_sweep() -> list[dict]:
    commit = _git_commit()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provenance = {
        "experiment": EXPERIMENT,
        "scorer_version": scorer.SCORER_VERSION,
        "melodic_version": melodic.MELODIC_VERSION,
        "scorer_epsilon_cents": SCORER_EPSILON_CENTS,
        "dedup_epsilons_cents": list(DEDUP_EPSILONS_CENTS),
        "comma_limit_cents": COMMA_LIMIT_CENTS,
        "git_commit": commit,
        "timestamp_utc": stamp,
    }
    rows: list[dict] = []
    for name, seeds, choose_k in BASES:
        base_row = {
            **provenance,
            "base": name, "base_seeds": list(seeds), "cps_k": choose_k,
            "variant": "unperturbed",
            "position_index": None, "perturbed_factor": None,
            "k": None, "sign": None, "replacement": None,
            "displacement_cents": 0.0,
            "replacement_factorization": None,
            "replacement_is_prime": None, "shared_factors": None,
            **evaluate_scale(seeds, choose_k),
        }
        rows.append(base_row)
        print(f"{name} base: exact (P,S)=({base_row['exact']['P']},"
              f"{base_row['exact']['S']}), tempered (P,S)="
              f"({base_row['tempered']['P']},{base_row['tempered']['S']})")
        for pos, n, k, sign, m, new_seeds in perturbation_variants(seeds):
            sign_tag = "plus" if sign > 0 else "minus"
            rows.append({
                **provenance,
                "base": name, "base_seeds": list(seeds), "cps_k": choose_k,
                "variant": f"pos{pos}_n{n}_k{k}_{sign_tag}",
                "position_index": pos, "perturbed_factor": n,
                "k": k, "sign": sign, "replacement": m,
                "displacement_cents": displacement_cents(n, k, sign),
                "replacement_factorization": {
                    str(p): e for p, e in sorted(factorize(m).items())
                },
                "replacement_is_prime": is_prime(m),
                "shared_factors": list(
                    shared_factors(m, seeds[:pos] + seeds[pos + 1:])
                ),
                **evaluate_scale(new_seeds, choose_k),
            })
        print(f"{name}: {sum(r['base'] == name for r in rows) - 1} variants")
    return rows


# ---------------------------------------------------------------------------
# hypothesis verdicts
# ---------------------------------------------------------------------------


def _variants(rows: list[dict], base: str) -> list[dict]:
    return [r for r in rows
            if r["base"] == base and r["variant"] != "unperturbed"]


def _base_row(rows: list[dict], base: str) -> dict:
    return next(r for r in rows
                if r["base"] == base and r["variant"] == "unperturbed")


def verdict_h_s1(rows: list[dict]) -> dict:
    """Exact drop + no recovery; tempered recovery k* vs displacement."""
    out: dict = {}
    for name, _, _ in BASES:
        base = _base_row(rows, name)
        base_exact = base["exact"]["score_min"]
        base_temp = base["tempered"]["score_min"]
        variants = _variants(rows, name)
        small_k = [r for r in variants if r["k"] in SMALL_K]
        exact_drops = sum(r["exact"]["score_min"] < base_exact
                          for r in small_k)
        k16 = [r for r in variants if r["k"] == NO_RECOVERY_K]
        exact_recoveries_k16 = [
            r["variant"] for r in k16
            if r["exact"]["score_min"] >= base_exact
        ]
        recovery = {}
        for pos, n in enumerate(next(b for b in BASES if b[0] == name)[1]):
            for sign in SIGNS:
                sign_tag = "plus" if sign > 0 else "minus"
                series = sorted(
                    (r for r in variants
                     if r["position_index"] == pos and r["sign"] == sign),
                    key=lambda r: r["k"],
                )
                k_star = next(
                    (r["k"] for r in series
                     if r["tempered"]["score_min"] >= base_temp), None)
                disp = next((r["displacement_cents"] for r in series
                             if r["k"] == k_star), None)
                recovery[f"pos{pos}_n{n}_{sign_tag}"] = {
                    "k_star": k_star,
                    "displacement_at_k_star": disp,
                    "displacement_inside_scorer_eps":
                        None if disp is None else disp < SCORER_EPSILON_CENTS,
                    "tempered_series": {
                        str(r["k"]): r["tempered"]["score_min"]
                        for r in series
                    },
                    "exact_series": {
                        str(r["k"]): r["exact"]["score_min"] for r in series
                    },
                }
        out[name] = {
            "base_exact_score_min": base_exact,
            "base_tempered_score_min": base_temp,
            "exact_drop_small_k": {
                "dropped": exact_drops, "of": len(small_k),
            },
            "exact_recoveries_at_k16": exact_recoveries_k16,
            "tempered_recovery": recovery,
        }
    return out


def verdict_h_s2(rows: list[dict]) -> dict:
    """Tone-count transitions per (base, pos, sign, eps_dedup)."""
    out: dict = {}
    for name, seeds, _ in BASES:
        base = _base_row(rows, name)
        variants = _variants(rows, name)
        per_config: dict = {}
        any_change = False
        for pos, n in enumerate(seeds):
            for sign in SIGNS:
                sign_tag = "plus" if sign > 0 else "minus"
                series = sorted(
                    (r for r in variants
                     if r["position_index"] == pos and r["sign"] == sign),
                    key=lambda r: r["k"],
                )
                eps_map = {}
                for eps in DEDUP_EPSILONS_CENTS:
                    counts = {str(r["k"]): r["tone_survival"][str(eps)]
                              for r in series}
                    distinct = sorted(set(counts.values()))
                    transitions = [
                        series[i]["k"]
                        for i in range(1, len(series))
                        if series[i]["tone_survival"][str(eps)]
                        != series[i - 1]["tone_survival"][str(eps)]
                    ]
                    if len(distinct) > 1:
                        any_change = True
                    eps_map[str(eps)] = {
                        "counts_by_k": counts,
                        "transition_ks": transitions,
                    }
                per_config[f"pos{pos}_n{n}_{sign_tag}"] = eps_map
        out[name] = {
            "base_tone_survival": base["tone_survival"],
            "any_tone_count_change": any_change,
            "per_config": per_config,
        }
    return out


def verdict_h_s3(rows: list[dict]) -> dict:
    """Matched +- pairs at same (base, pos, k): sharing composite vs prime."""
    out: dict = {}
    for name, seeds, _ in BASES:
        variants = _variants(rows, name)
        index = {(r["position_index"], r["k"], r["sign"]): r for r in variants}
        pairs = []
        exact_w = exact_t = exact_l = 0
        temp_w = temp_t = temp_l = 0
        for pos, n in enumerate(seeds):
            for k in range(K_MIN, K_MAX + 1):
                plus = index.get((pos, k, 1))
                minus = index.get((pos, k, -1))
                if plus is None or minus is None:
                    continue
                sides = {}
                for r in (plus, minus):
                    if r["replacement_is_prime"]:
                        sides.setdefault("prime", r)
                    elif r["shared_factors"]:
                        sides.setdefault("sharing", r)
                if set(sides) != {"prime", "sharing"}:
                    continue
                sh, pr = sides["sharing"], sides["prime"]
                d_exact = sh["exact"]["P"] - pr["exact"]["P"]
                d_temp = (sh["tempered"]["score_min"]
                          - pr["tempered"]["score_min"])
                exact_w += d_exact > 0
                exact_t += d_exact == 0
                exact_l += d_exact < 0
                temp_w += d_temp > 0
                temp_t += d_temp == 0
                temp_l += d_temp < 0
                pairs.append({
                    "position_index": pos, "perturbed_factor": n, "k": k,
                    "sharing_m": sh["replacement"],
                    "sharing_factors": sh["shared_factors"],
                    "prime_m": pr["replacement"],
                    "exact_P_sharing": sh["exact"]["P"],
                    "exact_P_prime": pr["exact"]["P"],
                    "tempered_min_sharing": sh["tempered"]["score_min"],
                    "tempered_min_prime": pr["tempered"]["score_min"],
                })
        out[name] = {
            "matched_pairs": len(pairs),
            "exact_P": {"sharing_wins": exact_w, "ties": exact_t,
                        "prime_wins": exact_l},
            "tempered_score_min": {"sharing_wins": temp_w, "ties": temp_t,
                                   "prime_wins": temp_l},
            "pairs": pairs,
        }
    return out


def verdict_symmetry(rows: list[dict]) -> dict:
    """Pre-registered structural check: P == S everywhere, both paths."""
    bad = [r["variant"] for r in rows
           if r["exact"]["P"] != r["exact"]["S"]
           or r["tempered"]["P"] != r["tempered"]["S"]]
    return {"violations": bad, "holds": not bad}


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    rows = run_sweep()
    with RECEIPT_PATH.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    verdicts = {
        "experiment": EXPERIMENT,
        "receipt": RECEIPT_PATH.name,
        "rows": len(rows),
        "H-S1": verdict_h_s1(rows),
        "H-S2": verdict_h_s2(rows),
        "H-S3": verdict_h_s3(rows),
        "P_equals_S": verdict_symmetry(rows),
    }
    with VERDICT_PATH.open("w") as fh:
        json.dump(verdicts, fh, indent=2)
    print(f"\nwrote {len(rows)} rows -> {RECEIPT_PATH}")
    print(f"verdicts -> {VERDICT_PATH}")

    # console digest (full numbers live in the verdict file)
    for name, _, _ in BASES:
        s1 = verdicts["H-S1"][name]
        print(f"\n[{name}] base exact min={s1['base_exact_score_min']} "
              f"tempered min={s1['base_tempered_score_min']}")
        print(f"  H-S1 exact drops (k in {SMALL_K[0]}..{SMALL_K[-1]}): "
              f"{s1['exact_drop_small_k']['dropped']}"
              f"/{s1['exact_drop_small_k']['of']}; "
              f"exact recoveries at k=16: {s1['exact_recoveries_at_k16']}")
        for cfg, rec in s1["tempered_recovery"].items():
            print(f"  H-S1 recovery {cfg}: k*={rec['k_star']} "
                  f"disp={rec['displacement_at_k_star']}")
        s2 = verdicts["H-S2"][name]
        print(f"  H-S2 any tone-count change: {s2['any_tone_count_change']}")
        s3 = verdicts["H-S3"][name]
        print(f"  H-S3 matched pairs={s3['matched_pairs']} "
              f"exact_P {s3['exact_P']} "
              f"tempered {s3['tempered_score_min']}")
    print(f"\nP==S structural check: {verdicts['P_equals_S']['holds']}")


if __name__ == "__main__":
    main()
