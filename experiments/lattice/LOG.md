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

## 2026-08-09 — Gate back-fill: G-015 PASS, G-016 PASS (Marcus, via merge)

Session-start reconciliation per GATES.md protocol (merge implies pass;
next session back-fills). Marcus merged PR #33 (MOS-LAT-002) and PR #34
(BRIDGE-001) on 2026-07-30, plus PR #36 (ARCHIVE-001 index, no gate
attached). Ledger updated: G-015 PASS (H-M1 null on the mixed-tail
corpus; conjugate-descriptor program closed), G-016 PASS (H-B2 refuted
under strict containment; blackjack carries the full EG4 hexany at
ε = 3¢). With these, every experiment in the SPEC's original queue is
run and gated. Open: G-013 only (SUBSET-MEL-001 spec review), which
waits on the subset brainstorm session — a conversation with Marcus,
not a run.

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

## 2026-08-09 — MUR-001 pre-registration (entry BEFORE any implementation or run)

**Experiment:** census of murchana (window/anchor position) as a structural
parameter, quantifying the MOS-LAT-001 "murchana rescue" at corpus scale.
Runner: `mur001.py`; receipts: `results/mur001.jsonl` (one line per
(generator, N) row with per-anchor arrays) + `results/mur001_summary.json`.
Frozen verifiers, imported READ-ONLY: melodic v0.1.0 (`score_melodic`) and
triads scorer v1.1.0 (`score_tempered` = the anchored convention).

**Where anchor-dependence actually enters (the invariance argument, resolved
FIRST as commissioned).** For a plain generated chain with one fixed
generator g, the anchored window [b0, b0+N) octave-reduces to the anchor-0
scale TRANSPOSED by b0·g mod 1. Every interval-structure property — M1 gap
classes, M2 constant structure, M3 propriety, all functions of the circular
interval spectrum — is transposition-invariant, hence anchor-INVARIANT: a
naive census of those columns is trivially constant, and that null is a
PREDICTION here (H-MU0), not a surprise. Anchor becomes a real degree of
freedom in exactly three places, two of them in scope:
1. **Cut-and-project window-representability** (moslat001.py
   `verify_level`/`murchana_analysis`): whether the chain segment
   [b0, b0+N) is EXACTLY the set selected by its own internal-coordinate
   hull, ι(b) = b·g′ − ⌊b·g⌋. Decompose ι(b) = b·(g′−g) + frac(b·g): a
   line of slope ±conj_sep plus a sawtooth determined by the Sturmian
   floor word of g. The hull and the intruder census depend on the
   length-~N factor of that word AT b0 — a genuinely anchor-dependent,
   non-transposition-covariant property. This is where MOS-LAT-001's
   intruder failures and murchana rescues live. THE census object.
2. **The anchored triad scorer**: score_tempered scores octave-reduced
   representatives, so transposition changes which tones wrap the octave
   and hence (P, S). Anchor-dependent BY CONVENTION; recorded per anchor
   as a descriptive lens only (no hypothesis).
3. JI-embedding containment (BRIDGE-001's anchor intervals) — OUT OF
   SCOPE here; but note for H-MU2 below that BRIDGE-001's contiguous
   anchor intervals are containment-of-a-fixed-chain-set intervals,
   contiguous BY CONSTRUCTION (span ⊆ [b0, b0+N) defines an interval in
   b0), a categorically different property from murchana
   representability.

**Corpus (locked):** union of the MOS-LAT-001 noble corpus
(`moslat001.canonical_preambles` → 27 generators, all-1s tail, exact ℚ(√5))
and the MOS-LAT-002 mixed-tail quadratic corpus
(`moslat002.enumerate_corpus` → 216 generators, exact ℚ(√d)); 243 distinct
generators (disjoint by eventual-CF uniqueness — asserted). Rows: per
generator, the FIRST zigzag level (levels 0–9, `families/mos.py`) attaining
each distinct cardinality N ∈ [5, 22] — the exact `run_step2_rows`/
`run_rows` recipe; expected 97 + 788 = 885 rows. Anchors: b0 ∈ [−N, N]
(2N+1 per row; matches moslat001's murchana_analysis sweep).

**Per (row, anchor), computed with exact quadratic arithmetic (iota
imported from moslat001; works on Q5 and Quad):** hull of ι over the
segment; representable bit = no intruder in the scan range; intruder count.
Scan-pad justification, registered: with cs = |g − g′| and W = hull width
≤ (N−1)·cs + 1, any b at distance m from the nearest segment endpoint has
|ι(b) − ι(endpoint)| ≥ m·cs − 1, so m > (W+1)/cs ⇒ no intrusion; pad
D = 2N + ceil(2/cs) + 8 strictly exceeds N + 2/cs. Float fast-path for the
in-hull comparison with exact confirmation inside a 1e-9 ambiguity band
(float error of ι is ≤ ~1e-12 at these magnitudes). Per anchor also: frozen
melodic triple (propriety classification, CS violation count, gap-class
count) of the projected scale, and frozen P at ε ∈ {2, 3}¢ (descriptive).
Monotonicity, exact and registered: ι is strictly monotone in b iff
g′ ∉ (0, 1) (steps are g′ and g′−1) — moslat001's conj_sep > 1 flag is
sufficient but NOT necessary; the census uses the exact criterion.

**Constants (locked):** anchors [−N, N]; N ∈ [5, 22]; levels 0–9; scan pad
D as above; melodic defaults (dedup 0.01¢, gap/CS 0.5¢, propriety 1e-9¢);
triad ε ∈ {2.0, 3.0}¢, max_span default 1200¢; seed 20260725; 9999
permutations, add-one rule; python3.12, stdlib only, deterministic; run
twice, receipts must be bit-identical (sha256 recorded in the results
entry).

**Pre-registered hypotheses and verdict criteria:**

- **H-MU0 (invariance null rail):** for every row, the melodic triple
  (propriety classification, CS violations, gap-class count) is IDENTICAL
  across all 2N+1 anchors. Predicted violations: exactly 0 — the
  transposition argument above is exact, and float noise (~1e-11¢) is
  orders below every epsilon, with no exact spectral coincidences possible
  for a quadratic irrational generator. ANY violation = implementation bug:
  the runner writes receipts, reports the rows, and exits nonzero; the
  experiment halts for investigation.
- **H-MU1 (rescue genericity, from the MOS-LAT-001 receipts):** every row
  with ≥ 1 non-representable anchor has ≥ 1 representable anchor.
  Statistic: the number of ZERO-RESCUE rows (no representable anchor at
  all); KEPT iff 0. Registered tension, stated before running: H-MU1
  extrapolates MOS-LAT-001 (where every failing level had rescuing shifts,
  counts 5/15/41/109), but the drift-budget derivation under H-MU4 predicts
  zero-rescue rows on the mixed corpus's small-conj_sep tail. H-MU1 and
  H-MU4(b) cannot both hold; the census adjudicates.
- **H-MU2 (contiguity, as commissioned):** the representable-anchor set R
  of each partially-representable row (some but not all anchors, |R| ≥ 2)
  is a contiguous integer interval. Registered prediction: REFUTED — the
  MOS-LAT-001 receipts ALREADY show non-contiguous R (murchana examples
  [−4,−2,−1,2,3] at N=4; [−7,−4,−2,3,5] at N=7), and the BRIDGE-001
  intervals that motivated the hypothesis are contiguous by construction
  (see item 3 above). The census quantifies prevalence: fraction of
  partially-representable rows with contiguous R.
- **H-MU2b (registered replacement — three-distance structure):** because
  representability at b0 is a function of a fixed-length factor of the
  Sturmian floor word at b0, R should inherit rotation-orbit structure:
  for every row with |R| ≥ 3, the interior gaps between consecutive
  representable anchors take AT MOST 3 distinct values (prior data:
  {2,3,5} and {1,2} patterns in the moslat001 examples). KEPT iff zero
  rows violate; each violation reported with its gap multiset.
- **H-MU3 (rescue fraction vs CF structure):** over NON-monotone rows,
  with ρ = |R|/(2N+1) and rows labeled is_cf_convergent (exact convergents
  of the digit string preamble+periodic tail, membership of (num, den) as
  in moslat001): Δ = mean ρ(non-convergent) − mean ρ(convergent) > 0
  (convergent levels are where anchor-0 failures concentrated in
  MOS-LAT-001; predict they are harder across the whole anchor sweep, not
  just at anchor 0). Test: one-sided permutation of the convergent labels
  WITHIN generator strata, seed 20260725, 9999 permutations, add-one rule.
  SUPPORTED iff Δ > 0 AND p < 0.05.
- **H-MU4 (drift-budget law — own sharper question, derived before
  running from ι = b·(g′−g) + frac(b·g)):** let T = N·cs (total internal
  drift across the window). The sawtooth contributes O(1) spread while
  selection density is ~width/cs, so representability needs the drift term
  to dominate: (a) monotone rows (g′ ∉ (0,1)): ALL anchors representable —
  theorem rail, violations = bug; (b) among non-monotone rows, zero-rescue
  rows EXIST (refuting H-MU1) and T separates zero-rescue from
  rescue-possible with AUC ≥ 0.95 (T as score for "has ≥ 1 representable
  anchor"); (c) band predictions: every zero-rescue row has T < 2, and
  every non-monotone row with T > 4 has ≥ 1 representable anchor. KEPT
  iff (a) 0 violations, (b) both classes non-empty and AUC ≥ 0.95,
  (c) both band claims hold; partial outcomes reported per clause.

**Order:** commit this entry → tests/test_mur001.py (moslat001-receipt
fixtures pinned: g3=(1,2) N=11 anchor-0 intruder [11], |R| = 15; g4=(2,2)
N=7 R = {−7,−4,−2,3,5}, N=19 |R| = 15; golden monotone all-representable)
+ mur001.py, suite green BEFORE the first run → run twice, bit-identity
check → results entry → FINDINGS.md → GATES row G-018 → PR.

## 2026-08-09 — MUR-001 results + verdicts

**Run:** mur001.py, python3.12, ~40 s; run twice, receipts **bit-identical**
(sha256 `mur001.jsonl` e3584d59…adda6d, `mur001_summary.json`
2675ed55…feb839). 243 generators, 885 rows (97 noble + 788 mixed — exactly
the MOS-LAT-001/002 row sets, asserted by tests), 20,019 anchor
evaluations at b0 ∈ [−N, N]; exact ℚ(√d) arithmetic; frozen scorer v1.1.0
and melodic v0.1.0 read-only; seed 20260725, 9999 permutations.

**H-MU0 — KEPT (null rail), 0 violations.** The melodic triple (propriety
class, CS violations, gap-class count) is identical across all 2N+1
anchors on every row — the transposition-invariance argument confirmed
exactly, at float noise orders below every epsilon.

**H-MU1 — REFUTED, decisively; the registered H-MU4(b) tension resolves in
H-MU4's favor.** 537/885 rows are ZERO-RESCUE (no representable anchor at
all). Of the 709 rows that fail at anchor 0, only **172 (24.3%) have any
rescuing anchor**. The refutation does not need the mixed corpus: the
noble corpus alone has 69/97 zero-rescue rows. MOS-LAT-001's
"every failure rescued" was an artifact of its 4-generator step-1 sample,
whose failing rows all sat inside the rescue band (T = N·|g−g′| ≈ 1.4–5).
Murchana rescue is a minority phenomenon, not a generic one.

**H-MU2 — REFUTED, as registered.** Of 202 partially-representable rows
with |R| ≥ 2, **200 are non-contiguous** (contiguous fraction 0.99%; the
two contiguous cases are |R| = 2 rows). BRIDGE-001's contiguous anchor
intervals were containment-by-construction; murchana representability is
a different, non-interval object.

**H-MU2b — KEPT on 295/299 rows, REFUTED as stated.** 4 rows exceed 3
distinct interior anchor-gap values, and all four violate with the SAME
gap set {1, 2, 4, 7} ([0;1,1,1,(3)*] N=14; [0;2,1,(2,3)*] N=19;
[0;1,1,1,(2,3)*] N=11 and N=19). Post-hoc reading (labeled): 7 = 1+2+4,
consistent with a skipped occurrence in a three-distance return
structure — the sets look like unions of Sturmian-factor occurrence sets,
as the registered heuristic argued, but the ≤3 bound is not exact.

**H-MU3 — NULL under the registered rule, with the direction REVERSED.**
Over the 761 non-monotone rows: mean ρ(convergent) = 0.116 >
mean ρ(non-convergent) = 0.082, Δ = −0.0342, one-sided p = 1.0000 — the
observed Δ sits at the opposite extreme of the within-generator
permutation distribution. Post-hoc observation (labeled, not a verdict):
CF-convergent levels are EASIER to rescue across the full anchor sweep —
opposite of the anchor-0 intuition MOS-LAT-001 suggested (convergent
levels are where anchor 0 fails, but they are also where OTHER anchors
succeed most often).

**H-MU4 — (a) KEPT, (b) KEPT, (c) REFUTED narrowly.**
(a) All 124 monotone rows (exact criterion g′ ∉ (0,1)) are representable
at every anchor, zero violations — and SHARPER than predicted: the
fully-representable rows are EXACTLY the monotone rows (124 = 124), so on
this corpus monotonicity ⇔ murchana-free; every non-monotone row fails at
some anchor. (b) Zero-rescue (537) vs rescue-possible (224) non-monotone
rows are separated by the drift budget T = N·|g−g′| at **AUC 0.9742**
≥ the registered 0.95. (c) The band constants miss: 5 zero-rescue rows
have T > 2 (max 2.362), refuting "zero-rescue ⇒ T < 2"; "T > 4 ⇒
rescue-possible" held (0 violations). Empirical overlap band:
T ∈ [0.753, 2.362].

**Descriptive P lens (registered no-hypothesis):** the anchored frozen
triad count P is **anchor-INVARIANT on all 885 rows at both ε ∈ {2, 3}¢**
(0 rows vary). Under the frozen convention (max_span 1200¢), murchana
never moves the harmonic count — the harmonic axis is a property of the
scale up to transposition here, while window-representability is not.
Practical consequence: murchana is harmonically FREE and structurally
binding — choosing an anchor costs nothing in P and decides whether the
scale is a true cut-and-project window set.

**Kept.** mur001.py exactly as committed before the first run (no post-run
changes); receipts `results/mur001.jsonl` + `results/mur001_summary.json`.
Lattice suite 124/124 OK (incl. 14 new mur001 tests pinned to MOS-LAT-001
receipts), triads suite 88/88 OK; freeze checks OK before AND after
(scorer pin 1a840af9…9b592, melodic pin a16f162b…7535, both unchanged).
Findings promoted to FINDINGS.md; gate row G-018 appended.

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

## 2026-08-18 — MUR-002 pre-registration (entry BEFORE any implementation or run)

**Experiment:** calibrate the program's murchana machinery against the
primary source of the concept — the Indian grāma/mūrchanā system — as
Wilson actually lattices it. Runner: `mur002.py`; receipts:
`results/mur002.jsonl` (one line per (scale, rotation) row) +
`results/mur002_summary.json`; transcription: `MUR002_TRANSCRIPTION.md`
(derived data only, page-cited; the scan stays in place per the archive
rule). Frozen verifiers imported READ-ONLY: triads scorer v1.1.0
(`score`, `score_tempered`) and melodic v0.1.0 (`score_melodic`,
`best_val_kendall_tau`). Stacks on MUR-001 (research/mur-001, PR #39).

**What Wilson actually drew (read 2026-08-18, in place; pages of
`~/Documents/scans by Kraig/2010_02_24/Hanson/LatticingRagaScales.pdf`,
37 pp; read pp. 1–26).** NOT a 22-śruti lattice: the constant background
is Figure 1, "Major-Minor Triadic Lattice for 53 (redrawn from 1942
original)" — L. A. Hanson's 5-limit hexagonal lattice, rows = chains of
fifths, adjacent rows a 5/4 apart, every hex carrying a note name
(/ = +81/80, \ = −81/80 relative to the 5-limit spelling), an exact
ratio 3^a·5^b, and its 53-EDO degree (schisma 32805/32768 and kleisma
tempered). p.1 is the bare figure; pp. 2–19 plot eighteen numbered ragas
as red dots (18 Nat Bhairav, 17 Madhubanti, 16 Jogiya Todi, 15 Bhairav,
14 Anand Bhairav, 13 "No Name", 12 Lalit, 11 Todi, 10 Lalit₂, 9 Purvi,
8 Marwa, 7 Bhairavi, 6 Asawari, 5 Kafi, 4 **Old Kafi**, 3 Khamaj,
2 Bilawal, 1 Kalyan). **p.20 is the 22-śruti object**: "Outlined in red
is the theoretical scale of 22 steps, of modern India … E.W. 1997" —
22 hexes with śruti numbers 0–21, i.e. exact ratios 1/1, 256/243, 16/15,
10/9, 9/8, 32/27, 6/5, 5/4, 81/64, 4/3, 27/20, 45/32, 729/512, 3/2,
128/81, 8/5, 5/3, 27/16, 16/9, 9/5, 15/8, 243/128 — twelve on the
Pythagorean row (3^−5..3^6), five on the 5-row (5·3^k, k = −2..2), five
on the 1/5-row (3^k/5, k = −1..3); with Wilson's own margin note that
135/128 vs 256/243, 405/256 vs 128/81, 1215/1024 vs 32/27 "and so forth"
are schismatically equivalent. pp. 21–23: Boomsliter & Creel "extended
reference patterns" (major: two fifth-chains a 5/4 apart; minor; and a
"blue" pattern to "compare with independently derived ratios for Marwa,
Purvi, Lalit₂, Todi, Lalit"). pp. 24–26 and 36–37: Hanson keyboard
geometry (19-tone sets, tubulongs), not raga material. Wilson does NOT
draw a madhyama-grāma anywhere in pp. 1–26; the ṣaḍja-grāma appears
under his label "Old Kafi" (p.16): {1/1, 10/9, 32/27, 4/3, 3/2, 5/3,
16/9} = the classical 4-3-2-4-4-3-2 śruti pattern read on the 22-śruti
set. The madhyama-grāma used below is DERIVED (Pa lowered one śruti,
3/2 → 40/27) and is labeled derived, not transcribed, in every receipt.
Every raga has C = 1/1 as its dot (Sa); Wilson's raga placements use the
5-limit spellings /C# 135/128, /G# 405/256, /D# 1215/1024, //A#
3645/2048 rather than their Pythagorean schisma-twins — the p.20 note is
about exactly this. A second 22 at the archive root, `BilawalDiamond22.jpg`,
is K. Grady's (dated 20-10-23), not Wilson's; noted in the transcription,
descriptive only.

**Corpus (locked; every ratio exact `Fraction`, every scale contains
1/1):**
- S22 — the p.20 22-śruti set (śruti index = sorted rank).
- SA — ṣaḍja-grāma = Wilson's Old Kafi (p.16); MA — madhyama-grāma,
  derived (SA with 3/2 → 40/27).
- R1..R18 — the eighteen raga scales as drawn (pp. 2–19), exact spellings
  as placed on the lattice; plus for each, its "śruti-spelled" twin
  (each tone snapped to the S22 tone of the same 53-degree) and its
  53-EDO image (degree = 31·e3 + 17·e5 mod 53, the figure's own numbers,
  cross-checked against the transcribed degrees).
- All 7 rotations (mūrchanās) of every 7-tone scale; the 22 rotations of
  S22 for the invariance rail only.

**Constants (locked):** melodic defaults (dedup 0.01¢, gap/CS 0.5¢,
propriety 1e-9¢); CS ε-sweep for H-R5: {0.5, 1.0, 1.5, 1.9, 2.0, 2.5,
3.0, 5.0}¢; triad ε ∈ {2, 3, 5, 15}¢ tempered + the exact rational path
(`score`), max_span default (2/1 exact, 1200¢ tempered); "within-tolerance"
for the chain/EDO fit tests = 5¢ (and 2¢ reported); coarse step word:
T iff step > 150¢ else s; m4_proto = (tonic-relative step word as exact
ratios; interval-from-tonic set as exact ratios + cents; tonic-consonance
count = number of tones forming exactly one of {3/2, 4/3, 5/4, 6/5, 5/3,
8/5} with the tonic) — computed in the runner, NOT added to melodic.py;
python3.12 stdlib only; deterministic; run twice, receipts bit-identical
(sha256 recorded in the results entry).

**Mode-blindness, stated up front.** M1–M3 are functions of the circular
interval spectrum, hence rotation-invariant (MUR-001 H-MU0 rail); and the
frozen anchored triad scorer is EXACTLY transposition-invariant by
construction (each triad is anchored at its middle tone b, with a and c
the unique pitch-class representatives in (b/2, b) and (b, 2b) — the
loop over b covers the pitch-class set, so a transposed set yields the
same multiset of ratio triples; max_span c/a is likewise relative).
Every frozen number in this experiment is therefore mūrchanā-blind by
theorem; the experiment measures AROUND that with m4_proto and says so.

**Pre-registered hypotheses, predictions derived by hand from the
ratios BEFORE any code:**

- **H-R1 (grāma structure).** SA and MA are both STRICTLY PROPER and CS
  (hand check: SA steps (10/9, 16/15, 9/8, 9/8, 10/9, 16/15, 9/8): 1-step
  max 203.9 < 2-step min 294.1; 2-step max 407.8 < 3-step min 498.0;
  3-step max 590.2 < 4-step min 609.8; MA steps (10/9, 16/15, 9/8, 10/9,
  9/8, 16/15, 9/8): 2-step max 386.3, 3-step [498.0, 590.2]; strict at
  every span pair). Both have exactly 3 gap classes (9/8 ×3, 10/9 ×2,
  16/15 ×2 → M1 = 1.557 bits) — so M1–M3 CANNOT distinguish SA from MA
  at all. Rail: all 7 mūrchanās of each grāma have identical M1–M3
  triples (0 violations, else bug). m4_proto: all 7 rotations of each
  grāma have DISTINCT tonic step words (both words are primitive).
  Mūrchanā matches to Wilson's own diatonic thaats — exact ratio-set
  matches predicted: Bilawal (p.18: 1, 9/8, 5/4, 4/3, 3/2, 27/16, 15/8)
  = SA rotated to Ni (16/9); Khamaj (p.17) = SA rotated to Ma (4/3);
  neither is a rotation of MA (MA's Ni-rotation is Ptolemy's 5/3 major,
  1 tone off Bilawal; MA's Ma-rotation is 1 tone off Khamaj). Coarse
  T/s words match but exact ratios differ by comma shifts for: Kafi
  (Dorian word = SA at Sa; 2 tones differ: 9/8, 27/16 vs 10/9, 5/3),
  Kalyan (SA at Ga; 2 tones), Asawari (SA at Pa; 2 tones), Bhairavi (SA
  at Ri; 5 tones). Verdict: KEPT iff propriety/CS as stated for SA and
  MA AND the two exact matches (Bilawal@Ni, Khamaj@Ma) hold; each
  coarse-match/comma-count claim reported separately.
- **H-R2 (22 as housing).** (a) S22 under the frozen scorers: NOT a MOS
  (three gap classes 256/243 ×7, 81/80 ×10, 25/24 ×5); IMPROPER (two
  adjacent limmas 90.2+90.2 = 180.4 > 3-step min 21.5+70.7+21.5 =
  113.7); CS at ε = 0.5¢ (predicted YES — mechanism in H-R5); exact
  P = S = 45 (fifths 19 + 4:5:6 ×9 + 3:4:5 ×9 + 8:9:10 ×8, and the set
  is inversionally symmetric under x → 3/x, so S = P); tempered counts
  at 2/3/5/15¢ reported (no prediction: schisma near-coincidences and
  the informative-guard pull in opposite directions). (b) Chain tests:
  S22 is NOT an exact single-generator chain (rank-1 3-gap sets satisfy
  L = M + S; here 90.2 ≠ 70.7 + 21.5 by exactly the schisma), but its
  53-EDO image IS the chain of 22 fifths, positions −10..+11 (predicted
  set equality: {31k mod 53 : k = −10..11} == S22 degrees), and a
  Pythagorean chain of 22 fifths at the same anchor matches S22 22/22
  within 5¢ (max deviation 1 schisma = 1.95¢). Against BRIDGE-001's
  22-tone hosts: best-offset match counts within 5¢ predicted ≤ 10/22
  for 22-EDO and ≤ 10/22 for orwell-22 (⟨22,35,51,62⟩, 271.385¢ chain),
  vs 22/22 for 53-EDO (within 2¢). So Wilson's 22 is a DIFFERENT object
  from the orwell/22-EDO window: a fifth-chain window (rank-1 modulo the
  schisma), i.e. the schismatic-temperament fold of a 5-limit block.
  (c) Housing: all 18 ragas are subsets of S22 modulo 53 (18/18), but
  only the 7 with no schismatic spelling (Bhairavi, Asawari, Kafi, Old
  Kafi, Khamaj, Bilawal, Kalyan) are exact-JI subsets (7/18). Verdict:
  KEPT iff (a) MOS-no/improper/CS-yes/exact 45=45, (b) the three chain
  claims and both ≤ 10/22 bounds, (c) 18/18 and 7/18 all hold; clauses
  reported separately.
- **H-R3 (rotation-invariance of P on lattice subsets).** By the
  transposition argument above, exact and tempered (P, S) are identical
  across all 7 rotations of every raga and both grāmas, at every ε
  (tempered path: float noise ≪ ε). Predicted violations: 0 — a rail
  now, but a rail worth writing down because it means "supersets good
  for rotating" carry NO harmonic cost under the frozen convention.
- **H-R4 (grāma shift = comma perturbation, not rotation).** SA → MA is
  the one-śruti (81/80) lowering of Pa; MA is NOT a rotation of SA (nor
  of its inversion) — checked by word: (m s L L m s L) vs (m s L m L s L).
  Frozen scorers: melodic triple UNCHANGED (both strictly proper, CS,
  1.557 bits); exact triads MOVE UP: SA (P, S) = (11, 7) → MA (13, 9)
  (hand count under the anchored convention: SA fifths 5 + 3:4:5 ×2 +
  4:5:6 ×2 + 8:9:10 ×2 = 11; fourths 5 + 12:15:20 ×1 + 10:12:15 ×1 +
  36:40:45 ×0 = 7; MA fifths 5 + 3 + 3 + 2 = 13; fourths 5 + 1 + 2 + 1
  = 9); tempered 2¢ and 3¢ equal the exact counts (no near-coincidence
  inside 3¢ in either scale). Relation to SHADOW-001: this is a comma
  perturbation that INCREASES exact coincidences — opposite in sign to
  H-S1's "immediate and permanent" loss — because 40/27 lands ON the
  5-limit lattice adjacent to 10/9 and 5/3 (the sharing/connectivity
  effect of H-S3, in a rank-2 5-limit setting rather than a CPS one).
  Verdict: KEPT iff (11,7) → (13,9) exact and the melodic triple is
  identical; partial outcomes reported.
- **H-R5 (own sharper question — the schisma as a CS phase
  transition).** Because S22's exact spelling separates every 53-degree
  collision by exactly one schisma (32805/32768 = 1.9537¢), and no other
  sub-2¢ coincidence exists in the set (row span ≤ 2 in e5, so only
  single schismas occur), the frozen CS check on exact S22 gives
  violations = 0 for ε_CS ∈ {0.5, 1.0, 1.5, 1.9} and > 0 for
  ε_CS ∈ {2.0, 2.5, 3.0, 5.0}; the 53-EDO image of S22 is NOT CS at
  0.5¢, with the fifth (3/2 at 13 steps vs the schismatic 16384/10935 at
  12 steps, both degree 31) among the violating classes. Verdict: KEPT
  iff all four sub-2¢ epsilons give 0, all four ≥ 2¢ give > 0, and the
  53-image is non-CS with degree-31 in the violation list.

**Registered descriptive lenses (no hypothesis):** per-raga melodic
triple and P/S; class prediction recorded for the record only — strictly
proper: Old Kafi, Bilawal, Khamaj, Kalyan; improper: the other 14
(Pythagorean tritone for Kafi/Asawari/Bhairavi; a 32/27 or 92¢ step
adjacent to a large step for the Bhairav/Todi/Purvi/Marwa/Lalit family);
Wilson-spelling vs śruti-spelling vs 53-EDO (P, S) at every ε.

**Order:** commit this entry → tests/test_mur002.py + mur002.py, lattice
suite green BEFORE the first run → run twice, bit-identity → results
entry (incl. the ≤15-line M4 proposal) → FINDINGS.md → PR (gate G-020
lives in the ledger PR #37; proposed row in the PR body).

## 2026-08-18 — MUR-002 results + verdicts

**Run:** mur002.py, python3.12, ~2 s; run twice, receipts **bit-identical**
(sha256 `mur002.jsonl` 5aa6daf2…5d2a29, `mur002_summary.json`
f081ac00…578584). 199 rows: S22 × 22 rotations + its 53-EDO image, SA and
MA × 7 mūrchanās, 18 ragas × (7 rotations as drawn + śruti-spelled +
53-EDO image). Frozen scorer v1.1.0 (exact `score` + tempered at
ε ∈ {2, 3, 5, 15}¢) and melodic v0.1.0 read-only; freeze checks OK before
AND after (scorer pin 1a840af9…9b592, melodic pin a16f162b…7535). Corpus
transcription with page citations: `MUR002_TRANSCRIPTION.md`; the scan
was read in place (pp. 1–26), nothing copied.

**H-R1 — KEPT.** ṣaḍja-grāma (Wilson's "Old Kafi", p.16) and the derived
madhyama-grāma are both STRICTLY PROPER (0 violations, 0 equalities) and
CS (0 violations), each with 3 gap classes (9/8 ×3, 10/9 ×2, 16/15 ×2;
M1 = 1.5567 bits), best val ⟨7, 11, 15⟩ at τ = 0 with 2 tie pairs — the
frozen melodic triple is IDENTICAL for SA and MA, as predicted. Rail:
melodic triple identical across all 7 mūrchanās of each grāma (0
violations). m4_proto separates what M1–M3 cannot: 7/7 distinct tonic
step words per grāma; tonic-consonance counts across SA's mūrchanās
3, 3, 1, 4, 1, 3, 3 (Sa, Ri, Ga, Ma, Pa, Dha, Ni), MA's 2, 4, 2, 4, 3, 3, 4.
Thaat lookup, exactly as predicted: **Bilawal (p.18) = SA rotated to Ni
(k = 6), Khamaj (p.17) = SA rotated to Ma (k = 3), both exact ratio-set
matches; neither is a rotation of MA** (MA@6 is Ptolemy's 5/3 major,
one tone off Bilawal; MA@3 one tone off Khamaj). Coarse T/s words match a
SA mūrchanā with comma-shifted tones for Kafi (SA@0, 2 tones: 9/8, 27/16
vs 10/9, 5/3), Kalyan (SA@2, 2 tones), Asawari (SA@4, 2 tones), Bhairavi
(SA@1, 5 tones) — the modern thaats sit closer to the ṣaḍja-grāma than
to the madhyama-grāma (post-hoc, labeled: MA's nearest rotations differ
by 1, 1, 1, 3, 4, 5 tones for Bilawal, Khamaj, Kalyan, Kafi, Asawari,
Bhairavi). MA's Ri-mūrchanā {1, 16/15, 6/5, 4/3, 3/2, 8/5, 9/5} is the
5-limit Phrygian — the "just" Bhairavi Wilson did NOT draw (his Bhairavi
is the Pythagorean chain).

**H-R2 — REFUTED as stated on one number, KEPT on every structural
clause.** (a) S22: 3 gap classes (81/80 ×10, 25/24 ×5, 256/243 ×7 —
21.51 / 70.67 / 90.23¢; NOT a MOS), IMPROPER (10 violating span pairs),
CS at 0.5¢ (0 violations), best val ⟨22, 35, 51⟩ at τ = 0 (the
orwell/22-EDO patent val orders it perfectly), exact **P = S = 48**, not
the predicted 45: the hand count omitted the fifth primitive 5-limit
arithmetic progression with c/a ≤ 2, **18:25:32** (a, 25a/18, 16a/9),
which S22 realizes 3× (e.g. 6/5 : 5/3 : 32/15), plus its harmonic-mean
twin 225:288:400 3× — the enumeration in the receipt lists exactly
2:3:4 ×19, 3:4:5 ×9, 4:5:6 ×9, 8:9:10 ×8, 18:25:32 ×3 (and mirrors).
Tempered (P, S): 70/70 at 2¢, 79/79 at 3¢, 88/88 at 5¢, 218/218 at 15¢
(G = 110/110/98/90); its 53-EDO image scores 59/88/98/220 — the
schisma-twins that the exact set separates recombine into
near-coincidences at 2¢ from the other side. (b) All chain claims KEPT:
S22 is not an exact rank-1 chain (three-gap defect L − M − S = −1.9537¢
= exactly one schisma), its 53-degrees are exactly {31k mod 53 :
k = −10..11}, and the Pythagorean chain of 22 fifths anchored at −10
matches it 22/22 within 2¢ WITHOUT any offset (max deviation 1.9537¢).
Against BRIDGE-001's hosts: best-offset matches within 5¢ — 22-EDO 5/22
(2/22 at 2¢), orwell-22 10/22 (6/22 at 2¢; at the registered ≤ 10 bound),
53-EDO 22/22 (also at 2¢). Wilson's 22 is a fifth-chain window
(schismatic fold of a 5-limit block), a different object from the orwell
window. (c) Housing KEPT: all 18 ragas ⊆ S22 modulo 53 (18/18); exactly
the 7 without schismatic spellings are exact-JI subsets (7/18: Bhairavi,
Asawari, Kafi, Old Kafi, Khamaj, Bilawal, Kalyan).

**H-R3 — KEPT, 0 violations on 21 scales** (S22's 22 rotations, SA, MA and
the 18 ragas × 7): exact and tempered (P, S, G) identical across every
rotation at every ε. As argued in the pre-registration this is a theorem
of the anchored convention; on the record now for lattice subsets, not
just chain windows (MUR-001): under the frozen scorers a mūrchanā costs
nothing harmonically and changes nothing melodically — everything the
grāma system cares about lives outside M1–M3 and P.

**H-R4 — REFUTED as stated on one number, direction and mechanism KEPT.**
MA is not a rotation of SA nor of its inversion (the SAME coarse word
TsTTTsT, different exact words (m s L L m s L) vs (m s L m L s L)); the
melodic triple is identical (predicted); exact triads SA (11, 7) →
MA **(13, 10)** — predicted (13, 9); the hand count missed the 12:15:20
at 16/9 : 10/9 : 40/27 (I wrote "80/27 ✗" — 80/27 octave-reduces to
40/27, which MA contains). Both P and S rise; tempered 2/3/5¢ equal the
exact counts on both scales (no sub-5¢ near-coincidence), and at 15¢ SA
= (13, 11), MA = (13, 12). Reading (as pre-registered): the one-śruti
comma shift is a comma perturbation that GAINS exact coincidences —
opposite in sign to SHADOW-001 H-S1 — because 40/27 lands on lattice
edges (fifth to 10/9, fourth to 5/3, 5/4 above 32/27), the H-S3
connectivity effect in a rank-2 5-limit setting. The grāma system is a
historical instance of "comma perturbation of a lattice subset", and the
frozen harmonic axis registers it (+2 P, +3 S) while the melodic axis is
blind to it.

**H-R5 — KEPT, sharp.** CS violations of exact S22 by ε_CS: 0.5 → 0,
1.0 → 0, 1.5 → 0, 1.9 → 0, **2.0 → 30**, 2.5 → 30, 3.0 → 30, 5.0 → 30 —
a step function at the schisma (1.9537¢), constant on both sides. The
53-EDO image is not CS at 0.5¢ (30 violations, the same 30 classes),
and the fifth (degree 31, 701.9¢) is among them at 12 AND 13 steps
(3/2 vs the schismatic 16384/10935), as predicted. Post-hoc, labeled: the
same phase transition governs the ragas — at 0.5¢ the ragas as DRAWN
are CS 7/18, the śruti-spelled twins 16/18, and the 53-EDO images 7/18;
so 9 ragas are CS in exact JI only by the schisma, and every raga's CS
status is a spelling-thin property of the same kind as S22's.

**Descriptive lenses (registered, no hypothesis).** Propriety histogram
exactly the registered class prediction: strictly proper 4 (Old Kafi,
Bilawal, Khamaj, Kalyan), improper 14 (Kafi/Asawari/Bhairavi by the
Pythagorean tritone; the Bhairav–Todi–Purvi–Marwa–Lalit family by an
augmented second or 92¢ step). Exact (P, S) as drawn: Old Kafi = Bilawal
= Khamaj = (11, 7) (they are one scale up to mūrchanā), Kalyan (10, 13),
Anand Bhairav (9, 9), Nat Bhairav and Madhubanti (9, 6), Marwa (7, 10),
Lalit₂ and Purvi (7, 7), Kafi/Asawari/Bhairavi/Bhairav (6, 6), Lalit,
No Name, Todi (5, 5), Jogiya Todi (4, 4). Post-hoc, labeled: **Wilson's
schismatic spellings never lose and six times gain exact triads over the
śruti spelling** (Lalit 5 → 4, Lalit₂ 7 → 6, Marwa (7, 10) → (6, 9), No
Name 5 → 4, Purvi 7 → 6, Todi 5 → 4; 12 ragas tie, 0 lose) — /C#
135/128 makes an exact 3/2 with /F# 45/32 and 4:5:6 with 405/256, which
256/243 cannot; the "Major-Minor Triadic Lattice" placement is
triad-optimal on the exact path, by machine check.

**M4 proposal (≤ 15 lines, INPUT to a future decision; not implemented).**
M4 = tonic-anchored melodic score of a scale S given a tonic t ∈ S:
inputs: the interval-from-tonic set I(S,t) = {s/t reduced}, the tonic
step word w(S,t), a consonance set C (default the 5-limit {3/2, 4/3, 5/4,
6/5, 5/3, 8/5}, later prime-limit-parametrized) and a tolerance ε.
Compute (i) tonic anchoring A = |I ∩ C|/|I−{1}| (fraction of tones in
exact/ε-consonance with the tonic — SA 3/6, Khamaj 4/6, the Lydian
mūrchanā 1/6 in this run); (ii) tonic frame F = 1 if 3/2 ∈ I else 0.5 if
4/3 ∈ I else 0 (the Sa–Pa / Sa–Ma frame; MA scores 0.5, SA 1); (iii)
word primitivity/rotation class of w (which mūrchanā of which grāma the
scale IS: MUR-002 shows Bilawal and Khamaj are SA@6, SA@3 exactly);
(iv) comma distance to the nearest grāma mūrchanā (tones differing, as
computed here: Kafi 2, Kalyan 2, Asawari 2, Bhairavi 5). Formula
candidate: M4 = A · (1 + F)/2, tie-broken by (iv). What it ranks
differently from M1–M3: the seven mūrchanās of one grāma (identical
M1–M3, P) get seven M4 values; SA vs MA (identical M1–M3) separate by F;
Wilson's Pythagorean Bhairavi (A = 2/6, F = 1) vs MA's just Phrygian
(A = 4/6, F = 1) separate by A. Validation gate: a blind ear check on
mūrchanā pairs of one grāma, like G-006 — the only test that can say
whether tonic-anchoring is what the ear ranks.

**Kept.** mur002.py exactly as committed before the first run; receipts
`results/mur002.jsonl` + `results/mur002_summary.json`;
`MUR002_TRANSCRIPTION.md`. Lattice suite 145/145 OK (21 new mur002 tests),
triads suite unchanged; freeze checks OK before AND after. Findings
promoted to FINDINGS.md; gate G-020 (ledger PR #37) — proposed row in
the PR body.

## 2026-08-18 — SUBSET-MEL-000 pre-registration (entry BEFORE any run)

**What this is.** A `-000`: a machine CENSUS of the 72 structurally embedded
CPS subsets of a handful of eikosanies, producing ranked tables (several
orderings, deliberately not one score) for Marcus to react to in the still-
pending SUBSET-MEL-001 brainstorm (gate G-013). It claims NO aggregator.
Doctrine on record it serves (G-012): "we usually don't play the eikosany, we
play its subsets — dekanies, hexanies are the melodic sweet spots";
melody ≈ low gap_classes/N ∧ propriety; CS is a first-class axis;
improper-but-valid spice must never be zeroed out. Ledger: gate **G-022**
(consolidated in PR #37; GATES.md not edited by this session).

**Primary sources this censuses by machine** (archive/INDEX.md paths, cite
don't vendor): `1-3-5-7-9-11dekanyCS.jpg` (Wilson's matrix of the twelve
2)5/3)5 dekanies of {1,3,5,7,9,11} on one shared degree grid — exactly the
12 dekanies enumerated here for the classic seed);
`2010_02_24B/CPS B/Eikosany.pdf` p.1 (1967: "members of 3·5·7·11 hexany
alternate or complementary set" — embedded-hexany addressing);
`dekany_14_tone_constant_structure/` (Kraig→Marcus: the 1-3-7-9-15 dekany
is NOT CS by itself and needs 4 added tones) and the Scala archive entry
`Wilson-Grady_1-3-5-7-9 doubledekany` ("constant structure scale of the 2)5
and 3)5 1-3-5-7-9 dekanies", 14 tones — so the bare 1-3-5-7-9 dekany is
not CS either); `2010_02_24/CPS/DAlessandroFull.pdf` p.3 (the 2⁶ power set
by Pascal level — the subset family in one picture). Notation: canonical
CPS(n,k) = n choose k; Erv's "k)n" is the reverse — translated, not corrected.

**Corpus (deterministic).** Seed eikosanies CPS(6,3): (1) classic
{1,3,5,7,9,11}; (2) flagship {1,7,9,11,15,29} (CS-EIK-001, first strictly
proper eikosany); (3–5) the top three CS winners by `cs_margin_cents`
descending in `results/cseik001.jsonl`, EXCLUDING the flagship, ties broken
by ascending seed tuple: {13,17,21,23,25,27} (9.22¢, G-012 max-margin),
{1,3,13,21,23,25} (3.01¢), {1,3,11,13,25,27} (2.77¢). Five seeds × 72
subsets = 360 rows. All five are true 20-tone eikosanies (no product
collisions), asserted at run time.

**The 72 subsets per seed** (index-structural, from the Johnson graph J(6,3)):
6 dekanies "fix one factor IN" (3-products containing x; 10 tones = x·CPS(5,2)
of S∖{x}); 6 dekanies "fix one factor OUT" (3-products avoiding x; 10 tones =
CPS(5,3) of S∖{x}); 30 hexanies "x in, y out" (6 tones = x·CPS(4,2) of
S∖{x,y}); 15 harmonic tetrads "x,y in" (4 tones = xy·(S∖{x,y})); 15
subharmonic tetrads "x,y out" (4 tones = 3-products of S∖{x,y}).
6+6+30+15+15 = 72 — pinned in tests. Johnson-graph adjacency = shared-tone
counts between all subset pairs (exact tone identity), recorded so
modulation paths are recoverable; the algebra says IN(x)∩OUT(x) = ∅,
IN(x)∩IN(y) = tetrad_in(x,y), IN(x)∩OUT(y) = hexany(x in, y out) — pinned
in tests, and the whole 72×72 matrix is seed-independent for collision-free
seeds (stored once, checked identical per seed).

**Per-subset measurements.** Frozen melodic v0.1.0 (M1 gap classes,
gap_classes/N, entropy; M2 CS at 0.5¢; M3 propriety class + violations),
exact-rational CS (cseik001.cs_check, read-only import) + CS margin, step
word (gaps labelled a<b<c… by 0.5¢ cluster class), frozen triad scorer
v1.1.0: exact path (P,S,G) and tempered path at ε ∈ {2, 3}¢ with G-002
balance buckets (triads/search.balance_bucket), triad survival ratio =
tempered P / exact P (and S/S) — "the subset's own theoretical count" is its
exact-rational count.

**Orderings reported per seed (dekanies and hexanies separately), none of
them "the score":**
- melodic-first: (gap_classes/N ↑, propriety rank ↑ [strict < proper <
  improper], M3 violations ↑, exact CS violations ↑, name);
- harmonic-first: (P+S at 3¢ ↓, exact P+S ↓, P at 3¢ ↓, name);
- CS-first: (exact CS violations ↑, gap_classes/N ↑, propriety rank ↑,
  M3 violations ↑, name).
Spice list = improper subsets whose harmonic-first rank within (seed, type)
is in the top third — listed explicitly so they are not lost.
`.scl` exports (results/scl/subsetmel000/, to_scala convention: lowest
canonical tone = 1/1, provenance names the parent eikosany, the subset, and
the standalone CPS recreation in Wilsonic): per seed, the top dekany under
each of the three orderings (deduplicated) and the top two distinct
hexanies under melodic-first — for Marcus's ear check.

**Pre-registered hypotheses and predictions:**

- **H-SM1 (dekany IN/OUT asymmetry) — I predict EXACT SYMMETRY, derived.**
  fix-IN(x) = x·CPS(5,2)(T) and fix-OUT(x) = CPS(5,3)(T) = Π(T)/CPS(5,2)(T)
  with T = S∖{x}, so the two dekanies of the same x are an exact inversion
  pair (checked symbolically for one case before this entry; no scoring
  run). Inversion preserves the interval spectrum at every span ⇒ identical
  M1/M2/M3 and exact CS/margin, step word reversed; the anchored scorer
  swaps P↔S exactly (P+S equal). Same for the tetrads: tetrad_in(x,y) and
  tetrad_out(x,y) are inversions (harmonic vs subharmonic). The 30 hexanies
  are 15 transposition pairs (x·H vs y·H) ⇒ identical on every axis
  including P=S. So the real between-dekany variation is WHICH factor is
  dropped: 12 dekanies collapse to 6 melodic classes. Sub-prediction
  (composite-9 fingerprint, LAT-MEL-001): for the classic seed the three
  dekany classes that keep {1,3,9} intact (drop 5, 7, or 11) have MORE exact
  CS violations than the three that break the 3² = 1·9 relation (drop 1, 3,
  or 9). Any measured asymmetry within an IN/OUT pair is a bug or a
  canonicalization artifact, not a finding.
- **H-SM2 (hexany CS rail).** Classic seed: exactly 26/30 hexanies CS
  (13/15 classes); the 4 failures are the two transpositions each of the
  {1,3,5,9} and {1,3,7,9} hexanies (LAT-MEL-001 receipts: the only
  composite-9 failures inside this seed) — i.e. hexany(7 in, 11 out),
  hexany(11 in, 7 out), hexany(5 in, 11 out), hexany(11 in, 5 out).
  Flagship: 30/30 CS — no pair-product or seed-ratio coincidence up to
  powers of 2 exists among {1,7,9,11,15,29} (checked by hand: 3 ∉ S so
  1·9 = 3² cannot fire), so no exact intra-hexany interval duplication.
  Predict 30/30 for {13,17,21,23,25,27} as well; the two {1,3,…} winners
  contain 1 and 3 but not 9, so predict 30/30 there too. Family rail:
  ≥ 26/30 on every seed.
- **H-SM3 (subset vs whole).** Flagship (strictly proper at N=20): NOT all
  12 dekanies strictly proper — strict propriety of the 20-tone does not
  descend to 10-tone subsets (subset spans mix parent spans); predict 2–4
  of the 6 dekany classes non-improper (4–8 of 12). Classic (improper at
  N=20): predict 0–2 of 6 classes non-improper (0–4 of 12), and the
  primary-source rail: the drop-11 dekany (= the 1-3-5-7-9 dekany, 2)5 and
  3)5) is NOT exact-CS (Wilson–Grady needed 14 tones to make it CS).
- **H-SM4 (harmonic rails).** (a) survival ≥ 1.0 for every subset at both
  ε (tempered ≥ exact for JI); (b) hexany survival EXACTLY 1.0 at 2¢ for
  all 30 hexanies of the classic and the flagship (no overshoot; SHADOW-001
  never saw a hexany overshoot), overshoot allowed only in the wide-seed
  winners; (c) tetrads: two-in tetrads have P ≥ S (harmonic series segment
  ⇒ arithmetic means), two-out have S ≥ P with the counts exactly swapped
  (inversion); (d) dekanies: exact P ≠ S for a majority of the 12 (CPS(5,2)
  is not self-inverse), classic mean exact P+S per dekany in [15, 35]
  (against eikosany 57+57).
- **H-SM5 (rankings disagree).** Spearman ρ (average ranks; scipy-free,
  moslat001.ranks read-only) between the melodic-first order and the
  harmonic-first order over a seed's 12 dekanies is < 0.5 for the classic
  AND the flagship; pooled over all 60 dekanies also < 0.5; classic 30
  hexanies < 0.5. This is the fact the SUBSET-MEL-001 aggregator must live
  with. (n is small — the sign and magnitude are reported, not a p-value.)

**Determinism:** python3.12 stdlib only, no randomness; runner
`subsetmel000.py`; tests `tests/test_subsetmel000.py` written and green
BEFORE the first run; receipts `results/subsetmel000.jsonl` (360 rows) +
`results/subsetmel000_summary.json` (orderings, verdict numbers, adjacency
matrix once) + `results/scl/subsetmel000/*.scl`. Both frozen pins verified
before and after (scorer 1a840af9…9b592, melodic a16f162b…7535). Anything
computed after this entry that is not listed here is labelled POST-HOC.

## 2026-08-18 — SUBSET-MEL-000 results + verdicts

**Run:** `subsetmel000.py` (~0.8 s, receipts bit-identical across three
runs), 5 seeds × 72 = 360 rows → `results/subsetmel000.jsonl`;
`results/subsetmel000_summary.json` (three orderings per seed for dekanies
and hexanies, verdict numbers, spice lists, the 72×72 shared-tone matrix
once); 21 `.scl` → `results/scl/subsetmel000/`. Tests
`tests/test_subsetmel000.py` 32/32 green before the first run; lattice
suite 142/142; both freeze pins verified before and after (scorer
1a840af9…9b592, melodic a16f162b…7535). Seeds by the pre-registered rule:
{1,3,5,7,9,11}, {1,7,9,11,15,29}, {13,17,21,23,25,27}, {1,3,13,21,23,25},
{1,3,11,13,25,27}. Johnson adjacency identical across all 5 seeds (stored
once). Post-run receipt-field additions (labelled in code): `P_raw`,
`S_raw`, `degenerate_dropped` on the tempered rows; `n_distinct_keys` on
the rank-disagreement blocks. No pre-registered verdict field depends on
them.

**H-SM1 — KEPT (exact symmetry, as derived).** All 30 IN/OUT dekany pairs
identical on M1/M2/M3 and exact CS, with (P,S) swapped exactly on the exact
path AND at 3¢ (30/30); all 75 hexany transposition pairs identical on
every axis; all 75 tetrad IN/OUT pairs (P,S)-swapped. So a seed has 6
dekany classes, 15 hexany classes, 15 tetrad classes — the census tables
are half their nominal size, by algebra. The composite-9 sub-prediction is
REFUTED as stated: classic classes keeping {1,3,9} (drop 5/7/11) have 14/22/
12 exact CS-violation classes vs 12/20/12 for those breaking it (drop 1/3/
9) — means 16.0 vs 14.7 in the predicted direction, but not uniform (drop-3
= 20 > drop-11 = 12).

**H-SM2 — KEPT exactly.** Classic: 26/30 hexanies CS (exact and M2 at
0.5¢ agree), the four failures being precisely the predicted hexany(5 in,
11 out), (11 in, 5 out) [= {1,3,7,9}] and (7 in, 11 out), (11 in, 7 out)
[= {1,3,5,9}]. Flagship 30/30; the three other CS winners 30/30 each.
Family rail (≥ 26/30 on every seed) holds.

**H-SM3 — flagship REFUTED, classic KEPT, and the direction is the
finding.** Flagship (strictly proper at N = 20): 0/12 dekanies non-improper
(predicted 4–8), 0/12 CS; its least-improper dekany class is drop-29
= CPS(5,2){1,7,9,11,15} (4 violating span pairs vs 8 for the other five).
Classic: 0/12 non-improper (predicted 0–4), 0/12 CS; the drop-11 dekany
(= the 1-3-5-7-9 dekany, 2)5/3)5) has 12 exact CS-violation classes — the
Wilson–Grady 14-tone completion rail holds. Across all five seeds: **0/60
dekanies are proper and 0/60 are CS.** Hexanies: classic 10/30 non-improper
(8 strictly proper = classes {1,3,5,7}, {1,7,9,11}, {3,7,9,11}, {5,7,9,11};
proper {1,3,5,9}); flagship 6/30 (3 classes: {7,9,11,15}, {1,9,11,29},
{1,7,9,11}); {13,17,21,23,25,27} 6/30; {1,3,13,21,23,25} 4/30;
{1,3,11,13,25,27} 0/30. Propriety does not descend from the eikosany to its
subsets — it INVERTS: the improper classic has more proper hexanies than the
first strictly proper eikosany.

**H-SM4 — rails: (a) KEPT at 2¢, REFUTED-and-explained at 3¢; (b) SPLIT;
(c) KEPT with a correction; (d) KEPT.** (a) At 2¢ tempered ≥ exact for
P and S on all 360 rows. At 3¢, 68 rows have tempered < exact — every one
has `degenerate_dropped` > 0 and raw ≥ exact: the frozen scorer's per-
triple ε-guard (SPEC constraint 2) drops triples whose P/S/G labels are not
ε-separable, and the guard widens with ε; "survival vs the exact count"
must be read on raw counts at ε ≥ 3. (b) Hexany exact-survival at 2¢:
classic 30/30 KEPT; flagship 28/30 REFUTED — hexany(1 in, 9 out)/(9 in,
1 out) = CPS(4,2){7,11,15,29} overshoots 2 → 3; {13,17,21,23,25,27} 20/30,
the two {1,3,…} winners 28/30. (c) 75/75 two-in tetrads have P ≥ S and
75/75 IN/OUT tetrad pairs swap exactly (harmonic vs subharmonic) — KEPT;
but the brief's premise "tetrads are trivially all-triads-present" is
FALSE under the anchored scorer: 10/75 harmonic tetrads have exact
P = S = 0, the modal value is (P,S) = (1,0) (24/75), max (5,2). (d) 60/60
dekanies have exact P ≠ S; classic dekany exact P+S mean 27.5, range
[18, 41] (predicted [15, 35]) — the richest is the drop-11 = 1-3-5-7-9
dekany at 25+16 = 41. The CS-winner seeds' dekanies are harmonically thin:
flagship mean 10.5 [6, 12], {13,…,27} 7.5 [3, 9], {1,3,13,21,23,25} 10.0,
{1,3,11,13,25,27} 10.8 — roughly a third of the classic.

**H-SM5 — SPLIT, and the split is more useful than a clean verdict.**
Spearman (average ranks) melodic-first vs harmonic-first over 12
dekanies: classic 0.373 (< 0.5, KEPT); flagship 0.650 (≥ 0.5, REFUTED —
but with only 2 distinct melodic keys among 12: the drop-29 pair vs ten
tied, so one pair carries the whole ρ); {13,…,27} 0.390 (2 distinct keys);
{1,3,13,21,23,25} and {1,3,11,13,25,27}: ONE distinct melodic key — the
melodic axis is fully degenerate on their dekanies, ρ = 0 by convention
(vacuous). Pooled 60 dekanies: ρ = −0.283 (KEPT); classic 30 hexanies
0.315 (KEPT). CS-first vs harmonic pooled: −0.492. Reading for G-013: where
the frozen melodic axis discriminates at all, it disagrees with the
harmonic axis (weakly positive within the classic, negative pooled) — but
the sharper fact is that on coincidence-free seeds it does not
discriminate among dekanies.

**Orderings, classic {1,3,5,7,9,11} (top 3; IN/OUT twins collapsed):**
dekanies melodic-first: drop-5 = CPS(5,2){1,3,7,9,11} (6 classes/10,
improper 6, CS viol 14, P/S 16/11 at 3¢) > drop-1 {3,5,7,9,11} (7,
improper 6, viol 12, 14/10) > drop-11 {1,3,5,7,9} (7, improper 6, viol 12,
25/16); harmonic-first: drop-11 (25+16 = 41) > drop-7 {1,3,5,9,11}
(19+13; improper 8, viol 22) > drop-9 {1,3,5,7,11} (16+11); CS-first:
drop-1 (12) = drop-11 (12) = drop-9 (12; but 9 gap classes/10) — ties
broken by gap_classes/N. Hexanies melodic-first: {1,3,9,11} (the only
3-class hexany — improper) > {5,7,9,11} > {3,7,9,11} (strict, 4 classes);
harmonic-first: {1,3,5,9} (P 9, proper, NOT CS) > {1,3,7,9} (7, improper,
not CS) > {1,3,9,11}; CS-first = melodic-first here.
**Flagship {1,7,9,11,15,29}:** dekanies melodic-first = CS-first: drop-29
= CPS(5,2){1,7,9,11,15} (improper 4, 8/11 at 3¢) > drop-1 (improper 8,
8/5) > drop-11 (improper 8, 4/3); harmonic-first: drop-29 (11+8 = 19)
> drop-15 {1,7,9,11,29} (9+4) > drop-1 (8+5). Hexanies melodic-first:
{7,9,11,15} (strict, P 1) > {1,7,9,11} (strict, P 3) > {1,9,11,29}
(strict, P 1); harmonic-first: {1,7,9,11} (3) > {7,9,11,29} (2, improper)
> {9,11,15,29} (2, improper).
**Spice (improper, top-third harmonic within kind):** classic — the
1-3-5-7-9 dekany (drop-11, 41 exact triads, 12 CS violations) and drop-7
{1,3,5,9,11} (32, 22 violations); hexanies {1,3,7,9} (7+7, not CS),
{1,3,5,11} (5+5), {3,5,7,9} (4+4); tetrads two-in {7,11}, {5,11}, {7,9}.
Flagship — every dekany is spice by definition (all improper); hexanies
{7,9,11,29}, {9,11,15,29}, {1,11,15,29}, {1,7,11,15} at 2+2. Full lists in
the summary JSON.

**.scl exports (21):** per seed the top dekany under each ordering
(deduplicated: classic 3 files — drop-5 melodic, drop-11 harmonic, drop-1
CS; every CS winner 2 files — melodic+cs coincide) and the top two distinct
hexanies under melodic-first. Classic hexany picks: hexany(5 in, 7 out)
= 5·{1,3,9,11} (3 gap classes, improper — the gap_classes/N-first lens
prefers it to the strictly proper 4-class ones; a deliberate provocation
for the ear) and hexany(1 in, 3 out) = {5,7,9,11} (strictly proper).

**POST-HOC lenses (not pre-registered):**
1. **The generic dekany fingerprint.** 22 of the 30 dekany classes in the
   census — all 24 classes of the four CS-winner seeds except flagship
   drop-29 (improper 4) and {13,…,27} drop-13 (improper 6) — share ONE
   frozen-melodic profile: 6 gap classes (2.370951 bits), improper (8
   violating span pairs), exactly 12 exact CS-violation classes. Controls
   CPS(5,2){31,37,41,43,47} and {17,19,23,29,31} reproduce it exactly;
   {1,3,5,7,11} gives 9 classes/12 violations, {101,103,107,109,113} 8/16.
   So at the dekany level M1/M2 are functions of the seed pitch-ARRANGEMENT
   class, not of the seeds' harmonic identity, and only exact coincidences
   (composite 9 in the classic) move them. Minimum exact CS violations over
   all 60 dekanies: 12. Conjecture for a follow-up (CS-DEK-001?): no
   CPS(5,2) of five distinct odd seeds is CS — each seed ratio b/c occurs
   three times as a dekany interval (ab/ac, db/dc, eb/ec) and generically
   subtends different spans; Wilson–Grady's 14-tone completion is the
   constructive witness.
2. **ε-guard at 3¢** (H-SM4a): the 68 tempered-below-exact rows are 100%
   guard-explained (raw ≥ exact on all 68).

**Kept.** Runner, tests, receipts stand; both frozen scorers untouched. What
this hands the G-013 brainstorm: (i) IN/OUT dekanies are inversions — score
6 classes, not 12; (ii) no dekany here is proper or CS, and hexany propriety
inverts relative to the eikosany level — "subset-first" cannot mean "the
eikosany-level winner has the best subsets"; (iii) the frozen M1–M3 are
nearly blind at the dekany level for coincidence-free seeds — the
aggregator needs graded quantities (violation SIZES in cents, near-CS
distance, evenness), not class counts alone; (iv) the harmonic axis is
where CS-winner dekanies pay (a third of the classic's triads); (v) the
spice is real and named — the 1-3-5-7-9 dekany is the classic's richest
subset and its least melodic by every frozen lens.

## 2026-08-18 — BRIDGE-001b pre-registration (entry BEFORE any run)

**Contract:** the three named BRIDGE-001 follow-ups (LOG 2026-07-29 results:
"sweep k₂ instead of argmin", "tone-set minimax … the obvious future tuning
lens", and SPEC §BRIDGE-001 design decision 2's "two-gap-ness becomes an
OBJECTIVE, not an assumption"). Same object as BRIDGE-001 in every other
respect: EG4 = tesseract on {1,3,5,7} (16 formal vertices, 8 distinct tones
= divisors of 105), hexany CPS(4,2) + both tetranies as embedded subsets,
hosts = rank-2 temperaments at N ∈ 7..22 (vals = patent ± 1 per odd
coordinate), the 63-comma enumeration, Marcus's monotonicity filter FIRST,
strict MOS-window containment with the MOS-LAT-001 anchor sweep, frozen
triads v1.1.0 `score_tempered` (ε = 2¢, max_span 1200¢) for survival, frozen
melodic v0.1.0 for the host window. Runner `bridge001b.py` IMPORTS
`bridge001.py`'s enumeration, val/comma/nullspace/HNF machinery,
monotonicity filter, host/anchor receipt and scoring conventions read-only
(no re-derivation); receipts `results/bridge001b.jsonl` +
`results/bridge001b_summary.json`; `bridge001.jsonl` is NOT rewritten.
Note: SPEC's other BRIDGE-001b clause (filler-set enumeration on the
generator chain — "CPS image indices + filler set") is NOT run here; it is
a separate design and is deferred to BRIDGE-001c so this run stays a clean
three-filter variant of BRIDGE-001. Both frozen pins verified before
writing this entry (scorer 1a840af9…9b592, melodic a16f162b…7535).

**Rail (must reproduce BRIDGE-001 bit-for-bit before anything else):** with
k₂ = argmin (bridge001.choose_completion) and prime minimax
(bridge001.minimax_generator), the rows tagged `rail` must yield exactly
BRIDGE-001's contained Pareto front (`results/bridge001_summary.json`):
orwell-22 ⟨22,35,51,62⟩ g = 271.3854¢, max tone err 2.727139¢, hexany P =
2; miracle ⟨19,31,43,53⟩ / ⟨20,32,46,56⟩ / ⟨21,33,49,59⟩ g = 116.5878¢,
max tone err 6.857995¢, hexany P = 3 — same numbers to the printed 6
decimals, same k₂, same mapping, same aliases; also mothra 5.678¢ and
meantone 7.672¢ as dominated contained rows. The summary carries a
`rail_reproduced` boolean computed by direct comparison against the
BRIDGE-001 summary file (front rows: N, val, k2, mapping, generator_cents,
max_error_cents, collision_count, hexany_image_P,
posthoc_hexany_full_recovery_eps).

**H-B3 — k₂ sweep (completion is a design axis, not an argmin).** For every
monotone (comma c, val v, N) pair, EVERY primitive kernel-box monzo k₂
independent of c is admitted; rows are deduped by (mapping M = HNF of the
saturated left-kernel of [c,k₂], N, v), with `comma_aliases` = every
enumerated comma in ker M and `k2_witnesses` = every k₂ producing M for
that (c,v). Scale probe (counts only, no scoring, run 2026-08-18 to size
the sweep): 1615 monotone (c,v) pairs, **33,711 distinct (M, N, v) rows**
(mean 124 temperaments per val, max 921), 1.6 s to enumerate — so NO
pruning is applied; the row count is itself a prediction (reproduce
33,711). Predictions, tuning = prime minimax (BRIDGE-001's), front =
non-dominated contained rows in (hexany image P at ε=2 ↑, collision count ↓,
max tone error ↓), dedup by (M, N, v):
- Named mid-accuracy temperaments the argmin skipped now APPEAR as scored
  rows: **magic** (225/224 ∩ 245/243, ⟨1 0 2 −1],⟨0 5 1 12]) at N = 19
  (patent ⟨19,30,44,53⟩, anchor interval [0,0] — chain span exactly 19) and
  N = 22 (patent, anchor ∈ [−3,0]), CONTAINED, prime minimax 5.15¢, max
  tone error ≈ 9.0¢ (on 21/16: e3 + e7 = 3.87 + 5.15), hexany P ≤ 1;
  **garibaldi** (32805/32768 ∩ 5120/5103) at N = 12 (patent) and N = 17
  (⟨17,27,39,47⟩, a7 = patent −1), both UNCONTAINED (EG4 chain span 24: 7
  needs 14 fifths, 35/32 needs 22 — no N ≤ 22 window holds it), so
  garibaldi cannot enter the contained front at any tuning; also expected
  as contained-but-dominated: pajara-22 (period 600¢, span 6, tone err ≈
  18¢ on 21/16), superpyth-17/22, porcupine-15/22, keemun-19, negri-19,
  lemba-16, godzilla-19 — all with max tone error > 9¢.
- **The prime-minimax contained front is UNCHANGED**: exactly BRIDGE-001's
  four rows (orwell-22 P=2 2.727¢; miracle 19/20/21 P=3 6.858¢). Reason: per
  (c,v) the sweep only adds temperaments LESS accurate than the argmin one,
  and entering the front needs P ≥ 4, or P = 3 with tone error < 6.858¢, or
  tone error < 2.727¢ — none of the named entrants qualifies (magic P ≤ 1).
  **P-COMMA family call holds: 225/224 owns every non-dominated contained
  row.** Falsifier: any front row whose aliases exclude 225/224 — predicted
  none; if one exists it is named in the results entry.
- Max hexany P at ε=2 over ALL contained rows stays 3 (miracle) under prime
  minimax.

**H-B4 — tone-set minimax (tune to the 8 EG4 images, not the 3 primes).**
Second tuning per (M, N, v): pure octaves, period exactly 1200/x, G = the
exact piecewise-linear minimax of max over the 8 distinct EG4 tone monzos
(octave-reduced; 1/1 contributes the zero line) of |T(t) − cents(t)|, same
crossing solver as bridge001.minimax_generator generalized to an arbitrary
monzo list, tie → smaller G. Both tunings are measured on every row (both
sets of per-tone errors, score_tempered, subsets, host step classes, ε
regimes, hexany full-recovery ε). Hand-derived predictions (pins, written
before the solver exists; the linear-in-δ error model, δ = G − G_prime):
- **miracle**: prime-minimax errors e3 = e5 = −2.428, e7 = −2.002 (sign-
  coherent) give e21 = −4.430, e105 = −6.858; the tone-set optimum
  balances e21 (slope +4) against e105 (slope −3) at δ = −0.347¢ →
  **max tone error 5.82¢** (e21 = e105 = −5.82; e3 = e15 = −4.51, e5 =
  0.00, e7 = e35 = −1.31). NOT below 4¢ — the orchestrator's guess is
  refuted by derivation: 3/2 (slope +6) and 105/64 (slope −3) pull
  opposite ways and 21/16 caps the gain. Drop 6.858 → 5.82 (−1.04¢).
- **orwell-22**: mixed-sign e3 = −2.257, e5 = −0.470, e7 = +2.257 give
  e15 = −2.727 (slope +4) vs e7 (slope +8): δ = +0.039¢ → **max tone
  error 2.570¢** (Δ = −0.157¢, "within 0.3¢" as the orchestrator guessed);
  e3 = −1.983, e5 = −0.588, e7 = +2.570, e21 = +0.588, e35 = +1.983,
  e105 = 0.000.
- Other named contained rows: meantone-17/19 7.672 → 4.81¢; magic-22
  9.02 → 5.36¢; mothra-21 5.678 → 5.48¢. So under tone-set tuning the
  ERROR ranking of named contained hosts becomes orwell 2.57 < meantone
  4.81 < magic 5.36 < mothra 5.48 < miracle 5.82 — miracle falls from
  second to last. Whether the FRONT flips is decided by hexany P (below).
- **Hexany survival under retune (H-B2 strict revival test).** The frozen
  scorer's tempered test is translation-invariant (middle vs mean of the
  outer tones), so survival tracks INTERVAL errors inside the hexany, not
  absolute tone errors vs 1/1. Hand-checked triads (base (6,6): 5:6:7,
  30:35:40, 28:35:42, 21:28:35, and the two octave-spanned 5:15/2:10 and
  7:21/2:14 whose deviation is exactly −e3):
  · miracle prime: e3 = −2.43 fails the two e3-triads and 21:28:35 at 2¢
    (dev ≈ 2.43) → P = 3, recovers at ε = 3 ✓ (matches BRIDGE-001);
    miracle tone-set: e3 = −4.51, 6/5 = −4.51, 7/6 = −3.20 → only 30:35:40
    survives → **P = 1, full (6,6) recovery moves 3 → 5¢**. H-B2 is NOT
    revived by the retune; the deficit widens.
  · orwell prime: e3 = −2.257 fails both e3-triads → P = 2 ✓ (matches);
    orwell tone-set: e3 = −1.983 → both e3-triads pass with 0.017¢ margin
    → **P = 4** (5:6:7 at 3.24¢ and 30:35:40 at −3.4¢ still fail); full
    recovery stays at ε = 4. (Margin caveat: 1.983 vs 2.000 — a float
    surprise here would give P = 2, and is recorded as such.)
  · magic-22 tone-set: 5/3 = −8.2, 7/5 = +7.9 → P = 1; meantone tone-set
    P = 0; mothra tone-set P ≤ 1.
- **Predicted tone-set contained front: orwell-22 ALONE** (P = 4, 2.570¢,
  0 collisions) — miracle (P = 1, 5.82¢) becomes DOMINATED by orwell and
  drops off; no contained row reaches P ≥ 5 or error < 2.570¢. Verdict
  criteria: "flip" = any change in front membership or order vs the prime
  front — predicted YES (miracle exits), by domination, not by re-ranking.
- **Both outcomes' meaning for H-B2, pre-registered:** if ANY contained
  injective row reaches full hexany (6,6) at ε = 2¢ under the tone-set
  tuning, H-B2 is REVIVED under the strict reading — the 2¢ bridge exists
  and BRIDGE-001's refutation was an artifact of the pre-registered tuning
  choice (report the row, and it becomes the flagship). If none does
  (predicted), BRIDGE-001's refutation is ROBUST to the tuning objective:
  the one-cent gap is structural at N ≤ 22, and absolute-error tuning is
  the wrong lens for survival (H-B6).

**H-B5 — two-gap-ness as an objective column.** For every CONTAINED row and
BOTH tunings, the anchored N-note host window (host_receipt's `notes`:
npp generator steps from the used anchor × x periods) is scored with the
frozen melodic.py (score_melodic: gap_class_count at ε_gap 0.5¢, is_cs at
ε_CS 0.5¢, propriety classification); `gap_classes` is a COLUMN in the
front, never a filter. Predictions:
- Front rows: orwell-22 → 2 gap classes (22 is an orwell MOS: L 72.0¢ ×9,
  s 42.5¢ ×13, L/s 1.70 → STRICTLY PROPER, CS); miracle-21 (blackjack) →
  2 classes (L 82.5¢ ×10, s 34.1¢ ×11, L/s 2.42 → IMPROPER, CS);
  miracle-19 and -20 → 3 classes (34.1, 82.5, 116.6¢), improper. So of
  the prime front's four rows exactly two are true 2-step MOS, and the
  only strictly-proper bridge host is orwell-22.
- No 3-step contained candidate strictly beats the best 2-step one on
  hexany P at ε = 2 (prime: 3-step max = 3 = miracle-19/20 ties
  blackjack; tone-set: 2-step orwell-22 holds P = 4 and no 3-step row
  exceeds it). Reported either way as the (gap_classes × P) table.
- Descriptive (no verdict): distribution of gap classes over all contained
  rows, and the joint (2-step ∧ proper ∧ P ≥ 2) count.

**H-B6 (own, sharper question): the absolute-error and survival objectives
are NOT aligned.** For the BRIDGE-001 front rows, `hexany_interval_maxerr`
(max |error| over the 15 pairwise hexany-image intervals, translation-
invariant) is the quantity survival tracks: miracle prime 2.86¢ → tone-set
4.51¢ (worse: recovery 3 → 5); orwell prime 4.51¢ → tone-set 4.55¢
(unchanged: recovery 4 → 4, but P 2 → 4 because e3 crosses under the 2¢
threshold). Prediction: over ALL contained rows, the tone-set retune lowers
max tone error in every row (by construction, ≤ prime value) but does NOT
raise the contained-set maximum hexany P at ε = 2 above 4, and lowers P on
at least one BRIDGE-001 front row (miracle: 3 → 1). Kept iff both halves
hold. Consequence if kept: a survival-aware tuning (interval-minimax over
the hexany image, or a direct triad-deviation minimax) is the right next
lens — NOT run here (not pre-registered), named for BRIDGE-001c.

**Constants (locked):** N ∈ 7..22; vals patent ± 1; commas =
bridge001.enumerate_commas() (63); kernel box |e3| ≤ 8, |e5| ≤ 5, |e7| ≤ 4;
ε_tempered = 2.0¢; recovery/regime sweep ε ∈ 1..15; melodic ε_dedup 0.01¢,
ε_gap 0.5¢, ε_CS 0.5¢, ε_prop 1e-9¢ (melodic.py defaults); dominance =
(P ↑, collisions ↓, max tone error ↓); FLOAT_EPS 1e-6 for host step
classes (bridge001's). Names for temperaments are labels only, resolved
from comma pairs at load (miracle 225/224∩1029/1024, orwell ∩1728/1715,
magic ∩245/243, garibaldi 32805/32768∩5120/5103, meantone 81/80∩126/125,
mothra 81/80∩1029/1024, pajara 50/49∩64/63, …); an unnamed mapping is
reported by its HNF.

**Determinism:** python3.12 stdlib only, no randomness, sorted iteration
everywhere; run twice, receipts must be byte-identical (sha256 recorded in
the results entry). Tests `tests/test_bridge001b.py` green BEFORE the first
run (tone-set solver pins for miracle 5.82¢/δ −0.347 and orwell 2.570¢/δ
+0.039 at 2 decimals; sweep dedup; melodic host scoring on a known MOS;
rail equality on the miracle/orwell rows; label resolution). Frozen files
untouched; freeze checks A run before and after.

## 2026-08-18 — BRIDGE-001b results + verdicts

**Run:** `bridge001b.py` (~95 s, bit-identical across two runs: jsonl
sha256 fec91947…4f78, sidecar b8844db1…1894, summary 6043f29e…b8bd);
receipts `results/bridge001b.jsonl` (2,903 FULL rows = every contained or
rail (argmin) row), `results/bridge001b_uncontained.jsonl.gz` (30,808
compact rows: uncontained non-rail — no bridge can live there; the full
33,711-row dump was 77 MB), `results/bridge001b_summary.json`. Tests
20/20 new (lattice suite 130/130) green before the first run, including
the hand-derived tone-set pins; freeze checks A OK on both pins before and
after (scorer 1a840af9…9b592, melodic a16f162b…7535); frozen files
untouched. Enumeration: 63 commas, 2205 (c,v) pairs, 590 monotonicity
rejections, 1615 monotone pairs → **33,711 distinct (mapping, N, val)
rows exactly as the scale probe predicted**, 19,818 distinct rank-2
mappings, 1,880 contained rows (791 distinct contained mappings), 1,101
rail rows (78 contained rail rows = BRIDGE-001's 78 contained
temperaments).

**Rail — REPRODUCED bit-for-bit.** The prime-tuned rail front equals
BRIDGE-001's summary front on every compared field (4 rows: orwell-22
2.727139¢ P=2, miracle-19/20/21 6.857995¢ P=3; same k₂, mapping,
generator, collisions, recovery ε, and comma_aliases == rail_commas);
mothra-21 5.678412¢ and meantone-17/19 7.672444¢ reappear as dominated
contained rail rows. `rail.bridge001_comparison.reproduced = true`.

**The unpre-registered discovery that reframes H-B3/H-B4/H-B6 verdicts:
the count-based survival criterion is unsound for grossly detuned
images.** The pre-registered fronts (P at ε=2 ↑, collisions ↓, max tone
error ↓, NO error cap) admitted rows the k₂ sweep surfaced with 64–155¢
tone errors and P = 5–7: e.g. ⟨1 0 1 2],⟨0 4 3 2] (kernel comma 49/48
only, g = 498.3¢, max tone error 119.2¢) at N = 12/17 with hexany
"P = 5" (its 3/2 is 91¢ sharp; the image is a different scale whose
ACCIDENTAL near-arithmetic triples out-count the hexany's eight faces),
and two 155¢ rows with P = 7 and 2 collisions. BRIDGE-001 never met this
because argmin picked accurate temperaments. Two POST-HOC lenses, labelled
in the runner and summary, changing no pre-registered field: (a)
**in-budget fronts** — restrict to max tone error < 15¢ (BRIDGE-001's own
ε_bridge regime: over-budget rows are by definition not bridges); (b)
**triad-identity lens** — `posthoc_identity_P/S`: how many of the hexany's
OWN twelve labelled triads (enumerated on the exact rational path,
`posthoc.hexany_base_triads`) keep their label in the image at ε (frozen
`classify_cents_triple`, same octave placement). Count and identity lenses
agree on FULL survival for every in-budget contained row (0 disagreements;
10 over-budget ones disagree) and on the P/S counts themselves for every
in-budget row below 13.7¢ (the only mismatches are seven unnamed rows at
13.7–14.9¢ where count P = 1, identity 0 — accidental coincidences begin
around there); the identity lens exposes the artifacts (the 119¢ "P = 5"
rows have identity P = 0; the 155¢ "P = 7" rows identity 2; the 64¢
schismatic-with-7=3-fifths rows keep identity 4 because their 5-limit
faces are honestly accurate). Only
16 (prime) / 45 (tone-set) of the 1,880 contained rows are in-budget:
**the k₂ sweep is 98% junk temperaments — the argmin was hiding a
population, not a front.** Verdicts below give the pre-registered letter
first, then the in-budget/identity reading.

**H-B3 (k₂ sweep) — letter FALSIFIED, substance KEPT.**
- Letter: the prime front is NOT unchanged — the two 119¢ ⟨1 0 1 2],
  ⟨0 4 3 2] rows (N = 12 ⟨12,20,27,34⟩, N = 17 ⟨17,28,38,48⟩; aliases
  {49/48}) join it, so "225/224 owns every non-dominated contained row" is
  falsified in letter — the first non-225/224 front row is named. Under
  the in-budget lens (and under the identity lens, budget or not, at
  ε = 2), the prime front is EXACTLY BRIDGE-001's four rows and 225/224
  owns all of them. In-budget contained max hexany P = 3 (miracle), as
  predicted; unrestricted max is 5 (artifact).
- Named entrants, all as predicted: **magic** appears at N = 19 (patent,
  anchor [0,0]) and N = 22 (patent, anchor [−3,0]), contained, prime
  minimax 5.15¢, max tone error **9.017¢** (pred. 9.02; on 21/16), tone-set
  **5.364¢** (pred. 5.36), hexany P = 1 (pred. ≤ 1), recovery ε = 8 —
  dominated under both tunings; magic-16 (uncontained) turns out to be a
  rail row already. **Garibaldi** appears at N = 7, 12, 17 (⟨17,27,39,47⟩,
  a7 = patent−1 as predicted, plus N = 7 unpredicted), all UNCONTAINED
  (chain span 24 as predicted) — and all three are rail rows: BRIDGE-001
  had scored garibaldi (2.71¢, hexany P = 4 at 2¢, full at 3¢!) but its
  window (24 > 22) hid it; garibaldi is the best-surviving mid-accuracy
  temperament in the sweep and simply needs N ≥ 29. Also contained-but-
  dominated as predicted: pajara (18.2¢, 9 vals), superpyth-15/17/22
  (28.4¢), porcupine-15/16/21/22 (18.2¢), keemun (20.5¢), negri (31.6¢),
  lemba (30.4¢), godzilla-14/15/19 (19.1¢); one unpredicted in-budget
  contained newcomer: **doublewide-22** (50/49 ∩ 875/864, period 600¢,
  ⟨22,35,51,62⟩, 10.2¢, hexany P = 3 = identity 3, 2-step STRICTLY PROPER,
  CS) — dominated by miracle on error, but the only in-budget row besides
  orwell that is simultaneously 2-step, proper and P ≥ 2 under prime
  tuning.

**H-B4 (tone-set minimax) — KEPT in every derived number; front flips as
predicted; H-B2 NOT revived.**
- miracle: max tone error 6.857995 → **5.817315¢** (pred. 5.82; δ =
  −0.3469¢, secor 116.5878 → 116.2409¢; e5 goes to exactly 0.000, e3 =
  e15 = −4.510, e21 = e105 = −5.817). NOT below 4¢ — the orchestrator's
  guess is refuted, the derivation held.
- orwell-22: 2.727139 → **2.570508¢** (pred. 2.570; δ = +0.0392¢, g
  271.3854 → 271.4246¢; e3 = −1.983, e7 = +2.571, e105 = 0.000).
- Named error ranking under tone-set: orwell 2.571 < meantone 4.815 <
  magic 5.364 < mothra 5.482 < miracle 5.817 — exactly the predicted
  order; miracle falls from second to last.
- Hexany survival under retune (identity lens confirms every hand-checked
  deviation): miracle P 3 → **2** (pred. 1: the 21:28:35 face survives at
  −1.69¢, hand estimate was −2.7), full (6,6) recovery **3 → 5¢** (pred.
  5; the two octave-spanned faces sit at exactly |e3| = 4.510¢);
  orwell P 2 → **4** (pred. 4; the two e3-faces pass at 1.983¢ — the
  0.017¢ margin held), recovery stays 4 (5:6:7 at 3.24¢, 30:35:40 at
  −3.42¢). Doublewide 3 → 3; magic 1 → 1; mothra 2 → 2; meantone 1 → 1.
- **Tone-set in-budget front = orwell-22 ALONE** (P = 4 = identity 4,
  2.570¢, 0 collisions, 2-step, strictly proper, CS) — miracle is
  dominated by orwell and exits; `front_flipped = true` in letter too
  (the letter front adds the 64¢/155¢ artifacts, identity P 4/2). No
  contained row reaches P ≥ 5 in budget or error < 2.570¢.
- **H-B2 strict revival: ZERO rows** under either tuning
  (`h_b2_revived_rows = []`; identity full (6,6) at ε = 2 among contained
  rows: 0/0). BRIDGE-001's refutation is ROBUST to the tuning objective:
  the one-cent gap is structural at N ≤ 22, and (H-B6) absolute-error
  tuning is the wrong lens for survival. Addressing-only (uncontained)
  best stays ennealimmal-18: 0.204¢ prime → 0.132¢ tone-set, span 8 > 2.

**H-B5 (two-gap objective) — KEPT (one propriety miss).** Front rows:
orwell-22 → 2 gap classes (42.47¢ ×13, 71.99¢ ×9; L/s 1.70), STRICTLY
PROPER, CS ✓; blackjack (miracle-21) → 2 classes (34.12 ×11, 82.47 ×10;
L/s 2.42), IMPROPER (10 violating span pairs), CS ✓; miracle-19 → 3
classes (34.12, 82.47, 116.59), improper, NOT CS (18 violations) ✓;
miracle-20 → 3 classes, NOT CS, but **PROPER** (0 violations; predicted
improper — with a single 116.6¢ step among 10+9 the spectrum still nests).
So exactly two of BRIDGE-001's four front rows are true 2-step MOS and the
only strictly-proper bridge host is orwell-22, as predicted. 3-step vs
2-step: in budget, prime 3-step max P = 3 (miracle-19/20/22) ties the
2-step max 3 (blackjack); tone-set 2-step max 4 (orwell) beats 3-step max
2 — no 3-step contained candidate beats a 2-step one on the harmonic side
✓ (unrestricted table: 2-step and 3-step both max 5/7, the over-budget
artifacts). Gap-class distribution over all 1,880 contained rows: 1-step
11/26, 2-step 928/941, 3-step 941/913 (prime/tone-set) — 49% 2-step,
inside the predicted 30–60%; in budget 11+5 / 26+19. Joint (2-step ∧
non-improper ∧ P ≥ 2, in budget): prime {orwell-22, doublewide-22};
tone-set adds ⟨1 2 2 3],⟨0 9 −7 4] at N = 21/22 (225/224 ∩ 12288/12005,
10.9¢, P = 4, strictly proper). Interesting corollary for the design
paradigm: retuning does not change gap-class counts on any front row
(the melodic column is tuning-robust at these δ), so two-gap-ness and
survival can be optimized independently.

**H-B6 (objectives not aligned) — letter FALSIFIED by the same artifact,
KEPT in budget.** Tone-set lowers max tone error on all 33,711 rows ✓
(by construction). Contained max hexany P: unrestricted 5 → 7 (artifact
rows; letter falsified), in budget 3 → 4 (orwell) ✓ not above 4. A
BRIDGE-001 front row loses P ✓ (miracle 3 → 2, recovery 3 → 5).
`hexany_interval_maxerr` (translation-invariant, the quantity the frozen
test sees): miracle 2.855 → 5.817¢ (hand: 2.86 → 4.51 — I omitted the
21/16-vs-5/4 pair, whose error becomes 5.817 once e5 = 0), orwell 4.984 →
5.141¢. Reading: minimizing absolute error vs 1/1 can move the hexany's
internal intervals either way; orwell gains survival, miracle loses it.
The survival-aware tuning (interval or direct triad-deviation minimax) is
named for BRIDGE-001c, unrun.

**Vs the BRIDGE-000 standard:** unchanged corners — Wilson's pitch-just
corner (0¢, 7 collisions, 100% survival) and the tempered-faithful corner,
now sharpened to orwell-22 at 2.570¢ with 4/6 identity faces at 2¢ and all
6 at 4¢, 0 collisions, strictly proper 2-step host. Nothing at N ≤ 22
reaches full survival at 2¢ under any tuning; the sweep of 33,711
temperaments finds no third corner.

**Kept.** Runner, tests, receipts stand; frozen scorers untouched. Post-hoc
additions (in-budget fronts, identity lens, `posthoc.*` in the summary,
`posthoc_identity_*` per tuning) are labelled in code and here. Method
note for BRIDGE-002 (EG6, 2-comma kernels): any Pareto front over a k₂
sweep must be error-capped or identity-scored — the count-based P is not
a survival measure once tone errors exceed ~10¢. Gate G-021 (ledger PR
#37) proposed row in the PR body.

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

## 2026-08-19 — EAR-ε pre-registration (entry BEFORE any stimulus generation)

**Question:** at what detuning does MARCUS's ear lose the "lock" — the
fused, reinforcing quality of a proportional/subcontrary triad? ET-001
fixed the machine side: 12-EDO first supports the full patent 4:5:6/10:12:15
pair at ε = 14.859022¢ (the cultural epsilon) and locks its power chord at
1.955001¢ (= its fifth error, exactly). The literature anchor
(CLAUDE.md, "Tolerance and Perception") puts human pitch discrimination at
roughly 5–10¢ in musically relevant registers. EAR-ε builds the detuning
ladder that straddles both numbers and the blinded protocol for Marcus to
locate his own thresholds in one sitting. This entry pre-registers design,
stimuli, blinding, response protocol, analysis, and falsifiable
predictions BEFORE any stimulus is generated; the listening results are a
standing ear-check gate (G-025, QUEUED in ledger PR #37) and come back
later, exactly as G-006's did. This is a human-subject-style
pre-registration: nothing in the analysis may be chosen after Marcus has
heard a note.

**Stimulus form (decision + justification).** Each rung is a MINIMAL .scl
tuning — root at 1/1 (degree 0, implicit), the triad's tones as the only
other degrees, octave 2/1 — NOT a full 12-note tuning with one triad
detuned. Justification: (i) control — the percept under test is the fused
triad, and context tones would add uncontrolled beats and melodic
distraction; (ii) portability — any MTS-ESP synth renders exactly the
triad, three adjacent MIDI keys from the root sound it, no navigation
skill required; (iii) precedent — G-002/G-006 both used small, decisive,
single-percept stimuli. Root maps to MIDI 60 at Wilsonic's default
reference frequency (~261.63 Hz), left untouched for every rung, so
register is constant and beat rates are comparable across rungs.

**Stimulus families and ladders (locked; cents exact to the shown
precision, generated from 1200·log2 of the just ratios).** Just anchors:
M3 = 386.313714¢ (5/4), m3 = 315.641287¢ (6/5), P5 = 701.955001¢ (3/2),
δ_pc = 1200·log2(3) − 1900 = 1.955001¢ (the exact 12-EDO fifth error).
- **Family A (major prototype 4:5:6, third detuned):** degrees
  {0, M3 + δ, P5}; δ ∈ {0, ±2, ±5, ±8, ±11, ±14.86, ±18, ±22}¢ —
  15 rungs. The ladder brackets the 5–10¢ literature band (rungs 2, 5, 8,
  11) and includes the cultural epsilon literally (±14.86) plus
  headroom above it (±18, ±22).
- **Family B (power chord 2:3:4, fifth detuned):** degrees {0, P5 + δ}
  (canonical 2-degree scale; keys 60-61-62 sound root–fifth–octave);
  δ ∈ {0, ±1, ±1.955001, ±3, ±5, ±8}¢ — 11 rungs. δ = −1.955001 IS the
  12-EDO fifth (700.000000¢); the ladder brackets ET-001's 1.955 lock.
- **Family C (subcontrary/minor prototype 10:12:15, third detuned):**
  degrees {0, m3 + δ, P5}; same 15-rung δ ladder as A. Included because
  minor lock-loss may differ from major, and that asymmetry would be a
  finding.
- **Family D (12-EDO anchors, 3 rungs):** the literal 12-EDO major
  (0, 400, 700), minor (0, 300, 700), and power chord (0, 700, 1200).
  These are the actual sonorities ET-001's thresholds describe; they tie
  the ladder to the phase diagram end-to-end.
44 stimuli total.

**Scorer rails (registered; the frozen scorer is the referee).** In
families A/B/C the detuned tone is exactly the mean tone of its class, so
the frozen classifier's deviation equals |δ| EXACTLY (the P condition
|1200·log2((fa+fc)/(2·fb))| is fb-linear and fa+fc is held fixed; dually
for S). Rails, verified by frozen `classify_cents_triple` per rung and
recorded in the manifest: for δ ≠ 0 the target class (P for A/B-as-2:3:4,
S for C and B-as-3:4:6 — the power chord carries BOTH labels at |δ|, its
3:4:6 reading being the subcontrary dual ET-001 recorded) is ABSENT at
ε = |δ| − 1e−6 and PRESENT at ε = |δ| + 1e−6; for δ = 0, present at
ε = 1e−6. Family D deviations must equal ET-001's numbers:
D-major P dev = D-minor S dev = 14.859022¢ (the (4,3)/(3,4) type pair),
D-power P dev = 1.955001¢ — each verified by the same ±1e−6 flip. Guard
separations (outer pairs 70.28–203.91¢) exceed every ε used, so no rung
is degeneracy-dropped. Additionally each rung's FULL scale is scored by
frozen `score_tempered` at the ET-001 grid ε ∈ {1, 2, 3, 5, 10, 14.86,
20}¢ and the counts stored in the manifest (joinable with et001.jsonl);
registered scale-level rail: crossing ε = |δ| the target class count
jumps by exactly +1 (families A/C; +1 in BOTH P and S for B). Known and
registered, NOT railed: (i) family A/C scales contain octave-inversion
triples (e.g. A's 3:4:5 reading at deviation ≈ 0.6255·|δ|, C's
15:20:24-ish at ≈ 43.8¢ + O(δ)) whose grid behavior is recorded as
scorer fact; (ii) the ±14.86 rungs sit within float noise of the 14.86
grid point under the strict-< comparison — their classification AT that
single grid ε is knife-edge, is recorded as whatever the scorer returns,
and carries no rail and no interpretive weight.

**Blinding (registered).** Filenames are opaque rung ids in PRESENTATION
order: eareps_B_01..11, eareps_A_01..15, eareps_C_01..15,
eareps_D_01..03. Within each family the rung order is shuffled by
`random.Random(20260819)` — seed 20260819, pre-registered here —
consuming the rng in listening-block order B, A, C, D. The .scl headers
carry NO provenance (unlike G-006): the δ value is the secret, and a
cents line is unavoidable, so the protocol doc instructs Marcus never to
open the files in a text editor. The δ assignment lives only in
results/eareps_key.json; the technical record (deltas, deviations, grid
classifications) lives in results/eareps_manifest.json. BOTH are sealed:
Marcus must not open either, nor this experiment's PR diff of those two
files, until his responses are written to results/eareps_responses.json.
Family identity (major/minor/power) is audible anyway and is not treated
as a secret; magnitude and sign of δ are.

**Response protocol (registered; plain version in
EAREPS_PROTOCOL.md).** One sitting, blocks in order B, A, C, D, files in
numbered order within a block. Same synth patch throughout: sustained,
harmonically rich, STEADY — no vibrato, chorus, unison detune, or delay
(those mask or fake beats); same playback chain throughout (note which).
Per rung: load the .scl (Wilsonic's Scala design via drag-and-drop, or
any MTS-ESP-respecting Scala host; ONE running Wilsonic instance —
MTS-ESP single-master rule), hold MIDI keys 60-61-62 together for at
least 5 seconds, twice; then write ONE verdict before moving on:
**locked** (fuses into a single reinforcing sonority) / **beating**
(audible waver or roughness, but the chord still reads as in-tune-ish) /
**broken** (the fusion is gone; it reads as mistuned). Optional per rung:
fusion rating 1–5 (5 = perfectly fused) and free notes. Replaying the
current rung is allowed; REVISING an earlier verdict after moving on is
not (commit-as-you-go, the G-006 write-then-unseal discipline). Responses
go in a copy of results/eareps_responses.template.json saved as
results/eareps_responses.json. Only after that file is written may the
key or manifest be opened.

**Analysis plan (registered — decided before any listening).** Per
family-direction (A-sharp, A-flat, B-sharp, B-flat, C-sharp, C-flat),
order rungs by |δ|. Let L = max |δ| with verdict "locked" (L = 0 if
none beyond the δ=0 rung... the δ=0 rung itself counts as locked
territory) and K = min |δ| with verdict "broken". **Threshold
T = (L + K) / 2** — the midpoint between the last "locked" and the first
"broken"; "beating" verdicts between them are the transition band,
reported descriptively. Censoring: if no rung is "broken", T is
right-censored (report "T > max rung"); if even the smallest nonzero
rung is "broken", T < that rung. Non-monotone verdicts (a "broken" below
a "locked") do not change the rule — T is still computed from max-locked
and min-broken — but are flagged. **Validity rule:** the δ = 0 rung of
each of A, B, C is a catch trial; if any δ = 0 rung is judged "broken",
that family's block is invalid and must be re-run on a fresh sitting
(the file order stays fixed; no new stimuli are generated).

**Falsifiable predictions (committed now):**
- **P-E1 (the cultural epsilon is cultural, not perceptual).** Marcus's
  major-third lock-loss lies BELOW 14.86¢ in both directions:
  T_A(sharp) < 14.86 AND T_A(flat) < 14.86, with the committed band
  **both T_A ∈ [6, 12]¢**. KEPT if both in band; WEAK-KEPT if both
  < 14.86 but either outside [6, 12]; REFUTED if either ≥ 14.86 (which
  would mean 12-EDO's major third is inside his lock tolerance and the
  "cultural" epsilon is perceptual after all).
- **P-E2 (fifths are far tighter).** T_B(sharp) ≤ 3¢ AND T_B(flat) ≤ 3¢.
  REFUTED if either exceeds 3¢. Sub-prediction **P-E2b:** the ±1.955001
  rungs (the 12-EDO fifth and its sharp mirror) are NOT "broken" (locked
  or beating) — i.e. for fifths, culture sits just inside perception,
  the opposite regime from thirds where culture (14.86) sits far above
  the predicted perceptual band.
- **P-E3 (sharp/flat asymmetry of the third, direction committed).**
  First-order combination-tone reasoning predicts NO asymmetry: for
  4 : 5·2^(±δ/1200) : 6 the two first-order difference tones split
  symmetrically about the root's octave (5+x−4 = 1+x vs 6−5−x = 1−x)
  and beat at rate ∝ |δ| regardless of sign. The committed asymmetry is
  therefore CULTURAL: a lifetime of 12-EDO's +13.69¢-SHARP major thirds
  should extend sharp tolerance. Prediction:
  **T_A(sharp) − T_A(flat) ≥ +1.5¢** (half the local rung spacing).
  REFUTED if the gap is < 1.5¢ (no asymmetry: the physics-symmetric null
  wins) or reversed (flat-tolerant: also a finding, and a strike against
  the acculturation account).
- **Exploratory, no commitment:** T_C vs T_A (minor vs major lock-loss
  asymmetry — either direction is a finding); family D consistency
  checks (P-E1 implies D-major and D-minor are heard non-locked; P-E2b
  implies D-power is not broken).

**Machinery (locked).** Generator experiments/lattice/eareps.py —
python3.12 stdlib only, deterministic (the one rng use is the
pre-registered seed above), no wall-clock fields anywhere; outputs
results/scl/eareps/*.scl (44 files), results/eareps_manifest.json
(sealed technical record incl. all rails and grid classifications),
results/eareps_key.json (sealed answer key),
results/eareps_responses.template.json (unsealed — the one file Marcus
copies). Two runs must be bit-identical on every output (diff recorded).
Frozen inputs read-only: triads scorer v1.1.0 (`classify_cents_triple`,
`score_tempered`, `mean_separation_cents`), melodic v0.1.0 untouched by
this experiment. Tests tests/test_eareps.py green BEFORE the first
generation run (ladder math, |δ|-deviation identity, per-rung scorer
flips, guard margins, .scl syntax and no-provenance blinding, shuffle
determinism, D-anchor deviations = ET-001's numbers). Freeze checks A on
both pins before and after. NOT in scope: any listening result, any
threshold — those are Marcus's, and land in a later results entry
against gate G-025.

**Scale expectation:** 44 tiny .scl files, one manifest, one key, one
template; seconds to generate. If it grows past that the design is wrong.

## 2026-08-19 — EAR-ε stimuli built (what was generated, NOT listening results)

**Run:** `eareps.py` (seconds; outputs bit-identical across two runs by
diff on all 44 .scl files, manifest, key, and template), stimuli
`results/scl/eareps/` (44 files), sealed technical record
`results/eareps_manifest.json`, sealed answer key
`results/eareps_key.json`, unsealed
`results/eareps_responses.template.json`, protocol
`EAREPS_PROTOCOL.md`. Frozen triads scorer v1.1.0 used read-only as the
referee; melodic v0.1.0 untouched. Lattice suite 159/159 green pre- and
post-run (29 new eareps tests), freeze checks A OK on both pins before
and after (scorer 1a840af9…9b592, melodic a16f162b…7535).

**Rails — all held, zero failures across 44 rungs.** Every family-A/B/C
rung's target class flips in frozen `classify_cents_triple` exactly at
ε = |δ| ± 1e−6 (the |δ|-deviation identity confirmed by the referee, not
just the mirror), including family B's BOTH readings — 2:3:4 proportional
on the sounding triple and 3:4:6 subcontrary on the fifth-below voicing
(P5+δ−1200, 0, P5+δ); build note: the S label lives on that octave-dual
triple, not on the sounding (0, P5+δ, 1200), which is where the +1
scale-count jump for S comes from. Full-scale `score_tempered` counts
jump by exactly +1 per target class across each threshold. Family D
anchors reproduce ET-001's numbers through an independent path:
12-EDO major P and minor S deviations both 14.859022¢, power chord P
1.955001¢, each scorer-verified at ±1e−6. Registered knife-edge behavior
recorded: at grid ε = 14.86 the A ±14.86 rungs land just at/above
(excluded, strict <) while the C ±14.86 rungs land just below
(included) — float noise exactly where the pre-registration said it
would be, no rail, no interpretive weight.

**Blinding executed as registered:** presentation shuffles from seed
20260819, rng consumed in block order B, A, C, D; filenames are
presentation-order ids (eareps_B_01..11, A_01..15, C_01..15, D_01..03);
.scl headers carry no provenance. The manifest and key are SEALED for
Marcus (both carry a _warning field; the protocol doc repeats it) until
results/eareps_responses.json exists.

**Not in this entry, by design:** any threshold, any verdict, any
listening note — those are Marcus's sitting, land in a later entry, and
decide P-E1/P-E2/P-E3 against gate G-025 (QUEUED in ledger PR #37).

**Run receipt:** 2026-08-19, python3.12 — lattice suite 159/159 OK
(25 melodic + 12 shadow001 + 18 moslat001 + 22 bridge001 + 37 moslat002
+ 16 et001 + 29 eareps), freeze checks A OK on both pins before and
after. Outputs bit-identical across two runs (diff on all 47 files).

## 2026-10-10 — coordination: branch merged with main; playground state is the input

**Context (not a run):** this branch (`research/lattice-recurrence-playground`)
forked from main at PR #41 and carried only the interactive playground
(`docs/lattice-recurrence-playground.html`). Main had since merged ten
research PRs (#42–#51: ET-001..003, MUR-001/002, SUBSET-MEL-000, BRIDGE-001b,
EAR-ε, EPS-TIER-001). Merged `origin/main` in (clean, no conflicts; both
frozen pins untouched). The two experiments below start from the playground
state Marcus pasted: hexany 1·3·5·7 seeded into Erv's 0.418935 recurrence
with order lift k = 2, ρ = 1 (direction 1), and the playground's best chain
fits for the hexany at 2¢ (direction 2). They are kept as SEPARATE
experiments per Marcus's instruction (2026-10-08, "program A / program B").
Reporting tier is LOCK 2¢ only (G-026: no tier above LOCK until G-025).

Scratch derivations for the pre-registrations below used INDEPENDENT code
(a mirror of the anchored classification; no frozen-scorer calls), per the
ET-003 convention. The one playground claim they overturn is recorded here
so it is on the record before any run: the playground's 0.5¢ grid search
reported no 2¢ chain fit for the hexany below N = 33; the exact minimax
sweep finds one at N = 22 (see CPSFIT-001).

## 2026-10-10 — MERU-001 pre-registration (entry BEFORE any implementation or run)

**Question (program A, Marcus 2026-10-08):** seed a generator's linear
recurrence with the tones of a CPS and watch pure harmony bend into pure
melody; compare generators on identical seeds. Erv re-seeded his own
recurrences with harmonic material (meruthree.pdf: 192, 336, 588, 1029 into
H[n] = H[n−1] + 4H[n−4]; 13, 23, 35, 53 into the LLSLS page), so this
continues his practice with CPS seeds. SPEC.md reserved the name MERU-001
for the CPS-seeded recurrence bridge (H-M2); the Rauzy-window view of
3-term recurrences is deferred to MERU-002.

**Construction.** Seeds: the hexany CPS(4,2){1,3,5,7} = {35/32, 5/4, 21/16,
3/2, 7/4, 15/8} (155.14, 386.31, 470.78, 701.96, 968.83, 1088.27¢). Sixteen
two-term recurrences H[n] = a·H[n−i] + b·H[n−j], the playground's fifteen
presets from Erv's pages plus the generator the playground selected in
direction 2 (fit351 = H[n−1] + 128H[n−6], 351.34¢, provenance: direction-2
output, included as a generator only). Two seedings, both chain-aligned
(seed m placed in the octave nearest G^m, the playground's default):
- **LIFT** — all six hexany tones are seeds. For order j < 6 the
  characteristic polynomial is multiplied by (x^k − ρ^k), k = 6 − j, ρ = 1
  (the playground's state: for 0.418935, H[n] = H[n−1] + H[n−2] − H[n−3] +
  32H[n−4] − 32H[n−6]). For j ≥ 6 the six tones are cycled with octave
  copies to fill j seeds (no lift).
- **EXACT** — the first j tones (pitch order) are the seeds and the
  two-term recurrence runs unlifted, so every term satisfies it exactly.
  For j ≥ 6 EXACT = LIFT.
Integer-coefficient recurrences on rational seeds give exact rationals; all
sequence arithmetic is `fractions.Fraction`. 130 generated terms; windows of
the W most recent terms, W ∈ {7, 12}, scrubbed over every n.

**Per-window measurements.** Frozen triads v1.1.0 on the exact window
(`score`, rational path) AND on the window in cents (`score_tempered`,
ε = 2¢, default max_span); frozen melodic v0.1.0 (`score_melodic`, defaults;
M1 also at gap ε = 2¢, logged). Descriptors (not frozen, all independent
code): ratio deviation 1200·log2(H[n]/H[n−1]) − 1200·log2 G; chain error =
max over window tones of the circular distance to the ideal W-chain
anchored at H[n]; interval retention = number of the 21 (W = 7) or 66
(W = 12) window dyads within 2¢ of one of the hexany's 15 interval classes
(transposition-invariant; the playground's "tones on the lattice" is kept
too but rotates with n and is reported as such); recurrence-triad count
rt(n) (the law below); lift residual = max over the window's recurrence
triads of |1200·log2(H[m]/(aH[m−i] + bH[m−j]))|; and a MIRROR of the
anchored exact classification (independent reimplementation, span ≤ 2/1)
whose (P, S, G) must equal the frozen exact result on every window — any
disagreement is a verification failure, never patched.

**The law (derived in scratch, the central registered claim).** For a
two-term recurrence with power-of-two coefficients a = 2^p, b = 2^q,
2·(H[n]/2) = aH[n−i] + bH[n−j] says H[n]/2 is the ARITHMETIC MEAN of
aH[n−i] and bH[n−j]; since a, b are octave shifts, the pitch classes
H[n−i], H[n], H[n−j] form an exact proportional triad in every window that
holds all three — provided the two addends lie within an octave of each
other, r = a·G^(j−i)/b ∈ (1/2, 2), which is also the frozen v1.1.0 span
rule. This is the arithmetic content of Erv's "like 4:5:6", "like 2:3:5",
"like 12:19:26" annotations and of P.21c (difference tones land on the
series): a proportional triad is exactly one whose difference tones
coincide. r per recurrence (G, cents, |λ₂|/G, lift k, r, in-octave):
0.418935 1·H[n−1]+32·H[n−4] (2.673880, 502.72¢, 0.880, k 2, r 0.597, in);
0.238186 1·H[n−1]+2·H[n−3] (1.695621, 914.18, 0.641, 3, 1.438, in);
Fig12#12 H[n−1]+H[n−7] (1.255423, 393.81, 0.838, 0, 3.915, OUT);
0.415227 4·H[n−8]+8·H[n−9] (1.333508, 498.27, 0.992, 0, 0.667, in);
meta-meantone 2·H[n−3]+2·H[n−4] (1.494530, 695.63, 0.867, 2, 1.494, in);
silver 8·H[n−9]+7·H[n−10] (1.332604, 497.10, 0.994, 0, 1.523, in but NOT
power-of-two — the control); Fibonacci (1.618034, 833.09, 0.618, 4, 1.618,
in); meta-pelog H[n−1]+H[n−3] (1.465571, 661.76, 0.682, 3, 2.148, OUT);
meta-slendro H[n−2]+H[n−3] (1.324718, 486.82, 0.755, 3, 1.325, in);
meta-Ptolemy H[n−3]+H[n−4] (1.220744, 345.31, 0.871, 2, 1.221, in);
0.591780 16·H[n−8]+16·H[n−9] (1.507105, 710.14, 0.992, 0, 1.507, in);
LLSLS H[n−2]+2·H[n−3] (1.521380, 726.46, 0.754, 3, 0.761, in);
meta-slendro-2 H[n−1]+4·H[n−4] (1.748403, 967.25, 0.784, 2, 1.336, in);
0.773743 2·H[n−3]+128·H[n−10] (1.709700, 928.49, 0.988, 0, 0.667, in);
Pell 2·H[n−1]+H[n−2] (2.414214, 325.86, 0.414, 4, 4.828, OUT); fit351
H[n−1]+128·H[n−6] (2.450010, 351.34, 0.944, 0, 0.690, in).

**Predictions (mirror numbers; the frozen scorer is the referee).**
- **P-M1 (law, EXACT seeding).** At every window after the seeds, frozen
  exact P ≥ rt(n) = max(0, W − j) (the floor is never violated), S = 0 and
  G = 0 in the stationary limit, and P = W − j exactly at the last window
  (n = 129 + seeds): W = 7 / 12 → 0.418935 3/8, 0.238186 4/9,
  meta-meantone 3/8, Fibonacci 5/10, meta-slendro 4/9, meta-Ptolemy 3/8,
  LLSLS 4/9, meta-slendro-2 3/8, fit351 1/6, 0.415227 0/3, 0.591780 0/3,
  0.773743 0/2; and 0/0 for the three out-of-octave recurrences (Fig12#12,
  meta-pelog, Pell) and for the non-power-of-two silver control (its
  triple (8H[n−9], H[n]/2, 7H[n−10]) is exact but 7H[n−10] is not a window
  pitch class). Excess over the floor (P > rt) occurs only in early
  windows as seed echoes and vanishes: mirror counts of such windows at
  W = 7 / 12 — 0.415227 14/28, 0.591780 14/23, 0.773743 1/2,
  meta-meantone 4/6, Fibonacci 1/1, meta-slendro 1/2, meta-Ptolemy 2/3,
  meta-pelog 0/3, all others 0/0.
- **P-M2 (the lift kills exactness; the tempered tier recovers it).** In
  LIFT runs with k > 0 the sequence no longer satisfies the two-term
  relation, only its asymptotic form (residual ∝ (ρ/G)^n = G^(−n)), so
  frozen exact P = 0 at every post-seed window except mirror-listed seed
  echoes (0.238186 W7 n = 12, 13; W12 n = 17, 18; Fibonacci W12 n = 17–19;
  meta-Ptolemy W7 one window, W12 n = 17–20 and a few later; all others
  zero), while frozen tempered P@2¢ ≥ rt(n) for every n ≥ n_lock, the
  first window whose recurrence triads all have residual ≤ 2¢ (W = 7 / 12):
  0.418935 12/17, 0.238186 18/23, meta-meantone 21/26, Fibonacci 18/23,
  meta-slendro 26/31, meta-Ptolemy 36/41, LLSLS 20/25, meta-slendro-2
  17/22. The tempered tier therefore sees the generator's own triads
  roughly one window-length after the seeds leave; the ρ knob sets that
  delay (ρ = 1 here; (ρ/G) per step).
- **P-M3 (crossover law).** Define n_chain(ε) = first post-seed window with
  chain error ≤ ε. Then Δn = n_chain(0.5¢) − n_chain(2¢) ≈ log 4 / log(G/λ₂)
  = 2 / log2(G/λ₂): predicted Δn (and the mirror's measured Δn, LIFT W = 7)
  0.418935 10.8 (9), 0.238186 3.1 (3), Fig12#12 7.8 (8), meta-meantone 9.7
  (12), Fibonacci 2.9 (1), meta-pelog 3.6 (5), meta-slendro 4.9 (5),
  meta-Ptolemy 10.0 (8), LLSLS 4.9 (6), meta-slendro-2 5.7 (4), Pell 1.6
  (0), fit351 24.0 (20). Registered tolerance: |Δn − predicted| ≤ 3 for
  all twelve, both W. The four slow recurrences (|λ₂|/G ≥ 0.988: 0.415227,
  silver, 0.591780, 0.773743; predicted Δn 115–239) do not reach chain
  error 2¢ within 130 steps at either W — harmony persists because the
  bend is slow, Marcus's second knob beside ρ.
- **P-M4 (interval retention is structural, absolute retention is not).**
  Stationary interval retention at 2¢ (W = 7 / 12): 0.418935 1/6,
  Fibonacci 3/8, meta-slendro-2 6/11, Pell 5/15, fit351 5/13, 0.773743 2/5,
  0.415227 0/2, silver 0/2, 0.591780 0/2, meta-pelog 0/2, all others 0/0.
  Absolute "tones on the lattice" after the seeds exit is > 0 at a
  fraction of steps set by rotation alone (≈ 6 tones × W × 4¢ / 1200¢),
  for every generator — it is not a property of the recurrence.
- **P-M5 (melody arrives).** For the twelve fast recurrences the last
  window (n = 129 + seeds) has M1 gap-class count ≤ 3 at gap ε = 2¢
  (three-gap theorem on a converged chain), and its M3 propriety class
  equals that of the pure W-chain of the same generator. LIFT and EXACT
  share every stationary value (same G): the seeds set the transient, not
  the limit.

**Deliverables:** `meru001.py`; `results/meru001.jsonl` (one row per
recurrence × seeding × W × n) + `results/meru001_summary.json`
(law/lock/crossover tables, verdicts, mirror-vs-frozen census);
`results/scl/meru001/` — for 0.418935, Fibonacci and meta-meantone (LIFT,
W = 7) the seed window, the lock window and the last window, offered for
listening (standing ear-check gate). Tests `tests/test_meru001.py` green
before the first run. Stdlib only, python3.12, no randomness, no
wall-clock fields; two runs bit-identical.

## 2026-10-10 — CPSFIT-001 pre-registration (entry BEFORE any implementation or run)

**Question (program B, Marcus 2026-10-08):** choose one generator and note
count whose MOS field approximates a CPS field, in the spirit of
equal-temperament approximation; within 2¢ counts as at least as good as
12-ET. The playground's direction 2 did this with a 0.5¢ generator grid.
This experiment does it EXACTLY and then asks what the fits are.

**Construction.** Lattices: the hexany CPS(4,2){1,3,5,7} (primary, G-004
EG4-first), the EG4 tesseract's 8 distinct tones {1, 35/32, 5/4, 21/16,
3/2, 105/64, 7/4, 15/8} (BRIDGE-001's object — the cross-rail), and
Ptolemy's just major (control; the playground reported a 12-chain of
498.26¢ within 0.45¢). For each N ∈ 5..48: the generator g* ∈ (0, 600¢]
minimizing the largest circular error of any lattice tone to a degree of
the N-note chain {k·g : k ∈ [s, s+N−1]} with s ≤ 0 ≤ s+N−1 (the chain
contains 1/1). Solved exactly: for a tolerance ε each (tone, k) admits a
g-interval of half-width ε/|k| around every (cents + 1200m)/k; a sweep over
interval endpoints with per-tone active sets decides feasibility (does
some window of N consecutive k containing 0 meet every tone's active set);
bisection on ε (14 halvings from 60¢) finds the assignment; ternary search
on g for that assignment gives ε*(N) and g*(N). Then: the k-assignment's
homomorphism test (does an integer mapping (k₃, k₅, k₇) with k(tone) =
Σ eₚkₚ exist — the fit is a val, not an accident); the kernel of that
mapping (period = octave, octave row from the fitted cents; 7-limit commas
in the box |e₃| ≤ 12, |e₅| ≤ 6, |e₇| ≤ 5, < 60¢, Tenney height ≤ 2^40 —
BRIDGE-001's box); whether the chain is a 2-step MOS; frozen triads v1.1.0
(`score_tempered`, ε = 2¢) and frozen melodic v0.1.0 of the full chain
scale; the lattice IMAGE (the fitted tones only) under the frozen tempered
scorer at ε ∈ {1, 2, 3, 5}¢ — hexany triad survival at the LOCK tier — plus
the mirror's per-triad deviation and the smallest ε recovering every exact
triad; equal temperaments N = 5..72 the same way; and the nearest two-term
recurrences within 2¢ of g* (coefficients {1..8, 16, 32, 64, 128}, order
≤ 12, coprime (i, j), direct and complement), flagged power-of-two and
in-octave per the MERU-001 law.

**Predictions (independent scratch sweep; the frozen scorer referees the
triad claims).**
- **P-F1 (the staircase).** Hexany ε*(N), g*(N): N = 6 42.23¢ @ 257.15;
  7 40.76 @ 465.30; 8 28.52 @ 357.79; 9 24.41 @ 361.90; 10 23.30 @ 118.69;
  11 18.85 @ 249.36; 12–14 13.73 @ 318.36; **15 4.815 @ 502.86**; 16–17
  4.771 @ 116.50; 18 3.275 @ 77.92; 19–21 2.571 @ 271.42; **22–30 1.367 @
  193.79**; 31–48 0.743 @ 77.20. So the smallest chain containing the
  hexany within 2¢ has **N = 22** (the playground's grid said 33, an
  earlier scratch said 65 — both artifacts of grid resolution), within 1¢
  N = 31, within 5¢ N = 15, within 15¢ N = 12. EG4: the same generators
  with N shifted (2¢ first at N = 24, 1.367¢; 271.42 at N = 19–23, 2.571¢;
  502.86 at N = 16–17). Ptolemy: N = 7 8.60¢ @ 502.35; 12–22 0.434 @
  498.26; 23–29 0.434 @ 249.13; 30–35 0.336 @ 475.53; 36+ 0.140 @ 565.99.
- **P-F2 (fits are vals).** Every hexany optimum at N ≥ 11 is homomorphic;
  N = 7 and N = 10 are not. Mappings (k₃, k₅, k₇) and kernels: N = 15
  (−1, −4, −10), kernel 3136/3125, 225/224, 126/125, 81/80 — a septimal
  MEANTONE, and the generator is Erv's 0.418935 recurrence to −0.14¢
  (power-of-two, in-octave): direction 2 rediscovers Erv's recurrence
  from the lattice alone, and the law explains it — 2L⁴ = L³ + 4 says four
  fourths meet 5/4 as an arithmetic-mean condition; N = 16 (6, −7, −2),
  kernel 2401/2400, 1029/1024, 225/224 (miracle; BRIDGE-001's blackjack);
  N = 19 (7, −3, 8), kernel 225/224, 1728/1715, 6144/6125 (orwell —
  BRIDGE-001's mapping [[1,0,3,1],[0,7,−3,8]] reproduced, free minimax
  2.571¢ against its 2.727¢ prime-minimax tuning); N = 22 (16, 2, 5),
  kernel 2401/2400, 3136/3125 (6144/6125 their product); N = 31
  (−22, 5, −3), kernel 2401/2400, 65625/65536. Ptolemy N = 7 (−1, 8-free;
  k₃ = −1, k₅ = −4): also Erv's generator, to +0.38¢ — the best seven-note
  chain for the just major scale is a meantone fourth.
- **P-F3 (tone fidelity ≠ triad survival at LOCK).** Hexany image
  survival at ε = 2¢ of its 12 exact triads (6 P + 6 S; sign-coherent
  errors stack, ET-003/BRIDGE-001 lesson): N = 15 2/12 (max dev 7.25¢,
  full recovery at ε ≥ 7.25); N = 16 6/12 (2.94 — BRIDGE-001's "blackjack
  recovers at 3¢" reproduced); N = 19 8/12 (3.42); **N = 22 10/12 (2.08 —
  within-2¢ tones, two triads lost by 0.08¢)**; N = 31 12/12 (0.32). EG4:
  N = 16 4/24, 19 16/24, 24 20/24. Survival is the frozen tempered P + S of
  the image scale; the mirror's deviations are the explanation.
- **P-F4 (cross-direction, the law as a floor on the fit).** The N = 15
  hexany chain at 502.86¢ sits 0.14¢ from a power-of-two in-octave
  recurrence of lag j = 4, so by the MERU-001 law it carries ≥ N − j = 11
  near-exact proportional triads: frozen P@2¢ of that chain ≥ 11.
  Likewise the Ptolemy N = 7 chain (502.35¢, 0.38¢ from the same
  recurrence): P@2¢ ≥ 3. No such floor is claimed for the other fits (their
  nearest recurrences are either non-power-of-two or > 0.8¢ away).
- **P-F5 (ET comparison).** No N-EDO with N ≤ 41 contains the hexany
  within 2¢ (the playground found 41-ET at 2.26¢ at best); the first
  within 2¢ is reported as a measurement.

**Deliverables:** `cpsfit001.py`; `results/cpsfit001.jsonl` (one row per
lattice × N, plus ET rows) + `results/cpsfit001_summary.json`;
`results/scl/cpsfit001/` — the hexany N = 15 (Erv's generator) and N = 22
chains, offered for listening (standing gate). Tests
`tests/test_cpsfit001.py` green before the first run. Stdlib only,
python3.12, deterministic, no wall-clock fields; two runs bit-identical.

## 2026-10-10 — MERU-001 results + verdicts

**Run:** `meru001.py` (94 s; receipts `results/meru001.jsonl`, 8,164 rows =
16 recurrences × 2 seedings × 2 windows × every n, + `results/meru001_summary.json`;
two runs bit-identical, `cmp` on both files and the nine .scl). Frozen
triads v1.1.0 and melodic v0.1.0 read-only, pins verified; lattice suite
335/335 green before the run (22 new tests). **Mirror vs frozen exact:
0 disagreements over 8,164 windows.**

- **P-M1 — KEPT.** Under EXACT seeding every registered stationary count
  reproduces: P(last window) = W − j for the twelve in-octave power-of-two
  recurrences (3/8, 4/9, 3/8, 5/10, 4/9, 3/8, 4/9, 3/8, 1/6, 0/3, 0/3, 0/2 at
  W = 7/12 in LOG order), 0/0 for Fig12#12, meta-pelog, Pell and the silver
  control; S = G = 0 at every last window; the floor P ≥ rt(n) is never
  violated (0 of 3,968 post-seed windows); and the seed-echo census matches
  the mirror window for window (0.415227 14/28, 0.591780 14/23, 0.773743
  1/2, meta-meantone 4/6, Fibonacci 1/1, meta-slendro 1/2, meta-Ptolemy 2/3,
  meta-pelog 0/3, all others 0/0). The law is exact and the frozen scorer
  sees it.
- **P-M2 — KEPT.** All eight lifted recurrences: exact P = 0 after the seeds
  leave except the mirror-listed echoes (0.238186 two windows at each W,
  Fibonacci three at W = 12, meta-Ptolemy one/six), every n_lock as
  registered (12/17, 18/23, 21/26, 18/23, 26/31, 36/41, 20/25, 17/22), and
  tempered P@2¢ ≥ rt(n) at every window from n_lock on (0 violations). The
  lift turns the generator's own triads from exact into 2¢-tempered, about
  one window-length after the seeds exit; the exact and tempered paths
  disagree on purpose, and both are right.
- **P-M3 — REFUTED as registered, held on eleven of twelve.** |Δn − 2/log2
  (G/λ₂)| ≤ 3 holds for every seeding and window of the eleven faster
  recurrences (e.g. 0.418935: 9/13/11/13 vs 10.8; meta-Ptolemy 8/9/9/11 vs
  10.0; Fibonacci 1/1/2/2 vs 2.9; Pell 0 vs 1.6) and fails only on fit351,
  the slowest of the "fast" group (λ₂/G = 0.944): Δn = 20 against 24.0 at
  W = 7, and at W = 12 the 0.5¢ crossing never arrives within 130 steps.
  The four slow recurrences (≥ 0.988) never reach chain error 2¢, as
  predicted. The decay law is right about the rate; the crossing step of a
  max-over-tones descriptor jitters by a few steps when λ₂ is a complex pair,
  and the jitter scales with the time constant. A tolerance of 3 steps was
  too tight for a 24-step constant; the refutation stands as registered.
- **P-M4 — KEPT.** Stationary interval retention matches all sixteen
  registered pairs; absolute "tones on the lattice" fires at 6–23% of
  post-seed windows at W = 7 (rotation estimate 14%) for every generator,
  including those with zero structural retention. The playground's
  "window tones on lattice" stat is a rotation artifact and should be
  read as such.
- **P-M5 — KEPT.** Every fast recurrence ends at ≤ 3 gap classes (gap ε = 2¢)
  at both W, the last window's propriety class equals the pure chain's
  (strictly proper for 0.418935, meta-meantone, meta-Ptolemy, fit351 at
  W = 7; improper for the rest), and LIFT and EXACT agree on every
  stationary value.

**Measured, not registered (post-hoc lenses, labelled):** (1) the tempered
tier counts MORE than the law's floor on converged chains — Fibonacci W = 7
P@2¢ = 7 vs rt 5, meta-slendro 5 vs 4, fit351 6 vs 1 (the 351.3¢ chain is
MOS-LAT-002's neutral-third hot spot) — and P = S at 2¢ on every converged
chain (chain inversional symmetry), while the exact path has S = 0: the
subcontrary partners of the recurrence triads exist only to within the
transient. (2) The slow four keep exact seed-echo triads for twenty-plus
windows (0.415227 W = 12: P = 6, 6, 7, 6 … at n = 20–23 against a floor
of 3) — persistence of harmony is literal there. (3) G@2¢ = 9 on every
converged W = 7 chain: consecutive chain degrees are exact geometric triads,
never counted in any loss, as designed.

**Kept.** Runner and receipts stand; nine .scl exports under
`results/scl/meru001/` (0.418935, Fibonacci, meta-meantone; seed window,
lock window, last window) are offered for listening — gate G-028.

## 2026-10-10 — CPSFIT-001 results + verdicts

**Run:** `cpsfit001.py` (23 s; `results/cpsfit001.jsonl`, 333 rows = 3
lattices × (chain N = 5..48 feasible + ET N = 5..72), +
`results/cpsfit001_summary.json`; two runs bit-identical). Frozen triads
v1.1.0 (`score_tempered`, 2¢) and melodic v0.1.0 read-only; frozen
survival vs the mirror's per-triad deviations: 0 disagreements.

- **P-F1 — KEPT.** Hexany staircase reproduced at every registered N to
  0.01¢ in both ε* and g*; minimal N: 22 at 2¢ (1.367¢ @ 193.787), 31 at
  1¢ (0.743 @ 77.198), 15 at 5¢ (4.815 @ 502.860), 12 at 15¢; EG4 24 at 2¢;
  Ptolemy 12 at 2¢ (0.434 @ 498.262), 7 at 10¢ (8.603 @ 502.346). The
  playground's "no fit below N = 33" was its 0.5¢ grid missing basins of
  width 2ε/|k| ≈ 0.1¢.
- **P-F2 — KEPT.** Non-homomorphic hexany optima are exactly N = 7 and
  N = 10; every mapping as registered: N = 15 (−1, −4, −10) with kernel
  3136/3125, 225/224, 126/125, 50625/50176, 81/80 — septimal meantone, and
  the generator is Erv's 0.418935 recurrence to −0.139¢; N = 16 (6, −7, −2)
  kernel 2401/2400, 16875/16807, 225/224, 1029/1024 (miracle); N = 19
  (7, −3, 8) kernel 65625/65536, 6144/6125, 225/224, 1728/1715 (orwell,
  BRIDGE-001's mapping); N = 22 (16, 2, 5) kernel 2401/2400, 6144/6125,
  3136/3125; N = 31 (−22, 5, −3) kernel 2401/2400, 65625/65536. Ptolemy
  N = 7: (−1, −4), Erv's generator to +0.375¢.
- **P-F3 — KEPT.** Hexany image survival at 2¢ (frozen P + S): N = 15 2/12
  (full recovery at 7.250¢), 16 6/12 (2.940), 19 8/12 (3.420), 22 10/12
  (2.080), 31 12/12 (0.321); EG4 16 4/24, 19 16/24, 24 20/24. All within-2¢
  tones at N = 22 and two triads still lost — by 0.08¢.
- **P-F4 — KEPT.** The N = 15 hexany chain scores P@2¢ = 12 ≥ 11, the
  Ptolemy N = 7 chain P@2¢ = 3 ≥ 3: the MERU-001 law predicts the frozen
  triad count of a direction-2 fit from its nearest recurrence alone.
- **P-F5 — KEPT, and stronger than registered.** No N-EDO up to 72 contains
  the hexany within 2¢; the best ≤ 41 is 31-EDO at 6.265¢ and the best ≤ 72
  is 53-EDO at 4.76¢. A 22-note rank-2 chain does what no equal temperament
  below 73 notes does.

**Measured, not registered (post-hoc lenses, labelled):** (1) **triad
survival is not monotone in N while tone error is**: N = 11 (249.355¢,
mapping (−2, −8, −1), kernel 19683/19600, 245/243, 81/80) keeps 8/12 hexany
triads at 2¢ with tone errors up to 18.85¢, then N = 12–15 keep only 2/12
at 13.7–4.8¢; the mechanism is exact cancellation — in 15/16 : 5/4 : 15/8
the mistuned 5 appears in all three tones and the deviation collapses to
the 3/2 error (0.665¢), and 5/4 : 3/2 : 7/4 survives at 1.99¢ because the
5 and 7 errors cancel across the mean. Program B's objective at the
harmonic axis has to be survival, not tone error; CPSFIT-002 should
minimize max triad deviation directly. (2) Full-chain frozen P@2¢ grows
with N and with the generator's neighbourhood (N = 18 at 77.9¢ already 40,
N = 31 at 77.2¢ 91), so a fit's harmonic wealth is dominated by the host
chain's own coincidences, not by the embedded hexany. (3) The playground's
direction-2 picks (33–38-note 115.96¢ chains, 41-note 351.4¢) do not appear
on the exact staircase at all.

**Kept.** Runner and receipts stand; `results/scl/cpsfit001/` holds the
hexany N = 15 (Erv's generator) and N = 22 chains for listening — gate
G-029.

**Run receipt:** 2026-10-10, python3.12 — lattice suite 335/335 OK (22 new:
13 meru001 + 9 cpsfit001), freeze checks A OK on both pins (scorer
1a840af9…b592, melodic a16f162b…7535); all four receipts and all eleven
.scl bit-identical across two runs.

## 2026-10-10 — MERU-002 pre-registration (entry BEFORE any implementation or run)

**Question (program A, the second knob):** the playground's order lift
multiplies the characteristic polynomial by (x^k − ρ^k) and claims "a smaller
ρ bends the seeds faster"; the research list proposed a ρ sweep as a
"harmony half-life" knob. MERU-001 ran ρ = 1 only. This experiment sweeps ρ
and asks three things: does the lock step follow ρ alone, does the chain
step follow max(ρ, |λ₂|) with a plateau below |λ₂|, and does a longer
transient keep any of the seed harmony. It also re-registers the MERU-001
crossover law P-M3 with a tolerance that scales with the time constant,
since a fixed 3-step tolerance refuted it on the slowest fast recurrence.

**Construction.** Three recurrences from MERU-001, chosen for their spread
of |λ₂|/G: 0.418935 (H[n] = H[n−1] + 32·H[n−4]; G = 2.673880, |λ₂| =
2.3523, |λ₂|/G = 0.880), Fibonacci (G = 1.618034, |λ₂| = 0.618034, 0.382),
meta-meantone (2·H[n−3] + 2·H[n−4]; G = 1.494530, |λ₂| = 1.29529, 0.867).
Seeds: the hexany CPS(4,2){1,3,5,7}, LIFT seeding exactly as MERU-001
(k = 6 − j extra seeds, chain-aligned octaves), but with the lift
coefficient c = ρ^k taken over the exact rational ladder ρ ∈ {1/4, 1/2,
3/4, 1, 5/4, 11/8, 23/16, 3/2, 25/16, 7/4, 2, 9/4, 5/2, 21/8}, keeping only
ρ < G (so 14 values for 0.418935, 9 for Fibonacci, 9 for meta-meantone).
The sequence stays exact (Fractions). Windows W ∈ {7, 12}, 130 generated
terms, n₀ = 6 + W − 1 the first post-seed window. Per window: frozen exact
and 2¢ triads (v1.1.0), frozen melodic (v0.1.0), the mirror, the lift
residual, chain error, interval retention at 2¢, as MERU-001. Derived per
(recurrence, ρ, W): n_lock (first post-seed window with lift residual ≤
2¢), n_chain(ε) for ε ∈ {2, 0.5}, Δn, mean frozen P@2¢ and mean interval
retention over the transient windows n₀ ≤ n < n_chain(2¢), and whether any
term went non-positive. τ_eff = 1/log2(G / max(ρ, |λ₂|)).

**Predictions (independent scratch sweep 2026-10-10; the frozen scorer
referees every triad count).**
- **P-R1 (the lock follows ρ alone).** The lift residual decays as (ρ/G)^n,
  so n_lock depends on ρ and not on |λ₂|. Registered n_lock, W = 7: 0.418935
  ρ ≤ 3/2 → 12 (= n₀), 7/4 → 14, 2 → 18, 9/4 → 28, 5/2 → 72; Fibonacci
  ρ ≤ 3/4 → 12, 1 → 14, 5/4 → 22, 3/2 → 54; meta-meantone ρ ≤ 1/2 → 12, 3/4
  and 1 → 13, 5/4 → 23. W = 12: the same values with the plateau at 17
  (0.418935 ρ ≤ 7/4 → 17, 2 → 18; Fibonacci ρ ≤ 1 → 17; meta-meantone ρ ≤ 1
  → 17; the rest as at W = 7). The law: n_lock is non-decreasing in ρ, and
  for every point with n_lock > n₀ + 2, n_lock · log2(G/ρ) ∈ [5.5, 8.5]
  (the residual's intercept in bits; scratch 5.9–8.2). The unlisted ladder
  points (11/8, 23/16, 25/16) are predicted by the same law, tolerance ±2
  steps around the interpolated value.
- **P-R2 (the chain follows max(ρ, |λ₂|); plateau below |λ₂|).** n_chain(2¢)
  at W = 7 stays within ±4 of one value for every ρ with ρ < |λ₂|: 0.418935
  53 for ρ ≤ 9/4, then 94 at ρ = 5/2 (ρ/G = 0.935 > 0.880); meta-meantone
  39–46 for ρ ≤ 5/4, then 71 at 11/8 and 133 at 23/16; Fibonacci's plateau
  is only ρ ≤ 1/2 (16, 16), then 17, 22, 31, 43, 55, 75, 135 for ρ = 3/4 …
  25/16. Above |λ₂| n_chain(2¢) is strictly increasing in ρ. The law:
  (n_chain(2¢) − n₀) / τ_eff ∈ [5.0, 8.5] for every (recurrence, ρ) at W = 7
  (scratch 5.5–7.95).
- **P-R3 (ρ does not buy harmony).** Over the transient windows at W = 7,
  mean frozen P@2¢ is non-increasing in ρ for ρ ≥ 1 (jitter ≤ +0.5 between
  adjacent ladder points), and the ρ with the longest transient has the
  LOWEST mean P@2¢ of its recurrence, ≤ 2.0 (scratch: 1.67, 1.56, 1.80).
  Mean interval retention at 2¢ never exceeds 3.0 of the hexany's 15
  interval classes × 21 pairs for any ρ (scratch max 2.61). Exact seed-echo
  windows (P > rt) are 0 for every ρ. So the research list's "harmony
  half-life" reading of ρ is wrong as stated: a large ρ keeps the sequence
  away from the chain, not near the lattice. Harmony persistence belongs to
  EXACT seeding of slow recurrences (MERU-001 lens 2), not to the lift.
- **P-R4 (crossover law, re-registered).** Δn = n_chain(0.5¢) − n_chain(2¢)
  satisfies |Δn − 2τ_eff| ≤ max(3, 0.3 · 2τ_eff) at both W for every
  (recurrence, ρ) that reaches 0.5¢ within 130 steps. Scratch at W = 7:
  0.418935 9–11 vs 10.8 (ρ ≤ 9/4), 20 vs 20.6 (5/2); Fibonacci 1, 1, 2, 1, 4,
  20 vs 1.4, 1.4, 1.8, 2.9, 5.4, 18.3; meta-meantone 7–12 vs 9.7. The ρ = 1
  rows reproduce MERU-001's LIFT rows exactly (same seeds, same
  coefficients).
- **P-R5 (positivity).** 0.418935 at ρ = 21/8 produces a non-positive term
  (the lift coefficient −32·ρ² overwhelms the sum) and is excluded from the
  descriptors with its first non-positive index recorded; every other
  (recurrence, ρ < G) pair stays positive for all 136 terms.

**Deliverables:** `meru002.py`; `results/meru002.jsonl` (one row per
recurrence × ρ × W × n) + `results/meru002_summary.json`;
`results/scl/meru002/` — 0.418935 at ρ = 1 and ρ = 5/2, W = 7, the window at
the ρ = 1 lock step (n = 12), at n = 40, and at n = 100, offered for
listening: does the long ρ = 5/2 transient sound like anything at all?
Tests `tests/test_meru002.py` green before the first run. Stdlib only,
python3.12, deterministic, no wall-clock fields; two runs bit-identical.

## 2026-10-10 — MERU-002 results + verdicts

**Run:** `meru002.py` (20.5 min, exact rationals with ρ^k denominators;
receipts `results/meru002.jsonl`, 7,395 rows = 32 (recurrence, ρ) pairs ×
2 windows × every n, + `results/meru002_summary.json`; two runs
bit-identical, `cmp` on both receipts and the six .scl). Frozen triads
v1.1.0 and melodic v0.1.0 read-only, pins verified before and after;
lattice suite 344/344 green before the run (9 new tests). **Mirror vs
frozen exact: 0 disagreements over 7,395 windows.** ρ = 1 rows reproduce
MERU-001's LIFT rows (n_lock 12/17, n_chain 53/56, Δn 9/13 for 0.418935;
18/23, 22/27 for Fibonacci; 21/26, 39/43 for meta-meantone).

- **P-R1 — REFUTED as registered; the registration was wrong, not the
  law.** The scratch sweep defined n_lock on a single term's residual; the
  runner uses MERU-001's window maximum (every generated term in the
  window within 2¢). With k = 2 the lifted roots are ±ρ, so the single-term
  residual oscillates with period 2 and crosses 2¢ early at a
  near-cancellation; the window maximum waits for the envelope. Every
  registered number above the plateau is therefore too small (0.418935
  W = 7: 14/16/18/24/34/84 at ρ = 5/4 … 5/2 against 12/12/14/18/28/72;
  Fibonacci 14/14/18/30/74 against 12/12/14/22/54; meta-meantone 15/21/37
  against 13/13/23), 58 checks fail, and the "constant intercept" claim is
  false too: n_lock · log2(G/ρ) falls monotonically with ρ, from 13.3 to
  8.2 bits (0.418935, W = 7), 12.5 to 8.1 (Fibonacci), 14.9 to 7.6
  (meta-meantone); the residual's amplitude depends on ρ through the lift
  coefficient ρ^k, so the intercept is not a constant of the recurrence.
  What survives, measured not registered: n_lock is non-decreasing in ρ on
  all three recurrences and both windows (0 inversions in 31 ladder steps),
  and at matched ρ/G the lock step is nearly the same across recurrences
  whose |λ₂|/G differ by 0.5 — Fibonacci ρ/G = 0.773 → 30 against 0.418935
  ρ/G = 0.748 → 24; meta-meantone 0.836 → 37 against 0.418935 0.841 → 34 —
  so the lock does follow ρ and not |λ₂|, as the decay argument says.
- **P-R2 — REFUTED as registered on one row, held on the other thirty.**
  The scratch printed its "never reached" sentinel (135 = last index) for
  Fibonacci at ρ = 25/16 and the registration copied it as a crossing; the
  runner reports None (chain error never ≤ 2¢ in 130 steps, as ρ/G = 0.966
  predicts, τ_eff = 20). Everything else held exactly: the 0.418935
  plateau is 53 for every ρ ≤ 2 and 54 at 9/4 (ρ/G = 0.841 < 0.880), then
  94 at 5/2; meta-meantone 39–46 for ρ ≤ 5/4, then 71 and 133; Fibonacci
  16, 16, 17, 22, 31, 43, 55, 75 strictly increasing above |λ₂|; every
  registered n_chain(2¢) reproduced; and (n_chain(2¢) − n₀)/τ_eff ∈
  [5.55, 7.95] on all 30 rows (0.418935: 7.58 on every plateau row, 7.76,
  7.95 above it; Fibonacci 5.55–7.34; meta-meantone 5.57–7.10), inside the
  registered [5.0, 8.5]. The chain follows max(ρ, |λ₂|).
- **P-R3 — KEPT.** ρ buys no harmony. Mean frozen P@2¢ over the transient
  windows at W = 7 is non-increasing in ρ for ρ ≥ 1 within the 0.5 jitter
  (0.418935: 4.15, 4.10, 4.07, 4.15, 3.98, 3.98, 3.83, 3.41, 2.52, 1.67;
  Fibonacci: 3.60, 2.84, 2.10, 1.91, 1.73, 1.59; meta-meantone: 3.67, 2.18,
  1.83, 1.80); the longest transient has the lowest mean on each (1.67,
  1.59, 1.80, all ≤ 2.0); mean interval retention never exceeds 2.61 of 21
  pairs; exact echo windows are 0 on all 32 pairs. A large ρ keeps the
  sequence away from the chain and not near the lattice.
- **P-R4 — KEPT.** With tolerance max(3, 0.3·2τ_eff), |Δn − 2τ_eff| holds
  on all 54 (recurrence, ρ, W) rows that reach 0.5¢: worst cases
  meta-meantone W = 7 at ρ ∈ {1/2, 1} Δn = 12 and ρ ∈ {3/4, 5/4} Δn = 7
  against 9.7 (tolerance 3), Fibonacci ρ = 3/2 W = 12 16 against 18.3
  (tolerance 5.5), 0.418935 ρ = 5/2 20/22 against 20.6. MERU-001's P-M3
  stands in this form: the rate is right and the crossing jitters by a few
  steps that scale with the time constant.
- **P-R5 — KEPT.** 0.418935 at ρ = 21/8 goes non-positive at n = 53 (the
  lift coefficient −32·ρ² = −220.5 on H[n−6]); every other pair stays
  positive through 136 terms.

**Measured, not registered (post-hoc lenses, labelled):** (1) At W = 12 the
locks are 5 steps later than at W = 7 on the plateau and the same offset
persists above it (0.418935 ρ = 2: 24 → 29; 5/2: 84 → 89), consistent with
the window-maximum definition. (2) Fibonacci ρ ≤ 3/4 has a transient of
only 4–5 windows and the highest mean P@2¢ of the run (5.75, 4.75, 5.20):
the hexany seeds, chain-aligned, are already close to a φ-chain in step
size, so the chain arrives before the seeds have left the window. (3) The
meta-meantone chain's own interval retention of the hexany is the largest
(stationary 0 at W = 7 in MERU-001, but transient means 1.9–2.6 here, above
the other two), the meantone fourth being 2.4¢ from the hexany's 21/16 : 1
step class.

**Kept.** Runner and receipts stand; six .scl windows under
`results/scl/meru002/` (0.418935, ρ = 1 and ρ = 5/2, W = 7, n = 12, 40, 100)
are offered for listening — gate G-030: does the long ρ = 5/2 transient at
n = 40 sound like anything, or like a scale drifting?

**Run receipt:** 2026-10-10, python3.12 — lattice suite 344/344 OK (9 new:
test_meru002), freeze checks A OK on both pins (scorer 1a840af9…b592,
melodic a16f162b…7535) before and after; both receipts and all six .scl
bit-identical across two runs.

## 2026-10-10 — CPSFIT-002 pre-registration (entry BEFORE any implementation or run)

**Question (program B, the objective):** CPSFIT-001's post-hoc lens 1 found
that triad survival is not monotone in tone error (N = 11 keeps 8/12 hexany
triads at 2¢ with tone errors up to 18.85¢, because a prime mistuned in all
three tones cancels in the mean condition) and asked for the fit to
minimize triad deviation directly. This experiment does that and asks what
changes: the N at which every lattice triad survives at the LOCK tier, the
generators and mappings the new objective picks, and whether the worst
triad is even the right thing to minimize.

**Construction.** Same lattices as CPSFIT-001 (hexany CPS(4,2){1,3,5,7},
the EG4 tesseract's 8 tones, Ptolemy's just major) and the same chain
model: N notes of one generator g ∈ (0, 600¢], window of consecutive k
containing 1/1, each lattice tone assigned to its nearest degree in the
window. New objective: for a fixed assignment, the deviation of each exact
lattice triad re-voiced in the chain (the mirror's `triad_deviations`:
the middle tone against the arithmetic or harmonic mean of the outer two,
in cents) and the objective is the LARGEST such deviation, subject to the
largest tone error ≤ 20¢ (so every tone still sits on a chain degree at
the ET7 tier; without a cap the objective is free to abandon tones). The
set of candidate assignments is enumerated on a 0.5¢ grid of g (an
assignment valid within 20¢ occupies a g-interval of width ≥ 40/(N−1)¢ ≥
0.85¢, so the grid misses none); for each assignment g is refined by
golden-section search on its interval; ties in the objective break toward
the smaller tone error. Per fit, as CPSFIT-001: homomorphism and kernel,
MOS flag, frozen tempered triads of the chain at 2¢, frozen melodic, the
lattice IMAGE under the frozen tempered scorer at 2¢ (survival, the
referee), the mirror's deviations, nearest two-term recurrences. N ∈ 5..48.
No ET rows (ET has no g to move).

**Predictions (independent scratch sweep 2026-10-10, 0.5¢ grid + golden
refinement; the frozen scorer referees survival).**
- **P-T1 (the triad staircase).** Hexany dev*(N), g*(N): N ≤ 10 infeasible
  under the 20¢ cap; 11: 17.92 @ 249.55; 12: 17.03 @ 318.93; 13–14: 7.95 @
  490.09; 15: 5.14 @ 503.19; 16–21: 2.43 @ 116.59; **22–30: 1.156 @ 193.91**;
  31–47: 0.305 @ 77.195; 48: 0.295 @ 582.45. Ptolemy: 7–11: 10.13 @ 506.25;
  12–35: 0.257 @ 498.25; 36: 0.112 @ 565.99. EG4: ≤ 11 infeasible; 12: 22.97
  @ 249.74; 13–14: 8.60 @ 490.36; 15: 7.95 @ 163.37; 16–17: 3.91 @ 116.34;
  18–22: 3.69 @ 77.91; 23: 1.595 @ 193.31; 24–30: 1.349 @ 193.88; 31–48:
  0.331 @ 77.191. Tolerances: 0.05¢ on dev*, 0.1¢ on g* (the runner refines
  the same assignment).
- **P-T2 (full survival arrives earlier).** Frozen image P + S at 2¢ reaches
  12/12 for the hexany first at **N = 22** (CPSFIT-001: N = 31): the
  generator moves from 193.787 to 193.908¢ and the largest tone error rises
  from 1.367 to 2.22¢ — one tone leaves the LOCK tier so that all twelve
  triads enter it. EG4 reaches 24/24 first at N = 23 (193.31¢, mapping
  (−15, 2, 5), tone error 3.88¢; CPSFIT-001: 20/24 at N = 24, 24/24 at 31).
  Ptolemy 23/23 at N = 12 as before. Survival under the new objective is
  ≥ survival under tone-minimax at every N ≥ 15 on all three lattices.
- **P-T3 (the mappings).** Hexany optima are homomorphic at every feasible
  N except 48: 11 (−2, −8, −1); 12 (6, 5, 3); 13–14 (−1, −9, 2), a mapping
  the tone staircase never visits; 15 (−1, −4, −10); 16–21 (6, −7, −2);
  22–30 (16, 2, 5) (at N = 30 a non-homomorphic assignment ties at 1.156¢
  and the tone-error tie-break keeps the val); 31–47 (−22, 5, −3); at N = 48
  a non-homomorphic assignment at 582.45¢ beats the val by 0.010¢ and is
  reported as such.
- **P-T4 (the worst triad is not the count).** At N = 11 the triad-minimax
  optimum (249.55¢) keeps 4/12 hexany triads by the mirror where the
  tone-minimax optimum (249.36¢) keeps 6/12 by the mirror and 8/12 by the
  frozen image scorer (CPSFIT-001; the frozen count also admits triads the
  tempering creates). Registered on the referee: frozen image survival at
  the triad-minimax N = 11 optimum is LESS than 8, and at Ptolemy N = 7 the
  frozen survival at 506.25¢ is less than at Erv's 502.35¢ (mirror 0/23
  against 5/23). Minimizing the largest deviation can lower the number of
  surviving triads; a count objective is CPSFIT-003.
- **P-T5 (the law survives the move).** The N = 15 hexany optimum moves from
  502.86 (0.14¢ from Erv's 0.418935 recurrence) to 503.19¢ (0.46¢): the
  hexany's own triads pull the generator away from the recurrence's. The
  chain still sits within 2¢ of the power-of-two in-octave recurrence, so
  by the MERU-001 law frozen P@2¢ of the N = 15 chain ≥ 11.

**Deliverables:** `cpsfit002.py`; `results/cpsfit002.jsonl` (one row per
lattice × feasible N) + `results/cpsfit002_summary.json`;
`results/scl/cpsfit002/` — the hexany N = 22 chain at 193.908¢ (all twelve
triads within 2¢) beside CPSFIT-001's 193.787¢, offered for listening
(standing gate). Tests `tests/test_cpsfit002.py` green before the first
run. Stdlib only, python3.12, deterministic, no wall-clock fields; two
runs bit-identical.

## 2026-10-10 — CPSFIT-002 results + verdicts

**Run:** `cpsfit002.py` (13.4 min; receipts `results/cpsfit002.jsonl`, 117
rows = hexany N = 11..48, EG4 N = 12..48, Ptolemy N = 7..48, +
`results/cpsfit002_summary.json`; two runs bit-identical, `cmp` on both
receipts and the .scl). Frozen triads v1.1.0 (`score_tempered`, 2¢) and
melodic v0.1.0 read-only, pins verified; lattice suite 354/354 green before
the run (10 new tests). The objective (fast triad evaluator) agrees with
the mirror's `triad_deviations` on every row (0 disagreements); frozen
image survival is the referee throughout.

- **P-T1 — KEPT on the hexany and EG4, REFUTED as registered on Ptolemy
  N = 23–35 by a tie.** Every hexany and EG4 rung reproduces to the
  registered tolerance (hexany 17.924 @ 249.549, 17.026 @ 318.934, 7.951 @
  490.094, 5.140 @ 503.185, 2.428 @ 116.588, **1.156 @ 193.908**, 0.305 @
  77.195, 0.295 @ 582.450; EG4 22.973 @ 249.740 … 1.595 @ 193.309, 1.349 @
  193.883, 0.331 @ 77.191), and the first feasible N under the 20¢ cap is
  11, 12, 7 as registered. On Ptolemy the objective value 0.257¢ is reached
  by three different chains with the same tone error 0.50¢: 498.253
  (−1, 8, 0), its half 249.127 (−2, 16, 0), whose every second degree is the
  498-chain, and 233.916 (3, −24, 0). The scratch kept the first; the
  runner's registered tie-break (equal deviation, equal tone error, then
  the smaller g) keeps the second at N = 23–33 and the third at 34–35. The
  staircase of values is the registered one; the representative is not.
  An unregistered rung: Ptolemy N = 42–48 at **0.011¢ @ 249.018**
  (−2, −37, 0), tone error 0.02¢.
- **P-T2 — KEPT on the arrival, REFUTED as registered on dominance.** Full
  frozen survival arrives first at **N = 22 for the hexany (12/12 at
  193.908¢, tone error 2.22¢; CPSFIT-001 needed N = 31)**, N = 23 for EG4
  (24/24 at 193.309¢, mapping (−15, 2, 5), tone error 3.87¢; CPSFIT-001
  needed 31), N = 12 for Ptolemy, all as registered. The clause "survival
  under the new objective ≥ tone-minimax survival at every N ≥ 15" is
  false at hexany N = 18–21 (6 against 8) and EG4 N = 19–22 (14 against
  16): the miracle chain at 116.588¢ has the smaller worst triad (2.43¢
  against orwell's 3.42¢ at 271.425¢) but orwell keeps more triads. The
  scratch table showed exactly this and the registration asserted the
  opposite; the error is the session's.
- **P-T3 — KEPT.** Every hexany mapping as registered, including the
  (−1, −9, 2) rung at N = 13–14 that the tone staircase never visits, and
  the N = 48 optimum is non-homomorphic (582.450¢, 0.295¢ against the
  (−22, 5, −3) val's 0.305¢).
- **P-T4 — KEPT.** Frozen survival at the hexany N = 11 triad-minimax
  optimum is 4 against 8 at the tone-minimax optimum; Ptolemy N = 7 is 0
  against 6 at Erv's 502.346¢. The worst triad is not the count.
- **P-T5 — KEPT.** The N = 15 chain at 503.185¢ (0.463¢ from Erv's
  H[n−1] + 32·H[n−4], power-of-two, in-octave) scores frozen P@2¢ = 17 ≥
  11.

**Measured, not registered (post-hoc lenses, labelled):** (1) The
objective trades one tone for all twelve triads: at N = 22 the generator
moves 0.121¢ and the 7/4's error rises from 1.37 to 2.22¢ while the two
triads that CPSFIT-001 lost by 0.08¢ come in; the chain's own P@2¢ is 37.
(2) Half-generator ties are generic: whenever an N-chain of g contains the
lattice, the 2N-chain of g/2 contains it with the same triad deviations,
so from N ≈ 2·N_min on the objective cannot distinguish them and the
tie-break decides; a report should quotient by this. (3) The EG4 N = 23
fit (−15, 2, 5) differs from (16, 2, 5) only in the 3-mapping, and 31
generators of 193.309¢ are 5992.6¢, 7.4¢ short of five octaves: the chain
nearly closes at 31 and the two mappings are the two sides of that
near-closure. (4) The count objective is the open question this run
sharpens: at N = 18–21 the miracle and orwell chains disagree on which
matters, the worst triad or the number of survivors, and only the ear can
say which it hears.

**Kept.** Runner and receipts stand; `results/scl/cpsfit002/` holds the
hexany N = 22 chain at 193.908¢ (all twelve triads within 2¢) beside
CPSFIT-001's 193.787¢ chain — gate G-031.

**Run receipt:** 2026-10-10, python3.12 — lattice suite 354/354 OK (10 new:
test_cpsfit002), freeze checks A OK on both pins (scorer 1a840af9…b592,
melodic a16f162b…7535); both receipts and the .scl bit-identical across
two runs.

## 2026-10-11 — CPSFIT-003 pre-registration (entry BEFORE any implementation or run)

**Question (program B, the third objective).** CPSFIT-002 showed that the
worst triad and the number of surviving triads disagree: at hexany N = 18
to 21 the miracle chain has the smaller worst triad and the orwell chain
keeps more triads. This experiment makes the count the objective. For each
N it finds the generator and murchana that keep the MOST exact lattice
triads within 2 cents, with the frozen scorer as referee. It asks three
things. Does the count objective choose different generators from the
tone-minimax (CPSFIT-001) and the worst-triad-minimax (CPSFIT-002) at
N = 11 to 22, on the hexany, EG4 and the dekanies? What does the count buy
at the miracle/orwell fork? And does the self-inverse CPS theorem hold on
the dekany pair the way the playground page states it?

**Lattices.** Five, all 7-limit (9 = 3², so the mapping machinery of
CPSFIT-001 applies unchanged):
1. hexany CPS(4,2){1,3,5,7}: 6 tones, 12 exact triads (6 P + 6 S).
2. EG4 tesseract, 8 tones: 24 exact triads (12 + 12).
3. dekany CPS(5,2){1,3,5,7,9}: 10 tones, 41 exact triads (25 P + 16 S).
4. the exact reflection 1/CPS(5,2) (the control for the inversion theorem):
   10 tones, 41 exact triads (16 P + 25 S).
5. dekany CPS(5,3){1,3,5,7,9}, which equals 945/512 times lattice 4:
   10 tones, 41 exact triads (16 P + 25 S).
The dekany with 11 is out of scope here because the mapping and kernel
code is 7-limit.

**Chain model (as CPSFIT-002).** N notes of one generator g in (0, 600]
cents, window of consecutive degrees that contains degree 0, every lattice
tone within 20 cents of its assigned degree. Candidate assignments are the
nearest-degree assignments found on the 0.5 cent grid (CPSFIT-002's
enumeration). Each candidate is then explored over its FULL tone-cap basin,
the intersection of the per-tone intervals of half-width 20/|k| cents, and
not only within 0.5 cents of the grid point. So a candidate can be
evaluated at a g where it is no longer the nearest-degree assignment. The
image is still a valid image: every tone sits within 20 cents of its
degree.

**Survival predicate (shared with cpsfit001's mirror and with the frozen
guard).** An exact triad, voiced with each member at its fitted degree in
the octave nearest the exact pitch, survives at ε iff |dev| < ε and the
AM–HM separation ≥ ε. Here ε = 2 cents (LOCK).

**Objective and search.** For a fixed assignment the voiced members are
linear in g, so each triad's survival set in g is a union of intervals. The
sweep samples the basin at steps of at most 0.1 cents, bisects every
boundary 40 times, and also bisects zero crossings of the signed deviation
between two dead samples (a window narrower than the sample step). The
count as a function of g is piecewise constant. Segments narrower than
0.01 cents are discarded: a registered count must survive a change of g by
±0.005 cents. The objective is the largest count over all candidates and
segments. The representative inside the best segment is the g that
maximizes the smallest margin ε − |dev| over the surviving triads. When
every triad survives this is CPSFIT-002's minimax. Ties break toward the
smaller tone error, then the smaller g (keys rounded to 10⁻⁶). The murchana
is reported as the full range of window starts that contain the assignment
and degree 0, not only the smallest.

**Referee.** The frozen triads v1.1.0 `score_tempered` of the IMAGE (the
fitted pitch classes) at 2 cents, P + S. The objective counts exact lattice
triads only. The frozen count can be larger, because the tempering can
create triads among the image pitch classes that the exact lattice does
not have. Both counts are reported on every row. Per fit, as CPSFIT-001:
homomorphism (extended by a transposed-val test, k = j + Σ eₚkₚ for one
constant j), kernel, MOS flag, frozen chain scores at 2 cents, frozen
melodic, image survival at 1, 2, 3 and 5 cents, the mirror's deviations,
nearest two-term recurrences. Comparison columns: the tone-minimax fit
(cpsfit001.fit) and the triad-minimax fit (cpsfit002.fit_triads) are
recomputed in the runner for all five lattices at the same N. For the
hexany and EG4 the recomputed values must match the CPSFIT-001 and
CPSFIT-002 receipts. N runs from 11 to 36. Infeasible N (no assignment
under the cap) are reported as such.

**Predictions (independent scratch sweep 2026-10-11, same survival
predicate, same tie-break. The frozen scorer referees the counts).**
Tolerances: counts exact, g within 0.02 cents, tone error and deviation
within 0.05 cents.

- **P-C1 (the count staircases).** Rows give N: count / exact @ g
  (mapping), then the tone error of the representative.
  Hexany: 11: 6/12 @ 249.211 (−2, −8, −1), 20.00 (the representative sits
  on the tone cap). 12–15: 8/12 @ 317.175 (6, 5, 3), 17.74. 16–17: 10/12 @
  116.676 (6, −7, −2), 5.22. 18–21: 10/12 @ 77.818 (9, 5, −3), 3.87. 22–30:
  12/12 @ 193.908 (16, 2, 5), 2.22. 31–36: 12/12 @ 77.195 (−22, 5, −3),
  0.75.
  EG4: 11 infeasible. 12–14: 10/24 @ 249.211 (−2, −8, −1), 20.00. 15: 16/24
  @ 317.175 (6, 5, 3), 17.74. 16–17: 18/24 @ 116.676 (6, −7, −2), 7.12.
  18–22: 20/24 @ 77.791 (9, 5, −3), 4.03. 23: 24/24 @ 193.309 (−15, 2, 5),
  3.87. 24–30: 24/24 @ 193.883 (16, 2, 5), 2.21. 31–36: 24/24 @ 77.191
  (−22, 5, −3), 0.92.
  Dekany CPS(5,2): 11–14 infeasible. 15–17: 12/41 @ 503.939 (−1, −4, −10),
  20.00. 18: 14/41 @ 497.514 (no val), 20.00. 19–24: 25/41 @ 317.049
  (6, 5, 3), 18.75. 25: 26/41 @ 234.429 (3, 17, −1), 4.28. 26–32: 32/41 @
  498.066 (−1, 8, 14), 4.10. 33–34: 34/41 @ 351.484 (no val), 9.59. 35–36:
  37/41 @ 316.825 (6, 5, 22), 4.21.
  Dekany CPS(5,3): 11–16 infeasible. 17–21: 13/41 @ 497.381 (no val),
  20.00. 22: 17/41 @ 233.453 (3, 12, −1), 13.53. 23: 22/41 @ 350.827 (no
  val), 20.00. 24–25: 25/41 @ 317.049 (6, 5, 3), 18.75. 26–32: 32/41 @
  498.066 (−1, 8, 14), 4.08. 33–34: 34/41 @ 351.484 (no val), 9.59. 35–36:
  35/41 @ 497.399 (no val), 6.47.
  The "no val" rows are registered as non-homomorphic under the transposed
  test too (shift j = 0 everywhere a val exists).
- **P-C2 (the count picks differently).** For N in 11 to 22, the count
  optimum's generator lies within 0.05 cents of the tone-minimax optimum at
  NO N on any of the four distinct lattices. It lies within 0.05 cents of
  the triad-minimax optimum only at hexany N = 22 (193.908) and dekany
  CPS(5,2) N = 15–17 (503.939). Where the vals agree the generators still
  differ: hexany N = 16–17 keeps the miracle val (6, −7, −2) and moves g
  from 116.502/116.588 to 116.676, which raises the tone error from 4.77 to
  5.22 cents and the count from 6 to 10. Hexany N = 22–30 agrees with
  CPSFIT-002 (193.908, 12/12) and N = 31–36 agrees with both (77.195).
- **P-C3 (referee dominance, with one registered exception).** Frozen
  image survival at the count optimum is ≥ frozen survival at the
  tone-minimax optimum at every feasible N on all five lattices, and ≥
  frozen survival at the triad-minimax optimum at every feasible N except
  dekany CPS(5,2) N = 18. There the triad-minimax chain (503.939) scores
  15 by the frozen referee against 14 for the count optimum (497.514),
  while the exact counts are 12 against 14: three created triads tip the
  referee. Strict gains over BOTH prior objectives: hexany N = 12–21 (8 vs
  2–4 at 12–15, 10 vs 6 at 16–17, 10 vs 8/6 at 18–21), EG4 N = 12–22 (18 vs
  12 at 16–17, 20 vs 16/14 at 18–22), dekany CPS(5,2) N = 19–36 (32 vs 27
  at 26–32, 37 vs 33 at 35–36), dekany CPS(5,3) N = 17–36.
- **P-C4 (full survival).** The first N with every exact triad surviving
  is 22 for the hexany, 23 for EG4, and none up to 36 for either dekany
  (best 37/41 for CPS(5,2) at N = 35, 35/41 for CPS(5,3) at N = 35). These
  equal CPSFIT-002's arrival N where it was reached, as the predicate
  implies (a full count is a worst deviation under 2 cents with every
  separation at least 2 cents).
- **P-C5 (the inversion theorem, exact half and transposed half).**
  (a) The exact reflection 1/CPS(5,2) reproduces CPS(5,2)'s staircase at
  every N: same count, same g to 0.001 cents, same worst deviation and
  margin, with P and S swapped exactly in the frozen image (P₅₂ = S_refl,
  S₅₂ = P_refl at every N), and the mirrored window −(s + N − 1) is a valid
  window of the reflected fit. (b) CPS(5,3) does NOT reproduce it. Its
  staircase differs from CPS(5,2)'s at N = 17–25 and 35–36 and agrees at
  N = 26–34. The page's background fact "one fit of a dekany solves both
  dekanies" is therefore refuted as stated, because CPS(5,3) is the
  reflection TRANSPOSED by 945/512 (1061.49 cents), and a transposition by
  an interval that is not a chain degree changes a fit whose chain is
  pinned to contain the lattice's 1/1. The page will be corrected to the
  reflection statement when the receipt lands (the receipt wins).
  Measured in the scratch for the tone-minimax fit too: CPS(5,3) has the
  same generator and error as CPS(5,2) only at N = 17–19 and differs at
  N = 11–16 and 20–24.
- **P-C6 (the fork dissolves).** At hexany N = 18–21 neither miracle
  (6/12) nor orwell (8/12) is the count optimum: the (9, 5, −3) chain at
  77.818 cents keeps 10/12 with tone error 3.87 cents. At N = 16–17 the
  miracle val itself keeps 10/12 once g moves to 116.676. CPSFIT-002's
  miracle-against-orwell disagreement was a property of the two objectives,
  not of the two vals.
- **P-C7 (created triads, registered as a measurement).** The frozen
  referee exceeds the exact count at hexany N = 11 (8 vs 6), EG4 N = 12–14
  (12 vs 10) and 15 (18 vs 16), CPS(5,2) N = 15–17 (15 vs 12) and 19–24
  (27 vs 25), CPS(5,3) N = 17–21 (17 vs 13), 22 (19 vs 17), 23 (23 vs 22)
  and 24–25 (27 vs 25). It equals the exact count on every other row.

**Deliverables.** The runner `cpsfit003.py`. The receipts
`results/cpsfit003.jsonl` (one row per lattice × feasible N) and
`results/cpsfit003_summary.json`. Three Scala files under
`results/scl/cpsfit003/`, offered for listening as a standing gate: the
hexany N = 16 chain at 116.676 (miracle, 10 of 12), the hexany N = 18 chain
at 77.818 (10 of 12), and the dekany CPS(5,2) N = 26 chain at 498.066 (32
of 41). Tests `tests/test_cpsfit003.py` are green before the first run.
Stdlib only, python3.12, deterministic, no wall-clock fields. Two runs
must be bit-identical.

## 2026-10-11 — CPSFIT-003 results + verdicts

**Run:** `cpsfit003.py` (602 s. Receipts `results/cpsfit003.jsonl`, 115
rows = hexany N = 11..36, EG4 12..36, CPS(5,2) 15..36, its reflection
15..36, CPS(5,3) 17..36, plus `results/cpsfit003_summary.json`.) Frozen
triads v1.1.0 (`score_tempered`, 2 cents) and melodic v0.1.0 read-only,
pins verified. Lattice suite 371/371 green before the run (17 new tests).
The objective (exact count) agrees with the mirror's survival count on
every row (0 disagreements). The recomputed tone-minimax and triad-minimax
fits match the CPSFIT-001 and CPSFIT-002 receipts on the hexany and EG4
(0 mismatches).

- **P-C1 — KEPT.** Every registered rung reproduces on all four distinct
  lattices: counts exact, generators within 0.02 cents, tone errors within
  0.05 cents, mappings as registered, and every "no val" row is also free
  of a transposed val. First feasible N: 11, 12, 15, 15, 17 as registered.
- **P-C2 — KEPT.** For N ≤ 22 the count optimum sits within 0.05 cents of
  the tone-minimax optimum at no N on any lattice. It sits within 0.05
  cents of the triad-minimax optimum only at hexany N = 22 and CPS(5,2)
  N = 15–17. Hexany N = 16–17 keeps the miracle val (6, −7, −2) and moves
  the generator to 116.676 cents: count 10 against 6 for both prior
  objectives.
- **P-C3 — REFUTED as registered, held in substance.** The runner found
  two referee exceptions against the triad-minimax fit, (CPS(5,2), 18) and
  (reflection, 18), where the registration named only the first. The
  reflection lattice duplicates its partner's rows by construction, so the
  second exception is the first one seen in the mirror. The session left it
  off the list. The error is the session's. The numbers at CPS(5,2) N = 18
  are as registered: frozen 14 against 15, exact 14 against 12, three
  created triads tip the referee. There are no exceptions against the
  tone-minimax fit on any lattice.
- **P-C4 — KEPT.** First full survival at N = 22 (hexany), 23 (EG4), none
  up to 36 for either dekany. Best partial: 37/41 at N = 35 for CPS(5,2),
  35/41 at N = 35 for CPS(5,3). Wherever the count is full the
  triad-minimax fit is full too.
- **P-C5 — (a) KEPT, (b) REFUTED as registered, held in substance.**
  (a) The exact reflection reproduces CPS(5,2)'s staircase at every N:
  same count, generator, worst deviation and margin to 0.001 cents, P and
  S swapped exactly in the frozen image, and the mirrored window
  −(s + N − 1) is a valid window of the reflected fit at every N.
  (b) CPS(5,3) differs from CPS(5,2) at N = 15–23, 25 and 35–36, and
  agrees at N = 24 and 26–34. The registration said "differs at 17–25 and
  35–36, agrees at 26–34". Two session errors. First, the registered lists
  were copied from the scratch table before the 0.01 cent segment-width
  rule was added. That rule moved CPS(5,3) at N = 24–25 from a knife-edge
  26 at 309.996 cents to 25 at 317.049 cents, which is CPS(5,2)'s rung at
  N = 24, so N = 24 now agrees. Second, the runner counts N = 15–16, where
  CPS(5,2) is feasible and CPS(5,3) is not, as differences, and the scratch
  compared only the overlap. The finding stands: of the 20 values of N
  where both dekanies are feasible, 10 give different fits. The page's
  claim "one fit of a dekany solves both dekanies" is false as stated and
  is corrected to the reflection statement.
- **P-C6 — KEPT.** Hexany N = 18–21: 10/12 at 77.818 cents under
  (9, 5, −3). N = 16–17: 10/12 under the miracle val. The miracle/orwell
  fork of CPSFIT-002 was a property of the two objectives.
- **P-C7 — REFUTED as registered, held in substance.** Every registered
  created-triad row reproduces exactly. The reflection lattice's rows
  (N = 15–17: 15 against 12, N = 19–24: 27 against 25) were not
  registered, and they duplicate CPS(5,2)'s rows as in P-C3. No other
  unregistered created triads appear on any row.

**Measured, not registered (post-hoc lenses, labelled).** (1) The CPS(5,2)
N = 26 chain at 498.066 cents is a schismatic fourth chain: mapping
(−1, 8, 14), kernel 32805/32768, 5120/5103, 225/224, 4000/3969. It keeps
32 of 41 exact triads at 2 cents with tone error 4.10 cents, and its own
frozen P at 2 cents is 97. Both prior objectives stop at 27 on the same
val. (2) The count's 34/41 at N = 33–34 is the 351.484 cent neutral-third
chain, MOS-LAT-002's hot spot, with no val and tone error 9.59 cents. The
count objective finds it and the tone and triad objectives do not. (3) The
hexany N = 16 win is narrow: the 10/12 segment is 0.026 cents wide and the
margin at the representative is 0.098 cents. The N = 18 chain at 77.818
has kernel 6144/6125, 1029/1024, 126/125, and all ten of its survivors sit
between 1 and 2 cents (image survival at 1 cent is 0). (4) The
representative sits on the 20 cent tone cap at hexany N = 11, EG4
N = 12–14, CPS(5,2) N = 15–18 and CPS(5,3) N = 17–21 and 23, so those
rungs depend on the cap. A cap sweep (5, 10, 20 cents) is the natural
control. (5) The count optimum is a level of its generator (a 2-step MOS)
at only a few N: the hexany at 15, 25 and 31, EG4 at 14, 15, 25 and 31,
CPS(5,2) at 19 and 29, CPS(5,3) at 17 and 29. Everywhere else it is a
3-step chain. (6) At 5 cents the
frozen referee counts 43 image triads on the CPS(5,2) N = 26 chain, more
than the lattice's 41, which is the created-triad effect at a looser tier.

**Kept.** Runner and receipts stand. `results/scl/cpsfit003/` holds the
hexany N = 16 chain at 116.676 cents (10 of 12), the hexany N = 18 chain at
77.818 cents (10 of 12) and the CPS(5,2) N = 26 chain at 498.066 cents (32
of 41), offered for listening as gate G-032.

**Run receipt:** 2026-10-11, python3.12 — lattice suite 371/371 OK (17 new:
test_cpsfit003), freeze checks A OK on both pins (scorer 1a840af9…b592,
melodic a16f162b…7535). Both receipts and the three .scl are bit-identical
across two runs (`cmp`). Each run 602 s.

## 2026-10-12 — RANK3-001 pre-registration (entry BEFORE any implementation or run)

**Question (Marcus, 2026-10-12).** The iOS Wilsonic (Wilsonic_v_1_8_6,
`Wilsonic/Brun/Brun3.m`, 2016) builds scales from the octave and TWO
generators with Viggo Brun's three-term algorithm (Erv's "Viggo Rhythm"
paper). Marcus did not port it to Wilsonic MTS-ESP for lack of time and
asked whether it lets a smaller scale hold a larger just lattice. If it
does, rank 3 is to be explored in full. This experiment measures that: for
each note count N, the smallest largest-tone-error at which a Brun3 scale
holds the lattice, the triads that survive, and the temperament each
winning scale is.

**The Brun3 construction (ported, to be a new file `brun3.py`).** Inputs
O > G0 > G1 > 0 in octaves. Level 0 is the single interval O. At each level
the three current intervals are sorted large to small. The largest A is
replaced by A − B (calc type AB) or A − C (calc type AC). In the step list
every copy of the old largest step is replaced by its two pieces, with the
iOS "balance" rule: the second piece B goes first unless the previous step
already equals B. Levels run to 7. Each step is tracked as an exact
integer triple over (O, G0, G1), so every degree is an integer combination
and a fitted lattice has a three-row val (octave, G0, G1 rows). Rank here counts the octave: a 7-limit
lattice is rank 4 and a two-generator scale is rank 3 (octave-equivalently
3 and 2, the convention of SPEC.md), so a rank-3 fit leaves exactly one
comma in the kernel.
The port reproduces the iOS header's example: (2/1, 3/2, 5/4) under AB
gives levels of 1, 2, 3, 5, 7, 10, 15 and 22 notes, the 5-note level is
1/1, 5/4, 4/3, 3/2, 15/8, and AC at level 5 gives 1/1, 16/15, 5/4, 4/3,
3/2, 8/5, 15/8. Murchana (mode) rotates the scale to any degree.

**Lattices.** Hexany CPS(4,2){1,3,5,7}, the EG4 tesseract (8 tones),
dekany CPS(5,2){1,3,5,7,9}, and the eikosany CPS(6,3){1,3,5,7,9,11}
(20 tones, 114 exact triads: 57 P + 57 S). The eikosany is rank 5, so no
rank-3 scale can hold it exactly. It is included to measure how close
two generators get and how many triads survive, which is the number
Marcus cares about.

**Search.** Objective: the largest circular tone error (tone minimax, as
CPSFIT-001), with the lattice's 1/1 on a scale degree (the mode). Stage 1
enumerates (g0, g1) on a 2 cent grid over 0 < g1 < g0 < 1200 cents, both
calc types, levels 1 to 7, every mode, and keeps the best candidates per
N. Stage 2 refines each candidate exactly: with the scale's coefficient
structure, mode and nearest-degree assignment held fixed, the minimax over
(g0, g1) is a Chebyshev linear program in two unknowns. The runner solves
it exactly (vertex enumeration), subject to the ordering constraints that
keep the Brun3 structure valid, and rejects a solution whose structure
changes. Per fit: the three-row val by exact integer solve on the tones'
monzos, the kernel comma (box |e3| ≤ 12, |e5| ≤ 6, |e7| ≤ 5, under 60
cents, Tenney height ≤ 2^40), frozen image survival at 2 cents (P + S),
the mirror's triad deviations, whether the scale has 2 or 3 step sizes,
frozen melodic of the scale. Stdlib only, multiprocessing allowed,
deterministic, two bit-identical runs. The scratch that produced the
predictions used a 2 cent grid with a coordinate-descent refinement and
no exactness guarantee, so the registered errors are UPPER bounds: the
runner must find an error at most the registered value plus 0.05 cents
at each listed N. A better optimum with a different comma refutes the
comma clause.

**Predictions (scratch sweep 2026-10-12, 2 cent grid, python3.11 with
numpy; the frozen scorer referees survival).**
- **P-R1 (hexany staircase and commas).** N: error ≤ (comma, survival at
  2 cents). 10: 2.57 (225/224, 4/12). 15: 2.81 (1029/1024, 10/12). 19:
  0.61 (65625/65536, 12/12). 20: 2.57 (225/224, 10/12). 21: 0.12
  (2401/2400, 12/12). 24: 0.46 (32805/32768, 12/12). 27: 0.12 (2401/2400;
  12/12). 29: 0.25 (32805/32768, 12/12). The first N within 2 cents is 19
  (rank 2: 22) and the first N with all 12 triads is 19 (rank 2: 31 under
  the tone fit, 22 under the triad fit). Survival is ≥ the listed value.
- **P-R2 (EG4).** 10: 2.57 (225/224, 8/24). 15: 2.81 (1029/1024, 18/24).
  19: 0.47 (65625/65536, 24/24). 21: 0.12 (2401/2400, 24/24). 24: 0.46
  (32805/32768, 24/24). First full survival at N = 19 (rank 2: 23).
- **P-R3 (dekany with 9).** 21: 3.27 (1728/1715, 25/41). 29: 0.66
  (32805/32768, 41/41), with G0 a fifth of 701.73 cents and G1 of 64.0
  cents. Rank 2 reached 37/41 at best below N = 37 and never 41. So the
  schisma, tempered once, is what the dekany with 9 needs.
- **P-R4 (eikosany).** No Brun3 scale up to level 7 (N ≤ 34) holds the
  eikosany within 10 cents. The best is about 12 cents at N = 31, and
  survival never exceeds 29 of 114 at any N ≤ 34. Two generators are not
  enough for a rank-5 lattice. Three generators (Brun's four-term
  algorithm) are the natural next step and are out of scope here.
- **P-R5 (every winner is a val).** At every N listed in P-R1 to P-R3 the
  optimum is homomorphic with exactly one kernel comma under 60 cents in
  the box, and the comma is the one listed.
- **P-R6 (depth).** Every hexany fit within 3 cents occurs at level 7, the
  deepest level, and both calc types appear among the winners (AC at
  N = 10 and 24, AB elsewhere).

**Deliverables.** `brun3.py` (the port, stdlib) with tests pinned to the
iOS example. `rank3001.py` and `tests/test_rank3001.py`, green before the
first run. Receipts `results/rank3001.jsonl` and
`results/rank3001_summary.json`. Scala exports under `results/scl/rank3001/`
for the hexany at N = 19 and N = 21 and the dekany at N = 29, offered for
listening as a standing gate.

## 2026-10-12 — RANK3-001 results + verdicts

**Run:** `rank3001.py` (50 s with 8 worker processes. Receipts
`results/rank3001.jsonl`, 122 rows = one per lattice and note count, plus
`results/rank3001_summary.json`.) Frozen triads v1.1.0 (`score_tempered`,
2 cents) and melodic v0.1.0 read-only, pins verified. Lattice suite
388/388 green before the first run (8 tests for `brun3.py`, 10 for the
runner). Four generator pairs on the grid are commensurable with the octave
(600 with 450 cents, 900 with 300, 1050 with 450, 1050 with 750, all under
A−C) and Brun3 runs out of intervals there. The runner skips and counts
them. Every refined fit kept its Brun3 structure at the solution.

- **P-R1 — REFUTED as registered on one clause, held on the rest.** Every
  error bound holds and the runner improves on three: hexany N = 19 is
  0.47 cents (registered 0.61), N = 24 is 0.24 (registered 0.46), N = 29 is
  0.24 (registered 0.25). Every registered comma reproduces (225/224 at
  N = 10 and 20, 1029/1024 at 15, 65625/65536 at 19, 2401/2400 at 21 and
  27, 32805/32768 at 24 and 29). The first N within 2 cents is 19 and the
  first N with all 12 triads is 19, as registered. The clause that fell:
  at N = 20 the runner's optimum (699.384 and 693.772 cents) has the same
  worst tone error as the scratch's (2.571 against 2.574 cents, a better
  solution by 0.003 cents) and keeps 4 triads where the scratch's chain
  kept 10. Tone minimax has ties at N = 20 and the tie-break is the error,
  so a survival floor was not a prediction the objective could carry. The
  error is the session's.
- **P-R2 — KEPT.** EG4 reproduces every rung and comma, with N = 19 at
  0.47 cents (24/24) and N = 24 at 0.24, and first full survival at N = 19.
- **P-R3 — REFUTED as registered on the generator pair, held on the
  rest.** The dekany with 9 reaches 41/41 at N = 29 under the schisma
  32805/32768 at 0.651 cents (registered 0.66), and 25/41 at N = 21 under
  1728/1715 at 3.27 cents. The runner's N = 29 scale uses the pair
  (498.262, 27.047) cents, a fourth and a 27 cent step, where the scratch's
  pair was (701.73, 64.0). The two scales are different (their closest
  modes differ by 6.2 cents), both are schismatic, and the runner's is the
  better one. A generator pair is a choice of coordinates on the
  temperament and is not invariant, which is what the session told Marcus
  the same day and then registered anyway. The comma is the invariant and
  it held. The error is the session's.
- **P-R4 — REFUTED as registered, held on the quantity the scratch
  measured.** No Brun3 scale up to level 7 holds the eikosany within 10
  cents. The best is 11.98 cents at N = 31, as registered. Survival by the
  mirror (exact triads, |dev| < 2 and separation ≥ 2 cents) never exceeds
  28 of 114, inside the registered 29. Survival by the frozen referee
  reaches 59 of 114 at N = 28 and 58 at N = 22 and 24, because the frozen
  scorer counts every triad among the 20 image pitch classes, and at 15
  cents of tone error the tempering creates dozens that the lattice does
  not have. The registration said "survival" and the runner's verdict
  used the frozen number, so the clause fell. The scratch's number was the
  mirror. Both are now on every row. The error is the session's.
- **P-R5 — REFUTED as registered, held in substance.** Every winner at a
  registered N is a val. At N = 10 and 20 (hexany) and N = 10 (EG4) the
  kernel box holds two commas under 60 cents, 225/224 and its square
  50625/50176. The kernel is rank 1 as the registration meant, and the
  listing counts a multiple as a second comma. The error is the session's
  wording.
- **P-R6 — KEPT.** Every hexany fit within 3 cents is at level 7, and the
  calc types at the registered N are as listed (A−C at N = 10 and 24, A−B
  elsewhere).

**Measured, not registered (post-hoc lenses, labelled).** (1) New rungs
the scratch missed: hexany N = 18 at 2.18 cents under 1728/1715 (4/12),
N = 23 at 2.18 cents with no val (8/12), N = 22 at 1.34 under 6144/6125
(10/12). (2) Hexany N = 26 keeps all 12 triads at 1.07 cents with NO val:
a rank-3 accident, the first non-homomorphic fit in the program with full
survival. Three generator pairs tie at that N ((424.78, 119.89),
(424.78, 230.55), (775.22, 119.89)), which is the coordinate freedom of
P-R3 again. (3) EG4 N = 31 at 4.30 cents tempers 81/80 alone: a meantone
with 7 left free, which is the first time the syntonic comma appears in
these fits. EG4 N = 18 tempers 875/864 (10/24). The dekany at N = 14
tempers 49/48 (15.3 cents, 12/41). (4) The rank-2 and rank-3 ladders side
by side for the hexany at 2 cents: rank 1 (ET) needs more than 72 notes
(CPSFIT-001 scanned 5 to 72 and found none; the comma-dial page computes
the first as 130-ET at 1.78 cents, which is not a receipt), rank 2
needs 22 (1.37 cents, 10/12), rank 3 needs 19 (0.47 cents, 12/12), rank 4
is the hexany itself at 6 notes and zero error. Each rank buys one comma.
(5) Every count-and-error winner at level 7 has three step sizes. The only
two-step winners are the dekany at N = 30 and the eikosany at N = 29,
neither of them a good fit. A rank-3 scale that holds a lattice is a
three-interval pattern, not an MOS, which is what Brun's algorithm says it
should be. (6) The eikosany stays at 12 to 16 cents from N = 22 up with no
val anywhere, which is the rank-5 wall. Three generators are the next
rung.

**Kept.** Runner and receipts stand. `results/scl/rank3001/` holds the
hexany N = 19 scale (1002.862 and 385.844 cents, 65625/65536), the hexany
N = 21 scale (350.978 and 231.294 cents, 2401/2400) and the dekany N = 29
scale (498.262 and 27.047 cents, the schisma), offered for listening as
gate G-033.

**Run receipt:** 2026-10-12, python3.12 — lattice suite 388/388 OK (18 new:
test_brun3, test_rank3001), freeze checks A OK on both pins (scorer
1a840af9…b592, melodic a16f162b…7535). Both receipts and the three .scl are
bit-identical across two runs (`cmp`). Each run 50 s with 8 workers.

## 2026-10-13 — GOLD-002 pre-registration (entry BEFORE any implementation or run)

**Question (Marcus, 2026-10-13, a series he asked Claude to own).** Erv
found his recurrence generators by optimizing proportional and subcontrary
triads by hand. The first five measured sat 0.07 to 0.61 cents from a
golden generator. Is "optimize the triads and you land near a noble
number" a law? If it is, the generator-family selector in the planned
Wilsonic design costs nothing. If it is not, the selector is a real trade
between closure character and harmony. This experiment measures the
claim against a null model, because nobles are dense: with seed
denominators up to 60 there are 1102 golden generators in 600 cents, so
any generator at all sits within 0.18 cents of one on average. Nearness
only means something against the nearness of a random generator at the
same complexity.

**Generators.** The seventeen Erv and control generators the repo already
cites with sources: the sixteen two-term recurrences of MERU-001 (the
roots of H[n] = a·H[n−i] + b·H[n−j]: Erv 0.418935, 0.238186, Fig 12 #12,
0.415227, meta-meantone, the silver control 8H[n−9] + 7H[n−10], Fibonacci,
meta-pelog, meta-slendro, meta-Ptolemy, 0.591780, LLSLS, meta-slendro 2,
0.773743, Pell, and the playground pick fit351), plus phi (Fig 12 entry 1).
Each is folded to (0, 0.5] because g and 1 − g make the same chains. The
archive scans (read in place, never vendored) extend this list in a later
pass, GOLD-003.

**Nobles and complexity.** A golden generator is (a + φc)/(b + φd) for a
unimodular pair a/b, c/d (|bc − ad| = 1), either order. Silver uses
1 + √2. The COMPLEXITY of a noble is the smallest max(b, d) over every pair
that generates it, which is the seed pair where its scale-tree path starts
to alternate. The ladder is Q = 8, 12, 20, 30, 60 (22, 46, 128, 278 and
1102 golden generators, 33, 69, 192, 417 and 1653 silver). The earlier
page enumeration took only neighbours at the deepest Farey level and gave
every noble complexity 60. That is corrected here and on the page.

**Null model.** 20000 generators uniform on (0, 0.5], seed 20261013. For
each family and Q, the nearest-noble distance of each random generator
gives a distribution. Each Erv generator's distance is reported with its
percentile in that distribution. The strong form of the law says most of
the seventeen sit in the low tail (percentile ≤ 0.10) at some single Q.
The expected count under the null is 1.7 of 17.

**Chain triads.** For each Erv generator and its nearest golden (Q = 60),
the frozen P + S at 2 cents (`score_tempered`) of the N-chain of each at
the golden generator's MOS levels up to 41, from degree 0.

**Predictions (scratch 2026-10-13, deterministic, same definitions as the
runner).**
- **P-G2-1 (null distances).** Median nearest-golden distance of a random
  generator: 8.58, 4.21, 1.52, 0.71 and 0.18 cents at Q = 8, 12, 20, 30,
  60. Tenth percentile: 1.35, 0.66, 0.24, 0.11, 0.027 cents. Silver
  medians 5.54, 2.69, 0.97, 0.45, 0.11 cents.
- **P-G2-2 (the strong law is refuted).** Golden, Erv generators at or
  below the tenth percentile: Q = 8: 5 of 17 (0.418935, meta-meantone, the
  silver control, Fibonacci, phi). Q = 12: 5 (meta-meantone, Fibonacci,
  meta-pelog, fit351, phi). Q = 20: 3 (0.418935, the silver control,
  0.773743). Q = 30: 2 (meta-slendro, 0.773743). Q = 60: 4 (meta-slendro,
  meta-Ptolemy, 0.773743, Pell). Silver: 4, 5, 6, 4, 4. At no Q do more
  than 6 of 17 fall in the tail, so "most" fails at every Q. The weak form
  survives: 3 to 6 against an expected 1.7, and 0.773743 sits on a golden
  generator of complexity 20 to 0.00 cents.
- **P-G2-3 (registered distances, 0.01 cent tolerance).** Nearest golden
  at Q = 20: 0.418935 −0.12, 0.238186 −1.23, Fig 12 #12 −10.58, 0.415227
  −1.02, meta-meantone −0.58, silver control +0.16, Fibonacci −0.65,
  meta-pelog +0.31, meta-slendro +2.74, meta-Ptolemy +3.60, 0.591780 −0.30,
  LLSLS −2.74, meta-slendro 2 −2.72, 0.773743 −0.00, Pell −1.92, fit351
  −0.45, phi −0.65 cents. At Q = 60: 0.418935 +0.09 (seeds 18/43, 13/31),
  0.238186 +0.61, Fig 12 #12 −0.17, 0.415227 +0.07, meta-meantone +0.11,
  silver control −0.08, Fibonacci +0.07, meta-pelog +0.12, meta-slendro
  +0.02, meta-Ptolemy −0.02, 0.591780 +0.17, LLSLS −0.19, meta-slendro 2
  −0.05, 0.773743 −0.00, Pell −0.01, fit351 +0.11, phi +0.07.
- **P-G2-4 (Erv against the noble on the chain's own triads).** At the
  deepest common MOS level ≤ 41, Erv's generator out-scores its nearest
  golden (Q = 60) on frozen P + S at 2 cents for nine (0.418935 212
  against 190 at N = 31, 0.238186 138 against 94 at 25, Fig 12 #12 364
  against 314 at 40, meta-meantone 156 against 140 at 31, Fibonacci 366
  against 264 at 36, meta-slendro 404 against 380 at 37, meta-Ptolemy 400
  against 354 at 38, LLSLS 396 against 390 at 38, phi 366 against 264 at
  36), loses for six (0.415227 492 against 494 at 41, silver control 302
  against 372 at 41, meta-pelog 100 against 152 at 29, 0.591780 128
  against 154 at 27, meta-slendro 2 308 against 326 at 36, fit351 634
  against 652 at 41) and ties for two (0.773743 at 31, Pell at 37). At
  every level of 12 or fewer notes the two tie. Being near a noble is not
  the same as having its triads: a tenth of a cent moves dozens of
  2 cent coincidences at 30 notes.

**Deliverables.** `gold002.py`, `tests/test_gold002.py` green before the
first run, receipts `results/gold002.jsonl` + `results/gold002_summary.json`.
No Scala exports (nothing new to hear, because the generators are already on the
page). A gate for the verdict on the law and the design selector.

## 2026-10-13 — GOLD-002 results + verdicts

**Run:** `gold002.py` (about 10 s. Receipts `results/gold002.jsonl`, 17
rows, and `results/gold002_summary.json`. Two runs bit-identical, `cmp` on
both.) Frozen triads v1.1.0 read-only, pin verified. Lattice suite
399/399 green before the first run (11 new tests).

- **P-G2-1 — KEPT.** The null model reproduces every registered figure.
  A random generator sits a median 8.58, 4.21, 1.52, 0.71 and 0.18 cents
  from the nearest golden generator at Q = 8, 12, 20, 30 and 60.
- **P-G2-2 — KEPT. The strong law is refuted.** The golden tail
  memberships at every Q are exactly as registered (5, 5, 3, 2 and 4 of
  17), the silver tail counts are 4, 5, 6, 4 and 4, and at no Q do more
  than 6 of the 17 generators sit at or below the tenth percentile. "Most
  of Erv's generators sit near a noble number" is false at every
  complexity. The weak form stands: 3 to 6 in the tail against 1.7
  expected, and 0.773743 sits on a golden generator of complexity 20 to
  0.00 cents.
- **P-G2-3 — KEPT.** Every registered distance at Q = 20 and Q = 60
  reproduces within 0.01 cents, and 0.418935's nearest golden generator at
  Q = 60 is seeded by 18/43 and 13/31.
- **P-G2-4 — REFUTED as registered on one clause, held on the
  classification.** The nine Erv wins, six golden wins and two ties at the
  deepest common level reproduce exactly. The clause "at every level of
  12 or fewer notes the two tie" fails once: 0.238186 against its nearest
  golden at N = 9 scores 16 against 12. The scratch table showed that
  figure and the session wrote "every" anyway. The error is the
  session's. Every other level of 12 or fewer notes is a tie (15 of 16
  generators, all of their shallow levels).

**Measured, not registered (post-hoc lenses, labelled).** (1) The silver
family is as close to Erv's generators as the golden one: at Q = 20, six
of 17 sit in the silver tail (0.418935, the silver control, Fibonacci,
0.591780, fit351 and phi) against three in the golden tail. Erv's
2-zig/2-zag page may be the better description of several of his
generators. (2) The nearness and the triads part company at depth: nine
of Erv's generators out-score their nearest golden on the chain's own
P + S at 2 cents at the deepest common level, by as much as 138 to 94
(0.238186 at N = 25) and 366 to 264 (Fibonacci at N = 36), while the
nearest golden to 0.415227 wins 494 to 492 at N = 41 and the one nearest
the silver control wins 372 to 302. A tenth of a cent is nothing at 7
notes and everything at 30. (3) For the design: the generator-family
selector is a real trade. For most of Erv's generators a noble neighbour
of modest complexity does not exist within the tolerance that preserves
their triads, so "golden" and "best triads" are different settings and
the design should show the price of each. Erv's own list belongs in the
selector as its own family.

**Kept.** Runner and receipts stand. Nothing new to hear. Gate G-034 is
the verdict on the law and on the selector.

**Run receipt:** 2026-10-13, python3.12 — lattice suite 399/399 OK (11 new:
test_gold002), freeze check A OK (scorer 1a840af9…b592). Both receipts
bit-identical across two runs (`cmp`).

## 2026-10-13 — GOLD-001 pre-registration (entry BEFORE any implementation or run)

**Question (Marcus, 2026-10-13, the series Claude owns).** The planned
Wilsonic design fits an MOS to an Euler genus by triad survival and offers
the generator family as an aesthetic choice: free optimum, golden, silver,
Erv's list, ET. What does a family cost? For each lattice and note count
N, this experiment scores the golden and silver families by the same
triad-survival objective as CPSFIT-003 and compares them with the free
optimum, on a complexity ladder, with and without the MOS constraint
(the design needs a level, so a chain that is not a level does not count
for it). GOLD-002 (same day) showed that nobles are dense, so a family's
reach is measured per complexity Q, never only at Q = 60.

**Lattices.** Hexany CPS(4,2){1,3,5,7}, the EG4 tesseract, dekany
CPS(5,2){1,3,5,7,9}, and the eikosany's embedded subsets on seeds
1·3·5·7·9·11 from the SUBSET-MEL-000 census: 30 hexanies (one seed in,
one out), 6 dekanies with a seed in and 6 with a seed out. N runs 11 to
36 for the three 7-limit lattices and 11 to 24 for the 42 subsets.

**Measures, per lattice and N.**
1. The free count optimum c* and its generator g*: CPSFIT-003's receipts
   for the hexany, EG4 and the dekany, and `cpsfit003.fit_count` for the
   subsets. If any noble candidate keeps more triads than c*, the free
   optimum is reported as that larger count and the CPSFIT-003 receipt is
   flagged as beaten (its grid seeding can miss a narrow basin).
2. The free optimum restricted to MOS levels: CPSFIT-003's count segments
   intersected with the set of g for which N is a scale-tree level, which
   is the union of the open intervals between Farey neighbours p/q and
   p'/q' with q + q' = N. Exact, not a grid.
3. For each family (golden, silver) and each complexity Q in 8, 12, 20,
   30, 60: the best candidate by count (tie: smaller tone error) over all
   windows within the 20 cent tone cap, any N, and the best whose N is a
   level of the candidate. Candidates and complexity as GOLD-002 defines
   them (`gold002.nobles`).
4. The nearest candidate to g* at each Q, its distance and its count.
Survival is the mirror predicate (|dev| < 2 cents and separation ≥ 2) and
the frozen `score_tempered` count of the image is reported beside it.

**Predictions (scratch 2026-10-13, Q ladder and null as GOLD-002, the
MOS-only free optimum on a 0.5 cent grid, so its registered values are
lower bounds).**
- **P-G1-1 (hexany, golden).** At Q = 60 the golden best equals c* at
  every N from 11 to 36 except 16 and 17 (8 against 10). At Q ≤ 20 the
  golden best is 8 at every N from 12 to 36 and never reaches 10 or 12.
  At Q = 8 it is 4 at N = 15 to 31 and 5 at 32 to 36. The hexany's free
  optimum at N = 12 to 15 (317.175 cents, 8 of 12) is itself a golden
  generator of complexity 11 (seeds 3/11 and 1/4, in Erv's 64) to 0.005
  cents.
- **P-G1-2 (hexany, silver).** Silver reaches 10 at N = 18 to 28 and 12
  at N = 29 to 36 with complexity ≤ 20, and 12 from N = 22 at Q = 60. At
  Q ≤ 20 silver beats golden at every N from 16 to 36.
- **P-G1-3 (hexany, MOS only).** The golden best that is a level reaches
  12 first at N = 25 and again at 31 (193.993 cents, complexity 37),
  only at Q = 60. At Q ≤ 20 the level-only golden best never exceeds 8.
  The exact MOS-only free optimum is ≥ 8 at N = 15 and 19, and ≥ 12 at
  N = 25 and 31.
- **P-G1-4 (nearest golden to the free generator).** At Q = 60 the
  nearest golden to g* keeps c* at every N from 11 to 30 (distance ≤ 0.1
  cents) and keeps only 4 of 12 at N = 31 to 36 (0.17 cents away, outside
  the basin). At Q = 20 it keeps c* only at N = 12 to 15.
- **P-G1-5 (EG4).** Golden at Q = 60 equals c* only at N = 12 to 15 and
  36, and sits at 16 (N = 16 to 22), 20 (N = 23), 22 (N = 24 to 35)
  against 18, 20, 24, 24. Silver at Q = 60 equals c* at N = 12 to 15 and
  from 24 (24 of 24). Level-only golden at Q = 60 reaches 22 at N = 25
  and 31 and never 24.
- **P-G1-6 (dekany with 9).** At N = 13 to 18 a golden candidate at
  Q = 30 keeps 16 triads where CPSFIT-003's receipt has 12 (N = 15 to 17)
  and 14 (N = 18): the receipt is beaten and the free optimum is at least
  16 there. From N = 19 golden at Q = 60 trails: 22 against 25 (N = 19 to
  24), 25 against 26, 27 against 32 (N = 26 to 30), 29 against 32, 34
  against 34 (N = 33 to 34) and 34 against 37. Silver at Q = 20 reaches
  25 at N = 23 to 24, 27 to 28 at 26 to 32, 34 at 33 to 34 and 37 at 35
  to 36, so silver at complexity 20 equals or beats golden at
  complexity 60 at every N from 23 on.
- **P-G1-7 (eikosany subsets, aggregate over feasible cells).** Hexanies,
  408 cells: golden at Q = 60 reaches c* in 339, silver at Q = 60 in 369,
  golden at Q = 20 in 172, and silver at Q = 20 is at least golden at
  Q = 20 in 354. Full survival of a subset's own triads occurs in 165
  cells for the free optimum, 128 for golden at Q = 60 and 85 for silver
  at Q = 20. Dekanies, 124 cells: golden at Q = 60 reaches c* in 59,
  golden at Q = 20 in 11, and silver at Q = 20 is at least golden at
  Q = 20 in 97. Tolerance: ± 3 cells on every count, because the free
  optimum is recomputed and may move by one.
- **P-G1-8 (the design statement).** On every lattice the golden family
  at complexity ≤ 20 loses triads to the free optimum at most N, the
  silver family at the same complexity loses fewer, and the MOS-level
  constraint costs more than either family. The selector is a real
  trade and the N at which a family first reaches full survival is the
  number the design must show.

**Deliverables.** `gold001.py` on `gold002.nobles` and the CPSFIT-003
machinery, `tests/test_gold001.py` green before the first run, receipts
`results/gold001.jsonl` and `results/gold001_summary.json`, Scala exports
under `results/scl/gold001/` for the hexany's complexity-11 golden
generator at its 15-note level and the silver 12-of-12 chain at N = 29,
offered for listening. A gate.

## 2026-10-13 — GOLD-001 results + verdicts

**Run:** `gold001.py` v1.0.1 (about 130 s with 8 workers. Receipts
`results/gold001.jsonl`, 666 rows = 45 lattices × their N ranges, and
`results/gold001_summary.json`. Two runs bit-identical, `cmp` on both
receipts and the two .scl.) Frozen triads v1.1.0 read-only, pin verified.
Lattice suite green before the first run (7 new tests, then 8). Version
1.0.1 fixed a verdict bug found on the first run of 1.0.0: the subset
aggregate and the EG4 equality lists treated a survival count of zero as a
missing candidate. The measurements did not change. The recorded run is
1.0.1.

**A correction to CPSFIT-003.** A noble candidate is a chain the free
search should have found. In 28 rows one keeps more triads than the free
fit: the dekany with 9 at N = 13 to 18 keeps 16 under the golden generator
249.263 cents (complexity 29) where CPSFIT-003's receipt had 12 at N = 15
to 17 and 14 at N = 18 and no fit at 13 to 14. CPSFIT-003 seeds its
assignments on a 0.5 cent grid and this basin is narrower than that. The
runner reports the larger count as the effective free optimum and flags
the receipt. The CPSFIT-003 staircase on the page stands for the hexany
and EG4 and is superseded for the dekany at N = 13 to 18.

- **P-G1-1 — KEPT.** On the hexany the golden best at complexity 60
  equals the free count at every N except 16 and 17 (8 against 10), at
  complexity 20 or less it is 8 at every N from 12 to 36, at complexity 8
  it is 4 at N = 15 to 31 and 5 at 32 to 36, and the free optimum at
  N = 12 to 15 is the complexity-11 golden generator seeded by 3/11 and
  1/4 to 0.005 cents.
- **P-G1-2 — REFUTED as registered on one clause, held on the rest.**
  Silver at complexity 20 or less reaches 10 at N = 18 to 28 and 12 from
  N = 29, and silver at complexity 60 reaches 12 from N = 22, as
  registered. The clause "silver beats golden at complexity 20 or less
  from N = 16" fails at N = 16 and 17 (6 against 8). The scratch table
  showed those two values and the session wrote 16. The error is the
  session's. The clause holds from N = 18.
- **P-G1-3 — KEPT.** The level-only golden best reaches 12 exactly at
  N = 25 and 31 at 193.993 cents, never above 8 at complexity 20 or less,
  and the exact MOS-only free optimum is 8 at N = 15 and 19 and 12 at 25
  and 31 (and 30, 32, 34, which the lower bounds did not cover).
- **P-G1-4 — REFUTED as registered on N = 16 and 17, held on the rest.**
  The nearest golden to the free generator at complexity 60 keeps the free
  count at every N from 11 to 30 except 16 and 17, where it sits 0.097
  cents away and keeps 8 of the 10, and keeps 4 at N = 31 to 36. The
  scratch showed (0.1, 8) at N = 16 and 17 and the session registered a
  range that included them. The error is the session's. At complexity 20
  it keeps the free count only at N = 12 to 15, as registered.
- **P-G1-5 — REFUTED as registered on the values at N = 18 to 22, held
  on the rest.** EG4's golden best at complexity 60 equals the free count
  at N = 12 to 15 and 36 and nowhere else. Its values are 16 at N = 16 to
  17, 18 at N = 18 to 22, 20 at 23, 22 at 24 to 35. The registration wrote
  16 for the whole range 16 to 22. The scratch table showed 18 at 18 to
  22 and the session compressed the range. The error is the session's.
  Silver at complexity 60 equals the free count at N = 12 to 15 and from
  24, and the level-only golden best reaches 22 at N = 25 and 31 and
  never 24, as registered.
- **P-G1-6 — KEPT.** The dekany: the free count is at least 16 at N = 13
  to 18 (the receipt is beaten there), golden at complexity 60 is 22, 25,
  27, 29 and 34 on the registered ranges, silver at complexity 20 is 25,
  27 or more, 34 and 37 on its ranges, and silver at complexity 20 equals
  or beats golden at complexity 60 at every N from 23.
- **P-G1-7 — KEPT.** Hexany subsets, 408 cells: golden at complexity 60
  reaches the free count in 339, silver at 60 in 367, golden at 20 in
  169, silver at 20 is at least golden at 20 in 354, and full survival
  occurs in 165, 128 and 85 cells for the free optimum, golden at 60 and
  silver at 20. Dekany subsets, 124 cells: 59, 11 and 97. All within the
  registered 3 cells (the free optimum moved by the beaten-receipt rule
  in a few cells).
- **P-G1-8 — KEPT.** On each of the three 7-limit lattices the golden
  family at complexity 20 loses triads to the free optimum at more than
  half of the note counts, silver at the same complexity is at least
  golden at more than half, and the exact MOS-only optimum is below the
  free optimum at more than half.

**Measured, not registered (post-hoc lenses, labelled).** (1) The exact
MOS-only staircase for the hexany: a pure two-step scale keeps all 12
hexany triads at 2 cents first at N = 25 (193.91 cents, the breed-family
generator, 10 at N = 21 and 22), then at 30, 31, 32 and 34. For EG4 all 24
first at N = 25 and 31. For the dekany with 9, 25 of 41 at N = 19 (317.05
cents) and 32 at N = 29 (498.07 cents, schismatic). These are the numbers
the Wilsonic design's Gral has to make playable, because the design wants
a level. (2) The dekany's new 16-triad chain at N = 13 to 18 is the
249.263 cent golden generator of complexity 29 (seeds 6/29, 5/24), the
same neighbourhood as the hexany's N = 11 free optimum (249.211). (3) On
the eikosany's dekanies no family and no free chain reaches full survival
at N ≤ 24, and on its hexanies the free optimum reaches full survival in
165 of 408 cells against 128 for golden at complexity 60. (4) The two
Scala exports: the hexany at the complexity-11 golden generator's
15-note level (317.170 cents, 8 of 12) and the silver chain at N = 29
(316.827 cents, 12 of 12, tone error under 4 cents), which is the
cheapest noble full survival on the hexany at complexity 20.

**Kept.** Runner and receipts stand. Gate G-035 is the verdict on the
selector's price.

**Run receipt:** 2026-10-13, python3.12 — lattice suite 407/407 OK (8 new:
test_gold001), freeze check A OK (scorer 1a840af9…b592). Both receipts and
the two .scl bit-identical across two runs of v1.0.1 (`cmp`), about 130 s
each with 8 workers.

## 2026-10-14 — SUBFIT-001 pre-registration (entry BEFORE any implementation or run)

**Question (Marcus, 2026-10-13, the design goal).** The planned Wilsonic
design fits one MOS to an Euler genus and lets the player move through
the genus's subsets while the fitted scale stays under the hands. The
subset doctrine says the music lives in the subsets, so the fit that
matters is the one that keeps the most subsets playable at once. For the
classic eikosany on 1·3·5·7·9·11 and each note count N, which single
generator chain keeps the most of its 72 embedded subsets fully playable,
how many of the eikosany's 114 exact triads does it keep, and what does
the MOS-level constraint cost? The Gral makes a dense scale playable, so
N runs to 72.

**Objects.** The eikosany CPS(6,3){1,3,5,7,9,11}: 20 tones, 114 exact
triads (57 proportional, 57 subcontrary). Its 72 embedded subsets from
the SUBSET-MEL-000 census: 30 hexanies (one seed in, one out), 6 dekanies
with a seed in, 6 with a seed out, 15 harmonic tetrads, 15 subharmonic
tetrads. Every exact triad of every subset is one of the eikosany's 114
(checked, 0 unmatched). The subsets' own triad counts vary: hexanies have
2 to 18, dekanies 18 to 41, tetrads 1 to 7, because 9 = 3² makes some
pairs of tones coincide.

**Chain model.** N consecutive degrees of one generator g in (0, 600]
cents, any window (mode). There is NO tone cap: a tone outside every
surviving triad may sit anywhere, because the design only needs the
subsets it keeps. Each tone goes to the nearest degree inside the
window. A triad survives when its voiced members satisfy the mirror
predicate (|dev| < 2 cents and separation ≥ 2 cents). A subset is
PLAYABLE when every one of its exact triads survives. The objective per N
is lexicographic: most playable hexanies plus dekanies, then most playable
tetrads, then most of the 114 triads kept, then the smaller largest tone
error among the tones that sit in a kept triad.

**Search.** Stage 1: g on a 0.1 cent grid, every window, the objective as
above. Stage 2: the twelve best distinct grid generators per N refined on
a 0.002 cent grid over ± 0.1 cents. Also the MOS-only variant: the same
search restricted to g for which N is a scale-tree level (the exact level
intervals of GOLD-001), reported beside the free result. Per winner: the
list of playable subsets by name, the frozen `score_tempered` count of the
20-tone image, the val of the fit if one exists (11-limit, as RANK3-001
computes it) and the kernel commas, and the level flag. Stdlib,
multiprocessing over N, deterministic, two bit-identical runs.

**Predictions (scratch 2026-10-14, 0.1 cent grid with 0.002 cent
refinement, tones assigned to the nearest degree of the whole
2N − 1 degree chain and then checked against the window, so the
registered counts are LOWER BOUNDS for the exact per-window assignment,
and the generators are registered within 0.05 cents).**
- **P-S1 (the staircase, playable hexanies / dekanies / tetrads and
  triads kept).** N = 11: 1/0/1, 16 triads (500.04 cents). 12: 1/0/1, 17
  (566.33). 13: 2/0/1, 16 (350.98). 14 to 16: 2/0/2, 20 to 26 (351.32).
  17 to 23: 3/0/3, 24 to 30 (351.32). 24: 3/0/5, 32 (350.76). 25: 4/0/4,
  52 (271.61). 26 to 34: 6/1/7, 39 to 43 (350.76). 35 to 36: 7/1/7, 48
  (350.76). 37 to 38: 9/0/9, 59 (116.73). 39: 7/1/8, 52 (350.76). 40:
  7/1/9, 50 (497.77). 41 to 44: 8/1/10, 73 (339.40). 45 to 48: 12/2/12,
  84 (339.40). 49 to 69: 16/2/16, 76 (497.77). 70 to 72: 20/4/20, 102
  (175.38).
- **P-S2 (no chain up to 72 notes keeps every subset).** The best keeps
  20 of 30 hexanies and 4 of 12 dekanies, at N = 70, with 102 of 114
  triads. No chain keeps a dekany before N = 26 or more than 3 hexanies
  before N = 25.
- **P-S3 (four generators own the staircase).** From N = 14 to 36 the
  neutral-third generators 351.32 and 350.76 cents win every N except 25
  (271.61). From 41 to 48 it is 339.40 cents, from 49 to 69 the fourth
  497.77 cents, from 70 the 175.38 cent generator. The miracle generator
  116.73 cents wins only N = 37 and 38 with 9 hexanies and no dekany.
- **P-S4 (the MOS-level constraint).** Among levels the best are: N = 46
  at 339.40 cents keeps 12 hexanies and no dekany (82 triads), N = 53 at
  497.77 keeps 16 hexanies and 2 dekanies (76 triads), N = 31 at 116.7
  keeps 5 hexanies, N = 68 at 193.8 keeps 8 hexanies and 1 dekany. At
  every N where the free winner is not a level, the level-only best is
  strictly below it in playable hexanies, except N = 46 and 53 where the
  free winner is itself a level.
- **P-S5 (tone error does not predict playability).** The largest error
  among tones in kept triads is 27 to 28 cents for the winners at N = 14
  to 20, 9 cents at 21 to 39, and 4 to 5 cents from N = 40, while the
  playable count climbs from 2 to 20 hexanies. A chain can keep three
  hexanies with tones 28 cents off their degrees, because the kept
  triads sit on degrees that share the error.

**Deliverables.** `subfit001.py` and `tests/test_subfit001.py` green
before the first run, receipts `results/subfit001.jsonl` and
`results/subfit001_summary.json`, Scala exports under
`results/scl/subfit001/` for the winners at N = 26 (350.76), 45 (339.40),
49 (497.77) and 70 (175.38), and the N = 46 and 53 levels, offered for
listening. A gate.

## 2026-10-14 — SUBFIT-001 results + verdicts

**Run:** `subfit001.py` (809 s per run with 8 workers. Receipts
`results/subfit001.jsonl`, 62 rows, and `results/subfit001_summary.json`.
Two runs bit-identical, `cmp` on both receipts and the six .scl.) Frozen
triads v1.1.0 read-only, pin verified. Lattice suite 413/413 green before
the first run (6 new tests).

**All five predictions are refuted as registered, and the cause is a
flaw in the registration, not in the runner.** The scratch assigned each
tone to its nearest degree of the whole 2N − 1 degree chain and then
asked whether that degree sat in the window. The runner assigns each
tone to its nearest degree INSIDE the window, as registered. With no
tone cap, the two differ a lot: a tone whose nearest degree lies outside
the window is given the nearest degree inside it, however far away, and
a triad whose three members land on in-window degrees that happen to
satisfy the mean condition counts as kept even when those degrees are
nowhere near the just pitches. The largest error among tones in kept
triads is 71 cents at N = 11, 52 at N = 12 and 13, 33 to 37 at N = 15 to
17, 29 at N = 20 to 23, 22 at N = 26 to 32, and falls under 10 cents only
from N = 37. So at small N the objective was counting created
coincidences in the chain, not the eikosany's subsets, and the
registered "lower bound" clause on the counts held for a bad reason.
Below N = 37 the counts are not evidence about the eikosany. From N = 37
the errors are 4 to 10 cents and the counts mean what they were meant
to mean.

- **P-S1 — REFUTED as registered.** Counts never fell below the
  registered lower bounds, as the clause allowed, but the generators and
  triad totals differ at 20 of 62 N. Winners by N: 11: 248.87 cents
  (2 hexanies, 22 triads). 12 to 14: 498.50 (3, 3, 2 hexanies). 15 to
  16: 498.04 (3). 17 to 23: 351.39 (4 then 5 hexanies). 24 to 25: 317.13
  (6 hexanies, 56 triads). 26 to 36: 350.75 (7 to 9 hexanies, 1 dekany).
  37: 350.76 (12 hexanies, 2 dekanies, 70 triads). 38 to 48: 351.44 (14
  hexanies, 2 dekanies, 88 triads). 49 to 56: 497.77 (16 hexanies, 2
  dekanies, 76 triads). 57 to 69: 316.78 (18 hexanies, 2 dekanies, 96
  triads). 70 to 72: 175.38 (20 hexanies, 4 dekanies, 102 triads).
- **P-S2 — REFUTED as registered on the small-N clause.** The best chain
  is at N = 70 with 20 hexanies, 4 dekanies and 102 triads, as registered,
  and no chain keeps every subset. The first dekany arrives at N = 26, as
  registered. "No more than 3 hexanies before N = 25" fails: 4 at N = 17
  to 19 and 5 at 20 to 23, with tones up to 34 cents off. See the flaw
  above.
- **P-S3 — REFUTED as registered.** The neutral-third generators own
  N = 17 to 23 and 26 to 48, with 498.5 and 498.0 cents (a fourth) at 12
  to 16 and 317.13 at 24 to 25 instead. The miracle generator wins at no
  N: the exact assignment gives 351.444 cents 14 hexanies at N = 37 to
  48 where the scratch had 9 for miracle at 37 to 38.
- **P-S4 — REFUTED as registered.** The level-only winners differ: N = 46
  keeps 12 hexanies and 2 dekanies at 443.13 cents (the scratch had
  339.40 with none), N = 53 keeps 16 and 2 at 497.77 as registered, N = 41
  is a level of 351.44 with 14 hexanies and 2 dekanies, N = 72 keeps 20
  hexanies and 4 dekanies at 483.28 as a level (100 triads), N = 67
  keeps 14 and 2 at 483.28. The free winner is a level at N = 12, 17, 41
  and 53, not at 46. The clause "level-only strictly below free in
  hexanies" fails at N = 11, 14 and others where both are small.
- **P-S5 — REFUTED as registered.** The error bands were an artefact of
  the scratch's assignment. The exact figures are above.

**Measured, not registered (post-hoc lenses, labelled).** (1) From N = 37
on, where the kept triads sit within 10 cents of the just pitches, the
staircase reads: 14 hexanies and 2 dekanies at 38 to 48 notes under the
neutral third 351.444 cents (a level at N = 41), 16 and 2 at 49 to 56
under the fourth 497.774 (a level at N = 53, kernel 131072/130977 and
41503/41472), 18 and 2 at 57 to 69 under 316.778 (kernel 4375/4374 and
160083/160000), 20 and 4 at 70 to 72 under 175.378 (kernel 2401/2400 and
131072/130977), and 20 and 4 as a 72-note level under 483.28 cents. (2)
The 41-note level of 351.444 cents and the 53-note level of 497.774 cents
are the two MOS the design can use today for the eikosany: 14 of 30
hexanies with 2 of 12 dekanies, and 16 with 2, every kept tone within
9.5 and 4.2 cents. (3) The follow-up, SUBFIT-002, puts a per-tone cap in
the predicate (a triad counts only when all three tones sit within the
cap of their just pitch, 20 cents as CPSFIT-003 and 10 cents as a
stricter tier) and re-registers from a capped scratch. (4) Of the six
Scala exports, the three at N = 49, 53 and 70 are worth hearing. The N = 26
and 45 chains carry 22 and 9.5 cent errors and the N = 46 level is the
443 cent one.

**Kept.** Runner and receipts stand as the measurement of the registered
(flawed) objective. Gate G-036.

**Run receipt:** 2026-10-14, python3.12 — lattice suite 413/413 OK (6 new:
test_subfit001), freeze check A OK (scorer 1a840af9…b592). Both receipts and
the six .scl bit-identical across two runs (`cmp`), 809 s each with 8
workers.

## 2026-10-14 — SUBFIT-002 pre-registration (entry BEFORE any implementation or run)

**Question.** SUBFIT-001 scored a chain by the eikosany subsets it keeps
playable and dropped the per-tone cap. Its runner then counted chain
coincidences below 37 notes, because three in-window degrees that
satisfy the mean condition counted as a kept triad however far they sat
from the just pitches. This experiment puts the cap back into the
predicate and re-measures the same staircase at two tiers, 20 cents (the
CPSFIT-003 cap) and 10 cents (a stricter tier), on the same search.
Marcus's gate G-036 asks which cap defines "the subset is still there".
Both are reported so the gate can choose.

**Construction.** Everything as SUBFIT-001 (the eikosany on 1·3·5·7·9·11,
its 114 exact triads and 72 census subsets, N from 11 to 72, a 0.1 cent
grid of g with a 0.002 cent refinement of the twelve best, every window,
tones to the nearest in-window degree, the MOS-only variant on the exact
level intervals) with one change to the predicate: a triad survives only
when its three tones each sit within CAP cents of their just pitch at
the assigned degree AND the mirror condition holds (|dev| < 2 cents,
separation ≥ 2 cents). A subset is playable when every one of its exact
triads survives. The objective and tie-breaks are SUBFIT-001's. The
runner is `subfit002.py`, which reuses SUBFIT-001's objects and search
and parametrizes the predicate by the cap. The scratch that produced the
predictions ran the same search with the same predicate, so the
registered values are exact to the counts and to 0.01 cents on g.

**Predictions (scratch 2026-10-14, `subfit2_sweep.py` on the SUBFIT-001
search).** Rows give N: generator (cents), playable hexanies / dekanies /
tetrads, triads kept, largest error among tones in kept triads.
- **P-T20 (cap 20).** 11 to 12: 124.23, 1/0/0, 10 to 12, 16.2. 13: 350.98,
  1/0/1, 8, 8.1. 14 to 15: 351.32, 1/0/2, 12 to 18, 9.1. 16: 351.32,
  2/0/2, 21, 9.1. 17 to 21: 351.32, 3/0/3, 24, 9.1. 22 to 23: 317.13,
  4/0/5, 50, 18.1. 24 to 25: 317.13, 6/0/6, 56, 18.1. 26 to 29: 350.75,
  6/1/7, 43, 19.2. 30 to 31: 350.75, 6/1/7, 47, 19.2. 32: 350.75, 6/1/7,
  55. 33: 350.75, 7/1/8, 56. 34: 350.75, 8/1/8, 61. 35 to 36: 350.75,
  9/1/9, 66, 19.2. 37: 350.76, 12/2/12, 70, 10.3. 38 to 48: 351.44,
  14/2/14, 88, 9.5. 49 to 56: 497.77, 16/2/16, 76, 4.2. 57 to 69: 316.78,
  18/2/18, 96, 8.7. 70 to 72: 175.38, 20/4/20, 102, 4.6.
- **P-T10 (cap 10).** 11 to 12: 175.49, 0/0/1, 10, 8.1. 13: 350.98,
  1/0/1, 8. 14 to 15: 351.32, 1/0/2, 12 to 18, 9.1. 16: 351.32, 2/0/2,
  21. 17 to 21: 351.32, 3/0/3, 24, 9.1. 22 to 23: 351.32, 3/0/3, 25.
  24 to 25: 350.76, 3/0/5, 32, 8.3. 26 to 29: 350.76, 6/1/7, 39, 8.3.
  30 to 31: 350.76, 6/1/7, 42, 9.4. 32: 350.76, 6/1/7, 49, 9.9. 33 to 34:
  350.76, 7/1/8, 52, 9.9. 35 to 36: 350.76, 8/1/8, 58, 9.9. 37: 351.44,
  10/1/12, 80, 9.5. 38 to 72: identical to cap 20.
- **P-T-A (the caps agree where it matters).** From N = 38 to 72 the two
  caps give the same generator, mode, counts and triads at every N. They
  differ at N = 37 (cap 20 keeps 12 hexanies and 2 dekanies at 350.76,
  cap 10 keeps 10 and 1 at 351.44) and below.
- **P-T-B (the shape).** Under both caps the first dekany arrives at
  N = 26, the best chain is N = 70 with 20 hexanies, 4 dekanies and 102
  triads, and no chain keeps every subset. Under cap 10 no chain keeps a
  hexany at N = 11 or 12 and none keeps more than 3 before N = 26.
- **P-T-C (levels).** The free winner is a level at N = 17, 41 and 53
  under cap 20 and at N = 17, 24, 41 and 53 under cap 10. The level-only
  best keeps 14 hexanies and 2 dekanies at N = 41 (351.44) and N = 58
  (351.44), 16 and 2 at N = 53 (497.77), 20 and 4 at N = 72 (483.28, 100
  triads), 12 and 2 at N = 46 and 65 (443.13), 6 hexanies at N = 31
  (116.68), under both caps.
- **P-T-D (design floors for the eikosany in one MOS).** The smallest
  level that keeps at least 14 hexanies is N = 41, at least 16 is N = 53,
  at least 20 is N = 72, with every kept tone within 9.5, 4.2 and 8.0
  cents, under both caps.

**Deliverables.** `subfit002.py` and `tests/test_subfit002.py` green
before the first run, receipts `results/subfit002.jsonl` (one row per
cap and N) and `results/subfit002_summary.json`, Scala exports under
`results/scl/subfit002/` for the N = 41 and N = 72 levels and the N = 37
cap-20 chain. The N = 49, 53 and 70 chains are already in the Wilsonic
library from SUBFIT-001. A gate.

## 2026-10-14 — SUBFIT-002 results + verdicts

**Run:** `subfit002.py` (about 8200 s for the first run and 7200 s for the second with 8 workers over 124 (cap, N) tasks, against 809 s for SUBFIT-001's single cap; the machine was shared with other work and I did not profile it.
Receipts `results/subfit002.jsonl`, 124 rows, and
`results/subfit002_summary.json`. Two runs bit-identical, `cmp` on both
receipts and the three .scl.) Frozen triads v1.1.0 read-only, pin
verified. Lattice suite 422/422 green before the first run (9 new tests).

**All six predictions KEPT.** The runner is the scratch's search with the
scratch's predicate, so this is a reproduction and not a surprise. The
value of the run is the receipts and the structure of each winner, which
the scratch did not compute.

- **P-T20 — KEPT.** Every N from 11 to 72 matches the registered
  generator within 0.01 cents, the registered counts exactly, and the
  registered triads and errors.
- **P-T10 — KEPT.** Same, and from N = 38 the rows equal the cap-20 rows.
- **P-T-A — KEPT.** The two caps agree at every N from 38 to 72 and
  differ at 37.
- **P-T-B — KEPT.** First dekany at N = 26 under both caps, best chain
  N = 70 (20 hexanies, 4 dekanies, 102 triads) under both, no chain keeps
  every subset, no hexany at N = 11 or 12 under cap 10 and none keeps
  more than 3 before N = 26.
- **P-T-C — KEPT.** Free winner is a level at N = 17, 41, 53 (cap 20) and
  17, 24, 41, 53 (cap 10). Level-only values as registered at N = 31, 41,
  46, 53, 58, 65, 72.
- **P-T-D — KEPT.** The smallest level with at least 14, 16, 20 hexanies
  is N = 41, 53, 72, within 9.5, 4.2, 8.0 cents, under both caps.

**Measured, not registered (post-hoc lenses, labelled).** (1) The cap
decides nothing above 37 notes. Below it, the cap-20 staircase keeps 4
to 9 hexanies at N = 22 to 36 with tones 18 to 19 cents off, and cap 10
keeps 3 to 8 with tones within 10. Whether an 18-cent tone "is" the
eikosany tone is the ear question of G-036, and the two tables give the
gate both answers. (2) Structure of the winners, from the runner's
11-limit val solve on the assignment. This is the finding the scratch
could not see: the neutral-third winner 351.444 at N = 38 to 48, and so
the 41-note and 58-note levels, is NOT a homomorphic image of the
11-limit lattice. No integer val maps the eikosany's monzos to the
assigned degrees, so the 14 hexanies and 2 dekanies are kept by an
assignment that is not a temperament: the same just interval lands on
different step counts in different places of the chain. The cap-20
free winners that ARE homomorphic: N = 24 to 25 (317.126, 6 hexanies,
tones 18 cents off), N = 37 (350.756, 12 hexanies and 2 dekanies, val
(2, -16, 13, 5) on primes 3, 5, 7, 11, kernel 32805/32768 and
19712/19683), N = 49 to 56 (497.774, val (-1, 8, 14, -23), kernel
131072/130977 and 41503/41472), N = 57 to 69 (316.778, val (6, 5, 22,
-21), kernel 4375/4374 and 160083/160000), N = 70 to 72 (175.378, val
(4, -32, -15, 10), kernel 2401/2400 and 131072/130977). Among the
level-only winners the homomorphic ones with six or more hexanies are
N = 46 and 65 (443.128, val (7, 9, 13, -15), kernel 4375/4374 and
8019/8000, 12 hexanies and 2 dekanies within 8.3 cents), N = 53
(497.774, 16 and 2), N = 63 (38.31, 12 and 0, 86 triads within 5.8) and
N = 72 (483.278, val (-6, -29, 2, 21), kernel 3025/3024 and
420175/419904, 20 and 4, 100 triads within 8.0). The 31-note 116.68
level (6 hexanies) and the 41- and 58-note 351.444 levels are not
homomorphic. So if the design requires one val (a Gral keyboard where
every just interval is one fixed step vector), the eikosany's MOS
floors move to 46 notes for 12 hexanies, 53 for 16 and 72 for 20, and
the 41-note level drops out. Same under cap 10. (3) The three new .scl: the 41-note level (14 hexanies, 2 dekanies,
within 9.5 cents), the 72-note level (20 and 4, 100 triads, within 8.0),
and the 37-note cap-20 chain of 350.756 (12 and 2, within 10.3), which
is the smallest chain that keeps twelve hexanies.

**Kept.** Gate G-037.

## 2026-10-14 — GOLD-003 pre-registration (entry BEFORE any implementation or run)

**Principle this experiment serves (Marcus, 2026-10-14).** Nobility does
not predict harmony, because there is no mechanism for it. Harmony is a
Diophantine condition between k·g and log2 of the primes. Nobility is a
condition on g's own continued fraction. The two are independent. So the
statement "Erv's optimum is under a cent from a golden generator" is not
the statement to test, because nobles of complexity 60 are about one
cent apart and every generator is near one. The statement to test is:
a triad-optimal generator is a survival SEGMENT (the interval of g over
which the count-optimal triads all stay within tolerance, CPSFIT-003's
`segment_cents`), harmony cannot choose inside the segment, and a noble
inside the segment is a free melodic upgrade (L/s → φ at every level,
the Fibonacci ladder of MOS sizes, Gral cells of constant shape). The
question is whether the segments contain nobles more often than chance.

**Arm A (this registration): segments against randomly placed segments.**
Objects: the 22 distinct count-optimal segments of CPSFIT-003 (115 rows
on hexany, EG4, dek52, dek52refl, dek53 for N = 11 to 36. A segment is
distinct by its rounded end points, so the reflected dekany and the
shared dek53 segments count once), widths 0.02 to 0.43 cents, and the
15 segments that remain when overlapping intervals are merged across
lattices (the hexany and EG4 segments at 317 cents become one). Nobles:
`gold002.nobles(m, 60)` for golden (m = 1) and silver (m = 2), folded to
(0, 600] cents, complexity ladder Q = 8, 12, 20, 30, 60. Statistic: the
number of segments that contain at least one noble of complexity ≤ Q.
Null: 20000 draws (seed 20261014) in which every segment keeps its width
and is placed uniformly on (0, 600). The p-value is the fraction of draws with at
least the observed count. Decision rule, fixed now: ten tests per
segment set (two families × five Q), so a result counts as a signal
only at p ≤ 0.005. Between 0.005 and 0.05 it is a hint. Above 0.05 it is
nothing.

**Predictions (scratch 2026-10-14, `gold3_sweep.py`).**
- **P-G3-1 (distinct segments, golden).** Contained counts by Q = 8, 12,
  20, 30, 60: 1, 3, 3, 4, 7 of 22, null means 0.12, 0.24, 0.68, 1.47,
  5.12, p = 0.11, 0.0012, 0.028, 0.054, 0.22. Only Q = 12 is a signal.
- **P-G3-2 (distinct segments, silver).** 1, 1, 3, 3, 14 of 22, null
  means 0.17, 0.37, 1.02, 2.17, 6.90, p = 0.16, 0.31, 0.077, 0.37,
  0.0007. Only Q = 60 is a signal, and at Q = 60 the silver set is 1653
  nobles about 0.36 cents apart, so this is the density regime and not
  evidence about low-complexity nobles.
- **P-G3-3 (merged segments).** Golden: 1, 2, 2, 3, 6 of 15, p = 0.075,
  0.0095, 0.070, 0.068, 0.090. Silver: 1, 1, 3, 3, 9 of 15, p = 0.11,
  0.22, 0.024, 0.16, 0.011. No test reaches 0.005. The golden Q = 12
  result falls from a signal to a hint when the 317-cent coincidence is
  counted once.
- **P-G3-4 (which nobles).** The golden nobles of complexity ≤ 12 that
  sit inside a segment are exactly two: 317.170 cents (3/11, 1/4,
  complexity 11), inside the hexany N = 12 to 15 and EG4 N = 15 segments
  (Erv's generator, the hexany count optimum), and 503.786 cents (2/3,
  1/2, complexity 3) inside the dekany N = 15 to 17 segment. The silver
  nobles of complexity ≤ 20 inside a segment are 351.472 (0/1, 1/1,
  complexity 1) in the dekany N = 33 to 34 segment, 316.827 (4/15, 5/19)
  in the dekany N = 35 to 36 segment and 77.850 (1/13, 0/1) in the
  hexany N = 18 to 21 segment.
- **P-G3-5 (the verdict I expect).** Arm A gives at most a hint: a
  Bonferroni-level signal on the distinct-segment set at golden Q = 12
  that does not survive merging. This is consistent with the principle
  and is not evidence that nobility predicts harmony. It says two of
  Erv's shallow goldens sit inside count-optimal segments, which is what
  "chosen inside the segment" predicts for a small catalogue and what
  "near a golden" cannot distinguish.

**Arm B (defined now, predictions deferred).** Treatment: the nobles Erv
ear-marked on his scale-tree sheets (the 1994 Peirce-sequence page
Marcus shared, plus the fuller page where every Farey delta carries its
golden limit, not yet located). Control: the un-marked nobles of the
same complexity on the same sheets. Statistic: the fraction of each set
whose value lies inside any count-optimal segment (CPSFIT-003's, plus
the eikosany subset winners of SUBFIT-002 once their segments are
measured). Exact test on the two fractions. Arm B is registered when the
marked set is transcribed. I will write its predictions before that
transcription is scored.

**Deliverables.** `gold003.py` and `tests/test_gold003.py` green before
the first run, receipts `results/gold003.jsonl` (one row per segment set,
family and Q) and `results/gold003_summary.json`. No new scales. A gate.

## 2026-10-14 — GOLD-003 results + verdicts (arm A)

**Run:** `gold003.py` (under a minute per run. Receipts `results/gold003.jsonl`, 20 rows,
and `results/gold003_summary.json`. Two runs bit-identical, `cmp` on both.)
Inputs read-only: `results/cpsfit003.jsonl` and `gold002.nobles`. Lattice
suite 429/429 green before the first run (7 new tests).

**All five predictions KEPT.** The measured table, distinct segments
(22): golden contained 1, 3, 3, 4, 7 at Q = 8, 12, 20, 30, 60 with
p = 0.109, 0.0020, 0.027, 0.052, 0.223. Silver 1, 1, 3, 3, 14 with
p = 0.16, 0.31, 0.073, 0.37, 0.0006. Merged segments (15): golden 1, 2,
2, 3, 6 with p = 0.073, 0.012, 0.073, 0.065, 0.086. Silver 1, 1, 3, 3, 9
with p = 0.107, 0.21, 0.024, 0.16, 0.0084. Signals at the registered
0.005 level: distinct golden Q = 12 and distinct silver Q = 60 only.
Merged golden Q = 12 is a hint. The contained goldens at Q = 12 are
317.170 (3/11, 1/4) and 503.786 (2/3, 1/2), as registered.

**Reading, under the principle.** Arm A is a hint and no more. Two of
the shallow goldens sit inside count-optimal segments, and that is
consistent with "chosen inside the segment" for a small catalogue. It
is not evidence that nobility predicts harmony, and the registration
said in advance that it could not be. The silver Q = 60 signal is the
density regime (1653 nobles about 0.36 cents apart against segments up
to 0.43 cents wide) and I do not read it. The test that can decide
something is arm B, Erv's ear-marked nobles against the un-marked nobles
of the same complexity, and that waits on the sheets.

**Measured, not registered (post-hoc, labelled).** (1) The two Q = 12
containments are the two segments with the widest margins in the whole
CPSFIT-003 table, 0.43 and 0.16 cents, and a wide segment is more likely
to contain anything. A width-matched null is the same null, so this
does not change the p-values, but it says the hint rests on the two
easiest segments. (2) The 351.472-cent silver of complexity 1, which is
the pure silver generator (1 + √2 folded), sits inside the dekany
N = 33 to 34 segment. That is one silver coincidence at the lowest
possible complexity, on one lattice, and I note it without reading it.

**Kept.** Gate G-038.

## 2026-10-17 — Note: Erv's 1994 "Scale-Tree (Peirce Sequence)" top sheet reproduced from the Stern-Brocot tree

Not an experiment. A check of the noble enumeration against Erv's hand,
before Fork B's first registration. The bottom row of the top sheet
(32 decimals, transcribed from the scan Marcus shared 2026-10-14) is
reproduced 32 of 32 to ten decimals by one rule: build the tree to depth
5 from 0/1 and 1/0, and for each leaf interval a/b .. c/d write the
golden limit (a + φc)/(b + φd), with the roles of the two ends swapped on
the right-hand side of each parent. Examples: 0.2763932023 is
(1 + 2φ)/(4 + 7φ) for the interval 1/4 .. 2/7, 0.4198212717 is
(2 + 3φ)/(5 + 7φ) for 2/5 .. 3/7, 0.6180339887 is (3 + 5φ)/(5 + 8φ) for
3/5 .. 5/8. So the sheet is the complexity-8 golden catalogue, laid out
by Farey interval, and `gold002.nobles` agrees with it entry for entry.
This is the vocabulary the scale-tree search will use: a golden generator
is a leaf interval and an alternating path, not a decimal.

## 2026-10-17 — DYNMOS-001 pre-registration (entry BEFORE any implementation or run)

**Fork B, first experiment.** Marcus chose the dynamic MOS as the road
less traveled (2026-10-16): one generator stays fixed, and the MOS level
and the murchana change to fit the Euler-genus subset the player has
selected. The design unit is the subset, and the structure is any
Euler genus, with no theory of seeds required. This experiment measures,
for a fixed list of generators and two seed sets, the smallest MOS level
of each generator that keeps each subset playable, which window does it,
and what a move between two dekanies costs.

**Objects.** Two seed sets. The canonical eikosany 1·3·5·7·9·11 (20
tones, 114 exact triads) and Marcus's 1·45·135·225·19·377 (20 distinct
pitch classes, 30 exact triads, steps down to 8.9 cents). For each, the
SUBSET-MEL-000 census of 72 subsets (30 hexanies, 6 + 6 dekanies, 15 + 15
tetrads) with the exact proportional and subcontrary triads of each
subset's own tones (`cpsfit001.exact_triads`, `cpsfit002.prep_triads`).
A subset with zero exact triads is VACUOUS: it has no harmonic
constraint, it is excluded from every coverage count, and it is reported
on its own. On the canonical set no subset is vacuous. On Marcus's set 24
are: 12 hexanies and 6 + 6 tetrads. Summed over subsets, the canonical
set has 684 subset-triad incidences and Marcus's has 228.

**Generators (fixed list, cents).** Marcus's two favourites, both Erv
recurrences: 285.823 (0.238186, H[n−1] + 2H[n−3]) and 502.722 (0.418935,
H[n−1] + 32H[n−4]). Two shallow goldens: 503.786 (2/3, 1/2) and 317.170
(3/11, 1/4). Six SUBFIT-002 winners: 351.444, 497.774, 443.128, 483.278,
175.378, 316.778. Two controls: 116.676 (miracle) and 193.908 (the
hexany count optimum). Note that 316.778 and 317.170 are 0.39 cents
apart and give almost the same results.

**Predicate (the plugin-shaped candidate).** For a generator g, the MOS
levels are the Farey levels of g/1200 up to 72 notes, at least 5 notes
(`gold002.levels_of`). For a level N and a window of N consecutive chain
degrees, each subset tone goes to its nearest degree inside the window.
The window keeps the subset when every tone is within 20 cents of its
degree and every exact triad of the subset survives the mirror predicate
(deviation under 2 cents, separation at least 2 cents) at the assigned
pitches. The subset's level N* is the smallest level with a keeping
window. The window is the one with the smallest largest tone error, then
the smaller mode number. The referee is the same search over every N
from 5 to 72, not only levels.

**Transition cost.** For every pair of dekanies that both have a level
N*, the common tones are counted, and a common tone is KEPT when both
windows give it the same chain degree k and RETUNED otherwise. A pair
with no common tones is a contrast pair. A pair with common tones is an
affinity pair. The level change is |N*a − N*b|.

**Predictions (scratch 2026-10-17, `dynmos_sweep.py`, same predicate).**
- **P-D1 (Marcus's generators).** 285.823 keeps no subset of either
  structure at any N up to 72. 502.722 keeps no subset of the canonical
  set at any level (one hexany at a non-level N), and on Marcus's set it
  keeps 4 of the 18 non-vacuous hexanies, all at N = 43, and no dekany.
- **P-D2 (canonical coverage at levels).** Hexanies / dekanies / tetrads
  kept, and subset-triad incidences kept of 684: 503.786: 2 / 0 / 2 / 12.
  317.170: 8 / 0 / 10 / 120. 351.444: 14 / 2 / 14 / 292, every kept tone
  within 9.5 cents. 497.774: 16 / 2 / 16 / 220, within 4.2. 443.128: 12 /
  2 / 12 / 222. 483.278: 20 / 4 / 20 / 310. 175.378: 12 / 0 / 22 / 220.
  316.778: 18 / 2 / 19 / 311. 116.676: 12 / 0 / 15 / 123. 193.908: 12 / 2 /
  15 / 279.
- **P-D3 (how small a level a subset needs, canonical).** The smallest
  level that keeps any hexany is 17 (351.444) and the smallest that keeps
  any dekany is 41 (351.444 and 497.774). Hexany N* multisets: 351.444
  {17 ×3, 24 ×3, 41 ×8}. 497.774 {29 ×6, 41 ×6, 53 ×4}. 316.778 {19, 34 ×6,
  53 ×11}. 443.128 {19 ×2, 27, 46 ×9}. 483.278 {32, 37, 42 ×5, 52 ×3, 57 ×6,
  62 ×2, 67 ×2}. 116.676 {31 ×9, 41 ×3}. Dekany N*: 351.444 {41, 41},
  497.774 {41, 41}, 443.128 {46, 46}, 316.778 {53, 53}, 483.278 {62, 62,
  67, 67}, 193.908 {68, 68}.
- **P-D4 (Marcus's set at levels, with denominators 18 hexanies, 12 dekanies,
  18 tetrads, 228 incidences).** 316.778: 14 / 7 / 18 / 193. 317.170: 14 /
  6 / 18 / 178. 193.908: 15 / 6 / 17 / 179. 443.128: 12 / 6 / 15 / 171.
  483.278: 16 / 5 / 17 / 169. 351.444: 12 / 4 / 17 / 149. 116.676: 12 / 5 /
  12 / 75. 175.378: 6 / 2 / 16 / 76. 497.774: 7 / 2 / 11 / 55. 503.786: 6 /
  4 / 6 / 30. The smallest level that keeps a dekany of this set is 15
  (316.778), and hexanies are kept at 11 (316.778 and 317.170).
- **P-D5 (transitions).** Canonical: only 483.278 has affinity pairs, 4 of
  them at levels 62 and 67, with 0 of 20 common tones retuned. 351.444,
  497.774, 443.128, 316.778 and 193.908 keep exactly 2 dekanies each,
  which form 1 contrast pair and no affinity pair. Marcus's set: 316.778
  has 18 affinity pairs with 36 of 90 common tones retuned and 3 contrast
  pairs. 317.170: 12 pairs, 20 of 60. 443.128: 12 pairs, 25 of 60.
  193.908: 12 pairs, 21 of 60. 483.278: 8 pairs, 11 of 40. 116.676: 8
  pairs, 9 of 40. 351.444: 4 pairs, 9 of 20. 503.786: 4 pairs, 3 of 20.
- **P-D6 (what the level restriction costs).** On the canonical set the
  referee keeps the same hexany count as the levels for 497.774, 443.128,
  483.278, 316.778, 116.676, 193.908 and 285.823, and more for 502.722 (1
  vs 0), 503.786 (4 vs 2), 317.170 (12 vs 8), 351.444 (16 vs 14) and
  175.378 (22 vs 12, and 4 dekanies vs 0).

**What this already says, before the run.** Fork B makes a hexany of the
canonical eikosany playable in 17 to 34 notes where Fork A needed 41 to
72, and a dekany in 41. On Marcus's set the just structure itself has
only 30 exact triads and 12 of its 30 hexanies have none. So the triad
proxy has nothing to say about those 12, and the contrast Marcus hears
in that set is at least partly something the proxy does not measure.
That is the incompleteness case he predicted, stated as a count.

**Deliverables.** `dynmos001.py` and `tests/test_dynmos001.py` green
before the first run, receipts `results/dynmos001.jsonl` (one row per
generator and seed set) and `results/dynmos001_summary.json`, Scala
exports under `results/scl/dynmos001/`: the 17-note level of 351.444 with
its canonical hexany, the 29-note level of 497.774 with its hexany, and
the 15-note level of 316.778 with Marcus's dekany. A gate.

## 2026-10-17 — DYNMOS-001 results + verdicts

**Run:** `dynmos001.py` v1.0.1 (about ten seconds per run with 8 workers
over 24 generator × seed-set tasks. Receipts `results/dynmos001.jsonl`,
24 rows, and `results/dynmos001_summary.json`. Two runs bit-identical,
`cmp` on both receipts and the three .scl.) Lattice suite 438/438 green
before the first run (9 new tests). Version 1.0.1 fixed a verdict
bookkeeping slip: P-D3 and P-D4 compared a registered generator set with
a sorted measured tuple in registration order. No prediction or
measurement changed. Both runs were repeated after the fix.

**All six predictions KEPT.** As a reproduction of the scratch this was
expected. The content is in the tables, which are the first numbers for
Fork B.

- **P-D1 — KEPT.** 285.823 keeps nothing at any N on either set. 502.722
  keeps nothing of the canonical set at a level and 4 of 18 non-vacuous
  hexanies of Marcus's set, all at 43 notes, no dekany.
- **P-D2 — KEPT.** Canonical coverage at levels as registered.
- **P-D3 — KEPT.** A canonical hexany is first playable at 17 notes
  (351.444) and a canonical dekany at 41 (351.444 and 497.774). The level
  multisets match.
- **P-D4 — KEPT.** Marcus's set: 24 vacuous subsets, 30 exact triads,
  coverage as registered, a dekany at 15 notes (316.778) and hexanies at
  11 (316.778 and 317.170).
- **P-D5 — KEPT.** Transition tables as registered.
- **P-D6 — KEPT.** The level restriction costs nothing in hexanies for
  seven of the twelve generators on the canonical set and costs 175.378
  the most (12 vs 22 hexanies, 0 vs 4 dekanies).

**What Fork B buys, in numbers (canonical eikosany).** Fork A needed 41
notes for the first MOS that keeps 14 hexanies and 2 dekanies, and 72
for 20 and 4. Under Fork B the same generators keep individual hexanies
in 17 to 34 notes: 351.444 keeps three at 17 and three at 24, 497.774
keeps six at 29, 316.778 keeps one at 19 and six at 34, 443.128 keeps
two at 19. Dekanies still need 41 to 68 notes, because a dekany carries
18 to 41 exact triads and the chain has to hold them all at once. So the
dynamic MOS halves the melodic scale for a hexany and does nothing for a
dekany. The transition tables say why contrast is cheap and affinity is
not yet measured on the canonical set: each generator keeps exactly two
dekanies and they are complements, so there is one contrast pair and no
affinity pair, except 483.278, which keeps four dekanies at 62 and 67
notes with every common tone kept at the same degree.

**Measured, not registered (post-hoc lenses, labelled).** (1) A retuned
common tone means the two windows gave the same just tone two different
chain degrees, which is the per-subset version of the non-homomorphic
finding of SUBFIT-002. On the canonical set 483.278 retunes nothing,
which is consistent with its single val. On Marcus's set 316.778 retunes
36 of 90 common tones across its 18 affinity pairs, so a player moving
between those dekanies would hear 40 percent of the shared tones move.
(2) Marcus's set is the incompleteness case stated as a count: 30 exact
triads in the whole genus against 114, 12 of 30 hexanies with none, and
steps of 8.9 and 12.3 cents between tones in the 3·5 cluster. The proxy
is silent on 24 of its 72 subsets. The set's high coverage numbers
(316.778 keeps 14 of 18 hexanies and 7 of 12 dekanies) are coverage of
a smaller harmonic demand, and the ear gate decides what the near-unison
pairs are doing. (3) 316.778 and 317.170 are 0.39 cents apart and give
the same coverage to within one hexany, so the Erv golden is a free
choice inside that generator's segment here too. (4) Marcus's two
favourite generators do not fit either structure under this proxy. Both
are Erv recurrences chosen for other scales and other reasons, and the
right reading is that the proxy does not see what he hears in them,
which is the charter's case, and not that the generators are wrong.

**Kept.** Gate G-039.

## 2026-10-23 — G-031 decided on the Ear Bench (first gate judged there)

**What was compared.** CPSFIT-002's triad-minimax chain (A: 193.908¢, N = 22,
all 12 hexany triads within 2¢, worst 1.16¢, one tone 2.22¢ off with 1/1
pinned) against CPSFIT-001's tone-minimax chain (B: 193.787¢, N = 22, 10 of
12 within 2¢, worst 2.08¢ on 4:5:6 and 10:12:15, every tone within 1.37¢).
Same val and the same step pattern from 1/1 (LsssLsssLsssLssLssLsss); the
steps differ by at most 2.4¢, and B's large and small steps are a little
more even (2.20 against 2.30).

**How.** Ear Bench v1.2.0, local copy, reed timbre, nonlinearity off,
1/1 = 261.6256 Hz. Four passages composed from the hexany's triads, each
played as X then Y with the order hidden and drawn per page load:

| Passage | Tests | Preferred |
|---|---|---|
| Scale run | melody | B (tone fit) |
| Tune | melody shaped by the harmony | A (triad fit) |
| Chorale (all 12 triads, common-tone voice leading, bass) | harmony | A (triad fit) |
| Tune over chorale | both | B (tone fit) |

Verdict: **Pass.** Marcus: "I hear a lot of good triads in both. the
biggest differences to me are how good the melody is." His earlier sighted
note (2026-10-22, arpeggios only) said B was clearly the more melodic and
that an arpeggio cannot answer a harmonic question, which is why the
passages were built.

**Reading, with its limits.** Each passage is one blind binary trial, so
the four picks are not a statistic. What they do say: in harmony alone the
ear went with the chain that holds all twelve triads, which is what the
worst-triad objective was built to buy, and in Marcus's words the triads
are good in both and the melody is where they differ. So the gate's
question ("the worst triad or the number of good ones?") has no audible
answer at this level of fit, 10 against 12 triads within 2¢, and the
deciding axis is melodic. That supports the joint melody-and-harmony
objective Marcus asked for on 2026-10-22: a fitter that already keeps the
triads should break ties on a melodic measure (the frozen melodic.py
v0.1.0 is one candidate) rather than on a finer triad bound. Not
registered as a prediction; it is the brief for whichever fit experiment
comes next.

**Kept.** Judgments (8 records, including the cleared-then-restored Pass
from the bench's save bug on 2026-10-22) in
`experiments/ear_bench/judgments/marcus-w-hobbs.jsonl`. Gate G-031 PASS.

## 2026-10-24 — G-032 decided on the Ear Bench; timbre becomes a judged factor

**What was compared (N = 16, both on the miracle val).** CPSFIT-003's count
chain (A: 116.676¢, 10 of the hexany's 12 triads within 2¢, one tone 5.22¢
out) against CPSFIT-002's worst-triad chain (B: 116.588¢, 6 of 12, worst
tone 4.86¢). The worst-triad chains at N = 16 and 18 had never been
exported; `cpsfit002_audition.py` wrote them from the recorded rows on
2026-10-23 without re-running anything. The N = 18 comparison (count
77.818¢ against worst-triad 116.588¢) is on the bench and not yet judged.

**How.** Ear Bench v1.2.0, local copy, 1/1 = 261.6256 Hz, blind X/Y:

| Passage | Timbre | Preferred |
|---|---|---|
| Scale run | reed | A (count) |
| Tune | electric piano | B (worst triad) |
| Chorale | electric piano | A (count) |
| Tune over chorale | electric piano | A (count) |

Verdict: **Pass**, set under the electric piano. Marcus: "the timbre is
very important. I prefer the electric piano timbre, but I could easily
score differently with a different timbre such as reed."

**Reading, with its limits.** One blind trial per passage, and the picks
were made under two timbres, so the four are not one condition. In the
harmonic passages (chorale, tune over chorale) the ear went with the chain
that keeps ten triads and pays for it with one tone 5¢ out, which answers
the gate's question for this pair and leaves the count objective as the
default. The tune went the other way, as in G-031 where the melodic
passages split, so melody keeps acting as the axis that the triad
objectives do not see.

**Post-hoc observation (not registered): why timbre should move the
verdict.** The two timbres expose mistuning differently. The reed is 16
sustained harmonics at 1/n, so a 2¢ triad error shows up as beating among
many coinciding upper partials. The electric piano is mostly harmonics 1
to 4 with a fast-decaying tine at 7 and 11, so after the attack there are
few coinciding partials left to beat, and small triad errors are much
harder to hear. That is the tuning and timbre relationship (Sethares):
the same chains are being heard through two different sieves. The
consequence for the program is that a verdict is a verdict about a chain
and a timbre together. The bench now keeps picks per timbre, with a fresh
blind draw for each, and every judgment carries its timbre, so the
dataset can show where the ear's verdict depends on the instrument. Where
it does, that is itself a design result for Wilsonic: which timbres a
fitted scale should be offered with.

**Kept.** 13 judgment records in
`experiments/ear_bench/judgments/marcus-w-hobbs.jsonl`. Gate G-032 PASS on
the listening question; the floating-origin and cap-sweep design questions
stay open.

## 2026-10-24 — G-029 decided on the Ear Bench: Erv's 15-note chain wins the harmony

**What was compared.** CPSFIT-001's two exported chains for the 1·3·5·7
hexany. A: the 15-note chain of 502.860¢, Erv's 0.418935 recurrence (a
septimal meantone), whose hexany triads sit 0.40¢ (3:4:5, 12:15:20), 4.63¢
(6:7:8, 21:24:28), 4.82¢ (2:3:4, 3:4:6), 5.13¢ (4:5:6, 10:12:15) and 7.25¢
(5:6:7, 30:35:42) from just, so 2 of 12 within 2¢, median 4.8¢. B: the
22-note chain of 193.787¢, 10 of 12 within 2¢, worst 2.08¢.

**How.** Ear Bench, local copy, electric piano (the judging standard),
one octave down (1/1 sounding at 130.81 Hz), nonlinearity off, blind X/Y:

| Passage | Preferred |
|---|---|
| Scale run | B (22-note) |
| Tune | A (Erv's 15-note) |
| Chorale | A (Erv's 15-note) |
| Tune over chorale | A (Erv's 15-note) |

Verdict: **Pass**, no notes.

**Reading, with its limits.** One blind trial per passage. The two scales
have different sizes, so the run and the tune give away which is which
(15 notes against 22); the chorale plays the same twelve chords in both and
stays blind. In that chorale the ear preferred the chain whose triads are
off by a median of 4.8¢ and up to 7.25¢ over the chain that holds them
within 2.1¢. Two conditions were in play and both matter. The electric
piano has few sustained upper partials, so small errors make little
beating (see the G-032 entry), and one octave down every beat rate halves.
Under the judging standard, then, 5 to 7¢ triad errors were not heard as
a defect, and something else about the 15-note chain won. The 2¢ LOCK
tier that CPSFIT-001 to 003 optimise is far stricter than this listening
needed. That is a measurement for EAR-ε (G-025) to make properly, and its
pre-registered prediction already expects the major third to lose its lock
somewhere between 6 and 12¢.

**Post-hoc implication (not registered).** If the ear tolerates about 5¢ on
the hexany's triads under the electric piano, the fits have been paying
notes for precision this listening does not use: the 22-note chain exists
to get under 2¢. A fit objective with a looser, ear-calibrated tolerance
would favour smaller scales, and Erv's 0.418935 at 15 notes is exactly
such a scale. This argues for running EAR-ε before the next fit
experiment, so that the tolerance the fits use is one Marcus's ear has
measured.

**Kept.** 18 judgment records. Gate G-029 PASS.

## 2026-10-24 — Note: generator-first exploration on the Ear Bench, and a single-val discrepancy at 351.444¢

**Why.** Marcus: the generator is an aesthetic choice made up front, like
the timbre, and the question is how any combination product set's triads and
melodies sit on it; the fitting results stay valuable, above all "optimise
for triads, because melody is forgiving". The Ear Bench now has a generator
explorer: a palette of 1,028 golden nobles (complexity at most 58, GOLD-002's
enumerator, `experiments/ear_bench/palette.py`), and `docs/ear-bench/
generator.js`, which places any CPS on any generator's MOS levels.

**Learnings carried into it.** Triads held rank the levels (the count
objective, G-032) and melody facts only describe them (G-031); bands at 2¢
(LOCK) and 5 and 10¢ (G-029's listening, provisional until EAR-ε); the 20¢
tone cap, with a triad counted only when its three tones are present; window
and transposition both float (G-032's open floating-origin question, taken
as yes here); a prime-based single-val flag on every placement (SUBFIT-002);
no ranking by complexity (nobility and harmony are independent).

**Cross-check.** `experiments/ear_bench/tests/generator_check.js` reproduces
every registered count it was given: CPSFIT-001 (10 and 2 of 12), CPSFIT-002
(6 and 12), CPSFIT-003 (10, 10, and 32 of 41 on the dekany), DYNMOS-001 (8),
and SUBFIT-002's hexanies kept (14, 12, 16, 20 at 41, 46, 53, 72 notes).

**Discrepancy, open.** The same placement of the canonical eikosany on the
41-note level of 351.444¢ (all 20 tones within 4.48¢, 14 hexanies kept) is a
single val: 3, 5, 7 and 11 map to 2, 25, 13 and 5 generators, with prime
errors +0.93, −0.21, −0.05 and +5.90¢, and every tone's chain position
follows from it. SUBFIT-002's post-hoc solve reported this level as not a
homomorphic image of the lattice, and G-037 asks whether the design must be
one val, which would move the floors to 46, 53 and 72 notes. Before G-037 is
decided, SUBFIT-002's val solve should be rerun against this val to find
which reading is right (a narrower mapping range in the solve is one
possible cause). Nothing registered changes here.
