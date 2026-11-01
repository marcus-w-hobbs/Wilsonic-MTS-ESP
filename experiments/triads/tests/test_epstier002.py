"""EPS-TIER-002 goldens (G-027), written before the first run: tiers derived
from the EAR-eps receipt, the collapse filter (identity, lowest member kept,
octave wrap into the root, single linkage), per-class scoring matching the
frozen scorer, the LOCK rail against EPS-TIER-001, and the .scl reader."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import epstier002 as et  # noqa: E402
import scorer  # noqa: E402
from families.mos import mos_scales  # noqa: E402


def receipt(a, b, c):
    th = {}
    for fam, (s, f) in (("A", a), ("B", b), ("C", c)):
        th[f"{fam}-sharp"] = {"T": s, "censored": None if s is not None else "T > 8"}
        th[f"{fam}-flat"] = {"T": f, "censored": None if f is not None else "T > 8"}
    return {"thresholds": th}


class TestTiers(unittest.TestCase):
    def test_stricter_side_of_each_family(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.json"
            p.write_text(json.dumps(receipt((10.0, 8.43), (None, 4.0), (7.43, 13.5))))
            t = et.tiers(p)
        self.assertEqual(t["EAR"], (8.43, 7.43))
        self.assertEqual(t["EAR5"], (4.0, 4.0))
        self.assertEqual(t["LOCK"], (2.0, 2.0))
        self.assertEqual((t["ET5"], t["ET7"]), ((14.86, 14.86), (32.01, 32.01)))

    def test_real_receipt_gives_the_agreed_ear_tier(self):
        self.assertEqual(et.tiers()["EAR"], (8.43, 7.43))


class TestCollapse(unittest.TestCase):
    def test_identity_when_steps_are_wide(self):
        s = (0.0, 200.0, 400.0, 500.0, 700.0, 900.0, 1100.0)
        self.assertEqual(et.collapse(s, 8.43), s)

    def test_close_pair_keeps_the_lower(self):
        self.assertEqual(et.collapse((0.0, 300.0, 305.0, 700.0), 8.43), (0.0, 300.0, 700.0))

    def test_wrap_merges_into_the_root(self):
        self.assertEqual(et.collapse((0.0, 400.0, 1195.0), 8.43), (0.0, 400.0))

    def test_single_linkage_chains(self):
        self.assertEqual(et.collapse((0.0, 500.0, 506.0, 512.0, 900.0), 8.43), (0.0, 500.0, 900.0))

    def test_strictly_closer_than_eps(self):
        self.assertEqual(et.collapse((0.0, 300.0, 308.43), 8.43), (0.0, 300.0, 308.43))


class TestScoring(unittest.TestCase):
    def test_equal_eps_matches_the_frozen_scorer(self):
        s = mos_scales(500.0 / 1200.0)[12]
        r = scorer.score_tempered(s, 14.86)
        got = et.score_tier(s, (14.86, 14.86), collapsed=False)
        self.assertEqual(got["PSG"], [r.proportional, r.subcontrary, r.geometric])

    def test_per_class_reads_p_and_s_from_their_own_eps(self):
        s = mos_scales(497.0 / 1200.0)[17]
        got = et.score_tier(s, (8.43, 7.43), collapsed=False)
        self.assertEqual(got["PSG"][0], scorer.score_tempered(s, 8.43).proportional)
        self.assertEqual(got["PSG"][1], scorer.score_tempered(s, 7.43).subcontrary)

    def test_lock_rail_12edo(self):
        s = mos_scales(500.0 / 1200.0)[12]
        self.assertEqual(et.score_tier(s, (2.0, 2.0), collapsed=False)["PSG"], [12, 12, 72])


class TestScl(unittest.TestCase):
    def test_reads_cents_and_ratios(self):
        text = "! x.scl\n!\nTest\n 3\n!\n 386.313714\n 3/2\n 2/1\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.scl"
            p.write_text(text)
            cents = et.read_scl(p)
        self.assertEqual(len(cents), 3)
        self.assertAlmostEqual(cents[0], 0.0)
        self.assertAlmostEqual(cents[1], 386.313714)
        self.assertAlmostEqual(cents[2], 701.955001, places=5)

    def test_every_gate_folder_has_its_auditions(self):
        counts = {g: len(et.gate_files(g)) for g in et.GATE_FOLDERS}
        self.assertEqual(counts, {"G-028": 9, "G-030": 6, "G-033": 3, "G-035": 2,
                                  "G-036": 6, "G-037": 3, "G-039": 3})


if __name__ == "__main__":
    unittest.main()
