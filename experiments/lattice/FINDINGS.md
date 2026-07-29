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
