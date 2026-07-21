# Verification ledger — what is grounded, and how hard

Every claim the harness relies on, graded by receipt strength. Nothing on
this list is allowed to silently upgrade itself; a claim moves up only
when the artifact in its row exists.

Grades, weakest to strongest:
- **READ** — line-cited code reading. No execution. Can be wrong.
- **SIMULATED** — algorithm re-derived from source text and run in Python;
  never compared against executing C++.
- **EXECUTED** — the real compiled C++ ran and its output is recorded.
- **BIT-EXACT** — real C++ output matches the Python mirror at the
  IEEE-754 bit level (crossval001.py exits nonzero on any mismatch).

## Grounded claims

| Claim | Grade | Receipt |
|---|---|---|
| Float octave reduction is half-open [1,2); 2.0f→1.0f; boundary neighbors behave as documented | **BIT-EXACT** | cpp_receipts float_reduce cases ↔ cpp_mirror; results/crossval001.json link1 (27/27, 2026-07-20) |
| Rational octave reduction uses exact Fraction math with FLOAT loop conditions | **BIT-EXACT** | cpp_receipts rational_reduce cases ↔ mirror |
| Boundary anomaly: rational (2²⁵−1)/2²⁴ reduces to 33554431/33554432 **< 1**, outside [1,2), because floatValue() rounds to 2.0f | **BIT-EXACT** | cpp_receipts r_boundary_2e25; pinned in tests/test_cpp_mirror.py |
| CPS tones are plain float products then float octave reduction; integer seeds ≤ these magnitudes give floats equal to the exact rationals | **BIT-EXACT** | cpp_receipts cps_product_reduce cases (incl. non-integer seeds 1.3×2.6) |
| CPS multiplies tones in shortDescriptionText string-sort order (irrelevant for k=2, order-sensitive for k≥3) | READ | CPSTuningBase.h:100–104, CPSTuningBase.cpp:104 |
| CPS never uniquifies (duplicates kept); pipeline is octaveReduce → sort → uniquify | READ | CPSTuningBase.cpp:18; TuningImp.cpp:507–518 |
| uniquify() dedups on exact float via map; last-in-array wins ties | READ | MicrotoneArray.cpp:434–455 |
| Brun level→cardinality = scale-tree zigzag denominators (fifth: 1,2,3,5,7,12,17,29,41,53, levels 0–9) | **EXECUTED** | tests/test_tuning testBrunZigzag runs the real Brun::brun/brunArray; crossval002 float32-faithful re-derivation agrees |
| MOS degrees built in log space, p = degree·g mod 1, murchana 0 default | **EXECUTED (1 ulp)** | real Brun instances via tests/research_cli vs float32 simulation: 15 scales, every degree within 1 ulp (libm pow is the only slack); results/crossval002.json |
| Plugin triad analyzer semantics: search loop (absolute 0.0005 linear tolerance, 9/8–4/3 filter, one-octave+wrap domain, wrapped-index dedup) PLUS post-loop NPO-map filter that DROPS every octave-wrapping triad from the reported lists | **EXECUTED** | real analyzer runs in tests/test_tuning (46 checks); mirror models both stages and was corrected by first execution — see FINDINGS.md 2026-07-21. Corrected mirror predicted hexany 1-3-5-9 = (1,2) before the C++ ran; confirmed |
| Mirror ↔ real analyzer agreement at corpus scale | **EXECUTED** | crossval002: 70 hexanies bit-exact scales + equal counts, 15 MOS scales ≤1 ulp + equal counts, 0 mismatches |
| MicrotoneArray octaveReduce → sort → uniquify pipeline (incl. dup-keeping before uniquify) | **EXECUTED** | tests/test_tuning testMicrotoneArrayPipeline runs the real MicrotoneArray.cpp |
| Plugin analyzer massively undercounts vs exact scorer: hexany 1-3-5-7 reports (1,2) vs exact (8,8) anchored; attribution: wrap-drop (1,2)→loop (2,2)→no interval filter (4,2)→domain/dedup → exact | EXECUTED | results/crossval001.json link2 (plugin/loop/no-filter columns), all 70 hexanies + segment |
| Analyzer tolerance is register-dependent in cents: 0.865¢ at f=1 vs 0.433¢ at f≈2 | EXECUTED (arithmetic) | crossval001 tolerance_register_table |
| Scorer conventions (duality, transposition variance/invariance) | EXECUTED | tests/test_scorer.py goldens; TRIAD-004a/b/c |

## Known gaps (do not treat these as grounded)

1. **libm-dependent paths (pow, log2f, exp2f) cannot be mirrored
   bit-exactly** — cents↔frequency conversions compare within 1 ulp /
   epsilon, never bit equality (observed max deviation in crossval002:
   1 ulp).
2. **Repo CLAUDE.md misstates the analyzer tolerance space** ("0.0005 in
   unit pitch space" — it is absolute linear frequency, TuningImp.cpp:793
   post-split). Correction proposed to Marcus; not yet applied since it
   is a tracked repo doc.
3. **Stub caveat:** the test binaries compile real Source files against
   stub headers (tests/JuceHeader.h, tests/WilsonicAppSkin.h — inert
   scaffolding: assertions, locks, string formatting, UI geometry).
   AffineTransform is identity under stub, so Gral DISPLAY coordinates
   computed in tests are meaningless and never asserted. Makefile `cmp`
   proves copied sources are byte-identical; paint bodies are tests-only
   no-ops (tests/paint_stubs.cpp) since the real ones live in
   TuningImp+paint.cpp / Brun+Paint.cpp and need JUCE Graphics.
4. **CPS classes (CPSTuningBase, CPS_4_2, …) still not compiled under
   test** — the CPS product chain is replicated (two-seed float product,
   validated bit-exact vs Microtone path) but CPSTuningBase.cpp itself
   has UI/subset dependencies. Next candidate for the same treatment.
5. **uniquify float-key tie-breaking (last-in-array wins)** exercised
   only implicitly; no dedicated golden yet.
