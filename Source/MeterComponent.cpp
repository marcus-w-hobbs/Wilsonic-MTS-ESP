/*
  ==============================================================================

    MeterComponent.cpp
    Created: 27 Feb 2021 2:11:36am
    Author:  Joshua Hodge

  ==============================================================================
*/

#include <JuceHeader.h>
#include "MeterComponent.h"

MeterComponent::MeterComponent (WilsonicProcessor& p) : processor (p)
{

}

MeterComponent::~MeterComponent()
{

}

void MeterComponent::paintOverChildren (Graphics& g)
{
    auto bounds = getLocalBounds().reduced (20, 35).translated (0, 10);
    auto leftMeter = bounds.removeFromTop (bounds.getHeight() / 2).reduced (0, 5);
    auto rightMeter = bounds.reduced (0, 5);
    
    g.setColour (Colour::fromRGB (247, 190, 67));
    const atomic<float>& rms = processor.getRMS();
    auto rmsLevel = jmap<float> (rms.load(), 0.0f, 1.0f, 0.1f, leftMeter.getWidth());
    
    g.fillRoundedRectangle (leftMeter.getX(), leftMeter.getY(), rmsLevel, leftMeter.getHeight(), 5);
    g.fillRoundedRectangle (rightMeter.getX(), rightMeter.getY(), rmsLevel, rightMeter.getHeight(), 5);
    
    g.setColour (Colour::fromRGB (246, 87, 64).withAlpha (0.5f));
    const atomic<float>& peak = processor.getPeak();
    auto peakLevel = jmap<float> (peak.load(), 0.0f, 1.0f, 0.1f, leftMeter.getWidth());
    
    g.fillRoundedRectangle (leftMeter.getX(), leftMeter.getY(), peakLevel, leftMeter.getHeight(), 5);
    g.fillRoundedRectangle (rightMeter.getX(), rightMeter.getY(), peakLevel, rightMeter.getHeight(), 5);
    
    g.setColour (Colours::white);
    g.drawRoundedRectangle (leftMeter.toFloat(), 5, 2.0f);
    g.drawRoundedRectangle (rightMeter.toFloat(), 5, 2.0f);
}

void MeterComponent::resized()
{
   
}
