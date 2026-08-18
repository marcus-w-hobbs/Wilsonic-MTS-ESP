# The Tunings That Ring: an open research program on Erv Wilson's scale designs

**Marcus Hobbs · first posted 2026-07-25 · status: living document, revised as experiments land. Receipts for every claim live in [the repository](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP).**

Erv Wilson spent his lifetime searching, by hand, for scales that resolve one
of music's oldest tensions. A scale that serves **melody** wants to be
stepwise and singable and built from just a few step sizes, and a scale that
serves **harmony** wants chords whose combination tones reinforce each other
rather than beat against each other, and Erv wanted structures that do both
at the same time. I worked at his side from 1995 to 2005, turning his
diagrams into software while he drew the next one. Erv passed away in 2016,
and I have kept going because the search he started was never finished. In
this post I describe how I have tried to make that search falsifiable, with
a scoring function anyone can read, a queue of experiments whose predictions
are registered before they run, and an open invitation to tear both apart.

I want to say two things up front. First, I run the entire computational
program in collaboration with an AI agent (Claude), and I will be precise
below about what that means and why I believe it works. Second, everything
here is public, including the scorer, the receipts, and the failures. If you
think the scoring function is wrong, and in at least one measured way I know
it is incomplete, then I want to hear from you.
[Skip to the invitation](#an-invitation-help-me-improve-the-scoring-function)
if that is why you came.

---

## The scoring function, fully disclosed

The harmonic axis is a frozen Python module,
[`experiments/triads/scorer.py`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/triads/scorer.py)
(v1.1.0). For frequencies `a < b < c`, all of the math happens in
**frequency space** rather than in cents:

- **proportional** (major prototype 4:5:6): `2b = a + c`, which places the
  middle tone at the arithmetic mean of the outer tones
- **subcontrary** (minor prototype 10:12:15): `b(a + c) = 2ac`, which places
  the middle tone at the harmonic mean
- **geometric** (neutral): `b² = ac`, which the scorer counts but never
  scores

Why these three? When the middle tone sits at the arithmetic or harmonic
mean, the first-order sum and difference tones land on other scale degrees,
so the triad audibly locks. This is Wilson's proportional-triad criterion,
and it is the same sonority the plugin's own analyzer looks for.

Several conventions make the numbers mean something, so I will spell them
out:

- **Exact arithmetic for JI.** The rational path runs on
  `fractions.Fraction` from end to end, so there are no floats and no
  epsilon anywhere in it. The tempered path reconstructs
  `f = 2^(cents/1200)` and admits a single hyperparameter ε (default 2¢),
  which appears only in the comparison layer.
- **Middle-anchored sampling.** For each scale degree `b`, the outer tones
  range over the unique octave representatives in `(b/2, b)` and `(b, 2b)`.
  I chose this over the naive two-octave window because it is exactly
  self-dual, meaning that inverting the scale swaps the proportional and
  subcontrary counts (P ↔ S), and it is exactly transposition-invariant.
  The window convention fails both tests, so we keep it only for comparison.
- **Triads fit within an octave** (outer ratio ≤ 2/1, v1.1.0). 1:2:3 is
  arithmetically proportional, but it is not the chord this criterion is
  about. I validated this rule by ear, and it re-ranked results enough that
  v1.0.0 and v1.1.0 numbers are never mixed.
- **Octave reduction is half-open `[1, 2)`**, matching the shipping plugin
  bit for bit.
- **A degeneracy guard on the tempered path.** A triple whose arithmetic and
  harmonic means are closer than ε cannot be shown to be proportional rather
  than subcontrary, so it counts as neither. I explain below why this guard
  exists, because it has an instructive origin story.

### Known limitations

I have measured these rather than hedged about them, because I believe the
defects list is part of the disclosure:

1. **P = S exactly for every MOS and every CPS(2k, k).** Both families are
   inversionally symmetric as pitch-class sets, and the anchored scorer
   commutes exactly with inversion. The consequence is that the aggregate
   `min(P, S)`, which was once primary, cannot discriminate within these
   families at all, so I have demoted it to a statistic that is recorded but
   no longer optimized.
2. **The aggregator is unsettled, and my ear is the reason.** My listening
   check validated the classifier, because the triads it finds really do
   lock, but it rejected `min(P, S)` as a ranking. I found that I want
   proportional-heavy and subcontrary-heavy and geometric-heavy scales as
   distinct musical characters rather than as a scalarized compromise.
   Current reporting uses balance buckets instead, and an aggregator I would
   be willing to freeze does not exist yet. This is the single best entry
   point for outside critique.
3. **Counts are not weighted by audibility.** A triad at the edge of ε
   counts the same as an exact rational coincidence, and register, timbre,
   and critical band are ignored entirely.
4. **The plugin's own analyzer has a register-dependent tolerance.** Its
   `0.0005` linear-frequency threshold is ≈0.865¢ for triads rooted near 1/1
   but ≈0.433¢ near the octave, which makes it twice as strict at the top of
   the octave, and nothing in the theory motivates that. I measured this
   against the real compiled C++, and I am tracking it as a plugin issue
   because I did not want it silently "fixed."
5. **The melodic axis (below) is brand new** and has not yet had its own
   ear check.

## Why let an AI optimize against a scoring function?

The working pattern is one Andrej Karpathy has described for AI-driven
research: put the machine in the *outer* loop, operating on experiments, and
keep deterministic computation in the *inner* loop, operating on parameters.

- **The inner loop** is plain Python with no AI in it: exhaustive and
  quality-diversity batch search over scale families (Combination Product
  Sets and MOS generators), with every candidate generated, scored, and
  archived, headless and reproducible.
- **The outer loop** is an AI agent (Claude) that proposes a hypothesis,
  writes the pre-registration entry before the run happens, including the
  prediction, the tolerances, and the expected failure modes, then
  implements, runs, and files the verdict as kept-or-reverted. The surprises
  become the next hypotheses.
- **I hold three things the loop cannot hold.** I decide what is worth
  asking, my ear supplies the ground truth that the metric only
  approximates, and I decide when a measurement standard is frozen.

Why does this work for scale aesthetics in particular? Because the search
spaces are enormous but cheap to evaluate. A scorer verdict costs
microseconds, so an agent can test a thousand parameterizations of a
hypothesis in the time it takes a human to test one. And Wilson's own
practice was already shaped like a loop, because he would draw, listen, and
redraw. The machine runs the draw-and-score part of that loop at scale, and
it keeps receipts.

The obvious objection is Goodhart's law, and it bit us immediately, in a way
I found both alarming and instructive. Early on, the tempered-path optimizer
discovered that a **1-cent generator** was the global optimum of `min(P, S)`
at every cardinality from 5 to 10 and at every ε, because if you cram all
the tones together then every triple is within ε of both mean conditions
simultaneously. The scale is musical nonsense, but the score was perfect,
and seeing that happen so quickly convinced me that the scorer had to be
protected from the thing optimizing against it. That episode is why the
scorer is **frozen**, pinned by SHA-256, enforced by CI, and changeable only
with my explicit approval, and it is why the degeneracy guard exists,
because an optimizer that can edit its own verifier is not really being
verified. I accept that the metric may be wrong, but I will not let it drift
silently while something optimizes against it.

The second firewall is my ear. Twice now the listening check has overruled
the machine, once by validating the triad classifier while rejecting the
`min(P, S)` aggregator, and once by forcing the within-an-octave span rule.
Optimization pressure is applied only to metrics that have survived a human
ear, and every archived number records which scorer version produced it.

## Past: what the loop has already found

Everything below is receipt-backed in the repo
([FINDINGS.md](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/triads/FINDINGS.md),
`results/`):

- **The offline mirror is bit-exact against the shipping plugin.** We
  reproduced 70 hexanies with zero mismatches and 15 MOS scales within 1 ulp
  against the real compiled C++, so I can trust that an offline score
  describes the scale the plugin would actually produce.
- **All 29 eikosanies from odd seeds ≤ 15 sit exactly on P = S.** This is an
  instance of the inversional-symmetry theorem above, and I enjoyed the
  order in which it arrived, because the loop discovered it empirically
  first and we proved it structural afterward.
- **MOS generator sweeps** show triad-count hot spots that are stable across
  cardinality, near 571.6¢ at odd cardinalities, at the pure fourth at
  N = 12, and at 416¢ at N = 20. Mapping why these spots are hot is an open
  experiment, which I describe below.
- **The melodic axis exists as of this week.** It consists of three scorers,
  gap-size entropy (which lives in three-gap-theorem territory), Wilson's
  constant-structure criterion, and Rothenberg propriety, and each one is a
  pure function of a pitch-class set with every tolerance logged.
- **The melodic unit tests immediately corrected two pieces of folklore**
  that had been written into our own spec, and this genuinely surprised me.
  The 12-EDO diatonic is not a constant structure, because the 600¢ tritone
  subtends both 3 and 4 steps. And the 12-tone Pythagorean chromatic is
  strictly proper, because the classic improper scale is actually the
  Pythagorean *diatonic*, whose 611.7¢ augmented fourth exceeds its 588.3¢
  diminished fifth. I was glad to see the harness catch errors in its own
  spec's assumptions before running a single experiment, because that is
  exactly what I built it to do.

## Present: scoring Wilson's harmonic objects for melody

**LAT-MEL-001** runs the melodic scorers over the full harmonic corpus: all
70 hexanies, all 29 eikosanies, MOS controls (which should saturate the
melodic scores), and random controls (which should floor them). The
predictions were registered before the run, and I quote them from the spec:

- **H-L1**: the eikosany on {1,3,5,7,9,11} is a constant structure by
  machine check at 0.5¢. This claim has long been attributed to Wilson, and
  I would rather verify it than keep assuming it, and either outcome will be
  a finding.
- **H-L2**: CPS scales are systematically improper and multi-gap relative to
  MOS at matched cardinality, which would quantify the folk claim that "CPS
  lacks melodic continuity," but melodic rank varies within the CPS family,
  so it discriminates exactly where the harmonic axis, stuck on the P = S
  diagonal, cannot.
- **H-L4 is Wilson's 1965 rank–gap conjecture, and it is the one I most
  want to test.** In a letter to John Chalmers dated 21 Aug 1965, Wilson
  conjectured that the minimum number of melodic step sizes grows with the
  odd-limit: 2 at the 3-limit, 3 at the 5-limit, 4 at the 7-limit, **5 at
  the 9-limit**, and 6 at the 11-limit. The 9-limit case forks the
  conjecture, because 9 = 3² adds no new prime. Does a {1,3,5,7,9} region
  behave like rank 3, which is the prime-rank reading and predicts a minimum
  of 4 gaps, or like 4 independent identities, which is Wilson's literal
  claim and predicts a minimum of 5? The gap counter can discriminate
  directly. If Wilson's literal version wins, then composite identities are
  load-bearing melodic dimensions even though they sit in the interior of
  the harmonic lattice, and that would connect to the comma experiments
  below.

## Future: the queue, and why each experiment is there

Where do we go from here? Each experiment in the queue is there because it
tests something I cannot currently answer, and I want to explain the reason
alongside the design.

**SHADOW-001 — comma perturbation of CPS factors.** This takes a practice of
mine and makes it falsifiable. I replace a CPS factor n with `2^k·n ± 1`,
which is always odd and therefore co-prime with the octave. The pitch
displacement halves with each step of k while the prime content changes
completely, so for example 255 = 3·5·17 sits 6.8¢ under the octave and
4095 = 3²·5·7·13 sits 0.42¢ under it. I predict that exact-coincidence
triads drop for small k and recover discontinuously when the displacement
falls inside the scorer's ε, that the dedup behavior snaps at a threshold
k\* which shifts by exactly one per doubling of the dedup tolerance, and,
this is the thesis I care most about, that perturbations which share factors
with the base set (255 shares 3 and 5) will outperform prime perturbations
of comparable size such as 257, because staying connected to the existing
factors matters more than the novelty of a new prime.

**MOS-LAT-001 — the hidden lattice of a noble generator.** Every
quadratic-irrational generator is a loop in the scale tree, and its
continued fraction is a walk in GL(2,ℤ), so the MOS at each level should be
exactly a cut-and-project set, meaning lattice points whose conjugate
coordinate falls in a window, which is the Fibonacci-chain picture. Step 1
verifies that construction against the plugin's own Brun recursion at every
level. Step 2 asks whether the triad-count hot spots across generators
correlate with geometric descriptors of the conjugate embedding, such as
window width and spectral gap, rather than with the generator value itself.
I insist on a permutation test here, because showing that hot spots exist is
easy and showing that something explains them is much harder. If this works
it would turn the MOS sweep's empirical bumps into arithmetic.

**BRIDGE-000 — D'Alessandro as calibration standard.** Wilson executed the
melody⇄harmony bridge by hand in D'Alessandro (1975/1989). He applied a
31-tone template, which is precisely the 31-EDO patent val, homomorphically
to 38 just tones, producing exactly 7 duplicated degrees that realize three
kernel commas (385/384, 2079/2048, 121/120), and he resolved them with
keyboard geometry rather than by tempering a single cent. The inverted
version, which Kraig Grady built as a marimba, keeps the val but lifts 11
differently, and the two versions turn out to be the two standard 11-limit
meantone extensions, hiding in a pair of 50-year-old diagrams. The
experiment is to encode the val, reproduce all 38 placements and all 7
collisions against the primary-source scans, and then run the frozen scorer
on D'Alessandro, which would be its first quantitative harmonic-fidelity
measurement. I want every machine-proposed bridge that follows to have to
beat it.

**BRIDGE-001 — CPS structure inside an MOS.** This is the endgame question
for me: given an MOS whose hidden lattice approximates a Combination Product
Set, does the CPS subset structure survive, so that you can still navigate
hexanies inside it with stepwise voice leading between subset chords? Rank
accounting makes the search finite, because embedding the {1,3,5,7} genus
(rank 3) into an MOS (rank 2) means choosing exactly one comma to temper, so
we can enumerate the kernels, reject any whose val order contradicts pitch
order, and measure triad survival on what remains. D'Alessandro proves that
a third regime exists, in which every pitch stays exactly just and only the
*addressing* is tempered, and the cost is paid in duplicate keyboard
positions instead of cents.

**PARETO-001 — the melody × harmony frontier.** Once both axes are scored, I
can plot every scale the program has ever generated on the plane of
(melodic score, harmonic score). The conjecture I think is worth testing is
that Wilson's published designs sit on or near the Pareto frontier of that
plot, which would mean his lifetime of hand search was, in effect,
multi-objective optimization. The shape of that frontier, whether it is a
smooth trade-off or a sharp knee, would itself be a finding about what scale
design is.

Further out, and speculative on purpose, are 3-term recurrences seeded with
CPS values (Meru and Rauzy-fractal windows, rank-3 cut-and-project), and
treating temperament as a feature, so that specific comma collisions are
heard as reinforcement instead of error.

## An invitation: help me improve the scoring function

This is the part I actually want responses to. The scorer measures one
aesthetic, the mean-coincidence triad, and the one new axis measures melodic
viability, and together that is nowhere near a theory of what makes a tuning
beautiful. Here are the things I would genuinely like to argue about:

- **Aggregation.** Given (P, S, G) and triad quality, what is the right
  harmonic objective? My ear rejected `min(P, S)`, and the balance buckets I
  use now are a placeholder. Is the honest answer that no scalar exists and
  the Pareto view is the finished product?
- **Balancing melody and harmony.** Once PARETO-001 exists, is
  distance-to-frontier a musically meaningful penalty? Should the axes be
  weighted by use, so that a performance scale and a drone scale are judged
  differently?
- **Missing dimensions.** Difference-tone audibility weighting, because
  register and amplitude matter and my counts ignore both. Critical-band
  roughness. Voice-leading economy between subset chords. Tetrads and
  beyond, because Wilson's own CPS structures are built from higher-order
  chords, so a triad-only scorer under-values them almost by construction.
- **Counterexamples, most of all.** I am looking for scales that sound
  extraordinary and score badly, or that score brilliantly and sound dead.
  One good counterexample would teach me more than any amount of agreement,
  because the whole apparatus exists to be falsified.

You can engage via
[GitHub Discussions](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/discussions)
for ideas and argument, or
[Issues](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues) for
concrete scorer proposals and bug reports. The scales the program surfaces
are exported as Scala `.scl` files in the results directories, so you can
listen before you argue, and I hope you do listen first.

---

*Production note, in the spirit of transparency: the experiments, the code,
and the first drafts of documents like this one are produced by an AI agent
(Claude) operating inside the research loop described above. I set the
questions, I review every finding against the primary sources and my own
ear, and no measurement standard changes without my explicit approval.
Whatever mistakes survive that process are my responsibility.*
