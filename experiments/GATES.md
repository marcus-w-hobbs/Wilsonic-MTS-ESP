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
| G-017 | 2026-08-09 | ET-001 review: (N, ε) phase diagram of equal temperaments under the frozen scorers | PASS 2026-09-29 — merged by Marcus (PR #38; merge implies pass); cultural epsilon confirmed at 14.859¢, power chords lock at the fifth error 1.955¢ |
| G-018 | 2026-08-09 | MUR-001 review: murchana window-regularity census | PASS 2026-09-29 — merged by Marcus (PR #39); murchana rescue minority-rule, monotone ⇔ murchana-free, drift budget AUC 0.974, murchana harmonically free |
| G-019 | 2026-08-18 | ET-002 review: the 351-class subset census of 12-EDO under the frozen scorers (stacked on ET-001) | PASS 2026-09-29 — merged by Marcus (PR #44); diatonic unique 7-note P+S champion via fifths + WT3, 80% of 12-EDO subsets improper, bebop dominant tops N=8 |
| G-020 | 2026-08-18 | MUR-002 review: grāma/mūrchanā calibration against Wilson's LatticingRagaScales (archive, read in place, page-cited) | PASS 2026-09-29 — merged by Marcus (PR #45); fifth-chain-mod-schisma reading of the 22-śruti set on record; M4 tonic-anchored proposal accepted as input (commissioning decision still open — see next steps) |
| G-021 | 2026-08-18 | BRIDGE-001b review: filtered EG4 bridge design (k₂ sweep, tone-set minimax, two-gap objective) | PASS 2026-09-29 — merged by Marcus (PR #46); H-B2 not revived under any tuning, in-budget front = orwell-22 alone, identity lens adopted for BRIDGE-002 |
| G-022 | 2026-08-18 | SUBSET-MEL-000 review: machine census of the 72 embedded CPS subsets of the eikosany — data for the G-013 brainstorm, not the spec | PASS 2026-09-29 — merged by Marcus (PR #43, via integration PR); 21 .scl on main under results/scl/subsetmel000/ — audition still open as a standing ear-check feeding the G-013 brainstorm |
| G-023 | 2026-08-18 | Blog post 002 editorial pass ("the machine keeps deriving Wilson") — first-person voice per the site writing-style rule | PASS 2026-09-29 — merged by Marcus (PR #42); post 002 live at docs/research-blog-002.md; editorial amendments remain his to push as a follow-up if wanted |
| G-024 | 2026-08-19 | ET-003 review: the comma-kernel history of 12-EDO (Pythagorean → meantone → Werckmeister III → 12-EDO under one val) | PASS 2026-09-29 — merged by Marcus (PR #49); 5-limit kernel = (81/80,128/125) lattice, 81/80 buys 8/12 addresses, 128/125 buys closure, melodic walk is a hump not a descent |
| G-025 | 2026-08-19 | EAR-ε ear check: Marcus's lock-loss thresholds vs the cultural epsilon (44 blinded rungs, key sealed; decides P-E1/P-E2/P-E3) | PENDING — ladder + blinded protocol built ([PR #48](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/48), stacked on #38); YOUR ACTION: listen per EAREPS_PROTOCOL.md, save results/eareps_responses.json, then unseal the key; predictions committed: third lock-loss 6–12¢ < 14.86, fifth ≤3¢ (12-EDO fifth survives), sharp-tolerant ≥1.5¢ |
| G-026 | 2026-09-29 | EPS-TIER-001 review: should a 12-ET-derived epsilon (ET5 14.86¢ / ET7 32.01¢) join LOCK 2¢ as reporting tiers? | PASS 2026-09-29 — Marcus chose (b) then (a): no tier above LOCK until G-025's lock-loss numbers are in; after that, adopt the loose tiers as report tiers only behind a collapse-within-ε filter (report layer, no scorer unfreeze). Follow-up EPS-TIER-002 QUEUED on G-025; see triads/FINDINGS.md 2026-09-29 |
| G-027 | 2026-09-29 | EPS-TIER-002: collapse-within-ε report filter + re-run EPS-TIER-001 tiers, choosing the above-LOCK tier(s) from G-025's results | QUEUED (needs G-025) |
| G-028 | 2026-10-09 | BRIDGE-002 review: eikosany payload inside 11-limit rank-2 hosts at N ≤ 46 — H-C1 KEPT (no 2¢ bridge; hemififths-41 44/57 at 2¢, full at 6¢; amity-46 42/57 at 4.9¢), window not accuracy blocks (H-C2), tone-set tuning refuted as a rule (H-C3), D'Alessandro val is an addressing optimum (H-C4); ear-check `.scl` under results/scl/bridge002/ (hemififths-41, amity-46, rodan-41); merge its PR | PENDING — [branch claude/combination-product-symmetry-adqmm4](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/tree/claude/combination-product-symmetry-adqmm4); decides BRIDGE-002b scope (N ≤ 72 for miracle-72, budgeted survival tuning) |

## Currently blocked by gates

- Waves 1–3 are fully merged (2026-09-29, PRs #37–#39, #42–#49): G-017–G-024
  all PASS. Open decisions: G-025 (EAR-ε listen, which now also unblocks G-027 / EPS-TIER-002 — follow
  experiments/lattice/EAREPS_PROTOCOL.md, save responses, then unseal) and
  G-013 (SUBSET-MEL-001 spec, waiting on the subset brainstorm; the
  SUBSET-MEL-000 table + 21 .scl are now on main to react to).
- G-028 (BRIDGE-002 review, 2026-10-09): the eikosany payload run is on
  branch `claude/combination-product-symmetry-adqmm4` — no 2¢ bridge at
  N ≤ 46, hemififths-41 and amity-46 are the hosts to hear
  (results/scl/bridge002/). Its PASS decides BRIDGE-002b's scope.
- Runnable next once Marcus says go: M4 tonic-anchored scorer (NEW file, per
  the MUR-002 proposal + blind mūrchanā ear check), BRIDGE-002b (N ≤ 72 for
  miracle-72; budgeted survival tuning), BRIDGE-001c (filler-set design),
  SUBSET-MEL-001 (after the brainstorm).
