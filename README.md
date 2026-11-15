# Wilsonic MTS-ESP

<img src="./Resources/wilsonic_icon_03_512.png" alt="Wilsonic Icon" width="200">

Wilsonic MTS-ESP is an advanced audio plugin and standalone application for creative sound design and music production. It tunes up the software synthesizers in your DAW via MTS-ESP to the scale designs of Erv Wilson; it has a simple synth that you can use to confirm your synths are all in tune.  The Wilsonic Controller target outputs MIDI, while also tuning up all soft synths in your DAW via MTS-ESP.  You can use WilsonicController to perform on Wilson's generalized keyboard designs.

**This repository holds two things that serve one search.** The **plugin** lets you play Erv Wilson's scale designs in your DAW. The **research harness** under [`experiments/`](experiments/) is where I look for new ones, carrying on by computer the search Erv pursued by hand across a lifetime of diagrams. I treat both as first-class, and the research section below describes where that search has gone so far. See [The Research Program](#the-research-program--continuing-erv-wilsons-search).

## Features

- Interactive musical scale design and visualization of the tuning systems of Erv Wilson
- Scale design parameters are automatable in your DAW, and therefore editable
- Standalone application and plugin formats (VST3, AU)
- MTS-ESP support for microtuning
- WilsonicController outputs MIDI, while also tuning up all soft synths in your DAW via MTS-ESP
- Cross-platform compatibility (macOS, Windows)

## The Research Program — Continuing Erv Wilson's Search

<!--
Keeping this section current: when an experiment lands or a gate is decided,
update (1) the paragraph for its period in "How the question changed",
(2) its row in "The roads so far", and (3) "Where I'm headed" when a
crossroads closes or a new one opens. Move the snapshot date. Sources of
truth: experiments/GATES.md, experiments/*/FINDINGS.md, and the survey in
docs/crossroads/data.js. Prose follows .claude/rules/writing-style.md.
-->

Erv Wilson (1928–2016) spent his life searching, by hand and across thousands of diagrams, for scales that serve **melody** (stepwise, singable lines) and **harmony** (chords whose overtones reinforce each other) at the same time. I worked at his side from 1995 to 2005, building his designs into software while we talked. This codebase is the most complete computational implementation of his theories that I know of, and since July 2026 it has also been where I keep his search going, with frozen scorers, a bit-exact model of the plugin's own math, Claude Code sessions that design and run the experiments, and my own ears deciding what is any good.

When I started, I thought the job was to count triads. Four months and forty-one decision gates later, the question has grown well beyond that, and this section is my attempt to show the whole of it: the roads I have explored, what each one taught me, and where I am heading and why. It is a snapshot taken on 15 November 2026. The live record is the gate ledger, [`experiments/GATES.md`](experiments/GATES.md), where 31 gates have passed, 9 are waiting on me, and 1 is queued behind another.

**New here as a researcher?** Start with [The Tunings That Ring](docs/research-blog-001.md), my first research note, which discloses the scoring function in full, including its measured limitations, and invites you to critique and extend it in [Discussions](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/discussions). Then read [The Machine Keeps Deriving Wilson](docs/research-blog-002.md), which tells three episodes in which exhaustive searches re-derived Erv's hand results (the 1975 D'Alessandro template, its pitch-just addressing trick, and the 1993 golden-generator table), with every number linked to its receipt. For the current state of every road at once, open the [Wilsonic Crossroads](docs/crossroads/index.html) page, which carries a live gap-fill workbench and a map of all 28 research directions with their gates and open choices.

### How the question changed

**Counting triads (July 2026).** I began with the triads harness in [`experiments/triads/`](experiments/triads/), which searches the seed space of Combination Product Sets and counts their proportional, subcontrary and geometric triads with a frozen scorer. A proportional triad puts its middle tone at the arithmetic mean of the outer frequencies, a subcontrary triad puts it at the harmonic mean, and a geometric triad at the geometric mean. All three are relations among the frequencies themselves, and when one holds, the difference tones reinforce each other and the chord audibly locks in. My first ear check (G-002) passed the classifier and rejected the aggregator, because I did not want `min(P,S)` ranking scales when P-heavy, S-heavy and G-heavy scales are all worth wanting. Along the way the harness showed that every hexany sits exactly on the P = S diagonal, and it found three bugs in the plugin's own triad analyzer.

**Melody gets its own axis (late July).** Triads alone say nothing about whether a scale is singable, so I started a second module, [`experiments/lattice/`](experiments/lattice/), with a frozen melodic scorer (`melodic.py` v0.1.0, frozen after I agreed with its rankings 8 times out of 8 in a blind ear check, G-006). The first thing it told me was uncomfortable. The 1-3-5-7-9-11 eikosany is not a constant structure, and no eikosany on odd seeds up to 15 is (0 of 29), while hexanies nearly always are (66 of 70). I suspected special seedings might still get there, and CS-EIK-001 found 32 constant-structure eikosanies, among them {1, 7, 9, 11, 15, 29}, the first strictly proper eikosany I know of, which I heard as the most melodic eikosany I had played. Then the census of the eikosany's 72 embedded subsets (SUBSET-MEL-000) showed that propriety flips between the whole structure and its parts. That changed how I think about playing these structures, because I play the subsets, so the melody has to work inside each one.

**Deriving Erv's reasoning from his results (July and August).** Erv's papers record his results and almost never his reasoning, and Kraig Grady, Gary David and Stephen Taylor have all told me the same thing. So a large part of this work has been reconstructing that reasoning and checking it against the scans Kraig made of the archive, which I read in place and never copy into this repository (the derived index is [`experiments/archive/INDEX.md`](experiments/archive/INDEX.md)). An exhaustive search re-derived the 1975 D'Alessandro template exactly, all seven collisions included, and Erv's mapping turned out to be tie-optimal (BRIDGE-000). I calibrated the tools on music everyone knows: 12-EDO's "cultural epsilon" is 14.86¢, the diatonic scale wins the seven-note class among 12-EDO's 351 subset classes, and the road from Pythagorean tuning through meantone and Werckmeister III to 12-EDO can be measured stage by stage (ET-001, ET-002, ET-003). Erv's raga lattice turned out to be a 53-tone 5-limit lattice, with the 22 śrutis as a window on the chain of fifths taken modulo the schisma (MUR-002). Some roads ended. The conjugate-descriptor hypothesis for MOS scales came back null twice (MOS-LAT-001 and 002), and placing the EG4 faithfully inside an MOS of 22 notes or fewer failed, with the best hosts missing full triad survival by one cent (BRIDGE-001 and 001b).

**Fitting harmony inside melody (October).** In October I narrowed the goal (described below), and the work turned to one question: given a just harmonic structure, which one-generator scale (an MOS) holds its triads? A hexany fits inside a 22-note chain within 2¢, which no equal temperament below 73 notes manages, and the 15-note fit turned out to be Erv's own 0.418935 generator, a septimal meantone (CPSFIT-001). Counting the surviving triads, instead of bounding the worst one, kept more triads at every size up to 21 notes (CPSFIT-002, CPSFIT-003), and when I listened at 16 notes I preferred the counted chain (G-032). A second generator, built the way my iOS Wilsonic builds it with Viggo Brun's three-term algorithm, holds every hexany triad at 19 notes, and each added generator buys exactly one comma (RANK3-001). Power-of-two Meru recurrences turned out to generate proportional triads exactly (MERU-001). I tested the idea that optimising for triads lands you on golden (noble) generators, and it failed against a random-generator null, with silver generators fitting Erv's choices as well as golden ones do (GOLD-001, 002, 003). That taught me to keep nobility and harmony apart, so in the design a golden generator gets picked inside the range of generators where the triads survive, and nobility is never used to predict harmony. For the whole eikosany, one generator chain keeps at most 20 of its 30 hexanies, and the dense scales the design could use today have 41, 53 and 72 notes (SUBFIT-001, SUBFIT-002). When the generator stays fixed and the level and mode change with each subset, a hexany becomes playable in 17 to 34 notes (DYNMOS-001). The newest road leaves the subset's own tones exact and fills the melodic gaps between them with added tones. GAPFILL-001 put every gap-filling method side by side, and while no single method turns every subset into a constant structure, their union does for all 42 subsets on each of three seed sets. GAPFILL-002 then asked for one shared table of added tones serving every subset of the genus at once, and a table of 12 to 35 tones serves 31 to 42 subsets whose separate fills would have needed 137 to 206. On the Ear Bench I preferred arithmetic division over parent tones for filling a single hexany (G-040), and the shared genus table over the shared division table for the whole genus (G-041).

**The ear becomes the judge (late October and November).** The scorers give me measurements I trust, and they are still proxies. So I built the [Ear Bench](docs/ear-bench/), a browser listening bench that plays blind passages (a scale run, a tune, a chorale, and the tune over the chorale) so I can compare two scales without knowing which is which. G-031 was the first gate I decided there. The surprise came with G-029, where I preferred Erv's 15-note meantone chain, whose triads are off by 5 to 7 cents, over a 22-note chain that kept ten of the hexany's twelve triads within 2 cents, in the chorale, the tune and the tune over the chorale. I also found I could judge the same pair differently on a reed than on an electric piano, so the electric piano is now my judging standard. In November I finally sat the EAR-ε ladder, 44 blinded detunings, to find where a triad stops locking for me. Under the strictest case (a reed with 16 partials at middle C) a major third holds to 8.43¢ flat and 10.0¢ sharp and a minor third to 7.43¢ on one side and 13.5¢ on the other, and those thresholds are now the EAR reporting tier, shown beside the 2¢ LOCK tier on every result (G-025, G-027). My 25 blind judgments so far are published under CC BY 4.0 in [`experiments/ear_bench/judgments/`](experiments/ear_bench/judgments/), and [JUDGING.md](experiments/ear_bench/JUDGING.md) explains how anyone can judge alongside me.

**What came back to the plugin.** The research reads `Source/` and never edits it, and a finding reaches the plugin only through its own reviewed PR in the plugin lane. Two of the three analyzer bugs are now fixed that way: geometric triads are computed ([#59](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/59), closing [#13](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues/13)), and the triad tolerance is expressed in cents so it no longer depends on register ([#61](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pull/61), closing [#12](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues/12)). The third, the analyzer dropping triads that wrap around the octave, is documented in [`experiments/triads/FINDINGS.md`](experiments/triads/FINDINGS.md) and still open.

### The roads so far

Each row names its experiments and where it stands. The dated, receipt-backed findings are in [`experiments/lattice/FINDINGS.md`](experiments/lattice/FINDINGS.md) and [`experiments/triads/FINDINGS.md`](experiments/triads/FINDINGS.md), and the open questions behind each pending gate are in [`experiments/GATES.md`](experiments/GATES.md).

| Road | Experiments | Where it stands |
|---|---|---|
| **Measuring and listening** | | |
| Triad scorer (frozen, v1.1.0) | HEX-001, LOOP-001 | Decided: classifier ear-validated, balance buckets replace `min(P,S)` (G-001–G-003) |
| Melodic scorer (frozen, v0.1.0) | LAT-MEL-001 | Decided: blind ear check 8 of 8 (G-006) |
| Tolerance set by ear | EPS-TIER-001, 002, EAR-ε | Decided: my lock-loss thresholds (8.43¢ P, 7.43¢ S) are the EAR tier beside LOCK 2¢ (G-025, G-026, G-027) |
| Ear Bench and public judgments | `experiments/ear_bench/` | In use for every scale-emitting experiment |
| **Harmonic structure first** | | |
| Constant-structure eikosanies | CS-EIK-001 | Decided: 32 exist, composite seeds are necessary (G-012) |
| Playing the subsets | SUBSET-MEL-000 | Census done (G-022); the subset scoring spec waits on a brainstorm (G-013) |
| **Erv's reasoning, re-derived** | | |
| D'Alessandro keyboard | BRIDGE-000 | Decided: reproduced exactly, Erv's val tie-optimal (G-014) |
| CPS inside a small MOS | BRIDGE-001, 001b | Decided: refuted at 22 notes or fewer, robust to the tuning objective (G-016, G-021) |
| MOS as cut-and-project windows | MOS-LAT-001, 002 | Closed: null result twice (G-015) |
| Equal temperaments as calibration | ET-001, 002, 003 | Decided (G-017, G-019, G-024) |
| Murchana and the raga lattice | MUR-001, 002 | Decided (G-018, G-020) |
| Shadow tones (comma perturbation) | SHADOW-001 | Decided |
| **Melody fitted around harmony** | | |
| CPS-seeded chain fits | CPSFIT-001, 002, 003 | Judged on the Ear Bench (G-029, G-031, G-032) |
| Two generators (rank 3) | RANK3-001 | Ran; waiting on my ear (G-033) |
| Fork A: one dense MOS for the whole eikosany | SUBFIT-001, 002 | Ran; waiting on my ear and the one-val question (G-036, G-037) |
| Fork B: dynamic MOS per subset | DYNMOS-001 | Ran; waiting on my ear (G-039) |
| **Generators** | | |
| Golden and silver families | GOLD-001, 002, 003 | Ran; strong golden law refuted; selector decision waiting (G-034, G-035, G-038) |
| Recurrences seeded by CPS tones | MERU-001, 002 | Ran; waiting on my ear (G-028, G-030) |
| **Filling the gaps** | | |
| Gap-filling per subset, then one table for the genus | GAPFILL-001, 002, [epimore memo](docs/research-epimore-mediant.md) | Judged on the Ear Bench (G-040, G-041); the next runs (a symmetric completion lister, a propriety-weighted cover) are unblocked |
| **Earmarked, not started** | | |
| Generalized D'Alessandro problem, generator-to-recurrence, an eikosany hexany chorale for the bench | | Ideas on record, each waiting for its moment |

### Where I'm headed, and why

Where do we go from here? The destination is a new scale design in the plugin. You choose an Euler genus on any seeds (the eikosany first), Wilsonic fits it with a one-generator melodic scale chosen by how many of the genus's proportional and subcontrary triads survive, and you move through the genus's subsets as chords while the fitted scale stays playable as melody, on a Gral keyboard with the subset pitches marked. It will be added at the end of the designs list so that existing presets and DAW automation keep working. Three convictions shape how I get there.

- **My ear is the judge.** The triad count is the part I can compute, and I treat it as a proxy. One of my favourite seed sets, 1·45·135·225·19·377, has only 30 exact triads and 12 hexanies with none at all, and I still love how it sounds. When a scale I like scores badly, the measurement gets reported and the decision stays with me.
- **A finding is finished when it runs in the plugin**, deterministically, in bounded time, with its parameters in APVTS, and without touching the designs that already ship. Exhaustive scans keep running alongside as the referee, because I want to follow every line of thought at once.
- **Any seeds, with the octave as the period.** There is no theory yet for choosing good seeds, so nothing in the fitter may depend on one. I keep the octave as the period by conviction, having explored other periods before.

These are the decisions in front of me now, each with its evidence laid out on the [Crossroads](docs/crossroads/index.html) page:

- Which melodic unit the design uses: Fork A, one dense 41- to 72-note MOS on a Gral for the whole genus, or Fork B, a fixed generator whose level and mode change with the selected subset, or both (G-036, G-037, G-039).
- Whether the fit must be a single val. SUBFIT-002 found that the 41-note neutral-third level has no single val, and the Ear Bench's newer generator explorer finds one, so that solve gets rerun before I decide (G-037).
- Which generator families the design offers (the free optimum, golden, silver, Erv's own list, equal temperaments), each shown with its triad cost (G-034, G-035, G-038).
- Where rank 3 goes, whether into a three-generator eikosany fit or into the plugin as a Brun3 design (G-033).

I also try to be modest about what the program cannot see yet. The triad proxy is blind to whatever I hear in seed sets like the one above, the CPS tuning classes are still not compiled under test (the open item in [`experiments/triads/VERIFICATION.md`](experiments/triads/VERIFICATION.md)), and the P = S diagonal results are measured but not yet stated as formal theorems.

### How the work is organized

**Two systems, one search.**

| | The Plugin (`Source/`, `Builds/`) | The Research Harness (`experiments/`) |
|---|---|---|
| **What it is** | The product, C++/JUCE, runs in your DAW | Offline exploration in pure Python, built against stub JUCE headers |
| **What it does** | Plays Erv's designs and broadcasts MTS-ESP | Searches tuning families, fits melody to harmony, exports auditions |
| **Who it's for** | Musicians | The research, and any musician who wants what it finds |
| **Touches the other?** | No | Reads the plugin's source to mirror it and files bugs as issues; never edits it |

**The loop.** Each experiment follows the "autoresearch" pattern. In the inner loop, deterministic code with no LLM in it runs a batch search or an exhaustive scan and writes an append-only archive. In the outer loop, a Claude Code session works on the experiment itself: it pre-registers a hypothesis and its predictions, implements the runner, runs it, and logs hypothesis, result, and kept or reverted. When a run reaches a point that needs a human, the session opens a gate in [`GATES.md`](experiments/GATES.md) and stops there, and only I flip a gate to PASS or FAIL, either in chat, by merging the linked PR, or by saving a verdict on the Ear Bench.

**Frozen referees.** The triad scorer ([`experiments/triads/scorer.py`](experiments/triads/scorer.py), v1.1.0) and the melodic scorer ([`experiments/lattice/melodic.py`](experiments/lattice/melodic.py), v0.1.0) are hash-pinned and checked in CI, because I do not want an optimizer that can change the rules it is scored by. Only I change them, and new measurements go in new files. Every result records the scorer version that produced it, and every claim is graded by the strength of its receipt (READ, SIMULATED, EXECUTED, BIT-EXACT).

**The firewall.** The harness builds a bit-exact mirror of the plugin's tuning math, exports discoveries as playable `.scl` files, and records how to recreate each scale in the plugin. It never modifies a `Source/` file, never changes what the plugin draws or plays, and never touches the APVTS layout, presets or automation. Work moves in three lanes (plugin, research, chore), one lane per PR, as described in [CONTRIBUTING.md](CONTRIBUTING.md).

**The two seams.** The systems meet in two places. The first is cross-validation: the Python mirror ([`cpp_mirror.py`](experiments/triads/cpp_mirror.py)) is validated bit-exact against the compiled C++ (70 hexanies and 15 MOS scales with 0 mismatches, and the geometric triads with 0 mismatches in CROSSVAL-003), and the real `TuningImp`, `Brun` and `MicrotoneArray` run under test. That is what lets me trust an offline score as the scale the plugin would produce. The second is recreation: every `.scl` the harness emits carries a `RECREATE IN WILSONIC` block, so a discovery drops straight back into the plugin.

```
! RECREATE IN WILSONIC:
!   Design: Combination Product Sets
!   Scale: 6_3   [Eikosany (20 tones)]
!   A = 1 ... F = 11
!   APVTS: CPSCALE=6_3, CPSA=1, ... CPSF=11
```

### Where to read more

- **Blog posts:** [The Tunings That Ring](docs/research-blog-001.md) and [The Machine Keeps Deriving Wilson](docs/research-blog-002.md), also published at [wilsonic.co/blog](https://www.wilsonic.co/blog).
- **The lab notebooks:** [`experiments/GATES.md`](experiments/GATES.md) (every decision), the two `FINDINGS.md` files linked above (dated results), the `LOG.md` beside each (run history), [`experiments/lattice/SPEC.md`](experiments/lattice/SPEC.md) (the registered hypotheses), and [`experiments/triads/VERIFICATION.md`](experiments/triads/VERIFICATION.md) (what is grounded, and how hard).
- **Playgrounds** in [`docs/`](docs/index.html): Crossroads, the Lattice MOS-Fit and Lattice Recurrence playgrounds, Comma Dial, Diophantine Harmony, and the Wilson generator landscape. They are single HTML files that run in a browser.
- **The Ear Bench:** source in [`docs/ear-bench/`](docs/ear-bench/); for a MIDI controller, run it locally with `python experiments/ear_bench/serve.py` and open it in Chrome.
- **Design prompts and proposals:** [`prompts/`](prompts/) and [`plans/`](plans/).

## Installation

### macOS

1. Download the latest Wilsonic installer for macOS from the [releases page](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/releases).
2. Open the downloaded `.zip` file and follow the installation wizard.
3. The standalone application will be installed in your Applications folder.
4. Audio Unit (AU) and VST3 plugins will be installed in their respective system folders.

### Windows

1. Download the latest Wilsonic installer for Windows 10 from the [releases page](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/releases).
2. Run the downloaded `.exe` file and follow the installation wizard.
3. The standalone application will be installed in the specified location (default: Program Files).
4. VST3 plugins will be installed in the system VST3 folder.

## Building from Source

### Prerequisites

- JUCE 9.0.1 (Projucer + modules) — the `.jucer` files use the Projucer's global
  module path, which defaults to `~/JUCE/modules`; CI clones the `9.0.1` tag there
- C++17 compatible compiler
- Xcode (for macOS) or Visual Studio (for Windows)

### Build Instructions

1. Clone the repository:
   ```
   git clone https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP.git
   cd Wilsonic-MTS-ESP
   ```

2. Open the Wilsonic.jucer or WilsonicController.jucer file in Projucer.

3. In Projucer, select your target IDE (Xcode for macOS or Visual Studio for Windows) and click "Save and Open in IDE".

4. Build the project in your IDE:
   - For Xcode: Select the desired target and click "Build"
   - For Visual Studio: Select the desired configuration and platform, then build the solution

5. The built standalone application and plugins will be in the "Builds" directory.

For more detailed build commands and platform-specific instructions, see [CLAUDE.md](./CLAUDE.md#build-commands).

## Running Tests

**Plugin unit tests** — compile and run the C++ tests, which exercise the real
tuning code (`TuningImp`, `Brun`, `MicrotoneArray`, …) against stub headers:

```bash
make -C tests run
```

**Research harness tests** — pure Python, no JUCE required (Python 3.12). Each
module has its own suite, and the research CI runs all three:

```bash
cd experiments/triads && python3.12 -m unittest discover -s tests
```

```bash
cd experiments/lattice && python3.12 -m unittest discover -s tests
```

```bash
cd experiments/ear_bench && python3.12 -m unittest discover -s tests
```

The harness also cross-validates its Python mirror against the compiled C++
(`python3.12 crossval001.py`, `crossval002.py`, `crossval003.py`) and enforces
the scorer freezes (`./check_freeze.sh` in `experiments/triads/` and
`experiments/lattice/`). See [How the work is organized](#how-the-work-is-organized) above.

## Usage

The end-user manual lives in this repository at [docs/manual](docs/manual/README.md), and the website renders the same pages at [wilsonic.co/documentation](https://www.wilsonic.co/documentation). Start with the [Quick Start](docs/manual/quick-start.md), and if the app seems silent, read [Which Wilsonic Is Which](docs/manual/which-wilsonic.md).

## Design Philosophy

Wilsonic MTS-ESP is designed to enable professional music production with microtonal scale designs by Erv Wilson in the DAW of your choice, where all the parameters to the scale design are automatable in the DAW.  See [parameters](./daw_automated_params.txt) for a list of the parameters that can be automated.

The source of truth for all state is therefore JUCE's AudioProcessorValueTreeState.  The Processor owns the APVTS and all Models.  The Model objects own the Tuning objects, and bind them to APVTS, and provide an interface for the UI objects.  The Tuning objects are responsible for generating the MTS-ESP data.  Tuning objects know how to draw themselves.  Components delegate drawing to the Model objects, which pass the drawing on to the Tuning objects.  

The Editor is only responsible for rendering the UI, which is implemented as a LookAndFeel and Component hierarchy.  The Editor is not guaranteed to ever be created.

For a detailed technical overview of the architecture and development guidelines, see [CLAUDE.md](./CLAUDE.md#architecture-overview). 

## Contributing

We welcome contributions to Wilsonic! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

For developers: See [CLAUDE.md](./CLAUDE.md) for detailed technical documentation about the codebase architecture, build system, and especially important guidance on adding new scale designs.

## License

The code in this repository is released under the [MIT License](LICENSE).

My listening judgments from the Ear Bench, the files in
`experiments/ear_bench/judgments/`, are released under the
[Creative Commons Attribution 4.0 International licence](LICENSES/CC-BY-4.0.txt).
You can reuse and adapt them for any purpose, commercial work included, as long
as you credit Marcus Hobbs and link back to this repository.

Third-party code this project uses or includes (JUCE, MTS-ESP, and Björn
Ottosson's Oklab colour code) keeps its own licence.

## Acknowledgements

- **Erv Wilson (1928–2016)** — whose theories this project implements and whose search it continues. Everything here is downstream of his work.
- [JUCE](https://juce.com/) - Cross-platform audio application framework
- [MTS-ESP](https://github.com/ODDSound/MTS-ESP) - Microtuning support library

## Contact

For support or inquiries, please [open an issue](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues) on this repository.
