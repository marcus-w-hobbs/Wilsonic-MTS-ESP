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
