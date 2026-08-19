"""Unit tests for et002.py (ET-002, the 12-EDO subset census) — enumeration
counts (Pólya), canonical forms, tags, the analytic pattern-count mirror,
mirror-vs-frozen-scorer agreement on named scales, the balance-bucket copy,
and the frontier lens. Written and green BEFORE the first experiment run
(LOG.md pre-registration, 2026-08-18).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "triads"))

import et002 as et  # noqa: E402

from scorer import score_tempered  # noqa: E402  (frozen v1.1.0, referee)
from melodic import score_melodic  # noqa: E402  (frozen v0.1.0, referee)
from search import balance_bucket as search_balance_bucket  # noqa: E402

DIATONIC = (0, 2, 4, 5, 7, 9, 11)
PENTATONIC = (0, 2, 4, 7, 9)
MAJOR = (0, 4, 7)
MINOR = (0, 3, 7)


class TestEnumeration(unittest.TestCase):
    def test_polya_count_351(self):
        classes = et.enumerate_t_classes()
        self.assertEqual(len(classes), 351)
        self.assertEqual(len(set(classes)), 351)

    def test_per_size_histogram(self):
        hist = et.size_histogram(et.enumerate_t_classes())
        self.assertEqual(
            [hist[n] for n in range(1, 13)],
            [1, 6, 19, 43, 66, 80, 66, 43, 19, 6, 1, 1],
        )

    def test_ti_class_count_223(self):
        classes = et.enumerate_t_classes()
        self.assertEqual(len({et.canonical_ti(c) for c in classes}), 223)

    def test_inversionally_symmetric_95(self):
        classes = et.enumerate_t_classes()
        self.assertEqual(
            sum(1 for c in classes if et.is_inversionally_symmetric(c)), 95
        )

    def test_limited_transposition_16(self):
        classes = et.enumerate_t_classes()
        self.assertEqual(
            sum(1 for c in classes if et.transposition_period(c) < 12), 16
        )
        self.assertEqual(et.transposition_period((0, 2, 4, 6, 8, 10)), 2)
        self.assertEqual(et.transposition_period(DIATONIC), 12)

    def test_classes_are_canonical_and_sorted(self):
        classes = et.enumerate_t_classes()
        for c in classes:
            self.assertEqual(et.canonical_t(c), c)
        self.assertEqual(
            list(classes), sorted(classes, key=lambda c: (len(c), c))
        )


class TestCanonicalForms(unittest.TestCase):
    def test_diatonic_canonical(self):
        self.assertEqual(et.canonical_t(DIATONIC), (0, 1, 3, 5, 6, 8, 10))

    def test_step_word_diatonic(self):
        self.assertEqual(et.step_word(DIATONIC), "1221222")
        self.assertEqual(et.step_word((0,)), "c")  # 12 encoded as 'c'
        self.assertEqual(et.step_word((0, 6)), "66")

    def test_interval_vector_diatonic(self):
        self.assertEqual(et.interval_vector(DIATONIC), (2, 5, 4, 3, 6, 1))

    def test_rahn_prime_forms(self):
        self.assertEqual(et.rahn_prime_form(DIATONIC), (0, 1, 3, 5, 6, 8, 10))
        self.assertEqual(et.rahn_prime_form(MAJOR), (0, 3, 7))
        self.assertEqual(et.rahn_prime_form(MINOR), (0, 3, 7))
        self.assertEqual(et.rahn_prime_form((0, 1, 4, 5, 8, 9)),
                         (0, 1, 4, 5, 8, 9))

    def test_ti_key_joins_major_and_minor(self):
        self.assertEqual(et.canonical_ti(MAJOR), et.canonical_ti(MINOR))
        self.assertNotEqual(et.canonical_t(MAJOR), et.canonical_t(MINOR))

    def test_cents(self):
        self.assertEqual(et.cents((0, 3, 7)), (0.0, 300.0, 700.0))


class TestTags(unittest.TestCase):
    def test_tags_are_distinct_classes(self):
        keys = [et.canonical_t(v) for v in et.TAGS.values()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_named_lookups(self):
        self.assertIn("diatonic", et.tags_for(et.canonical_t(DIATONIC)))
        self.assertIn("pentatonic", et.tags_for(et.canonical_t(PENTATONIC)))
        self.assertIn("whole_tone", et.tags_for(et.canonical_t(
            (0, 2, 4, 6, 8, 10))))
        self.assertIn("messiaen_1", et.tags_for(et.canonical_t(
            (0, 2, 4, 6, 8, 10))))
        self.assertIn("octatonic", et.tags_for(et.canonical_t(
            (0, 1, 3, 4, 6, 7, 9, 10))))
        self.assertIn("chromatic", et.tags_for(tuple(range(12))))
        self.assertEqual(et.tags_for((0, 1, 2, 4)), [])


class TestMirror(unittest.TestCase):
    """Pattern-count mirror pinned to the pre-registration algebra."""

    def test_qualifying_types_at_grid(self):
        self.assertEqual(et.qualifying_types(1.0, "P"), ())
        self.assertEqual(et.qualifying_types(2.0, "P"), ((7, 5),))
        self.assertEqual(set(et.qualifying_types(5.0, "P")), {(1, 1), (7, 5)})
        self.assertEqual(set(et.qualifying_types(10.0, "P")),
                         {(5, 4), (7, 5)})
        self.assertEqual(set(et.qualifying_types(14.86, "P")),
                         {(2, 2), (4, 3), (5, 4), (7, 5)})
        self.assertEqual(set(et.qualifying_types(20.0, "S")),
                         {(2, 2), (3, 4), (4, 5), (5, 7)})

    def test_pattern_count(self):
        self.assertEqual(et.pattern_count(DIATONIC, 4, 3), 3)  # major triads
        self.assertEqual(et.pattern_count(DIATONIC, 3, 4), 3)  # minor triads
        self.assertEqual(et.pattern_count(DIATONIC, 2, 2), 3)  # WT trichords
        self.assertEqual(et.pattern_count(DIATONIC, 7, 5), 6)  # ic5
        self.assertEqual(et.pattern_count(DIATONIC, 1, 1), 0)

    def test_mirror_grid_diatonic(self):
        p = [et.mirror_counts(DIATONIC, e)[0] for e in et.EPS_GRID]
        s = [et.mirror_counts(DIATONIC, e)[1] for e in et.EPS_GRID]
        self.assertEqual(p, [0, 6, 6, 6, 9, 15, 15])
        self.assertEqual(s, [0, 6, 6, 6, 9, 15, 15])

    def test_mirror_grid_full_12(self):
        full = tuple(range(12))
        p = [et.mirror_counts(full, e)[0] for e in et.EPS_GRID]
        g = [et.mirror_counts(full, e)[2] for e in et.EPS_GRID]
        self.assertEqual(p, [0, 12, 24, 24, 24, 48, 48])
        self.assertEqual(g, [72, 72, 72, 72, 60, 60, 60])

    def test_p_at_2_is_ic5(self):
        for pcs in (DIATONIC, PENTATONIC, MAJOR, (0, 1, 2), (0, 6)):
            self.assertEqual(et.mirror_counts(pcs, 2.0)[0],
                             et.interval_vector(pcs)[4])

    def test_mirror_melodic_named(self):
        self.assertEqual(et.mirror_melodic(DIATONIC),
                         {"propriety": "proper", "propriety_violations": 0,
                          "is_cs": False, "cs_violations": 1,
                          "gap_class_count": 2})
        self.assertEqual(et.mirror_melodic(PENTATONIC)["propriety"],
                         "strictly_proper")
        self.assertTrue(et.mirror_melodic(PENTATONIC)["is_cs"])
        self.assertEqual(et.mirror_melodic((0, 3, 6))["propriety"], "proper")
        self.assertEqual(et.mirror_melodic((0,))["gap_class_count"], 1)


class TestMirrorVsFrozen(unittest.TestCase):
    """The frozen scorers are the referee: agreement on named scales."""

    def test_scorer_agrees_on_named(self):
        for pcs in (DIATONIC, PENTATONIC, MAJOR, MINOR, (0, 1, 2), (0,),
                    (0, 6), tuple(range(12)), (0, 1, 2, 3, 6, 7, 8, 9)):
            for e in et.EPS_GRID:
                r = score_tempered(et.cents(pcs), e)
                self.assertEqual(
                    (r.proportional, r.subcontrary, r.geometric),
                    et.mirror_counts(pcs, e), (pcs, e))

    def test_melodic_agrees_on_named(self):
        for pcs in (DIATONIC, PENTATONIC, MAJOR, (0, 3, 6), (0,), (0, 6),
                    (0, 1, 2, 4), tuple(range(12))):
            m = score_melodic(et.cents(pcs))
            got = {
                "propriety": m.propriety.classification,
                "propriety_violations": m.propriety.violating_span_pairs,
                "is_cs": m.constant_structure.is_cs,
                "cs_violations": m.constant_structure.violations,
                "gap_class_count": m.gap_entropy.gap_class_count,
            }
            self.assertEqual(got, et.mirror_melodic(pcs), pcs)


class TestBucketsAndFrontier(unittest.TestCase):
    def test_balance_bucket_matches_search(self):
        for p in range(0, 25):
            for s in range(0, 25):
                self.assertEqual(et.balance_bucket(p, s),
                                 search_balance_bucket(p, s), (p, s))

    def test_frontier_toy(self):
        rows = [
            {"canonical": (0, 1), "n": 2, "gc": 2, "ps": 2, "improper": False},
            {"canonical": (0, 6), "n": 2, "gc": 1, "ps": 0, "improper": False},
            {"canonical": (0, 2), "n": 2, "gc": 2, "ps": 0, "improper": True},
            {"canonical": (0, 1, 2), "n": 3, "gc": 2, "ps": 1,
             "improper": True},
        ]
        front = et.pareto_front(rows)
        self.assertEqual(front, [(0, 1), (0, 6), (0, 1, 2)])
        self.assertEqual(et.pareto_front(rows, proper_only=True),
                         [(0, 1), (0, 6)])


class TestRowShape(unittest.TestCase):
    def test_build_row_diatonic(self):
        row = et.build_row(et.canonical_t(DIATONIC))
        self.assertEqual(row["n"], 7)
        self.assertEqual(row["step_word"], "1221222")
        self.assertIn("diatonic", row["tags"])
        self.assertEqual(row["derived"]["major_triads"], 3)
        self.assertEqual(row["derived"]["minor_triads"], 3)
        self.assertEqual(row["grid"]["14.86"]["P"], 15)
        self.assertEqual(row["grid"]["14.86"]["balance"], "diagonal")
        self.assertTrue(row["mirror_agrees"]["harmonic"])
        self.assertTrue(row["mirror_agrees"]["melodic"])
        # Dorian is its own inversion: the diatonic IS T/I-symmetric
        self.assertTrue(row["is_inversionally_symmetric"])


if __name__ == "__main__":
    unittest.main()
