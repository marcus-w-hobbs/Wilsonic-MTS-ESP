# Experiment log — triad optimization harness

Format: hypothesis → result → kept/reverted. Entry written BEFORE each run.
Scorer freeze status: **v0.1.0 DRAFT — not yet approved by Marcus.**

## 2026-07-20 — §5 repo verification (pre-Phase-0)

**Hypothesis:** the plan's assumptions about octave reduction, Brun
level→cardinality, and CPS normalization match the C++.

**Result:** mostly confirmed, three corrections (details in plan §5, §5.1):
octave reduction is half-open [1,2) as assumed (Microtone.cpp:475); Brun
levels 0–9 map to the scale-tree ZIGZAG denominators (incl. semiconvergents),
not CF convergents (Brun.cpp:269); CPS has no normalization and no 1/1, is
float end-to-end, and never uniquifies (CPSTuningBase.cpp:18,94). The
plugin's own triad analyzer differs from the plan scorer in three ways
(absolute-frequency tolerance, 9/8–4/3 interval filter, one-octave domain) —
recorded in plan §5.1; cross-validation applies to scale generation only.

**Kept.** Plan updated inline.

## 2026-07-20 — Phase 0: scorer.py + golden tests

**Hypothesis:** the §1.1 two-octave-window scorer satisfies TRIAD-004
(exact P↔S swap under scale inversion) for any scale.

**Result:** FALSIFIED for scales containing 1/1. Segment 8..16 scores
(P,S) = (46,8) but its subharmonic dual scores (7,42), not (8,46) — a
boundary artifact of the [1,4) window (the inverted sample is the
reflection 4/T with 4 replaced by 1). The classifier itself is exact:
scoring the reflected multiset 4/T swaps exactly for every scale tested.
Also discovered: the window convention is not transposition-invariant
(hexany ×3 scores (11,11) vs (10,9)).

**Fix candidate implemented alongside spec:** middle-anchored convention
(triad middle drawn from canonical octave; outer tones = unique pitch-class
representatives in (b/2, b) and (b, 2b)). Empirically exact self-duality
for ALL scales including 1/1-bearing ones, and exact transposition
invariance. Hexany 1-3-5-7 scores exactly (8,8) under it — on the P = S
diagonal, as the CPS symmetry hypothesis predicts. Both conventions live in
scorer.py v0.1.0; **primary-convention choice is Marcus's call before
freeze**. Note: odd-seeded CPS never contains 1/1, so Phase 1 hexany work
is unaffected by the window caveat either way.

Golden corrections: 12-EDO major triad deviation from proportional is
−14.859¢ → TRIAD-003 threshold corrected from ε=14 to ε=15 in the plan.

Tests: 29/29 pass (`python3.12 -m unittest discover -s tests`), covering
TRIAD-001..004 plus transposition invariance and provenance fields.

**Kept.**
