# Findings — lattice module (dated, one paragraph each, linked to artifacts)

Findings promoted here from `experiments/lattice/LOG.md` once they are
receipt-backed. Same convention as `experiments/triads/FINDINGS.md`: each entry
is dated, one paragraph, and names the artifact under
`experiments/lattice/results/` that grounds it. Grade claims by receipt strength
(READ → SIMULATED → EXECUTED → BIT-EXACT), as in the triads verification ledger.

The contract and hypotheses (H-L1, H-L4a/b, etc.) live in
`experiments/lattice/SPEC.md`.

**2026-07-28 — Noble-MOS cut-and-project round trip is exact iff the
conjugate is far enough away; the failure mode is a single extra tone, and
it is a murchana artifact, not a scale property.** (EXECUTED, exact
ℚ(√5) arithmetic end to end; `results/moslat001.json`, step1; runner
`moslat001.py`; scale ground truth `families/mos.py`, the Brun.cpp:269
zigzag.) Eigen-embedding lattice points (octaves a, generator-steps b) as
(physical a + b·g, internal a + b·g′): for nobles with |g − g′| > 1 —
1/φ (741.64¢) and [0;2,(1)*] (458.36¢) — the internal coordinate is
strictly monotone along the chain, and the Brun zigzag scale at EVERY
level 0–9 is exactly a window set (both the a-priori window derived from
the level's zigzag fraction and the internal-hull window; projections
match `mos_cents` at ≤ 1e-6¢). For nobles with |g − g′| < 1 —
[0;1,2,(1)*] (868.33¢) and [0;2,2,(1)*] (503.79¢) — the murchana-0 chain
segment [0, q) FAILS window-representability at exactly the tail levels
whose zigzag fraction lies above g (defect u = q·g − p < 0): the next
chain point b = q lands strictly inside the window (single intruder, zero
exclusions), so the tightest window admits exactly one extra tone,
frac(q·g). The pre-registered guess that failures would track
SEMICONVERGENT levels is REFUTED — both semiconvergent levels in the
corpus pass, and every failure is at a true CF convergent. At every
failing level a majority of shifted chain segments [b0, b0+q) ARE
window-representable (5, 15, 41, 109 of 2q+1 shifts, identical counts
across both generators — structural), so the cut-and-project picture holds
for the MOS up to transposition; what fails is the b = 0-anchored segment
the plugin's Brun construction uses. Practical corollary for BRIDGE work:
window-set machinery on noble MOS must either check |g − g′| > 1 or work
murchana-up-to-shift.

**2026-07-28 — H-M1 is NULL on the all-1s-tail corpus: no conjugate-
embedding descriptor beats raw generator value for predicting triad hot
spots.** (EXECUTED; `results/moslat001.json`, step2; frozen scorer v1.1.0,
ε = 2¢, max_span 1200¢; seed 20260725, 9999 stratified permutations.)
Corpus: 27 noble generators (all CF digit strings, digits ≤ 3, preamble
≤ 3, all-1s tail), 97 (generator, cardinality) rows at N ∈ [5, 22];
P = S on every row (anchored-scorer inversional symmetry, again). Hot
spots are real — P spans 0–62, topped by [0;3,1,3,(1)*] ≈ 317.17¢ (noble
minor third) with P = 62 at N = 19, then the noble fifth
[0;1,1,2,(1)*] ≈ 696.21¢ and its octave complement [0;2,2,(1)*] ≈ 503.79¢
tied at P = 51 (complement symmetry) — but no pre-registered descriptor
(conj_sep, window_width, spread, norm_spread) reaches |partial ρ| > 0.05
or p < 0.35 against the g01 baseline (ρ = −0.162, p = 0.350). The null is
informative about the CORPUS, not just the hypothesis: with an all-1s
tail the SPEC's spectral-gap descriptor is constant (φ², logged in the
receipt) and the rest are near-functions of (N, |g − g′|), so the
conjugate geometry barely varies. Discriminating H-M1 needs a mixed-tail
(metallic 2s/3s) corpus, where the hidden lattice genuinely differs;
reserved for a follow-up run.
