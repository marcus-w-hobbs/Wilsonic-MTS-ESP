# EAR-ε listening protocol — where does YOUR ear lose the lock?

44 tiny tunings in `results/scl/eareps/`. Each one is a single triad,
some perfectly in tune, some detuned by an amount you don't know. Your
job: for each one, say whether it still "locks" — fuses into one
reinforcing sonority — in one sitting, before looking at any answer.

**Sealed until you're done:** `results/eareps_key.json` and
`results/eareps_manifest.json` (and their diffs in this experiment's
PR). Don't open the .scl files in a text editor either — the cents
values give the game away. Load them by ear only.

## Setup (once)

1. One running Wilsonic instance (MTS-ESP master rule), plus any
   MTS-ESP synth — or any synth that loads .scl directly.
2. Pick a sustained, harmonically rich, STEADY patch — organ or plain
   saw pad. **No vibrato, chorus, unison detune, or delay** (they mask
   or fake the beats you're listening for). Same patch and same
   playback chain for all 44 files; note both in the response file.
3. Leave the reference frequency at its default. Don't retune between
   files.
4. Copy `results/eareps_responses.template.json` to
   `results/eareps_responses.json`. Fill in the header fields
   (date, patch, chain).

## Listening (one sitting, ~30–45 min)

Go block by block, in this order, files in numbered order:

1. `eareps_B_01` … `B_11`  (three-note chords on two degrees + octave)
2. `eareps_A_01` … `A_15`
3. `eareps_C_01` … `C_15`
4. `eareps_D_01` … `D_03`

Per file:

1. Load the .scl (drag into Wilsonic's Scala design, or your synth's
   Scala import).
2. Hold the three keys **60-61-62** (the mapping root and the next two
   keys) together for at least 5 seconds. Release. Hold again.
3. Write ONE verdict in the response file before moving to the next:
   - `locked` — fuses into a single in-tune sonority; steady.
   - `beating` — audible waver or roughness, but it still reads as
     the chord, more or less in tune.
   - `broken` — the fusion is gone; it reads as mistuned.
   Optional: `fusion_1to5` (5 = perfectly fused) and free `notes`.

Rules of the game:

- Replay the CURRENT file as often as you like.
- Once you've written a verdict and moved on, **don't revise it** —
  commit-as-you-go, same discipline as G-006.
- No peeking at the key, the manifest, or the .scl text until
  `eareps_responses.json` is saved.

## Afterwards

Save `results/eareps_responses.json`, then open the key and manifest
freely. Report in any session ("EAR-ε responses are in") and the
analysis runs exactly as pre-registered in LOG.md (2026-08-19 entry):
per family and direction, your threshold is the midpoint between the
last `locked` and the first `broken`. That entry also holds the three
predictions this sitting will keep or refute. Gate: G-025.
