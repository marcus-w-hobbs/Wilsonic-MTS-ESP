# Contributing to Wilsonic

This repo is **two peer systems in one tree** (see the README): a JUCE audio
plugin and a computational research harness for Erv Wilson's tuning theory.
Contributions flow through pull requests in one of three **lanes**, and the
lanes are designed so plugin developers and researchers never step on each
other.

Most contributors here work with Claude Code (or another coding agent). The
rules below are written to be equally binding on humans and agents.

## The three lanes

| Lane | Branch prefix | You may touch | CI gate |
|---|---|---|---|
| **Plugin** | `plugin/` | `Source/`, `tests/`, `*.jucer`, `version.h`, `Resources/`, `Tunings/` | `plugin.yml`: Linux + macOS builds, C++ unit tests |
| **Research** | `research/` | `experiments/`, `plans/`, `prompts/`, `docs/` | `research.yml`: scorer freeze check + Python suite |
| **Chore** | `chore/` | Everything else: README, CONTRIBUTING, CLAUDE.md, `.github/`, `scripts/` | Whichever workflows the touched paths trigger |

Rules that make parallelism safe:

1. **One lane per PR.** A PR that touches both `Source/` and `experiments/`
   will be asked to split. (Exception: the maintainer may land cross-lane
   changes, e.g. a seam migration — see below.)
2. **The research firewall is one-way.** Research code *reads* plugin source
   (to build its bit-exact mirror) but **never edits it**. Bugs the harness
   finds in `Source/` are filed as GitHub issues, not fixed in research PRs.
3. **The frozen scorer is off-limits to everyone but the maintainer.**
   `experiments/triads/scorer.py` is SHA-pinned and CI-enforced
   (`check_freeze.sh`). If your change fails the freeze check, revert it —
   don't update the pin.

## Worktrees: how to work in parallel

The lane contract lives in the **branch name**; the worktree directory is a
disposable checkout named to match. Use the helper:

```bash
scripts/worktree.sh new plugin gral-keyboard-zoom    # → .claude/worktrees/plugin-gral-keyboard-zoom, branch plugin/gral-keyboard-zoom
scripts/worktree.sh new research lattice-shadow      # research lane, same pattern
scripts/worktree.sh list                             # all worktrees; flags name/branch drift
scripts/worktree.sh done plugin-gral-keyboard-zoom   # safe teardown (refuses dirty/unmerged work)
```

Claude Code sessions that auto-create their own worktrees are fine — the
directory name doesn't matter as much as the branch you eventually PR from.
Before opening the PR, make sure the branch follows the lane prefix (rename
with `git branch -m` if needed).

Worktrees are naturally isolated here: `Builds/` is gitignored and generated
per-checkout by Projucer, and the research harness writes results inside its
own tree. Two caveats when running things from parallel worktrees:

- **MTS-ESP has one master per machine.** Two standalone Wilsonic instances
  from different worktrees will fight over master registration — "my tuning
  change does nothing" usually means the *other* worktree's build won.
  Run one instance at a time when testing tuning output.
- **Don't run two `make -C tests` in the same worktree concurrently**; each
  worktree has its own `tests/build/`, so cross-worktree is fine.

## Choke points: serialize, don't parallelize

A few files are append-ordered or huge-XML and will corrupt user-facing state
(DAW automation, presets) or produce unmergeable diffs if two PRs touch them
at once. **Before starting work that touches one of these, check
`gh pr list` — if an open PR already touches it, coordinate or wait.**

| Choke point | Why |
|---|---|
| `Source/WilsonicProcessor+Params.cpp` | APVTS parameter groups are **order-sensitive**; reordering breaks DAW automation and every saved preset |
| `Source/DesignsModel.{h,cpp}`, `DesignsProtocol.h` | Design registration is **append-only at the END**; index is baked into presets/favorites. Two PRs appending = index collision |
| `Wilsonic.jucer`, `WilsonicController.jucer` | 95 KB XML; every new `Source/` file registers here; parallel edits conflict noisily |
| `Source/all_tunings.json` | Large generated preset data; regeneration in two branches is unmergeable |
| `tests/Makefile` (`CORE_SRCS`) + `tests/research_cli.cpp` | The plugin↔research seam (below) |

Adding a whole new scale design touches ~9 files including the first three
rows — treat it as owning all of them for the life of the PR. Follow the
checklist in `CLAUDE.md` ("Adding New Scale Designs").

## The seam: where plugin work can break research work

The research harness compiles real plugin files headlessly
(`tests/research_cli.cpp` + the `CORE_SRCS` list in `tests/Makefile`) and
mirrors specific `Source/` line ranges in `experiments/triads/cpp_mirror.py`.
This is the **only** place the lanes couple, and the coupling points from
research → plugin, so:

- **Plugin PRs** that touch seam files (`TuningImp.*`, `Microtone.*`,
  `MicrotoneArray.*`, `Brun.*`, `Fraction.*`, `WilsonicMath.*`, anything in
  `CORE_SRCS`): CI builds `research_cli` for you; if your refactor moves code
  the mirror cites by line range, note it in the PR so the maintainer can
  re-run cross-validation (`experiments/triads/crossval*.py`).
- **Research PRs** never modify seam files — extend `research_cli.cpp` output
  only via a plugin-lane or maintainer PR.

## PR mechanics

- Branch from `origin/main`; keep PRs small and single-lane.
- Fill in the PR template — it asks you to declare your lane and check the
  choke-point list.
- CI must be green. Research PRs run in ~1 minute; plugin PRs build JUCE on
  two platforms and take a while — don't push-loop, build locally first
  (`CLAUDE.md` has the commands).
- Commit style: `<type>: <description>` with types
  `feat|fix|refactor|docs|test|chore|perf|ci`.
- Research PRs should update the lab notebook (`experiments/*/LOG.md`,
  `FINDINGS.md`) in the same PR as the results they describe, and every
  result must record the scorer version that produced it.

## Reporting issues

Use the issue templates. For harness-discovered plugin bugs, include the
harness receipt (script + output) that demonstrates the discrepancy.
