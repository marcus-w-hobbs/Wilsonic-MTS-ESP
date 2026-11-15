#!/usr/bin/env bash
# Test for the Windows release scripts in this folder: check-exporter.sh,
# build-project.sh, build-installer.sh, wilsonic.iss and ci-build.targets.
# It needs no Visual Studio and no Inno Setup: msbuild and ISCC are replaced
# by fakes that record their arguments, and the four build products are
# fabricated PE headers. Where a real ISCC.exe is installed, as on the
# windows-2022 runner, the last section also compiles wilsonic.iss for real.
# Runs on bash 3.2 (macOS) and on Git Bash (Windows).
# Usage: release/windows/test-windows-scripts.sh
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SELF_DIR/../.." && pwd)"
CHECK="$SELF_DIR/check-exporter.sh"
PROJECT="$SELF_DIR/build-project.sh"
INSTALLER="$SELF_DIR/build-installer.sh"
ISS="$SELF_DIR/wilsonic.iss"
TARGETS="$SELF_DIR/ci-build.targets"
TEST_VERSION="9.9.9-test"

pass=0; fail=0
ok()  { pass=$((pass+1)); echo "  ok   $1"; }
bad() { fail=$((fail+1)); echo "  FAIL $1"; }
expect_file() { # desc path
    if [ -e "$2" ]; then ok "$1"; else bad "$1 (missing $2)"; fi
}
expect_grep() { # desc pattern file
    if grep -q -- "$2" "$3" 2>/dev/null; then ok "$1"; else bad "$1 (no '$2' in $3)"; fi
}
expect_no_grep() { # desc pattern file
    if grep -q -- "$2" "$3" 2>/dev/null; then bad "$1 (found '$2' in $3)"; else ok "$1"; fi
}
expect_rc() { # desc want_rc log cmd...
    local desc="$1" want="$2" log="$3"; shift 3
    local rc=0; "$@" > "$log" 2>&1 || rc=$?
    if [ "$rc" -eq "$want" ]; then ok "$desc"; else bad "$desc (rc $rc, want $want)"; sed 's/^/    | /' "$log"; fi
}

SANDBOX="$(mktemp -d 2>/dev/null || mktemp -d -t wilsonic-win-test)"
trap 'rm -rf "$SANDBOX"' EXIT
LOG="$SANDBOX/run.log"

echo "files exist"
for f in "$CHECK" "$PROJECT" "$INSTALLER"; do
    if [ -x "$f" ]; then ok "$(basename "$f") executable"; else bad "$(basename "$f") missing or not executable"; fi
done
expect_file "wilsonic.iss" "$ISS"
expect_file "ci-build.targets" "$TARGETS"
if [ "$fail" -gt 0 ]; then echo; echo "$pass passed, $fail failed"; exit 1; fi

# ---- check-exporter.sh -------------------------------------------------------
echo "check-exporter.sh accepts the real .jucer files"
expect_rc "exit status 0" 0 "$LOG" "$CHECK"
expect_grep "reports the Wilsonic target folder" "Wilsonic.jucer.*Builds/VisualStudio2022" "$LOG"
expect_grep "reports the WilsonicController target folder" "WilsonicController.jucer.*Builds/VisualStudio2022-WilsonicController" "$LOG"

echo "check-exporter.sh refuses a .jucer without a VS2022 exporter"
J="$SANDBOX/jucer-none"; mkdir -p "$J"
sed '/<VS2022 /,/<\/VS2022>/d' "$REPO/Wilsonic.jucer" > "$J/Wilsonic.jucer"
cp "$REPO/WilsonicController.jucer" "$J/"
expect_rc "exit status 1" 1 "$LOG" env WILSONIC_ROOT="$J" "$CHECK"
expect_grep "says plainly what is missing" "Wilsonic.jucer has no Visual Studio 2022 exporter" "$LOG"
expect_no_grep "does not blame the other project" "WilsonicController.jucer has no" "$LOG"

echo "check-exporter.sh refuses a moved target folder"
J="$SANDBOX/jucer-moved"; mkdir -p "$J"
cp "$REPO/Wilsonic.jucer" "$J/"
sed 's|targetFolder="Builds/VisualStudio2022-WilsonicController"|targetFolder="Builds/Elsewhere"|' \
    "$REPO/WilsonicController.jucer" > "$J/WilsonicController.jucer"
expect_rc "exit status 1" 1 "$LOG" env WILSONIC_ROOT="$J" "$CHECK"
expect_grep "names the folder it found" "Builds/Elsewhere" "$LOG"

echo "check-exporter.sh refuses an exporter without a Release configuration"
J="$SANDBOX/jucer-norelease"; mkdir -p "$J"
cp "$REPO/WilsonicController.jucer" "$J/"
awk '/<VS2022 /{v=1} /<\/VS2022>/{v=0} !(v && /isDebug="0"/)' "$REPO/Wilsonic.jucer" > "$J/Wilsonic.jucer"
expect_rc "exit status 1" 1 "$LOG" env WILSONIC_ROOT="$J" "$CHECK"
expect_grep "says the Release configuration is missing" "no Release configuration" "$LOG"

# ---- wilsonic.iss, read as text ------------------------------------------------
echo "wilsonic.iss"
expect_grep "keeps the v0.43 AppId" 'AppId={{78427BB9-1C86-41AB-BC1F-53E7203BDCDD}' "$ISS"
expect_grep "refuses to compile without /DVersion" '#error' "$ISS"
expect_no_grep "no hardcoded user path" 'C:\\Users' "$ISS"
expect_no_grep "no OneDrive path" 'OneDrive' "$ISS"
expect_no_grep "no pinned 0.43" '0\.43"' "$ISS"
expect_grep "installs Wilsonic.exe" 'Standalone Plugin\\Wilsonic.exe' "$ISS"
expect_grep "installs WilsonicController.exe" 'Standalone Plugin\\WilsonicController.exe' "$ISS"
expect_grep "installs the Wilsonic VST3 under Common Files" 'Wilsonic.vst3".*{commoncf}\\VST3' "$ISS"
expect_grep "installs the WilsonicController VST3 under Common Files" 'WilsonicController.vst3".*{commoncf}\\VST3' "$ISS"
expect_grep "installs the 64-bit LIBMTS.dll to Common Files\\MTS-ESP" 'Win\\64bit\\LIBMTS.dll".*{commoncf}\\MTS-ESP' "$ISS"
expect_no_grep "does not install the 32-bit LIBMTS.dll" '32bit' "$ISS"
expect_grep "installs MTS-ESP.conf only if absent" 'MTS-ESP.conf".*{commoncf}\\MTS-ESP.*onlyifdoesntexist' "$ISS"
expect_grep "64-bit install mode" '^ArchitecturesInstallIn64BitMode=' "$ISS"
expect_grep "replaces the uninstall log of an older install" '^UninstallLogMode=overwrite$' "$ISS"
expect_grep "LIBMTS.dll is never uninstalled" 'LIBMTS.dll".*uninsneveruninstall' "$ISS"
expect_grep "MTS-ESP.conf is never uninstalled" 'MTS-ESP.conf".*uninsneveruninstall' "$ISS"

# ---- build-project.sh with a fake msbuild --------------------------------------
# The fake records its arguments, finds the file-logger path the script asked
# for, and writes a log there. FAKE_MSBUILD_MODE makes it misbehave.
FAKE_MSBUILD="$SANDBOX/fake-msbuild"
cat > "$FAKE_MSBUILD" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$FAKE_MSBUILD_ARGS"
log=""; sln="$1"
for a in "$@"; do
    case "$a" in -flp:*) log="$(printf '%s' "$a" | sed 's/^-flp:logfile=\([^;]*\).*/\1/')" ;; esac
done
[ -n "$log" ] || exit 9
# build-project.sh hands msbuild Windows paths where cygpath exists.
if command -v cygpath >/dev/null 2>&1; then sln="$(cygpath -u "$sln")"; log="$(cygpath -u "$log")"; fi
out="$(dirname "$sln")/x64/Release/VST3"
mkdir -p "$out"
case "${FAKE_MSBUILD_MODE:-ok}" in
    ok)   echo '  CL.exe /c /nologo /W4 /O2 /MD thing.cpp' > "$log" ;;
    gl)   echo '  CL.exe /c /nologo /W4 /O2 /GL /MD thing.cpp' > "$log" ;;
    zi)   echo '  CL.exe /c /Zi /nologo /W4 /O2 /MD thing.cpp' > "$log" ;;
    pdb)  echo '  CL.exe /c /nologo /W4 /O2 /MD thing.cpp' > "$log"; : > "$out/Wilsonic.pdb" ;;
    nocl) echo 'Build succeeded.' > "$log" ;;
    fail) echo 'error C1234' > "$log"; exit 1 ;;
esac
FAKE
chmod +x "$FAKE_MSBUILD"
export FAKE_MSBUILD_ARGS="$SANDBOX/msbuild.args"
new_sln() { # -> path of a fresh fake solution
    local d; d="$(mktemp -d "$SANDBOX/sln.XXXXXX")"
    mkdir -p "$d/Builds/VisualStudio2022"
    : > "$d/Builds/VisualStudio2022/Wilsonic.sln"
    echo "$d/Builds/VisualStudio2022/Wilsonic.sln"
}

echo "build-project.sh without link-time optimisation or debug symbols"
SLN="$(new_sln)"
expect_rc "exit status 0" 0 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=NO DEBUG_SYMBOLS=NO "$PROJECT" "$SLN"
expect_grep "builds Release" '^-p:Configuration=Release$' "$FAKE_MSBUILD_ARGS"
expect_grep "builds x64" '^-p:Platform=x64$' "$FAKE_MSBUILD_ARGS"
expect_grep "turns whole program optimisation off" '^-p:WholeProgramOptimization=false$' "$FAKE_MSBUILD_ARGS"
expect_grep "passes WilsonicLTO=NO" '^-p:WilsonicLTO=NO$' "$FAKE_MSBUILD_ARGS"
expect_grep "passes WilsonicDebugSymbols=NO" '^-p:WilsonicDebugSymbols=NO$' "$FAKE_MSBUILD_ARGS"
if cmp -s "$TARGETS" "$(dirname "$SLN")/Directory.Build.targets"; then
    ok "ci-build.targets installed beside the solution as Directory.Build.targets"
else
    bad "Directory.Build.targets missing beside the solution or differs from ci-build.targets"
fi

echo "build-project.sh with link-time optimisation and debug symbols"
SLN="$(new_sln)"
expect_rc "exit status 0" 0 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=YES DEBUG_SYMBOLS=YES FAKE_MSBUILD_MODE=gl "$PROJECT" "$SLN"
expect_no_grep "leaves whole program optimisation alone" 'WholeProgramOptimization' "$FAKE_MSBUILD_ARGS"
expect_no_grep "does not pass WilsonicLTO" 'WilsonicLTO' "$FAKE_MSBUILD_ARGS"
expect_no_grep "does not pass WilsonicDebugSymbols" 'WilsonicDebugSymbols' "$FAKE_MSBUILD_ARGS"

echo "build-project.sh refuses a build that ignored the switches"
SLN="$(new_sln)"
expect_rc "fails when /GL is still on the compile line" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=NO DEBUG_SYMBOLS=NO FAKE_MSBUILD_MODE=gl "$PROJECT" "$SLN"
expect_grep "says /GL was found" '/GL' "$LOG"
SLN="$(new_sln)"
expect_rc "fails when /Zi is still on the compile line" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=NO DEBUG_SYMBOLS=NO FAKE_MSBUILD_MODE=zi "$PROJECT" "$SLN"
expect_grep "says debug information was found" 'still compiled with debug information' "$LOG"
SLN="$(new_sln)"
expect_rc "fails when a .pdb was written" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=NO DEBUG_SYMBOLS=NO FAKE_MSBUILD_MODE=pdb "$PROJECT" "$SLN"
expect_grep "says the build wrote a .pdb" 'the build wrote' "$LOG"
expect_grep "names the .pdb" 'Wilsonic.pdb' "$LOG"
SLN="$(new_sln)"
expect_rc "fails when the log has no compile line to check" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=NO DEBUG_SYMBOLS=NO FAKE_MSBUILD_MODE=nocl "$PROJECT" "$SLN"
expect_grep "says there was nothing to check" 'no compiler command line' "$LOG"

echo "build-project.sh failure cases"
SLN="$(new_sln)"
expect_rc "fails when msbuild fails" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=NO DEBUG_SYMBOLS=NO FAKE_MSBUILD_MODE=fail "$PROJECT" "$SLN"
expect_rc "fails on a missing solution" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" "$PROJECT" "$SANDBOX/nope/Wilsonic.sln"
expect_grep "says to resave" 'resave' "$LOG"
expect_rc "fails on a bad LTO value" 1 "$LOG" env MSBUILD="$FAKE_MSBUILD" LTO=maybe "$PROJECT" "$SLN"

# ---- build-installer.sh with a fake ISCC ----------------------------------------
# A fake product is just enough of a PE header for the x64 check: "MZ", the
# offset of the PE header at 0x3C, "PE\0\0", and the machine field.
make_pe() { # out machine(x64|x86)
    local out="$1" m
    case "$2" in x64) m='\x64\x86' ;; x86) m='\x4c\x01' ;; esac
    mkdir -p "$(dirname "$out")"
    {
        printf 'MZ'
        head -c 58 /dev/zero
        printf '\x40\x00\x00\x00'
        printf 'PE\x00\x00'
        printf "$m"
        head -c 64 /dev/zero
    } > "$out"
}
make_products() { # root
    make_pe "$1/w/Standalone Plugin/Wilsonic.exe" x64
    make_pe "$1/w/VST3/Wilsonic.vst3/Contents/x86_64-win/Wilsonic.vst3" x64
    make_pe "$1/c/Standalone Plugin/WilsonicController.exe" x64
    make_pe "$1/c/VST3/WilsonicController.vst3/Contents/x86_64-win/WilsonicController.vst3" x64
}
# The fake ISCC records its arguments and writes the installer the real one
# would, named by the same rule as OutputBaseFilename in wilsonic.iss.
FAKE_ISCC="$SANDBOX/fake-iscc"
cat > "$FAKE_ISCC" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$FAKE_ISCC_ARGS"
version=""; out=""; suffix="-unsigned"
for a in "$@"; do
    case "$a" in
        /DVersion=*)   version="${a#/DVersion=}" ;;
        /DOutputDir=*) out="${a#/DOutputDir=}" ;;
        /DSigned)      suffix="" ;;
    esac
done
[ "${FAKE_ISCC_MODE:-ok}" = fail ] && exit 2
if command -v cygpath >/dev/null 2>&1; then out="$(cygpath -u "$out")"; fi
mkdir -p "$out"
echo fake > "$out/Wilsonic_Win64_v${version}${suffix}.exe"
FAKE
chmod +x "$FAKE_ISCC"
export FAKE_ISCC_ARGS="$SANDBOX/iscc.args"
run_installer() { # products-root out-dir extra args...
    local root="$1" out="$2"; shift 2
    "$INSTALLER" --version "$TEST_VERSION" --wilsonic-build "$root/w" \
        --controller-build "$root/c" --out "$out" "$@"
}

echo "build-installer.sh packages fake products unsigned"
P="$SANDBOX/products"; make_products "$P"
expect_rc "exit status 0" 0 "$LOG" env ISCC="$FAKE_ISCC" SIGNING=0 "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out"
expect_file "installer named Wilsonic_Win64_v${TEST_VERSION}-unsigned.exe" "$SANDBOX/out/Wilsonic_Win64_v${TEST_VERSION}-unsigned.exe"
expect_grep "passes the version to ISCC" "^/DVersion=${TEST_VERSION}\$" "$FAKE_ISCC_ARGS"
expect_grep "passes the Wilsonic build folder" '^/DWilsonicBuild=' "$FAKE_ISCC_ARGS"
expect_grep "passes the WilsonicController build folder" '^/DControllerBuild=' "$FAKE_ISCC_ARGS"
expect_grep "passes the MTS-ESP folder" '^/DMtsEspDir=' "$FAKE_ISCC_ARGS"
expect_no_grep "does not ask for signing" '^/DSigned$' "$FAKE_ISCC_ARGS"
expect_grep "compiles wilsonic.iss" 'wilsonic.iss$' "$FAKE_ISCC_ARGS"
expect_grep "checked that the products are x64" 'LIBMTS.dll are x64' "$LOG"
expect_grep "checked libMTS against PIN" 'matches PIN' "$LOG"

echo "build-installer.sh with relative build folders, run from another folder"
# ISCC resolves a relative path against the repo root, not the caller's
# folder, so the script has to hand it the absolute folders it checked.
expect_rc "exit status 0" 0 "$LOG" env ISCC="$FAKE_ISCC" SIGNING=0 sh -c 'cd "$1" && shift && "$@"' sh "$P" \
    "$INSTALLER" --version "$TEST_VERSION" --wilsonic-build w --controller-build c --out out-rel
expect_grep "the Wilsonic build folder reaches ISCC absolute" '^/DWilsonicBuild=\(/\|[A-Za-z]:\)' "$FAKE_ISCC_ARGS"
expect_grep "the WilsonicController build folder reaches ISCC absolute" '^/DControllerBuild=\(/\|[A-Za-z]:\)' "$FAKE_ISCC_ARGS"
expect_file "the installer lands in the caller's relative output folder" "$P/out-rel/Wilsonic_Win64_v${TEST_VERSION}-unsigned.exe"

echo "build-installer.sh signing switch"
expect_rc "SIGNING=1 without SIGNTOOL_COMMAND fails" 1 "$LOG" env ISCC="$FAKE_ISCC" SIGNING=1 "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out-s0"
expect_rc "SIGNING=1 with SIGNTOOL_COMMAND succeeds" 0 "$LOG" env ISCC="$FAKE_ISCC" SIGNING=1 SIGNTOOL_COMMAND='signtool sign $f' "$INSTALLER" \
    --version "$TEST_VERSION" --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out-s1"
expect_grep "passes /DSigned" '^/DSigned$' "$FAKE_ISCC_ARGS"
expect_grep "passes the sign tool to ISCC" '^/Swilsonicsign=signtool sign \$f$' "$FAKE_ISCC_ARGS"
expect_file "signed installer drops the -unsigned suffix" "$SANDBOX/out-s1/Wilsonic_Win64_v${TEST_VERSION}.exe"

echo "build-installer.sh refusals"
expect_rc "invalid version" 1 "$LOG" env ISCC="$FAKE_ISCC" "$INSTALLER" --version "nope" \
    --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out-x"
P2="$SANDBOX/products-missing"; make_products "$P2"; rm "$P2/c/Standalone Plugin/WilsonicController.exe"
expect_rc "missing product" 1 "$LOG" env ISCC="$FAKE_ISCC" "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P2/w" --controller-build "$P2/c" --out "$SANDBOX/out-x"
expect_grep "names the missing product" 'WilsonicController.exe' "$LOG"
P3="$SANDBOX/products-x86"; make_products "$P3"; make_pe "$P3/w/VST3/Wilsonic.vst3/Contents/x86_64-win/Wilsonic.vst3" x86
expect_rc "32-bit product" 1 "$LOG" env ISCC="$FAKE_ISCC" "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P3/w" --controller-build "$P3/c" --out "$SANDBOX/out-x"
expect_grep "says it is not x64" 'not an x64' "$LOG"
P4="$SANDBOX/products-text"; make_products "$P4"; echo "not a binary" > "$P4/w/Standalone Plugin/Wilsonic.exe"
expect_rc "product that is not a PE file" 1 "$LOG" env ISCC="$FAKE_ISCC" "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P4/w" --controller-build "$P4/c" --out "$SANDBOX/out-x"
M="$SANDBOX/mts-esp"; cp -R "$REPO/release/mts-esp" "$M"; echo tampered >> "$M/Win/64bit/LIBMTS.dll"
expect_rc "LIBMTS.dll that does not match PIN" 1 "$LOG" env ISCC="$FAKE_ISCC" "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P/w" --controller-build "$P/c" --mts-esp "$M" --out "$SANDBOX/out-x"
expect_grep "says PIN does not match" 'do not match PIN' "$LOG"
expect_rc "ISCC failure" 1 "$LOG" env ISCC="$FAKE_ISCC" FAKE_ISCC_MODE=fail "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out-x"
expect_rc "ISCC that is not there" 1 "$LOG" env ISCC="$SANDBOX/no-such-iscc" "$INSTALLER" --version "$TEST_VERSION" \
    --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out-x"
if [ -e "$SANDBOX/out-x" ] && [ -n "$(ls -A "$SANDBOX/out-x" 2>/dev/null)" ]; then
    bad "a refused build left files in the output folder"
else
    ok "refused builds wrote no installer"
fi

# ---- the real ISCC, where there is one -----------------------------------------
REAL_ISCC=""
if command -v ISCC.exe >/dev/null 2>&1; then
    REAL_ISCC="$(command -v ISCC.exe)"
elif [ -x "/c/Program Files (x86)/Inno Setup 6/ISCC.exe" ]; then
    REAL_ISCC="/c/Program Files (x86)/Inno Setup 6/ISCC.exe"
fi
if [ -n "$REAL_ISCC" ]; then
    echo "build-installer.sh with the real ISCC ($REAL_ISCC)"
    expect_rc "compiles wilsonic.iss from fake products" 0 "$LOG" env ISCC="$REAL_ISCC" SIGNING=0 "$INSTALLER" --version "$TEST_VERSION" \
        --wilsonic-build "$P/w" --controller-build "$P/c" --out "$SANDBOX/out-real"
    expect_file "real installer named Wilsonic_Win64_v${TEST_VERSION}-unsigned.exe" "$SANDBOX/out-real/Wilsonic_Win64_v${TEST_VERSION}-unsigned.exe"
    if [ -s "$SANDBOX/out-real/Wilsonic_Win64_v${TEST_VERSION}-unsigned.exe" ]; then ok "installer is not empty"; else bad "installer is empty"; fi
else
    echo "no ISCC.exe on this machine: skipping the real compile of wilsonic.iss"
fi

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
