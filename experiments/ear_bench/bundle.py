"""Ear Bench bundler: every .scl the experiments emit, tied to its gate.

Walks experiments/*/results/scl/**.scl, parses each scale (cents or
ratios), and reads experiments/GATES.md so each scale folder carries the
gate that asks Marcus to listen to it. Writes one JSON file that the Ear
Bench page (docs/ear-bench/) loads; the page never changes when a new
experiment lands, only this bundle does.

Gate linkage is read from the ledger itself: a gate row that names
`results/scl/<folder>` owns that folder. Folders whose gate names them
some other way are listed in EXTRA_FOLDER_GATES.

Blind folders (sealed keys) are flagged so the page hides their cents,
ratios and triad analysis.

Usage:
    python experiments/ear_bench/bundle.py            # writes docs/ear-bench/data.json
    python experiments/ear_bench/bundle.py --out PATH
"""

from __future__ import annotations

import argparse
import json
import math
import re
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXPERIMENTS = REPO / "experiments"
GATES_MD = EXPERIMENTS / "GATES.md"
DEFAULT_OUT = REPO / "docs" / "ear-bench" / "data.json"

BUNDLE_VERSION = "1.0.0"

# Folders whose gate row does not spell out results/scl/<folder>.
EXTRA_FOLDER_GATES = {
    "eareps": "G-025",
    "g006": "G-006",
    "g012": "G-012",
}

# Sealed-key folders: the page must not show their numbers.
BLIND_FOLDERS = {"eareps", "g006"}

# Listening protocols the page knows how to run for a folder.
FOLDER_PROTOCOLS = {"eareps": "eareps"}

# JI references the page aligns a chain against to show the lattice's own
# triads inside it. Ids are scale_id() values of scales in the bundle.
HEXANY_1357 = "triads.triads.CPS_4_2_N6_1-3-5-7"
DEKANY_13579 = "triads.triads.CPS_5_2_N10_1-3-5-7-9"
EIKOSANY_CANONICAL = "lattice.g012.canonical_eikosany_1_3_5_7_9_11"
# Default A/B for gates whose question compares two specific chains.
GATE_PAIRS = {
    "G-031": ("lattice.cpsfit002.cpsfit002_hexany_N22_g193.908", "lattice.cpsfit001.cpsfit001_hexany_N22_g193.79"),
    "G-032": ("lattice.cpsfit003.cpsfit003_hexany_N16_g116.676", "lattice.cpsfit003.cpsfit003_hexany_N18_g77.818"),
}
SUBSET_TAG = re.compile(r"hexany\[in=(\d+),out=(\d+)\]")

GATE_ROW = re.compile(r"^\|\s*(G-\d{3})\s*\|\s*([^|]*)\|(.*)\|\s*([^|]*)\|\s*$")
SCL_FOLDER_REF = re.compile(r"results/scl/([a-z0-9_]+)")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
DOC_ID_UNSAFE = re.compile(r"[^A-Za-z0-9_\-.~:@+]")


def pitch_to_cents(token: str) -> tuple[float, str | None]:
    """One Scala pitch line's first token -> (cents, ratio text or None)."""
    if "." in token:
        return float(token), None
    ratio = Fraction(token)
    if ratio <= 0:
        raise ValueError(f"non-positive ratio {token!r}")
    return 1200.0 * math.log2(ratio), f"{ratio.numerator}/{ratio.denominator}"


def parse_scl(text: str) -> dict:
    """Parse Scala text into description, comments, cents and ratios.

    The returned degrees exclude the implicit 1/1 and include the period
    line (normally 2/1 or 1200.0), exactly as the file lists them.
    """
    comments: list[str] = []
    body: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("!"):
            if not body:
                comments.append(line[1:].strip())
            continue
        body.append(line)
    if len(body) < 2:
        raise ValueError("missing description or note count")
    description, count_line = body[0], body[1]
    count = int(count_line.split()[0])
    pitch_lines = [line for line in body[2:] if line]
    if len(pitch_lines) < count:
        raise ValueError(f"declares {count} notes, lists {len(pitch_lines)}")
    cents: list[float] = []
    ratios: list[str | None] = []
    for line in pitch_lines[:count]:
        value, ratio = pitch_to_cents(line.split()[0])
        cents.append(round(value, 6))
        ratios.append(ratio)
    return {
        "description": description,
        "comments": [c for c in comments if c],
        "cents": cents,
        "ratios": ratios if any(r is not None for r in ratios) else None,
    }


def strip_markdown(text: str) -> str:
    return MD_LINK.sub(r"\1", text).replace("`", "").strip()


def parse_gates(markdown: str) -> list[dict]:
    """Ledger rows -> [{id, opened, gate, status, state, folders}]."""
    gates = []
    for line in markdown.splitlines():
        match = GATE_ROW.match(line)
        if not match:
            continue
        gate_id, opened, gate_text, status = (part.strip() for part in match.groups())
        state = status.split()[0].rstrip(":—-") if status else ""
        gates.append({
            "id": gate_id,
            "opened": opened,
            "gate": strip_markdown(gate_text),
            "status": strip_markdown(status),
            "state": state,
            "folders": sorted(set(SCL_FOLDER_REF.findall(gate_text + status))),
        })
    return gates


def folder_gate_map(gates: list[dict]) -> dict[str, str]:
    mapping = dict(EXTRA_FOLDER_GATES)
    for gate in gates:
        for folder in gate["folders"]:
            mapping.setdefault(folder, gate["id"])
    return mapping


def scale_id(module: str, folder: str, stem: str) -> str:
    """A stable id that is also a legal db document id."""
    return DOC_ID_UNSAFE.sub("_", f"{module}.{folder}.{stem}")


def collect_scales(experiments: Path, gate_of: dict[str, str]) -> list[dict]:
    scales = []
    for path in sorted(experiments.glob("*/results/scl/**/*.scl")):
        rel = path.relative_to(experiments)
        module = rel.parts[0]
        folder_parts = rel.parts[3:-1]
        folder = "/".join(folder_parts) if folder_parts else module
        parsed = parse_scl(path.read_text(encoding="utf-8", errors="replace"))
        blind = folder in BLIND_FOLDERS
        scales.append({
            "id": scale_id(module, folder.replace("/", "."), path.stem),
            "file": f"experiments/{rel.as_posix()}",
            "name": path.stem,
            "module": module,
            "folder": folder,
            "gate": gate_of.get(folder),
            "blind": blind,
            "protocol": FOLDER_PROTOCOLS.get(folder),
            **parsed,
        })
    return scales


def reference_for(scale: dict, names: set[str]) -> str | None:
    """The JI scale a fitted chain approximates, when the bundle holds it."""
    name, desc, folder = scale["name"], scale["description"], scale["folder"]
    if scale["module"] != "lattice" or folder in BLIND_FOLDERS or folder in {"g012", "subsetmel000"}:
        return None
    if "marcus" in name:
        return None
    subset = SUBSET_TAG.search(name)
    if subset and "canonical" in name:
        prefix = f"lattice.subsetmel000.sm000_1-3-5-7-9-11_hexany_in{subset[1]}_out{subset[2]}_"
        match = sorted(n for n in names if n.startswith(prefix))
        return match[0] if match else EIKOSANY_CANONICAL
    if "eikosany" in name:
        return EIKOSANY_CANONICAL
    if "dek52" in name:
        return DEKANY_13579
    if "hexany" in name or "hexany seeds" in desc:
        return HEXANY_1357
    return None


def build_bundle(experiments: Path = EXPERIMENTS, gates_md: Path = GATES_MD) -> dict:
    gates = parse_gates(gates_md.read_text(encoding="utf-8"))
    gate_of = folder_gate_map(gates)
    scales = collect_scales(experiments, gate_of)
    ids = {s["id"] for s in scales}
    scales = [{**s, "reference": ref if (ref := reference_for(s, ids)) in ids else None} for s in scales]
    used = {s["gate"] for s in scales if s["gate"]}
    gates = [{**g, "pair": list(GATE_PAIRS[g["id"]])} if g["id"] in GATE_PAIRS and set(GATE_PAIRS[g["id"]]) <= ids else g
             for g in gates]
    return {
        "version": BUNDLE_VERSION,
        "gates": [g for g in gates if g["id"] in used],
        "scales": scales,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    bundle = build_bundle()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, indent=1) + "\n", encoding="utf-8")
    pending = [g["id"] for g in bundle["gates"] if g["state"] == "PENDING"]
    print(f"{len(bundle['scales'])} scales, {len(bundle['gates'])} gates "
          f"({len(pending)} pending: {', '.join(pending)}) -> {args.out}")


if __name__ == "__main__":
    main()
