"""Generator explorer: the palette, and generator.js against registered results."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import palette  # noqa: E402


class TestPalette(unittest.TestCase):
    def test_dense_golden_palette(self):
        p = palette.build()
        gs = [n["g"] for n in p["nobles"]]
        self.assertEqual(p["count"], len(gs))
        self.assertGreaterEqual(p["count"], 1024)
        self.assertEqual(gs, sorted(gs))
        self.assertTrue(all(0 < g <= 0.5 for g in gs))
        self.assertTrue(all(n["complexity"] <= palette.COMPLEXITY_MAX for n in p["nobles"]))

    def test_written_palette_matches_build(self):
        written = json.loads(palette.OUT.read_text(encoding="utf-8"))
        self.assertEqual(written["count"], palette.build()["count"])


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class TestGeneratorJs(unittest.TestCase):
    def test_reproduces_registered_results(self):
        run = subprocess.run(["node", str(HERE / "generator_check.js")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr or run.stdout)


if __name__ == "__main__":
    unittest.main()
