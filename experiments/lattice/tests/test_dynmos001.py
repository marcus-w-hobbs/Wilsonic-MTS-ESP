"""Unit tests for dynmos001.py (DYNMOS-001, Fork B). Written BEFORE the
first run (LOG.md pre-registration 2026-10-17). Pins: the census and the
vacuous rule on both seed sets (canonical 0 vacuous, 114 exact triads;
Marcus's 24 vacuous, 30 exact triads), the predicate on a known case
(351.444 at N = 17 keeps a canonical hexany within 9.5 cents, and a
vacuous subset is never evaluated), the level list of a generator, the
transition bookkeeping on synthetic rows, and the verdict helpers.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dynmos001 as dm  # noqa: E402


class TestObjects(unittest.TestCase):
    def test_census_and_vacuous(self):
        can = dm.prep(dm.SEEDSETS["canonical"])
        mar = dm.prep(dm.SEEDSETS["marcus"])
        self.assertEqual((len(can), len(mar)), (72, 72))
        self.assertEqual(sum(s["vacuous"] for s in can), 0)
        self.assertEqual(sum(s["vacuous"] for s in mar), 24)
        self.assertEqual(sum(s["vacuous"] for s in mar if s["kind"] == "hexany"), 12)
        self.assertEqual(sum(s["ntri"] for s in can), 684)
        self.assertEqual(sum(s["ntri"] for s in mar), 228)

    def test_genus_facts(self):
        self.assertEqual(dm.genus_facts(dm.SEEDSETS["canonical"])["exact_triads"], 114)
        f = dm.genus_facts(dm.SEEDSETS["marcus"])
        self.assertEqual((f["distinct_pc"], f["exact_triads"]), (20, 30))
        self.assertLess(f["min_step_cents"], 9.0)

    def test_levels(self):
        self.assertEqual(dm.levels(351.444), [7, 10, 17, 24, 41, 58])
        self.assertEqual(dm.levels(285.823), [5, 9, 13, 17, 21, 25, 46, 67])


class TestPredicate(unittest.TestCase):
    def test_hexany_at_17(self):
        subs = [s for s in dm.prep(dm.SEEDSETS["canonical"]) if s["kind"] == "hexany"]
        hits = [dm.best_window(s["tc"], s["tri"], 351.444, 17) for s in subs]
        kept = [h for h in hits if h]
        self.assertEqual(len(kept), 3)
        self.assertTrue(all(h["err"] <= 9.55 for h in kept))
        self.assertTrue(all(-16 <= -h["mode"] <= 0 for h in kept))

    def test_first_level_smallest(self):
        s = next(s for s in dm.prep(dm.SEEDSETS["canonical"]) if s["kind"] == "hexany")
        lv = dm.first_level(s, 497.774, dm.levels(497.774))
        if lv:
            self.assertIn(lv["N"], dm.levels(497.774))
            self.assertIsNone(dm.best_window(s["tc"], s["tri"], 497.774, [n for n in dm.levels(497.774) if n < lv["N"]][-1]) if lv["N"] > 5 else None)

    def test_marcus238186_keeps_nothing_at_levels(self):
        subs = [s for s in dm.prep(dm.SEEDSETS["canonical"]) if not s["vacuous"]][:10]
        for s in subs:
            self.assertIsNone(dm.first_level(s, 285.823, dm.levels(285.823)))


class TestTransitions(unittest.TestCase):
    def test_kept_vs_retuned(self):
        subs = [{"name": "a", "kind": "dekany_in", "tones": ["1", "3", "5"]}, {"name": "b", "kind": "dekany_out", "tones": ["3", "5", "7"]},
                {"name": "c", "kind": "dekany_in", "tones": ["11", "13"]}]
        rows = [{"level": {"N": 10, "assign": [0, 1, 4], "mode": 0, "err": 1}}, {"level": {"N": 12, "assign": [1, 5, 2], "mode": 0, "err": 1}},
                {"level": None}]
        tr = dm.transitions(subs, rows)
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["common"], tr[0]["kept"], tr[0]["retuned"], tr[0]["dN"]), (2, 1, 1, 2))


def _row(g, seeds, hexN, dekN, trans=(0, 0, 0, 0)):
    subs = []
    for n in hexN:
        subs.append({"name": f"h{n}", "kind": "hexany", "ntri": 6, "vacuous": False, "level": {"N": n, "err": 5.0, "assign": [], "mode": 0}, "any": {"N": n, "err": 5.0, "assign": [], "mode": 0}})
    for n in dekN:
        subs.append({"name": f"d{n}", "kind": "dekany_in", "ntri": 20, "vacuous": False, "level": {"N": n, "err": 5.0, "assign": [], "mode": 0}, "any": {"N": n, "err": 5.0, "assign": [], "mode": 0}})
    aff, ret, com, con = trans
    tr = [{"common": 4, "kept": 4, "retuned": 0, "Na": 62, "Nb": 67, "dN": 5} for _ in range(aff)] + [{"common": 0, "kept": 0, "retuned": 0, "Na": 62, "Nb": 62, "dN": 0} for _ in range(con)]
    if aff:
        tr[0]["retuned"] = ret; tr[0]["kept"] = 4 - ret
    return {"generator": g, "seeds": seeds, "subsets": subs, "transitions": tr, "genus": {"exact_triads": 114 if seeds == "canonical" else 30}}


class TestVerdicts(unittest.TestCase):
    def test_p_d3_on_registered_shape(self):
        p = dm.PREDICTIONS["P-D3"]
        rows = []
        for g in dm.GENERATORS:
            hexN = [n for n, c in p["hexN"].get(g, {}).items() for _ in range(c)]
            dekN = [n for n, c in p["dekN"].get(g, {}).items() for _ in range(c)]
            rows.append(_row(g, "canonical", hexN, dekN))
        self.assertTrue(dm.verdict_p_d3(rows)["kept"])
        rows[4]["subsets"][0]["level"]["N"] = 10    # sub351444's first hexany now at 10: min hexany level moves
        self.assertFalse(dm.verdict_p_d3(rows)["kept"])

    def test_coverage_counts(self):
        r = _row("x", "canonical", [17, 17, 24], [41])
        c = dm.coverage(r)
        self.assertEqual((c["hexany"], c["dekany"], c["incidences"]), ((3, 3), (1, 1), (38, 38)))
        self.assertEqual(c["hexN"], {17: 2, 24: 1})


if __name__ == "__main__":
    unittest.main()
