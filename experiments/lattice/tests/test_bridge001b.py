"""Unit tests for bridge001b.py (BRIDGE-001b) — generalized minimax solver
(prime vs tone-set objectives, hand-derived pins), k2 sweep + mapping
dedup, temperament label resolution, host-window melodic scoring, the
hexany interval-error column, and rail equality against BRIDGE-001's
receipts. Written BEFORE the first experiment run (LOG.md pre-registration,
2026-08-18).

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import bridge001 as br  # noqa: E402
import bridge001b as bb  # noqa: E402


def mapping_of(a: str, b: str):
    return br.hnf_mapping(br.nullspace_saturated(
        [br.monzo_of(Fraction(a)), br.monzo_of(Fraction(b))]))


MIRACLE = mapping_of("225/224", "1029/1024")
ORWELL = mapping_of("225/224", "1728/1715")
MEANTONE = mapping_of("81/80", "126/125")
MAGIC = mapping_of("225/224", "245/243")
GARIBALDI = mapping_of("32805/32768", "5120/5103")


class TestGeneralizedMinimax(unittest.TestCase):
    def test_prime_objective_reproduces_bridge001_solver(self):
        for m in (MIRACLE, ORWELL, MEANTONE, MAGIC):
            g0, e0 = br.minimax_generator(m)
            g1, e1 = bb.minimax_generator_over(m, bb.PRIME_MONZOS)
            self.assertAlmostEqual(g0, g1, places=9)
            self.assertAlmostEqual(e0, e1, places=9)

    def test_miracle_tone_set_pin(self):
        # hand-derived (LOG 2026-08-18): e21 (slope +4) balances e105
        # (slope -3) at delta = -0.347c; max tone error 5.82c
        g_prime, _ = br.minimax_generator(MIRACLE)
        g_tone, err = bb.tone_set_minimax(MIRACLE)
        self.assertAlmostEqual(err, 5.82, delta=0.02)
        self.assertAlmostEqual(g_tone - g_prime, -0.347, delta=0.005)

    def test_orwell_tone_set_pin(self):
        # hand-derived: e15 (slope +4) balances e7 (slope +8) at +0.039c
        g_prime, _ = br.minimax_generator(ORWELL)
        g_tone, err = bb.tone_set_minimax(ORWELL)
        self.assertAlmostEqual(err, 2.570, delta=0.01)
        self.assertAlmostEqual(g_tone - g_prime, 0.039, delta=0.005)

    def test_tone_set_never_worse_than_prime_on_tones(self):
        for m in (MIRACLE, ORWELL, MEANTONE, MAGIC):
            g_prime, _ = br.minimax_generator(m)
            _g_tone, err_tone = bb.tone_set_minimax(m)
            worst_prime = max(abs(e) for e in bb.tone_errors(m, g_prime))
            self.assertLessEqual(err_tone, worst_prime + 1e-9)


class TestSweep(unittest.TestCase):
    def test_miracle_val_sweep_contains_argmin_and_miracle(self):
        c = br.monzo_of(Fraction(225, 224))
        v = (21, 33, 49, 59)
        box = br.kernel_box_for(v)
        swept = bb.sweep_temperaments(c, box, {})
        self.assertIn(MIRACLE, swept)
        self.assertIn(br.monzo_of(Fraction(1029, 1024)), swept[MIRACLE])
        k2, mapping, _g, _e = br.choose_completion(c, v, box, {})
        self.assertIn(mapping, swept)
        self.assertIn(k2, swept[mapping])
        self.assertGreater(len(swept), 1)

    def test_magic_appears_for_245_243_at_19_patent(self):
        c = br.monzo_of(Fraction(245, 243))
        v = br.patent_val(19)
        self.assertEqual(br.vdot(v, c), 0)
        swept = bb.sweep_temperaments(c, br.kernel_box_for(v), {})
        self.assertIn(MAGIC, swept)

    def test_every_swept_mapping_is_supported_by_val(self):
        c = br.monzo_of(Fraction(81, 80))
        v = br.patent_val(19)
        for mapping in bb.sweep_temperaments(c, br.kernel_box_for(v), {}):
            self.assertIsNotNone(br.val_combo(v, mapping))


class TestNames(unittest.TestCase):
    def test_named_mappings_resolve(self):
        names = bb.resolve_names()
        self.assertEqual(names[MIRACLE], "miracle")
        self.assertEqual(names[ORWELL], "orwell")
        self.assertEqual(names[MAGIC], "magic")
        self.assertEqual(names[GARIBALDI], "garibaldi")
        self.assertEqual(names[MEANTONE], "meantone")

    def test_negri_is_49_48_and_225_224(self):
        # 7-limit negri: its 5-limit comma 16875/16384 must lie in the kernel
        negri = mapping_of("49/48", "225/224")
        for row in negri:
            self.assertEqual(br.vdot(row, br.monzo_of(Fraction(16875, 16384))), 0)
        self.assertEqual(bb.resolve_names()[negri], "negri")

    def test_eg4_chain_spans(self):
        self.assertEqual(bb.chain_span(MAGIC), 19)
        self.assertEqual(bb.chain_span(GARIBALDI), 24)
        self.assertEqual(bb.chain_span(MIRACLE), 16)
        self.assertEqual(bb.chain_span(ORWELL), 19)


class TestHostWindow(unittest.TestCase):
    def test_pythagorean_12_two_classes(self):
        # 3/2 chain, 12 notes: a 2-step MOS (5 limmas + 7 apotomes)
        mapping = ((1, 0), (0, 1))
        notes = bb.window_cents(1200.0, 701.955, 12, 0, 1)
        self.assertEqual(len(notes), 12)
        rec = bb.melodic_receipt(notes)
        self.assertEqual(rec["gap_classes"], 2)
        self.assertTrue(rec["is_cs"])
        del mapping

    def test_blackjack_window_two_classes_improper(self):
        g, _ = br.minimax_generator(MIRACLE)
        mono = br.monotonicity((21, 33, 49, 59))
        host = br.host_receipt(MIRACLE, g, 21, mono["degrees"])
        notes = bb.window_cents(1200.0, g, 21, host["anchor_used"], 1)
        rec = bb.melodic_receipt(notes)
        self.assertEqual(rec["gap_classes"], 2)
        self.assertEqual(rec["gap_classes"], host["host_step_classes"])
        self.assertEqual(rec["propriety"], "improper")   # L/s = 2.42

    def test_period_2_window_has_n_notes(self):
        notes = bb.window_cents(600.0, 109.0, 22, 0, 2)
        self.assertEqual(len(notes), 22)


class TestHexanyIntervalError(unittest.TestCase):
    def test_zero_errors(self):
        errs = {p: 0.0 for p in br.HEXANY_PRODUCTS}
        self.assertEqual(bb.hexany_interval_maxerr(errs), 0.0)

    def test_miracle_prime_value(self):
        # hand-derived: worst hexany-internal interval is 15/8 vs 7/4
        # (e3 + e5 - e7 = -2.86c) under prime minimax
        g, _ = br.minimax_generator(MIRACLE)
        errs = bb.tone_errors_by_product(MIRACLE, g)
        self.assertAlmostEqual(bb.hexany_interval_maxerr(errs), 2.86, delta=0.02)


class TestIdentityLens(unittest.TestCase):
    """POST-HOC lens (added after the first run, LOG 2026-08-18 results):
    the hexany's own twelve labelled triads and their survival."""

    def test_hexany_has_six_plus_six_identity_triads(self):
        labels = [t[0] for t in bb.HEXANY_TRIADS]
        self.assertEqual(labels.count("proportional"), 6)
        self.assertEqual(labels.count("subcontrary"), 6)

    def test_exact_hexany_survives_fully(self):
        import math
        temp = {p: 1200 * math.log2(br.reduce_rational(Fraction(p)))
                for p in br.HEXANY_PRODUCTS}
        self.assertEqual(bb.identity_survival(temp, 0.01), (6, 6))

    def test_miracle_prime_identity_matches_count_lens(self):
        # BRIDGE-001: miracle hexany (3,3) at 2c, full (6,6) at 3c
        g, _ = br.minimax_generator(MIRACLE)
        temp = {p: bb.tempered_pitch(MIRACLE, g, br.monzo_of(
            br.reduce_rational(Fraction(p)))) for p in br.HEXANY_PRODUCTS}
        self.assertEqual(bb.identity_survival(temp, 2.0), (3, 3))
        self.assertEqual(bb.identity_survival(temp, 3.0), (6, 6))

    def test_grossly_detuned_image_keeps_no_identity(self):
        # 100c-scale random-looking offsets: count lens may still find
        # accidental triples; the identity lens must not
        temp = {3: 700.0, 5: 300.0, 7: 1000.0, 15: 1100.0, 21: 400.0, 35: 50.0}
        self.assertEqual(bb.identity_survival(temp, 2.0), (0, 0))


class TestRailEquality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        with (HERE / "results" / "bridge001.jsonl").open() as fh:
            for line in fh:
                r = json.loads(line)
                if r["status"] == "scored":
                    cls.rows[(r["comma"], tuple(r["val"]))] = r

    def test_miracle_21_and_orwell_22_match_bridge001(self):
        for comma, val, mapping in (("225/224", (21, 33, 49, 59), MIRACLE),
                                    ("225/224", (22, 35, 51, 62), ORWELL)):
            ref = self.rows[(comma, val)]
            self.assertEqual(tuple(tuple(r) for r in ref["mapping"]), mapping)
            row = bb.measure_both(mapping, val, val[0])
            prime = row["tunings"]["prime"]
            self.assertAlmostEqual(prime["generator_cents"],
                                   ref["generator_cents"], places=9)
            self.assertEqual(prime["max_error_cents"], ref["max_error_cents"])
            self.assertEqual(prime["hexany"]["P"],
                             ref["subsets"]["hexany"]["image_P"])
            self.assertEqual(prime["hexany_full_recovery_eps"],
                             ref["posthoc_hexany_full_recovery_eps"])
            self.assertEqual(row["contained"], ref["host"]["contained"])


if __name__ == "__main__":
    unittest.main()
