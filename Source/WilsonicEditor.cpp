// This file contains the basic framework code for a JUCE plugin editor.

#include "WilsonicEditor.h"
#include "SnapshotMode.h"
#include "WilsonicMidiKeyboardComponent.h"
#include "WilsonicProcessor.h"
#include <juce_audio_plugin_client/Standalone/juce_StandaloneFilterWindow.h>

#pragma mark - lifecycle

unique_ptr<BubbleMessageComponent> WilsonicEditor::__bubbleMessageComponent = nullptr;

/**
 * @brief Constructor for the WilsonicEditor class.
 * @param in_processor Reference to the WilsonicProcessor object.
 */
WilsonicEditor::WilsonicEditor(WilsonicProcessor& in_processor)
: AudioProcessorEditor(&in_processor)
, _processor(in_processor)
, _appRootComponent(_processor) {
    // Configure the editor
    setResizable(true, true);
    addAndMakeVisible(_appRootComponent);

    // Set the look and feel of the editor
    auto lf = _processor.getAppSkin().getLookAndFeel();
    setLookAndFeel(lf.get());
    
    // Create a global bubble message component
    // There should only be one bubble message component, hence the assertion
    jassert(__bubbleMessageComponent == nullptr);
    __bubbleMessageComponent = make_unique<BubbleMessageComponent>();
    __bubbleMessageComponent->setLookAndFeel(lf.get());
    addChildComponent(*__bubbleMessageComponent);

    // Get the dimensions of the window from the properties file
    // If no dimensions are found, fall back on the default size
    auto bounds = _processor.restoreWindowBounds();
    if (!bounds.isEmpty()) {
        // Set the bounds of the window
        // This may not work because the StandaloneFilterApp manages the window size
        setBounds(bounds);
    } else {
        // Set the default size of the window
        setSize(_processor.getAppSkin().getWindowWidth(), _processor.getAppSkin().getWindowHeight());
    }

    // Standalone only: when launched as `Wilsonic --snapshot <manifest.json>
    // <output-dir>`, render one PNG per manifest entry and exit. A NOP for
    // normal launches and plugin builds.
    SnapshotMode::startIfRequested(_processor, *this);
}

WilsonicEditor::~WilsonicEditor() {
    __bubbleMessageComponent = nullptr;
    // Snapshot mode forces its own window size; don't persist it as the
    // user's preferred bounds.
    if (!SnapshotMode::isActive()) {
        _processor.saveWindowBounds(getTopLevelComponent()->getBounds());
    }
}

#pragma mark - drawing

void WilsonicEditor::paint(Graphics& g) {
    g.fillAll(_processor.getAppSkin().getBgColor());
    if (AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::green);
        g.drawRect(getLocalBounds(), 2);
    }
}

void WilsonicEditor::resized() {
    auto area = getLocalBounds();
    _appRootComponent.setBounds(area);
}

// ADD NEW SCALE DESIGN HERE

#pragma mark - DesignsProtocol

void WilsonicEditor::showBrunTuning() {
    _appRootComponent.showBrunTuning();
}

void WilsonicEditor::showCoPrimeTuning() {
    _appRootComponent.showCoPrimeTuning();
}

void WilsonicEditor::showCPSTuning() {
    _appRootComponent.showCPSTuning();
}

void WilsonicEditor::showDiamondsTuning() {
    _appRootComponent.showDiamondsTuning();
}

void WilsonicEditor::showEqualTemperamentTuning() {
    _appRootComponent.showEqualTemperamentTuning();
}

void WilsonicEditor::showEulerGenusV2Tuning() {
    _appRootComponent.showEulerGenusV2Tuning();
}

void WilsonicEditor::showMorphTuning() {
    _appRootComponent.showMorphTuning();
}

void WilsonicEditor::showPartchTuning() {
    _appRootComponent.showPartchTuning();
    showAudioDeviceSettings();
}

void WilsonicEditor::showPersian17NorthIndianTuning() {
    _appRootComponent.showPersian17NorthIndianTuning();
}

void WilsonicEditor::showPresetsTuning() {
    _appRootComponent.showPresetsTuning();
}

void WilsonicEditor::showRecurrenceRelationTuning() {
    _appRootComponent.showRecurrenceRelationTuning();
}

void WilsonicEditor::showScalaTuning() {
    _appRootComponent.showScalaTuning();
}

void WilsonicEditor::showTritriadicTuning() {
    _appRootComponent.showTritriadicTuning();
}

#pragma mark - Pages

void WilsonicEditor::showSynth() {
    _appRootComponent.showSynth();
}

#pragma mark - BubbleMessageComponent

void WilsonicEditor::showBubbleMessage(BubbleDrawable& targetComponent) {
    auto textToShow = targetComponent.getBubbleMessage();

    // empty string is a NOP
    if (textToShow.length() == 0) {
        return;
    }

    AttributedString text(textToShow);
    text.setJustification(Justification::centred);
    text.setColour(targetComponent.findColour(TextButton::textColourOffId));
    __bubbleMessageComponent->setAllowedPlacement(targetComponent.getBubblePlacement());
    __bubbleMessageComponent->showAt(&targetComponent, text, 0, true, false);
}

#pragma mark - Audio/MIDI Settings for iOS Standalone

// TODO: This leaks
void WilsonicEditor::showAudioDeviceSettings() {
    // This is specific to iOS WilsonicController standalone builds.
#if JucePlugin_Build_Standalone && JUCE_IOS
    auto& deviceManager = juce::StandalonePluginHolder::getInstance()->deviceManager;
    
    auto audioDeviceSelector = std::make_unique<juce::AudioDeviceSelectorComponent>(deviceManager,
                                                                                    0, 2,  // minimumInputChannels, maximumInputChannels
                                                                                    0, 2,  // minimumOutputChannels, maximumOutputChannels
                                                                                    true,  // showMidiInputOptions
                                                                                    true,  // showMidiOutputSelector
                                                                                    true,  // showChannelsAsStereoPairs
                                                                                    false  // hideAdvancedOptions
                                                                                    );
    audioDeviceSelector->setBounds(0, 0, 400, 600);
    auto* dialogWindow = new juce::DialogWindow("Audio/MIDI Settings", juce::Colours::lightgrey, true);
    dialogWindow->centreWithSize(400, 600);
    dialogWindow->setResizable(true, true);
    dialogWindow->setVisible(true);
    dialogWindow->setContentOwned(audioDeviceSelector.release(), true);
#endif
}
