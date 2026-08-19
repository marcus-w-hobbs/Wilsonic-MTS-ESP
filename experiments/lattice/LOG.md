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
