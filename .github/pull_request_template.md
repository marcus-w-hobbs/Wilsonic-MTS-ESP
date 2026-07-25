# PR

## Lane

<!-- Pick exactly one — see CONTRIBUTING.md. One lane per PR. -->

- [ ] **Plugin** (`plugin/*` — `Source/`, `tests/`, `*.jucer`)
- [ ] **Research** (`research/*` — `experiments/`, `plans/`, `prompts/`, `docs/`)
- [ ] **Chore** (`chore/*` — docs, CI, scripts, config)

## What & why

<!-- A few sentences. For research PRs: which experiment IDs, and which
     scorer version produced the results. -->

## Choke points

<!-- Check any that this PR touches, and confirm no other open PR touches
     the same one (gh pr list). Leave unchecked if none. -->

- [ ] `Source/WilsonicProcessor+Params.cpp` (APVTS order — append only)
- [ ] `Source/DesignsModel.*` / `DesignsProtocol.h` (design registry — append at END)
- [ ] `Wilsonic.jucer` / `WilsonicController.jucer`
- [ ] `Source/all_tunings.json`
- [ ] Seam files (`CORE_SRCS` in `tests/Makefile`, `tests/research_cli.cpp`) —
      if a refactor moved code that `experiments/triads/cpp_mirror.py` cites
      by line range, say so here

## Test plan

<!-- Plugin: local build + `make -C tests run`. Research: harness suite +
     notebook (LOG.md/FINDINGS.md) updated in this PR. -->
