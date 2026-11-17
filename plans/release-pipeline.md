# Release pipeline design

Status: draft for Marcus to approve. Written 2026-11-10 from a Q&A session.
Lane: chore. Touches `.github/`, `scripts/`, a new `release/` folder, `VERSION.txt`.

## Goal

One command releases Wilsonic. Marcus pushes a tag. GitHub Actions builds the
macOS and Windows installers, signs and notarizes the macOS one, drafts release
notes, and creates a draft pre-release on GitHub. Marcus tests the installers on
M1 in Ableton Live and clicks Publish. The website updates itself.

No build step runs on M1, M2, or claw. M1 is for testing only.

## Decisions made

| # | Decision | Answer |
|---|----------|--------|
| 1 | Build machines | GitHub Actions hosted runners (macos-15, windows-2022) |
| 2 | Apple account state | Unknown. Marcus will check. Design covers both cases. |
| 3 | Where secrets live | GitHub Actions secrets in this repo |
| 4 | Windows signing | None for now. A signing step exists but is off. |
| 5 | Windows contents | Same as v0.43: 64-bit Wilsonic.exe, WilsonicController.exe, both VST3s, LIBMTS.dll, MTS-ESP.conf |
| 6 | Where the pipeline lives | This repo, under `release/`. The installer repo is archived after migration. |
| 7 | macOS packager | `pkgbuild` + `productbuild`. The Packages.app project is retired. |
| 8 | Trigger | Tag push `v*`, plus manual `workflow_dispatch` for test builds |
| 9 | Version source | One `VERSION.txt` file at the repo root. A script writes the other files. |
| 10 | Next version | `0.45.0-beta` |
| 11 | Test gate | CI creates a draft pre-release. Marcus tests on M1, then publishes by hand. |
| 12 | WilsonicController | Ships inside the same installer |
| 13 | Release notes | CI drafts from merged PR titles. Marcus edits before publish. |
| 14 | Docs per release | `docs/manual`, website pages, README Installation section |
| 15 | Website download links | The site reads GitHub Releases at build time |
| 16 | libMTS on macOS | Bundle the pinned version. Add a workflow that proposes updates. |
| 17 | ODDSound license | 0BSD. Redistribution is permitted. A LICENSE copy ships next to the binaries. |

## Decision log

The table above is what I decided before building. This log is what I
decided while building, in the order it happened, with the evidence and
with what would make me revisit each one. It is the record to come back to.
The layers below it are: this file for the why, `release/README.md` for how
it works today, the comments in `.github/workflows/release.yml` for the
line-by-line why, and the pull requests (#83, #84, #85 and onward) for the
history of each change. Run numbers are GitHub Actions run ids in this repo.

### 2026-11-11: CI Release builds run without link-time optimisation

The Projucer writes `LLVM_LTO = YES` into every Release configuration and
neither `.jucer` turns it off. On the three-core, 7 GB `macos-15` runner that
meant six monolithic LTO links per project, and the first two runs of the
workflow (42952880906 and 42958231779) were cancelled at the six-hour job
limit while still inside the Wilsonic build. I pass `LLVM_LTO=NO` on the
`xcodebuild` command line, which overrides the project, so the `.jucer`
files and local Xcode builds keep LTO. The CI binary is therefore an
ordinary `-O3` build. Revisit if `LLVM_LTO=YES_THIN` turns out to be
affordable, or if we ever measure that LTO changes the plugin's audio
performance enough to matter.

### 2026-11-11: build universal with the generic destination, and refuse anything else

Run 43001616208 was the first to finish, and its package held arm64-only
plugins inside an installer that declares `x86_64,arm64`. A scheme build
without a `-destination` lets Xcode pick "My Mac", which sets
`ONLY_ACTIVE_ARCH=YES`. Both builds now pass
`-destination 'generic/platform=macOS'`, and `build-pkg.sh` runs `lipo` on
all six products and refuses any that is not `arm64 x86_64`, so this cannot
slip through again. Revisit when Intel support is dropped, together with
`hostArchitectures` in `distribution.xml`.

### 2026-11-11: hand the system plug-in folders to the runner user

Both `.jucer` Release configurations set `vst3BinaryLocation` and
`auBinaryLocation`, so the exported projects end with an install phase that
copies into `/Library/Audio/Plug-Ins`, and run 42997408825 failed there with
`ditto: Permission denied`. The alternative was to edit both `.jucer` files,
which are a plugin-lane choke point. I chose a `sudo mkdir` and `chown` step
on the runner instead, because it touches nothing the plugin lane owns.
Revisit if the `.jucer` install locations change for another reason.

### 2026-11-14: move the dSYMs, free DerivedData, allow five and a half hours

Run 43010618605 was the first universal build. It took 3 h 44 min, so the
four-hour timeout I had added was too tight, and it died in the dSYM step
with `No space left on device`: each universal dSYM is 1.9 GB and a `ditto`
copy doubled them on a nearly full disk. The step now moves them and deletes
`~/Library/Developer/Xcode/DerivedData` before the upload, and the job
timeout is 330 minutes, still under the six-hour limit that discards the
logs. Run 43054238610 confirmed it: green in 3 h 39 min, with the disk going
from 8.5 GB free to 25 GB.

### 2026-11-14: pull-request dry runs build without debug symbols

Of the 3 h 39 min, compiling both architectures took 48 and 53 minutes per
project and `dsymutil` took 65 and 47, with three 1.9 GB dSYMs per project
being written at once on a 7 GB machine. A dry run only has to prove that
the pipeline still packages, so on `pull_request` the builds pass
`GCC_GENERATE_DEBUGGING_SYMBOLS=NO` and the two dSYM steps are skipped. Tag
and manual runs keep their debug symbols and dSYMs. The cost is that the
dSYM steps are exercised only by those runs, so a change to them needs
`gh workflow run release.yml --ref <branch>` rather than a pull request to
test. I predicted the dry run would take half the time; the first one, run
43669865878, took 1 h 02 min, with the compiles down to 30 and 29 minutes
because `-g` costs compile time as well as the `dsymutil` pass. Options I
have not taken yet, roughly by payoff: build the two
projects in parallel jobs and package in a third, throttle the three
`dsymutil` processes so they stop swapping, or move to a six-core runner if
one is free for a public repository.

### 2026-11-15: Windows Release builds run without whole program optimisation

The Projucer does on Windows what it does on the Mac: every Release
configuration gets whole program optimisation, `/GL` on the compiler and
`/LTCG` on the linker, and neither `.jucer` turns it off. I wanted a
measurement before deciding, so run 43761715303 built Wilsonic without it and
WilsonicController, which is nearly the same code, with it. Wilsonic built in
10 min 37 s. WilsonicController did not build at all: after 7 min 13 s the
librarian stopped on the shared-code library with `LNK1248: image size
(1003274F2) exceeds maximum allowable size (FFFFFFFF)`, because the `/GL`
object files came to more than 4 GB. That settled it without any comparison
of build times, and both projects now build with `LTO=NO`, an ordinary `/O2`
build, the same choice as on the Mac. What I have not checked is whether a Release
build in Visual Studio on my own Windows laptop fails the same way; I expect
it does, and the fix there would be the link-time optimisation setting of
the VS2022 Release configuration in both `.jucer` files, which is a
plugin-lane change. Revisit if that setting changes in the `.jucer`, which
would make the override redundant, or if the shared-code library is ever
small enough to try `/GL` again.

### 2026-11-15: the build switches go through Directory.Build.targets, and the script checks the log

The Projucer writes its compile and link settings as MSBuild item metadata,
and a `/p:` property on the `msbuild` command line cannot change item
metadata. The alternative was to edit both `.jucer` files, which are a
plugin-lane choke point. Instead `build-project.sh` copies
`release/windows/ci-build.targets` beside the generated solution as
`Directory.Build.targets`, which MSBuild imports after the project's own
settings, and that file turns off `/GL`, `/LTCG`, `/Zi` and the `.pdb` when
asked. Because a switch that silently does nothing is what cost the Mac job
its first two runs, the script then reads the `msbuild` log and fails if
`/GL` or `/Zi` is still on a compiler command line, or if a `.pdb` exists
when none should. Runs 43761715303 and 43763872675 passed that check with
both switches off, and runs 43763913790 and 43767579628 with debug symbols
on. Revisit if
the `.jucer` files ever carry these settings themselves.

### 2026-11-15: dry runs build without debug symbols on Windows too, and it saves almost nothing there

The Projucer's Visual Studio exporter generates debug symbols in Release by
default, so a tag or manual run produces three `.pdb` files per project and
uploads them as `Wilsonic_Win64_v<version>-PDBs`, the Windows counterpart of
the dSYM artifact. A `pull_request` dry run passes `DEBUG_SYMBOLS=NO` and
uploads none, the same rule as on the Mac. I expected a saving like the
Mac's and did not get one. With symbols, run 43763913790 built Wilsonic in
11 min 07 s and WilsonicController in 10 min 57 s, run 43767579628 took 14
min 26 s and 14 min 27 s, and uploading 331 MB of zipped `.pdb` files took
25 to 30 seconds. Without symbols, the builds took 10 min 37 s in run
43761715303 and 13 min 32 s each in run 43763872675. The difference between
two runners is larger than the difference the symbols make. (GitHub shows
runs 43763913790 and 43767579628 as cancelled. They are manual runs on the
branch, and I cancelled each one after its Windows job had finished green,
to stop a four-hour Mac job that had nothing new to tell me. For
43763913790 the numbers are from its first attempt.) I kept the rule so that the two platforms behave the same way and a
dry run uploads only installers. Revisit if having two paths ever hides a
bug in the `.pdb` upload; building symbols on every run would cost about
half a minute per project.

### 2026-11-15: the Projucer is built on the Windows runner and cached (open question 4)

Open question 4 asked what to do if building the Projucer on the Windows
runner took more than about ten minutes. It takes two and a half to three:
2 min 32 s in run 43761715303, 2 min 27 s in run 43763913790 and 3 min 04 s
in run 43763872675, all on a cache miss. On a hit, run 43767579628 restored
the 4.4 MB `Projucer.exe` in two seconds and skipped the build. The cache key is the runner image and the JUCE tag, the same shape as
the Mac's. So I do not commit the generated `Builds/` folders and I do not
publish a prebuilt Projucer. Revisit if a JUCE upgrade pushes the Projucer
build past ten minutes.

### 2026-11-15: the Windows job gets a 90 minute timeout

The whole job took 26 min 19 s in run 43763913790 and 31 min 14 s in run
43767579628, both with debug symbols and the `.pdb` upload, and 31 min 43 s
in run 43763872675, the dry run. Ninety minutes is about three times the
slowest, so a slow runner still
finishes and a stuck build fails long before GitHub's six-hour limit.
Revisit if a run comes within twenty minutes of the timeout.

### 2026-11-15: the installer keeps the v0.43 layout, with the VST3s as single files

The Projucer now builds each VST3 as a bundle folder,
`Wilsonic.vst3\Contents\x86_64-win\Wilsonic.vst3`, with a `moduleinfo.json`
beside it. The v0.43 installer installed only the module, as a single file
at `Common Files\VST3\Perfect Buzz Music\Wilsonic\Wilsonic.vst3`. I kept
that: `wilsonic.iss` takes the module out of the bundle and installs it to
the same path, under the same AppId `{78427BB9-1C86-41AB-BC1F-53E7203BDCDD}`
that `windows_installer_64.iss` used. An upgrade then replaces the old file
where it is. Installing the bundle instead would leave the v0.43 file in
place next to it, and a host could then find Wilsonic twice. The smoke test in
runs 43763913790 and 43763872675 confirmed the six install paths and that
the uninstall entry sits under that AppId with the right version. Run
43767579628 went further and installed the published v0.43 installer on the
runner, then the new one over it: v0.43 wrote the same four files to the
same paths under the same AppId, and after the upgrade Windows had one
Wilsonic entry, showing the new version. Revisit if
a host refuses the single-file form or I want `moduleinfo.json` installed;
the move to the bundle then needs an `[InstallDelete]` entry for the old
file.

### 2026-11-15: uninstalling Wilsonic leaves LIBMTS.dll and MTS-ESP.conf

This is the one place where the new installer deliberately behaves
differently from v0.43. `Common Files\MTS-ESP\LIBMTS.dll` is shared by every
MTS-ESP plugin on the machine, and the v0.43 uninstaller removed it, which
would break the other plugins. Both MTS-ESP files now carry
`uninsneveruninstall`. ODDSound's own installer marks itself
`Uninstallable=no`, which amounts to the same thing. Installing still
overwrites `LIBMTS.dll` with the pinned build and writes `MTS-ESP.conf`
only when there is none, as before, and the smoke test checks all three
behaviours on the runner. The flag was not enough on its own, and I only
learned that from a review of this pull request. v0.43 recorded both files
in its uninstall log, and Inno Setup appends to an existing log on an
upgrade, so someone who upgraded from v0.43 and later uninstalled would
still have lost `LIBMTS.dll`. `wilsonic.iss` therefore sets
`UninstallLogMode=overwrite`, which starts a fresh log. Inno Setup's
documentation advises against that mode because files an older version
installed and the new one does not would be left behind, and that does not
apply here because the file list is the v0.43 file list. Run 43767579628
checked it on the runner: v0.43 installed, the new installer over it, an
uninstall, and both MTS-ESP files still there. Revisit if I want uninstall to remove everything
Wilsonic installed, or when open question 3, downgrade protection for
libMTS, is settled for both platforms.

### 2026-11-15: the installer accepts Windows 11 on ARM

v0.43 said `ArchitecturesAllowed=x64`, which current Inno Setup deprecates.
The replacements are `x64os`, which keeps the old meaning, and
`x64compatible`, which also admits Windows 11 on ARM, where x64 hosts and
their x64 plugins run under emulation. I chose `x64compatible`. Nobody has
tried it on an ARM machine. Revisit if Wilsonic ever ships a native ARM64
Windows build.

### 2026-11-15: the Windows installer is named -unsigned on every kind of run

Windows signing is off (decision 4), so `prepare` outputs `win_signing=0`
for tag, manual and pull-request runs alike, and the file is
`Wilsonic_Win64_v<version>-unsigned.exe` in an artifact of the same name
without the extension, matching the Mac convention, and the suffix tells
whoever downloads the file that it is unsigned. The asset name this plan
gives for a release,
`Wilsonic_Win64_v0.45.0-beta.exe`, has no suffix, so Phase 5 has to decide
whether the release job publishes the file under its `-unsigned` name or
renames it. Revisit in Phase 5, and again when a certificate exists.

### 2026-11-15: bash scripts under Git Bash, Inno Setup from the runner image, and a silent install on the runner

Three smaller choices that belong together. The Windows scripts are bash,
run under the Git Bash that the runner image includes, so that
`test-windows-scripts.sh` can exercise them on my Mac with `msbuild` and
`ISCC.exe` faked; a `.gitattributes` keeps the scripts LF and the libMTS
files byte-exact, because Git for Windows would otherwise check them out
with CRLF and `MTS-ESP.conf` would stop matching `PIN`. Inno Setup is the
copy on the `windows-2022` image, version 6.7.1 in run 43763913790, and it
is not pinned. And after building the installer the job runs it silently on
the runner with `smoke-install.ps1`, checks what landed and uninstalls,
first as a fresh install and then as an upgrade over the v0.43 installer,
which it downloads from this repo's own v0.43-beta release and checks
against a sha256 in the workflow. That is a Windows Server image with no
audio host, so it tells me the installer works and nothing about whether
the plugin loads in a DAW. Revisit the
first if the image drops Git Bash, the second if a later image drops Inno
Setup or a new version changes the result, in which case the job should
install a pinned version itself, and the third after the first release from
this pipeline, when the upgrade test should start from that release.

### 2026-11-16: new Developer ID certificates and an API key for notarization (Phase 0)

Decision 2 in the table says the state of the Apple account was unknown. I
checked it. The Developer ID Application and Developer ID Installer
certificates that signed v0.43 both expired on 2026-10-04, so on 2026-11-16
I created new ones on my M1 music laptop, which is the only Mac that holds
their private keys. Both expire on 2027-12-16, so renewing them is a yearly
task, and it is written down under "Recurring maintenance" below. Each
certificate needed its own certificate signing request, because Apple
rejects a request file that has already been used. I created additional
certificates and revoked nothing, because revoking a Developer ID
certificate breaks the installed copies of software already signed with it.
Notarization uses an App Store Connect Team API key named "Wilsonic
Notarization" with the Developer role. Its key ID and issuer ID are in the
repository secrets and nowhere in this repo, which is public. I set the six
`APPLE_*` secrets the same day. Revisit before 2027-12-16, and if the API
key is ever revoked.

### 2026-11-16: a tag or manual run is always signed, and a missing secret fails it

The mac section of this plan used to say that when the signing secrets do
not exist the job should build ad hoc, skip notarization and name the asset
`-unsigned`, so that manual test builds kept working while the Apple account
was unsorted. The account is sorted, so I took that fallback out. `prepare`
turns signing on for every tag push and every manual run and off for every
pull request, and nothing else decides it. A signed run that is missing a
secret stops in the first minute of the mac job and names the secret. The
failure I most want to avoid is a release that goes out unsigned without
anyone noticing, and a run that fell back would have looked green. The pull
request dry run is still there for anyone who wants an unsigned package.
Revisit if I ever need an unsigned build from a branch that has no pull
request.

### 2026-11-16: the secrets are tried out before the build starts, and the keychain exists only while signing

`release/mac/signing-keychain.sh check` runs right after the script tests,
before JUCE is cloned. It makes a temporary keychain, imports both `.p12`
files, checks that both identities are valid, signs a scratch file with each
of them with a secure timestamp, and asks App Store Connect for the
notarization history with the API key. It submits nothing to Apple. When I
wrote it the six secret values had never been used, and the build that sits
between this step and the real signing takes about three and a half hours,
so I wanted a wrong `.p12` password or a wrong issuer ID to cost one minute
and to say which secret it was. The same step prints the day each
certificate expires and puts a warning on the run when one has fewer than 45
days left.

Then it deletes the keychain and the decoded key again. My first version
kept them for the signing step, and a code review of the branch pointed out
that this left an unlocked signing keychain and the notary key on the runner
for the whole build, beside a JUCE clone, a Projucer restored from a cache
and everything `xcodebuild` runs. So the job now runs
`signing-keychain.sh setup` a second time once the build has finished, just
before `build-pkg.sh`, and a step marked `if: always()` deletes the keychain
and the key after the verify step whether the job passed or failed. Making
the keychain twice costs a second or two. No script that touches a secret
prints one or runs with tracing on, and `test-signing.sh` checks that by
planting recognisable fake secrets and searching every log for them.

I tried the whole signed path once before the first full build, as run
43986494367 on a throwaway branch where stub bundles stood in for the JUCE
build, and the mac job took 70 seconds, notarization included. All six
secrets worked the first time, which I had not expected. That stub package
was notarized under my team and never uploaded, and the branch is deleted.
A second short run, 43988075748, tried the check-then-setup order with stub
bundles and without submitting anything to Apple, and confirmed that the
signing folder and the keychain are gone between the two steps and again at
the end. Revisit if the probe signing ever fails for a reason that has
nothing to do with the secrets, such as Apple's timestamp server being down,
because then it would block a release that might have gone through three
hours later. Open question 8 is about who can reach these secrets at all.

### 2026-11-16: the Developer ID signature goes on after the build, in build-pkg.sh

Step 4 of the mac job in this plan had `xcodebuild` sign with the Developer
ID identity. I left the build signed ad hoc on every kind of run and put the
real signing in `build-pkg.sh`, which already had a `SIGNING=1` path from
Phase 2. A dry run then builds exactly what a release builds, Xcode never
needs the keychain, and the signing lives in a script that
`release/mac/test-signing.sh` exercises on my Mac. Signing a bundle a second
time replaces its signature and its entitlements with it, so the script
first reads the entitlements Xcode gave each bundle and hands them back to
`codesign`. Today that is one entitlement on each standalone app,
`com.apple.security.cs.allow-dyld-environment-variables`, which comes from
`hardenedRuntimeOptions` in the `.jucer` files, and none on the plugins. I
read that off the package from run 43770766926 before writing the script.
The script drops `com.apple.security.get-task-allow` if it ever finds it,
because Xcode can add it to a build and Apple refuses to notarize it. One
consequence is that the `release/mac/entitlements.plist` this plan once
listed does not exist. The `.jucer` files remain the one place where
entitlements are declared, and a change there reaches the release without
any change here. Every bundle is signed with the hardened runtime and a
secure timestamp, and `productsign` signs the package with a timestamp too.
Revisit if a bundle ever gains nested code such as a helper or a framework.
The deep verify that follows each signing call will fail when that happens,
and the script will then have to sign from the inside out.

### 2026-11-16: libMTS.dylib ships with ODDSound's own signature

I expected to have to sign `libMTS.dylib` myself, because Apple notarizes a
package only when every binary inside it carries a Developer ID signature
and a secure timestamp. ODDSound already takes care of that. The pinned
build is signed by `Developer ID Application: David Gamble (ZTMS6M322L)`
with a timestamp of 2025-08-26. So the package installs their bytes
unchanged. The file still matches `PIN`, it still carries the signature of
the people who built it, and every other MTS-ESP plugin on the machine loads
the same file it would get from ODDSound's own installer. With `SIGNING=1`,
`build-pkg.sh` checks that signature before it builds anything and stops if
it is missing, and `verify-pkg.sh` compares the packaged copy with `PIN`.
Apple's notary service accepted the package that way in run 43986494367, and
its log lists both slices of `libMTS.dylib` in the ticket. Revisit if a future libMTS arrives unsigned or Apple starts
refusing it. Signing it with my identity would be the fallback, and the
`PIN` comparison in the tests would then need rethinking. Looking at this
turned up something else, which is open question 7.

### 2026-11-16: four checks on the finished package, and the upload depends on them

After stapling, `release/mac/verify-pkg.sh` runs
`pkgutil --check-signature`, `spctl -a -vv -t install`,
`xcrun stapler validate`, and `codesign --verify --deep --strict` on each of
the six bundles inside the package, and it also checks that each bundle
names my Developer ID Application identity, has a secure timestamp and the
hardened runtime, and carries no `get-task-allow`. One miss fails the job,
and the upload step comes after it, so a package that failed a check never
becomes an artifact. For `spctl` the script insists on the words
`source=Notarized Developer ID`, because on a machine where Gatekeeper is
switched off `spctl` accepts everything and that acceptance would prove
nothing. When Apple rejects a submission, `notarize.sh` prints Apple's log
for it and fails; it prints the log for an accepted one as well, because an
accepted submission can still carry warnings. Run 43986494367 passed every check on the stub package, with `spctl`
answering `accepted`, `source=Notarized Developer ID`. What the job
cannot tell me is whether the package installs and the plugins load on a
real Mac. That is still the test gate, and I have not done it yet for a
signed package.

## Facts that shape the design

- This repo is public, so GitHub-hosted runners cost nothing, macOS included.
- `plugin.yml` already builds both projects on macos-15 with JUCE 9.0.1. It
  builds Projucer from source each run. The release workflow reuses that recipe
  and caches the Projucer build.
- The v0.43 macOS package had seven components: standalone, AU, and VST3 for
  each of Wilsonic and WilsonicController, plus an MTS-ESP support component
  that installed `libMTS.dylib` and `MTS-ESP.conf` to
  `/Library/Application Support/MTS-ESP`. The Distribution set
  `hostArchitectures="x86_64,arm64"`. The new scripts reproduce this exactly.
- v0.43 shipped libMTS 1.02. ODDSound's current release is 1.03
  (2025-09-04). Their repo publishes a universal `libMTS.dylib`, 32 and 64 bit
  `LIBMTS.dll`, a `CHANGELOG.md`, and `MTS-ESP.conf` under `libMTS/`.
- The vendored `Source/MTS-ESP/libMTSMaster.{h,cpp}` date from November 2023.
  ODDSound's current `Master/` fixed a name clash (2025-09-30) and documents
  `MTS_Master_ShouldUpdateLibrary()`, which lets the plugin tell the user their
  installed libMTS is older than the API it was built with.
- The version number lives in four files today: `version.h`, `Wilsonic.jucer`,
  `WilsonicController.jucer`, and the Inno Setup script.
- The website hardcodes the two v0.43 asset URLs in
  `components/ui/download-buttons.tsx` and names the version in
  `app/downloads/page.tsx`. The website already renders `docs/manual` and
  `docs/blog` from this repo, and `website-deploy-hook.yml` already triggers a
  Vercel rebuild when docs merge.
- GitHub's `releases/latest` endpoint skips pre-releases. The website must list
  releases and take the newest one that is not a draft.

## Repository layout after the change

```
VERSION.txt                      # 0.45.0-beta (not "VERSION": that name shadows the C++ <version> header on macOS)
release/
  README.md                      # how to cut a release, one page
  mac/
    build-pkg.sh                 # pkgbuild x7, productbuild, and with SIGNING=1 codesign x6 and productsign
    distribution.xml             # title, hostArchitectures, choices, pkg-refs
    signing-keychain.sh          # the temporary keychain from the Apple secrets: check before the build, setup before signing, teardown after
    notarize.sh                  # notarytool submit --wait, Apple's log, stapler staple
    verify-pkg.sh                # pkgutil, spctl, stapler and codesign checks on the finished package
    test-build-pkg.sh            # test for the packaging, from fake bundles
    test-signing.sh              # test for the four signing scripts, with security, productsign, spctl and xcrun faked
    test-lib.sh                  # what the two tests share
  windows/
    wilsonic.iss                 # Inno Setup, paths relative to repo root, version from /DVersion
    check-exporter.sh            # both .jucer files have a VS2022 exporter with a Release configuration
    build-project.sh             # msbuild one solution, Release x64, LTO and debug symbols switchable
    ci-build.targets             # the MSBuild overrides behind those two switches
    build-installer.sh           # PIN check, x64 check, ISCC
    smoke-install.ps1            # silent install, check, uninstall; for the runner or a VM
    test-windows-scripts.sh      # test for the scripts, with msbuild and ISCC faked
  mts-esp/
    PIN                          # ODDSound commit sha, libMTS version, sha256 of each binary
    LICENSE                      # ODDSound 0BSD text
    MTS-ESP.conf
    Mac/libMTS.dylib             # universal x86_64 + arm64
    Win/64bit/LIBMTS.dll
    Win/32bit/LIBMTS.dll         # kept for parity with ODDSound; not installed
scripts/
  set-version.sh                 # VERSION.txt -> version.h, both .jucer, nothing else
  check-version.sh               # fails if VERSION.txt, version.h, .jucer, and git tag disagree
  check-release-docs.sh          # fails if README or docs/manual name a version other than VERSION.txt
.github/
  release.yml                    # categories for generated release notes, by PR label
  workflows/
    release.yml                  # the pipeline
    mts-esp-bump.yml             # weekly check for a newer libMTS, opens a PR
    website-deploy-hook.yml      # existing, plus a `release: published` trigger
```

The three `.command` scripts, the `.pkgproj`, and `symbolicate*` do not move.
The installer repo keeps them as history and is archived.

## Version handling

`VERSION.txt` holds a semver string such as `0.45.0-beta`. The rules:

1. `scripts/set-version.sh` reads `VERSION.txt` and writes:
   - `version.h`: `VERSION_MAJOR 0`, `VERSION_MINOR 45`, `VERSION_PATCH 0`,
     `VER_NUM 0.45.0`, `VERSION_STRING "0.45.0-beta"`, `BETA 1` when the
     string has a `-` suffix, else `0`.
   - both `.jucer` files: `version="0.45.0"`. Projucer wants numeric fields.
   - Then it runs `Projucer --resave` on both projects when Projucer is present.
2. `scripts/check-version.sh` runs in CI on every PR and on tag push. On tag
   push it also checks `v$(cat VERSION.txt)` equals the tag.
3. Marcus bumps a version with one command, then commits and tags:

```bash
echo 0.45.0-beta > VERSION.txt && scripts/set-version.sh
git commit -am "chore: bump version to 0.45.0-beta"
git tag v0.45.0-beta && git push && git push --tags
```

A tag that contains `-` creates a pre-release. A tag without one creates a
normal release. Both start as drafts.

Asset names: `Wilsonic_Mac_v0.45.0-beta.pkg` and
`Wilsonic_Win64_v0.45.0-beta.exe`. The macOS asset is the notarized, stapled
`.pkg` itself. v0.43 wrapped it in a `.zip`, which added a step for users and
hid the stapled ticket from Gatekeeper on first open. See open question 1.

## The release workflow

`release.yml` runs on `push: tags: ['v*']` and on `workflow_dispatch` with
inputs `version` (string) and `publish` (boolean, default false). Four jobs.

It also runs on `pull_request` for changes under `release/` or to the
workflow file itself, as a dry run: `prepare`, `mac` and `windows`,
`SIGNING=0` forced, the artifacts named `-unsigned`, no tag check, no
secrets read and nothing published. That way a change to the packaging is
exercised on real macOS and Windows runners before it merges. The `release`
job does not run on `pull_request`.

### prepare (ubuntu)

1. Check out. Run `scripts/check-version.sh` and `scripts/check-release-docs.sh`.
2. Output `version`, `is_prerelease`, `mac_asset`, `win_asset`.

### mac (macos-15)

1. Restore a cached Projucer 9.0.1 build. Build it on a cache miss. Cache key
   is the JUCE tag.
2. `Projucer --resave` both `.jucer` files.
3. On a tag push or a manual run, `release/mac/signing-keychain.sh check`:
   create a temporary keychain, import the Developer ID Application and
   Developer ID Installer `.p12` files, check that all six secrets work
   before the build starts, and delete the keychain again. A missing secret
   fails the run. A pull request dry run skips this, reads no secrets, and
   names its asset `...-unsigned.pkg`.
4. `xcodebuild` Release for `Wilsonic - All` and `WilsonicController - All`
   with `CODE_SIGN_IDENTITY="-"`, on every kind of run, and `LLVM_LTO=NO` on
   the command line, because the Projucer's Release default of full LTO ran
   the Wilsonic build past the six-hour job limit on the hosted runners.
   Outputs land in `Builds/MacOSX/build/Release` and
   `Builds/MacOSX-WilsonicController/build/Release`.
5. On a tag push or a manual run, `release/mac/signing-keychain.sh setup`
   makes the keychain again, now that the build is over. Then
   `release/mac/build-pkg.sh`:
   - stage each product into its own root
     (`/Applications`, `/Library/Audio/Plug-Ins/Components`,
     `/Library/Audio/Plug-Ins/VST3`, `/Library/Application Support/MTS-ESP`)
   - when signing is on, `codesign` each of the six bundles with
     `Developer ID Application: Perfect Buzz Music (LXFXL9GS49)`, the
     hardened runtime, a secure timestamp and the entitlements the build
     gave it
   - `pkgbuild` one component package per product with the same identifiers
     v0.43 used, for example `com.marcussatellite.Wilsonic-MTS-ESP.vst3`,
     so upgrades over v0.43 replace cleanly
   - `productbuild --distribution release/mac/distribution.xml` into one
     `.pkg`, with `hostArchitectures="x86_64,arm64"` set in the XML rather
     than patched in afterwards
   - `productsign` with Developer ID Installer when signing is on
6. `release/mac/notarize.sh`: `xcrun notarytool submit --wait` with the App
   Store Connect API key, then `xcrun stapler staple`. It prints
   `notarytool log` for the submission and fails on anything but Accepted.
7. `release/mac/verify-pkg.sh`: `pkgutil --check-signature`,
   `spctl -a -vv -t install`, `xcrun stapler validate`, and
   `codesign --verify --deep --strict` on each bundle. Then, always, delete
   the keychain and the decoded key.
8. Upload the `.pkg` and the `.dSYM` folders as artifacts. A `pull_request`
   dry run builds without debug symbols and uploads only the `.pkg`.

### windows (windows-2022)

As built in Phase 4. The steps run under Git Bash, so the scripts are the
same ones the test runs on a Mac.

1. `release/windows/check-exporter.sh`: both `.jucer` files must have a
   Visual Studio 2022 exporter with a Release configuration. Then
   `release/windows/test-windows-scripts.sh`, which also compiles
   `wilsonic.iss` with the runner's real `ISCC.exe` from fake products.
2. Clone JUCE 9.0.1 to `C:\JUCE`, which is the Projucer's default global
   module path on Windows, and restore a cached `Projucer.exe`. On a miss,
   build the Projucer with `msbuild`.
3. `Projucer --resave` both `.jucer` files.
4. `release/windows/build-project.sh Builds/VisualStudio2022/Wilsonic.sln`
   and the same for
   `Builds/VisualStudio2022-WilsonicController/WilsonicController.sln`. That
   is `msbuild -p:Configuration=Release -p:Platform=x64` with whole program
   optimisation off, and with debug symbols off on a `pull_request` dry run.
5. Signing step: present, disabled, documented. Turning it on takes the
   secrets, uncommenting its `env` block, and making `prepare` output
   `win_signing=1`.
6. `release/windows/build-installer.sh`, which checks libMTS against `PIN`,
   checks that the products are x64 and runs Inno Setup from the runner
   image: `ISCC.exe /DVersion=0.45.0-beta release/windows/wilsonic.iss`. The
   script uses paths relative to the repo root and takes its version from the
   `/D` define.
7. `release/windows/smoke-install.ps1`: install the result silently on the
   runner, check the six files, the MTS-ESP.conf rule and the uninstall,
   then do it again as an upgrade over the published v0.43 installer.
8. Upload the `.exe` as an artifact, `Wilsonic_Win64_v<version>-unsigned`,
   and on tag and manual runs the `.pdb` files as a second one.

### release (ubuntu, after mac and windows)

1. Download both artifacts.
2. On tag push, or on manual run with `publish: true`:
   `gh release create v0.45.0-beta --draft --prerelease --generate-notes --title "Wilsonic 0.45.0-beta" <assets>`.
   `--generate-notes` builds the body from merged PR titles since the previous
   tag, grouped by `.github/release.yml` categories.
3. On manual run with `publish: false`, stop here. The artifacts stay
   downloadable from the workflow run for 90 days.

### Secrets

| Secret | Contents |
|--------|----------|
| `APPLE_DEV_ID_APP_P12` | base64 of the Developer ID Application certificate and key |
| `APPLE_DEV_ID_INSTALLER_P12` | base64 of the Developer ID Installer certificate and key |
| `APPLE_P12_PASSWORD` | password used when exporting the two `.p12` files |
| `APPLE_API_KEY_ID` | App Store Connect API key ID |
| `APPLE_API_ISSUER_ID` | App Store Connect issuer ID |
| `APPLE_API_KEY_P8` | base64 of the `.p8` private key |
| `VERCEL_DEPLOY_HOOK_URL` | already defined for the docs hook |

Secrets are never available to pull requests from forks, and `release.yml`
runs on `pull_request` only as an unsigned dry run of `prepare`, `mac` and
`windows`, with no secrets.

## Test gate

1. CI leaves a draft pre-release with both installers attached.
2. Marcus downloads both to M1 and installs them over the previous version.
3. Marcus runs the checks in `release/README.md`: standalone opens, AU passes
   `auval -v aumu Wlsn Mrcs`, VST3 loads in Ableton Live, a tuning reaches a
   client synth over MTS-ESP, WilsonicController loads.
4. Marcus edits the release notes and clicks Publish.
5. Publishing fires the `release: published` event. The deploy-hook workflow
   rebuilds the website.

If a test fails, Marcus deletes the draft and the tag, fixes, and tags again.

## Website

1. `download-buttons.tsx` and `app/downloads/page.tsx` stop hardcoding URLs.
   A small server-side helper calls `GET /repos/marcus-w-hobbs/Wilsonic-MTS-ESP/releases`,
   filters out drafts, takes the first entry, and picks the asset whose name
   ends in `.pkg` and the one that ends in `.exe`. The page shows the tag name
   and the publish date. It falls back to the releases page URL if the API
   call fails.
2. The page revalidates once per hour, same as the docs. The deploy hook makes
   a publish visible within about a minute.
3. `website-deploy-hook.yml` gains `on: release: types: [published]`.

This is one PR in the wilsonic-website repo. It can land before the first new
release, because the v0.43 release already matches the filter.

## Docs per release

- `docs/manual/installation.md` and the README Installation section stop
  naming a version. They say "the latest release" and link to the releases
  page. `scripts/check-release-docs.sh` fails CI if any `v0.\d+` string other
  than the current version appears in those files.
- `docs/manual/installation.md` gains a short section on what the installer
  puts where, including the MTS-ESP support component, and how to uninstall.
- The website renders `docs/manual` from this repo, so those changes reach
  the site through the existing hook.
- Website-only pages that name a version (today, the downloads page) switch to
  the API helper above.

## libMTS pinning and updates

Why pin: a user's installed `libMTS` is shared by every MTS-ESP plugin on the
machine. Shipping it inside the Wilsonic installer means a fresh machine works
with one download. The risk is shipping an old one. v0.43 shipped 1.02 for
over a year after 1.03 came out.

Design:

1. `release/mts-esp/PIN` records the ODDSound commit sha, the libMTS version
   from their `CHANGELOG.md`, and the sha256 of each binary. The release
   workflow verifies the hashes before packaging.
2. `mts-esp-bump.yml` runs weekly and on demand. It fetches ODDSound `main`,
   reads `libMTS/CHANGELOG.md`, and compares the top version to `PIN`. When
   newer, it downloads the binaries, `MTS-ESP.conf`, and `Master/*.{h,cpp}`,
   writes `PIN`, and opens a PR titled `chore: bump libMTS to 1.04` with the
   changelog entry in the body. Marcus reviews and merges. The `Master`
   source is in the plugin lane, so the PR touches two lanes on purpose and
   says so in its body. If that is unacceptable, the bump opens two PRs.
3. The installers overwrite an existing `libMTS` with the pinned one.
   ODDSound states that newer libMTS is backward compatible with older
   masters, but says nothing about the reverse, so overwriting with an older
   file is the one case to avoid. See open question 3.
4. The plugin calls `MTS_Master_ShouldUpdateLibrary()` after registering and
   shows a one-line notice with a link to ODDSound's installer when it returns
   true. This covers users who installed Wilsonic once and never updated.

## One-time setup for Marcus

1. On developer.apple.com, confirm team LXFXL9GS49 is active. Find or create
   a Developer ID Application and a Developer ID Installer certificate. Export
   each with its private key as `.p12` from Keychain Access on the Mac that
   holds the key. If no Mac holds the key, or the certificate has expired,
   create an additional certificate with a new certificate signing request,
   one request per certificate. Never revoke a Developer ID certificate to
   make room for a new one, because revoking it breaks the installed copies
   of software already signed with it.
2. On App Store Connect, Users and Access, Integrations, create a Team key
   with the Developer role. Download the `.p8` once.
3. Add the six Apple secrets to this repo. Delete the local `.p12` and `.p8`
   files afterwards.
4. Confirm `VERCEL_DEPLOY_HOOK_URL` exists.
5. Run the workflow by hand once with `publish: false` to confirm signing and
   notarization pass.

All five were done by 2026-11-16. The decision log has the details.

## Recurring maintenance

What has to happen on a calendar, whether or not there is a release.

- **Every year, before 2027-12-16 the first time: renew the two Developer ID
  certificates.** Both the Application and the Installer certificate expire
  on 2027-12-16. On the Mac that will hold the new private keys, which today
  is my M1, make a new certificate signing request in Keychain Access for
  each certificate, because Apple rejects a request file that was already
  used. On developer.apple.com create an additional Developer ID Application
  and an additional Developer ID Installer certificate from those requests.
  Do not revoke the old ones. Export each new certificate with its private
  key as a `.p12`, set `APPLE_DEV_ID_APP_P12` and
  `APPLE_DEV_ID_INSTALLER_P12` to `base64 -i <file>` of each, set
  `APPLE_P12_PASSWORD` if the password changed, and delete the `.p12` files.
  Then run the workflow by hand, `gh workflow run release.yml`, and check
  that the mac job passes. The setup step of that job prints the expiry date
  of both certificates on every signed run and raises a warning on the run
  once either has fewer than 45 days left, so a release in the last weeks
  will remind me. If the name on the certificates ever changes, the two
  identity names in the `env` block of the `mac` job change with it.
- **The App Store Connect API key** has no expiry date. It needs replacing
  only if it is revoked or leaks: create a new Team key with the Developer
  role and set `APPLE_API_KEY_ID`, `APPLE_API_ISSUER_ID` and
  `APPLE_API_KEY_P8` again.
- **libMTS** is checked weekly by `mts-esp-bump.yml` once Phase 8 exists.
  Until then I look at ODDSound's repository before each release.

## Migration from the installer repo

1. Copy `LIBMTS.dll` files and `MTS-ESP.conf` into `release/mts-esp/`, then
   replace them with ODDSound's 1.03 versions and write `PIN`.
2. Port `windows_installer_64.iss` to `release/windows/wilsonic.iss`.
3. Port the component list from the `.pkgproj` into `build-pkg.sh` and
   `distribution.xml`. The identifiers and install paths are known from the
   expanded v0.43 package.
4. In the installer repo: untrack and purge the two password files, rotate
   those credentials, update its README to point here, archive it on GitHub.

## Phases

| Phase | Deliverable | Verify by | Status |
|-------|-------------|-----------|--------|
| 0 | Apple secrets in place | `security find-identity` inside a manual workflow run lists both Developer ID certs | Complete, 2026-11-16 |
| 1 | `VERSION.txt`, `set-version.sh`, `check-version.sh`, CI check on PRs | A PR that edits `version.h` by hand fails CI | Merged, #83 |
| 2 | `release/mac/*`, `mac` job, manual run unsigned | `.pkg` artifact installs on M2 with `SIGNING=0` semantics | Merged, #84, #85 and #86 |
| 3 | `mac` job signed and notarized | `spctl --assess --type install` passes on the downloaded `.pkg` | Merged 2026-11-16, #89. Run 43988398507 produced the signed package. Not yet installed on a real Mac |
| 4 | `release/windows/*`, `windows` job | `.exe` artifact installs on claw or a Windows VM | Merged 2026-11-16, #88. Not yet installed on a real Windows machine |
| 5 | `release` job, draft pre-release, generated notes | Tag `v0.45.0-beta` produces a draft with two assets and a notes body | |
| 6 | Website reads releases, hook on publish | Publishing the draft changes the download buttons within a few minutes | |
| 7 | Docs check and manual updates | `check-release-docs.sh` passes on main | |
| 8 | `mts-esp-bump.yml` | Manual run against a fake older `PIN` opens a PR | |
| 9 | Installer repo archived | Repo shows Archived on GitHub | |

Phases 1, 2, and 4 can start before Phase 0 completes. Phase 3 and 5 need it.

Phase 0 was finished on 2026-11-16. I created the two Developer ID
certificates and the App Store Connect API key and set the six `APPLE_*`
secrets, and the decision log entry of that date has the details. Its verify
step is the first thing the signed mac job does. In run
43986494367 `security find-identity` listed both identities as valid, each
key signed a scratch file with a secure timestamp, and App Store Connect
accepted the API key.

Phase 3 was built on 2026-11-16: on a tag push or a manual run the `mac` job
signs the six bundles and the package, notarizes the package with Apple,
staples the ticket and checks the result with `pkgutil`, `spctl`, `stapler`
and `codesign`. Run 43986494367 did all of that on stub bundles, and pull
request #89 merged the same day.

The first run on the real build was 43988398507, a manual run on the last
commit of the branch. It was still building when I merged, and it finished
green about an hour and twenty minutes later. The `mac` job took 3
hours 25 minutes with debug symbols. The two builds took 94 and 105 minutes
of that, and everything Phase 3 added took about two minutes: 3 seconds to
try the secrets out before the build, 3 seconds to make the keychain again
after it, 21 seconds to sign the six bundles and build and sign the package,
73 seconds for Apple to notarize it and for the staple, and 19 seconds to
verify. Apple accepted the package with no issues, and
`spctl -a -vv -t install` answered `accepted` and
`source=Notarized Developer ID` on the runner. The same commit's pull
request dry run, 43988377347, stayed unsigned and skipped every step that
reads a secret.

The verify step of this phase asks for `spctl` to pass on the downloaded
`.pkg`, so the Claude Code session that built the phase downloaded the
artifact to my M2, on macOS 26.5.1, and checked it there without installing
it. `spctl` gave the same answer,
`xcrun stapler validate` passed, and `pkgutil --check-signature` printed
"Notarization: trusted by the Apple notary service", a line that the
macOS 15 runner does not print even for a stapled package. One part is
still open. Nobody has installed the signed `.pkg` on a real Mac yet, so
nothing is known about how the installer behaves on macOS 14, whether the
plug-ins load in a host, or whether the standalone apps can load ODDSound's
library, which is open question 7. That test is mine to do on the M1.

Phase 4 was built on 2026-11-15 in pull request #88, which merged on
2026-11-16: `release/windows/` and
the `windows` job, which produces `Wilsonic_Win64_v0.44.0-unsigned.exe` on
the `windows-2022` runner and installs it there silently as a smoke test,
fresh and as an upgrade over v0.43. Its verify step is still open. Nobody
has installed the `.exe` on a real Windows machine yet, and that test is
mine to do on claw or in a VM, including a VST3 scan in a host and a tuning
sent to a client over MTS-ESP.

## Open questions

1. macOS asset as bare `.pkg` or as `.zip`? I recommend bare `.pkg`.
2. Does the plugin need a macOS deployment target change? `plugin.yml` builds
   with `-sdk macosx15.5`. The installer should state the minimum macOS
   version in `distribution.xml` so older machines get a clear message.
3. libMTS downgrade protection on macOS. Options: a preinstall script that
   reads the ODDSound receipt with `pkgutil --pkg-info` and skips the
   component when a newer one is installed, or accept the overwrite because
   the bump workflow keeps the pin current. I recommend the preinstall script
   when it costs under an hour, otherwise accept.
4. Projucer build time on the Windows runner. If it exceeds about ten minutes
   even with caching, commit the generated `Builds/` for the two exporters
   instead, or publish a prebuilt Projucer as a release asset of this repo.
   Answered on 2026-11-15: it takes two and a half to three minutes on a
   cache miss and a second or two on a hit, so neither fallback is needed. The
   run numbers are in the decision log.
5. Should `auval` run on the CI runner as a smoke test? It needs the
   component installed in `~/Library/Audio/Plug-Ins/Components`, which the
   runner allows. It catches a broken AU before Marcus downloads anything.
6. Which GitHub labels group the release notes? A first cut:
   `feature`, `fix`, `research`, `docs`, `chore`.
7. Can the standalone apps load libMTS at all? Both are signed with the
   hardened runtime, and their only entitlement is
   `com.apple.security.cs.allow-dyld-environment-variables`. Under the
   hardened runtime macOS refuses to load a library signed by a different
   team unless the app has
   `com.apple.security.cs.disable-library-validation`, and `libMTS.dylib` is
   signed by ODDSound's team. I tried it on 2026-11-16 with a ten-line
   program that calls `dlopen` on the installed `libMTS.dylib`: it loads
   normally, fails with "mapping process and mapped file (non-platform) have
   different Team IDs" once the program is signed with the hardened runtime,
   and loads again with that entitlement added. The v0.43 standalone has the
   same signature shape, so if this is a problem it is an old one. I have
   not run the Wilsonic standalone itself to see whether it registers as the
   MTS-ESP master. The plugins inside a host are a different case, because
   the host process does the loading. If the standalone is affected, the fix
   is to add the entitlement to `hardenedRuntimeOptions` in both `.jucer`
   files, which is a plugin-lane change, and the release signing would pick
   it up without any change here.
8. Should the six Apple secrets move into a GitHub Environment? They are
   repository secrets today, so the `if:` conditions in `release.yml` keep
   an honest pull request away from them and nothing more. Anyone who can
   push a branch to this repo could edit the workflow in that branch and
   read them, and so could a manual run on any branch or a `v*` tag on any
   commit. Pull requests from forks cannot. An environment, say `release`,
   that only `main` and `v*` tags may deploy to, with `environment: release`
   on the `mac` job, would close that. The cost is that a manual run on a
   branch could then no longer sign, and that is exactly how Phase 3 was
   tested before it merged. A required reviewer on the environment would
   keep branch runs possible with my approval. Today I am the only person
   with write access, so this is mine to decide and it changes repository
   settings, which is why it is a question here. The same review suggested
   pinning the JUCE clone and the GitHub actions to commit hashes in place
   of tags.

## Assumptions

- The plugin repo stays public.
- The Developer ID team remains LXFXL9GS49 and the installer identifiers stay
  under `com.marcussatellite.`.
- 32-bit Windows is not shipped. The 32-bit DLL is vendored only to mirror
  ODDSound's layout.
- No Linux installer in this round. The Linux CI build stays as a gate only.
