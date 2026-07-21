/*
  ==============================================================================

    AppTuningModel.h
    Created: 14 Mar 2021 3:41:31pm
    Author:  Marcus W. Hobbs

 ==========================================================================**====
*/

#pragma once

#include <JuceHeader.h>
#include "AppVersion.h"
#include "PresetsModel.h"
#include "TuningImp.h"
#include "TuningTableImp.h"
#include "Tuning_Include.h"

// forward
class WilsonicProcessor;

// class that represents the global tuning table for the keyboard and mts-esp
// global tuning table = the designs model's current automatable state

class AppTuningModel final
: public ModelBase
, public ActionBroadcaster
{
public:
    // static methods
    static const ParameterID getAppTuningNoteNumberMiddleCParameterID() { return ParameterID("APPTUNINGNOTENUMBERMIDDLEC", AppVersion::getVersionHint()); }
    static const String getAppTuningNoteNumberMiddleCParameterName() { return "App Tuning|Note Number Middle C"; }
    
    static const ParameterID getAppTuningFrequencyMiddleCParameterID() { return ParameterID("APPTUNINGFREQUENCYMIDDLEC", AppVersion::getVersionHint()); }
    static const String getAppTuningFrequencyMiddleCParameterName() { return "App Tuning|Frequency Middle C"; }
    
    static const ParameterID getAppTuningOctaveMiddleCParameterID() { return ParameterID("APPTUNINGOCTAVEMIDDLEC", AppVersion::getVersionHint()); }
    static const String getAppTuningOctaveMiddleCParameterName() { return "App Tuning|Period Middle C"; }

    static const ParameterID getAppTuningNPOOverrideParameterID() { return ParameterID("APPTUNINGNPOOVERRIDE", AppVersion::getVersionHint()); }
    static const String getAppTuningNPOOverrideParameterName() { return "App Tuning|Notes Per Octave Override"; }
    
    static const ParameterID getAppTuningNPOOverrideEnableParameterID() { return ParameterID("APPTUNINGNPOOVERRIDE_ENABLE", AppVersion::getVersionHint()); }
    static const String getAppTuningNPOOverrideEnableParameterName() { return "App Tuning|Enable Notes Per Octave Override"; }

    static const String getAppTuningModelChangedMessage() { return "AppTuningModelChangedMessage";}

    // lifecycle
    AppTuningModel(WilsonicProcessor&);
    ~AppTuningModel() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AppTuningModel)

public:
    // ModelBase
    void setApvts(shared_ptr<AudioProcessorValueTreeState>);
    String getGroupID() override;
    String getGroupName() override;
    String getSubgroupSeparator() override;
    ParameterID getDesignParameterID() override; // key for this design's Favorites array
    StringArray getFavoritesParameterIDs() override; // used for Favorites
    unique_ptr<AudioProcessorParameterGroup> createParams() override;    
    void attachParameterListeners() override;
    void detachParameterListeners() override;
    void parameterChanged(const String& parameterID, float newValue) override;
    void updateProperties() override;

    // global tuning
    void setTuning(shared_ptr<Tuning> inputTuning);
    shared_ptr<Tuning> getTuning() override;

    // frequency
    float getTuningTableFrequency(unsigned long index);

    // NPO
    unsigned long getTuningTableNPO();

    // Genus Space keyboard mapping: display a subset of the tuning table's
    // notes as a compact keyboard where every drawn slot triggers its note
    // number in the full table ("root space").  The subset is expressed as
    // formal product identities (Microtone shortDescriptionText).  An empty
    // subset, an NPO override, or a full subset all yield the identity map.
    void setKeyboardSubset(const vector<string>& subsetDescriptions);
    bool keyboardSubsetActive();
    unsigned long getKeyboardNPO(); // keys drawn per octave
    unsigned long getKeyboardNumSlots(); // number of drawable keyboard slots
    int keyboardSlotToNoteNumber(int slot); // -1 when slot is out of range
    int noteNumberToKeyboardSlot(int noteNumber); // -1 when nn is not a subset member

    // Color

    // input frequency is in Hz
    Colour colorForFrequency(float f, float value = 1.0, float delta = 0.f);

    // input pitch is on [0,1] and therefore is already normalized by period
    Colour colorForPitch01(float p01, float value = 1.0, float delta = 0.f);
    static Colour colorForPitchNoOffset(float p);
    void setPitchColorOffset(float offset01);
    float getPitchColorOffset();
    Colour getTuningTableColor(unsigned long index);

    // Microtone Short Description
    void _setTuningTableShortDescription(string desc, unsigned long index);
    string getTuningTableShortDescription(unsigned long index);
    void _setTuningTableShortDescription2(string desc, unsigned long index);
    string getTuningTableShortDescription2(unsigned long index);
    void _setTuningTableCentsDescription(string desc, unsigned long index);
    string getTuningTableCentsDescription(unsigned long index);

    // debug description
    string getDescription();

    // mode (experimental) keep as int
    void setMode(int mode);
    int getMode();

    // properties
    bool uiGetNPOOverrideEnable();
    void uiSetNPOOverrideEnable(bool shouldEnable);
    float uiGetNPOOverride();
    void uiSetNPOOverride(float npo);
    float uiGetNoteNumberMiddleC();
    void uiSetNoteNumberMiddleC(float nn);
    float uiGetFrequencyMiddleC();
    void uiSetFrequencyMiddleC(float f);

    // keep these as int
    float uiGetOctaveMiddleC();
    void uiSetOctaveMiddleC(int o);

    // for debug builds only
    void setOverrideWithTuningTests();

private:
    // private members
    WilsonicProcessor& _processor;

    // still need npo for now
    unsigned long _notesPerOctave = 12;
    
    // global tuning used by the keyboard and synth
    shared_ptr<Tuning> _previousTuning;
    shared_ptr<Tuning> _targetTuning;
    shared_ptr<Tuning> _defaultTuning12ET; // default tuning 12et
    float _pitchColorOffset01 = 0.f;
    unsigned long _interpolationCounter = 0;
    static constexpr unsigned long _numInterpolationSteps = 20; // 20 / 80 = 0.25s
    static constexpr int _interpolationTimerHz = 80; // 48000 samples per second / 512 sample per render block
    TuningTableImp _interpolatedTable {};
    void _updateTuning();

    // Genus Space keyboard mapping
    vector<string> _keyboardSubsetDescriptions {};
    array<int, WilsonicProcessorConstants::numMidiNotes> _keyboardSlotToNoteNumber {};
    array<int, WilsonicProcessorConstants::numMidiNotes> _keyboardNoteNumberToSlot {};
    unsigned long _keyboardNumSlots = 0;
    unsigned long _keyboardNPO = 0;
    bool _keyboardSubsetActive = false;
    void _rebuildKeyboardSubsetMap();

    // Colour
    void _setTuningTableColor(Colour c, unsigned long index);
    array<Colour, WilsonicProcessorConstants::numMidiNotes> _tuningTableColor{};

    // Labels of microtone descriptions
    array<string, WilsonicProcessorConstants::numMidiNotes> _tuningTableShortDescription {};
    array<string, WilsonicProcessorConstants::numMidiNotes> _tuningTableShortDescription2 {};
    array<string, WilsonicProcessorConstants::numMidiNotes> _tuningTableCentsDescription {};

    // override with tuning tests
    bool _overrideWithTuningTests = false;

    // private methods
    void _tuningChangedUpdateUI() override;
};
