"""GAPFILL-002 — one shared fill table for every subset of an Euler genus
(LOG.md pre-registration 2026-10-31; committed before this file's receipts).

Marcus (2026-10-31), choosing the one-table framing: GAPFILL-001 filled each
subset on its own, and the fills that give the best melody (arithmetic and
harmonic division, recurrences, MOS windows) share almost no tones across
subsets, so a composer moving hexany to hexany meets new tones every time.
Here every subset must find its constant-structure completion inside ONE
small set F of added tones. The instrument is then one fixed tuning table
(the eikosany plus F) and each subset selects its keys, which is the shape
of the EG6 root-mapping spec (root table, subset keyboards).

Two stages, exact over what stage 1 lists:
  1. completions  for each subset, every inclusion-minimal CS completion
                  from the table's pool with at most SLACK tones more than
                  its smallest one (GAPFILL-001's gap-directed search, run
                  to enumerate instead of to stop), under a node budget
  2. cover        the smallest F such that every coverable subset has a
                  listed completion inside F (branch and bound, greedy
                  upper bound, lower bound = the largest single shortfall)

Tables (pools are global: a subset may use any tone of the table):
  PARENT     the eikosany's own tones (common tones)
  GENUS      every tone of the Euler genus
  EPI        every subset's arithmetic, harmonic and mediant split points
  EPI-AM     arithmetic split points only (the mirror test)
  EPI-HM     harmonic split points only
  MOS        one generator's chain (DYNMOS-001 windows, tempered), the
             generator covering most subsets with the smallest F
  EXACT      PARENT + GENUS + EPI together
  EXACT+MOS  EXACT plus the MOS table's chain
Arm C asks the top-first question: the smallest CS superset of the eikosany
itself from the EXACT pool, and whether the eikosany plus F of each table is
CS as a whole.

Every subset's playable scale (subset + its assigned completion) is scored
with the frozen scorers exactly as in GAPFILL-001 (gapfill001.score).

Frozen inputs (read-only): experiments/triads/scorer.py v1.1.0,
experiments/lattice/melodic.py v0.1.0. Read-only helpers: gapfill001,
dynmos001, families.cps.

Receipts: results/gapfill002.jsonl (one row per seed set x table x subset)
+ results/gapfill002_summary.json; results/scl/gapfill002/*.scl. Stdlib
only, deterministic, no wall-clock fields.

Run from experiments/lattice/:  python3.12 gapfill002.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import dynmos001 as dm  # noqa: E402
import gapfill001 as g1  # noqa: E402
import melodic as mel  # noqa: E402
from families.cps import cps_scale  # noqa: E402
from scorer import SCORER_VERSION  # noqa: E402

GAPFILL002_VERSION = "1.0.0"
EXPERIMENT = "GAPFILL-002"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "gapfill002.jsonl"
SUMMARY = RESULTS_DIR / "gapfill002_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "gapfill002"

CENTS = g1.CENTS
SLACK = 2                 # completions up to this many tones above a subset's smallest
ENUM_BUDGET = 60_000      # search nodes per subset per table (global pool)
ENUM_LIMIT = 200          # completions kept per subset per table
COVER_BUDGET = 50_000     # branch-and-bound nodes per table
TOP_N_MAX = 40            # arm C: largest eikosany superset searched
TOP_BUDGET = 200_000
WORKERS = 8
TABLES = ("PARENT", "GENUS", "EPI-AM", "EPI-HM", "EPI", "EXACT", "MOS", "EXACT+MOS")
# A combined table also lists its components' completions and starts from their tables.
PARTS = {"EPI": ("EPI-AM", "EPI-HM"), "EXACT": ("PARENT", "GENUS", "EPI"), "EXACT+MOS": ("EXACT", "MOS")}
SHOWCASE = "canonical"


def key(c: float) -> float:
    return round(c % CENTS, 6)


# ---------------------------------------------------------------------------
# stage 1: completions
# ---------------------------------------------------------------------------


def completions(base: list[float], pool: list[float], prio: dict[float, int] | None = None
                ) -> tuple[list[frozenset], int, bool]:
    """Inclusion-minimal CS completions of base from pool, at most SLACK tones
    above the smallest. Tones shared by more subsets (prio) are tried first,
    so a capped list leans toward completions a table can share. Returns
    (completions as frozensets of keys, nodes, budget or limit hit)."""
    prio = prio or {}
    pool = sorted({key(p) for p in pool if g1.clear_of(p, base)}, key=lambda k: (-prio.get(k, 0), k))
    nodes, found, first = 0, set(), None

    def dfs(cs: list[float], added: tuple, left: int, start: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > ENUM_BUDGET or len(found) >= ENUM_LIMIT:
            raise TimeoutError
        if g1.need(cs) > left:
            return
        if g1.max_step(cs) <= g1.CAP:
            if g1.is_cs(cs):
                found.add(tuple(sorted(added)))
                return
            cands, after = [i for i in range(start, len(pool)) if g1.clear_of(pool[i], cs)], True
        else:
            lo, hi = g1.widest(cs)
            cands, after = [i for i, p in enumerate(pool) if g1.inside(p, lo, hi) and g1.clear_of(p, cs)], False
        if left == 0:
            return
        for i in cands:
            dfs(sorted(cs + [pool[i]]), added + (i,), left - 1, i + 1 if after else start)

    out = False
    try:
        for depth in range(0, g1.N_SEARCH_MAX - len(base) + 1):
            dfs(sorted(base), (), depth, 0)
            if found and first is None:
                first = depth
            if first is not None and depth >= first + SLACK:
                break
    except TimeoutError:
        out = True
    return minimal({frozenset(pool[i] for i in c) for c in found}), nodes, out


def minimal(comps: set[frozenset]) -> list[frozenset]:
    return sorted((c for c in comps if not any(o < c for o in comps)), key=lambda c: (len(c), sorted(c)))


# ---------------------------------------------------------------------------
# stage 2: the cover
# ---------------------------------------------------------------------------


def _masks(comps: list[list[frozenset]]) -> tuple[list[float], list[list[int]]]:
    tones = sorted({t for cs in comps for c in cs for t in c})
    bit = {t: 1 << i for i, t in enumerate(tones)}
    return tones, [[sum(bit[t] for t in c) for c in cs] for cs in comps]


def _short(masks: list[int], F: int) -> int:
    return min((m & ~F).bit_count() for m in masks)


def _helps(G: int, masks: list[list[int]], left) -> int:
    return sum(1 for j in left if any(not (d & ~G) for d in masks[j]))


def greedy_cover(masks: list[list[int]]) -> int:
    """Upper bound: serve the subset with the largest shortfall by its
    completion that leaves the most other subsets served."""
    F, left = 0, [i for i, m in enumerate(masks) if m]
    while left:
        i = max(left, key=lambda i: (_short(masks[i], F), -i))
        m = min(masks[i], key=lambda m: (-_helps(F | m, masks, left), (m & ~F).bit_count(), m))
        F |= m
        left = [j for j in left if _short(masks[j], F)]
    return F


def _extend(F: int, masks: list[list[int]]) -> int:
    """A start F completed greedily until every coverable subset is served."""
    left = [i for i, m in enumerate(masks) if m and _short(m, F)]
    while left:
        i = max(left, key=lambda i: (_short(masks[i], F), -i))
        F |= min(masks[i], key=lambda m: (-_helps(F | m, masks, left), (m & ~F).bit_count(), m))
        left = [j for j in left if _short(masks[j], F)]
    return F


def exact_cover(comps: list[list[frozenset]], starts: tuple = ()) -> tuple[frozenset, int, bool, int]:
    """Smallest F with a listed completion of every coverable subset inside it
    (ties: the lowest tones). starts: tables already found (a combined table
    starts from its components' solutions). Returns (F, nodes, proven optimal
    over the listed completions, lower bound at the root)."""
    tones, masks = _masks(comps)
    bit = {t: b for b, t in enumerate(tones)}
    weight = [sum(any(m >> b & 1 for m in ms) for ms in masks) for b in range(len(tones))]
    def rank(m: int, F: int) -> tuple:
        new = m & ~F
        return new.bit_count(), -sum(w for b, w in enumerate(weight) if new >> b & 1), m
    ups = [greedy_cover(masks)] + [_extend(sum(1 << bit[t] for t in S if t in bit), masks) for S in starts]
    best = [min(ups, key=lambda F: (F.bit_count(), F))]
    nodes = 0

    def bound(F: int, short: dict[int, int]) -> int:
        """Shortfalls of subsets whose open tones are pairwise disjoint add up."""
        used, lb = 0, 0
        for i in sorted(short, key=lambda i: (-short[i], i)):
            open_ = 0
            for m in masks[i]:
                open_ |= m & ~F
            if not open_ & used:
                used |= open_
                lb += short[i]
        return max(lb, max(short.values()))

    def rec(F: int, U: list[int]) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > COVER_BUDGET:
            raise TimeoutError
        short = {i: _short(masks[i], F) for i in U}
        short = {i: v for i, v in short.items() if v}
        if not short:
            if (F.bit_count(), F) < (best[0].bit_count(), best[0]):
                best[0] = F
            return
        if F.bit_count() + bound(F, short) >= best[0].bit_count():
            return
        i = max(short, key=lambda i: (short[i], -len(masks[i]), -i))
        for m in sorted(masks[i], key=lambda m: rank(m, F)):
            rec(F | m, list(short))

    root = {i: _short(m, 0) for i, m in enumerate(masks) if m}
    lower = bound(0, root) if root else 0
    proven = True
    try:
        rec(0, list(root))
    except TimeoutError:
        proven = False
    return frozenset(t for b, t in enumerate(tones) if best[0] >> b & 1), nodes, proven, lower


# ---------------------------------------------------------------------------
# pools
# ---------------------------------------------------------------------------


def subsets(seeds: tuple[int, ...]) -> list[dict]:
    return [s for s in dm.prep(seeds) if s["kind"] in g1.KINDS]


def mos_generator(seedset: str) -> str:
    """The generator GAPFILL-001's MOS-CS chose most often on this seed set
    (registered receipts; ties broken by name)."""
    picks: dict[str, int] = {}
    for line in g1.RESULTS.read_text().splitlines():
        r = json.loads(line)
        if r["seedset"] == seedset and r["method"] == "MOS-CS" and r["ok"]:
            picks[r["generator"]] = picks.get(r["generator"], 0) + 1
    return min(picks, key=lambda g: (-picks[g], g))


def window(sub: dict, gc: float) -> list[float]:
    """Every degree of the subset's DYNMOS-001 window of generator gc."""
    w = dm.first_level(sub, gc, dm.levels(gc))
    return [] if not w else [key(k * gc) for k in range(-w["mode"], -w["mode"] + w["N"])]


def own_pools(seeds: tuple[int, ...], sub: dict, gc: float) -> dict[str, dict[float, object]]:
    """Each table's pool for one subset as GAPFILL-001 would build it:
    key -> Fraction (exact) or the key itself (tempered)."""
    tones = sorted(Fraction(t) for t in sub["tones"])
    ex = lambda xs: {key(g1.cents_of(x)): x for x in xs}
    eik, gen = set(cps_scale(seeds, 3)), set(g1.genus(seeds))
    epi = set(g1.epi_pool(tones))
    mos = {k: k for k in window(sub, gc)}
    exact = ex(eik | gen | epi)
    return {"PARENT": ex(eik), "GENUS": ex(gen), "EPI": ex(epi), "EPI-AM": ex(g1.epi_fill(tones, "AM") or []),
            "EPI-HM": ex(g1.epi_fill(tones, "HM") or []), "EXACT": exact, "MOS": mos, "EXACT+MOS": {**mos, **exact}}


# ---------------------------------------------------------------------------
# one seed set
# ---------------------------------------------------------------------------


def _enum_task(args: tuple) -> tuple[list[frozenset], int, bool]:
    """A subset's completions from its own pool (so a table never covers less
    than GAPFILL-001 did) and from the whole table's pool, shared tones first."""
    tc, own, glob, prio = args
    a, na, oa = completions(tc, own)
    b, nb, ob = completions(tc, glob, prio)
    return minimal(set(a) | set(b)), na + nb, oa or ob


def table(seedset: str, name: str, subs: list[dict], owns: list[dict], workers: Pool, done: dict) -> dict:
    tcs = [sorted(s["tc"]) for s in subs]
    mine = [{k for k in o[name]} for o in owns]
    exact = {k: v for o in owns for k, v in o[name].items() if isinstance(v, Fraction)}
    glob = sorted(set().union(*mine))
    prio = {k: sum(k in m for m in mine) for k in glob}
    bare = [{key(c) for c in tc} for tc in tcs]
    jobs = [(tc, [k for k in m if k not in b], [k for k in glob if k not in b], prio)
            for tc, m, b in zip(tcs, mine, bare)]
    listed = workers.map(_enum_task, jobs)
    parts = [done[p] for p in PARTS.get(name, ())]
    comps = [minimal(set(c).union(*(p["comps"][i] for p in parts))) for i, (c, _, _) in enumerate(listed)]
    F, nodes, optimal, lower = exact_cover(comps, tuple(frozenset(p["F"]) for p in parts))
    print(f"  {seedset}/{name}: pool {len(glob)}, |F| {len(F)} (lower bound {lower}), cover nodes {nodes}, proven {optimal}",
          file=sys.stderr, flush=True)
    return {"seedset": seedset, "table": name, "pool": len(glob), "F": sorted(F), "cover_nodes": nodes,
            "optimal": optimal, "lower_bound": lower, "comps": comps, "enum_nodes": sum(n for _, n, _ in listed),
            "enum_capped": sum(o for _, _, o in listed), "exact": exact}


def assign(seedset: str, t: dict, subs: list[dict], ctx: dict) -> list[dict]:
    """Each subset's smallest completion inside F (ties: more P + S, then cents), scored."""
    rows, F = [], set(t["F"])
    for s, comps in zip(subs, t["comps"]):
        tones = sorted(Fraction(x) for x in s["tones"])
        row = {"seedset": seedset, "table": t["table"], "subset": s["name"], "kind": s["kind"],
               "n_subset": len(tones), "coverable": bool(comps),
               "own_min": min((len(c) for c in comps), default=None)}
        inside = [c for c in comps if c <= F]
        if not inside:
            rows.append({**row, "ok": False})
            continue
        scored = []
        for c in inside:
            added = [t["exact"].get(k, k) for k in sorted(c)]
            scored.append((len(c), -g1.score(tones, added, None, ctx)["PS"], sorted(c), added))
        _, _, _, added = min(scored, key=lambda x: x[:3])
        rows.append({**row, "ok": True, **g1.score(tones, added, None, ctx)})
    return rows


def neighbours(rows: list[dict], subs: list[dict]) -> dict:
    """Common tones between subsets that share tones: in the bare subsets and
    in their filled scales (the affinity strategy)."""
    by = {r["subset"]: r for r in rows if r["ok"]}
    bare = {s["name"]: {key(c) for c in s["tc"]} for s in subs}
    pairs = shared_bare = shared_filled = 0
    names = sorted(by)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if bare[a] & bare[b]:
                pairs += 1
                shared_bare += len(bare[a] & bare[b])
                shared_filled += len({key(c) for c in by[a]["scale_cents"]} & {key(c) for c in by[b]["scale_cents"]})
    return {"pairs": pairs, "mean_common_bare": round(shared_bare / pairs, 3) if pairs else None,
            "mean_common_filled": round(shared_filled / pairs, 3) if pairs else None}


def top_first(seeds: tuple[int, ...], pool: set[Fraction]) -> dict:
    """Arm C: the smallest CS superset of the eikosany from the exact pool."""
    eik = sorted(g1.cents_of(t) for t in cps_scale(seeds, 3))
    saved = (g1.N_SEARCH_MAX, g1.NODE_BUDGET)
    g1.N_SEARCH_MAX, g1.NODE_BUDGET = TOP_N_MAX, TOP_BUDGET
    try:
        got, nodes, out = g1.cs_search(eik, [g1.cents_of(p) for p in pool])
    finally:
        g1.N_SEARCH_MAX, g1.NODE_BUDGET = saved
    return {"eikosany_cs": mel.score_melodic(eik).constant_structure.is_cs,
            "eikosany_max_step": round(g1.max_step(eik), 3),
            "found": got is not None, "added": None if got is None else len(got), "nodes": nodes, "budget_exhausted": out}


def run_seedset(seedset: str, workers: Pool) -> tuple[list[dict], list[dict], dict]:
    seeds = g1.SEEDSETS[seedset]
    subs = subsets(seeds)
    ctx = {"eik": set(cps_scale(seeds, 3)), "gen": set(g1.genus(seeds))}
    gen_id = mos_generator(seedset)
    owns = [own_pools(seeds, s, dm.GENERATORS[gen_id]) for s in subs]
    done: dict[str, dict] = {}
    for name in TABLES:
        done[name] = {**table(seedset, name, subs, owns, workers, done), "generator": gen_id if "MOS" in name else None}
    tables = list(done.values())
    exact_all = {v for o in owns for v in o["EXACT"].values()}
    rows, heads = [], []
    eik = sorted(g1.cents_of(t) for t in ctx["eik"])
    for t in tables:
        rs = assign(seedset, t, subs, ctx)
        rows += rs
        whole = sorted({key(c) for c in eik} | set(t["F"]))
        ok = [r for r in rs if r["ok"]]
        summed = sum(r["own_min"] for r in rs if r["coverable"])
        heads.append({
            "seedset": seedset, "table": t["table"], "generator": t.get("generator"), "pool": t["pool"],
            "F_size": len(t["F"]), "F": [str(t["exact"][k]) if k in t["exact"] else k for k in t["F"]],
            "optimal": t["optimal"], "lower_bound": t["lower_bound"], "cover_nodes": t["cover_nodes"], "enum_capped": t["enum_capped"],
            "coverable": sum(r["coverable"] for r in rs), "covered": len(ok), "per_subset_minima_summed": summed,
            "cs": sum(r["cs"] for r in ok), "proper": sum(r["propriety"] != "improper" for r in ok),
            "strictly_proper": sum(r["propriety"] == "strictly_proper" for r in ok),
            "mean_n": round(sum(r["n"] for r in ok) / len(ok), 3) if ok else None,
            "mean_PS_gain": round(sum(r["PS_gain"] for r in ok) / len(ok), 3) if ok else None,
            "extra_over_own_min": sum(r["added"] - r["own_min"] for r in ok),
            "max_tenney": max((r["max_tenney"] for r in ok), default=0.0),
            "whole_table_n": len(whole), "whole_table_cs": mel.score_melodic(whole).constant_structure.is_cs,
            "whole_table_max_step": round(g1.max_step(whole), 3),
            "neighbours": neighbours(rs, subs),
        })
    return rows, heads, top_first(seeds, exact_all)


def write_scl(heads: list[dict]) -> list[str]:
    """The whole instrument (eikosany + F) of every canonical table."""
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    eik = sorted(g1.cents_of(t) for t in cps_scale(g1.SEEDSETS[SHOWCASE], 3))
    written = []
    for h in heads:
        if h["seedset"] != SHOWCASE or not h["covered"]:
            continue
        F = [g1.cents_of(Fraction(f)) if isinstance(f, str) else f for f in h["F"]]
        cs = sorted({key(c) for c in eik + F} - {0.0}) + [CENTS]
        # "eikosany" in the name links the canonical eikosany as the Ear Bench reference.
        path = SCL_DIR / f"{SHOWCASE}_eikosany_table_{h['table']}.scl"
        lines = [f"! {path.name}", f"{EXPERIMENT} {SHOWCASE} eikosany + shared fill table {h['table']}"
                 + (f" ({h['generator']})" if h["generator"] else "") + f", {len(F)} added tones",
                 f" {len(cs)}", "!"] + [f" {c:.4f}" for c in cs]
        path.write_text("\n".join(lines) + "\n")
        written.append(str(path.relative_to(_HERE)))
    return written


def main() -> dict:
    rows, heads, tops = [], [], {}
    with Pool(WORKERS) as workers:
        for seedset in g1.SEEDSETS:
            r, h, top = run_seedset(seedset, workers)
            rows += r
            heads += h
            tops[seedset] = top
    RESULTS_DIR.mkdir(exist_ok=True)
    with RESULTS.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    receipt = {"experiment": EXPERIMENT, "version": GAPFILL002_VERSION, "scorer_version": SCORER_VERSION,
               "melodic_version": mel.MELODIC_VERSION, "cap": g1.CAP, "min_step": g1.MIN_STEP,
               "slack": SLACK, "enum_budget": ENUM_BUDGET, "enum_limit": ENUM_LIMIT, "cover_budget": COVER_BUDGET,
               "top_n_max": TOP_N_MAX, "top_budget": TOP_BUDGET, "seedsets": g1.SEEDSETS,
               "tables": heads, "top_first": tops, "scl": write_scl(heads)}
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{'seedset/table':22s} |F| summed cover/able cs proper strict  +PS  meanN common bare>filled whole-CS opt")
    for h in receipt["tables"]:
        nb = h["neighbours"]
        print(f"{h['seedset'] + '/' + h['table']:22s} {h['F_size']:3d} {h['per_subset_minima_summed']:6d} "
              f"{h['covered']:3d}/{h['coverable']:<3d} {h['cs']:3d} {h['proper']:5d} {h['strictly_proper']:5d} "
              f"{h['mean_PS_gain']!s:6s} {h['mean_n']!s:6s} {nb['mean_common_bare']}>{nb['mean_common_filled']} "
              f"{h['whole_table_cs']!s:5s} {h['optimal']}" + (f"  {h['generator']}" if h["generator"] else ""))
    for s, t in receipt["top_first"].items():
        print(f"{s}: eikosany CS {t['eikosany_cs']}, max step {t['eikosany_max_step']}; top-first CS superset "
              f"{'found, +' + str(t['added']) if t['found'] else 'not found'} (nodes {t['nodes']}, budget out {t['budget_exhausted']})")


if __name__ == "__main__":
    _print_summary(main())
