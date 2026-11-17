#!/usr/bin/env bash
# Notarize a signed macOS package and staple the ticket to it.
#
# Usage: release/mac/notarize.sh <signed.pkg>
#
# Environment:
#   NOTARY_KEY_FILE      path of the App Store Connect .p8 key (signing-keychain.sh writes it)
#   APPLE_API_KEY_ID     the key ID
#   APPLE_API_ISSUER_ID  the issuer ID
#   NOTARY_TIMEOUT       how long to wait for Apple, default 45m
#
# Submits with `notarytool submit --wait`, then fetches and prints Apple's log
# for the submission whatever the verdict, because an accepted submission can
# still carry warnings. Anything but "Accepted" fails. An accepted package is
# stapled and the staple validated.
#
# This script never prints the key ID, the issuer ID or the key, and tracing
# is switched off below so a caller's `bash -x` cannot print them either.
set -euo pipefail
set +x

die() { echo "notarize.sh: $*" >&2; exit 1; }
log() { echo "notarize.sh: $*"; }

PKG="${1:-}"
[ -n "$PKG" ] || die "usage: notarize.sh <signed.pkg>"
[ -f "$PKG" ] || die "$PKG not found"
for name in NOTARY_KEY_FILE APPLE_API_KEY_ID APPLE_API_ISSUER_ID; do
    [ -n "${!name:-}" ] || die "$name is not set"
done
[ -f "$NOTARY_KEY_FILE" ] || die "NOTARY_KEY_FILE points at $NOTARY_KEY_FILE, which does not exist"
NOTARY_TIMEOUT="${NOTARY_TIMEOUT:-45m}"

WORK="$(mktemp -d -t wilsonic-notarize)"
trap 'rm -rf "$WORK"' EXIT

log "submitting $(basename "$PKG") to the Apple notary service and waiting up to $NOTARY_TIMEOUT"
submit_rc=0
xcrun notarytool submit "$PKG" \
    --key "$NOTARY_KEY_FILE" --key-id "$APPLE_API_KEY_ID" --issuer "$APPLE_API_ISSUER_ID" \
    --wait --timeout "$NOTARY_TIMEOUT" --output-format json \
    > "$WORK/submit.json" 2> "$WORK/submit.err" || submit_rc=$?

json_field() { # field -> value, or nothing
    plutil -extract "$1" raw -o - "$WORK/submit.json" 2>/dev/null || true
}
id="$(json_field id)"
status="$(json_field status)"

if [ -z "$id" ]; then
    sed 's/^/  /' "$WORK/submit.err" >&2
    sed 's/^/  /' "$WORK/submit.json" >&2
    die "notarytool submit failed (exit status $submit_rc) before Apple gave the submission an id. If the message above is about credentials, check APPLE_API_KEY_ID, APPLE_API_ISSUER_ID and APPLE_API_KEY_P8."
fi
log "submission id $id, status ${status:-unknown}"

log "Apple's log for submission $id:"
xcrun notarytool log "$id" \
    --key "$NOTARY_KEY_FILE" --key-id "$APPLE_API_KEY_ID" --issuer "$APPLE_API_ISSUER_ID" \
    || echo "notarize.sh: could not fetch the log for $id" >&2
echo

if [ "$status" != "Accepted" ]; then
    sed 's/^/  /' "$WORK/submit.err" >&2
    die "Apple did not accept the package: status ${status:-unknown} (notarytool exit status $submit_rc). The log above lists each issue."
fi

xcrun stapler staple "$PKG" || die "the notarization ticket did not staple to $PKG"
xcrun stapler validate "$PKG" || die "the stapled ticket on $PKG does not validate"
log "notarized and stapled $PKG (submission $id)"
