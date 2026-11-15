#!/usr/bin/env bash
# Build the Wilsonic macOS installer from already-built products.
#
# Seven component packages (pkgbuild), one per product plus the MTS-ESP
# support folder, wrapped by productbuild into one .pkg using
# release/mac/distribution.xml. Identifiers and install locations are the
# ones the v0.43 Packages.app installer used, so this installer upgrades a
# v0.43 install in place. Design: plans/release-pipeline.md.
#
# Usage:
#   release/mac/build-pkg.sh [--version X.Y.Z[-pre]] [--wilsonic-build DIR]
#                            [--controller-build DIR] [--mts-esp DIR] [--out DIR]
#
# Defaults: the version in VERSION.txt, the Release folders plugin.yml builds
# into, release/mts-esp, and release/out.
#
# Environment:
#   SIGNING=0 (default)  no codesign, no productsign; output ends in -unsigned.pkg
#   SIGNING=1            codesign each product with the hardened runtime and a
#                        timestamp using DEVELOPER_ID_APP, then productsign the
#                        product with DEVELOPER_ID_INSTALLER. Both must be set.
#                        Notarization is not done here (Phase 3).
#
# Runs on bash 3.2 (macOS) with only pkgbuild, productbuild, ditto, lipo,
# shasum and PlistBuddy, all part of macOS or the Xcode command line tools.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF_DIR/../.." && pwd)"
# shellcheck source=../../scripts/version-lib.sh
. "$ROOT/scripts/version-lib.sh"

die()  { echo "build-pkg.sh: $*" >&2; exit 1; }
log()  { echo "build-pkg.sh: $*"; }

usage() {
    sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
}

VERSION=""
WILSONIC_BUILD="$ROOT/Builds/MacOSX/build/Release"
CONTROLLER_BUILD="$ROOT/Builds/MacOSX-WilsonicController/build/Release"
MTS_ESP_DIR="$ROOT/release/mts-esp"
OUT_DIR="$ROOT/release/out"
DISTRIBUTION="$SELF_DIR/distribution.xml"
SIGNING="${SIGNING:-0}"

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

# ---- version ---------------------------------------------------------------
if [ -z "$VERSION" ]; then
    VERSION_FILE="$(version_root)/VERSION.txt"
    [ -f "$VERSION_FILE" ] || die "$VERSION_FILE not found and no --version given"
    VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
fi
version_is_valid "$VERSION" || die "'$VERSION' is not MAJOR.MINOR.PATCH[-PRERELEASE]"
version_parse "$VERSION"
# Component packages carry the numeric core (pkgbuild wants dotted integers);
# the product title and the file name carry the full string.
PKG_VERSION="$V_CORE"

# ---- signing configuration -------------------------------------------------
case "$SIGNING" in
    0) ;;
    1)
        [ -n "${DEVELOPER_ID_APP:-}" ] || die "SIGNING=1 needs DEVELOPER_ID_APP (a 'Developer ID Application: ...' identity)"
        [ -n "${DEVELOPER_ID_INSTALLER:-}" ] || die "SIGNING=1 needs DEVELOPER_ID_INSTALLER (a 'Developer ID Installer: ...' identity)"
        ;;
    *) die "SIGNING must be 0 or 1 (got '$SIGNING')" ;;
esac

# ---- the seven components --------------------------------------------------
# name | source folder | package identifier | install location
# The identifier doubles as the component package file name, which is what
# distribution.xml's pkg-ref elements point at.
PRODUCTS="Wilsonic.app|$WILSONIC_BUILD|com.marcussatellite.Wilsonic-MTS-ESP.standalone|/Applications
Wilsonic.component|$WILSONIC_BUILD|com.marcussatellite.Wilsonic-MTS-ESP.component|/Library/Audio/Plug-Ins/Components
Wilsonic.vst3|$WILSONIC_BUILD|com.marcussatellite.Wilsonic-MTS-ESP.vst3|/Library/Audio/Plug-Ins/VST3
WilsonicController.app|$CONTROLLER_BUILD|com.marcussatellite.WilsonicController-MTS-ESP.standalone|/Applications
WilsonicController.component|$CONTROLLER_BUILD|com.marcussatellite.WilsonicController-MTS-ESP.component|/Library/Audio/Plug-Ins/Components
WilsonicController.vst3|$CONTROLLER_BUILD|com.marcussatellite.WilsonicController-MTS-ESP.vst3|/Library/Audio/Plug-Ins/VST3"
MTS_IDENTIFIER="com.marcussatellite.Wilsonic-MTS-ESP.MTS-ESP-support"
MTS_LOCATION="/Library/Application Support/MTS-ESP"

# ---- preflight -------------------------------------------------------------
for tool in pkgbuild productbuild ditto lipo shasum /usr/libexec/PlistBuddy; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool not found"
done
[ -f "$DISTRIBUTION" ] || die "$DISTRIBUTION not found"

missing="$(echo "$PRODUCTS" | while IFS='|' read -r name src _ _; do
    [ -d "$src/$name" ] || echo "$src/$name"
done)"
if [ -n "$missing" ]; then
    echo "build-pkg.sh: products missing, build them first:" >&2
    echo "$missing" | sed 's/^/  /' >&2
    exit 1
fi

# Every product must be a universal binary. A scheme build that lets Xcode
# pick "My Mac" as the destination sets ONLY_ACTIVE_ARCH=YES and quietly
# produces arm64-only bundles, which this installer would then offer to
# Intel Macs. The architectures come back sorted so the order lipo prints
# them in does not matter.
archs_of() { # path -> "arm64 x86_64" or whatever lipo found, or "not a Mach-O binary"
    lipo -archs "$1" 2>/dev/null | tr ' ' '\n' | sort | tr '\n' ' ' | sed 's/ $//' | grep . || echo "not a Mach-O binary"
}
single_arch="$(echo "$PRODUCTS" | while IFS='|' read -r name src _ _; do
    exe="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$src/$name/Contents/Info.plist" 2>/dev/null || true)"
    bin="$src/$name/Contents/MacOS/${exe:-${name%.*}}"
    archs="$(archs_of "$bin")"
    [ "$archs" = "arm64 x86_64" ] || echo "$bin ($archs)"
done)"
if [ -n "$single_arch" ]; then
    echo "build-pkg.sh: products are not universal arm64 x86_64 binaries:" >&2
    echo "$single_arch" | sed 's/^/  /' >&2
    exit 1
fi
log "all six products are universal arm64 x86_64 binaries"

# libMTS must be the pinned bytes before it goes anywhere near a package.
PIN="$MTS_ESP_DIR/PIN"
[ -f "$PIN" ] || die "$PIN not found"
if ! (cd "$MTS_ESP_DIR" && grep -E '^[0-9a-f]{64}  ' PIN | shasum -a 256 -c --status -); then
    (cd "$MTS_ESP_DIR" && grep -E '^[0-9a-f]{64}  ' PIN | shasum -a 256 -c - >&2) || true
    die "files in $MTS_ESP_DIR do not match PIN; re-vendor from the pinned ODDSound commit"
fi
for f in Mac/libMTS.dylib MTS-ESP.conf; do
    [ -f "$MTS_ESP_DIR/$f" ] || die "$MTS_ESP_DIR/$f not found"
done
archs="$(archs_of "$MTS_ESP_DIR/Mac/libMTS.dylib")"
[ "$archs" = "arm64 x86_64" ] || die "libMTS.dylib is '$archs', expected a universal arm64 x86_64 binary"
log "libMTS $(sed -n 's/^libmts_version=//p' "$PIN") matches PIN ($archs)"

# The minimum OS in distribution.xml must be the deployment target the plugin
# was built for, or the installer will accept machines the plugin cannot run on.
if [ -f "$ROOT/Wilsonic.jucer" ]; then
    jucer_min="$(sed -n 's/.*macOSDeploymentTarget="\([^"]*\)".*/\1/p' "$ROOT/Wilsonic.jucer" | head -1)"
    dist_min="$(sed -n 's/.*<os-version min="\([^"]*\)".*/\1/p' "$DISTRIBUTION" | head -1)"
    if [ -n "$jucer_min" ] && [ "$jucer_min" != "$dist_min" ]; then
        die "distribution.xml says os-version min=\"$dist_min\" but Wilsonic.jucer macOSDeploymentTarget is \"$jucer_min\""
    fi
fi

# ---- work area -------------------------------------------------------------
WORK="$(mktemp -d -t wilsonic-pkg)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/roots" "$WORK/plists" "$WORK/components" "$OUT_DIR"

# PlistBuddy's Set fails on a key --analyze left out (plugin bundles get no
# BundleIsRelocatable entry), so fall back to Add.
plist_set() { # plist keypath type value
    /usr/libexec/PlistBuddy -c "Set $2 $4" "$1" 2>/dev/null \
        || /usr/libexec/PlistBuddy -c "Add $2 $3 $4" "$1"
}

# Mark every bundle pkgbuild --analyze found as not relocatable, so Installer
# puts it at the install location even if an old copy sits somewhere else.
pin_bundles() { # component.plist
    local plist="$1" i=0
    while /usr/libexec/PlistBuddy -c "Print :$i" "$plist" >/dev/null 2>&1; do
        plist_set "$plist" ":$i:BundleIsRelocatable" bool false
        plist_set "$plist" ":$i:BundleOverwriteAction" string upgrade
        i=$((i+1))
    done
    [ "$i" -gt 0 ] || die "pkgbuild --analyze found no bundle in $(dirname "$plist")"
}

sign_product() { # bundle path
    [ "$SIGNING" = "1" ] || return 0
    log "codesign $(basename "$1")"
    codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID_APP" "$1"
    codesign --verify --strict "$1"
}

build_component() { # name src identifier location
    local name="$1" src="$2" id="$3" loc="$4"
    local root="$WORK/roots/$id" plist="$WORK/plists/$id.plist"
    mkdir -p "$root"
    ditto "$src/$name" "$root/$name"
    sign_product "$root/$name"
    pkgbuild --analyze --root "$root" "$plist" >/dev/null
    pin_bundles "$plist"
    pkgbuild --quiet --root "$root" --component-plist "$plist" \
        --identifier "$id" --version "$PKG_VERSION" --install-location "$loc" \
        "$WORK/components/$id.pkg"
    log "built $id.pkg ($name -> $loc)"
}

echo "$PRODUCTS" | while IFS='|' read -r name src id loc; do
    build_component "$name" "$src" "$id" "$loc"
done

# MTS-ESP support: plain files, no bundle, so no component plist.
mts_root="$WORK/roots/$MTS_IDENTIFIER"
mkdir -p "$mts_root"
cp "$MTS_ESP_DIR/Mac/libMTS.dylib" "$mts_root/libMTS.dylib"
cp "$MTS_ESP_DIR/MTS-ESP.conf" "$mts_root/MTS-ESP.conf"
chmod 755 "$mts_root/libMTS.dylib"
chmod 644 "$mts_root/MTS-ESP.conf"
pkgbuild --quiet --root "$mts_root" \
    --identifier "$MTS_IDENTIFIER" --version "$PKG_VERSION" --install-location "$MTS_LOCATION" \
    "$WORK/components/$MTS_IDENTIFIER.pkg"
log "built $MTS_IDENTIFIER.pkg (libMTS.dylib, MTS-ESP.conf -> $MTS_LOCATION)"

# ---- product ---------------------------------------------------------------
sed "s/__VERSION__/$VERSION/g" "$DISTRIBUTION" > "$WORK/distribution.xml"
productbuild --quiet --distribution "$WORK/distribution.xml" \
    --package-path "$WORK/components" --version "$VERSION" \
    "$WORK/product.pkg"

if [ "$SIGNING" = "1" ]; then
    PKG="$OUT_DIR/Wilsonic_Mac_v$VERSION.pkg"
    rm -f "$PKG"
    productsign --sign "$DEVELOPER_ID_INSTALLER" "$WORK/product.pkg" "$PKG"
    pkgutil --check-signature "$PKG"
else
    PKG="$OUT_DIR/Wilsonic_Mac_v$VERSION-unsigned.pkg"
    rm -f "$PKG"
    cp "$WORK/product.pkg" "$PKG"
fi
log "wrote $PKG"
