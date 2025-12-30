/*
 ==============================================================================

 RecurrenceRelationModel.cpp
 Created: 21 Mar 2022 8:44:44pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "RecurrenceRelationModel.h"
#include "DesignsModel.h"

#pragma mark - static

const StringArray RecurrenceRelationModel::__HnParameterIDs {
    getRecurrenceRelationHn1ParameterID().getParamID(),
    getRecurrenceRelationHn2ParameterID().getParamID(),
    getRecurrenceRelationHn3ParameterID().getParamID(),
    getRecurrenceRelationHn4ParameterID().getParamID(),
    getRecurrenceRelationHn5ParameterID().getParamID(),
    getRecurrenceRelationHn6ParameterID().getParamID(),
    getRecurrenceRelationHn7ParameterID().getParamID(),
    getRecurrenceRelationHn8ParameterID().getParamID(),
    getRecurrenceRelationHn9ParameterID().getParamID()
};

const StringArray RecurrenceRelationModel::__CnParameterIDs {
    getRecurrenceRelationCn1ParameterID().getParamID(),
    getRecurrenceRelationCn2ParameterID().getParamID(),
    getRecurrenceRelationCn3ParameterID().getParamID(),
    getRecurrenceRelationCn4ParameterID().getParamID(),
    getRecurrenceRelationCn5ParameterID().getParamID(),
    getRecurrenceRelationCn6ParameterID().getParamID(),
    getRecurrenceRelationCn7ParameterID().getParamID(),
    getRecurrenceRelationCn8ParameterID().getParamID(),
    getRecurrenceRelationCn9ParameterID().getParamID()
};


#pragma mark - lifecycle

RecurrenceRelationModel::RecurrenceRelationModel() {
    // rr has good defaults
    _recurrenceRelation = make_shared<RecurrenceRelation>();
    _recurrenceRelation->setOnTuningUpdate([this]() {uiNeedsUpdate();});
    _recurrenceRelation->setOnDivergence([this]() {_tuningDivergedUpdateUI();});
}

RecurrenceRelationModel::~RecurrenceRelationModel() {
    removeAllActionListeners();
    detachParameterListeners();
}

#pragma mark - public methods

shared_ptr<Tuning> RecurrenceRelationModel::getTuning() {
    return _recurrenceRelation;
}


#pragma mark - processor processBlock

// called only once: on construction of processor

unique_ptr<AudioProcessorParameterGroup> RecurrenceRelationModel::createParams()
{
    // juce String macros for automation formatting
    auto str_max_length = [](float value, int ) { return String(value).substring(0, 6); };
    auto str_float_value = [](const String& text) { return text.getFloatValue(); };

    // Tuning Param Group

    auto paramGroup = make_unique<AudioProcessorParameterGroup>
    (getGroupID(), getGroupName(), getSubgroupSeparator(),

     // Tuning Params

     // Seeds

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn1ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn1ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn1ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn2ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn2ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn2ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn3ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn3ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn3ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn4ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn4ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn4ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn5ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn5ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn5ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn6ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn6ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn6ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn7ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn7ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn7ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn8ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn8ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn8ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     make_unique<AudioParameterFloat>
     (RecurrenceRelationModel::getRecurrenceRelationHn9ParameterID(),
      RecurrenceRelationModel::getRecurrenceRelationHn9ParameterName(),
      NormalisableRange<float>
      (RecurrenceRelation::getSeedMin(),
       RecurrenceRelation::getSeedMax(),
       RecurrenceRelation::getSeedIntervalValue()
       ),
      RecurrenceRelation::getSeedDefault(),
      RecurrenceRelationModel::getRecurrenceRelationHn9ParameterName(),
      AudioProcessorParameter::genericParameter,
      str_max_length,
      str_float_value
      ),

     // Coefficients
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn1ParameterID(),
      getRecurrenceRelationCn1ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn2ParameterID(),
      getRecurrenceRelationCn2ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn3ParameterID(),
      getRecurrenceRelationCn3ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn4ParameterID(),
      getRecurrenceRelationCn4ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn5ParameterID(),
      getRecurrenceRelationCn5ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn6ParameterID(),
      getRecurrenceRelationCn6ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn7ParameterID(),
      getRecurrenceRelationCn7ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn8ParameterID(),
      getRecurrenceRelationCn8ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationCn9ParameterID(),
      getRecurrenceRelationCn9ParameterName(),
      RecurrenceRelation::getCoefficientsDescription(),
      RecurrenceRelation::getCoefficientDefault()
      ),


     // Indices
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationIndexParameterID(),
      getRecurrenceRelationIndexParameterName(),
      RecurrenceRelation::getIndicesDescription(),
      0
      ),

     // Offset
     make_unique<AudioParameterInt>
     (getRecurrenceRelationOffsetParameterID(),
      getRecurrenceRelationOffsetParameterName(),
      RecurrenceRelation::getOffsetMin(),
      RecurrenceRelation::getOffsetMax(),
      RecurrenceRelation::getOffsetDefault()
      ),

     // Number of terms
     make_unique<AudioParameterInt>
     (getRecurrenceRelationNumTermsParameterID(),
      getRecurrenceRelationNumTermsParameterName(),
      RecurrenceRelation::getNumberOfTermsMin(),
      RecurrenceRelation::getNumberOfTermsMax(),
      RecurrenceRelation::getNumberOfTermsDefault()
      ),

     // Sum Type
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationSumTypeParameterID(),
      getRecurrenceRelationSumTypeParameterName(),
      RecurrenceRelation::getSumTypeDescription(),
      RecurrenceRelation::getSumTypeDefault()
      ),

     // Seed Space
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationSeedSpaceParameterID(),
      getRecurrenceRelationSeedSpaceParameterName(),
      RecurrenceRelation::getSeedSpaceDescription(),
      RecurrenceRelation::getSeedSpaceDefault()
      )

     );

    return paramGroup;
}

String RecurrenceRelationModel::getGroupID() {
    return "Recurrence Relation";
}

String RecurrenceRelationModel::getGroupName() {
    return "Recurrence Relation";
}

String RecurrenceRelationModel::getSubgroupSeparator() {
    return " | ";
}

// key for this design's Favorites array
ParameterID RecurrenceRelationModel::getDesignParameterID() {
    return ParameterID("RECURRENCERELATION_PARAMETERID_DESIGNS", AppVersion::getVersionHint());
}

// used for Favorites
StringArray RecurrenceRelationModel::getFavoritesParameterIDs() {
    
    return StringArray(getRecurrenceRelationHn1ParameterID().getParamID(),
                       getRecurrenceRelationCn1ParameterID().getParamID(),
                       getRecurrenceRelationHn2ParameterID().getParamID(),
                       getRecurrenceRelationCn2ParameterID().getParamID(),
                       getRecurrenceRelationHn3ParameterID().getParamID(),
                       getRecurrenceRelationCn3ParameterID().getParamID(),
                       getRecurrenceRelationHn4ParameterID().getParamID(),
                       getRecurrenceRelationCn4ParameterID().getParamID(),
                       getRecurrenceRelationHn5ParameterID().getParamID(),
                       getRecurrenceRelationCn5ParameterID().getParamID(),
                       getRecurrenceRelationHn6ParameterID().getParamID(),
                       getRecurrenceRelationCn6ParameterID().getParamID(),
                       getRecurrenceRelationHn7ParameterID().getParamID(),
                       getRecurrenceRelationCn7ParameterID().getParamID(),
                       getRecurrenceRelationHn8ParameterID().getParamID(),
                       getRecurrenceRelationCn8ParameterID().getParamID(),
                       getRecurrenceRelationHn9ParameterID().getParamID(),
                       getRecurrenceRelationCn9ParameterID().getParamID(),
                       getRecurrenceRelationIndexParameterID().getParamID(),
                       getRecurrenceRelationOffsetParameterID().getParamID(),
                       getRecurrenceRelationNumTermsParameterID().getParamID(),
                       getRecurrenceRelationSumTypeParameterID().getParamID(),
                       getRecurrenceRelationSeedSpaceParameterID().getParamID()
                       );
}

// called only once: after assigning _avpts
void RecurrenceRelationModel::attachParameterListeners() {
    jassert (_apvts != nullptr);
    for (auto pid : getFavoritesParameterIDs()) {
        _apvts->addParameterListener (pid, this);
    }
}

void RecurrenceRelationModel::detachParameterListeners() {
    jassert (_apvts != nullptr);
    for (auto pid : getFavoritesParameterIDs()) {
        _apvts->removeParameterListener (pid, this);
    }
}

void RecurrenceRelationModel::parameterChanged(const String& parameterID, float newValue) {
    // indices
    if(parameterID == getRecurrenceRelationIndexParameterID().getParamID()) {
        _recurrenceRelation->setIndices(static_cast<unsigned long>(newValue));
        
        return;
    }

    // number of terms
    else if(parameterID == getRecurrenceRelationNumTermsParameterID().getParamID()) {
        _recurrenceRelation->setNumberOfTerms(static_cast<unsigned long>(newValue));
        
        return;
    }

    // offset
    else if(parameterID == getRecurrenceRelationOffsetParameterID().getParamID()) {
        _recurrenceRelation->setOffset(static_cast<unsigned long>(newValue));

        return;
    }

    // Sum Type
    else if(parameterID == getRecurrenceRelationSumTypeParameterID().getParamID()) {
        _recurrenceRelation->setSumTypeByIndex(static_cast<unsigned long>(newValue));
        return;
    }

    // Seed Space
    else if(parameterID == getRecurrenceRelationSeedSpaceParameterID().getParamID()) {
        _recurrenceRelation->setSeedSpaceByIndex(static_cast<unsigned long>(newValue));
        return;
    }

    // Seeds
    unsigned long i = 1;
    for(auto pid : __HnParameterIDs) {
        if(parameterID == pid) {
            _recurrenceRelation->setSeed(newValue, i);
            
            return;
        }
        i++;
    }

    // Coefficients
    i = 1;
    for(auto cid : __CnParameterIDs) {
        if(parameterID == cid) {
            _recurrenceRelation->setCoefficientByIndex(static_cast<unsigned long>(newValue), i);
            
            return;
        }
        i++;
    }

    // note that _recurrenceRelation marks UI as needing update with a completion block
    
    // error
    jassertfalse;
}

void RecurrenceRelationModel::updateProperties() {
}

#pragma mark - update Designs model

void RecurrenceRelationModel::_tuningChangedUpdateUI() {
    // broadcast that tuning has changed
    sendActionMessage(DesignsModel::getRecurrenceRelationTuningChangedActionMessage());
}

void RecurrenceRelationModel::_tuningDivergedUpdateUI() {
    // broadcast that tuning has diverged
    sendActionMessage(DesignsModel::getRecurrenceRelationTuningDivergedActionMessage());
}

#pragma mark - UI methods

// selects from pre-computed list of indices...i.e,(i=1, j=9)
void RecurrenceRelationModel::uiSetIndices(unsigned long value) {
    jassert(value < static_cast<unsigned long>(RecurrenceRelation::getIndicesDescription().size()));
    auto key = getRecurrenceRelationIndexParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetIndices() {
    return _recurrenceRelation->getIndices();
}

// index is 1-9, not 0-8
void RecurrenceRelationModel::uiSetSeed(float value, unsigned long i_1_9) {
    jassert(i_1_9 > 0 && i_1_9 < 10);
    auto key = __HnParameterIDs[static_cast<int>(i_1_9 - 1)];
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

float RecurrenceRelationModel::uiGetSeed(unsigned long i_1_9) {
    jassert(i_1_9 > 0 && i_1_9 < 10);
    auto id = __HnParameterIDs[static_cast<int>(i_1_9 - 1)];
    auto& param = *_apvts->getRawParameterValue(id);
    
    return param.load();
}

// index is 1-9, not 0-8
void RecurrenceRelationModel::uiSetCoefficient(unsigned long value, unsigned long i_1_9) {
    jassert(i_1_9 > 0 && i_1_9 < 10);
    auto key = __CnParameterIDs[static_cast<int>(i_1_9 - 1)];
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetCoefficient(unsigned long i_1_9) {
    jassert(i_1_9 > 0 && i_1_9 < 10);
    auto id = __CnParameterIDs[static_cast<int>(i_1_9 - 1)];
    auto& param = *_apvts->getRawParameterValue(id);

    return static_cast<unsigned long>(param.load());
}

void RecurrenceRelationModel::uiSetNumberOfTerms(unsigned long value) {
    jassert(value >= RecurrenceRelation::getNumberOfTermsMin());
    jassert(value <= RecurrenceRelation::getNumberOfTermsMax());
    auto key = getRecurrenceRelationNumTermsParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetNumberOfTerms() {
    auto& param = *_apvts->getRawParameterValue(getRecurrenceRelationNumTermsParameterID().getParamID());

    return static_cast<unsigned long>(param.load());
}

void RecurrenceRelationModel::uiSetOffset(unsigned long value) {
    jassert(value >= RecurrenceRelation::getOffsetMin());
    jassert(value <= RecurrenceRelation::getOffsetMax());
    auto key = getRecurrenceRelationOffsetParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetOffset() {
    auto& param = *_apvts->getRawParameterValue(getRecurrenceRelationOffsetParameterID().getParamID());

    return static_cast<unsigned long>(param.load());
}

const string RecurrenceRelationModel::getLog() {
    return _recurrenceRelation->getLog();
}

#pragma mark - Sum Type UI

void RecurrenceRelationModel::uiSetSumType(unsigned long value) {
    jassert(value < 2);
    auto key = getRecurrenceRelationSumTypeParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(static_cast<float>(value));
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetSumType() {
    auto& param = *_apvts->getRawParameterValue(getRecurrenceRelationSumTypeParameterID().getParamID());
    return static_cast<unsigned long>(param.load());
}

#pragma mark - Seed Space UI

void RecurrenceRelationModel::uiSetSeedSpace(unsigned long value) {
    jassert(value < 2);
    auto key = getRecurrenceRelationSeedSpaceParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(static_cast<float>(value));
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetSeedSpace() {
    auto& param = *_apvts->getRawParameterValue(getRecurrenceRelationSeedSpaceParameterID().getParamID());
    return static_cast<unsigned long>(param.load());
}
