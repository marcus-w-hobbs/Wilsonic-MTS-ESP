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
