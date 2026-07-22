"""LOOP-001: batch quality-diversity search over CPS seed space.

Plan §3.1 inner loop: deterministic, no LLM. Enumerate/mutate parameters ->
generate scale -> score with the FROZEN scorer -> keep per-bin elites.
Runs headless and time-boxed; the archive is append-only and is the museum.

WHY THIS SEARCH SPACE. The diagonal theorem (FINDINGS.md 2026-07-21) says
every MOS and every CPS(n, n/2) sits exactly on P = S under the anchored
convention, so min(P, S) == P there and the balance criterion does no work.
Two consequences shape this search:

  * Symmetric families (hexany CPS(4,2), eikosany CPS(6,3), dekany
    CPS(5,2)+CPS(5,3) pairs are NOT individually symmetric -- see below):
    the interesting axis is P itself, plus G and prime limit.
  * ASYMMETRIC families -- CPS(n, k) with k != n/2 -- are where min(P, S)
    can actually differentiate, because CPS(n, k) inverts to CPS(n, n-k)
    rather than to itself. These are searched deliberately: an asymmetric
    construction that scores HIGH on min(P, S) is the genuinely novel
    result plan §LOOP-003 asks for.

Archive bins (plan §3.1 descriptors): family, cardinality, P/S balance
bucket, prime limit of the seed set. Elite per bin = highest min(P, S),
ties broken by P*S, then G, then smaller seeds (prefer simpler tunings).

Determinism: the RNG seed is a parameter and is recorded in every record,
so any run is exactly reproducible. Re-running with the same seed and
budget reproduces the archive.

Usage (from experiments/triads/):
    python3.12 search.py --seconds 300
    python3.12 search.py --seconds 3600 --rng-seed 7 --out results/archive.jsonl
    python3.12 search.py --report-only        # re-report an existing archive
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Iterable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import scorer  # noqa: E402
from families.cps import cps_scale  # noqa: E402

# Seed pool: odd integers. Wilson's own sets live here (1,3,5,7,9,11,15) and
# so does Marcus's eikosany calibration set (1,45,135,225,19,377).
SEED_POOL = tuple(range(1, 400, 2))
SMALL_PRIMES = (3, 5, 7, 11, 13)

# (n, k) families. k != n/2 entries are the asymmetric ones where min(P,S)
# can differentiate; they are searched at the same weight as the classics.
FAMILIES: tuple[tuple[int, int], ...] = (
    (4, 2),   # hexany            6 tones   symmetric
    (5, 2),   # dekany           10 tones   ASYMMETRIC (inverts to 5,3)
    (5, 3),   # dekany           10 tones   ASYMMETRIC (inverts to 5,2)
    (6, 2),   # pentadekany      15 tones   ASYMMETRIC (inverts to 6,4)
    (6, 3),   # eikosany         20 tones   symmetric
    (6, 4),   # pentadekany      15 tones   ASYMMETRIC (inverts to 6,2)
)

LANDMARKS: tuple[tuple[str, tuple[int, ...], int], ...] = (
    ("hexany_1-3-5-7", (1, 3, 5, 7), 2),
    ("hexany_1-3-5-9", (1, 3, 5, 9), 2),
    ("eikosany_1-3-5-7-9-11", (1, 3, 5, 7, 9, 11), 3),
    ("eikosany_marcus_calibration", (1, 45, 135, 225, 19, 377), 3),
    ("dekany_1-3-5-7-9_k2", (1, 3, 5, 7, 9), 2),
    ("dekany_1-3-5-7-9_k3", (1, 3, 5, 7, 9), 3),
    ("pentadekany_1-3-5-7-9-11_k2", (1, 3, 5, 7, 9, 11), 2),
    ("pentadekany_1-3-5-7-9-11_k4", (1, 3, 5, 7, 9, 11), 4),
)


def prime_limit(seeds: Iterable[int]) -> int:
    """Largest prime factor appearing in any seed (1 for the all-ones case)."""
    limit = 1
    for s in seeds:
        n = int(s)
        f = 2
        while f * f <= n:
            while n % f == 0:
                limit = max(limit, f)
                n //= f
            f += 1
        if n > 1:
            limit = max(limit, n)
    return limit


def balance_bucket(p: int, s: int) -> str:
    """Coarse P/S balance descriptor — the archive's diversity axis."""
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


@dataclass(frozen=True)
class Candidate:
    seeds: tuple[int, ...]
    k: int


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def evaluate(cand: Candidate) -> Optional[dict]:
    """Score a candidate with the frozen scorer. None if degenerate."""
    try:
        scale = cps_scale(cand.seeds, cand.k)
    except ValueError:
        return None
    if len(scale) < 3:
        return None
    r = scorer.score(scale)
    return {
        "family": f"CPS({len(cand.seeds)},{cand.k})",
        "seeds": list(cand.seeds),
        "k": cand.k,
        "cardinality": len(scale),
        "P": r.proportional, "S": r.subcontrary, "G": r.geometric,
        "score_min": r.score_min, "score_product": r.score_product,
        "balance": balance_bucket(r.proportional, r.subcontrary),
        "prime_limit": prime_limit(cand.seeds),
        "convention": r.convention,
        "scorer_version": r.scorer_version,
    }


def bin_key(rec: dict) -> tuple:
    return (rec["family"], rec["cardinality"], rec["balance"],
            rec["prime_limit"])


def is_better(new: dict, cur: dict) -> bool:
    """Elite comparison: min(P,S), then P*S, then G, then simpler seeds."""
    def rank(r: dict) -> tuple:
        return (r["score_min"], r["score_product"], r["G"],
                -sum(r["seeds"]), -max(r["seeds"]))
    return rank(new) > rank(cur)


def mutate(cand: Candidate, rng: random.Random) -> Candidate:
    """One mutation operator, chosen uniformly. Seeds stay distinct/odd."""
    seeds = list(cand.seeds)
    op = rng.randrange(4)
    i = rng.randrange(len(seeds))
    if op == 0:                                   # replace with pool draw
        seeds[i] = rng.choice(SEED_POOL)
    elif op == 1:                                 # multiply by a small prime
        seeds[i] = seeds[i] * rng.choice(SMALL_PRIMES)
    elif op == 2:                                 # divide out a prime factor
        p = rng.choice(SMALL_PRIMES)
        if seeds[i] % p == 0 and seeds[i] // p >= 1:
            seeds[i] //= p
        else:
            seeds[i] = rng.choice(SEED_POOL)
    else:                                         # nudge to a neighbouring odd
        seeds[i] = max(1, seeds[i] + rng.choice((-2, 2)))
    if len(set(seeds)) != len(seeds):             # keep seeds distinct
        return random_candidate(len(cand.seeds), cand.k, rng)
    return Candidate(tuple(sorted(seeds)), cand.k)


def random_candidate(n: int, k: int, rng: random.Random) -> Candidate:
    return Candidate(tuple(sorted(rng.sample(SEED_POOL, n))), k)


def load(path: Path) -> tuple[dict, dict]:
    meta: dict = {}
    archive: dict[tuple, dict] = {}
    with path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if "_meta" in rec:
                meta = rec["_meta"]
                continue
            archive[bin_key(rec)] = rec
    return archive, meta



def search(seconds: float, rng_seed: int, out_path: Path,
           exhaustive_max: int = 21) -> dict:
    """Time-boxed MAP-Elites over the CPS families. Returns the archive."""
    rng = random.Random(rng_seed)
    commit = _commit()
    evaluated = 0
    improvements = 0

    # The archive ACCUMULATES across runs (plan §3.1: append-only, "the
    # archive IS the museum"). Without this each run overwrote the last and
    # discoveries were silently lost -- observed directly: run 1 found a
    # CPS(5,3) at min=21 that run 2, with a different random walk, did not,
    # and the rewrite erased it. Merging also means a long search can be
    # built from several short ones.
    archive: dict[tuple, dict] = {}
    carried = 0
    if out_path.exists():
        prior, _ = load(out_path)
        archive.update(prior)
        carried = len(prior)

    def offer(rec: Optional[dict], origin: str) -> bool:
        nonlocal improvements
        if rec is None:
            return False
        rec = {**rec, "origin": origin}
        key = bin_key(rec)
        cur = archive.get(key)
        if cur is None or is_better(rec, cur):
            archive[key] = rec
            improvements += 1
            return True
        return False

    def offer_with_dual(cand: Candidate, origin: str) -> None:
        """Offer a candidate AND its period-space dual CPS(n, n-k).

        CPS(n,k) inverts to CPS(n,n-k) on the same seeds, so the dual's
        (P,S) is the exact swap and its min(P,S) is identical. Evaluating
        only one of the pair leaves the archive asymmetrically incomplete:
        the first run reported the classic dekany UNBEATEN at CPS(5,2)
        while 5-7-15-35-45 scored min=21 there -- it had simply never been
        tried at k=2. Costs one extra scoring, buys a dual-complete archive.
        """
        nonlocal evaluated
        offer(evaluate(cand), origin)
        evaluated += 1
        n, k = len(cand.seeds), cand.k
        if n - k != k and 1 <= n - k <= n:
            offer(evaluate(Candidate(cand.seeds, n - k)), f"{origin}_dual")
            evaluated += 1

    # Landmarks are tracked SEPARATELY from the archive as well as offered
    # to it. MAP-Elites evicts a cell's occupant as soon as something better
    # lands there, so a landmark held only in the archive silently vanishes
    # from the comparison table -- which is exactly the table the ear checks
    # depend on. Observed in the first run: 4 of 8 landmarks disappeared.
    landmark_records: list[dict] = []
    for name, seeds, k in LANDMARKS:
        rec = evaluate(Candidate(tuple(seeds), k))
        if rec is not None:
            tagged = {**rec, "landmark": name}
            landmark_records.append(tagged)
            offer(tagged, "landmark")
            evaluated += 1

    # Phase 1: EXHAUSTIVE over small odd seeds. This region is where the
    # musically interesting sets live and it is small enough to enumerate,
    # so the winners it reports are provably optimal there rather than
    # merely the best thing random search happened to find. Random search
    # (phase 2) then explores the unbounded remainder.
    exhaustive_odds = tuple(o for o in SEED_POOL if o <= exhaustive_max)
    exhaustive_counts: dict[str, int] = {}
    for n, k in FAMILIES:
        fam = f"CPS({n},{k})"
        for combo in combinations(exhaustive_odds, n):
            offer_with_dual(Candidate(combo, k), "exhaustive")
            exhaustive_counts[fam] = exhaustive_counts.get(fam, 0) + 1

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        n, k = FAMILIES[rng.randrange(len(FAMILIES))]
        elites = [r for key, r in archive.items()
                  if key[0] == f"CPS({n},{k})"]
        if elites and rng.random() < 0.7:                # exploit
            parent = rng.choice(elites)
            cand = mutate(Candidate(tuple(parent["seeds"]), k), rng)
            origin = "mutation"
        else:                                            # explore
            cand = random_candidate(n, k, rng)
            origin = "random"
        offer_with_dual(cand, origin)

    stamp_meta = {
        "rng_seed": rng_seed, "seconds": seconds, "commit": commit,
        "scorer_version": scorer.SCORER_VERSION,
        "convention": scorer.PRIMARY_CONVENTION,
        "evaluated": evaluated, "improvements": improvements,
        "cells_filled": len(archive),
        "exhaustive_max_odd": exhaustive_max,
        "exhaustive_counts": exhaustive_counts,
        "landmarks": landmark_records,
        "cells_carried_in": carried,
    }
    out_path.parent.mkdir(exist_ok=True)
    with out_path.open("w", encoding="ascii") as fh:
        fh.write(json.dumps({"_meta": stamp_meta}) + "\n")
        for key in sorted(archive, key=lambda t: (t[0], t[1], t[2], t[3])):
            fh.write(json.dumps(archive[key]) + "\n")
    return {"meta": stamp_meta, "archive": archive,
            "landmarks": landmark_records}


def report(archive: dict[tuple, dict], meta: dict, top: int = 3,
           landmarks: Optional[list] = None) -> None:
    carried = meta.get("cells_carried_in", 0)
    print(f"LOOP-001 archive — scorer {meta['scorer_version']} "
          f"({meta['convention']}), rng_seed={meta['rng_seed']}, "
          f"{meta['evaluated']} candidates evaluated this run, "
          f"{meta['cells_filled']} cells filled "
          f"({carried} carried in from earlier runs — the archive "
          f"accumulates, plan §3.1)")

    by_family: dict[str, list[dict]] = {}
    for rec in archive.values():
        by_family.setdefault(rec["family"], []).append(rec)

    # Rankings are per (family, CARDINALITY). Plan §1.3: raw counts grow
    # combinatorially with cardinality, so a 13-tone scale's count must
    # never be compared against a 15-tone one. Product collisions make this
    # a live issue, not a formality -- e.g. CPS(6,2) on 1-3-5-7-9-15
    # collapses to 13 tones and would otherwise "beat" the 15-tone classic.
    print("\n=== WINNERS per family and cardinality (by min(P,S), then P*S) ===")
    for family in sorted(by_family):
        print(f"\n{family}:")
        by_card: dict[int, list[dict]] = {}
        for rec in by_family[family]:
            by_card.setdefault(rec["cardinality"], []).append(rec)
        for card in sorted(by_card, reverse=True):
            rows = sorted(by_card[card],
                          key=lambda r: (-r["score_min"], -r["score_product"]))
            print(f"  N={card}:")
            for r in rows[:top]:
                tag = f"  [{r['landmark']}]" if "landmark" in r else ""
                seeds = "-".join(str(s) for s in r["seeds"])
                print(f"    min={r['score_min']:4d}  (P,S,G)=({r['P']},"
                      f"{r['S']},{r['G']})  {r['prime_limit']:3d}-limit  "
                      f"seeds {seeds}{tag}")

    off = [r for r in archive.values() if r["P"] != r["S"]]
    print(f"\n=== OFF-DIAGONAL entries (P != S): {len(off)} ===")
    print("These are the only ones where min(P,S) does work the raw P count")
    print("does not — the diagonal theorem makes P == S structural elsewhere.")
    for r in sorted(off, key=lambda r: -r["score_min"])[:top * 3]:
        seeds = "-".join(str(s) for s in r["seeds"])
        print(f"  {r['family']} min={r['score_min']:4d} (P,S)=({r['P']},"
              f"{r['S']}) {r['balance']:>12}  seeds {seeds}")

    print("\n=== LANDMARK comparison (within its own cardinality bin) ===")
    lm = landmarks if landmarks is not None else [
        r for r in archive.values() if "landmark" in r]
    for rec in sorted(lm, key=lambda r: r["landmark"]):
        seeds = "-".join(str(s) for s in rec["seeds"])
        peers = [r for r in by_family[rec["family"]]
                 if r["cardinality"] == rec["cardinality"]]
        better = sorted((r for r in peers
                         if r["score_min"] > rec["score_min"]),
                        key=lambda r: -r["score_min"])
        verdict = (f"{len(better)} beat it" if better else "UNBEATEN")
        print(f"  {rec['landmark']:30} N={rec['cardinality']:2d} "
              f"min={rec['score_min']:4d} "
              f"(P,S,G)=({rec['P']},{rec['S']},{rec['G']})  {verdict}"
              f"   seeds {seeds}")
        for b in better[:top]:
            bseeds = "-".join(str(s) for s in b["seeds"])
            print(f"      beaten by min={b['score_min']:4d} "
                  f"(P,S)=({b['P']},{b['S']}) {b['prime_limit']:3d}-limit "
                  f"seeds {bseeds}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=300.0)
    ap.add_argument("--rng-seed", type=int, default=1)
    ap.add_argument("--out", type=Path,
                    default=HERE / "results" / "archive.jsonl")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--exhaustive-max", type=int, default=21,
                    help="enumerate ALL seed sets from odds <= this first")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    if args.report_only:
        archive, meta = load(args.out)
        report(archive, meta, args.top, meta.get("landmarks"))
        return

    result = search(args.seconds, args.rng_seed, args.out,
                    args.exhaustive_max)
    report(result["archive"], result["meta"], args.top,
           result["landmarks"])
    print(f"\narchive -> {args.out}")


if __name__ == "__main__":
    main()
