/*
  ==============================================================================

    Brun+Gral.cpp
    Created: 11 Aug 2023 2:25:38pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "Brun.h"
#include "BrunMicrotone.h"
#include "MicrotoneArray.h"
#include "TuningImp.h"
#include "WilsonicAppSkin.h"
#include "WilsonicProcessorConstants.h"
#include <memory>

#pragma mark - _gralPaintTransform

// duplicate code of TuningImp with one critical changes to handle _levelGral == absoluteMinLevel
// AffineTransform of the Gral display.
AffineTransform Brun::_gralPaintTransform() {
    auto const p0 = microtoneAtNoteNumber(0); // any note will do, just need the hex octave vector
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
    auto const rotation_adjustment = (_levelGral == absoluteMinLevel) ? 0.f : pi_2 - angle;
    // shear and rotate entire plane
    auto shear = AffineTransform::shear(_gralHexShearX, 0.f);
    auto plane_rotation = AffineTransform::rotation(rotation_adjustment + _gralHexRotationRadians, _gralHexOrigin.getX(), _gralHexOrigin.getY());
    auto final_transform = shear.followedBy(plane_rotation);

    return final_transform;
}

#pragma mark - _mapGralToBrunMicrotones

// This function maps Gral points to Brun microtones.
void Brun::_mapGralToBrunMicrotones(MicrotoneArray& microtoneArray, Point<float> generator_vector, Point<float> octave_vector) {
    auto const npo = static_cast<int>(microtoneArray.count());
    jassert(npo > 0);

    // create a shared pointer to a vector of integers representing the Gral column pattern
    _gral_column_pattern = make_shared<vector<int>>(static_cast<unsigned long>(octave_vector.x + octave_vector.y), 0);
    
    // define a lambda function to add a point to the Gral column pattern
    auto mos_pattern_add = [this,octave_vector](Point<float> p) {
        // calculate the index of the point in the Gral column pattern
        auto index = static_cast<unsigned long>(p.x + p.y) % static_cast<unsigned long>(octave_vector.x + octave_vector.y);
        if (index >= 0) {
            (*_gral_column_pattern)[index]++; // increment the value at the index in the Gral column pattern
        }
        (*_gral_column_pattern)[index]++; // increment the value at the index in the Gral column pattern
    };

    // calculate the hexagonal octave vector
    Point<float> hex_octave_vector = transformGral2Hex(octave_vector);

    // iterate over all degrees
    for (auto i = 0; i < npo; i++) {
        BrunMicrotone* note_mt = dynamic_cast<BrunMicrotone*>(microtoneArray.microtoneAtIndex(static_cast<unsigned long>(i)).get());
        jassert(note_mt != nullptr);
        
        // calculate the point for the current degree
        Point<float> note_point = static_cast<float>(note_mt->getScaleDegree()) * generator_vector;
        auto const positive_degree = note_mt->getScaleDegree() >= 0;
        auto const q = _octaveReduceGralPoint(note_point, octave_vector, positive_degree);
        note_point = q;
        
        // set the Gral Erv point and octave vector for the microtone
        note_mt->setGralErvPoint(note_point);
        note_mt->setGralErvOctaveVector(octave_vector);
        auto const hex_point = transformGral2Hex(note_point);
        note_mt->setGralHexPoint(hex_point);
        note_mt->setHexOctaveVector(hex_octave_vector);
        mos_pattern_add(note_point);
    }
}
