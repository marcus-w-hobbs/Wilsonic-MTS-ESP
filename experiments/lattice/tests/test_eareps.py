"""Unit tests for eareps.py (EAR-ε) — ladder math, the |δ|-deviation
identity, per-rung frozen-scorer rails, guard margins, .scl syntax and
no-provenance blinding, shuffle determinism, and the family-D anchors
against ET-001's numbers. Written and green BEFORE the first stimulus
generation run (LOG.md pre-registration, 2026-08-19).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from math import log2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import eareps as ee  # noqa: E402

from scorer import (  # noqa: E402  (frozen v1.1.0, read-only referee)
    PROPORTIONAL,
    SUBCONTRARY,
    mean_separation_cents,
)

CULTURAL_EPS = 14.859021711645774        # ET-001: 1200*log2((2^(-1/3)+2^(1/4))/2)
FIFTH_ERROR = 1.9550008653873192         # ET-001: 1200*log2(3) - 1900


class TestLadders(unittest.TestCase):
    def test_third_ladder_literals(self):
        self.assertEqual(ee.LADDER_THIRD_MAGS,
                         (2.0, 5.0, 8.0, 11.0, 14.86, 18.0, 22.0))

    def test_fifth_ladder_literals(self):
        self.assertEqual(len(ee.LADDER_FIFTH_MAGS), 5)
        self.assertEqual(ee.LADDER_FIFTH_MAGS[0], 1.0)
        self.assertAlmostEqual(ee.LADDER_FIFTH_MAGS[1], FIFTH_ERROR,
                               places=12)
        self.assertEqual(ee.LADDER_FIFTH_MAGS[2:], (3.0, 5.0, 8.0))

    def test_ladder_expansion(self):
        lad = ee.ladder((2.0, 5.0))
        self.assertEqual(lad, (0.0, 2.0, -2.0, 5.0, -5.0))

    def test_just_anchors(self):
        self.assertAlmostEqual(ee.M3_CENTS, 1200 * log2(5 / 4), places=12)
        self.assertAlmostEqual(ee.m3_CENTS, 1200 * log2(6 / 5), places=12)
        self.assertAlmostEqual(ee.P5_CENTS, 1200 * log2(3 / 2), places=12)
        self.assertAlmostEqual(ee.DELTA_PC_CENTS, FIFTH_ERROR, places=12)

    def test_eps_grid_is_et001_grid(self):
        self.assertEqual(ee.EPS_GRID, (1.0, 2.0, 3.0, 5.0, 10.0, 14.86, 20.0))


class TestRungs(unittest.TestCase):
    def setUp(self):
        self.fams = ee.build_rungs()

    def test_counts(self):
        self.assertEqual(len(self.fams["A"]), 15)
        self.assertEqual(len(self.fams["B"]), 11)
        self.assertEqual(len(self.fams["C"]), 15)
        self.assertEqual(len(self.fams["D"]), 3)
        self.assertEqual(sum(len(v) for v in self.fams.values()), 44)

    def test_requested_deltas_vs_generated_cents(self):
        for rung in self.fams["A"]:
            self.assertAlmostEqual(rung.triple[1],
                                   ee.M3_CENTS + rung.delta_cents, places=9)
            self.assertEqual(rung.triple[0], 0.0)
            self.assertEqual(rung.triple[2], ee.P5_CENTS)
        for rung in self.fams["C"]:
            self.assertAlmostEqual(rung.triple[1],
                                   ee.m3_CENTS + rung.delta_cents, places=9)
        for rung in self.fams["B"]:
            self.assertAlmostEqual(rung.triple[1],
                                   ee.P5_CENTS + rung.delta_cents, places=9)
            self.assertEqual(rung.triple[2], 1200.0)

    def test_degrees_end_with_octave(self):
        for fam in self.fams.values():
            for rung in fam:
                self.assertEqual(rung.degrees[-1], 1200.0)
                # the sounding triple above the root is exactly the .scl
                # degrees (family B's triple ends at the octave itself)
                self.assertEqual(rung.triple[1:],
                                 rung.degrees[:len(rung.triple) - 1])

    def test_target_classes(self):
        for rung in self.fams["A"]:
            self.assertEqual(rung.targets, (PROPORTIONAL,))
        for rung in self.fams["C"]:
            self.assertEqual(rung.targets, (SUBCONTRARY,))
        for rung in self.fams["B"]:
            self.assertEqual(set(rung.targets), {PROPORTIONAL, SUBCONTRARY})


class TestDeviationIdentity(unittest.TestCase):
    """The detuned tone is the mean tone of its class, so the scorer's
    deviation equals |δ| exactly (up to float roundoff)."""

    def test_deviation_equals_abs_delta(self):
        fams = ee.build_rungs()
        for fam in ("A", "B", "C"):
            for rung in fams[fam]:
                for cls, triple in rung.target_triples:
                    self.assertAlmostEqual(
                        ee.deviation_cents(triple, cls),
                        abs(rung.delta_cents), places=6,
                        msg=f"{fam} delta={rung.delta_cents} cls={cls}")

    def test_family_d_anchors_match_et001(self):
        d_major, d_minor, d_power = ee.build_rungs()["D"]
        self.assertAlmostEqual(
            ee.deviation_cents(d_major.triple, PROPORTIONAL),
            CULTURAL_EPS, places=9)
        self.assertAlmostEqual(
            ee.deviation_cents(d_minor.triple, SUBCONTRARY),
            CULTURAL_EPS, places=9)
        self.assertAlmostEqual(
            ee.deviation_cents(d_power.triple, PROPORTIONAL),
            FIFTH_ERROR, places=9)


class TestScorerRails(unittest.TestCase):
    """Every rung verified against the FROZEN scorer: target class absent
    at d − 1e−6, present at d + 1e−6, full-scale count jump exactly +1."""

    def test_all_rails_pass(self):
        fams = ee.build_rungs()
        for fam, rungs in fams.items():
            for rung in rungs:
                rails = ee.rail_check(rung)
                self.assertTrue(
                    rails["rail_ok"],
                    msg=f"{fam} delta={rung.delta_cents}: {rails}")

    def test_guard_never_drops_a_rung(self):
        """Outer-pair separation exceeds every ε used (grid max 20, rails
        up to 22 + 1e−6), so no rung is degeneracy-dropped."""
        fams = ee.build_rungs()
        for rungs in fams.values():
            for rung in rungs:
                for _cls, triple in rung.target_triples:
                    sep = mean_separation_cents(triple[0], triple[2])
                    self.assertGreater(sep, 22.0 + 1e-6)

    def test_zero_delta_locks_at_epsilon_zero_plus(self):
        fams = ee.build_rungs()
        for fam in ("A", "B", "C"):
            rung = fams[fam][0]
            self.assertEqual(rung.delta_cents, 0.0)
            rails = ee.rail_check(rung)
            for cls in rung.targets:
                self.assertIn(cls, rails["classify_high"])


class TestBlinding(unittest.TestCase):
    def test_shuffle_deterministic(self):
        p1 = ee.presentation()
        p2 = ee.presentation()
        self.assertEqual(p1, p2)

    def test_shuffle_is_permutation(self):
        pres = ee.presentation()
        fams = ee.build_rungs()
        for fam in ee.BLOCK_ORDER:
            self.assertEqual(sorted(pres[fam]), sorted(fams[fam]))

    def test_shuffle_actually_shuffles(self):
        pres = ee.presentation()
        fams = ee.build_rungs()
        for fam in ("A", "B", "C"):
            self.assertNotEqual(pres[fam], fams[fam])

    def test_scl_text_is_blind(self):
        """No provenance in the stimulus files: no ratios, no family
        words, no delta values or signs beyond the raw pitch lines."""
        text = ee.scl_text("eareps_A_07", (388.31371, 701.955, 1200.0))
        low = text.lower()
        for forbidden in ("delta", "detun", "major", "minor", "power",
                          "just", "4:5:6", "10:12:15", "2:3:4", "third",
                          "fifth", "cents from"):
            self.assertNotIn(forbidden, low)
        text.encode("ascii")   # must be pure ASCII

    def test_scl_syntax(self):
        rid = "eareps_A_07"
        degrees = (ee.M3_CENTS + 8.0, ee.P5_CENTS, 1200.0)
        text = ee.scl_text(rid, degrees)
        lines = text.splitlines()
        self.assertEqual(lines[0], f"! {rid}.scl")
        # description line = the opaque id, then the degree count
        i_desc = lines.index(rid)
        self.assertEqual(lines[i_desc + 1].strip(), str(len(degrees)))
        pitch_lines = [l for l in lines[i_desc + 2:] if not
                       l.startswith("!")]
        self.assertEqual(len(pitch_lines), len(degrees))
        self.assertEqual(pitch_lines[-1].strip(), "1200.00000")
        # generated cents round-trip: requested detuning is in the file
        self.assertAlmostEqual(float(pitch_lines[0]),
                               ee.M3_CENTS + 8.0, places=5)

    def test_rung_ids(self):
        self.assertEqual(ee.rung_id("A", 7), "eareps_A_07")
        self.assertEqual(ee.rung_id("D", 3), "eareps_D_03")


class TestAssembly(unittest.TestCase):
    def setUp(self):
        self.manifest, self.key, self.template, self.files = ee.build_all()

    def test_file_count_and_names(self):
        self.assertEqual(len(self.files), 44)
        self.assertEqual(
            sorted(self.files),
            sorted(f"{rid}.scl" for rid in self.manifest["rungs"]))

    def test_no_rail_failures(self):
        self.assertEqual(self.manifest["rail_failures"], 0)

    def test_manifest_grid_complete(self):
        for rid, row in self.manifest["rungs"].items():
            self.assertEqual(sorted(row["grid"]),
                             sorted(f"{e:g}" for e in ee.EPS_GRID))
            for cell in row["grid"].values():
                for k in ("triple_labels", "scale_P", "scale_S", "scale_G"):
                    self.assertIn(k, cell)

    def test_key_matches_manifest(self):
        self.assertEqual(sorted(self.key["rungs"]),
                         sorted(self.manifest["rungs"]))
        for rid, row in self.key["rungs"].items():
            self.assertEqual(row["delta_cents"],
                             self.manifest["rungs"][rid]["delta_cents"])

    def test_template_covers_all_rungs_in_order(self):
        self.assertEqual(list(self.template["responses"]),
                         list(self.manifest["rungs"]))
        for row in self.template["responses"].values():
            self.assertEqual(row, {"verdict": "", "fusion_1to5": None,
                                   "notes": ""})

    def test_sealed_warnings_present(self):
        self.assertIn("SEALED", self.manifest["_warning"])
        self.assertIn("SEALED", self.key["_warning"])
        self.assertNotIn("_warning", self.template)

    def test_knife_edge_flagged(self):
        flagged = [rid for rid, row in self.manifest["rungs"].items()
                   if row["knife_edge_at_14.86"]]
        self.assertEqual(len(flagged), 4)   # ±14.86 in families A and C
        for rid in flagged:
            self.assertAlmostEqual(
                abs(self.manifest["rungs"][rid]["delta_cents"]), 14.86)

    def test_block_sizes_in_presentation_order(self):
        ids = list(self.manifest["rungs"])
        self.assertTrue(all(i.startswith("eareps_B_") for i in ids[:11]))
        self.assertTrue(all(i.startswith("eareps_A_") for i in ids[11:26]))
        self.assertTrue(all(i.startswith("eareps_C_") for i in ids[26:41]))
        self.assertTrue(all(i.startswith("eareps_D_") for i in ids[41:]))

    def test_determinism_end_to_end(self):
        again = ee.build_all()
        self.assertEqual((self.manifest, self.key, self.template,
                          self.files), again)


if __name__ == "__main__":
    unittest.main()
