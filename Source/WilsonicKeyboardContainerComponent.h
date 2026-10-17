/**
 * @file RootKeyboardContainerComponent.h
 * @brief Contains the declaration of the WilsonicKeyboardContainerComponent class.
 * @author Marcus W. Hobbs
 * @date Created: 7 Mar 2021 4:46:37pm
 */

#pragma once

#include <JuceHeader.h>
#include "AppExperiments.h"
#include "AppTuningModel.h"
#include "DeltaBroadcaster.h"
#include "DeltaListener.h"
#include "WilsonicComponentBase.h"
#include "WilsonicAppSkin.h"
#include "WilsonicMidiKeyboardComponent.h"
#include "WilsonicPitchWheelComponent.h"
#include "WilsonicProcessor.h"

/**
 * @class WilsonicKeyboardContainerComponent
 * @brief This class represents the keyboard container component of the Wilsonic application.
 * 
 * It inherits from WilsonicComponentBase, ActionListener, ActionBroadcaster, Timer, and Button::Listener.
 * It contains methods for painting, resizing, handling mouse events, and adjusting key size.
 * It also contains private members for various UI elements and state variables.
 */
class WilsonicKeyboardContainerComponent
: public WilsonicComponentBase
, public ActionListener
, public ActionBroadcaster
, private Timer
, private Button::Listener
{
public:
    /**
     * @brief Constructor for the WilsonicKeyboardContainerComponent class.
     * @param WilsonicProcessor& Reference to the WilsonicProcessor object.
     * @param DeltaListener& Reference to the DeltaListener object.
     */
    WilsonicKeyboardContainerComponent(WilsonicProcessor&, DeltaListener&);
    
    /**
     * @brief Destructor for the WilsonicKeyboardContainerComponent class.
     */
    ~WilsonicKeyboardContainerComponent() override;
    
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(WilsonicKeyboardContainerComponent)

public:
    // public methods
    void paint(Graphics&) override;
    void resized() override;
    void actionListenerCallback(const String& message) override;
    void mouseDown(const MouseEvent& event) override;
    void mouseDrag(const MouseEvent& event) override;
    void adjustKeySizeFactorByDelta(int delta); // can be negative
    static String const getToggleShowKeyBoardChangedMessage() {return "toggleShowKeyboardChangedMessage";}

private:
    // private members
    bool _showPitchWheel = false;
    bool _showKeyboard = true;
    unique_ptr<DrawableButton> _midiPanicButton = nullptr;
    unique_ptr<DrawableButton> _keyboardButton = nullptr;
    unique_ptr<DrawableButton> _pitchWheelButton = nullptr;
    unique_ptr<DrawableButton> _triadsButton = nullptr;
    unique_ptr<DrawableButton> _geometricTriadsButton = nullptr;
    unique_ptr<ToggleButton> _npoOverrideToggle = nullptr;
    Slider _npoOverrideSlider;
    Label _octaveMiddleCSliderLabel { "octavemiddlecsliderlabel", "Period Middle C" };
    Slider _octaveMiddleCSlider;
    Label _noteNumberMiddleCSliderLabel { "notenumbermiddlecsliderlabel", "Note Number Middle C" };
    Slider _noteNumberMiddleCSlider;
    Label _frequencyMiddleCSliderLabel { "frequencymiddlecsliderlabel", "Frequency Middle C" };
    Slider _frequencyMiddleCSlider;
    Slider _pitchColorOffset01Slider;
    unique_ptr<WilsonicPitchWheelComponent> _pitchWheel;
    WilsonicMidiKeyboardComponent _keyboardComponent; // OWNER
    DeltaBroadcaster _deltaBroadcaster;
    Point<int> _lastMousePosition {0,0};

    // private methods
    void timerCallback() override;
    void buttonClicked(Button*) override;
    DrawableImage _getMidiPanicHelper(bool big);
    DrawableImage _getPitchWheelHelper(bool desaturate, bool big);
    DrawableImage _getTriadsHelper(float saturationMultiplier01, bool big);
    DrawableImage _getGeometricTriadsHelper(float saturationMultiplier01, bool big);
    DrawableImage _getKeyboardHelper(bool desaturate, bool big);
};
