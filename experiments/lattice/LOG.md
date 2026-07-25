# Experiment log — lattice (melody ⇄ lattice ⇄ harmony)

Format: hypothesis → result → kept/reverted. Entry written BEFORE each run.
This is the **lattice module's own notebook**, deliberately separate from
`experiments/triads/LOG.md` so the two research workstreams never fight over
the same append-only file. Same discipline, different file. Findings promoted
to `experiments/lattice/FINDINGS.md`; receipts under
`experiments/lattice/results/`.

The contract is `experiments/lattice/SPEC.md` (hypotheses, tolerances, design
decisions, primary-source citations). Execution order: SPEC.md §"Order of
execution".

## Scorer baselines

- **Frozen triad scorer**: `experiments/triads/scorer.py` **v1.1.0**, untouched
  by this module (SPEC.md freeze-compliance clause). Anything scored with the
  frozen scorer here — BRIDGE-000's D'Alessandro harmonic-fidelity measurement,
  `.scl` ear-check exports — is a **v1.1.0** measurement (triads counted within
  a single octave; the ear-validated regime). Never mix with v1.0.0 numbers.
- **Melodic scorer**: `experiments/lattice/melodic.py`, versioned
  independently, starts at **v0.1.0**; freeze (hash-pin pattern) after Marcus
  reviews LAT-MEL-001.

_No runs yet — melodic.py and LAT-MEL-001 are the first deliverables._
