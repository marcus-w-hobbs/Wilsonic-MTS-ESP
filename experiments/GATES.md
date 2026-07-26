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
| G-005 | 2026-07-25 | Merge [PR #19](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/19): melodic.py v0.1.0 + tests, incl. two SPEC-parenthetical corrections (12-EDO diatonic not CS; Pythagorean 12 strictly proper / Pyth-7 is the improper fixture) | **PENDING** |
| G-006 | 2026-07-25 | LAT-MEL-001 review: do M1–M3 rank scales the way your ear does? PASS triggers melodic.py freeze (hash-pin at v0.1.x) | QUEUED (needs G-005, then the LAT-MEL-001 run) |
| G-007 | 2026-07-25 | H-L1 verdict interpretation: eikosany CS or not — what it means for the claim attributed to Wilson | QUEUED (needs LAT-MEL-001 receipts) |
| G-008 | 2026-07-25 | Merge [PR #20](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/20): CI runs the lattice test suite (chore lane) | **PENDING** |
| G-009 | 2026-07-25 | Merge [PR #21](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/21): research blog post 001 "The Tunings That Ring" + README pointer — editorial pass is yours (first-person voice) | **PENDING** |
| G-010 | 2026-07-25 | Merge [PR #18](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/18): worktree.sh dead-cwd fix (chore lane, pre-existing) | **PENDING** |

## Currently blocked by gates

- **LAT-MEL-001** (and everything downstream: SHADOW-001, MOS-LAT-001,
  BRIDGE-000/001) is blocked on **G-005** — melodic.py must be on `main`
  before its numbers count.
