// Ableton Live .ascl export tests.
//
// A small reader applies the Live 12 rules described in AbletonAscl.h (key
// mapping from NOTE_RANGE_BY_INDEX, the REFERENCE_PITCH formula with float32
// cents, label = name + octave, the 12-note quirk). The reader is checked
// first against Ableton's own 11-EDO and 22-EDO fixtures, then every export
// is replayed through it and must land on Wilsonic's tuning table for all
// 128 keys within 0.01 cents.

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "../Source/AbletonAscl.h"
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

#define CHECK_MSG(cond, msg)                                               \
    do {                                                                   \
        ++checks;                                                          \
        if (!(cond)) {                                                     \
            ++failures;                                                    \
            std::printf("FAIL %s:%d: %s [%s]\n", __FILE__, __LINE__, #cond, \
                        std::string(msg).c_str());                         \
        }                                                                  \
    } while (0)

// ---------------------------------------------------------------------------
// Live-rules reader
// ---------------------------------------------------------------------------

struct LiveTuning
{
    std::string description;
    int n = 0;
    std::vector<float> cents;        // cents[0] = 0, cents[1..n-1], cents[n] = pseudo-octave (float32, as Live stores them)
    std::vector<std::string> names;  // NOTE_NAMES, degree 0 first
    bool hasRef = false;
    int refOct = 0, refIdx = 0;
    double refHz = 0.0;
    bool hasRange = false, hasMax = false;
    int minOct = 0, minIdx = 0, maxOct = 0, maxIdx = 0;
    std::string source, link;
    std::vector<std::string> errors;
};

std::string trim(const std::string& s)
{
    auto const a = s.find_first_not_of(" \t");
    if (a == std::string::npos) return "";
    auto const b = s.find_last_not_of(" \t");
    return s.substr(a, b - a + 1);
}

// Live's argument splitting: spaces separate, double quotes group, no escapes.
std::vector<std::string> splitArgs(const std::string& s, std::vector<std::string>& errors)
{
    std::vector<std::string> out;
    std::size_t i = 0;
    while (i < s.size()) {
        if (s[i] == ' ') { ++i; continue; }
        if (s[i] == '"') {
            auto const end = s.find('"', i + 1);
            if (end == std::string::npos) { errors.push_back("unterminated quote: " + s); return out; }
            out.push_back(s.substr(i + 1, end - i - 1));
            i = end + 1;
        } else {
            auto end = s.find(' ', i);
            if (end == std::string::npos) end = s.size();
            out.push_back(s.substr(i, end - i));
            i = end;
        }
    }
    return out;
}

bool parsePitch(const std::string& raw, double& centsOut, std::string& error)
{
    auto const line = trim(raw);
    std::istringstream in(line);
    std::string token;
    in >> token;
    if (token.find('.') != std::string::npos) {
        centsOut = std::strtod(token.c_str(), nullptr);
        return true;
    }
    auto const slash = token.find('/');
    if (slash == std::string::npos) {
        error = "pitch line is a bare integer (Live needs p/q or a cents value with '.'): " + line;
        return false;
    }
    auto const p = std::strtoll(token.substr(0, slash).c_str(), nullptr, 10);
    auto const q = std::strtoll(token.substr(slash + 1).c_str(), nullptr, 10);
    if (p <= 0 || q <= 0) { error = "bad ratio: " + line; return false; }
    centsOut = 1200.0 * std::log2(static_cast<double>(p) / static_cast<double>(q));
    return true;
}

LiveTuning parseAscl(const std::string& text)
{
    LiveTuning t;
    if (text.find('\r') != std::string::npos) t.errors.push_back("CR found: file must use LF line endings");
    if (text.size() >= 3 && static_cast<unsigned char>(text[0]) == 0xEF) t.errors.push_back("UTF-8 BOM present");

    std::vector<std::string> lines;
    {
        std::istringstream in(text);
        std::string line;
        while (std::getline(in, line)) lines.push_back(line);
    }
    int bodyIndex = 0; // 0 = description, 1 = N, then pitches
    int pitchesSeen = 0;
    bool seenNames = false, seenRef = false, seenRange = false, seenSource = false, seenLink = false;
    t.cents.push_back(0.f);
    for (auto const& line : lines) {
        if (line.rfind("! @ABL ", 0) == 0) {
            auto const rest = line.substr(7);
            auto const sp = rest.find(' ');
            auto const keyword = rest.substr(0, sp);
            auto const argText = sp == std::string::npos ? "" : rest.substr(sp + 1);
            if (keyword == "NOTE_NAMES") {
                if (seenNames) t.errors.push_back("NOTE_NAMES more than once");
                seenNames = true;
                t.names = splitArgs(argText, t.errors);
                if (static_cast<int>(t.names.size()) != t.n) t.errors.push_back("NOTE_NAMES count " + std::to_string(t.names.size()) + " != N " + std::to_string(t.n));
            } else if (keyword == "REFERENCE_PITCH") {
                if (seenRef) t.errors.push_back("REFERENCE_PITCH more than once");
                seenRef = true;
                auto args = splitArgs(argText, t.errors);
                if (args.size() != 3) { t.errors.push_back("REFERENCE_PITCH needs 3 args"); continue; }
                t.hasRef = true;
                t.refOct = std::atoi(args[0].c_str());
                t.refIdx = std::atoi(args[1].c_str());
                t.refHz = std::strtod(args[2].c_str(), nullptr);
                if (t.refOct < -99 || t.refOct > 99) t.errors.push_back("REFERENCE_PITCH octave out of -99..99");
                if (t.refIdx < 0 || t.refIdx >= t.n) t.errors.push_back("REFERENCE_PITCH degree out of 0..N-1");
            } else if (keyword == "NOTE_RANGE_BY_INDEX") {
                if (seenRange) t.errors.push_back("more than one NOTE_RANGE_*");
                seenRange = true;
                if (!t.hasRef) t.errors.push_back("NOTE_RANGE_BY_INDEX before REFERENCE_PITCH");
                auto args = splitArgs(argText, t.errors);
                if (args.size() != 2 && args.size() != 4) { t.errors.push_back("NOTE_RANGE_BY_INDEX needs 2 or 4 args"); continue; }
                t.hasRange = true;
                t.minOct = std::atoi(args[0].c_str());
                t.minIdx = std::atoi(args[1].c_str());
                if (args.size() == 4) {
                    t.hasMax = true;
                    t.maxOct = std::atoi(args[2].c_str());
                    t.maxIdx = std::atoi(args[3].c_str());
                }
                for (auto o : {t.minOct, t.maxOct}) if (o < -99 || o > 99) t.errors.push_back("NOTE_RANGE octave out of -99..99");
                if (t.minIdx < 0 || t.minIdx >= t.n || (t.hasMax && (t.maxIdx < 0 || t.maxIdx >= t.n))) t.errors.push_back("NOTE_RANGE degree out of range");
            } else if (keyword == "NOTE_RANGE_BY_FREQUENCY") {
                if (seenRange) t.errors.push_back("more than one NOTE_RANGE_*");
                seenRange = true;
            } else if (keyword == "SOURCE") {
                if (seenSource) t.errors.push_back("SOURCE more than once");
                seenSource = true;
                t.source = argText;
            } else if (keyword == "LINK") {
                if (seenLink) t.errors.push_back("LINK more than once");
                seenLink = true;
                t.link = argText;
            } else if (keyword == "SCALE" || keyword == "SCALE_PITCHES" || keyword == "SCALE_NOTE_NAMES") {
                // parsed by Live, no effect for non-12 tunings in 12.4.6
            } else {
                t.errors.push_back("unknown directive " + keyword);
            }
            continue;
        }
        if (!line.empty() && line[0] == '!') continue; // comment
        if (bodyIndex == 0) {
            t.description = line;
            bodyIndex = 1;
        } else if (bodyIndex == 1) {
            t.n = std::atoi(trim(line).c_str());
            if (t.n <= 0) t.errors.push_back("bad N: " + line);
            bodyIndex = 2;
        } else {
            double c = 0.0;
            std::string err;
            if (!parsePitch(line, c, err)) { t.errors.push_back(err); continue; }
            t.cents.push_back(static_cast<float>(c));
            ++pitchesSeen;
        }
    }
    if (pitchesSeen != t.n) t.errors.push_back("expected " + std::to_string(t.n) + " pitch lines, got " + std::to_string(pitchesSeen));
    if (t.n > 1 && t.cents.size() > 1 && t.cents.back() <= 0.f) t.errors.push_back("descending pseudo-octave");
    return t;
}

struct LiveNote { int oct; int idx; };

LiveNote liveKeyToNote(const LiveTuning& t, int key)
{
    auto const total = t.minIdx + key;
    auto const oct = t.minOct + static_cast<int>(std::floor(static_cast<double>(total) / t.n));
    auto const idx = ((total % t.n) + t.n) % t.n;
    return {oct, idx};
}

double liveFrequency(const LiveTuning& t, LiveNote note)
{
    auto const pc = static_cast<double>(t.cents[static_cast<std::size_t>(t.n)]);
    auto const c = static_cast<double>(t.cents[static_cast<std::size_t>(note.idx)]);
    auto const cRef = static_cast<double>(t.cents[static_cast<std::size_t>(t.refIdx)]);
    return t.refHz * std::pow(2.0, (pc * (note.oct - t.refOct) + c - cRef) / 1200.0);
}

std::string liveLabel(const LiveTuning& t, int key)
{
    if (t.n == 12) {
        return t.names[static_cast<std::size_t>(key % 12)] + std::to_string(key / 12 - 2);
    }
    auto const note = liveKeyToNote(t, key);
    return t.names[static_cast<std::size_t>(note.idx)] + std::to_string(note.oct);
}

double centsApart(double a, double b)
{
    return std::fabs(1200.0 * std::log2(a / b));
}

bool hasWarning(const std::vector<std::string>& warnings, const std::string& needle)
{
    for (auto const& w : warnings) if (w.find(needle) != std::string::npos) return true;
    return false;
}

// ---------------------------------------------------------------------------
// Fixtures from Ableton's own files
// ---------------------------------------------------------------------------

std::string edoFixture(int n, const std::string& directives)
{
    std::string s = "! fixture\n" + std::to_string(n) + "-EDO\n" + std::to_string(n) + "\n";
    for (int i = 1; i < n; ++i) {
        char buf[64];
        std::snprintf(buf, sizeof buf, "%.7f\n", 1200.0 * i / n);
        s += buf;
    }
    s += "2/1\n";
    s += directives;
    return s;
}

void testReader11Edo()
{
    auto const text = edoFixture(11,
        "! @ABL NOTE_NAMES \"0\\11 \" \"1\\11 \" \"2\\11 \" \"3\\11 \" \"4\\11 \" \"5\\11 \" \"6\\11 \" \"7\\11 \" \"8\\11 \" \"9\\11 \" \"10\\11 \"\n"
        "! @ABL REFERENCE_PITCH 3 8 440.0\n"
        "! @ABL NOTE_RANGE_BY_INDEX -3 5 9 0\n");
    auto t = parseAscl(text);
    CHECK_MSG(t.errors.empty(), t.errors.empty() ? "" : t.errors.front());
    CHECK(t.n == 11);
    auto const k0 = liveKeyToNote(t, 0);
    CHECK(k0.oct == -3 && k0.idx == 5);
    auto const k127 = liveKeyToNote(t, 127);
    CHECK(k127.oct == 9 && k127.idx == 0);
    auto const k69 = liveKeyToNote(t, 69);
    CHECK(k69.oct == 3 && k69.idx == 8);
    CHECK(std::fabs(liveFrequency(t, k69) - 440.0) < 1e-6);
    CHECK(centsApart(liveFrequency(t, liveKeyToNote(t, 70)), 440.0 * std::pow(2.0, 1.0 / 11.0)) < 1e-4);
    CHECK(t.names.size() == 11);
    CHECK(t.names[3] == "3\\11 ");  // literal backslash, trailing space kept
    CHECK(liveLabel(t, 69) == "8\\11 3");
}

void testReader22Edo()
{
    auto const text = edoFixture(22,
        "! @ABL REFERENCE_PITCH 3 17 440.0\n"
        "! @ABL NOTE_RANGE_BY_INDEX 0 14 6 9\n");
    auto t = parseAscl(text);
    CHECK_MSG(t.errors.empty(), t.errors.empty() ? "" : t.errors.front());
    auto const k0 = liveKeyToNote(t, 0);
    CHECK(k0.oct == 0 && k0.idx == 14);
    auto const k69 = liveKeyToNote(t, 69);
    CHECK(k69.oct == 3 && k69.idx == 17);
    CHECK(std::fabs(liveFrequency(t, k69) - 440.0) < 1e-6);
    auto const k127 = liveKeyToNote(t, 127);
    CHECK(k127.oct == 6 && k127.idx == 9);
}

void testReaderRejections()
{
    auto bare = parseAscl("desc\n2\n3\n2/1\n");
    CHECK(!bare.errors.empty()); // bare "3" is not a ratio line
    auto crlf = parseAscl("desc\r\n1\r\n2/1\r\n");
    CHECK(!crlf.errors.empty());
    auto rangeFirst = parseAscl("desc\n1\n2/1\n! @ABL NOTE_RANGE_BY_INDEX 0 0\n! @ABL REFERENCE_PITCH 3 0 440.0\n");
    CHECK(!rangeFirst.errors.empty());
    auto badCount = parseAscl("desc\n2\n3/2\n2/1\n! @ABL NOTE_NAMES \"a \"\n");
    CHECK(!badCount.errors.empty());
}

// ---------------------------------------------------------------------------
// Export round trips
// ---------------------------------------------------------------------------

AsclOptions options(const std::string& design)
{
    AsclOptions o;
    o.fileName = "test.ascl";
    o.exportDate = "2026-10-18";
    o.designName = design;
    o.appVersion = "vTEST";
    return o;
}

// Export, parse, and replay every key through Live's rules.
LiveTuning roundTrip(Tuning& tuning, const AsclOptions& o, std::vector<std::string>& warnings, const std::string& label)
{
    auto const text = AbletonAscl::makeAscl(tuning, o, warnings);
    CHECK_MSG(!text.empty(), label + ": export refused: " + (warnings.empty() ? "" : warnings.front()));
    auto t = parseAscl(text);
    CHECK_MSG(t.errors.empty(), label + ": " + (t.errors.empty() ? "" : t.errors.front()));
    if (text.empty() || !t.errors.empty()) return t;
    CHECK_MSG(t.hasRef && t.hasRange && t.hasMax, label + ": REFERENCE_PITCH / NOTE_RANGE_BY_INDEX missing");
    int skipped = 0;
    double worst = 0.0;
    for (int k = 0; k < 128; ++k) {
        auto const fW = static_cast<double>(tuning.getTuningTableFrequency(static_cast<unsigned long>(k)));
        if (fW < AbletonAscl::liveMinHz || fW > AbletonAscl::liveMaxHz) { ++skipped; continue; }
        auto const fL = liveFrequency(t, liveKeyToNote(t, k));
        worst = std::max(worst, centsApart(fL, fW));
        // the label is the degree's name, a space, then the octave number
        auto tone = tuning.microtoneAtNoteNumber(static_cast<unsigned long>(k));
        auto const expectedName = AbletonAscl::sanitizeName(AbletonAscl::degreeName(*tone)) + " ";
        auto const lbl = liveLabel(t, k);
        CHECK_MSG(lbl.rfind(expectedName, 0) == 0, label + ": key " + std::to_string(k) + " label '" + lbl + "' expected name '" + expectedName + "'");
    }
    CHECK_MSG(worst < 0.01, label + ": worst key error " + std::to_string(worst) + " cents");
    if (skipped > 0) CHECK_MSG(hasWarning(warnings, "21000 Hz"), label + ": keys outside 4 Hz-21 kHz but no warning");
    // the exported range is exactly the 128 keys
    auto const last = liveKeyToNote(t, 127);
    CHECK_MSG(last.oct == t.maxOct && last.idx == t.maxIdx, label + ": NOTE_RANGE max is not key 127");
    return t;
}

MicrotoneArray edoArray(int n)
{
    MicrotoneArray ma;
    for (int i = 0; i < n; ++i) {
        auto m = std::make_shared<Microtone>(static_cast<float>(i) / static_cast<float>(n), std::to_string(i), Microtone::Space::LogPeriod, 2.f);
        m->setDegreeName(std::to_string(i) + "\\" + std::to_string(n));
        ma.addMicrotone(m);
    }
    return ma;
}

void testTwelveEdoRotation()
{
    for (auto mc : {60UL, 61UL, 57UL}) {
        TuningImp t;
        t.setMicrotoneArray(edoArray(12));
        t.setNoteNumberMiddleC(mc);
        std::vector<std::string> w;
        auto live = roundTrip(t, options("ET"), w, "12-EDO mc=" + std::to_string(mc));
        // names[k mod 12] must be the degree Wilsonic puts on key k
        for (int k = 0; k < 128; ++k) {
            auto const expected = AbletonAscl::degreeName(*t.microtoneAtNoteNumber(static_cast<unsigned long>(k))) + " ";
            CHECK_MSG(live.names[static_cast<std::size_t>(k % 12)] == expected, "12-EDO mc=" + std::to_string(mc) + " key " + std::to_string(k));
        }
        CHECK(hasWarning(w, "rotated") == (mc % 12 != 0));
    }
}

// A rational CPS-style tuning: products of lettered seeds, octave-reduced and sorted.
struct NamedSeed { unsigned long value; std::string letter; };

MicrotoneArray cpsArray(const std::vector<NamedSeed>& seeds, int k)
{
    MicrotoneArray ma;
    auto const n = static_cast<int>(seeds.size());
    // all k-combinations by bitmask
    for (int mask = 0; mask < (1 << n); ++mask) {
        if (__builtin_popcount(static_cast<unsigned>(mask)) != k) continue;
        auto product = std::make_shared<Microtone>(1UL, 1UL);
        std::string name;
        for (int i = 0; i < n; ++i) {
            if (!(mask & (1 << i))) continue;
            product = product->multiply(std::make_shared<Microtone>(seeds[static_cast<std::size_t>(i)].value, 1UL));
            name += seeds[static_cast<std::size_t>(i)].letter;
        }
        product->setDegreeName(name);
        ma.addMicrotone(product);
    }
    return ma;
}

class HexanyForGolden : public TuningImp
{
public:
    const std::string getParameterDescription() override { return "A=1 B=3 C=5 D=7"; }
};

void testHexanyGolden()
{
    HexanyForGolden t;
    t.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}}, 2));
    CHECK(t.getProcessedArrayCount() == 6UL);
    // degree 0 is 35/32, not 1/1
    CHECK(t.getProcessedArrayNPO().microtoneAtIndex(0)->getNumerator() == 35UL);
    std::vector<std::string> w;
    auto o = options("CPS 4_2 hexany");
    o.fileName = "Wilsonic CPS 4_2 A=1 B=3 C=5 D=7.ascl";
    o.appVersion = "v0.44.0";
    roundTrip(t, o, w, "hexany");
    // a 6-note scale spans 21 periods over 128 keys, so most keys are outside
    // Live's 4 Hz-21 kHz window; that is the only warning expected
    CHECK_MSG(w.size() == 1 && hasWarning(w, "21000 Hz"), w.empty() ? "no warning" : w.front());

    auto const text = AbletonAscl::makeAscl(t, o, w);
    auto const fRef = AbletonAscl::formatFixed(static_cast<double>(t.getTuningTableFrequency(60)), 6);
    CHECK(std::fabs(static_cast<double>(t.getTuningTableFrequency(60)) - 286.152962) < 0.001);
    std::string expected =
        "! Wilsonic CPS 4_2 A=1 B=3 C=5 D=7.ascl\n"
        "! exported 2026-10-18 by Wilsonic MTS-ESP v0.44.0\n"
        "! design: CPS 4_2 hexany\n"
        "! parameters: A=1 B=3 C=5 D=7\n"
        "! 0 CD 35/32 0.000 cents\n"
        "! 1 AC 5/4 231.174 cents\n"
        "! 2 BD 21/16 315.641 cents\n"
        "! 3 AB 3/2 546.815 cents\n"
        "! 4 AD 7/4 813.686 cents\n"
        "! 5 BC 15/8 933.129 cents\n"
        "!\n"
        "Wilsonic CPS 4_2 hexany A=1 B=3 C=5 D=7\n"
        "!\n"
        "6\n"
        "!\n"
        "8/7\n"
        "6/5\n"
        "48/35\n"
        "8/5\n"
        "12/7\n"
        "2/1\n"
        "!\n"
        "! @ABL NOTE_NAMES \"CD \" \"AC \" \"BD \" \"AB \" \"AD \" \"BC \"\n"
        "! @ABL REFERENCE_PITCH 3 0 " + fRef + "\n"
        "! @ABL NOTE_RANGE_BY_INDEX -7 0 14 1\n"
        "! @ABL SOURCE Wilsonic MTS-ESP v0.44.0: CPS 4_2 hexany A=1 B=3 C=5 D=7\n";
    CHECK_MSG(text == expected, "hexany golden mismatch:\n--- got ---\n" + text + "--- expected ---\n" + expected);
}

void testEikosanyNames()
{
    TuningImp t;
    t.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}, {9, "E"}, {11, "F"}}, 3));
    CHECK(t.getProcessedArrayCount() == 20UL);
    std::vector<std::string> w;
    auto live = roundTrip(t, options("CPS 6_3 eikosany"), w, "eikosany");
    std::vector<std::string> names = live.names;
    std::sort(names.begin(), names.end());
    names.erase(std::unique(names.begin(), names.end()), names.end());
    CHECK(names.size() == 20UL);
    CHECK(names.front() == "ABC ");
    CHECK(names.back() == "DEF ");
}

void testBrunMos()
{
    Brun b;
    b.setGenerator(0.5849625f); // log2(3/2)
    b.setLevel(4UL);            // 7-tone MOS
    CHECK(b.getProcessedArrayCount() == 7UL);
    std::vector<std::string> w;
    auto live = roundTrip(b, options("MOS"), w, "MOS 7");
    for (int i = 0; i < 7; ++i) CHECK(live.names[static_cast<std::size_t>(i)] == std::to_string(i) + " ");
    // tonic is degree 0 and sits on middle C
    CHECK(liveLabel(live, 60) == "0 3");
}

void testMiddleCExtremes()
{
    for (auto mc : {0UL, 127UL}) {
        TuningImp t;
        t.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}}, 2));
        t.setNoteNumberMiddleC(mc);
        std::vector<std::string> w;
        auto live = roundTrip(t, options("CPS"), w, "hexany mc=" + std::to_string(mc));
        CHECK(live.refOct >= -2 && live.refOct <= 8);
    }
}

void testTinyScalesShiftOctaves()
{
    // N = 1 with middle C at key 0 overflows Wilsonic's float32 tuning table
    // (2^127 * 261 Hz > FLT_MAX; TuningTableImp asserts on inf) before the
    // exporter ever runs, so the low extreme used here is key 20, which still
    // needs more than 99 octaves of labels above middle C.
    for (auto n : {1, 2}) {
        for (auto mc : {20UL, 60UL, 127UL}) {
            TuningImp t;
            MicrotoneArray ma;
            ma.addMicrotone(std::make_shared<Microtone>(1UL, 1UL));
            if (n == 2) ma.addMicrotone(std::make_shared<Microtone>(3UL, 2UL));
            t.setMicrotoneArray(ma);
            t.setNoteNumberMiddleC(mc);
            std::vector<std::string> w;
            auto const label = "N=" + std::to_string(n) + " mc=" + std::to_string(mc);
            auto live = roundTrip(t, options("tiny"), w, label);
            CHECK_MSG(live.minOct >= -99 && live.maxOct <= 99, label);
            CHECK_MSG(live.refOct >= -2 && live.refOct <= 8, label);
            // N=1 with middle C at either end needs more than 99 octaves of room
            auto const needsShift = (n == 1 && mc != 60UL);
            CHECK_MSG(hasWarning(w, "shifted") == needsShift, label + " shift warning");
            // a 1-note scale spans 128 periods: most keys are outside 4 Hz-21 kHz
            if (n == 1) CHECK_MSG(hasWarning(w, "21000 Hz"), label);
        }
    }
}

void testNpoOverride()
{
    for (auto npo : {5, 20}) {
        TuningImp t;
        t.setCanNPOOverride(true);
        t.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}}, 2));
        t.setNPOOverride(npo);
        t.setNPOOverrideEnable(true);
        CHECK(t.getProcessedArrayNPOCount() == static_cast<unsigned long>(npo));
        std::vector<std::string> w;
        auto live = roundTrip(t, options("CPS"), w, "NPO " + std::to_string(npo));
        CHECK(live.n == npo);
        if (npo == 20) {
            // repeated degrees keep the source name, and repeats are flagged
            CHECK(live.names[0] == live.names[1] || live.names[0] == live.names[2]);
            CHECK(hasWarning(w, "same value"));
        }
    }
}

void testOctaveReduceOff()
{
    TuningImp t;
    t.setOctaveReduce(false);
    t.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}}, 2)); // 3, 5, 7, 15, 21, 35
    std::vector<std::string> w;
    roundTrip(t, options("CPS"), w, "octave reduce off");
    CHECK(hasWarning(w, "outside"));
}

void testSortOff()
{
    TuningImp t;
    t.setSort(false);
    MicrotoneArray ma;
    for (auto r : std::vector<std::pair<unsigned long, unsigned long>> {{1, 1}, {7, 4}, {5, 4}, {3, 2}}) {
        ma.addMicrotone(std::make_shared<Microtone>(r.first, r.second));
    }
    t.setMicrotoneArray(ma);
    std::vector<std::string> w;
    auto live = roundTrip(t, options("unsorted"), w, "sort off");
    CHECK(hasWarning(w, "ascending"));
    // listed order is preserved: degree 1 is 7/4, degree 2 is 5/4
    CHECK(live.cents.size() == 5 && live.cents[1] > live.cents[2]);
    CHECK(live.names.size() == 4 && live.names[1] == "7/4 ");
}

void testPeriodThree()
{
    TuningImp t;
    t.setOctave(3.f);
    MicrotoneArray ma;
    for (auto r : std::vector<std::pair<unsigned long, unsigned long>> {{1, 1}, {5, 3}, {7, 3}, {9, 3}, {11, 3}}) {
        ma.addMicrotone(std::make_shared<Microtone>(r.first, r.second, "", Microtone::Space::Linear, 3.f));
    }
    t.setMicrotoneArray(ma);
    std::vector<std::string> w;
    auto const text = AbletonAscl::makeAscl(t, options("BP"), w);
    CHECK(text.find("\n3/1\n") != std::string::npos);
    roundTrip(t, options("BP"), w, "period 3/1");
}

void testQuoteInName()
{
    TuningImp t;
    MicrotoneArray ma;
    auto a = std::make_shared<Microtone>(1UL, 1UL);
    a->setDegreeName("say \"hi\"");
    ma.addMicrotone(a);
    ma.addMicrotone(std::make_shared<Microtone>(3UL, 2UL));
    t.setMicrotoneArray(ma);
    std::vector<std::string> w;
    auto live = roundTrip(t, options("quote"), w, "quote in name");
    CHECK(live.names.size() == 2 && live.names[0] == "say \xE2\x80\xB3hi\xE2\x80\xB3 ");
    CHECK(AbletonAscl::sanitizeName("a\"b\tc") == "a\xE2\x80\xB3" "bc");
}

void testUniquifyMergesNames()
{
    TuningImp t;
    t.setCanUniquify(true);
    t.setUniquify(true);
    MicrotoneArray ma;
    auto cSharp = std::make_shared<Microtone>(25UL, 24UL);
    cSharp->setDegreeName("C#");
    auto dFlat = std::make_shared<Microtone>(25UL, 24UL);
    dFlat->setDegreeName("Db");
    ma.addMicrotone(std::make_shared<Microtone>(1UL, 1UL));
    ma.addMicrotone(cSharp);
    ma.addMicrotone(dFlat);
    t.setMicrotoneArray(ma);
    CHECK(t.getProcessedArrayCount() == 2UL);
    CHECK(t.getProcessedArrayNPO().microtoneAtIndex(1)->getDegreeName() == "C#|Db");
}

void testFallbackNames()
{
    Microtone rational(5UL, 4UL);
    CHECK(AbletonAscl::degreeName(rational) == "5/4");
    Microtone unity(1UL, 1UL);
    CHECK(AbletonAscl::degreeName(unity) == "1/1");
    Microtone irrational(1.25f);
    CHECK(AbletonAscl::degreeName(irrational) == "386.3\xC2\xA2");
    Microtone named(1.25f);
    named.setDegreeName("AB");
    CHECK(AbletonAscl::degreeName(named) == "AB");
    CHECK(named.clone()->getDegreeName() == "AB"); // survives clone()
}

// TuningImp::_update asserts (npoOverride(0)) before it reaches its own
// N == 0 "unity" branch in a debug build, so the empty case is presented to
// the exporter through an override rather than a real empty tuning.
class EmptyTuning : public TuningImp
{
public:
    MicrotoneArray getProcessedArrayNPO() override { return MicrotoneArray(); }
    unsigned long getProcessedArrayNPOCount() override { return 0UL; }
};

void testRefusals()
{
    EmptyTuning empty;
    std::vector<std::string> w;
    auto const text = AbletonAscl::makeAscl(empty, options("empty"), w);
    CHECK(text.empty());
    CHECK(hasWarning(w, "ERROR") && hasWarning(w, "N == 0"));

    // a period of 1 (or less) cannot be exported either
    TuningImp flat;
    flat.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}}, 2));
    flat.setOctave(1.f);
    std::vector<std::string> w2;
    CHECK(AbletonAscl::makeAscl(flat, options("flat"), w2).empty());
    CHECK(hasWarning(w2, "ERROR") && hasWarning(w2, "period"));
}

void testScaleDirectivesOption()
{
    TuningImp t;
    t.setMicrotoneArray(cpsArray({{1, "A"}, {3, "B"}, {5, "C"}, {7, "D"}}, 2));
    std::vector<std::string> w;
    auto o = options("CPS");
    CHECK(AbletonAscl::makeAscl(t, o, w).find("@ABL SCALE") == std::string::npos);
    o.includeScaleDirectives = true;
    o.linkUrl = "https://example.invalid/wilsonic";
    auto const text = AbletonAscl::makeAscl(t, o, w);
    CHECK(text.find("! @ABL SCALE \"CD \" \"CPS \" 0\n") != std::string::npos);
    CHECK(text.find("! @ABL SCALE_PITCHES i i i i i i\n") != std::string::npos);
    CHECK(text.find("! @ABL LINK https://example.invalid/wilsonic\n") != std::string::npos);
    auto live = parseAscl(text);
    CHECK_MSG(live.errors.empty(), live.errors.empty() ? "" : live.errors.front());
}

void testHelpers()
{
    auto const m = AbletonAscl::keyMapping(0, 60, 6);
    CHECK(m.period == -10 && m.degree == 0UL);
    auto const m2 = AbletonAscl::keyMapping(127, 60, 6);
    CHECK(m2.period == 11 && m2.degree == 1UL);
    auto const m3 = AbletonAscl::keyMapping(59, 60, 12);
    CHECK(m3.period == -1 && m3.degree == 11UL);
    CHECK(AbletonAscl::formatFixed(286.1529623, 6) == "286.152962");
    CHECK(AbletonAscl::defaultFileName("CPS 4_2", "A=1 B=3 C=5 D=7") == "CPS_4_2_A=1_B=3_C=5_D=7.ascl");
    CHECK(AbletonAscl::defaultFileName("MOS", "G: 0.583333, L: 5, P: 2.000000, M: 0") == "MOS_G_0.583333_L_5_P_2.000000_M_0.ascl");
    CHECK(AbletonAscl::defaultFileName("", "") == "wilsonic.ascl");
}

} // namespace

int main()
{
    testReader11Edo();
    testReader22Edo();
    testReaderRejections();
    testHelpers();
    testFallbackNames();
    testUniquifyMergesNames();
    testTwelveEdoRotation();
    testHexanyGolden();
    testEikosanyNames();
    testBrunMos();
    testMiddleCExtremes();
    testTinyScalesShiftOctaves();
    testNpoOverride();
    testOctaveReduceOff();
    testSortOff();
    testPeriodThree();
    testQuoteInName();
    testRefusals();
    testScaleDirectivesOption();

    std::printf("test_ascl: %d checks, %d failures\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
