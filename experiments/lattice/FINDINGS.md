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

**2026-08-09 — ET-001: the cultural epsilon of 12-EDO is 14.86¢; power chords are real scorer objects at 1.955¢; and below ~0.1¢ the first-lock metric is numerology, not quality.** (EXECUTED; `results/et001.jsonl` + `et001_summary.json`; every lock threshold analytic AND confirmed by the frozen scorer at ±1e−6¢, 798 calls, receipts bit-identical across two runs.) The (N, ε) phase diagram of full N-EDO scales, N = 2..60, under frozen triads v1.1.0 (primary anchored convention — ε is a per-mean-condition CENTS deviation with the sep ≥ ε degeneracy guard, so a triple counts exactly on (dev, sep]; NOT the plugin's register-dependent linear 0.0005) and frozen melodic v0.1.0. Headlines: (1) 12-EDO first supports the full patent 4:5:6/10:12:15 pair at **ε = 14.8590¢** — Marcus's recalled 14.86 confirmed to 2 dp — while per-N cultural epsilons rank 34-EDO the culture-set champion (0.4359¢) ahead of 53 (1.367), 19 (3.039), 31 (3.890), 41 (6.116), 22 (8.781), 12 (14.859): meantone hosts buy major+minor at 3–4¢ where 12 needs ~15¢. (2) The scorer's octave-span limit is inclusive, so 2:3:4 power chords are scored: 12-EDO's true first proportional lock is the power chord at **1.9550¢ = exactly its fifth error** (the identity is exact for every N). (3) The naive "champions lock first by fifth error" ranking [53, 41, 29, 58, 12] is REFUTED: the measured top 5 is [50, 41, 49, 39, 53], led by accidental near-exact arithmetic-progression chords in the teens limit (50-EDO hits ≈15:17:19 at 0.0085¢; 41's rank 2 is an accidental (22,16), not its famous fifth; 53 is the only top-5 lock that IS a fifth), and an un-guardable symmetric-cluster family (dev = sep/2 exactly, ∝1/N²; C♯–D–D♯ is "proportional" in 12-EDO for ε ∈ (2.887, 5.773]) floors the metric near 0.1¢ at large N — so first-lock ε is a coincidence detector below ~0.1¢ and the ε-grid count tables {1,2,3,5,10,14.86,20}¢ are the robust cross-N lens (joinable by ET-002/EAR-ε). Rails all held: P = S exactly everywhere (anchored self-duality on inversionally-symmetric scales), G = N·⌊N/2⌋ at ε→0, and every N-EDO is melodically trivial as predicted (strictly proper, CS, 1 gap class, 0 bits) — equal temperaments sit at the degenerate-melody corner of the program's Pareto axes with per-row receipts to join against.

**2026-08-18 — ET-002: the 351-subset census of 12-EDO — the frozen scorers' entire harmonic picture of 12-EDO below 20¢ is five patterns, the diatonic wins the seven-note class uniquely (but not on raw triad count), 80% of subsets are improper, and jazz's bebop scales top the eight-note frontier.** (EXECUTED; `results/et002.jsonl` + `et002_summary.json`; 351 T-classes × 7 ε = 2457 frozen-scorer calls, every P/S/G value AND every melodic value confirmed against an independent integer mirror, receipts bit-identical across two runs; pre-registration LOG 2026-08-18.) Because every 12-EDO subset triple is one of ET-001's 12-EDO types, the census's harmonic side at the grid {1,2,3,5,10,14.86,20}¢ is entirely combinatorial and now on receipt: P@1 = 0 for all 351 classes; **P@2 = S@2 = ic5** (the 2:3:4 power chord is the only living type at 2¢, so 321 fifth-bearing classes score and 30 fifth-free ones do not); the guard-window chromatic cluster adds exactly six fifth-free cluster classes at 3–5¢ and then exits (105 classes have P@10 < P@5 — the ET-001 cluster floor census-wide); the second-inversion major (3:4:5-type, 7.84¢) arrives at 10¢ and root-position major plus the whole-tone trichord at 14.86¢, so **P@14.86 = ic5 + 2·Maj + WT3, S@14.86 = ic5 + 2·Min + WT3** for every class — each major triad counted at its third and its fifth, never in first inversion — and Maj = P@10 − P@2, Min = S@10 − S@2 are readable off the frozen grid. Headlines: (1) H-T1 kept: the cultural epsilon is inherited by every subset; balance buckets at 14.86¢ are diagonal 231 / skew 31+31 / strong 28+28 / near 1+1, P = S in all 351 classes for ε ≤ 5¢. (2) H-T2 kept in the scorer's sense: the diatonic (proper, not strict; NOT CS — tritone at 3 and 4 steps) scores P = S = [0,6,6,6,9,15,15] and is the UNIQUE 7-note maximum of P+S (30), P and S (15), zero ties — but the literal "most major+minor triads" claim is refuted as pre-registered: two hexatonic-plus-one heptads carry 7 triads to the diatonic's 6, and the diatonic wins only because it also holds the 7-note maximum of fifths (ic5 = 6) and three whole-tone trichords. (3) H-T3 kept: strictly proper 23 (6.6%), proper 46 (13.1%), improper 282 (80.3%), CS 51 (14.5%); the pentatonic is the only strictly proper pentad, no heptad is strictly proper, and the 23 strictly proper classes are exactly the pre-registered list (dyads, sus/major/minor/augmented trichords, seven tetrads, pentatonic, hexatonic, whole-tone, octatonic, chromatic); max gap_classes/N = 1.0 for the 32 distinct-gap classes (N ≤ 4). (4) H-T4 kept: the per-N (gap classes ↓, P+S@14.86 ↑) frontier has 24 members — diatonic, pentatonic, whole-tone, hexatonic, Guidonian hexachord (tops N=6), Messiaen 3 (tops N=9), chromatic, sus trichord, augmented triad, diminished seventh — with the major and minor triads and the octatonic NOT on it and six improper classes ON it (reported, not zeroed). Post-hoc: the N=8 frontier winner is the bebop dominant (C D E F G A B♭ B, P=S=19, improper) and the only proper diatonic superset is the bebop major (P=S=17, top of the proper-only frontier at N=8, second only to the diatonic in (P+S)/N among proper 5–8-note classes); the strong_P bucket is led by the fourth-chained major-triad hexachord (0,1,3,5,8,9) at (10,6). Archive context: Wilson's "Some Basic Patterns Underlying Genus 12 & 17" (`2010_02_24B/12&17/BasicPttnsGenus12&17.pdf` pp.1–3, ©1980) frames 12 as the diatonic modulated through six keys — the census confirms, under the frozen scorers, that of 351 subsets the diatonic is the class the 12-tone genus is built to distinguish, and says exactly why (fifths + triads + stepwise thirds, not triads alone).

**2026-08-19 — ET-003: the comma-kernel history of 12-EDO — the walk into V12's kernel is measurable stage by stage: Pythagorean tuning already had sub-2¢ schismatic triads, meantone's first lock is septimal and sub-cent, Werckmeister III has a handedness and a 0.25¢ C major, and 12-EDO wins only at its own 14.86¢ epsilon (by one triple).** (EXECUTED; `results/et003.jsonl` + `et003_summary.json`; four historical lifts of the SAME 11-limit patent val ⟨12,19,28,34,42⟩ — Pythagorean −5..+6, quarter-comma meantone −5..+6, Werckmeister III 1691, 12-EDO — under frozen triads v1.1.0 and melodic v0.1.0; every grid value and all 130 lock thresholds scorer-verified at ±1e−6¢, zero mirror failures; receipts bit-identical across two runs; pre-registration LOG 2026-08-19, all five hypotheses KEPT.) The kernel census: V12's 5-limit kernel inside the registered box is exactly the (81/80)^a(128/125)^b lattice — 5 members, with monzo(81/80) × monzo(128/125) = −⟨12,19,28⟩ as an integer identity — 29 members at the 7-limit, 122 at the 11-limit; 33/32 and 121/120 are NOT members (V12 maps both to one step), so the D'Alessandro commas do not transfer to 12. The harmonic walk, all scorer-refereed: Pythagorean-12 tops the P column at ε ≤ 2¢ (11 pure-fifth power chords at dev 0; root-position schismatic majors at EXACTLY the schisma 1.9537¢, root-position ditone majors at EXACTLY the syntonic comma 21.5063¢ — the kernel commas are literally visible as triadic deviations); meantone tops it at 5–10¢ (root 4:5:6 at 3.22¢) and its FIRST lock is the septimal 6:7:8 at 0.7394¢, bought by 225/224 and 126/125 ((75/64)/(7/6) and (144/125)/(8/7), exact); 12-EDO tops it only at ε ≥ 14.86¢ and then by a single triple over meantone (48 vs 47). Attribution held exactly: 81/80 alone buys only 8 of 12 major-triad addresses in a 12-note chain (the wrapped thirds are dim4 = 32/25, off 5/4 by exactly the untempered 128/125), 128/125 buys the other 4 plus the 12th fifth, and the 7-limit kernel members buy NOTHING in 12-EDO at ε ≤ 20¢ — equal temperament forecloses the sub-cent septimal door meantone had opened (P@1: 2 → 0). The melodic side refutes the monotone story as pre-registered: all four stages are strictly proper constant structures, and gap classes run 2 → 2 → 4 → 1 (entropy 0.98 → 0.98 → 1.92 → 0 bits) — history's melodic complexity is a hump peaking at the well-temperament, not a descent, and propriety was never traded. Werckmeister III is the only stage where P ≠ S (its fifth word TTTPPTPPPPPP is chirally asymmetric; (P,S) = (10,9) at 1–2¢, (18,19) at 5¢, (48,46) at 20¢) and its per-root best-voicing major devs are the 1691 key-color doctrine as a number: C 0.2516¢ (31× closer to exact proportionality than any 12-EDO voicing) up through C♯/F♯/G♯ at 13.4727¢ = 1200·log₂(129/128) exactly — every key under the cultural epsilon, no two key groups alike, which is precisely "every key usable, no key identical". At ε = 5¢ the coverage ordering is meantone 8 > Werckmeister 4 > Pythagorean 3 > 12-EDO 0: at tight tolerance the endpoint of the walk is the WORST major-triad machine of its own history. Archive context: Wilson draws 12-Equal as one point of the meantone continuum in `2010_02_24B/12&17/BasicPttnsGenus12&17.pdf` p.2 (©1980) — ET-003 is that picture measured, with the well-temperament as the off-continuum detour.
