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

## 2026-07-21 — Real C++ under test + CROSSVAL-002 (entry before run)

**Context:** Marcus approved touching the plugin for test coverage ("the
high/long road"). Plugin refactor: TuningImp::paint/_paintHelper moved to
new TuningImp+paint.cpp (pure code motion, repo's existing +paint idiom),
dead WilsonicProcessor include removed from Brun+Gral.cpp; full Xcode
Shared Code build SUCCEEDED. New tests/test_tuning compiles the REAL
TuningImp/Brun/MicrotoneArray/Microtone/Fraction and runs them; CI now
runs it (build.yml).

**First execution of the real analyzer FALSIFIED the mirror:** real
hexany 1-3-5-7 reports (1,2), not the loop-level (2,2) the mirror
predicted. Root cause read from source and confirmed: the analyzer's
octave-wrap machinery finds cross-octave triads, but the post-loop
NPO-map filter (TuningImp.cpp:849-858) looks up UNWRAPPED indices in a
map keyed 0..npo-1 — every wrapped triad is silently dropped from the
reported lists. Mirror now models both stages (npo_map_filter toggle);
corrected mirror PREDICTED hexany 1-3-5-9 = (1,2) before the C++ test
ran, and the C++ test confirmed. test_tuning: 46/46. Python suite: 43/43.

**Hypothesis (CROSSVAL-002):** across all 70 hexanies and a 15-scale MOS
sweep, the real CLI's scales match the mirror bit-for-bit (hexany) /
within 1 ulp (MOS, libm pow), and its reported counts equal the mirror's
plugin-exact counts.

**Result:** CONFIRMED, 0 mismatches (results/crossval002.json). 70
hexany scales bit-exact; 15 MOS scales cardinality-exact and within 1 ulp
on every degree; all 85 analyzer count pairs equal. The mirror is now
corpus-validated against the executing plugin code, and the research
harness can use tests/research_cli (real C++) as a generation oracle.
Side observation for later: the fifth-generator MOS scales report (0,0)
triads under the plugin's 0.0005 absolute tolerance — the Pythagorean
thirds miss the arithmetic-mean coincidences, consistent with theory.

**Kept.** Runs: `make -C tests run`, `python3.12 crossval002.py`.

## 2026-07-21 — overnight: HEX-003 + EIK-001 (entry before run)

**Hypothesis (HEX-003):** the period-space dual of every hexany swaps P
and S exactly under both conventions (pipeline duality holds: odd-seed
CPS never contains 1/1), so dual rankings are identical and hexanies are
self-dual as a family.

**Hypothesis (EIK-001):** CPS(6,3) is self-inverse, so every eikosany —
including Marcus's calibration set {1,45,135,225,19,377} — sits exactly
on P = S under the anchored convention, extending the hexany diagonal
theorem to 20 tones.

**Result:** BOTH CONFIRMED (results/hex003_eik001.json). HEX-003: 0 swap
failures across 70 duals × 2 conventions. EIK-001: all 29 eikosanies sit
exactly on P = S (anchored) — the diagonal theorem holds at 20 tones,
even for the calibration set, and even the window convention stays
within ±2 of the diagonal at this size. Ranking: the classic
1-3-5-7-9-11 eikosany tops the field at P=S=77 (G=12); Marcus's
{1,45,135,225,19,377} scores P=S=22, G=0 — rank 29/29 by min(P,S).
That last fact is the sharpest felt-sense-vs-metric probe yet: if the
calibration set sounds richer to Marcus than its bottom rank suggests,
min(P,S) is missing something his ear hears (candidates: prime-limit
color, difference-tone structure, or triad QUALITY weighting vs raw
count). Playable: results/scl/eik_1-3-5-7-9-11.scl and
eik_1-45-135-225-19-377.scl. Ear-check queued for Marcus (HEX-002/EIK).

**Kept.** Run: `python3.12 hex003_eik001.py`.

## 2026-07-21 — overnight: MOS-001/002 generator sweep (entry before run)

**Hypothesis:** the generator landscape for anchored min(P,S) at ε=2¢ is
mostly dead (score 0) with isolated hot generators; simple-ratio regions
(fifth complement ~498¢, meantone ~504¢) score above noble/EDO
landmarks at matched cardinality, and score varies smoothly enough with
ε (0.5/1/2/5 logged per point) that ε=2 is not a phase-transition edge.

**Result:** MOSTLY CONFIRMED, one guard weakness exposed. Fine sweep:
0.1¢ over (0,600]¢, 30,009 (generator, cardinality) records × 4 ε
(results/mos001_fine.jsonl; guarded rankings in
mos001_fine_guarded.txt; ε table in mos002_epsilon_sensitivity.txt).
Signal that is stable across ε — the real discoveries:
- **g ≈ 571.6–572.0¢ dominates odd cardinalities** (N=7,9,11,13,15,17;
  e.g. N=17 min=78 at ε=2). Not an obvious simple ratio; complement
  ≈628.4¢ ≈ 23/16. Prime candidate for a closer look + ear check.
- **N=12 is won by 498.2–498.5¢ — the pure fourth** (fifth-generator
  Pythagorean MOS), min=25 at ε=2. Wilson's fifth wins its home bin.
- 416.3¢ owns N=20 across ε=0.5/1/2; 486.7–498¢ (fourth region) owns
  N=12/17/22 at tight ε; 286¢ region owns N=13/21.
- Landmarks: fifth-MOS N=12 (19,19) vs meantone-504¢ N=12 (2,2) at ε=2 —
  just intonation beats meantone decisively on this metric.
Guard weakness: at ε=0.5/1 the 4ε min-step guard still admits 2–4¢
micro-generators, which top N=5–10 bins (min step scales with the guard
so tiny-ε bins stay polluted). The degeneracy treatment belongs in the
scorer or in a scale-shape prior — Marcus's call (see FINDINGS.md
ε-degeneracy entry). Every record carries all four ε scores, so any
future guard re-ranks for free.

**Kept.** Runs: `python3.12 mos001.py --step 0.1 ...`,
`python3.12 mos_report.py results/mos001_fine.jsonl`.

## 2026-07-21 — DECISION 1: anchored is the primary convention (Marcus)

**Decision:** middle-anchored is PRIMARY; two-octave-window retained for
comparison only. Marcus's call, presented with the frozen counterexamples.

**Grounds:** anchored is exactly self-dual for every scale (incl.
1/1-bearing) and exactly transposition-invariant; window is neither
(segment 8..16 → (46,8) vs dual (7,42); hexany ×3 → (11,11) vs (10,9),
both pinned in tests/test_scorer.py). The plan §1.1 text specified a
sampling procedure while §4 TRIAD-004 specified an invariant that "MUST
pass exactly"; where they conflict the invariant wins. The window's P≠S
scatter for CPS is boundary noise, not signal.

**Applied, purely additively:** scorer.py gains `score()` /
`score_tempered()` as the canonical entry points (dispatch to anchored),
`PRIMARY_CONVENTION`/`ANCHORED_CONVENTION`/`WINDOW_CONVENTION` constants,
and `score_rational_window` / `score_cents_window` names — the legacy
`score_rational` / `score_cents` remain as aliases to the WINDOW pair, so
every existing script (hex001, mos001, crossval001, hex003_eik001) and
every archived record keeps its exact meaning. Module docstring now states
the decision, its rationale, and the P=S diagonal consequence. Plan §1.1
annotated `[SUPERSEDED 2026-07-21]`. Four new goldens pin the dispatch so
a later edit cannot silently repoint `score()`.

**Not changed:** no scoring arithmetic, no result files. Suite 52 → 56/56.

**Kept.** Run: `python3.12 -m unittest discover -s tests`.
