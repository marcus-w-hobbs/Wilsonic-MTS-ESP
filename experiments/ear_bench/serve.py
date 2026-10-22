"""Local Ear Bench server: the page with Web MIDI, verdicts saved to the repo.

The published artifact cannot use MIDI (its frame blocks the API), so for a
hardware controller run the bench locally in Chrome. This server serves
docs/ear-bench/ and gives the page a tiny verdict API, so verdicts made
locally land in experiments/ear_bench/results/verdicts.json, where any
session reads them, instead of only in that browser's localStorage.

    python experiments/ear_bench/serve.py            # http://localhost:8765
    python experiments/ear_bench/serve.py --port 9000

Binds to 127.0.0.1 only.
"""

from __future__ import annotations

import argparse
import json
import re
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAGE_DIR = REPO / "docs" / "ear-bench"
VERDICTS = Path(__file__).resolve().parent / "results" / "verdicts.json"
# Live page diagnostics (audio, MIDI, errors) so a session can see what the
# open bench is doing without screenshots. Not committed.
STATUS = Path(__file__).resolve().parent / "results" / "status.json"
STATUS_API = "/api/status"
_status: dict = {}

COLLECTIONS = ("gates", "scales", "comparisons", "eareps")
DOC_ID = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")
MAX_BODY = 256 * 1024
API = "/api/verdicts"
_lock = threading.Lock()


def build_id(page_dir: Path = PAGE_DIR) -> str:
    """Changes whenever any page file changes, so open pages can reload themselves."""
    stamps = [f.stat().st_mtime_ns for f in page_dir.iterdir() if f.is_file()]
    return format(max(stamps, default=0), "x")


def empty_store() -> dict:
    return {c: {} for c in COLLECTIONS}


def load(path: Path = VERDICTS) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return empty_store()
    return {**empty_store(), **{c: data.get(c, {}) for c in COLLECTIONS}}


def apply_write(store: dict, payload: object) -> dict:
    """Validate one {collection, id, body} write and return the new store."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    collection, doc_id, body = payload.get("collection"), payload.get("id"), payload.get("body")
    if collection not in COLLECTIONS:
        raise ValueError(f"unknown collection {collection!r}")
    if not isinstance(doc_id, str) or not DOC_ID.match(doc_id):
        raise ValueError("invalid document id")
    if not isinstance(body, dict):
        raise ValueError("body must be an object")
    return {**store, collection: {**store[collection], doc_id: body}}


def save(store: dict, path: Path = VERDICTS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


class Handler(SimpleHTTPRequestHandler):
    def _json(self, status: int, obj: object) -> None:
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self) -> None:
        if not self.path.startswith(API):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path == STATUS_API:
            with _lock:
                self._json(200, _status)
            return
        if self.path == API:
            with _lock:
                self._json(200, load())
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != STATUS_API:
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._json(413, {"error": "body missing or too large"})
            return
        try:
            report = json.loads(self.rfile.read(length))
            client = report.get("client") if isinstance(report, dict) else None
            if not isinstance(client, str) or not DOC_ID.match(client):
                raise ValueError("report needs a client id")
            with _lock:
                _status[client] = {**report, "receivedAt": time.strftime("%Y-%m-%dT%H:%M:%S")}
                save(_status, STATUS)
        except (ValueError, json.JSONDecodeError) as err:
            self._json(400, {"error": str(err)})
            return
        self._json(200, {"ok": True, "build": build_id()})

    def log_message(self, fmt: str, *args) -> None:
        if STATUS_API not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def do_PUT(self) -> None:  # noqa: N802
        if self.path != API:
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._json(413, {"error": "body missing or too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            with _lock:
                save(apply_write(load(), payload))
        except (ValueError, json.JSONDecodeError) as err:
            self._json(400, {"error": str(err)})
            return
        except OSError as err:
            self._json(500, {"error": f"could not write verdicts: {err}"})
            return
        self._json(200, {"ok": True})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(PAGE_DIR)))
    print(f"Ear Bench on http://localhost:{args.port}  (verdicts -> {VERDICTS.relative_to(REPO)})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
