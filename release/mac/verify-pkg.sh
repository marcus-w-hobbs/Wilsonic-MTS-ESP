#!/usr/bin/env bash
# Check that a macOS package is signed, notarized and stapled, and that what
# it installs is signed too. Every check runs, each prints what the tool said,
# and one miss fails the script.
#
# Usage: release/mac/verify-pkg.sh <signed.pkg>
#
# Environment:
#   DEVELOPER_ID_APP        the identity every bundle must be signed with
#   DEVELOPER_ID_INSTALLER  the identity the package must be signed with
#
# Checks:
#   pkgutil --check-signature     signed by DEVELOPER_ID_INSTALLER, trusted timestamp
#   spctl -a -vv -t install       Gatekeeper accepts it as Notarized Developer ID
#   xcrun stapler validate        the notarization ticket is stapled
#   codesign --verify --deep --strict on each of the six bundles inside, plus
#     DEVELOPER_ID_APP as the authority, a secure timestamp, the hardened
#     runtime, and no get-task-allow entitlement
#   libMTS.dylib inside           a valid Developer ID signature with a
#     timestamp, and the same bytes as release/mts-esp/PIN
# It also asks spctl about the two apps and prints the answer without failing
# on it, because an app taken out of a package has no ticket of its own.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF_DIR/../.." && pwd)"

die() { echo "verify-pkg.sh: $*" >&2; exit 1; }

PKG="${1:-}"
[ -n "$PKG" ] || die "usage: verify-pkg.sh <signed.pkg>"
[ -f "$PKG" ] || die "$PKG not found"
[ -n "${DEVELOPER_ID_APP:-}" ] || die "DEVELOPER_ID_APP is not set"
[ -n "${DEVELOPER_ID_INSTALLER:-}" ] || die "DEVELOPER_ID_INSTALLER is not set"

WORK="$(mktemp -d -t wilsonic-verify)"
trap 'rm -rf "$WORK"' EXIT

misses=0
miss() { misses=$((misses+1)); echo "verify-pkg.sh: MISS $*" >&2; }
good() { echo "verify-pkg.sh: ok   $*"; }
# Run a command, show its output indented, keep it in $WORK/out, return its status.
run() {
    local rc=0
    echo "\$ $*"
    "$@" > "$WORK/out" 2>&1 </dev/null || rc=$?
    sed 's/^/  /' "$WORK/out"
    return "$rc"
}
said() { grep -qF -- "$1" "$WORK/out"; }

# ---- the package -------------------------------------------------------------
if run pkgutil --check-signature "$PKG"; then
    if said "$DEVELOPER_ID_INSTALLER"; then good "package signed by $DEVELOPER_ID_INSTALLER"
    else miss "package is not signed by \"$DEVELOPER_ID_INSTALLER\""; fi
    if said "Signed with a trusted timestamp"; then good "package signature has a trusted timestamp"
    else miss "package signature has no trusted timestamp"; fi
else
    miss "pkgutil --check-signature failed"
fi

if run spctl -a -vv -t install "$PKG"; then
    if said "source=Notarized Developer ID"; then good "Gatekeeper accepts the package as Notarized Developer ID"
    else miss "spctl accepted the package without saying source=Notarized Developer ID, so this proves nothing about notarization"; fi
else
    miss "Gatekeeper (spctl -t install) does not accept the package"
fi

if run xcrun stapler validate "$PKG"; then good "the notarization ticket is stapled"
else miss "xcrun stapler validate failed"; fi

# ---- what it installs ----------------------------------------------------------
EXP="$WORK/expanded"
pkgutil --expand-full "$PKG" "$EXP"
bundles="$(find "$EXP" -path '*/Payload/*' \( -name '*.app' -o -name '*.component' -o -name '*.vst3' \) -prune -print | sort)"
count="$(printf '%s\n' "$bundles" | grep -c . || true)"
if [ "$count" -eq 6 ]; then good "six bundles in the package"
else miss "expected six bundles in the package, found $count"; fi

while IFS= read -r bundle; do
    [ -n "$bundle" ] || continue
    name="$(basename "$bundle")"
    if run codesign --verify --deep --strict --verbose=2 "$bundle"; then good "$name verifies deeply and strictly"
    else miss "$name: codesign --verify --deep --strict failed"; fi
    run codesign -dvv "$bundle" || true
    if said "Authority=$DEVELOPER_ID_APP"; then good "$name signed by $DEVELOPER_ID_APP"
    else miss "$name is not signed by \"$DEVELOPER_ID_APP\""; fi
    if said "Timestamp="; then good "$name has a secure timestamp"
    else miss "$name has no secure timestamp"; fi
    if grep -q 'flags=.*runtime' "$WORK/out"; then good "$name has the hardened runtime"
    else miss "$name does not have the hardened runtime"; fi
    codesign -d --entitlements - --xml "$bundle" > "$WORK/entitlements" 2>/dev/null </dev/null || true
    if grep -q 'get-task-allow' "$WORK/entitlements"; then miss "$name carries the get-task-allow entitlement"
    else good "$name has no get-task-allow entitlement"; fi
done <<EOF
$bundles
EOF

libmts="$(find "$EXP" -path '*/Payload/libMTS.dylib' -print | head -1)"
if [ -n "$libmts" ]; then
    if run codesign --verify --strict --verbose=2 "$libmts"; then good "libMTS.dylib signature verifies"
    else miss "libMTS.dylib: codesign --verify --strict failed"; fi
    run codesign -dvv "$libmts" || true
    if said "Authority=Developer ID Application:" && said "Timestamp="; then good "libMTS.dylib has a Developer ID signature with a secure timestamp"
    else miss "libMTS.dylib has no Developer ID signature with a secure timestamp"; fi
    pinned="$(grep ' Mac/libMTS.dylib$' "$ROOT/release/mts-esp/PIN" | cut -d' ' -f1)"
    actual="$(shasum -a 256 "$libmts" | cut -d' ' -f1)"
    if [ "$actual" = "$pinned" ]; then good "libMTS.dylib is byte for byte the pinned ODDSound build"
    else miss "libMTS.dylib sha256 $actual does not match release/mts-esp/PIN ($pinned)"; fi
else
    miss "no libMTS.dylib in the package"
fi

# ---- for information: the apps on their own ------------------------------------
while IFS= read -r bundle; do
    case "$bundle" in *.app) ;; *) continue ;; esac
    run spctl -a -vv -t exec "$bundle" \
        || echo "verify-pkg.sh: note: spctl does not accept $(basename "$bundle") on its own (not counted as a miss)"
done <<EOF
$bundles
EOF

echo
if [ "$misses" -ne 0 ]; then
    die "$misses check(s) missed for $(basename "$PKG")"
fi
echo "verify-pkg.sh: all checks passed for $(basename "$PKG")"
