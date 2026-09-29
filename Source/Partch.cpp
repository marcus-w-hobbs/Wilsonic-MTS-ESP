/*
 ==============================================================================
 
 Partch.cpp
 Created: 27 May 2024 1:53:24pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "Partch.h"
#include "WilsonicProcessor.h"

#pragma mark - lifecycle

// __scaleNames is a static member that holds the names of all the scales represented by the Partch class.
const StringArray Partch::__scaleNames {
    "43 Tone Scale",
    "Diamond Marimba: 43 mapping",
    "Diamond Marimba",
    "Quadrangularis Reversum"
};

// all_scales is a static member that holds all the scales represented by the Partch class.
const vector<Partch::Scale> Partch::all_scales {
    Partch::Scale::Partch43,
    Partch::Scale::DiamondMarimba43,
    Partch::Scale::DiamondMarimba,
    Partch::Scale::QuadrangularisReversum
};

Partch::Partch() {
    auto pt = [&](unsigned long nn, float octave, unsigned long num, unsigned long den, float gralx, float graly, Point<float> octave_vector, bool o1, bool u1, bool o3, bool u3, bool o5, bool u5, bool o7, bool u7, bool o9, bool u9, bool o11, bool u11) -> PartchMicrotone_p {
        jassert(den > 0);
        auto const f = (static_cast<float>(num) / static_cast<float>(den)) * powf(2.f, octave)*1.5f; // 1/1 = G = 1.5*C
        string desc = to_string(num) + "/" + to_string(den);
        auto note_mt = make_shared<PartchMicrotone>(f, desc, o1, u1, o3, u3, o5, u5, o7, u7, o9, u9, o11, u11);
        jassert(note_mt != nullptr);
        
        note_mt->setMidiNoteNumber(nn);
        auto const note_point = Point<float>(gralx, graly);
        note_mt->setGralErvPoint(note_point);
        note_mt->setGralErvOctaveVector(octave_vector);
        auto const gral_erv_point_final = note_point + (octave_vector * octave);
        note_mt->setGralErvPointFinal(gral_erv_point_final);
        
        auto const hex_octave_vector = transformGral2Hex(octave_vector);
        note_mt->setHexOctaveVector(hex_octave_vector);
        auto const hex_point = transformGral2Hex(note_point);
        note_mt->setGralHexPoint(hex_point);
        auto const gral_hex_point_final = transformGral2Hex(gral_erv_point_final);
        note_mt->setGralHexPointFinal(gral_hex_point_final);
        
        return note_mt;
    };
    
    // Partch 43
    auto const po43 = Point<float>(2, 5); // octave in gral coords
    //                                                              o1     u1      o3     u3      o5     u5      o7     u7      o9     u9      o11    u11
    _partch43.addMicrotone(pt( 0, 0.f,    1,  1,    0,  0, po43,   true,  true,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt( 1, 0.f,   81, 80,   -2,  1, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt( 2, 0.f,   33, 32,    3, -1, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt( 3, 0.f,   21, 20,    1,  0, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt( 4, 0.f,   16, 15,   -1,  1, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt( 5, 0.f,   12, 11,   -3,  2, po43,  false, false,   true, false,  false, false,  false, false,  false, false,  false,  true));
    _partch43.addMicrotone(pt( 6, 0.f,   11, 10,    4, -1, po43,  false, false,  false, false,  false,  true,  false, false,  false, false,   true, false));
    _partch43.addMicrotone(pt( 7, 0.f,   10,  9,    2,  0, po43,  false, false,  false, false,   true, false,  false, false,  false,  true,  false, false));
    _partch43.addMicrotone(pt( 8, 0.f,    9,  8,    0,  1, po43,  false,  true,  false, false,  false, false,  false, false,   true, false,  false, false));
    _partch43.addMicrotone(pt( 9, 0.f,    8,  7,   -2,  2, po43,   true, false,  false, false,  false, false,  false,  true,  false, false,  false, false));
    _partch43.addMicrotone(pt(10, 0.f,    7,  6,    3,  0, po43,  false, false,  false,  true,  false, false,   true, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(11, 0.f,   32, 27,    1,  1, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(12, 0.f,    6,  5,   -1,  2, po43,  false, false,   true, false,  false,  true,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(13, 0.f,   11,  9,    4,  0, po43,  false, false,  false, false,  false, false,  false, false,  false,  true,   true, false));
    _partch43.addMicrotone(pt(14, 0.f,    5,  4,    2,  1, po43,  false,  true,  false, false,   true, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(15, 0.f,   14, 11,    0,  2, po43,  false, false,  false, false,  false, false,   true, false,  false, false,  false,  true));
    _partch43.addMicrotone(pt(16, 0.f,    9,  7,   -2,  3, po43,  false, false,  false, false,  false, false,  false,  true,   true, false,  false, false));
    _partch43.addMicrotone(pt(17, 0.f,   21, 16,    3,  1, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(18, 0.f,    4,  3,    1,  2, po43,   true, false,  false,  true,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(19, 0.f,   27, 20,   -1,  3, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(20, 0.f,   11,  8,    4,  1, po43,  false,  true,  false, false,  false, false,  false, false,  false, false,   true, false));
    _partch43.addMicrotone(pt(21, 0.f,    7,  5,    2,  2, po43,  false, false,  false, false,  false,  true,   true, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(22, 0.f,   10,  7,    0,  3, po43,  false, false,  false, false,   true, false,  false,  true,  false, false,  false, false));
    _partch43.addMicrotone(pt(23, 0.f,   16, 11,   -2,  4, po43,   true, false,  false, false,  false, false,  false, false,  false, false,  false,  true));
    _partch43.addMicrotone(pt(24, 0.f,   40, 27,    3,  2, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(25, 0.f,    3,  2,    1,  3, po43,  false,  true,   true, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(26, 0.f,   32, 21,   -1,  4, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(27, 0.f,   14,  9,    4,  2, po43,  false, false,  false, false,  false, false,   true, false,  false,  true,  false, false));
    _partch43.addMicrotone(pt(28, 0.f,   11,  7,    2,  3, po43,  false, false,  false, false,  false, false,  false,  true,  false, false,   true, false));
    _partch43.addMicrotone(pt(29, 0.f,    8,  5,    0,  4, po43,   true, false,  false, false,  false,  true,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(30, 0.f,    5,  3,    3,  3, po43,  false, false,  false,  true,   true, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(31, 0.f,   27, 16,    1,  4, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(32, 0.f,   12,  7,   -1,  5, po43,  false, false,   true, false,  false, false,  false,  true,  false, false,  false, false));
    _partch43.addMicrotone(pt(33, 0.f,    7,  4,    4,  3, po43,  false,  true,  false, false,  false, false,   true, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(34, 0.f,   16,  9,    2,  4, po43,   true, false,  false, false,  false, false,  false, false,  false,  true,  false, false));
    _partch43.addMicrotone(pt(35, 0.f,    9,  5,    0,  5, po43,  false, false,  false, false,  false,  true,  false, false,   true, false,  false, false));
    _partch43.addMicrotone(pt(36, 0.f,   18, 11,   -2,  5, po43,  false, false,  false, false,  false, false,  false, false,   true, false,  false,  true));
    _partch43.addMicrotone(pt(37, 0.f,   20, 11,   -2,  6, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false,  true));
    _partch43.addMicrotone(pt(38, 0.f,   11,  6,    5,  3, po43,  false, false,  false,  true,  false, false,  false, false,  false, false,   true, false));
    _partch43.addMicrotone(pt(39, 0.f,   15,  8,    3,  4, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(40, 0.f,   40, 21,    1,  5, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(41, 0.f,   64, 33,   -1,  6, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _partch43.addMicrotone(pt(42, 0.f,  160, 81,    4,  4, po43,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    
    // Diamond Marimba mapped to Partch 43
    // this is not the tuning...this is a subset of 128nn of Partch43 at 60nn = middle c
    auto const podm43 = Point<float>(0, 6); // octave in gral coords
    //                                                                               o1     u1      o3     u3      o5     u5      o7     u7      o9     u9      o11    u11
    _diamondMarimba43_60nn.addMicrotone(pt( 60, 0.f,   1,  1,    0,  0,   podm43,   true,  true,  false, false,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 60, 0.f,   5,  5,    0,  1,   podm43,  false, false,  false, false,   true,  true,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 60, 0.f,   3,  3,    0,  2,   podm43,  false, false,   true,  true,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 60, 0.f,   7,  7,    0,  3,   podm43,  false, false,  false, false,  false, false,   true,  true,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 60, 0.f,   9,  9,    0,  4,   podm43,  false, false,  false, false,  false, false,  false, false,   true,  true,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 60, 0.f,  11, 11,    0,  5,   podm43,  false, false,  false, false,  false, false,  false, false,  false, false,   true,  true));
    _diamondMarimba43_60nn.addMicrotone(pt( 74, 0.f,   5,  4,   -1,  1,   podm43,  false,  true,  false, false,   true, false,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 72, 0.f,   6,  5,   -1,  2,   podm43,  false, false,   true, false,  false,  true,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 70, 0.f,   7,  6,   -1,  3,   podm43,  false, false,  false,  true,  false, false,   true, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 76, 0.f,   9,  7,   -1,  4,   podm43,  false, false,  false, false,  false, false,  false,  true,   true, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 73, 0.f,  11,  9,   -1,  5,   podm43,  false, false,  false, false,  false, false,  false, false,  false,  true,   true, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 46, 0.f,   8,  5,    1,  0,   podm43,   true, false,  false, false,  false,  true,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 48, 0.f,   5,  3,    1,  1,   podm43,  false, false,  false,  true,   true, false,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 50, 0.f,  12,  7,    1,  2,   podm43,  false, false,   true, false,  false, false,  false,  true,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 44, 0.f,  14,  9,    1,  3,   podm43,  false, false,  false, false,  false, false,   true, false,  false,  true,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 47, 0.f,  18, 11,    1,  4,   podm43,  false, false,  false, false,  false, false,  false, false,   true, false,  false,  true));
    _diamondMarimba43_60nn.addMicrotone(pt( 85, 0.f,   3,  2,   -2,  2,   podm43,  false,  true,   true, false,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 81, 0.f,   7,  5,   -2,  3,   podm43,  false, false,  false, false,  false,  true,   true, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 85, 0.f,   9,  6,   -2,  4,   podm43,  false, false,  false,  true,  false, false,  false, false,   true, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 88, 0.f,  11,  7,   -2,  5,   podm43,  false, false,  false, false,  false, false,  false,  true,  false, false,   true, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 35, 0.f,   4,  3,    2,  0,   podm43,   true, false,  false,  true,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 39, 0.f,  10,  7,    2,  1,   podm43,  false, false,  false, false,   true, false,  false,  true,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 35, 0.f,  12,  9,    2,  2,   podm43,  false, false,   true, false,  false, false,  false, false,  false,  true,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 32, 0.f,  14, 11,    2,  3,   podm43,  false, false,  false, false,  false, false,   true, false,  false, false,  false,  true));
    _diamondMarimba43_60nn.addMicrotone(pt( 94, 0.f,   7,  4,   -3,  3,   podm43,  false,  true,  false, false,  false, false,   true, false,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 96, 0.f,   9,  5,   -3,  4,   podm43,  false, false,  false, false,  false,  true,  false, false,   true, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 98, 0.f,  11,  6,   -3,  5,   podm43,  false, false,  false,  true,  false, false,  false, false,  false, false,   true, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 26, 0.f,   8,  7,    3,  0,   podm43,   true, false,  false, false,  false, false,  false,  true,  false, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 24, 0.f,  10,  9,    3,  1,   podm43,  false, false,  false, false,   true, false,  false, false,  false,  true,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 22, 0.f,  12, 11,    3,  2,   podm43,  false, false,   true, false,  false, false,  false, false,  false, false,  false,  true));
    _diamondMarimba43_60nn.addMicrotone(pt(111, 0.f,   9,  8,   -4,  4,   podm43,  false,  true,  false, false,  false, false,  false, false,   true, false,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt(109, 0.f,  11, 10,   -4,  5,   podm43,  false, false,  false, false,  false,  true,  false, false,  false, false,   true, false));
    _diamondMarimba43_60nn.addMicrotone(pt(  9, 0.f,  16,  9,    4,  0,   podm43,   true, false,  false, false,  false, false,  false, false,  false,  true,  false, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 11, 0.f,  20, 11,    4,  1,   podm43,  false, false,  false, false,   true, false,  false, false,  false, false,  false,  true));
    _diamondMarimba43_60nn.addMicrotone(pt(123, 0.f,  11,  8,   -5,  5,   podm43,  false,  true,  false, false,  false, false,  false, false,  false, false,   true, false));
    _diamondMarimba43_60nn.addMicrotone(pt( 40, 0.f,  16, 11,    5,  0,   podm43,   true, false,  false, false,  false, false,  false, false,  false, false,  false,  true));
    _diamondMarimba43 = MicrotoneArray(_diamondMarimba43_60nn); // will be overwritten in setNoteNumberMiddleC

    // Diamond Marimba
    auto const podm = Point<float>(0, 6); // octave in gral coords
    //                                                                     o1     u1      o3     u3      o5     u5      o7     u7      o9     u9      o11    u11
    _diamondMarimba.addMicrotone(pt(0,  0.f,   1,  1,    0,  0,   podm,   true,  true,  false, false,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   5,  5,    0,  1,   podm,  false, false,  false, false,   true,  true,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   3,  3,    0,  2,   podm,  false, false,   true,  true,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   7,  7,    0,  3,   podm,  false, false,  false, false,  false, false,   true,  true,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   9,  9,    0,  4,   podm,  false, false,  false, false,  false, false,  false, false,   true,  true,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,  11, 11,    0,  5,   podm,  false, false,  false, false,  false, false,  false, false,  false, false,   true,  true));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   5,  4,   -1,  1,   podm,  false,  true,  false, false,   true, false,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   6,  5,   -1,  2,   podm,  false, false,   true, false,  false,  true,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   7,  6,   -1,  3,   podm,  false, false,  false,  true,  false, false,   true, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   9,  7,   -1,  4,   podm,  false, false,  false, false,  false, false,  false,  true,   true, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,  11,  9,   -1,  5,   podm,  false, false,  false, false,  false, false,  false, false,  false,  true,   true, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,   8,  5,    1,  0,   podm,   true, false,  false, false,  false,  true,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,   5,  3,    1,  1,   podm,  false, false,  false,  true,   true, false,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  12,  7,    1,  2,   podm,  false, false,   true, false,  false, false,  false,  true,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  14,  9,    1,  3,   podm,  false, false,  false, false,  false, false,   true, false,  false,  true,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  18, 11,    1,  4,   podm,  false, false,  false, false,  false, false,  false, false,   true, false,  false,  true));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   3,  2,   -2,  2,   podm,  false,  true,   true, false,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   7,  5,   -2,  3,   podm,  false, false,  false, false,  false,  true,   true, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   9,  6,   -2,  4,   podm,  false, false,  false,  true,  false, false,  false, false,   true, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,  11,  7,   -2,  5,   podm,  false, false,  false, false,  false, false,  false,  true,  false, false,   true, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,   4,  3,    2,  0,   podm,   true, false,  false,  true,  false, false,  false, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  10,  7,    2,  1,   podm,  false, false,  false, false,   true, false,  false,  true,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  12,  9,    2,  2,   podm,  false, false,   true, false,  false, false,  false, false,  false,  true,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  14, 11,    2,  3,   podm,  false, false,  false, false,  false, false,   true, false,  false, false,  false,  true));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   7,  4,   -3,  3,   podm,  false,  true,  false, false,  false, false,   true, false,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,   9,  5,   -3,  4,   podm,  false, false,  false, false,  false,  true,  false, false,   true, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  0.f,  11,  6,   -3,  5,   podm,  false, false,  false,  true,  false, false,  false, false,  false, false,   true, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,   8,  7,    3,  0,   podm,   true, false,  false, false,  false, false,  false,  true,  false, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  10,  9,    3,  1,   podm,  false, false,  false, false,   true, false,  false, false,  false,  true,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -1.f,  12, 11,    3,  2,   podm,  false, false,   true, false,  false, false,  false, false,  false, false,  false,  true));
    _diamondMarimba.addMicrotone(pt(0,  1.f,   9,  8,   -4,  4,   podm,  false,  true,  false, false,  false, false,  false, false,   true, false,  false, false));
    _diamondMarimba.addMicrotone(pt(0,  1.f,  11, 10,   -4,  5,   podm,  false, false,  false, false,  false,  true,  false, false,  false, false,   true, false));
    _diamondMarimba.addMicrotone(pt(0, -2.f,  16,  9,    4,  0,   podm,   true, false,  false, false,  false, false,  false, false,  false,  true,  false, false));
    _diamondMarimba.addMicrotone(pt(0, -2.f,  20, 11,    4,  1,   podm,  false, false,  false, false,   true, false,  false, false,  false, false,  false,  true));
    _diamondMarimba.addMicrotone(pt(0,  1.f,  11,  8,   -5,  5,   podm,  false,  true,  false, false,  false, false,  false, false,  false, false,   true, false));
    _diamondMarimba.addMicrotone(pt(0, -2.f,  16, 11,    5,  0,   podm,   true, false,  false, false,  false, false,  false, false,  false, false,  false,  true));
    
    // Quadrangularis Reversum
    auto const poqr = Point<float>(0, 10); // octave in gral coords
    //                                                               o1     u1      o3     u3      o5     u5      o7     u7      o9     u9      o11    u11
    _reversum.addMicrotone(pt(0,  0.f,   1,  1,    0,  0,   poqr,   true,  true,  false, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   5,  5,    0,  1,   poqr,  false, false,  false, false,   true,  true,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   3,  3,    0,  2,   poqr,  false, false,   true,  true,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   7,  7,    0,  3,   poqr,  false, false,  false, false,  false, false,   true,  true,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   9,  9,    0,  4,   poqr,  false, false,  false, false,  false, false,  false, false,   true,  true,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,  11, 11,    0,  5,   poqr,  false, false,  false, false,  false, false,  false, false,  false, false,   true,  true));
    _reversum.addMicrotone(pt(0,  0.f,   5,  4,    1,  0,   poqr,  false,  true,  false, false,   true, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   6,  5,    1,  1,   poqr,  false, false,   true, false,  false,  true,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   7,  6,    1,  2,   poqr,  false, false,  false,  true,  false, false,   true, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   9,  7,    1,  3,   poqr,  false, false,  false, false,  false, false,  false,  true,   true, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,  11,  9,    1,  4,   poqr,  false, false,  false, false,  false, false,  false, false,  false,  true,   true, false));
    _reversum.addMicrotone(pt(0, -1.f,   8,  5,   -1,  1,   poqr,   true, false,  false, false,  false,  true,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,   5,  3,   -1,  2,   poqr,  false, false,  false,  true,   true, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  12,  7,   -1,  3,   poqr,  false, false,   true, false,  false, false,  false,  true,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  14,  9,   -1,  4,   poqr,  false, false,  false, false,  false, false,   true, false,  false,  true,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  18, 11,   -1,  5,   poqr,  false, false,  false, false,  false, false,  false, false,   true, false,  false,  true));
    _reversum.addMicrotone(pt(0,  0.f,   3,  2,    2,  0,   poqr,  false,  true,   true, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   7,  5,    2,  1,   poqr,  false, false,  false, false,  false,  true,   true, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   9,  6,    2,  2,   poqr,  false, false,  false,  true,  false, false,  false, false,   true, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,  11,  7,    2,  3,   poqr,  false, false,  false, false,  false, false,  false,  true,  false, false,   true, false));
    _reversum.addMicrotone(pt(0, -1.f,   4,  3,   -2,  2,   poqr,   true, false,  false,  true,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  10,  7,   -2,  3,   poqr,  false, false,  false, false,   true, false,  false,  true,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  12,  9,   -2,  4,   poqr,  false, false,   true, false,  false, false,  false, false,  false,  true,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  14, 11,   -2,  5,   poqr,  false, false,  false, false,  false, false,   true, false,  false, false,  false,  true));
    _reversum.addMicrotone(pt(0,  0.f,   7,  4,    3,  0,   poqr,  false,  true,  false, false,  false, false,   true, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,   9,  5,    3,  1,   poqr,  false, false,  false, false,  false,  true,  false, false,   true, false,  false, false));
    _reversum.addMicrotone(pt(0,  0.f,  11,  6,    3,  2,   poqr,  false, false,  false,  true,  false, false,  false, false,  false, false,   true, false));
    _reversum.addMicrotone(pt(0, -1.f,   8,  7,   -3,  3,   poqr,   true, false,  false, false,  false, false,  false,  true,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  10,  9,   -3,  4,   poqr,  false, false,  false, false,   true, false,  false, false,  false,  true,  false, false));
    _reversum.addMicrotone(pt(0, -1.f,  12, 11,   -3,  5,   poqr,  false, false,   true, false,  false, false,  false, false,  false, false,  false,  true));
    _reversum.addMicrotone(pt(0,  1.f,   9,  8,    4,  0,   poqr,  false,  true,  false, false,  false, false,  false, false,   true, false,  false, false));
    _reversum.addMicrotone(pt(0,  1.f,  11, 10,    4,  1,   poqr,  false, false,  false, false,  false,  true,  false, false,  false, false,   true, false));
    _reversum.addMicrotone(pt(0, -2.f,  16,  9,   -4,  4,   poqr,   true, false,  false, false,  false, false,  false, false,  false,  true,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,  20, 11,   -4,  5,   poqr,  false, false,  false, false,   true, false,  false, false,  false, false,  false,  true));
    _reversum.addMicrotone(pt(0,  1.f,  11,  8,    5,  0,   poqr,  false,  true,  false, false,  false, false,  false, false,  false, false,   true, false));
    _reversum.addMicrotone(pt(0, -2.f,  16, 11,   -5,  5,   poqr,   true, false,  false, false,  false, false,  false, false,  false, false,  false,  true));

    //                                                               o1     u1      o3     u3      o5     u5      o7     u7      o9     u9      o11    u11
    // 1/1 alto
    _reversum.addMicrotone(pt(0, -1.f,   1,  1,    9, -2,   poqr,   true,  true,  false, false,  false, false,  false, false,  false, false,  false, false));
    
    // left side alto
    _reversum.addMicrotone(pt(0, -3.f,   3,  2,    4, -3,   poqr,  false,  true,   true, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,   7,  5,    4, -2,   poqr,  false, false,  false, false,  false,  true,   true, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,   7,  4,    5, -3,   poqr,   true, false,  false, false,  false, false,   true, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,   5,  3,    5, -2,   poqr,  false, false,  false,  true,   true, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,  21, 20,    6, -3,   poqr,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,  11,  6,    6, -2,   poqr,  false, false,  false,  true,  false, false,  false, false,  false, false,   true, false));
    _reversum.addMicrotone(pt(0, -2.f,   9,  8,    7, -3,   poqr,  false,  true,  false, false,  false, false,  false, false,   true, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,  16, 15,    7, -2,   poqr,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,   5,  4,    8, -3,   poqr,  false,  true,  false, false,   true, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,   7,  6,    8, -2,   poqr,  false, false,  false,  true,  false, false,   true, false,  false, false,  false, false));

    // right side alto
    _reversum.addMicrotone(pt(0, -3.f,   4,  3,    4,  3,   poqr,   true, false,  false,  true,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,  10,  7,    4,  4,   poqr,  false, false,  false, false,   true, false,  false,  true,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,   8,  5,    5,  2,   poqr,  false,  true,  false, false,  false,  true,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,  16,  9,    5,  3,   poqr,   true, false,  false, false,  false, false,  false, false,  false,  true,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,   9,  5,    6,  1,   poqr,  false, false,  false, false,  false,  true,  false, false,   true, false,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,  15,  8,    6,  2,   poqr,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,  10,  9,    7,  1,   poqr,  false, false,  false, false,   true, false,  false, false,  false,  true,  false, false));
    _reversum.addMicrotone(pt(0, -3.f,  40, 21,    7,  0,   poqr,  false, false,  false, false,  false, false,  false, false,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,   8,  7,    8, -1,   poqr,   true, false,  false, false,  false, false,  false,  true,  false, false,  false, false));
    _reversum.addMicrotone(pt(0, -2.f,   6,  5,    8,  0,   poqr,  false, false,   true, false,  false,  true,  false, false,  false, false,  false, false));
    
    // defaults
    setCanNPOOverride(false); // can NOT use Gral when NPO Override is enabled
    setNPOOverrideEnable(false);
    setCanUniquify(false);
    setUniquify(false);
    setCanSort(true);
    setSort(true);
    setOctaveReduce(false);
    setOctaveRepeat(true);
    setTuningName("Partch");
    setCanScala(false);
    setNoteNumberMiddleC(60);

    // postProcess and update
    setPostProcessPreTuningUpdate([this](){TuningImp::_gralPostProcessBlockImp();});
    _partchUpdate();
}

Partch::~Partch() {
    
}

#pragma mark - Setters/Getters

void Partch::setScale(Scale scale) {
    _scale = scale;
    _partchUpdate();
}

int const Partch::getScale() {
    return static_cast<int>(_scale);
}

void Partch::setGralHexScale(float newScale) {
    const ScopedLock sl(_lock);
    newScale = jlimit(0.1f, 5.f, newScale);
    if(WilsonicMath::floatsAreNotEqual(newScale, _gralHexScale)) {
        _gralHexScale = newScale;
        _partchUpdate();
    }
}

float Partch::getGralHexScale() {
    return _gralHexScale;
}

void Partch::setGralHexRotationRadians(float newRotationRadians) {
    const ScopedLock sl(_lock);
    newRotationRadians = jlimit(-MathConstants<float>::pi, MathConstants<float>::pi, newRotationRadians);
    if(WilsonicMath::floatsAreNotEqual(newRotationRadians, _gralHexRotationRadians)) {
        _gralHexRotationRadians = newRotationRadians;
        _partchUpdate();
    }
}

float Partch::getGralHexRotationRadians() {
    return _gralHexRotationRadians;
}

void Partch::setGralHexShearX(float newShearX) {
    const ScopedLock sl(_lock);
    newShearX = jlimit(-1.f, 1.f, newShearX);
    if(WilsonicMath::floatsAreNotEqual(newShearX, _gralHexShearX)) {
        _gralHexShearX = newShearX;
        _partchUpdate();
    }
}

float Partch::getGralHexShearX() {
    return _gralHexShearX;
}

void Partch::setGralHexOriginOffsetFactorX (float newOffsetX) {
    const ScopedLock sl(_lock);
    newOffsetX = jlimit(-2.f, 2.f, newOffsetX);
    if (WilsonicMath::floatsAreNotEqual(newOffsetX, _gralHexOriginOffsetFactorX)) {
        _gralHexOriginOffsetFactorX = newOffsetX;
        _partchUpdate();
    }
}

float Partch::getGralHexOriginOffsetFactorX() {
    return _gralHexOriginOffsetFactorX;
}

void Partch::setGralHexOriginOffsetFactorY(float newOffsetY) {
    const ScopedLock sl(_lock);
    newOffsetY = jlimit(-2.f, 2.f, newOffsetY);
    if(WilsonicMath::floatsAreNotEqual(newOffsetY, _gralHexOriginOffsetFactorY)) {
        _gralHexOriginOffsetFactorY = newOffsetY;
        _partchUpdate();
    }
}

float Partch::getGralHexOriginOffsetFactorY() {
    return _gralHexOriginOffsetFactorY;
}

void Partch::setO1(bool o1) {
    _o1 = o1;
}

bool Partch::getO1() const {
    return _o1;
}

void Partch::setU1(bool u1) {
    _u1 = u1;
}

bool Partch::getU1() const {
    return _u1;
}

void Partch::setO3(bool o3) {
    _o3 = o3;
}

bool Partch::getO3() const {
    return _o3;
}

void Partch::setU3(bool u3) {
    _u3 = u3;
}

bool Partch::getU3() const {
    return _u3;
}

void Partch::setO5(bool o5) {
    _o5 = o5;
}

bool Partch::getO5() const {
    return _o5;
}

void Partch::setU5(bool u5) {
    _u5 = u5;
}

bool Partch::getU5() const {
    return _u5;
}

void Partch::setO7(bool o7) {
    _o7 = o7;
}

bool Partch::getO7() const {
    return _o7;
}

void Partch::setU7(bool u7) {
    _u7 = u7;
}

bool Partch::getU7() const {
    return _u7;
}

void Partch::setO9(bool o9) {
    _o9 = o9;
}

bool Partch::getO9() const {
    return _o9;
}

void Partch::setU9(bool u9) {
    _u9 = u9;
}

bool Partch::getU9() const {
    return _u9;
}

void Partch::setO11(bool o11) {
    _o11 = o11;
}

bool Partch::getO11() const {
    return _o11;
}

void Partch::setU11(bool u11) {
    _u11 = u11;
}

bool Partch::getU11() const {
    return _u11;
}

#pragma mark - Drawing

bool Partch::canPaintTuning() {
    return true;
}

void Partch::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    g.fillAll(processor.getAppSkin().getBgColor());
    if(AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::green);
        g.drawRect(bounds, 2);
    }

    // NPOOverride is not supported for Partch scales
    if(getNPOOverrideEnable()) {
        _paintNPOOverride(processor, g, bounds);
        return;
    }
    
    // paint
    _paintPartch(processor, g, bounds);
}

// Paint variants
void Partch::_paintPartch(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    g.saveState(); // save the current state of the graphics context
    _paintHelper(processor, g, bounds);
    const ScopedLock sl(_lock);
    auto bounds_center = bounds.getCentre().toFloat();
    _gralHexOrigin.setX(bounds_center.x + 0.5f * bounds.getWidth()  * _gralHexOriginOffsetFactorX); // updates _gralPaintTransform()
    _gralHexOrigin.setY(bounds_center.y + 0.5f * bounds.getHeight() * _gralHexOriginOffsetFactorY); // updates _gralPaintTransform()

    // Calculate the margin, width, and height of the hexagon
    float const hexMargin  = _getHexMargin();
    float const hexWidth   = _getHexWidth();
    float const hexHeight  = _getHexHeight();
    float const pathWidth  = hexWidth - 2 * hexMargin;
    float const pathHeight = hexHeight - 2 * hexMargin;
    Path hexPath;
    
    // Define the points of the hexagon
    hexPath.startNewSubPath(pathWidth, 0.5f * pathHeight);
    hexPath.lineTo(0.75f * pathWidth,  pathHeight);
    hexPath.lineTo(0.25f * pathWidth,  pathHeight);
    hexPath.lineTo(0.f,                0.5f * pathHeight);
    hexPath.lineTo(0.25f * pathWidth,  0.f);
    hexPath.lineTo(0.75f * pathWidth,  0.f);
    hexPath.closeSubPath();

    // Get the global transform for all drawing and mouse events
    auto const finalGralPaintTransform = _gralPaintTransform(); // we're locked in for the rest of this method

    // Lambda for painting
    auto paint = [&](unsigned long i, PartchMicrotone* note_mt) {
        jassert(note_mt != nullptr);
        if(note_mt->getFilterNote()) // skip filtered notes
            return;
        
        // Check if the note is currently playing
        bool voice_is_playing = false;
        auto voice_rms = 0.f;
#if JucePlugin_IsSynth
        // If the plugin is a synth, get the voice states
        auto vs = processor.getVoiceStates();
        if(!vs.noVoicesPlaying()) {
            for (unsigned long vsi = 0; vsi < WilsonicProcessorConstants::numVoices; vsi++) {
                auto const v = vs.voiceState[vsi];
                auto const nnv = v.nn;
                if (nnv == note_mt->getMidiNoteNumber()) {
                    voice_is_playing = true;
                    voice_rms = v.rms;
                    break;
                }
            }
        }
#elif JucePlugin_IsMidiEffect
        // If the plugin is a midi effect, get the RMS for the current note number
        float const rms = processor.getKeyboardRMSForNN(i);
        if (rms > 0.f) {
            voice_is_playing = true;
            voice_rms = rms;
        }
#else
        // If the plugin is neither a synth nor a midi effect, assert false
        jassertfalse;
#endif
        auto hex_point_final = note_mt->getGralHexPointFinal();
        auto hex_transform = _cartesian2HexTransform(hex_point_final).followedBy(finalGralPaintTransform);
        auto touchPointPath = hexPath;
        touchPointPath.applyTransform(hex_transform);
        note_mt->setTouchPointPath(touchPointPath); // this is what makes nnForDeviceSpace work

        // Fill the hexagon based on the pitch of the microtone
        // If the scale degree of the microtone is not 0 or 1 and the voice is not playing, darken the color
        // darken if not playing
        float c_delta = 0.f;
        if (!voice_is_playing) {
            // darken more if otonal/utonal is selected but this tone is not otonal/utonal (NOP if none is selected)
            if(note_mt->isOtonalUtonal(_o1, _u1, _o3, _u3, _o5, _u5, _o7, _u7, _o9, _u9, _o11, _u11)) {
                c_delta = -2.f;
            } else {
                c_delta = -4.5f;
            }
        } else { // If the voice is playing, brighten the color, no matter otonal/utonal
            c_delta = 12.f * voice_rms;
        }
        
        // Get the color based on the pitch of the microtone
        auto p01 = note_mt->getPitchValue01();
        auto c = processor.getAppTuningModel()->colorForPitch01(p01, 1.f, c_delta);
        g.setColour(c);
        g.fillPath(hexPath, hex_transform);

        float hexLineWidth = 1.f;
        // TODO: make octave a different color
//        if(note_mt->getScaleDegree() == 0) { // octave
//            g.setColour(Colour(255,255,255));
//            hexLineWidth = voice_is_playing ? 5.f * (1.f + voice_rms) : 5.f;
//        } else if (note_mt->getScaleDegree() == 1) {// generator
//            g.setColour(Colour(128,255,128));
//            hexLineWidth = voice_is_playing ? 5.f * (1.f + voice_rms) : 5.f;
//        } else {
//            g.setColour(voice_is_playing ? Colours::grey.brighter(voice_rms) : Colours::grey);
//            hexLineWidth = voice_is_playing ? 2.f * (1.f + 2.f * voice_rms) : 2.f;
//        }
        g.setColour(voice_is_playing ? Colours::grey.brighter(voice_rms) : Colours::grey);
        hexLineWidth = voice_is_playing ? 2.f * (1.f + 2.f * voice_rms) : 2.f;
        g.strokePath(hexPath, PathStrokeType(hexLineWidth), hex_transform);

        if (AppExperiments::showDebugBoundingBox) {
            auto dc = Colours::limegreen;
            g.setColour(dc);
            g.strokePath(hexPath, PathStrokeType(1.f), hex_transform);
        }

        // Draw the text labels for the scale degree, pitch value, and note number of the microtone
        auto const fontHeight = 10.f * _gralHexScale;
        g.setFont(Font(FontOptions(fontHeight)));
        string labelStr0 = note_mt->getShortDescriptionText();
        auto const f = getTuningTableFrequency(i);
        auto labelStr1 = String(f, 2);
        string labelStr2 = to_string(i);
        g.setColour(Colours::black);
        g.saveState();
        g.addTransform(hex_transform);
        auto text_rect = Rectangle<float>(0.f, 0.f, pathWidth, pathHeight);
        auto tr0 = text_rect.removeFromTop(0.3333f * hexHeight);
        g.drawText(labelStr0, tr0, Justification::centred);
        auto tr1 = text_rect.removeFromTop(0.3333f * hexHeight);
        g.drawText(labelStr1, tr1, Justification::centred);
        auto tr2 = text_rect.removeFromTop(0.3333f * hexHeight);
        g.drawText(labelStr2, tr2, Justification::centred);
        g.restoreState();
    };
    
    // Diamond Marimba 43 is painted differently than the others
    if(_scale == Scale::DiamondMarimba43) {
        for(unsigned long i = 0; i < _diamondMarimba43_60nn.count(); i++) {
            PartchMicrotone* mt = dynamic_cast<PartchMicrotone*>(_diamondMarimba43.microtoneAtIndex(i).get());
            jassert(mt != nullptr);
            auto const nn = mt->getMidiNoteNumber();
            paint(nn, mt);
        }
    } else {
        // Iterate over the sorted scale, draw as hexagons
        for(unsigned long nn = 0; nn < WilsonicProcessorConstants::numMidiNotes; nn++) {
            PartchMicrotone* mt = dynamic_cast<PartchMicrotone*>(microtoneAtNoteNumber(nn).get());
            jassert(mt != nullptr);
            paint(nn, mt);
        }
    }

    // draw text
    g.setColour(Colours::white);
    auto const fontHeight = 16.f;
    g.setFont(Font(FontOptions(fontHeight)));
    if(_scale == Scale::Partch43) {
        g.drawFittedText("Harry Partch set the 1/1 as G:\nScale will be tuned to 1.5 * Frequency Middle C value\nSet Frequency Middle C to 261.333333 for a G at 784Hz", bounds, Justification::bottomRight, 5);
    } else if(_scale == Scale::DiamondMarimba43) {
        g.drawFittedText("Harry Partch set the 1/1 as G:\nScale will be tuned to 1.5 * Frequency Middle C value\nSet Frequency Middle C to 261.333333 for a G at 784Hz", bounds, Justification::bottomRight, 5);
    } else if(_scale == Scale::DiamondMarimba) {
        g.drawFittedText("Harry Partch set the 1/1 as G:\nScale will be tuned to 1.5 * Frequency Middle C value\nSet Frequency Middle C to 261.333333 for a G at 784Hz", bounds, Justification::bottomRight, 5);
    } else if (_scale == Scale::QuadrangularisReversum) {
        g.drawFittedText("Harry Partch set the 1/1 as G:\nScale will be tuned to 1.5 * Frequency Middle C value\nSet Frequency Middle C to 261.333333 for a G at 784Hz", bounds, Justification::bottomRight, 5);
    } else {
        jassertfalse;
    }

    g.restoreState(); // restore the state after drawing the Gral
}

void Partch::_paintNPOOverride(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    g.saveState();
    _paintHelper(processor, g, bounds);
    g.setColour(Colours::white);
    auto const fontHeight = 16.f;
    g.setFont(Font(FontOptions(fontHeight)));
    g.drawFittedText("Can't draw Partch because\nNPO Override is enabled.\n\nDisable NPO Override to resume drawing Gral.", bounds, Justification::centred, 5);
    g.restoreState();
}

#pragma mark - _gralPaintTransform

// AffineTransform of the Gral display.
AffineTransform Partch::_gralPaintTransform() {
    auto const p0 = (_scale == Scale::DiamondMarimba43) ? _diamondMarimba43_60nn.microtoneAtIndex(0) : microtoneAtNoteNumber(0); // any note will do, just need the hex octave vector
    jassert(p0 != nullptr);
    auto octave_vec = p0->getHexOctaveVector();
    auto octave_vec_transform = _cartesian2HexTransform(octave_vec);
    auto xfmd_octave_vec = octave_vec.transformedBy(octave_vec_transform);
    auto origin = Point<float>(0.f, 0.f);
    auto origin_transform = _cartesian2HexTransform(origin);
    auto xfmd_origin = origin.transformedBy(origin_transform);
    // calculate the angle between the origin and the transformed octave vector
    // 12 o'clock = 0, 3 o'clock = Pi/2, 6 o'clock = Pi, 9 o'clock = -Pi/2
    auto const angle = xfmd_origin.getAngleToPoint(xfmd_octave_vec);
    constexpr float pi_2 = 0.5f * 3.14159265358979323846f;
    // calculate the rotation adjustment based on the level of the Gral and the angle
    // the absoluteMinLevel/1/1 mapping is vertical
    auto const rotation_adjustment = pi_2 - angle;
    // shear and rotate entire plane
    auto shear = AffineTransform::shear(_gralHexShearX, 0.f);
    auto plane_rotation = AffineTransform::rotation(rotation_adjustment + _gralHexRotationRadians, _gralHexOrigin.getX(), _gralHexOrigin.getY());
    auto final_transform = shear.followedBy(plane_rotation);

    return final_transform;
}

#pragma mark - nnForDeviceSpace

// This function returns the note number for a given device space.
int Partch::nnForDeviceSpace(Point<int> xy) {
    const ScopedLock sl(_lock);
    auto result = -1;
    auto xfm_xy = xy.toFloat();

    // lambda for getting touchpoint
    auto nn = [&](Microtone_p note_mt) -> int {
        jassert(note_mt != nullptr);
        // get the touch point path for the microtone
        auto retVal = -1;
        auto tp = note_mt->getTouchPointPath(); // stored in screen coords by paint method
        if (tp.contains(xfm_xy)) {
            retVal = static_cast<int>(note_mt->getMidiNoteNumber());
            return retVal; // for overlapping rects this returns the first note
        }
        return retVal;
    };
    
    // Diamond Marimba 43 is treated differently than the others
    if(_scale == Scale::DiamondMarimba43) {
        for(unsigned long i = 0; i < _diamondMarimba43.count(); i++) {
            auto const mt = _diamondMarimba43.microtoneAtIndex(i);
            result = nn(mt);
            if(result != -1) break;
        }
    } else {
        // Iterate over the sorted scale
        for(unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
            auto mt = microtoneAtNoteNumber(i);
            result = nn(mt);
            if(result != -1) break;
        }
    }

    return result;
}

#pragma mark - _partchUpdate()

void Partch::setNoteNumberMiddleC(unsigned long nn) {
    const ScopedLock sl(_lock);
    TuningImp::setNoteNumberMiddleC(nn);
    for(unsigned long i = 0; i < _diamondMarimba43_60nn.count(); i++) {
        auto const mt = _diamondMarimba43_60nn.microtoneAtIndex(i)->clone();
        int mtnnc = static_cast<int>(mt->getMidiNoteNumber());
        int nnmc = mtnnc - (60 - static_cast<int>(getNoteNumberMiddleC()));
        while(nnmc < 0) nnmc += 43; // transpose into [0,127]
        while(nnmc >= static_cast<int>(WilsonicProcessorConstants::numMidiNotes)) nnmc -= 43; // transpose into [0,127]
        jassert(nnmc >= 0);
        jassert(nnmc < static_cast<int>(WilsonicProcessorConstants::numMidiNotes));
        mt->setMidiNoteNumber(static_cast<unsigned long>(nnmc));
        _diamondMarimba43.setMicrotone(mt, i);
    }
}

// The postProcess block is set in the constructor helper: _gralPostProcessBlockImp
// setMicrotoneArray calls TuningImp::_update,
// which calls the postProcess block,
// and THEN the tuningUpdated callback
void Partch::_partchUpdate() {
    const ScopedLock sl(_lock);
    switch(_scale) {
        case Scale::Partch43:
            setMicrotoneArray(_partch43);
            break;
        case Scale::DiamondMarimba43:
            // note _diamondMarimba43_60nn is used for drawing only...the actual scale is _partch43
            setMicrotoneArray(_partch43);
            break;
        case Scale::DiamondMarimba:
            setMicrotoneArray(_diamondMarimba);
            break;
        case Scale::QuadrangularisReversum:
            setMicrotoneArray(_reversum);
            break;
            default:
            jassertfalse;
    }
}
