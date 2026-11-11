# Release pipeline design

Status: draft for Marcus to approve. Written 2026-11-10 from a Q&A session.
Lane: chore. Touches `.github/`, `scripts/`, a new `release/` folder, `VERSION`.

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
| 9 | Version source | One `VERSION` file at the repo root. A script writes the other files. |
| 10 | Next version | `0.45.0-beta` |
| 11 | Test gate | CI creates a draft pre-release. Marcus tests on M1, then publishes by hand. |
| 12 | WilsonicController | Ships inside the same installer |
| 13 | Release notes | CI drafts from merged PR titles. Marcus edits before publish. |
| 14 | Docs per release | `docs/manual`, website pages, README Installation section |
| 15 | Website download links | The site reads GitHub Releases at build time |
| 16 | libMTS on macOS | Bundle the pinned version. Add a workflow that proposes updates. |
| 17 | ODDSound license | 0BSD. Redistribution is permitted. A LICENSE copy ships next to the binaries. |

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
VERSION                          # 0.45.0-beta
release/
  README.md                      # how to cut a release, one page
  mac/
    build-pkg.sh                 # pkgbuild x7, productbuild, optional sign + notarize
    distribution.xml             # title, hostArchitectures, choices, pkg-refs
    entitlements.plist           # hardened runtime entitlements for the standalone
  windows/
    wilsonic.iss                 # Inno Setup, paths relative to repo root, version from VERSION
  mts-esp/
    PIN                          # ODDSound commit sha, libMTS version, sha256 of each binary
    LICENSE                      # ODDSound 0BSD text
    MTS-ESP.conf
    Mac/libMTS.dylib             # universal x86_64 + arm64
    Win/64bit/LIBMTS.dll
    Win/32bit/LIBMTS.dll         # kept for parity with ODDSound; not installed
scripts/
  set-version.sh                 # VERSION -> version.h, both .jucer, nothing else
  check-version.sh               # fails if VERSION, version.h, .jucer, and git tag disagree
  check-release-docs.sh          # fails if README or docs/manual name a version other than VERSION
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

`VERSION` holds a semver string such as `0.45.0-beta`. The rules:

1. `scripts/set-version.sh` reads `VERSION` and writes:
   - `version.h`: `VERSION_MAJOR 0`, `VERSION_MINOR 45`, `VERSION_PATCH 0`,
     `VER_NUM 0.45.0`, `VERSION_STRING "0.45.0-beta"`, `BETA 1` when the
     string has a `-` suffix, else `0`.
   - both `.jucer` files: `version="0.45.0"`. Projucer wants numeric fields.
   - Then it runs `Projucer --resave` on both projects when Projucer is present.
2. `scripts/check-version.sh` runs in CI on every PR and on tag push. On tag
   push it also checks `v$(cat VERSION)` equals the tag.
3. Marcus bumps a version with one command, then commits and tags:

```bash
echo 0.45.0-beta > VERSION && scripts/set-version.sh
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

### prepare (ubuntu)

1. Check out. Run `scripts/check-version.sh` and `scripts/check-release-docs.sh`.
2. Output `version`, `is_prerelease`, `mac_asset`, `win_asset`.

### mac (macos-15)

1. Restore a cached Projucer 9.0.1 build. Build it on a cache miss. Cache key
   is the JUCE tag.
2. `Projucer --resave` both `.jucer` files.
3. If signing secrets exist, create a temporary keychain and import the
   Developer ID Application and Developer ID Installer `.p12` files. If they
   do not exist, build ad-hoc, skip notarization, and name the asset
   `...-unsigned.pkg`. This keeps manual test builds working before the
   Apple account is sorted.
4. `xcodebuild` Release for `Wilsonic - All` and `WilsonicController - All`
   with `CODE_SIGN_IDENTITY="Developer ID Application: Perfect Buzz Music (LXFXL9GS49)"`,
   hardened runtime on, timestamp on. Outputs land in
   `Builds/MacOSX/build/Release` and `Builds/MacOSX-WilsonicController/build/Release`.
5. `release/mac/build-pkg.sh`:
   - stage each product into its own root
     (`/Applications`, `/Library/Audio/Plug-Ins/Components`,
     `/Library/Audio/Plug-Ins/VST3`, `/Library/Application Support/MTS-ESP`)
   - `pkgbuild` one component package per product with the same identifiers
     v0.43 used, for example `com.marcussatellite.Wilsonic-MTS-ESP.vst3`,
     so upgrades over v0.43 replace cleanly
   - `productbuild --distribution release/mac/distribution.xml` into one
     `.pkg`, with `hostArchitectures="x86_64,arm64"` set in the XML rather
     than patched in afterwards
   - `productsign` with Developer ID Installer when signing is on
6. `xcrun notarytool submit --wait` with the App Store Connect API key, then
   `xcrun stapler staple`. On failure, print `notarytool log` and fail.
7. Upload the `.pkg` and the `.dSYM` folders as artifacts.

### windows (windows-2022)

1. Restore a cached Projucer build. On a miss, clone JUCE 9.0.1 and build
   Projucer with `msbuild`.
2. `Projucer --resave` both `.jucer` files.
3. `msbuild Builds/VisualStudio2022/Wilsonic.sln /p:Configuration=Release /p:Platform=x64`
   and the same for `WilsonicController.sln`.
4. Run Inno Setup, which GitHub's Windows runners already include:
   `ISCC.exe /DVersion=0.45.0-beta release/windows/wilsonic.iss`.
   The script uses paths relative to the repo root and takes its version from
   the `/D` define.
5. Signing step: present, disabled, documented. If Marcus later adds a
   certificate or Azure Trusted Signing, only secrets and one `if:` change.
6. Upload the `.exe` as an artifact.

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
does not run on `pull_request` at all.

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
   holds the key. If no Mac holds the key, revoke and create new ones.
2. On App Store Connect, Users and Access, Integrations, create a Team key
   with the Developer role. Download the `.p8` once.
3. Add the six Apple secrets to this repo. Delete the local `.p12` and `.p8`
   files afterwards.
4. Confirm `VERCEL_DEPLOY_HOOK_URL` exists.
5. Run the workflow by hand once with `publish: false` to confirm signing and
   notarization pass.

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

| Phase | Deliverable | Verify by |
|-------|-------------|-----------|
| 0 | Apple secrets in place | `security find-identity` inside a manual workflow run lists both Developer ID certs |
| 1 | `VERSION`, `set-version.sh`, `check-version.sh`, CI check on PRs | A PR that edits `version.h` by hand fails CI |
| 2 | `release/mac/*`, `mac` job, manual run unsigned | `.pkg` artifact installs on M2 with `SIGNING=0` semantics |
| 3 | `mac` job signed and notarized | `spctl --assess --type install` passes on the downloaded `.pkg` |
| 4 | `release/windows/*`, `windows` job | `.exe` artifact installs on claw or a Windows VM |
| 5 | `release` job, draft pre-release, generated notes | Tag `v0.45.0-beta` produces a draft with two assets and a notes body |
| 6 | Website reads releases, hook on publish | Publishing the draft changes the download buttons within a few minutes |
| 7 | Docs check and manual updates | `check-release-docs.sh` passes on main |
| 8 | `mts-esp-bump.yml` | Manual run against a fake older `PIN` opens a PR |
| 9 | Installer repo archived | Repo shows Archived on GitHub |

Phases 1, 2, and 4 can start before Phase 0 completes. Phase 3 and 5 need it.

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
5. Should `auval` run on the CI runner as a smoke test? It needs the
   component installed in `~/Library/Audio/Plug-Ins/Components`, which the
   runner allows. It catches a broken AU before Marcus downloads anything.
6. Which GitHub labels group the release notes? A first cut:
   `feature`, `fix`, `research`, `docs`, `chore`.

## Assumptions

- The plugin repo stays public.
- The Developer ID team remains LXFXL9GS49 and the installer identifiers stay
  under `com.marcussatellite.`.
- 32-bit Windows is not shipped. The 32-bit DLL is vendored only to mirror
  ODDSound's layout.
- No Linux installer in this round. The Linux CI build stays as a gate only.
