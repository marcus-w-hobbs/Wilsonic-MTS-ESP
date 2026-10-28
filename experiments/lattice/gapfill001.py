"""GAPFILL-001 — gap-filling methods for Euler-genus subsets, side by side
(LOG.md pre-registration 2026-10-27; committed before this file).

Marcus (2026-10-27): "let's accumulate methods for filling in gaps, explore
the tradeoffs. the goal is to embrace the JI harmony and create amazing
melodies." A subset keeps its exact just tones and a method adds tones until
no step is wider than CAP cents. A method is a POOL (where candidate tones
come from) and a SELECTOR (how they are chosen):

  pools     PARENT  exact tones of the parent eikosany (common tones)
            GENUS   exact tones of the whole Euler genus (all seed products)
            EPI     exact split points: arithmetic mean (AM), harmonic mean
                    (HM) or mediant (MED) of a gap's endpoints, recursively
                    (Archytas / Ptolemy division; Stern-Brocot for MED)
            REC     exact terms of a MERU-001 recurrence seeded with the subset
            MOS     degrees of the DYNMOS-001 window of a fixed generator
                    (tempered)
  selectors GREEDY  constructive: fill the widest gap first (plugin-shaped)
            CS      the smallest constant-structure superset inside the pool,
                    gap-directed iterative deepening under a node budget
  reference MOS-PURE the DYNMOS-001 window itself (the subset retuned)

Every result is scored the same way: frozen triads v1.1.0 (score_tempered,
2 cents), frozen melodic v0.1.0 (M1 gap classes, M2 constant structure at
0.5 cents, M3 propriety), plus the cost of the added tones (exact or
tempered, Tenney height, membership in the eikosany and the genus).

Frozen inputs (read-only, CI-enforced):
  experiments/triads/scorer.py   v1.1.0  (score_tempered)
  experiments/lattice/melodic.py v0.1.0  (score_melodic)
Read-only helpers: subsetmel000.enumerate_subsets, dynmos001 (generators,
prep, first_level), meru001 (recurrences, seeding).

Receipts: results/gapfill001.jsonl (one row per seed set x subset x method)
+ results/gapfill001_summary.json; results/scl/gapfill001/*.scl. Stdlib
only, deterministic, no wall-clock fields; two runs must be bit-identical.

Run from experiments/lattice/:  python3.12 gapfill001.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import combinations
from math import log2, prod
from multiprocessing import Pool
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TRIADS_DIR = _HERE.parent / "triads"
for _p in (str(_HERE), str(_TRIADS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import dynmos001 as dm  # noqa: E402
import melodic as mel  # noqa: E402
import meru001 as mr  # noqa: E402
from families.cps import cps_scale  # noqa: E402
from scorer import SCORER_VERSION, score_tempered  # noqa: E402

GAPFILL001_VERSION = "1.0.1"   # 1.0.1: search CS test uses M2's cluster-start rule exactly (was chained linkage); 2 flagship MOS rows move, no prediction changes
EXPERIMENT = "GAPFILL-001"
RESULTS_DIR = _HERE / "results"
RESULTS = RESULTS_DIR / "gapfill001.jsonl"
SUMMARY = RESULTS_DIR / "gapfill001_summary.json"
SCL_DIR = RESULTS_DIR / "scl" / "gapfill001"

CENTS = 1200.0
CAP = 160.0          # widest step allowed after filling
MIN_STEP = 20.0      # an added tone stays this far from every tone already there
EPS_LOCK = 2.0       # triad tier (G-026)
CS_EPS = mel.DEFAULT_CS_EPSILON_CENTS   # 0.5 cents, the frozen M2 default
N_SEARCH_MAX = 24    # CS search never grows a scale past this
NODE_BUDGET = 200_000
REC_STEPS = 130      # terms generated per recurrence (MERU-001)
REC_POOL = 60        # recurrence terms offered to the CS search
WORKERS = 8
KINDS = ("hexany", "dekany_in", "dekany_out")
SEEDSETS = {"canonical": (1, 3, 5, 7, 9, 11), "flagship": (1, 7, 9, 11, 15, 29),
            "marcus": (1, 45, 135, 225, 19, 377)}
METHODS = ("PARENT-CS", "GENUS-GREEDY", "GENUS-CS", "EPI-AM", "EPI-HM", "EPI-MED", "EPI-CS",
           "REC-GREEDY", "REC-CS", "MOS-GREEDY", "MOS-CS", "MOS-PURE")
EXACT_METHODS = ("PARENT-CS", "GENUS-GREEDY", "GENUS-CS", "EPI-AM", "EPI-HM", "EPI-MED", "EPI-CS",
                 "REC-GREEDY", "REC-CS")
LOW_HEIGHT_METHODS = ("PARENT-CS", "GENUS-GREEDY", "GENUS-CS", "EPI-AM", "EPI-HM", "EPI-MED", "EPI-CS")
SHOWCASE = (("canonical", "hexany[in=9,out=11]"), ("canonical", "dekany_in[in=1,out=none]"))


# ---------------------------------------------------------------------------
# exact pitch helpers
# ---------------------------------------------------------------------------


def red(x: Fraction) -> Fraction:
    x = Fraction(x)
    while x >= 2:
        x /= 2
    while x < 1:
        x *= 2
    return x


def cents_of(x) -> float:
    return CENTS * log2(float(x))


def tenney(x: Fraction) -> float:
    return log2(x.numerator * x.denominator)


def genus(seeds: tuple[int, ...]) -> list[Fraction]:
    return sorted({red(prod(c)) for r in range(len(seeds) + 1) for c in combinations(seeds, r)})


def gaps(cs: list[float]) -> list[tuple[float, float]]:
    """Circular gaps (lo, hi) of sorted cents; the last one wraps past 1200."""
    return [(a, b) for a, b in zip(cs, cs[1:])] + [(cs[-1], cs[0] + CENTS)]


def widest(cs: list[float]) -> tuple[float, float]:
    return max(gaps(cs), key=lambda g: (g[1] - g[0], -g[0]))


def max_step(cs: list[float]) -> float:
    return max(b - a for a, b in gaps(cs))


def inside(c: float, lo: float, hi: float) -> bool:
    """c (mod 1200) lies in the gap at least MIN_STEP from both ends."""
    c = c % CENTS
    if c < lo:
        c += CENTS
    return lo + MIN_STEP <= c <= hi - MIN_STEP


def clear_of(c: float, cs: list[float]) -> bool:
    return all(dm.circ(c, x) >= MIN_STEP for x in cs)


def is_cs(cs: list[float]) -> bool:
    """Search-time CS test with the frozen M2 semantics: sorted interval sizes
    join the open cluster while within CS_EPS cents of its first member, and
    a cluster subtended by two step counts is a violation. M2 itself is the
    verdict in the receipt."""
    n = len(cs)
    ivs = sorted(((cs[(i + k) % n] - cs[i]) % CENTS, k) for k in range(1, n) for i in range(n))
    spans, first = set(), None
    for v, k in ivs:
        if first is None or v - first > CS_EPS:
            spans, first = set(), v
        spans.add(k)
        if len(spans) > 1:
            return False
    return True


# ---------------------------------------------------------------------------
# selectors
# ---------------------------------------------------------------------------


def need(cs: list[float]) -> int:
    """Lower bound on the tones still needed to bring every gap under CAP."""
    return sum(max(0, -(-int(b - a) // int(CAP)) - 1) for a, b in gaps(cs))


def cs_search(base: list[float], pool: list[float]) -> tuple[list[float] | None, int, bool]:
    """Smallest CS superset of base from pool with every step <= CAP.
    Returns (added cents or None, nodes used, budget exhausted)."""
    pool = sorted(p % CENTS for p in pool if clear_of(p, base))
    nodes = 0

    def dfs(cs: list[float], added: list[float], left: int, start: int):
        nonlocal nodes
        nodes += 1
        if nodes > NODE_BUDGET:
            raise TimeoutError
        if need(cs) > left:
            return None
        if max_step(cs) <= CAP:
            if is_cs(cs):
                return added
            cands = [i for i in range(start, len(pool)) if clear_of(pool[i], cs)]
        else:
            lo, hi = widest(cs)
            mid = (lo + hi) / 2
            cands = sorted((i for i, p in enumerate(pool) if inside(p, lo, hi) and clear_of(p, cs)),
                           key=lambda i: (abs(((pool[i] - lo) % CENTS) + lo - mid), pool[i]))
        if left == 0:
            return None
        for i in cands:
            got = dfs(sorted(cs + [pool[i]]), added + [pool[i]], left - 1,
                      i + 1 if max_step(cs) <= CAP else start)
            if got is not None:
                return got
        return None

    try:
        for depth in range(0, N_SEARCH_MAX - len(base) + 1):
            got = dfs(sorted(base), [], depth, 0)
            if got is not None:
                return sorted(got), nodes, False
    except TimeoutError:
        return None, nodes, True
    return None, nodes, False


def greedy(base: list[float], pool: list, key=None) -> list | None:
    """Fill the widest gap over CAP with the pool tone ranked first by key
    (default: nearest the gap centre). pool items are (cents, payload)."""
    cs, added = sorted(base), []
    while max_step(cs) > CAP:
        lo, hi = widest(cs)
        mid = (lo + hi) / 2
        cands = [it for it in pool if inside(it[0], lo, hi) and clear_of(it[0], cs)]
        if not cands:
            return None
        pick = min(cands, key=key or (lambda it: (abs(((it[0] % CENTS - lo) % CENTS) + lo - mid), it[0])))
        added.append(pick)
        cs = sorted(cs + [pick[0] % CENTS])
    return added


# ---------------------------------------------------------------------------
# pools
# ---------------------------------------------------------------------------


def split_point(a: Fraction, b: Fraction, rule: str) -> Fraction:
    if rule == "AM":
        return (a + b) / 2
    if rule == "HM":
        return 2 * a * b / (a + b)
    return Fraction(a.numerator + b.numerator, a.denominator + b.denominator)


def epi_fill(tones: list[Fraction], rule: str) -> list[Fraction] | None:
    """Split every gap wider than CAP at its AM / HM / mediant, recursively.
    AM and HM depend only on the gap ratio, so equal gaps split identically."""
    pts = sorted(set(tones))
    added = []
    while True:
        wide = [(a, b) for a, b in zip(pts, pts[1:] + [2 * pts[0]]) if cents_of(b / a) > CAP]
        if not wide:
            return added
        a, b = max(wide, key=lambda g: (b_over(g), g[0]))
        m = split_point(a, b, rule)
        if not (cents_of(m / a) >= MIN_STEP and cents_of(b / m) >= MIN_STEP):
            return None
        added.append(red(m))
        pts = sorted(set(pts) | {red(m)})


def b_over(g) -> float:
    return cents_of(g[1] / g[0])


def epi_pool(tones: list[Fraction]) -> list[Fraction]:
    out = set()
    for rule in ("AM", "HM", "MED"):
        out |= set(epi_fill(tones, rule) or [])
    return sorted(out - set(tones))


def rec_terms(tones: list[Fraction], rec: dict) -> list[Fraction]:
    coefs, order = rec["coefs_exact"], rec["j"]
    mode = "EXACT" if order <= len(tones) else "LIFT"
    seeds = mr.place_seeds(tuple(sorted(tones)), order, rec["log2G"], mode)
    h = mr.run_recurrence(coefs, seeds, REC_STEPS)
    out, seen = [], set(tones)
    for x in h[order:]:
        if x > 0:
            r = red(x)
            if r not in seen:
                seen.add(r)
                out.append(r)
    return out


def recurrences() -> list[dict]:
    return [mr.build_recurrence(rid, a, i, b, j) for rid, a, i, b, j, _ in mr.RECURRENCES]


def mos_windows(sub: dict) -> list[dict]:
    """For each DYNMOS-001 generator with a keeping level: the window."""
    out = []
    for gid, gc in dm.GENERATORS.items():
        w = dm.first_level(sub, gc, dm.levels(gc))
        if w:
            ks = range(-w["mode"], -w["mode"] + w["N"])
            free = [(k * gc) % CENTS for k in ks if k not in set(w["assign"])]
            out.append({"gen": gid, "gc": gc, "N": w["N"], "err": w["err"], "free": free,
                        "chain": sorted((k * gc) % CENTS for k in ks)})
    return out


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------


def score(tones: list[Fraction], added: list, retuned: list[float] | None, ctx: dict) -> dict:
    """added items: Fraction (exact) or float (tempered cents)."""
    base_c = [cents_of(t) for t in tones] if retuned is None else list(retuned)
    add_c = [cents_of(a) if isinstance(a, Fraction) else float(a) for a in added]
    cs = sorted(c % CENTS for c in base_c + add_c)
    tri = score_tempered(cs, EPS_LOCK)
    tri0 = score_tempered(sorted(cents_of(t) for t in tones), EPS_LOCK)
    m = mel.score_melodic(cs)
    exact = [a for a in added if isinstance(a, Fraction)]
    return {
        "n": len(cs), "added": len(added), "max_step": round(max_step(cs), 3),
        "P": tri.proportional, "S": tri.subcontrary, "PS": tri.proportional + tri.subcontrary,
        "PS_gain": tri.proportional + tri.subcontrary - tri0.proportional - tri0.subcontrary,
        "cs": m.constant_structure.is_cs, "cs_search_agrees": is_cs(cs) == m.constant_structure.is_cs,
        "propriety": m.propriety.classification, "gap_classes": m.gap_entropy.gap_class_count,
        "gap_classes_per_n": round(m.gap_entropy.gap_class_count / len(cs), 4),
        "exact_added": len(exact), "tempered_added": len(added) - len(exact),
        "subset_retuned": retuned is not None,
        "max_tenney": round(max((tenney(a) for a in exact), default=0.0), 3),
        "in_eikosany": sum(a in ctx["eik"] for a in exact), "in_genus": sum(a in ctx["gen"] for a in exact),
        "added_tones": [str(a) if isinstance(a, Fraction) else round(a, 4) for a in added],
        "scale_cents": [round(c, 4) for c in cs],
    }


# ---------------------------------------------------------------------------
# one subset, every method
# ---------------------------------------------------------------------------


def run_subset(task: tuple[str, int]) -> list[dict]:
    seedset, idx = task
    seeds = SEEDSETS[seedset]
    sub = [s for s in dm.prep(seeds) if s["kind"] in KINDS][idx]
    tones = sorted(Fraction(t) for t in sub["tones"])
    tc = [cents_of(t) for t in tones]
    ctx = {"eik": set(cps_scale(seeds, 3)), "gen": set(genus(seeds))}
    rows = []

    def emit(method, added, retuned=None, **extra):
        row = {"seedset": seedset, "subset": sub["name"], "kind": sub["kind"], "method": method,
               "n_subset": len(tones), "subset_max_step": round(max_step(sorted(tc)), 3)}
        if added is None:
            row.update({"ok": False, **extra})
        else:
            row.update({"ok": True, **score(tones, added, retuned, ctx), **extra})
        rows.append(row)

    def search(method, pool_exact=None, pool_cents=None, **extra):
        if pool_exact is not None:
            by_c = {round(cents_of(p) % CENTS, 6): p for p in pool_exact}
            got, nodes, out = cs_search(tc, list(by_c))
            added = None if got is None else [by_c[round(c, 6)] for c in got]
        else:
            got, nodes, out = cs_search(tc, pool_cents)
            added = got
        emit(method, added, nodes=nodes, budget_exhausted=out, **extra)

    search("PARENT-CS", pool_exact=sorted(ctx["eik"] - set(tones)))
    gen_pool = sorted(ctx["gen"] - set(tones))
    g = greedy(tc, [(cents_of(p), p) for p in gen_pool],
               key=lambda it: (tenney(it[1]), it[0]))
    emit("GENUS-GREEDY", None if g is None else [p for _, p in g])
    search("GENUS-CS", pool_exact=gen_pool)
    for rule in ("AM", "HM", "MED"):
        emit(f"EPI-{rule}", epi_fill(tones, rule))
    search("EPI-CS", pool_exact=epi_pool(tones))

    best = None
    for rec in recurrences():
        terms = rec_terms(tones, rec)
        g = greedy(tc, [(cents_of(t), (n, t)) for n, t in enumerate(terms)],
                   key=lambda it: it[1][0])
        if g is not None and (best is None or len(g) < len(best[1])):
            best = (rec, g, terms)
    if best:
        emit("REC-GREEDY", [t for _, (_, t) in best[1]], recurrence=best[0]["id"])
        search("REC-CS", pool_exact=best[2][:REC_POOL], recurrence=best[0]["id"])
    else:
        emit("REC-GREEDY", None)
        emit("REC-CS", None)

    wins = mos_windows(sub)
    bestm = None
    for w in wins:
        g = greedy(tc, [(c, c) for c in w["free"]])
        if g is not None and (bestm is None or (len(g), w["N"]) < (len(bestm[1]), bestm[0]["N"])):
            bestm = (w, g)
    if bestm:
        emit("MOS-GREEDY", [c for _, c in bestm[1]], generator=bestm[0]["gen"], level=bestm[0]["N"])
        search("MOS-CS", pool_cents=bestm[0]["free"], generator=bestm[0]["gen"], level=bestm[0]["N"])
    else:
        emit("MOS-GREEDY", None)
        emit("MOS-CS", None)
    if wins:
        w = min(wins, key=lambda w: (w["N"], w["err"]))
        emit("MOS-PURE", [], retuned=w["chain"], generator=w["gen"], level=w["N"])
    else:
        emit("MOS-PURE", None)
    return rows


# ---------------------------------------------------------------------------
# summary + exports
# ---------------------------------------------------------------------------


def summarize(rows: list[dict]) -> dict:
    out = {}
    for seedset in SEEDSETS:
        for method in METHODS:
            rs = [r for r in rows if r["seedset"] == seedset and r["method"] == method]
            ok = [r for r in rs if r["ok"]]
            mean = lambda k: round(sum(r[k] for r in ok) / len(ok), 3) if ok else None
            out[f"{seedset}/{method}"] = {
                "subsets": len(rs), "filled": len(ok), "cs": sum(r["cs"] for r in ok),
                "proper": sum(r["propriety"] != "improper" for r in ok),
                "mean_n": mean("n"), "mean_added": mean("added"), "mean_PS_gain": mean("PS_gain"),
                "mean_max_tenney": mean("max_tenney"), "tempered_rows": sum(r["tempered_added"] > 0 or r["subset_retuned"] for r in ok),
                "all_added_in_eikosany": sum(r["added"] > 0 and r["in_eikosany"] == r["added"] for r in ok),
                "cs_search_disagreements": sum(not r["cs_search_agrees"] for r in ok),
                "budget_exhausted": sum(r.get("budget_exhausted", False) for r in rs),
            }
    for seedset in SEEDSETS:
        subs = sorted({r["subset"] for r in rows if r["seedset"] == seedset})
        cs_by = {s: {r["method"] for r in rows if r["seedset"] == seedset and r["subset"] == s and r["ok"] and r["cs"]}
                 for s in subs}
        parent = {s for s in subs if "PARENT-CS" in cs_by[s]}
        out[f"{seedset}/coverage"] = {
            "subsets": len(subs), "cs_parent": len(parent),
            "cs_exact_ji": sum(bool(cs_by[s] & set(EXACT_METHODS)) for s in subs),
            "cs_exact_ji_low_height": sum(bool(cs_by[s] & set(LOW_HEIGHT_METHODS)) for s in subs),
            "cs_any": sum(bool(cs_by[s]) for s in subs),
            "parent_holdouts": [s for s in subs if s not in parent],
            "holdouts_rescued_by": {s: sorted(cs_by[s]) for s in subs if s not in parent},
        }
    out["am_hm_mirror"] = mirror_check(rows)
    return out


def partner(name: str) -> str:
    """The inversion partner inside the same family (hexany x in y out <-> y in x out;
    dekany in x <-> dekany out x)."""
    kind, rest = name.split("[")
    a, b = (part.split("=")[1] for part in rest.rstrip("]").split(","))
    if kind == "hexany":
        return f"hexany[in={b},out={a}]"
    if kind == "dekany_in":
        return f"dekany_out[in=none,out={a}]"
    return f"dekany_in[in={b},out=none]"


def mirrored(a: list[float], b: list[float], tol: float = 0.01) -> bool:
    sa = [y - x for x, y in zip(a, a[1:] + [a[0] + CENTS])]
    sb = [y - x for x, y in zip(b, b[1:] + [b[0] + CENTS])][::-1]
    return any(all(abs(x - y) < tol for x, y in zip(sa, sb[i:] + sb[:i])) for i in range(len(sb)))


def mirror_check(rows: list[dict]) -> dict:
    """EPI-AM of a subset against EPI-HM of its inversion partner."""
    idx = {(r["seedset"], r["subset"], r["method"]): r for r in rows}
    pairs = mirror = swap = 0
    for (s, n, m), r in idx.items():
        q = idx.get((s, partner(n), "EPI-HM"))
        if m == "EPI-AM" and r["ok"] and q and q["ok"]:
            pairs += 1
            mirror += mirrored(r["scale_cents"], q["scale_cents"])
            swap += (r["P"], r["S"], r["cs"], r["propriety"]) == (q["S"], q["P"], q["cs"], q["propriety"])
    return {"pairs": pairs, "steps_mirrored": mirror, "P_S_swapped_cs_propriety_equal": swap}


def write_scl(rows: list[dict]) -> list[str]:
    SCL_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for seedset, name in SHOWCASE:
        for r in rows:
            if r["seedset"] == seedset and r["subset"] == name and r["ok"]:
                safe = name.replace("[", "_").replace("]", "").replace("=", "").replace(",", "_")
                path = SCL_DIR / f"{seedset}_{safe}_{r['method']}.scl"
                cs = [c for c in r["scale_cents"] if c > 0] + [CENTS]
                lines = [f"! {path.name}", f"{EXPERIMENT} {seedset} {name} filled by {r['method']}",
                         f" {len(cs)}", "!"] + [f" {c:.4f}" for c in cs]
                path.write_text("\n".join(lines) + "\n")
                written.append(str(path.relative_to(_HERE)))
    return written


def tasks() -> list[tuple[str, int]]:
    out = []
    for seedset, seeds in SEEDSETS.items():
        n = sum(s["kind"] in KINDS for s in dm.prep(seeds))
        out += [(seedset, i) for i in range(n)]
    return out


def main() -> dict:
    with Pool(WORKERS) as p:
        rows = [r for rs in p.map(run_subset, tasks()) for r in rs]
    RESULTS_DIR.mkdir(exist_ok=True)
    with RESULTS.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    receipt = {"experiment": EXPERIMENT, "version": GAPFILL001_VERSION, "scorer_version": SCORER_VERSION,
               "melodic_version": mel.MELODIC_VERSION, "cap": CAP, "min_step": MIN_STEP, "eps_lock": EPS_LOCK,
               "node_budget": NODE_BUDGET, "n_search_max": N_SEARCH_MAX, "seedsets": SEEDSETS,
               "summary": summarize(rows), "scl": write_scl(rows)}
    SUMMARY.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def _print_summary(receipt: dict) -> None:
    print(f"{'seedset/method':28s} filled  cs proper  meanN  +PS  tenney temp eik")
    for k, v in receipt["summary"].items():
        if k.endswith("/coverage") or k == "am_hm_mirror":
            continue
        print(f"{k:28s} {v['filled']:3d}/{v['subsets']:<3d} {v['cs']:3d} {v['proper']:4d}  {v['mean_n']!s:6s} "
              f"{v['mean_PS_gain']!s:6s} {v['mean_max_tenney']!s:7s} {v['tempered_rows']:3d} {v['all_added_in_eikosany']:3d}"
              + (f"  budget-out {v['budget_exhausted']}" if v["budget_exhausted"] else ""))
    for s in SEEDSETS:
        c = receipt["summary"][f"{s}/coverage"]
        print(f"{s}: CS from parent {c['cs_parent']}/{c['subsets']}, exact low-height {c['cs_exact_ji_low_height']}, "
              f"exact any {c['cs_exact_ji']}, any {c['cs_any']}")
        for h, ms in c["holdouts_rescued_by"].items():
            print(f"   holdout {h}: {', '.join(ms) or 'none'}")
    print("AM/HM mirror:", receipt["summary"]["am_hm_mirror"])


if __name__ == "__main__":
    _print_summary(main())
