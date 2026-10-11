# The Machine Keeps Deriving Wilson: three episodes from the lattice module

**Marcus Hobbs · first posted 2026-08-18 · status: living document, revised as experiments land. Receipts for every claim live in [the repository](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP).**

*Series: this is the second post in the research program. The first,
[The Tunings That Ring](research-blog-001.md), discloses the scoring
function and explains why an AI agent sits in the outer loop of the
search.*

In the first post I described a queue of experiments whose predictions
were registered before they ran. Since then the whole queue has run and
been gated in
[`experiments/GATES.md`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/GATES.md),
and a pattern showed up that I had not planned for. Whenever I gave the
machine an exhaustive search over a space Erv Wilson had worked in by
hand, it kept arriving at the thing Erv had already drawn. I want to tell
three of those episodes in the order they happened, with every number
linked to the file that holds it, because the pattern is only
interesting if the receipts are real. The findings are collected in
[`experiments/lattice/FINDINGS.md`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/FINDINGS.md)
and the dated pre-registrations and verdicts are in
[`LOG.md`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/LOG.md).

---

## Episode 1: BRIDGE-000, and the 1975 keyboard comes out of an exhaustive search

D'Alessandro is a keyboard design Erv issued in 1975. He took the
1.3.5.7.9.11 Combination Product Set series, which is 32 tones from the
Euler genus plus 6 "pigtail" tones for 38 tones in all, and he mapped
them onto 31 keyboard degrees using a template that is exactly the 31-EDO
patent val ⟨31, 49, 72, 87, 107⟩. I finally reproduced it from the primary
source as BRIDGE-000. The scan of "D'Alessandro, Like a Hurricane" lives
in the archive Kraig Grady scanned, and I read it in place and committed
only a derived table of anchors with figure numbers, which is
[`BRIDGE000_TRANSCRIPTION.md`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/BRIDGE000_TRANSCRIPTION.md).

Before opening the scan I registered a prediction, H-B1, that Erv's val
would minimize the number of tie-pairs, meaning two tones landing on one
degree, over the 80 vals that differ from his by ±1 in any odd
coordinate. Thirty-eight tones on 31 degrees force at least 7 collisions
by pigeonhole, so the prediction was that his template would hit exactly
7 and that no neighbor would do better.

The reproduction came out exact on every anchor. The 38 tones sit on a
consecutive chain of fifths from −1 to +36, the collisions land at
exactly degrees {0, 5, 10, 13, 18, 23, 28}, and the comma census is
385/384 three times, 2079/2048 twice, and 121/120 twice, which matches
figure 24 and matches the legend Erv wrote on figure 26 himself, where he
marked the 2079/2048 pairs with a plus and the 385/384 pairs with an
asterisk
([`bridge000.json`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/bridge000.json)).
The frozen scorer then gave D'Alessandro its first quantitative harmonic
measurement: P = S = 154 and G = 28 on the full 38-tone set, and all 15
embedded hexanies are addressed injectively, so none of Erv's seven
collisions ever puts two tones of the same hexany on one key. That pair
of numbers, harmonic wealth against 7 collisions at zero cents of error,
is now the calibration standard every machine-proposed bridge has to
beat.

H-B1 was kept exactly as registered. None of the 80 neighbors is better
than Erv's val and exactly one ties it, and the one that ties maps 3 to
19 steps of 31, which is a fifth near 735¢ that nobody would tune, while
the worst neighbor has 52 tie-pairs. So the 1975 template is, by machine
check, the optimal 31-degree addressing of these 38 tones, and it is the
only accurate val at the optimum.

I want to say what that felt like, because it was the moment this post
started to exist. I sat next to Erv for ten years and I watched him do
this kind of thing with a pencil, and I always assumed he was choosing
well, but I had never had a way to ask whether he was choosing
optimally. When the sweep came back with zero better neighbors, what I
felt was recognition, because I had seen him solve discrete problems by
inspection many times, and here was one of them measured. It also tied
the program together in a way I did not expect. The val-tie quantity had
already explained why the bare eikosany fails to be a constant structure
(LAT-MEL-001 found 32 interval classes that subtend two step counts, and
the eikosany's best val has 13 tied pairs), and it had delimited the
constant-structure eikosanies in CS-EIK-001, and now it turned out to be
exactly the quantity Erv's 1975 template minimizes.

## Episode 2: BRIDGE-001, and the 1975 trick shows up in the machine's own answers

The next question was the one I called the endgame in the first post.
Can a Combination Product Set live inside an MOS, so that its subset
chords become melodically addressable regions with stepwise voice
leading between them? I scoped it to the {1,3,5,7} tesseract, 16 formal
vertices and 8 distinct tones, hosted in an MOS of at most 22 notes. The
search enumerated 63 pre-registered 7-limit commas against ±1-patent
vals at N from 7 to 22, which is 2205 comma-and-val pairs, of which 590
were rejected because the val order contradicted pitch order
([`bridge001.jsonl`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/bridge001.jsonl),
[`bridge001_summary.json`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/bridge001_summary.json)).

I had registered a pass for H-B2, and it failed under the strict reading.
No candidate at N ≤ 22 is at once injective on the 8 tones, contained in
an N-note MOS window at any anchor, and fully triad-surviving on the
hexany at the scorer's ε of 2¢. What surprised me was where the two
halves separated. Ennealimmal, at 2401/2400 with 4375/4374, has a maximum
tone error of 0.204¢ with full hexany survival, but its generator counts
push the chain span past every window of 22 or fewer notes, and the
contained candidates, a front owned entirely by 225/224 as I had
predicted, top out at hexany survival of (3, 3) at 2¢. So the thing
blocking a faithful bridge at these cardinalities is the MOS window, and
tuning accuracy was already good enough.

Then I swept ε after the fact. Miracle, with the val ⟨21, 33, 49, 59⟩
and the secor generator of 116.588¢, recovers the full (6, 6) hexany at
ε = 3¢, and orwell-22, with ⟨22, 35, 51, 62⟩, a 271.385¢ generator, and
a maximum tone error of 2.727¢, recovers it at ε = 4¢. The bar I had
registered was one cent too strict for the best MOS host under 22 notes,
so blackjack, the 21-note miracle MOS, carries a full hexany with one
extra cent of triad tolerance.

Two structural things came out of the same run that I value more than
the headline. First, 1026 of the scored candidates have degree collisions
in which the two tones keep distinct pitches, so they share an address
and are told apart by their position on the chain, and the best of these
has a maximum error of 0.492¢ (2401/2400 under ⟨7, 11, 17, 20⟩, with
address-commas 16/15 and 21/20). That is D'Alessandro's third regime,
pitch kept just and only the addressing tempered, and it arose
spontaneously in a search that knew nothing about the 1975 keyboard. I
had thought of that regime as an idiosyncrasy of Erv's, and it turns out
to be what the lattice offers whenever there are more tones than
degrees. Second, no row on the Pareto front contains the genus at anchor
0, because miracle needs anchors between −14 and −9 and orwell between
−6 and −3, so the murchana-anchor sweep that MOS-LAT-001 had flagged as a
corollary turned out to be load-bearing on every successful embedding.
Against the BRIDGE-000 standard the design space is two corners with
nothing between them at this scale: Erv holds 0¢ of error with 7
collisions and every subset triad surviving, and the tempered hosts hold
0 collisions with 2.7¢ to 6.9¢ of error and full survival only from ε of
3¢ to 4¢.

## Episode 3: MOS-LAT-001 and 002, a null result twice, and then the archive

This is the episode I was most excited about going in, and it failed,
and I want to explain why the failure was still useful. The idea was
that a noble generator's MOS is a cut-and-project set of a
two-dimensional lattice, so the triad hot spots in the generator sweep
might correlate with the geometry of the hidden lattice, such as the
conjugate separation, the window width, or the spectral gap, and if that
had worked the empirical bumps would have become arithmetic.

The construction itself checked out. For nobles with |g − g′| > 1 the
plugin's Brun construction is exactly a window set at every level from 0
to 9, and for the closer conjugates the anchored segment fails at certain
convergent levels by exactly one intruding tone while shifted segments
pass, which is a murchana artifact and became the anchor sweep BRIDGE-001
later needed
([`moslat001.json`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/moslat001.json)).
Then the correlation test came back null. Over 27 noble generators and
97 rows at N from 5 to 22 the hot spots were real, with P ranging from 0
to 62 and the top at the noble minor third near 317.17¢ with P = 62 at
N = 19, but no descriptor reached |partial ρ| above 0.05 or p below 0.35
against a baseline of ρ = −0.162 at p = 0.350. There was an honest
excuse, because on an all-1s tail the spectral gap is constant at φ² and
the corpus barely varies, so I re-ran it with mixed tails as
MOS-LAT-002: 216 distinct quadratic generators over ℚ(√d) for
d ∈ {2, 3, 5, 13, 15, 21}, 788 rows, and a spectral gap now ranging from
5.83 to 61.98. It was null again. The nearest miss was the spectral gap
at ρ = −0.064 and p = 0.0635, weaker than the baseline |ρ| = 0.071, and
every Holm-adjusted p was 0.32 or higher
([`moslat002.json`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/moslat002.json)).

I was disappointed, and I want to say so plainly, because I liked that
idea and I had written it into the first post as the experiment that
would turn bumps into arithmetic. But the null was worth having for two
reasons. The pre-registration had said that a second null on a
non-degenerate corpus would close the descriptor program, so it closed
cleanly and I did not have to argue with myself about it. And the run
handed me a mechanism I now believe. Two generators from unrelated
fields, 351.40¢ in ℚ(√15) with a spectral gap of 61.98 and 351.47¢ in
ℚ(√2) with a gap of 5.83, score identically at P = 45 for N = 17, so at
ε = 2¢ the triad count is a locally stable function of where the
generator sits on the circle, while every conjugate descriptor jumps
with the arithmetic identity and therefore cannot carry information the
generator value does not already carry.

Then I went into the archive, and the null turned into the third
episode. Kraig's scans include a three-page table titled "64 Golden
Generators for Two-Interval Patterns (MOS)," © 1993 by Erv Wilson, with
the HP-calculator program he used to compute it, and the derived index in
[`experiments/archive/INDEX.md`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/archive/INDEX.md)
cites it as `2010_02_20/MOS/GoldenGenerators.pdf`. Row #18 of Erv's table
is .264308496 of an octave, which is 317.17¢, the generator that tops
both of my corpora, and all four MOS-LAT-001 generators are rows of that
table up to octave complement. So the corpus I thought I had designed for
this experiment was a table Erv had already computed on a calculator in
1993, and I did not know that when I built it. The same batch holds his
Hanson working papers (`2010_02_24/Hanson/HansonMisc.pdf`, page 4), where
he wrote out all the triads in the 19-tone MOS with a 5-step generator,
13 major and 13 minor, which is Larry Hanson's kleismic 19 out of 34, and
which is the very scale that scores P = 62 at N = 19 in my sweep. He had
already counted, by hand and around 1993, the major and minor triads of
the scale my sweep ranks first, which is the same kind of quantity my
scorer counts, and I only found his page after the sweep had run. Per the archive rule I have reproduced none of those
pages here, only the citations.

## Briefly: the first strictly proper eikosany

One more result belongs here, and it runs the other way, because the
machine found something inside Erv's own family that I had not seen him
draw. LAT-MEL-001 had found that the canonical {1,3,5,7,9,11} eikosany
is not a constant structure and that no eikosany from odd seeds up to 15
is, so I conjectured that special seedings might be, and CS-EIK-001 ran
the exhaustive search over 6-subsets of the odds up to 31, which is 7488
true 20-tone eikosanies, and found 32 constant structures
([`cseik001.jsonl`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/cseik001.jsonl)).
The flagship is {1, 7, 9, 11, 15, 29}, the only one that is also strictly
proper, with a constant-structure margin of 7.63¢ and P = S = 21 against
the canonical eikosany's 57, so the harmonic cost of melodic order is
visible in a single pair of scales. Since strict propriety implies
constant structure by a known theorem, its honest headline is the first
strictly proper eikosany, and the literature check corrected the
epimorphy count to 18 of 32
([`cseik001_posthoc.json`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/blob/main/experiments/lattice/results/cseik001_posthoc.json)).
When I played it I wrote that it "feels the most melodic to me at the
eikosany level," and the same session produced a doctrine I now hold,
which is that we rarely play the whole eikosany and mostly play its
dekanies and hexanies, so the melodic score of a CPS should probably be a
distribution over its embedded subsets, with the number of gap classes
relative to N as the primary penalty and propriety alongside it. That
became SUBSET-MEL-001, which is queued. An equal-temperament phase
diagram is also at gate as PR #38, and I will not report on it until it
merges.

## What I make of this

Each of the three exhaustive searches landed on something Erv had done
by hand, because the 1975 template is tie-optimal, the 1975 addressing
trick is what the lattice offers whenever tones exceed degrees, and the
top of the noble-generator sweep is row 18 of his 1993 table. I take that
as evidence that his hand search was doing real optimization, and it
makes me want to treat his published designs as validation points for
whatever the machine proposes next.

I also want to be modest about what has been shown. Tie-optimal is a
statement about a ±1 neighborhood of 80 vals at N = 31, and one neighbor
tied, so it is optimality among plausible templates and it is a long way
from uniqueness. The bridge search stopped at N ≤ 22 and at one genus,
and its verdict moved with a single cent of ε, so the frozen scorers,
with their 2¢ tolerance and their within-an-octave span, are one
operationalization of "harmonic" and a different one could re-rank the
front. The nulls in MOS-LAT are nulls for five descriptors across 885
rows, and they tell me nothing about why the generator value is what
matters. The ear checks are one listener, me, and the eikosany audition
was a discovery listen rather than a blind one. And the archive index
covers about 53 pages read visually out of 5,889, so it is possible that
I found these coincidences because I went looking for them, and a fuller
read could turn up disagreements.

## Where do we go from here?

What is it about a generator's position on the circle that makes 317¢
hot and its neighbors cold? That is the question the two nulls leave me
with, and I want to attack it with generator arithmetic directly, through
continued-fraction digit statistics and cents-neighborhood structure and
the complement symmetry that showed up on every run. Alongside that,
SUBSET-MEL-001 needs a spec, because everything I now believe about CPS
melody lives at the subset level. BRIDGE-000b should reproduce Erv's 1980
version of D'Alessandro, the genus 3³·5·7·11² with 8 pigtails, and
BRIDGE-002 should try the eikosany itself as a bridge payload, and both
should tune by a tone-set minimax, because orwell's mixed-sign prime
errors cancel in compound tones while miracle's stack up to 6.86¢ on
105/64. And PARETO-001 can now be drawn, since both axes are scored and
D'Alessandro sits at one corner of it.

## An invitation: tell me where the machine is fooling me

The invitation from the first post stands, and I would add one thing to
it. If you know a place in Erv's papers where he chose differently from
what these searches would recommend, I want to know about it most of
all, because a disagreement between his hand and my machine would be a
better finding than any of the agreements above. Ideas and argument go to
[GitHub Discussions](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/discussions),
and concrete proposals and bugs go to
[Issues](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues). The
scales are exported as Scala `.scl` files under
[`experiments/lattice/results/scl/`](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/tree/main/experiments/lattice/results/scl),
so you can listen before you argue.

---

*Production note, as in the first post: the experiments, the code, and
the first drafts of documents like this one are produced by an AI agent
(Claude) operating inside the research loop. I set the questions, I
review every finding against the primary sources and my own ear, and no
measurement standard changes without my explicit approval. Whatever
mistakes survive that process are my responsibility.*
