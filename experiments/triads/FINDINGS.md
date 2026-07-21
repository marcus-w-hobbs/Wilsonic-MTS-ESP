# Findings — dated, one paragraph each, linked to artifacts

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
