#!/usr/bin/env bash
#
# Regenerate the manual's screenshots with the standalone's offscreen
# snapshot mode (see Source/SnapshotMode.h).
#
# Usage:
#   scripts/regenerate_manual_screenshots.sh <path-to-Wilsonic.app-or-binary> [manifest] [output-dir]
#
# Example:
#   scripts/regenerate_manual_screenshots.sh \
#     ~/Library/Developer/Xcode/DerivedData/Wilsonic-*/Build/Products/Debug/Wilsonic.app
#
# Notes:
# - Quit any other running Wilsonic instance first: MTS-ESP allows one
#   master per machine, and a second instance can change what the status
#   indicator shows in the captures.
# - The app window appears briefly while entries render; the process
#   exits by itself, nonzero if any entry failed.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <path-to-Wilsonic.app-or-binary> [manifest] [output-dir]" >&2
    exit 2
fi

APP_PATH="$1"
MANIFEST="${2:-$REPO_ROOT/docs/manual/screenshots.json}"
OUTPUT_DIR="${3:-$REPO_ROOT/docs/manual/images}"

# Accept either the .app bundle or the inner binary.
if [[ -d "$APP_PATH" && "$APP_PATH" == *.app ]]; then
    BINARY="$APP_PATH/Contents/MacOS/$(basename "$APP_PATH" .app)"
else
    BINARY="$APP_PATH"
fi

if [[ ! -x "$BINARY" ]]; then
    echo "error: not an executable: $BINARY" >&2
    exit 2
fi

if [[ ! -f "$MANIFEST" ]]; then
    echo "error: manifest not found: $MANIFEST" >&2
    exit 2
fi

if pgrep -x Wilsonic >/dev/null 2>&1; then
    echo "warning: another Wilsonic instance is running; it holds the MTS-ESP master slot and may affect captures" >&2
fi

echo "rendering $(basename "$MANIFEST") -> $OUTPUT_DIR"
"$BINARY" --snapshot "$MANIFEST" "$OUTPUT_DIR"
echo "done"
