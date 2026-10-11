# Lattice MOS-Fit Playground — feedback round 1

Date: October 11, 2026. Audience: microtonal musicians familiar with MOS and CPS.

Status: source review and provisional teaching plan only. No film, storyboard commitment, research sweep or paid model call. The original HTML and research checkout were not changed. Instructions embedded in the artifact were treated as content.

## The explanation I would build

The central question is **what should a melodic chain preserve when it carries a harmonic lattice?** The research becomes compelling when the audience can see that different answers to that question select different tunings.

Start with one hexany and the two 22-note fits in the saved research results, before discussing the full search machinery. The generator changes by only 0.121587 cents, but the error pattern changes enough to recover two original triads under the chosen 2-cent test.

| Fixed hexany, N = 22 | Tone-minimax fit | Worst-triad fit |
| --- | ---: | ---: |
| Generator | 193.786723¢ | 193.908310¢ |
| Largest tone error | 1.367438¢ | 2.218549¢ |
| Largest original-triad deviation | 2.080065¢ | 1.156108¢ |
| Original triads within 2¢ | 10 / 12 | 12 / 12 |
| Generator mapping of 3, 5, 7 | (16, 2, 5) | (16, 2, 5) |

These are generator chains; the selected N = 22 example has **three step sizes**. It must not be introduced as a two-step MOS. Marcus explicitly chose to keep whether non-MOS chains are valid outcomes as an open research question. The presentation must preserve that uncertainty rather than select a winner.

A useful close-up is the original proportional triad `7/8 : 35/32 : 21/16`. Its middle tone is the arithmetic mean of the other two before fitting. After fitting, its deviation changes from 2.080065¢ to 1.156108¢. The corresponding recovered subcontrary example is `5/4 : 3/2 : 15/8`. Both values were reproduced from the stored ratios and generator mapping; see `numerical-evidence.json`.

Provisional audience journey:

1. **Pose a musical choice.** Show the same six target tones inside two chains. Let the viewer predict whether the closer tone fit must preserve more original triads.
2. **Make preservation concrete.** Follow one named triad through the mapping. Introduce the precise P/S condition and its error measure, even for an audience that already knows CPS.
3. **Reveal the tradeoff.** Show which two triads cross the 2¢ boundary, while one tone moves farther from its just target. Treat the boundary as a declared criterion, not a perceptual cliff.
4. **Open the search space.** Explain generator, finite chain window, note count and MOS eligibility. Show the staircase only after the audience knows which quantity is minimized.
5. **Return to musical judgment.** Separate original-triad survival, newly created triads, melodic structure and listening. The evidence supports different numerical objectives; the pending ear checks have not selected a preferred sound.

Keep golden/silver families and complementary-CPS inversion as later investigations or separate pieces unless Marcus chooses one as the central subject. Each deserves more explanation than a quick concluding montage.

## Source feedback — address before a film brief is locked

### R1 — “Triads kept” currently counts a different quantity

**Status: confirmed from code, browser and saved results. Priority: essential.**

The `imageTriads` function re-counts all qualifying P/S triads in the fitted image. It does not retain the identity of the exact source triads. Nevertheless, the selected-chain card says “triads kept … (of exact),” and the background says “The page reports the lattice's count.” Those statements are not true for all inputs.

Reproduction in the unmodified preview: choose the `1·3·5·7·9` dekany, enter generator **503.9386743166747¢**, and select **N = 18**, window start **−17** (1/1 at position 17), tolerance **2¢**. The card reports **9 / 6**, or **15**, under “triads kept.” The CPSFIT-003 receipt for that same prior worst-triad fit records **12 original survivors** and **15 total image triads**. Three newly created triads account for the difference.

**Requested source improvement:** give original survivors and newly created/total image triads separate identities, labels and values. Use the same definition in tables, comparisons, charts and the copied handoff. A total image count alone must not certify preservation of the original triads. Preserve any distinctness/degeneracy rules of the frozen referee.

**Acceptance example:** this case shows 12 original survivors and 15 total image triads without calling all 15 survivors. Attach a receipt for each metric.

### R2 — Decide whether the destination is MOS or general generator chains

**Status: confirmed source behavior; Marcus has chosen to keep the musical scope open. Priority: essential.**

The title and opening promise MOS scales, while the default free search admits arbitrary chain sizes and many central results are three-step chains. The source does disclose this later, but the audience's initial expectation differs from the problem actually solved.

Also, `runFit` finds one unrestricted tone-minimax winner per N. The “only MOS” option filters those winners afterward. It does not rerun the search to find the best MOS at that N. A non-MOS unrestricted winner being hidden does not establish that no acceptable MOS exists at that N.

**Requested source improvement:** distinguish “best chain” from “best MOS,” and state whether the checkbox merely filters returned winners. Present unrestricted chains and MOS as explicitly different candidates in the open research question. If making a claim about the best MOS, supply a genuinely MOS-constrained result. Do not infer MOS infeasibility from the absence of a displayed winner.

**Acceptance:** a viewer can state the admissible scale family and optimization objective before reading a result.

### R3 — Rational generators do not stop at closure

**Status: reproduced in browser. Priority: essential for ET comparisons.**

Select the built-in **12-ET fifth, 700¢**. “MOS sizes ≤ 60” displays **2 3 5 7 12 17 29 41 53**. Past closure, the table reports a zero small step and `Infinity` for L:s. The chain has repeated pitch classes, not 17 or more distinct notes. `mosPath` does not terminate on reaching the rational generator.

**Requested source improvement:** handle rational closure and floating-point comparisons explicitly; distinguish generator positions from distinct pitch classes throughout counts, classification and Scala export.

**Acceptance:** the 700¢ chain closes at 12 distinct notes, does not invent additional distinct-note MOS levels beyond closure, and exports a consistent scale.

### R4 — A source handoff can silently contain stale results

**Status: reproduced in browser. Priority: essential for a reliable feedback loop.**

Choose the dekany and run the equal-temperament family search. Then switch the lattice to Ptolemy. The family table retains rows such as **3/10 captured** even though the active lattice has seven tones. The generated handoff continues to describe family-search results under the current lattice heading. Code inspection also shows that tolerance, maximum N, family selection and pinned comparisons do not consistently invalidate or recompute every affected result.

**Requested source improvement:** bind each result to the lattice, tolerance, search bounds, objective and precision used to compute it. On a relevant input change, recompute or mark it stale and omit it from the current handoff. Keep pinned comparisons self-contained if comparing different input states is intentional.

**Acceptance:** switching lattices cannot produce a handoff that describes old results as findings for the new lattice. The state export contains sufficient information to reproduce each included result.

### R5 — Make the reflection operations explicit

**Status: identities verified numerically; prose conflates operations. Priority: resolve before teaching inversion.**

Write a chain as `C(g,s,N) = {(s+j)g mod 1200 : j=0,…,N−1}`. Then:

- Complement g, keep s: `C(1200−g,s,N) = −C(g,s,N)`.
- Keep g, mirror s: `C(g,−s−N+1,N) = −C(g,s,N)`.
- Complement g AND mirror s: `C(1200−g,−s−N+1,N) = C(g,s,N)`.

The page's wording sometimes combines complementing the generator, reflecting the lattice and mirroring the murchana without making clear which operation is applied to which object. The N = 22 example reproduced these identities to floating-point precision. The exact-reflection versus transposed-complementary-CPS distinction in CPSFIT-003 should remain intact.

**Requested source improvement:** add one labeled diagram or explicit correspondence specifying g, s, lattice reflection and any transposition. Also call 1/1 a fixed reference where appropriate: the default hexany's six target ratios do not themselves include 1/1.

### R6 — Tighten the claims that frame numerical evidence

**Status: source text issues and evidence gaps. Priority: before narration.**

- The tolerance note says “2 cents is below … 1.96 cents.” It is above it. Say approximately the 12-ET fifth's error, and name the interval rather than calling this generally “as good as 12-ET.”
- The note under the fixed-generator table describes a globally optimized generator, although this table holds station 2's generator fixed. Make each table's variable and fixed quantities explicit.
- “Exact” needs a declared numerical meaning. The JavaScript uses finite bisection and local refinement. Provide precision and a reference-result check, and distinguish a complete search model from an exact-real answer. This review did not prove the optimizer's global correctness.
- Claims that recurrence generators sit near noble generators need the seed-denominator bound and an appropriate baseline before proximity is presented as a general relationship. Retain them as bounded observations if that comparison has not been done.
- Clarify “at a large N where the chain's commas vanish.” Distinguish small target approximation errors from exact harmonic relations and from which commas a specified mapping tempers out. Increasing N alone should not be presented as proof of an exact embedding.
- Keep the pending listening decisions visible. Gates G-029, G-031 and G-032 remain pending in the research checkout. Do not turn “more original triads satisfy this test” into “this tuning sounds better.”

## The feedback loop

**Round 1 — this review:** resolve metric identity, MOS scope, rational closure and stale handoffs first. No need to settle every open research question to repair those parts of the source.

**Round 2 — Marcus supplies a revised artifact:** compare against this saved revision; rerun the bounded examples above; record each item as fixed, clarified, deferred or open. Re-evaluate changed claims against their actual receipts. Do not silently modify the source during review.

**Round 3 — an explanation rehearsal:** produce a short text treatment and a still-image storyboard only when requested. For every beat, record the intended audience inference and the evidence needed. Marcus can correct the conceptual framing before any production run.

**Production readiness:** one agreed subject, unambiguous objectives and counts, a reproducible example, source-backed numbers and clearly labeled open/listening questions. Film generation starts only when Marcus asks for it.

## Evidence and limits

- Reviewed HTML: `playground.html`, an unchanged copy of `<original download>/Lattice MOS-Fit Playground.html`.
- HTML SHA-256: `20e9e932480dc751ca9ed5812a44033444bf40bad322c9318ea18c4001046464`.
- Research checkout: `<Wilsonic checkout>`, commit `3e3cf91cbd1bf5add95801b0be8c6840f8648683`.
- Principal receipt: `experiments/lattice/results/cpsfit003.jsonl`, SHA-256 `3f6c5d743bfcbc059cf3a0029ae7d204d4e33319e4bee817c53c1800f77852b6`.
- Numerical examples and bounded reproduction: `numerical-evidence.json`.
- Browser evidence: `initial.png`, `dekany-count.png`.
- Source anchors in the copied HTML: introduction 144; tolerance note 233; fixed-table note 270; background 289–300; triad count 390–403 and 756–765; scale-tree traversal 404–422; free optimization/filtering 963–990; handoff and invalidation 993–1040; mirror display 908–912.

This review examines the source's teaching argument, selected behavior and consistency with existing results. It is not an exhaustive optimizer audit, a proof of the research claims or a listening evaluation. No manuscript or website publication was performed.
