/*
  ==============================================================================

    EulerGenusComponentV2.h
    Created: 27 Nov 2021 6:37:37pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "AppTuningModel.h"
#include "CPSElementComponentV2.h"
#include "CPSTuningBase.h"
#include "DeltaComboBox.h"
#include "EulerGenusModel.h"
#include "EulerGenusViewModel.h"
#include "SeedSliderComponent.h"
#include "Tuning_Include.h"
#include "WilsonicAppSkin.h"
#include "WilsonicAppTuningComponent.h"
#include "WilsonicProcessor.h"

class EulerGenusComponentV2 
: public WilsonicAppTuningComponent
, private ActionListener
{
public:
    // Lifecycle
    EulerGenusComponentV2(WilsonicProcessor&);
    ~EulerGenusComponentV2() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(EulerGenusComponentV2)

public:
    void paint(Graphics&) override;
    void resized() override;

    // app tuning title
    const string getAppTuningTitle() override;

    // click...elements call this method passing in their component ID
    void singleClickDAWKey(DAWKey dawKey); // "select"
    void controlClickDAWKey(DAWKey dawKey); // "drill"
    void commandClickDAWKey(DAWKey dawKey); // "back button"

    
private:
    CriticalSection _lock;
    unique_ptr<SeedSliderComponent> _seedSliderComponent;
    ToggleButton _genusSpaceToggle; // keep drill-path root as global tuning/MIDI mapping
    unique_ptr<AudioProcessorValueTreeState::ButtonAttachment> _genusSpaceAttachment;
    BubbleDrawable _mainElementBubble;
    shared_ptr<CPSElementComponentV2> _mainElement {nullptr};
    static String const __mainElementBubbleText;
    static String const __eg6BubbleText;
    BubbleDrawable _subsetsBubble;
    static String const __subsetsBubbleText;
    vector<shared_ptr<CPSElementComponentV2>> _subsets0 {};
    vector<shared_ptr<CPSElementComponentV2>> _subsets1 {};

    // private member functions
    void _resizedEulerGenus(Rectangle<int>);
    void _resizedCPS(Rectangle<int>);
    void _tuningChangedUpdateUI();
    void actionListenerCallback(const String&) override;
    bool keyPressed(const KeyPress& key) override;
};
