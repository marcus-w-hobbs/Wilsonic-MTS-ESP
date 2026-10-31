"""Listening passages: compose.js against the bundled gap-fill scales."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class TestComposeJs(unittest.TestCase):
    def test_chorale_and_added_harmony(self):
        run = subprocess.run(["node", str(HERE / "compose_check.js")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr or run.stdout)


if __name__ == "__main__":
    unittest.main()
