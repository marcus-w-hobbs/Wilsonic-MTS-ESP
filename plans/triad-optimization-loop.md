# Plan: Agent-Driven Triad Optimization for Wilsonic-MTS-ESP

**Status:** Draft v0.1 — written off-repo; all items tagged `[VERIFY-REPO]` must be
checked against actual code before implementation.
**Objective:** Discover novel tunings that maximize proportional (arithmetic-mean)
and subcontrary (harmonic-mean) triads, using an agent-in-the-outer-loop
experiment harness (Karpathy autoresearch pattern) over Wilson's tuning families.

---

## 1. Mathematical Foundations

### 1.1 Scale representation

A tuning is a finite set of pitches. Two representations, both required:

- **Rational form** (JI families: CPS, harmonic/subharmonic segments,
  recurrence-relation scales): each degree is a positive rational `p/q`,
  octave-reduced to `[1, 2)`, deduplicated, sorted ascending. Use exact
  rational arithmetic (Python `fractions.Fraction`) — no floats anywhere in
  the JI path.
- **Real form** (MOS / tempered families): each degree is a real number in
  cents, reduced mod 1200, sorted. Comparisons use tolerance ε (see 1.4).

**Two-octave sample:** given octave-reduced scale `S`, the search domain for
triads is `T = S ∪ 2S` (rational form) or `T = S ∪ (S + 1200)` (cents form).
Rationale: proportional/subcontrary relationships routinely span the octave
boundary; a single octave systematically undercounts. This matches the
"reduce → sort → octave-repeat → two-octave sample" procedure Marcus specified.

`[SUPERSEDED 2026-07-21 — Marcus's call: the PRIMARY convention is
**middle-anchored**, not this two-octave window. The window as written here
fails §4 TRIAD-004 (segment 8..16 scores (46,8), its dual (7,42) not (8,46))
and is not transposition-invariant (hexany 1-3-5-7 = (10,9), ×3 = (11,11));
both counterexamples are frozen in tests/test_scorer.py. Anchored convention:
for each degree b (triad middle) in the canonical octave, the outer tones are
the unique octave-shifted representatives of scale pitch classes in the open
windows a ∈ (b/2, b) and c ∈ (b, 2b) — exactly self-dual for every scale and
exactly transposition-invariant. The window scorer is retained for comparison
(scorer.score_rational_window / score_cents_window); new work calls
scorer.score() / scorer.score_tempered(). Structural consequence recorded in
FINDINGS.md: all MOS and all CPS(n, n/2) sit exactly on P = S under anchored,
so min(P,S) ≡ P inside those families — a statement about the loss in §1.3,
not about the sampling convention.]`

### 1.2 Triad definitions (frequency space)

For pitches `a < b < c` drawn from `T`:

- **Proportional (arithmetic) triad:** `b` is the arithmetic mean →
  `2b = a + c`. Prototype: 4:5:6 (major triad).
- **Subcontrary (harmonic) triad:** `b` is the harmonic mean →
  `2/b = 1/a + 1/c`, i.e. `b = 2ac/(a+c)`. Prototype: 10:12:15 (minor triad).
  Equivalent: the *periods* (reciprocals) are in arithmetic progression —
  this is precisely the frequency/period duality already established in the
  RecurrenceRelation research (arithmetic in period space ↔ subcontrary in
  frequency space).
- **Geometric triad (bonus, off by default):** `b² = ac`. Feature-flagged;
  excluded from the primary loss in v1.

CRITICAL: all three definitions are relations on **frequency ratios**, not
cents. An arithmetic mean of frequencies is NOT a cents midpoint. The scorer
must never do triad math in log space; cents appear only in the ε-comparison
layer for tempered scales.

### 1.3 Counts and loss function

For a two-octave sample `T` of size `m`, iterate all `C(m, 3)` ordered triples
(brute force is fine: m ≤ ~50 → ≤ ~20k triples, microseconds).

Let `P` = count of proportional triads, `S` = count of subcontrary triads.

**Degeneracy guards (both are mandatory):**

1. **Size normalization.** Raw counts grow combinatorially with cardinality.
   All scoring and archiving is done **within fixed-cardinality bins**
   (e.g. N ∈ {5..22}). Never compare a 12-note scale's raw count to a
   19-note scale's.
2. **Balance requirement.** An unconstrained maximizer of `P + S` converges
   to a harmonic-series segment (all P, no S) or subharmonic segment (dual).
   Primary loss rewards *simultaneity*:

   ```
   score(S) = min(P, S)          # primary, v1
   score2(S) = P * S             # secondary, logged for comparison
   ```

   Also log the raw pair `(P, S)` for every candidate — the Pareto frontier
   in the (P, S) plane per cardinality bin is itself a research artifact,
   plausibly where new theorems live.

**Hypothesis to test (from the 2×2 SumType × SeedSpace matrix):**
frequency-space constructions should skew P-heavy, period-space duals
S-heavy, and CPS structures (combinatorially symmetric under inversion)
should sit near the P = S diagonal. The scorer makes this falsifiable.

### 1.4 Equality tolerance

- **Rational path:** exact equality of Fractions. Zero hyperparameters.
- **Tempered path:** `2b = a+c` is checked as
  `|1200·log2((a+c)/(2b))| < ε`, with frequencies reconstructed from cents
  (`f = 2^(cents/1200)`). ε is the **single honest hyperparameter** of the
  system. Default ε = 2.0 cents; every result records the ε it was scored
  under; sensitivity sweep ε ∈ {0.5, 1, 2, 5} is a required Phase 2 report.
- `[ADDED 2026-07-21 — Marcus's call: **ε-degeneracy guard**, tempered path
  only.` A triple contributes to no count (P, S, or G) unless its own
  arithmetic and harmonic means are distinguishable at ε, i.e.
  `|1200·log2(AM/HM)| ≥ ε` — below that threshold the two mean conditions
  are the same condition, so classifying the middle tone asserts nothing.
  Equivalent to a span cutoff: 58.8¢ (ε=0.5), 83.2¢ (ε=1), 117.7¢ (ε=2),
  186.1¢ (ε=5). Introduces NO new hyperparameter — it is derived from ε.
  No-op on the rational path (conditions already mutually exclusive).
  Motivation: unguarded, a 1¢ generator is the global optimum of min(P,S)
  at every cardinality N=5–10 at every ε; §3.2's reward-hacking firewall is
  worthless if the metric itself is hackable. Unguarded counts are still
  recorded (`*_raw`, `degenerate_dropped`). Rejected alternatives and their
  measured failures: FINDINGS.md ε-degeneracy entry.`]`

---

## 2. Tuning Family Generators (candidate space)

Each family is a parameterized generator function → octave-reduced scale.
These mirror structures already implemented in Wilsonic-MTS-ESP
`[VERIFIED 2026-07-20: C++ is ground truth for scale generation, but note the
plugin's CPS path is float arithmetic end-to-end and never uniquifies — see
§5 items 1, 3. "Same inputs → same scales" means agreement within float
tolerance against the plugin's canonical form, not exact rational equality.]`.

### 2.1 CPS (combination product sets)

- Parameters: seed multiset `A = {a₁..aₙ}` (positive integers, typically odd),
  choose-k. Scale = octave-reduced products of all k-subsets: `C(n, k)` tones.
- Hexany: n=4, k=2 → 6 tones. Eikosany: n=6, k=3 → 20 tones.
- **Dual (period-space) CPS:** same construction on reciprocals of seeds,
  then invert products back to frequency. Required for the 2×2 matrix test.
- Seed space for exhaustive phases: odds in `[1, 15]` (hexany),
  curated pools for eikosany (includes Marcus's {1,45,135,225,19,377} as a
  named calibration point).

### 2.2 MOS (moments of symmetry)

- Parameters: generator `g` (cents, or fraction of period), period (1200 by
  default), and level = number of stacked generators before closure.
- Construction: stack `g` mod period, k times; a MOS exists at cardinalities
  given by the **Brun/scale-tree zigzag** of `g/period` — NOT the classical
  continued-fraction convergents alone; the zigzag includes semiconvergent
  steps. `[VERIFIED-REPO 2026-07-20: Brun::brun(level, g) at Brun.cpp:269–299
  runs the zigzag `level` times; cardinality at level L = denominator of the
  L-th zigzag fraction. Levels 0..9 (Brun.h:43–44,
  absoluteMinLevel/absoluteMaxLevel). For g = log2(3/2) the level→cardinality
  map is 1, 2, 3, 5, 7, 12, 17, 29, 41, 53 (levels 0–9) — note 2/3, 4/7,
  10/17, 17/29 appear, which are zigzag/semiconvergent steps, not CF
  convergents of 0.585. Scale degrees are built in LOG space:
  p = degree·g01 mod 1 (Brun.cpp:308–357, _microtoneArrayBrun), with degrees
  centered on murchana (auto default = numScaleDegrees/2, Brun.cpp:322–326).
  g01 ∈ [0,1] is the generator as a fraction of the period, float. The Python
  mos.py generator must mirror the zigzag recurrence exactly (num = 2·Y1+Y2,
  den = 2·X1+X2 with swap when mosB > mosA).]`
- Sampling: generator swept over `(0, 600]` cents (symmetry makes the upper
  half redundant) at 0.1-cent resolution for grid phases; continuous for
  optimizer phases. Noble-number and simple-ratio generators flagged as
  landmarks in reports.

### 2.3 Recurrence relations (Phase 3+)

- Parameters: recurrence coefficients + seeds, in frequency space or period
  space, arithmetic or harmonic SumType — the full 2×2 matrix from the
  planned RecurrenceRelation extension. This plan's scorer is the evaluation
  half of that work; the generator half lands when the C++ extension does.
  `[VERIFY-REPO: RecurrenceRelation class interface before specifying the
  Python mirror.]`

### 2.4 Harmonic/subharmonic segments (control group)

- `h:h+1:...:2h` and its subharmonic dual. Not interesting as discoveries —
  they are the known degenerate optima of P alone and S alone — but mandatory
  as calibration anchors and as the corners of the (P, S) plane.

---

## 3. Architecture: Two Loops

### 3.1 Inner loop — deterministic search (no LLM)

Plain computation. For a fixed family and parameter region: enumerate or
mutate parameters → generate scale → score → append to archive. The agent
never proposes individual parameter values; tokens are wasted there.

**Archive: MAP-Elites** (quality-diversity, not single-optimum search).
- Bin descriptors: (family, cardinality, P/S ratio bucket, and for MOS the
  generator region / for CPS the max-prime-limit of seeds).
- Cell contents: best-scoring candidate per bin + full (P, S, params) record.
- Storage: single SQLite file or JSONL, append-only, committed to repo.
  The archive IS the museum of discovered tunings.

### 3.2 Outer loop — agent (Karpathy autoresearch pattern)

The agent (Claude Code session) operates on the *experiment code and
strategy*, not on parameters:

1. Read archive + last run's report.
2. Propose ONE change: new mutation operator, new parameter region, new
   family variant, new descriptor binning, new hypothesis to test.
3. Implement it, run the inner loop (time-boxed), regenerate report.
4. Keep the change iff archive-level metrics improved (new cells filled,
   or cell bests raised); otherwise revert. Git commit per kept change,
   conventional-commit message stating the hypothesis and outcome.
5. Append a 3-line entry to `experiments/LOG.md`: hypothesis → result → kept/reverted.

**Reward-hacking firewall (non-negotiable):**
- `scorer.py` is the frozen verifier. The agent has read access, no write
  access (enforce via CI check: any diff touching `scorer.py` in an
  agent-loop commit fails the run).
- Scorer changes happen only in human-reviewed commits, and every scorer
  version is tagged; archive records the scorer version that produced each
  entry.

### 3.3 Repo layout (new, additive — touches no existing plugin code)

```
experiments/
  triads/
    scorer.py            # frozen verifier: scale -> (P, S, G, score)
    families/
      cps.py             # hexany/eikosany/dekany + period-space duals
      mos.py             # generator stacking + convergent cardinalities
      segments.py        # harmonic/subharmonic controls
    search.py            # inner loop: enumerate/mutate + MAP-Elites archive
    archive.sqlite       # the museum (or archive.jsonl)
    report.py            # Pareto plots, bin coverage, landmark tables
    LOG.md               # agent experiment log
    tests/
      test_scorer.py     # golden cases, see Phase 0
```

Python 3.12, stdlib + numpy + matplotlib only. No JUCE build required to run
experiments — the C++ plugin is consulted only for cross-validation of scale
generation `[VERIFY-REPO]`.

---

## 4. Phases

### Phase 0 — Frozen scorer + golden tests (½ day)
Requirements:
- **TRIAD-001:** scorer computes (P, S, G) on exact rationals for a two-octave
  sample per §1.1–1.2.
- **TRIAD-002:** golden tests: 4:5:6 → proportional; 10:12:15 → subcontrary;
  1/1–5/4–3/2 recognized as proportional (equals 4:5:6); harmonic segment
  8..16 → P = C(9,3)-adjusted expected count, S small; subharmonic dual
  mirrors it with P and S swapped (duality test — this MUST pass exactly).
- **TRIAD-003:** tempered path with ε; golden test: 12-EDO major triad
  detected as proportional at ε = 15 cents, not at ε = 14 or ε = 2. [CORRECTED
  2026-07-20: the exact deviation is −14.859¢, so the original ε = 14 claim
  was wrong by 0.9¢. Documents that 12-EDO thirds are *not* proportional at
  musical precision — itself a nice calibration fact.]
- **TRIAD-004:** duality invariant test: scoring the inverted scale
  (reciprocals, re-reduced) swaps P and S exactly (rational path).
  This is the strongest single correctness check available.
  [REFINED 2026-07-20 after empirical falsification: under the §1.1
  two-octave-window sample, the pipeline swap is exact ONLY for scales not
  containing 1/1 — when 1/1 is a degree, the inverted sample is the
  reflection 4/T with boundary element 4 replaced by 1, and counts differ
  (segment 8..16: (P,S) = (46,8) but dual scores (7,42)). The underlying
  AM↔HM theorem is exact for every scale: classifying the reflected
  multiset 4/T always swaps exactly (verified). A middle-anchored
  convention (each triad's middle drawn from the canonical octave, outer
  tones the unique pitch-class representatives in (b/2, b) and (b, 2b)) is
  BOTH exactly self-dual for all scales AND exactly
  transposition-invariant (the window convention is neither: hexany
  transposed by 3 scores (11,11) vs (10,9)). Both conventions are
  implemented in scorer.py; the primary-convention decision is Marcus's,
  pre-freeze. Note: odd-seeded CPS scales never contain 1/1 (odd products
  are never powers of two), so the window convention's duality is exact on
  the entire Phase 1 domain either way. Under the anchored convention the
  1-3-5-7 hexany scores exactly (P,S) = (8,8) — on the P = S diagonal,
  consistent with the §1.3 CPS symmetry hypothesis.]

### Phase 1 — Exhaustive hexany calibration (½ day)
**[STATUS 2026-07-21: HEX-001 done; HEX-003 done (exact swap, 0 failures);
HEX-002 ear check awaiting Marcus — top .scl files in
experiments/triads/results/scl/. Bonus: EIK-001 eikosany calibration done;
all CPS(6,3) sit exactly on P=S; calibration set ranks 29/29 by min(P,S).]**
- **HEX-001:** enumerate all C(8,4) = 70 seed sets from odds {1,3,...,15};
  score all; rank by min(P,S) and by P·S within the 6-note bin.
- **HEX-002:** report where 1-3-5-7 ranks. Ear-check against Marcus's
  aesthetic ordering — if the metric ranks hexanies in an order that feels
  wrong, the loss function gets revised BEFORE any agent loop runs. This is
  the felt-sense ↔ loss-function alignment step (Ultimate Research Paper
  prerequisite).
- **HEX-003:** score period-space duals of all 70; verify the P↔S swap
  prediction empirically.

### Phase 2 — MOS generator sweep (1 day)
**[STATUS 2026-07-21: MOS-001 done (0.1¢ fine sweep, 30k records);
MOS-002 done (ε ∈ {0.5,1,2,5} recorded per point; sensitivity table in
results/). MOS-003 partial: landmark table in sweep reports; hot
generators found at ~571.6¢ (odd N), 498¢ (N=12, the pure fourth), 416¢
(N=20). Open scorer-spec issue: ε-degeneracy of near-equal-step scales —
see FINDINGS.md; treatment decision is Marcus's before scorer freeze.
Note: all MOS and all CPS(n, n/2) sit exactly on P=S under anchored
scoring (structural inversion symmetry) — min(P,S) only differentiates
asymmetric families; see FINDINGS.md diagonal-theorem entry.]**
- **MOS-001:** grid sweep g ∈ (0, 600] at 0.1¢, cardinalities from
  convergents up to N = 22, score at ε = 2¢; plot score vs generator per
  cardinality bin.
- **MOS-002:** ε sensitivity sweep per §1.4.
- **MOS-003:** landmark table: where do 3/2-ish generators (meantone region,
  ~696–702¢... note: reduced to ≤600 as complement), noble generators, and
  known Wilson MOS land on the score curves?

### Phase 3 — Agent loop on open space (ongoing)
- **LOOP-001:** MAP-Elites archive + mutation search over eikosany seed
  space (intractable exhaustively: seed pools beyond small odd sets) and
  continuous MOS generators.
- **LOOP-002:** agent outer loop per §3.2, time-boxed sessions, LOG.md
  discipline.
- **LOOP-003:** first research question for the agent: characterize the
  Pareto frontier of (P, S) per cardinality — do CPS structures dominate it,
  and does any non-CPS construction reach the P = S diagonal at comparable
  scores? A "yes, non-CPS" finding is a genuinely novel result.

### Phase 4 — RecurrenceRelation integration (when C++ extension lands)
- **RR-001:** Python mirror of the 2×2 SumType × SeedSpace generator;
  archive descriptors gain the matrix quadrant; test the quadrant→(P,S)-skew
  hypothesis from §1.3 at scale.

---

## 5. Assumptions to verify against the repo before Phase 0

**Verification pass completed 2026-07-20 (branch claude/triad-optimization-harness-044fe1).**

1. `[VERIFIED]` **Octave reduction is half-open `[1, period)`.**
   Microtone::octaveReduce(period) (Microtone.cpp:475–556): Linear space
   reduces via repeated multiply/divide by period, then asserts
   `>= 1.f && < _period` (lines 514–515 rational, 544–545 float). The
   rational path uses exact Fraction mult/div, but loop *conditions* compare
   `.floatValue()` — float boundary comparisons on a rational value.
   LogPeriod space reduces to `[0, 1)`. **Dedup:**
   MicrotoneArray::uniquify() (MicrotoneArray.cpp:434–455) keys a
   `map<float, Microtone_p>` on exact float frequency — no epsilon; ties
   (bit-identical floats) resolved by reverse iteration + map::insert, so the
   LAST element in array order wins. **CRITICAL CAVEAT: CPS tunings never
   uniquify** — CPSTuningBase constructor calls `setCanUniquify(false)`
   (CPSTuningBase.cpp:18) and TuningImp defaults `_uniquify = false`
   (TuningImp.h:192). The plugin's hexany is ALWAYS 6 entries, duplicates
   kept, even when octave-reduced products collide. The processing pipeline
   is octaveReduce → sort → uniquify (TuningImp::_update, TuningImp.cpp:507–518);
   sort is ascending by float frequency (MicrotoneArray.cpp:388–405),
   std::sort (unstable).
2. `[VERIFIED]` **Brun level→cardinality is the scale-tree zigzag, levels
   0–9.** See corrected §2.2. Cardinality(level L) = denominator of the L-th
   zigzag fraction from Brun::brun (Brun.cpp:269–299); for the fifth:
   1,2,3,5,7,12,17,29,41,53.
3. `[VERIFIED]` **No CPS normalization of any kind.**
   CPSTuningBase::multiplyByCommonTones (CPSTuningBase.cpp:94–125) computes
   a plain float product of seed frequency values — no division by a
   reference product, no 1/1 re-anchoring. Products are then octave-reduced
   to [1,2) by _update. Canonical plugin form for archives: **octave-reduced
   raw k-products, sorted ascending by frequency, duplicates kept, no 1/1
   inserted** (hexany 1-3-5-7 = {35/32, 5/4, 21/16, 3/2, 7/4, 15/8}; degree 0
   = lowest tone, mapped to middle C). **Also: plugin CPS seeds are FLOATS**
   — APVTS float params via CPS::A(float) (CPS.cpp:85–91, CPSModel.cpp:55,
   218–220), so the entire plugin CPS path is float arithmetic. The Python
   exact-rational path is an idealization; C++ cross-validation must compare
   within float tolerance (~1e-6 relative), never exact equality.
4. `[VERIFY-REPO]` RecurrenceRelation interface (Phase 4 only — not checked
   in the 2026-07-20 pass).
5. Whether MTS-ESP export from archive entries is worth a small
   `to_scala()/to_mts()` writer in Phase 1 so top discoveries are
   immediately playable. (Recommended: yes — the ear-check in HEX-002
   requires it anyway.)

### 5.1 Bonus finding: the C++ triad analyzer is NOT the plan's scorer

TuningImp::_analyzeProportionalTriads (TuningImp.cpp:782–857) differs from
§1.1–1.4 in three load-bearing ways; do not expect raw counts to match:

- **Tolerance is absolute linear frequency**, not pitch/cents:
  `fabsf(mean − kmf) < 0.0005` on octave-reduced frequencies in [1,2)
  (TuningImp.cpp:809, 833, 845). (Repo CLAUDE.md says "unit pitch space" —
  that is incorrect per the code.)
- **Musical interval filter:** the mean must satisfy
  9/8 < mean/root < 4/3 (TuningImp.cpp:822–825) — only compact,
  triad-shaped sonorities are counted.
- **Domain is one octave + one wrapped degree**, not a two-octave sample:
  root i ∈ [0, npo), fifth j ∈ [i+2, npo+2) with j % npo and a single
  octave factor (TuningImp.cpp:812–819). Triads are deduped by unordered
  degree-index set {i, k%npo, j%npo} (TuningImp.cpp:835, 847).

The plan's scorer (all C(m,3) triples over a two-octave sample, no interval
filter, exact rationals) is a strict superset by design. C++ ground truth
applies to **scale generation** cross-validation only; any triad-count
cross-check must first replicate the three filters above.

## 6. Explicitly out of scope (v1)

- Geometric triads in the primary loss (logged only).
- Tetrads and larger sonorities (natural v2: proportional tetrads ↔ Wilson's
  "flanked" structures — but not now).
- Any modification to the shipping plugin. Everything lives in `experiments/`.
- Timbre/roughness models. The loss is purely structural counting; the
  felt-sense alignment happens through HEX-002 listening, not through a
  psychoacoustic model bolted on prematurely.
