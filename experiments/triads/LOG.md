# Experiment log — triad optimization harness

Format: hypothesis → result → kept/reverted. Entry written BEFORE each run.
Scorer freeze status: **v1.1.0 FROZEN 2026-07-21 by Marcus.** Changes to
scorer.py require his explicit approval, enforced by the `scorer_freeze`
CI job (hash pin + agent-loop marker; see check_freeze.sh). v1.1.0 was a
deliberate, approved unfreeze from v1.0.0 — the process working, not a
bypass. Results scored under different versions must never be compared;
every record carries `scorer_version` and `max_span`.

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

## 2026-07-21 — DECISION 2: ε-degeneracy guard lives in the scorer (Marcus)

**Decision:** option (d) — a tempered triple contributes to NO count unless
its own arithmetic and harmonic means are distinguishable at ε, i.e.
`|1200·log2(AM/HM)| ≥ ε`. Tempered path only; raw unguarded counts kept.

**Why not the three options as originally framed** (all measured over the
3,006-record coarse sweep × 4 ε before adopting anything):
- (a) *discount triples that are also geometric*: FAILS. 1–3¢ generators
  still won N=6–10 at ε=2 and ε=5. Narrow triples match P and S but
  usually not G — G fires only when the middle tone happens to land near
  the cents-midpoint.
- (a′) *discount triples labelled both P and S* (sharper variant found
  mid-probe): clears ε=2 and ε=5, FAILS at ε=0.5, where near-misses split
  on a knife edge — triple (0,2,3)¢ has AM and HM **0.0013¢** apart, both
  ≈0.5¢ from the middle, so one condition lands inside ε and the other
  outside and it scores as a PURE proportional.
- (b) *scorer-level min-step guard*: a scale-shape prior inside the frozen
  verifier, and min-step is the wrong invariant — it is exactly what
  under-filters today.
- (c) *raw scorer + report-layer guard*: the agent loop rewards on scorer
  output (plan §3.2), so a report-only guard means the agent optimizes the
  polluted metric. The reward hack is concrete: an unguarded 1¢ generator
  is the **global optimum of min(P,S) at every cardinality N=5–10 at every
  ε** (N=10 scores 100 raw).

**Why (d):** if a triple's AM and HM are closer together than the
resolution you are measuring at, calling it "proportional" asserts nothing
— the identical triple is equally "subcontrary". Not an opinion about
scale shape, a statement about what the measurement resolves. Equivalent
to a span cutoff (AM/HM separation is monotone in c/a): 58.8¢ at ε=0.5,
83.2¢ at ε=1, 117.7¢ at ε=2, 186.1¢ at ε=5. No-op on the exact rational
path (the three conditions are already mutually exclusive, no ε), so every
hexany/eikosany/duality result stands unchanged.

**Applied:** `mean_separation_cents` + `is_informative_triple` in
scorer.py, applied in both tempered scorers; ScoreResult gains
`proportional_raw`/`subcontrary_raw`/`geometric_raw`/`degenerate_dropped`;
mos001.py records guarded AND raw per ε; mos_report.py's min-step guard
defaults off (retained behind `--guard-factor` for pre-decision runs).
Suite 56 → 62/62.

## 2026-07-21 — MOS-003: re-rank the sweep under the guard (entry before run)

**Hypothesis:** re-running the 0.1¢ fine sweep with the guard on (1) kills
both named artifacts — the 1¢ micro-generator and the ~599¢ near-2-EDO
that owned N=15/17 — at every ε without a report-layer filter, and (2)
leaves the g ≈ 571.6–572.0¢ odd-cardinality story standing at tight ε
while weakening it at ε=2. Coarse-sweep prediction from the probe: at ε=2
the N=7/9/15/17 winners move off 572¢ (to ≈539/286/317/286¢) while 572¢
holds N=11; at ε=1 572¢ still takes N=7/9/11/15.

**Result:** (1) CONFIRMED — both artifacts gone at every ε with no report
filter. The 1¢ generator scores 0 everywhere; N=15/17 at ε=2 moved off
599¢ (near-2-EDO) to 565.5¢. (2) PARTLY CONFIRMED, and the coarse-sweep
prediction was too pessimistic: at 0.1¢ resolution the odd-cardinality
region survives as **565.5–572.2¢**, with the exact peak ε-dependent —
572.0¢ owns N=7/9/11 and 572.2¢ owns N=15 at ε=1, while 565.5¢ owns
N=11/15/17 at ε=2. So the headline restates as "the 565–572¢ region
dominates odd cardinalities", not a single generator.

New signal the guard exposed: **the fourth/fifth region wins far more
bins than before**, because it was previously buried under degenerate
scores — 497.6¢ (N=5), 498.5¢ (N=7), 498.4/498.2¢ (N=12), 486.8¢
(N=12/17/22) at tight ε. Wilson's fifth was always there; the degeneracy
was hiding it. Landmarks at ε=2, N=12: fifth-MOS (19,19) vs meantone-504¢
(2,2) — the just-intonation-beats-meantone result is unchanged.

**Honest residue:** small-N bins at extreme ε still admit cluster scales
whose triples are individually informative — 29.5¢/41.7¢ at N=6 (tight ε),
123.3¢ at N=8 and 220.5¢ at N=16 (ε=5). These are NOT resolution
artifacts: their anchored triples span ~1200¢ and genuinely resolve. What
makes them unmusical is scale *shape* (six notes inside 150¢), which we
deliberately kept out of the verifier. If those bins matter, the fix is a
declared scale-shape prior in the search/archive layer, not in the scorer.

Artifacts regenerated: results/mos001_fine.jsonl (30,009 records, now
carrying guarded AND raw counts + dropped per ε),
mos002_epsilon_sensitivity.txt, mos001_fine_report.txt,
mos001_fine_guarded.txt (legacy min-step guard, comparison only). The ε
table is now reproducible via `mos_report.py --epsilon-table` instead of
ad hoc.

**Kept.** Runs: `python3.12 mos001.py --step 0.1 --out
results/mos001_fine.jsonl` (3m47s), `python3.12 mos_report.py
results/mos001_fine.jsonl [--epsilon-table]`.

## 2026-07-21 — DECISION 3: scorer FROZEN at v1.0.0 (Marcus)

**Decision:** freeze scorer.py at 1.0.0, embodying decisions 1 and 2.
Enforcement mechanism: **A + B** (Marcus's call).

- **A — hash pin.** `scorer.sha256` pins the file's SHA-256; CI fails on
  any edit until a human refreshes the pin. Fails closed regardless of
  commit message, author or branch.
- **B — agent-loop marker.** Commits whose message carries `[agent-loop]`
  or `Agent-Loop: true` fail if their diff touches scorer.py.

Both directions verified, not just asserted: A passes clean and fails on a
tampered file; B passes over real unmarked history (3 commits scanned) and,
in a throwaway clone, caught a marked commit that touched scorer.py **even
after the working tree had been restored** — the case A alone would pass.
That is the complementarity: A catches the state, B catches the history.

**Honest limit, stated at decision time:** neither check stops an agent
that also rewrites the pin file. The guarantee is that a scorer change can
never be SILENT — the pin diff is one loud line in review. Branch
protection on main is the only harder backstop, and that is Marcus's to
enable.

**Applied:** SCORER_VERSION 0.1.0 → 1.0.0 with a version-history block in
the docstring; `check_freeze.sh` (runnable locally: `./check_freeze.sh` for
A alone, `./check_freeze.sh <base> <head>` for both); `scorer.sha256`;
new `scorer_freeze` CI job — the repo had **no Python job at all** before,
so the 64-test suite was never running in CI. Tag `scorer-v1.0.0`.
Two goldens pin SCORER_VERSION so a bump cannot happen without a
deliberate test edit. Suite 62 → 64/64.

**From here on:** any scorer change I want goes to Marcus as a proposal
first, whatever the ear checks turn up.

**Follow-up, same day — the guard bit its own documentation.** Running
check B over the freeze commit failed: the commit message *describes* the
marker strings, and the first implementation matched them anywhere in the
message. Fixed to git-trailer semantics — bracketed marker in the SUBJECT
line only, or a standalone `Agent-Loop: true` trailer line — so prose
about the mechanism cannot trip it. Both marked forms re-verified as still
caught in a throwaway clone, and the freeze commit now passes. Cheap
receipt that check B actually runs rather than silently passing.

**Provenance re-run under 1.0.0.** Every experiment regenerated so its
records carry the frozen version instead of 0.1.0: hex001 (70 hexanies),
hex003_eik001 (duals + 29 eikosanies), crossval001, crossval002, both MOS
sweeps, all three report artifacts. **Every number is identical ignoring
the provenance fields** — verified by diffing against the committed
versions (hex001 70/70, eikosany file, crossval001, fine sweep
30,009/30,009). This is the receipt that decision 1 changed nothing but
names and decision 2's guard is a genuine no-op on the exact path. C++
test_tuning 46/46, crossval002 0 mismatches, Python 64/64.

## 2026-07-21 — DECISION 4: wrap-drop NOT fixed (Marcus)

**Decision:** no UI changes to Wilsonic right now. Recorded in FINDINGS.md
as a **known bug, deliberately deferred** — deliberately NOT as "intended
behavior", because the analyzer's own wrap machinery (octave factors, j to
npo+1) exists to find these triads and only the post-loop NPO-map lookup
discards them. Calling it intended would make it harder to revisit.

**Risk-reducing reading done at decision time** (so a future fix is
cheaper): both UI consumers already handle unwrapped indices correctly,
because both convert degree → MIDI note and go through the 128-note tuning
table rather than indexing the npo array — keyboard
(WilsonicMidiKeyboardComponent+paint.cpp:176, already range-checked) and
pitch wheel (TuningRendererComponent.cpp:165, via microtoneAtNoteNumber →
getPitchValue01). So the eventual fix is contained to the filter and
touches no rendering. The 46 test_tuning checks now pin the buggy behavior
deliberately rather than incidentally.

**No code changed.** Plugin untouched.

## 2026-07-21 — LOOP-001: batch CPS search (entry before run)

**Context:** Marcus redirected to what the harness is for — offline/batch
search reporting winning tuning parameters.

**Search-space reasoning:** the diagonal theorem says min(P,S) ≡ P for
every MOS and every CPS(n, n/2), so a search over eikosanies alone cannot
exercise the balance criterion at all. This search therefore covers the
ASYMMETRIC families too — CPS(5,2)/(5,3) and CPS(6,2)/(6,4), where
CPS(n,k) inverts to CPS(n,n−k) rather than to itself and P ≠ S is
possible. That is where min(P,S) does work the raw P count does not, and
where plan §LOOP-003's "does any non-CPS-symmetric construction reach the
diagonal at comparable scores" becomes answerable.

**Two-phase inner loop** (plan §3.1, no LLM): phase 1 enumerates ALL seed
sets from odds ≤ 21 for all six families, so winners in the musically
interesting region are provably optimal there rather than whatever random
search happened to hit; phase 2 is time-boxed MAP-Elites (70% mutate an
elite, 30% random) over odds ≤ 399, which includes Marcus's calibration
set values. Archive bins: (family, cardinality, P/S balance bucket, prime
limit). RNG seed recorded; runs are exactly reproducible.

**Hypothesis:** (1) the classic Wilson seed sets top their own cardinality
bins; (2) the asymmetric families produce exact dual pairs — CPS(n,k) and
CPS(n,n−k) on the same seeds swap P and S exactly; (3) high-prime-limit
seed sets fill archive cells but do not beat the classics on min(P,S).

**Result:** pending — run below.

**Caught during smoke tests, before the real run:** the first report
ranked across cardinalities within a family, violating plan §1.3's
size-normalization rule. CPS(6,2) on 1-3-5-7-9-15 collapses to 13 tones
(product collisions) and appeared to "beat" the 15-tone classic. Rankings
are now per (family, cardinality).

## 2026-07-21 — DECISION 5 applied: CLAUDE.md tolerance correction (Marcus)

Approved and applied. All three mentions in the repo CLAUDE.md now state
that the analyzer's 0.0005 is an absolute difference in **linear
frequency**, not unit pitch space, with the consequence spelled out: the
same constant is ≈0.865¢ at f=1 but ≈0.433¢ near the octave, so the
analyzer is twice as strict at the top of the octave as the bottom. The
old text also called it a perceptual threshold comparable to 5–10¢ pitch
discrimination — corrected, since both figures are an order of magnitude
tighter; it is effectively an exactness test for JI coincidences. Points
at crossval001's tolerance_register_table, which measured it against the
real compiled analyzer. VERIFICATION.md gap 2 CLOSED. Docs only.

## 2026-07-21 — .scl artifacts must carry UI recreation params (Marcus)

**Requirement:** every .scl this harness emits must say, in comments, the
tuning design and parameters needed to rebuild it in the Wilsonic UI.

**Applied:** `families.cps.wilsonic_recreation_lines()` emits a RECREATE
IN WILSONIC block — design name ("Combination Product Sets"), the Scale
selector value (`4_2`, `5_3`, `6_3`, …, from CPSModel::__scaleNames,
CPSModel.cpp:16), every seed as its UI letter A–F, the APVTS parameter
string (CPSCALE/CPSA…CPSF, CPSModel.h:73-84), which letters are unused at
that scale selection, and the score + provenance. It also states BOTH
notations — canonical CPS(n,k) and Erv's reversed k)n — so no future
reader has to guess which convention a file used.

scala.to_scala/write_scl take a `provenance` argument; hex001,
hex003_eik001 and archive_scl all pass it. **All 37 .scl files on disk
regenerated and verified to carry the block (37/37).** Five goldens pin
the mapping against the plugin source so it cannot silently drift.

## 2026-07-21 — LOOP-001 result + three flaws found in the search itself

**Result vs hypothesis:** (1) CONFIRMED for the eikosany — 1-3-5-7-9-11 is
UNBEATEN at N=20 (min=77) across ~58k candidates. (2) CONFIRMED — every
asymmetric pair swaps exactly, e.g. CPS(5,2)/(5,3) on 1-3-5-7-9 give
(31,18)/(18,31). (3) FALSIFIED in part — several classics ARE beaten
within their own cardinality bin, always by more BALANCED sets rather
than higher-P ones, which is exactly what min(P,S) is built to reward:
- dekany 1-3-5-7-9 (min=18, (31,18)) beaten by 3-5-15-21-45 (min=20,
  (24,20)); an earlier run also found 5-7-15-35-45 at min=21 ((23,21)).
- pentadekany 1-3-5-7-9-11 (min=27, (70,27)) beaten by 3-5-7-21-63-315
  (min=33, (35,33) — nearly on the diagonal), 3-5-7-15-45-175 (min=29)
  and 5-9-15-19-21-45 (min=29).
- hexany 1-3-5-7 (min=8) beaten by 1-3-5-9 and 3-7-15-21 (min=9), which
  reproduces HEX-001 exactly — a good consistency check on the new code.
- Marcus's calibration eikosany: 75 archive cells beat its min=22.

Final consolidated archive: 3,417 cells over two independent random walks
(rng_seed 1 and 2) plus the exhaustive odds≤21 pass, ~95k candidates.

**Three flaws found in my own search before trusting its numbers:**
1. Rankings compared across cardinalities, violating plan §1.3 size
   normalization. CPS(6,2) on 1-3-5-7-9-15 collapses to 13 tones via
   product collisions and appeared to beat the 15-tone classic. Fixed:
   rankings are per (family, cardinality).
2. The archive was DUAL-INCOMPLETE: it declared the classic dekany
   UNBEATEN at CPS(5,2) while 5-7-15-35-45 scored min=21 there — that
   seed set had only ever been tried at k=3. Fixed: every candidate is
   evaluated together with its dual CPS(n,n−k).
3. Landmarks were being EVICTED from their MAP-Elites cells, so 4 of 8
   silently vanished from the comparison table — the very table the ear
   checks depend on. Fixed: landmarks tracked separately from the archive.
Plus: each run OVERWROTE the archive, losing prior discoveries (run 1's
min=21 dekany was erased by run 2). Fixed: the archive now accumulates
across runs per plan §3.1's append-only requirement, with carry-in
reported.

**Kept.** Runs: `python3.12 search.py --seconds 900 --rng-seed N`,
`python3.12 archive_scl.py`, `python3.12 search.py --report-only`.

## 2026-07-21 — EAR CHECK (HEX-002/EIK): metric validated, loss is not

**Marcus's verdict, decades of listening:** the proportional/subcontrary
lock-in is real and the CPS sets the loop surfaced are the intended
aesthetic. Detail in FINDINGS.md. The gate plan §HEX-002 set is PASSED
for the classifier and FAILED for min(P,S) as a ranking — he wants
P-heavy, S-heavy and G-heavy equally, which a balance loss penalizes.

**Kept, with the loss demoted.** No scorer change needed for this: P, S
and G were already recorded on every result and every archive record, so
the fix is entirely in the reporting layer (per-bucket winners x 5
lenses), exactly as the ε design intended.

## 2026-07-21 — DECISION: scorer v1.1.0, triads within an octave (Marcus)

**Deliberate unfreeze**, the first since the freeze, following the
process it was built for: proposed with measurements, approved
explicitly, applied, re-pinned, re-tagged.

**Change:** count only triads with outer ratio c/a ≤ 2/1 (rational) or
span ≤ 1200¢ (tempered). `max_span=None` reproduces v1.0.0 exactly, so
the old numbers stay reachable and auditable rather than being redefined
away. ScoreResult records `max_span`, so no record is ambiguous about
which regime produced it.

**Rejected in the same breath:** the plugin's 9/8..4/3 third band. It
does not commute with inversion — measured, the self-inverse eikosany
scores (20,29) under it — so adopting it would have destroyed the exact
duality that TRIAD-004 exists to protect.

**Goldens:** 11 failed on the bump, as they should. Each was re-derived,
not just re-pinned; the major-triad window case was re-checked by hand
from the triads listed in its own comment, and the two it drops are
exactly (1,2,3) and (1,3/2,3) — the first being Marcus's own example.
Suite 80 → 86/86, including a test that the v1.0.0 numbers are still
reachable via max_span=None.

**Also discovered by the bump:** the octave limit repairs the window
convention's P↔S duality failure on the segment counterexample
((36,6) → (6,36) exactly). G still fails to swap and the window is still
not transposition-invariant, so anchored remains primary — but the test
now records the improvement instead of asserting a stale failure.

**Re-pinned** scorer.sha256, tag scorer-v1.1.0. All v1.0.0 archives are
stale by construction and were regenerated.

## 2026-07-21 — Issues filed for the two plugin-side changes

- #12 analyzer tolerance is register-dependent (linear frequency, not
  cents) — the research scorer already compares in cents; this is the
  plugin only.
- #13 geometric triads: `_geometricTriads` is declared, has a getter, and
  is only ever `.clear()`ed — never computed. Enabling them in the UI is
  real work (both analyzer copies, a third dot colour, and the
  `numProportional + numSubcontrary == numAllTriads` assertion in
  WilsonicMidiKeyboardComponent+paint.cpp must go).
