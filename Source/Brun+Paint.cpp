/*
 ==============================================================================

 Brun+Paint.cpp
 Created: 19 May 2023 2:10:20pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

// Importing necessary libraries and files
#include "Brun.h"
#include "BrunMicrotone.h"
#include "MicrotoneArray.h"
#include "TuningImp.h"
#include "WilsonicAppSkin.h"
#include "WilsonicProcessor.h"
#include "WilsonicProcessorConstants.h"

#pragma mark - drawing

// Function to check if the tuning can be painted
bool Brun::canPaintTuning() {
    return true;
}

// Function to paint the WilsonicProcessor object based on the display mode
void Brun::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    if(AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::green);
        g.drawRect(bounds, 2);
    }
    
    switch (_displayMode) {
        case DisplayMode::Cartesian:
            _paintCartesian(processor, g, bounds);
            break;
        case DisplayMode::Horogram:
            _paintHorogram(processor, g, bounds);
            break;
        case DisplayMode::HorogramInverse:
            _paintInverseHorogram(processor, g, bounds);
            break;
        case DisplayMode::Gral:
            if(getNPOOverrideEnable()) {
                _paintGralNPOOverride(processor, g, bounds);
            } else {
                _paintGral(processor, g, bounds);
            }
            break;
        default:
            jassertfalse;
            break;
    }
}

#pragma mark - paint Cartesian

// Function to paint the Cartesian representation of the Brun object
void Brun::_paintCartesian(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    const ScopedLock sl(_lock);
    g.saveState();
    _paintHelper(processor, g, bounds);
    auto const levelCount = getLabelArray().size();
    auto const level = getLevel();
    auto const w = bounds.getWidth();
    auto const h = bounds.getHeight();
    auto const xMargin = 0.f;
    auto const xw = max(w - 2 * xMargin, 1.f);
    auto const yh = max(h - 2.f * 0.f, 1.f);

    // Iterating over all levels
    for (auto l = Brun::absoluteMinLevel; l <= Brun::absoluteMaxLevel; l++) {
        auto microtoneArray = _microtoneArrayBrunAllLevels[l];
        jassert(microtoneArray != nullptr);

        // scale degrees X
        for (unsigned long degree = 0; degree < microtoneArray->count(); degree++) {
            auto mt = microtoneArray->microtoneAtIndex(degree);
            auto mtb = static_pointer_cast<BrunMicrotone>(mt);
            jassert(mtb != nullptr);
            auto const p = mt->getPitchValue01();
            auto const degreeLevel = mtb->getLevel();
            auto const x0 = xMargin + p * xw;
            auto const y0 = yh * float(l) / float(levelCount);
            auto const y1 = yh * float(l + 1) / float(levelCount);
            auto c = processor.getAppTuningModel()->colorForPitch01(p, 1.f, (l != level) ? -3.f : 0.f);
            g.setColour(c);
            auto const l01 = clamp(0.f, float(levelCount - degreeLevel + 1) / float(levelCount), 1.f);
            auto const thickness = 6.f * l01 + 1.f;
            g.drawLine(x0, y0, x0, y1, thickness);
        }
    }

    auto const x0 = 0;
    auto const x1 = bounds.getWidth();
    auto const levelHeight = bounds.getHeight() / float(levelCount);
    auto const currentLevel = level;
    for (unsigned long l = 0; l < levelCount; l++) {
        auto const y0 = l * levelHeight;
        auto const y1 = (l + 1) * levelHeight;
        auto const r = Rectangle<int>::leftTopRightBottom(x0, static_cast<int>(y0), x1, static_cast<int>(y1));
        auto outlineColor = (l == currentLevel) ? Colours::white : Colours::grey;
        g.setColour(outlineColor);
        auto outlineThickness = (l == currentLevel) ? 3.f : 1.f;
        g.drawRect(r, static_cast<int>(outlineThickness));
    }

    g.restoreState();
}

#pragma mark - Paint Horogram

// Function to paint the Horogram representation of the Brun object
void Brun::_paintHorogram(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    
    //
    const ScopedLock sl(_lock);
    g.saveState();
    _paintHelper(processor, g, bounds);

    // Function to convert degrees to radians
    auto radians01 = [](float d01) {
        return d01 * 2.f * 3.14159265358979323846f;
    };
    
    // Function to convert Horogram coordinates to Cartesian coordinates
    auto horagram01ToCartesian01 = [&](Point<float> p) {
        float thetaRadians = radians01(p.getX()) - 0.5f * 3.14159265358979323846f;
        return Point<float>(p.getY() * cos(thetaRadians), p.getY() * sin(thetaRadians));
    };
    
    // Function to draw an ellipse
    auto ellipse = [&](Point<float> center, Point<float> dims, float line_thickness) {
        g.drawEllipse(center.getX() - 0.5f * dims.getX(), center.getY() - 0.5f * dims.getY(), dims.getX(), dims.getY(), line_thickness);
    };
    
    // Function to clamp a value between a minimum and maximum
    auto clamp = [](float min, float x, float max) {
        return (x < min ? min : (x > max ? max : x));
    };
    
    // Function to interpolate between two values
    auto linearInterp = [&](float valA, float valB, float fract) {
        return valA + ((valB - valA) * clamp(0.0, fract, 1.0));
    };
    
    // Function to calculate the line width for the current level
    auto lineWidthForCurrentLevel = [&](float currentLevel, float min, float max) {
        return linearInterp(max, min, currentLevel / static_cast<float>(Brun::absoluteMaxLevel));
    };

    //
    unsigned long const level = getLevel();
    unsigned long const maxLevel = getMaxLevel();
    auto microtoneArray = getMicrotoneArray(); // deep copy
    auto brunArray = MicrotoneArray(*_brunArray);
    float const x = static_cast<float>(bounds.getX());
    float const y = static_cast<float>(bounds.getY());
    float const w = static_cast<float>(bounds.getWidth());
    float const h = static_cast<float>(bounds.getHeight());
    float const r = 0.95f * min(w, h);
    float const xp = x + 0.5f * w;
    float const yp = y + 0.5f * h;

    // Drawing the circles for each level
    g.setColour(Colours::grey);
    for (unsigned long l = 0UL; l < maxLevel + 1UL; l++) {
        float r0 = r * (static_cast<float>(l) + 1.f) / (static_cast<float>(maxLevel) + 1.f);
        ellipse(Point<float>(xp, yp), Point<float>(r0,r0), l < level ? 3.f : 1.f);
    }

    // Drawing the lines for each scale degree
    g.setColour(Colours::white);
    unsigned long currentLevel = 0;
    
    // Loop through each scale degree in the microtone array
    for (unsigned long scaleDegree = 0; scaleDegree < microtoneArray.count(); scaleDegree++) {
        // Get the microtone at the current scale degree
        auto mt = dynamic_cast<BrunMicrotone*>(microtoneArray.microtoneAtIndex(scaleDegree).get());
        // Check if the level of the microtone is less than or equal to the current level
        if (mt->getLevel() <= level) {
            // Calculate the line width based on the current level
            float lineWidth = 0.8f * lineWidthForCurrentLevel(static_cast<float>(currentLevel), 1.0f, 0.3333f * processor.getAppSkin().getSmallDotRadius());
            float t0 = mt->getPitchValue01(); // Get the pitch value of the microtone
            float r0 = r * static_cast<float>(currentLevel) / (static_cast<float>(Brun::getMaxLevel()) + 1.f);// Calculate the inner radius of the line
            float r1 = r * (static_cast<float>(Brun::getMaxLevel()) + 1.f) / (static_cast<float>(Brun::getMaxLevel()) + 1.0f);// Calculate the outer radius of the line
            auto p0 = horagram01ToCartesian01(Point<float>(t0, 0.5f * r0)) + Point<float>(xp, yp);// Calculate the start point of the line
            auto p1 = horagram01ToCartesian01(Point<float>(t0, 0.5f * r1)) + Point<float>(xp, yp);// Calculate the end point of the line
            g.setColour(processor.getAppTuningModel()->colorForPitch01(mt->getPitchValue01()));// Set the color of the line based on the pitch value of the microtone
            g.drawLine(p0.x, p0.y, p1.x, p1.y, lineWidth);
            g.fillEllipse(p1.x - 0.5f * processor.getAppSkin().getSmallDotRadius(),
                          p1.y - 0.5f * processor.getAppSkin().getSmallDotRadius(),
                          processor.getAppSkin().getSmallDotRadius(),
                          processor.getAppSkin().getSmallDotRadius());// Draw the ellipse at the end point of the line
            g.fillEllipse(p0.x - 0.5f * processor.getAppSkin().getSmallDotRadius(),
                          p0.y - 0.5f * processor.getAppSkin().getSmallDotRadius(),
                          processor.getAppSkin().getSmallDotRadius(),
                          processor.getAppSkin().getSmallDotRadius());            // Draw the ellipse at the start point of the line
        }
        // Check if the current scale degree is the denominator of the microtone at the current level and if the current level is less than the count of the brun array minus 1
        if (scaleDegree + 1 == brunArray.microtoneAtIndex(currentLevel)->getDenominator() && currentLevel < brunArray.count() - 1) {
            currentLevel++;
        }
    }
    
    // Restore the previous state of the graphics context
    g.restoreState();
}
#pragma mark - paint Inverse Horogram

// Function to paint the Inverse Horogram representation of the Brun object
void Brun::_paintInverseHorogram(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    const ScopedLock sl(_lock);
    g.saveState();
    _paintHelper(processor, g, bounds);

    // Function to convert degrees to radians
    auto radians01 = [&](float d01) {
        return d01 * 2.f * 3.14159265358979323846f; // don't clamp d01
    };

    // Function to convert Horogram coordinates to Cartesian coordinates
    // Horogram coordinates are polar coordinates where the angle is represented by the x value and the radius by the y value
    auto horagram01ToCartesian01 = [&](Point<float> p) {
        float thetaRadians = radians01(p.getX());
        thetaRadians -= 0.5f * 3.14159265358979323846f;
        const float x = p.getY() * cos(thetaRadians);
        const float y = p.getY() * sin(thetaRadians);

        return Point<float>(x, y);
    };

    // Function to clamp a value between a minimum and maximum value
    auto clamp = [&](float min, float x, float max) {
        return (x < min ? min : (x > max ? max : x));
    };

    auto linearInterp = [&](float valA, float valB, float fract) {
        float fract01 = clamp(0.0, fract, 1.0);

        return valA + ((valB - valA) * fract01);
    };

    auto lineWidthForCurrentLevel = [&](float currentLevel, float min, float max) {
        float const frac = static_cast<float>(currentLevel) / static_cast<float>(Brun::absoluteMaxLevel);
        float const lineWidth = linearInterp(max, min, frac);

        return lineWidth;
    };

    const float x = bounds.getX();
    const float y = bounds.getY();
    const float w = bounds.getWidth();
    const float h = bounds.getHeight();
    const float xp = x + 0.5f * w; // center
    const float yp = y + 0.5f * h; // center
    const float inset =  0.95f;
    const float r = inset * jmin(w, h);
    auto microtoneArray = getMicrotoneArray(); // copy
    auto brunArray = MicrotoneArray(*_brunArray); // copy

    g.setColour(Colours::white);
    unsigned long currentLevel = 0;
    const float scaleTweak = 0.8f;
    // Iterate over the microtone array
    for (unsigned long scaleDegree = 0; scaleDegree < microtoneArray.count(); scaleDegree++) {
        BrunMicrotone* bmt = dynamic_cast<BrunMicrotone*>(microtoneArray.microtoneAtIndex(scaleDegree).get());
        jassert(bmt != nullptr);
        if (bmt->getLevel() <= _level) {
            const float lineWidth = scaleTweak * lineWidthForCurrentLevel(static_cast<float>(currentLevel), 1.f, 4.f);
            const float t0 = bmt->getPitchValue01();
            const float r1 = r * (1.f - (static_cast<float>(currentLevel) / (static_cast<float>(_maxLevel) + 1.f)));
            const float r0 = 0.1f;
            const Point<float> p00 = horagram01ToCartesian01(Point<float>(t0, 0.5f * r0));
            const Point<float> p0(p00.x + xp, p00.y + yp);
            const Point<float> p11 = horagram01ToCartesian01(Point<float>(t0, 0.5f * r1));
            const Point<float> p1(p11.x + xp, p11.y + yp);
            auto c = processor.getAppTuningModel()->colorForPitch01(bmt->getPitchValue01());
            g.setColour(c);
            g.drawLine(p0.x, p0.y, p1.x, p1.y, lineWidth);
            const float bigR0 = 0.875f * scaleTweak * processor.getAppSkin().getSmallDotRadius();
            const float lilR0 =  0.25f * scaleTweak * processor.getAppSkin().getSmallDotRadius();
            const float bigR = lineWidthForCurrentLevel(currentLevel, lilR0, bigR0);
            g.fillEllipse(Rectangle<float>(p1.x - 0.5f * bigR, p1.y - 0.5f * bigR, bigR, bigR));
        }

        // Get the microtone at the current level
        Microtone_p b = brunArray.microtoneAtIndex(currentLevel);
        // Check if the scale degree is equal to the denominator of the microtone and the current level is less than the count of the Brun array
        if (scaleDegree + 1 == b->getDenominator() && currentLevel < brunArray.count() - 1) {
            currentLevel++;
        }
    }

    g.restoreState();
}

#pragma mark - Paint Gral

/**
 * @brief Paints the Gral representation of the Brun object.
 *
 * @param processor The WilsonicProcessor object.
 * @param g The Graphics object.
 * @param bounds The bounds of the object.
 */

void Brun::_paintGral(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds)
{
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
    auto const finalGralPaintTransform = Brun::_gralPaintTransform(); // we're locked in for the rest of this method

    // Iterate over the sorted scale, draw as hexagons
    for (unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
        BrunMicrotone* note_mt = dynamic_cast<BrunMicrotone*>(microtoneAtNoteNumber(i).get());
        jassert(note_mt != nullptr);
        if(note_mt == nullptr)
            continue;
        if(note_mt->getFilterNote()) // skip filtered notes
            continue;
        
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
        float c_delta = 0.f;
        
        // If the scale degree of the microtone is not 0 or 1 and the voice is not playing, darken the color
        if (note_mt->getScaleDegree() != 0 && note_mt->getScaleDegree() != 1 && !voice_is_playing) { // darken if not octave/gen, not playing
            c_delta = -2.f;
        } else if (voice_is_playing) { // If the voice is playing, brighten the color
            c_delta = 12.f * voice_rms;
        }
        
        // Get the color based on the pitch of the microtone
        auto p01 = note_mt->getPitchValue01();
        auto c = processor.getAppTuningModel()->colorForPitch01(p01, 1.f, c_delta);
        g.setColour(c);
        g.fillPath(hexPath, hex_transform);

        float hexLineWidth = 1.f;
        if(note_mt->getScaleDegree() == 0) { // octave
            g.setColour(Colour(255,255,255));
            hexLineWidth = voice_is_playing ? 5.f * (1.f + voice_rms) : 5.f;
        } else if (note_mt->getScaleDegree() == 1) {// generator
            g.setColour(Colour(128,255,128));
            hexLineWidth = voice_is_playing ? 5.f * (1.f + voice_rms) : 5.f;
        } else {
            g.setColour(voice_is_playing ? Colours::grey.brighter(voice_rms) : Colours::grey);
            hexLineWidth = voice_is_playing ? 2.f * (1.f + 2.f * voice_rms) : 2.f;
        }
        g.strokePath(hexPath, PathStrokeType(hexLineWidth), hex_transform);

        if (AppExperiments::showDebugBoundingBox) {
            auto dc = Colours::limegreen;
            g.setColour(dc);
            g.strokePath(hexPath, PathStrokeType(1.f), hex_transform);
        }

        // Draw the text labels for the scale degree, pitch value, and note number of the microtone
        auto const fontHeight = 10.f * _gralHexScale;
        g.setFont(Font(FontOptions(fontHeight)));
        string labelStr0 = to_string(note_mt->getScaleDegree());
        string labelStr1 = to_string(static_cast<int>(1200.f * note_mt->getPitchValue01()));
        string labelStr2 = to_string(i);
        g.setColour(Colours::white);
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
    }

    g.restoreState(); // restore the state after drawing the Gral

    if (_gral_column_pattern != nullptr) {
        g.saveState(); // save the state before drawing the column pattern
        g.setColour(Colours::white);
        auto const fontHeight = 12.f;
        g.setFont(Font(FontOptions(fontHeight)));

        // Create a string for the column pattern of the Gral
        String pattern = "";
        for(unsigned long ii = 0; ii < _gral_column_pattern->size(); ii++) {
            auto p = (*_gral_column_pattern)[ii];
            pattern += String(p);
            if (ii < _gral_column_pattern->size() - 1) {
                pattern += ", ";
            }
        }
        g.drawText(pattern, bounds, Justification::topRight);
        g.restoreState(); // restore the state after drawing the column pattern
    }
}

#pragma mark - Paint Gral NPO Override

// does not paint the Brun object in a Gral, because NPO override is enabled
void Brun::_paintGralNPOOverride(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    g.saveState(); // save the state before drawing the NPO Override message
    _paintHelper(processor, g, bounds);
    g.setColour(Colours::white);
    auto const fontHeight = 16.f;
    g.setFont(Font(FontOptions(fontHeight)));
    g.drawFittedText("Can't draw Gral because\nNPO Override is enabled.\n\nDisable NPO Override to resume drawing Gral.", bounds, Justification::centred, 5);
    g.restoreState(); // restore the state after drawing the NPO Override message
}
