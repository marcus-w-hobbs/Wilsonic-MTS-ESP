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
**2026-07-28 — SHADOW-001: the ε-recovery law of comma perturbation
(H-S1 kept).** [EXECUTED — `results/shadow001.jsonl`,
`results/shadow001_verdicts.json`] Replacing one CPS factor n with
2ᵏ·n ± 1 breaks exact triadic coincidences immediately and permanently:
across 277 variants of the 1-3-5-7 hexany and 1-3-5-7-9-11 eikosany
(scorer v1.1.0, exact path), 96/97 small-k variants drop strictly below
base and none recover by k=16 — exact counts settle to k-independent
floors set by which factor was hit (hexany 1/0/3/4, eikosany
22/18/27/32/25/41 for n=1/3/5/7/9/11; perturbing 3 kills every exact
hexany triad). On the tempered path (ε=2¢) recovery is discontinuous
and law-like: sustained recovery lands at the pre-registered
k* = min{k : 1200·log2(1+1/(2ᵏn)) < ε} in 16/20 position×sign configs
(19/20 inside ε), with n=1 recovering at exactly k=10 on both bases and
both signs. Surprise: 52 eikosany variants OVERSHOOT base tempered
(up to 69 vs 61) at displacements ~0.2–2¢ before decaying to base —
a shadow tone just inside scorer ε buys extra near-coincidences that
the exact tone cannot; the hexany never overshoots.

**2026-07-28 — SHADOW-001: ε_dedup is inert; tone-collapse is exact
lattice arithmetic (H-S2 refuted).** [EXECUTED —
`results/shadow001.jsonl`] The pre-registered dedup-snap prediction
(sharp k*, shifting 1 per doubling of ε_dedup) is false on these bases:
in all 279 rows the deduped tone count equals the exact tone count at
every ε_dedup ∈ {0.01, 0.1, 0.5, 2}¢, because the smallest pairwise
comma the whole sweep produces is 2.912¢ (595/594) — above the largest
dedup epsilon. Tone counts do collapse, but only by exact rational
collision at small k, identically at every epsilon: m=15 and m=33
(perturbing 1) and m=55 (perturbing 7) each merge two eikosany tone
pairs exactly (e.g. 15·3·7 = 5·7·9 = 315, 33·3·7 = 7·9·11 = 693,
55·1·3 = 3·5·11 = 165), giving 18-tone eikosanies. Perturbation also
mints new sub-20¢ commas from nothing (both base spectra are empty
below 20¢): 595/594, 561/560, 441/440, 352/351 head the list —
comma-perturbation as a comma FACTORY is the usable output here.

**2026-07-28 — SHADOW-001: connectivity beats pure novelty, without a
single counterexample (H-S3 kept).** [EXECUTED —
`results/shadow001.jsonl`, `results/shadow001_verdicts.json`] Over 57
matched ± pairs at the same (base, position, k) where one replacement is
a composite sharing primes with the surviving factors and the other is
prime, the sharing side wins exact P 11 times, ties 46, and NEVER loses
(one-sided sign test p = 2⁻¹¹ ≈ 0.0005). Flagship cases: hexany
15 vs 17 at k=4 — exact P 6 vs 2, with m=15=3·5 restoring the full
unperturbed count (6,6) at 111.7¢ displacement; and eikosany
385 = 5·7·11 vs prime 383 at (n=3, k=7) — exact P 24 vs 18, where
replacing 3 by 385/128 is literally a 385/384 displacement (4.503¢),
one of the three D'Alessandro kernel commas of BRIDGE-000. The effect
is exact-path only: the tempered ε=2 lens goes 13W/1T/18L (drowned by
the overshoot effect), so "connectivity beats pure novelty" is a
statement about exact coincidence structure, not about ε-blurred
counts. Auxiliary: P = S held in all 279 rows — CPS(n, n/2)
inversional symmetry is seed-value independent, as pre-registered.
