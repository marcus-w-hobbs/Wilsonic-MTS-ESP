/*
 ==============================================================================

 AbletonAscl.cpp
 Created: 18 Oct 2026
 Author:  Marcus W. Hobbs

 See AbletonAscl.h. The Live behaviour encoded here (key mapping, pitch
 formula, label rules, the 12-note quirk, limits) was observed in the Live
 12.4.6 binary and Ableton's bundled .ascl files; items that are inferred
 rather than observed are marked in the PR's manual checklist.

 ==============================================================================
 */

#include "AbletonAscl.h"

#include <JuceHeader.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <limits>
#include <locale>
#include <numeric>
#include <sstream>

#include "MicrotoneArray.h"
#include "WilsonicProcessorConstants.h"

namespace
{
constexpr int kNumKeys = static_cast<int>(WilsonicProcessorConstants::numMidiNotes); // 128
constexpr double kCentsPerOctave = 1200.0;
constexpr double kTableMatchToleranceCents = 0.01;
constexpr std::uint64_t kMaxRatioTerm = 0x7fffffffULL; // 31 bits
constexpr std::size_t kMaxFileNameStem = 80;
constexpr char kLF = '\n';

// exact equality without -Wfloat-equal (two processed degrees sharing one float value)
bool sameValue(double a, double b)
{
    return !(a < b) && !(b < a);
}

double centsBetween(double lower, double upper)
{
    return kCentsPerOctave * std::log2(upper / lower);
}

// Collapse CR/LF/tab runs to one space so a value fits on one Scala line.
std::string oneLine(const std::string& text)
{
    std::string out;
    out.reserve(text.size());
    bool pendingSpace = false;
    for (char c : text) {
        auto const ch = static_cast<unsigned char>(c);
        if (ch == '\r' || ch == '\n' || ch == '\t' || ch == ' ') {
            pendingSpace = !out.empty();
            continue;
        }
        if (ch < 0x20 || ch == 0x7f) {
            continue;
        }
        if (pendingSpace) {
            out += ' ';
            pendingSpace = false;
        }
        out += static_cast<char>(ch);
    }
    return out;
}

std::string quotedName(const std::string& name)
{
    return "\"" + name + " \""; // trailing space: Live glues the octave number straight onto the name
}

struct Ratio
{
    bool valid = false;
    std::uint64_t num = 0;
    std::uint64_t den = 1;
};

// v[i] / v[0] as a reduced ratio when both tones are rational and the terms fit 31 bits.
Ratio ratioOver(Microtone& tone, Microtone& reference)
{
    Ratio r;
    if (!tone.isRational() || !reference.isRational()) {
        return r;
    }
    auto const num = static_cast<std::uint64_t>(tone.getNumerator()) * static_cast<std::uint64_t>(reference.getDenominator());
    auto const den = static_cast<std::uint64_t>(tone.getDenominator()) * static_cast<std::uint64_t>(reference.getNumerator());
    if (num == 0 || den == 0) {
        return r;
    }
    auto const g = std::gcd(num, den);
    r.num = num / g;
    r.den = den / g;
    r.valid = r.num <= kMaxRatioTerm && r.den <= kMaxRatioTerm;
    return r;
}

// The period as p/q when the float is exactly a small rational (2, 3, 3/2...).
Ratio periodRatio(double period)
{
    Ratio r;
    for (std::uint64_t q = 1; q <= 1024; ++q) {
        auto const pq = period * static_cast<double>(q);
        auto const p = std::llround(pq);
        if (p > 0 && std::fabs(pq - static_cast<double>(p)) < 1e-9) {
            auto const g = std::gcd(static_cast<std::uint64_t>(p), q);
            r.num = static_cast<std::uint64_t>(p) / g;
            r.den = q / g;
            r.valid = true;
            return r;
        }
    }
    return r;
}

std::string ratioText(const Ratio& r)
{
    return std::to_string(r.num) + "/" + std::to_string(r.den);
}

int floorDiv(int a, int b)
{
    auto q = a / b;
    if ((a % b != 0) && ((a < 0) != (b < 0))) {
        --q;
    }
    return q;
}
} // namespace

namespace AbletonAscl
{

std::string formatFixed(double value, int decimals)
{
    std::ostringstream out;
    out.imbue(std::locale::classic());
    out.setf(std::ios::fixed);
    out.precision(decimals);
    out << value;
    return out.str();
}

KeyMapping keyMapping(int key, int noteNumberMiddleC, unsigned long count)
{
    auto const n = static_cast<int>(count);
    auto const d = key - noteNumberMiddleC;
    auto const r = floorDiv(d, n);
    auto const i = d - r * n;
    return {r, static_cast<unsigned long>(i)};
}

std::string sanitizeName(const std::string& name)
{
    std::string out;
    out.reserve(name.size());
    for (char c : name) {
        auto const ch = static_cast<unsigned char>(c);
        if (ch == '"') {
            out += "\xE2\x80\xB3"; // U+2033 DOUBLE PRIME
        } else if (ch < 0x20 || ch == 0x7f) {
            continue; // control characters
        } else {
            out += static_cast<char>(ch);
        }
    }
    return out;
}

std::string degreeName(Microtone& m)
{
    auto const& set = m.getDegreeName();
    if (!set.empty()) {
        return set;
    }
    if (m.isRational()) {
        return std::to_string(m.getNumerator()) + "/" + std::to_string(m.getDenominator());
    }
    auto const cents = kCentsPerOctave * std::log2(static_cast<double>(m.getFrequencyValue()));
    return formatFixed(cents, 1) + "\xC2\xA2"; // U+00A2 CENT SIGN
}

std::string defaultFileName(const std::string& designName, const std::string& parameters)
{
    auto const raw = oneLine(designName + " " + parameters);
    std::string stem;
    for (char c : raw) {
        auto const ch = static_cast<unsigned char>(c);
        auto const ok = std::isalnum(ch) || ch == '-' || ch == '.' || ch == '=';
        if (ok) {
            stem += static_cast<char>(ch);
        } else if (!stem.empty() && stem.back() != '_') {
            stem += '_';
        }
    }
    while (!stem.empty() && (stem.back() == '_' || stem.back() == '.')) {
        stem.pop_back();
    }
    if (stem.size() > kMaxFileNameStem) {
        stem.resize(kMaxFileNameStem);
    }
    if (stem.empty()) {
        stem = "wilsonic";
    }
    return stem + ".ascl";
}

std::string makeAscl(Tuning& tuning, const AsclOptions& options, std::vector<std::string>& warnings)
{
    auto fail = [&warnings](const std::string& why) {
        warnings.push_back("ERROR: " + why);
        return std::string {};
    };

    // ---- inputs (TuningImp::_update's) -----------------------------------
    auto degrees = tuning.getProcessedArrayNPO();
    auto const n = degrees.count();
    if (n == 0) {
        return fail("the tuning has no notes (N == 0)");
    }
    auto const period = static_cast<double>(tuning.getOctave());
    if (!(period > 1.0) || !std::isfinite(period)) {
        return fail("the period must be greater than 1 (got " + formatFixed(period, 6) + ")");
    }
    std::vector<double> v(n);
    for (unsigned long i = 0; i < n; ++i) {
        v[i] = static_cast<double>(degrees.microtoneAtIndex(i)->getFrequencyValue());
        if (!(v[i] > 0.0) || !std::isfinite(v[i])) {
            return fail("degree " + std::to_string(i) + " has a non-positive or non-finite value");
        }
    }
    auto const mc = static_cast<int>(tuning.getNoteNumberMiddleC());
    auto const fMC = static_cast<double>(tuning.getFrequencyMiddleC());
    auto const oMC = tuning.getOctaveMiddleC();

    // ---- degree checks (export, but warn) ---------------------------------
    bool ascending = true, duplicates = false, outsidePeriod = false;
    for (unsigned long i = 0; i < n; ++i) {
        if (i > 0 && v[i] < v[i - 1]) ascending = false;
        for (unsigned long j = 0; j < i; ++j) {
            if (sameValue(v[i], v[j])) duplicates = true;
        }
        if (v[i] < v[0] || v[i] >= v[0] * period) outsidePeriod = true;
    }
    if (!ascending) warnings.push_back("degrees are not in ascending order; Live's handling of an unsorted degree list is untested");
    if (duplicates) warnings.push_back("two or more degrees have the same value");
    if (outsidePeriod) warnings.push_back("a degree falls outside [degree 0, degree 0 * period); Live's handling is untested");

    // ---- Wilsonic's frequency per key, integer arithmetic -------------------
    std::vector<double> fW(static_cast<std::size_t>(kNumKeys));
    std::vector<KeyMapping> map(static_cast<std::size_t>(kNumKeys));
    auto const octaveFactor = std::pow(period, static_cast<double>(oMC));
    int mismatches = 0, outOfRange = 0, filtered = 0;
    for (int k = 0; k < kNumKeys; ++k) {
        auto const km = keyMapping(k, mc, n);
        map[static_cast<std::size_t>(k)] = km;
        auto const f = v[km.degree] * std::pow(period, static_cast<double>(km.period)) * fMC * octaveFactor;
        fW[static_cast<std::size_t>(k)] = f;
        auto const table = static_cast<double>(tuning.getTuningTableFrequency(static_cast<unsigned long>(k)));
        if (table > 0.0 && std::fabs(centsBetween(table, f)) > kTableMatchToleranceCents) {
            ++mismatches;
        }
        if (table < liveMinHz || table > liveMaxHz) {
            ++outOfRange;
        }
        auto const tone = tuning.microtoneAtNoteNumber(static_cast<unsigned long>(k));
        if (tone != nullptr && tone->getFilterNote()) {
            ++filtered;
        }
    }
    jassert(mismatches == 0);
    if (mismatches > 0) warnings.push_back("internal: " + std::to_string(mismatches) + " keys where the export formula disagrees with Wilsonic's tuning table");
    if (outOfRange > 0) warnings.push_back(std::to_string(outOfRange) + " keys fall outside Live's playable range of 4 Hz to 21000 Hz and will be silent in Live");
    if (filtered > 0) warnings.push_back(std::to_string(filtered) + " notes are filtered in Wilsonic; the .ascl format cannot express per-key filtering, so Live will play them");

    // ---- octave labels ------------------------------------------------------
    auto const rMin = map.front().period;
    auto const rMax = map.back().period;
    int base = defaultBaseOctave;
    if (base + rMin < liveMinOctave) {
        base = liveMinOctave - rMin;
    } else if (base + rMax > liveMaxOctave) {
        base = liveMaxOctave - rMax;
    }
    if (base != defaultBaseOctave) {
        warnings.push_back("octave labels shifted so middle C reads as octave " + std::to_string(base) + " instead of 3 (Live allows octaves -99..99)");
    }
    auto octaveOf = [&](int key) { return base + map[static_cast<std::size_t>(key)].period; };

    // ---- reference key -------------------------------------------------------
    int kr = mc;
    if (octaveOf(kr) < referenceOctaveMin || octaveOf(kr) > referenceOctaveMax) {
        for (int step = 1; step < kNumKeys; ++step) {
            auto const lo = mc - step, hi = mc + step;
            if (hi < kNumKeys && octaveOf(hi) >= referenceOctaveMin && octaveOf(hi) <= referenceOctaveMax) { kr = hi; break; }
            if (lo >= 0 && octaveOf(lo) >= referenceOctaveMin && octaveOf(lo) <= referenceOctaveMax) { kr = lo; break; }
        }
    }
    auto const fRef = static_cast<double>(tuning.getTuningTableFrequency(static_cast<unsigned long>(kr)));
    // 6 decimals, plus one per leading zero for the tiny reference frequencies
    // a 1- or 2-note scale can force (key 107 of a 1-note scale with middle C
    // on key 127 is 2^-20 * 261 Hz), so at least 6 significant digits survive
    auto const refDecimals = fRef >= 1.0 ? 6 : 6 + static_cast<int>(std::ceil(-std::log10(std::max(fRef, 1e-30))));

    // ---- names -----------------------------------------------------------------
    std::vector<std::string> names(n);
    for (unsigned long i = 0; i < n; ++i) {
        names[i] = sanitizeName(degreeName(*degrees.microtoneAtIndex(i)));
    }
    std::vector<std::string> noteNames = names;
    bool rotated = false;
    if (static_cast<int>(n) == liveTwelveNoteQuirkN) {
        // Live labels key k with names[k mod 12]; Wilsonic puts degree (k - mc) mod 12 there.
        for (int j = 0; j < liveTwelveNoteQuirkN; ++j) {
            noteNames[static_cast<std::size_t>(j)] = names[keyMapping(j, mc, n).degree];
        }
        rotated = (mc % liveTwelveNoteQuirkN) != 0;
        if (rotated) {
            warnings.push_back("12-note tuning with middle C on key " + std::to_string(mc) + ": NOTE_NAMES rotated so Live's piano roll labels land on the right keys; Live's tuning list will show the names in rotated order");
        }
    }

    // ---- text -------------------------------------------------------------------
    auto const designName = oneLine(options.designName.empty() ? tuning.getTuningName() : options.designName);
    auto const parameters = tuning.getParameterDescription();
    auto const summary = oneLine(designName + " " + oneLine(parameters));
    auto const version = oneLine(options.appVersion);

    std::string out;
    out += "! " + oneLine(options.fileName) + kLF;
    out += "! exported " + oneLine(options.exportDate) + " by Wilsonic MTS-ESP " + version + kLF;
    out += "! design: " + designName + kLF;
    {
        std::istringstream in(parameters);
        std::string line;
        bool first = true;
        while (std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            out += std::string("! ") + (first ? "parameters: " : "            ") + line + kLF;
            first = false;
        }
        if (first) out += "! parameters:" + std::string(1, kLF);
    }
    for (unsigned long i = 0; i < n; ++i) {
        auto tone = degrees.microtoneAtIndex(i);
        auto const value = tone->isRational()
            ? std::to_string(tone->getNumerator()) + "/" + std::to_string(tone->getDenominator())
            : formatFixed(v[i], 6);
        out += "! " + std::to_string(i) + " " + names[i] + " " + value + " " + formatFixed(centsBetween(v[0], v[i]), 3) + " cents" + kLF;
    }
    out += "!" + std::string(1, kLF);
    out += "Wilsonic " + summary + kLF; // description: Live shows it as Info Text
    out += "!" + std::string(1, kLF);
    out += std::to_string(n) + kLF;
    out += "!" + std::string(1, kLF);
    for (unsigned long i = 1; i < n; ++i) {
        auto const r = ratioOver(*degrees.microtoneAtIndex(i), *degrees.microtoneAtIndex(0));
        out += (r.valid ? ratioText(r) : formatFixed(centsBetween(v[0], v[i]), 6)) + kLF;
    }
    {
        auto const r = periodRatio(period);
        out += (r.valid ? ratioText(r) : formatFixed(kCentsPerOctave * std::log2(period), 6)) + kLF;
    }
    out += "!" + std::string(1, kLF);
    if (rotated) {
        out += "! NOTE_NAMES are rotated: Live labels a 12-note tuning from key 0 by (key mod 12)" + std::string(1, kLF);
    }
    out += "! @ABL NOTE_NAMES";
    for (auto const& name : noteNames) {
        out += " " + quotedName(name);
    }
    out += kLF;
    out += "! @ABL REFERENCE_PITCH " + std::to_string(octaveOf(kr)) + " " + std::to_string(map[static_cast<std::size_t>(kr)].degree) + " " + formatFixed(fRef, refDecimals) + kLF;
    out += "! @ABL NOTE_RANGE_BY_INDEX " + std::to_string(octaveOf(0)) + " " + std::to_string(map.front().degree)
         + " " + std::to_string(octaveOf(kNumKeys - 1)) + " " + std::to_string(map.back().degree) + kLF;
    out += "! @ABL SOURCE Wilsonic MTS-ESP " + version + ": " + summary + kLF;
    if (!options.linkUrl.empty()) {
        out += "! @ABL LINK " + oneLine(options.linkUrl) + kLF;
    }
    if (options.includeScaleDirectives) {
        // Inferred from Live's own exporter, not observed in the binary: root name, scale name, root index.
        out += "! @ABL SCALE " + quotedName(noteNames.front()) + " " + quotedName(designName) + " 0" + kLF;
        out += "! @ABL SCALE_PITCHES";
        for (unsigned long i = 0; i < n; ++i) out += " i";
        out += kLF;
    }
    return out;
}

} // namespace AbletonAscl
