"""Ear Bench judgment export: record shapes, dedupe across stores, append-only."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import export_judgments as ex  # noqa: E402

SCALES = {
    "s.a": {"id": "s.a", "file": "experiments/x/a.scl", "sha256": "aa"},
    "s.b": {"id": "s.b", "file": "experiments/x/b.scl", "sha256": "bb"},
}
STORE = {
    "gates": {
        "G-031": {"verdict": "pass", "notes": "B more melodic", "updatedAt": "2026-10-22T02:24:50Z"},
        "G-099": {"verdict": None, "notes": "", "updatedAt": "2026-10-22T03:00:00Z"},
    },
    "scales": {"s.a": {"gate": "G-031", "rating": 4, "note": "", "updatedAt": "2026-10-22T02:05:00Z"}},
    "comparisons": {
        "G-031__s.a__s.b": {
            "gate": "G-031", "a": "s.a", "b": "s.b", "prefer": "b", "updatedAt": "2026-10-22T04:00:00Z",
            "picks": {
                "passage:run": {"x": "a", "pick": "y", "preferred": "b", "at": "2026-10-23T04:36:59Z",
                                "context": {"timbre": "organ", "baseHz": 261.6256}},
                "passage:chorale@epiano": {"x": "b", "pick": "y", "preferred": "a", "at": "2026-10-24T21:31:18Z",
                                           "context": {"timbre": "epiano"}},
                "P:231.2,546.8,813.7": "a",
                "S:0.0,1.0,2.0": None,
            },
        }
    },
}


class TestRecords(unittest.TestCase):
    def setUp(self):
        self.recs = ex.records(STORE, "claude.ai", "marcus-w-hobbs", SCALES)
        self.by_kind = {}
        for r in self.recs:
            self.by_kind.setdefault(r["kind"], []).append(r)

    def test_kinds_and_skips_empty(self):
        self.assertEqual(sorted(self.by_kind), ["blind_preference", "chord_preference", "gate_verdict",
                                                "overall_preference", "scale_rating"])
        self.assertEqual([r["gate"] for r in self.by_kind["gate_verdict"]], ["G-031"])
        self.assertEqual(len(self.by_kind["chord_preference"]), 1)

    def test_blind_pick_keeps_mapping_context_and_scale_hashes(self):
        r = next(x for x in self.by_kind["blind_preference"] if x["passage"] == "run")
        self.assertEqual((r["passage"], r["x_was"], r["pick"], r["preferred"]), ("run", "a", "y", "b"))
        self.assertTrue(r["blind"])
        self.assertEqual(r["context"]["timbre"], "organ")
        self.assertEqual(r["a"]["sha256"], "aa")
        self.assertEqual(r["b"]["file"], "experiments/x/b.scl")

    def test_timbre_keyed_pick_names_passage_and_timbre(self):
        picks = {r["passage"]: r for r in self.by_kind["blind_preference"]}
        self.assertEqual(picks["chorale"]["timbre"], "epiano")
        self.assertEqual(picks["run"]["timbre"], "organ")  # legacy key: timbre from context

    def test_ids_are_stable(self):
        again = ex.records(STORE, "claude.ai", "marcus-w-hobbs", SCALES)
        self.assertEqual([r["id"] for r in self.recs], [r["id"] for r in again])


class TestMerge(unittest.TestCase):
    def test_dedupes_and_never_rewrites(self):
        a = ex.records(STORE, "claude.ai", "j", SCALES)
        b = ex.records(STORE, "local", "j", SCALES)  # same docs synced into the other store
        first = ex.merge([], a + b)
        self.assertEqual(len(first), len(a))  # one judgment synced into two stores is still one judgment
        self.assertEqual({r["source"] for r in first}, {"claude.ai"})
        self.assertEqual(ex.merge(first, a + b), [])
        times = [r["at"] for r in first]
        self.assertEqual(times, sorted(times))


class TestLoaders(unittest.TestCase):
    def test_dump_and_local_layouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gates").mkdir()
            (root / "gates" / "G-031.json").write_text(json.dumps({"verdict": "fail", "updatedAt": "t"}))
            self.assertEqual(ex.load_dump(root)["gates"]["G-031"]["verdict"], "fail")
            local = root / "verdicts.json"
            local.write_text(json.dumps({"scales": {"s.a": {"rating": 3}}}))
            self.assertEqual(ex.load_local(local)["scales"]["s.a"]["rating"], 3)
            self.assertEqual(ex.load_local(root / "missing.json")["gates"], {})


if __name__ == "__main__":
    unittest.main()
