// Stub WilsonicAppSkin for the standalone test binaries.
//
// The real WilsonicAppSkin.h pulls in the full JUCE LookAndFeel stack.
// Tuning-code files use exactly two symbols from it, both plain string
// utilities; the implementations below are copied verbatim from
// Source/WilsonicAppSkin.cpp (floatDescription: lines 137-150,
// replaceAll: lines 125-135). Neither affects any numeric value under
// test.
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

    static void replaceAll(std::string& str, const std::string& from, const std::string& to)
    {
        if(from.empty()) {
            return;
        }

        size_t start_pos = 0;
        while((start_pos = str.find(from, start_pos)) != std::string::npos) {
            str.replace(start_pos, from.length(), to);
            start_pos += to.length();
        }
    }
};
