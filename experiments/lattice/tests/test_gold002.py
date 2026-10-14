"""Unit tests for gold002.py (GOLD-002). Written BEFORE the first run
(LOG.md pre-registration 2026-10-13). Pins: the noble enumeration (2 - phi
has complexity 1, the ladder counts, the 0.419009 noble has seeds 18/43,
13/31 and complexity 43), the null percentile, the generator list, the
chain P + S of Erv's 0.418935 at its shallow levels, and the verdict
helpers on synthetic rows.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gold002 as g2  # noqa: E402


class TestNobles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.golden = g2.nobles(1)
        cls.silver = g2.nobles(2)

    def test_counts_by_Q(self):
        self.assertEqual([sum(1 for c in self.golden if c[2] <= q) for q in g2.Q_LADDER], [22, 46, 128, 278, 1102])
        self.assertEqual([sum(1 for c in self.silver if c[2] <= q) for q in g2.Q_LADDER], [33, 69, 192, 417, 1653])

    def test_two_minus_phi_is_simplest(self):
        g, seeds, cx = min(self.golden, key=lambda c: abs(c[0] - (2 - g2.PHI)))
        self.assertAlmostEqual(g, 2 - g2.PHI, places=9)
        self.assertEqual(cx, 1)

    def test_erv_418935_neighbour(self):
        g, seeds, cx = g2.nearest(self.golden, 0.418934662571, 60)
        self.assertEqual(seeds, "18/43,13/31")
        self.assertEqual(cx, 43)
        self.assertAlmostEqual((g - 0.418934662571) * 1200, 0.089, places=2)
        g20, _, cx20 = g2.nearest(self.golden, 0.418934662571, 20)
        self.assertLessEqual(cx20, 20)
        self.assertAlmostEqual((g20 - 0.418934662571) * 1200, -0.12, places=1)

    def test_folded_and_sorted(self):
        self.assertTrue(all(0 < c[0] <= 0.5 for c in self.golden))
        self.assertEqual([c[0] for c in self.golden], sorted(c[0] for c in self.golden))


class TestNull(unittest.TestCase):
    def test_percentile(self):
        ds = [0.0, 1.0, 2.0, 3.0]
        self.assertEqual(g2.percentile(ds, 0.5), 0.25)
        self.assertEqual(g2.percentile(ds, -2.5), 0.75)
        self.assertEqual(g2.percentile(ds, 10.0), 1.0)

    def test_null_distances_are_sorted_and_positive(self):
        cands = g2.nobles(1, 12)
        ds = g2.null_distances(cands, 12, [0.1, 0.2, 0.3, 0.4])
        self.assertEqual(ds, sorted(ds))
        self.assertTrue(all(d >= 0 for d in ds))


class TestGenerators(unittest.TestCase):
    def test_list(self):
        gens = g2.erv_generators()
        self.assertEqual(len(gens), 17)
        self.assertEqual(gens[0]["id"], "erv418935")
        self.assertAlmostEqual(gens[0]["g01"], 0.418934662571, places=6)
        self.assertEqual(gens[-1]["id"], "phi")

    def test_levels_of_erv_418935(self):
        self.assertEqual(g2.levels_of(0.418934662571), [2, 3, 5, 7, 12, 19, 31])

    def test_chain_ps_shallow_levels(self):
        g = 0.418934662571 * 1200
        self.assertEqual(g2.chain_ps(g, 7), 6)
        self.assertEqual(g2.chain_ps(g, 12), 16)


def _row(rid, tail_g, tail_s, deepest):
    by_q = lambda tails: {str(q): {"dist_cents": 0.0, "null_percentile": 0.05 if q in tails else 0.5,
                                   "in_tail": q in tails} for q in g2.Q_LADDER}
    n, e, s = deepest
    return {"id": rid, "golden": {"by_Q": by_q(tail_g), "nearest_Q60": {"seeds": ""},
                                  "chain_PS_2c": [{"N": 7, "erv_PS_2c": 4, "noble_PS_2c": 4},
                                                  {"N": n, "erv_PS_2c": e, "noble_PS_2c": s}]},
            "silver": {"by_Q": by_q(tail_s)}}


class TestVerdicts(unittest.TestCase):
    def test_p_g2_4_classifies(self):
        rows = [_row("erv418935", (), (), (31, 212, 190)), _row("silver414", (), (), (41, 302, 372)),
                _row("pell", (), (), (37, 240, 240))]
        v = g2.verdict_p_g2_4(rows)
        self.assertEqual(v["failures"], [])
        rows[0]["golden"]["chain_PS_2c"][-1]["noble_PS_2c"] = 300
        self.assertFalse(g2.verdict_p_g2_4(rows)["kept"])

    def test_strong_law_flag(self):
        rows = [_row(f"g{i}", (20,), (), (31, 1, 1)) for i in range(10)]
        v = g2.verdict_p_g2_2(rows)
        self.assertTrue(v["strong_law_holds"])


if __name__ == "__main__":
    unittest.main()
