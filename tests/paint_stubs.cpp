// Tests-only no-op definitions for paint methods whose real bodies live in
// TuningImp+paint.cpp and Brun+Paint.cpp (which require WilsonicProcessor /
// JUCE Graphics and are NOT linked into the test binaries). Linking these
// satisfies the vtables; no test exercises painting.

#include "../Source/Brun.h"
#include "../Source/TuningImp.h"

void TuningImp::paint(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
void TuningImp::_paintHelper(WilsonicProcessor&, Graphics&, Rectangle<int>) {}

bool Brun::canPaintTuning() { return false; }
void Brun::paint(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
void Brun::_paintCartesian(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
void Brun::_paintHorogram(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
void Brun::_paintInverseHorogram(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
void Brun::_paintGral(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
void Brun::_paintGralNPOOverride(WilsonicProcessor&, Graphics&, Rectangle<int>) {}
