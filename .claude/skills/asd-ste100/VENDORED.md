# Vendored skill: asd-ste100

Source: https://github.com/danyuchn/asd-ste100-skill (MIT, Dustin Yuchen Teng)
Commit: 32511c6992ecb5f1971e46a2943f2e6adceedafe (2026-10-04), skill version 0.4.0
Vendored: 2026-10-09, unmodified (SKILL.md, references/, examples/, scripts/, LICENSE).

Why it is checked in: a skill installed under `~/.claude/skills/` on one
machine is invisible to cloud sessions and to other clones; a skill under
`.claude/skills/` loads for every session on this repository.

Scope note for this repository: the skill's own description limits it to
agent-facing and procedural text (tool descriptions, error messages,
inter-agent instructions, system prompts, status reports) and excludes
creative copy. Project prose for people (site copy, README text, talk
abstracts, posts) follows `.claude/rules/writing-style.md`, which asks for
Marcus's first-person explanatory voice; the two do not overlap.

Linter (manual): `python3 .claude/skills/asd-ste100/scripts/ste-lint.py <file>`
