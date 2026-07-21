// Stub WilsonicAppSkin for the cpp_receipts harness.
//
// Microtone.cpp uses exactly one symbol from the real WilsonicAppSkin
// (which pulls in the full JUCE LookAndFeel stack): the string formatter
// floatDescription. The implementation below is copied verbatim from
// Source/WilsonicAppSkin.cpp:137-150 so descriptions match too; it has no
// effect on any numeric value under test.
#pragma once

#include <iomanip>
#include <sstream>
#include <string>

struct WilsonicAppSkin
{
    static std::string const floatDescription(float f, int places = 1)
    {
        std::ostringstream out;
        out << std::fixed << std::setprecision(places) << f;
        std::string s = out.str();

        // Remove trailing zeros
        s.erase(s.find_last_not_of('0') + 1, std::string::npos);
        // Remove trailing dot if necessary
        if (s.back() == '.') {
            s.pop_back();
        }

        return s;
    }
};
