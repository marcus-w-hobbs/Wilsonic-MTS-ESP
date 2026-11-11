#!/usr/bin/env bash
# Write the version from VERSION.txt into every file that carries it.
#
# Usage:
#   scripts/set-version.sh            # read VERSION.txt
#   scripts/set-version.sh 0.45.0-beta  # write VERSION.txt, then proceed
#
# Writes: version.h, Wilsonic.jucer, WilsonicController.jucer.
# Then runs Projucer --resave on both projects when Projucer is found
# (PROJUCER env var, else ~/JUCE/Projucer.app). Builds/ is gitignored, so a
# missing Projucer only means you resave by hand before building.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=version-lib.sh
. "$SELF_DIR/version-lib.sh"

ROOT="$(version_root)"
VERSION_FILE="$ROOT/VERSION.txt"

if [ $# -gt 1 ]; then
    echo "set-version.sh: expected at most one argument" >&2; exit 1
fi
if [ $# -eq 1 ]; then
    printf '%s\n' "$1" > "$VERSION_FILE"
fi
[ -f "$VERSION_FILE" ] || { echo "set-version.sh: $VERSION_FILE not found" >&2; exit 1; }

VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
if ! version_is_valid "$VERSION"; then
    echo "set-version.sh: '$VERSION' is not MAJOR.MINOR.PATCH[-PRERELEASE]" >&2; exit 1
fi
version_parse "$VERSION"

# version.h: regenerate the whole file so the output is deterministic.
version_render_header > "$ROOT/version.h.tmp"
if ! cmp -s "$ROOT/version.h.tmp" "$ROOT/version.h" 2>/dev/null; then
    mv "$ROOT/version.h.tmp" "$ROOT/version.h"
    echo "wrote version.h ($VERSION)"
else
    rm -f "$ROOT/version.h.tmp"
fi

# .jucer: Projucer wants a numeric version, so the pre-release suffix is
# dropped there. Only a three-part version="x.y.z" attribute is touched.
for jucer in Wilsonic.jucer WilsonicController.jucer; do
    f="$ROOT/$jucer"
    [ -f "$f" ] || { echo "set-version.sh: $f not found" >&2; exit 1; }
    sed -E "s/ version=\"[0-9]+\.[0-9]+\.[0-9]+\"/ version=\"$V_CORE\"/" "$f" > "$f.tmp"
    if ! cmp -s "$f.tmp" "$f"; then
        mv "$f.tmp" "$f"
        echo "wrote $jucer ($V_CORE)"
    else
        rm -f "$f.tmp"
    fi
done

# Optional Projucer resave.
PROJUCER_BIN="${PROJUCER:-$HOME/JUCE/Projucer.app/Contents/MacOS/Projucer}"
if [ -x "$PROJUCER_BIN" ]; then
    for jucer in Wilsonic.jucer WilsonicController.jucer; do
        "$PROJUCER_BIN" --resave "$ROOT/$jucer" >/dev/null && echo "resaved $jucer"
    done
else
    echo "Projucer not found at $PROJUCER_BIN; resave both .jucer files before building"
fi
