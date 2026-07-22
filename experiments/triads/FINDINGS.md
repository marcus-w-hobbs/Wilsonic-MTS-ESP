# Findings — dated, one paragraph each, linked to artifacts

**2026-07-21 — The P = S diagonal is structural for every
single-generator scale, and for CPS(n, k) with k = n/2.** All 29
eikosanies (including the {1,45,135,225,19,377} calibration set) and
every MOS at every generator/cardinality in the sweeps score P = S
exactly under the anchored convention (results/hex003_eik001.json,
results/mos001_coarse.jsonl). Reason: both families are inversionally
symmetric as pitch-class sets (a generator chain reversed is the same
set; CPS(n, n−k) is the inverted CPS(n, k) up to transposition), and the
anchored scorer commutes exactly with inversion. Consequence for the
research program: min(P, S) cannot DIFFERENTIATE within these families —
it equals P — so the interesting axes there are P itself, G, and triad
quality; P ≠ S can only distinguish asymmetric constructions (harmonic
segments, stellations, recurrence relations, arbitrary scales). This
sharpens plan §1.3's balance hypothesis into a theorem-shaped statement
worth proving formally.

**2026-07-21 — Tempered-path ε-degeneracy: near-equal-step scales
multi-count.** In the MOS sweep at ε = 2¢, a 1¢ generator tops
cardinalities 5–10 and ~599¢ (near 600 = 2-EDO multiple) tops N=15/17:
when adjacent steps are within a few ε, AM, GM, and HM of a triple
coincide inside ε, so the same triple counts as P, S, AND G, and
min(P,S) explodes for micro-cluster and near-equal-step scales
(mos001_coarse.jsonl: N=10 at g=1¢ scores 100 with G=117). Raw counts
stay honest in the archive; mos_report.py added a REPORT-layer guard
(exclude scales whose min step ≤ 4ε, factor printed).

**RESOLVED 2026-07-21 — the guard belongs in the scorer, and the right
invariant is per-triple, not per-scale.** Marcus's decision: a tempered
triple contributes to no count unless its own arithmetic and harmonic
means are distinguishable at ε, `|1200·log2(AM/HM)| ≥ ε`. Below that the
two mean conditions are one condition, so "proportional" asserts nothing
— the identical triple is equally "subcontrary". Equivalently a span
cutoff (58.8¢ at ε=0.5, 117.7¢ at ε=2, 186.1¢ at ε=5). Three weaker rules
were measured and rejected over the coarse sweep × 4 ε: discounting
also-geometric triples fails (narrow triples match P and S but not G
unless the middle happens to sit near the cents-midpoint); discounting
triples labelled both P and S fails at ε=0.5 on a knife edge (triple
0-2-3¢ has AM and HM 0.0013¢ apart, so one condition lands inside ε and
the other outside and it scores as a *pure* proportional); a min-step
guard is a scale-shape prior and under-filters. The stake was concrete:
unguarded, a 1¢ generator is the global optimum of min(P,S) at every
cardinality N=5–10 at every ε — the reward hack the frozen verifier
exists to prevent. The guard is a no-op on the exact rational path, so
every hexany/eikosany result stands unchanged. Re-ranked fine sweep:
LOG.md MOS-003. Residual honest limitation: cluster scales whose triples
DO resolve (six notes inside 150¢) still score; excluding those is a
scale-shape prior and belongs in the search/archive layer, not the
verifier.

**2026-07-21 — The analyzer silently discards every octave-wrapping triad
it finds.** First execution of the real `_analyzeProportionalTriads`
under test (tests/test_tuning) reported (1,2) for the 1-3-5-7 hexany
where the search loop provably finds (2,2). Cause, read and then
confirmed by prediction: the loop's wrap machinery (octave factors, j up
to npo+1) deliberately catches triads spanning the octave boundary, but
stored triads keep UNWRAPPED indices, and the post-loop NPO-map filter
(TuningImp.cpp:849–858) looks those up in a map keyed 0..npo-1 — so
every wrapped triad is dropped before reaching the UI lists. Half of the
hexany's reported majors and half the harmonic segment's (8→4)
disappear this way. The corrected mirror predicted hexany 1-3-5-9 =
(1,2) before the C++ test ran; confirmed, and then corpus-confirmed on
all 70 hexanies + 15 MOS scales with 0 mismatches
(results/crossval002.json). Wilson's proportional-triad concept has no
reason to exclude wrap triads, so this looks like a bug rather than a
choice; fixing it is a UI-visible behavior change and is Marcus's call —
the receipts here are the regression baseline either way.

**DECIDED 2026-07-21 — not fixing now (Marcus): no UI changes to Wilsonic
at this time.** Recorded as a known bug that is deliberately deferred, NOT
as intended behavior — the search loop's own wrap machinery (octave
factors, j to npo+1) exists precisely to find these triads, so the
original intent included them; only the post-loop NPO-map lookup discards
them. Additional reading done at decision time, which reduces the eventual
fix's risk: both UI consumers already handle unwrapped indices correctly,
because both convert degree → MIDI note (`nn60 + degree`) and go through
the 128-note tuning table rather than indexing the npo array — the
keyboard (WilsonicMidiKeyboardComponent+paint.cpp:176, which already
range-checks against numMidiNotes) and the pitch wheel
(TuningRendererComponent.cpp:165, via microtoneAtNoteNumber →
getPitchValue01, so an octave-up degree lands at the correct angle). So
whenever this is revisited, the change is contained to the filter
(map the pitch class `d % npo`, re-apply the octave offset) and touches no
rendering code. The 46 characterization checks in tests/test_tuning stay
as the regression baseline, and they now pin the buggy behavior
deliberately rather than incidentally.

**2026-07-20 — Every hexany sits exactly on the P = S diagonal (anchored
convention).** All 68 six-note hexanies from odd seeds ≤ 15 score P = S
*exactly* under middle-anchored scoring (results/hex001.jsonl, scorer
0.1.0, commit 277eb519). This is stronger than the plan §1.3 hypothesis
("CPS structures should sit NEAR the P = S diagonal") and is almost
certainly a theorem: a hexany is inversionally symmetric as a pitch-class
set (CPS(n,k) inverts to CPS(n,n−k) times a constant; for the hexany
k = n−k = 2), and the anchored scorer commutes exactly with inversion
(test_004b), so P = S follows structurally. The two-octave-window scorer
breaks this symmetry through its [1,4) boundary (e.g. 1-3-9-15 scores
(13,11) there vs (9,9) anchored) — which is evidence the window's P≠S
scatter for CPS is measurement noise, not signal. Worth proving formally;
also predicts eikosany (CPS(6,3), self-inverse) lands exactly on the
diagonal, testable in Phase 3.

**2026-07-20 — The plugin's triad badges understate scales' triad content
by ~4×, with a register-dependent tolerance.** Bit-exact mirroring of
`_analyzeProportionalTriads` (TuningImp.cpp:782–857) against the exact
scorer shows the analyzer reports (2,2) for the 1-3-5-7 hexany where the
true class counts are (8,8); zero of 70 hexanies agree
(results/crossval001.json, link2). Three causes, each now quantified: the
9/8–4/3 interval filter (by design — only compact triads get UI badges),
the one-octave+wrap search domain, and a tolerance of 0.0005 in absolute
linear frequency, which is 0.865¢ for triads rooted at 1/1 but only
0.433¢ near the octave — the plugin is twice as strict at the top of the
octave as the bottom, which nothing in the music theory motivates. None
of this affects the plugin's sound; it affects which triads get drawn.
If the C++ ever gets revised toward the exact scorer's semantics, the
receipt chain here is the regression baseline.

**2026-07-20 — 9-bearing seed sets outrank 1-3-5-7, via geometric
freebies.** The hexany sweep's top scorers are 1-3-5-9 and 1-3-9-15
(P=S=9, and G=4 each) vs 1-3-5-7's P=S=8, G=0. Seeds containing {1,3,9}
(a geometric progression) put products in geometric chains, which buys
both extra arithmetic coincidences and four geometric triads. The metric
currently ignores G in the loss; if the ear check (HEX-002, pending
Marcus) says 1-3-5-7 still sounds richer than 1-3-5-9, that is direct
felt-sense evidence about whether geometric-chain scales overcount as
"proportional-rich" — exactly the loss-function alignment question
Phase 1 exists to answer. Playable files: results/scl/hex_1-3-5-9.scl,
hex_1-3-9-15.scl, hex_1-3-5-7.scl.

**2026-07-21 — EAR CHECK PASSED: the classifier is validated, the
aggregator is not.** Marcus, on decades of listening: proportional and
subcontrary triads audibly "lock in", and the CPS sets this harness
surfaced are exactly the aesthetic he listens for. That validates the
things the scorer *measures* — the triad definitions, frequency-space
means, and the tolerance regime — which is the gate plan §HEX-002 set
before any agent loop was allowed to matter. It does NOT validate
min(P, S): asked directly, he wants P-heavy AND S-heavy AND G-heavy
scales equally, and a balance loss actively penalizes the first two. The
classic pentadekany at (70,27) scores 27 under min(P,S) and would lose to
a mediocre balanced scale at (30,30). Consequence: min(P,S) is demoted
from "the loss" to one lens among several; the MAP-Elites balance axis
(strong_P / skew_P / near_P / diagonal / near_S / …) becomes the
reporting contract, with per-bucket winners under min(P,S), P+S+G, P, S,
and G. Marcus's own eikosany {1,45,135,225,19,377} remains a puzzle: he
still loves it at 22 against the classic's 77, and has no alternative
axis to propose for it yet — the honest position is that both can be
true and the metric is incomplete rather than wrong. Counterweight worth
recording: he reports that MOS scales he likes have rarely scored badly
here, so the metric does track something real.

**2026-07-21 — Triads must fit within an octave (scorer v1.1.0).** Marcus:
1:2:3 is arithmetically proportional but spans an octave and a fifth, and
is not the sonority in question. The scorer now counts only triads whose
outer ratio c/a ≤ 2/1. Chosen over the plugin's other restriction — the
9/8..4/3 band on the third — because the span limit commutes with
inversion (c/a is untouched by it) while the band constrains only the
LOWER interval and therefore does not: measured, the self-inverse
eikosany scores (20,29) under the band, breaking a diagonal that is
structurally exact. That asymmetry is a third distinct defect in the
plugin analyzer, alongside the wrap-drop and the register-dependent
tolerance (issue #12). Verified for the span limit: exact self-duality (0
failures / 40 hexanies) and exact transposition invariance both survive.
Costs ~25-30% of counted triads and re-ranks materially — only 2/68
hexany positions keep their order, and 1-3-5-7 slips from 3rd to 4th
behind 1-3-7-9. Unexpected bonus: the span limit repairs the window
convention's duality failure for P and S (segment 8..16 now swaps exactly,
(36,6) → (6,36)); G still does not swap, and the window remains
non-transposition-invariant, so anchored stays primary.
