# The falsifiable loop — melody ⇄ lattice ⇄ harmony

Spec for three linked experiments: SHADOW-001, LAT-MEL-001, MOS-LAT-001.
Written 2026-07-22 (Marcus + Fable brainstorm session). This module is a
**sibling** of `experiments/triads/` — it imports the frozen scorer and
family generators read-only and MUST NOT modify `triads/scorer.py`
(v1.0.0 frozen, CI-enforced). All new scoring code (melodic axis) lives
here. Harness discipline is inherited: LOG.md entry BEFORE each run,
hypothesis → result → kept/reverted, receipts as JSON/JSONL in
`results/`, findings promoted to FINDINGS.md as dated paragraphs.

## Theoretical frame (so results stay interpretable)

Octave-equivalent JI ratios form the free abelian lattice over odd
primes (monzo space with the 2-axis quotiented out). Projection
π: lattice → ℝ/ℤ, v ↦ Σ vᵢ·log₂ pᵢ mod 1 is where melody lives.

- **Melody = rank-1-ness of the lattice region under π.** A lattice
  chunk is melodic to the degree that a single-generator chain
  approximates its projection (three-gap theorem: rank-1 ⇒ ≤3 gaps,
  MOS ⇒ 2).
- **Harmony = connectivity of the lattice region.** Short shared
  edges ⇒ coincidences ⇒ proportional/subcontrary triads (frozen
  scorer's P/S/G).
- The loop: score harmonic constructions (CPS) for melody
  (LAT-MEL-001); build lattices from melodic constructions (noble-MOS
  via recurrence/conjugate embedding) and score them for harmony
  (MOS-LAT-001); perturb the boundary between distinctness and
  degeneracy (SHADOW-001).

Known harness facts that constrain design (from triads/FINDINGS.md):

1. Anchored convention: P = S exactly for all MOS and all CPS(n, n/2)
   (inversional symmetry). So on these families the harmonic axis is
   **P itself + triad quality**, not min(P,S).
2. Per-triple ε-guard is in the frozen scorer; exact rational path
   unaffected.
3. CPS generation is float end-to-end, no normalization, no 1/1,
   never uniquifies (CPSTuningBase.cpp). Dedup/collapse measurements
   in SHADOW-001 must therefore be done in this module with an
   explicit, logged epsilon — the C++ won't do it for us.
4. Brun levels 0–9 follow scale-tree ZIGZAG (semiconvergents), not CF
   convergents (Brun.cpp:269). MOS-LAT-001 window checks must use the
   zigzag path, not the CF path.
5. Octave reduction is half-open [1,2) (Microtone.cpp:475).

---

## Melodic scorers (new code: `melodic.py`)

Three independent scores, all pure functions of a sorted pitch-class
multiset (cents in [0, 1200)), each returning a scalar plus receipts:

**M1 — gap entropy.** Sort, dedup (logged ε_dedup, default 0.01¢),
circular gaps, histogram with cluster tolerance ε_gap (default 0.5¢ to
match scorer ε). Score = Shannon entropy of gap-size distribution;
also report gap count. MOS ideal: 2 gaps, entropy ≤ log 2.

**M2 — constant-structure (CS) score.** Wilson's own criterion. For
scale of size N: for every pair (i, j), the interval spans |i−j| steps;
CS holds iff no interval size (within ε_CS, default 0.5¢) occurs at two
different step spans. Score = number of violating interval-size classes
(0 = CS). Additionally compute best-val Kendall tau: over vals
v = ⟨N, round(N·log₂3), round(N·log₂5), …⟩ for the scale's actual
prime limit plus ±1 perturbations per coordinate, Kendall-tau distance
between pitch order and val order; report the minimum. (Val search
space is small; log it.)

**M3 — Rothenberg propriety.** Proper iff max interval at span k ≤ min
interval at span k+1 for all k (strictly proper if <). Score ∈
{strictly proper, proper, improper} + count of violating span pairs.
Reference: Rothenberg 1978.

Unit tests before first run (harness rule): 12-EDO diatonic (proper,
CS, 2 gaps), 12-EDO whole-tone (strictly proper, 1 gap), a known
improper scale (e.g. Pythagorean [wolf] 12), and a random 6-note scale
(high gap entropy). Mirror the triads/tests structure.

---

## SHADOW-001 — comma perturbation of CPS factors

**Idea (Marcus's practice, formalized):** replace factor n with
2ᵏ·n ± 1. Always odd ⇒ co-prime to octave 2. Pitch displacement from
plain n is ≈ 1/(2ᵏ·n·ln 2) octaves — halves per k step. Injects new
primes ("reach") at vanishing pitch cost while softening the
degeneracy of 1 (e.g. 255 = 3·5·17 sits 6.8¢ below the octave;
4095 = 3²·5·7·13 sits 0.42¢ — inside scorer ε territory).

**Sweep:** base sets {1,3,5,7} (hexany CPS(4,2)), {1,3,5,7,9,11}
(eikosany CPS(6,3)); for each factor position, k ∈ 3..16, both signs.
One perturbed factor at a time first; pairs later if warranted.

**Measure per variant:** frozen-scorer (P, S, G) + triad quality;
tone-survival after dedup at ε_dedup ∈ {0.01, 0.1, 0.5, 2}¢; comma
spectrum (all pairwise intervals < 20¢); prime factorization of the
perturbed factor (prime vs composite, primes injected); M1–M3 melodic
scores.

**Falsifiable predictions (H-S1..3):**
- H-S1: exact-coincidence triads DROP relative to the unperturbed CPS
  for small k (the comma breaks alignment with the 1-products), and
  recover discontinuously when the displacement falls inside scorer ε
  (predicted threshold between k=8 and k=12 for n=1).
- H-S2: there is a sharp k* where dedup behavior snaps (tone count
  changes); k* shifts by exactly 1 per doubling of ε_dedup.
- H-S3: composite perturbations that share factors with the base set
  (e.g. 255 sharing 3, 5) yield higher triad counts than prime
  perturbations of comparable size (e.g. 257) — "connectivity beats
  pure novelty." This is the tweet-thesis made falsifiable.

## LAT-MEL-001 — melodic scoring of harmonic lattices (forward)

**Corpus:** all 70 hexanies from odd seeds ≤ 15 (reuse
triads/results/hex001.jsonl inputs), the 29 eikosanies from
hex003_eik001, dekanies if cheap, plus every SHADOW-001 variant.
Controls: MOS scales from the mos001 sweeps (should saturate the
melodic scores), random scales matched for cardinality (should floor
them).

**Falsifiable predictions (H-L1..3):**
- H-L1: the Eikosany {1,3,5,7,9,11} is a constant structure by machine
  check (M2 = 0 at ε_CS = 0.5¢). This verifies a claim attributed to
  Wilson rather than assuming it; either outcome is a finding.
- H-L2: CPS scales are systematically improper/multi-gap relative to
  MOS at matched cardinality (quantifies "CPS lacks melodic
  continuity" from CLAUDE.md), BUT rank within the CPS family varies —
  i.e. the melodic axis discriminates where the harmonic axis (P = S
  diagonal) cannot.
- H-L3: SHADOW perturbations degrade CS/propriety for small k and
  restore them as k → large (displacement → 0), with the restoration
  threshold tracking ε_CS the same way H-S2 tracks ε_dedup.

- H-L4 (**Wilson's 1965 rank–gap conjecture, two versions**). Primary
  source: Wilson letter to John Chalmers, 21 Aug 1965, and "The 3-gap
  theorem (Steinhaus conjecture) revisited" ©2005 (scan:
  `~/Library/Mobile Documents/com~apple~CloudDocs/Documents/ERV/scans
  by Kraig/2010_02_20/MOS/MOSMisc.pdf`; Wilson's own citation there:
  T. van Ravenstein, "The Three Gap Theorem (Steinhaus Conjecture)",
  J. Austral. Math. Soc. A 45 (1988) 360–370). In the 1965 letter
  Wilson conjectures the minimum number of melodic step sizes grows
  with the system: 3-limit min 2, 5-limit min 3, 7-limit min 4,
  **9-limit min 5**, 11-limit min 6. Note the fork: 9 = 3² adds no
  prime, so the two readings diverge —
  - H-L4a (prime-rank version): min gap count = (number of
    independent odd primes) + 1. Predicts a {1,3,5,7,9}-identity
    region behaves like rank 3 ⇒ min 4 gaps.
  - H-L4b (odd-identity version, Wilson's literal claim): min gap
    count = (number of odd identities) + 1 ⇒ min 5 gaps for the same
    region. Composites count as dimensions melodically even though
    they are lattice-interior harmonically.
  M1's gap counter can discriminate a vs b directly on generic lattice
  regions at fixed identity sets. Either outcome is a finding;
  b-wins would be the strongest support yet for the
  composites-as-load-bearing thesis (ties to H-S3). Modern
  generalizations of three-gap to higher rank exist (Haynes–Marklof
  line of work) — cite after verifying, not from memory.

**Deliverable:** results/latmel001.jsonl (one row per scale: family,
seeds/generator, M1–M3, frozen (P,S,G), quality) + first Pareto
scatter (melodic axis = propriety violations or gap entropy; harmonic
axis = P + quality). This is the map PARETO-001 will later refine.

## MOS-LAT-001 — the inverse: lattices from generators (round trip)

**Construction:** for a noble (or near-noble) generator g with zigzag
path from Brun levels 0–9: form the 2-term recurrence whose
characteristic root corresponds to g's continued-fraction tail; take
its 2×2 integer matrix M; eigen-embed ℤ² with physical axis (log-pitch)
and internal axis (algebraic conjugate). The MOS at each level should
be exactly the projection of lattice points whose internal coordinate
lies in a window (cut-and-project / Fibonacci-chain picture; window
derived from the level's convergent).

**Step 1 (verification, cheap):** for golden-ratio generator and 2–3
other nobles, confirm window-set == Brun scale at every level 0–9
against families/mos.py (which mirrors Brun.cpp zigzag). Any mismatch
is itself a finding (likely a semiconvergent-vs-convergent subtlety —
see constraint 4 above).

**Step 2 (the payoff):** score each level's scale with the frozen
scorer; separately compute lattice/window geometry descriptors (window
width, internal-coordinate spread, matrix spectral gap |λ|/|λ'|).
- H-M1: triad-count "hot spots" across generators correlate with a
  geometric descriptor of the conjugate embedding, not just with the
  generator value. (Exploratory but falsifiable: report correlation +
  permutation test; null = no descriptor beats generator-value binning.)
- H-M2 (bridge to Meru / CPS-seeded recurrence, future MERU-001):
  3-term recurrences seeded with CPS values define rank-3 embeddings
  (Rauzy-fractal windows); reserved, not in scope for 001.

**Deliverable:** results/moslat001.json (per generator × level:
verification bit, window params, frozen scores, descriptors).

## BRIDGE-001 — CPS subset structure inside an MOS (the endgame)

**Question (Marcus, 2026-07-22):** given an MOS whose hidden lattice
approximates a CPS, can the CPS subset structure (component CPS(n,k),
EulerGenus navigation) still be explored inside the MOS?

**Scope decision (Marcus, 2026-07-22): EG4 FIRST.** Target the
{1,3,5,7} Euler Genus — hexany CPS(4,2) (6 tones, octahedron, scorer
receipt (8,8) = its 8 triadic faces) up to the full 16-tone tesseract
— before EG6. Rationale: the EG4 lattice is rank 3 (primes 3,5,7), so
an MOS embedding needs exactly ONE comma, not two — the kernel
enumeration collapses to a short list of planar temperaments, and
host MOS cardinalities drop to the playable 7–22 range (6 addresses
for the hexany, 16 for the tesseract). Triad-survival becomes
literal: count surviving octahedron faces. All machinery
(val-assignment, monotonicity filter, filtered design BRIDGE-001b) is
factor-set-agnostic, so EG6 (eikosany, 2-comma kernels, N ≥ 20)
becomes **BRIDGE-002**, run only after EG4 validates the pipeline.
The eikosany-specific text below reads as the BRIDGE-002 scale-up;
method and design decisions apply to both.

**Answer to be verified: yes, structurally guaranteed; fidelity is the
measurable.** Subset containment is combinatorial (which factor
k-subsets) and survives ANY mapping; what's at risk is (a) injectivity
— do distinct eikosany tones collapse to one MOS degree, (b) metric
fidelity — cents error per tone, (c) triad survival under the frozen
scorer, (d) degree-consistency — the embedded subsets' step-span
patterns (reuse M2 machinery on the image).

**Rank accounting:** eikosany lattice is rank 4 (primes 3,5,7,11; the
9 is 3-interior). An MOS is rank 2 (period, generator). So an
embedding = a choice of exactly TWO independent commas to temper.
"Which MOS approximates CPS(6,3)" ⇔ "which 2-comma kernels of the
{3,5,7,9,11} lattice yield a rank-2 quotient whose MOS at N ≥ 20
carries the eikosany with small error." Finite, enumerable search;
organize candidates by hidden-lattice invariants per H-M1, not by raw
generator value.

**BRIDGE-000 — ground truth: D'Alessandro (Wilson 1975/1980/1989).**
Primary source: "D'Alessandro, Like a Hurricane" (scan:
`~/Library/Mobile Documents/com~apple~CloudDocs/Documents/ERV/scans
by Kraig/Marcus/anaphoria/dal.PDF`). Erv executed the bridge by hand:
his "template" is exactly the 31-EDO patent val (3→deg 18, 5→10,
7→25, 11→14; fifths-chain positions +1, +4, +10, +18; 9 = 3² treated
linearly: +2, deg 5 = 2·18 mod 31), applied HOMOMORPHICALLY ("the
final outcome is inevitable") to all 32 tones of the full
(0,6)–(6,6) EG6 PLUS 6 "pigtails" (fig 24: −1 = 3·5·7·9/11,
+8 = 3⁴·5, +9 = 7/3, +26 = 3⁴·5·11, +27 = 7·11/3, +36 = 11²) — 38
tones on 31 degrees, hence exactly 7 duplicated degrees
{0,5,10,13,18,23,28}. Five pairs are genus-internal (chain n ↔ n+31,
n = 0..4); two involve pigtails; together they realize exactly three
kernel commas: 385/384 (deg 18, 5, 23), 2079/2048 (deg 0, 10),
121/120 (deg 13, 28) — all resolved by keyboard geometry (distinct
linear positions), NOT by tempering pitch. The inverted D'Alessandro
(figs 26–27, Grady's marimba) keeps the same degree val but lifts 11
to −13 (≡ 18 mod 31; huygens vs meanpop, the two standard 11-limit
meantone extensions) — chain span shrinks to 31 and five collisions
become physical unisons, voiced by comma size (385/384 shares a bar;
2079/2048 split across octaves). So (val, integer LIFT) is a design
pair, not just the val — the lift is a free parameter BRIDGE search
should expose.
Task: encode the val, reproduce all 38 placements + 7 collision
pairs (both lifts) against the scan, then run the frozen scorer on
D'Alessandro — its first-ever harmonic fidelity measurement. This is
the calibration standard every BRIDGE candidate must beat. Run
before BRIDGE-001.
Note: the template's 9 = 3² arithmetic takes the H-L4a (prime-rank)
side while Wilson's 1965 letter takes H-L4b (odd-identity) — the
fork is internal to Wilson's own corpus.

**Three success regimes** (regime iii discovered in dal.PDF):
- (iii) *pitch-just, address-tempered* (the D'Alessandro regime):
  keep all pitches exactly just; temper only the degree bookkeeping.
  Error budget = 0 by construction; every CPS triad survives exactly;
  the cost appears as duplicate addresses (measure with M2) and is
  paid by keyboard geometry or octave voicing. Also historical prior
  art for LAT-MEL: Wilson 1968, "2 Eikosanies melodically compatible
  with modulus 22."

**Two tempering regimes, both interesting:** (i) faithful — all 20 tones
distinct, subsets intact, errors < ε_bridge (sweep 1–15¢); (ii)
tempered-merge — a comma identifies specific CPS tones; not failure
but temperament-as-feature (a smaller eikosany image with reinforced
coincidences). Log collisions with their comma monzos.

**Method:** for candidate (g, N): nearest-degree map of the eikosany
into the MOS; record collision count, per-tone error, frozen (P,S,G)
of the image AND of each embedded hexany, M2 consistency of each
subset. Objective: maximize (embedded-hexany triad survival) subject
to injectivity or principled merges.

**Payoff:** each hexany becomes a melodically-addressable REGION of
the MOS; modulation between subset chords becomes stepwise voice
leading. Direct substrate for the EG6 root-mapping feature (subset
keyboards in root space gain a melodic fingerboard). Depends on
melodic.py (M2) and MOS-LAT-001 descriptors; run after both.

**Design decisions (Marcus, 2026-07-22):**

1. *No nearest-degree rounding.* Degree assignment is BY THE VAL the
   kernel determines — algebraic, homomorphic by construction, cannot
   self-contradict. All error appears as detuning (measured by the
   error budget), never as structural contradiction. The only
   consistency check needed is monotonicity: val order == pitch order
   (M2 / epimorphy). Non-monotone kernel ⇒ REJECT, logging which
   comma caused the violation. Apply this filter first in the kernel
   enumeration, before error-budget work.

2. *Filtered design (cardinality fix, BRIDGE-001b).* Keep the rank-2
   temperament; drop chain-contiguity. Scale = CPS image indices on
   the generator chain + a filler set chosen by exact enumeration to
   maximize M1/M2/propriety subject to containing the image (filler
   budget ~3–6 from ~20 candidate slots — thousands of cases,
   deterministic, no stochastic solver). Two-gap-ness becomes an
   OBJECTIVE, not an assumption; 3-gap outcomes acceptable if scored.
   Note: removing tones can restore val monotonicity — kernels
   failing consistency on the full MOS may pass on the filtered
   scale, so re-run the monotonicity filter per filtered candidate.
   This is a new PARADIGM for Wilsonic (objective-defined vs
   generative design); if it ever ships, the solver must be
   exhaustive-deterministic (same APVTS params ⇒ same scale, every
   session) and lands at the END of the designs list per the
   compatibility rule. Research stays harness-side until then.

---

## Search parameterization note (applies to all generator sweeps)

Parameterize generator searches by BOUNDED CF DIGIT STRINGS, not by
grid points in (0,1). Rationale: a CF is a walk in GL(2,ℤ) (each
digit aₖ is the matrix [[aₖ,1],[1,0]]; convergents are the
accumulated columns — cf. Wilson's MOS Sequencer page in MOSMisc.pdf,
which computes exactly this by hand). Periodic tail ⇔ quadratic
generator ⇔ the walk loops ⇔ the hidden lattice (loop body = which
lattice; preamble digits = window placement/Möbius mask). Digit
influence is hierarchical (early digits coarse/all levels, late
digits deep levels only), so digit-string enumeration respects the
landscape's real structure — the (0,1) grid's "fractal spikiness" is
a coordinate artifact. Practical bound: digits ≤ ~5, depth ≤ ~9
(human MOS-depth limit) ⇒ low-millions of walks, exhaustively
enumerable, arithmetic identity (field, conjugate, loop) known by
construction. Compare zigzag/semiconvergent handling against
Brun.cpp:269 before trusting level alignment.

Rollout (Marcus, 2026-07-22): digit-string enumeration runs ALONGSIDE
the existing mos001-style grid sweeps for one cross-check run (the
mos001 receipts are the regression baseline — confirm both find the
same top generators), then digit-strings become the standard
parameterization for all subsequent sweeps.

## Order of execution

1. melodic.py + tests (blocks everything).
2. LAT-MEL-001 on the existing corpora (pure post-processing, no new
   scale generation) — cheapest, delivers H-L1 immediately.
3. SHADOW-001 (needs only families/cps.py + a perturbation wrapper).
4. MOS-LAT-001 step 1, then step 2.

Scorer-freeze compliance: nothing here edits triads/scorer.py; melodic
scores are a NEW axis, versioned independently (melodic.py starts at
v0.1.0, freeze after LAT-MEL-001 review, same hash-pin pattern if
kept).
