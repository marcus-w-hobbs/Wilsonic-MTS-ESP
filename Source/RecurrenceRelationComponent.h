/*
  ==============================================================================

    RecurrenceRelationComponent.h
    Created: 21 Mar 2022 9:28:45pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "AppTuningModel.h"
#include "BubbleDrawable.h"
#include "DeltaComboBox.h"
#include "RecurrenceRelationCoefficientComponent.h"
#include "RecurrenceRelationSeedComponent.h"
#include "SeedSlider.h"
#include "WilsonicAppTuningComponent.h"
#include "WilsonicPitchWheelComponent.h"
#include "WilsonicProcessor.h"

class RecurrenceRelationComponent
: public WilsonicAppTuningComponent
, private ActionListener
{
    // lifecycle
public:
    RecurrenceRelationComponent(WilsonicProcessor&);
    ~RecurrenceRelationComponent() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(RecurrenceRelationComponent)

public:
    // UI
    void paint(Graphics&) override;
    void resized() override;

    // tuning title
    const string getAppTuningTitle() override;

    // ActionListener callback
    void actionListenerCallback(const String&) override;

private:
    // private members
    CriticalSection _lock;
    BubbleDrawable _coefficientBubble;
    unique_ptr<RecurrenceRelationCoefficientComponent> _coefficientSliderComponent;
    BubbleDrawable _seedBubble;
    unique_ptr<RecurrenceRelationSeedComponent> _seedSliderComponent;
    BubbleDrawable _indexBubble;
    unique_ptr<DeltaComboBox> _indexComboBox;
    BubbleDrawable _offsetBubble;
    unique_ptr<SeedSlider> _offsetSlider;
    BubbleDrawable _numTermsBubble;
    unique_ptr<SeedSlider> _numTermsSlider;
    BubbleDrawable _sumTypeBubble;
    unique_ptr<DeltaComboBox> _sumTypeComboBox;
    BubbleDrawable _seedSpaceBubble;
    unique_ptr<DeltaComboBox> _seedSpaceComboBox;
    unique_ptr<WilsonicPitchWheelComponent> _pitchWheelComponent;
    unique_ptr<TextEditor> _textEditor;

    // private methods
    void _tuningChangedUpdateUI();
};
