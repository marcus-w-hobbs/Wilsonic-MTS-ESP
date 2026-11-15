#!/usr/bin/env bash
# Build the Wilsonic Windows installer from already-built products.
#
# It checks the vendored libMTS files against release/mts-esp/PIN, checks
# that the four products and LIBMTS.dll are x64 PE files, and compiles
# release/windows/wilsonic.iss with Inno Setup's command line compiler. What
# the installer contains and where it puts things is in wilsonic.iss, which
# keeps the v0.43 AppId and install paths so it upgrades a v0.43 install in
# place. Design: plans/release-pipeline.md.
#
# Usage:
#   release/windows/build-installer.sh [--version X.Y.Z[-pre]]
#       [--wilsonic-build DIR] [--controller-build DIR] [--mts-esp DIR] [--out DIR]
#
# Defaults: the version in VERSION.txt, the x64 Release folders of the two
# Visual Studio 2022 exporters, release/mts-esp, and release/out.
#
# Environment:
#   SIGNING=0 (default)  nothing is signed; output ends in -unsigned.exe
#   SIGNING=1            Inno Setup signs the four products, the uninstaller
#                        and the installer with the command in
#                        SIGNTOOL_COMMAND, which must be set and must contain
#                        $f where the file name goes. Nobody has run this path
#                        with a real certificate yet.
#   ISCC                 the Inno Setup compiler (default: ISCC.exe on PATH,
#                        then C:\Program Files (x86)\Inno Setup 6\ISCC.exe).
#                        The test points it at a fake.
#
# Runs on Git Bash (Windows) and, for the test, on bash 3.2 (macOS).
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF_DIR/../.." && pwd)"
# shellcheck source=../../scripts/version-lib.sh
. "$ROOT/scripts/version-lib.sh"

die() { echo "build-installer.sh: $*" >&2; exit 1; }
log() { echo "build-installer.sh: $*"; }

usage() {
    sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
}

VERSION=""
WILSONIC_BUILD="$ROOT/Builds/VisualStudio2022/x64/Release"
CONTROLLER_BUILD="$ROOT/Builds/VisualStudio2022-WilsonicController/x64/Release"
MTS_ESP_DIR="$ROOT/release/mts-esp"
OUT_DIR="$ROOT/release/out"
SCRIPT="$SELF_DIR/wilsonic.iss"
SIGNING="${SIGNING:-0}"
ISCC="${ISCC:-}"

while [ $# -gt 0 ]; do
    case "$1" in
        --version)          VERSION="${2:-}"; shift 2 ;;
        --wilsonic-build)   WILSONIC_BUILD="${2:-}"; shift 2 ;;
        --controller-build) CONTROLLER_BUILD="${2:-}"; shift 2 ;;
        --mts-esp)          MTS_ESP_DIR="${2:-}"; shift 2 ;;
        --out)              OUT_DIR="${2:-}"; shift 2 ;;
        -h|--help)          usage; exit 0 ;;
        *) die "unknown argument '$1' (try --help)" ;;
    esac
done

# ISCC resolves a relative path against the repo root, not the caller's
# folder, so make the three input folders absolute here. One that does not
# exist is left as given; the checks below report it.
abs_dir() {
    if [ -d "$1" ]; then (cd "$1" && pwd); else printf '%s\n' "$1"; fi
}
WILSONIC_BUILD="$(abs_dir "$WILSONIC_BUILD")"
CONTROLLER_BUILD="$(abs_dir "$CONTROLLER_BUILD")"
MTS_ESP_DIR="$(abs_dir "$MTS_ESP_DIR")"

# ---- version ---------------------------------------------------------------
if [ -z "$VERSION" ]; then
    [ -f "$ROOT/VERSION.txt" ] || die "VERSION.txt not found and no --version given"
    VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION.txt")"
fi
version_is_valid "$VERSION" || die "'$VERSION' is not MAJOR.MINOR.PATCH[-PRERELEASE]"

case "$SIGNING" in
    0) SUFFIX="-unsigned" ;;
    1) SUFFIX=""
       [ -n "${SIGNTOOL_COMMAND:-}" ] || die "SIGNING=1 needs SIGNTOOL_COMMAND, the sign command with \$f for the file name" ;;
    *) die "SIGNING must be 0 or 1, got '$SIGNING'" ;;
esac
INSTALLER_NAME="Wilsonic_Win64_v${VERSION}${SUFFIX}.exe"

# ---- the Inno Setup compiler -------------------------------------------------
if [ -z "$ISCC" ]; then
    if command -v ISCC.exe >/dev/null 2>&1; then
        ISCC="$(command -v ISCC.exe)"
    else
        ISCC="/c/Program Files (x86)/Inno Setup 6/ISCC.exe"
    fi
fi
[ -x "$ISCC" ] || die "Inno Setup compiler not found at '$ISCC'; install Inno Setup 6 or set ISCC"
[ -f "$SCRIPT" ] || die "$SCRIPT not found"

# ---- libMTS against PIN ------------------------------------------------------
PIN="$MTS_ESP_DIR/PIN"
[ -f "$PIN" ] || die "$PIN not found"
if command -v shasum >/dev/null 2>&1; then
    SHA="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
    SHA="sha256sum"
else
    die "neither shasum nor sha256sum found"
fi
# shellcheck disable=SC2086
if ! (cd "$MTS_ESP_DIR" && grep -E '^[0-9a-f]{64}  ' PIN | tr -d '\r' | $SHA -c - >/dev/null 2>&1); then
    # shellcheck disable=SC2086
    (cd "$MTS_ESP_DIR" && grep -E '^[0-9a-f]{64}  ' PIN | tr -d '\r' | $SHA -c - >&2) || true
    die "files in $MTS_ESP_DIR do not match PIN; re-vendor from the pinned ODDSound commit"
fi
log "libMTS $(sed -n 's/^libmts_version=//p' "$PIN" | tr -d '\r') matches PIN"

# ---- products ----------------------------------------------------------------
# The machine field of a PE file sits right after the "PE\0\0" signature,
# whose offset is the little-endian 32-bit number at 0x3C. x64 is 0x8664.
pe_machine() { # file -> x64, or the raw bytes, or not-pe
    local f="$1" b o sig
    b="$(od -An -tx1 -j60 -N4 "$f" 2>/dev/null | tr -d ' \n')"
    [ "${#b}" -eq 8 ] || { echo not-pe; return; }
    o=$(( 0x${b:6:2}${b:4:2}${b:2:2}${b:0:2} ))
    sig="$(od -An -tx1 -j"$o" -N6 "$f" 2>/dev/null | tr -d ' \n')"
    case "$sig" in
        504500006486) echo x64 ;;
        50450000*)    echo "machine 0x${sig:10:2}${sig:8:2}" ;;
        *)            echo not-pe ;;
    esac
}
PRODUCTS=(
    "$WILSONIC_BUILD/Standalone Plugin/Wilsonic.exe"
    "$WILSONIC_BUILD/VST3/Wilsonic.vst3/Contents/x86_64-win/Wilsonic.vst3"
    "$CONTROLLER_BUILD/Standalone Plugin/WilsonicController.exe"
    "$CONTROLLER_BUILD/VST3/WilsonicController.vst3/Contents/x86_64-win/WilsonicController.vst3"
    "$MTS_ESP_DIR/Win/64bit/LIBMTS.dll"
)
for p in "${PRODUCTS[@]}"; do
    [ -f "$p" ] || die "product not found: $p (build both projects in Release for x64 first)"
done
for p in "${PRODUCTS[@]}"; do
    m="$(pe_machine "$p")"
    [ "$m" = x64 ] || die "$p is not an x64 PE file ($m); the installer is 64-bit only"
done
log "all four products and LIBMTS.dll are x64"

# ---- compile -----------------------------------------------------------------
# ISCC is a Windows program: give it Windows paths where cygpath exists, and
# stop Git Bash rewriting the /D switches into paths.
winpath() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s\n' "$1"; fi
}
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
ISCC_ARGS=(
    "/DVersion=$VERSION"
    "/DWilsonicBuild=$(winpath "$WILSONIC_BUILD")"
    "/DControllerBuild=$(winpath "$CONTROLLER_BUILD")"
    "/DMtsEspDir=$(winpath "$MTS_ESP_DIR")"
    "/DOutputDir=$(winpath "$OUT_DIR")"
)
if [ "$SIGNING" = 1 ]; then
    ISCC_ARGS+=("/DSigned" "/Swilsonicsign=$SIGNTOOL_COMMAND")
fi
ISCC_ARGS+=("$(winpath "$SCRIPT")")

log "compiling wilsonic.iss for $VERSION with $ISCC (SIGNING=$SIGNING)"
if ! MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$ISCC" "${ISCC_ARGS[@]}"; then
    rm -f "$OUT_DIR/$INSTALLER_NAME"
    die "ISCC failed"
fi
[ -s "$OUT_DIR/$INSTALLER_NAME" ] || die "ISCC succeeded but $OUT_DIR/$INSTALLER_NAME is missing or empty"
log "wrote $OUT_DIR/$INSTALLER_NAME ($(wc -c < "$OUT_DIR/$INSTALLER_NAME" | tr -d ' ') bytes)"
