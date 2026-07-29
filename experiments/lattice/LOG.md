# Experiment log — lattice (melody ⇄ lattice ⇄ harmony)

Format: hypothesis → result → kept/reverted. Entry written BEFORE each run.
This is the **lattice module's own notebook**, deliberately separate from
`experiments/triads/LOG.md` so the two workstreams never fight over the same
append-only file. Same discipline, different file. Findings promoted to
`experiments/lattice/FINDINGS.md`; receipts under `experiments/lattice/results/`.

The contract is `experiments/lattice/SPEC.md` (hypotheses, tolerances, design
decisions, primary-source citations). Execution order: SPEC.md §"Order of
execution".

## Scorer baselines

- **Frozen triad scorer**: `experiments/triads/scorer.py` **v1.1.0**, unchanged
  by this module (SPEC.md freeze-compliance clause). Anything scored with the
  frozen scorer here — e.g. BRIDGE-000's D'Alessandro harmonic-fidelity
  measurement, `.scl` ear-check exports — is a **v1.1.0** measurement (triads
  counted within a single octave; the ear-validated regime). Do not mix with
  pre-2026-07-24 v1.0.0 numbers.
- **Melodic scorer**: `experiments/lattice/melodic.py`, versioned
  independently, starts at **v0.1.0**; freeze (hash-pin pattern) after Marcus
  reviews LAT-MEL-001.

## 2026-07-24 — coordination: branch brought current to scorer v1.1.0

**Context (not a run):** this branch forked from `16a7913` (triads LOOP-001)
when the frozen scorer was v1.0.0. The triads session then landed v1.1.0 (PR
#14 → `main`): triads must now fit **within an octave**, an ear-validated
change that re-ranks results and drops ~25–30% of prior counts. Scoring the
lattice queue against v1.0.0 would have produced numbers incomparable with the
current frozen scorer and with any future triads work.

**Action:** merged `origin/main` into this branch (non-destructive merge, not a
rebase, since the branch is pushed and lives in a worktree). Clean merge, no
conflicts; `scorer.py` now v1.1.0 with its pin intact, harness suite 88/88.
`experiments/lattice/SPEC.md` preserved. No lattice code written yet, so there
were no stale lattice receipts to regenerate.

**Kept.** Every lattice receipt from here records scorer 1.1.0.

## 2026-07-25 — melodic.py v0.1.0: M1/M2/M3 scorers + unit tests

**Hypothesis (pre-run):** the three melodic scorers specced in SPEC.md
§"Melodic scorers" can be implemented as pure functions of a cents
pitch-class multiset and will reproduce the SPEC's expected unit-test
outcomes: 12-EDO diatonic (proper, CS, 2 gaps), 12-EDO whole-tone (strictly
proper, 1 gap), Pythagorean [wolf] 12 (improper), random 6-note (high gap
entropy).

**Design decisions (logged before the run):**
- Canonical form delegates to the frozen scorer's `canonical_cents_scale`
  (read-only import, scorer v1.1.0) so both axes agree on what "the scale"
  is; dedup ε default 0.01¢ per SPEC (scorer's own default is 1e-6¢).
- Clustering (M1 gaps, M2 interval sizes): sorted values, new cluster when
  value − cluster_minimum > ε. Anchored to the cluster MINIMUM, not the
  previous value — no unbounded chaining; deterministic.
- M1 entropy reported in BITS (base 2); the SPEC's "entropy ≤ log 2" for
  MOS reads as ≤ 1 bit.
- M2 machine check: spans 1..N−1, all N·(N−1) circular intervals; a size
  class at ≥2 distinct spans is one violation. Val lens (exact rationals
  only): patent val for the scale's actual prime limit, ±1 per odd-prime
  coordinate, FULL product (3^k vals, logged); Kendall tau = discordant
  pair count, ties recorded separately, deterministic first-minimum wins.
- M3 comparisons use ε_prop = 1e-9¢ as a float-noise guard only; equality
  within ε_prop blocks strictness, not propriety.

**Result (goldens hand-derived while pinning, then suite executed):** two
SPEC parentheticals are FALSE and are corrected in the pinned tests:
1. 12-EDO diatonic is NOT a constant structure — the 600¢ tritone subtends
   3 steps (F–B) and 4 steps (B–F′): exactly one violating class. (It IS
   proper-but-not-strict via the max-span-3 = min-span-4 = 600¢ equality.)
   Pythagorean diatonic and Pythagorean 12 ARE CS (611.73 vs 588.27¢ split
   cleanly at ε_CS = 0.5¢) — CS-ness here is a JI-vs-tempering distinction,
   a nice first sanity signal for the melodic axis.
2. Pythagorean [wolf] 12 is STRICTLY PROPER (apotome/limma runs never cross
   spans; zero violations, zero equalities). The known-improper fixture is
   the Pythagorean DIATONIC 7 — aug4 611.73¢ at 3 steps > dim5 588.27¢ at
   4 steps, Rothenberg's classic example. Tests pin the machine-checked
   truth for both scales.
Suite: experiments/lattice/tests/test_melodic.py, run recorded below.

**Kept.** melodic.py v0.1.0 as implemented; SPEC.md §"Melodic scorers"
parentheticals stand corrected by machine check (SPEC text left untouched —
it is the historical contract; corrections live here, in the module
docstring, and in the pinned tests). Not yet frozen: freeze follows
Marcus's LAT-MEL-001 review per SPEC.

**Run receipt:** 2026-07-25, python3.12 — lattice suite 25/25 OK; triads
suite re-run 88/88 OK; scorer freeze check A OK (pin 1a840af9…9b592
unchanged). No receipts under results/ yet — this entry gates the first
LAT-MEL-001 run.

## 2026-07-25 — LAT-MEL-001: melodic scoring of the harmonic corpus (pre-registration)

**Hypotheses under test (SPEC §LAT-MEL-001), predictions BEFORE the run:**
- **H-L1:** the eikosany {1,3,5,7,9,11} is a constant structure at ε_CS = 0.5¢
  (M2 violations = 0). Verifies the claim attributed to Wilson. Prediction:
  PASS (CS), but either outcome is a finding.
- **H-L2:** CPS scales are systematically improper/multi-gap vs MOS at matched
  cardinality, BUT melodic rank varies within the CPS family. Predictions:
  (a) ≥80% of hexanies/eikosanies classify improper while ≥80% of true MOS
  controls classify proper-or-strict; (b) mean gap-class count of CPS exceeds
  MOS at matched N by ≥2; (c) within-family spread: hexany gap entropy and
  propriety-violation counts are NOT constant (the melodic axis discriminates
  on the P = S diagonal where the harmonic axis cannot).
- **H-L3** deferred (needs SHADOW-001 variants — none exist yet).
- **H-L4** deferred to a designed lattice-region corpus (identity-set regions,
  not whole CPS scales); this run only establishes the M1 baseline.

**Corpus (deterministic):** 70 hexanies = odd_seed_sets(4,15); 29 eikosanies =
odd_seed_sets(6,15) ∪ {1,45,135,225,19,377} (the hex003_eik001 set); dekanies
SKIPPED this run (scope). Controls: true MOS (zigzag cardinalities 5–22) for
generators g ∈ {701.955¢ fifth, 498.045¢ fourth, 571.6¢, 416.2¢, 741.638¢
noble/φ} (hot spots from mos001 receipts + the classic pair + one noble);
rank-1 chains at exactly N = 6 and N = 20 for the same generators
(cardinality-matched controls); 20 random uniform scales each at N = 6 and
N = 20, seed 20260725.

**Scorers:** melodic.py v0.1.0 (M1/M2/M3 defaults: ε_dedup 0.01¢, ε_gap 0.5¢,
ε_CS 0.5¢) + best-val Kendall tau on the JI corpus; frozen triad scorer
v1.1.0 primary entry points (rational path for JI, tempered ε = 2.0¢ for
cents-only controls). Every row records versions and epsilons.

**Deliverable:** results/latmel001.jsonl (one row per scale) + Pareto scatter
(melodic = gap entropy & propriety; harmonic = anchored P) for the G-006
review. Runner: latmel001.py (deterministic, stdlib only).

## 2026-07-25 — LAT-MEL-001: results and verdict

**Run:** latmel001.py, 174 rows → results/latmel001.jsonl (70 hexanies, 29
eikosanies incl. calibration set, 25 true MOS, 10 rank-1 chains, 40 random).
Post-hoc diagnostics (labeled as such, exact-rational, zero floats) →
results/latmel001_posthoc.json.

**H-L1: REFUTED — decisively, at every tolerance including exact.** The
eikosany {1,3,5,7,9,11} is NOT a constant structure: 32 interval-size classes
occur at two adjacent spans, and the coincidences are EXACT rational
identities, not ε-artifacts — 9/8 subtends both 3 and 4 steps; 22/21 and
21/20 subtend 1 and 2; 12/11 and 11/10 subtend 2 and 3 (full list in the
post-hoc receipts). Same verdict at ε_CS ∈ {0.5, 0.1, 0.01, 1e-6}¢.
**Family-wide: 0/29 eikosanies are CS, while 66/70 hexanies ARE CS.**
Mechanism found via the val lens: the best val ⟨20,32,46,56,70⟩ (a +1
perturbation on the 11 coordinate beats the patent val) orders the eikosany
with zero inversions but **13 tie pairs** — 13 pairs of tones share a val
degree, so the degree map is weakly monotone, never epimorphic onto 20
degrees, and a tied degree is exactly what lets one interval subtend two step
counts. Interpretation (for G-007): Wilson's melodic-compatibility statements
(e.g. "2 Eikosanies melodically compatible with modulus 22", 1968) likely
refer to CPS *embedded in a larger modulus*, not the bare 20-tone
octave-reduced scale — refuting H-L1 on the bare scale *strengthens* the
BRIDGE program's premise that melodic viability comes from the embedding.

**H-L2: CONFIRMED, with an instructive control-side surprise.**
(a) Hexanies 81% improper, eikosanies 100% — prediction ≥80% met. BUT true
MOS are only 8/25 proper-or-strict (prediction said ≥80%): propriety of an
MOS is generator-dependent (noble φ 741.64¢: 4/4 strictly proper; 416.2¢ and
571.6¢ — the triad hot spots! — 0/13 proper). The SPEC's "MOS saturate the
melodic scores" holds for gaps and CS (every MOS: exactly 2 gap classes,
25/25 CS) but NOT for propriety. Noted: the harmonic hot-spot generators
produce IMPROPER MOS — a first hint the two axes genuinely trade off.
(b) Gap classes at matched cardinality: hexany mean 3.94 vs MOS exactly 2;
eikosany 9.86 vs 2 (random: 5.95 at N=6, 18.55 at N=20 — CPS sits between
MOS and random, closer to random as k grows). Prediction (Δ ≥ 2) met.
(c) Within-family discrimination: 13/70 hexanies are non-improper (11 of 13
contain both 1 and 5), propriety violations spread 0..4, CS fails for
exactly 4 hexanies — and all four contain 9 alongside 3 or 15, i.e. the
composite 9 = 3² creates the exact interval duplications. M1 entropy is
nearly degenerate within-family (66/70 hexanies share entropy 1.918) — gap
COUNT and propriety discriminate; entropy mostly does not at fixed N.
**The composite-9 CS fingerprint feeds H-L4b and H-S3 directly.**

**H-L3, H-L4:** untouched this run (no SHADOW variants; no designed
lattice-region corpus yet), as pre-registered.

**Kept.** Receipts stand; melodic.py v0.1.0 unchanged by the run. G-006
(does the melodic axis rank the way the ear does?) and G-007 (H-L1
interpretation) are now PENDING on Marcus with these receipts as evidence.
