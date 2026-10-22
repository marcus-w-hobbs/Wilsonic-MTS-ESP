"""Local Ear Bench server: verdict validation and storage."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import serve  # noqa: E402


class TestApplyWrite(unittest.TestCase):
    def test_write_lands_in_collection_without_mutating_input(self):
        store = serve.empty_store()
        out = serve.apply_write(store, {"collection": "gates", "id": "G-031", "body": {"verdict": "pass"}})
        self.assertEqual(out["gates"]["G-031"], {"verdict": "pass"})
        self.assertEqual(store["gates"], {})

    def test_rejects_bad_collection_id_and_body(self):
        store = serve.empty_store()
        bad = [
            {"collection": "secrets", "id": "x", "body": {}},
            {"collection": "gates", "id": "../etc", "body": {}},
            {"collection": "gates", "id": "G-031", "body": [1, 2]},
            ["not", "an", "object"],
        ]
        for payload in bad:
            with self.assertRaises(ValueError):
                serve.apply_write(store, payload)


class TestLoadSave(unittest.TestCase):
    def test_round_trip_and_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results" / "verdicts.json"
            self.assertEqual(serve.load(path), serve.empty_store())
            store = serve.apply_write(serve.empty_store(), {"collection": "scales", "id": "a.b", "body": {"rating": 4}})
            serve.save(store, path)
            self.assertEqual(serve.load(path)["scales"]["a.b"], {"rating": 4})

    def test_corrupt_file_reads_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "verdicts.json"
            path.write_text("{not json")
            self.assertEqual(serve.load(path), serve.empty_store())


if __name__ == "__main__":
    unittest.main()
