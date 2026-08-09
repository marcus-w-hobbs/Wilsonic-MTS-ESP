# Findings — lattice module (dated, one paragraph each, linked to artifacts)

Findings promoted here from `experiments/lattice/LOG.md` once they are
receipt-backed. Same convention as `experiments/triads/FINDINGS.md`: each entry
is dated, one paragraph, and names the artifact under
`experiments/lattice/results/` that grounds it. Grade claims by receipt strength
(READ → SIMULATED → EXECUTED → BIT-EXACT), as in the triads verification ledger.

The contract and hypotheses (H-L1, H-L4a/b, etc.) live in
`experiments/lattice/SPEC.md`.

_No findings yet — melodic.py and LAT-MEL-001 are the first deliverables._

**2026-07-25 — The eikosany is not a constant structure; hexanies almost always are.** (EXECUTED; exact-rational post-hoc BIT-EXACT.) Machine check of H-L1 against `results/latmel001.jsonl` + `results/latmel001_posthoc.json`: the {1,3,5,7,9,11} eikosany has 32 interval-size classes that subtend two different step counts, as exact rational identities (9/8 at 3 and 4 steps; 22/21 and 21/20 at 1 and 2; …) — not tolerance artifacts (verdict identical at ε_CS from 0.5¢ down to 1e-6¢). No eikosany from odd seeds ≤ 15 is CS (0/29); hexanies are generically CS (66/70), and the only 4 failures all contain the composite 9 beside 3 or 15 — 9 = 3² manufactures the coincidences. Mechanism: the eikosany's best val ⟨20,32,46,56,70⟩ is weakly but never strictly monotone (13 tied pairs), and tied val degrees are precisely how one interval spans two step counts. Interpretation pending Marcus (G-007): Wilson's melodic claims for eikosanies likely live at the modulus/embedding level (22, 31), which is the BRIDGE premise — the bare CPS fails melodically exactly where the embedding program says it should.

**2026-07-25 — CPS vs MOS on the melodic axis: confirmed trade-off, with a twist.** (EXECUTED.) H-L2 against the same receipts: CPS scales are melodically deficient vs rank-1 controls at matched cardinality (hexany mean 3.94 gap classes, eikosany 9.86, vs exactly 2 for every true MOS; 81%/100% improper), yet the melodic axis discriminates *within* the CPS family where the harmonic P = S diagonal cannot (13/70 hexanies non-improper — 11 contain both 1 and 5; propriety violations 0..4). The twist: true MOS do NOT saturate propriety — it is generator-dependent, and the mos001 harmonic hot-spot generators (416.2¢, 571.6¢) produce uniformly IMPROPER MOS while the noble φ generator is uniformly strictly proper. First direct evidence in this harness that the harmonic and melodic axes pull against each other — exactly the tension PARETO-001 will map.
**2026-07-28 — SHADOW-001: the ε-recovery law of comma perturbation
(H-S1 kept).** [EXECUTED — `results/shadow001.jsonl`,
`results/shadow001_verdicts.json`] Replacing one CPS factor n with
2ᵏ·n ± 1 breaks exact triadic coincidences immediately and permanently:
across 277 variants of the 1-3-5-7 hexany and 1-3-5-7-9-11 eikosany
(scorer v1.1.0, exact path), 96/97 small-k variants drop strictly below
base and none recover by k=16 — exact counts settle to k-independent
floors set by which factor was hit (hexany 1/0/3/4, eikosany
22/18/27/32/25/41 for n=1/3/5/7/9/11; perturbing 3 kills every exact
hexany triad). On the tempered path (ε=2¢) recovery is discontinuous
and law-like: sustained recovery lands at the pre-registered
k* = min{k : 1200·log2(1+1/(2ᵏn)) < ε} in 16/20 position×sign configs
(19/20 inside ε), with n=1 recovering at exactly k=10 on both bases and
both signs. Surprise: 52 eikosany variants OVERSHOOT base tempered
(up to 69 vs 61) at displacements ~0.2–2¢ before decaying to base —
a shadow tone just inside scorer ε buys extra near-coincidences that
the exact tone cannot; the hexany never overshoots.

**2026-07-28 — SHADOW-001: ε_dedup is inert; tone-collapse is exact
lattice arithmetic (H-S2 refuted).** [EXECUTED —
`results/shadow001.jsonl`] The pre-registered dedup-snap prediction
(sharp k*, shifting 1 per doubling of ε_dedup) is false on these bases:
in all 279 rows the deduped tone count equals the exact tone count at
every ε_dedup ∈ {0.01, 0.1, 0.5, 2}¢, because the smallest pairwise
comma the whole sweep produces is 2.912¢ (595/594) — above the largest
dedup epsilon. Tone counts do collapse, but only by exact rational
collision at small k, identically at every epsilon: m=15 and m=33
(perturbing 1) and m=55 (perturbing 7) each merge two eikosany tone
pairs exactly (e.g. 15·3·7 = 5·7·9 = 315, 33·3·7 = 7·9·11 = 693,
55·1·3 = 3·5·11 = 165), giving 18-tone eikosanies. Perturbation also
mints new sub-20¢ commas from nothing (both base spectra are empty
below 20¢): 595/594, 561/560, 441/440, 352/351 head the list —
comma-perturbation as a comma FACTORY is the usable output here.

**2026-07-28 — SHADOW-001: connectivity beats pure novelty, without a
single counterexample (H-S3 kept).** [EXECUTED —
`results/shadow001.jsonl`, `results/shadow001_verdicts.json`] Over 57
matched ± pairs at the same (base, position, k) where one replacement is
a composite sharing primes with the surviving factors and the other is
prime, the sharing side wins exact P 11 times, ties 46, and NEVER loses
(one-sided sign test p = 2⁻¹¹ ≈ 0.0005). Flagship cases: hexany
15 vs 17 at k=4 — exact P 6 vs 2, with m=15=3·5 restoring the full
unperturbed count (6,6) at 111.7¢ displacement; and eikosany
385 = 5·7·11 vs prime 383 at (n=3, k=7) — exact P 24 vs 18, where
replacing 3 by 385/128 is literally a 385/384 displacement (4.503¢),
one of the three D'Alessandro kernel commas of BRIDGE-000. The effect
is exact-path only: the tempered ε=2 lens goes 13W/1T/18L (drowned by
the overshoot effect), so "connectivity beats pure novelty" is a
statement about exact coincidence structure, not about ε-blurred
counts. Auxiliary: P = S held in all 279 rows — CPS(n, n/2)
inversional symmetry is seed-value independent, as pre-registered.
**2026-07-28 — Noble-MOS cut-and-project round trip is exact iff the
conjugate is far enough away; the failure mode is a single extra tone, and
it is a murchana artifact, not a scale property.** (EXECUTED, exact
ℚ(√5) arithmetic end to end; `results/moslat001.json`, step1; runner
`moslat001.py`; scale ground truth `families/mos.py`, the Brun.cpp:269
zigzag.) Eigen-embedding lattice points (octaves a, generator-steps b) as
(physical a + b·g, internal a + b·g′): for nobles with |g − g′| > 1 —
1/φ (741.64¢) and [0;2,(1)*] (458.36¢) — the internal coordinate is
strictly monotone along the chain, and the Brun zigzag scale at EVERY
level 0–9 is exactly a window set (both the a-priori window derived from
the level's zigzag fraction and the internal-hull window; projections
match `mos_cents` at ≤ 1e-6¢). For nobles with |g − g′| < 1 —
[0;1,2,(1)*] (868.33¢) and [0;2,2,(1)*] (503.79¢) — the murchana-0 chain
segment [0, q) FAILS window-representability at exactly the tail levels
whose zigzag fraction lies above g (defect u = q·g − p < 0): the next
chain point b = q lands strictly inside the window (single intruder, zero
exclusions), so the tightest window admits exactly one extra tone,
frac(q·g). The pre-registered guess that failures would track
SEMICONVERGENT levels is REFUTED — both semiconvergent levels in the
corpus pass, and every failure is at a true CF convergent. At every
failing level a majority of shifted chain segments [b0, b0+q) ARE
window-representable (5, 15, 41, 109 of 2q+1 shifts, identical counts
across both generators — structural), so the cut-and-project picture holds
for the MOS up to transposition; what fails is the b = 0-anchored segment
the plugin's Brun construction uses. Practical corollary for BRIDGE work:
window-set machinery on noble MOS must either check |g − g′| > 1 or work
murchana-up-to-shift.

**2026-07-28 — H-M1 is NULL on the all-1s-tail corpus: no conjugate-
embedding descriptor beats raw generator value for predicting triad hot
spots.** (EXECUTED; `results/moslat001.json`, step2; frozen scorer v1.1.0,
ε = 2¢, max_span 1200¢; seed 20260725, 9999 stratified permutations.)
Corpus: 27 noble generators (all CF digit strings, digits ≤ 3, preamble
≤ 3, all-1s tail), 97 (generator, cardinality) rows at N ∈ [5, 22];
P = S on every row (anchored-scorer inversional symmetry, again). Hot
spots are real — P spans 0–62, topped by [0;3,1,3,(1)*] ≈ 317.17¢ (noble
minor third) with P = 62 at N = 19, then the noble fifth
[0;1,1,2,(1)*] ≈ 696.21¢ and its octave complement [0;2,2,(1)*] ≈ 503.79¢
tied at P = 51 (complement symmetry) — but no pre-registered descriptor
(conj_sep, window_width, spread, norm_spread) reaches |partial ρ| > 0.05
or p < 0.35 against the g01 baseline (ρ = −0.162, p = 0.350). The null is
informative about the CORPUS, not just the hypothesis: with an all-1s
tail the SPEC's spectral-gap descriptor is constant (φ², logged in the
receipt) and the rest are near-functions of (N, |g − g′|), so the
conjugate geometry barely varies. Discriminating H-M1 needs a mixed-tail
(metallic 2s/3s) corpus, where the hidden lattice genuinely differs;
reserved for a follow-up run.

**2026-07-28 — Constant-structure eikosanies exist, composites are necessary, and CS exceeds epimorphy.** (EXECUTED; CS criterion exact-rational.) CS-EIK-001 (`results/cseik001.jsonl`), exhaustive over 6-subsets of odds ≤ 31: 32 of 7488 true 20-tone eikosanies are exact constant structures (Marcus's G-007 conjecture confirmed), with CS margins up to 9.22¢; none has an all-prime seeding and every one contains a composite seed (necessity), while 8/32 refute the stronger claim that composite factors must be shared. The theoretical surprise: only 4/32 winners are epimorphic — 28 are constant structures admitting NO consistent val (v·mᵢ = i unsolvable in integers), so CS is strictly weaker than epimorphy on this family, and the val-tie mechanism from LAT-MEL-001 explains failure but not success. Flagship discovery **{1,7,9,11,15,29}**: the only winner that is also strictly proper — CS (margin 7.63¢), strictly proper, P = S = 21 — the first eikosany in the program that is melodically well-formed on every axis, at a measured harmonic cost (canonical eikosany P = 57). One seeding pair now brackets the melody⇄harmony frontier for CPS(6,3).

**2026-07-28 — Calibration of the CS-EIK-001 claims against the literature (correction).** (EXECUTED; sources en.xen.wiki/w/Constant_structure and /w/Detempering, read 2026-07-28.) Three adjustments, recorded before any external announcement: (1) the flagship's headline is "**the first strictly proper eikosany**" — strictly proper ⇒ CS is a known theorem, so {1,7,9,11,15,29}'s constant structure is a corollary, not an independent virtue; (2) epimorphy recomputed under the standard subgroup-val definition: **18/32 CS winners are epimorphic; 14/32 admit no val whatsoever** (`results/cseik001_posthoc.json`) — CS ⊋ epimorphic is known in the abstract from a minimal 3-tone example, so our contribution is prevalence and naturalness (twenty tones, inside Wilson's own family), not the inclusion itself; (3) 31/32 winners have linearly dependent step sets, consistent with the known theorem that CS with independent steps forces epimorphy — the CS eikosanies are CS *because of* comma relations among their steps, the structural bridge to BRIDGE-000/001.

**2026-07-29 — D'Alessandro reproduced exactly; the calibration standard exists.** (EXECUTED; construction and commas exact-rational; anchors eye-verified against dal.PDF figs 24/26–27 — `BRIDGE000_TRANSCRIPTION.md`.) Wilson's fig-24 D'Alessandro is reproduced in full from the template: 38 tones on a consecutive huygens chain −1..+36, seven collisions at degrees {0,5,10,13,18,23,28} realizing exactly {385/384 ×3, 2079/2048 ×2, 121/120 ×2}, meanpop lift giving 5 physical unisons (fig 26's own +/✻ legend). The Pareto calibration standard every BRIDGE candidate must beat: harmonic wealth P = S = 154, G = 28 with **all 15 embedded hexanies injectively addressed**, versus addressing cost of 7 collisions — the pigeonhole floor — at zero cents error. Receipts: `results/bridge000.json`.

**2026-07-29 — H-B1: Wilson's template is the tie-optimal val (kept as pre-registered).** (EXECUTED.) Over the ±1 val neighborhood at N = 31, Wilson's ⟨31,49,72,87,107⟩ hits the pigeonhole floor of 7 tie-pairs with zero triple-occupied degrees; no neighbor does better and the single tying neighbor (3→19\31) is tuning-nonsensical. The 1975 keyboard template is, by machine check, the optimal 31-degree addressing of the 38-tone set — Wilson hand-solved a discrete optimization problem, and the val-tie quantity that failed the bare eikosany (LAT-MEL-001), delimited the CS winners (CS-EIK-001), is precisely what his template minimizes.

**2026-07-29 — H-M1 is NULL again on a non-degenerate corpus: the
conjugate-geometry descriptor program is dead; triad hot spots live on the
generator value, not the hidden lattice.** (EXECUTED, exact ℚ(√d)
arithmetic; `results/moslat002.json`; runner `moslat002.py`, statistics
imported read-only from `moslat001.py` so the runs are comparable by
construction; frozen scorer v1.1.0, ε = 2¢; seed 20260725, 9999 stratified
permutations.) MOS-LAT-002 rebuilt the MOS-LAT-001 corpus with MIXED
periodic CF tails — all period-1/2 digit strings over {1,2,3} except the
all-1s tail; 216 distinct quadratic generators (exactly the predicted 27
per tail), 788 (g, N) rows at N ∈ [5, 22] — so the spectral gap |λ/λ′|,
CONSTANT (φ²) on the old corpus, now takes five values spanning 5.83–61.98,
conj_sep spans 0.0021–4.58, and the fields range over ℚ(√d),
d ∈ {2, 3, 5, 13, 15, 21}. The registered prediction (with genuine
conjugate-geometry variation at least one descriptor beats generator-value
binning) is REFUTED: no descriptor passes either prong of the verdict rule
(best: spectral_gap ρ = −0.064, p = 0.0635 vs baseline |ρ| = 0.071;
Holm-adjusted all ≥ 0.32; conj_sep/window_width/spread/norm_spread all
|ρ| ≤ 0.035, p ≥ 0.34). P = S on all 788 rows, again. The receipt's
post-hoc smoking gun (not registered): near-identical generator VALUES
from unrelated fields score identically — 351.40¢ in ℚ(√15) (gap 61.98)
vs 351.47¢ in ℚ(√2) (gap 5.83), both P = 45 at N = 17 — and the ~317¢
noble-minor-third region is hot under four different tails across both
corpora, while the corpus-max P = 64 sits at [0;1,3,2,(1,3)*] ≈ 924.66¢,
N = 22. Mechanism consistent with both nulls: at scorer ε = 2¢ the triad
count is a locally stable function of the generator's position on the
circle, while every conjugate-embedding descriptor is discontinuous in
that position — the descriptor cannot carry information the g01 rank
doesn't. Program consequence, as pre-registered: stop searching embedding
descriptors; organize the hot-spot landscape by generator arithmetic
directly (CF digit statistics, cents-neighborhood structure, complement
symmetry).

**2026-07-29 — BRIDGE-001: the MOS window, not tuning accuracy, is what blocks a faithful EG4 bridge at N ≤ 22 — and the best hosts miss full triad survival by exactly one cent.** (EXECUTED; `results/bridge001.jsonl` + `bridge001_summary.json`; 63 pre-registered 7-limit commas × ±1-patent vals at N ∈ 7..22 = 2205 (comma, val) pairs, 590 monotonicity rejections, zero commas fully killed.) H-B2 is REFUTED as pre-registered: no candidate is simultaneously injective on the 8 distinct tesseract tones (16 formal vertices; seed 1 pairs them two-to-one — the BRIDGE-000 convention), contained in an N-note MOS window at any anchor, and full-hexany-surviving at the frozen scorer's ε = 2¢. The two halves exist separately: addressing-only passers reach 0.204¢ max tone error with full survival (ennealimmal, 2401/2400 ∩ 4375/4374) but their generator counts blow the chain span past every N ≤ 22 window, while contained candidates — a front owned entirely by 225/224, as predicted — top out at hexany (3,3) at 2¢. The post-hoc ε-sweep resolves the gap: **miracle/blackjack (⟨21,33,49,59⟩, secor 116.588¢) recovers the full (6,6) at ε = 3¢, orwell-22 (⟨22,35,51,62⟩, 271.385¢, max tone error 2.727¢) at ε = 4¢** — the bridge exists, at the price of one extra cent of triad tolerance. Three structural bonuses: (1) 1026 candidates show degree collisions that are NOT pitch merges — same address, different pitch — so D'Alessandro's pitch-just/address-tempered regime iii emerges spontaneously in a machine search (best at 0.492¢, address-commas 16/15 and 21/20); (2) per-tone EG4 error is not the prime minimax — orwell's mixed-sign prime errors cancel in compound tones while miracle's sign-coherent errors triple up on 105/64 (6.86¢ ≈ 3 × its 2.43¢ minimax), motivating a tone-set-minimax tuning lens; (3) no front row contains the genus at anchor 0 — the MOS-LAT-001 murchana-anchor corollary is load-bearing in every successful embedding. Against the BRIDGE-000 standard the design space is two opposite corners with nothing between: Wilson's pitch-just corner (0¢, 7 collisions, 100% survival) versus the tempered-faithful corner (0 collisions, 2.7–6.9¢, survival from ε = 3–4¢).

**2026-08-09 — MUR-001: murchana rescue is minority-rule; monotonicity ⇔ murchana-free; the drift budget T = N·|g − g′| is the governing parameter — and murchana is harmonically free.** (EXECUTED, exact ℚ(√d) arithmetic; `results/mur001.jsonl` + `results/mur001_summary.json`, bit-identical across two runs; runner `mur001.py`; frozen scorer v1.1.0 and melodic v0.1.0 read-only.) Census of window-representability over every anchor b0 ∈ [−N, N] for all 885 (generator, N) rows of the MOS-LAT-001 ∪ MOS-LAT-002 corpus (243 generators, 20,019 anchor evaluations). Anchor-dependence enters ONLY through the cut-and-project machinery: the projected scale's interval structure is a transposition, and the pre-registered null rail held exactly (melodic triple anchor-invariant on every row, 0 violations) — moreover the anchored frozen triad count P is empirically anchor-invariant on all 885 rows at ε ∈ {2, 3}¢, so murchana costs nothing harmonically while deciding window-set structure. The MOS-LAT-001 "murchana rescue" does NOT generalize: 537/885 rows have no representable anchor at all (69/97 already in the noble corpus), and only 172 of 709 anchor-0 failures (24.3%) are rescued — rescue is governed by the drift budget T = N·|g − g′|, which separates zero-rescue from rescue-possible non-monotone rows at AUC 0.974 (empirical critical band T ∈ [0.75, 2.36]; T > 4 always rescues, monotone g′ ∉ (0,1) ⇒ every anchor works, and the fully-representable rows are exactly the 124 monotone rows). Representable-anchor sets are quasi-periodic, not intervals (200/202 non-contiguous; interior anchor-gaps take ≤ 3 distinct values on 295/299 rows, the 4 exceptions all showing {1,2,4,7} with 7 = 1+2+4 — union-of-Sturmian-occurrence structure). Direction surprise, post-hoc: CF-convergent levels are EASIER to rescue across the full sweep (mean ρ 0.116 vs 0.082) — the registered prediction was the reverse and came out NULL at p = 1.0 one-sided. Practical corollary sharpened from MOS-LAT-001: window-set machinery on generated scales should check g′ ∉ (0,1) first, then the T band; sweeping anchors is worth it only inside T ≳ 0.75, and no anchor sweep can save T ≲ 0.75.
