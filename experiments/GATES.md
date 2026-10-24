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
  4. Save a verdict on the Ear Bench (https://claude.ai/artifact/XNptx9B3t9yXGgDvmJeVbf,
     source docs/ear-bench/). Sessions read its database with ArtifactData
     (`gates/<G-NNN>`, `scales/<id>`, `comparisons/<id>`, `eareps/responses`)
     and treat a saved Pass/Fail as the decision. For MIDI controllers the bench
     runs locally (`python experiments/ear_bench/serve.py`, Chrome), and saves to
     `experiments/ear_bench/results/verdicts.json` instead; sessions read both.
     Rebuild its scale bundle with
     `python experiments/ear_bench/bundle.py` whenever a gate adds `.scl` files.
- **Statuses:** `PENDING` (waiting on Marcus — the loop is stopped here),
  `QUEUED` (will become PENDING when its prerequisites land), `PASS`, `FAIL`
  (both dated, with notes).
- Ear checks are standing gates: any `.scl` export offered for listening is
  implicitly PENDING until Marcus reports back.
- **Every experiment that emits scales ships an Ear Bench audition** (charter,
  Marcus 2026-10-22): its `.scl` files go under `results/scl/<folder>/`, its gate
  row names that folder, and a chain-vs-chain comparison registers its JI
  reference and default A/B pair in `experiments/ear_bench/bundle.py`, so the
  blind passages work with nothing extra. Marcus judges on the bench; before a
  session records a decision it runs `experiments/ear_bench/export_judgments.py`,
  and the judgments are released in `experiments/ear_bench/judgments/` per
  `experiments/ear_bench/JUDGING.md`. **Standard timbre: electric piano**
  (Marcus 2026-10-24, one timbre to keep listening time down; EAR-ε excepted,
  it needs a sustained tone).

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
| G-028 | 2026-10-10 | MERU-001 review: the power-of-two recurrence law (P-M1/P-M2 kept), crossover law refuted-as-registered on 1/12; ear check of nine .scl windows under results/scl/meru001/ (0.418935, Fibonacci, meta-meantone: seed, lock, last) | PENDING — does the lock window sound like the seed window's harmony arriving at the chain, or like a new chord? |
| G-029 | 2026-10-10 | CPSFIT-001 review: hexany inside a 22-note chain at 1.37¢ (no ET < 73 does it), N = 15 fit is Erv's 0.418935 (septimal meantone), survival non-monotone in tone error; ear check of results/scl/cpsfit001/ (N = 15 and N = 22 chains); decide whether CPSFIT-002 optimizes triad deviation instead of tone error | PENDING |
| G-030 | 2026-10-10 | MERU-002 review: the ρ knob of the order lift buys no harmony (P-R3 kept; mean P@2¢ falls with ρ), chain step follows max(ρ, λ₂) (P-R2 held on 30/31 rows), lock step follows ρ (P-R1 refuted as registered: wrong lock definition in the scratch); ear check of six .scl under results/scl/meru002/ (0.418935 at ρ = 1 vs 5/2; n = 12, 40, 100) | PENDING — does the long ρ = 5/2 transient at n = 40 sound like anything, or like a scale drifting? Decide whether ρ stays a playground control or is dropped as a research knob |
| G-031 | 2026-10-10 | CPSFIT-002 review: minimizing the worst hexany triad instead of the worst tone brings full 2¢ survival from N = 31 down to N = 22 (193.908¢, one tone at 2.22¢); EG4 from 31 to 23; but the worst-triad objective loses to the count at N = 18–21 (miracle 6/12 vs orwell 8/12); ear check of results/scl/cpsfit002/ (N = 22 at 193.908 vs CPSFIT-001 at 193.787) | PASS 2026-10-23 — first gate decided on the Ear Bench (blind X/Y passages, reed, 1/1 = 261.63 Hz): chorale and tune preferred the triad fit 193.908, scale run and tune-over-chorale preferred the tone fit 193.787; Marcus: "I hear a lot of good triads in both. the biggest differences to me are how good the melody is." The worst-triad objective stands (both chains carry the triads; melody separates them); the count objective already ran as CPSFIT-003 (G-032). Judgments: experiments/ear_bench/judgments/marcus-w-hobbs.jsonl; log: experiments/lattice/LOG.md 2026-10-23 |
| G-032 | 2026-10-11 | CPSFIT-003 review: the count objective beats both prior objectives at every N ≤ 21 on the hexany and EG4 (hexany 10/12 at N = 16 by the miracle val moved 0.17¢, 10/12 at N = 18 by (9, 5, −3) at 77.818¢ where miracle/orwell gave 6 and 8) and on the dekanies from N = 19 (32/41 at N = 26 on a schismatic fourth chain); the frozen referee counts created triads (one row where it ranks the chains the other way); the inversion theorem is exact for the reflection and false for the transposed partner CPS(5,3) (page fact corrected); ear check of results/scl/cpsfit003/ (hexany N = 16 and 18, dekany N = 26) | PASS 2026-10-24 — judged on the Ear Bench at N = 16 (count 116.676, 10 of 12, one tone 5.2¢ out, against worst-triad 116.588, 6 of 12, worst tone 4.86¢): the count chain was preferred in the chorale, the tune over the chorale and the scale run, the worst-triad chain in the tune; mixed timbres (run under reed, the rest under electric piano) and Marcus notes the timbre matters ("I prefer the electric piano timbre, but I could easily score differently with a different timbre such as reed"). Ten good triads with one tone out beat six at 4.8¢; the count objective stands. Not settled by this listening and still open: the floating chain origin and the 5/10/20¢ cap sweep. N = 18 comparison not yet judged. Log: experiments/lattice/LOG.md 2026-10-24 |
| G-033 | 2026-10-12 | RANK3-001 review: two generators (iOS Brun3, ported) hold the hexany at N = 19 within 0.47¢ with all 12 triads (rank 2 needed 31) and the dekany with 9 at N = 29 within 0.65¢ with all 41 (rank 2 never did); each rank buys one comma (ET: none up to 72 and the page computes 130; rank 2: 22; rank 3: 19; JI: 6, for the hexany at 2¢); the eikosany needs a third generator; ear check of results/scl/rank3001/ (hexany N = 19 at 65625/65536, N = 21 at 2401/2400, dekany N = 29 schismatic) | PENDING — does a three-step scale with every hexany triad inside sound like the hexany or like a new scale with the hexany in it? Decide: (a) rank-3 count objective next, (b) three generators (Brun four-term) for the eikosany, (c) a Brun3 design in Wilsonic MTS-ESP (plugin lane, end of the designs list), (d) a rank-3 station on the page |
| G-034 | 2026-10-13 | GOLD-002 review: the strong golden law is refuted (never more than 6 of Erv's 17 generators in the 10th-percentile tail at any complexity, against 1.7 expected); silver fits them as well as golden; nearness ≠ harmony at depth (9 Erv wins, 6 golden wins, 2 ties on the chain's own triads); decide the design selector: free optimum / golden / silver / Erv's list / ET as separate families with the triad cost shown | PENDING — is the weak signal (0.418935 and 0.773743 at Q 20, meta-meantone and Fibonacci at Q 8) worth GOLD-003 on the full archive, and is Erv's list its own family in the selector? |
| G-035 | 2026-10-13 | GOLD-001 review: the family selector's price measured — golden at complexity ≤ 20 loses triads to the free optimum on every lattice (hexany stuck at 8/12 where free reaches 12), silver loses fewer (hexany 12/12 at N = 29, dekany ≥ golden-60 from N = 23), the MOS-level constraint costs more than either (first pure MOS with all 12 hexany triads: N = 25); CPSFIT-003's dekany rows N = 13–18 beaten (16 at 249.263¢); ear check of results/scl/gold001/ (hexany 15-note golden level, 29-note silver chain) | PENDING — decide the selector: free / golden / silver / Erv's list / ET, each with triad cost and N shown; and whether 25 notes with a Gral is the hexany's design floor |
| G-036 | 2026-10-14 | SUBFIT-001 review: one generator chain keeps at most 20/30 hexanies + 4/12 dekanies of the eikosany at N = 70; usable MOS today: 41-note level of 351.44¢ (14 + 2, within 9.5¢) and 53-note level of 497.77¢ (16 + 2, within 4.2¢); the cap-free predicate counted chain coincidences below N = 37 (all five predictions refuted as registered; SUBFIT-002 adds a per-tone cap); ear check of results/scl/subfit001/ N = 49, 53, 70 | PENDING — is 41 or 53 notes on a Gral the eikosany's design floor, and which cap (10¢ or 20¢) defines "the subset is still there" for SUBFIT-002? |
| G-037 | 2026-10-14 | SUBFIT-002 review: with a per-tone cap (20¢ and 10¢) the eikosany subset staircase agrees from N = 38 up, so the design numbers stand on either cap (41-note 351.444¢ level 14 + 2 within 9.5¢; 53-note 497.774¢ level 16 + 2 within 4.2¢; 72-note 483.278¢ level 20 + 4 within 8.0¢; all six predictions kept); post-hoc: the 351.444¢ winner and its 41/58-note levels are NOT homomorphic (no single 11-limit val), the homomorphic level floors are 46 notes (443.128¢, 12 + 2), 53 (16 + 2) and 72 (20 + 4); ear check of results/scl/subfit002/ (37-note cap-20 chain, 41- and 72-note levels; library IDs 83–85) | PENDING — (a) which cap, 10¢ or 20¢, defines "the subset is still there" (they only disagree below 38 notes); (b) must the design's fit be one val (homomorphic), which drops the 41-note level and makes 46/53/72 the floors, or is a non-temperament assignment acceptable when every kept triad is within the cap? |
| G-038 | 2026-10-14 | GOLD-003 arm A review: CPSFIT-003's count-optimal survival segments contain golden nobles of complexity ≤ 12 in 3 of 22 cases vs 0.24 expected (p = 0.002; 2 of 15 merged, p = 0.012): 317.170¢ (3/11, 1/4) and 503.786¢ (2/3, 1/2); nothing else reaches the pre-set 0.005 level below complexity 60; all five predictions kept; read as a hint consistent with "the noble is chosen INSIDE the survival segment", never as nobility predicting harmony | PENDING — (a) is the segment-containment statistic the right formalisation of Erv's practice; (b) locate the scale-tree sheets with ear-marked goldens (the Farey-delta page) so arm B (marked vs un-marked nobles at matched complexity) can be registered; (c) should the design's golden selector be "snap to the noble inside the segment, else show the triad cost"? |
| G-039 | 2026-10-17 | DYNMOS-001 review (Fork B, dynamic MOS, generator fixed, level + window per subset): canonical hexanies playable at 17–34 notes (351.444¢ at 17/24, 497.774¢ at 29 within 4.2¢, 443.128¢ at 19) vs 41–72 for the whole genus; dekanies still 41–68; 483.278¢ keeps 4 dekanies at 62/67 with all common tones kept; every other generator keeps 2 complementary dekanies (contrast only); Marcus's 0.238186 and 0.418935 keep nothing of the canonical set; Marcus's 1·45·135·225·19·377 has 30 exact triads and 12 triad-free hexanies (the proxy's blind spot); all six predictions kept; ear check of results/scl/dynmos001/ (library IDs 86–88) | PENDING — (a) is a 17- to 34-note hexany scale with the generator fixed the right melodic unit for Fork B; (b) which transition cost matters, retuned common tones or the level jump; (c) what do you hear in the 1·45·135·225·19·377 near-unison pairs that the triad proxy cannot see; (d) are 0.238186 and 0.418935 generators for other structures, and which? |

## Currently blocked by gates

- 2026-10-24: G-032 PASS on the bench (count objective preferred at N = 16); timbre is now a judged factor (picks kept per timbre).
- 2026-10-23: G-031 PASS, the first gate judged on the Ear Bench: with both 22-note chains carrying the hexany's triads, Marcus heard the difference in the melody. Next on the bench: G-029, G-032.
- 2026-10-17: DYNMOS-001 ran (G-039): Fork B's first numbers; next Fork B experiment waits on (a) and (b).
- 2026-10-14: GOLD-003 arm A ran (G-038): segment containment is a hint only; arm B waits on Erv's ear-marked scale-tree sheets.
- 2026-10-14: SUBFIT-002 ran (G-037): the cap does not change the eikosany's MOS floors above 38 notes, but the 41-note neutral-third level is not a single-val fit; G-037 asks whether the design requires one val (floors 46/53/72) and which cap. SUBFIT-001 (G-036) stands.
- 2026-10-13: GOLD-002 (G-034) and GOLD-001 (G-035) ran; the generator-family series is measured. Next per the design goal: the rank-2 count objective on the eikosany's subsets jointly, and the Gral playability of the 25-note MOS floor.
- 2026-10-12: RANK3-001 (two generators, Brun3) ran on `research/lattice-recurrence-playground`;
  G-033 is its review + ear-check gate.
- 2026-10-11: CPSFIT-003 (count objective) ran on `research/lattice-recurrence-playground`;
  G-032 is its review + ear-check gate. Open on the same branch: G-028, G-029,
  G-030, G-031 (ear checks). The MOS-fit playground page carries the receipts.
- 2026-10-10: MERU-001 and CPSFIT-001 (the playground's two directions) ran on
  `research/lattice-recurrence-playground`; G-028 and G-029 are their review +
  ear-check gates. CPSFIT-002 (triad-deviation objective) and MERU-002 (ρ sweep,
  dekany/eikosany seeds, Rauzy window) are runnable once Marcus says go.

- Waves 1–3 are fully merged (2026-09-29, PRs #37–#39, #42–#49): G-017–G-024
  all PASS. Open decisions: G-025 (EAR-ε listen, which now also unblocks G-027 / EPS-TIER-002 — follow
  experiments/lattice/EAREPS_PROTOCOL.md, save responses, then unseal) and
  G-013 (SUBSET-MEL-001 spec, waiting on the subset brainstorm; the
  SUBSET-MEL-000 table + 21 .scl are now on main to react to).
- Runnable next once Marcus says go: M4 tonic-anchored scorer (NEW file, per
  the MUR-002 proposal + blind mūrchanā ear check), BRIDGE-002 (identity/
  in-budget front rule per G-021), SUBSET-MEL-001 (after the brainstorm).
