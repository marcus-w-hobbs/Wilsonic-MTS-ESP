#!/usr/bin/env bash
# Check that both .jucer files can produce the Visual Studio 2022 solutions
# the Windows release job builds.
#
# For Wilsonic.jucer and WilsonicController.jucer it requires a <VS2022>
# exporter whose targetFolder is the folder the job builds in, with a Release
# configuration. It only reads the files. If something is missing it says
# what, and the fix is a plugin-lane change to a choke-point file, made in the
# Projucer and not here.
#
# Usage: release/windows/check-exporter.sh
#
# Environment:
#   WILSONIC_ROOT  folder holding the two .jucer files (default: the repo
#                  root). The test uses it to point at edited copies.
#
# Runs on bash 3.2 (macOS) and on Git Bash (Windows).
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${WILSONIC_ROOT:-$(cd "$SELF_DIR/../.." && pwd)}"

failures=0
complain() { echo "check-exporter.sh: $*" >&2; failures=$((failures+1)); }

check() { # jucer-name expected-target-folder
    local name="$1" want="$2" file="$ROOT/$1" block folder
    if [ ! -f "$file" ]; then
        complain "$name not found in $ROOT"
        return
    fi
    # Everything from the opening <VS2022 ...> tag to its closing tag.
    block="$(sed -n '/<VS2022[ >]/,/<\/VS2022>/p' "$file" | tr -d '\r')"
    if [ -z "$block" ]; then
        complain "$name has no Visual Studio 2022 exporter (no <VS2022> element under <EXPORTFORMATS>)." \
                 "The Windows job cannot build it. Add the exporter in the Projucer with target folder $want;" \
                 "that is a plugin-lane change to a choke-point file."
        return
    fi
    folder="$(printf '%s\n' "$block" | sed -n 's/.*<VS2022[^>]* targetFolder="\([^"]*\)".*/\1/p' | head -1)"
    if [ "$folder" != "$want" ]; then
        complain "$name exports Visual Studio 2022 to '$folder', but the Windows job builds in '$want'."
        return
    fi
    if ! printf '%s\n' "$block" | grep -q '<CONFIGURATION [^>]*isDebug="0"'; then
        complain "$name has a Visual Studio 2022 exporter with no Release configuration (no CONFIGURATION with isDebug=\"0\")."
        return
    fi
    echo "check-exporter.sh: $name has a Visual Studio 2022 exporter with a Release configuration, target folder $folder"
}

check Wilsonic.jucer Builds/VisualStudio2022
check WilsonicController.jucer Builds/VisualStudio2022-WilsonicController

[ "$failures" -eq 0 ]
