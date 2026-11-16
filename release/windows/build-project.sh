#!/usr/bin/env bash
# Build one Projucer-generated Visual Studio solution in Release for x64.
#
# It copies ci-build.targets beside the solution as Directory.Build.targets,
# runs msbuild, and then reads the build log to confirm that the two switches
# below did what they say. A switch that silently does nothing would cost
# hours on a hosted runner, which is how the macOS job lost its first two
# runs, so the script fails instead of trusting it.
#
# Usage:
#   release/windows/build-project.sh <path/to/Project.sln>
#
# Environment:
#   LTO=NO (default)            no /GL and no /LTCG, whatever the project says
#   LTO=YES                     leave the Projucer's Release default, which is
#                               whole program optimisation
#   DEBUG_SYMBOLS=YES (default) leave the Projucer's default, which is /Zi and
#                               a .pdb per target
#   DEBUG_SYMBOLS=NO            no /Zi and no .pdb
#   MSBUILD                     msbuild to run (default: msbuild.exe on PATH).
#                               The test points it at a fake.
#
# The log goes to <solution folder>/msbuild-<Project>.log.
# Runs on bash 3.2 (macOS, for the test) and on Git Bash (Windows).
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS="$SELF_DIR/ci-build.targets"

die() { echo "build-project.sh: $*" >&2; exit 1; }
log() { echo "build-project.sh: $*"; }

usage() {
    sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
}

case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") die "no solution given (try --help)" ;;
esac
SLN="$1"
LTO="${LTO:-NO}"
DEBUG_SYMBOLS="${DEBUG_SYMBOLS:-YES}"
MSBUILD="${MSBUILD:-msbuild.exe}"

case "$LTO" in YES|NO) ;; *) die "LTO must be YES or NO, got '$LTO'" ;; esac
case "$DEBUG_SYMBOLS" in YES|NO) ;; *) die "DEBUG_SYMBOLS must be YES or NO, got '$DEBUG_SYMBOLS'" ;; esac
[ -f "$SLN" ] || die "$SLN not found; resave the .jucer with the Projucer first"
[ -f "$TARGETS" ] || die "$TARGETS not found"
command -v "$MSBUILD" >/dev/null 2>&1 || die "msbuild not found ('$MSBUILD'); set MSBUILD or put msbuild.exe on PATH"

SLN_DIR="$(cd "$(dirname "$SLN")" && pwd)"
NAME="$(basename "$SLN" .sln)"
BUILD_LOG="$SLN_DIR/msbuild-$NAME.log"

cp "$TARGETS" "$SLN_DIR/Directory.Build.targets"

# The dash form of each switch, because Git Bash rewrites arguments that
# start with a slash into Windows paths.
ARGS="-m -nologo -v:minimal -p:Configuration=Release -p:Platform=x64"
if [ "$LTO" = NO ]; then
    # The property switches off /GL and the default /LTCG; WilsonicLTO lets
    # ci-build.targets override the explicit LinkTimeCodeGeneration as well.
    ARGS="$ARGS -p:WholeProgramOptimization=false -p:WilsonicLTO=NO"
fi
if [ "$DEBUG_SYMBOLS" = NO ]; then
    ARGS="$ARGS -p:WilsonicDebugSymbols=NO"
fi

# msbuild is a Windows program: give it Windows paths where cygpath exists.
winpath() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s\n' "$1"; fi
}

log "building $NAME (Release, x64, LTO=$LTO, DEBUG_SYMBOLS=$DEBUG_SYMBOLS)"
rm -f "$BUILD_LOG"
# shellcheck disable=SC2086
if ! "$MSBUILD" "$(winpath "$SLN_DIR/$NAME.sln")" $ARGS -fl "-flp:logfile=$(winpath "$BUILD_LOG");verbosity=normal;encoding=UTF-8"; then
    die "msbuild failed for $NAME; the full log is $BUILD_LOG"
fi

# ---- did the switches take? ----------------------------------------------------
[ -f "$BUILD_LOG" ] || die "msbuild wrote no log at $BUILD_LOG, so the switches cannot be checked"
if [ "$LTO" = NO ] || [ "$DEBUG_SYMBOLS" = NO ]; then
    COMPILES="$(grep -i 'cl\.exe .*/c ' "$BUILD_LOG" || true)"
    [ -n "$COMPILES" ] || die "no compiler command line in $BUILD_LOG, so the switches cannot be checked"
    if [ "$LTO" = NO ] && printf '%s\n' "$COMPILES" | grep -q -- ' /GL '; then
        die "LTO=NO, but $NAME was still compiled with /GL; Directory.Build.targets did not take effect"
    fi
    if [ "$DEBUG_SYMBOLS" = NO ]; then
        if printf '%s\n' "$COMPILES" | grep -Eq -- ' /Z[i7I] '; then
            die "DEBUG_SYMBOLS=NO, but $NAME was still compiled with debug information; Directory.Build.targets did not take effect"
        fi
        PDBS="$(find "$SLN_DIR/x64/Release" -name '*.pdb' 2>/dev/null || true)"
        [ -z "$PDBS" ] || die "DEBUG_SYMBOLS=NO, but the build wrote: $PDBS"
    fi
    log "checked the compiler command lines in $(basename "$BUILD_LOG"): LTO=$LTO, DEBUG_SYMBOLS=$DEBUG_SYMBOLS"
fi
log "built $NAME; products under x64/Release:"
find "$SLN_DIR/x64/Release" \( -name '*.exe' -o -name '*.vst3' -o -name '*.pdb' \) -type f 2>/dev/null \
    | sed "s|^$SLN_DIR/|  |" | sort
