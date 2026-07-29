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

## 2026-07-25 — G-006 blind ear check: 8/8 agreement with M3 propriety

**Protocol:** 8 sealed-key pairs (results/scl/g006/, seed 20260725), each one
non-improper vs one improper scale at matched cardinality; Marcus listened
blind in Wilsonic, same routine per scale; the key stayed sealed until all
eight verdicts were written down. Pre-registered bar: ≥6/8 = PASS territory.

**Result: 8/8.** Every pick matched the machine's propriety call — the six
hexany pairs AND both MOS pairs (5- and 13-tone). Marcus's picks with
confidence: p1 a (sure — "beautiful scale": the 1-3-5-7 hexany), p2 b (sure,
"hard no" on the improper partner), p3 b (sure), p4 a (lean), p5 a (lean),
p6 a, p7 b (sure — improper 571.6¢ MOS: "talk about a limp"), p8 b (clear).

**Qualitative notes worth more than the score (verbatim substance):**
1. On p4/p5 Marcus judged BOTH members melodically valid — the proper member
   wins on *even distribution* ("easier for musicians/composers to pick up"),
   while the improper member is "completely valid… spicy" melodically. His
   instruction: "remember these two because this is a great challenge to our
   melody scoring." → Propriety is predicting ACCESSIBILITY/evenness, not
   validity; improper-but-valid is a real region, and a future aggregate
   must not zero it out. Direct input to the melody+harmony aggregator
   design (PARETO-001 / balance work).
2. p7 is a clean perceptual confirmation of the LAT-MEL-001 trade-off
   finding: the harmonic hot-spot generator 571.6¢ MOS was heard as lame
   ("a limp") next to noble φ — harmony-optimal and melody-optimal
   generators genuinely diverge, by ear, not just by metric.

**Gate status:** evidence complete; decision is Marcus's alone (a session
never passes its own gate). 8/8 ≥ pre-registered PASS bar. On G-006 PASS,
melodic.py v0.1.0 freezes (hash-pin, scorer.py pattern).

## 2026-07-25 — Gate decisions: G-006 PASS, G-007 PASS-with-amendment (Marcus)

**G-006 PASS (Marcus, 2026-07-25, via chat):** melodic.py FROZEN at v0.1.0.
Basis: 8/8 blind ear check (entry above). Enforcement: melodic.sha256 pin
(a16f162b…7535) + experiments/lattice/check_freeze.sh (triads pattern,
check A). CI wiring of the check is a chore-lane follow-up. From here,
melodic.py is a frozen verifier: agent-loop commits must never modify it.

**G-007 PASS with amendment (Marcus, 2026-07-25, via chat):** accepted that
the eikosany is, in general, NOT a constant structure (LAT-MEL-001).
Marcus's amendment, verbatim in substance: there may exist seedings
{A,B,C,D,E,F} whose eikosany IS a constant structure — finding them would
be "a very exciting area of research", deserving of its own high-value
score, and CS-ness "might be more important than the triad scoring"
(argument: 12-ET has bad triads, is a constant structure, and is very
useful). Consequences queued: (1) a CS-eikosany existence search is a new
experiment candidate (working name CS-EIK-001) — note the LAT-MEL-001
mechanism gives a crisp machine formulation: exact-CS follows from
epimorphy (a val v with v(2)=20 mapping the 20 tones monotonically onto
degrees 0..19 with no ties — the {1,3,5,7,9,11} best val had 13 ties), so
the search space reduces to seed sets admitting a tie-free monotone val;
(2) CS weight relative to triad counts is a first-class question for the
melody+harmony aggregator design. Ledger reconciliation (G-006/G-007 rows)
deferred until PR #23 merges to avoid GATES.md conflicts.
## 2026-07-28 — MOS-LAT-001 pre-registration (entry BEFORE any run)

**Experiment (SPEC.md §MOS-LAT-001):** cut-and-project round trip for noble
generators, then the H-M1 descriptor test. Runner: `moslat001.py`; receipts:
`results/moslat001.json`. Frozen scorer v1.1.0 via `score_tempered`
(ε = 2.0¢ default, max_span 1200¢ default, both recorded per row).

**Construction (logged before implementation):** every generator here has CF
tail all 1s, so the tail recurrence is Fibonacci, M = [[1,1],[1,0]],
eigenvalues φ and −1/φ, and every generator lies in ℚ(√5). The preamble
digits act as the GL(2,ℤ) Möbius mask (SPEC §Search parameterization note);
conjugation by the preamble matrix preserves eigenvalues, so the SPEC's
suggested descriptor |λ|/|λ′| = φ² is CONSTANT across the whole all-1s-tail
corpus and carries zero information here. It is recorded once as a design
note, and the varying arithmetic invariant that replaces it is the conjugate
separation |g − g′| = 2√5/c (c = the denominator of g in lowest ℚ(√5) form).
Eigen-embedding used, exact in ℚ(√5) (integer triple (a, b, c) for
(a + b√5)/c; Galois conjugate = √5 → −√5): lattice point (octaves a,
generator-steps b) ↦ physical x = a + b·g (log-pitch, octaves), internal
ι = a + b·g′. Octave reduction x ∈ [0, 1) fixes a = −⌊b·g⌋, so admissible
points are parametrized by b with ι(b) = b·g′ − ⌊b·g⌋. Exact integer/isqrt
arithmetic end to end; floats only for receipts and for feeding
`families/mos.py` (which is the ground truth for the Brun zigzag and stays
untouched).

**Step-1 verification prediction (the registered claim):** for each of the
four nobles g1 = [0;1̄] = (−1+√5)/2 ≈ 0.618034 (741.64¢),
g2 = [0;2,1̄] = (3−√5)/2 ≈ 0.381966 (458.36¢),
g3 = [0;1,2,1̄] = (5+√5)/10 ≈ 0.723607 (868.33¢),
g4 = [0;2,2,1̄] = (7+√5)/22 ≈ 0.419821 (503.79¢),
and every Brun level 0–9 with zigzag fraction (p, q) from
`families/mos.py::zigzag` (semiconvergent path, Brun.cpp:269 — SPEC known
fact 4): the window-selected set {b : ι(b) ∈ W_L} equals {0,…,q−1} exactly,
and its projection {(b·g01·1200) mod 1200} matches `mos_cents(g01, q)` at
1e-6¢ elementwise. Two windows are checked per level: (a) the A-PRIORI
window derived from the level's zigzag fraction, W_L = the half-open
interval between 0 (closed) and ι(q) = q·g′ − ⌊q·g⌋ (open) — note
ι(q) = w_L or w_L + 1 with w_L = q·g′ − p depending on the sign of the
defect u_L = q·g − p, i.e. on the zigzag side; (b) the closed HULL window
[min, max] of ι over b ∈ {0,…,q−1}, scanned against all b ∈ [−(5q+100),
6q+100] (drift bound makes intruders outside that range impossible).
Refined prediction: for g1, g2 the internal coordinate is strictly monotone
in b (|step| = |(g′−g) + {g, g−1}| bounded away from 0 because |g′−g| =
√5 > 1), so all 10 levels verify — this is a theorem, the run confirms the
implementation. For g3, g4, |g′−g| = 2√5/10 ≈ 0.447 and 2√5/22 ≈ 0.203 are
< 1, ι is NOT monotone, and single-interval window representability is
genuinely at risk. Registered prediction: any failures are confined to
levels whose zigzag fraction is a SEMICONVERGENT (not a best-approximation
convergent) of g — the semiconvergent-vs-convergent subtlety the SPEC
anticipates. A failure is a documented finding (which levels, which
intruder/excluded b), not an error.

**H-M1 (registered test):** corpus = all CF digit strings with digits ≤ 3
and preamble length ≤ 3 before the all-1s tail, canonicalized by dropping
preambles ending in 1 (…,1,1̄ ≡ …,1̄ — identical value), = 27 distinct noble
generators, each exact in ℚ(√5). For each generator, every MOS cardinality
N ∈ [5, 22] reachable at Brun levels 0–9; per (g, N) row: frozen
score_tempered counts (P, S, G, score_min, raw fields, ε = 2¢) plus
pre-registered descriptors of the conjugate embedding:
  d1 conj_sep = |g − g′| (per generator);
  d2 window_width = |q·g′ − p| at the row's level (per row);
  d3 spread = max−min of ι(b) over b ∈ [0, N) (per row);
  d4 norm_spread = d3 / (N·d1) (per row, dimensionless).
Test: partial Spearman ρ(descriptor, P | N) — rank-transform, residualize
descriptor ranks and P ranks on N ranks by least squares, Pearson on
residuals. Null (SPEC: "no descriptor beats generator-value binning"):
baseline = identical machinery with predictor g01 (rank-based, so this
subsumes any monotone binning of generator value). Permutation test:
descriptor values shuffled WITHIN cardinality strata (preserves the
descriptor–N marginal), seed 20260725, 9999 permutations (≥999 per SPEC),
two-sided p = fraction of permuted |ρ| ≥ observed |ρ| (add-one rule).
Registered verdict rule: H-M1 is SUPPORTED iff some descriptor has
permutation p < 0.05 AND |ρ| > |ρ_baseline(g01)|; otherwise null — and a
null is a reportable finding. Known limitation, logged now: rows sharing a
generator are not independent (pseudo-replication); the stratified
permutation limits but does not eliminate this — interpret p-values as
descriptive, not confirmatory.

**Order:** implement moslat001.py + unit tests (Q5 arithmetic, generator
values, monotone-case window theorem, stats determinism) → run → receipts →
results entry below → FINDINGS.md promotion → full lattice + triads suites.

## 2026-07-28 — MOS-LAT-001 results

**Step 1 (verification table, receipt `results/moslat001.json` → step1):**
cents bit 10/10 levels for all four generators (projection == mos_cents at
≤ 1e-6¢). Window bits split exactly along the monotonicity line predicted:

- `[0;(1)*]` (1/φ, 741.64¢) and `[0;2,(1)*]` (458.36¢), |g−g′| = √5 > 1:
  **10/10 levels verified under BOTH windows** — the registered monotone
  theorem, confirmed by the implementation.
- `[0;1,2,(1)*]` (868.33¢), |g−g′| = √5/5 ≈ 0.447: hull window verifies at
  levels {0,1,2,4,6,8}, **fails at {3,5,7,9}** (fractions 3/4, 8/11, 21/29,
  55/76). `[0;2,2,(1)*]` (503.79¢), |g−g′| = √5/11 ≈ 0.203: hull verifies
  at {0,1,2,3,5,7,9}, **fails at {4,6,8}** (3/7, 8/19, 21/50).

**Registered semiconvergent prediction REFUTED.** Both semiconvergent
levels in the corpus (g3's 1/2 at L1, g4's 1/3 at L2, `is_cf_convergent =
false`) PASS the hull window; every hull failure is at a true CF
convergent. The exact failure law (from the receipts, exact arithmetic):
the hull window fails iff ι(q) — the internal coordinate of the NEXT chain
point b = q — lands strictly INSIDE the hull of {ι(0..q−1)}; in this
corpus that happens exactly at tail levels with defect u = q·g − p < 0
(zigzag fraction above g), where the chain's q-th step moves into the
window interior. Every failure has the SINGLE intruder b = q and zero
excluded points: the smallest window containing the level's scale admits
exactly one extra tone, frac(q·g). It is strictly interior (not on an
edge), so no half-open edge convention rescues it.

**The a-priori window "0-to-ι(q)" is the wrong closed form when ι is
non-monotone** (ap bit fails from L1/L2 on for g3/g4): the hull then
extends on both sides of 0 (for g3/g4 the conjugate is positive and small,
so ι(1) = g′ > 0 is the persistent upper hull edge while the drift is
negative). Hull extremes sit at parent-fraction indices (argmax at b = 1
resp. 2, argmin at q−1 resp. q−2 — Stern–Brocot parents), so a correct
closed form needs both parent vectors, not just the level vector. Not
pursued further here.

**Murchana rescue (investigation commissioned by the pre-registration):**
at EVERY hull-failing level, most contiguous chain segments [b0, b0+q) of
the same generator chain ARE window-representable — counts 5, 15, 41, 109
of the 2q+1 shifts tested, identical across g3 and g4 at corresponding
depths (structural, not generator-specific). So the cut-and-project
picture holds for these MOS as scales-up-to-transposition; what fails at
u < 0 convergent levels is specifically the murchana-0 (b = 0-anchored)
segment the plugin's Brun construction uses.

**Step 2 / H-M1 (receipt → step2):** 97 rows, 27 generators, cardinalities
5–22, frozen scorer v1.1.0, ε = 2¢, max_span 1200¢. P = S on all 97 rows
(inversional symmetry, consistent with triads/FINDINGS.md). Hot spots are
real (P ranges 0–62; top: preamble [3,1,3] ≈ 317.17¢ at N = 19 with
P = 62; the noble fifth [1,1,2] ≈ 696.21¢ and its octave complement [2,2]
≈ 503.79¢ tie at P = 51, complement symmetry as expected). **H-M1 verdict:
NULL.** Partial Spearman ρ(descriptor, P | N), stratified permutation
(seed 20260725, 9999 perms): g01 baseline ρ = −0.162 (p = 0.350);
conj_sep ρ = +0.027 (p = 0.773); window_width ρ = +0.015 (p = 0.874);
spread ρ = −0.046 (p = 0.598); norm_spread ρ = −0.025 (p = 0.788). No
descriptor beats generator-value binning; nothing is significant at all.
Honest caveat, logged in the pre-registration and confirmed: on an
all-1s-tail corpus the SPEC's spectral-gap descriptor is CONSTANT (φ²) and
the remaining descriptors are near-functions of (N, conj_sep) — the
corpus has too little conjugate-geometry variation to discriminate. The
natural follow-up is a mixed-tail corpus (metallic tails of 2s and 3s),
where the hidden lattice actually varies; reserved for a future run.

**Kept.** moslat001.py as implemented (one post-first-run addition, logged:
per-level investigation fields u_sign / iota_q_vs_hull / murchana_analysis
were added to `verify_level` after the first run exposed the failure
pattern — they change no verification bit, and the H-M1 statistics are
bit-identical across both runs, same seed). Findings promoted to
FINDINGS.md.

**Run receipt:** 2026-07-28, python3.12, runtime ~7 s — receipt
`results/moslat001.json` (scorer 1.1.0 recorded per row); lattice suite
43/43 OK (25 melodic + 18 moslat001); triads suite 88/88 OK; freeze check
A OK (pin 1a840af9…9b592 unchanged).
