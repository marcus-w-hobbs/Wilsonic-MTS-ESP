#!/usr/bin/env bash
# Test for release/mac/build-pkg.sh. It needs no Xcode build and no signing
# certificate: it fabricates the six product bundles, packages them with
# SIGNING=0, expands the result with pkgutil and checks what came out.
# Runs on bash 3.2 (macOS). Usage: release/mac/test-build-pkg.sh
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SELF_DIR/../.." && pwd)"
BUILD="$SELF_DIR/build-pkg.sh"
# shellcheck source=test-lib.sh
. "$SELF_DIR/test-lib.sh"

SANDBOX="$(mktemp -d -t wilsonic-pkg-test)"
trap 'rm -rf "$SANDBOX"' EXIT
WBUILD="$SANDBOX/Builds/MacOSX/build/Release"
CBUILD="$SANDBOX/Builds/MacOSX-WilsonicController/build/Release"
OUT="$SANDBOX/out"
STUB_UNIVERSAL="$SANDBOX/stub-universal"
STUB_ARM64="$SANDBOX/stub-arm64"
make_stub "$STUB_UNIVERSAL" arm64 x86_64
make_stub "$STUB_ARM64" arm64
make_products "$WBUILD" "$CBUILD"

echo "script exists and is executable"
[ -x "$BUILD" ] && ok "build-pkg.sh executable" || bad "build-pkg.sh missing or not executable"

echo "build-pkg.sh packages fake bundles unsigned"
rc=0
SIGNING=0 "$BUILD" \
    --version "$TEST_VERSION" \
    --wilsonic-build "$WBUILD" \
    --controller-build "$CBUILD" \
    --out "$OUT" > "$SANDBOX/build.log" 2>&1 || rc=$?
if [ "$rc" -eq 0 ]; then ok "exit status 0"; else bad "exit status $rc"; sed 's/^/    | /' "$SANDBOX/build.log"; fi
expect_grep "checked that the products are universal" "universal arm64 x86_64" "$SANDBOX/build.log"

PKG="$OUT/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg"
expect_file "product named Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg" "$PKG"
if [ ! -f "$PKG" ]; then
    echo; echo "$pass passed, $fail failed"; exit 1
fi

EXP="$SANDBOX/expanded"
pkgutil --expand-full "$PKG" "$EXP"
DIST="$EXP/Distribution"

echo "distribution"
expect_file "Distribution present" "$DIST"
expect_grep "hostArchitectures x86_64,arm64" 'hostArchitectures="x86_64,arm64"' "$DIST"
expect_grep "minimum macOS 10.13 (from the .jucer deployment target)" '<os-version min="10.13"' "$DIST"
expect_grep "title names Wilsonic" '<title>Wilsonic' "$DIST"
expect_grep "product version is the full version" "<product version=\"$TEST_VERSION\"" "$DIST"
expect_grep "installs to the system domain" 'enable_localSystem="true"' "$DIST"
expect_eq "seven choices in the outline" "$(grep -c '<line choice=' "$DIST")" "7"

echo "component packages"
expect_eq "seven component packages" "$(find "$EXP" -name PackageInfo | wc -l | tr -d ' ')" "7"
check_component() { # identifier install-location payload-entry
    local id="$1" loc="$2" entry="$3" info
    info="$(grep -l "identifier=\"$id\"" "$EXP"/*/PackageInfo 2>/dev/null | head -1)"
    if [ -z "$info" ]; then bad "$id present"; return; fi
    ok "$id present"
    expect_grep "$id version $TEST_CORE" "version=\"$TEST_CORE\"" "$info"
    expect_grep "$id installs to $loc" "install-location=\"$loc\"" "$info"
    expect_file "$id payload has $entry" "$(dirname "$info")/Payload/$entry"
}
check_component com.marcussatellite.Wilsonic-MTS-ESP.standalone /Applications Wilsonic.app
check_component com.marcussatellite.Wilsonic-MTS-ESP.component /Library/Audio/Plug-Ins/Components Wilsonic.component
check_component com.marcussatellite.Wilsonic-MTS-ESP.vst3 /Library/Audio/Plug-Ins/VST3 Wilsonic.vst3
check_component com.marcussatellite.WilsonicController-MTS-ESP.standalone /Applications WilsonicController.app
check_component com.marcussatellite.WilsonicController-MTS-ESP.component /Library/Audio/Plug-Ins/Components WilsonicController.component
check_component com.marcussatellite.WilsonicController-MTS-ESP.vst3 /Library/Audio/Plug-Ins/VST3 WilsonicController.vst3
check_component com.marcussatellite.Wilsonic-MTS-ESP.MTS-ESP-support "/Library/Application Support/MTS-ESP" libMTS.dylib

echo "bundles are not relocatable"
for info in "$EXP"/*/PackageInfo; do
    if grep -q '<bundle path=' "$info"; then
        expect_no_grep "$(basename "$(dirname "$info")") has no <relocate> bundle" '<relocate>' "$info"
    fi
done

echo "MTS-ESP support payload"
MTS_INFO="$(grep -l 'identifier="com.marcussatellite.Wilsonic-MTS-ESP.MTS-ESP-support"' "$EXP"/*/PackageInfo | head -1)"
MTS_PAYLOAD="$(dirname "$MTS_INFO")/Payload"
expect_file "libMTS.dylib" "$MTS_PAYLOAD/libMTS.dylib"
expect_file "MTS-ESP.conf" "$MTS_PAYLOAD/MTS-ESP.conf"
expect_eq "libMTS.dylib matches the PIN" \
    "$(shasum -a 256 "$MTS_PAYLOAD/libMTS.dylib" | cut -d' ' -f1)" \
    "$(grep ' Mac/libMTS.dylib$' "$REPO/release/mts-esp/PIN" | cut -d' ' -f1)"
expect_eq "libMTS.dylib is universal" "$(lipo -archs "$MTS_PAYLOAD/libMTS.dylib")" "x86_64 arm64"

echo "build-pkg.sh refuses a libMTS that does not match the PIN"
TAMPERED="$SANDBOX/mts-esp"
cp -R "$REPO/release/mts-esp" "$TAMPERED"
echo "# tampered" >> "$TAMPERED/MTS-ESP.conf"
rc=0
SIGNING=0 "$BUILD" \
    --version "$TEST_VERSION" \
    --wilsonic-build "$WBUILD" \
    --controller-build "$CBUILD" \
    --mts-esp "$TAMPERED" \
    --out "$SANDBOX/out-tampered" > "$SANDBOX/tampered.log" 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then ok "non-zero exit on PIN mismatch"; else bad "accepted a tampered MTS-ESP.conf"; fi
expect_grep "names the PIN in the error" "PIN" "$SANDBOX/tampered.log"
[ -e "$SANDBOX/out-tampered/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg" ] \
    && bad "wrote a pkg despite the PIN mismatch" || ok "wrote no pkg"

echo "build-pkg.sh refuses a product that is not universal"
SINGLE="$SANDBOX/single"
ditto "$WBUILD" "$SINGLE"
cp "$STUB_ARM64" "$SINGLE/Wilsonic.vst3/Contents/MacOS/Wilsonic"
rc=0
SIGNING=0 "$BUILD" \
    --version "$TEST_VERSION" \
    --wilsonic-build "$SINGLE" \
    --controller-build "$CBUILD" \
    --out "$SANDBOX/out-single" > "$SANDBOX/single.log" 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then ok "non-zero exit on an arm64-only product"; else bad "packaged an arm64-only product"; fi
expect_grep "names the single-arch product" "Wilsonic.vst3" "$SANDBOX/single.log"
expect_grep "reports what lipo found" "(arm64)" "$SANDBOX/single.log"
[ -e "$SANDBOX/out-single/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg" ] \
    && bad "wrote a pkg despite the single-arch product" || ok "wrote no pkg"

echo "build-pkg.sh refuses a missing product"
rm -rf "$CBUILD/WilsonicController.vst3"
rc=0
SIGNING=0 "$BUILD" \
    --version "$TEST_VERSION" \
    --wilsonic-build "$WBUILD" \
    --controller-build "$CBUILD" \
    --out "$SANDBOX/out-missing" > "$SANDBOX/missing.log" 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then ok "non-zero exit on a missing product"; else bad "packaged with a product missing"; fi
expect_grep "names the missing product" "WilsonicController.vst3" "$SANDBOX/missing.log"

finish
