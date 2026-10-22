"""Ear Bench bundler: Scala parsing, ledger parsing, gate linkage."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bundle  # noqa: E402

CENTS_SCL = """! demo.scl
!
Demo chain, N = 3
 3
!
 116.675544
 233.351089
 1200.000000
"""

RATIO_SCL = """! CPS(4,2) seeds 1-3-5-7
!
! RECREATE IN WILSONIC:
!   Design: Combination Product Sets
!
CPS(4,2) seeds 1-3-5-7
 3
!
 8/7
 3
 2/1
"""

LEDGER = """| ID | Opened | Gate | Status |
|----|--------|------|--------|
| G-028 | 2026-10-10 | MERU-001 review; ear check of results/scl/meru001/ | PENDING — does the lock window sound like the seed? |
| G-012 | 2026-07-28 | CS-EIK-001 review, see [PR #28](https://x/28) | PASS 2026-07-29 — merged |
| G-099 | 2026-10-20 | `results/scl/a_b/` and results/scl/c1 | QUEUED (needs G-028) |
"""


class TestParseScl(unittest.TestCase):
    def test_cents_lines(self):
        parsed = bundle.parse_scl(CENTS_SCL)
        self.assertEqual(parsed["description"], "Demo chain, N = 3")
        self.assertEqual(parsed["cents"], [116.675544, 233.351089, 1200.0])
        self.assertIsNone(parsed["ratios"])
        self.assertEqual(parsed["comments"], ["demo.scl"])

    def test_ratio_and_integer_lines(self):
        parsed = bundle.parse_scl(RATIO_SCL)
        self.assertEqual(parsed["ratios"], ["8/7", "3/1", "2/1"])
        self.assertAlmostEqual(parsed["cents"][0], 231.174094, places=5)
        self.assertAlmostEqual(parsed["cents"][1], 1901.955001, places=5)
        self.assertAlmostEqual(parsed["cents"][2], 1200.0, places=6)
        self.assertIn("Design: Combination Product Sets", parsed["comments"])

    def test_short_body_rejected(self):
        with self.assertRaises(ValueError):
            bundle.parse_scl("! x\nDesc\n 3\n!\n 100.0\n")

    def test_non_positive_ratio_rejected(self):
        with self.assertRaises(ValueError):
            bundle.pitch_to_cents("0/1")


class TestGates(unittest.TestCase):
    def setUp(self):
        self.gates = bundle.parse_gates(LEDGER)

    def test_rows_and_states(self):
        self.assertEqual([g["id"] for g in self.gates], ["G-028", "G-012", "G-099"])
        self.assertEqual([g["state"] for g in self.gates], ["PENDING", "PASS", "QUEUED"])

    def test_links_stripped(self):
        self.assertEqual(self.gates[1]["gate"], "CS-EIK-001 review, see PR #28")

    def test_folders_found(self):
        self.assertEqual(self.gates[0]["folders"], ["meru001"])
        self.assertEqual(self.gates[2]["folders"], ["a_b", "c1"])

    def test_folder_map_prefers_ledger_then_extras(self):
        mapping = bundle.folder_gate_map(self.gates)
        self.assertEqual(mapping["meru001"], "G-028")
        self.assertEqual(mapping["eareps"], "G-025")
        self.assertEqual(mapping["g012"], "G-012")


class TestScaleId(unittest.TestCase):
    def test_brackets_and_equals_replaced(self):
        sid = bundle.scale_id("lattice", "dynmos001", "x_hexany[in=5,out=7]")
        self.assertEqual(sid, "lattice.dynmos001.x_hexany_in_5_out_7_")


class TestReference(unittest.TestCase):
    def ref(self, name, desc="", folder="cpsfit001", module="lattice", names=()):
        scale = {"name": name, "description": desc, "folder": folder, "module": module}
        return bundle.reference_for(scale, set(names))

    def test_hexany_dekany_eikosany(self):
        self.assertEqual(self.ref("cpsfit001_hexany_N22_g193.79"), bundle.HEXANY_1357)
        self.assertEqual(self.ref("meru001_fib_LIFT_W7_n018_lock", "Fibonacci; hexany seeds; window"), bundle.HEXANY_1357)
        self.assertEqual(self.ref("cpsfit003_dek52_N26_g498.066"), bundle.DEKANY_13579)
        self.assertEqual(self.ref("subfit002_eikosany_cap20_N41_mos_g351.444"), bundle.EIKOSANY_CANONICAL)

    def test_subset_hexany_prefers_census_scale(self):
        census = "lattice.subsetmel000.sm000_1-3-5-7-9-11_hexany_in5_out7_melodic1"
        got = self.ref("dynmos001_canonical_sub351444_N17_hexany[in=5,out=7]", folder="dynmos001", names=[census])
        self.assertEqual(got, census)
        missing = self.ref("dynmos001_canonical_sub497774_N29_hexany[in=11,out=5]", folder="dynmos001")
        self.assertEqual(missing, bundle.EIKOSANY_CANONICAL)

    def test_no_reference_for_other_seeds_or_library(self):
        self.assertIsNone(self.ref("dynmos001_marcus_sub316778_N15_dekany_in[in=1,out=none]", folder="dynmos001"))
        self.assertIsNone(self.ref("CPS_4_2_N6_1-3-5-7", folder="triads", module="triads"))
        self.assertIsNone(self.ref("eareps_A_01", folder="eareps"))


class TestCollect(unittest.TestCase):
    def test_tree_walk_links_gate_and_blind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meru = root / "lattice" / "results" / "scl" / "meru001"
            blind = root / "lattice" / "results" / "scl" / "eareps"
            meru.mkdir(parents=True)
            blind.mkdir(parents=True)
            (meru / "a.scl").write_text(CENTS_SCL)
            (blind / "eareps_A_01.scl").write_text(CENTS_SCL)
            gates_md = root / "GATES.md"
            gates_md.write_text(LEDGER)
            result = bundle.build_bundle(root, gates_md)
        by_name = {s["name"]: s for s in result["scales"]}
        self.assertEqual(by_name["a"]["gate"], "G-028")
        self.assertFalse(by_name["a"]["blind"])
        self.assertTrue(by_name["eareps_A_01"]["blind"])
        self.assertEqual(by_name["eareps_A_01"]["protocol"], "eareps")
        self.assertEqual({g["id"] for g in result["gates"]}, {"G-028"})


if __name__ == "__main__":
    unittest.main()
