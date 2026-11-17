#!/usr/bin/env bash
# Test for the signing path: signing-keychain.sh, build-pkg.sh with SIGNING=1,
# notarize.sh and verify-pkg.sh. It needs no certificate, no Apple account and
# no network. security, productsign, spctl, xcrun and pkgutil --check-signature
# are faked by small scripts put first on PATH, so nothing here touches a real
# keychain. codesign is a wrapper round the real tool that signs ad hoc, which
# gives real signatures to verify and real entitlements to read.
# Runs on bash 3.2 (macOS). Usage: release/mac/test-signing.sh
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SELF_DIR/../.." && pwd)"
KEYCHAIN_SH="$SELF_DIR/signing-keychain.sh"
BUILD="$SELF_DIR/build-pkg.sh"
NOTARIZE="$SELF_DIR/notarize.sh"
VERIFY="$SELF_DIR/verify-pkg.sh"
# shellcheck source=test-lib.sh
. "$SELF_DIR/test-lib.sh"

SANDBOX="$(mktemp -d -t wilsonic-signing-test)"
# KEEP_SANDBOX=1 leaves the logs behind for a look after a failure.
if [ -n "${KEEP_SANDBOX:-}" ]; then echo "sandbox: $SANDBOX"; else trap 'rm -rf "$SANDBOX"' EXIT; fi
FAKES="$SANDBOX/fakes"
mkdir -p "$FAKES"
export FAKE_LOG="$SANDBOX/calls.log"
: > "$FAKE_LOG"

APP_ID="Developer ID Application: Test Team (TESTTEAM01)"
INSTALLER_ID="Developer ID Installer: Test Team (TESTTEAM01)"

# ---- fakes -------------------------------------------------------------------
cat > "$FAKES/security" <<'FAKE'
#!/bin/bash
echo "security $*" >> "$FAKE_LOG"
last="${@: -1}"
case "$1" in
    create-keychain) : > "$last" ;;
    delete-keychain) rm -f "$last" ;;
    import)
        if [ -n "${FAKE_IMPORT_FAIL:-}" ]; then
            case "$2" in *"$FAKE_IMPORT_FAIL"*)
                echo "security: SecKeychainItemImport: MAC verification failed during PKCS12 import (wrong password?)" >&2
                exit 1 ;;
            esac
        fi ;;
    find-identity) printf '%s\n' "${FAKE_IDENTITIES:-}" ;;
    find-certificate) cat "${FAKE_CERT_PEM:-/dev/null}" ;;
    list-keychains) [ $# -eq 3 ] && echo '    "/Users/someone/Library/Keychains/login.keychain-db"' ;;
esac
exit 0
FAKE

# codesign: every call is recorded. A signing call is passed to the real tool
# with the identity replaced by "-" (ad hoc) and without --timestamp and
# --keychain, which ad hoc signing cannot use. A display call goes to the real
# tool and then, when FAKE_AUTHORITY is set, adds the lines a Developer ID
# signature would show, except for libMTS.dylib, whose real signature has to
# speak for itself. FAKE_ENTITLEMENTS replaces what an entitlements query
# prints. Everything else is the real tool.
cat > "$FAKES/codesign" <<'FAKE'
#!/bin/bash
echo "codesign $*" >> "$FAKE_LOG"
REAL=/usr/bin/codesign
args=(); sign=0; display=0; entitlements=0; skip=""
last="${@: -1}"
for a in "$@"; do
    if [ "$skip" = identity ]; then args+=("-"); skip=""; continue; fi
    if [ "$skip" = drop ]; then skip=""; continue; fi
    case "$a" in
        --sign|-s) sign=1; args+=("$a"); skip=identity ;;
        --timestamp) ;;
        --keychain) skip=drop ;;
        -d|-dv|-dvv|-dvvv|--display) display=1; args+=("$a") ;;
        --entitlements) entitlements=1; args+=("$a") ;;
        *) args+=("$a") ;;
    esac
done
if [ "$sign" = 1 ]; then
    if [ -n "${FAKE_CODESIGN_FAIL:-}" ]; then
        echo "codesign: errSecInternalComponent" >&2
        exit 1
    fi
    exec "$REAL" "${args[@]}"
fi
if [ "$display" = 1 ] && [ "$entitlements" = 1 ] && [ -n "${FAKE_ENTITLEMENTS:-}" ]; then
    printf '%s\n' "$FAKE_ENTITLEMENTS"
    exit 0
fi
if [ "$display" = 1 ]; then
    rc=0
    "$REAL" "$@" || rc=$?
    case "$last" in *libMTS.dylib) exit "$rc" ;; esac
    if [ -n "${FAKE_AUTHORITY:-}" ]; then
        {
            echo "Authority=$FAKE_AUTHORITY"
            echo "Authority=Developer ID Certification Authority"
            echo "Authority=Apple Root CA"
            echo "Timestamp=Nov 16, 2026 at 12:00:00 PM"
        } >&2
    fi
    exit "$rc"
fi
exec "$REAL" "$@"
FAKE

cat > "$FAKES/productsign" <<'FAKE'
#!/bin/bash
echo "productsign $*" >> "$FAKE_LOG"
if [ -n "${FAKE_PRODUCTSIGN_FAIL:-}" ]; then
    echo "productsign: error: Could not find appropriate signing identity" >&2
    exit 1
fi
n=$#
out="${@: -1}"
in="${@: $((n-1)):1}"
cp "$in" "$out"
FAKE

cat > "$FAKES/pkgutil" <<'FAKE'
#!/bin/bash
case " $* " in
    *" --check-signature "*)
        echo "pkgutil $*" >> "$FAKE_LOG"
        printf '%s\n' "${FAKE_PKGUTIL_OUTPUT:-Status: no signature}"
        exit "${FAKE_PKGUTIL_RC:-0}" ;;
esac
exec /usr/sbin/pkgutil "$@"
FAKE

cat > "$FAKES/spctl" <<'FAKE'
#!/bin/bash
echo "spctl $*" >> "$FAKE_LOG"
printf '%s\n' "${FAKE_SPCTL_OUTPUT:-}" >&2
exit "${FAKE_SPCTL_RC:-0}"
FAKE

cat > "$FAKES/xcrun" <<'FAKE'
#!/bin/bash
echo "xcrun $*" >> "$FAKE_LOG"
case "$1 $2" in
    "notarytool history") [ "${FAKE_HISTORY_RC:-0}" -eq 0 ] || echo "Error: HTTP status code: 401. Invalid credentials." >&2
                          exit "${FAKE_HISTORY_RC:-0}" ;;
    "notarytool submit")  printf '%s\n' "${FAKE_SUBMIT_JSON:-}"
                          [ "${FAKE_SUBMIT_RC:-0}" -eq 0 ] || echo "Error: submission failed" >&2
                          exit "${FAKE_SUBMIT_RC:-0}" ;;
    "notarytool log")     printf '%s\n' "${FAKE_NOTARY_LOG:-no log}" ;;
    "stapler staple")     exit "${FAKE_STAPLE_RC:-0}" ;;
    "stapler validate")   exit "${FAKE_VALIDATE_RC:-0}" ;;
    *) echo "fake xcrun: unexpected $*" >&2; exit 64 ;;
esac
FAKE
chmod +x "$FAKES"/*

# Everything under test runs through this, so the fakes win over the real tools.
with_fakes() { PATH="$FAKES:$PATH" "$@"; }
calls() { grep -c -- "$1" "$FAKE_LOG" 2>/dev/null || true; }

# ---- fake secrets ------------------------------------------------------------
# Distinctive strings, so the test can prove that none of them reaches a log.
P12_PASSWORD="p12-password-NEVER-PRINT-ME"
KEY_ID="KEYIDNEVERPRINT"
ISSUER_ID="11111111-2222-3333-4444-neverprintme"
printf 'fake application p12 bytes' > "$SANDBOX/app.p12"
printf 'fake installer p12 bytes' > "$SANDBOX/installer.p12"
printf -- '-----BEGIN PRIVATE KEY-----\nP8BODYNEVERPRINTME\n-----END PRIVATE KEY-----\n' > "$SANDBOX/key.p8"
APP_B64="$(base64 -i "$SANDBOX/app.p12")"
INSTALLER_B64="$(base64 -i "$SANDBOX/installer.p12")"
P8_B64="$(base64 -i "$SANDBOX/key.p8")"

openssl req -x509 -newkey rsa:2048 -nodes -days 400 -subj "/CN=test" \
    -keyout "$SANDBOX/cert-key.pem" -out "$SANDBOX/cert-good.pem" >/dev/null 2>&1
openssl req -x509 -newkey rsa:2048 -nodes -days 10 -subj "/CN=test" \
    -keyout "$SANDBOX/cert-key.pem" -out "$SANDBOX/cert-soon.pem" >/dev/null 2>&1

GOOD_IDENTITIES="  1) 0123456789ABCDEF0123456789ABCDEF01234567 \"$APP_ID\"
  2) 89ABCDEF0123456789ABCDEF0123456789ABCDEF \"$INSTALLER_ID\"
     2 valid identities found"

# Run signing-keychain.sh with a full set of fake secrets. Extra VAR=value
# arguments override or blank any of them.
run_keychain() { # logfile subcommand [VAR=value ...]
    local logfile="$1" sub="$2"; shift 2
    rc=0
    env -u GITHUB_EVENT_NAME \
        SIGNING_DIR="$SIGNING_DIR" GITHUB_ENV="$SANDBOX/github-env" \
        DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" \
        APPLE_DEV_ID_APP_P12="$APP_B64" APPLE_DEV_ID_INSTALLER_P12="$INSTALLER_B64" \
        APPLE_P12_PASSWORD="$P12_PASSWORD" APPLE_API_KEY_ID="$KEY_ID" \
        APPLE_API_ISSUER_ID="$ISSUER_ID" APPLE_API_KEY_P8="$P8_B64" \
        FAKE_IDENTITIES="$GOOD_IDENTITIES" FAKE_CERT_PEM="$SANDBOX/cert-good.pem" \
        PATH="$FAKES:$PATH" "$@" \
        "$KEYCHAIN_SH" "$sub" > "$logfile" 2>&1 || rc=$?
}
expect_no_secret() { # desc logfile
    local leaked=""
    for s in "$P12_PASSWORD" "$KEY_ID" "$ISSUER_ID" "$APP_B64" "$INSTALLER_B64" "$P8_B64" "P8BODYNEVERPRINTME"; do
        if grep -qF -- "$s" "$2" 2>/dev/null; then leaked="$leaked $s"; fi
    done
    if [ -z "$leaked" ]; then ok "$1"; else bad "$1 (found:$leaked)"; fi
}
fresh() { SIGNING_DIR="$SANDBOX/signing-$1"; rm -rf "$SIGNING_DIR"; : > "$FAKE_LOG"; : > "$SANDBOX/github-env"; }

echo "scripts exist and are executable"
for s in "$KEYCHAIN_SH" "$BUILD" "$NOTARIZE" "$VERIFY"; do
    if [ -x "$s" ]; then ok "$(basename "$s") executable"; else bad "$(basename "$s") missing or not executable"; fi
done
if [ ! -x "$KEYCHAIN_SH" ] || [ ! -x "$NOTARIZE" ] || [ ! -x "$VERIFY" ]; then
    finish; exit 1
fi

echo "no script that handles a secret traces its commands"
for s in "$KEYCHAIN_SH" "$NOTARIZE"; do
    expect_no_grep "$(basename "$s") has no set -x" '^[[:space:]]*set -[a-wyz]*x' "$s"
    expect_grep "$(basename "$s") turns tracing off" '^set +x' "$s"
done

# ---- signing-keychain.sh -----------------------------------------------------
echo "signing-keychain.sh setup refuses a run with secrets missing"
fresh missing
run_keychain "$SANDBOX/missing.log" setup APPLE_P12_PASSWORD= APPLE_API_KEY_P8=
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/missing.log"
expect_grep "names APPLE_P12_PASSWORD" "APPLE_P12_PASSWORD" "$SANDBOX/missing.log"
expect_grep "names APPLE_API_KEY_P8" "APPLE_API_KEY_P8" "$SANDBOX/missing.log"
expect_no_grep "does not name a secret that is set" "APPLE_API_KEY_ID" "$SANDBOX/missing.log"
expect_grep "says it will not fall back to unsigned" "unsigned" "$SANDBOX/missing.log"
expect_eq "made no keychain" "$(calls 'security create-keychain')" "0"
expect_no_secret "prints no secret value" "$SANDBOX/missing.log"

echo "signing-keychain.sh setup refuses a pull_request run"
fresh pr
run_keychain "$SANDBOX/pr.log" setup GITHUB_EVENT_NAME=pull_request
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/pr.log"
expect_grep "says why" "pull_request" "$SANDBOX/pr.log"
expect_eq "made no keychain" "$(calls 'security create-keychain')" "0"

echo "signing-keychain.sh setup with good secrets"
fresh good
run_keychain "$SANDBOX/setup.log" setup
expect_zero "exit status 0" "$rc" "$SANDBOX/setup.log"
KEYCHAIN="$SIGNING_DIR/wilsonic-signing.keychain-db"
expect_eq "created one keychain" "$(calls "security create-keychain .*$KEYCHAIN")" "1"
expect_eq "imported two .p12 files" "$(calls 'security import .* -f pkcs12')" "2"
expect_eq "let codesign and productsign use the keys" "$(calls 'security import .*-T /usr/bin/codesign .*-T /usr/bin/productsign')" "2"
expect_eq "set the key partition list" "$(calls 'security set-key-partition-list')" "1"
expect_eq "put the keychain on the search list, keeping the login keychain" \
    "$(calls "security list-keychains -d user -s $KEYCHAIN /Users/someone/Library/Keychains/login.keychain-db")" "1"
expect_no_file "application .p12 deleted after import" "$SIGNING_DIR/developer-id-application.p12"
expect_no_file "installer .p12 deleted after import" "$SIGNING_DIR/developer-id-installer.p12"
expect_file "notary key written" "$SIGNING_DIR/notary-key.p8"
if cmp -s "$SIGNING_DIR/notary-key.p8" "$SANDBOX/key.p8"; then ok "notary key is the decoded secret"; else bad "notary key differs from the decoded secret"; fi
expect_eq "notary key is private" "$(stat -f '%Lp' "$SIGNING_DIR/notary-key.p8" 2>/dev/null)" "600"
expect_eq "signing folder is private" "$(stat -f '%Lp' "$SIGNING_DIR" 2>/dev/null)" "700"
expect_eq "probe-signed with the application identity and a timestamp" \
    "$(calls "codesign .*--timestamp .*--keychain $KEYCHAIN .*--sign $APP_ID")" "1"
expect_eq "probe-signed a package with the installer identity" \
    "$(calls "productsign .*--timestamp .*--keychain $KEYCHAIN .*--sign $INSTALLER_ID")" "1"
expect_eq "checked the API key against App Store Connect" "$(calls 'xcrun notarytool history')" "1"
expect_grep "exports SIGNING_KEYCHAIN to later steps" "^SIGNING_KEYCHAIN=$KEYCHAIN\$" "$SANDBOX/github-env"
expect_grep "exports NOTARY_KEY_FILE to later steps" "^NOTARY_KEY_FILE=$SIGNING_DIR/notary-key.p8\$" "$SANDBOX/github-env"
expect_grep "lists the application identity" "$APP_ID" "$SANDBOX/setup.log"
expect_grep "lists the installer identity" "$INSTALLER_ID" "$SANDBOX/setup.log"
expect_grep "reports when the certificate expires" "expires" "$SANDBOX/setup.log"
expect_no_grep "no expiry warning for a certificate with a year left" "::warning" "$SANDBOX/setup.log"
expect_no_secret "prints no secret value" "$SANDBOX/setup.log"

echo "signing-keychain.sh teardown"
rc=0
SIGNING_DIR="$SIGNING_DIR" with_fakes "$KEYCHAIN_SH" teardown > "$SANDBOX/teardown.log" 2>&1 || rc=$?
expect_zero "exit status 0" "$rc" "$SANDBOX/teardown.log"
expect_eq "deleted the keychain" "$(calls "security delete-keychain $KEYCHAIN")" "1"
expect_no_file "signing folder gone, notary key with it" "$SIGNING_DIR"
rc=0
SIGNING_DIR="$SIGNING_DIR" with_fakes "$KEYCHAIN_SH" teardown > "$SANDBOX/teardown2.log" 2>&1 || rc=$?
expect_zero "a second teardown is harmless" "$rc" "$SANDBOX/teardown2.log"

echo "signing-keychain.sh check tries the secrets out and leaves nothing behind"
fresh check
run_keychain "$SANDBOX/check.log" check
expect_zero "exit status 0" "$rc" "$SANDBOX/check.log"
CHECK_KEYCHAIN="$SIGNING_DIR/wilsonic-signing.keychain-db"
expect_eq "created a keychain" "$(calls "security create-keychain .*$CHECK_KEYCHAIN")" "1"
expect_eq "imported two .p12 files" "$(calls 'security import .* -f pkcs12')" "2"
expect_eq "probe-signed with the application identity" "$(calls "codesign .*--sign $APP_ID")" "1"
expect_eq "probe-signed a package with the installer identity" "$(calls "productsign .*--sign $INSTALLER_ID")" "1"
expect_eq "checked the API key against App Store Connect" "$(calls 'xcrun notarytool history')" "1"
expect_eq "deleted the keychain again" "$(calls "security delete-keychain $CHECK_KEYCHAIN")" "1"
expect_no_file "signing folder gone, notary key with it" "$SIGNING_DIR"
expect_no_grep "exports nothing to later steps" "SIGNING_KEYCHAIN\|NOTARY_KEY_FILE" "$SANDBOX/github-env"
expect_no_secret "prints no secret value" "$SANDBOX/check.log"

echo "signing-keychain.sh check leaves nothing behind when a secret is wrong"
fresh checkfail
run_keychain "$SANDBOX/checkfail.log" check FAKE_HISTORY_RC=1
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/checkfail.log"
expect_grep "names the key id secret" "APPLE_API_KEY_ID" "$SANDBOX/checkfail.log"
expect_eq "deleted the keychain all the same" "$(calls "security delete-keychain $SIGNING_DIR/wilsonic-signing.keychain-db")" "1"
expect_no_file "signing folder gone" "$SIGNING_DIR"

echo "signing-keychain.sh setup twice in a row starts clean"
fresh twice
run_keychain "$SANDBOX/twice1.log" setup
run_keychain "$SANDBOX/twice2.log" setup
expect_zero "second setup exit status 0" "$rc" "$SANDBOX/twice2.log"
expect_eq "took the first keychain off the search list before making the second" \
    "$(calls "security delete-keychain $SIGNING_DIR/wilsonic-signing.keychain-db")" "1"
SIGNING_DIR="$SIGNING_DIR" with_fakes "$KEYCHAIN_SH" teardown > /dev/null 2>&1 || true

echo "signing-keychain.sh setup warns when a certificate is close to expiry"
fresh soon
run_keychain "$SANDBOX/soon.log" setup FAKE_CERT_PEM="$SANDBOX/cert-soon.pem"
expect_zero "still exit status 0" "$rc" "$SANDBOX/soon.log"
expect_grep "warns" "::warning" "$SANDBOX/soon.log"

echo "signing-keychain.sh setup names the secret when a .p12 does not import"
fresh import
run_keychain "$SANDBOX/import.log" setup FAKE_IMPORT_FAIL=developer-id-installer
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/import.log"
expect_grep "names the .p12 secret" "APPLE_DEV_ID_INSTALLER_P12" "$SANDBOX/import.log"
expect_grep "names the password secret" "APPLE_P12_PASSWORD" "$SANDBOX/import.log"
expect_no_secret "prints no secret value" "$SANDBOX/import.log"

echo "signing-keychain.sh setup names the secret when base64 is damaged"
fresh base64
run_keychain "$SANDBOX/base64.log" setup 'APPLE_DEV_ID_APP_P12=***not base64***'
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/base64.log"
expect_grep "names the secret" "APPLE_DEV_ID_APP_P12" "$SANDBOX/base64.log"

echo "signing-keychain.sh setup names the secret when an identity is missing"
fresh identity
run_keychain "$SANDBOX/identity.log" setup \
    "FAKE_IDENTITIES=  1) 0123456789ABCDEF0123456789ABCDEF01234567 \"$APP_ID\"
     1 valid identities found"
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/identity.log"
expect_grep "names the installer .p12 secret" "APPLE_DEV_ID_INSTALLER_P12" "$SANDBOX/identity.log"
expect_grep "names the identity it wanted" "$INSTALLER_ID" "$SANDBOX/identity.log"

echo "signing-keychain.sh setup names the secret when the key cannot sign"
fresh probe
run_keychain "$SANDBOX/probe.log" setup FAKE_CODESIGN_FAIL=1
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/probe.log"
expect_grep "names the application .p12 secret" "APPLE_DEV_ID_APP_P12" "$SANDBOX/probe.log"
expect_grep "shows what codesign said" "  codesign: errSecInternalComponent" "$SANDBOX/probe.log"
expect_grep "mentions the locked keychain as a cause" "keychain is locked" "$SANDBOX/probe.log"

echo "signing-keychain.sh setup names the secret when the .p8 is not a key"
fresh p8
run_keychain "$SANDBOX/p8.log" setup "APPLE_API_KEY_P8=$(printf 'not a key' | base64)"
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/p8.log"
expect_grep "names the secret" "APPLE_API_KEY_P8" "$SANDBOX/p8.log"

echo "signing-keychain.sh setup names the secrets when App Store Connect refuses the key"
fresh history
run_keychain "$SANDBOX/history.log" setup FAKE_HISTORY_RC=1
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/history.log"
expect_grep "names the key id secret" "APPLE_API_KEY_ID" "$SANDBOX/history.log"
expect_grep "names the issuer id secret" "APPLE_API_ISSUER_ID" "$SANDBOX/history.log"
expect_grep "names the .p8 secret" "APPLE_API_KEY_P8" "$SANDBOX/history.log"
expect_grep "shows what notarytool said" "Invalid credentials" "$SANDBOX/history.log"
expect_no_secret "prints no secret value" "$SANDBOX/history.log"

# ---- build-pkg.sh with SIGNING=1 ---------------------------------------------
WBUILD="$SANDBOX/Builds/MacOSX/build/Release"
CBUILD="$SANDBOX/Builds/MacOSX-WilsonicController/build/Release"
STUB_UNIVERSAL="$SANDBOX/stub-universal"
make_stub "$STUB_UNIVERSAL" arm64 x86_64
make_products "$WBUILD" "$CBUILD"
# The two apps arrive from Xcode signed ad hoc with entitlements. One of them
# is the entitlement the .jucer asks for. The other is get-task-allow, which
# Xcode can add to a build and Apple refuses to notarize.
cat > "$SANDBOX/build.entitlements" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>com.apple.security.cs.allow-dyld-environment-variables</key><true/>
<key>com.apple.security.get-task-allow</key><true/>
</dict></plist>
PLIST
# Unsigned copies, for the verify-pkg.sh test at the end.
UNSIGNED_W="$SANDBOX/unsigned/wilsonic"
UNSIGNED_C="$SANDBOX/unsigned/controller"
mkdir -p "$SANDBOX/unsigned"
ditto "$WBUILD" "$UNSIGNED_W"
ditto "$CBUILD" "$UNSIGNED_C"
for b in "$WBUILD"/Wilsonic.app "$CBUILD"/WilsonicController.app; do
    /usr/bin/codesign --force --options runtime --entitlements "$SANDBOX/build.entitlements" --sign - "$b" 2>/dev/null
done
for b in "$WBUILD"/Wilsonic.component "$WBUILD"/Wilsonic.vst3 "$CBUILD"/WilsonicController.component "$CBUILD"/WilsonicController.vst3; do
    /usr/bin/codesign --force --options runtime --sign - "$b" 2>/dev/null
done

echo "build-pkg.sh with SIGNING=1 signs the six products and the package"
: > "$FAKE_LOG"
OUT="$SANDBOX/out"
FAKE_KEYCHAIN="$SANDBOX/fake.keychain-db"
rc=0
SIGNING=1 DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" SIGNING_KEYCHAIN="$FAKE_KEYCHAIN" \
    FAKE_PKGUTIL_OUTPUT="Status: signed by a developer certificate issued by Apple for distribution" \
    with_fakes "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$WBUILD" --controller-build "$CBUILD" \
    --out "$OUT" > "$SANDBOX/build.log" 2>&1 || rc=$?
expect_zero "exit status 0" "$rc" "$SANDBOX/build.log"
PKG="$OUT/Wilsonic_Mac_v${TEST_VERSION}.pkg"
expect_file "product named Wilsonic_Mac_v${TEST_VERSION}.pkg, without -unsigned" "$PKG"
expect_no_file "no -unsigned package beside it" "$OUT/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg"
expect_eq "six signing calls with hardened runtime, a timestamp, the keychain and the application identity" \
    "$(calls "codesign --force --options runtime --timestamp --keychain $FAKE_KEYCHAIN .*--sign $APP_ID")" "6"
for b in Wilsonic.app Wilsonic.component Wilsonic.vst3 WilsonicController.app WilsonicController.component WilsonicController.vst3; do
    expect_eq "signed $b" "$(calls "codesign --force .*--sign $APP_ID .*/$b\$")" "1"
    expect_eq "verified $b deeply and strictly" "$(calls "codesign --verify --deep --strict .*/$b\$")" "1"
done
expect_eq "did not sign libMTS.dylib again" "$(calls 'codesign --force .*libMTS.dylib')" "0"
expect_grep "checked the signature ODDSound put on libMTS.dylib" "libMTS.dylib is signed" "$SANDBOX/build.log"
expect_eq "productsign with a timestamp, the keychain and the installer identity" \
    "$(calls "productsign --timestamp --keychain $FAKE_KEYCHAIN --sign $INSTALLER_ID ")" "1"

if [ -f "$PKG" ]; then
    EXP="$SANDBOX/expanded"
    /usr/sbin/pkgutil --expand-full "$PKG" "$EXP"
    APP_PAYLOAD="$EXP/com.marcussatellite.Wilsonic-MTS-ESP.standalone.pkg/Payload/Wilsonic.app"
    VST_PAYLOAD="$EXP/com.marcussatellite.Wilsonic-MTS-ESP.vst3.pkg/Payload/Wilsonic.vst3"
    MTS_PAYLOAD="$EXP/com.marcussatellite.Wilsonic-MTS-ESP.MTS-ESP-support.pkg/Payload/libMTS.dylib"
    /usr/bin/codesign -d --entitlements - --xml "$APP_PAYLOAD" > "$SANDBOX/app.entitlements" 2>/dev/null || true
    expect_grep "the app keeps the entitlement from the build" "allow-dyld-environment-variables" "$SANDBOX/app.entitlements"
    expect_no_grep "the app loses get-task-allow" "get-task-allow" "$SANDBOX/app.entitlements"
    expect_grep "says that it dropped get-task-allow" "get-task-allow" "$SANDBOX/build.log"
    /usr/bin/codesign -dvv "$APP_PAYLOAD" > "$SANDBOX/app.display" 2>&1 || true
    expect_grep "the app has the hardened runtime" "flags=.*runtime" "$SANDBOX/app.display"
    /usr/bin/codesign -dvv "$VST_PAYLOAD" > "$SANDBOX/vst.display" 2>&1 || true
    expect_grep "the VST3 has the hardened runtime" "flags=.*runtime" "$SANDBOX/vst.display"
    expect_eq "libMTS.dylib still matches the PIN" \
        "$(shasum -a 256 "$MTS_PAYLOAD" | cut -d' ' -f1)" \
        "$(grep ' Mac/libMTS.dylib$' "$REPO/release/mts-esp/PIN" | cut -d' ' -f1)"
else
    bad "no package to expand"
fi

echo "build-pkg.sh with SIGNING=1 refuses a libMTS.dylib without a Developer ID signature"
ADHOC_MTS="$SANDBOX/mts-esp-adhoc"
cp -R "$REPO/release/mts-esp" "$ADHOC_MTS"
/usr/bin/codesign --force --sign - "$ADHOC_MTS/Mac/libMTS.dylib" 2>/dev/null
(cd "$ADHOC_MTS" && { grep -vE '^[0-9a-f]{64}  ' PIN; shasum -a 256 Mac/libMTS.dylib Win/64bit/LIBMTS.dll Win/32bit/LIBMTS.dll MTS-ESP.conf; } > PIN.new && mv PIN.new PIN)
rc=0
SIGNING=1 DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" \
    with_fakes "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$WBUILD" --controller-build "$CBUILD" \
    --mts-esp "$ADHOC_MTS" --out "$SANDBOX/out-adhoc" > "$SANDBOX/adhoc.log" 2>&1 || rc=$?
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/adhoc.log"
expect_grep "names libMTS.dylib" "libMTS.dylib" "$SANDBOX/adhoc.log"
expect_grep "says what is missing" "Developer ID" "$SANDBOX/adhoc.log"
expect_no_file "wrote no package" "$SANDBOX/out-adhoc/Wilsonic_Mac_v${TEST_VERSION}.pkg"

echo "build-pkg.sh with SIGNING=1 refuses a bundle whose entitlements it cannot read"
NOSIG_W="$SANDBOX/nosig/wilsonic"
mkdir -p "$SANDBOX/nosig"
ditto "$WBUILD" "$NOSIG_W"
/usr/bin/codesign --remove-signature "$NOSIG_W/Wilsonic.vst3"
rc=0
SIGNING=1 DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" \
    with_fakes "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$NOSIG_W" --controller-build "$CBUILD" \
    --out "$SANDBOX/out-nosig" > "$SANDBOX/nosig.log" 2>&1 || rc=$?
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/nosig.log"
expect_grep "names the bundle" "entitlements of .*Wilsonic.vst3" "$SANDBOX/nosig.log"
expect_no_file "wrote no package" "$SANDBOX/out-nosig/Wilsonic_Mac_v${TEST_VERSION}.pkg"

echo "build-pkg.sh with SIGNING=1 stops when codesign fails"
rc=0
SIGNING=1 DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" FAKE_CODESIGN_FAIL=1 \
    with_fakes "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$WBUILD" --controller-build "$CBUILD" \
    --out "$SANDBOX/out-codesign" > "$SANDBOX/codesign-fail.log" 2>&1 || rc=$?
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/codesign-fail.log"
expect_no_file "wrote no signed package" "$SANDBOX/out-codesign/Wilsonic_Mac_v${TEST_VERSION}.pkg"
expect_no_file "wrote no unsigned package either" "$SANDBOX/out-codesign/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg"

echo "build-pkg.sh with SIGNING=1 stops when productsign fails"
rc=0
SIGNING=1 DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" FAKE_PRODUCTSIGN_FAIL=1 \
    with_fakes "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$WBUILD" --controller-build "$CBUILD" \
    --out "$SANDBOX/out-productsign" > "$SANDBOX/productsign-fail.log" 2>&1 || rc=$?
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/productsign-fail.log"
expect_no_file "wrote no signed package" "$SANDBOX/out-productsign/Wilsonic_Mac_v${TEST_VERSION}.pkg"
expect_no_file "wrote no unsigned package either" "$SANDBOX/out-productsign/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg"

# ---- notarize.sh -------------------------------------------------------------
run_notarize() { # logfile [VAR=value ...]
    local logfile="$1"; shift
    : > "$FAKE_LOG"
    rc=0
    env NOTARY_KEY_FILE="$SANDBOX/key.p8" APPLE_API_KEY_ID="$KEY_ID" APPLE_API_ISSUER_ID="$ISSUER_ID" \
        PATH="$FAKES:$PATH" "$@" \
        "$NOTARIZE" "$PKG" > "$logfile" 2>&1 || rc=$?
}
SUBMISSION="2efe2717-52ef-43a5-96dc-0797e4ca1041"

echo "notarize.sh staples an accepted package"
run_notarize "$SANDBOX/notarize.log" \
    "FAKE_SUBMIT_JSON={\"id\":\"$SUBMISSION\",\"message\":\"Processing complete\",\"status\":\"Accepted\"}" \
    'FAKE_NOTARY_LOG={"status": "Accepted", "issues": null}'
expect_zero "exit status 0" "$rc" "$SANDBOX/notarize.log"
expect_eq "submitted with the API key and waited" \
    "$(calls "xcrun notarytool submit $PKG --key $SANDBOX/key.p8 --key-id $KEY_ID --issuer $ISSUER_ID --wait")" "1"
expect_eq "fetched the log for the submission" "$(calls "xcrun notarytool log $SUBMISSION ")" "1"
expect_eq "stapled the ticket" "$(calls "xcrun stapler staple $PKG")" "1"
expect_eq "validated the staple" "$(calls "xcrun stapler validate $PKG")" "1"
expect_grep "prints the submission id" "$SUBMISSION" "$SANDBOX/notarize.log"
expect_no_secret "prints no secret value" "$SANDBOX/notarize.log"

echo "notarize.sh fails and prints Apple's log when the package is rejected"
run_notarize "$SANDBOX/rejected.log" \
    "FAKE_SUBMIT_JSON={\"id\":\"$SUBMISSION\",\"message\":\"Processing complete\",\"status\":\"Invalid\"}" \
    'FAKE_NOTARY_LOG={"status": "Invalid", "issues": [{"message": "The signature does not include a secure timestamp."}]}'
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/rejected.log"
expect_eq "fetched the log for the submission" "$(calls "xcrun notarytool log $SUBMISSION ")" "1"
expect_grep "prints the issue from Apple's log" "secure timestamp" "$SANDBOX/rejected.log"
expect_grep "says the status" "Invalid" "$SANDBOX/rejected.log"
expect_eq "did not staple" "$(calls 'xcrun stapler staple')" "0"
expect_no_secret "prints no secret value" "$SANDBOX/rejected.log"

echo "notarize.sh fails when the submission never reaches Apple"
run_notarize "$SANDBOX/nosubmit.log" FAKE_SUBMIT_JSON= FAKE_SUBMIT_RC=1
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/nosubmit.log"
expect_grep "shows what notarytool said" "submission failed" "$SANDBOX/nosubmit.log"
expect_eq "did not staple" "$(calls 'xcrun stapler staple')" "0"

echo "notarize.sh fails when the ticket does not staple"
run_notarize "$SANDBOX/nostaple.log" \
    "FAKE_SUBMIT_JSON={\"id\":\"$SUBMISSION\",\"message\":\"Processing complete\",\"status\":\"Accepted\"}" \
    FAKE_STAPLE_RC=65
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/nostaple.log"

echo "notarize.sh refuses to run without its three settings"
rc=0
env -u APPLE_API_KEY_ID NOTARY_KEY_FILE="$SANDBOX/key.p8" APPLE_API_ISSUER_ID="$ISSUER_ID" PATH="$FAKES:$PATH" \
    "$NOTARIZE" "$PKG" > "$SANDBOX/nokey.log" 2>&1 || rc=$?
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/nokey.log"
expect_grep "names what is missing" "APPLE_API_KEY_ID" "$SANDBOX/nokey.log"

# ---- verify-pkg.sh -----------------------------------------------------------
GOOD_PKGUTIL="Package \"$(basename "$PKG")\":
   Status: signed by a developer certificate issued by Apple for distribution
   Notarization: trusted by the Apple notary service
   Signed with a trusted timestamp on: 2026-11-16 20:00:00 +0000
   Certificate Chain:
    1. $INSTALLER_ID"
GOOD_SPCTL="$PKG: accepted
source=Notarized Developer ID
origin=$INSTALLER_ID"
run_verify() { # logfile [VAR=value ...]
    local logfile="$1"; shift
    : > "$FAKE_LOG"
    rc=0
    env DEVELOPER_ID_APP="$APP_ID" DEVELOPER_ID_INSTALLER="$INSTALLER_ID" \
        FAKE_AUTHORITY="$APP_ID" FAKE_PKGUTIL_OUTPUT="$GOOD_PKGUTIL" FAKE_SPCTL_OUTPUT="$GOOD_SPCTL" \
        PATH="$FAKES:$PATH" "$@" \
        "$VERIFY" "$PKG" > "$logfile" 2>&1 || rc=$?
}

echo "verify-pkg.sh accepts a signed, notarized, stapled package"
run_verify "$SANDBOX/verify.log"
expect_zero "exit status 0" "$rc" "$SANDBOX/verify.log"
expect_eq "ran pkgutil --check-signature" "$(calls "pkgutil --check-signature $PKG")" "1"
expect_eq "ran spctl as an install assessment" "$(calls "spctl -a -vv -t install $PKG")" "1"
expect_eq "ran stapler validate" "$(calls "xcrun stapler validate $PKG")" "1"
expect_eq "ran codesign --verify --deep --strict on six bundles" "$(calls 'codesign --verify --deep --strict')" "6"
expect_grep "shows the spctl verdict" "source=Notarized Developer ID" "$SANDBOX/verify.log"
expect_grep "shows the pkgutil verdict" "trusted by the Apple notary service" "$SANDBOX/verify.log"
expect_grep "says that everything passed" "all checks passed" "$SANDBOX/verify.log"

# Each case must fail for its own reason: exactly one MISS, and the right one.
expect_only_miss() { # desc logfile miss-text
    expect_nonzero "$1" "$rc" "$2"
    expect_grep "$1: says so" "MISS $3" "$2"
    expect_eq "$1: nothing else missed" "$(grep -c 'MISS ' "$2" || true)" "1"
}

echo "verify-pkg.sh fails on each miss"
run_verify "$SANDBOX/v-pkgutil.log" FAKE_PKGUTIL_RC=1 "FAKE_PKGUTIL_OUTPUT=Status: no signature"
expect_only_miss "pkgutil finds no signature" "$SANDBOX/v-pkgutil.log" "pkgutil --check-signature failed"
run_verify "$SANDBOX/v-installer.log" "FAKE_PKGUTIL_OUTPUT=   Status: signed by a developer certificate issued by Apple for distribution
   Signed with a trusted timestamp on: 2026-11-16 20:00:00 +0000
    1. Developer ID Installer: Someone Else (OTHERTEAM1)"
expect_only_miss "package signed by another installer identity" "$SANDBOX/v-installer.log" "package is not signed by"
run_verify "$SANDBOX/v-pkg-timestamp.log" "FAKE_PKGUTIL_OUTPUT=   Status: signed by a developer certificate issued by Apple for distribution
   Signed with an untrusted timestamp on: 2026-11-16 20:00:00 +0000
    1. $INSTALLER_ID"
expect_only_miss "package without a trusted timestamp" "$SANDBOX/v-pkg-timestamp.log" "package signature has no trusted timestamp"
run_verify "$SANDBOX/v-spctl-rc.log" FAKE_SPCTL_RC=3 "FAKE_SPCTL_OUTPUT=$PKG: rejected
source=Unnotarized Developer ID"
expect_only_miss "spctl rejects" "$SANDBOX/v-spctl-rc.log" "Gatekeeper (spctl -t install) does not accept"
expect_grep "shows what spctl said" "Unnotarized" "$SANDBOX/v-spctl-rc.log"
run_verify "$SANDBOX/v-spctl-src.log" "FAKE_SPCTL_OUTPUT=$PKG: accepted
override=security disabled"
expect_only_miss "spctl accepts without saying Notarized Developer ID" "$SANDBOX/v-spctl-src.log" "spctl accepted the package without saying"
run_verify "$SANDBOX/v-staple.log" FAKE_VALIDATE_RC=65
expect_only_miss "stapler validate fails" "$SANDBOX/v-staple.log" "xcrun stapler validate failed"

run_verify "$SANDBOX/v-authority.log" "FAKE_AUTHORITY=Developer ID Application: Someone Else (OTHERTEAM1)"
expect_nonzero "bundles signed by another identity" "$rc" "$SANDBOX/v-authority.log"
expect_eq "six misses, one per bundle, all about the identity" \
    "$(grep -c "MISS .* is not signed by \"$APP_ID\"" "$SANDBOX/v-authority.log" || true)" "6"
expect_eq "and no other miss" "$(grep -c 'MISS ' "$SANDBOX/v-authority.log" || true)" "6"

run_verify "$SANDBOX/v-adhoc.log" FAKE_AUTHORITY=
expect_nonzero "bundles with only an ad hoc signature" "$rc" "$SANDBOX/v-adhoc.log"
expect_eq "six misses about the identity" "$(grep -c 'MISS .* is not signed by' "$SANDBOX/v-adhoc.log" || true)" "6"
expect_eq "six misses about the timestamp" "$(grep -c 'MISS .* has no secure timestamp' "$SANDBOX/v-adhoc.log" || true)" "6"
expect_eq "and no other miss" "$(grep -c 'MISS ' "$SANDBOX/v-adhoc.log" || true)" "12"

run_verify "$SANDBOX/v-taskallow.log" 'FAKE_ENTITLEMENTS=<plist><dict><key>com.apple.security.get-task-allow</key><true/></dict></plist>'
expect_nonzero "bundles that carry get-task-allow" "$rc" "$SANDBOX/v-taskallow.log"
expect_eq "six misses about get-task-allow" "$(grep -c 'MISS .* carries the get-task-allow entitlement' "$SANDBOX/v-taskallow.log" || true)" "6"
expect_eq "and no other miss" "$(grep -c 'MISS ' "$SANDBOX/v-taskallow.log" || true)" "6"

PKG_SIGNED="$PKG"

echo "verify-pkg.sh fails on a package whose libMTS.dylib is not the pinned, signed build"
rc=0
SIGNING=0 "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$WBUILD" --controller-build "$CBUILD" \
    --mts-esp "$ADHOC_MTS" --out "$SANDBOX/out-unpinned" > "$SANDBOX/unpinned-build.log" 2>&1 || rc=$?
expect_zero "built a package around an ad hoc libMTS.dylib" "$rc" "$SANDBOX/unpinned-build.log"
PKG="$SANDBOX/out-unpinned/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg"
# The bundles in it are the ad hoc ones Xcode would leave, which the fake
# vouches for; the fake does not vouch for libMTS.dylib.
run_verify "$SANDBOX/v-unpinned.log" 'FAKE_ENTITLEMENTS=<plist><dict/></plist>'
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/v-unpinned.log"
expect_grep "misses the Developer ID signature" "MISS libMTS.dylib has no Developer ID signature" "$SANDBOX/v-unpinned.log"
expect_grep "misses the PIN" "MISS libMTS.dylib sha256" "$SANDBOX/v-unpinned.log"
expect_eq "and no other miss" "$(grep -c 'MISS ' "$SANDBOX/v-unpinned.log" || true)" "2"

echo "verify-pkg.sh fails on a package with unsigned bundles inside"
rc=0
SIGNING=0 "$BUILD" --version "$TEST_VERSION" --wilsonic-build "$UNSIGNED_W" --controller-build "$UNSIGNED_C" \
    --out "$SANDBOX/out-unsigned" > "$SANDBOX/unsigned-build.log" 2>&1 || rc=$?
expect_zero "built an unsigned package" "$rc" "$SANDBOX/unsigned-build.log"
# These stubs carry only the linker's ad hoc signature of the executable,
# with no sealed bundle and no hardened runtime.
PKG="$SANDBOX/out-unsigned/Wilsonic_Mac_v${TEST_VERSION}-unsigned.pkg"
run_verify "$SANDBOX/v-unsigned.log"
expect_nonzero "non-zero exit" "$rc" "$SANDBOX/v-unsigned.log"
expect_eq "six bundles fail the deep, strict verify" \
    "$(grep -c 'MISS .*codesign --verify --deep --strict failed' "$SANDBOX/v-unsigned.log" || true)" "6"
expect_eq "six bundles lack the hardened runtime" \
    "$(grep -c 'MISS .* does not have the hardened runtime' "$SANDBOX/v-unsigned.log" || true)" "6"
PKG="$PKG_SIGNED"

finish
