// Research CLI: runs the plugin's REAL tuning code headlessly and emits
// JSON, so the Python research harness (experiments/triads/) can use the
// C++ as ground truth for scale generation and triad analysis.
//
// Usage:
//   research_cli hexany A B C D          four float seeds, CPS(4,2)
//   research_cli mos GENERATOR LEVEL     generator in [0,1] (fraction of
//                                        octave, log2 space), level 0..9
//
// Output: one JSON object on stdout:
//   {"scale": [{"float": f, "bits": "xxxxxxxx"}, ...],
//    "proportional": N, "subcontrary": N}
// scale = the processed array (octave-reduced, sorted); counts = the
// analyzer's REPORTED triads (post NPO-map filter, matching the UI).

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>

#include "../Source/Brun.h"
#include "../Source/Microtone.h"
#include "../Source/MicrotoneArray.h"
#include "../Source/TuningImp.h"

namespace
{

std::uint32_t bits(float f)
{
    std::uint32_t u = 0;
    std::memcpy(&u, &f, sizeof u);
    return u;
}

void emitResult(Tuning& t)
{
    auto processed = t.getProcessedArray();
    std::printf("{\"scale\": [");
    for (unsigned long i = 0; i < processed.count(); ++i) {
        auto const f = processed.microtoneAtIndex(i)->getFrequencyValue();
        std::printf("%s{\"float\": %.9g, \"bits\": \"%08x\"}",
                    i == 0 ? "" : ", ", static_cast<double>(f), bits(f));
    }
    std::printf("], \"proportional\": %lu, \"subcontrary\": %lu}\n",
                static_cast<unsigned long>(t.getProportionalTriads().size()),
                static_cast<unsigned long>(t.getSubcontraryTriads().size()));
}

int runHexany(int argc, char** argv)
{
    if (argc != 6) {
        std::fprintf(stderr, "hexany needs 4 seeds\n");
        return 2;
    }
    float seeds[4];
    for (int i = 0; i < 4; ++i)
        seeds[i] = std::strtof(argv[2 + i], nullptr);

    // The numeric core of CPSTuningBase::multiplyByCommonTones: plain
    // float products of seed pairs, tones in Linear space at period 2.
    auto ma = MicrotoneArray();
    for (int i = 0; i < 4; ++i) {
        for (int j = i + 1; j < 4; ++j) {
            auto f = 1.f;
            f *= seeds[i];
            f *= seeds[j];
            ma.addMicrotone(std::make_shared<Microtone>(
                f, "", Microtone::Space::Linear, 2.f));
        }
    }
    TuningImp t;
    t.setMicrotoneArray(ma); // octave-reduce, sort, analyze (no uniquify)
    emitResult(t);
    return 0;
}

int runMos(int argc, char** argv)
{
    if (argc != 4) {
        std::fprintf(stderr, "mos needs GENERATOR LEVEL\n");
        return 2;
    }
    auto const g = std::strtof(argv[2], nullptr);
    auto const level = static_cast<unsigned long>(std::strtoul(argv[3], nullptr, 10));
    Brun b;
    b.setGenerator(g);
    b.setLevel(level);
    emitResult(b);
    return 0;
}

} // namespace

int main(int argc, char** argv)
{
    if (argc >= 2 && std::strcmp(argv[1], "hexany") == 0)
        return runHexany(argc, argv);
    if (argc >= 2 && std::strcmp(argv[1], "mos") == 0)
        return runMos(argc, argv);
    std::fprintf(stderr, "usage: research_cli hexany A B C D | mos GENERATOR LEVEL\n");
    return 2;
}
