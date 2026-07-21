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
| Brun level→cardinality = scale-tree zigzag denominators (fifth: 1,2,3,5,7,12,17,29,41,53, levels 0–9) | SIMULATED | zigzag re-derived from Brun.cpp:269–299, run in Python (plan §2.2); C++ never executed |
| MOS degrees built in log space, p = degree·g mod 1, murchana-centered | READ | Brun.cpp:308–357 |
| Plugin triad analyzer semantics (absolute 0.0005 linear tolerance, 9/8–4/3 filter, one-octave+wrap domain, pitch-class-set dedup) | READ → mirror | TuningImp.cpp:782–857; mirror in cpp_mirror.analyze_proportional_triads. **The mirror's float ops are bit-faithful by construction, but the analyzer itself has never been executed** (TuningImp.cpp is not compilable standalone). |
| Plugin analyzer massively undercounts vs exact scorer: hexany 1-3-5-7 (2,2) vs exact (8,8) anchored; attribution: interval filter (2,2)→(4,2), remainder = restricted domain + pitch-class dedup | EXECUTED (mirror) | results/crossval001.json link2, all 70 hexanies + segment |
| Analyzer tolerance is register-dependent in cents: 0.865¢ at f=1 vs 0.433¢ at f≈2 | EXECUTED (arithmetic) | crossval001 tolerance_register_table |
| Scorer conventions (duality, transposition variance/invariance) | EXECUTED | tests/test_scorer.py 29 goldens; TRIAD-004a/b/c |

## Known gaps (do not treat these as grounded)

1. **The real _analyzeProportionalTriads has never executed under test.**
   The mirror is a line-by-line transcription with bit-faithful float ops,
   but transcription error is possible. Closing this requires either a
   heavier stub harness (TuningImp pulls JUCE/MTS/processor) or adding a
   TuningTests+Analyzer.cpp to the plugin's test suite — the latter
   touches the Xcode project, so it is Marcus's call.
2. **Brun zigzag never executed in C++.** Brun.cpp is not compilable
   standalone (TuningImp dependency). The Python zigzag is SIMULATED
   grade. Same remedy options as (1).
3. **MicrotoneArray::uniquify/sort never executed** (MicrotoneArray.cpp
   includes Tuning.h). READ grade; low risk (std::map semantics) but not
   receipts.
4. **libm-dependent paths (powf, log2f, exp2f) cannot be mirrored
   bit-exactly** — cents↔frequency conversions in the MOS path will need
   epsilon comparisons, never bit equality.
5. **Repo CLAUDE.md misstates the analyzer tolerance space** ("0.0005 in
   unit pitch space" — it is absolute linear frequency, TuningImp.cpp:809).
   Correction proposed to Marcus; not yet applied since it is a tracked
   repo doc.
6. **Stub caveat:** cpp_receipts compiles the real Microtone.cpp/
   Fraction.cpp against stub JuceHeader/WilsonicAppSkin headers (inert
   scaffolding: assertions, one string formatter, UI geometry types).
   Numerics under test never touch the stubs; the Makefile `cmp` proves
   the compiled source is byte-identical to the repo's.
