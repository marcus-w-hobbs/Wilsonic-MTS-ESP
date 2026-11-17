# Release tooling

This folder holds what turns a built Wilsonic into an installer. The design
and the phases it is built in are in [plans/release-pipeline.md](../plans/release-pipeline.md).
As of Phase 3 a tag push or a manual run builds the macOS package signed
with my Developer ID certificates, notarized by Apple and stapled. The
Windows installer is built unsigned. A pull request builds both unsigned as
a dry run. The GitHub release itself is a later phase.

## What is here

| Path | Purpose |
|------|---------|
| `mac/build-pkg.sh` | Builds the macOS installer from already-built products with `pkgbuild` and `productbuild`. |
| `mac/distribution.xml` | The product definition: title, `hostArchitectures="x86_64,arm64"`, minimum macOS, one choice per component. |
| `mac/test-build-pkg.sh` | Test for the two files above. It fakes the six product bundles, so it needs neither Xcode nor a certificate. |
| `mac/signing-keychain.sh` | `setup` turns the six Apple secrets into a temporary keychain and a notary key file, and checks that every one of them works. `unlock` unlocks the keychain again. `teardown` deletes all of it. |
| `mac/notarize.sh` | Submits a signed package to Apple with `notarytool`, waits, prints Apple's log, and staples the ticket. |
| `mac/verify-pkg.sh` | Checks a finished package with `pkgutil`, `spctl`, `stapler` and `codesign`, and fails on any miss. |
| `mac/test-signing.sh` | Test for the three scripts above and for `build-pkg.sh` with `SIGNING=1`. It fakes `security`, `productsign`, `spctl` and `xcrun`, and signs ad hoc, so it needs no certificate and no Apple account. |
| `mac/test-lib.sh` | The assertions and fake bundles the two tests share. |
| `windows/wilsonic.iss` | The Inno Setup script for the 64-bit Windows installer. Paths are relative to the repo root and the version comes from `/DVersion=`. |
| `windows/check-exporter.sh` | Checks that both `.jucer` files have a Visual Studio 2022 exporter with a Release configuration, and says which one does not. |
| `windows/build-project.sh` | Builds one generated solution in Release for x64 with `msbuild`, with link-time optimisation and debug symbols switched by `LTO` and `DEBUG_SYMBOLS`. |
| `windows/ci-build.targets` | The MSBuild file behind those two switches. `build-project.sh` copies it beside the solution as `Directory.Build.targets`. |
| `windows/build-installer.sh` | Checks libMTS against `PIN`, checks the products are x64, and runs Inno Setup's `ISCC.exe` on `wilsonic.iss`. |
| `windows/smoke-install.ps1` | Installs an installer silently, checks what landed, and uninstalls. With `-UpgradeFrom` it installs an older installer first. For the CI runner or a VM. |
| `windows/test-windows-scripts.sh` | Test for the scripts above. It fakes `msbuild`, `ISCC.exe` and the build products, so it runs on a Mac. |
| `mts-esp/` | ODDSound's libMTS 1.03 as vendored: the universal `Mac/libMTS.dylib`, both Windows `LIBMTS.dll`, `MTS-ESP.conf`, their 0BSD `LICENSE`, and `PIN`. |
| `mts-esp/PIN` | The ODDSound commit, the libMTS version from their changelog, and the sha256 of each binary. `build-pkg.sh` refuses to package if a file does not match. |

## Running build-pkg.sh on a Mac

I build both projects in Release first, with Xcode or with the Projucer and
`xcodebuild`, so that these six bundles exist:

```
Builds/MacOSX/build/Release/Wilsonic.app
Builds/MacOSX/build/Release/Wilsonic.component
Builds/MacOSX/build/Release/Wilsonic.vst3
Builds/MacOSX-WilsonicController/build/Release/WilsonicController.app
Builds/MacOSX-WilsonicController/build/Release/WilsonicController.component
Builds/MacOSX-WilsonicController/build/Release/WilsonicController.vst3
```

Then, from the repo root:

```bash
release/mac/build-pkg.sh
```

That reads the version from `VERSION.txt`, verifies `release/mts-esp` against
`PIN`, refuses any of the six products that is not a universal arm64 and
x86_64 binary, builds seven component packages and writes
`release/out/Wilsonic_Mac_v<version>-unsigned.pkg`. The `out` folder is
gitignored. `--help` lists the flags for pointing the script at other build
folders or an output folder, and `--version` overrides `VERSION.txt`, which
the test uses.

The installer puts things where the v0.43 installer did, under the same
package identifiers, so it upgrades a v0.43 install in place:

| Component identifier | Installs |
|----------------------|----------|
| `com.marcussatellite.Wilsonic-MTS-ESP.standalone` | `/Applications/Wilsonic.app` |
| `com.marcussatellite.Wilsonic-MTS-ESP.component` | `/Library/Audio/Plug-Ins/Components/Wilsonic.component` |
| `com.marcussatellite.Wilsonic-MTS-ESP.vst3` | `/Library/Audio/Plug-Ins/VST3/Wilsonic.vst3` |
| `com.marcussatellite.WilsonicController-MTS-ESP.standalone` | `/Applications/WilsonicController.app` |
| `com.marcussatellite.WilsonicController-MTS-ESP.component` | `/Library/Audio/Plug-Ins/Components/WilsonicController.component` |
| `com.marcussatellite.WilsonicController-MTS-ESP.vst3` | `/Library/Audio/Plug-Ins/VST3/WilsonicController.vst3` |
| `com.marcussatellite.Wilsonic-MTS-ESP.MTS-ESP-support` | `/Library/Application Support/MTS-ESP/libMTS.dylib` and `MTS-ESP.conf` |

The component packages carry the numeric part of the version, `0.45.0` for
`0.45.0-beta`, because `pkgbuild` wants dotted integers. The product title
and the file name carry the full string. The minimum macOS in
`distribution.xml` is `10.13`, which is `macOSDeploymentTarget` in
`Wilsonic.jucer`; the script fails if the two ever disagree.

### Signing

`SIGNING=0` is the default and does nothing. With `SIGNING=1`, the script
signs each of the six bundles with the hardened runtime and a secure
timestamp using the identity in `DEVELOPER_ID_APP`, then signs the package
with the identity in `DEVELOPER_ID_INSTALLER` and drops the `-unsigned`
suffix:

```bash
SIGNING=1 \
DEVELOPER_ID_APP="Developer ID Application: Perfect Buzz Music (LXFXL9GS49)" \
DEVELOPER_ID_INSTALLER="Developer ID Installer: Perfect Buzz Music (LXFXL9GS49)" \
release/mac/build-pkg.sh
```

That works on a Mac whose keychain holds both identities, which today is
only my M1. When `SIGNING_KEYCHAIN` is set, both tools look in that keychain
and nowhere else, and that is how CI runs it.

Two details are worth knowing. The bundles come out of Xcode signed ad hoc,
and signing a bundle again replaces its entitlements along with its
signature, so the script reads the entitlements each bundle was built with
and passes them back to `codesign`. Today that is
`com.apple.security.cs.allow-dyld-environment-variables` on the two
standalone apps, from `hardenedRuntimeOptions` in the `.jucer` files, and
nothing on the plugins. It drops `get-task-allow` if it finds it, because
Apple will not notarize a binary that has it. And `libMTS.dylib` is not
signed again. ODDSound ships it signed with their own Developer ID and a
timestamp, which is what Apple asks of every binary in a notarized package,
so the installer carries their file byte for byte and the script only checks
that the signature is there.

### Notarizing and verifying

```bash
NOTARY_KEY_FILE=/path/to/AuthKey.p8 APPLE_API_KEY_ID=... APPLE_API_ISSUER_ID=... \
release/mac/notarize.sh release/out/Wilsonic_Mac_v<version>.pkg

DEVELOPER_ID_APP="Developer ID Application: Perfect Buzz Music (LXFXL9GS49)" \
DEVELOPER_ID_INSTALLER="Developer ID Installer: Perfect Buzz Music (LXFXL9GS49)" \
release/mac/verify-pkg.sh release/out/Wilsonic_Mac_v<version>.pkg
```

`notarize.sh` submits the package with an App Store Connect API key and
waits for Apple. It prints Apple's log for the submission whether the answer
is yes or no, fails on anything but Accepted, and then staples the ticket to
the package so that it installs on a Mac with no network. `verify-pkg.sh`
runs `pkgutil --check-signature`, `spctl -a -vv -t install` and
`xcrun stapler validate` on the package, then expands it and runs
`codesign --verify --deep --strict` on each bundle inside. It runs every
check, prints what each tool said, and exits non-zero if any of them missed.
I never run these two by hand for a release, because the workflow does, but
`verify-pkg.sh` is also a quick way to look at a package I downloaded.

### The Apple secrets

A signed run needs six repository secrets, and
[the plan](../plans/release-pipeline.md) lists them under "Secrets".
`signing-keychain.sh setup` reads them from the environment at the start of
the `mac` job. If one is missing the job stops there and names it, and it
never goes on to build an unsigned package. If they are all present the
script tries each one out: it imports the two `.p12` files into a temporary
keychain, checks that both identities are valid, signs a scratch file with
each, and asks App Store Connect for the notarization history. A wrong
password or an expired certificate therefore fails in the first minute and
says which secret to look at, and the three and a half hours of building
only start once all six are known to work. It also prints the day each
certificate expires and puts a warning on the run when one has fewer than
45 days left. The certificates last about a year, and the plan's "Recurring
maintenance" section has the renewal steps.

None of these scripts prints a secret, and the ones that handle them switch
shell tracing off. The keychain and the decoded key are deleted by a step
that runs whether the job passed or failed.

### Testing the scripts

```bash
release/mac/test-build-pkg.sh
release/mac/test-signing.sh
```

Each takes a few seconds and runs on any Mac. The CI `mac` job runs both
before the real build, so a broken script fails fast instead of after a long
JUCE build. `test-signing.sh` puts fake `security`, `productsign`, `spctl`
and `xcrun` commands first on `PATH`, so it never touches a real keychain or
talks to Apple, and it wraps `codesign` so that the signing calls really
happen, ad hoc. It also plants recognisable fake secrets and searches every
log for them. `KEEP_SANDBOX=1` leaves its logs behind for a look.

## The Windows installer

The Windows installer is an Inno Setup script, `windows/wilsonic.iss`, that I
ported from the v0.43 script in the old installer repo. That one pinned
version 0.43 and read everything from OneDrive paths on my Windows laptop.
The new one takes its version from `/DVersion=` and reads everything from
paths relative to the repo root, so it compiles on any machine that has the
two Release builds:

```
ISCC.exe /DVersion=0.45.0-beta release\windows\wilsonic.iss
```

It writes `release\out\Wilsonic_Win64_v<version>-unsigned.exe`. In practice
I run `release/windows/build-installer.sh` from Git Bash instead, because it
checks things first: that `release/mts-esp` matches `PIN`, and that the four
products and `LIBMTS.dll` are x64 PE files. That second check is the Windows
cousin of the universal-binary check in `build-pkg.sh`.

The installer contains what v0.43 contained and puts it where v0.43 put it:

| File | Installed to |
|------|--------------|
| `Wilsonic.exe` | `C:\Program Files\Perfect Buzz Music\Wilsonic\Wilsonic\` |
| `WilsonicController.exe` | `C:\Program Files\Perfect Buzz Music\Wilsonic\WilsonicController\` |
| `Wilsonic.vst3` | `C:\Program Files\Common Files\VST3\Perfect Buzz Music\Wilsonic\` |
| `WilsonicController.vst3` | `C:\Program Files\Common Files\VST3\Perfect Buzz Music\WilsonicController\` |
| `LIBMTS.dll` (64-bit) | `C:\Program Files\Common Files\MTS-ESP\` |
| `MTS-ESP.conf` | `C:\Program Files\Common Files\MTS-ESP\`, only if there is none |

It also keeps the v0.43 AppId, `{78427BB9-1C86-41AB-BC1F-53E7203BDCDD}`. Inno
Setup uses the AppId to recognise an earlier install, so the new installer
upgrades v0.43 in place and Windows shows one Wilsonic entry under Apps. The
32-bit `LIBMTS.dll` is vendored but not installed, because I do not ship a
32-bit Wilsonic.

Three things differ from v0.43, and each is in the decision log in the plan.
The VST3s are still installed as single `.vst3` files, although the Projucer
now builds each one as a bundle folder; I take the module out of the bundle
so the upgrade replaces the old file where it is. Uninstalling Wilsonic now
leaves `LIBMTS.dll` and `MTS-ESP.conf` behind, because every other MTS-ESP
plugin on the machine uses them, and v0.43 removed them; that takes both
the `uninsneveruninstall` flag and `UninstallLogMode=overwrite`, because an
upgrade would otherwise keep the v0.43 uninstall log, which lists them. And the installer
accepts Windows 11 on ARM, which runs x64 hosts under emulation.

### Building on Windows by hand

With Visual Studio 2022, the Projucer and Inno Setup 6 installed, from Git
Bash at the repo root, after resaving both `.jucer` files:

```bash
release/windows/build-project.sh Builds/VisualStudio2022/Wilsonic.sln
release/windows/build-project.sh Builds/VisualStudio2022-WilsonicController/WilsonicController.sln
release/windows/build-installer.sh
```

`build-project.sh` needs `msbuild.exe` on `PATH`, which a Developer Command
Prompt provides, or its path in `MSBUILD`. `LTO=YES` keeps the Projucer's
whole program optimisation and `DEBUG_SYMBOLS=NO` drops the `.pdb` files.
After the build it reads the `msbuild` log and fails if a switch it was asked
for did not reach the compiler, because a switch that silently does nothing
is what cost the macOS job its first two runs.

### Signing

There is no Windows code signing yet. `SIGNING=1` with a sign command in
`SIGNTOOL_COMMAND` makes `build-installer.sh` hand that command to Inno
Setup, which then signs the four products, the uninstaller and the installer
and drops the `-unsigned` suffix. I have tested that the script passes the
right arguments, and nobody has run it with a real certificate. An unsigned
installer brings up the SmartScreen warning; More info, then Run anyway.

### Testing the scripts

```bash
release/windows/test-windows-scripts.sh
```

This runs on a Mac in a second or two. On a machine that has `ISCC.exe` it
also compiles `wilsonic.iss` for real from fake products, which is how the
script itself gets tested on the Windows runner before the long build.

## What the workflow does so far

`.github/workflows/release.yml` runs on a `v*` tag push, by hand from the
Actions tab with two inputs, `version` and `publish`, and on pull requests
that touch `release/` or the workflow file. The pull request run is a dry
run: unsigned, no tag check, no secrets, nothing published, and built
without debug symbols so it uploads no dSYMs or PDBs. A tag push and a
manual run sign and notarize the macOS package. Three jobs exist today:

1. `prepare` on Ubuntu runs `scripts/check-version.sh`. On a tag push it also
   requires the tag to equal `v$(cat VERSION.txt)`, and on a manual run with
   `version` filled in it requires that to equal `VERSION.txt` as well, so
   the input is a guard against building the wrong thing rather than a way to
   rename the build. It outputs the version, whether it is a pre-release, and
   the asset name.
2. `mac` on `macos-15` runs the packaging and signing tests, and on a tag
   or manual run sets up the signing keychain and checks the Apple secrets.
   Then it clones JUCE 9.0.1, restores the Projucer build from a cache keyed
   on the JUCE tag or builds it on a miss, resaves both `.jucer` files, and
   builds both projects in Release with `CODE_SIGN_IDENTITY="-"` and
   `LLVM_LTO=NO`. On a tag or manual run `build-pkg.sh` runs with
   `SIGNING=1`, `notarize.sh` and `verify-pkg.sh` follow, the keychain is
   deleted, and the job uploads `Wilsonic_Mac_v<version>.pkg` and the dSYM
   bundles as workflow artifacts. On a pull request `build-pkg.sh` runs with
   `SIGNING=0`, the builds pass `GCC_GENERATE_DEBUGGING_SYMBOLS=NO`, the
   signing and dSYM steps are skipped, and the one artifact is
   `Wilsonic_Mac_v<version>-unsigned.pkg`.
3. `windows` on `windows-2022` first runs `check-exporter.sh` and the script
   test, then clones JUCE 9.0.1 to `C:\JUCE`, restores `Projucer.exe` from a
   cache keyed on the JUCE tag or builds it on a miss, resaves both `.jucer`
   files, builds both solutions with `build-project.sh` and `LTO=NO`, runs
   `build-installer.sh` with `SIGNING=0`, installs the result silently with
   `smoke-install.ps1`, once fresh and once as an upgrade over the published
   v0.43 installer, and uploads `Wilsonic_Win64_v<version>-unsigned.exe`.
   Tag and manual runs also upload the `.pdb` files. The `msbuild` logs are
   uploaded on every run, pass or fail.

The `LLVM_LTO=NO` needs a word. The Projucer switches full link-time
optimisation on for every Release configuration, and neither `.jucer` file
turns it off, so a Release build links each of the three plugin formats
twice over, once per architecture, through a monolithic LTO link that is
slow and hungry for memory. On GitHub's three-core macOS runners the first
two workflow runs spent more than six hours inside the Wilsonic build step
and were cancelled by the job limit, so the workflow passes `LLVM_LTO=NO`
on the `xcodebuild` command line, where it wins over the project setting.
A Release build made in Xcode on my own machine still uses LTO, so the CI
binary is an ordinary `-O3` build rather than an LTO one. Without LTO an
arm64-only Wilsonic build took 27 minutes on the runner and the
WilsonicController build 26. I expected the universal build to take about
twice that, because it compiles everything twice, and it took four times:
106 minutes for Wilsonic and 116 for WilsonicController, so the whole job
runs about three and three quarter hours. Compiling both architectures took
44 of the Wilsonic minutes; the rest was `dsymutil` writing the universal
dSYM for the VST3, a single step that ran for an hour on the three-core
runner. The job has a timeout of five and a half hours so a stuck build
still fails before GitHub's limit, and I would like to try
`LLVM_LTO=YES_THIN` next and see what it costs.

That hour is why a pull request dry run builds without debug symbols. A dry
run only has to prove that the pipeline still packages, so it skips
`dsymutil` and the dSYM upload. I expected that to halve the job, and it
did better: without `-g` the compiles themselves dropped to 30 and 29
minutes, and the first dry run took 1 h 02 min in all. Tag and
manual runs keep the debug symbols and upload the dSYMs. The one cost is
that the two dSYM steps are exercised only by those runs, so a change to
them needs `gh workflow run release.yml --ref <branch>` rather than a pull
request to test it. The reasoning behind these choices, with the run
numbers, is in the decision log in
[plans/release-pipeline.md](../plans/release-pipeline.md).

The dSYMs are also why the job moves them into `release/dsyms` instead of
copying them, and deletes Xcode's `DerivedData` before uploading. The
universal dSYMs run to a few gigabytes, and the first universal run filled
the runner disk while `ditto` was copying them.

One more runner detail. The Release configurations in both `.jucer` files
set a VST3 and an AU binary location, so the exported projects finish with
an install phase that copies each plugin into `/Library/Audio/Plug-Ins`.
The runner user cannot write there, so the job creates those folders and
hands them to that user with `sudo` before building.

The `-destination 'generic/platform=macOS'` on each `xcodebuild` line is
there because a scheme build without it lets Xcode pick "My Mac" as the
destination, and that sets `ONLY_ACTIVE_ARCH=YES`, so the first run that got
through the build produced arm64-only plugins inside an installer that
claims to support Intel Macs. The generic destination honours the project's
two architectures, and `build-pkg.sh` now refuses any product that is not
universal so this cannot slip through again.

The Windows job is much quicker than the Mac one, about half an hour. The
first run built Wilsonic without whole program optimisation in 10 minutes 37
seconds and WilsonicController with it, because I wanted to see the
difference before choosing. What I saw was that the build with it does not
link: the object files for the shared-code library came to more than 4 GB
and the librarian stopped with `LNK1248`. So on Windows `LTO=NO` is what
lets the build link at all, and I suspect a Release build from Visual Studio
on my laptop fails the same way today, which I have not checked. What surprised me in
the other direction is that debug symbols cost almost nothing here. The two
builds took between eleven and fourteen and a half minutes each with them
and between ten and a half and thirteen and a half without, so the runner I
happen to get matters more than the symbols do. The Projucer takes two and a half to three minutes to
build on a cache miss and a second or two to restore on a hit. The job has a 90
minute timeout.

The silent install at the end of the Windows job is worth knowing the limits
of. It proves that the installer runs, that the six files land where the
table above says, that an existing `MTS-ESP.conf` survives and a missing one
is written, and that an uninstall leaves the shared MTS-ESP files. The
second pass downloads the v0.43 installer from this repo's v0.43-beta
release, installs it, installs the new one over it, and checks that Windows
then lists Wilsonic once, that the older `LIBMTS.dll` was replaced by the
pinned one, and that an uninstall still leaves the MTS-ESP files. All of
that runs on Windows Server with no audio host, so it does not tell me that
the VST3 loads in Live or that a tuning reaches a client. I still have to do
that by hand on a Windows machine.

The `publish` input is accepted and ignored. It belongs to the `release` job
in Phase 5. The only steps that read a secret are the signing setup and the
notarization in the `mac` job, and both are skipped on a pull request.

To try it by hand:

```bash
gh workflow run release.yml --ref <branch>
```

Then download the artifact from the run page, or with
`gh run download <run-id>`. A manual run signs and notarizes, so its
`Wilsonic_Mac_v<version>.pkg` opens in Installer without a Gatekeeper
warning. The `-unsigned` package from a pull request dry run does show the
warning; right-click, Open, or allow it in System Settings, Privacy &
Security.

## Updating libMTS

Until the bump workflow of Phase 8 exists, I update by hand: download the
files from the ODDSound commit I want with `curl` from
`raw.githubusercontent.com`, check `lipo -archs Mac/libMTS.dylib` prints
`x86_64 arm64`, replace the files in `mts-esp/`, and rewrite `PIN` with the
new commit, the version from their `CHANGELOG.md`, and
`shasum -a 256 Mac/libMTS.dylib Win/64bit/LIBMTS.dll Win/32bit/LIBMTS.dll MTS-ESP.conf`
run from inside `mts-esp/`. `test-build-pkg.sh` checks the packaged dylib
against `PIN`, so a stale `PIN` fails the test.
