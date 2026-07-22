/*
 ==============================================================================

 TuningImp+paint.cpp
 Created: 20 Jul 2026

 Drawing methods for TuningImp, split from TuningImp.cpp so the tuning
 numerics compile without WilsonicProcessor (same idiom as
 CPSTuningBase+paint.cpp and Brun+Gral.cpp). This file is pure code
 motion: paint() and _paintHelper() are verbatim from TuningImp.cpp.

 ==============================================================================
 */

#include "TuningImp.h"
#include "WilsonicProcessor.h"

#pragma mark - drawing

// if one were to set canPaintTuning to true, but not provide a custom paint method, this default would be called
void TuningImp::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    g.fillAll(processor.getAppSkin().getBgColor());
    g.setColour(Colours::grey);
    g.drawText(getTuningName(), bounds, Justification::centred);
}

void TuningImp::_paintHelper(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    g.fillAll(processor.getAppSkin().getBgColor());
    if (AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::mediumpurple);
        g.drawRect(bounds, 2);
        g.drawText(String(_debug_paint_counter++), bounds, Justification::topRight);
    }
}
