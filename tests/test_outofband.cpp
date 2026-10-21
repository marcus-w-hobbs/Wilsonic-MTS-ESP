// Tests for the out-of-band output stage (Source/TuningOutput.{h,cpp}).
//
// computeTuningOutput() is the one place Wilsonic decides what to do with
// a key whose raw tuning-table frequency falls outside Ableton Live's
// playable band (4 Hz .. 21 kHz inclusive) or is not a usable number at
// all (NaN, infinite, <= 0). The tuning itself stays raw; this stage runs
// only on the way out to MTS-ESP, the built-in synth and the keyboard.
//
// The last two tests push a REAL TuningImp (N = 1) and a REAL Brun (N = 2)
// through the stage, so the key -> frequency mapping under test is the
// plugin's own.

#include <cmath>
#include <cstdio>
#include <limits>
#include <memory>
#include <vector>

#include "../Source/Brun.h"
#include "../Source/Microtone.h"
#include "../Source/MicrotoneArray.h"
#include "../Source/TuningConstants.h"
#include "../Source/TuningImp.h"
#include "../Source/TuningOutput.h"

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

#define CHECK_NEAR(a, b)                                                   \
    do {                                                                   \
        ++checks;                                                          \
        double va = static_cast<double>(a);                                \
        double vb = static_cast<double>(b);                                \
        if (!(std::fabs(va - vb) <= 1e-9 * std::fmax(1.0, std::fabs(vb)))) { \
            ++failures;                                                    \
            std::printf("FAIL %s:%d: %s ~= %s (%.9g != %.9g)\n", __FILE__, \
                        __LINE__, #a, #b, va, vb);                         \
        }                                                                  \
    } while (0)

constexpr unsigned long kNumKeys = WilsonicProcessorConstants::numMidiNotes;
constexpr double kMin = TuningConstants::kPlayableMinHz;
constexpr double kMax = TuningConstants::kPlayableMaxHz;

const float kNaN = std::numeric_limits<float>::quiet_NaN();
const float kInf = std::numeric_limits<float>::infinity();

struct Table
{
    float raw[kNumKeys];
    explicit Table(float fill = 440.f)
    {
        for (unsigned long k = 0; k < kNumKeys; ++k) {
            raw[k] = fill;
        }
    }
};

bool inBand(double hz)
{
    return std::isfinite(hz) && hz >= kMin && hz <= kMax;
}

unsigned long countFiltered(const TuningOutput& out)
{
    unsigned long n = 0;
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        n += out.filtered[k] ? 1UL : 0UL;
    }
    return n;
}

// ---------------------------------------------------------------------------

void testAllInBandIsIdentity()
{
    // Sanity: the constants are what Live uses.
    CHECK(kMin == 4.0);
    CHECK(kMax == 21000.0);

    Table t;
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        t.raw[k] = 8.f + static_cast<float>(k) * 100.f; // 8 .. 12708 Hz
    }
    for (auto policy : {OutOfBandPolicy::Filter, OutOfBandPolicy::PassThrough}) {
        auto out = computeTuningOutput(t.raw, policy);
        CHECK(countFiltered(out) == 0UL);
        for (unsigned long k = 0; k < kNumKeys; ++k) {
            CHECK(out.hz[k] == static_cast<double>(t.raw[k]));
        }
    }
}

void testBoundariesAreInclusive()
{
    Table t;
    t.raw[10] = 4.0f;        // in
    t.raw[11] = 21000.0f;    // in
    t.raw[12] = 3.9999f;     // out
    t.raw[13] = 21000.001f;  // out (float rounds up to 21000.0019..., still > 21000)
    CHECK(static_cast<double>(t.raw[13]) > kMax);
    CHECK(static_cast<double>(t.raw[12]) < kMin);

    auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
    CHECK(!out.filtered[10]);
    CHECK(out.hz[10] == 4.0);
    CHECK(!out.filtered[11]);
    CHECK(out.hz[11] == 21000.0);
    CHECK(out.filtered[12]);
    CHECK(out.filtered[13]);
    CHECK(countFiltered(out) == 2UL);
    // both out-of-band keys take the nearest LOWER in-band key
    CHECK(out.hz[12] == 21000.0); // key 11
    CHECK(out.hz[13] == 21000.0); // key 12 is filtered, so key 11 again

    // Pass through keeps the raw values and filters nothing
    auto pass = computeTuningOutput(t.raw, OutOfBandPolicy::PassThrough);
    CHECK(countFiltered(pass) == 0UL);
    CHECK(pass.hz[12] == static_cast<double>(t.raw[12]));
    CHECK(pass.hz[13] == static_cast<double>(t.raw[13]));
}

// N = 1, period 2, middle C on key 60 at 261.6 Hz: key k = 261.6 * 2^(k-60).
// Keys 0..53 are below 4 Hz, keys 67..127 are above 21 kHz, 54..66 are in.
void testOneNotePerOctaveSynthetic()
{
    Table t;
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        t.raw[k] = 261.6f * std::pow(2.f, static_cast<float>(static_cast<int>(k) - 60));
    }
    CHECK(static_cast<double>(t.raw[53]) < kMin);
    CHECK(static_cast<double>(t.raw[54]) >= kMin);
    CHECK(static_cast<double>(t.raw[66]) <= kMax);
    CHECK(static_cast<double>(t.raw[67]) > kMax);

    auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
    CHECK(countFiltered(out) == 54UL + 61UL);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        if (k < 54) {
            // no lower in-band key: take the lowest in-band key
            CHECK(out.filtered[k]);
            CHECK(out.hz[k] == static_cast<double>(t.raw[54]));
        } else if (k <= 66) {
            CHECK(!out.filtered[k]);
            CHECK(out.hz[k] == static_cast<double>(t.raw[k]));
        } else {
            // the highest in-band key below it
            CHECK(out.filtered[k]);
            CHECK(out.hz[k] == static_cast<double>(t.raw[66]));
        }
    }
    // every stand-in is itself playable
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        CHECK(inBand(out.hz[k]));
    }

    // Pass through: raw everywhere, nothing filtered, even below 4 Hz
    auto pass = computeTuningOutput(t.raw, OutOfBandPolicy::PassThrough);
    CHECK(countFiltered(pass) == 0UL);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        CHECK(pass.hz[k] == static_cast<double>(t.raw[k]));
    }
}

// The neighbour rule walks KEY NUMBERS, not pitch. A non-monotonic table
// must take the stand-in from the adjacent key number even when a closer
// pitch sits elsewhere.
void testNeighbourRuleUsesKeyOrder()
{
    Table t(440.f);
    t.raw[10] = 1000.f;   // in band, lower neighbour of key 11
    t.raw[11] = 2.f;      // out of band (sub-audio)
    t.raw[12] = 300.f;    // in band, higher neighbour; closer in pitch to 2 Hz
    auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
    CHECK(out.filtered[11]);
    CHECK(out.hz[11] == 1000.0);
    CHECK(!out.filtered[10]);
    CHECK(!out.filtered[12]);

    // a run of out-of-band keys all take the last in-band key below the run
    Table r(440.f);
    r.raw[20] = 700.f;
    r.raw[21] = 30000.f;
    r.raw[22] = 1.f;
    r.raw[23] = 50000.f;
    r.raw[24] = 900.f;
    auto run = computeTuningOutput(r.raw, OutOfBandPolicy::Filter);
    CHECK(run.hz[21] == 700.0);
    CHECK(run.hz[22] == 700.0);
    CHECK(run.hz[23] == 700.0);
    CHECK(run.filtered[21] && run.filtered[22] && run.filtered[23]);
    CHECK(!run.filtered[24] && run.hz[24] == 900.0);

    // key 0 has no lower key: it takes the nearest HIGHER in-band key
    Table h(440.f);
    h.raw[0] = 100000.f;
    h.raw[1] = 60000.f;
    h.raw[2] = 500.f;
    auto hi = computeTuningOutput(h.raw, OutOfBandPolicy::Filter);
    CHECK(hi.filtered[0] && hi.hz[0] == 500.0);
    CHECK(hi.filtered[1] && hi.hz[1] == 500.0);
}

void testUnusableValues()
{
    Table t(440.f);
    t.raw[30] = kNaN;
    t.raw[40] = kInf;
    t.raw[50] = -kInf;
    t.raw[60] = 0.f;
    t.raw[70] = -5.f;
    const unsigned long bad[] = {30, 40, 50, 60, 70};

    // Filter: all five are filtered and replaced by the lower neighbour (440)
    auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
    CHECK(countFiltered(out) == 5UL);
    for (auto k : bad) {
        CHECK(out.filtered[k]);
        CHECK(out.hz[k] == 440.0);
    }

    // Pass through: replaced (never sent raw) but NOT filtered
    auto pass = computeTuningOutput(t.raw, OutOfBandPolicy::PassThrough);
    CHECK(countFiltered(pass) == 0UL);
    for (auto k : bad) {
        CHECK(!pass.filtered[k]);
        CHECK(pass.hz[k] == 440.0);
    }
    // ... and every output value is a usable number in both modes
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        CHECK(std::isfinite(out.hz[k]) && out.hz[k] > 0.0);
        CHECK(std::isfinite(pass.hz[k]) && pass.hz[k] > 0.0);
    }

    // Pass through with sub-audio neighbours: the neighbour rule walks
    // usable keys, so an unusable key takes a sub-audio stand-in unchanged.
    Table s(0.5f);
    s.raw[64] = kNaN;
    auto sub = computeTuningOutput(s.raw, OutOfBandPolicy::PassThrough);
    CHECK(!sub.filtered[64]);
    CHECK(sub.hz[64] == 0.5);

    // Pass through, unusable key 0: no lower key, so the next higher usable one
    Table z(440.f);
    z.raw[0] = kNaN;
    z.raw[1] = -kInf;
    z.raw[2] = 2.f; // sub-audio but usable
    auto zero = computeTuningOutput(z.raw, OutOfBandPolicy::PassThrough);
    CHECK(!zero.filtered[0] && zero.hz[0] == 2.0);
    CHECK(!zero.filtered[1] && zero.hz[1] == 2.0);
}

// Keys the tuning itself marks unmapped (Microtone::getFilterNote) are
// filtered under both policies, take a stand-in, and never stand in for
// their neighbours.
void testPreFilteredKeys()
{
    Table t(440.f);
    t.raw[40] = 500.f;   // in band but unmapped
    t.raw[41] = 1.f;     // out of band: must skip key 40 and take key 39
    bool pre[kNumKeys] = {};
    pre[40] = true;

    auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter, pre);
    CHECK(countFiltered(out) == 2UL);
    CHECK(out.filtered[40] && out.hz[40] == 440.0);
    CHECK(out.filtered[41] && out.hz[41] == 440.0);
    CHECK(!out.filtered[39] && !out.filtered[42]);

    auto pass = computeTuningOutput(t.raw, OutOfBandPolicy::PassThrough, pre);
    CHECK(countFiltered(pass) == 1UL);
    CHECK(pass.filtered[40] && pass.hz[40] == 440.0);
    CHECK(!pass.filtered[41] && pass.hz[41] == 1.0); // raw sub-audio passes through

    // nullptr means no pre-filtered keys: identical to the two-argument call
    auto plain = computeTuningOutput(t.raw, OutOfBandPolicy::Filter, nullptr);
    auto two = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        CHECK(plain.hz[k] == two.hz[k] && plain.filtered[k] == two.filtered[k]);
    }
    CHECK(!two.filtered[40] && two.hz[41] == 500.0);
}

void testNoKeyInBandClampsToEdge()
{
    // all below
    {
        Table t(1.f);
        auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
        CHECK(countFiltered(out) == kNumKeys);
        for (unsigned long k = 0; k < kNumKeys; ++k) {
            CHECK(out.hz[k] == kMin);
        }
    }
    // all above
    {
        Table t(50000.f);
        auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
        CHECK(countFiltered(out) == kNumKeys);
        for (unsigned long k = 0; k < kNumKeys; ++k) {
            CHECK(out.hz[k] == kMax);
        }
    }
    // mixed, none in band: each key clamps its OWN raw value to the edge
    {
        Table t(1.f);
        t.raw[100] = 90000.f;
        t.raw[101] = kInf;
        t.raw[102] = -kInf;
        t.raw[103] = kNaN;
        t.raw[104] = 0.f;
        t.raw[105] = -3.f;
        auto out = computeTuningOutput(t.raw, OutOfBandPolicy::Filter);
        CHECK(countFiltered(out) == kNumKeys);
        CHECK(out.hz[0] == kMin);
        CHECK(out.hz[100] == kMax);
        CHECK(out.hz[101] == kMax);
        CHECK(out.hz[102] == kMin);
        CHECK(out.hz[103] == kMin);
        CHECK(out.hz[104] == kMin);
        CHECK(out.hz[105] == kMin);
    }
    // Pass through with NO usable key at all: clamp too, never filtered
    {
        Table t(kNaN);
        t.raw[5] = kInf;
        t.raw[6] = -1.f;
        auto out = computeTuningOutput(t.raw, OutOfBandPolicy::PassThrough);
        CHECK(countFiltered(out) == 0UL);
        CHECK(out.hz[0] == kMin);
        CHECK(out.hz[5] == kMax);
        CHECK(out.hz[6] == kMin);
    }
}

void testPassThroughSubAudioIsRaw()
{
    Table t(440.f);
    t.raw[0] = 0.25f;
    t.raw[1] = 1.f;
    t.raw[2] = 3.9f;
    t.raw[127] = 40000.f;
    auto out = computeTuningOutput(t.raw, OutOfBandPolicy::PassThrough);
    CHECK(countFiltered(out) == 0UL);
    CHECK(out.hz[0] == 0.25);
    CHECK(out.hz[1] == 1.0);
    CHECK(out.hz[2] == static_cast<double>(3.9f));
    CHECK(out.hz[127] == 40000.0);
}

// ---------------------------------------------------------------------------
// End to end through the plugin's own tuning code.

void fillRaw(Tuning& tuning, float raw[kNumKeys])
{
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        raw[k] = tuning.getTuningTableFrequency(k);
    }
}

void testDefault12ETNeverFilters()
{
    TuningImp t; // default 12ET, middle C = key 60 at 261.6255653 Hz
    float raw[kNumKeys];
    fillRaw(t, raw);
    auto out = computeTuningOutput(raw, OutOfBandPolicy::Filter);
    CHECK(countFiltered(out) == 0UL);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        CHECK(out.hz[k] == static_cast<double>(raw[k]));
    }
}

void testRealTuningImpOneNote()
{
    // N = 1 through TuningImp::_update: one microtone, octave 2, middle C
    // on key 60. Mirrors testOneNotePerOctaveSynthetic with the real table.
    auto ma = MicrotoneArray();
    ma.addMicrotone(std::make_shared<Microtone>(1.f, "", Microtone::Space::Linear, 2.f));
    TuningImp t;
    t.setMicrotoneArray(ma);
    CHECK(t.getProcessedArrayCount() == 1UL);
    CHECK(t.getNoteNumberMiddleC() == 60UL);

    float raw[kNumKeys];
    fillRaw(t, raw);
    CHECK_NEAR(raw[60], TuningConstants::middleCFrequency);
    CHECK_NEAR(raw[61], 2.f * TuningConstants::middleCFrequency);
    // the raw table really does leave the band at both ends
    CHECK(static_cast<double>(raw[0]) < kMin);
    CHECK(static_cast<double>(raw[127]) > kMax);

    auto out = computeTuningOutput(raw, OutOfBandPolicy::Filter);
    CHECK(countFiltered(out) == 54UL + 61UL);
    CHECK(out.filtered[53] && !out.filtered[54]);
    CHECK(!out.filtered[66] && out.filtered[67]);
    for (unsigned long k = 0; k < 54; ++k) {
        CHECK(out.hz[k] == static_cast<double>(raw[54]));
    }
    for (unsigned long k = 54; k <= 66; ++k) {
        CHECK(out.hz[k] == static_cast<double>(raw[k]));
    }
    for (unsigned long k = 67; k < kNumKeys; ++k) {
        CHECK(out.hz[k] == static_cast<double>(raw[66]));
    }

    // the tuning itself is untouched by the output stage
    float again[kNumKeys];
    fillRaw(t, again);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        CHECK(again[k] == raw[k]);
    }
}

void testRealBrunTwoNotes()
{
    // N = 2 through a real Brun (level 1 of the fifth generator is a
    // 2-note MOS). 128 keys span 64 periods, so both ends leave the band.
    Brun b;
    b.setGenerator(0.5849625f);
    b.setLevel(1UL);
    CHECK(b.getProcessedArrayCount() == 2UL);

    float raw[kNumKeys];
    fillRaw(b, raw);
    CHECK(static_cast<double>(raw[0]) < kMin);
    CHECK(static_cast<double>(raw[127]) > kMax);

    auto out = computeTuningOutput(raw, OutOfBandPolicy::Filter);
    unsigned long lowest = kNumKeys, highest = kNumKeys;
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        if (inBand(raw[k])) {
            if (lowest == kNumKeys) {
                lowest = k;
            }
            highest = k;
        }
    }
    CHECK(lowest < highest && highest < kNumKeys);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        bool const expectFiltered = !inBand(raw[k]);
        CHECK(out.filtered[k] == expectFiltered);
        CHECK(inBand(out.hz[k]));
        if (!expectFiltered) {
            CHECK(out.hz[k] == static_cast<double>(raw[k]));
        } else if (k < lowest) {
            CHECK(out.hz[k] == static_cast<double>(raw[lowest]));
        } else if (k > highest) {
            CHECK(out.hz[k] == static_cast<double>(raw[highest]));
        }
    }
    // the 2-note MOS is monotonic in key order, so no interior key filters
    for (unsigned long k = lowest; k <= highest; ++k) {
        CHECK(!out.filtered[k]);
    }
}

} // namespace

int main()
{
    testAllInBandIsIdentity();
    testBoundariesAreInclusive();
    testOneNotePerOctaveSynthetic();
    testNeighbourRuleUsesKeyOrder();
    testUnusableValues();
    testPreFilteredKeys();
    testNoKeyInBandClampsToEdge();
    testPassThroughSubAudioIsRaw();
    testDefault12ETNeverFilters();
    testRealTuningImpOneNote();
    testRealBrunTwoNotes();

    std::printf("test_outofband: %d checks, %d failures\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
