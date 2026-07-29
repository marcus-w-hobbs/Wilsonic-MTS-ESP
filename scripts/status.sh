#!/usr/bin/env bash
# status.sh — one-command research status. Read-only; safe from any worktree.
#
#   ./scripts/status.sh
#
# Answers "status?" without poking around: every worktree (branch, dirty,
# ahead/behind, last commit), every open PR with CI check rollup, every
# PENDING gate from experiments/GATES.md, and per-module experiment state
# (last LOG.md entry, newest receipt in results/).
#
# Nothing here mutates anything. Requires: git, gh (authenticated), jq via gh.

set -euo pipefail

bold=$(tput bold 2>/dev/null || true)
dim=$(tput dim 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)

section() { printf '\n%s== %s ==%s\n' "${bold}" "$1" "${reset}"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "status.sh: not inside a git repository" >&2
  exit 1
}

# ---------------------------------------------------------------------------
section "Worktrees (local, right now)"
# ---------------------------------------------------------------------------
git -C "$ROOT" worktree list --porcelain | awk '/^worktree /{print $2}' |
while read -r wt; do
  branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  ab="no upstream"
  if git -C "$wt" rev-parse --abbrev-ref '@{upstream}' >/dev/null 2>&1; then
    counts=$(git -C "$wt" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null || echo "? ?")
    behind=${counts%%	*}; ahead=${counts##*	}
    ab="ahead ${ahead}, behind ${behind}"
  fi
  last=$(git -C "$wt" log -1 --format='%h %s (%cr)' 2>/dev/null || echo "-")
  printf '%s%s%s\n' "${bold}" "${branch}" "${reset}"
  printf '  %s\n' "${wt}"
  printf '  %s dirty file(s) · %s\n' "${dirty}" "${ab}"
  printf '  %slast: %s%s\n' "${dim}" "${last}" "${reset}"
done

# ---------------------------------------------------------------------------
section "Open PRs (the merge queue)"
# ---------------------------------------------------------------------------
if command -v gh >/dev/null 2>&1; then
  gh pr list --json number,title,headRefName,isDraft,statusCheckRollup --jq '
    if length == 0 then "none — merge queue is empty" else
    .[] | "#\(.number) [\(.headRefName)]\(if .isDraft then " (draft)" else "" end) \(.title)\n    checks: \(
      [.statusCheckRollup[]? | (.conclusion // .state // "PENDING")]
      | if length == 0 then "none"
        else (group_by(.) | map("\(.[0]|ascii_downcase) x\(length)") | join(", ")) end)"
    end' 2>/dev/null || echo "gh query failed (auth? network?)"
else
  echo "gh not installed — see https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/pulls"
fi

# ---------------------------------------------------------------------------
section "Gates waiting on Marcus"
# ---------------------------------------------------------------------------
# GATES.md may not be merged to every branch yet: look in this worktree first,
# then any sibling worktree.
GATES=""
for wt in "$ROOT" $(git -C "$ROOT" worktree list --porcelain | awk '/^worktree /{print $2}'); do
  if [ -f "$wt/experiments/GATES.md" ]; then GATES="$wt/experiments/GATES.md"; break; fi
done
if [ -n "$GATES" ]; then
  printf '%sledger: %s%s\n' "${dim}" "$GATES" "${reset}"
  pending=$(grep -E '^\| G-[0-9]+.*\*\*PENDING\*\*' "$GATES" |
    sed -E 's/^\| (G-[0-9]+) \| [^|]+ \| ([^|]+) \|.*/\1  \2/' || true)
  if [ -n "$pending" ]; then
    printf '%s\n' "$pending"
  else
    echo "none pending — nothing is waiting on you"
  fi
else
  echo "experiments/GATES.md not found in any worktree"
fi

# ---------------------------------------------------------------------------
section "Experiment modules (this worktree's branch)"
# ---------------------------------------------------------------------------
found=0
for d in "$ROOT"/experiments/*/; do
  [ -f "$d/LOG.md" ] || continue
  found=1
  name=$(basename "$d")
  lastlog=$(grep -E '^## ' "$d/LOG.md" | tail -1 | sed 's/^## //')
  printf '%s%s%s\n' "${bold}" "${name}" "${reset}"
  printf '  last log entry: %s\n' "${lastlog:-<none>}"
  if [ -d "$d/results" ]; then
    newest=$(ls -t "$d/results" 2>/dev/null | head -1)
    if [ -n "$newest" ]; then
      when=$(date -r "$d/results/$newest" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "?")
      printf '  newest receipt: results/%s (%s)\n' "$newest" "$when"
    else
      printf '  newest receipt: %snone yet%s\n' "${dim}" "${reset}"
    fi
  fi
done
[ "$found" = 1 ] || echo "no experiments/*/LOG.md on this branch"

printf '\n%sReminder: experiments compute only inside a live Claude session — a quiet\nworktree is an idle worktree, not a stuck one. Dashboard artifact: ask any\nsession to "refresh the dashboard".%s\n' "${dim}" "${reset}"
