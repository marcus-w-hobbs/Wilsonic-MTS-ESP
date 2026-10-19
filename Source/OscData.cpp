/*
  ==============================================================================

    OscData.cpp
    Created: 14 Feb 2021 6:51:17pm
    Author:  Joshua Hodge

  ==============================================================================
*/

#include "AppTuningModel.h"
#include "OscData.h"
#include "WilsonicProcessor.h"

OscData::OscData(WilsonicProcessor& processor)
: dsp::Oscillator<float>()
, _processor (processor)
{

}

OscData::OscData(WilsonicProcessor& processor, const function<NumericType (NumericType)>& /*function*/, size_t /*lookupTableNumPoints*/)
: dsp::Oscillator<float>()
, _processor (processor)
{

}

void OscData::prepareToPlay(double sampleRate, int samplesPerBlock, int outputChannels)
{
    resetAll();
    
    dsp::ProcessSpec spec;
    spec.maximumBlockSize = (uint32)samplesPerBlock;
    spec.sampleRate = sampleRate;
    spec.numChannels = (uint32)outputChannels;
    
    prepare (spec);
    fmOsc.prepare (spec);
    gain.prepare (spec);    
    _sampleRate = sampleRate;
}

void OscData::setType(const int oscSelection)
{
    switch (oscSelection)
    {
        // Sine
        case 0:
            initialise([](float x) { return sinf (x); });
            break;
            
        // Saw
        case 1:
            initialise([] (float x) { return x / MathConstants<float>::pi; });
            break;
          
        // Square
        case 2:
            initialise([] (float x) { return x < 0.0f ? -1.0f : 1.0f; });
            break;
            
        default:
            // You shouldn't be here!
            jassertfalse;
            break;
    }
}

void OscData::setGain(const float levelInDecibels)
{
    gain.setGainDecibels(levelInDecibels);
}

// Output stage (TuningOutput.h). The key that actually sounds is the note
// plus the oscillator pitch offset, so the filter and Nyquist gates are
// re-evaluated here, which setParams reaches every block, not only at note-on.
// The offset can push the index past either end of the table; clamp in int.
void OscData::_updateFrequencyForKey()
{
    auto const key = static_cast<unsigned long>(jlimit(0, static_cast<int>(WilsonicProcessorConstants::numMidiNotes) - 1, lastMidiNote + lastPitch));
    auto const atm = _processor.getAppTuningModel();
    auto const f = atm->getOutputFrequency (key);
    bool const atOrAboveNyquist = _sampleRate > 0.0 && static_cast<double>(f) >= 0.5 * _sampleRate;
    _silent = atm->isKeyFiltered (key) || atOrAboveNyquist;
    setFrequency (f + fmModulator);
}

void OscData::setOscPitch(const int pitch)
{
    lastPitch = pitch;
    _updateFrequencyForKey();
}

void OscData::setFreq(const int midiNoteNumber)
{
    lastMidiNote = midiNoteNumber;
    _updateFrequencyForKey();
}

void OscData::setFmOsc(const float freq, const float depth)
{
    fmDepth = depth;
    fmOsc.setFrequency(freq);
    _updateFrequencyForKey();
}

void OscData::renderNextBlock(dsp::AudioBlock<float>& audioBlock)
{
    jassert(audioBlock.getNumSamples() > 0);
    if (_silent)
    {
        audioBlock.clear();
        return;
    }
    process(dsp::ProcessContextReplacing<float>(audioBlock));
    gain.process(dsp::ProcessContextReplacing<float>(audioBlock));
}

float OscData::processNextSample(float input)
{
    fmModulator = fmOsc.processSample(input) * fmDepth;
    if (_silent)
    {
        return 0.f;
    }
    return gain.processSample(processSample(input));
}

void OscData::setParams(const int oscChoice, const float oscGain, const int oscPitch, const float fmFreq, const float inFmDepth)
{
    setType(oscChoice);
    setGain(oscGain);
    setOscPitch(oscPitch);
    setFmOsc(fmFreq, inFmDepth);
}

void OscData::resetAll()
{
    reset();
    fmOsc.reset();
    gain.reset();
}
