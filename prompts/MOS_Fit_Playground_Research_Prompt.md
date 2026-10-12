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

**Research questions, in priority order**
1. Count objective (CPSFIT-003): DONE 2026-10-11. Open follow-ups: sweep the
   20¢ tone cap (5, 10, 20) as a control, because the small-N optima sit on
   the cap; and a transposition-free fit (chain origin floating), which
   restores the CPS(n,k)/CPS(n,n−k) symmetry. Gate G-032 decides both.
2. Golden fits: for each lattice, the golden (then silver) generator with the
   smallest level that holds it at 2, 3, 5¢. How far is it from the free
   optimum at that N? Is the near-coincidence of Erv's recurrence generators
   with golden ones a general law (do the free optima also land near nobles)?
3. Inversion: DONE 2026-10-11 (CPSFIT-003 P-C5). The reflection 1/L fits
   identically at the mirrored window with P/S swapped. The partner
   CPS(n,n−k) is the reflection TRANSPOSED by ∏F and gets different fits
   under the pinned-origin model, so the search cannot be halved across
   partners unless the fit becomes transposition-free. The page lists the
   murchanas that hold the lattice by direct scan.
4. Subsets: fit the 15 hexanies of the eikosany separately and jointly; which
   chain holds the most subsets at once (subset-first doctrine)?
5. Rank 3: two generators + octave; the D'Alessandro method on a general
   seed. Start with the hexany and the 2-of-5 dekany.
6. Quotient half-generator ties (an N-chain of g equals the 2N-chain of g/2).
7. Hear it: the page exports Scala text; build the ear-check set for the
   hexany at N=15, 19, 22, 31 and the best golden fit, for gates G-029/G-031.

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
