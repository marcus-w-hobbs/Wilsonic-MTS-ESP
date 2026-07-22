// Stub JuceHeader for the cpp_receipts harness.
//
// Same technique as tests/JuceHeader.h (narenratan's CI setup): lets the
// REAL Source/*.cpp files compile without the JUCE framework. Only inert
// scaffolding is stubbed (assertions, debug logging, UI geometry types);
// every number under test is computed by the plugin's actual code.
#pragma once
#include <cassert>
#include <cmath>
#include <limits>
#include <string>

#ifndef jassert
#define jassert(x) assert(x)
#endif
#ifndef jassertfalse
#define jassertfalse assert(false)
#endif
#ifndef DBG
#define DBG(x)
#endif

template <typename Type>
static constexpr const Type& jlimit(const Type& lower, const Type& upper, const Type& value)
{
    return value < lower ? lower : (value > upper ? upper : value);
}

// Minimal stand-ins for JUCE types Microtone stores but never uses numerically.
template <typename T>
struct Point
{
    T x {}, y {};
    Point() = default;
    Point(T xx, T yy) : x(xx), y(yy) {}
};

struct Path
{
};

// Fraction.cpp's error branch concatenates juce::String; the branch only
// fires on denominator==0, which the harness never does.
struct String
{
    explicit String(unsigned long) {}
    explicit String(long) {}
    explicit String(int) {}
};

inline std::string operator+(const char* lhs, const String&) { return lhs; }
inline std::string operator+(const std::string& lhs, const String&) { return lhs; }
