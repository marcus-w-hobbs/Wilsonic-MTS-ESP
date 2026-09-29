"""Unit tests for et001.py (ET-001) — EDO corpus construction, the analytic
mirror (per-class deviations, guard separation, closed-form identities),
lock-candidate machinery, patent landmarks, and mirror-vs-frozen-scorer
agreement on generic triples. Written and green BEFORE the first experiment
run (LOG.md pre-registration, 2026-08-09).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from math import log2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import et001 as et  # noqa: E402

from scorer import (  # noqa: E402  (frozen v1.1.0, read-only referee)
    classify_cents_triple,
    mean_separation_cents,
)
from melodic import score_melodic  # noqa: E402  (frozen v0.1.0)


class TestCorpus(unittest.TestCase):
    def test_edo_scale_12(self):
        s = et.edo_scale(12)
        self.assertEqual(len(s), 12)
        self.assertEqual(s[0], 0.0)
        self.assertEqual(s[1], 100.0)
        self.assertEqual(s[-1], 1100.0)

    def test_edo_scale_rejects_zero(self):
        with self.assertRaises(ValueError):
            et.edo_scale(0)

    def test_type_enumeration_count(self):
        # #{(p,q): 1<=p,q<=N-1, p+q<=N} = N(N-1)/2
        for n in (2, 3, 12, 60):
            self.assertEqual(len(et.triple_types(n)), n * (n - 1) // 2)


class TestMirrorHandDerived(unittest.TestCase):
    """Pins from the pre-registration scratch derivation (LOG 2026-08-09)."""

    def test_power_chord_12(self):
        t = et.mirror_type(12, 7, 5)
        self.assertAlmostEqual(t.dev_p, 1.955001, places=5)
        # closed form: patent fifth error exactly
        self.assertAlmostEqual(t.dev_p, 1200.0 * log2(3) - 1900.0, places=9)

    def test_major_456_12(self):
        t = et.mirror_type(12, 4, 3)
        self.assertAlmostEqual(t.dev_p, 14.859022, places=5)
        self.assertAlmostEqual(t.sep, 70.281957, places=5)

    def test_symmetric_cluster_12(self):
        # symmetric types: dev_P = dev_S = sep/2 exactly (AM/GM = GM/HM)
        t = et.mirror_type(12, 1, 1)
        self.assertAlmostEqual(t.dev_p, 2.886509, places=5)
        self.assertAlmostEqual(t.dev_p, t.sep / 2.0, places=9)
        self.assertAlmostEqual(t.dev_s, t.sep / 2.0, places=9)
        self.assertEqual(t.dev_g, 0.0)

    def test_duality_identity(self):
        # dev_S(q,p) == dev_P(p,q): same numerator over fa*fc
        for n, p, q in ((12, 4, 3), (19, 6, 5), (31, 10, 8), (53, 31, 22)):
            self.assertAlmostEqual(
                et.mirror_type(n, p, q).dev_p,
                et.mirror_type(n, q, p).dev_s,
                places=9,
            )

    def test_geometric_dev_is_step_difference(self):
        t = et.mirror_type(12, 5, 2)
        self.assertAlmostEqual(t.dev_g, 3 * 100.0, places=9)

    def test_power_chord_identity_all_n(self):
        # (F, N-F) has dev_P == patent fifth error for every N
        for n in (12, 29, 41, 53, 60):
            f, err = et.patent_fifth(n)
            t = et.mirror_type(n, f, n - f)
            self.assertAlmostEqual(t.dev_p, err, places=9)


class TestMirrorVsFrozenScorer(unittest.TestCase):
    """The referee-agreement tests: mirror math must match the frozen code
    on individual triples (labels and guard), across anchors."""

    def test_sep_matches_frozen_mean_separation(self):
        for n, p, q in ((12, 7, 5), (12, 1, 1), (19, 6, 5), (53, 31, 22)):
            s = 1200.0 / n
            t = et.mirror_type(n, p, q)
            self.assertAlmostEqual(
                t.sep, mean_separation_cents(-p * s, q * s), places=9
            )

    def test_labels_match_classify_cents_triple(self):
        # (dev_X < eps) iff X in frozen labels, for a spread of types/eps,
        # at anchor b = 0 and at a nonzero anchor (transposition).
        cases = [(12, 7, 5), (12, 4, 3), (12, 1, 1), (19, 6, 5),
                 (31, 7, 6), (41, 22, 16), (50, 9, 8)]
        for eps in (1.0, 5.0, 14.86):
            for n, p, q in cases:
                s = 1200.0 / n
                t = et.mirror_type(n, p, q)
                for b in (0.0, 3 * s):
                    labels = classify_cents_triple(
                        b - p * s, b, b + q * s, eps
                    )
                    for cls, name in (("P", "proportional"),
                                      ("S", "subcontrary"),
                                      ("G", "geometric")):
                        dev = {"P": t.dev_p, "S": t.dev_s,
                               "G": t.dev_g}[cls]
                        if abs(dev - eps) < 1e-9:
                            continue  # knife edge: not asserted
                        self.assertEqual(
                            dev < eps, name in labels,
                            msg=f"n={n} pq=({p},{q}) b={b} eps={eps} {cls}",
                        )


class TestLockMachinery(unittest.TestCase):
    def test_lock_candidates_sorted_and_guarded(self):
        cands = et.lock_candidates(et.triple_types(12), "P")
        devs = [d for d, _, _ in cands]
        self.assertEqual(devs, sorted(devs))
        # pre-registered 12-EDO P spectrum head
        self.assertAlmostEqual(devs[0], 1.955001, places=5)
        self.assertEqual((cands[0][1], cands[0][2]), (7, 5))
        self.assertAlmostEqual(devs[1], 2.886509, places=5)
        self.assertAlmostEqual(devs[2], 7.837351, places=5)

    def test_asymmetric_filter(self):
        cands = et.lock_candidates(
            et.triple_types(12), "P", asymmetric_only=True
        )
        self.assertTrue(all(p != q for _, p, q in cands))
        self.assertEqual((cands[0][1], cands[0][2]), (7, 5))

    def test_entry_multiplicity_and_interference(self):
        types = et.triple_types(12)
        self.assertEqual(
            et.entry_multiplicity(types, "P", 1.955001, 1e-4), 1
        )
        self.assertEqual(
            et.entry_multiplicity(types, "P", 0.5, 1e-4), 0
        )
        self.assertFalse(et.sep_interference(types, 1.955001, 1e-6))
        # sep of (1,1) is 5.773017: a window centred there must interfere
        self.assertTrue(et.sep_interference(types, 5.773017, 1e-3))


class TestPatentLandmarks(unittest.TestCase):
    def test_patent_fifth_12_53(self):
        self.assertEqual(et.patent_fifth(12)[0], 7)
        self.assertAlmostEqual(et.patent_fifth(12)[1], 1.955001, places=5)
        self.assertEqual(et.patent_fifth(53)[0], 31)
        self.assertAlmostEqual(et.patent_fifth(53)[1], 0.068208, places=5)

    def test_patent_major_pq(self):
        self.assertEqual(et.patent_major_pq(12), (4, 3))
        self.assertEqual(et.patent_major_pq(19), (6, 5))
        self.assertEqual(et.patent_major_pq(31), (10, 8))
        self.assertEqual(et.patent_major_pq(53), (17, 14))


class TestMelodicRail(unittest.TestCase):
    def test_12_edo_is_trivially_melodic(self):
        m = score_melodic(et.edo_scale(12))
        self.assertEqual(m.propriety.classification, "strictly_proper")
        self.assertEqual(m.gap_entropy.gap_class_count, 1)
        self.assertEqual(m.gap_entropy.entropy_bits, 0.0)
        self.assertTrue(m.constant_structure.is_cs)

    def test_2_edo_edge(self):
        m = score_melodic(et.edo_scale(2))
        self.assertEqual(m.propriety.classification, "strictly_proper")
        self.assertEqual(m.gap_entropy.gap_class_count, 1)


class TestScorerCache(unittest.TestCase):
    def test_cache_hits(self):
        c = et.ScorerCache()
        a = c.counts(5, 2.0)
        b = c.counts(5, 2.0)
        self.assertIs(a, b)
        self.assertEqual(c.calls, 1)

    def test_count_classes(self):
        c = et.ScorerCache()
        r = c.counts(5, 2.0)
        self.assertEqual(c.count(5, 2.0, "P"), r.proportional)
        self.assertEqual(c.count(5, 2.0, "S"), r.subcontrary)
        self.assertEqual(c.count(5, 2.0, "G"), r.geometric)


if __name__ == "__main__":
    unittest.main()
