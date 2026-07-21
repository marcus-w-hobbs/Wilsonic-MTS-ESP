// Stub JuceHeader for the standalone test binaries.
//
// Lets REAL Source/*.cpp files compile and run without the JUCE framework.
// Only inert scaffolding is stubbed: assertions, debug logging, locks
// (tests are single-threaded), string formatting, and UI geometry types.
// Numeric code under test never depends on stub behavior, with one
// documented exception: AffineTransform is identity, so Gral DISPLAY
// coordinates computed under test are meaningless — no test asserts them.
#pragma once
#include <cassert>
#include <cmath>
#include <limits>
#include <initializer_list>
#include <set>
#include <sstream>
#include <string>
#include <vector>

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

// --- threading (tests are single-threaded; locks are no-ops) --------------

struct CriticalSection
{
};

struct ScopedLock
{
    explicit ScopedLock(const CriticalSection&) {}
};

// --- string (functional wrapper; formatting is std::, not juce::) ---------
// Affects only description/Scala-comment TEXT, never tuning numerics.

class String
{
public:
    String() = default;
    String(const char* s) : _s(s) {}
    String(const std::string& s) : _s(s) {}
    explicit String(int v) : _s(std::to_string(v)) {}
    explicit String(long v) : _s(std::to_string(v)) {}
    explicit String(unsigned long v) : _s(std::to_string(v)) {}
    explicit String(float v) { std::ostringstream o; o << v; _s = o.str(); }
    explicit String(double v) { std::ostringstream o; o << v; _s = o.str(); }

    String operator+(const String& other) const { return String(_s + other._s); }
    String& operator+=(const String& other) { _s += other._s; return *this; }
    bool operator==(const String& other) const { return _s == other._s; }
    bool operator<(const String& other) const { return _s < other._s; }

    const std::string& toStdString() const { return _s; }
    bool isEmpty() const { return _s.empty(); }

private:
    std::string _s;
};

inline String operator+(const char* lhs, const String& rhs)
{
    return String(lhs) + rhs;
}

inline std::ostream& operator<<(std::ostream& os, const String& s)
{
    return os << s.toStdString();
}

// --- colour ---------------------------------------------------------------

struct Colour
{
    unsigned int argb = 0;
    Colour() = default;
    explicit Colour(unsigned int c) : argb(c) {}
    Colour darker(float = 0.3f) const { return *this; }
    Colour brighter(float = 0.4f) const { return *this; }
};

namespace Colours
{
inline const Colour red {0xffff0000};
inline const Colour grey {0xff808080};
inline const Colour mediumpurple {0xff9370db};
} // namespace Colours

// --- geometry (data carriers only; no test asserts UI geometry) -----------

struct AffineTransform;

template <typename T>
struct Point
{
    T x {}, y {};
    Point() = default;
    Point(T xx, T yy) : x(xx), y(yy) {}
    T getX() const { return x; }
    T getY() const { return y; }
    void setX(T xx) { x = xx; }
    void setY(T yy) { y = yy; }
    Point<float> toFloat() const { return Point<float>(static_cast<float>(x), static_cast<float>(y)); }
    Point operator+(const Point& o) const { return Point(x + o.x, y + o.y); }
    Point operator-(const Point& o) const { return Point(x - o.x, y - o.y); }
    Point operator*(T s) const { return Point(x * s, y * s); }
    Point& operator+=(const Point& o) { x += o.x; y += o.y; return *this; }
    bool operator==(const Point& o) const { return x == o.x && y == o.y; }
    bool operator!=(const Point& o) const { return !(*this == o); }
    Point& operator-=(const Point& o) { x -= o.x; y -= o.y; return *this; }
    Point translated(T dx, T dy) const { return Point(x + dx, y + dy); }
    Point transformedBy(const AffineTransform&) const { return *this; }
    // juce::Point::getAngleToPoint formula (clockwise from vertical)
    float getAngleToPoint(const Point& o) const
    {
        return std::atan2(static_cast<float>(o.x - x), static_cast<float>(y - o.y));
    }
    String toString() const
    {
        std::ostringstream out;
        out << x << ", " << y;
        return String(out.str());
    }
};

template <typename T>
inline Point<T> operator*(T s, const Point<T>& p)
{
    return Point<T>(s * p.x, s * p.y);
}

template <typename T>
struct MathConstants
{
    static constexpr T pi = static_cast<T>(3.141592653589793238L);
    static constexpr T twoPi = static_cast<T>(2) * pi;
    static constexpr T halfPi = pi / static_cast<T>(2);
};

struct Path
{
    template <typename T>
    bool contains(Point<T>) const { return false; }
    void clear() {}
};

template <typename T>
struct Rectangle
{
    T x {}, y {}, w {}, h {};
    Rectangle() = default;
    Rectangle(T xx, T yy, T ww, T hh) : x(xx), y(yy), w(ww), h(hh) {}
    T getWidth() const { return w; }
    T getHeight() const { return h; }
    T getX() const { return x; }
    T getY() const { return y; }
};

// IDENTITY transform: Gral display coordinates computed under stub are
// meaningless; tuning-table and triad numerics never touch this type.
struct AffineTransform
{
    static AffineTransform translation(float, float) { return {}; }
    static AffineTransform rotation(float, float, float) { return {}; }
    static AffineTransform shear(float, float) { return {}; }
    static AffineTransform scale(float) { return {}; }
    static AffineTransform scale(float, float) { return {}; }
    AffineTransform translated(float, float) const { return {}; }
    AffineTransform translated(Point<float>) const { return {}; }
    AffineTransform followedBy(const AffineTransform&) const { return {}; }
    template <typename T>
    void transformPoint(T&, T&) const {}
};

struct StringArray
{
    std::vector<String> strings;
    StringArray() = default;
    StringArray(std::initializer_list<const char*> items)
    {
        for (auto* item : items)
            strings.emplace_back(item);
    }
    const String& operator[](int i) const { return strings[static_cast<size_t>(i)]; }
    int size() const { return static_cast<int>(strings.size()); }
};

// Some headers name juce types with explicit namespace qualification.
namespace juce
{
template <typename T>
using Point = ::Point<T>;
using String = ::String;
} // namespace juce

// Referenced only in signatures of paint methods, whose bodies live in
// paint_stubs.cpp for the test binaries.
class Graphics;
class WilsonicProcessor;

struct Justification
{
    enum Flags { centred, topRight };
    Justification(Flags) {}
};
