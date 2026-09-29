/*
 ==============================================================================

 TuningRendererComponent.cpp
 Created: 3 Feb 2022 8:50:43pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "TuningRendererComponent.h"
#include "AppExperiments.h"
#include "AppTuningModel.h"
#include "Microtone.h"
#include "VoiceStates.h"
#include "WilsonicProcessorConstants.h"

#pragma mark - lifecycle

TuningRendererComponent::TuningRendererComponent(WilsonicProcessor& processor, bool updateBasedOnSynth)
: WilsonicComponentBase(processor)
, _updateBasedOnAppTuningSynthNotes(updateBasedOnSynth)
{
    _timerHelper();
}

TuningRendererComponent::~TuningRendererComponent()
{
    stopTimer();
}

#pragma mark - drawing

void TuningRendererComponent::paint(Graphics& g)
{
    g.fillAll(_processor.getAppSkin().getBgColor());

    if(AppExperiments::showDebugBoundingBox)
    {
        // DEBUG
        g.setColour(Colours::green);
        g.drawRect(getLocalBounds(), 2);

        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }

    // if the tuning can paint itself

    if(_tuning != nullptr && _tuning->canPaintTuning())
    {
        _tuning->paint(_processor, g, getLocalBounds());
        return;
    }

    // default is to paint pitch wheel
    _paint04(g);
}

void TuningRendererComponent::resized()
{
    // nop
}

void TuningRendererComponent::_paint04(Graphics& g) {
    g.fillAll(_processor.getAppSkin().getBgColor()); // bg
    if(_tuning == nullptr) { // NOP
        return;
    }

    // copy tuning's processedArray
    auto ma = MicrotoneArray(_tuning->getProcessedArrayNPO());

    // empty tuning is a "null" symbol
    if(ma.count() == 0) {
        g.setColour(Colours::grey);
        g.drawText ("0", getLocalBounds(), Justification::centred);
        
        return;
    }

    // Layout
    auto const globalFontHeightMin = _processor.getAppSkin().getFontHeightMin() * _customFontScale;
    auto const horizontalScale = _processor.getAppSkin().getFontHorizontalScale();
    auto const area = getLocalBounds();
    auto const x0 = 0.5f * area.getWidth();
    auto const y0 = 0.5f * area.getHeight();
    auto const dimension = jmin(area.getWidth(), area.getHeight());
    auto const margin = 0.78f;
    auto const radius00 = (0.52f) * 0.5f * margin * dimension; // dot: scale degree
    auto const radius10 = (1.00f) * 0.5f * margin * dimension; // text
    auto const lineSmallThickness = 2.f;
    auto const lineLargeThickness = lineSmallThickness;
    auto const dotSmallRadius = 13.f;
    auto const dotLargeRadius = 16.f * dotSmallRadius;
    constexpr float pi = 3.14159265358979323846f;
    auto const pitchOffset = -1.f * pi;

    // LAMBDA for sin/cos
    auto sx = [&](auto radius, auto pitch) -> float {
        
        return x0 + radius * sinf(2.f * pi * -pitch + pitchOffset);
    };

    auto cy = [&](auto radius, auto pitch) -> float {
        
        return y0 + radius * cosf(2.f * pi * -pitch + pitchOffset);
    };

    // LAMBDA for drawing a line from origin to the dot
    auto draw = [&](auto& mt, auto vmag) -> void {
        // get colour based on microtone pitch
        auto const p01 = mt->getPitchValue01();
        auto const colour = _processor.getAppTuningModel()->colorForPitch01(p01);
        g.setColour(colour);

        // draw line
        auto const x1 = sx(radius00, p01);
        auto const y1 = cy(radius00, p01);
        auto const lineThickness = lineSmallThickness + vmag * (lineLargeThickness - lineSmallThickness);
        g.drawLine(x0, y0, x1, y1, lineThickness);

        // draw dot at end of line
        auto r = Rectangle<float>();
        r.setSize(dotSmallRadius, dotSmallRadius);
        r.setCentre(Point<float> (x1, y1));
        g.fillEllipse(r);

        // stroke playing dot
        auto rp = Rectangle<float>();
        auto dotRadius = dotSmallRadius + vmag * (dotLargeRadius - dotSmallRadius);
        rp.setSize(dotRadius, dotRadius);
        rp.setCentre(Point<float> (x1, y1));
        Path path;
        path.addEllipse(rp);
        g.strokePath(path, PathStrokeType(1.f));

        // lambda for text
        auto drawText = [&](auto text, int minLen, auto radius01) {
            if(text.empty()) {
                
                return;
            }
            auto const x2 = sx(radius01 * radius10, p01);
            auto const y2 = cy(radius01 * radius10, p01);
            auto strLen = jmax(int(text.length()), minLen); 
            auto w = jmax(strLen * globalFontHeightMin, globalFontHeightMin); 
            auto fontHeight = jmax(globalFontHeightMin, w * (2.f + 3.f * radius01 * 0.4f)); 
            g.setFont(Font(FontOptions(fontHeight)).withHorizontalScale(horizontalScale));
            g.drawText(text, Rectangle<float> (w, fontHeight).withCentre(Point<float> (x2, y2)), Justification::centred);
        };

        // draw the microtone descriptions
        auto const minLen = 9;
        drawText(mt->getShortDescriptionText(),  minLen, 0.70f);
        drawText(mt->getShortDescriptionText3(), minLen, 0.95f);
        drawText(mt->getShortDescriptionText2(), minLen, 1.20f);
    };

    // proportional triads experiment
    if(AppExperiments::showProportionalTriadsOnPitchWheel) {
        auto const nn60 = _tuning->getNoteNumberMiddleC();

        // lambda for drawing a dot for a degree of a triad
        auto aat = [&](auto scaleDegree, auto r) -> void {
            auto const nnRoot = nn60 + scaleDegree;
            auto const mt = _tuning->microtoneAtNoteNumber(nnRoot);
            if(mt->getFilterNote())
                return;
            auto const pitch = mt->getPitchValue01();
            auto const x = sx(r, pitch);
            auto const y = cy(r, pitch);
            auto rect = Rectangle<float>();
            rect.setSize(dotSmallRadius, dotSmallRadius);
            rect.setCentre(Point<float> (x, y));
            g.fillEllipse(rect);
        };

        // draw tick marks for aesthetic analysis
        g.setColour(_processor.getAppSkin().getProportionalTriadDotColour());
        auto const radius20 = (0.67f) * 0.5f * margin * dimension; // dot: proportional triad scale degree
        auto const radius21 = (0.80f) * 0.5f * margin * dimension; // dot: subcontrary triad scale degree
        for(auto triad : _tuning->getProportionalTriads()) {
            aat(triad.getRoot(), radius20);
            aat(triad.getThird(), radius20);
            aat(triad.getFifth(), radius20);
        }
        g.setColour(_processor.getAppSkin().getSubcontraryTriadDotColour());
        for(auto triad : _tuning->getSubcontraryTriads()) {
            aat(triad.getRoot(), radius21);
            aat(triad.getThird(), radius21);
            aat(triad.getFifth(), radius21);
        }
    }

    // draw a constant line+dot for each microtone(min line width)
    for(unsigned long i = ma.count() - 1; i >= 0; i--) {
        auto const mt = ma.microtoneAtIndex(i);
        draw(mt, 0.f); // LAMBDA mt, rms 0
    }

#if JucePlugin_IsSynth
    // optimization
    auto vs = _processor.getVoiceStates();
    if(vs.noVoicesPlaying()) {
        return;
    }

    // render playing notes
    if(_updateBasedOnAppTuningSynthNotes) {
        // draw a dynamic line+dot for each microtone based on voice amplitude
        for(unsigned long i = 0; i < WilsonicProcessorConstants::numVoices; i++) {
            // experiment plumbing _appTuning into pitch wheel
            auto tolerance = 0.001f; // technically the tolerance comparison should be in pitch space
            auto v = vs.voiceState[i];
            auto nnv = v.nn;
            auto vmag = v.rms;

            // only render if the velocity is above 0
            if(vmag > 0) {
                // get the microtone of the app tuning(implies the global, i.e., keyboard's tuning)
                auto mtv = _processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(nnv);
                if(mtv->getFilterNote()) // skip filtered notes
                    continue;
                // loop through *this instance of pitch wheel's tuning* for equivalent frequency value microtones
                // for some pages the happy path is the global and this pitch wheel are the same tuning
                // in cps this illuminate subsets!
                for(unsigned long ii = 0; ii < ma.count(); ii++) {
                    auto mt = ma.microtoneAtIndex(ii);
                    if(fabsf(mtv->getFrequencyValue() - mt->getFrequencyValue()) < tolerance) {
                        draw(mtv, vmag);
                    }
                }
            }
        }
    }
#elif JucePlugin_IsMidiEffect
    // render playing notes
    if(_updateBasedOnAppTuningSynthNotes) {
        // draw a dynamic line+dot for each microtone based on voice amplitude
        for(unsigned long nn = 0; nn < WilsonicProcessorConstants::numMidiNotes; nn++) {
            // experiment plumbing _appTuning into pitch wheel
            auto const tolerance = 0.001f; // technically the tolerance comparison should be in pitch space
            auto const vmag = _processor.getKeyboardRMSForNN(nn);

            // only render if the velocity is above 0
            if(vmag > 0) {
                // get the microtone of the app tuning(implies the global, i.e., keyboard's tuning)
                auto mtv = _processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(nn);
                if(mtv->getFilterNote()) // skip filtered notes
                    continue;

                // loop through *this instance of pitch wheel's tuning* for equivalent frequency value microtones
                // for some pages the happy path is the global and this pitch wheel are the same tuning
                // in cps this illuminate subsets!
                for(unsigned long ii = 0; ii < ma.count(); ii++) {
                    auto mt = ma.microtoneAtIndex(ii);
                    if(fabsf(mtv->getFrequencyValue() - mt->getFrequencyValue()) < tolerance) {
                        draw(mtv, vmag);
                    }
                }
            }
        }
    }

#else
    jassertfalse;
#endif
}

#pragma mark - methods

void TuningRendererComponent::setUpdateBasedOnAppTuningSynthNotes(bool update) {
    _updateBasedOnAppTuningSynthNotes = update;
    _timerHelper();
}

void TuningRendererComponent::_timerHelper() {
    stopTimer();
    if(_tuning == nullptr || !_updateBasedOnAppTuningSynthNotes) {
        
        return;
    }

    if(_updateBasedOnAppTuningSynthNotes) {
        auto const npo = _tuning->getProcessedArrayNPOCount();
        auto const hz = AppExperiments::getFrameRateForNPO(npo);
        if(hz > 0) {
            //DBG ("TuningRendererComponent timer STARTED for npo:" << npo << ", hz: " << hz);
            startTimerHz(hz);
        } else {
            //DBG ("TuningRendererComponent timer STOPPED for npo:" << npo << ", hz: " << hz);
            stopTimer();
        }
    }
}

// 1 = default logic
void TuningRendererComponent::setCustomFontScale(float scale01) {
    if(WilsonicMath::floatsAreNotEqual(_customFontScale, scale01)) {
        _customFontScale = scale01;
        repaint();
    }
}

#pragma mark - Tuning

void TuningRendererComponent::setTuning(shared_ptr<Tuning> inputTuning) {
    _tuning = inputTuning;
    _timerHelper();
    repaint();
}

#pragma mark - Timer

void TuningRendererComponent::timerCallback() {
    if(isShowing()) {
        repaint();
    }
}
