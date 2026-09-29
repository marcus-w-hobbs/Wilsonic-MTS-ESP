/*
  ==============================================================================

    CustomComponent.cpp
    Created: 20 Feb 2021 9:51:27am
    Author:  Joshua Hodge

  ==============================================================================
*/

#include <JuceHeader.h>
#include "CustomComponent.h"

using SliderAttachment = AudioProcessorValueTreeState::SliderAttachment;
using SliderStyle = Slider::SliderStyle;

SliderWithLabel::SliderWithLabel (String labelName, String paramId, shared_ptr<AudioProcessorValueTreeState> apvts, const int width, const int height, SliderStyle style)
{
    sliderWidth = width;
    sliderHeight = height;
    
    slider.setSliderStyle (style);
    slider.setTextBoxStyle (Slider::TextBoxBelow, true, textBoxWidth, textBoxHeight);
    addAndMakeVisible (slider);
    
    label.setFont (Font (FontOptions (fontHeight)));
    label.setText (labelName, dontSendNotification);
    label.setJustificationType (Justification::centred);
    addAndMakeVisible (label);
    
    attachment = make_unique<SliderAttachment>(*apvts,  paramId,  slider);
}

void SliderWithLabel::resized()
{
    auto const dialToLabelRatio = 15;
    auto const labelHeight = 18;
    
    jassert (sliderWidth > 0);
    jassert (sliderHeight > 0);
    
    label.setBounds (0, 0, sliderWidth, labelHeight);
    slider.setBounds (0, 0 + dialToLabelRatio, sliderWidth, sliderHeight);
}


CustomComponent::CustomComponent()
{

}

CustomComponent::~CustomComponent()
{
    
}

#pragma mark - drawing

void CustomComponent::paint (Graphics& g)
{
    g.fillAll (Colours::black);
    auto bounds = getLocalBounds();
    g.setColour (boundsColour);
    g.drawRoundedRectangle (bounds.toFloat().reduced (10.0f), 5.0f, 2.0f);
    
    g.setColour (Colours::yellow);
    g.setFont (fontHeight);
    g.setFont (g.getCurrentFont().boldened());
    
    jassert (_name.isNotEmpty());
    g.drawText (_name, 20, 15, 100, 25, Justification::left);
}

void CustomComponent::resized()
{

}

