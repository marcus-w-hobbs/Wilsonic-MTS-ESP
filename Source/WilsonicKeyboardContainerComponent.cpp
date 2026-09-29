/*
 ==============================================================================

 WilsonicKeyboardContainerComponent.cpp
 Created: 7 Mar 2021 4:46:37pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include <JuceHeader.h>
#include "Brun.h"
#include "FavoritesIconRenderer.h"
#include "WilsonicEditor.h"
#include "WilsonicKeyboardContainerComponent.h"

#pragma mark - lifecycle

WilsonicKeyboardContainerComponent::WilsonicKeyboardContainerComponent
(
  WilsonicProcessor& processor,
  DeltaListener& deltaListener
)
: WilsonicComponentBase(processor)
, _keyboardComponent(_processor, WilsonicMidiKeyboardComponent::horizontalKeyboard) {
    //
    auto const labelFontSize = WilsonicAppSkin::comboBoxFontSize;
    auto const font = Font::plain;

    // Initialize the MIDI Panic Button
    {
        auto small = _getMidiPanicHelper(false);
        auto big = _getMidiPanicHelper(true);
        _midiPanicButton = make_unique<DrawableButton> ("MIDI Panic", DrawableButton::ImageFitted);
        _midiPanicButton->setImages (&small, &big, &big, &small, &small, &big, &big, &small);
        _midiPanicButton->setClickingTogglesState(true);
        _midiPanicButton->setTooltip("MIDI Panic: turns off all playing notes");
        _midiPanicButton->addListener(this);
        addAndMakeVisible (*_midiPanicButton);
    }

    // Initialize the Keyboard Button
    {
        auto on_small = _getKeyboardHelper(false, false);
        auto on_big = _getKeyboardHelper(false, true);
        auto off_small = _getKeyboardHelper(true, false);
        auto off_big = _getKeyboardHelper(true, true);
        _keyboardButton = make_unique<DrawableButton>("Keyboard", DrawableButton::ImageFitted);
        _keyboardButton->setImages (&off_small, &off_big, &on_big,  &off_small,
                                    &on_small,  &on_big,  &off_big, &off_small);
        _keyboardButton->setClickingTogglesState(true);
        _keyboardButton->setTooltip("Toggle Keyboard");
        _keyboardButton->setToggleState(_processor.restoreKeyboardVisible(), dontSendNotification);
        _showKeyboard = _processor.restoreKeyboardVisible();
        _keyboardButton->addListener(this);
        addAndMakeVisible(*_keyboardButton);
    }

    // Initialize the Pitch Wheel Button
    {
        auto on_small = _getPitchWheelHelper(false, false);
        auto on_big = _getPitchWheelHelper(false, true);
        auto off_small = _getPitchWheelHelper(true, false);
        auto off_big = _getPitchWheelHelper(true, true);
        _pitchWheelButton = make_unique<DrawableButton> ("Keyboard Pitch Wheel", DrawableButton::ImageFitted);
        _pitchWheelButton->setImages (&off_small, &off_big, &on_big,  &off_small,
                                      &on_small,  &on_big,  &off_big, &off_small);
        _pitchWheelButton->setClickingTogglesState(true);
        _pitchWheelButton->setTooltip ("Toggle Keyboard Pitch Wheel");
        _pitchWheelButton->setToggleState(_processor.restorePitchWheelInKeyboard(), dontSendNotification);
        _pitchWheelButton->addListener(this);
        addAndMakeVisible (*_pitchWheelButton);
    }

    // Initialize the show triads button
    {
        auto on_small = _getTriadsHelper(1.f, false);
        auto on_big = _getTriadsHelper(1.f, true);
        auto off_small = _getTriadsHelper(0.1f, false);
        auto off_big = _getTriadsHelper(0.1f, true);
        _triadsButton = make_unique<DrawableButton> ("Triads", DrawableButton::ImageFitted);
        _triadsButton->setImages (&off_small, &off_big, &on_big,  &off_small,
                                  &on_small,  &on_big,  &off_big, &off_small);
        _triadsButton->setClickingTogglesState(true);
        _triadsButton->setTooltip ("Toggle the display of triads on the keyboard.\nThis can improve performance.");
        _triadsButton->setToggleState(_processor.restoreShowProportionalTriads(), dontSendNotification);
        _triadsButton->addListener(this);
        addAndMakeVisible (*_triadsButton);
    }

    // NPO override toggle
    _npoOverrideToggle = make_unique<ToggleButton>("NPO Override");
    _npoOverrideToggle->setToggleState(_processor.getAppTuningModel()->uiGetNPOOverrideEnable(), dontSendNotification);
    _npoOverrideToggle->setHelpText("Toggle Note-Per-Octave Override");
    _npoOverrideToggle->addListener(this);
    addAndMakeVisible(*_npoOverrideToggle);

    // NPO override slider
    addAndMakeVisible(_npoOverrideSlider);
    _npoOverrideSlider.setSliderStyle(Slider::IncDecButtons);
    _npoOverrideSlider.setRange(Tuning::npoOverrideMin, Tuning::npoOverrideMax, 1.f);
    _npoOverrideSlider.setDoubleClickReturnValue(true, Tuning::npoOverrideDefault);
    _npoOverrideSlider.setValue(_processor.getAppTuningModel()->uiGetNPOOverride());
    _npoOverrideSlider.setIncDecButtonsMode(Slider::incDecButtonsDraggable_Vertical);
    _npoOverrideSlider.setTooltip ("When Notes-Per-Octave Override is toggled on:\nFor scales that support NPO override:\nNotes are duplicated or removed to create a final scale with this many notes per octave");
    _npoOverrideSlider.onValueChange = [this] {
        auto const npo = static_cast<float>(_npoOverrideSlider.getValue());
        _processor.getAppTuningModel()->uiSetNPOOverride(npo);
    };

    // Initialize the Label: Octave at Middle C
    addAndMakeVisible(_octaveMiddleCSliderLabel);
    _octaveMiddleCSliderLabel.setFont(Font(FontOptions(labelFontSize, font)));

    // Initialize the Slider: Octave at Middle C
    addAndMakeVisible(_octaveMiddleCSlider);
    _octaveMiddleCSlider.setSliderStyle(Slider::IncDecButtons);
    _octaveMiddleCSlider.setRange(Tuning::octaveMiddleCMin, Tuning::octaveMiddleCMax, 1.f);
    _octaveMiddleCSlider.setDoubleClickReturnValue(true, Tuning::octaveMiddleCDefault);
    _octaveMiddleCSlider.setValue(_processor.getAppTuningModel()->uiGetOctaveMiddleC());
    _octaveMiddleCSlider.setIncDecButtonsMode(Slider::incDecButtonsDraggable_Vertical);
    _octaveMiddleCSlider.setTooltip ("The Octave at Middle C (note number 60)\n2^octave:\n2^-2 = 1/4\n2^-1 = 1/2\n2^0 = 1\n2^1 = 2\n2^2 = 4");
    _octaveMiddleCSlider.onValueChange = [this] {
        auto const octave = _octaveMiddleCSlider.getValue();
        _processor.getAppTuningModel()->uiSetOctaveMiddleC(static_cast<int>(octave));
    };

    // Initialize the Label: MIDI Note Number at Middle C
    addAndMakeVisible(_noteNumberMiddleCSliderLabel);
    _noteNumberMiddleCSliderLabel.setFont(Font(FontOptions(labelFontSize, font)));

    // Initialize the Slider: MIDI Note Number at Middle C
    addAndMakeVisible(_noteNumberMiddleCSlider);
    _noteNumberMiddleCSlider.setSliderStyle(Slider::IncDecButtons);
    _noteNumberMiddleCSlider.setRange(Tuning::noteNumberMiddleCMin, Tuning::noteNumberMiddleCMax, 1.f);
    _noteNumberMiddleCSlider.setValue(_processor.getAppTuningModel()->uiGetNoteNumberMiddleC());
    _noteNumberMiddleCSlider.setDoubleClickReturnValue(true, Tuning::noteNumberMiddleCDefault);
    _noteNumberMiddleCSlider.setTooltip ("MIDI Note Number at Middle C\n\nDefaults to 60");
    _noteNumberMiddleCSlider.setIncDecButtonsMode(Slider::incDecButtonsDraggable_Vertical);
    _noteNumberMiddleCSlider.onValueChange = [this] {
        auto const noteNumberMiddleC = static_cast<float>(_noteNumberMiddleCSlider.getValue());
        _processor.getAppTuningModel()->uiSetNoteNumberMiddleC(noteNumberMiddleC);
    };

    // Initialize the Label: Frequency at Middle C
    addAndMakeVisible(_frequencyMiddleCSliderLabel);
    _frequencyMiddleCSliderLabel.setFont(Font(FontOptions(labelFontSize, font)));

    // Initialize the Slider: Frequency at Middle C(centered an octave about 12et def)
    addAndMakeVisible(_frequencyMiddleCSlider);
    _frequencyMiddleCSlider.setSliderStyle(Slider::LinearHorizontal);
    _frequencyMiddleCSlider.setRange(Tuning::frequencyMiddleCMin, Tuning::frequencyMiddleCMax, 0);
    _frequencyMiddleCSlider.setValue(_processor.getAppTuningModel()->uiGetFrequencyMiddleC());
    _frequencyMiddleCSlider.setDoubleClickReturnValue(true, Tuning::frequencyMiddleCDefault);
    _frequencyMiddleCSlider.setNumDecimalPlacesToDisplay(WilsonicProcessorConstants::defaultNumPrecisionDigits);
    _frequencyMiddleCSlider.setTooltip("Frequency at Middle C, relative to equal tempered A");
    _frequencyMiddleCSlider.onValueChange = [this] {
        auto const frequencyMiddleC = _frequencyMiddleCSlider.getValue();
        _processor.getAppTuningModel()->uiSetFrequencyMiddleC(static_cast<float>(frequencyMiddleC));
    };

    // Add this as listener of the global app tuning
    _processor.getAppTuningModel()->addActionListener(this);

    // Initialize the pitch wheel
    _pitchWheel = make_unique<WilsonicPitchWheelComponent>(_processor, AppExperiments::tuningRendererPlayingNotes);
    _pitchWheel->setCustomFontScale(WilsonicAppSkin::defaultPitchWheelFontScale);
    _pitchWheel->setTuning(_processor.getAppTuningModel()->getTuning());
    _pitchWheel->setDrawText(false);
    addAndMakeVisible(*_pitchWheel);
    _showPitchWheel = _processor.restorePitchWheelInKeyboard();
    _pitchWheel->setVisible(_showPitchWheel);

    // Initialize the pitch color offset
    _pitchColorOffset01Slider.setSliderStyle(Slider::RotaryHorizontalVerticalDrag);
    _pitchColorOffset01Slider.setTextBoxStyle(Slider::NoTextBox, false, 0, 0);
    _pitchColorOffset01Slider.setRange(0.0, 1.0);
    float offset = _processor.restorePitchColorOffset();
    _pitchColorOffset01Slider.setValue(offset);
    _pitchColorOffset01Slider.setDoubleClickReturnValue(true, 0.f);
    _pitchColorOffset01Slider.setTooltip ("Set the color of Middle C");
    _pitchColorOffset01Slider.setRotaryParameters(0.f, MathConstants<float>::twoPi, false);
    _pitchColorOffset01Slider.onValueChange = [this] {
        auto v = _pitchColorOffset01Slider.getValue();
        _processor.getAppTuningModel()->setPitchColorOffset ((float)v);
    };
    addAndMakeVisible(_pitchColorOffset01Slider);

    // Initialize the keyboard
    addAndMakeVisible(_keyboardComponent);

    // Initialize the delta broadcaster
    _deltaBroadcaster.addChangeListener (&deltaListener);

    // This is just to grab focus one time after being displayed,
    // then it is disabled
    startTimer(400);
}

WilsonicKeyboardContainerComponent::~WilsonicKeyboardContainerComponent() {
    _processor.getAppTuningModel()->removeActionListener(this);
    _npoOverrideToggle->removeListener(this);
    _deltaBroadcaster.removeAllChangeListeners();
}

#pragma mark - drawing

void WilsonicKeyboardContainerComponent::paint(Graphics& g) {
    g.fillAll(Colours::darkgrey.darker().darker());
    if (AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::lightgreen);
        g.drawRect(getLocalBounds(), 1);
        g.drawRect(_midiPanicButton->getBounds());
        g.drawRect(_keyboardButton->getBounds());
        g.drawRect(_pitchWheelButton->getBounds());
        g.drawRect(_triadsButton->getBounds());
        g.drawRect(_pitchColorOffset01Slider.getBounds());
        g.drawRect(_octaveMiddleCSlider.getBounds());
        g.drawRect(_noteNumberMiddleCSlider.getBounds());
        g.drawRect(_frequencyMiddleCSlider.getBounds());
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
    
    if(_processor.getAppTuningModel()->getTuning()->getCanNPOOverride()) {
        _npoOverrideSlider.setEnabled(true);
        _npoOverrideToggle->setEnabled(true);
    } else {
        _npoOverrideSlider.setEnabled(false);
        _npoOverrideToggle->setEnabled(false);
    }
}

void WilsonicKeyboardContainerComponent::resized() {
    // layout constants
    auto const yMargin = static_cast<int>(15.f);
    auto const componentHeight = static_cast<int>(WilsonicAppSkin::sliderHeight);
    auto const labelHeight = static_cast<int>(WilsonicAppSkin::labelHeight);
    auto area = getLocalBounds();
    area.removeFromTop(static_cast<int>(0.5f * yMargin)); // same as bottom

    // row for controls

    // TODO: Mode experiment is not layed out correctly VV
    // | pitchWheelButton | triadsButton | pitchColorOffset01] | NPO override | middleC label | middleCNN label | middleCFreq label |
    auto topArea = area.removeFromTop(labelHeight + componentHeight);
    auto const nw = topArea.getWidth() / 5.f; // 5 elements
    auto const nws = static_cast<int>(jmax(nw - 50.f, 0.25f*130.f)); // per element width inset
    auto const h = topArea.getHeight();
    auto const x = topArea.getX();
    auto const y = topArea.getY();
    auto topArea0 = Rectangle<int>(static_cast<int>(x + 0 * nw), y, static_cast<int>(nw), h).withSizeKeepingCentre(nws, h); // pitch wheel, triads, and pitch offset
    auto topArea1 = Rectangle<int>(static_cast<int>(x + 1 * nw), y, static_cast<int>(nw), h).withSizeKeepingCentre(nws, h); // +/- slider
    auto topArea2 = Rectangle<int>(static_cast<int>(x + 2 * nw), y, static_cast<int>(nw), h).withSizeKeepingCentre(nws, h); // +/- slider
    auto topArea3 = Rectangle<int>(static_cast<int>(x + 3 * nw), y, static_cast<int>(nw), h).withSizeKeepingCentre(nws, h); // +/- slider
    auto topArea4 = Rectangle<int>(static_cast<int>(x + 4 * nw), y, static_cast<int>(nw), h).withSizeKeepingCentre(nws, h); // +/- slider

    // pitch wheel button and triads button
    auto const ta0w = static_cast<int>(topArea0.getWidth() / 5.f); // five elements
    auto topArea0_l = topArea0.removeFromRight(ta0w);
    auto tba = topArea0.removeFromRight(ta0w);
    auto pwba = topArea0.removeFromRight(ta0w);
    auto ska = topArea0.removeFromRight(ta0w);
    auto mpba = topArea0.removeFromRight(ta0w);
    _midiPanicButton->setBounds(mpba);
    _keyboardButton->setBounds(ska);
    _pitchWheelButton->setBounds(pwba);
    _triadsButton->setBounds(tba);
    _pitchColorOffset01Slider.setBounds(topArea0_l); // pitch color offset rotary slider

    // npo override
    _npoOverrideToggle->setBounds(topArea1.removeFromTop(labelHeight));
    _npoOverrideSlider.setBounds(topArea1);
    
    // Octave
    _octaveMiddleCSliderLabel.setBounds(topArea2.removeFromTop(labelHeight));
    _octaveMiddleCSlider.setBounds(topArea2);

    // MIDI nn for Middle C
    _noteNumberMiddleCSliderLabel.setBounds(topArea3.removeFromTop(labelHeight));
    _noteNumberMiddleCSlider.setBounds(topArea3);

    // Frequency at Middle C
    _frequencyMiddleCSliderLabel.setBounds(topArea4.removeFromTop(labelHeight));
    _frequencyMiddleCSlider.setBounds(topArea4);

    // spacer
    area.removeFromTop(static_cast<int>(0.5f * yMargin)); // same as top

    if (_processor.restoreKeyboardVisible()) {
        // the remainder is Pitch Wheel + Keyboard
        if (_showPitchWheel) {
            auto pitchWheelArea = area.removeFromLeft(_keyboardComponent.getHeight()); // square
            _pitchWheel->setBounds(pitchWheelArea);
        }
        _pitchWheel->setVisible(_showPitchWheel);
        _keyboardComponent.setBounds(area);
    } else {
        // push pitch wheel and keyboard offscreen
        auto offscreen_area = Rectangle<int>(area.getX() + area.getWidth(), area.getY() + area.getHeight(), area.getWidth(), area.getHeight());

        // the remainder is Pitch Wheel + Keyboard
        if (_showPitchWheel) {
            auto pitchWheelArea = offscreen_area.removeFromLeft(_keyboardComponent.getHeight()); // square
            _pitchWheel->setBounds(pitchWheelArea);
        }
        _pitchWheel->setVisible(_showPitchWheel);
        _keyboardComponent.setBounds(offscreen_area);
    }
}

#pragma mark - timer

void WilsonicKeyboardContainerComponent::timerCallback() {
    stopTimer();
#if JUCE_IOS || JUCE_ANDROID
    // NOP
#else
    _keyboardComponent.grabKeyboardFocus();
#endif
    resized();
}

#pragma mark - ActionListener

// this component is unique from others because it is expected
// to present the state of the global app tuning table
void WilsonicKeyboardContainerComponent::actionListenerCallback(const String& message) {
    if (message == AppTuningModel::getAppTuningModelChangedMessage()) {
        // update sliders/toggles
        auto const atm = _processor.getAppTuningModel();
        _npoOverrideToggle->setToggleState(atm->uiGetNPOOverrideEnable(), dontSendNotification);
        _npoOverrideSlider.setValue(atm->uiGetNPOOverride(), dontSendNotification);
        _octaveMiddleCSlider.setValue(atm->uiGetOctaveMiddleC(), dontSendNotification);
        _noteNumberMiddleCSlider.setValue(atm->uiGetNoteNumberMiddleC(), dontSendNotification);
        _frequencyMiddleCSlider.setValue(atm->uiGetFrequencyMiddleC(), dontSendNotification);

        // pitch wheel: update tuning
        _pitchWheel->setTuning(_processor.getAppTuningModel()->getTuning());
        
        // ui
        repaint();
        _keyboardComponent.repaint();
    }
}

#pragma mark - Button handler

void WilsonicKeyboardContainerComponent::buttonClicked(Button* button) {
    // "!" Midi panic
    auto mpb = dynamic_cast<Button*>(_midiPanicButton.get());
    if (mpb == button) {
        _processor.allNotesOff();
        mpb->setToggleState(false, dontSendNotification);
        resized();

        return;
    }

    // "S" Show/Hide Keyboard
    auto kb = dynamic_cast<Button*>(_keyboardButton.get());
    if (kb == button) {
        _showKeyboard = !_showKeyboard;
        _processor.saveKeyboardVisible(_showKeyboard);
        sendActionMessage(getToggleShowKeyBoardChangedMessage());
        resized();
        
        return;
    }
    
    // "P" Pitch Wheel
    auto pfb = dynamic_cast<Button*>(_pitchWheelButton.get());
    if (pfb == button) {
        _showPitchWheel = !_showPitchWheel;
        _processor.savePitchWheelInKeyboard(_showPitchWheel);
        resized();

        return;
    }

    // Triads
    auto tb = dynamic_cast<Button*>(_triadsButton.get());
    if (tb == button) {
        auto const show = _processor.restoreShowProportionalTriads();
        _processor.saveShowProportionalTriads(!show);
        _keyboardComponent.repaint();

        return;
    }
    
    // npo override enable toggle
    auto noet = dynamic_cast<ToggleButton*>(_npoOverrideToggle.get());
    if(noet == button) {
        auto const atm = _processor.getAppTuningModel();
        atm->uiSetNPOOverrideEnable(_npoOverrideToggle->getToggleState());

        return;
    }
    
    jassertfalse;
}

#pragma mark - Mouse Handler

void WilsonicKeyboardContainerComponent::mouseDown(const MouseEvent& event) {
    _lastMousePosition = event.getMouseDownPosition();
}

void WilsonicKeyboardContainerComponent::mouseDrag(const MouseEvent& event) {
    auto const delta = event.getPosition() - _lastMousePosition;
    _deltaBroadcaster.setDelta(delta);
    _deltaBroadcaster.sendChangeMessage();
}

void WilsonicKeyboardContainerComponent::adjustKeySizeFactorByDelta(int delta) {
    _keyboardComponent.adjustKeySizeFactorByDelta(delta);
}

#pragma mark - drawing helpers

DrawableImage WilsonicKeyboardContainerComponent::_getMidiPanicHelper(bool big) {
    auto const w_big = 100;
    auto const w_small = 80;
    auto const h_big = 100;
    auto const h_small = 80;
    auto const x_big = 0;
    auto const x_small = 10;
    auto const y_big = 0;
    auto const y_small = 10;
    Rectangle<int> bounds(big ? x_big : x_small, big ? y_big : y_small, big ? w_big : w_small, big ? h_big : h_small);
    Image image(Image::ARGB, w_big, h_big, true);
    Graphics g(image);
    g.setColour(Colours::red);
    g.setFont(60);
    auto f = g.getCurrentFont();
    if (big) {
        f = f.boldened();
    }
    g.setFont(f);
    g.drawText("!!", bounds, Justification::centred);
    auto normal = DrawableImage(image);

    return normal;
}


DrawableImage WilsonicKeyboardContainerComponent::_getPitchWheelHelper(bool desaturate, bool big) {
    auto const w_big = 100;
    auto const w_small = 80;
    auto const h_big = 100;
    auto const h_small = 80;
    auto const x_big = 0;
    auto const x_small = 10;
    auto const y_big = 0;
    auto const y_small = 10;
    Rectangle<int> bounds(big ? x_big : x_small, big ? y_big : y_small, big ? w_big : w_small, big ? h_big : h_small);
    Image image(Image::ARGB, w_big, h_big, true);
    Graphics g(image);
    auto tuning = make_shared<Brun>(); // 7 of 12et
    FavoritesIconRenderer::paintFavoritesPitchWheel(_processor, g, tuning, bounds);
    if (desaturate) {
        image.desaturate();
    }
    auto normal = DrawableImage(image);

    return normal;
}

// 1.f, 0.5f
DrawableImage WilsonicKeyboardContainerComponent::_getTriadsHelper(float saturationMultiplier01, bool big) {
    auto const lineThickness = 4;
    auto const outlineThickness = 2;
    auto const w = big ? 80 : 100;
    auto const h = big ? 80 : 100;
    auto const dotR = 12;
    auto const inset = 14;
    auto const root = inset;
    auto const fifth = w - inset;
    auto const minorx = 0.4f * w;
    auto const minory = (big ? 0.2f : 0.25f) * h;
    auto const majorx = 0.6f * w;
    auto const majory = (big ? 0.8f : 0.75f) * h;
    auto const minorColour = _processor.getAppSkin().getSubcontraryTriadDotColour().withMultipliedSaturation(saturationMultiplier01);
    auto const majorColour = _processor.getAppSkin().getProportionalTriadDotColour().withMultipliedSaturation(saturationMultiplier01);
    auto const whiteColour = Colours::white.withBrightness(saturationMultiplier01);
    Image image(Image::ARGB, w, h, true);
    Graphics g(image);
    // subcontrary
    g.setColour(minorColour);
    // subcontrary: draw line, cheat y offset so ellipses are centered
    g.drawLine(root, minory + 0.5f*dotR, fifth, minory + 0.5f*dotR, lineThickness);
    g.fillEllipse(root, minory, dotR, dotR);
    g.fillEllipse(minorx, minory, dotR, dotR);
    g.fillEllipse(fifth, minory, dotR, dotR);
    // subcontrary: white outline
    g.setColour(whiteColour);
    g.drawEllipse(root, minory, dotR, dotR, outlineThickness);
    g.drawEllipse(minorx, minory, dotR, dotR, outlineThickness);
    g.drawEllipse(fifth, minory, dotR, dotR, outlineThickness);
    // proportional
    g.setColour(majorColour);
    // proportional: draw line, cheat y so ellipses are centered
    g.drawLine(root, majory + 0.5f*dotR, fifth, majory + 0.5f*dotR, lineThickness);
    g.fillEllipse(root, majory, dotR, dotR);
    g.fillEllipse(majorx, majory, dotR, dotR);
    g.fillEllipse(fifth, majory, dotR, dotR);
    // proportional: white outline
    g.setColour(whiteColour);
    g.drawEllipse(root, majory, dotR, dotR, outlineThickness);
    g.drawEllipse(majorx, majory, dotR, dotR, outlineThickness);
    g.drawEllipse(fifth, majory, dotR, dotR, outlineThickness);
    auto normal = DrawableImage(image);

    return normal;
}

DrawableImage WilsonicKeyboardContainerComponent::_getKeyboardHelper(bool desaturate, bool big) {
    auto const w_big = 100;
    auto const w_small = 80;
    auto const h_big = 100;
    auto const h_small = 80;
    auto const x_big = 0;
    auto const x_small = 10;
    auto const y_big = 0;
    auto const y_small = 10;
    Rectangle<int> bounds(big ? x_big : x_small, big ? y_big : y_small, big ? w_big : w_small, big ? h_big : h_small);
    Image image(Image::ARGB, w_big, h_big, true);
    Graphics g(image);
    auto tuning = make_shared<Brun>(); // 7 of 12et
    auto const num_keys = 5;
    auto const key_width = (big ? w_big : w_small) / num_keys;
    for(auto key = 0; key < num_keys; key++) {
        float const x = static_cast<float>(key) / static_cast<float>(num_keys);
        auto const key_colour = _processor.getAppTuningModel()->colorForPitch01(x);
        g.setColour(key_colour);
        auto k = bounds.removeFromLeft(key_width);
        g.fillRect(k);
    }
    if (desaturate) {
        image.desaturate();
    }
    auto normal = DrawableImage(image);

    return normal;
}
