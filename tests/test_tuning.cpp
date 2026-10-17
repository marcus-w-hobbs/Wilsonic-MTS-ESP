// Characterization tests running the plugin's REAL tuning code:
// Microtone/Fraction octave reduction, the MicrotoneArray pipeline,
// TuningImp::_update end-to-end (including _analyzeProportionalTriads),
// and the Brun zigzag / MOS construction.
//
// Golden values are cross-checked against the Python research harness
// (experiments/triads/): the float32 mirror predicted the analyzer counts
// asserted here before this binary ever ran (crossval001, 2026-07-20).

#include <array>
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
    // Harmonic segments are arithmetic, not geometric: 9-12-16 is the one
    // b^2 = ac chain in 8..16 and its 4/3 lower interval sits exactly on
    // the strict upper edge of the 9/8..4/3 window, so G is 0.
    CHECK_EQ_UL(t.getGeometricTriads().size(), 0UL);
    CHECK_EQ_UL(t.getAllTriads().size(), 5UL);
}

// Every triad of the given type in `triads`, as (root, third, fifth).
std::vector<std::array<unsigned long, 3>> degreesOf(std::vector<PythagoreanMeans> triads,
                                                    PythagoreanMeans::Type type)
{
    std::vector<std::array<unsigned long, 3>> out;
    for (auto& t : triads) {
        if (t.getType() == type) {
            out.push_back({t.getRoot(), t.getThird(), t.getFifth()});
        }
    }
    return out;
}

void testAnalyzerGeometricCPSWindowed()
{
    // Issue #13 asks for geometric triads (b^2 = ac). The research scorer
    // counts them with octave equivalence and no interval window and sees
    // G > 0 on the 9-bearing hexanies; the plugin analyzer keeps its
    // 9/8..4/3 lower-interval window for all three types, and a CPS
    // geometric chain is always a stack of one seed ratio (3-9-27 and
    // 5-15-45 in 1-3-5-9 are stacks of 3/2), which the window excludes.
    // PREDICTED by the scratch float32 mirror on 2026-10-17 before this
    // test ran: hexany 1-3-5-9 reports (P, S, G) = (1, 2, 0).
    auto ma = MicrotoneArray();
    ma.addMicrotone(cpsTone(1.f, 3.f));
    ma.addMicrotone(cpsTone(1.f, 5.f));
    ma.addMicrotone(cpsTone(1.f, 9.f));
    ma.addMicrotone(cpsTone(3.f, 5.f));
    ma.addMicrotone(cpsTone(3.f, 9.f));
    ma.addMicrotone(cpsTone(5.f, 9.f));

    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getGeometricTriads().size(), 0UL);
    CHECK_EQ_UL(t.getAllTriads().size(), 3UL);
}

void testAnalyzerGeometric12ET()
{
    // 12-ET has no exact arithmetic or harmonic means but is nothing but
    // geometric means: 0-3-6 (ratio 2^(3/12) ~ 1.189) and 0-4-8 (2^(4/12)
    // ~ 1.260) both sit inside the 9/8..4/3 window; 0-5-10 (1.335) does
    // not. Of the 12 chains the loop finds, the two whose fifth wraps past
    // the octave (roots 6 and 7 of 0-3-6) are dropped by the NPO-map
    // filter, as every wrapped triad is. PREDICTED (0, 0, 10) by the
    // scratch mirror before this test ran.
    auto ma = MicrotoneArray();
    for (int k = 0; k < 12; ++k) {
        ma.addMicrotone(std::make_shared<Microtone>(
            std::pow(2.f, static_cast<float>(k) / 12.f), "", Microtone::Space::Linear, 2.f));
    }
    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getProcessedArrayCount(), 12UL);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 0UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 0UL);
    CHECK_EQ_UL(t.getGeometricTriads().size(), 10UL);
    CHECK_EQ_UL(t.getAllTriads().size(), 10UL);

    auto const geo = degreesOf(t.getGeometricTriads(), PythagoreanMeans::Type::Geometric);
    CHECK_EQ_UL(geo.size(), 10UL);
    std::vector<std::array<unsigned long, 3>> const expected = {
        {0, 3, 6}, {0, 4, 8}, {1, 4, 7}, {1, 5, 9}, {2, 5, 8},
        {2, 6, 10}, {3, 6, 9}, {3, 7, 11}, {4, 7, 10}, {5, 8, 11}};
    for (auto const& e : expected) {
        bool found = false;
        for (auto const& g : geo) {
            if (g == e) found = true;
        }
        CHECK(found);
    }
    // every triad in the geometric list is tagged Geometric, and all of
    // them (and nothing else) appear in the combined list
    CHECK_EQ_UL(degreesOf(t.getAllTriads(), PythagoreanMeans::Type::Geometric).size(), 10UL);
    CHECK_EQ_UL(degreesOf(t.getAllTriads(), PythagoreanMeans::Type::Proportional).size(), 0UL);
    CHECK_EQ_UL(degreesOf(t.getAllTriads(), PythagoreanMeans::Type::Subcontrary).size(), 0UL);
}

void testAnalyzerGeometricJustChain()
{
    // 1 9/8 5/4 25/16 3/2 15/8: a chain of two 5/4s (1, 5/4, 25/16) is the
    // one in-window geometric triad; 9/8-5/4-? and the 6/5 chain
    // 25/16-15/8-9/4 wrap or miss. Alongside it the scale carries two
    // arithmetic and one harmonic mean. PREDICTED (2, 1, 1) with the
    // geometric triad at degrees (0, 2, 4) by the scratch mirror before
    // this test ran.
    auto ma = MicrotoneArray();
    for (float f : {1.f, 9.f / 8.f, 5.f / 4.f, 25.f / 16.f, 3.f / 2.f, 15.f / 8.f}) {
        ma.addMicrotone(std::make_shared<Microtone>(f, "", Microtone::Space::Linear, 2.f));
    }
    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getProcessedArrayCount(), 6UL);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 2UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 1UL);
    CHECK_EQ_UL(t.getGeometricTriads().size(), 1UL);
    CHECK_EQ_UL(t.getAllTriads().size(), 4UL);
    auto const geo = degreesOf(t.getGeometricTriads(), PythagoreanMeans::Type::Geometric);
    CHECK_EQ_UL(geo.size(), 1UL);
    if (!geo.empty()) {
        CHECK_EQ_UL(geo[0][0], 0UL);
        CHECK_EQ_UL(geo[0][1], 2UL);
        CHECK_EQ_UL(geo[0][2], 4UL);
    }
}

void testAnalyzerClearsBelowThreeNotes()
{
    // Found in review of #13: the analyzer returned early for npo < 3
    // BEFORE clearing the triad lists, so the previous scale's triads
    // survived. Invisible while ET had no triads at all; with geometric
    // triads, 12-ET -> ET npo 2 would keep ten stale rows on a two-note
    // keyboard. Every list must be empty after the shrink.
    auto ma = MicrotoneArray();
    for (int k = 0; k < 12; ++k) {
        ma.addMicrotone(std::make_shared<Microtone>(
            std::pow(2.f, static_cast<float>(k) / 12.f), "", Microtone::Space::Linear, 2.f));
    }
    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getGeometricTriads().size(), 10UL);

    auto two = MicrotoneArray();
    two.addMicrotone(std::make_shared<Microtone>(1.f, "", Microtone::Space::Linear, 2.f));
    two.addMicrotone(std::make_shared<Microtone>(1.5f, "", Microtone::Space::Linear, 2.f));
    t.setMicrotoneArray(two);
    CHECK_EQ_UL(t.getProcessedArrayCount(), 2UL);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 0UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 0UL);
    CHECK_EQ_UL(t.getGeometricTriads().size(), 0UL);
    CHECK_EQ_UL(t.getAllTriads().size(), 0UL);
}

void testAnalyzerGeometric6ET()
{
    // Smallest ET with in-window geometric chains: 0-2-4 and 1-3-5 (ratio
    // 2^(1/3) ~ 1.26); 2-4-6 wraps and is dropped. PREDICTED (0, 0, 2).
    auto ma = MicrotoneArray();
    for (int k = 0; k < 6; ++k) {
        ma.addMicrotone(std::make_shared<Microtone>(
            std::pow(2.f, static_cast<float>(k) / 6.f), "", Microtone::Space::Linear, 2.f));
    }
    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK_EQ_UL(t.getProportionalTriads().size(), 0UL);
    CHECK_EQ_UL(t.getSubcontraryTriads().size(), 0UL);
    CHECK_EQ_UL(t.getGeometricTriads().size(), 2UL);
    auto const geo = degreesOf(t.getGeometricTriads(), PythagoreanMeans::Type::Geometric);
    CHECK_EQ_UL(geo.size(), 2UL);
    if (geo.size() == 2) {
        CHECK((geo[0] == std::array<unsigned long, 3>{0, 2, 4}));
        CHECK((geo[1] == std::array<unsigned long, 3>{1, 3, 5}));
    }
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
    testAnalyzerGeometricCPSWindowed();
    testAnalyzerGeometric12ET();
    testAnalyzerGeometricJustChain();
    testAnalyzerGeometric6ET();
    testAnalyzerClearsBelowThreeNotes();
    testBrunZigzag();
    testBrunMosConstruction();

    std::printf("test_tuning: %d checks, %d failures\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
