"""Export Ear Bench judgments into the repo's public, append-only dataset.

A judge's verdicts, ratings and preferences live in two stores: the published
bench's database (pulled into a directory of JSON files, one per document, at
<dump>/<collection>/<id>.json) and the local bench's results/verdicts.json.
This script turns both into judgment records and appends the new ones to
experiments/ear_bench/judgments/<judge>.jsonl. A record never changes once
written; a changed verdict or note is a new record with a later time, so the
file is the full history of the judge's decisions.

Each record names what was heard by scale id, .scl path and the file's
SHA-256, so a judgment stays tied to the exact tuning even if an experiment
is regenerated. The EAR-eps sitting is excluded: its own protocol writes
experiments/lattice/results/eareps_responses.json.

    python experiments/ear_bench/export_judgments.py --judge marcus-w-hobbs \\
        --dump <dir> --local experiments/ear_bench/results/verdicts.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BUNDLE = REPO / "docs" / "ear-bench" / "data.json"
JUDGMENTS = HERE / "judgments"
SCHEMA_VERSION = 1
COLLECTIONS = ("gates", "scales", "comparisons")


def load_dump(directory: Path) -> dict:
    """<dir>/<collection>/<id>.json -> {collection: {id: body}}."""
    out = {c: {} for c in COLLECTIONS}
    for c in COLLECTIONS:
        for f in sorted((directory / c).glob("*.json")) if (directory / c).is_dir() else []:
            out[c][f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return out


def load_local(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    return {c: data.get(c, {}) for c in COLLECTIONS}


def scale_ref(scales: dict, scale_id: str | None) -> dict | None:
    if not scale_id:
        return None
    s = scales.get(scale_id)
    return {"id": scale_id, "file": s["file"], "sha256": s.get("sha256")} if s else {"id": scale_id}


def with_stimulus(ref: dict | None, stimulus: dict | None) -> dict | None:
    """A generator-explorer level is not a file: its stimulus (generator,
    notes, window, CPS, measured triad fit) is what identifies it."""
    if ref is None or not stimulus:
        return ref
    return {**ref, "stimulus": stimulus}


def record_id(rec: dict) -> str:
    key = json.dumps({k: rec[k] for k in ("judge", "kind", "gate", "subject", "at")}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def records(store: dict, source: str, judge: str, scales: dict) -> list[dict]:
    """One store -> judgment records (unsorted, may repeat across stores)."""
    out = []

    def add(kind, gate, subject, at, body):
        if not at:
            return
        rec = {"schema": SCHEMA_VERSION, "judge": judge, "kind": kind, "gate": gate,
               "subject": subject, "at": at, "source": source, **body}
        out.append({"id": record_id(rec), **rec})

    for gate, doc in store["gates"].items():
        if doc.get("verdict") or (doc.get("notes") or "").strip():
            add("gate_verdict", gate, gate, doc.get("updatedAt"), {
                "verdict": doc.get("verdict"), "notes": doc.get("notes", ""),
                "context": doc.get("context"), "provenance": doc.get("restoredBy") or doc.get("syncedFrom"),
            })
    for sid, doc in store["scales"].items():
        if doc.get("rating") or (doc.get("note") or "").strip():
            add("scale_rating", doc.get("gate"), sid, doc.get("updatedAt"), {
                "scale": with_stimulus(scale_ref(scales, sid), doc.get("stimulus")),
                "rating": doc.get("rating"), "note": doc.get("note", ""), "context": doc.get("context"),
            })
    for cid, doc in store["comparisons"].items():
        pair = {"a": with_stimulus(scale_ref(scales, doc.get("a")), doc.get("a_stimulus")),
                "b": with_stimulus(scale_ref(scales, doc.get("b")), doc.get("b_stimulus"))}
        if doc.get("prefer"):
            add("overall_preference", doc.get("gate"), cid, doc.get("updatedAt"),
                {**pair, "blind": False, "preferred": doc["prefer"]})
        for key, pick in (doc.get("picks") or {}).items():
            if isinstance(pick, dict):  # a blind passage pick: "passage:<id>" or "passage:<id>@<timbre>"
                passage, _, timbre = key.split(":", 1)[-1].partition("@")
                add("blind_preference", doc.get("gate"), f"{cid}|{key}", pick.get("at"), {
                    **pair, "blind": True, "passage": passage,
                    "timbre": timbre or (pick.get("context") or {}).get("timbre"), "x_was": pick.get("x"),
                    "pick": pick.get("pick"), "preferred": pick.get("preferred"), "context": pick.get("context"),
                })
            elif pick:  # a named chord-by-chord pick (no time of its own)
                add("chord_preference", doc.get("gate"), f"{cid}|{key}", doc.get("updatedAt"),
                    {**pair, "blind": False, "chord": key, "preferred": pick})
    return out


def merge(existing: list[dict], new: list[dict]) -> list[dict]:
    """Append records not already present (by id), oldest first."""
    seen = {r["id"] for r in existing}
    fresh = {}
    for r in new:
        if r["id"] not in seen:
            fresh.setdefault(r["id"], r)
    return sorted(fresh.values(), key=lambda r: (r["at"], r["id"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--judge", required=True)
    parser.add_argument("--dump", type=Path, help="directory of the published bench's database documents")
    parser.add_argument("--local", type=Path, help="the local bench's results/verdicts.json")
    args = parser.parse_args()
    scales = {s["id"]: s for s in json.loads(BUNDLE.read_text(encoding="utf-8"))["scales"]}
    found = []
    if args.dump:
        found += records(load_dump(args.dump), "claude.ai", args.judge, scales)
    if args.local:
        found += records(load_local(args.local), "local", args.judge, scales)
    out = JUDGMENTS / f"{args.judge}.jsonl"
    existing = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()] if out.is_file() else []
    added = merge(existing, found)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        for rec in added:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"{len(added)} new judgment record(s) appended to {out.relative_to(REPO)} ({len(existing) + len(added)} total)")


if __name__ == "__main__":
    main()
