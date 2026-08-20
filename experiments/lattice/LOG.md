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

## 2026-07-28 — SHADOW-001 pre-registration (entry written BEFORE any run)

**Experiment:** comma perturbation of CPS factors, SPEC.md §SHADOW-001.
Implementation `experiments/lattice/shadow001.py`; receipts to
`experiments/lattice/results/shadow001.jsonl` (one row per variant) plus a
verdict summary `results/shadow001_verdicts.json`.

**Sweep definition (fixed before run):** bases hexany = CPS(4,2) of
(1,3,5,7) and eikosany = CPS(6,3) of (1,3,5,7,9,11). For each factor
position, for k ∈ 3..16, for sign ∈ {+, −}: replace factor n with
m = 2^k·n ± 1, one perturbed factor at a time; skip a variant iff m
collides with another factor of the set. Predicted skips: hexany
(n=1, k=3, −) → m=7; eikosany (n=1, k=3, ±) → m ∈ {9, 7}. Expected rows:
4·14·2 − 1 = 111 hexany + 6·14·2 − 2 = 166 eikosany variants + 2
unperturbed baselines = 279.

**Epsilons (all logged per row):** frozen scorer v1.1.0 on BOTH paths —
`score()` exact-rational (control) and `score_tempered(cents,
epsilon_cents=2.0)` (H-S1's recovery prediction lives here); both at the
frozen default max_span (triads within an octave). Tone survival:
`canonical_cents_scale` dedup at ε_dedup ∈ {0.01, 0.1, 0.5, 2}¢ on the
exact-canonical scale's cents. Comma spectrum: all pairwise circular
intervals < 20¢. Melodic M1–M3 via `melodic.score_melodic_rational`
defaults (dedup 0.01¢, gap 0.5¢, CS 0.5¢, propriety 1e-9¢), melodic
v0.1.0. Displacement recorded exactly as
1200·|log2((2^k·n ± 1)/(2^k·n))| ≈ 1731.234/(2^k·n) cents.

**H-S1 (quoted from SPEC):** "exact-coincidence triads DROP relative to
the unperturbed CPS for small k (the comma breaks alignment with the
1-products), and recover discontinuously when the displacement falls
inside scorer ε (predicted threshold between k=8 and k=12 for n=1)."
Numeric pre-registration: (a) exact path is the control — for every
variant, exact score_min < the base's exact score_min at k = 3..7, and NO
recovery at k = 16 (exact coincidences, once broken, stay broken; any
exact recovery would have to come from new shared-factor coincidences,
H-S3's territory, not from k growing). Hexany base exact predicted (8,8)
per SPEC §BRIDGE-001; eikosany base measured at run time. (b) tempered
path at ε = 2¢: recovery k* := min k with variant tempered score_min ≥
base tempered score_min satisfies displacement(k*) < 2¢, i.e. predicted
k* per perturbed factor n: n=1 → 10 (disp 1.691¢; k=9 is 3.380¢),
n=3 → 9 (1.127¢), n=5 → 8 (1.353¢), n=7 → 7 (1.932¢), n=9 → 7 (1.503¢),
n=11 → 7 (1.230¢). The n=1 prediction (k*=10) sits inside SPEC's
"between k=8 and k=12".

**H-S2 (quoted from SPEC):** "there is a sharp k* where dedup behavior
snaps (tone count changes); k* shifts by exactly 1 per doubling of
ε_dedup." Numeric pre-registration: IF the collapse mechanism exists
(i.e. some surviving tone sits at the perturbed tone's unperturbed pitch
class, distance ≈ displacement), then k*(n, ε) = min k with
1731.234/(2^k·n) < ε: for n=1 that is k* = 10 (ε=2¢), 12 (0.5¢),
15 (0.1¢), 18 (0.01¢ — outside the sweep, prediction: no collapse seen);
ε 0.5→2¢ is two doublings ⇒ shift of exactly 2. Pre-registered mechanism
caveat (falsifiable the other way): hand analysis finds NO zero-distance
mixed pair in either base (the 20 eikosany products are 20 distinct odd
numbers; no 2-subproduct is octave-equivalent to a surviving 3-product),
so the strict mechanism may be absent ⇒ alternative outcome is tone
count CONSTANT in k at every ε ≤ 2¢ (H-S2 refuted on these bases), with
possible non-monotone collapse windows where a displaced tone transits a
close neighbor (e.g. 385/384-type pairs, 4.503¢). Either outcome is a
finding; the comma-spectrum receipts adjudicate.

**H-S3 (quoted from SPEC):** "composite perturbations that share factors
with the base set (e.g. 255 sharing 3, 5) yield higher triad counts than
prime perturbations of comparable size (e.g. 257) — 'connectivity beats
pure novelty.'" Numeric pre-registration: matched pairs = same (base,
position, k), sign + vs −, where exactly one of the two m is a
sharing composite (gcd of its odd part with the remaining factors'
primes > 1) and the other is prime. Test on the exact path (the only
path where "coincidence" is exact): sharing side wins (exact P strictly
greater) in ≥ 2/3 of matched pairs. Report win/tie/loss counts and the
same tally for tempered score_min at ε=2 as a secondary lens.

**Auxiliary structural check (pre-registered):** P = S exactly for EVERY
variant on both paths' guarded counts — CPS(n, n/2) inversional symmetry
is seed-value-independent, and the anchored scorer commutes with
inversion (triads/FINDINGS.md). Any P ≠ S row is a bug in the harness,
not a finding.

**Determinism:** stdlib only, fixed constants above, no randomness;
timestamps and git commit recorded as provenance only.

## 2026-07-28 — SHADOW-001 results + verdicts

**Receipts:** `results/shadow001.jsonl` (279 rows: 2 baselines + 111
hexany + 166 eikosany variants, exactly as pre-registered, including the
three predicted collision skips) and `results/shadow001_verdicts.json`.
Scorer v1.1.0 both paths, melodic v0.1.0, all epsilons as pre-registered.
Two identical runs (deterministic); ~6 s wall clock.

**Baselines (measured):** hexany exact (6,6) / tempered ε=2 (6,6);
eikosany exact (57,57) / tempered (61,61). The SPEC §BRIDGE-001 "(8,8)"
for the hexany is the v1.0.0 no-span number (verified:
`score(s, max_span=None)` = (8,8)); under v1.1.0's within-octave rule two
octahedron-face triads exceed the span, giving (6,6) — consistent with
the anchored block of `triads/results/hex001.jsonl`. Neither base has any
pairwise interval below 20¢ (both comma spectra empty).

**H-S1 — CONFIRMED (both clauses), one pre-registered exception class.**
Exact control: 38/39 hexany and 58/58 eikosany small-k (3..7) variants
drop strictly below base; ZERO exact recoveries at k=16. The single
non-drop is the sharing jackpot m=15=3·5 (n=1, k=4, −), which restores
exact (6,6) at 111.7¢ displacement — H-S3's mechanism, exactly the
carve-out pre-registered. Exact counts settle to k-independent floors:
hexany 1/0/3/4 for perturbed n=1/3/5/7 (perturbing 3 kills EVERY exact
triad of the hexany; see finding below), eikosany 22/18/27/32/25/41 for
n=1/3/5/7/9/11. Tempered path: sustained recovery k*_sust (post-hoc lens
added after first inspection, labeled in shadow001.py — the
pre-registered first-crossing detector is jackpot-contaminated) matches
the pre-registered k* in 16/20 configs and sits inside scorer ε in
19/20; n=1 recovers at exactly k=10 on both bases and both signs, inside
SPEC's "between k=8 and k=12". The four deviations are ±1-count jitter
around base (60 vs 61) at sub-cent displacements plus ONE outside-ε
early crossing: eikosany n=11 +, k=6, m=705=3·5·47 (sharing), disp
2.457¢. Verdict: kept.

**H-S1 surprise — tempered OVERSHOOT.** 52 eikosany variants score
ABOVE base tempered (up to 69 and 67 vs 61; e.g. n=7 −, k=7, disp
1.93¢), concentrated where displacement is ~0.2–2¢, decaying to exactly
base by k≈12–14. Shadow tones just inside ε satisfy near-coincidences
the unperturbed tone cannot — perturbation at the ε boundary is
temporarily WORTH TEMPERED TRIADS. The hexany never overshoots (0/111).

**H-S2 — REFUTED as pre-registered; the pre-registered mechanism caveat
is what happened.** ε_dedup was inert across the ENTIRE sweep: in all
279 rows the deduped tone count equals the exact tone count at every
ε ∈ {0.01, 0.1, 0.5, 2}¢ — no near-merge anywhere, hence no k*, hence
no shift-per-doubling. Root cause exactly as cautioned: no mixed pair
sits near zero distance, and the smallest comma produced anywhere in the
sweep is 2.912¢ (595/594, eikosany n=1 k=4 +) > the largest ε_dedup 2¢.
Tone counts DO change — but only by EXACT rational collision,
ε-independent and confined to small k on the eikosany: m=15 → 18 tones
({15,3,7}={5,7,9}=315, {15,3,11}={5,9,11}=495), m=33 → 18
({33,3,5}=495, {33,3,7}={7,9,11}=693), m=55 (n=7, k=3, −) → 18
({55,1,3}={3,5,11}=165, {55,1,9}={5,9,11}=495). Dedup "snapping" on
these bases is lattice arithmetic, not epsilon geometry. Verdict:
reverted (hypothesis falsified; finding promoted).

**H-S3 — CONFIRMED, unanimous direction.** 57 matched ±pairs (25 hexany,
32 eikosany) with one sharing-composite and one prime side. Exact path:
sharing wins 11, ties 46, prime wins 0 — the sharing side NEVER loses
(one-sided sign test vs even odds: p = 2⁻¹¹ ≈ 0.0005). Hexany:
15 vs 17 at k=4 gives exact P 6 vs 2. Eikosany wins cluster at small k
(m small ⇒ heavy factor overlap); at large k both sides hit the same
surviving-triad floor (ties). Jewel: the matched pair (n=3, k=7) is
385 = 5·7·11 vs prime 383 — replacing 3 with 385/128 is literally a
385/384 shift (4.503¢), one of BRIDGE-000's three D'Alessandro kernel
commas — and it wins exact P 24 vs 18. The tempered lens at ε=2 does NOT
track connectivity (13W/1T/18L, noise from the overshoot effect above);
"connectivity beats pure novelty" is an EXACT-path statement. Verdict:
kept.

**Auxiliary check:** P = S in all 279 rows on both paths (guarded
counts) — CPS(n, n/2) inversional symmetry survives arbitrary factor
replacement, as pre-registered.

**Exploratory (H-L3 preview, not pre-registered):** eikosany n=3 +
sweep: M2 CS violations go base 32 → 18 in the 1–5¢ displacement region
(BETTER than base) → back to 31–32 once displacement < ε_CS = 0.5¢
(k ≥ 12). The restoration threshold tracks ε_CS as H-L4/H-L3 predict,
and the mid-k IMPROVEMENT (a comma-sized perturbation melodically
cleans up the eikosany) is unexpected — queued as a LAT-MEL-001/H-L3
follow-up, not claimed as a finding yet (single-config observation).

**Run receipt:** 2026-07-28, python3.12 — lattice suite 37/37 OK
(25 melodic + 12 new shadow001 helper tests), triads suite 88/88 OK,
scorer freeze check A OK (pin 1a840af9…9b592 unchanged).
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

## 2026-07-28 — CS-EIK-001 pre-registration (entry BEFORE any run)

**Origin:** Marcus's G-007 amendment (2026-07-28, via chat): the eikosany is
generically not CS, but "there might be seeding of A,B,C,D,E,F such that the
resulting eikosany could be a constant structure… a very exciting area of
research… might be more important than the triad scoring (consider 12et: bad
triads, constant structure, very useful)."

**Datestamp erratum, recorded here once:** LOG/FINDINGS/GATES entries this
session dated 2026-07-25 (melodic.py v0.1.0 through the G-006/G-007 gate
decisions) were written on **2026-07-28** — the assistant datestamped them
wrong; the content and ordering are unaffected. Entries from SHADOW-001
onward carry correct dates.

**Design decisions (Marcus said "proceed"; defaults chosen and logged, his
to overrule at review):**
- Seed domain: 6 DISTINCT odd positive integers (octave-coprime convention),
  composites explicitly welcome. Exhaustive sweep odds ≤ 31 (C(16,6) = 8008
  seedings); pre-registered escalation: if zero CS found, extend exhaustively
  to odds ≤ 45 (C(23,6) = 100 947).
- A candidate counts as an eikosany only if its CPS(6,3) has 20 EXACTLY
  distinct tones after octave reduction; seedings with exact collisions
  (18-tone images etc.) are logged separately (tempered-merge regime), not
  eligible for the headline verdict.
- Criterion: EXACT constant structure (fractions.Fraction interval → span
  map; a size class at ≥2 spans is a violation; zero floats). For CS winners,
  a graded **CS margin**: the minimum cents distance between any two interval
  sizes occurring at different spans — the ε up to which the scale stays CS
  under the melodic scorer (12-ET's margin is ∞ in-family; bigger = more
  robustly CS). Full panel for winners and near-misses (≤ 2 violating
  classes): frozen harmonic (P,S,G) v1.1.0 exact path, frozen melodic v0.1.0
  M1–M3, best-val tau/ties, and an exact epimorphy check (solve v·mᵢ = i over
  ℚ for the pitch-ordered tones with v(2) = 20; epimorphic iff consistent and
  integral).

**Pre-registered predictions:**
- P1 (Marcus's conjecture): at least one CS eikosany exists at odds ≤ 31.
- P2 (connectivity thesis, extending H-S3): every CS winner's seed set
  contains composite seeds sharing prime factors with other seeds; no
  all-prime seeding ({1} ∪ 5 distinct odd primes) is CS.
- P3 (mechanism): CS winners are exactly the epimorphic seedings — CS and
  tie-free-val epimorphy coincide on this family. A CS-but-not-epimorphic
  winner would be a notable finding either way.

**Deliverable:** results/cseik001.jsonl (one row per seeding: seeds,
distinct-tone count, violations, margin if CS; full panel where computed) +
verdicts in the results entry. Runner: cseik001.py, stdlib, deterministic.

## 2026-07-28 — CS-EIK-001 results + verdicts

**Run:** cseik001.py, exhaustive odds ≤ 31 (8008 seedings, ~10 s): 7488 true
20-tone eikosanies, 520 degenerate (exact product collisions, logged, out of
scope). Receipts: results/cseik001.jsonl. Escalation clause unused.

**P1 — KEPT. Marcus's conjecture confirmed: 32 CS eikosanies exist**
(0.43% of true eikosanies). 20 of the 32 remain CS at the frozen melodic
scorer's 0.5¢ default (margin > 0.5¢); best margin 9.22¢
({13,17,21,23,25,27}). Cross-checked: exact-CS + margin agrees with frozen
melodic constant_structure at 0.5¢ on all 32.

**P2 — SPLIT, refined.** All-prime seedings are never CS (0 winners — kept),
and **every winner contains at least one composite seed** (kept). But the
factor-sharing half is REFUTED: 8/32 winners' composites share no prime with
any other seed. Refined thesis: composites are NECESSARY for CS,
factor-sharing is not.

**P3 — REFUTED, and the refutation is the discovery.** Only 4/32 winners are
epimorphic ({1,5,7,13,15,31}, {1,15,19,27,29,31}, {3,7,13,15,19,29},
{7,15,19,25,29,31}). The other 28 are **constant structures with NO
consistent val** (the linear system v·mᵢ = i is inconsistent or non-integer)
— CS strictly exceeds epimorphy on this family. Epimorphy ⇒ CS stands as
theorem; the converse fails 28 times in one sweep.

**Flagship: {1, 7, 9, 11, 15, 29}** — the only STRICTLY PROPER winner: CS
with margin 7.63¢, strictly proper, P = S = 21, 7 gap classes. Against
LAT-MEL-001's baseline (0/29 eikosanies CS, 100% improper at odds ≤ 15) this
is the first eikosany in the program that is simultaneously CS and proper.
Harmonic cost is visible: P = 21 vs the canonical eikosany's 57 — the
melody⇄harmony trade-off as a single pair of scales. Ear check queued as
part of G-012.

**Kept.** Both frozen scorers untouched (pins verified); melodic CS at 0.5¢
and exact-CS agree on every winner.

## 2026-07-28 — CS-EIK-001 post-hoc: literature calibration and a P3 correction

**Correction (before any announcement):** the run's epimorphy solver demanded
an INTEGER val on the full prime basis; the standard definition (xen wiki
"Detempering"/Epimorphic: v on the subgroup generated by the scale, ℚ-
consistency sufficient) is weaker. Corrected P3 numbers: **18/32 CS winners
are epimorphic, 14/32 admit no val at all** (inconsistent system). P3 remains
REFUTED (CS ≠ epimorphy) but by 14, not 28. Receipts:
results/cseik001_posthoc.json.

**Literature calibration (en.xen.wiki/w/Constant_structure, /w/Detempering):**
(1) our exact-CS criterion is precisely Wilson's/the wiki's definition
(interval matrix, exact identity, no tolerance) — the CS margin is our
extension; (2) strictly proper ⇒ CS is a KNOWN theorem, so the flagship's
correct headline is "**first strictly proper eikosany**" — its CS-ness
follows by theorem (our receipts agree: 20/20 strictly-proper scales CS,
0 proper-not-strict CS); (3) "epimorphic strictly stronger than CS" is known
in the abstract via the minimal 3-tone counterexample {5/4, 32/25, 2/1} —
what is NEW here is prevalence and naturalness: 14 twenty-tone CS-no-val
scales inside Wilson's own CPS(6,3) family; (4) the known theorem "CS +
linearly independent steps ⇒ epimorphic" is consistent with our data (31/32
winners have dependent step sets — their CS-ness lives on comma relations,
which is exactly the BRIDGE connection).

**Kept**, with P3's magnitude corrected in place before external claims.

## 2026-07-28 — G-012 ear check (discovery audition, not blind) + two Marcus insights

**Protocol:** results/scl/g012/, three scales, known identities, same routine
as G-006 (same patch/register, stepwise walks, transposed motives; subsets
explored in Wilsonic as EG6 where noted).

**Verdicts (Marcus):**
1. Canonical {1,3,5,7,9,11}: "doesn't feel symmetric enough to be melodic."
2. Flagship {1,7,9,11,15,29}: "feels the most melodic to me at the eikosany
   level" — pitch-wheel evenness visibly matches strict propriety. Subset
   walkthrough deferred to the subset session.
3. Max-margin {13,17,21,23,25,27}: "comparable to scale 1" at the full-scale
   level; played as EG6, "some melodic hexanies in there."

**Retro-prediction check (receipts):** flagship & max-margin both 7 gap
classes at N=20; canonical 10. Gap-class count alone ranks {flagship,
max-margin} > canonical; propriety separates flagship (strictly proper) from
max-margin (improper). The CONJUNCTION (few classes AND proper) reproduces
Marcus's ranking exactly. Hexany nuance: all 12 strictly-proper hexanies
have 4 gap classes; the only 3-class hexanies (4 of them) are improper —
class-count and propriety are partially independent axes; both load.

**Insight 1 (Marcus, for future research):** "we usually don't play the
eikosany, we usually play the subsets of it (dekanies, hexanies are melodic
sweet spots)." → The melodic score of a CPS should perhaps be the
DISTRIBUTION of melodic scores over its embedded subset CPS, not the
full-scale M1–M3. Direct dovetail with BRIDGE's hexany-as-addressable-region
endgame and the EG6 root-mapping feature. Queued: subset-melodic experiment
(working name SUBSET-MEL-001) + brainstorm session.

**Insight 2 (Marcus, aesthetic principle):** MOS beauty = two-interval
patterns (Fibonacci repetitions); three-interval scales can also be
beautiful; "optimizing for fewer interval sizes relative to the notes per
octave is key for melody… 6 notes with 6 different sizes can not [be
melodic]." → Concrete functional form for the melodic aggregator:
gap_classes/N as a primary penalty, conjoined with propriety. Random
controls (≈N classes) sit at his "cannot be melodic" floor, as predicted.

**G-012 status:** ear evidence complete and consistent with the corrected
claims; decision (merge PR #29 correction + formal pass) remains Marcus's.

## 2026-07-29 — BRIDGE-000 pre-registration (entry BEFORE reading the scan or any run)

**Contract:** SPEC §BRIDGE-000. Design decisions (Marcus, 2026-07-29, via
structured Q&A):
1. Scope: fig-24 D'Alessandro (32 EG6 tones + 6 pigtails = 38 tones on 31
   degrees) with BOTH lifts — +18 (huygens) and −13 (meanpop, inverted
   D'Alessandro, figs 26–27). The 1980 version (genus 3³·5·7·11², 8
   pigtails) is deferred to BRIDGE-000b.
2. Calibration standard = PARETO PAIR, no scalar: (harmonic wealth: frozen
   v1.1.0 triad scores of the 38-tone JI pitch set + per-embedded-hexany
   triad survival) × (addressing cost: collision count, comma identities,
   degree-consistency of the val image). Every future BRIDGE candidate must
   match or beat on both coordinates.
3. Additional measurement: H-B1 only (Marcus declined raw-set melodic panel
   and per-subset melodic panel for this run; subsets wait for
   SUBSET-MEL-001).
4. Verification: FULL transcription of fig 24 (+ figs 26–27 for the lift)
   from dal.PDF, read in place (never vendored — [erv-scan-archive rule]),
   committed as a derived table citing figure numbers; the encoded val must
   reproduce every placement and every collision pair exactly.

**H-B1 (pre-registered, before opening the scan or computing anything):**
Wilson's 31-EDO patent val ⟨31, 49, 72, 87, 107⟩ (with 9 = 3² linear, lift
+18 for 11; and the −13-lift variant) MINIMIZES val-degree tie-pairs for the
38-tone D'Alessandro set over the ±1-per-odd-coordinate val neighborhood at
N = 31 — i.e., the template is the tie-optimal addressing, not merely an
adequate one. Ties are forced (38 tones on 31 degrees ⇒ ≥ 7 collisions by
pigeonhole, with equality iff no degree hosts 3+ tones); prediction: Wilson's
val achieves EXACTLY the pigeonhole floor of 7, and no neighbor val does
better (some may tie at 7; report the count). Either outcome is a finding —
a neighbor val beating Wilson would be the surprise of the quarter.

**Expected placements (from SPEC/memory, to be checked against the scan, not
derived from it):** 3→18, 5→10, 7→25, 11→14 (+18 lift); 9 = 2·18 mod 31 = 5;
pigtails at degrees −1≡30, +8, +9, +26, +27, +36≡5; duplicated degrees
exactly {0, 5, 10, 13, 18, 23, 28}; kernel commas 385/384 (degs 18, 5, 23),
2079/2048 (degs 0, 10), 121/120 (degs 13, 28).

**Deliverables:** derived transcription table (figure-cited), bridge000.py,
results/bridge000.json (placements, collisions, Pareto-pair standard, H-B1
sweep), LOG verdict, FINDINGS promotion, PR. Gate G-014 opens on completion.

## 2026-07-29 — BRIDGE-000 results + verdicts

**Run:** bridge000.py (~1 s), receipts results/bridge000.json; scan anchors
in BRIDGE000_TRANSCRIPTION.md (dal.PDF figs 24, 26–27 read in place).

**Verification: EXACT, every pre-registered expectation reproduced.** 38
tones (32 EG6 + 6 pigtails), huygens chain −1..+36 consecutive, 38 distinct
pitch classes; collisions at exactly {0,5,10,13,18,23,28}; comma census
exactly {385/384 ×3, 2079/2048 ×2, 121/120 ×2}; all fig-24 template anchors
and pigtail identities reproduced. Meanpop lift: EG6 core span 31 slots
(SPEC's "shrinks to 31"), full 38-tone span −26..+30, and exactly **5
position-unisons** — matching SPEC's "five collisions become physical
unisons" and fig 26's own +/✻ comma legend.

**The calibration standard (Pareto pair) is now on record:**
- Harmonic wealth: full 38-tone set P = S = 154, G = 28 (frozen v1.1.0,
  exact path; the set is inversionally symmetric). **All 15 embedded
  hexanies are injectively addressed** — Wilson's seven collisions never
  land two tones of the same hexany on one key. Per-hexany (P,S) recorded.
- Addressing cost: 7 collisions = the pigeonhole floor exactly (38 tones,
  31 degrees), zero triple-occupied degrees, commas as above.
- Cents error: 0 by construction (regime iii, pitch-just).

**H-B1 — KEPT, verbatim as pre-registered.** Wilson's val ⟨31,49,72,87,107⟩
achieves exactly the pigeonhole floor (7 tie-pairs, 0 triples); of the 80
neighbor vals (±1 per odd coordinate), **none is better** and exactly one
ties — ⟨31,50,71,87,107⟩, a mapping-inaccurate val (3→19\31, a ~735¢ fifth)
that no one would tune. Worst neighbor: 52 tie-pairs. Wilson's template is
the tie-optimal AND the only accurate val at the optimum: the 1975 keyboard
is, by machine check, the best possible 31-degree addressing of these 38
tones. The val-tie lens (LAT-MEL-001 → CS-EIK-001 → here) now spans the
whole program: ties explain the eikosany's CS failure, their absence defines
the CS winners, and their minimization is what Wilson's hand computed.

**Kept.** Frozen scorers untouched; pins verified; G-014 opened.

## 2026-07-29 — MOS-LAT-002 pre-registration (entry BEFORE any run)

**Experiment:** the registered follow-up to MOS-LAT-001 (LOG 2026-07-28: "the
natural follow-up is a mixed-tail corpus (metallic tails of 2s and 3s), where
the hidden lattice actually varies"). H-M1 retest on a quadratic-generator
corpus with MIXED periodic CF tails, where the spectral gap |λ/λ′| is
genuinely non-constant. Runner: `moslat002.py`; receipts:
`results/moslat002.json`. Frozen scorer v1.1.0 via `score_tempered` (ε = 2.0¢
default, max_span 1200¢ default, both recorded per row). `moslat001.py` is
NOT modified; its rank-statistics machinery (`ranks`, `partial_spearman`,
`stratified_permutation_p`) and `iota` are imported read-only so the two runs
are statistically comparable by construction.

**Corpus (SPEC §Search parameterization note, digit-string enumeration):**
periodic tails = all digit strings of period length 1–2 over digits {1,2,3},
EXCLUDING the pure all-1s tail (that is MOS-LAT-001's corpus): (2)*, (3)*,
(1,2)*, (2,1)*, (1,3)*, (3,1)*, (2,3)*, (3,2)*. Note (1,1)*, (2,2)*, (3,3)*
collapse to period-1 strings and are not separate. Preambles: all digit
strings over {1,2,3} of length ≤ 3, including empty (40 per tail, 320 raw
(preamble, tail) pairs). Deduplication by EXACT generator value — a quadratic
irrational's CF digit sequence is unique, so (p₁..pₖ, (t₁t₂)*) duplicates
arise exactly when the preamble's last digits absorb into a rotation of the
tail; predicted distinct count 27 per tail = 216 generators (same
canonical-preamble census as MOS-LAT-001's 27), comfortably above the
registered floor of ≥ 40. All generators lie in (0,1) by construction
(leading digit ≥ 1). Rows: per generator, every distinct MOS cardinality
N ∈ [5, 22] reachable at Brun zigzag levels 0–9 (first level per
denominator), exactly as in `moslat001.run_step2_rows`; generators with no
cardinality in range contribute zero rows (count reported).

**Construction (logged before implementation):** tail matrix
M = Π [[0,1],[1,tᵢ]] (Möbius matrix of x ↦ 1/(tᵢ+x), composed in digit
order); the purely periodic value x = [0;(t₁..tₘ)*] is the fixed point of M,
i.e. the root in (0,1) of m₂₁x² + (m₂₂−m₁₁)x − m₁₂ = 0, with discriminant
D = tr(M)² − 4·det(M), det(M) = (−1)^m. Standard reduced-CF theory: exactly
one root lies in (0,1) (x = 1/θ with θ > 1 reduced purely periodic, whose
conjugate lies in (−1, 0), so x′ = 1/θ′ < −1), asserted at construction. Preamble digits applied as g = F_{d₁}∘…∘F_{dₖ}(x),
F_d(y) = 1/(d+y), exact. Arithmetic: exact ℚ(√d) throughout — integer triple
(a, b, c) for (a + b√d)/c with d SQUAREFREE (square part of D folded into b),
normalized c > 0, gcd = 1; Galois conjugate √d → −√d; exact sign/floor as in
moslat001's Q5, generalized to arbitrary non-square d. For this tail set
D ∈ {8, 13} (period 1, tr 2, 3, det −1: D = tr²+4) and D = tr²−4 with
tr = 2 + t₁t₂ ∈ {4,5,7,8,11} (period 2, det +1) → squarefree
d ∈ {2, 3, 5, 13, 15, 21} (tr = 11 gives D = 117 = 9·13 → d = 13 again) —
recorded per generator; D is never a
perfect square here (checked: tr²+4 and tr²−4 are non-square for these
traces), so every generator is a genuine quadratic irrational. Floats only
for receipts, mos_cents scoring (same as MOS-LAT-001), and the spectral gap.

**Descriptors per row (d1–d4 identical to MOS-LAT-001, d5 new):**
  d1 conj_sep = |g − g′| (per generator);
  d2 window_width = |q·g′ − p| at the row's level;
  d3 spread = max−min of ι(b) = b·g′ − ⌊b·g⌋ over b ∈ [0, N);
  d4 norm_spread = d3 / (N·d1);
  d5 spectral_gap = |λ/λ′| of the TAIL matrix = λ² (since |det M| = 1),
     a tail-cycle invariant (conjugation-invariant, so rotations (1,2)/(2,1)
     share it while their generator values differ). Registered prediction of
     the achieved spread — the point of the corpus: five distinct values
     {(1+√2)² ≈ 5.828, ((3+√13)/2)² ≈ 10.908, (2+√3)² ≈ 13.928,
     ((5+√21)/2)² ≈ 22.956, (4+√15)² ≈ 61.984}, an order-of-magnitude range,
     vs the CONSTANT φ² ≈ 2.618 of MOS-LAT-001's all-1s corpus. The achieved
     min/max/#distinct of ALL five descriptors will be reported explicitly so
     the contrast with the degenerate corpus is on the record.

**H-M1 restated for the new corpus (the registered test):** outcome
y = P (frozen proportional count), control z = N (cardinality). For each
predictor x ∈ {g01_baseline, conj_sep, window_width, spread, norm_spread,
spectral_gap} — FIXED order, one rng consumed in that order — compute
partial Spearman ρ(x, P | N) (rank-transform, residualize x-ranks and
P-ranks on N-ranks by least squares, Pearson on residuals; the imported
moslat001 functions), then a stratified permutation test: shuffle x within
cardinality strata, seed 20260725, 9999 permutations, two-sided
p = fraction of permuted |ρ| ≥ observed |ρ|, add-one rule. NULL (as in
MOS-LAT-001): no descriptor beats generator-value binning — the g01
baseline run through the identical machinery. Registered verdict rule
(unchanged): H-M1 SUPPORTED iff some descriptor has permutation p < 0.05
AND |ρ| > |ρ_baseline(g01)|; otherwise NULL. Sensitivity report (secondary,
non-verdict): Holm correction over the 5 descriptors, recorded in the
receipt either way.

**Registered prediction:** from MOS-LAT-001's own post-mortem — its null was
attributed to the corpus (spectral gap constant, remaining descriptors
near-functions of (N, conj_sep)), not to the hypothesis — we predict that
with genuine conjugate-geometry variation AT LEAST ONE descriptor (most
plausibly d5 spectral_gap or d1 conj_sep, now decoupled from it) beats the
generator-value baseline under the verdict rule. A second null on THIS
corpus kills the descriptor program: it would say triad hot spots are not a
function of the hidden lattice's conjugate geometry at all, and refocus the
search on generator arithmetic directly (CF digit statistics, field
discriminants). Either outcome is a reportable finding. Secondary registered
expectation: P = S on every row (anchored-scorer inversional symmetry on
MOS, as in every run so far).

**Known limitations, logged now (inherited from MOS-LAT-001):** rows sharing
a generator are pseudo-replicated; the stratified permutation limits but
does not eliminate this — p-values are descriptive, not confirmatory.
spectral_gap takes only ~5 distinct values across ~216 generators, so its
rank test is coarse (many ties); that is the honest granularity of a
tail-cycle invariant on a period ≤ 2 corpus.

**Order:** implement moslat002.py + unit tests (Quad exact arithmetic incl.
squarefree reduction, tail fixed-point known values, preamble application,
cross-tail dedup identities, spectral-gap values, corpus census, stats
determinism) → run → receipts → results entry below → FINDINGS.md promotion
→ full lattice + triads suites + both freeze checks.

## 2026-07-29 — MOS-LAT-002 results + verdict

**Run:** moslat002.py, python3.12, ~65 s; receipts `results/moslat002.json`
(scorer 1.1.0, ε = 2¢, max_span 1200¢ recorded per row; seed 20260725,
9999 stratified permutations, moslat001's own statistics code objects,
asserted identical by the test suite).

**Corpus census — exactly as pre-registered.** 320 raw (preamble, tail)
pairs → **216 distinct generators** (the predicted 27 per tail; 104
rotation-absorption duplicates dropped, every duplicate agreeing on its
tail cycle), 788 (g, N) rows at N ∈ [5, 22]. Descriptor spread — the
registered proof of non-degeneracy vs MOS-LAT-001:

| descriptor    | achieved range        | #distinct | MOS-LAT-001    |
|---------------|-----------------------|-----------|----------------|
| g01           | [0.2638, 0.7913]      | 216       | 27 values      |
| conj_sep      | [0.00210, 4.5826]     | 128       | 18 values      |
| spectral_gap  | [5.8284, 61.9839]     | **5**     | **constant φ²**|
| window_width  | [0.0174, 87.034]      | 594       | —              |
| spread        | [0.7022, 82.243]      | 669       | —              |
| norm_spread   | [0.6196, 62.079]      | 761       | —              |

The five spectral-gap values are the registered set {(1+√2)², ((3+√13)/2)²,
(2+√3)², ((5+√21)/2)², (4+√15)²} — an 10.6× range where MOS-LAT-001 had a
single point. P = S on all 788 rows (registered expectation kept).

**H-M1 verdict: NULL — the registered prediction is REFUTED.** Partial
Spearman ρ(descriptor, P | N), stratified permutation: g01 baseline
ρ = −0.0711 (p = 0.2531); conj_sep ρ = +0.0349 (p = 0.3387); window_width
ρ = +0.0333 (p = 0.3835); spread ρ = +0.0235 (p = 0.5006); norm_spread
ρ = −0.0296 (p = 0.4023); spectral_gap ρ = −0.0642 (p = 0.0635). The
nearest miss, spectral_gap, fails BOTH prongs of the registered verdict
rule: p ≥ 0.05 and |ρ| = 0.064 < |ρ_baseline| = 0.071. Holm-adjusted
(secondary, registered): all descriptors ≥ 0.3175. With 8× the rows and
genuine conjugate-geometry variation, no descriptor beats generator-value
binning — the same verdict as the degenerate corpus, now without the
corpus excuse. **Per the pre-registration this kills the descriptor
program**: triad hot spots are not a function of the hidden lattice's
conjugate geometry; future search should organize by generator arithmetic
directly (CF digit statistics, value neighborhoods), not by embedding
descriptors.

**Post-hoc observation (NOT registered, mechanism candidate):** hot spots
pin to generator-VALUE neighborhoods across arithmetically unrelated
fields. Flagship pair: `[0;3,2,2,(2,3)*]` = 351.40¢ (ℚ(√15), gap 61.98)
and `[0;3,(2)*]` = 351.47¢ (ℚ(√2), gap 5.83) — 0.07¢ apart in value,
maximally apart in every lattice descriptor, identical P = 45 at N = 17.
The ~317¢ noble-minor-third region is hot under FOUR different tails
(316.73–318.01¢, P = 48/45/42 here, plus MOS-LAT-001's [0;3,1,3,(1)*]
317.17¢, P = 62), and the complement pair 848.53¢/351.47¢ ties at P = 45
(complement symmetry again). Consistent mechanism: with scorer ε = 2¢,
P is a locally stable function of g01, while every conjugate-embedding
descriptor is violently discontinuous in g01 (it depends on the arithmetic
identity, not the location) — so no such descriptor can carry information
the g01 rank doesn't already carry. This is the refocus target the
pre-registration named: the hot-spot map lives on the circle, not on the
lattice.

**Hot spots (receipt → hot_spots):** top P = 64 at `[0;1,3,2,(1,3)*]`
≈ 924.66¢, N = 22 — exceeds MOS-LAT-001's corpus max (62). Then
`[0;2,1,1,(1,2)*]` ≈ 455.59¢ (P = 54, N = 21), `[0;1,3,(2)*]` ≈ 928.15¢
(P = 50, N = 22), `[0;3,1,3,(1,2)*]` ≈ 316.73¢ (P = 48, N = 19),
`[0;2,2,3,(2)*]` ≈ 492.58¢ (P = 46, N = 22), and the silver-tail pair
`[0;1,(2)*]`/`[0;3,(2)*]` ≈ 848.53¢/351.47¢ (P = 45, N = 17).

**Kept.** moslat002.py exactly as implemented before the run (no post-run
changes); exact ℚ(√d) arithmetic (Quad) verified by 33 new unit tests
written before the run, including the 216-generator census, tail
fixed-point identities, rotation absorption, and the statistics-reuse
contract (`partial_spearman`/`stratified_permutation_p`/`iota` ARE
moslat001's code objects). Lattice suite 88/88 OK; triads suite 88/88 OK;
freeze checks OK (scorer pin 1a840af9…9b592, melodic pin a16f162b…e7535
unchanged). Findings promoted to FINDINGS.md.

## 2026-07-29 — BRIDGE-001 pre-registration (entry BEFORE any implementation or run)

**Contract:** SPEC §BRIDGE-001, scoped to EG4 per Marcus's 2026-07-22 scope
decision, under his two binding design decisions (val-as-degree-assignment
with NO nearest-degree rounding; monotonicity as the only structural filter,
applied FIRST). Runner: `bridge001.py`; receipts:
`results/bridge001.jsonl` (one row per candidate, rejections included) +
`results/bridge001_summary.json` (Pareto front vs the BRIDGE-000 standard).
Frozen scorers: triads v1.1.0 (`score`, `score_tempered` at ε = 2.0¢,
default max_span) and melodic v0.1.0 (imported for provenance only this
run; subset melodic panels wait for SUBSET-MEL-001 per G-012 insight 1).

**Note for Marcus #1 — rank accounting (SPEC soft spot, resolved here).**
SPEC §BRIDGE-001 says the EG4 lattice (odd primes 3,5,7; octave-equivalent
rank 3) needs "exactly ONE comma" for an MOS embedding. Counting in the
full 2.3.5.7 group (rank 4): a linear MOS host (period 2/1 + one generator)
is rank 2, so the full kernel has rank 2 — TWO independent commas, not one.
(Octave-equivalently: rank 3 → rank 1 generator chain, still two.) The
practical resolution adopted: candidates are pairs (comma c, val v) with
v = ⟨N, a3, a5, a7⟩ at host cardinality N and v(c) = 0 — the explicit comma
names the planar temperament, the val supplies the rest of the kernel
implicitly, and the val IS the degree assignment (design decision 1). The
implicit second kernel generator is made concrete by the completion rule
below; it is a convention, flagged for review.

**Note for Marcus #2 — the "16-tone tesseract" counts formal vertices, not
pitches.** The EG4 tesseract of {1,3,5,7} has 16 vertices (all subsets),
but seed 1 pairs every subset S with S∪{1} at the SAME product, so the
pitch-class set is the 8 divisors of 105, octave-reduced: 1/1, 35/32, 5/4,
21/16, 3/2, 105/64, 7/4, 15/8. This is exactly the BRIDGE-000 convention
(EG6's 64 subsets = 32 distinct tones). All 16 vertices are listed in the
receipts; the 8 with/without-1 pairs are structural (comma 1/1, zero cost)
and are EXCLUDED from collision counts. Injectivity (H-B2) is evaluated on
the 8 distinct tones. Embedded subsets measured: hexany CPS(4,2) =
{3,5,7,15,21,35} and both tetranies CPS(4,1) = {1,3,5,7}, CPS(4,3) =
{15,21,35,105}.

**Comma enumeration (locked):** primitive monzos over (2,3,5,7) with odd
exponents |e3| ≤ 8, |e5| ≤ 5, |e7| ≤ 4, nonzero odd part, e2 = the unique
integer putting the >1 octave representative at 0 < cents < 60, Tenney
height n·d ≤ 2⁴⁰. The named list — 81/80, 64/63, 126/125, 225/224,
245/243, 1029/1024, 2401/2400, 3125/3087, 4375/4374 — is verified to be a
subset of the enumeration (all nine fit the box); the deduped final list is
logged in the summary receipt with its count.

**Vals (locked):** N ∈ 7..22; a_p ∈ patent ± 1 per odd coordinate (27 vals
per N, patent = ⟨N, round(N·log₂3), round(N·log₂5), round(N·log₂7)⟩).
Candidate = (c, v, N) iff v(c) = 0.

**Monotonicity filter (Marcus's decision 1, applied FIRST, before any
error-budget work):** unreduced degrees d(t) = v·monzo(octave-reduced t)
over the 8 distinct tones in pitch order must satisfy d(1/1) = 0,
d weakly increasing, d ≤ N. Any strict decrease ⇒ REJECT, logged with the
violating comma, val, and adjacent tone pair. Ties (including d = N, a
merge with the octave) are COLLISIONS — regime ii tempered-merge, a result,
not a failure — logged with the merged pair's comma monzo (which the val
provably kills).

**Completion rule (the implicit second comma, locked):** k₂ := the
primitive monzo in the val's kernel (same odd-exponent box; e2 =
−(a3e3+a5e5+a7e7)/N required integral), linearly independent of c, that
MINIMIZES the pre-registered tuning error of the rank-2 temperament with
kernel sat⟨c, k₂⟩; ties broken by smaller Tenney height, then lex smaller
(e3,e5,e7). Rationale, recorded before the run: the naive minimal-Tenney-
height completion is wrong — at (225/224, ⟨21,33,49,59⟩) it picks 36/35
(TH 1260, the august/augmented family, ~10¢ errors) over 1029/1024
(miracle, ~2.4¢); min-error is "the best rank-2 temperament this val
supports that tempers c", and is deterministic. Mapping matrix M (2×4) =
saturated left-kernel of [c, k₂] via Smith reduction, row-Hermite
normalized (period row first, M[0][0] = periods per octave x; x | N is
automatic because v factors through the quotient — asserted, not filtered).

**Tuning (locked, ONE choice):** pure-octave minimax over {3,5,7}: period
exactly 1200/x ¢; generator G the unique minimizer of
max_p |T(p) − 1200·log₂p|, T(p) = M₀ₚ·(1200/x) + M₁ₚ·G (piecewise-linear
exact minimax over pairwise crossings and per-line zeros; tie → smaller G).
Errors are reported per tone on the octave-reduced monzos.

**Measured per surviving candidate:** degree table of all 16 vertices;
collision count + comma monzos (8 distinct tones only); per-tone cents
error (max, mean); frozen score_tempered ε=2 of the tempered 8-tone image;
per-subset degree lists, addressing injectivity, and triad survival for
hexany/tetrany-1/tetrany-3 (survival = image guarded counts ≥ the subset's
own exact-path base counts, measured at run start; hexany base expected
(6,6) per the SHADOW-001 v1.1.0 correction — NOT the SPEC's stale (8,8));
MURCHANA/WINDOW-ANCHOR: generator-chain coordinates b(t) = M₁·monzo(t),
chain span, containment at anchor 0, and the full admissible anchor
interval when the span fits in N/x (MOS-LAT-001 corollary: anchoring is a
free design parameter — sweep before rejecting); host step-class count
(three-gap check on the anchored host at the optimal G) and a
degrees-match-host-ranks consistency bit; ε_bridge ∈ 1..15¢ regime sweep
(faithful iff injective ∧ max error < ε; tempered-merge iff collisions > 0
∧ max error < ε; else over-budget).

**Falsifiable predictions (registered before implementation):**
- **H-B2 (primary, from SPEC/program):** at least one candidate carries the
  full EG4 tesseract injectively (all 8 distinct tones, distinct degrees)
  at N ≤ 22 with max per-tone error < 15¢ and every hexany triad surviving
  score_tempered at ε = 2¢ (image (P,S) ≥ base (6,6)). Predicted PASS.
- **P-COMMA (which commas win, named before running):** the low-error end
  of the Pareto front is owned by 225/224 — flagship candidates predicted:
  orwell at N = 22 (patent val, completion 1728/1715, minimax ≈ 2.3¢),
  miracle at N = 21 (patent val, completion 1029/1024, ≈ 2.4¢), with
  garibaldi at N = 17 (a5 = patent+1, completion 5120/5103) close; magic
  (245/243 ∩ 225/224, N = 19/22, ≈ 5¢) and meantone (81/80 with 126/125
  completion, N = 12/19, ≈ 4–6¢) on the front only at the simplicity end.
  Predicted non-winners: 64/63 (error too large), 2401/2400 / 3125/3087 /
  4375/4374 standalone (too accurate to bind at N ≤ 22 — their best vals
  coincide with the winners above).
- **P-KILL (monotonicity):** no full kill among the nine named commas;
  full kills ≤ 25% of the enumerated list, concentrated where the val
  inverts the 84.47¢ adjacency 5/4 < 21/16 — i.e. rejections are logged
  overwhelmingly with v(21/20) < 0, at small N and off-patent vals.
- **P-MERGE:** zero tempered-merges in the ≤ 15¢ regime: the minimal
  EG4 tone-pair commas (21/20 = 84.47¢, 112/105 = 111.45¢, 16/15 =
  111.73¢, 15/14 = 119.44¢) all exceed the 60¢ comma bound, and any val
  killing one of them must spread ≥ 84¢ of comma over ≤ 22 degrees,
  predicting max per-tone error > 15¢.

**Determinism:** stdlib only, python3.12, no randomness; constants above;
timestamps/commit as provenance only. Unit tests
(tests/test_bridge001.py) are written and green BEFORE the first run.

## 2026-07-29 — BRIDGE-001 results + verdicts

**Run:** bridge001.py (~3 s, bit-identical across two runs), receipts
`results/bridge001.jsonl` (2205 rows: 1615 scored + 590 monotonicity
rejections) and `results/bridge001_summary.json`. 63 commas enumerated
(all 9 named included); scorer v1.1.0, melodic v0.1.0, tests 22/22 green
pre-run (including the hand-derived miracle minimax pin: G = 116.5878¢,
err = 2.4284¢ — reproduced by the solver to 4 decimals).

**H-B2 — REFUTED under the strict reading; the pre-registered PASS
prediction fails.** No candidate at N ≤ 22 is simultaneously (a) injective
on the 8 distinct tesseract tones, (b) CONTAINED in an N-note MOS window
(any anchor), and (c) full hexany triad survival at ε = 2¢. The two halves
exist separately and the gap between them is the finding:
- *Contained* candidates top out at hexany image (3,3) at ε = 2
  (miracle) — best contained errors 2.727¢ (orwell-22) / 6.858¢ (miracle).
- *Addressing-only* passers exist (32 rows; best: ennealimmal
  2401/2400 ∩ 4375/4374 at N = 18, max tone error 0.204¢, full hexany
  survival) — but every one FAILS containment: accurate microtemperaments
  need large generator counts, so the EG4 chain span (8 for ennealimmal's
  2-per-period classes, up to 34 elsewhere) exceeds every N ≤ 22 window.
  **The binding constraint on the bridge is the MOS window (chain span),
  not tuning accuracy.** The pre-registered H-B2 sentence was ambiguous on
  containment; the strict reading is the program's meaning of "carries"
  and is the headline verdict. Both readings are in the summary receipt.

**The one-cent resolution (post-hoc lens, labeled in bridge001.py, added
after first inspection like moslat001's investigation fields):** sweeping
the frozen scorer's ε on the contained flagships' hexany images —
**miracle/blackjack recovers the FULL (6,6) at ε = 3¢**; orwell-22 at
ε = 4¢. The bar the prediction set (2¢) was exactly one cent too strict
for the best N ≤ 22 MOS host. "CPS structure inside an MOS" costs one
cent of triad tolerance at these cardinalities.

**Pareto front (contained, dedup by temperament × N × val), all rows
alias 225/224 — P-COMMA's family call confirmed:**
- **orwell-22** ⟨22,35,51,62⟩ (patent), completion 1715/1728, g =
  271.385¢, minimax 2.257¢, max tone err 2.727¢, injective, TRUE 2-step
  MOS, anchor −3 (interval [−6,−3]), faithful from ε = 3, hexany (2,2)@2¢
  → (6,6)@4¢. The error flagship.
- **miracle 19/20/21/22**, completion 1029/1024, secor g = 116.588¢, max
  tone err 6.858¢, hexany (3,3)@2¢ → (6,6)@3¢, anchor ∈ [−14,−9] at
  N = 21. N = 21 (blackjack) is the true 2-step host (19, 20 are 3-step
  generated scales — kept on the front per the SPEC's BRIDGE-001b
  "two-gap-ness is an objective, not an assumption"). The survival
  flagship: earliest full-hexany recovery of any contained candidate.
- Also contained but dominated: mothra (81/80 ∩ 1029/1024, N = 21,
  5.678¢), meantone (N = 17/19, 7.672¢, hexany (1,1) — its EG4 span is 16
  so N = 12 does NOT contain the genus; 35/32 needs 14 fifths).

**P-COMMA — KEPT in family, corrected in detail.** 225/224 owns the
entire contained front, orwell-22 and miracle-21 as named. But magic and
garibaldi never materialize: the min-error completion rule, given
(245/243, patent-19) etc., always finds a MORE accurate second comma than
magic's (picks 3125/3136-family, err 2.47¢, uncontained) — the completion
is greedy-accurate and skips mid-accuracy temperaments entirely. A
BRIDGE-001b variant should sweep k₂ instead of argmin if the full
temperament Pareto is wanted per val.

**P-KILL — KEPT, mechanism clause refined.** ZERO commas fully killed
(prediction: ≤ 25%, none named); 590/2205 pairs rejected. Violating-pair
census: 5/4 < 21/16 is the plurality as predicted (292 of 856 violation
records) but not "overwhelming" — 1/1–2/1 range violations 178, 7/4 <
15/8 151, 105/64 < 7/4 121, boundary pairs 57 + 57.

**P-MERGE — KEPT, with a bonus discovery.** Pitch merges: 9 rows, min max
error 54.4¢ ≫ 15¢ — zero merges in the ≤ 15¢ regime, as predicted. But
1026 scored rows have DEGREE collisions that are NOT pitch merges — same
address, distinct pitch, resolved by chain position — i.e. **D'Alessandro's
regime iii arises spontaneously in the machine search** (min max-err
0.492¢: 2401/2400 at ⟨7,11,17,20⟩, address-commas 16/15 and 21/20). The
1975 keyboard's pitch-just/address-tempered trick is not an idiosyncrasy;
it is what the lattice offers whenever tones exceed degrees.

**Structural surprise — sign cancellation:** per-tone EG4 error is NOT
the prime minimax. Orwell's mixed-sign prime errors (−2.26, −0.47, +2.26)
cancel in compound tones (max tone err 2.73 ≈ minimax 2.26); miracle's
sign-coherent errors (−2.43, −2.43, −2.00) stack to −6.86 on 105/64
(3× its 2.43 minimax). A tone-set minimax (optimize over the 8 images,
not the 3 primes) is the obvious future tuning lens; not run here — the
tuning was pre-registered.

**Murchana corollary, confirmed in practice:** NO front row contains the
EG4 at anchor 0 — every host needs the MOS-LAT-001 anchor sweep (miracle
[−14,−9], orwell [−6,−3]). Anchoring-as-free-parameter is load-bearing
for BRIDGE, exactly as the corollary predicted.

**Vs the BRIDGE-000 standard:** D'Alessandro holds the pitch-just corner
(0¢, 7 collisions = pigeonhole floor, 100% subset survival); the best
EG4 bridges hold the opposite corner (0 collisions, 2.7–6.9¢, full
hexany survival only at ε = 3–4¢). Nothing at N ≤ 22 matches Wilson's
survival at zero collisions — the melody⇄harmony trade-off, now measured
as a two-corner Pareto with nothing in between at EG4 scale.

**Kept.** Runner and receipts stand; both frozen scorers untouched (pins
verified). Post-hoc additions logged above: per-row
`posthoc_hexany_full_recovery_eps` (contained rows only) and the
addressing-only H-B2 reading in the summary — neither changes any
pre-registered field.

**Run receipt:** 2026-07-29, python3.12 — lattice suite 77/77 OK
(25 melodic + 12 shadow001 + 18 moslat001 + 22 bridge001), triads suite
88/88 OK, freeze checks A OK on both pins (scorer 1a840af9…9b592,
melodic a16f162b…7535). Receipts bit-identical across two runs.

## 2026-08-09 — ET-001 pre-registration (entry BEFORE any implementation or run)

**Question:** what do the frozen scorers say about equal temperaments as a
family — the (N, ε) phase diagram. For every EDO N = 2..60, score the FULL
N-EDO scale with the frozen triad scorer's tempered path and chart, as a
function of ε, when proportional and subcontrary triads first appear
("lock") and how counts grow; run the frozen melodic scorers as the melody
axis so ETs join the program's melody⇄harmony Pareto tables. Runner:
`et001.py`; receipts `results/et001.jsonl` (one row per N, 59 rows) +
`results/et001_summary.json`. Tests `tests/test_et001.py` green before the
first run. Frozen scorers: triads v1.1.0 (`score_tempered`, PRIMARY
middle-anchored convention, default `max_span_cents = 1200`) and melodic
v0.1.0 (`score_melodic`, defaults). Stdlib only, python3.12, fully
deterministic; receipts carry no wall-clock fields; two runs must be
bit-identical (diff recorded in the results entry).

**What ε means operationally (read from the frozen code, not assumed).**
`score_tempered` ε is NOT the plugin's historic absolute linear-frequency
0.0005 (register-dependent, ≈0.43–0.87¢ across the octave —
CLAUDE.md/crossval001). It is a CENTS deviation applied per mean-condition
in the comparison layer: a triple a < b < c (cents) gets label P iff
|1200·log₂((fa+fc)/(2·fb))| < ε (strict), S and G analogously (frequencies
f = 2^(cents/1200)); labels are a set, so one triple can carry several.
Two structural clauses shape every lock below: (i) the octave-span limit
admits triples with c − a ≤ 1200 INCLUSIVE (`c - a > max_span_cents` skips),
so span-exactly-1200 chords are scored; (ii) the degeneracy guard drops a
triple from ALL counts unless its outer pair resolves the means:
sep(a,c) = |1200·log₂(AM/HM)| ≥ ε. So a triple with deviation d and
separation sep counts exactly on the half-open ε-interval (d, sep] — counts
are NOT monotone in ε, and a class's lock threshold is
ε* = min{d : d < sep}, with counts > 0 only strictly above ε*.

**Analytic mirror (the algebra the run must check; the scorer is the
referee, the mirror is not).** In N-EDO every anchor b is equivalent
(transposition invariance, exact for the anchored convention), so the
anchored sample factors: triple types (p, q) = steps below/above the middle,
1 ≤ p, q ≤ N−1, p + q ≤ N, each contributing exactly N counted triples
(one per anchor) when it qualifies. With s = 1200/N,
d_P(p,q) = |1200·log₂((2^(−ps/1200) + 2^(qs/1200))/2)|, d_S(p,q) = d_P(q,p)
(exact identity — same numerator over fa·fc), d_G = |q−p|·s, and sep
depends only on p+q. Closed forms derived before the run: the power chord
2:3:4-type (p = patent fifth steps F, q = N−F) has
d_P = |1200·log₂3 − 1900-equivalent| = the patent fifth error EXACTLY
(2^((N−p)s) = 2·2^(−ps) collapses the sum to 3·2^(−ps)); symmetric cluster
types (p = p) have d_P = d_S = sep/2 exactly (AM/GM = GM/HM), hence ALWAYS
qualify on (sep/2, sep], with sep/2 ∝ s²·ln2·const ≈ 2.89e−4·(2s)²/2 —
a 1/N² family that no guard removes.

**Corpus and constants (locked):** N ∈ 2..60 (59 scales), degrees
k·1200/N, k = 0..N−1. ε grid for count tables:
{1, 2, 3, 5, 10, 14.86, 20}¢ — 14.86 is Marcus's recalled cultural
epsilon kept literal (analytically it sits just ABOVE the true 12-EDO
major-triad threshold, so the patent major is included at that grid
point). Rail epsilon ε_G0 = 1e−6¢. Lock verification delta δ = 1e−6¢:
scorer must report class count 0 at ε*−δ and N·multiplicity at ε*+δ
(multiplicity = analytic ties within 1e−9¢). Melodic scorers at frozen
defaults. No other tunables.

**Falsifiable predictions (numbers derived analytically before the run;
scratch derivation with independent formulas only, no scorer calls):**
- **H-E1 (cultural epsilon).** "Full major+minor" = the patent 4:5:6
  proportional type (p, q) = (round(N·log₂(5/4)), round(N·log₂(6/5))) and
  its 10:12:15 subcontrary dual (q, p). Predicted 12-EDO threshold:
  **ε*_maj(12) = 14.8590¢** (= 1200·log₂((2^(−1/3)+2^(1/4))/2); Marcus's
  recalled 14.86 is confirmed to 2 dp and is on the correct side: 14.859022
  < 14.86). Verification: 12-EDO P count jumps 36 → 48 across
  ε*_maj ± δ (below: types (7,5), (5,4), (2,2) qualify; (1,1) is
  guard-dropped there since sep = 5.773 < ε). S mirrors exactly.
  Per-N patent-major thresholds (the "cultural epsilon of N" column),
  predicted: 19-EDO 3.0391, 22-EDO 8.7806, 31-EDO 3.8897, 34-EDO 0.4359,
  41-EDO 6.1163, 53-EDO 1.3671, 60-EDO 5.1410¢ — meantone-family story:
  19/31 support major+minor at ~3–4¢ where 12 needs ~14.9¢; 34 is the
  culture-set champion at 0.44¢.
- **H-E2 (power chords).** The frozen scorer DOES structurally count
  2:3:4-type proportional chords: span exactly 1200 passes the inclusive
  max_span test, and 3:4:6 (its subcontrary dual) likewise. Predicted:
  12-EDO's FIRST proportional lock overall is the power chord (7,5) at
  **ε* = 1.9550¢** (closed form 1200·log₂3 − 1900 = 1.955001¢ = the 12-EDO
  fifth error; Marcus's ≈2¢ recall confirmed), verified by P: 0 → 12
  across 1.9550 ± δ. Full predicted 12-EDO P lock spectrum head:
  1.9550 (7,5) < 2.8865 (1,1) < 7.8374 (5,4) < 11.5268 (2,2) <
  14.8590 (4,3) < 25.8640 (3,3).
- **H-E3 (ranking).** The naive cultural hypothesis — first-lock ε ranks
  by patent fifth error, top 5 = [53 (0.0682), 41 (0.4840), 29 (1.4933),
  58 (1.4933), 12 (1.9550)] — is REGISTERED AND PREDICTED REFUTED. The
  mirror says accidental near-AM coincidences beat famous fifths:
  predicted measured top 5 by first P lock =
  **[50 (0.008540¢, (9,8)), 41 (0.013540¢, (22,16)), 49 (0.047263¢,
  (28,20)), 39 (0.049463¢, (8,7)), 53 (0.068208¢, power chord (31,22))]**.
  "53 and 41 near the top" survives, but 41 gets there via an accidental
  (22,16) coincidence unrelated to its fifth, and 53 is the ONLY top-5
  entry whose lock is its fifth. The symmetric 1/N² cluster family enters
  the top 10 only at N = 59, 60 (0.1195, 0.1155¢). Verdict rule: every
  claimed lock confirmed by the scorer at ±δ; the cultural top-5 verdict
  is REFUTED iff the measured top 5 differs from the naive list.
- **H-E4 (melodic rails, sanity).** Every N-EDO under frozen melodic
  v0.1.0: gap_class_count = 1, entropy exactly 0.0 bits, is_cs = True,
  propriety = strictly_proper (adjacent-span margins are s > eps
  everywhere; N = 2 vacuously strict), gap_classes/N = 1/N. Any deviation
  at any N refutes.
- **R-DUAL (rail).** P = S exactly at every (N, grid ε) and every lock
  (EDO pitch-class sets are inversionally symmetric; the anchored scorer
  commutes with inversion). lock_P = lock_S.
- **R-G0 (rail).** At ε_G0 = 1e−6¢: P = S = 0 and G = N·⌊N/2⌋ for every N
  (symmetric types are float-exact geometric; smallest analytic P
  deviation in the whole sweep is 0.008540¢ ≫ 1e−6).
- **12-EDO grid pin.** P = S = [0, 12, 24, 24, 24, 48, 48] at
  ε = [1, 2, 3, 5, 10, 14.86, 20] — the 3-and-5¢ entries include the
  guard-window (1,1) cluster (2.887 < ε ≤ 5.773), the 14.86/20 entries
  include (2,2) but NOT (1,1); a sharp end-to-end pin of mirror vs scorer.

**Scale expectation:** ~35k analytic triple types, ~900 scorer calls,
59 receipt rows; minutes, not hours. If it grows past that the design is
wrong.

**Post-run obligations:** results entry here with per-hypothesis
KEPT/REFUTED/NULL, FINDINGS.md paragraph, gate row G-017 appended to
experiments/GATES.md (PENDING; sessions never self-approve), PR on
research/et-001. Anything not predicted above lands in clearly labeled
post-hoc fields.

## 2026-08-09 — ET-001 results + verdicts

**Run:** `et001.py` (~12 s, 798 scorer calls, receipts bit-identical across
two runs by diff on both files), receipts `results/et001.jsonl` (59 rows,
one per N) + `results/et001_summary.json`. Scorer v1.1.0, melodic v0.1.0,
lattice suite 130/130 green pre-run (16 new et001 tests), freeze checks A
OK on both pins before and after. Every analytic lock threshold in this
entry was confirmed by the frozen scorer at ε* ± 1e−6¢ (count 0 below
first locks, exact N·multiplicity jump above; zero verification failures
across all 59 N).

**H-E1 — KEPT. The cultural epsilon is 14.86¢, exactly as Marcus
recalled.** The patent 4:5:6/10:12:15 pair in 12-EDO locks at
**ε*_maj(12) = 14.859022¢** (2 dp: 14.86); scorer-verified P jump 36 → 48
across the threshold, S mirroring exactly. Per-N cultural epsilons
(patent-major threshold, all scorer-verified): 34-EDO **0.4359¢** (the
culture-set champion — and its first asymmetric lock IS its major triad),
53-EDO 1.3671, 19-EDO 3.0391, 31-EDO 3.8897, 41-EDO 6.1163, 22-EDO
8.7806, 12-EDO 14.8590. The meantone story quantified: 19 and 31 buy
full major+minor at 3–4¢ where 12 needs 14.9¢.

**H-E2 — KEPT, on the structural path.** The frozen scorer DOES count
2:3:4-type proportional chords: the octave-span limit is inclusive
(`c − a > max_span_cents` skips, so span exactly 1200¢ is scored). 12-EDO's
first proportional lock overall is the power chord (7,5) at
**ε* = 1.955001¢** — the closed form 1200·log₂3 − 1900, i.e. exactly the
patent fifth error, and that identity (power-chord deviation = fifth
error) is exact for every N. Verified 0 → 12. Marcus's ≈2¢ recall
confirmed at 1.955¢.

**H-E3 — naive REFUTED, mirror KEPT: first-lock is numerology above
~0.1¢, and the famous fifths mostly aren't first.** Measured top 5 by
first P lock: **50 (0.008540¢, (9,8)), 41 (0.013540¢, (22,16)),
49 (0.047263¢, (28,20)), 39 (0.049463¢, (8,7)), 53 (0.068208¢,
power chord (31,22))** — exactly the analytic-mirror prediction; the
naive fifth-error top 5 [53, 41, 29, 58, 12] is refuted. "53 and 41 near
the top" survives, but for opposite reasons: 53 is the ONLY top-5 entry
whose lock is its fifth; 41 gets rank 2 from an accidental (22,16)
coincidence unrelated to its fifth. The pre-registered symmetric-cluster
family (d = sep/2 exactly, ∝ 1/N², un-guardable by construction) enters
at ranks 8–9 (N = 60: 0.1155¢, N = 59: 0.1195¢) — below ~0.1¢ the
first-lock metric measures near-coincidence numerology, not triadic
quality; the grid counts are the robust lens.

**H-E4 — KEPT.** All 59 N-EDOs under frozen melodic v0.1.0: strictly
proper, constant structure, 1 gap class, exactly 0.0 bits entropy;
gap_classes/N = 1/N recorded per row for the program's Pareto axes.

**Rails — all KEPT.** R-DUAL: P = S exactly at every (N, ε) measured and
every lock (anchored self-duality on inversionally-symmetric scales,
again). R-G0: at ε = 1e−6¢, P = S = 0 and G = N·⌊N/2⌋ for every N. The
12-EDO grid pin P = S = [0, 12, 24, 24, 24, 48, 48] at
ε = [1, 2, 3, 5, 10, 14.86, 20] measured exactly as registered — the
3-and-5¢ entries are the guard-window (1,1) chromatic cluster, on record
as scorer behavior: C♯–D–D♯ counts as a proportional AND subcontrary
triad for ε ∈ (2.887, 5.773].

**Post-hoc (not registered, labeled).** (1) The accidental early locks
are near-exact arithmetic-progression chords in the teens limit:
50-EDO's (9,8) ≈ **15:17:19** (0.0085¢ from exact AM), 39-EDO's (8,7) ≈
13:15:17, 45-EDO's (25,18) ≈ 17:25:33 — ET numerology keeps landing on
AP chords Wilson's exact path would classify at zero tolerance. (2)
31-EDO's first asymmetric lock is the SEPTIMAL 6:7:8-type (7,6) at
1.1345¢ — the huygens host announces its 7-limit before its 5-limit
(4:5:6 at 3.89¢). (3) Raw grid counts at fixed ε grow superlinearly with
N (53-EDO P@2¢ = 424 vs 12-EDO's 12; N = 58 tops P@2¢ at 696); per-N or
per-type normalization is the right lens for cross-N comparison and is
left to the ET-002 join, which has the per-row tables it needs.

**Kept.** Runner and receipts stand; both frozen scorers untouched (pins
re-verified post-run). Gate G-017 appended to experiments/GATES.md
(PENDING, Marcus's review).

**Run receipt:** 2026-08-09, python3.12 — lattice suite 130/130 OK
(25 melodic + 12 shadow001 + 18 moslat001 + 22 bridge001 + 37 moslat002
+ 16 et001), freeze checks A OK on both pins (scorer 1a840af9…9b592,
melodic a16f162b…7535) before and after. Receipts bit-identical across
two runs (diff on et001.jsonl and et001_summary.json).

## 2026-08-18 — ET-002 pre-registration (entry BEFORE any implementation or run)

**Question:** the subset census of 12-EDO under the frozen scorers. Enumerate
every non-empty pitch-class set of Z12 up to TRANSPOSITION (Pólya:
(1/12)·Σ_{d|12} φ(d)·2^{12/d} = 4224/12 = 352 classes incl. empty and full ⇒
**351 non-empty**; per-size histogram 1, 6, 19, 43, 66, 80, 66, 43, 19, 6,
1, 1 for N = 1..12 — pinned in a test) and score each class on the melodic
side with frozen `melodic.py` v0.1.0 (`score_melodic`, defaults: propriety
class + violations, CS + violations, gap classes, gap_classes/N, entropy;
step-pattern word recorded alongside) and on the harmonic side with frozen
`triads/scorer.py` v1.1.0 (`score_tempered`, PRIMARY anchored convention,
default max_span 1200¢) at the ET-001 ε grid **{1, 2, 3, 5, 10, 14.86,
20}¢** — P, S, G, raw counts, and the G-002 balance bucket (verbatim copy of
`triads/search.py::balance_bucket`, cross-checked by a test) per (class, ε).
NOT a min(P,S) ranking. Secondary keys per row: the T/I class (lexmin over
transpositions of the set and its inversion, plus the Rahn prime form for
readability; 223 non-empty T/I classes — pinned), `is_inversionally_symmetric`
(predicted 95 of 351: 2·224 − 352 = 96 incl. empty), transposition period
(limited-transposition flag; 16 non-empty classes with period < 12), interval
vector, and tags for the well-known scales. Runner `et002.py`; receipts
`results/et002.jsonl` (351 rows) + `results/et002_summary.json`; tests
`tests/test_et002.py` green before the first run; stdlib only, python3.12,
deterministic, no wall-clock fields; two runs bit-identical (diff recorded).

**Canonical forms (locked).** T-class representative = lexicographically
smallest sorted 12-tuple-transposition of the set (so the diatonic is
(0,1,3,5,6,8,10) — Locrian at 0); cents = 100·pc. Step word = the
lexicographically smallest rotation of the circular gap sequence (necklace
representative; diatonic → "1221222"). Tags are by class membership, so
"diatonic 2212221", pentatonic, whole-tone (Messiaen 1), octatonic
(Messiaen 2), hexatonic/augmented scale, Messiaen 3–7 (all seven modes are
tagged; the four modes 1–4 named in the brief are among them, and the
limited-transposition FLAG covers the general concept), melodic and harmonic
minor, harmonic major, chromatic, major/minor/augmented/diminished triads,
sus (0,2,7) trichord, dominant and diminished sevenths, power chord (0,7),
tritone (0,6), Guidonian hexachord — are looked up, not searched.

**Analytic mirror (the algebra the run must check; the frozen scorer is the
referee, the mirror is not; independent integer combinatorics in scratch, no
frozen-scorer or melodic.py calls).** Every subset lives inside 12-EDO, so a
triple at anchor b is a 12-EDO type (p, q) with b − p and b + q in the set;
ET-001's 12-EDO type table therefore decides everything. Types with
proportional deviation < 20¢: (7,5) 1.9550 [sep 203.9], (1,1) 2.8865
[sep 5.7730], (5,4) 7.8374 [sep 115.7], (2,2) 11.5268 [sep 23.0537],
(4,3) 14.8590 [sep 70.28]; nothing else below (3,3) at 25.86¢. A type counts
on (dev, sep], so at the grid the qualifying P-types are: ε=1: none; ε=2:
(7,5); ε=3, 5: (1,1), (7,5); ε=10: (5,4), (7,5); ε=14.86, 20: (2,2), (4,3),
(5,4), (7,5); S-types are the transposes (q,p). Because p + q = 12 makes a
and c the SAME pitch class, the (7,5) power chord counts one triple per
ordered fourth (b, b+5): **P@2 = S@2 = ic5 (interval-vector entry 5) for
every class**. Pattern identities: (1,1) counts chromatic-trichord middles
c111 = #{b: b±1 ∈ S}; (4,3) counts each major-triad pc-set {r, r+4, r+7}
once (anchor = its third) and (5,4) counts the SAME set again (anchor = its
fifth; 3:4:5 voicing, deviation 7.84¢ < the root-position 14.86¢); (2,2)
counts whole-tone trichords WT3 = #{x, x+2, x+4} ⊂ S; duals count minor
triads {r, r+3, r+7} twice ((3,4) root, (4,5) first inversion 12:15:20).
Hence for every class:
  P@1 = 0; P@2 = ic5; P@3 = P@5 = ic5 + c111; P@10 = ic5 + Maj;
  P@14.86 = P@20 = ic5 + 2·Maj + WT3;   S likewise with Min.
So **Maj = P@10 − P@2 and Min = S@10 − S@2 are derivable from the frozen
scorer's own grid** (recorded as derived fields). G-types are the symmetric
(p,p) with dev_G = 0: G@1..5 = Σ_{p=1..6} m(p,p); G@10..20 drops p = 1
(sep 5.77) — full 12: G = [72,72,72,72,60,60,60] (ET-001's N·⌊N/2⌋ at ε→0).
The 12-EDO cluster floor of ET-001 (C♯–D–D♯ counted for ε ∈ (2.887, 5.773])
is inherited: counts are NOT monotone in ε — the mirror predicts **105
classes with P@10 < P@5** (guard exit of the (1,1) cluster).

**Falsifiable predictions (numbers from the mirror, to be confirmed or
refuted by the frozen scorers on all 351 classes):**
- **H-T1 (cultural epsilon inherited).** At ε = 1¢ every class has
  P = S = 0 (351/351). At ε = 2¢ exactly the classes with ic5 > 0 have
  P > 0: **321 of 351** (the 30 fifth-free classes: 1/5/10/10/3/1 at
  N = 1..6 — M5-images of the adjacent-semitone-free necklaces). At
  ε = 3 and 5¢ **327** classes have P > 0: the 321 plus exactly the six
  fifth-free classes containing a chromatic trichord — (0,1,2), (0,1,2,3),
  (0,1,2,4), (0,1,2,10), (0,1,2,3,4), (0,1,2,4,10). At ε = 10¢: 321 again
  (cluster dropped, no new fifth-free winners because a major triad
  contains a fifth); at 14.86/20¢: **330** (whole-tone trichords admit
  fifth-free classes such as (0,2,4)). P = S in all 351 classes for
  ε ≤ 5 (ic5 and c111 are inversion-invariant) and in exactly **231**
  classes at ε ∈ {10, 14.86, 20}; the census's N = 12 row must reproduce
  ET-001's P = S = [0, 12, 24, 24, 24, 48, 48] EXACTLY (rail). Predicted
  balance buckets at 14.86¢: diagonal 231, skew_P/S 31/31, strong_P/S
  28/28, near_P/S 1/1.
- **H-T2 (diatonic distinction).** (a) NOT CS (one violating class, the
  600¢ tritone at 3 and 4 steps — the SPEC correction on record); (b)
  proper but NOT strictly (span-3 max = span-4 min = 600¢); (c) at
  ε = 14.86¢ the diatonic scores **P = S = 15** = 6 power chords + 3 major
  triads × 2 voicings (root anchor (4,3) + second-inversion anchor (5,4)) +
  3 whole-tone trichords (C-D-E, F-G-A, G-A-B); grid P = S =
  [0, 6, 6, 6, 9, 15, 15]. Among the 66 seven-note classes the diatonic
  is the UNIQUE maximum of P + S (30; runner-up 26 = the improper
  (0,1,2,3,5,7,10)/(0,1,2,3,5,8,10) pair at (12,14)/(14,12)) and of P
  alone and S alone (15): **zero 7-note classes tie or beat it** under the
  scorer. HOWEVER, in the raw "number of major + minor triad pc-sets"
  sense (Maj + Min derived as above) the literal claim is predicted
  **REFUTED**: two hexatonic-plus-one classes, (0,1,2,5,6,9,10) and
  (0,1,2,4,5,8,9), carry 7 triads (4+3 / 3+4) against the diatonic's 6 —
  the diatonic wins the scorer's P + S only because it also carries the
  most fifths (ic5 = 6, the 7-note maximum, uniquely) and 3 whole-tone
  trichords. Both halves are registered; the receipts decide both.
- **H-T3 (propriety census).** Predicted over the 351 classes: strictly
  proper **23** (6.6%), proper **46** (13.1%), improper **282** (80.3%);
  CS **51** (14.5%). Per N (sp/p/imp): 1: 1/0/0; 2: 6/0/0; 3: 4/5/10;
  4: 7/6/30; 5: 1/9/56; 6: 2/11/67; 7: 0/5/61; 8: 1/4/38; 9: 0/3/16;
  10: 0/2/4; 11: 0/1/0; 12: 1/0/0. The 23 strictly proper classes are
  exactly: the 7 classes with N ≤ 2, (0,2,7), (0,3,7), (0,3,8), (0,4,8),
  (0,1,5,8), (0,1,6,7), (0,2,5,8), (0,2,5,9), (0,2,6,8), (0,2,6,9),
  (0,3,6,9), the pentatonic, the hexatonic, the whole-tone, the octatonic,
  and the chromatic — the pentatonic is the ONLY strictly proper 5-note
  class and NO 7-note class is strictly proper (Rothenberg: 12-EDO's 7-note
  MOS is only proper, and every other heptad is improper or proper).
  Max gap_classes/N = **1.0**, attained by all 32 classes with pairwise
  distinct gaps (N ≤ 4: sums 1+11, …, 1+2+9, …, 1+2+3+6, 1+2+4+5); for
  N ≥ 5 distinct gaps are impossible (1+2+3+4+5 > 12) so the max is 4/5.
  Melodic-side rails: gap classes and CS/propriety at 100¢ multiples are
  ε-independent (0.5¢ / 1e−9¢ guards inert), so the frozen results must
  equal the integer mirror row for row.
- **H-T4 (Pareto).** Frontier defined per cardinality N: classes not
  dominated on (gap_class_count ↓, P + S at 14.86¢ ↑) among classes of
  the same N (a global frontier is degenerate — the chromatic scale wins
  both axes, ET-001's degenerate-melody corner). Predicted union: **24
  classes**, including the diatonic (N=7, uniquely), the pentatonic
  (N=5, gc 2, P+S 14), whole-tone + hexatonic + the Guidonian hexachord
  (0,2,4,5,7,9) (N=6; the hexachord tops N=6 with P+S = 22), Messiaen 3
  (tops N=9 at 48), the chromatic (N=12), the sus trichord and augmented
  triad (N=3) — while the major and minor triads are NOT on it (P+S = 4
  tied by (0,2,7) at fewer gap classes) and the **octatonic is NOT on it**
  (P+S 32 < 38 at N=8, both gc 2). **Six improper classes ARE on the
  frontier**: (0,1,2,7), (0,2,4,6), (0,2,4,7), (0,2,4,9) at N=4, the
  bebop-dominant-type (0,1,2,3,5,7,8,10) at N=8 (P+S 38, the N=8 maximum),
  and (0,1,2,3,4,5,6,8,9,10) at N=10 — improper-but-valid spice, reported
  not zeroed. Proper-or-better frontier: 19 classes (post-hoc-free lens,
  also registered).
- **Rails.** R-DUAL: P = S at every ε for all 95 inversionally symmetric
  classes, and P(S) = S(−S) for every asymmetric pair (anchored scorer
  commutes with inversion). R-12: N = 12 row = ET-001 grid. R-G: G grid
  matches the symmetric-type mirror for every class. R-MEL: melodic
  results equal the integer mirror row for row (351/351).

**Constants (locked):** ε grid {1, 2, 3, 5, 10, 14.86, 20}¢; scorer
default max_span 1200¢; melodic defaults; frontier lens (gc, P+S@14.86)
per N; no other tunables. Scale: 351 × 7 = 2457 scorer calls + 351 melodic
calls; seconds. Anything not predicted above lands in clearly labeled
post-hoc fields.

**Archive context (read in place, cited by path+page):**
`2010_02_24B/12&17/BasicPttnsGenus12&17.pdf` pp.1–3 — Wilson, "Some Basic
Patterns Underlying Genus 12 & 17" (©1980, reprinted 1981/1983): the
12-tone genus is the Pythagorean major (diatonic) modulated through the six
keys E A D G C F, with 12-Equal drawn as one point of the meantone
continuum (p.2), and the just diatonic modulated through the same keys
yielding the 17-tone genus (p.3). Wilson's framing of 12 as the diatonic's
transposition closure is exactly the object this census tests: which of the
351 subsets the frozen scorers single out, and whether the diatonic is it.

**Post-run obligations:** results entry here with per-hypothesis
KEPT/REFUTED, FINDINGS.md paragraph, PR on research/et-002 stacked on #38;
gate G-019 lives in the consolidated ledger PR #37 (GATES.md NOT edited
here; proposed row text in the PR body).

## 2026-08-18 — ET-002 results + verdicts

**Run:** `et002.py` (~0.5 s, 2457 scorer calls + 351 melodic calls,
receipts bit-identical across two runs by diff on both files),
`results/et002.jsonl` (351 rows, one per T-class) +
`results/et002_summary.json`. Scorer v1.1.0, melodic v0.1.0, lattice suite
155/155 green pre-run (25 new et002 tests), freeze checks A OK on both
pins before and after. One runner fix between the first and second
invocation: the H-T1 verdict compared a sorted list of classes against an
unsorted literal (a comparison bug in the verdict code, not a prediction
change) — the receipts themselves were identical before and after the fix.
Enumeration rails as pinned: 351 T-classes with size histogram
1/6/19/43/66/80/66/43/19/6/1/1, 223 T/I classes, 95 inversionally
symmetric classes, 16 limited-transposition classes.

**Mirror rails — all KEPT, 351/351.** The pattern-count mirror (12-EDO
type table × embedded-pattern counts) agrees with the frozen scorer on P,
S AND G at every one of the 2457 (class, ε) points; the integer melodic
mirror agrees with frozen melodic.py on propriety class, violation counts,
CS and gap classes for every class. P = S at every ε for all 95 symmetric
classes; P(S) = S(−S) for every asymmetric pair. The N = 12 row reproduces
ET-001's P = S = [0, 12, 24, 24, 24, 48, 48] exactly.

**H-T1 — KEPT. The cultural epsilon is inherited by every subset, and the
whole harmonic side of 12-EDO at ε ≤ 20¢ is five patterns.** At ε = 1¢ all
351 classes score P = S = 0. At ε = 2¢ P = S = ic5 (interval-vector entry 5)
for every class — the 2:3:4 power chord is the ONLY triad type alive there —
so exactly the 321 fifth-bearing classes have P > 0 and the 30 fifth-free
classes (1/5/10/10/3/1 at N = 1..6) do not. At 3 and 5¢ the guard-window
chromatic cluster (C♯–D–D♯, ET-001) enters and 327 classes are positive:
the six new ones are precisely the fifth-free clusters (0,1,2), (0,1,2,3),
(0,1,2,4), (0,1,2,10), (0,1,2,3,4), (0,1,2,4,10). At 10¢ the cluster is
guard-dropped and the second-inversion major (3:4:5-type, 7.84¢) arrives:
321 classes; **105 classes have P@10 < P@5** (counts are not monotone in
ε — the ET-001 cluster floor, now census-wide). At 14.86/20¢ the root
major (4:5:6, 14.859¢) and the whole-tone trichord (2,2) arrive: 330
classes positive. P = S in all 351 classes for ε ≤ 5¢ and in exactly 231
for ε ≥ 10¢; balance buckets at 14.86¢: diagonal 231, skew 31/31, strong
28/28, near 1/1 — every number as pre-registered. Reporting identity: for
every class P@14.86 = ic5 + 2·Maj + WT3 and S@14.86 = ic5 + 2·Min + WT3
(each major triad is counted twice — root anchor and second-inversion
anchor — never in first inversion), so **Maj = P@10 − P@2 and
Min = S@10 − S@2 are readable straight off the frozen grid**.

**H-T2 — KEPT in the scorer's sense; the literal raw-triad maximum
REFUTED exactly as pre-registered.** The diatonic (0,1,3,5,6,8,10),
step word 1221222: NOT CS (1 violating class, the tritone at 3 and 4
steps), proper but not strictly (600¢ contact), grid P = S =
[0, 6, 6, 6, 9, 15, 15], derived Maj = Min = 3, WT3 = 3, ic5 = 6. Among
the 66 seven-note classes it is the UNIQUE maximum of P + S (30; runner-up
26), of P alone and of S alone (15) — **zero classes tie or beat it** —
and it is the only 7-note class on the (gc, P+S) frontier. But on raw
Maj + Min it is NOT the maximum: the two hexatonic-plus-one classes
(0,1,2,5,6,9,10) and (0,1,2,4,5,8,9) carry 7 triads (4+3 / 3+4) against
the diatonic's 6, and lose to it under the scorer only because the
diatonic also holds the 7-note maximum of fifths (ic5 = 6, unique) and
three whole-tone trichords. The scorer's "diatonic distinction" is
therefore a statement about triads + fifths + stepwise-thirds
together, not about triad count alone — worth remembering when the
aggregator is designed.

**H-T3 — KEPT.** Over the 351 classes: strictly proper 23 (6.6%), proper
46 (13.1%), improper 282 (80.3%); CS 51 (14.5%); the 23 strictly proper
classes are exactly the pre-registered list (7 with N ≤ 2; (0,2,7),
(0,3,7), (0,3,8), (0,4,8); seven tetrads incl. the diminished seventh;
pentatonic; hexatonic; whole-tone; octatonic; chromatic). The pentatonic
is the ONLY strictly proper 5-note class; NO 7-note class is strictly
proper (5 proper, 61 improper); no 7-, 9-, 10- or 11-note class is CS.
Max gap_classes/N = 1.0, attained by all 32 distinct-gap classes
(N ≤ 4); for N ≥ 5 the maximum is 4/5.

**H-T4 — KEPT.** The per-N frontier on (gap classes ↓, P + S at 14.86¢ ↑)
has 24 members (19 proper-or-better): the diatonic (N=7), pentatonic
(N=5), whole-tone + hexatonic + the Guidonian hexachord (N=6; the
hexachord tops N=6 at 22), Messiaen mode 3 (tops N=9 at 48), the
chromatic (N=12), the sus trichord and augmented triad (N=3), the
diminished seventh, and neither the major nor the minor triad (P+S = 4,
tied by (0,2,7) at fewer gap classes) nor the octatonic (32 < 38 at N=8,
both gc 2). Six improper classes ARE on the frontier: (0,1,2,7),
(0,2,4,6), (0,2,4,7), (0,2,4,9) at N=4, (0,1,2,3,5,7,8,10) at N=8 and
(0,1,2,3,4,5,6,8,9,10) at N=10 — reported, not zeroed, per the
improper-but-valid doctrine.

**Post-hoc (not registered, labeled).** (1) The N = 8 frontier winner
(0,1,2,3,5,7,8,10) [11122122] is the **bebop dominant** scale
(C D E F G A B♭ B): P = S = 19 (7 fifths, 4 major, 4 minor, 4 whole-tone
trichords), improper; the only PROPER 8-note superset of the diatonic is
(0,1,2,4,5,7,9,10) [11212212] = the **bebop major** (C D E F G A♭ A B),
P = S = 17, which tops the proper-only frontier at N = 8 and, at 4.25
(P+S)/N, is second only to the diatonic (4.29) among proper 5–8-note
classes — jazz practice's two chromatic-passing-tone scales are the
census's top-8 objects. (2) Balance-bucket winners at 14.86¢ (G-002
contract): strong_P is led by (0,1,3,5,8,9) [122313] = D♭–F–A♭ major
triads chained by fourths plus one minor (P,S) = (10,6), proper; its
inversion leads strong_S; the near_P/near_S singletons are the 9-note
pair (0,1,2,3,5,6,8,9,10)/(0,1,2,3,5,6,7,9,10) at (23,21)/(21,23); the
diagonal is 231 classes deep and its size-stratified tops ARE the frontier
above. (3) The whole-tone scale scores P = S = 6 at 14.86¢ entirely from
the symmetric (2,2) trichord in its guard window (11.53, 23.05] — a
census-wide reminder that ε ≥ 11.53¢ admits augmented-flavoured
"proportional" whole-tone trichords in any scale that has them, which is
what makes the diatonic's 15 rather than 12. (4) The six 10-note classes are the
chromatic minus one dyad, indexed by that dyad's interval class: deleting
an ic5 (fourth) or ic6 (tritone) dyad leaves a PROPER class, deleting
ic1–ic4 leaves an IMPROPER one; the two frontier members at N = 10 are the
ic4- and ic5-deletions (both P = S = 29), one improper and one proper —
near-chromatic propriety hinges on which dyad is removed.

**Kept.** Runner and receipts stand; both frozen scorers untouched (pins
re-verified post-run). Gate G-019 is queued in the consolidated ledger
(PR #37); GATES.md not edited here.

**Run receipt:** 2026-08-18, python3.12 — lattice suite 155/155 OK
(25 melodic + 12 shadow001 + 18 moslat001 + 22 bridge001 + 37 moslat002
+ 16 et001 + 25 et002), freeze checks A OK on both pins (scorer
1a840af9…9b592, melodic a16f162b…7535) before and after. Receipts
bit-identical across two runs (diff on et002.jsonl and et002_summary.json).

## 2026-08-19 — ET-003 pre-registration (entry BEFORE any implementation or run)

**Question:** the comma-kernel history of 12-EDO, made falsifiable under the
frozen scorers. The 11-limit patent val V12 = ⟨12, 19, 28, 34, 42⟩ has a
kernel; European practice walked INTO that kernel one comma at a time. Four
fixed stages, all sharing the SAME val/addressing (12 degrees, fifth = 7
steps), differing only in the lift (tuning map):
- **S1 Pythagorean 12** — chain of pure fifths (1200·log₂(3/2) =
  701.955001¢), chain positions −5..+6, octave-reduced; wolf G♯–E♭ =
  678.494990¢ (= pure fifth − Pythagorean comma).
- **S2 quarter-comma meantone 12** — fifth = 300·log₂5 = 696.578428¢
  (major third exactly 5/4 by construction), chain −5..+6; wolf G♯–E♭ =
  8400 − 11·f = 737.637287¢.
- **S3 Werckmeister III** — Andreas Werckmeister, *Musicalische
  Temperatur* (Quedlinburg, 1691), "Correct Temperament No. 1": fifths
  C–G, G–D, D–A, B–F♯ narrowed by 1/4 Pythagorean comma
  (PC = 1200·(12·log₂(3/2) − 7) = 23.460010¢; tempered fifth
  696.089998¢), all eight other fifths pure; circle closes exactly
  (8·P + 4·T = 8400 by construction). Cents table (from C, locked in the
  runner as the constant table): 0, 90.225, 192.180, 294.135, 390.225,
  498.045, 588.270, 696.090, 792.180, 888.270, 996.090, 1092.180 —
  matches Barbour, *Tuning and Temperament* (1951). Circle-of-fifths
  word from C: T T T P P T P P P P P P.
- **S4 12-EDO** — degrees k·100¢ (ET-001 rails apply).

Runner `et003.py`; receipts `results/et003.jsonl` (7 rows: 4 stages + 3
kernel-census rows) + `results/et003_summary.json`. Tests
`tests/test_et003.py` green before the first run. Frozen scorers: triads
v1.1.0 (`score_tempered`, PRIMARY anchored convention, default max_span
1200¢) and melodic v0.1.0 (`score_melodic`, defaults). ε grid
{1, 2, 3, 5, 10, 14.86, 20}¢ (ET-001's). Stdlib only, python3.12,
deterministic, no wall-clock fields; two runs bit-identical (diff
recorded). Comma enumeration and val arithmetic adapted from
`bridge001.py` (copy-with-attribution, generalized to per-limit prime
lists). Analytic mirror: an independent reimplementation of the anchored
classification formulas (ET-001 method, extended off-EDO: enumerate all
anchored triples of each 12-tone scale, per-triple deviation dev and
guard separation sep, count on the half-open interval (dev, sep]); the
frozen scorer is the referee at every grid point AND at every distinct
lock value ± δ (δ = 1e−6¢, tie clustering 1e−9¢). Scratch derivation for
everything below used independent formulas only — no frozen-scorer calls.

**H-K1 (kernel census).** Boxes: |e3| ≤ 12, |e5| ≤ 5, |e7| ≤ 4,
|e11| ≤ 3 (BRIDGE-001 box widened e3 8→12 SOLELY to admit the
Pythagorean comma, the historical comma of 12 — deviation flagged here),
0 < cents < 60, primitive, Tenney height n·d ≤ 2⁴⁰; kernel test
v(c) = 0 against the patent val truncations ⟨12,19,28⟩ / ⟨12,19,28,34⟩ /
⟨12,19,28,34,42⟩. Predicted counts: **5-limit exactly 5 members** —
81/80 (21.5063¢), 128/125 (41.0589¢), 2048/2025 (19.5526¢),
32805/32768 (1.9537¢), 531441/524288 (23.4600¢); **7-limit 29**
(the 5 plus 36/35, 50/49, 64/63, 126/125, 225/224, 3136/3125, 5120/5103,
4000/3969, … full list in receipts); **11-limit 122**. Non-members
predicted (derived, contradicting the naive reading list): **33/32 is
NOT in the kernel** (V12(33/32) = 1 step) and neither is 121/120
(V12 = 1) — the D'Alessandro commas do not transfer to 12. Cross-rails
(pinned in tests): (a) the 5-limit kernel of ⟨12,19,28⟩ is exactly
sat⟨81/80, 128/125⟩ — the vector cross product of their monzos is
−⟨12,19,28⟩ ITSELF (minor gcd 1 ⇒ saturated): "12-EDO is the unique
temperament killing both 81/80 and 128/125" as one integer identity;
(b) all five 5-limit members are (81/80)^a·(128/125)^b:
Pythagorean comma = (81/80)³/(128/125), diaschisma = (128/125)/(81/80),
schisma = (81/80)²/(128/125).

**H-K2 (the walk gains triads — grid tables, all scorer-refereed).**
Predicted (P, S) per stage at the grid ε = [1, 2, 3, 5, 10, 14.86, 20]:
- S1 Pythagorean: P = S = **[11, 19, 21, 19, 20, 37, 46]**,
  G = [30, 30, 30, 28, 28, 28, 28].
- S2 meantone: P = S = **[2, 2, 10, 28, 39, 47, 48]**,
  G = [30, 30, 30, 30, 28, 28, 28].
- S3 Werckmeister III: P = **[10, 10, 14, 18, 28, 40, 48]**,
  S = **[9, 9, 14, 19, 28, 40, 46]**, G = [20, 20, 20, 20, 39, 55, 58].
- S4 12-EDO: P = S = [0, 12, 24, 24, 24, 48, 48] (ET-001 rail, must
  reproduce exactly).
At the two named points: (P,S)@2¢ = S1 (19,19), S2 (2,2), S3 (10,9),
S4 (12,12); (P,S)@14.86¢ = S1 (37,37), S2 (47,47), S3 (40,40),
S4 (48,48). Predicted P-ordering per ε: ε=1: S1 > S3 > S2 > S4;
ε=2: S1 > S4 > S3 > S2; ε=3: S4 > S1 > S3 > S2 (12-EDO's rank-1 here is
the (1,1) chromatic-cluster guard-window artifact on record since
ET-001 — excluding (1,1)-type triples S1 wins); ε=5: S2 > S4 > S1 > S3;
ε=10: S2 > S3 > S4 > S1; ε=14.86: S4 > S2 > S3 > S1 (12-EDO wins by ONE
triple over meantone, 48 vs 47); ε=20: S4 = S2 = S3-on-P at 48 > S1.
So **12-EDO tops the P column only at ε ≥ 14.86** (modulo the ε=3
artifact) — the cultural-epsilon reading of ET-001, now historical.
First-lock spectrum heads (each verified at ±δ):
- S1: 0.0000¢ ×11 (power chords on the 11 pure fifths — dev exactly 0),
  then 1.0851 ×2 (schismatic 8:9:10: 9/8 below, Pyth dim3 65536/59049
  above), 1.2208 ×3 (schismatic major, 2nd inversion), **1.9537 ×3
  (schismatic major 4:5:6, root position: dev = EXACTLY the schisma —
  fa=1/1, fc=3/2 pure makes AM = 5/4 exactly, so dev =
  1200·log₂((5/4)/(8192/6561)) = 1200·log₂(32805/32768))**, 2.3500 ×2
  (limma-cluster, guard window (2.35, 4.70] — enters at 3, exits by 5),
  9.9873 ×1 (wolf-fifth schismatic major, 2nd inv), 11.9809 ×8
  (whole-tone trichord ±203.91), 12.0841 ×1 (wolf-fifth schismatic
  major, root), 13.4727 ×8 (ditone major 2nd inv: dev = EXACTLY
  1200·log₂(129/128), AM = (3/4 + 81/64)/2 = 129/128), 15.1499 ×3,
  **19.5526 ×6 (dim5-below + ditone-above pattern: dev = EXACTLY the
  diaschisma, AM/fb = 2025/2048)**. The Pythagorean ROOT-position ditone
  major sits at dev = EXACTLY 1200·log₂(81/80) = 21.5063 — never locks
  at ε ≤ 20: **the syntonic comma is visible as a triadic deviation the
  grid cannot reach**.
- S2: **0.7394 ×2 — meantone-12's FIRST lock is SEPTIMAL: the 6:7:8
  triple (aug-2nd 269.206¢ ≈ 7/6 below, dim-3rd 234.216¢ ≈ 8/7 above),
  locking below 1¢, so P@1 = 2 while 12-EDO's P@1 = 0.** Then 2.0143 ×8
  (major 2nd inv), 3.2239 ×8 (major 4:5:6 root), 3.6029 ×3 (5:6:7),
  3.8634 ×4 (5:7:9), 3.9578 ×2 (semitone cluster, window (3.96, 7.92]),
  4.2404 ×1, 5.3766 ×11 (power chords: dev = the quarter syntonic comma
  exactly), 7.3751 ×2 (7:8:9), 10.7531 ×8 (whole-tone ±193.16, window
  (10.75, 21.51]), 19.5614 ×1 (the G♯ double-wolf major — dim4 third +
  wolf fifth partially cancel back under 20¢).
- S3: 0.0 ×8 (pure fifths), 0.1021 ×1 (accidental near-exact cluster,
  window-bound), **0.2516 ×1 — Werckmeister III's C major in second
  inversion is 0.25¢ from exact proportionality**, 2.4456 ×1 (F major
  2nd inv), then the key-color ladder (full table below). Tempered
  fifths lock at exactly PC/4 = 5.8650 ×4.
- S4: 1.9550 ×12, 2.8865 ×12, 7.8374 ×12, 11.5268 ×12, 14.8590 ×12
  (ET-001 rail).
Wolf power chords never lock: S1 wolf dev = PC = 23.4600 exactly;
S2 wolf dev = 35.6820¢.
Duality rails: P = S at every ε for S1, S2, S4 (chain scales: inversion
= transposition; the anchored scorer commutes with both). **S3 is the
ONLY stage with P ≠ S** — its circle-of-fifths word TTTPPTPPPPPP is
chirally asymmetric (its reversal is not a rotation), predicted split:
(P,S) = (10,9) at ε=1 and 2, (18,19) at 5, (48,46) at 20, equal at
3, 10, 14.86. A well-temperament has a HANDEDNESS the frozen scorer can
see; neither the Pythagorean, meantone, nor equal lifts have one.

**H-K3 (melodic cost of the walk — frozen melodic v0.1.0 vs pinned
predictions).** Predicted per stage (propriety, CS violations,
gap classes, gap multiset ¢×count, entropy bits):
- S1: strictly proper (SPEC rail, test_melodic pin), CS (0 violations),
  2 gap classes {90.225×7, 113.685×5}, entropy 0.979869.
- S2: strictly proper, CS, 2 gap classes {76.049×5, 117.108×7},
  entropy 0.979869 (same 7-5 shape as S1: both are 12-note MOS of one
  generator; only the L/s ratio differs — 1.260 vs 1.540).
- S3: strictly proper, CS, **4 gap classes** {90.225×2, 96.090×4,
  101.955×2, 107.820×4}, entropy 1.918296 — the MELODIC-COMPLEXITY
  MAXIMUM of the walk.
- S4: strictly proper, CS, 1 gap class {100×12}, entropy 0.
**The monotone-uniformity story is predicted REFUTED**: gap classes run
2 → 2 → 4 → 1 and entropy 0.98 → 0.98 → 1.92 → 0 — history's melodic
complexity is a HUMP peaking at the well-temperament, not a monotone
descent into 12-EDO; and propriety was never traded at all (all four
stages strictly proper, all four CS). Step-size spread (max−min gap) is
also non-monotone: 23.460 (=PC) → 41.059 (=128/125, the meantone
maximum) → 17.595 → 0.

**H-K4 (which comma buys which triad).** Exact-identity claims (tests,
1e−9): S1 root ditone-major dev = 1200·log₂(81/80); S1 schismatic-major
root dev = 1200·log₂(32805/32768); S1 dim5+ditone dev =
1200·log₂(2048/2025); S2 wrapped ("wolf") third = dim4 = 32/25 exactly,
error vs 5/4 = 1200·log₂(128/125) exactly; S1 wolf-power-chord dev =
1200·log₂(531441/524288). Address censuses (per-address best-voicing
deviation, verified against the lock spectra): major-triad addresses
covered at ε, predicted table (stage: @2, @3, @5, @10, @14.86, @20):
S1: 3, 3, 3, 4, **12**, 12; S2: 0, 8, 8, 8, **8**, 9; S3: 1, 2, 4, 9,
**12**, 12; S4: 0, 0, 0, 12, **12**, 12. Minor-address coverage
predicted IDENTICAL row for row. Verdict claims:
- **81/80 alone does NOT buy all of 12-EDO's Maj/Min addresses —
  predicted NO** (the task's concrete question): a 12-note 81/80 chain
  covers exactly 8 of 12 (roots at chain −5..+2); the 4 missing roots'
  thirds wrap the chain to the dim4 = 32/25, off 5/4 by exactly the
  UNtempered 128/125. Tempering 128/125 too (S2 → S4) buys those 4
  addresses AND the 12th power chord (wolf → fifth): enharmonic closure
  is 128/125's purchase, exactly as the generalized-D'Alessandro
  framing prices it.
- The schisma 32805/32768 is S1's purchase: it puts 3 major addresses
  within 2¢ of exact proportionality centuries before meantone — the
  scorer sees medieval schismatic thirds as 12's first 5-limit triads.
- **The 7-limit kernel members buy NOTHING in 12-EDO at ε ≤ 20¢**:
  12-EDO's locked types are exactly the five ET-001 types, all with
  3- or 5-limit prototypes; predicted count of additional 12-EDO locks
  ≤ 20¢ = 0. The septimal action is in MEANTONE: its first lock
  (0.7394¢, 6:7:8) exists because 1/4-comma tempering happens to send
  A2 (just 75/64) within 2.34¢ of 7/6 and d3 (just 144/125) within
  3.05¢ of 8/7 — the mergers (75/64)/(7/6) = **225/224** and
  (144/125)/(8/7) = **126/125** (both V12 kernel members, both pinned
  as exact Fraction identities). The walk's last step S2/S3 → S4
  DESTROYS the sub-cent septimal lock (P@1: 2 → 0): **12-EDO forecloses
  the 7-limit door meantone had opened** — 64/63 and 50/49 are in V12's
  kernel but purchase no triad the grid can see.
**H-K5 (key color, pre-registered lens).** Werckmeister III's per-root
best-voicing major-triad deviation (the "key color" of 1691, now a
number): C 0.2516, F 2.4456, D = G 3.9273, B♭ 6.1166, B 7.6077,
E♭ = E = A 9.7924, C♯ = F♯ = G♯ 13.4727¢ (exactly 1200·log₂(129/128) —
those three roots carry a pure fifth + full Pythagorean ditone, S1's
second-inversion identity). Claims: (a) exactly 7 distinct values with
that multiset; (b) minimum at C — **W-III's C major is 31× closer to
exact proportionality than ANY 12-EDO major voicing** (0.2516 vs
7.8374¢); (c) even the worst key stays under the cultural epsilon,
which is WHY the coverage row hits 12 at 14.86 — "well-temperament =
every key usable, no key identical" as a theorem of the dev table;
(d) at ε = 5¢ the coverage ordering is S2 (8) > S3 (4) > S1 (3) >
S4 (0): **at tight tolerance, 12-EDO is the WORST major-triad machine
of the four stages — the endpoint of the walk pessimizes the 5-limit
and is redeemed only at its own 14.86¢ epsilon** (and at 14.86 meantone
is the only stage that fails closure, 8 < 12: the wolf's price).

**Constants (locked):** the four stage definitions above; ε grid
{1, 2, 3, 5, 10, 14.86, 20}¢; scorer default max_span 1200¢; melodic
defaults; δ = 1e−6¢; lock-tie clustering 1e−9¢; comma boxes as in H-K1;
no other tunables. Scale: ~28 grid calls + ~250 lock-verification calls
+ 8 melodic calls + census; seconds. Anything not predicted above lands
in clearly labeled post-hoc fields.

**Archive context (read in place, cited by path+page):**
`2010_02_24B/12&17/BasicPttnsGenus12&17.pdf` pp.1–3 (Wilson ©1980,
reprinted 1981/1983), already on record in ET-002: Wilson draws the
12-tone genus as the Pythagorean diatonic modulated through six keys
and **12-Equal as one point of the meantone continuum (p.2)** — the
meantone continuum IS the 81/80 line this experiment walks, S1 → S2 →
S4; ET-003 adds the frozen-scorer measurement of Wilson's picture, with
the well-temperament S3 as the off-continuum historical detour.

**Post-run obligations:** results entry here with per-hypothesis
KEPT/REFUTED, FINDINGS.md paragraph, PR on research/et-003 stacked on
research/et-002; gate G-024 lives in the consolidated ledger PR #37
(GATES.md NOT edited here; proposed row text in the PR body).

## 2026-08-19 — ET-003 results + verdicts

**Run:** `et003.py` (~0.35 s; 28 grid + 130 lock-verification frozen-scorer
calls + 4 frozen-melodic calls + the 3-limit census; receipts bit-identical
across two runs by diff on both files), receipts `results/et003.jsonl`
(7 rows: 3 kernel-census + 4 stage) + `results/et003_summary.json`. Scorer
v1.1.0, melodic v0.1.0, lattice suite 190/190 green pre-run (35 new et003
tests), freeze checks A OK on both pins before and after. One
verdict-comparison fix between the two invocation pairs: the H-K5 verdict
re-rounded receipt devs (stored at 6 dp) to 4 dp, double-rounding
3.9273497 → 3.92735 → 3.9274 against the pre-registered 4-dp literal
3.9273; replaced string-style equality with a 2e−4 value tolerance — a
comparison bug in the verdict code, not a prediction change (same class as
ET-002's H-T1 fix); the jsonl receipt rows carry no verdicts and are
unaffected. Mirror-vs-scorer: **zero failures at all 28 grid points and
all 130 lock-threshold ± δ points across the four stages** (25 + 24 + 71 +
10 ε points for S1/S2/S3/S4).

**H-K1 — KEPT, every number.** Kernel census within the pre-registered box:
5-limit exactly **5 members** — 81/80, 128/125, 2048/2025, 32805/32768,
531441/524288 (and the five are exactly the (81/80)^a·(128/125)^b lattice:
PC = (81/80)³/(128/125), diaschisma = (128/125)/(81/80), schisma =
(81/80)²/(128/125), pinned in tests); 7-limit **29** (head by Tenney
height: 36/35, 50/49, 64/63, 81/80, 126/125, 128/125, 225/224, 405/392,
2048/2025, 3125/3087, 3136/3125, 3645/3584, …); 11-limit **122**. The
cross-product rail held: monzo(81/80) × monzo(128/125) = −⟨12,19,28⟩ — the
Grassmann product of the two commas IS the val, so sat⟨81/80, 128/125⟩ is
the whole 5-limit kernel. As derived (against the naive reading list),
**33/32 and 121/120 are NOT kernel members** — V12 maps both to one step —
so the D'Alessandro commas do not transfer to 12.

**H-K2 — KEPT, grids exact.** All four grid tables measured exactly as
pre-registered, including the ET-001 rail row for S4 and the S3 chirality
split P = [10,10,14,18,28,40,48] vs S = [9,9,14,18→19,28,40,46]: P ≠ S at
ε ∈ {1, 2, 5, 20} exactly as predicted — **Werckmeister III is the only
stage with a handedness** (its fifth word TTTPPTPPPPPP is chirally
asymmetric; the sub-cent side shows it too: the 0.1021¢ accidental cluster
exists on the P side only). (P,S)@2¢ = S1 (19,19), S2 (2,2), S3 (10,9),
S4 (12,12); @14.86¢ = S1 (37,37), S2 (47,47), S3 (40,40), S4 (48,48). The
P-ordering per ε ran as registered: Pythagorean first at ε ≤ 2 (11 pure
fifths at dev 0; schismatic majors at exactly the schisma), meantone first
at 5–10¢, **12-EDO first only at ε ≥ 14.86 — and by ONE triple over
meantone (48 vs 47)**; the ε = 3 exception is 12-EDO's (1,1)
chromatic-cluster guard-window artifact, on record since ET-001. First
locks: S1 0.0¢ ×11; S2 **0.7394¢ ×2 — quarter-comma meantone's first lock
is the SEPTIMAL 6:7:8** (A2 ≈ 7/6, d3 ≈ 8/7), locking below 1¢ where
12-EDO has nothing; S3 0.0¢ ×8 then 0.1021, then **0.2516¢ — Werckmeister's
C major in second inversion**; S4 1.9550¢ ×12 (rail). Wolf power chords
never locked (S1 dev = PC exactly; S2 35.68¢).

**H-K3 — KEPT; the monotone-uniformity story REFUTED exactly as
registered.** Frozen melodic v0.1.0: all four stages strictly proper AND
constant structures (0 violations everywhere); gap classes walk
**2 → 2 → 4 → 1** with entropy 0.979869 → 0.979869 → 1.918296 → 0.0 bits
(runner's monotone_uniformity flag: False). History did not trade melodic
uniformity monotonically for 12-EDO's 1 gap class — the walk is a HUMP
with its melodic-complexity maximum at the well-temperament (4 step
sizes: 90.225×2, 96.090×4, 101.955×2, 107.820×4), and propriety was never
traded at all. Step-size spread is likewise non-monotone (23.46 → 41.06 →
17.60 → 0¢): meantone is the spread maximum (the untempered 128/125 IS
its wolf gap).

**H-K4 — KEPT.** Address censuses exact, minor ≡ major row for row.
Major-triad coverage (@2, 3, 5, 10, 14.86, 20¢): S1 = 3,3,3,4,**12**,12;
S2 = 0,8,8,8,**8**,9; S3 = 1,2,4,9,**12**,12; S4 = 0,0,0,12,**12**,12.
The registered attributions all held: **81/80 alone does NOT buy all of
12-EDO's triad addresses — a 12-note meantone chain covers exactly 8 of
12** (the four wrapped roots' thirds are the dim4 = 32/25 exactly, off 5/4
by exactly the untempered 128/125; test-pinned); **128/125 buys the
enharmonic closure** — the 4 wrapped addresses plus the 12th power chord;
the schisma bought S1 its 3 sub-2¢ major addresses centuries before
meantone; and **the 7-limit kernel members buy nothing in 12-EDO at
ε ≤ 20¢** — 12-EDO's locked types are exactly ET-001's five, while the
sub-cent septimal 6:7:8 that 225/224 + 126/125 hand to meantone
(Fraction identities (75/64)/(7/6) = 225/224, (144/125)/(8/7) = 126/125,
test-pinned) is DESTROYED by the last step of the walk: P@1 runs
2 → 0 from S2 to S4. Exact dev identities all verified to 1e−9: S1 root
ditone major = 1200·log₂(81/80); schismatic major root = the schisma;
dim5+ditone = the diaschisma; 2nd-inversion ditone = 1200·log₂(129/128);
S1 wolf power chord = the Pythagorean comma; S2 power chord = exactly a
quarter syntonic comma.

**H-K5 — KEPT (after the verdict-layer rounding fix above).** Werckmeister
key color measured as the predicted 12-value multiset: C 0.2516 < F 2.4456
< D = G 3.9273 < B♭ 6.1166 < B 7.6077 < E♭ = E = A 9.7924 < C♯ = F♯ = G♯
13.4727¢ (= 1200·log₂(129/128) exactly — pure fifth + full ditone, the S1
second-inversion identity). Seven distinct values; every key under the
cultural epsilon (hence coverage 12 at 14.86¢: "every key usable, no key
identical" as a dev-table theorem); **W-III's C major is 31× closer to
exact proportionality than any 12-EDO voicing** (0.2516 vs 7.8374¢). And
at ε = 5¢ the coverage ordering S2 (8) > S3 (4) > S1 (3) > **S4 (0)**
stands: at tight tolerance 12-EDO is the worst major-triad machine of the
four stages, redeemed only at its own 14.86¢ epsilon — while meantone is
the only stage that never closes the circle below 20¢ (8 < 12; its
double-wolf G♯ major surfaces alone at 19.5614¢).

**Post-hoc (labeled; nothing above depended on it).** The S3 receipts show
the S-side sub-cent régime differs from P not only in count but in kind:
the accidental 0.1021¢ P cluster (−101.96, +96.09 step pair) has no S
twin, so a listener-facing "handedness" claim would rest on sub-cent
proportional structure — flag for the EAR-ε program rather than for any
grid conclusion here.

**Kept.** Runner and receipts stand; both frozen scorers untouched (pins
re-verified post-run). Gate G-024 is queued in the consolidated ledger
(PR #37); GATES.md not edited here.

**Run receipt:** 2026-08-19, python3.12 — lattice suite 190/190 OK
(25 melodic + 12 shadow001 + 18 moslat001 + 22 bridge001 + 37 moslat002
+ 16 et001 + 25 et002 + 35 et003), freeze checks A OK on both pins
(scorer 1a840af9…9b592, melodic a16f162b…7535) before and after. Receipts
bit-identical across two runs (diff on et003.jsonl and et003_summary.json).
