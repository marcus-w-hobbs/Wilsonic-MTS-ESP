#!/usr/bin/env bash
# Lane-aware git worktree helper. See CONTRIBUTING.md ("Parallel development").
#
# The contract is carried by the BRANCH NAME (plugin/* | research/* | chore/*);
# the worktree directory is a disposable checkout named to match, so a
# `git worktree list` always tells you what is in flight and in which lane.
#
# Usage:
#   scripts/worktree.sh new <plugin|research|chore> <topic>   # create lane worktree
#   scripts/worktree.sh list                                  # list + flag name/branch drift
#   scripts/worktree.sh done <name> [--force]                 # safe teardown
#
# Teardown refuses to destroy uncommitted or unmerged work unless --force.

set -euo pipefail

fail() { echo "worktree.sh: $*" >&2; exit 1; }

# Resolve the PRIMARY repo root even when run from inside another worktree.
common_dir="$(git rev-parse --path-format=absolute --git-common-dir)" \
    || fail "not inside a git repository"
ROOT="$(dirname "$common_dir")"
WT_DIR="$ROOT/.claude/worktrees"

cmd="${1:-}"

case "$cmd" in
new)
    lane="${2:-}"; topic="${3:-}"
    case "$lane" in plugin|research|chore) ;; *)
        fail "lane must be plugin, research, or chore (got '${lane:-<none>}')
usage: scripts/worktree.sh new <plugin|research|chore> <topic>";;
    esac
    [ -n "$topic" ] || fail "missing <topic> (kebab-case, e.g. gral-keyboard-zoom)"
    case "$topic" in
        *[!a-z0-9-]*) fail "topic must be kebab-case: lowercase letters, digits, hyphens";;
    esac
    branch="$lane/$topic"
    dest="$WT_DIR/$lane-$topic"
    [ -e "$dest" ] && fail "$dest already exists"
    git -C "$ROOT" fetch origin main
    git -C "$ROOT" worktree add "$dest" -b "$branch" origin/main
    echo
    echo "created $dest on branch $branch (from origin/main)"
    echo "next:   cd $dest"
    ;;

list)
    git -C "$ROOT" worktree list
    # Flag worktrees under .claude/worktrees whose directory name does not
    # match their branch — drift makes parallel sessions hard to audit.
    git -C "$ROOT" worktree list --porcelain | awk '
        /^worktree /  { wt = substr($0, 10) }
        /^branch /    { br = substr($0, 8)
                        sub("refs/heads/", "", br)
                        flat = br; gsub("/", "-", flat)
                        n = split(wt, parts, "/"); base = parts[n]
                        # Claude Code auto-worktrees pair dir X with branch
                        # claude/X — that is convention, not drift.
                        if (wt ~ /\.claude\/worktrees\// && base != flat \
                            && br != "claude/" base)
                            printf "  DRIFT: %s is on branch %s\n", base, br }'
    ;;

done)
    name="${2:-}"; force="${3:-}"
    [ -n "$name" ] || fail "usage: scripts/worktree.sh done <worktree-dir-name> [--force]"
    target="$WT_DIR/$name"
    [ -d "$target" ] || fail "$target does not exist (see: scripts/worktree.sh list)"
    branch="$(git -C "$target" rev-parse --abbrev-ref HEAD)"

    if [ -n "$(git -C "$target" status --porcelain)" ] && [ "$force" != "--force" ]; then
        fail "$name has uncommitted changes. Commit or stash them, or pass --force."
    fi
    git -C "$ROOT" fetch origin main
    if ! git -C "$ROOT" merge-base --is-ancestor "$branch" origin/main 2>/dev/null \
        && [ "$force" != "--force" ]; then
        fail "branch $branch is not merged into origin/main. Open/land its PR first, or pass --force."
    fi

    git -C "$ROOT" worktree remove ${force:+--force} "$target"
    [ -e "$target" ] && fail "$target still exists after removal — inspect manually"
    echo "removed worktree $name"
    if git -C "$ROOT" merge-base --is-ancestor "$branch" origin/main 2>/dev/null; then
        git -C "$ROOT" branch -D "$branch"
        echo "deleted merged branch $branch"
    else
        echo "kept branch $branch (not merged)"
    fi
    ;;

*)
    fail "usage:
  scripts/worktree.sh new <plugin|research|chore> <topic>
  scripts/worktree.sh list
  scripts/worktree.sh done <name> [--force]"
    ;;
esac
