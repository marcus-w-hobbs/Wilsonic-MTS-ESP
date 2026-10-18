/*
  ==============================================================================

    This file contains the basic framework code for a JUCE plugin processor.

  ==============================================================================
*/

#pragma once

// includes
#include <JuceHeader.h>
#include "DesignsProtocol.h"
#include "libMTSMaster.h"
#include "MeterData.h"
#include "SynthSound.h"
#include "SynthVoice.h"
#include "VoiceStates.h"
#include "WilsonicAppSkin.h"
#include "WilsonicProcessorConstants.h"
#include "TuningOutput.h"

// ADD NEW SCALE DESIGN HERE
// forward declarations
class AppTuningModel;
class Brun2Model;
class CoPrimeModel;
class CPSModel;
class DesignsModel;
class DiamondsModel;
class EqualTemperamentModel;
class EulerGenusModel;
class FavoritesModelV2;
class MorphModel;
class PartchModel;
class Persian17NorthIndianModel;
class PresetsModel;
class RecurrenceRelationModel;
class ScalaModel;
class TritriadicModel;

// class
class WilsonicProcessor final
: public AudioProcessor
, public ActionBroadcaster
, private ActionListener
, private DesignsProtocol
, private Timer
{
public:
    // enums
    enum class MTS_ESP_Status {
        NotRegistered, // at start up we're not yet registered
        Registered, // registration was successful
        NeedToReregister, // not registered, and have IPC...offer user choice to register
        Failed, // failed to register
        NotSupported // ios, android, etc
    };

    // statics

    // TODO: for now sharing between targets is cool
    static File appLibraryDir() {
        // ~/Library/WilsonicMTSESP/
        File tuningsRoot = File::getSpecialLocation(File::userApplicationDataDirectory).getChildFile("WilsonicMTSESP");
        auto result = tuningsRoot.createDirectory();
        if (result.failed()) {
            DBG ("DEBUG: " << result.getErrorMessage());
            jassertfalse;
        }
        
        return tuningsRoot;
    }

    static const String getMtsEspStatusDidChangeMessage() { return "MTSESPSTATUSDIDCHANGE"; }
    static const String getMIDIPanicMessage() { return "MIDIPANICMESSAGE"; }

    // lifecycle

private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (WilsonicProcessor)

public:

#pragma mark - lifecycle

    WilsonicProcessor();
    ~WilsonicProcessor() override;

#pragma mark - plugin methods

    // Plugin methods
    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
   #ifndef JucePlugin_PreferredChannelConfigurations
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
   #endif
    void processBlock(AudioBuffer<float>&, MidiBuffer&) override;

    // Plugin properties
    AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;
    const String getName() const override;
    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;
    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int index) override;
    const String getProgramName (int index) override;
    void changeProgramName (int index, const String& newName) override;

    // Plugin state
    void getStateInformation(MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    // Synth audio levels
    const atomic<float>& getRMS();
    const atomic<float>& getPeak();
    VoiceStates getVoiceStates(); // struct: copy by value for synth
    void setVoiceStateFrequency(unsigned long nn, float frequency); // midi effect

    // keyboard
    shared_ptr<MidiKeyboardState> getKeyboardState(); // class, used by audio and message threads ==> can't copy
    float getKeyboardRMSForNN(unsigned long nn);
    void allNotesOff(); // to support synth+midi effect

    //
    WilsonicAppSkin& getAppSkin();
    // ADD NEW SCALE DESIGN HERE
    shared_ptr<AppTuningModel> getAppTuningModel();
    shared_ptr<CoPrimeModel> getCoPrimeModel();
    shared_ptr<CPSModel> getCPSModel();
    shared_ptr<DesignsModel> getDesignsModel();
    shared_ptr<DiamondsModel> getDiamondsModel();
    shared_ptr<Brun2Model> getBrun2Model();
    shared_ptr<EqualTemperamentModel> getEqualTemperamentModel();
    shared_ptr<EulerGenusModel> getEulerGenusModel();
    shared_ptr<FavoritesModelV2> getFavoritesModelV2(); // convenience
    shared_ptr<MorphModel> getMorphModel();
    shared_ptr<PartchModel> getPartchModel();
    shared_ptr<Persian17NorthIndianModel> getPersian17NorthIndianModel();
    shared_ptr<PresetsModel> getPresetsModel();
    shared_ptr<RecurrenceRelationModel> getRecurrenceRelationModel();
    shared_ptr<ScalaModel> getScalaModel();
    shared_ptr<TritriadicModel> getTritriadicModel();
    shared_ptr<AudioProcessorValueTreeState> getApvts();
    AudioProcessorValueTreeState::Listener* getProcessorAsListener();

    // ActionListener callback
    void actionListenerCallback(const String&) override;
    void debugLogApvtsState();

    // Timer
    void timerCallback() override;
    
#pragma mark - MTS-ESP
    // MTS-ESP status
    MTS_ESP_Status getMtsEspStatus();
    int getMtsEspNumberOfClients();
    bool resetMtsEsp();

#pragma mark - Properties
    // Properties
    void saveWindowBounds(Rectangle<int> bounds);
    Rectangle<int> restoreWindowBounds();
    void savePitchWheelInKeyboard(bool should_show);
    bool restorePitchWheelInKeyboard();
    void savePitchColorOffset(float offset);
    float restorePitchColorOffset();
    void saveKeyboardHeight(float height);
    float restoreKeyboardHeight();
    void saveKeyboardWidthFactor(float factor);
    float restoreKeyboardWidthFactor();
    void saveBrunDisplayMode(int mode);
    int restoreBrunDisplayMode();
    void saveShowProportionalTriads(bool should_show);
    bool restoreShowProportionalTriads();
    void saveShowGeometricTriads(bool should_show);
    bool restoreShowGeometricTriads();
    void saveKeyboardVisible(bool should_show);
    bool restoreKeyboardVisible();
    void saveOutOfBandPolicy(OutOfBandPolicy policy);
    OutOfBandPolicy restoreOutOfBandPolicy();
    void saveFavoritesStoreNPOOverride(bool should_store);
    bool restoreFavoritesStoreNPOOverride();
    void saveFavoritesStorePeriodMiddleC(bool should_store);
    bool restoreFavoritesStorePeriodMiddleC();
    void saveFavoritesStoreNNMiddleC(bool should_store);
    bool restoreFavoritesStoreNNMiddleC();
    void saveFavoritesStoreFrequencyMiddleC(bool should_store);
    bool restoreFavoritesStoreFrequencyMiddleC();
    void savePartchO1(bool o1);
    bool restorePartchO1();
    void savePartchU1(bool u1);
    bool restorePartchU1();
    void savePartchO3(bool o3);
    bool restorePartchO3();
    void savePartchU3(bool u3);
    bool restorePartchU3();
    void savePartchO5(bool o5);
    bool restorePartchO5();
    void savePartchU5(bool u5);
    bool restorePartchU5();
    void savePartchO7(bool o7);
    bool restorePartchO7();
    void savePartchU7(bool u7);
    bool restorePartchU7();
    void savePartchO9(bool o9);
    bool restorePartchO9();
    void savePartchU9(bool u9);
    bool restorePartchU9();
    void savePartchO11(bool o11);
    bool restorePartchO11();
    void savePartchU11(bool u11);
    bool restorePartchU11();

private:

#pragma mark - private members
    // private members; order is important
    WilsonicAppSkin _appSkin {}; // OWNER

    // OWNER: synth models
    // synth models
    Synthesiser _synth; // OWNER
    dsp::Reverb _reverb; // OWNER
    Reverb::Parameters _reverbParams; // OWNER
    VoiceStates _voiceStates {}; // OWNER
    MeterData _meter; // OWNER

    // tunings models...order is important
    shared_ptr<DesignsModel> _designsModel; // OWNER, order is important
    shared_ptr<AudioProcessorValueTreeState> _apvts; // order is important
    shared_ptr<MidiKeyboardState> _keyboardState;
    unique_ptr<PropertiesFile> _properties;

    // MTS-ESP
#if JUCE_IOS || JUCE_ANDROID
    MTS_ESP_Status _mtsEspStatus = MTS_ESP_Status::NotSupported;
    MTS_ESP_Status _mtsEspStatusPrevious = MTS_ESP_Status::NotSupported; // to avoid duplicate status updates
#else
    MTS_ESP_Status _mtsEspStatus = MTS_ESP_Status::NotRegistered;
    MTS_ESP_Status _mtsEspStatusPrevious = MTS_ESP_Status::NotRegistered; // to avoid duplicate status updates
#endif
    // Sample Rate for midi controller target
    float _sampleRateMIDIController = 48000.f;

#pragma mark - private methods
    // private methods
    void _MTS_helper();
    AudioProcessorValueTreeState::ParameterLayout _createParamGroup();
    unique_ptr<AudioProcessorParameterGroup> _createSynthParams();
    void _setSynthParams(); // called within process
    void _setSynthVoiceParams(); // called within process
    void _setSynthFilterParams(); // called within process
    void _setSynthReverbParams(); // called within process
    StringArray getSynthParameterIDs(); // used for Favorites

    // ADD NEW SCALE DESIGN HERE
    // DesignsProtocol
    void showBrunTuning() override;
    void showCoPrimeTuning() override;
    void showCPSTuning() override;
    void showDiamondsTuning() override;
    void showEqualTemperamentTuning() override;
    void showEulerGenusV2Tuning() override;
    void showMorphTuning() override;
    void showPartchTuning() override;
    void showPersian17NorthIndianTuning() override;
    void showPresetsTuning() override;
    void showRecurrenceRelationTuning() override;
    void showScalaTuning() override;
    void showTritriadicTuning() override;
};
