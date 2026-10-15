"""Unit tests for gold003.py (GOLD-003 arm A). Written BEFORE the first run
(LOG.md pre-registration 2026-10-14). Pins: segment loading (22 distinct,
15 merged, reflected dekany collapses), containment on synthetic segments,
the registered golden containments at Q = 12 (317.170 and 503.786 cents),
the null is seeded and reproducible, and the verdict helpers on synthetic
rows.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gold003 as g3  # noqa: E402


class TestSegments(unittest.TestCase):
    def test_distinct_and_merged(self):
        d = g3.load_segments()
        self.assertEqual(len(d), 22)
        self.assertTrue(all(s["lo"] < s["hi"] for s in d))
        self.assertTrue(all("refl" not in lat for s in d for lat in s["lattices"]))
        m = g3.merge_segments(d)
        self.assertEqual(len(m), 15)
        self.assertTrue(all(a["hi"] < b["lo"] for a, b in zip(m, m[1:])))
        both = [s for s in m if 316.85 < s["lo"] < 316.95]
        self.assertEqual(len(both), 1)
        self.assertEqual(sorted(both[0]["lattices"]), ["dek52", "dek53", "eg4", "hexany"])


class TestContainment(unittest.TestCase):
    def test_contained(self):
        cs = [10.0, 20.0, 30.0]
        self.assertEqual(g3.contained(cs, 9.0, 10.0), 0)
        self.assertEqual(g3.contained(cs, 10.5, 19.9), None)
        self.assertEqual(g3.contained(cs, 25.0, 35.0), 2)
        self.assertEqual(g3.contained(cs, 31.0, 40.0), None)

    def test_registered_golden_q12(self):
        nobles = g3.noble_cents(1, 12)
        cs = [c[0] for c in nobles]
        d = g3.load_segments()
        hits = {round(nobles[i][0], 3) for i in g3.observed(cs, d) if i is not None}
        self.assertEqual(hits, {317.170, 503.786})

    def test_null_seeded(self):
        cs = [c[0] for c in g3.noble_cents(1, 12)]
        a = g3.null_counts(cs, [0.1, 0.2, 0.4], 200, 7)
        b = g3.null_counts(cs, [0.1, 0.2, 0.4], 200, 7)
        self.assertEqual(a, b)
        self.assertTrue(all(0 <= k <= 3 for k in a))


def _row(set_name, family, Q, contained, null_mean, p, n_segments=22):
    v = "signal" if p <= g3.SIGNAL_P else "hint" if p <= g3.HINT_P else "nothing"
    return {"set": set_name, "family": family, "Q": Q, "contained": contained, "null_mean": null_mean, "p_ge": p,
            "n_segments": n_segments, "verdict": v, "hits": []}


def _registered_rows():
    rows = []
    for key in ("P-G3-1", "P-G3-2"):
        p = g3.PREDICTIONS[key]
        for Q, c, mu, pr in zip(g3.Q_LADDER, p["contained"], p["null_mean"], p["p"]):
            rows.append(_row("distinct", p["family"], Q, c, mu, pr))
    p = g3.PREDICTIONS["P-G3-3"]
    for fam in ("golden", "silver"):
        for Q, c, pr in zip(g3.Q_LADDER, p[fam]["contained"], p[fam]["p"]):
            rows.append(_row("merged", fam, Q, c, 1.0, pr, n_segments=15))
    return rows


class TestVerdicts(unittest.TestCase):
    def test_kept_on_registered(self):
        rows = _registered_rows()
        self.assertTrue(g3.verdict_counts(rows, "P-G3-1")["kept"])
        self.assertTrue(g3.verdict_counts(rows, "P-G3-2")["kept"])
        self.assertTrue(g3.verdict_p_g3_3(rows)["kept"])
        self.assertTrue(g3.verdict_p_g3_5(rows)["kept"])

    def test_refuted_on_change(self):
        rows = _registered_rows()
        r = next(r for r in rows if r["set"] == "distinct" and r["family"] == "golden" and r["Q"] == 12)
        r["p_ge"] = 0.02
        r["verdict"] = "hint"
        v = g3.verdict_counts(rows, "P-G3-1")
        self.assertFalse(v["kept"])
        self.assertFalse(g3.verdict_p_g3_5(rows)["kept"])

    def test_p_tolerance(self):
        self.assertTrue(g3._p_ok(0.13, 0.11))
        self.assertFalse(g3._p_ok(0.30, 0.11))
        self.assertTrue(g3._p_ok(0.004, 0.0012))
        self.assertFalse(g3._p_ok(0.006, 0.0012))


if __name__ == "__main__":
    unittest.main()
