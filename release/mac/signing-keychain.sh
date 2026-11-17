#!/usr/bin/env bash
# The temporary keychain a signed release build signs from, and the check that
# every Apple secret works before the long build starts.
#
# Usage:
#   release/mac/signing-keychain.sh check      # try out the six secrets, then delete everything again
#   release/mac/signing-keychain.sh setup      # the six secrets -> a keychain and a notary key file
#   release/mac/signing-keychain.sh teardown   # delete the keychain and every decoded file
#
# The workflow runs check before the long build and setup just before the
# signing step, so the keychain and the decoded key exist only while the
# steps that sign and notarize are running, and never while JUCE, the
# Projucer and xcodebuild run.
#
# check and setup read six secrets from the environment and fail, naming the
# secret, as soon as one is missing or does not work:
#   APPLE_DEV_ID_APP_P12        base64 of the Developer ID Application .p12
#   APPLE_DEV_ID_INSTALLER_P12  base64 of the Developer ID Installer .p12
#   APPLE_P12_PASSWORD          the password both .p12 files were exported with
#   APPLE_API_KEY_ID            App Store Connect API key ID
#   APPLE_API_ISSUER_ID         App Store Connect issuer ID
#   APPLE_API_KEY_P8            base64 of the .p8 private key
# and the two identity names it must find in them:
#   DEVELOPER_ID_APP            "Developer ID Application: ... (TEAMID)"
#   DEVELOPER_ID_INSTALLER      "Developer ID Installer: ... (TEAMID)"
#
# Both then sign a scratch file with each identity and ask App Store Connect
# for the notarization history, so a wrong password, an expired certificate or
# a wrong issuer ID stops the job in its first minute and not after the build.
# Nothing is submitted to Apple here.
#
# Everything lives in SIGNING_DIR (default $RUNNER_TEMP/wilsonic-signing).
# setup writes SIGNING_KEYCHAIN and NOTARY_KEY_FILE to $GITHUB_ENV for the
# later steps. check and setup refuse to run on a pull_request event.
#
# This script never prints a secret, and tracing is switched off below so a
# caller's `bash -x` cannot print one either.
set -euo pipefail
set +x

die() { echo "signing-keychain.sh: $*" >&2; exit 1; }
log() { echo "signing-keychain.sh: $*"; }

SIGNING_DIR="${SIGNING_DIR:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/wilsonic-signing}"
KEYCHAIN="$SIGNING_DIR/wilsonic-signing.keychain-db"
NOTARY_KEY="$SIGNING_DIR/notary-key.p8"
SECRET_NAMES="APPLE_DEV_ID_APP_P12 APPLE_DEV_ID_INSTALLER_P12 APPLE_P12_PASSWORD APPLE_API_KEY_ID APPLE_API_ISSUER_ID APPLE_API_KEY_P8"
# Warn when a certificate has less than this many days left.
EXPIRY_WARNING_DAYS=45

decode_secret() { # secret-name out-file
    local name="$1" out="$2"
    if ! printf '%s' "${!name}" | tr -d '[:space:]' | base64 --decode > "$out" 2>/dev/null || [ ! -s "$out" ]; then
        rm -f "$out"
        die "$name is not valid base64. It should be the single line that 'base64 -i <file>' prints."
    fi
}

import_p12() { # secret-name p12-file
    local name="$1" file="$2"
    if ! security import "$file" -k "$KEYCHAIN" -f pkcs12 -P "$APPLE_P12_PASSWORD" \
            -T /usr/bin/codesign -T /usr/bin/productsign -T /usr/bin/security \
            > "$SIGNING_DIR/import.log" 2>&1; then
        sed 's/^/  /' "$SIGNING_DIR/import.log" >&2
        rm -f "$file"
        die "the .p12 in $name did not import with the password in APPLE_P12_PASSWORD. Either the password is wrong, or the secret is not the .p12 that Keychain Access exported."
    fi
    rm -f "$file"
}

require_identity() { # identity-name secret-name find-identity-arguments...
    local identity="$1" secret="$2"; shift 2
    local valid
    valid="$(security find-identity -v "$@" "$KEYCHAIN" 2>&1 || true)"
    echo "$valid"
    case "$valid" in
        *"\"$identity\""*) ;;
        *)
            echo "signing-keychain.sh: every identity in the keychain, valid or not:" >&2
            security find-identity "$@" "$KEYCHAIN" >&2 2>&1 || true
            die "$secret does not hold a valid \"$identity\" identity. The list above shows what it holds; an expired certificate or one without its private key is not valid."
            ;;
    esac
}

report_expiry() { # identity-name
    local pem end
    pem="$(security find-certificate -c "$1" -p "$KEYCHAIN" 2>/dev/null || true)"
    [ -n "$pem" ] || return 0
    end="$(printf '%s\n' "$pem" | openssl x509 -noout -enddate 2>/dev/null | sed 's/^notAfter=//')"
    [ -n "$end" ] || return 0
    log "$1 expires $end"
    if ! printf '%s\n' "$pem" | openssl x509 -noout -checkend $((EXPIRY_WARNING_DAYS * 86400)) >/dev/null 2>&1; then
        echo "::warning title=Developer ID certificate expires soon::$1 expires $end. Create a new one before then; plans/release-pipeline.md, Recurring maintenance, has the steps."
    fi
}

make_keychain() {
    if [ "${GITHUB_EVENT_NAME:-}" = "pull_request" ]; then
        die "refusing to set up signing on a pull_request run. Pull request dry runs are unsigned and read no secrets."
    fi

    local missing="" name
    for name in $SECRET_NAMES; do
        [ -n "${!name:-}" ] || missing="$missing $name"
    done
    if [ -n "$missing" ]; then
        die "these GitHub Actions secrets are missing or empty:$missing. A tag or manual run is always signed and notarized, and it will not fall back to an unsigned package. Set them as plans/release-pipeline.md describes under Secrets."
    fi
    [ -n "${DEVELOPER_ID_APP:-}" ] || die "DEVELOPER_ID_APP is not set (a 'Developer ID Application: ...' identity name)"
    [ -n "${DEVELOPER_ID_INSTALLER:-}" ] || die "DEVELOPER_ID_INSTALLER is not set (a 'Developer ID Installer: ...' identity name)"

    umask 077
    # A keychain left by an earlier setup comes off the search list first.
    if [ -e "$KEYCHAIN" ]; then
        security delete-keychain "$KEYCHAIN" >/dev/null 2>&1 || true
    fi
    rm -rf "$SIGNING_DIR"
    mkdir -p "$SIGNING_DIR"
    chmod 700 "$SIGNING_DIR"

    # ---- decode ----
    decode_secret APPLE_DEV_ID_APP_P12 "$SIGNING_DIR/developer-id-application.p12"
    decode_secret APPLE_DEV_ID_INSTALLER_P12 "$SIGNING_DIR/developer-id-installer.p12"
    decode_secret APPLE_API_KEY_P8 "$NOTARY_KEY"
    chmod 600 "$NOTARY_KEY"
    if ! grep -q -- '-----BEGIN PRIVATE KEY-----' "$NOTARY_KEY"; then
        die "APPLE_API_KEY_P8 does not decode to a private key. It should be the base64 of the AuthKey .p8 file from App Store Connect."
    fi

    # ---- keychain ----
    local password
    password="$(openssl rand -hex 24)"
    security create-keychain -p "$password" "$KEYCHAIN"
    # No -t and no -u: the keychain never locks on a timer, so it cannot lock
    # itself between this step and the signing step.
    security set-keychain-settings "$KEYCHAIN"
    security unlock-keychain -p "$password" "$KEYCHAIN"
    import_p12 APPLE_DEV_ID_APP_P12 "$SIGNING_DIR/developer-id-application.p12"
    import_p12 APPLE_DEV_ID_INSTALLER_P12 "$SIGNING_DIR/developer-id-installer.p12"
    # Without this codesign stops to ask for the keychain password in a dialog
    # nobody can answer on a runner.
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$password" "$KEYCHAIN" >/dev/null
    # Keep whatever is on the user search list and put this keychain first.
    local existing=() line search_list
    search_list="$(security list-keychains -d user)" \
        || die "could not read the keychain search list"
    while IFS= read -r line; do
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line#\"}"; line="${line%\"}"
        [ -z "$line" ] || existing+=("$line")
    done <<EOF
$search_list
EOF
    security list-keychains -d user -s "$KEYCHAIN" ${existing[@]+"${existing[@]}"}
    log "created $KEYCHAIN"

    # ---- identities ----
    log "valid code signing identities:"
    require_identity "$DEVELOPER_ID_APP" APPLE_DEV_ID_APP_P12 -p codesigning
    log "valid identities of any kind:"
    require_identity "$DEVELOPER_ID_INSTALLER" APPLE_DEV_ID_INSTALLER_P12
    report_expiry "$DEVELOPER_ID_APP"
    report_expiry "$DEVELOPER_ID_INSTALLER"

    # ---- prove both keys sign, with a timestamp, without a prompt ----
    local probe="$SIGNING_DIR/probe"
    mkdir -p "$probe/root"
    echo "Wilsonic signing probe" > "$probe/file"
    echo "Wilsonic signing probe" > "$probe/root/file"
    if ! codesign --force --timestamp --keychain "$KEYCHAIN" --sign "$DEVELOPER_ID_APP" "$probe/file" > "$probe/codesign.log" 2>&1; then
        sed 's/^/  /' "$probe/codesign.log" >&2
        die "codesign could not sign a scratch file with \"$DEVELOPER_ID_APP\", the identity from APPLE_DEV_ID_APP_P12. The certificate imported and is valid, so the message above is the clue: errSecInternalComponent usually means the keychain is locked or codesign may not use the key (the partition list), and a timestamp error means Apple's timestamp server could not be reached. If neither fits, check that the .p12 was exported together with its private key."
    fi
    log "codesign signed a scratch file with a secure timestamp"
    pkgbuild --quiet --root "$probe/root" --identifier com.marcussatellite.wilsonic-signing-probe \
        --version 1 --install-location /private/tmp/wilsonic-signing-probe "$probe/probe.pkg"
    if ! productsign --timestamp --keychain "$KEYCHAIN" --sign "$DEVELOPER_ID_INSTALLER" \
            "$probe/probe.pkg" "$probe/probe-signed.pkg" > "$probe/productsign.log" 2>&1; then
        sed 's/^/  /' "$probe/productsign.log" >&2
        die "productsign could not sign a scratch package with \"$DEVELOPER_ID_INSTALLER\", the identity from APPLE_DEV_ID_INSTALLER_P12. The certificate imported and is valid, so the message above is the clue: a locked keychain, a key productsign may not use, or Apple's timestamp server being out of reach. If none of those fits, check that the .p12 was exported together with its private key."
    fi
    log "productsign signed a scratch package with a secure timestamp"
    rm -rf "$probe"

    # ---- prove the API key reaches the notary service ----
    if ! xcrun notarytool history --key "$NOTARY_KEY" --key-id "$APPLE_API_KEY_ID" --issuer "$APPLE_API_ISSUER_ID" \
            > "$SIGNING_DIR/notarytool.log" 2>&1; then
        sed 's/^/  /' "$SIGNING_DIR/notarytool.log" >&2
        die "App Store Connect refused the API key. Check APPLE_API_KEY_ID, APPLE_API_ISSUER_ID and APPLE_API_KEY_P8: they must be one Team key with the Developer role, its key ID, and the issuer ID shown above the key list."
    fi
    rm -f "$SIGNING_DIR/notarytool.log" "$SIGNING_DIR/import.log"
    log "App Store Connect accepted the API key"
}

setup() {
    make_keychain
    if [ -n "${GITHUB_ENV:-}" ]; then
        {
            echo "SIGNING_KEYCHAIN=$KEYCHAIN"
            echo "NOTARY_KEY_FILE=$NOTARY_KEY"
        } >> "$GITHUB_ENV"
    fi
    log "ready: SIGNING_KEYCHAIN=$KEYCHAIN NOTARY_KEY_FILE=$NOTARY_KEY"
}

# The same checks as setup, with nothing left behind whether they pass or fail.
check() {
    trap teardown EXIT
    make_keychain
    log "all six secrets work"
}

teardown() {
    # delete-keychain also takes the keychain off the search list.
    if [ -e "$KEYCHAIN" ]; then
        security delete-keychain "$KEYCHAIN" || rm -f "$KEYCHAIN"
        log "deleted $KEYCHAIN"
    fi
    rm -rf "$SIGNING_DIR"
    [ ! -e "$SIGNING_DIR" ] || die "could not remove $SIGNING_DIR"
    log "removed $SIGNING_DIR"
}

case "${1:-}" in
    check)    check ;;
    setup)    setup ;;
    teardown) teardown ;;
    *) die "usage: signing-keychain.sh check|setup|teardown" ;;
esac
