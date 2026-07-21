// cpp_receipts: execute the plugin's ACTUAL octave-reduction and rational
// arithmetic (Source/Microtone.cpp, Source/Fraction.cpp) and emit JSON so
// the Python side can assert bit-exact agreement with its float32 mirror.
//
// Every case prints the resulting float as raw IEEE-754 bits (hex) —
// "close enough" is not a receipt; bit equality is.

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cmath>

#include "../../../Source/Microtone.h"

namespace
{

std::uint32_t bits(float f)
{
    std::uint32_t u = 0;
    std::memcpy(&u, &f, sizeof u);
    return u;
}

bool first_record = true;

void emit(const char* kind, const char* label, float value,
          unsigned long num = 0, unsigned long den = 0)
{
    if (!first_record)
        std::printf(",\n");
    first_record = false;
    std::printf("  {\"kind\": \"%s\", \"label\": \"%s\", "
                "\"float\": %.9g, \"bits\": \"%08x\", "
                "\"num\": %lu, \"den\": %lu}",
                kind, label, static_cast<double>(value), bits(value), num, den);
}

void reduceFloatCase(const char* label, float input)
{
    Microtone m(input, "", Microtone::Space::Linear, 2.f);
    m.octaveReduce();
    emit("float_reduce", label, m.getFrequencyValue());
}

void reduceRationalCase(const char* label, unsigned long num, unsigned long den)
{
    // should_reduce=false so construction does not pre-normalize the
    // fraction; octaveReduce below is the operation under test.
    Microtone m(num, den, "", Microtone::Space::Linear, 2.f, false);
    m.octaveReduce();
    emit("rational_reduce", label, m.getFrequencyValue(),
         m.getNumerator(), m.getDenominator());
}

void cpsProductCase(const char* label, float seedA, float seedB)
{
    // The numeric core of CPSTuningBase::multiplyByCommonTones
    // (CPSTuningBase.cpp:107-120): plain float product, then the tone is
    // built in Linear space at the default period and octave-reduced by
    // TuningImp::_update.
    float f = 1.f;
    f *= seedA;
    f *= seedB;
    Microtone m(f, "", Microtone::Space::Linear, 2.f);
    m.octaveReduce();
    emit("cps_product_reduce", label, m.getFrequencyValue());
}

} // namespace

int main()
{
    std::printf("[\n");

    // --- float path: conventions and boundaries -------------------------
    reduceFloatCase("one", 1.0f);
    reduceFloatCase("two", 2.0f);
    reduceFloatCase("three", 3.0f);
    reduceFloatCase("three_point_five", 3.5f);
    reduceFloatCase("zero_point_three", 0.3f);
    reduceFloatCase("tiny", 1e-6f);
    reduceFloatCase("huge", 1e6f);
    reduceFloatCase("just_below_two", std::nextafterf(2.0f, 1.0f));
    reduceFloatCase("just_above_two", std::nextafterf(2.0f, 3.0f));
    reduceFloatCase("just_below_one", std::nextafterf(1.0f, 0.0f));
    reduceFloatCase("just_below_four", std::nextafterf(4.0f, 1.0f));

    // --- rational path: conventions and boundaries ----------------------
    reduceRationalCase("r_35_16", 35, 16);
    reduceRationalCase("r_3_1", 3, 1);
    reduceRationalCase("r_1_3", 1, 3);
    reduceRationalCase("r_2_1", 2, 1);
    reduceRationalCase("r_1_1", 1, 1);
    reduceRationalCase("r_45_8", 45, 8);
    reduceRationalCase("r_135_64", 135, 64);
    // Rational whose true value is just below 2 but whose floatValue()
    // rounds to exactly 2.0f: (2^25 - 1) / 2^24. The reduce loop's float
    // comparisons may push the exact rational OUTSIDE [1, 2).
    reduceRationalCase("r_boundary_2e25", 33554431UL, 16777216UL);
    // And one that rounds to just below 2.0f: (2^24 - 1) / 2^23.
    reduceRationalCase("r_boundary_2e24", 16777215UL, 8388608UL);

    // --- CPS product chain, seeds 1-3-5-7 as floats ---------------------
    cpsProductCase("cps_1x3", 1.0f, 3.0f);
    cpsProductCase("cps_1x5", 1.0f, 5.0f);
    cpsProductCase("cps_1x7", 1.0f, 7.0f);
    cpsProductCase("cps_3x5", 3.0f, 5.0f);
    cpsProductCase("cps_3x7", 3.0f, 7.0f);
    cpsProductCase("cps_5x7", 5.0f, 7.0f);
    // non-integer seeds (the plugin allows arbitrary float seeds)
    cpsProductCase("cps_1p3x2p6", 1.3f, 2.6f);

    std::printf("\n]\n");
    return 0;
}
