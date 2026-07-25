# The Tunings That Ring: an open research program on Erv Wilson's scale designs

**Marcus Hobbs · first posted 2026-07-25 · status: living document — this will be revised as experiments land. Receipts for every claim live in [the repository](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP).**

Erv Wilson spent a lifetime searching, by hand, for scales that solve music's
oldest tension: structures that serve **melody** (stepwise, singable, few step
sizes) and **harmony** (chords whose combination tones reinforce rather than
beat) at the same time. I worked at his side from 1995 to 2005, turning his
diagrams into software while he drew the next one. He's gone; the search
isn't. This post describes how I've made that search *falsifiable* — a scoring
function anyone can read, a queue of pre-registered experiments, and an
open invitation to tear both apart.

Two things up front. First, the entire computational program is run in
collaboration with an AI agent (Claude), and I'll be precise below about what
that means and why it works. Second, everything here is public: the scorer,
the receipts, the failures. If you think the scoring function is wrong — and
in at least one measured way it is incomplete — I want to hear from you.
[Skip to the invitation](#an-invitation-help-me-improve-the-scoring-function)
if that's why you came.

---

## The scoring function, fully disclosed

The harmonic axis is a frozen Python module,
[`experiments/triads/scorer.py`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/triads/scorer.py)
(v1.1.0). For frequencies `a < b < c`, all math in **frequency space**, never
cents:

- **proportional** (major prototype 4:5:6): `2b = a + c` — middle tone at the
  arithmetic mean of the outer tones
- **subcontrary** (minor prototype 10:12:15): `b(a + c) = 2ac` — middle tone
  at the harmonic mean
- **geometric** (neutral): `b² = ac` — counted, never scored

Why these three: when the middle tone sits at the arithmetic or harmonic mean,
first-order sum and difference tones land *on other scale degrees*. The triad
audibly locks. This is Wilson's proportional-triad criterion, and it is the
sonority the plugin's own analyzer looks for.

The conventions that make the numbers mean something:

- **Exact arithmetic for JI.** The rational path runs on `fractions.Fraction`
  end to end — zero floats, zero epsilon. The tempered path reconstructs
  `f = 2^(cents/1200)` and admits a single hyperparameter ε (default 2¢),
  which appears only in the comparison layer.
- **Middle-anchored sampling.** For each scale degree `b`, the outer tones
  range over the unique octave representatives in `(b/2, b)` and `(b, 2b)`.
  Chosen over the naive two-octave window because it is *exactly* self-dual
  (inverting the scale swaps proportional and subcontrary counts, P ↔ S) and
  *exactly* transposition-invariant. The window convention fails both; we
  keep it only for comparison.
- **Triads fit within an octave** (outer ratio ≤ 2/1, v1.1.0). 1:2:3 is
  arithmetically proportional but is not the chord this criterion is about.
  Ear-validated; it re-ranked results enough that v1.0.0 and v1.1.0 numbers
  are never mixed.
- **Octave reduction is half-open `[1, 2)`**, matching the shipping plugin
  bit for bit.
- **A degeneracy guard on the tempered path**: a triple whose arithmetic and
  harmonic means are closer than ε cannot be *shown* to be proportional
  rather than subcontrary, so it counts as neither. More on why below — this
  guard has a good origin story.

### Known limitations — measured, not hedged

Transparency means the defects list is part of the disclosure:

1. **P = S exactly for every MOS and every CPS(2k, k).** Both families are
   inversionally symmetric as pitch-class sets, and the anchored scorer
   commutes exactly with inversion. Consequence: the once-primary aggregate
   `min(P, S)` cannot discriminate *within* these families at all. It has
   been demoted to a recorded-but-not-optimized statistic.
2. **The aggregator is unsettled — by ear.** My listening check validated the
   *classifier* (the triads it finds do lock) but rejected `min(P, S)` as a
   ranking: I want proportional-heavy *and* subcontrary-heavy *and*
   geometric-heavy scales as distinct characters, not a scalarized compromise.
   Current reporting uses balance buckets instead. An aggregator worthy of
   freezing does not exist yet. This is the single best entry point for
   outside critique.
3. **Counts are not weighted by audibility.** A triad at the edge of ε counts
   the same as an exact rational coincidence; register, timbre, and critical
   band are ignored entirely.
4. **The plugin's own analyzer has a register-dependent tolerance.** Its
   `0.0005` linear-frequency threshold is ≈0.865¢ for triads rooted near 1/1
   but ≈0.433¢ near the octave — twice as strict at the top of the octave,
   which nothing in the theory motivates. Measured against the real compiled
   C++; tracked as a plugin issue, deliberately not silently "fixed."
5. **The melodic axis (below) is brand new** and has not yet had its own
   ear check.

## Why let an AI optimize against a scoring function?

The working pattern is what Andrej Karpathy has described for AI-driven
research: put the machine in the *outer* loop, operating on experiments, and
keep deterministic computation in the *inner* loop, operating on parameters.

- **Inner loop** — plain Python, no AI: exhaustive and quality-diversity
  batch search over scale families (Combination Product Sets, MOS
  generators), every candidate generated, scored, and archived. Headless and
  reproducible.
- **Outer loop** — an AI agent (Claude) proposes a hypothesis, writes the
  pre-registration entry *before* the run (prediction, tolerances, expected
  failure modes), implements, runs, and files the verdict as
  kept-or-reverted. Surprises become the next hypotheses.
- **The human** — I hold three things the loop cannot: the spec (what is
  worth asking), the ear (ground truth the metric approximates), and the
  freeze (what counts as a measurement).

Why this works for scale aesthetics in particular: the search spaces are
enormous but *cheap to evaluate* — a scorer verdict costs microseconds, so an
agent can test a thousand parameterizations of a hypothesis in the time a
human tests one. And Wilson's own practice was already loop-shaped: draw,
listen, redraw. The machine just runs the draw-score part of the loop at
scale, with receipts.

The obvious objection is Goodhart's law, and it bit us immediately —
concretely, and instructively. Early on, the tempered-path optimizer
discovered that a **1-cent generator** was the global optimum of `min(P, S)`
at every cardinality from 5 to 10 and at every ε: cram all the tones together
and every triple is within ε of *both* mean conditions simultaneously. The
scale is musical nonsense; the score was perfect. That episode is why the
scorer is **frozen** — SHA-256-pinned, CI-enforced, changeable only by
explicit human approval — and why the degeneracy guard exists: an optimizer
that can edit its own verifier is not being verified. The metric is allowed
to be wrong; it is not allowed to drift silently while something optimizes
against it.

The second firewall is the ear. Twice now the listening check has overruled
the machine — validating the triad classifier but rejecting the `min(P, S)`
aggregator, and forcing the within-an-octave span rule. Optimization pressure
is applied only to metrics that have survived a human ear, and every archived
number records which scorer version produced it.

## Past: what the loop has already found

Everything below is receipt-backed in the repo
([FINDINGS.md](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/triads/FINDINGS.md),
`results/`):

- **The offline mirror is bit-exact against the shipping plugin.** 70
  hexanies reproduced with zero mismatches and 15 MOS scales within 1 ulp
  against the real compiled C++ — an offline score can be trusted as the
  scale the plugin would actually produce.
- **All 29 eikosanies from odd seeds ≤ 15 sit exactly on P = S**, an instance
  of the inversional-symmetry theorem above — discovered empirically by the
  loop, then proven structural.
- **MOS generator sweeps** show triad-count hot spots that are stable across
  cardinality — near 571.6¢ at odd cardinalities, the pure fourth at N = 12,
  416¢ at N = 20. Mapping *why* these are hot is an open experiment (below).
- **The melodic axis exists as of this week**: three scorers — gap-size
  entropy (three-gap-theorem territory), Wilson's constant-structure
  criterion, and Rothenberg propriety — each a pure function of a pitch-class
  set with every tolerance logged.
- **The melodic unit tests immediately corrected two pieces of folklore**
  that had been written into our own spec: the 12-EDO diatonic is *not* a
  constant structure (the 600¢ tritone subtends both 3 and 4 steps), and the
  12-tone Pythagorean chromatic is *strictly proper* — the classic improper
  scale is the Pythagorean *diatonic*, whose 611.7¢ augmented fourth exceeds
  its 588.3¢ diminished fifth. A harness that catches errors in its own
  spec's assumptions before running a single experiment is the pattern
  working as intended.

## Present: scoring Wilson's harmonic objects for melody

**LAT-MEL-001** runs the melodic scorers over the full harmonic corpus — all
70 hexanies, all 29 eikosanies, MOS controls (which should saturate the
melodic scores), and random controls (which should floor them). Pre-registered
predictions, quoted from the spec:

- **H-L1**: the eikosany on {1,3,5,7,9,11} is a constant structure by machine
  check at 0.5¢. This *verifies* a claim long attributed to Wilson rather
  than assuming it — and either outcome is a finding.
- **H-L2**: CPS scales are systematically improper and multi-gap relative to
  MOS at matched cardinality — quantifying the folk claim that "CPS lacks
  melodic continuity" — *but* melodic rank varies within the CPS family,
  discriminating exactly where the harmonic axis (stuck on the P = S
  diagonal) cannot.
- **H-L4 — Wilson's 1965 rank–gap conjecture, the one I most want to test.**
  In a letter to John Chalmers (21 Aug 1965), Wilson conjectured the minimum
  number of melodic step sizes grows with the odd-limit: 3-limit 2, 5-limit
  3, 7-limit 4, **9-limit 5**, 11-limit 6. The 9-limit case forks the
  conjecture, because 9 = 3² adds no new prime: does a {1,3,5,7,9} region
  behave like rank 3 (prime-rank reading → minimum 4 gaps) or like 4
  independent identities (Wilson's literal claim → minimum 5)? The gap
  counter can discriminate directly. If Wilson's literal version wins,
  composite identities are *load-bearing melodic dimensions* even though
  they are lattice-interior harmonically — which would connect to the comma
  experiments below.

## Future: the queue, and why each experiment is there

**SHADOW-001 — comma perturbation of CPS factors.** A practice of mine turned
falsifiable: replace a CPS factor n with `2^k·n ± 1` (always odd, so co-prime
with the octave). Pitch displacement halves per step of k, while the *prime
content* changes completely — 255 = 3·5·17 sits 6.8¢ under the octave;
4095 = 3²·5·7·13 sits 0.42¢. Predictions: exact-coincidence triads drop for
small k and recover discontinuously when displacement falls inside scorer ε;
dedup behavior snaps at a threshold k\* that shifts by exactly one per
doubling of the dedup tolerance; and — the thesis I care about — perturbations
that *share factors* with the base set (255 shares 3 and 5) beat prime
perturbations of comparable size (257): **connectivity beats pure novelty**.

**MOS-LAT-001 — the hidden lattice of a noble generator.** Every
quadratic-irrational generator is a loop in the scale tree; its continued
fraction is a walk in GL(2,ℤ), and the MOS at each level should be exactly a
cut-and-project set — lattice points whose conjugate coordinate falls in a
window (the Fibonacci-chain picture). Step 1 verifies that construction
against the plugin's own Brun recursion at every level. Step 2 asks whether
triad-count hot spots across generators correlate with geometric descriptors
of the conjugate embedding (window width, spectral gap) rather than with the
generator value itself — with a permutation test, because "hot spots exist"
is cheap and "hot spots are *explained*" is not. This would turn the MOS
sweep's empirical bumps into arithmetic.

**BRIDGE-000 — D'Alessandro as calibration standard.** Wilson executed the
melody⇄harmony bridge *by hand* in D'Alessandro (1975/1989): a 31-tone
template — precisely the 31-EDO patent val — applied homomorphically to 38
just tones, producing exactly 7 duplicated degrees that realize three kernel
commas (385/384, 2079/2048, 121/120), resolved by keyboard geometry rather
than by tempering a single cent. The inverted version (Kraig Grady's marimba)
keeps the val but lifts 11 differently — the two standard 11-limit meantone
extensions, hiding in a pair of 50-year-old diagrams. The experiment: encode
the val, reproduce all 38 placements and all 7 collisions against the
primary-source scans, then run the frozen scorer on D'Alessandro — its
first-ever quantitative harmonic-fidelity measurement. Every machine-proposed
bridge that follows must beat it.

**BRIDGE-001 — CPS structure inside an MOS.** The endgame question: given an
MOS whose hidden lattice approximates a Combination Product Set, does the CPS
subset structure survive — can you still navigate hexanies inside it, with
stepwise voice leading between subset chords? Rank accounting makes the
search finite: embedding the {1,3,5,7} genus (rank 3) into an MOS (rank 2)
means choosing exactly one comma to temper; enumerate kernels, reject any
whose val order contradicts pitch order, measure triad survival on what
remains. D'Alessandro proves a third regime exists — keep every pitch exactly
just and temper only the *addressing* — where the cost is paid in duplicate
keyboard positions instead of cents.

**PARETO-001 — the melody × harmony frontier.** With both axes scored, plot
every scale the program has ever generated on (melodic score, harmonic
score). The conjecture worth testing: Wilson's published designs sit on or
near the Pareto frontier of that plot — that his lifetime of hand search was,
in effect, multi-objective optimization, and the frontier's *shape* (smooth
trade-off? sharp knee?) is itself a finding about what scale design is.

Further out, and speculative on purpose: 3-term recurrences seeded with CPS
values (Meru/Rauzy-fractal windows, rank-3 cut-and-project), and
temperament-as-feature — treating specific comma collisions not as error but
as reinforcement.

## An invitation: help me improve the scoring function

This is the part I actually want responses to. The scorer measures one
aesthetic — mean-coincidence triads — and one new axis measures melodic
viability. That is nowhere near a theory of what makes a tuning beautiful.
Things I would genuinely like to argue about:

- **Aggregation.** Given (P, S, G) and triad quality, what is the *right*
  harmonic objective? My ear rejected `min(P, S)`. Balance buckets are a
  placeholder. Is the honest answer that no scalar exists and the Pareto
  view is the finished product?
- **Melody + harmony balance.** Once PARETO-001 exists: is distance-to-frontier
  a musically meaningful penalty? Should the axes be weighted by use — a
  performance scale vs. a drone scale?
- **Missing dimensions.** Difference-tone audibility weighting (register and
  amplitude matter; my counts ignore both). Critical-band roughness.
  Voice-leading economy between subset chords. Tetrads and beyond — Wilson's
  own CPS structures are built from higher-order chords, and a triad-only
  scorer under-values them almost by construction.
- **Counterexamples, most of all.** Scales that sound extraordinary and score
  badly, or score brilliantly and sound dead. One good counterexample is
  worth more than any amount of agreement — the whole apparatus exists to be
  falsified.

Engage via
[GitHub Discussions](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/discussions)
for ideas and argument, or
[Issues](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues) for
concrete scorer proposals and bug reports. Scales the program surfaces are
exported as Scala `.scl` files in the results directories if you want to
listen before you argue — and I hope you do listen first.

---

*Production note, in the spirit of transparency: the experiments, code, and
first drafts of documents like this one are produced by an AI agent (Claude)
operating inside the research loop described above; I set the questions,
review every finding against the primary sources and my own ear, and no
measurement standard changes without my explicit approval. The mistakes that
survive that process are mine.*
