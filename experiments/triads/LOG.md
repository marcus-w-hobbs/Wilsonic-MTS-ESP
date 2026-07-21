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

## 2026-07-20 — HEX-001: exhaustive hexany sweep (entry written before run)

**Hypothesis:** among all 70 hexanies from odd seeds ≤ 15, the classic
1-3-5-7 ranks at or near the top of the 6-note bin on min(P,S); CPS
inversion symmetry keeps all hexanies near the P = S diagonal under the
anchored convention.

**Result:** CONFIRMED and sharpened. 70 hexanies scored (68 six-note, 2
five-note from product collisions). Under the anchored convention every
hexany sits EXACTLY on P = S — not near the diagonal, on it (see
FINDINGS.md). 1-3-5-7 ranks 3/68 (anchored, P=S=8) and 4/68 (window).
The winners are 9-bearing seed sets: 1-3-5-9 (P=S=9, G=4) and 1-3-9-15
(P=S=9, G=4) — the 3² inside the seeds buys extra arithmetic chains plus
four geometric triads. 3-5-7-15 ties 1-3-5-7 on every count under both
conventions, yet is a genuinely different scale (checked: not a
transposition and not the dual — an unexplained exact tie worth a look). Artifacts: results/hex001.jsonl (full provenance: scorer
0.1.0, commit 277eb519, exact products per entry), results/scl/*.scl for
the top 10 — ready for the HEX-002 ear check in Wilsonic.

**Kept.** Run: `python3.12 hex001.py`, deterministic, re-runnable.

## 2026-07-20 — CROSSVAL-001: executable receipts for the C++ (entry before run)

**Hypothesis:** (1) the real compiled Microtone/Fraction code agrees
bit-for-bit with a pure-Python float32 mirror on octave reduction and CPS
products, including the predicted boundary anomaly where the rational
(2^25−1)/2^24 reduces OUTSIDE [1,2); (2) the plugin triad analyzer's
counts diverge from the exact scorer in ways fully attributable to its
three known deviations (absolute linear tolerance — register-dependent in
cents, 9/8..4/3 interval filter, one-octave+wrap domain).

**Result:** (1) CONFIRMED, 27/27 cases bit-exact (results/crossval001.json),
including the boundary anomaly — the real plugin code reduces
(2^25−1)/2^24 to 33554431/33554432 < 1, an exact-rational violation of
[1,2) masked by float rounding. (2) CONFIRMED with a stronger headline
than expected: the plugin analyzer finds only (2,2) of the 1-3-5-7
hexany's (8,8) triad classes — 0/70 hexanies agree with exact counts.
Attribution: interval filter accounts for (2,2)→(4,2); the rest is the
restricted domain + pitch-class dedup. Tolerance is 0.865¢ at f=1 vs
0.433¢ at f≈2 (register-dependent by 2×). Mirror pinned by hermetic
goldens (tests/test_cpp_mirror.py); full suite now 40/40. Gaps that
remain ungrounded are enumerated in VERIFICATION.md (chief: the real
analyzer and Brun zigzag have never executed under test — closing those
requires touching the plugin test target, Marcus's call).

**Kept.** Runs: `make -C cpp_receipts run`, `python3.12 crossval001.py`.
