#!/usr/bin/env bash
# Fail if VERSION.txt, version.h and the two .jucer files disagree.
#
# Usage:
#   scripts/check-version.sh                  # consistency only
#   scripts/check-version.sh --tag v0.45.0-beta  # also require tag == v$(cat VERSION.txt)
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=version-lib.sh
. "$SELF_DIR/version-lib.sh"

ROOT="$(version_root)"
TAG=""
while [ $# -gt 0 ]; do
    case "$1" in
        --tag) TAG="${2:-}"; shift 2 ;;
        *) echo "check-version.sh: unknown argument '$1'" >&2; exit 1 ;;
    esac
done

errors=0
err() { echo "check-version.sh: $*" >&2; errors=$((errors+1)); }

[ -f "$ROOT/VERSION.txt" ] || { err "VERSION.txt not found"; exit 1; }
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION.txt")"
version_is_valid "$VERSION" || { err "'$VERSION' is not MAJOR.MINOR.PATCH[-PRERELEASE]"; exit 1; }
version_parse "$VERSION"

# version.h must equal what set-version.sh would write.
if [ -f "$ROOT/version.h" ]; then
    expected="$(version_render_header)"
    if [ "$expected" != "$(cat "$ROOT/version.h")" ]; then
        err "version.h does not match VERSION=$VERSION (run scripts/set-version.sh)"
    fi
else
    err "version.h not found"
fi

for jucer in Wilsonic.jucer WilsonicController.jucer; do
    f="$ROOT/$jucer"
    if [ -f "$f" ]; then
        got="$(version_jucer "$f")"
        [ "$got" = "$V_CORE" ] || err "$jucer has version=\"$got\", VERSION core is $V_CORE"
    else
        err "$jucer not found"
    fi
done

if [ -n "$TAG" ]; then
    [ "$TAG" = "v$VERSION" ] || err "tag '$TAG' does not match v$VERSION"
fi

if [ "$errors" -gt 0 ]; then
    exit 1
fi
echo "version $VERSION is consistent"
