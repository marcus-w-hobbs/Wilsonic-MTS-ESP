#!/usr/bin/env bash
# Shared helpers for the tests in this folder: the pass/fail counters, the
# expect_* assertions, and the fake product bundles. Sourced by
# test-build-pkg.sh and test-signing.sh, never run on its own.
# Runs on bash 3.2 (macOS).

TEST_VERSION="9.9.9-test"
TEST_CORE="9.9.9"

pass=0; fail=0
ok()  { pass=$((pass+1)); echo "  ok   $1"; }
bad() { fail=$((fail+1)); echo "  FAIL $1"; }
expect_file() { # desc path
    if [ -e "$2" ]; then ok "$1"; else bad "$1 (missing $2)"; fi
}
expect_no_file() { # desc path
    if [ -e "$2" ]; then bad "$1 ($2 exists)"; else ok "$1"; fi
}
expect_grep() { # desc pattern file
    if grep -q -- "$2" "$3" 2>/dev/null; then ok "$1"; else bad "$1 (no '$2' in $3)"; fi
}
expect_no_grep() { # desc pattern file
    if grep -q -- "$2" "$3" 2>/dev/null; then bad "$1 (found '$2' in $3)"; else ok "$1"; fi
}
expect_eq() { # desc actual expected
    if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (got '$2', want '$3')"; fi
}
expect_zero() { # desc status logfile
    if [ "$2" -eq 0 ]; then ok "$1"; else bad "$1 (exit status $2)"; sed 's/^/    | /' "$3"; fi
}
expect_nonzero() { # desc status logfile
    if [ "$2" -ne 0 ]; then ok "$1"; else bad "$1 (exit status 0)"; sed 's/^/    | /' "$3"; fi
}
finish() {
    echo
    echo "$pass passed, $fail failed"
    [ "$fail" -eq 0 ]
}

# A fake bundle: enough Info.plist for pkgbuild --analyze to see it as a
# bundle, plus a real Mach-O executable, because build-pkg.sh refuses any
# product that is not a universal arm64 x86_64 binary. The stubs are compiled
# once per run with the system C compiler, which comes with pkgbuild.
make_stub() { # out archs...
    local out="$1"; shift
    local flags=""
    for a in "$@"; do flags="$flags -arch $a"; done
    echo 'int main(void) { return 0; }' > "$out.c"
    # shellcheck disable=SC2086
    cc $flags -o "$out" "$out.c" \
        || { echo "test-lib.sh: cannot compile a stub for $*" >&2; exit 1; }
}
make_bundle() { # dir name type(APPL|BNDL) bundle-id; needs STUB_UNIVERSAL
    local dir="$1" name="$2" type="$3" id="$4"
    mkdir -p "$dir/Contents/MacOS"
    cp "$STUB_UNIVERSAL" "$dir/Contents/MacOS/$name"
    chmod +x "$dir/Contents/MacOS/$name"
    cat > "$dir/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>$id</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundlePackageType</key><string>$type</string>
<key>CFBundleShortVersionString</key><string>$TEST_CORE</string>
<key>CFBundleVersion</key><string>$TEST_CORE</string>
</dict></plist>
PLIST
}
# The six products, in the two Release folders build-pkg.sh reads.
make_products() { # wilsonic-build-dir controller-build-dir; needs STUB_UNIVERSAL
    local w="$1" c="$2"
    mkdir -p "$w" "$c"
    make_bundle "$w/Wilsonic.app"       Wilsonic APPL com.marcussatellite.Wilsonic
    make_bundle "$w/Wilsonic.component" Wilsonic BNDL com.marcussatellite.Wilsonic.component
    make_bundle "$w/Wilsonic.vst3"      Wilsonic BNDL com.marcussatellite.Wilsonic.vst3
    make_bundle "$c/WilsonicController.app"       WilsonicController APPL com.marcussatellite.WilsonicController
    make_bundle "$c/WilsonicController.component" WilsonicController BNDL com.marcussatellite.WilsonicController.component
    make_bundle "$c/WilsonicController.vst3"      WilsonicController BNDL com.marcussatellite.WilsonicController.vst3
}
