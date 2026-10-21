/*
 ==============================================================================

 AbletonAscl.h
 Created: 18 Oct 2026
 Author:  Marcus W. Hobbs

 Export the current tuning as an Ableton Live 12 .ascl file: a Scala .scl
 body plus "! @ABL" directives, so a Live Set without MTS-ESP plays every
 MIDI key 0-127 at the frequency Wilsonic's tuning table gives that key and
 the piano roll shows Wilsonic-style degree names.

 Pure: depends only on Tuning/Microtone, never on JUCE UI or the processor,
 so tests/Makefile compiles it against the stub JuceHeader.

 ==============================================================================
 */

#pragma once

#include <string>
#include <vector>

#include "Microtone.h"
#include "Tuning.h"

struct AsclOptions
{
    std::string fileName;                  // written into the first header comment
    std::string exportDate;                // e.g. "2026-10-18"
    std::string designName;                // e.g. "CPS", "MOS"; empty falls back to the tuning name
    std::string appVersion;                // e.g. "v0.44.0"
    std::string linkUrl;                   // project URL; empty omits LINK
    bool includeScaleDirectives = false;   // SCALE / SCALE_PITCHES: undocumented, untested in Live
};

namespace AbletonAscl
{
    // Live's limits (observed in the 12.4.6 binary / Ableton's bundled files)
    constexpr double liveMinHz = 4.0;
    constexpr double liveMaxHz = 21000.0;
    constexpr int liveMinOctave = -99;
    constexpr int liveMaxOctave = 99;
    constexpr int referenceOctaveMin = -2; // Ableton's spec for REFERENCE_PITCH
    constexpr int referenceOctaveMax = 8;
    constexpr int defaultBaseOctave = 3;   // Live's convention: C3 = key 60
    constexpr int liveTwelveNoteQuirkN = 12;

    // Wilsonic's key -> (period, degree) mapping, in integer arithmetic.
    // Mirrors TuningImp::_update: d = key - mc, period = floor(d / N),
    // degree = d - period * N.
    struct KeyMapping
    {
        int period;
        unsigned long degree;
    };
    KeyMapping keyMapping(int key, int noteNumberMiddleC, unsigned long count);

    // The .ascl text, or "" when the tuning cannot be exported (the reason is
    // appended to warnings prefixed "ERROR:"). Non-fatal findings are appended
    // as plain warnings. UTF-8, LF line endings, C-locale numbers.
    std::string makeAscl(Tuning& tuning, const AsclOptions& options, std::vector<std::string>& warnings);

    // The degree's display name: Microtone::getDegreeName() when a design set
    // it, else a ratio "n/d" for rational tones, else cents "386.3¢".
    std::string degreeName(Microtone& m);

    // Live quoting has no escape character: '"' -> '″', control chars dropped.
    std::string sanitizeName(const std::string& name);

    // "<design> <parameters>" reduced to a safe file name, ending ".ascl".
    std::string defaultFileName(const std::string& designName, const std::string& parameters);

    // Fixed-point number in the C locale (never the user's decimal comma).
    std::string formatFixed(double value, int decimals);
}
