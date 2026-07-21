# Findings — dated, one paragraph each, linked to artifacts

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
