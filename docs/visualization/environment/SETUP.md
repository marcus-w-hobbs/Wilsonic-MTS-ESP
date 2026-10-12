# Math-To-Manim environment baseline

Verified October 11, 2026 on macOS arm64 with Python 3.12.13 and Node.js 24.1.0. This is an observed platform-specific dependency snapshot, not a cross-platform or hash-locked distribution.

## Recreate the local environment

In a dedicated installation directory outside this research checkout:

```sh
git clone https://github.com/HarleyCoops/Math-To-Manim.git
cd Math-To-Manim
git checkout --detach 089ffd51ece10898cc3cdb00a9bb1588268f19e0
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[dev,render]' \
  -c /path/to/Wilsonic-MTS-ESP/docs/visualization/environment/python-constraints-macos-arm64.txt
npm ci --no-audit --no-fund
source .venv/bin/activate
```

Replace the constraints path with the actual checkout path. The constraints file includes macOS-specific packages and should not be treated as portable to other operating systems. Existing system tools used here were Cairo/Pango, FFmpeg, LaTeX and dvisvgm. Their availability alone is not sufficient: run the sample render to verify the TeX templates and libraries.

Use the `dev,render` extras. The upstream optional `astra` extra still constrains Manim below 0.20; using it would request a downgrade. The general render extra supports this installation. The upstream generic author prompt mentions 0.20, while the project brief explicitly requires the installed 0.22.0 APIs. No upstream implementation or dependency declarations were changed.

The source revision pins Codex CLI/SDK 0.156.1 through its npm lockfile. TypeSafe SDK is 0.7.2. Python package versions are recorded in `python-constraints-macos-arm64.txt`.

## Authentication

The primary Astra chain uses Codex ChatGPT login, not an OpenAI API key. Run `math-to-manim login` if the machine is not already signed in.

For TypeSafe Jev, create `.env.local` in the Math-To-Manim checkout containing `TYPESAFE_API_KEY=` followed by the real key. Keep it Git-ignored and restrict permissions with `chmod 600 .env.local`. Do not commit it, paste it into chat, or include it in source dossiers. The application reads it directly; no shell export is required.

```sh
math-to-manim doctor
```

Doctor verifies saved login/configuration, not remote key validity or model entitlement. On the preparation machine both credentials were locally recognized. No live model or Jev calls were made. A restricted process emitted a non-failing optional PATH-alias warning; the installed runtime loaded successfully.

## Local verification

```sh
uv --no-cache pip check --python .venv/bin/python
python -m pytest
python -m manim -ql --disable_caching \
  --media_dir artifacts/setup/render-manim-0.22.0 \
  tests/fixtures/cinematic_geodesic.scene.py GeodesicFilm
ffmpeg -v error \
  -i artifacts/setup/render-manim-0.22.0/videos/cinematic_geodesic.scene/480p15/GeodesicFilm.mp4 \
  -f null -
```

Recorded result: 330 tests passed, one non-failing temporary-response cleanup warning, 73 compatible packages, and a successful 8.6-second render with LaTeX and camera motion. See `verification.json`, `pytest-manim-0.22.0.txt` and `render-metadata.json`. Test paths in the retained log were normalized for portability. The test video itself is not committed.

## Skills and prompts

The prompt-engineering skill informed the structured brief and source/instruction separation. The installed Manim skill informed planning guidance, but its separate hand-coded route requires `manimce-best-practices`, which was not installed. The chosen native Math-To-Manim route does not depend on that optional skill.

Native stages: brief → mathematics → storyboard → scene → render → evidence audit. Astra independently audits evidence; TypeSafe Jev receives text and attributed image observations, not pixels. Use advisory Jev by default, explicit low-quality drafts and a modest revision limit. Advisory findings do not automatically stop the pipeline, so inspect them before delivery. These settings do not enforce a hard spending cap; the upstream runtime requests the fast service tier.

Live content generation remains contingent on Marcus's later request. Source review and local smoke renders do not authorize a final film.
