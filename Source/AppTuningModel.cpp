/*
 ==============================================================================

 WilsonicApplicationTuningModel.cpp
 Created: 14 Mar 2021 3:41:31pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "AppTuningModel.h"
#include "DesignsModel.h"
#include "ok_color.h"
#include "WilsonicProcessor.h"
#include "WilsonicProcessorConstants.h"

// TODO: Make MTSMPE conditional
#include "libMTSMaster.h"

#pragma mark - Lifecycle

AppTuningModel::AppTuningModel(WilsonicProcessor& processor)
: _processor(processor) {
    // default tuning
    _defaultTuning12ET = make_shared<TuningImp>();
    _defaultTuning12ET->setOctaveMiddleC(Tuning::octaveMiddleCDefault);
    _defaultTuning12ET->setFrequencyMiddleC(TuningConstants::middleCFrequency);
    _defaultTuning12ET->setNoteNumberMiddleC(Tuning::noteNumberMiddleCDefault);
    _defaultTuning12ET->setSort(true);
    _defaultTuning12ET->setOctaveReduce(true);
    _defaultTuning12ET->setUniquify(false);
    _defaultTuning12ET->setCanSort(true);
    _defaultTuning12ET->setCanUniquify(false);

    // default pointer
    _targetTuning = _defaultTuning12ET;

    // _pitchColorOffset01 is initialized in setApvts

    // cannot call update until apvts is set
    // cannot start timer until apvts is set
}

AppTuningModel::~AppTuningModel() {
    removeAllActionListeners();
    detachParameterListeners();
}

#pragma mark - ModelBase

void AppTuningModel::setApvts(shared_ptr<AudioProcessorValueTreeState> apvts) {
    ModelBase::setApvts(apvts); // call "super"
    
    // can't call this in constructor
    _pitchColorOffset01 = _processor.restorePitchColorOffset();
}

String AppTuningModel::getGroupID() {
    return "AppTuning";
}

String AppTuningModel::getGroupName() {
    return "AppTuning";
}

String AppTuningModel::getSubgroupSeparator() {
    return " | ";
}

// key for this design's Favorites array * not sure this makes sense
ParameterID AppTuningModel::getDesignParameterID() {
    return ParameterID("APP_TUNING_MODEL_NOT_A_DESIGN", AppVersion::getVersionHint());
}

StringArray AppTuningModel::getFavoritesParameterIDs() {
    return StringArray(getAppTuningOctaveMiddleCParameterID().getParamID(),
                       getAppTuningFrequencyMiddleCParameterID().getParamID(),
                       getAppTuningNoteNumberMiddleCParameterID().getParamID(),
                       getAppTuningNPOOverrideEnableParameterID().getParamID(),
                       getAppTuningNPOOverrideParameterID().getParamID());
}

// called only once: on construction of processor

unique_ptr<AudioProcessorParameterGroup> AppTuningModel::createParams() {
    // Tuning Params

    auto paramGroup = make_unique<AudioProcessorParameterGroup>
    (getGroupID(), getGroupName(), getSubgroupSeparator(),

     // Frequency at Middle C
     make_unique<AudioParameterFloat>
     (AppTuningModel::getAppTuningFrequencyMiddleCParameterID(),
      AppTuningModel::getAppTuningFrequencyMiddleCParameterName(),
      NormalisableRange<float>
      (Tuning::frequencyMiddleCMin,
       Tuning::frequencyMiddleCMax,
       0.f),
      Tuning::frequencyMiddleCDefault,
      AppTuningModel::getAppTuningFrequencyMiddleCParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int) { return String(value).substring(0, WilsonicProcessorConstants::defaultNumPrecisionDigits); },
[](const String& text) { return text.getFloatValue(); }
      ),

     // Note Number at Middle C
     make_unique<AudioParameterInt>
     (AppTuningModel::getAppTuningNoteNumberMiddleCParameterID(),
      AppTuningModel::getAppTuningNoteNumberMiddleCParameterName(),
      Tuning::noteNumberMiddleCMin,
      Tuning::noteNumberMiddleCMax,
      Tuning::noteNumberMiddleCDefault
      ),

     // Octave at Middle C
     make_unique<AudioParameterInt>
     (AppTuningModel::getAppTuningOctaveMiddleCParameterID(),
      AppTuningModel::getAppTuningOctaveMiddleCParameterName(),
      Tuning::octaveMiddleCMin,
      Tuning::octaveMiddleCMax,
      Tuning::octaveMiddleCDefault
      ),
     
     // NPO Override Enable
     make_unique<AudioParameterBool>
     (getAppTuningNPOOverrideEnableParameterID(),
      getAppTuningNPOOverrideEnableParameterName(),
      Tuning::npoOverrideEnableDefault),

     // NPO override
     make_unique<AudioParameterInt>
     (AppTuningModel::getAppTuningNPOOverrideParameterID(),
      AppTuningModel::getAppTuningNPOOverrideParameterName(),
      Tuning::npoOverrideMin,
      Tuning::npoOverrideMax,
      Tuning::npoOverrideDefault
      )
     );

    return paramGroup;
}

void AppTuningModel::attachParameterListeners() {
    jassert (_apvts != nullptr);
    for (auto pid : getFavoritesParameterIDs()) {
        _apvts->addParameterListener (pid, this);
    }
}

void AppTuningModel::detachParameterListeners() {
    jassert (_apvts != nullptr);
    for (auto pid : getFavoritesParameterIDs()) {
        _apvts->removeParameterListener (pid, this);
    }
}

// this catches changes from DAW's, but maybe not from ui interactions, or morphing.
// so we also update Tunings in other places.
void AppTuningModel::parameterChanged(const String& parameterID, float newValue) {
    if(parameterID == getAppTuningNoteNumberMiddleCParameterID().getParamID()) {
        _targetTuning->setNoteNumberMiddleC(static_cast<unsigned long>(newValue));
    } else if(parameterID == getAppTuningFrequencyMiddleCParameterID().getParamID()) {
        _targetTuning->setFrequencyMiddleC(newValue);
    } else if(parameterID == getAppTuningOctaveMiddleCParameterID().getParamID()) {
        _targetTuning->setOctaveMiddleC(static_cast<int>(newValue));
    } else if(parameterID == getAppTuningNPOOverrideParameterID().getParamID()) {
        _targetTuning->setNPOOverride(static_cast<int>(newValue));
    } else if(parameterID == getAppTuningNPOOverrideEnableParameterID().getParamID()) {
        _targetTuning->setNPOOverrideEnable(static_cast<bool>(newValue));
    } else {
        jassertfalse;
    }

    // this modelbase is different in that we do NOT throttle tuning table updates
    _updateTuning();
    
    // but, like other modelbase's, we DO want to throttle ui updates
    uiNeedsUpdate();
}

void AppTuningModel::updateProperties() {
}

#pragma mark - set/get/update tuning

void AppTuningModel::setTuning(shared_ptr<Tuning> inputTuning) {
#if DEBUG
    // NOP for tuning test overrides
    if (_overrideWithTuningTests) {
        DBG("WARNING: AppTuningModel locked to previously-set tuning");
        return;
    }
#endif
    
    // every design change resets the keyboard subset; the Euler Genus design
    // re-applies it via setKeyboardSubset immediately after setTuning
    _keyboardSubsetDescriptions.clear();

    // don't change
    if (inputTuning == _targetTuning) {// call _updateTuning every time the _targetTuning is updated
        // NOP, but need to fall through
    } else if (inputTuning == nullptr) { // change global tuning to local tuning
        _targetTuning = _defaultTuning12ET;
    } else { // change global to input tuning
        _targetTuning = inputTuning;
        _targetTuning->setOctaveMiddleC(static_cast<int>(uiGetOctaveMiddleC()));
        _targetTuning->setNoteNumberMiddleC(static_cast<unsigned long>(uiGetNoteNumberMiddleC()));
        _targetTuning->setFrequencyMiddleC(uiGetFrequencyMiddleC());
        _targetTuning->setNPOOverrideEnable(uiGetNPOOverrideEnable());
        _targetTuning->setNPOOverride(static_cast<int>(uiGetNPOOverride()));
    }
    
    // this modelbase is different in that we do NOT throttle tuning table updates
    _updateTuning();
    
    // but, like other modelbase's, we DO want to throttle ui updates
    uiNeedsUpdate();
}

shared_ptr<Tuning> AppTuningModel::getTuning() {
    return _targetTuning;
}

void AppTuningModel::_updateTuning() {
    const ScopedLock sl(_lock);
    bool const registered_as_mts_esp_source = _processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::Registered;
    auto const tuningName = _targetTuning->getTuningName();
    if(registered_as_mts_esp_source) {
#if JUCE_IOS || JUCE_ANDROID
        //NOP
#else
        auto const tuningNameCstr = tuningName.c_str();
        MTS_SetScaleName(tuningNameCstr);
        MTS_ClearNoteFilter();
#endif
    }

    // MTS frequencies
    for(unsigned long nn = 0; nn < WilsonicProcessorConstants::numMidiNotes; nn++) {
        // microtone at this note number
        auto microtone = _targetTuning->microtoneAtNoteNumber(nn);
        if(registered_as_mts_esp_source) {
#if JUCE_IOS || JUCE_ANDROID
            // NOP
#else
            auto const cnn = static_cast<char>(nn);
            auto const f = _targetTuning->getTuningTableFrequency(nn);
            MTS_SetNoteTuning(f, cnn); // both synth and midi efx
            if(microtone->getFilterNote()) {
                MTS_FilterNote(true, cnn, 0);
            }
#endif
        }

        // descriptions
        auto shortDescription = microtone->getShortDescriptionText();
        _setTuningTableShortDescription(shortDescription, nn);
        auto shortDescription2 = microtone->getShortDescriptionText2();
        _setTuningTableShortDescription2(shortDescription2, nn);
        auto centsDescription = microtone->getCentsValueDescription();
        _setTuningTableCentsDescription(centsDescription, nn);
        
        // color
        auto const p01 = microtone->getPitchValue01();
        auto color = microtone->getFilterNote() ? Colours::grey : colorForPitch01(p01); // grey for filtered notes
        _setTuningTableColor(color, nn);
    }
    
    
#if 0
    // this worked with jun-6 v, but not with pianoteq
    // temp test for mts channels
    for(auto c = 0; c < 16; c++) {
        MTS_SetMultiChannel(true, c);
        for(unsigned long nn = 0; nn < WilsonicProcessorConstants::numMidiNotes; nn++) {
            auto f = 261 * pow(2, (static_cast<double>(c)/12));
            MTS_SetMultiChannelNoteTuning(f , nn, c);
        }
    }
#endif

#if 0
    // once jun-6 had "set multichannel true" it stayed in multichannel mode until I used mts-esp to set it back to false.
    for(auto c = 0; c < 16; c++) {
        MTS_SetMultiChannel(false, c);
    }
#endif

    // the tuning table changed, so re-derive the keyboard subset mapping
    _rebuildKeyboardSubsetMap();
}

#pragma mark - Genus Space keyboard mapping

// empty subset clears; the keyboard reverts to the identity map
void AppTuningModel::setKeyboardSubset(const vector<string>& subsetDescriptions) {
    const ScopedLock sl(_lock);
    _keyboardSubsetDescriptions = subsetDescriptions;
    _rebuildKeyboardSubsetMap();
}

void AppTuningModel::_rebuildKeyboardSubsetMap() {
    const ScopedLock sl(_lock);
    _keyboardSlotToNoteNumber.fill(-1);
    _keyboardNoteNumberToSlot.fill(-1);
    _keyboardNumSlots = 0;
    _keyboardNPO = 0;
    _keyboardSubsetActive = false;
    if (_keyboardSubsetDescriptions.empty() || _targetTuning == nullptr) {
        return;
    }

    // NPO override wins: the override resamples the tuning table, so the
    // subset view is bypassed rather than mismapped
    if (uiGetNPOOverrideEnable()) {
        return;
    }

    // a subset as large as the table is the identity: keep the legacy display
    set<string> members(_keyboardSubsetDescriptions.begin(), _keyboardSubsetDescriptions.end());
    if (members.size() >= _targetTuning->getProcessedArrayNPOCount()) {
        return;
    }

    // compact ascending note numbers whose tone is a subset member into slots
    for (unsigned long nn = 0; nn < WilsonicProcessorConstants::numMidiNotes; nn++) {
        auto microtone = _targetTuning->microtoneAtNoteNumber(nn);
        if (microtone == nullptr) {
            continue;
        }
        if (members.count(microtone->getShortDescriptionText()) == 1) {
            _keyboardSlotToNoteNumber[_keyboardNumSlots] = static_cast<int>(nn);
            _keyboardNoteNumberToSlot[nn] = static_cast<int>(_keyboardNumSlots);
            _keyboardNumSlots++;
        }
    }
    _keyboardNPO = members.size();
    _keyboardSubsetActive = _keyboardNumSlots > 0;
}

bool AppTuningModel::keyboardSubsetActive() {
    const ScopedLock sl(_lock);
    return _keyboardSubsetActive;
}

unsigned long AppTuningModel::getKeyboardNPO() {
    const ScopedLock sl(_lock);
    return _keyboardSubsetActive ? _keyboardNPO : getTuningTableNPO();
}

unsigned long AppTuningModel::getKeyboardNumSlots() {
    const ScopedLock sl(_lock);
    return _keyboardSubsetActive ? _keyboardNumSlots : WilsonicProcessorConstants::numMidiNotes;
}

int AppTuningModel::keyboardSlotToNoteNumber(int slot) {
    const ScopedLock sl(_lock);
    if (slot < 0 || slot >= static_cast<int>(WilsonicProcessorConstants::numMidiNotes)) {
        return -1;
    }
    if (!_keyboardSubsetActive) {
        return slot;
    }

    return _keyboardSlotToNoteNumber[static_cast<unsigned long>(slot)];
}

int AppTuningModel::noteNumberToKeyboardSlot(int noteNumber) {
    const ScopedLock sl(_lock);
    if (noteNumber < 0 || noteNumber >= static_cast<int>(WilsonicProcessorConstants::numMidiNotes)) {
        return -1;
    }
    if (!_keyboardSubsetActive) {
        return noteNumber;
    }

    return _keyboardNoteNumberToSlot[static_cast<unsigned long>(noteNumber)];
}

#pragma mark - Frequency

float AppTuningModel::getTuningTableFrequency(unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);
    return _targetTuning->getTuningTableFrequency(nn);
}

// NPO

unsigned long AppTuningModel::getTuningTableNPO() {
    return _targetTuning->getProcessedArrayNPOCount();
}

#pragma mark - Color

void AppTuningModel::setPitchColorOffset(float offset01) {
    _pitchColorOffset01 = jlimit(0.f, 1.f, offset01);
    _processor.savePitchColorOffset(_pitchColorOffset01);
    _updateTuning(); // updates color for each midi note
}

float AppTuningModel::getPitchColorOffset() {
    return _pitchColorOffset01;
}

// DEPRECATED
Colour AppTuningModel::colorForFrequency(float f, float v01, float delta) {
    if (f <= 0 || std::isnan(f) || std::isinf(f)) { // must be positive and finite
        return AppExperiments::frequencyOutOfRangeColor();
    }
    auto const period = _targetTuning->getOctave();
    auto const middleC = _targetTuning->getFrequencyMiddleC();
    auto pitch = logf(f / middleC) / logf(period);
    while (pitch < 0) {
        pitch += 1.f;
    }
    auto const pitch01 = fmodf(pitch, 1.f); // unneccessary
    return colorForPitch01(pitch01, v01, delta); // this will add the pitchColorOffset
}

// pitch01 is log-base period of frequency, modulus 1

Colour AppTuningModel::colorForPitch01(float p01, float v01, float delta) {
    // must be finite
    if(std::isnan(p01) || std::isinf(p01) || std::isnan(delta) || std::isinf(delta)) {
        return AppExperiments::frequencyOutOfRangeColor();
    }
    p01 = jlimit(0.f, 1.f, p01); // TODO: fmodf this?
    p01 += _pitchColorOffset01;
    p01 = fmodf(p01, 1.f);
    auto const saturation = 0.7f;
    auto const value = 0.70f * v01;
    constexpr float delta_delta = 0.1f;
    auto const v = jlimit(0.f, 1.f, value + delta * delta_delta);

    // perceptually uniform color space
    ok_color::HSV const ok_hsv = {p01, saturation, v};
    auto const ok_rgb = ok_color::okhsv_to_srgb(ok_hsv);
    auto const rgb = Colour::fromFloatRGBA(ok_rgb.r, ok_rgb.g, ok_rgb.b, 1.f);
    return rgb;
}

// p is in log-base-period space
Colour AppTuningModel::colorForPitchNoOffset(float p) {
    // must be finite
    if (std::isnan(p) || std::isinf(p)) {
        return AppExperiments::frequencyOutOfRangeColor();
    }

    auto p01 = p;
    while (p01 >= 1.f) {
        p01 -= 1.f;
    }
    while (p01 < 0.f) {
        p01 += 1.f;
    }

    // clamp
    p01 = jlimit(0.f, 1.f, p01);
    auto const saturation = 0.7f;
    auto const value = 0.70f;

    // perceptually uniform color space
    ok_color::HSV const ok_hsv = {p01, saturation, value};
    auto const ok_rgb = ok_color::okhsv_to_srgb(ok_hsv);
    auto const rgb = Colour::fromFloatRGBA(ok_rgb.r, ok_rgb.g, ok_rgb.b, 1.f);
    return rgb;
}

void AppTuningModel::_setTuningTableColor(Colour c, unsigned long nn) {
    if (nn > 127) { // out of range is a NOP
        return;
    }
    _tuningTableColor[nn] = c;
}

Colour AppTuningModel::getTuningTableColor(unsigned long nn) {
    auto const i = jlimit<unsigned long>(0, 127, nn);
    auto const retVal = _tuningTableColor[i];
    return retVal;
}

#pragma mark - debug builds only

void AppTuningModel::setOverrideWithTuningTests() {
#if DEBUG
    _overrideWithTuningTests = true;
#endif
}

#pragma mark - Short Description

void AppTuningModel::_setTuningTableShortDescription(string desc, unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);
    _tuningTableShortDescription[nn] = desc;
}

string AppTuningModel::getTuningTableShortDescription(unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);

    return _tuningTableShortDescription[nn];
}

void AppTuningModel::_setTuningTableShortDescription2(string desc, unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);
    _tuningTableShortDescription2[nn] = desc;
}

string AppTuningModel::getTuningTableShortDescription2(unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);
    return _tuningTableShortDescription2[nn];
}

void AppTuningModel::_setTuningTableCentsDescription(string desc, unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);
    _tuningTableCentsDescription[nn] = desc;
}

string AppTuningModel::getTuningTableCentsDescription(unsigned long nn) {
    jassert(nn < WilsonicProcessorConstants::numMidiNotes);
    return _tuningTableCentsDescription[nn];
}

#pragma mark - debug

string AppTuningModel::getDescription() {
    ostringstream stringStream;
    for (unsigned long nn = 0; nn < WilsonicProcessorConstants::numMidiNotes; nn++) {
        auto const f = getTuningTableFrequency(nn); // frequency
        auto const d = getTuningTableShortDescription(nn); // short description
        stringStream << to_string(nn) << ": ";
        stringStream << to_string(f) << ": ";
        stringStream << d << endl;
    }
    return stringStream.str();
}

#pragma mark - update global tuning

// keep mode as int

void AppTuningModel::setMode(int mode) {
    _targetTuning->setMode(mode);
}

int AppTuningModel::getMode() {
    return _targetTuning->getMode();
}

bool AppTuningModel::uiGetNPOOverrideEnable() {
    auto id = getAppTuningNPOOverrideEnableParameterID().getParamID();
    auto& param = *_apvts->getRawParameterValue(id);
    auto const pfval = param.load();
    auto const retVal = (pfval > 0.f) ? true : false;
    return retVal;
}

void AppTuningModel::uiSetNPOOverrideEnable(bool shouldEnable) {
    auto key = getAppTuningNPOOverrideEnableParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(shouldEnable);
    param->setValueNotifyingHost(value01);
}

float AppTuningModel::uiGetNPOOverride() {
    auto id = getAppTuningNPOOverrideParameterID().getParamID();
    auto& param = *_apvts->getRawParameterValue(id);
    return param.load();
}

void AppTuningModel::uiSetNPOOverride(float npo) {
    auto key = getAppTuningNPOOverrideParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(npo);
    param->setValueNotifyingHost(value01);
}

float AppTuningModel::uiGetNoteNumberMiddleC() {
    auto id = getAppTuningNoteNumberMiddleCParameterID().getParamID();
    auto& param = *_apvts->getRawParameterValue(id);
    return param.load();
}

void AppTuningModel::uiSetNoteNumberMiddleC(float value) {
    auto key = getAppTuningNoteNumberMiddleCParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

float AppTuningModel::uiGetFrequencyMiddleC() {
    auto id = getAppTuningFrequencyMiddleCParameterID().getParamID();
    auto& param = *_apvts->getRawParameterValue(id);
    return param.load();
}

void AppTuningModel::uiSetFrequencyMiddleC(float value) {
    auto key = getAppTuningFrequencyMiddleCParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

float AppTuningModel::uiGetOctaveMiddleC() {
    auto id = getAppTuningOctaveMiddleCParameterID().getParamID();
    auto& param = *_apvts->getRawParameterValue(id);
    return param.load();
}

void AppTuningModel::uiSetOctaveMiddleC(int value) {
    auto key = getAppTuningOctaveMiddleCParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

#pragma mark - ActionBroadcaster

void AppTuningModel::_tuningChangedUpdateUI() {
    sendActionMessage(DesignsModel::getAppTuningChangedActionMessage()); // UNUSED
    sendActionMessage(getAppTuningModelChangedMessage()); // very much used
}
