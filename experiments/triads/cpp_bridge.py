"""Bridge to the real-C++ research CLI (tests/research_cli).

Builds the CLI on demand (make -C tests research_cli) and exposes typed
wrappers. The CLI compiles the plugin's actual tuning sources; every scale
degree comes back with its raw IEEE-754 bits so Python-side comparisons
can be exact.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TESTS_DIR = REPO_ROOT / "tests"
CLI = TESTS_DIR / "research_cli"


def build_cli() -> None:
    result = subprocess.run(
        ["make", "-C", str(TESTS_DIR), "research_cli"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"research_cli build failed:\n{result.stderr}")


def _run(args: list[str]) -> dict:
    if not CLI.exists():
        build_cli()
    result = subprocess.run(
        [str(CLI), *args], capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"research_cli {args} failed:\n{result.stderr}")
    return json.loads(result.stdout)


def hexany(seeds: list[float]) -> dict:
    """Real plugin hexany: {'scale': [{'float', 'bits'}...],
    'proportional': N, 'subcontrary': N} (reported, post wrap-drop)."""
    if len(seeds) != 4:
        raise ValueError("hexany needs 4 seeds")
    return _run(["hexany", *[repr(float(s)) for s in seeds]])


def mos(generator: float, level: int) -> dict:
    """Real Brun MOS at murchana 0 (plugin default)."""
    return _run(["mos", repr(float(generator)), str(int(level))])
