#!/usr/bin/env bash
# Scorer freeze enforcement — plan §3.2 reward-hacking firewall.
#
# scorer.py is the frozen verifier of the triad-optimization loop. An
# optimizer that can edit its own verifier is not being verified. Two
# independent checks, both run by the scorer-freeze CI job:
#
#   A. HASH PIN. scorer.sha256 pins the file's SHA-256. Any edit fails
#      until a human updates the pin. Fails closed on every path — commit
#      message, author and branch are irrelevant.
#   B. AGENT-LOOP MARKER. Commits marked as agent-loop work fail if their
#      diff touches scorer.py. Cheap, and gives a clearer error than A does
#      for the honest case. A commit is marked when EITHER
#        - its SUBJECT (first line) contains the bracketed marker, or
#        - it carries a standalone git trailer line "Agent-Loop: true".
#      Both forms are deliberately narrow: an earlier version matched the
#      marker anywhere in the message, so the commit that DOCUMENTED this
#      mechanism flagged itself. Prose about the guard must not trip it.
#
# Neither check can stop an agent that also rewrites the pin. What they
# buy is that a scorer change can never be SILENT: the pin diff is one
# loud line in review.
#
# Usage:
#   ./check_freeze.sh                  # hash pin only (local default)
#   ./check_freeze.sh <base> <head>    # + marker scan over a commit range
#
# To legitimately change the scorer (Marcus only): edit scorer.py, bump
# SCORER_VERSION, update the pinned version test, then run
#   shasum -a 256 scorer.py | awk '{print $1}' > scorer.sha256
# and tag the new version scorer-vX.Y.Z.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCORER="$HERE/scorer.py"
PIN="$HERE/scorer.sha256"
SUBJECT_MARKER_RE='\[agent-loop\]'                 # first line only
TRAILER_MARKER_RE='^Agent-Loop:[[:space:]]*true[[:space:]]*$'   # standalone line

fail() { echo "FREEZE VIOLATION: $*" >&2; exit 1; }

# ---- check A: hash pin ----------------------------------------------------
[ -f "$PIN" ] || fail "$PIN is missing; the scorer is unpinned."

if command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$SCORER" | awk '{print $1}')"
else
    actual="$(sha256sum "$SCORER" | awk '{print $1}')"
fi
expected="$(tr -d '[:space:]' < "$PIN")"

if [ "$actual" != "$expected" ]; then
    fail "scorer.py does not match its pin.
  expected $expected
  actual   $actual
scorer.py is frozen (plan §3.2). If Marcus approved this change, bump
SCORER_VERSION, update tests/test_scorer.py's pinned version, refresh
scorer.sha256, and tag the new version. Otherwise revert the edit."
fi
echo "freeze check A (hash pin): OK — scorer.py matches $expected"

# ---- check B: agent-loop marker over a commit range -----------------------
if [ $# -eq 2 ] && [ -n "$1" ] && [ "$1" != "0000000000000000000000000000000000000000" ]; then
    base="$1"; head="$2"
    scanned=0
    while read -r sha; do
        [ -n "$sha" ] || continue
        scanned=$((scanned + 1))
        marked=0
        git log -1 --format='%s' "$sha" | grep -Eqi "$SUBJECT_MARKER_RE" && marked=1
        git log -1 --format='%B' "$sha" | grep -Eqi "$TRAILER_MARKER_RE" && marked=1
        if [ "$marked" -eq 1 ]; then
            if git diff-tree --no-commit-id --name-only -r "$sha" \
                | grep -q '^experiments/triads/scorer\.py$'; then
                fail "agent-loop commit $sha modifies scorer.py.
The agent loop has read access to the verifier, never write access
(plan §3.2). Move the change to a human-reviewed commit."
            fi
        fi
    done < <(git rev-list "$base..$head" 2>/dev/null || true)
    echo "freeze check B (agent-loop marker): OK — $scanned commit(s) scanned"
else
    echo "freeze check B (agent-loop marker): skipped — no commit range given"
fi
