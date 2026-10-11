# Wilsonic MTS-ESP

<img src="./Resources/wilsonic_icon_03_512.png" alt="Wilsonic Icon" width="200">

Wilsonic MTS-ESP is an advanced audio plugin and standalone application for creative sound design and music production. It tunes up the software synthesizers in your DAW via MTS-ESP to the scale designs of Erv Wilson; it has a simple synth that you can use to confirm your synths are all in tune.  The Wilsonic Controller target outputs MIDI, while also tuning up all soft synths in your DAW via MTS-ESP.  You can use WilsonicController to perform on Wilson's generalized keyboard designs.

**This repository is two things in service of one search.** The **plugin** lets you *play* Erv Wilson's scale designs. The **research harness** (`experiments/triads/`) lets us *discover new ones* — a computational continuation of the search Wilson pursued by hand across a lifetime of diagrams. Both are first-class here. See [The Research Program](#the-research-program--continuing-erv-wilsons-search).

## Features

- Interactive musical scale design and visualization of the tuning systems of Erv Wilson
- Scale design parameters are automatable in your DAW, and therefore editable
- Standalone application and plugin formats (VST3, AU)
- MTS-ESP support for microtuning
- WilsonicController outputs MIDI, while also tuning up all soft synths in your DAW via MTS-ESP
- Cross-platform compatibility (macOS, Windows)

## The Research Program — Continuing Erv Wilson's Search

Erv Wilson (1928–2016) spent a lifetime searching, by hand, across thousands of diagrams, for scales that solve music's oldest tension at once: structures that serve **melody** (stepwise, singable lines) *and* **harmony** (chords whose overtones reinforce rather than fight). Marcus Hobbs worked at his side from 1995 to 2005, building his designs into software in real time. This codebase is the most complete computational implementation of Wilson's theories — and now, more than that, it is a place to keep searching.

Erv is gone. The search is not. Where Wilson worked with pencil and ear, we now work with a frozen scorer, a bit-exact model of the plugin's own math, and an agent-driven exploration loop that can sweep tuning space and report back the tunings that ring.

> **This is a first-class research program, not a folder of scripts.** The plugin ships; the harness explores. They are peers.

**New here as a researcher?** Start with [The Tunings That Ring](docs/research-blog-001.md) — a living research note covering past/present/future experiments, the scoring function disclosed in full (including its measured limitations), and an open invitation to critique and extend it via [Discussions](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/discussions). Then read [The Machine Keeps Deriving Wilson](docs/research-blog-002.md), the second post, which tells three episodes in which exhaustive searches re-derived Wilson's hand results (the 1975 D'Alessandro template, its pitch-just addressing trick, and the 1993 golden-generator table), with every number linked to its receipt.

### Two systems, one search

| | The Plugin (`Source/`, `Builds/`) | The Research Harness (`experiments/triads/`) |
|---|---|---|
| **What it is** | The product — C++/JUCE, runs in your DAW | Offline exploration — pure Python, no JUCE |
| **What it does** | Plays Wilson's designs, broadcasts MTS-ESP | Searches tuning families, reports winning parameters |
| **Who it's for** | Musicians | The research (and any musician who wants what it finds) |
| **Touches the other?** | No | **Never modifies the plugin** — mirrors it, files bugs as issues |

### Karpathy-style batch exploration

The harness follows the "autoresearch" pattern — an agent in the *outer* loop operating on the **experiment**, deterministic computation in the *inner* loop operating on the **parameters**:

- **Inner loop** (`search.py`, no LLM): deterministic **batch** search over Combination Product Set seed space — exhaustive across small odd seeds, then quality-diversity (MAP-Elites) search over a larger pool. Every candidate scale is generated, scored, and binned by character. Headless, time-boxed, append-only archive that accumulates across runs.
- **Outer loop** (a Claude Code session): operates on the experiment *code and strategy* — proposes a new mutation operator, family, descriptor, or hypothesis; implements it; reruns the batch; keeps the change only if the archive improved. Every run logged **hypothesis → result → kept/reverted**.
- **Frozen scorer** (`scorer.py`, **v1.1.0**, git-tagged): the single source of truth for what counts as a triad, and the reward-hacking firewall — an optimizer that can edit its own verifier is not being verified. Changes require explicit human approval, enforced in CI (SHA-256 pin + agent-loop-commit marker, `check_freeze.sh`). Every result records the scorer version that produced it.

**What the scorer measures — and what the ear confirmed.** A *proportional* (major-type) triad puts its middle tone at the arithmetic mean of the outer frequencies; a *subcontrary* (minor-type) at the harmonic mean; a *geometric* triad at the geometric mean. These are relations on **frequencies**, not cents. Such triads audibly *lock in* — their difference tones reinforce instead of beating. Decades of listening validated the classifier: the scales the loop surfaced are the sonority Wilson was after.

### The firewall — what the harness does NOT do

| The harness... | It does NOT... |
|---|---|
| reads plugin source to build a **bit-exact mirror** of the tuning math | modify, patch, or rebuild any `Source/` file |
| exports discoveries as playable `.scl` files | change what the plugin draws or plays |
| records how to **recreate each scale in the UI** (below) | alter APVTS layout, presets, or DAW automation |
| files plugin bugs it finds as **GitHub issues** | fix them without explicit approval |

Bugs the harness *found* in the plugin's triad analyzer (register-dependent tolerance; geometric triads declared but never computed; octave-wrapping triads silently dropped) are tracked as issues and **deliberately not fixed** here — they are UI-visible behavior changes and a separate decision.

### The two seams

The systems meet at exactly two well-defined places:

- **Cross-validation** — the Python mirror (`cpp_mirror.py`) is validated **bit-exact** against the real compiled C++ (70 hexanies + 15 MOS scales, 0 mismatches), and the real `TuningImp`/`Brun`/`MicrotoneArray` run under test. This is what lets an offline score be trusted as the scale the plugin would produce.
- **Recreation params** — every `.scl` the harness emits carries a `RECREATE IN WILSONIC` comment block, so any discovery drops straight back into the plugin:

  ```
  ! RECREATE IN WILSONIC:
  !   Design: Combination Product Sets
  !   Scale: 6_3   [Eikosany (20 tones)]
  !   A = 1 ... F = 11
  !   APVTS: CPSCALE=6_3, CPSA=1, ... CPSF=11
  ```

### Where the search stands

- **The classifier is ear-validated; the aggregator is open.** `min(P,S)` was demoted from "the loss" to one lens among several (P, S, G, P+S+G) — because P-heavy, S-heavy, *and* G-heavy scales are all worth wanting.
- **Everything is grounded.** Scorer frozen and tagged; Python and C++ suites green; every claim graded by receipt strength (READ → SIMULATED → EXECUTED → BIT-EXACT) in `experiments/triads/VERIFICATION.md`.
- **The lab notebook is public.** `experiments/triads/LOG.md` (run history), `FINDINGS.md` (dated results including the P=S diagonal theorem), `VERIFICATION.md` (what is grounded, and how hard).

### What's next

The search is just getting started:

- **The open puzzle**: Wilson-family scales that sound rich but score low on every current lens (Marcus's eikosany `{1,45,135,225,19,377}` is the standing example) — evidence of an aesthetic axis the metric hasn't captured yet.
- **Widen the net**: larger seed pools, MOS and recurrence-relation families, with the per-character lenses driving selection.
- **Close the last seam**: put the CPS tuning classes under test (the remaining ungrounded item in `VERIFICATION.md`).
- **Prove the theorems**: the P=S diagonal and its consequences are measured; they deserve formal statements.

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

**Research harness tests** — pure Python, no JUCE required (Python 3.12):

```bash
cd experiments/triads && python3.12 -m unittest discover -s tests
```

The harness also cross-validates its Python mirror against the compiled C++
(`python3.12 crossval001.py`, `crossval002.py`) and enforces the scorer freeze
(`./check_freeze.sh`). See the [research harness section](#the-research-harness--karpathy-style-batch-exploration) above.

## Usage

Refer to the [User Manual](https://drive.google.com/file/d/1BrTWlS9N4a0xTRUzwLxwr5R5JJ2RvF8n) for detailed instructions on how to use Wilsonic.

## Design Philosophy

Wilsonic MTS-ESP is designed to enable professional music production with microtonal scale designs by Erv Wilson in the DAW of your choice, where all the parameters to the scale design are automatable in the DAW.  See [parameters](./daw_automated_params.txt) for a list of the parameters that can be automated.

The source of truth for all state is therefore JUCE's AudioProcessorValueTreeState.  The Processor owns the APVTS and all Models.  The Model objects own the Tuning objects, and bind them to APVTS, and provide an interface for the UI objects.  The Tuning objects are responsible for generating the MTS-ESP data.  Tuning objects know how to draw themselves.  Components delegate drawing to the Model objects, which pass the drawing on to the Tuning objects.  

The Editor is only responsible for rendering the UI, which is implemented as a LookAndFeel and Component hierarchy.  The Editor is not guaranteed to ever be created.

For a detailed technical overview of the architecture and development guidelines, see [CLAUDE.md](./CLAUDE.md#architecture-overview). 

## Contributing

We welcome contributions to Wilsonic! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

For developers: See [CLAUDE.md](./CLAUDE.md) for detailed technical documentation about the codebase architecture, build system, and especially important guidance on adding new scale designs.

## License

Wilsonic is released under the [MIT License](LICENSE).

## Acknowledgements

- **Erv Wilson (1928–2016)** — whose theories this project implements and whose search it continues. Everything here is downstream of his work.
- [JUCE](https://juce.com/) - Cross-platform audio application framework
- [MTS-ESP](https://github.com/ODDSound/MTS-ESP) - Microtuning support library

## Contact

For support or inquiries, please [open an issue](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues) on this repository.
