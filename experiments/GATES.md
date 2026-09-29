# GATES.md — the approver's ledger

Single source of truth for **Marcus's decision queue** across all experiment
modules (triads, lattice, and future siblings). The dashboard artifact renders
this file; sessions read it at start-up to know what is and isn't authorized.

## Protocol

- **Sessions append gates; only Marcus flips status.** A session that reaches a
  decision point adds a `PENDING` row with evidence links and stops there. No
  session ever marks its own gate `PASS`/`FAIL`.
- **To decide, use any ONE of:**
  1. Tell any Claude session: `G-NNN pass` or `G-NNN fail — <reason>`. The
     session updates this file, records the dated call in the module's LOG.md
     (existing convention), and executes the consequence.
  2. Merge or close the linked PR on GitHub. Merging a PR **implies passing**
     every gate attached to it; the next session back-fills this ledger.
  3. Edit this file directly and push; sessions treat your edit as the decision.
- **Statuses:** `PENDING` (waiting on Marcus — the loop is stopped here),
  `QUEUED` (will become PENDING when its prerequisites land), `PASS`, `FAIL`
  (both dated, with notes).
- Ear checks are standing gates: any `.scl` export offered for listening is
  implicitly PENDING until Marcus reports back.

## Ledger

| ID | Opened | Gate | Status |
|----|--------|------|--------|
| G-001 | 2026-07-20 | Sampling convention: anchored vs window as primary | PASS 2026-07-21 — anchored primary (self-dual + transposition-invariant); window retained for comparison |
| G-002 | 2026-07-21 | Ear check of triad classifier + aggregator | PASS 2026-07-21 (classifier); FAIL (aggregator) — min(P,S) rejected as ranking; balance buckets are the reporting contract |
| G-003 | 2026-07-21 | Scorer v1.1.0 unfreeze/refreeze: octave span limit | PASS 2026-07-21 — max_span = 2/1; hash re-pinned |
| G-004 | 2026-07-22 | BRIDGE scope: EG4 before EG6 | PASS 2026-07-22 — EG4 first; eikosany becomes BRIDGE-002 |
| G-005 | 2026-07-25 | Merge [PR #19](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/19): melodic.py v0.1.0 + tests, incl. two SPEC-parenthetical corrections (12-EDO diatonic not CS; Pythagorean 12 strictly proper / Pyth-7 is the improper fixture) | PASS 2026-07-25 — merged by Marcus (merge implies pass) |
| G-006 | 2026-07-25 | LAT-MEL-001 review: do M1–M3 rank scales the way your ear does? PASS triggers melodic.py freeze (hash-pin at v0.1.x) | PASS 2026-07-28 — blind ear check 8/8; melodic.py frozen v0.1.0, pin a16f162b |
| G-007 | 2026-07-25 | H-L1 verdict interpretation: eikosany CS or not — what it means for the claim attributed to Wilson | PASS 2026-07-28 with amendment — generically not CS accepted; conjecture that special seedings could be CS spawned CS-EIK-001 (confirmed: 32 exist); CS elevated as first-class axis for aggregator design |
| G-011 | 2026-07-25 | Merge [PR #22](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/22): scripts/status.sh — one-command research status (chore lane) | PASS 2026-07-28 — merged (with #23, #25, #26, #27) |
| G-012 | 2026-07-28 | CS-EIK-001 review: 32 CS eikosanies found (P1 kept, P2 refined, P3 refuted at corrected 14/32); ear-check the flagship {1,7,9,11,15,29} (first strictly proper eikosany); merge its PRs | PASS 2026-07-29 — PRs #28/#29 merged; G-012 audition complete (flagship "most melodic at the eikosany level"); insights logged: subset-first doctrine + gap_classes/N ∧ propriety |
| G-013 | 2026-07-29 | SUBSET-MEL-001 spec review (after the subset brainstorm session Marcus requested): melodic scoring over embedded subset CPS | QUEUED (needs brainstorm output) |
| G-014 | 2026-07-29 | BRIDGE-000 review: D'Alessandro reproduced exactly (7 collisions, comma census matches fig 24); Pareto calibration standard on record; H-B1 KEPT — Wilson's val is tie-optimal. Merge its PR | PASS 2026-07-29 — Marcus, via chat + merge of PR #31; BRIDGE-001 (EG4) unblocked |
| G-015 | 2026-07-29 | MOS-LAT-002 review (mixed-tail H-M1 retest, agent running) | PASS 2026-07-30 — [PR #33](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/33) merged by Marcus (merge implies pass); H-M1 NULL again, conjugate-descriptor program closed |
| G-016 | 2026-07-29 | BRIDGE-001 review (EG4 CPS-inside-MOS, agent running): candidates vs the D'Alessandro Pareto standard | PASS 2026-07-30 — [PR #34](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/34) merged by Marcus (merge implies pass); H-B2 refuted under strict containment, bridge exists at ε = 3¢ (blackjack) |
| G-008 | 2026-07-25 | Merge [PR #20](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/20): CI runs the lattice test suite (chore lane) | PASS 2026-07-25 — merged by Marcus |
| G-009 | 2026-07-25 | Merge [PR #21](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/21): research blog post 001 "The Tunings That Ring" + README pointer — editorial pass is yours (first-person voice) | PASS 2026-07-25 — merged by Marcus |
| G-010 | 2026-07-25 | Merge [PR #18](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/18): worktree.sh dead-cwd fix (chore lane, pre-existing) | PASS 2026-07-25 — merged by Marcus |
| G-017 | 2026-08-09 | ET-001 review: (N, ε) phase diagram of equal temperaments under the frozen scorers | PENDING — cultural epsilon confirmed at 14.86¢ (12-EDO 4:5:6 locks at 14.859¢), power chords lock at the fifth error (1.955¢), naive first-lock ranking refuted by accidental AP-chord locks; [PR #38](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/38) |
| G-018 | 2026-08-09 | MUR-001 review: murchana window-regularity census | PENDING — rescue is minority-rule (172/709 anchor-0 failures rescued; 537/885 zero-rescue rows), monotone ⇔ murchana-free, drift budget T = N·|g−g′| separates at AUC 0.974, murchana harmonically free (triad P anchor-invariant on all rows); [PR #39](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/39) |
| G-019 | 2026-08-18 | ET-002 review: the 351-class subset census of 12-EDO under the frozen scorers (stacked on ET-001) | PENDING — H-T1..H-T4 kept (raw-triad half of H-T2 refuted as pre-registered): diatonic is the unique 7-note P+S max via fifths + triads + WT3 (not raw triad count); 80% of subsets improper, 23 strictly proper; bebop dominant tops N=8 on the frontier; [PR #44](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/44) (stacked on #38) |
| G-020 | 2026-08-18 | MUR-002 review: grāma/mūrchanā calibration against Wilson's LatticingRagaScales (archive, read in place, page-cited) | PENDING — Wilson draws ragas on Hanson's 1942 53-lattice, not a 22-śruti lattice; the 22-śruti set = a chain of 22 fifths mod the schisma (Pyth 22/22 within 2¢, 53-EDO 22/22, orwell-22 only 10/22); Bilawal = ṣaḍja@Ni, Khamaj = ṣaḍja@Ma exact; grāma comma shift GAINS triads (11,7)→(13,10); CS steps at the schisma. Decide (a) the fifth-chain reading, (b) commission M4 tonic-anchored score + blind mūrchanā ear check; [PR #45](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/45) (stacked on #39) |
| G-021 | 2026-08-18 | BRIDGE-001b review: filtered EG4 bridge design (k₂ sweep, tone-set minimax, two-gap objective) | PENDING — rail reproduces BRIDGE-001 bit-for-bit; H-B2 NOT revived under any tuning (the one-cent gap is structural at N≤22); tone-set minimax: miracle 6.858→5.817¢, orwell 2.727→2.571¢ and 4/6 hexany faces at 2¢ — in-budget front = orwell-22 alone; magic/garibaldi appear exactly as predicted (dominated/uncontained); count-based survival unsound above ~13¢ → identity lens (post-hoc). Decide: in-budget/identity reading as the BRIDGE-002 front rule; [PR #46](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/46) |
| G-022 | 2026-08-18 | SUBSET-MEL-000 review: machine census of the 72 embedded CPS subsets of the eikosany — data for the G-013 brainstorm, not the spec | PENDING — IN/OUT dekanies are exact inversion pairs (36 classes, not 72); 0/60 dekanies proper or CS across 5 seeds (even the strictly-proper flagship); frozen M1–M3 nearly blind at the dekany level (22/30 classes share one fingerprint); hexany propriety inverts vs eikosany level; rankings disagree where they discriminate (pooled ρ = −0.28). Ear-check the 21 .scl (results/scl/subsetmel000/, esp. the 1-3-5-7-9 dekany as named spice); [PR #43](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/43) |
| G-023 | 2026-08-18 | Blog post 002 editorial pass ("the machine keeps deriving Wilson") — first-person voice per the site writing-style rule | PENDING — draft docs/research-blog-002.md, three receipt-backed episodes (BRIDGE-000 tie-optimal val, BRIDGE-001 blackjack@3¢ + spontaneous regime iii, MOS-LAT double null → GoldenGenerators #18); self-audit removed 6 punchline sentences, 0 em-dash snaps; GoldenGenerators attributed to Erv 1993 per INDEX.md (check); [PR #42](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/42) |
| G-024 | 2026-08-19 | ET-003 review: the comma-kernel history of 12-EDO (Pythagorean → meantone → Werckmeister III → 12-EDO under one val) | PENDING — H-K1..K5 all kept: 5-limit kernel = the (81/80,128/125) lattice exactly (saturation rail); 81/80 alone buys only 8/12 major addresses, 128/125 buys enharmonic closure, 7-limit commas buy nothing in 12-EDO ≤20¢; 12-EDO wins only at ≥14.86¢ and by ONE triple (48 vs W-III's 47); melodic walk is a hump (gap classes 2→2→4→1), monotonicity refuted as pre-registered; W-III key color C 0.25¢…C♯ 13.47¢ exact; [PR #49](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/49) (stacked #38→#44) |
| G-025 | 2026-08-19 | EAR-ε ear check: Marcus's lock-loss thresholds vs the cultural epsilon (44 blinded rungs, key sealed; decides P-E1/P-E2/P-E3) | PENDING — ladder + blinded protocol built ([PR #48](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/48), stacked on #38); YOUR ACTION: listen per EAREPS_PROTOCOL.md, save results/eareps_responses.json, then unseal the key; predictions committed: third lock-loss 6–12¢ < 14.86, fifth ≤3¢ (12-EDO fifth survives), sharp-tolerant ≥1.5¢ |

## Currently blocked by gates

- The SPEC's original queue is fully run and fully gated (LAT-MEL-001,
  SHADOW-001, MOS-LAT-001/002, CS-EIK-001, BRIDGE-000/001 — all PASS).
- Fork-menu wave 1 (2026-08-09): ET-001 and MUR-001 ran; G-017/G-018 are
  PENDING on Marcus (PRs #38/#39, CI green).
- Fork-menu wave 2 (2026-08-18, "continue auto research"): ET-002, MUR-002,
  BRIDGE-001b, SUBSET-MEL-000, blog post 002 all ran/drafted; G-019–G-023
  PENDING on Marcus (PRs #42–#46). #44 stacks on #38, #45 on #39.
- Wave 3 (2026-08-19, "run them"): ET-003 ran (PR #49, stacked #38→#44) and
  the EAR-ε ladder is built (PR #48, stacked on #38); G-024/G-025 PENDING.
  Chore PR #47 tracks the writing-style rule. Every gate G-017–G-025 now
  waits on Marcus; nothing is running.
- G-013 (SUBSET-MEL-001 spec review) still waits on the subset brainstorm
  with Marcus; SUBSET-MEL-000 supplies the ranked table for him to react to.
  (Datestamp erratum: entries above marked 2026-07-25 were written
  2026-07-28 — see LOG.md.)
