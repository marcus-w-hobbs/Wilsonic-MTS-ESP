# Judging on the Ear Bench

I am the judge for this research program. Every experiment that produces a
scale ends with my ear deciding whether it is any good, and I record that
decision on the Ear Bench so it can be read, checked and reused. This file
explains how I make those judgments, what gets written down, and how anyone
else can do the same.

## Why I judge this way

The experiments in this repository score scales with numbers I trust as
measurements: how many proportional and subcontrary triads survive in a
chain, how far each tone sits from just intonation, how many notes a fit
needs. Those numbers are proxies. They tell me where to listen, and they
cannot tell me what I will hear. When I listened to G-031, the two chains
differed by at most 2.4 cents on any step, and I still heard one as clearly
more melodic, and I realised that the arpeggio I was playing could not answer
the harmonic question the gate was asking. So the bench now plays music
composed for the comparison, and I judge that music without knowing which
scale is which.

Erv Wilson worked out his scales by hand and tested them on instruments he
built. I have a computer that can search far more scales than either of us
could ever play, and the scarce resource is now my listening time. The bench
exists to spend that time well, and the record of my judgments is the signal
I want the search to learn from.

## How a judgment is made

For two scales that approximate the same just structure (a hexany, a dekany,
the eikosany), the bench composes four passages from the structure's own
triads and plays each one in both scales:

1. **Scale run**: the scale up and down one octave. Melody alone.
2. **Tune**: a melody in the scale's own steps that walks from chord tone to
   chord tone. Melody alone, but shaped by the harmony.
3. **Chorale**: every triad of the just structure, held, each moving to the
   next by common tones, with a bass an octave below. Harmony alone.
4. **Tune over chorale**: both at once.

Each passage plays as X then Y. Which scale is X is hidden from me and drawn
fresh every time the page loads. I pick X, Y or Same, and only then does the
bench show me which was which. A live strip shows which of X and Y is
sounding and which chord is being held, so I always know what I am hearing.

After the passages I make the gate's call (Pass, Fail or Listen again) and
write what I heard in my own words. Those notes matter as much as the picks,
because they are where a new experiment usually comes from.

## What gets recorded

Every judgment becomes one line in `judgments/<judge>.jsonl`. Mine are in
`judgments/marcus-w-hobbs.jsonl`. A line is never edited after it is written.
If I change my mind, that is a new line with a later time, so the file holds
the whole history of my decisions, including the reversals.

Each record has these fields:

| Field | Meaning |
|---|---|
| `kind` | `blind_preference` (a passage pick), `gate_verdict`, `overall_preference`, `chord_preference` or `scale_rating` |
| `judge`, `at`, `gate` | who, when (UTC), and which gate in `experiments/GATES.md` |
| `a`, `b` | the two scales: bench id, `.scl` path and the SHA-256 of the file I heard |
| `blind` | true only for passage picks, where the order was hidden |
| `passage`, `x_was`, `pick`, `preferred` | for a blind pick: which passage, which scale was X, what I chose, and what that means (`a`, `b` or `same`) |
| `verdict`, `notes` | for a gate verdict: my call and my words |
| `context` | how I was listening: timbre, ear nonlinearity, the frequency of 1/1, which copy of the bench, and its version |
| `source`, `provenance` | which store the judgment came from, and a note when a session restored or copied it |

The SHA-256 ties every judgment to the exact tuning I heard. If an experiment
is later regenerated and a scale changes, the old judgments still point at
the old file.

The EAR-ε sitting (G-025) is the one exception. It has its own blinded
protocol in `experiments/lattice/EAREPS_PROTOCOL.md` and its own results file.

## How the records get here

The bench saves to two places: the database behind the published page, and
`results/verdicts.json` when I run the local copy for a MIDI controller. A
session pulls both and runs

```bash
python experiments/ear_bench/export_judgments.py --judge marcus-w-hobbs --dump <database dump> --local experiments/ear_bench/results/verdicts.json
```

which appends only the records that are new. The same judgment saved in both
places counts once.

## Licence

My judgments in `judgments/` are released under the Creative Commons
Attribution 4.0 International licence (`LICENSES/CC-BY-4.0.txt` at the root of
the repository). You can reuse and adapt them for any purpose, commercial work
included, as long as you credit Marcus Hobbs and link back to this repository.
The code that produces and exports them is MIT, like the rest of the code here.

## Other judges

Anyone can judge these scales. Run the bench (the published page, or
`python experiments/ear_bench/serve.py` and Chrome), make your picks, and send
a pull request that adds your own `judgments/<your-name>.jsonl` in the same
format. I will read every one. Where someone hears something I missed, or
builds a better experiment or a better way to listen, I will take the idea
and name the person who had it.

## Limits

These are one person's aesthetic judgments, made through a browser
synthesizer, mostly at one register and with a handful of timbres. They
record what I hear and what I prefer under the conditions written beside each
one, and a preference between two scales that differ by a cent or two can be a
real perception or the order I heard them in. That is why the order
is blind, why every judgment carries its listening context, and why I keep
the reversals. A scale is only finished when it also runs in the Wilsonic
plugin and I have played it there.
