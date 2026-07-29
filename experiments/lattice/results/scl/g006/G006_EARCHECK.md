# G-006 blind ear check — does M3 (propriety) hear like you do?

16 scales, 8 pairs, in `results/scl/g006/`. Each pair contains one scale
the machine calls melodically well-formed (proper / strictly proper) and
one it calls improper — in randomized a/b order. **Do not open
`g006_key_SEALED.json` until your notes are written down.** (The .scl
comment headers name each scale for provenance; avoid reading file
contents while listening.)

- **Pairs 1–6:** hexanies, 6 tones each (same harmonic family, so what
  differs is the melodic shape).
- **Pair 7:** two 5-tone MOS. **Pair 8:** two 13-tone MOS.

## Protocol

For each pair, load both into Wilsonic (one instance at a time — MTS-ESP)
and play each as a MELODY: stepwise runs up and down, small motives,
whatever you'd improvise. Then note, per pair:

1. Which member (a/b) feels more melodically coherent — singable,
   stepwise, "walkable"?
2. Confidence: sure / lean / can't tell.

Report in any session as e.g.:
`G-006 notes: p1 a sure, p2 b lean, p3 tie, ... p8 a sure`

Scoring (any session): your picks vs the sealed key. Rough bar agreed in
advance: ≥6/8 with the machine → M3 is hearing something real (PASS
territory); ≤4/8 → the metric is not your ear (FAIL); 5/8 → more pairs.
Your call stands regardless — the bar is a prior, not a rule.
