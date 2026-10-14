# Lattice MOS-Fit Playground — research continuation prompt

Paste this into a new Claude Code session opened in the Wilsonic-MTS-ESP repo.

---

I am going all in on the Lattice MOS-Fit Playground. The question it exists to
answer: given a just lattice (a CPS or any set of ratios), which scales with
one melodic structure (an MOS, which includes ET as the one-step case) hold
every tone of the lattice within a tolerance, and what do those fits teach us
about balancing melody and harmony. Seeding recurrence relations and deriving
recurrences from generators are out of scope here (they are earmarked
elsewhere). Treat me as a co-investigator extending Erv Wilson's program.

**Where things are**
- Branch: `research/lattice-recurrence-playground` (research lane: edit only
  `experiments/`, `plans/`, `prompts/`, `docs/`; never `Source/`).
- The page: `docs/lattice-mos-fit-playground.html`, published at
  https://claude.ai/artifact/WVBseT9sXUwzk8MWyBS2XB (republish to the same
  URL with `url` from a new conversation). Read the file before changing it.
- Its stations: legend (12-ET vs harmonics 3, 5, 7, 9, 11), 1 lattice (CPS
  builder, ratio list, inversion readout, exact P/S triads), 2 generator
  (presets incl. Erv's generators and the fits found so far; scale tree +
  level table), 3 fit (fixed-generator table by level with best murchana;
  free exact minimax search per N; family search over golden/silver/bronze/ET
  generators; murchana slider with rotating step pattern; triads kept;
  Scala text), background facts, options, handoff prompt.
- Research receipts that the page agrees with: `experiments/lattice/`
  CPSFIT-001 (exact tone-minimax chain fit; hexany staircase 4.82¢@15,
  2.57@19, 1.37@22, 0.74@31; every optimum from N=11 is a val; N=15 is Erv's
  0.418935 septimal meantone; no ET<73 holds the hexany at 2¢) and CPSFIT-002
  (triad-minimax: full 12/12 survival at N=22, 193.908¢; worst-triad objective
  loses to the count at N=18–21) and CPSFIT-003 (count objective: the count
  optimum agrees with tone-minimax at no N ≤ 22 on any lattice; hexany 10/12
  at N=16 by the miracle val moved to 116.676¢ and at N=18–21 by (9,5,−3) at
  77.818¢ where miracle/orwell gave 6 and 8; EG4 18/24 at N=16, 20/24 at
  18–22; dekany 1·3·5·7·9 keeps 32/41 at N=26 on a schismatic fourth chain
  498.066¢ (−1,8,14), 37/41 at N=35, never 41 below N=37; the frozen referee
  counts created triads and can rank chains the other way, so both counts are
  on every row; the inversion theorem is EXACT for the reflection 1/L and
  FALSE for the transposed partner CPS(n,n−k): CPS(5,3) differs from CPS(5,2)
  at 10 of 20 feasible N). Gates G-029, G-031 and G-032 (ear checks) are
  PENDING on me in `experiments/GATES.md`.
- Erv's "64 Golden Generators" (1993) is decoded: g = (a+φc)/(b+φd) from the
  two scale-tree fractions where the path starts alternating; all 64
  regenerate; silver = 1+√2 (his 2-zig/2-zag), bronze = (3+√13)/2. Finding:
  every Erv recurrence generator sits 0.1–0.6¢ from a golden one.
- Frozen scorers (never edit; CI-enforced): `experiments/triads/scorer.py`
  v1.1.0 and `experiments/lattice/melodic.py` v0.1.0. New axes go in new
  files. Protocol for any experiment: pre-register predictions in
  `experiments/lattice/LOG.md` and commit BEFORE writing the runner; runner +
  unit tests green before the first run; two bit-identical runs; verdicts in
  LOG, a FINDINGS.md entry, and a new PENDING gate in GATES.md (never pass
  your own gate). Scratch sweeps and runners must share descriptor
  definitions; never copy a sentinel as a value.
- Writing: all page copy and research prose in ASD-STE100 form (load
  `/asd-ste100`, lint with its script); my first-person voice for posts; no
  paraprosdokians or em-dash snaps. MOS includes ET mathematically; an ET
  toggle is a musician's preference only.
- Work autonomously; batch decisions for me into gates and an end-of-stretch
  summary. Do not push without asking; commit freely on the branch.

**Where this is going (Marcus, 2026-10-12).** Music no one has heard, coherent
because it follows a model of how we hear pitch. Target object: the eikosany
CPS(6,3) on ANY six seeds A–F, fitted by one generator into one MOS, with every
embedded subset (dekanies, hexanies, tetrads) playable inside that same MOS.
Triads (P and S first) are the objective, not tones: a chain that holds all 20
tones and loses the triads is not a fit. Golden/noble generators are an
aesthetic axis to keep in the search space, not the objective. Murchana is a
control, not an axis. Inversion is a small fact about self-symmetric CPS, not a
program. Path to the musician: Wilsonic (Scala export first).

**Research questions, in priority order**
1. Triads as the objective on the page and on the eikosany: port the
   CPSFIT-003 count search into the page's free search (count-optimal beside
   tone-optimal); extend val/kernel code to 11-limit; run the count fit on the
   eikosany (CPSFIT-004). Controls from G-032: tone-cap sweep (5, 10, 20¢) and
   a transposition-free fit. Geometric triads as a possible third class.
2. Eikosany + subsets jointly: RAN 2026-10-14 as SUBFIT-001 (gate G-036).
   One chain keeps at most 20/30 hexanies + 4/12 dekanies at N = 70; usable
   MOS today: 41-note level of 351.44¢ (14 + 2) and 53-note level of
   497.77¢ (16 + 2). LESSON: a cap-free survival predicate counts chain
   coincidences (tones up to 71¢ off still "kept" a triad) — never drop the
   per-tone cap; SUBFIT-002 re-registers with 20¢ and 10¢ caps. Lesson 2:
   a scratch must use the SAME assignment rule as the runner (global vs
   in-window nearest degree changed every number). SUBFIT-002 RAN
   2026-10-14 (gate G-037): caps 20¢ and 10¢ agree from N = 38 up, all
   six predictions kept. Lesson 3: report `homomorphic` for every winner —
   the 351.444¢ neutral-third chain (41/58-note levels) keeps 14 hexanies
   by an assignment no single 11-limit val produces; the homomorphic
   level floors are 46 (443.128¢, 12 + 2), 53 (497.774¢, 16 + 2) and 72
   (483.278¢, 20 + 4). Open on G-037: cap choice and whether the design
   requires one val.
3. Any seeds, any generator: exact fit for six arbitrary seeds (primes > 7).
4. Golden as an aesthetic axis: RAN 2026-10-13 as GOLD-001 (gate G-035).
   Golden at complexity ≤ 20 loses triads to the free optimum on every
   lattice (hexany 8/12 where free has 12); silver loses fewer; the
   MOS-level constraint costs more than either; a pure MOS keeps all 12
   hexany triads first at N = 25. The selector is a real trade. Open: the
   page's family search scored by triad count (it scores tone error now);
   "noble only" vs "best triads" on the page; ear evals.
5. Erv's generators vs golden: RAN 2026-10-13 as GOLD-002 (gate G-034) on
   the 17 generators the repo cites. The strong law is refuted against a
   null model (3–6 of 17 in the tail, never most); silver fits as well;
   nearness ≠ harmony at depth. Complexity = minimal seed-denominator pair
   (gold002.nobles; the page's enumeration was corrected). Open: GOLD-003
   on the full archive (read in place, figure-cited) only if G-034 says the
   weak signal is worth it.
6. Hear it: six chains are in Wilsonic's user Scala library (hexany N=15, 16,
   18, 22×2; dekany N=26); gates G-029, G-031, G-032.
7. Rank 3: RAN 2026-10-12 as RANK3-001 (brun3.py = port of the iOS Wilsonic
   Brun3, Viggo Brun's three-term algorithm; runner rank3001.py). Hexany in
   19 notes at 0.47¢ with 12/12 (65625/65536), 21 at 0.12¢ (2401/2400);
   EG4 24/24 from N=19; dekany with 9 held in full at N=29 (schisma); the
   eikosany (rank 5) stops at 12¢ with no val: three generators (Brun
   four-term) are the next rung. Gate G-033. Lessons: register the COMMA,
   never the generator pair (coordinates are not invariant); say which
   survival count (mirror vs frozen) a clause uses; the frozen referee
   counts created triads heavily at 15¢ error. Open follow-ups: rank-3
   count objective, rank 4 for the eikosany, a Brun3 design in Wilsonic
   MTS-ESP (plugin lane), a rank-3 station on the page.
8. The half-generator tie quotient: still open, low priority.

**Playground improvements made 2026-10-11** (staircase chart with
free/station-2/family/ET on one picture, hover and click; val + kernel per
selected chain, with a transposed-val test; murchanas that hold the lattice
and the mirrored murchana; compare panel A vs B; CPSFIT-003 presets and
background facts; inversion fact corrected).

**Playground improvements still open**
- A count-objective column computed on the page (the JS search is tone
  minimax; CPSFIT-003 ran offline).
- Quotient the half-generator ties in the free-search table.
- Keep the page's numbers tied to the receipts; when a page claim and a
  receipt disagree, the receipt wins and the page is fixed.

Start by reading `experiments/lattice/LOG.md` (the CPSFIT entries),
`experiments/GATES.md`, the memory notes, and the page source. Then propose
the first experiment's pre-registration in the LOG, commit it, and go.
