#!/usr/bin/env bash
# Tests for scripts/set-version.sh and scripts/check-version.sh.
# Runs against a throwaway copy of the four version-bearing files, never the
# real repo. Usage: scripts/test-version-scripts.sh
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$SELF_DIR")"
SET="$SELF_DIR/set-version.sh"
CHECK="$SELF_DIR/check-version.sh"

pass=0; fail=0
ok()   { pass=$((pass+1)); echo "  ok   $1"; }
bad()  { fail=$((fail+1)); echo "  FAIL $1"; }
expect_eq() { # desc actual expected
    if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (got '$2', want '$3')"; fi
}
expect_rc() { # desc want_rc cmd...
    local desc="$1" want="$2"; shift 2
    local rc=0; "$@" >/dev/null 2>&1 || rc=$?
    if [ "$rc" -eq "$want" ]; then ok "$desc"; else bad "$desc (rc $rc, want $want)"; fi
}
macro() { # file NAME -> value
    sed -n "s/^#define $2 //p" "$1" | head -1
}
jucer_version() {
    sed -n 's/.* version="\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)".*/\1/p' "$1" | head -1
}

# Fresh sandbox seeded from the real files.
mk_sandbox() {
    local d; d="$(mktemp -d)"
    cp "$REPO/version.h" "$REPO/Wilsonic.jucer" "$REPO/WilsonicController.jucer" "$d/"
    [ -f "$REPO/VERSION.txt" ] && cp "$REPO/VERSION.txt" "$d/" || true
    echo "$d"
}

echo "scripts exist and are executable"
[ -x "$SET" ]   && ok "set-version.sh executable"   || bad "set-version.sh missing or not executable"
[ -x "$CHECK" ] && ok "check-version.sh executable" || bad "check-version.sh missing or not executable"

echo "set-version writes a pre-release"
S="$(mk_sandbox)"
echo "0.45.0-beta" > "$S/VERSION.txt"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
expect_eq "VERSION_MAJOR"  "$(macro "$S/version.h" VERSION_MAJOR)"  "0"
expect_eq "VERSION_MINOR"  "$(macro "$S/version.h" VERSION_MINOR)"  "45"
expect_eq "VERSION_PATCH"  "$(macro "$S/version.h" VERSION_PATCH)"  "0"
expect_eq "VER_NUM stays major.minor" "$(macro "$S/version.h" VER_NUM)" "0.45"
expect_eq "BETA is 1 for a suffix" "$(macro "$S/version.h" BETA)" "1"
expect_eq "VERSION_HINT = major*1000+minor" "$(macro "$S/version.h" VERSION_HINT)" "45"
expect_eq "VERSION_STRING" "$(macro "$S/version.h" VERSION_STRING)" "\"0.45.0-beta\""
expect_eq "Wilsonic.jucer version" "$(jucer_version "$S/Wilsonic.jucer")" "0.45.0"
expect_eq "WilsonicController.jucer version" "$(jucer_version "$S/WilsonicController.jucer")" "0.45.0"
expect_eq "jucer XML declaration untouched" "$(head -1 "$S/Wilsonic.jucer")" '<?xml version="1.0" encoding="UTF-8"?>'
expect_rc "check-version passes after set" 0 env WILSONIC_ROOT="$S" "$CHECK"
expect_rc "check-version passes with matching tag" 0 env WILSONIC_ROOT="$S" "$CHECK" --tag v0.45.0-beta
expect_rc "check-version fails with wrong tag" 1 env WILSONIC_ROOT="$S" "$CHECK" --tag v0.45.0
rm -rf "$S"

echo "set-version writes a stable release"
S="$(mk_sandbox)"
echo "1.2.3" > "$S/VERSION.txt"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
expect_eq "BETA is 0 without suffix" "$(macro "$S/version.h" BETA)" "0"
expect_eq "VER_NUM 1.2" "$(macro "$S/version.h" VER_NUM)" "1.2"
expect_eq "VERSION_HINT 1002" "$(macro "$S/version.h" VERSION_HINT)" "1002"
expect_eq "VERSION_STRING 1.2.3" "$(macro "$S/version.h" VERSION_STRING)" "\"1.2.3\""
rm -rf "$S"

echo "set-version is idempotent"
S="$(mk_sandbox)"
echo "0.45.0-beta" > "$S/VERSION.txt"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
cp "$S/version.h" "$S/first.h"; cp "$S/Wilsonic.jucer" "$S/first.jucer"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
expect_rc "version.h unchanged on second run" 0 cmp -s "$S/version.h" "$S/first.h"
expect_rc "jucer unchanged on second run" 0 cmp -s "$S/Wilsonic.jucer" "$S/first.jucer"
rm -rf "$S"

echo "set-version rejects bad input"
S="$(mk_sandbox)"
for v in "0.45" "v0.45.0" "0.45.0beta" "0.45.0-" "" "abc"; do
    echo "$v" > "$S/VERSION.txt"
    expect_rc "rejects '$v'" 1 env WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET"
done
rm -rf "$S"

echo "set-version accepts an explicit version argument"
S="$(mk_sandbox)"
echo "0.44.0" > "$S/VERSION.txt"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" 0.46.0-rc.1 >/dev/null
expect_eq "VERSION file rewritten" "$(cat "$S/VERSION.txt")" "0.46.0-rc.1"
expect_eq "VERSION_STRING from arg" "$(macro "$S/version.h" VERSION_STRING)" "\"0.46.0-rc.1\""
rm -rf "$S"

echo "check-version detects drift"
S="$(mk_sandbox)"
echo "0.45.0-beta" > "$S/VERSION.txt"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
sed -i.bak 's/^#define VERSION_MINOR 45/#define VERSION_MINOR 44/' "$S/version.h"
expect_rc "fails when version.h drifts" 1 env WILSONIC_ROOT="$S" "$CHECK"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
sed -i.bak 's/version="0.45.0"/version="0.44.0"/' "$S/WilsonicController.jucer"
expect_rc "fails when a jucer drifts" 1 env WILSONIC_ROOT="$S" "$CHECK"
rm -f "$S/VERSION.txt"
expect_rc "fails when VERSION.txt is missing" 1 env WILSONIC_ROOT="$S" "$CHECK"
rm -rf "$S"

echo "compatibility: current repo version round-trips"
S="$(mk_sandbox)"
before_vernum="$(macro "$S/version.h" VER_NUM)"
before_hint="$(macro "$S/version.h" VERSION_HINT)"
echo "0.44.0" > "$S/VERSION.txt"
WILSONIC_ROOT="$S" PROJUCER=/nonexistent "$SET" >/dev/null
expect_eq "VER_NUM unchanged for 0.44.0" "$(macro "$S/version.h" VER_NUM)" "$before_vernum"
expect_eq "VERSION_HINT unchanged for 0.44.0" "$(macro "$S/version.h" VERSION_HINT)" "$before_hint"
rm -rf "$S"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
