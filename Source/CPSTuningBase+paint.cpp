/*
 ==============================================================================

 CPSTuningBase+paint.cpp
 Created: 14 Feb 2022 9:25:49pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "CPSTuningBase.h"
#include "WilsonicProcessor.h"

AffineTransform CPSTuningBase::_tuningSpaceToDeviceSpaceForBounds(Rectangle<int> bounds) {
    auto const width = bounds.getWidth();
    auto const height = bounds.getHeight();
    auto const scale = jmin(width, height);
    auto trs = AffineTransform {}; // identity
    trs = trs.scaled(scale, scale);
    trs = trs.translated(0.5f * width, 0.5f * height);
    
    return trs;
}

// subclasses override if they can paint
bool CPSTuningBase::canPaintTuning() {
    return false;
}

// TODO: optimize paint by only drawing when necessary, including first time, resized
void CPSTuningBase::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    
    // BG
    auto& skin = processor.getAppSkin();
    g.fillAll(skin.getBgColor());
    g.setColour(skin.getBgColor());

    // debug
    if(AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::lightgreen);
        g.drawRect(bounds, 1);
        g.drawText(String(_debug_paint_counter++), bounds, Justification::topRight);
    }

    // constants
    float const minBounds = jmin(bounds.getWidth(), bounds.getHeight());
    auto const boundsMin = 150.f;         // magic pixel size
    auto const boundsMax = 2 * 4 * boundsMin; // magic pixel size
    auto const boundsScale01 = jmap(minBounds, boundsMin, boundsMax, 0.f, 1.f);
    auto const lineWidth = skin.getDefaultLineWidth();
    auto const dotSmallRadius = skin.getSmallDotRadius() * (1 + boundsScale01);
    auto const dotLargeRadius = skin.getLargeDotRadius();
    auto const tuningTransform = _tuningSpaceToDeviceSpaceForBounds(bounds);
    auto const globalFontHeightMin = processor.getAppSkin().getFontHeightMin();
    auto const horizontalScale = processor.getAppSkin().getFontHorizontalScale();
    auto const fontSize = jmap(minBounds, boundsMin, boundsMax, globalFontHeightMin, globalFontHeightMin * 4);

    // lambdas

    // strokes a line with the bg color as an outline for neat breaks
    auto strokeLine = [&] (Point<float> x, Point<float> y, Colour color) {
        auto x0 = Point<float> (x); // copy
        auto y0 = Point<float> (y); // copy
        x0.applyTransform(tuningTransform);
        y0.applyTransform(tuningTransform);
        g.setColour(skin.getBgColor());
        g.drawLine(x0.x, x0.y, y0.x, y0.y, lineWidth * 3 + 1 + 1);
        g.setColour(color);
        g.drawLine(x0.x, x0.y, y0.x, y0.y, lineWidth);
    };

    // paints a filled dot, stroked with bg color
    auto fillDot = [&] (Point<float> from) {
        // caller has set color already
        auto p0 = Point<float> (from); // copy
        p0.applyTransform(tuningTransform);
        auto r = Rectangle<float> ();
        r.setSize(dotSmallRadius, dotSmallRadius);
        r.setCentre(p0);
        g.fillEllipse(r);

        // stroke with bg color
        g.setColour(skin.getBgColor());
        g.drawEllipse(r, 2);
    };

    auto strokePlayingDot = [&] (Point<float> from, float vmag) {
        auto p0 = Point<float>(from); // copy
        p0.applyTransform(tuningTransform);
        auto const dotRadius = dotSmallRadius + vmag * (dotLargeRadius - dotSmallRadius);
        auto r = Rectangle<float> ();
        r.setSize(dotRadius, dotRadius);
        r.setCentre(p0);
        Path path;
        path.addEllipse(r);
        g.strokePath(path, PathStrokeType(1.f));
    };

    // expensive calculation(experiment)
    if(AppExperiments::tuningRendererHighlightsCPSSubsets) {
        // deep immutable copy
        auto ppa = processor.getAppTuningModel()->getTuning()->getProcessedArray();
        for(auto label : _labelArray) {
            label->isSubsetOfProcessorTuning = false;
            auto lmt = *label->mt->clone();
            lmt.octaveReduce();
            auto const p = lmt.getPitchValue01();
            auto const e = 0.001;
            for(unsigned long i = 0; i < ppa.count(); i++) {
                auto mt = ppa.microtoneAtIndex(i);
                auto const pmt = mt->getPitchValue01();
                auto const d = fabsf(p - pmt);
                if(d <= e) {
                    label->isSubsetOfProcessorTuning = true;
                    break;
                }
            }
        }
    }

    // COMPOSITE

    // line segments
    for(auto line : _lineArray) {
        auto x = get<0> (line);
        auto y = get<1> (line);

        // will be on [0,1]
        auto const p01 = fabsf(x->mt->getPitchValue01() - y->mt->getPitchValue01());
        auto intervalColor = Colour();
        if(AppExperiments::tuningRendererCPSIntervalsAsPitchColor) {
            intervalColor = processor.getAppTuningModel()->colorForPitch01(p01);
        } else {
            intervalColor = skin.getCPSIntervalColour();
        }

        // TODO: some tunings are "all dark" because no line segments meet this condition
        if(! x->isSubsetOfProcessorTuning || ! y->isSubsetOfProcessorTuning) {
            intervalColor = processor.getAppTuningModel()->colorForPitch01(p01, 1.f, -3);
        }

        // finally
        strokeLine(x->pt, y->pt, intervalColor);
    }

    // dots
    for(auto dot : _labelArray) {
        auto const p = dot->mt->getPitchValue01();
        auto c = processor.getAppTuningModel()->colorForPitch01(p);
        if(AppExperiments::tuningRendererHighlightsCPSSubsets) {
            if (! dot->isSubsetOfProcessorTuning) {
                c = c.darker(AppExperiments::tuningRendererCPSNonSubsetDarkenAmount);
            }
        }
        g.setColour(c);
        fillDot(dot->pt);
    }

    // labels
    //TODO: hook up to ui
    auto const displayFactors = false;
    g.setFont(Font(FontOptions(fontSize)).withHorizontalScale(horizontalScale));
    auto center = Point<float>(_p0->pt); // copy
    center.applyTransform(tuningTransform);
    for(auto label : _labelArray) {
        // vector for stack of text at a point near a tuning point
        auto hp = Point<float> (label->pt); // copy
        hp.applyTransform(tuningTransform);
        auto const vec = hp - center;
        auto const mag = hp.getDistanceFrom(center);
        auto const magic_radius = 1.5;
        auto normalized = Point<float>();
        if(mag <= 1.f) {
            // points in the center need a hard-coded unit vector
            normalized = Point<float> (0, -1 * magic_radius);
        } else {
            // otherwise normalize
            normalized = vec / (mag * (1 / magic_radius));
        }

        // color
        auto const p01 = label->mt->getPitchValue01();
        auto c = processor.getAppTuningModel()->colorForPitch01(p01);
        if (! label->isSubsetOfProcessorTuning) {
            c = c.darker(AppExperiments::tuningRendererCPSNonSubsetDarkenAmount);
        }
        g.setColour(c);

        // text rect...draw ABC
        auto ffr = Rectangle<float> (9 * fontSize, fontSize);
        auto ff = hp + normalized * fontSize;
        ffr.setCentre(ff);
        g.drawText(label->mt->getShortDescriptionText(), ffr, Justification::centred);

        // draw ABC + A*B*C + float
        if(displayFactors) {
            auto const yComponent = (hp.y > (0.5 * bounds.getHeight())) ? 1.f : -1.f;
            auto const textVec = Point<float> (0, yComponent);
            auto const fff = ff + fontSize * textVec;
            auto fffr = Rectangle<float> (9 * fontSize, fontSize);
            fffr.setCentre(fff);
            g.drawText(label->mt->getShortDescriptionText3(), fffr, Justification::centred);
        }
    }

    float const tolerance = 0.001f;

#if JucePlugin_IsSynth
    // optimization
    auto vs = processor.getVoiceStates();
    auto const no_notes_playing = vs.noVoicesPlaying();
    if(no_notes_playing) {
        return;
    }

    // stroke playing cps dot
    if(AppExperiments::tuningRendererPlayingNotes) {
        // draw a dynamic line+dot for each microtone based on voice amplitude
        for(unsigned long i = 0; i < WilsonicProcessorConstants::numVoices; i++) {
            auto v = vs.voiceState[i];
            auto const nnv = v.nn;
            auto const vmag = v.rms;

            // only render if the velocity is above tolerance
            if(vmag > 0) {
                // get the microtone of the app tuning(implies the global, i.e., keyboard's tuning)
                auto const mtv = processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(nnv);
                if(mtv->getFilterNote())
                    continue;
                auto const mtvp = mtv->getPitchValue01();

                // loop through this tuning's _labelArray
                for(auto dot : _labelArray) {
                    auto dot_mt = dot->mt;
                    dot_mt->octaveReduce();
                    auto const dot_mt_p = dot_mt->getPitchValue01();
                    if(fabsf(dot_mt_p - mtvp) <= tolerance) {
                        g.setColour(processor.getAppTuningModel()->colorForPitch01(dot_mt_p));
                        strokePlayingDot(dot->pt, vmag);
                    }
                }
            }
        }
    }
#elif JucePlugin_IsMidiEffect
    for(unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
        float const rms = processor.getKeyboardRMSForNN(i);
        if(rms > 0.f) {
            auto const mtv = processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(i);
            if(mtv->getFilterNote())
                continue;
            auto const mtvp = mtv->getPitchValue01();

            // loop through this tuning's _labelArray
            for(auto dot : _labelArray) {
                auto dot_mt = dot->mt;
                dot_mt->octaveReduce();
                auto const dot_mt_p = dot_mt->getPitchValue01();
                if(fabsf(dot_mt_p - mtvp) <= tolerance) {
                    g.setColour(processor.getAppTuningModel()->colorForPitch01(dot_mt_p));
                    strokePlayingDot(dot->pt, 0.4f * rms); // magic
                }
            }
        }
    }
#else
    jassertfalse;
#endif
}
