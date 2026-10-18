/*
  ==============================================================================

    EqualTemperament.cpp
    Created: 25 May 2022 7:58:16pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "EqualTemperament.h"
#include "TuningConstants.h"
#include "WilsonicProcessor.h"

// lifecycle

EqualTemperament::EqualTemperament()
: _npo(12)
{
    setCanNPOOverride(true);
    _updateET();
}

EqualTemperament::~EqualTemperament()
{

}

void EqualTemperament::setNPO(unsigned long npo)
{
    // lock
    const ScopedLock sl(_lock);

    jassert(npo >= minNPO);
    jassert(npo <= maxNPO);

    _npo = npo;
    _updateET();
}

unsigned long EqualTemperament::getNPO()
{
    return _npo;
}

void EqualTemperament::setPeriod(float period)
{
    // lock
    const ScopedLock sl(_lock);

    jassert(period >= TuningConstants::minPeriod);
    jassert(period <= TuningConstants::maxPeriod);
    
    setOctave(period);
    _updateET();
}

float EqualTemperament::getPeriod()
{
    return getOctave();
}

const string EqualTemperament::getParameterDescription()
{
    string retVal = "";
    retVal += "EDO: " + to_string(_npo);
    retVal += ", Period: " + to_string(getOctave());

    return retVal;
}

// drawing

bool EqualTemperament::canPaintTuning()
{
    return true;
}

void EqualTemperament::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds)
{
    // bg
    g.fillAll(processor.getAppSkin().getBgColor());

    // debug
    if (AppExperiments::showDebugBoundingBox)
    {
        // DEBUG
        g.setColour(Colours::green);
        g.drawRect(bounds, 2);
    }

    // outline, layout
    auto const x0 = bounds.getX();
    auto const intervals_width = bounds.getWidth();
    auto const y0 = bounds.getY();
    auto const line_thickness = 4;
    auto outlineColor = Colours::white;
    g.setColour(outlineColor);
    g.drawRect(bounds);

    // iterate over scale degrees
    for (auto i = 0UL; i < _npo; i++)
    {
        auto const p01 = static_cast<float>(i) / _npo;
        auto cp = processor.getAppTuningModel()->colorForPitch01(p01);
        g.setColour(cp);
        auto px = x0 + p01 * intervals_width;
        g.fillRect((int)(px - 0.5 * line_thickness), y0, line_thickness, bounds.getHeight());
        // render the octave
        if (i == 0)
        {
            px = x0 + intervals_width;
            g.fillRect((int)(px - 0.5 * line_thickness), y0, line_thickness, bounds.getHeight());
        }
    }
}

#pragma mark - Scala

String EqualTemperament::defaultScalaName()
{
    return String("edo_" + to_string (_npo) + ".scl");
}

String EqualTemperament::scalaComments()
{
    return TuningImp::scalaComments();
}

#pragma mark - update

void EqualTemperament::_updateET()
{
    // lock
    const ScopedLock sl (_lock);

    MicrotoneArray ma;
    for (auto i = 0UL; i < _npo; i++)
    {
        auto mt = make_shared<Microtone>(static_cast<float>(i) / static_cast<float>(_npo), to_string(i), Microtone::Space::LogPeriod, getOctave());
        mt->setDegreeName(to_string(i) + "\\" + to_string(_npo)); // "3\12", as in Ableton's EDO files
        ma.addMicrotone(mt);
    }
    setMicrotoneArray(ma); // calls TuningImp::update()
}
