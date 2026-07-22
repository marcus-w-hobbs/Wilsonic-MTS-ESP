// Characterization tests running the plugin's REAL tuning code:
// Microtone/Fraction octave reduction, the MicrotoneArray pipeline,
// TuningImp::_update end-to-end (including _analyzeProportionalTriads),
// and the Brun zigzag / MOS construction.
//
// Golden values are cross-checked against the Python research harness
// (experiments/triads/): the float32 mirror predicted the analyzer counts
// asserted here before this binary ever ran (crossval001, 2026-07-20).

#include <cmath>
#include <cstdio>
#include <memory>
#include <vector>

#include "../Source/Brun.h"
#include "../Source/Microtone.h"
#include "../Source/MicrotoneArray.h"
#include "../Source/TuningImp.h"

namespace
{
int checks = 0;
int failures = 0;

#define CHECK(cond)                                                        \
    do {                                                                   \
        ++checks;                                                          \
        if (!(cond)) {                                                     \
            ++failures;                                                    \
            std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);    \
        }                                                                  \
    } while (0)

#define CHECK_EQ_UL(a, b)                                                  \
    do {                                                                   \
        ++checks;                                                          \
        auto va = static_cast<unsigned long>(a);                           \
        auto vb = static_cast<unsigned long>(b);                           \
        if (va != vb) {                                                    \
            ++failures;                                                    \
            std::printf("FAIL %s:%d: %s == %s (%lu != %lu)\n", __FILE__,   \
                        __LINE__, #a, #b, va, vb);                         \
        }                                                                  \
    } while (0)

void testMicrotoneOctaveReduce()
{
    // half-open [1, 2)
    {
        Microtone m(2.f, "", Microtone::Space::Linear, 2.f);
        m.octaveReduce();
        CHECK(m.getFrequencyValue() == 1.f);
    }
    {
        Microtone m(3.f, "", Microtone::Space::Linear, 2.f);
        m.octaveReduce();
        CHECK(m.getFrequencyValue() == 1.5f);
    }
    // rational path: exact arithmetic, float loop conditions
    {
        Microtone m(35UL, 16UL, "", Microtone::Space::Linear, 2.f, false);
        m.octaveReduce();
        CHECK_EQ_UL(m.getNumerator(), 35UL);
        CHECK_EQ_UL(m.getDenominator(), 32UL);
    }
    // boundary anomaly (characterization, not endorsement): the rational
    // (2^25-1)/2^24 has floatValue exactly 2.0f, so the reduce loop
    // divides once too many and the exact rational leaves [1, 2).
    {
        Microtone m(33554431UL, 16777216UL, "", Microtone::Space::Linear, 2.f, false);
        m.octaveReduce();
        CHECK_EQ_UL(m.getNumerator(), 33554431UL);
        CHECK_EQ_UL(m.getDenominator(), 33554432UL); // < 1 !
    }
}

void testMicrotoneArrayPipeline()
{
    // octaveReduce -> sort -> uniquify collapses {3, 3/2, 6, 1, 2} to {1, 3/2}
    auto ma = MicrotoneArray();
    ma.addMicrotone(std::make_shared<Microtone>(3.f, "", Microtone::Space::Linear, 2.f));
    ma.addMicrotone(std::make_shared<Microtone>(1.5f, "", Microtone::Space::Linear, 2.f));
    ma.addMicrotone(std::make_shared<Microtone>(6.f, "", Microtone::Space::Linear, 2.f));
    ma.addMicrotone(std::make_shared<Microtone>(1.f, "", Microtone::Space::Linear, 2.f));
    ma.addMicrotone(std::make_shared<Microtone>(2.f, "", Microtone::Space::Linear, 2.f));
    auto reduced = ma.octaveReduce(2.f);
    CHECK_EQ_UL(reduced.count(), 5UL); // reduction keeps duplicates
    auto sorted = reduced.sort();
    auto unique = sorted.uniquify();
    CHECK_EQ_UL(unique.count(), 2UL);
    CHECK(unique.microtoneAtIndex(0)->getFrequencyValue() == 1.f);
    CHECK(unique.microtoneAtIndex(1)->getFrequencyValue() == 1.5f);
}

// The numeric core of CPSTuningBase::multiplyByCommonTones for two seeds.
std::shared_ptr<Microtone> cpsTone(float a, float b)
{
    auto f = 1.f;
    f *= a;
    f *= b;
    return std::make_shared<Microtone>(f, "", Microtone::Space::Linear, 2.f);
}

void testAnalyzerHexany1357()
{
    // Feed TuningImp the plugin-canonical hexany 1-3-5-7 (float pairwise
    // products). setMicrotoneArray triggers _update: octave reduction,
    // sort (no uniquify by default, matching CPS), tuning table fill, and
    // _analyzeProportionalTriads.
    //
    // CHARACTERIZATION golden (1, 2): the analyzer's search loop finds
    // (2, 2) — its octave-wrap machinery (jfac/kfac) exists to catch
    // cross-octave triads — but the post-loop NPO-map filter looks up
    // UNWRAPPED indices in a map keyed 0..npo-1, so every wrapped triad
    // is dropped from the reported lists. First run of this test exposed
    // that behavior (the float32 mirror initially predicted the
    // loop-level counts); the mirror now models both stages
    // (experiments/triads/cpp_mirror.py, npo_map_filter).
    auto ma = MicrotoneArray();
    ma.addMicrotone(cpsTone(1.f, 3.f));
    ma.addMicrotone(cpsTone(1.f, 5.f));
    ma.addMicrotone(cpsTone(1.f, 7.f));
    ma.addMicrotone(cpsTone(3.f, 5.f));
    ma.addMicrotone(cpsTone(3.f, 7.f));
    ma.addMicrotone(cpsTone(5.f, 7.f));

    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getProcessedArrayCount(), 6UL);
    // processed array is the octave-reduced, sorted hexany
    CHECK(t.getProcessedArray().microtoneAtIndex(0)->getFrequencyValue() == 35.f / 32.f);
    CHECK(t.getProcessedArray().microtoneAtIndex(5)->getFrequencyValue() == 15.f / 8.f);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 1UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 2UL);
}

void testAnalyzerHexany1359()
{
    // Golden (1, 2) PREDICTED by the corrected float32 mirror on
    // 2026-07-20, before this test ever ran — prediction-then-execution
    // is the receipt that the mirror models both analyzer stages.
    auto ma = MicrotoneArray();
    ma.addMicrotone(cpsTone(1.f, 3.f));
    ma.addMicrotone(cpsTone(1.f, 5.f));
    ma.addMicrotone(cpsTone(1.f, 9.f));
    ma.addMicrotone(cpsTone(3.f, 5.f));
    ma.addMicrotone(cpsTone(3.f, 9.f));
    ma.addMicrotone(cpsTone(5.f, 9.f));

    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getProcessedArrayCount(), 6UL);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 1UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 2UL);
}

void testAnalyzerHarmonicSegment()
{
    // Harmonic segment 8..15 over 8 (16 dedups to 1/1 and is omitted so
    // this matches the mirror's canonical 8-tone run). Loop finds (8, 1);
    // reported after the wrap-drop: (4, 1).
    auto ma = MicrotoneArray();
    for (int h = 8; h < 16; ++h) {
        ma.addMicrotone(std::make_shared<Microtone>(
            static_cast<float>(h) / 8.f, "", Microtone::Space::Linear, 2.f));
    }
    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getProcessedArrayCount(), 8UL);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 4UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 1UL);
}

void testBrunZigzag()
{
    // Level -> cardinality for the fifth-like generator: the scale-tree
    // zigzag denominators 1, 2, 3, 5, 7, 12, 17, 29, 41, 53.
    const float g = 0.5849625f; // log2(3/2)
    const unsigned long expectedDen[] = {1, 2, 3, 5, 7, 12, 17, 29, 41, 53};
    const unsigned long expectedNum[] = {1, 1, 2, 3, 4, 7, 10, 17, 24, 31};
    for (unsigned long level = 0; level <= 9; ++level) {
        auto conv = Brun::brun(level, g);
        CHECK_EQ_UL(conv->getNumerator(), expectedNum[level]);
        CHECK_EQ_UL(conv->getDenominator(), expectedDen[level]);
    }
    // brunArray(level, g) holds the whole zigzag path up to the level
    auto arr = Brun::brunArray(9UL, g);
    CHECK_EQ_UL(arr.count(), 10UL);
    CHECK_EQ_UL(arr.microtoneAtIndex(5)->getDenominator(), 12UL);
}

void testBrunMosConstruction()
{
    // Full Brun instance: level 5 at the fifth generator must produce the
    // 12-tone MOS; degrees are generator multiples mod 1 in log2 space.
    Brun b;
    b.setGenerator(0.5849625f);
    b.setLevel(5UL);
    CHECK_EQ_UL(b.getProcessedArrayCount(), 12UL);
    // Level 1 -> 2 tones; level 3 -> 5 tones
    b.setLevel(1UL);
    CHECK_EQ_UL(b.getProcessedArrayCount(), 2UL);
    b.setLevel(3UL);
    CHECK_EQ_UL(b.getProcessedArrayCount(), 5UL);
}

} // namespace

int main()
{
    testMicrotoneOctaveReduce();
    testMicrotoneArrayPipeline();
    testAnalyzerHexany1357();
    testAnalyzerHexany1359();
    testAnalyzerHarmonicSegment();
    testBrunZigzag();
    testBrunMosConstruction();

    std::printf("test_tuning: %d checks, %d failures\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
