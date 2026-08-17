/*
 ==============================================================================

 WilsonicPitchWheelComponent.cpp
 Created: 15 May 2021 4:34:18pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "WilsonicPitchWheelComponent.h"
#include "AppExperiments.h"
#include "AppTuningModel.h"
#include "Microtone.h"
#include "VoiceStates.h"
#include "WilsonicProcessorConstants.h"

#pragma mark - lifecycle

WilsonicPitchWheelComponent::WilsonicPitchWheelComponent(WilsonicProcessor& processor, bool updateBasedOnSynth)
: WilsonicComponentBase(processor)
, _updateBasedOnAppTuningSynthNotes(updateBasedOnSynth) {
    _timerHelper();
}

WilsonicPitchWheelComponent::~WilsonicPitchWheelComponent() {
    stopTimer();
}

#pragma mark - drawing

void WilsonicPitchWheelComponent::paint(Graphics& g) {
    g.fillAll(_processor.getAppSkin().getBgColor());
    if(AppExperiments::showDebugBoundingBox) {// DEBUG
        g.setColour(Colours::lightgreen);
        g.drawRect(getLocalBounds(), 1);
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
    _paint04(g);
}

/**
 * @brief Visualizes proportional triads
 * @param g Graphics context
 */
void WilsonicPitchWheelComponent::_paint04(Graphics& g) {
    if(_tuning == nullptr) { // If tuning is null, draw "No Tuning" and return
        g.setColour(Colours::grey);
        g.drawText ("No Tuning", getLocalBounds(), Justification::centred);

        return;
    }

    auto& skin = _processor.getAppSkin();
    auto ma = _tuning->getProcessedArrayNPO(); // returns deep copy
    if(ma.count() == 0) {// If tuning is empty, draw "0" and return
        g.setColour(Colours::grey);
        g.drawText ("0", getLocalBounds(), Justification::centred);
        return;
    }

    // layout parameters
    auto const globalFontHeightMin = skin.getFontHeightMin() * _customFontScale;
    auto const horizontalScale = skin.getFontHorizontalScale();
    auto const area = getLocalBounds();
    auto const x0 = 0.5f * area.getWidth();
    auto const y0 = 0.5f * area.getHeight();
    auto const dimension = jmin(area.getWidth(), area.getHeight());
    auto const margin = 0.78f;
    auto const radius00 = (_drawText ? 0.52f : 1.f) * 0.5f * margin * dimension;
    auto const radius10 = (1.00f) * 0.5f * margin * dimension;
    auto const lineSmallThickness = 2.f;
    auto const lineLargeThickness = lineSmallThickness;
    auto const dotSmallRadius = skin.getSmallDotRadius();
    auto const dotLargeRadius = skin.getLargeDotRadius();
    constexpr float pi = 3.14159265358979323846f;
    auto const pitchOffset = -1 * pi;

    // Define lambda functions for sin/cos
    // Function for calculating the x-coordinate of a point on a circle
    auto sx = [&](auto radius, auto pitch) -> float {
        return x0 + radius * sinf(2 * pi * -pitch + pitchOffset);
    };

    // Function for calculating the y-coordinate of a point on a circle
    auto cy = [&](auto radius, auto pitch) -> float {
        return y0 + radius * cosf(2 * pi * -pitch + pitchOffset);
    };

    // Define lambda function for drawing a line from origin to the dot
    // This function takes a microtone and a velocity magnitude as parameters
    auto draw = [&](auto& mt, auto vmag) -> void {
        // Get colour based on microtone pitch
        auto const p = mt->getPitchValue01();
        auto const colour = _processor.getAppTuningModel()->colorForPitch01(p);
        g.setColour(colour);

        // Draw line
        auto const x1 = sx(radius00, p);
        auto const y1 = cy(radius00, p);
        auto const lineThickness = lineSmallThickness + vmag * (lineLargeThickness - lineSmallThickness);
        g.drawLine(x0, y0, x1, y1, lineThickness);

        // Draw dot at end of line
        auto r = Rectangle<float> ();
        r.setSize(dotSmallRadius, dotSmallRadius);
        r.setCentre(Point<float> (x1, y1));
        g.fillEllipse(r);

        // Stroke playing dot
        auto rp = Rectangle<float>();
        auto dotRadius = dotSmallRadius + vmag * (dotLargeRadius - dotSmallRadius);
        rp.setSize(dotRadius, dotRadius);
        rp.setCentre(Point<float> (x1, y1));
        Path path;
        path.addEllipse(rp);
        g.strokePath(path, PathStrokeType(1.f));

        // Define a lambda function for drawing text on the pitch wheel
        // This function takes a text string, a minimum length for the text, and a radius as parameters
        auto drawText = [&](auto text, int minLen, auto radius01) {
            // Only draw text if it is not empty
            if(text.length() > 0) {
                // Calculate the x and y coordinates for the text based on the radius and pitch
                auto const x2 = sx(radius01 * radius10, p);
                auto const y2 = cy(radius01 * radius10, p);
                
                // Calculate the numerator for the font height calculation
                // This value is interpolated between 2 and 5 based on the radius
                auto magicNumerator = 2.f + (5.f - 2.f) * radius01; // / dimension; // < this is a start, but not in screen width
                magicNumerator *= 0.4f;
                
                // The denominator for the font height calculation is constant
                auto const magicDenominator = 1.f;
                
                // Ensure the text is at least minLen characters long
                auto shortDesc = String(text);
                auto strLen = jmax(int(shortDesc.length()), minLen); // [3, len]
                
                // Calculate the width of the text box based on the length of the text
                auto w = jmax(strLen * globalFontHeightMin, globalFontHeightMin); // [9, 9 * strlen]
                
                // Calculate the font height based on the width of the text box and the magic numbers
                auto fontHeight = jmax(globalFontHeightMin, (w * magicNumerator / (strLen * magicDenominator))); // [
                
                // Set the font for the text
                g.setFont(Font(FontOptions(fontHeight)).withHorizontalScale(horizontalScale));
                
                // Create a rectangle for the text box and set its center
                auto dr = Rectangle<float> (w, fontHeight);
                dr.setCentre(Point<float> (x2, y2));
                
                // Draw the text in the text box, centered
                g.drawText(shortDesc, dr, Justification::centred);
            }
        };

        // Draw the microtone descriptions
        auto const minLen = 9;
        if(_drawText) {
            drawText(mt->getShortDescriptionText(),  minLen, 0.70f);
            drawText(mt->getShortDescriptionText3(), minLen, 0.95f);
            drawText(mt->getShortDescriptionText2(), minLen, 1.20f);
        }
    };

    // Check if proportional triads are to be shown on pitch wheel
    // Proportional triads are a type of musical chord, which are to be visualized on the pitch wheel
    if(AppExperiments::showProportionalTriadsOnPitchWheel) {
        // Get the note number for Middle C from the tuning
        auto const nn60 = _tuning->getNoteNumberMiddleC();

        // Define a lambda function for drawing a dot for a degree of a triad
        // This function takes a scale degree and a radius as parameters
        auto aat = [&](auto scaleDegree, auto r) -> void {
            // Calculate the note number for the root of the triad
            auto const nnRoot = nn60 + scaleDegree;
            // Get the microtone at the root note number
            auto mt = _tuning->microtoneAtNoteNumber(nnRoot);
            if(mt->getFilterNote()) // skip filtered notes
                return;
            // Get the pitch value for the microtone
            auto const pitch = mt->getPitchValue01();
            // Calculate the x and y coordinates for the dot based on the radius and pitch
            auto const x = sx(r, pitch);
            auto const y = cy(r, pitch);
            // Create a rectangle for the dot and set its center
            auto rect = Rectangle<float>();
            rect.setSize(dotSmallRadius, dotSmallRadius);
            rect.setCentre(Point<float> (x, y));
            // Draw the dot
            g.fillEllipse(rect);
        };

        // Set the color for the proportional triad dots
        g.setColour(skin.getProportionalTriadDotColour());
        // Calculate the radius for the proportional and subcontrary triad dots
        auto const radius20 = (0.67f) * 0.5f * margin * dimension; // dot: proportional triad scale degree
        auto const radius21 = (0.80f) * 0.5f * margin * dimension; // dot: subcontrary triad scale degree
        // Draw dots for each degree of each proportional triad
        for(auto triad : _tuning->getProportionalTriads()) {
            aat(triad.getRoot(), radius20);
            aat(triad.getThird(), radius20);
            aat(triad.getFifth(), radius20);
        }
        // Set the color for the subcontrary triad dots
        g.setColour(skin.getSubcontraryTriadDotColour());
        // Draw dots for each degree of each subcontrary triad
        for(auto triad : _tuning->getSubcontraryTriads()) {
            aat(triad.getRoot(), radius21);
            aat(triad.getThird(), radius21);
            aat(triad.getFifth(), radius21);
        }
    }

    // Draw a constant line+dot for each microtone(min line width)
    for(int i = static_cast<int>(ma.count()) - 1; i >= 0; i--) {
        auto const mt = ma.microtoneAtIndex(static_cast<unsigned long>(i));
        draw(mt, 0.f);// Draw microtone with rms 0
    }

    auto const tolerance = 0.001f; // technically the tolerance comparison should be in pitch space

#if JucePlugin_IsSynth
    auto vs = _processor.getVoiceStates();
    if(vs.noVoicesPlaying()) { // If no voices are playing, return
        return;
    }

    // If drawing playing notes
    if(_updateBasedOnAppTuningSynthNotes) {
        // Draw a dynamic line+dot for each microtone based on voice amplitude
        for(unsigned long i = 0; i < WilsonicProcessorConstants::numVoices; i++) {
            auto v = vs.voiceState[i];
            auto nnv = v.nn;
            auto vmag = v.rms;
            // Only render if the velocity is above tolerance
            if(vmag > 0) {
                // Get the microtone of the app tuning(implies the global, i.e., keyboard's tuning)
                auto mtv = _processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(nnv);
                if(mtv->getFilterNote())
                    continue;
                // Loop through *this instance of pitch wheel's tuning* for equivalent frequency value microtones
                // For some pages the happy path is the global and this pitch wheel are the same tuning
                for(unsigned long ii = 0; ii < ma.count(); ii++) {
                    auto mt = ma.microtoneAtIndex(ii);
                    if(fabsf(mtv->getPitchValue01() - mt->getPitchValue01()) < tolerance) {
                        draw(mtv, vmag);
                        //DBG("nn:"+String(nnv)+", rms:"+String(vmag));
                    }
                }
            }
        }
    }
#elif JucePlugin_IsMidiEffect
    // For each midi note
    for (unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
        float const vmag = _processor.getKeyboardRMSForNN(i);
        // If velocity is above 0
        if (vmag > 0.f) {
            // Get the microtone of the app tuning
            auto mtv = _processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(i);
            if(mtv->getFilterNote())
                continue;

            // Loop through *this instance of pitch wheel's tuning* for equivalent frequency value microtones
            // For some pages the happy path is the global and this pitch wheel are the same tuning
            for(unsigned long ii = 0; ii < ma.count(); ii++) {
                auto mt = ma.microtoneAtIndex(ii);
                if(fabsf(mtv->getPitchValue01() - mt->getPitchValue01()) < tolerance) {
                    draw(mtv, vmag);
                    //DBG("nn:"+String(nnv)+", rms:"+String(vmag));
                }
            }
        }
    }
#else
    // If not a synth or midi effect, assert false
    jassertfalse;
#endif
}

/**
 * @brief Resizes the component
 */
void WilsonicPitchWheelComponent::resized()
{
    // nop
}

/**
 * @brief Sets whether to update based on app tuning synth notes
 * @param update Whether to update
 */
void WilsonicPitchWheelComponent::setUpdateBasedOnAppTuningSynthNotes(bool update)
{
    _updateBasedOnAppTuningSynthNotes = update;
    _timerHelper();
}

/**
 * @brief Helper function for timer
 */
void WilsonicPitchWheelComponent::_timerHelper() {
    // If tuning is null or not updating based on app tuning synth notes, stop timer and return
    if(_tuning == nullptr || !_updateBasedOnAppTuningSynthNotes) {
        stopTimer();
        return;
    }
    
    // If updating based on app tuning synth notes
    if(_updateBasedOnAppTuningSynthNotes) {
        auto const npo = _tuning->getProcessedArrayNPOCount();
        auto const hz = AppExperiments::getFrameRateForNPO(npo);
        // If hz is greater than 0, start timer
        if(hz > 0) {
//            DBG ("WilsonicPitchWheelComponent timer STARTED for npo:" << npo << ", hz: " << hz);
            startTimerHz(hz);
        } else {// Else, stop timer
            DBG ("WilsonicPitchWheelComponent timer STOPPED for npo:" << npo << ", hz: " << hz);
            stopTimer();
        }
    }
}

/**
 * @brief Sets the custom font scale
 * @param scale01 The scale to set
 */
void WilsonicPitchWheelComponent::setCustomFontScale(float scale01) {
    // If custom font scale is not equal to the input scale, set it and repaint
    if(WilsonicMath::floatsAreNotEqual(_customFontScale, scale01)) {
        _customFontScale = scale01;
        repaint();
    }
}

/**
 * @brief Sets whether to draw text
 * @param draw_text Whether to draw text
 */
void WilsonicPitchWheelComponent::setDrawText(bool draw_text) {
    _drawText = draw_text;
    repaint();
}

/**
 * @brief Sets the tuning
 * @param inputTuning The tuning to set
 */
void WilsonicPitchWheelComponent::setTuning(shared_ptr<Tuning> inputTuning) {
    _tuning = inputTuning;
    _timerHelper();
    repaint();
}

/**
 * @brief Callback function for timer
 */
void WilsonicPitchWheelComponent::timerCallback() {
    // If component is showing, repaint
    if(isShowing()) {
        repaint();
    }
}
