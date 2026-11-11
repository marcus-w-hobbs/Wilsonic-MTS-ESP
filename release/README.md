# Release tooling

This folder holds what turns a built Wilsonic into an installer. The design
and the phases it is built in are in [plans/release-pipeline.md](../plans/release-pipeline.md).
As of Phase 2 the macOS packaging works unsigned, locally and in CI. Signing,
notarization, the Windows installer and the GitHub release itself are later
phases.

## What is here

| Path | Purpose |
|------|---------|
| `mac/build-pkg.sh` | Builds the macOS installer from already-built products with `pkgbuild` and `productbuild`. |
| `mac/distribution.xml` | The product definition: title, `hostArchitectures="x86_64,arm64"`, minimum macOS, one choice per component. |
| `mac/test-build-pkg.sh` | Test for the two files above. It fakes the six product bundles, so it needs neither Xcode nor a certificate. |
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
`PIN`, builds seven component packages and writes
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
codesigns each product with the hardened runtime and a secure timestamp
using the identity in `DEVELOPER_ID_APP`, then signs the product with the
identity in `DEVELOPER_ID_INSTALLER` and drops the `-unsigned` suffix:

```bash
SIGNING=1 \
DEVELOPER_ID_APP="Developer ID Application: Perfect Buzz Music (LXFXL9GS49)" \
DEVELOPER_ID_INSTALLER="Developer ID Installer: Perfect Buzz Music (LXFXL9GS49)" \
release/mac/build-pkg.sh
```

Notarization and stapling are not in the script yet. That is Phase 3, and
it needs the Apple secrets that do not exist yet.

### Testing the script

```bash
release/mac/test-build-pkg.sh
```

This takes a few seconds and runs on any Mac. The CI `mac` job runs it too,
before the real build, so a broken script fails fast instead of after a
twenty-minute JUCE build.

## What the workflow does so far

`.github/workflows/release.yml` runs on a `v*` tag push, by hand from the
Actions tab with two inputs, `version` and `publish`, and on pull requests
that touch `release/` or the workflow file. The pull request run is a dry
run: unsigned, no tag check, no secrets, nothing published, and it stays
that way when Phase 3 adds signing for tags and manual runs. Two jobs exist
today:

1. `prepare` on Ubuntu runs `scripts/check-version.sh`. On a tag push it also
   requires the tag to equal `v$(cat VERSION.txt)`, and on a manual run with
   `version` filled in it requires that to equal `VERSION.txt` as well, so
   the input is a guard against building the wrong thing rather than a way to
   rename the build. It outputs the version, whether it is a pre-release, and
   the asset name.
2. `mac` on `macos-15` runs the packaging test, clones JUCE 9.0.1, restores
   the Projucer build from a cache keyed on the JUCE tag or builds it on a
   miss, resaves both `.jucer` files, builds both projects in Release with
   `CODE_SIGN_IDENTITY="-"`, runs `build-pkg.sh` with `SIGNING=0`, and
   uploads `Wilsonic_Mac_v<version>-unsigned.pkg` and the dSYM bundles as
   workflow artifacts.

The `publish` input is accepted and ignored. It belongs to the `release` job
in Phase 5. Nothing in the workflow reads a secret yet.

To try it by hand:

```bash
gh workflow run release.yml --ref <branch>
```

Then download the artifact from the run page, or with
`gh run download <run-id>`. An unsigned package shows a Gatekeeper warning
on install; right-click, Open, or allow it in System Settings, Privacy &
Security. That is expected until Phase 3.

## Updating libMTS

Until the bump workflow of Phase 8 exists, I update by hand: download the
files from the ODDSound commit I want with `curl` from
`raw.githubusercontent.com`, check `lipo -archs Mac/libMTS.dylib` prints
`x86_64 arm64`, replace the files in `mts-esp/`, and rewrite `PIN` with the
new commit, the version from their `CHANGELOG.md`, and
`shasum -a 256 Mac/libMTS.dylib Win/64bit/LIBMTS.dll Win/32bit/LIBMTS.dll MTS-ESP.conf`
run from inside `mts-esp/`. `test-build-pkg.sh` checks the packaged dylib
against `PIN`, so a stale `PIN` fails the test.
