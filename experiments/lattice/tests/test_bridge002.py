"""Unit tests for bridge002.py (BRIDGE-002, the eikosany as bridge payload).
Written BEFORE the first experiment run (LOG.md pre-registration 2026-10-09):
five-prime generalizations checked against the 7-limit originals on the
BRIDGE-001 fixtures, the payload and its identity triads, the join-of-vals
sweep, chain-span / minimax / identity pins, the survival grid, Wilson's
huygens-31 template, and the host-window melodic receipt.

Run from experiments/lattice/:
    python3.12 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import bridge001 as br  # noqa: E402  (7-limit originals)
import bridge001b as bb  # noqa: E402  (7-limit identity lens / solver)
import bridge002 as b2  # noqa: E402


def m11(*commas):
    return b2.mapping_of_commas(commas)


MIRACLE = m11("225/224", "1029/1024", "385/384")
ORWELL = m11("225/224", "1728/1715", "99/98")
MAGIC = m11("225/224", "245/243", "100/99")
HUYGENS = m11("81/80", "126/125", "99/98")
HEMIFIFTHS = m11("2401/2400", "5120/5103", "441/440")
RODAN = m11("245/243", "1029/1024", "385/384")
GARIBALDI = m11("32805/32768", "5120/5103", "385/384")
HUYGENS_31 = (31, 49, 72, 87, 107)      # D'Alessandro's template (BRIDGE-000)


class TestLinearAlgebraGeneralization(unittest.TestCase):
    def test_nullspace_matches_bridge001_in_four_dims(self):
        for a, b in (("225/224", "1029/1024"), ("81/80", "126/125"),
                     ("225/224", "1728/1715"), ("50/49", "64/63")):
            rows = [br.monzo_of(Fraction(a)), br.monzo_of(Fraction(b))]
            self.assertEqual(b2.nullspace_saturated(rows, 4),
                             br.nullspace_saturated(rows))
            self.assertEqual(b2.hnf_mapping(b2.nullspace_saturated(rows, 4)),
                             br.hnf_mapping(br.nullspace_saturated(rows)))

    def test_eleven_limit_mappings_restrict_to_seven_limit_ones(self):
        def m7(a, b):
            return br.hnf_mapping(br.nullspace_saturated(
                [br.monzo_of(Fraction(a)), br.monzo_of(Fraction(b))]))
        pairs = ((MIRACLE, m7("225/224", "1029/1024")),
                 (ORWELL, m7("225/224", "1728/1715")),
                 (MAGIC, m7("225/224", "245/243")),
                 (GARIBALDI, m7("32805/32768", "5120/5103")))
        for full, seven in pairs:
            self.assertEqual(tuple(r[:4] for r in full), seven)

    def test_known_mappings(self):
        self.assertEqual(MIRACLE, ((1, 1, 3, 3, 2), (0, 6, -7, -2, 15)))
        self.assertEqual(ORWELL, ((1, 0, 3, 1, 3), (0, 7, -3, 8, 2)))
        self.assertEqual(HUYGENS[1], (0, 1, 4, 10, 18))   # D'Alessandro chain

    def test_val_combo(self):
        self.assertEqual(b2.val_combo(b2.patent_val(31), MIRACLE), (31, 3))
        self.assertEqual(b2.val_combo(b2.patent_val(41), MIRACLE), (41, 4))
        self.assertIsNone(b2.val_combo(b2.patent_val(43), MIRACLE))


class TestPayload(unittest.TestCase):
    def test_twenty_distinct_tones_and_base(self):
        self.assertEqual(len(b2.TONES), 20)
        self.assertEqual(b2.FULL, (57, 57))
        self.assertEqual(b2.EIKOSANY_BASE.geometric, 6)
        self.assertEqual(len(b2.EIKOSANY_TRIADS), 114)
        self.assertEqual(b2.TONES[0]["ratio"], Fraction(33, 32))  # no 1/1

    def test_subsets_match_subsetmel000(self):
        import subsetmel000 as sm
        ref = {s.name: s for s in sm.enumerate_subsets(b2.SEEDS)
               if s.kind in ("hexany", "dekany_in", "dekany_out")}
        self.assertEqual(len(ref), 42)
        for s in b2.SUBSETS:
            self.assertIn(s["name"], ref)
            self.assertEqual(
                b2.canonical_rational_scale(Fraction(p) for p in s["products"]),
                ref[s["name"]].tones)
        self.assertEqual(len(b2.HEXANIES), 30)
        self.assertEqual(len(b2.DEKANIES), 12)

    def test_hexany_identity_triads_match_bridge001b(self):
        mine = b2.base_triads(br.HEXANY_PRODUCTS)
        self.assertEqual(sorted(mine), sorted(bb.HEXANY_TRIADS))

    def test_subset_triads_are_eikosany_triads(self):
        allt = set(b2.EIKOSANY_TRIADS)
        for s in b2.SUBSETS:
            self.assertTrue(set(s["triads"]) <= allt)


class TestMonotonicity(unittest.TestCase):
    def test_root_not_required_at_degree_zero(self):
        mono = b2.monotonicity(HUYGENS_31)
        self.assertTrue(mono["monotone"])
        self.assertEqual(mono["degrees"][0], 1)          # 33/32 -> degree 1
        self.assertEqual(mono["collisions"], [])         # injective

    def test_strict_decrease_rejects(self):
        v = (31, 49, 72, 87, 112)     # 11 mapped far too high
        mono = b2.monotonicity(v)
        self.assertFalse(mono["monotone"])
        self.assertTrue(mono["violations"])

    def test_degree_tie_is_collision(self):
        # 20-patent maps two eikosany tones to one degree (LAT-MEL-001: the
        # eikosany's best val <20,32,46,56,70> has tied pairs)
        mono = b2.monotonicity((20, 32, 46, 56, 70))
        self.assertTrue(mono["collisions"])


class TestJoinSweep(unittest.TestCase):
    def test_join_of_patent_vals(self):
        self.assertEqual(b2.join_mapping(b2.patent_val(31), b2.patent_val(41)),
                         MIRACLE)
        self.assertEqual(b2.join_mapping(b2.patent_val(22), b2.patent_val(31)),
                         ORWELL)
        self.assertEqual(b2.join_mapping(b2.patent_val(19), b2.patent_val(22)),
                         MAGIC)

    def test_dependent_val_gives_none(self):
        v = b2.patent_val(31)
        self.assertIsNone(b2.join_mapping(v, tuple(2 * x for x in v)))

    def test_every_join_is_supported_by_both_vals(self):
        v = b2.patent_val(31)
        for m in range(1, 12):
            for w in b2.vals_for(m):
                mapping = b2.join_mapping(v, w)
                if mapping is not None:
                    self.assertIsNotNone(b2.val_combo(v, mapping))
                    self.assertIsNotNone(b2.val_combo(w, mapping))

    def test_names_resolve(self):
        names = b2.resolve_names()
        self.assertEqual(names[MIRACLE], "miracle")
        self.assertEqual(names[ORWELL], "orwell")
        self.assertEqual(names[HUYGENS], "huygens")
        self.assertEqual(names[HEMIFIFTHS], "hemififths")


class TestChainSpans(unittest.TestCase):
    def span(self, mapping):
        return b2.host_receipt(mapping, 100, [0] * 20)["chain_span"]

    def test_pins(self):
        self.assertEqual(self.span(MIRACLE), 43)
        self.assertEqual(self.span(ORWELL), 31)
        self.assertEqual(self.span(HUYGENS), 30)
        self.assertEqual(self.span(HEMIFIFTHS), 38)
        self.assertEqual(self.span(RODAN), 41)
        self.assertEqual(self.span(GARIBALDI), 49)

    def test_huygens_31_contained_with_two_anchors(self):
        mono = b2.monotonicity(HUYGENS_31)
        host = b2.host_receipt(HUYGENS, 31, mono["degrees"])
        self.assertTrue(host["contained"])
        self.assertEqual(host["anchor_interval"][1] - host["anchor_interval"][0],
                         1)

    def test_miracle_41_not_contained(self):
        mono = b2.monotonicity(b2.patent_val(41))
        self.assertFalse(b2.host_receipt(MIRACLE, 41, mono["degrees"])
                         ["contained"])


class TestMinimax(unittest.TestCase):
    def test_prime_minimax_miracle_pin(self):
        g, err = b2.prime_minimax(MIRACLE)
        self.assertAlmostEqual(g % 1200, 116.591, delta=0.002)
        self.assertAlmostEqual(err, 2.451, delta=0.002)

    def test_prime_minimax_reproduces_bridge001_on_seven_limit(self):
        # restricting the 11-limit prime lines to {3,5,7} must give
        # bridge001's solver result on the 7-limit mapping
        for full in (MIRACLE, ORWELL, MAGIC):
            seven = tuple(r[:4] for r in full)
            g0, e0 = br.minimax_generator(seven)
            lines = b2.lines_for(full, b2.PRIME_MONZOS[:3])
            g1, e1 = b2.minimax_exact(lines)
            self.assertAlmostEqual(g0, g1, places=9)
            self.assertAlmostEqual(e0, e1, places=9)

    def test_fast_solver_equals_exact_solver(self):
        for mapping in (MIRACLE, ORWELL, HEMIFIFTHS, RODAN, HUYGENS):
            lines = b2.lines_for(mapping, b2.TONE_MONZOS)
            g0, e0 = b2.minimax_exact(lines)
            g1, e1 = b2.minimax_fast(lines)
            self.assertAlmostEqual(g0, g1, places=6)
            self.assertAlmostEqual(e0, e1, places=6)

    def test_interval_fast_equals_exact_on_small_case(self):
        lines = b2.interval_lines(MIRACLE, b2.TONE_MONZOS[:8])
        g0, e0 = b2.minimax_exact(lines)
        g1, e1 = b2.minimax_fast(lines)
        self.assertAlmostEqual(g0, g1, places=6)
        self.assertAlmostEqual(e0, e1, places=6)

    def test_tone_set_never_worse_than_prime_on_tones(self):
        for mapping in (MIRACLE, ORWELL, HEMIFIFTHS):
            gp, _ = b2.prime_minimax(mapping)
            _, et = b2.tone_set_minimax(mapping)
            worst = max(abs(e) for e in b2.tone_errors(mapping, gp))
            self.assertLessEqual(et, worst + 1e-9)


class TestIdentityPins(unittest.TestCase):
    def survival(self, mapping, g, eps):
        return b2.identity_survival(b2.tempered_by_product(mapping, g), eps,
                                    b2.EIKOSANY_TRIADS)

    def test_exact_image_survives_fully(self):
        import math
        temp = {p: 1200 * math.log2(b2.reduce_rational(Fraction(p)))
                for p in b2.PRODUCTS}
        self.assertEqual(b2.identity_survival(temp, 0.01, b2.EIKOSANY_TRIADS),
                         (57, 57))

    def test_miracle_prime_pin(self):
        g, _ = b2.prime_minimax(MIRACLE)
        self.assertEqual(self.survival(MIRACLE, g, 2.0), (29, 29))
        self.assertEqual(b2.identity_recovery(b2.tempered_by_product(MIRACLE, g),
                                              b2.EIKOSANY_TRIADS, b2.FULL), 4)

    def test_hemififths_interval_pin(self):
        g, _ = b2.interval_minimax(HEMIFIFTHS)
        self.assertEqual(self.survival(HEMIFIFTHS, g, 2.0), (44, 44))
        self.assertEqual(b2.identity_recovery(
            b2.tempered_by_product(HEMIFIFTHS, g), b2.EIKOSANY_TRIADS,
            b2.FULL), 6)

    def test_tone_set_lowers_miracle_raises_orwell(self):
        gp, _ = b2.prime_minimax(MIRACLE)
        gt, _ = b2.tone_set_minimax(MIRACLE)
        self.assertLess(self.survival(MIRACLE, gt, 2.0)[0],
                        self.survival(MIRACLE, gp, 2.0)[0])
        gp, _ = b2.prime_minimax(ORWELL)
        gt, _ = b2.tone_set_minimax(ORWELL)
        self.assertGreater(self.survival(ORWELL, gt, 2.0)[0],
                           self.survival(ORWELL, gp, 2.0)[0])

    def test_survival_grid_dominates_analytic(self):
        for mapping in (HEMIFIFTHS, RODAN):
            gp, _ = b2.prime_minimax(mapping)
            gt, _ = b2.tone_set_minimax(mapping)
            gi, _ = b2.interval_minimax(mapping)
            sg = b2.survival_grid(mapping, gp, (gp, gt, gi))
            best = max(sum(self.survival(mapping, g, 2.0)) for g in (gp, gt, gi))
            self.assertGreaterEqual(sg["identity_P"] + sg["identity_S"], best)
            self.assertEqual(sg["grid_points"] >= 1001, True)


class TestRows(unittest.TestCase):
    def test_huygens_31_full_row(self):
        mono = b2.monotonicity(HUYGENS_31)
        row = b2.measure_row(HUYGENS, HUYGENS_31, 31, mono, [b2.patent_val(12)],
                             "huygens", b2.enumerate_commas())
        self.assertEqual(row["schema"], "full")
        self.assertTrue(row["contained"])
        self.assertTrue(row["injective"])
        self.assertIn("81/80", row["kernel_commas"])
        for t in b2.TUNINGS:
            self.assertIsNotNone(row["tunings"][t])
            self.assertFalse(row["tunings"][t]["h_c1_pass"])
        mel = row["tunings"]["prime"]["melodic"]
        self.assertEqual(mel["gap_classes"], 2)             # 31-note meantone MOS
        self.assertEqual(mel["n_notes"], 31)
        hx = row["tunings"]["survival"]["hexanies"]["full_at_eps"]
        self.assertLessEqual(hx["2"], hx["3"])
        self.assertLessEqual(hx["3"], hx["4"])
        self.assertEqual(len(row["tunings"]["survival"]["hexanies"]["rows"]), 30)

    def test_uncontained_row_is_prime_only(self):
        v = b2.patent_val(41)
        mono = b2.monotonicity(v)
        self.assertTrue(mono["monotone"])
        row = b2.measure_row(MIRACLE, v, 41, mono, [b2.patent_val(31)],
                             "miracle", b2.enumerate_commas())
        self.assertFalse(row["contained"])
        self.assertIsNone(row["tunings"]["tone_set"])
        self.assertEqual(row["tunings"]["prime"]["identity_P"], 29)
        self.assertEqual(row["tunings"]["prime"]["identity_full_recovery_eps"], 4)

    def test_small_sweep_runs_and_dedupes(self):
        saved = (b2.N_RANGE, b2.W_RANGE)
        try:
            b2.N_RANGE, b2.W_RANGE = range(31, 32), range(1, 8)
            rows, meta = b2.run()
        finally:
            b2.N_RANGE, b2.W_RANGE = saved
        keys = [(tuple(map(tuple, r["mapping"])), tuple(r["val"])) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(meta["distinct_rows"], len(rows))
        self.assertGreater(meta["vals_monotone"], 0)
        self.assertTrue(any(r["name"] == "huygens" for r in rows))
        # the summary layer must accept compact rows (no h_c1_pass etc.)
        summary = b2.summarize(rows, meta)
        self.assertIn("h_c1", summary)
        self.assertEqual(summary["enumeration"]["distinct_rows"], len(rows))


class TestHostWindow(unittest.TestCase):
    def test_pythagorean_12_two_classes(self):
        notes = b2.window_cents(1200.0, 701.955, 12, 0, 1)
        self.assertEqual(b2.host_step_classes(notes, 12), 2)
        rec = b2.melodic_receipt(notes)
        self.assertEqual(rec["gap_classes"], 2)
        self.assertTrue(rec["is_cs"])

    def test_commas_box_contains_named(self):
        commas = {b2.frac_str(b2.ratio_of(c)) for c in b2.enumerate_commas()}
        for c in ("225/224", "385/384", "441/440", "99/98", "121/120",
                  "2401/2400", "5120/5103", "81/80", "1029/1024"):
            self.assertIn(c, commas)


if __name__ == "__main__":
    unittest.main()
