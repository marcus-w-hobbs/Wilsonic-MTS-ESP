/*
 ==============================================================================
 
 DesignsModel.cpp
 Created: 1 Nov 2021 8:01:35pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

// ADD NEW SCALE DESIGN HERE

/**
 * @file DesignsModel.cpp
 * @brief Contains the implementation of the DesignsModel class.
 * @details This file was created on 1 Nov 2021 at 8:01:35pm by Marcus W. Hobbs.
 */
#include "AppTuningModel.h"
#include "Brun2Model.h"
#include "CoPrimeModel.h"
#include "CPSModel.h"
#include "DesignsModel.h"
#include "DiamondsModel.h"
#include "EqualTemperamentModel.h"
#include "FavoritesModelV2.h"
#include "EulerGenusModel.h"
#include "MorphModel.h"
#include "PartchModel.h"
#include "Persian17NorthIndianModel.h"
#include "PresetsModel.h"
#include "RecurrenceRelationModel.h"
#include "ScalaModel.h"
#include "TritriadicModel.h"
#include "WilsonicEditor.h"
#include "WilsonicProcessor.h"

#pragma mark - lifecycle

// ADD NEW SCALE DESIGN HERE

/**
 * @brief Constructs a new DesignsModel object.
 * @details This constructor initializes the DesignsModel object with a reference to a WilsonicProcessor object.
 * @param processor A reference to a WilsonicProcessor object.
 */
DesignsModel::DesignsModel(WilsonicProcessor& processor)
: ActionBroadcaster()
, _processor(processor)
, _brun2Model(make_shared<Brun2Model>())
, _coPrimeModel(make_shared<CoPrimeModel>())
, _cpsModel(make_shared<CPSModel>())
, _diamondsModel(make_shared<DiamondsModel>())
, _equalTemperamentModel(make_shared<EqualTemperamentModel>())
, _eulerGenusModel(make_shared<EulerGenusModel>())
, _persian17NorthIndianModel(make_shared<Persian17NorthIndianModel>())
, _presetsModel(make_shared<PresetsModel>())
, _recurrenceRelationModel(make_shared<RecurrenceRelationModel>())
, _scalaModel(make_shared<ScalaModel>())
, _tritriadicModel(make_shared<TritriadicModel>())
, _favoritesModelV2(make_shared<FavoritesModelV2>(_processor))
, _morphModel(make_shared<MorphModel>(_processor))
, _partchModel(make_shared<PartchModel>(_processor))
, _appTuningModel(make_shared<AppTuningModel>(_processor))
{
    // Assert that the size of the design names, function names, tuning changed action message, tuning changed function names, and tuning param IDs for favorites are all zero.
    jassert(_designsNames.size() == 0);
    jassert(_functionNames.size() == 0);
    jassert(_tuningChangedActionMessage.size() == 0);
    jassert(_tuningChangedFunctionNames.size() == 0);
    jassert(_tuningParamIDsForFavorites.size() == 0);
    
    // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    // If you ever change this order you will break all users' presets, AND their Favorites
    // You must also update MorphABModel, which mimics this
    // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    int designIndex = 0;
    
    // 0
    // Add "Wilson's Garden" to the design names.
    _designsNames.add("Wilson's Garden");
    _tuningDesignKeys.push_back(_presetsModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showPresetsTuning();});
    _tuningChangedActionMessage.add(getPresetsTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_presetsModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this](){return _presetsModel->getFavoritesParameterIDs();});
    _presetsModel->addActionListener(this);
    _presetsModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 1
    // Add "Moments of Symmetry" to the design names.
    _designsNames.add("Moments of Symmetry");
    _tuningDesignKeys.push_back(_brun2Model->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showBrunTuning();});
    _tuningChangedActionMessage.add(getBrunTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_brun2Model->getTuning());});
    _tuningParamIDsForFavorites.push_back([this](){return _brun2Model->getFavoritesParameterIDs();});
    _brun2Model->addActionListener(this);
    _brun2Model->setDesignIndex(designIndex);
    designIndex++;
    
    // 2
    // Add "Persian 17 North Indian" to the design names.
    _designsNames.add("Persian 17 North Indian");
    _tuningDesignKeys.push_back(_persian17NorthIndianModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showPersian17NorthIndianTuning();});
    _tuningChangedActionMessage.add(getPersian17NorthIndianTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_persian17NorthIndianModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _persian17NorthIndianModel->getFavoritesParameterIDs();});
    _persian17NorthIndianModel->addActionListener(this);
    _persian17NorthIndianModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 3
    // Add "Combination Product Sets" to the design names.
    _designsNames.add("Combination Product Sets");
    _tuningDesignKeys.push_back(_cpsModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showCPSTuning();});
    _tuningChangedActionMessage.add(getCPSTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_cpsModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _cpsModel->getFavoritesParameterIDs();});
    _cpsModel->addActionListener(this);
    _cpsModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 4
    // Add "Euler Genus 6" to the design names.
    _designsNames.add("Euler Genus 6");
    _tuningDesignKeys.push_back(_eulerGenusModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showEulerGenusV2Tuning();});
    _tuningChangedActionMessage.add(getEulerGenusTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {
        _appTuningModel->setTuning(_eulerGenusModel->getTuning());
        // Genus Space: window the keyboard to the selected subset of the root
        _appTuningModel->setKeyboardSubset(_eulerGenusModel->getGenusSpaceSubsetDescriptions());
    });
    _tuningParamIDsForFavorites.push_back([this]() {return _eulerGenusModel->getFavoritesParameterIDs();});
    _eulerGenusModel->addActionListener(this);
    _eulerGenusModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 5
    // Add "Recurrence Relation" to the design names.
    _designsNames.add("Recurrence Relation");
    _tuningDesignKeys.push_back(_recurrenceRelationModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showRecurrenceRelationTuning();});
    _tuningChangedActionMessage.add(getRecurrenceRelationTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_recurrenceRelationModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _recurrenceRelationModel->getFavoritesParameterIDs();});
    _recurrenceRelationModel->addActionListener(this);
    _recurrenceRelationModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 6
    // Add "Equal Temperament" to the design names.
    _designsNames.add("Equal Temperament");
    _tuningDesignKeys.push_back(_equalTemperamentModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showEqualTemperamentTuning();});
    _tuningChangedActionMessage.add(getEqualTemperamentTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_equalTemperamentModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _equalTemperamentModel->getFavoritesParameterIDs();});
    _equalTemperamentModel->addActionListener(this);
    _equalTemperamentModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 7
    // Add "Tritriadic" to the design names.
    _designsNames.add("Tritriadic");
    _tuningDesignKeys.push_back(_tritriadicModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showTritriadicTuning();});
    _tuningChangedActionMessage.add(getTritriadicTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_tritriadicModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _tritriadicModel->getFavoritesParameterIDs();});
    _tritriadicModel->addActionListener(this);
    _tritriadicModel->setDesignIndex(designIndex);
    designIndex++;
    
    //8
    // Add "Scala" to the design names.
    _designsNames.add("Scala");
    _tuningDesignKeys.push_back(_scalaModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this](){showScalaTuning();});
    _tuningChangedActionMessage.add(getScalaTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_scalaModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _scalaModel->getFavoritesParameterIDs();});
    _scalaModel->addActionListener(this);
    _scalaModel->setDesignIndex(designIndex);
    designIndex++;
    
    //9
    // Add "CoPrime Grid" to the design names.
    _designsNames.add("CoPrime Grid");
    _tuningDesignKeys.push_back(_coPrimeModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this]() {showCoPrimeTuning();});
    _tuningChangedActionMessage.add(getCoPrimeTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_coPrimeModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _coPrimeModel->getFavoritesParameterIDs();});
    _coPrimeModel->addActionListener(this);
    _coPrimeModel->setDesignIndex(designIndex);
    designIndex++;
    
    //10
    // Add "Diamonds" to the design names.
    _designsNames.add("Diamonds");
    _tuningDesignKeys.push_back(_diamondsModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this]() {showDiamondsTuning();});
    _tuningChangedActionMessage.add(getDiamondsTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_diamondsModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _diamondsModel->getFavoritesParameterIDs();});
    _diamondsModel->addActionListener(this);
    _diamondsModel->setDesignIndex(designIndex);
    designIndex++;
    
    // 11
    // Morph!
    _designsNames.add("Morph");
    _tuningDesignKeys.push_back(_morphModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this]() {showMorphTuning();});
    _tuningChangedActionMessage.add(getMorphTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_morphModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _morphModel->getFavoritesParameterIDs();});
    _morphModel->addActionListener(this);
    _morphModel->setDesignIndex(designIndex);
    designIndex++;

    // 12
    // Partch
    _designsNames.add("Partch");
    _tuningDesignKeys.push_back(_partchModel->getDesignParameterID().getParamID());
    _functionNames.push_back([this]() {showPartchTuning();});
    _tuningChangedActionMessage.add(getPartchTuningChangedActionMessage());
    _tuningChangedFunctionNames.push_back([this]() {_appTuningModel->setTuning(_partchModel->getTuning());});
    _tuningParamIDsForFavorites.push_back([this]() {return _partchModel->getFavoritesParameterIDs();});
    _partchModel->addActionListener(this);
    _partchModel->setDesignIndex(designIndex);
    designIndex++;

    // ADD NEW SCALE DESIGN HERE

    // favorites is not a menu item, but still need to listen for automation
    _favoritesModelV2->addActionListener(this);
    
    // validate
    // Assert that the size of the designs names, tuning design keys, function names, tuning changed action message, tuning changed function names, and tuning param IDs for favorites are all equal.
    jassert(static_cast<unsigned long>(_designsNames.size()) == _tuningDesignKeys.size());
    jassert(static_cast<unsigned long>(_designsNames.size()) == _functionNames.size());
    jassert(_designsNames.size() == _tuningChangedActionMessage.size());
    jassert(static_cast<unsigned long>(_designsNames.size()) == _tuningChangedFunctionNames.size());
    jassert(static_cast<unsigned long>(_designsNames.size()) == _tuningParamIDsForFavorites.size());
    
    // when a user scala file is deleted the favoritesmodel needs to validate the favorites/morph entries.
    _scalaModel->addActionListener(_favoritesModelV2.get());
}

// ADD NEW SCALE DESIGN HERE

DesignsModel::~DesignsModel() {
    _brun2Model->removeAllActionListeners();
    _coPrimeModel->removeAllActionListeners();
    _cpsModel->removeAllActionListeners();
    _diamondsModel->removeAllActionListeners();
    _equalTemperamentModel->removeAllActionListeners();
    _eulerGenusModel->removeAllActionListeners();
    _partchModel->removeAllActionListeners();
    _persian17NorthIndianModel->removeAllActionListeners();
    _presetsModel->removeAllActionListeners();
    _recurrenceRelationModel->removeAllActionListeners();
    _scalaModel->removeAllActionListeners();
    _tritriadicModel->removeAllActionListeners();
    _favoritesModelV2->removeAllActionListeners();
    _morphModel->removeAllActionListeners();
    _appTuningModel->removeAllActionListeners();
    _favoritesModelV2->removeAllActionListeners();
    
    removeAllActionListeners();
    detachParameterListeners();
}

#pragma mark - public methods

// ADD NEW SCALE DESIGN HERE

/**
 * @brief Sets the AudioProcessorValueTreeState for the DesignsModel and its child models.
 * @param apvts The shared pointer to the AudioProcessorValueTreeState.
 */
void DesignsModel::setApvts(shared_ptr<AudioProcessorValueTreeState> apvts) {
    // Call the base class implementation of setApvts.
    // This also asserts that this method is only called once.
    ModelBase::setApvts(apvts);
    
    // Set the AudioProcessorValueTreeState for each child model and attach parameter listeners.
    // order is not important, so done alphabetically
    _brun2Model->setApvts(_apvts);
    _brun2Model->attachParameterListeners();
    
    _coPrimeModel->setApvts(_apvts);
    _coPrimeModel->attachParameterListeners();
    
    _cpsModel->setApvts(_apvts);
    _cpsModel->attachParameterListeners();
    
    _diamondsModel->setApvts(_apvts);
    _diamondsModel->attachParameterListeners();
    
    _equalTemperamentModel->setApvts(_apvts);
    _equalTemperamentModel->attachParameterListeners();
    
    _eulerGenusModel->setApvts(_apvts);
    _eulerGenusModel->attachParameterListeners();
    
    _morphModel->setApvts(_apvts);
    _morphModel->attachParameterListeners();
    
    _partchModel->setApvts(_apvts);
    _partchModel->attachParameterListeners();
    
    _persian17NorthIndianModel->setApvts(_apvts);
    _persian17NorthIndianModel->attachParameterListeners();
    
    _presetsModel->setApvts(_apvts);
    _presetsModel->attachParameterListeners();
    
    _recurrenceRelationModel->setApvts(_apvts);
    _recurrenceRelationModel->attachParameterListeners();
    
    _tritriadicModel->setApvts(_apvts);
    _tritriadicModel->attachParameterListeners();
    
    _scalaModel->setApvts(_apvts);
    _scalaModel->attachParameterListeners();
    
    _appTuningModel->setApvts(_apvts);
    _appTuningModel->attachParameterListeners();
    
    // Set the AudioProcessorValueTreeState for the favorites model.
    _favoritesModelV2->setApvts(_apvts);
    _favoritesModelV2->attachParameterListeners();
}

#pragma mark - Designs

unsigned long DesignsModel::getNumDesigns() {
    jassert(static_cast<unsigned long>(_designsNames.size()) == _functionNames.size());
    return static_cast<unsigned long>(_designsNames.size());
}

const StringArray DesignsModel::getDesignsNames() {
    jassert(static_cast<unsigned long>(_designsNames.size()) == _functionNames.size());
    return _designsNames;
}

// uiSetDesign and favoritesSetDesign are the only ways to set the global tuning

void DesignsModel::_checkDesignIndex(unsigned long index) {
    jassert(index >= 0);
    jassert(index < _tuningDesignKeys.size());
    jassert(index < _functionNames.size());
    jassert(index < _tuningChangedFunctionNames.size());
    jassert(index < static_cast<unsigned long>(_tuningChangedActionMessage.size()));
    jassert(index < _tuningParamIDsForFavorites.size());
}

void DesignsModel::uiSetDesign(unsigned long index) {
    _checkDesignIndex(index);
    _selectDesign(index);
    _updateAppTuning(index);
}

void DesignsModel::favoritesSetDesign(unsigned long index) {
    _checkDesignIndex(index);
    auto key = getDesignsParameterID();
    auto param = _apvts->getParameter(key.getParamID());
    auto range = _apvts->getParameterRange(key.getParamID());
    auto const value01 = range.convertTo0to1(index);
    param->setValueNotifyingHost(value01);
}

void DesignsModel::_selectDesign(unsigned long index) {
    auto func = _functionNames[index];
    if (func != nullptr) {
        func();
    } else {
        jassertfalse;
    }
}

void DesignsModel::_updateAppTuning(unsigned long index) {
    // Get the function that updates the app tuning.
    auto updateAppTuning = _tuningChangedFunctionNames[index];
    if (updateAppTuning != nullptr) {
        updateAppTuning();
    } else {
        jassertfalse;
    }
}

void DesignsModel::uiStoreFavorite() {
    if (_apvts == nullptr) {
        DBG("RACE: DesignsModel::uiStoreFavorite called before _apvts is set");
        jassertfalse;
    }
    
    // Check if the current tuning supports "Favorites".
    auto const current_tuning = _appTuningModel->getTuning();
    if(!current_tuning->getCanFavorite()) {
        // If it does not support "Favorites", log a message and return.
        DBG("Tuning does not support Favorites");
        return; // non-fatal
    }
    
    // Get the design parameter ID and the corresponding value.
    auto designs_param_id = DesignsModel::getDesignsParameterID().getParamID();
    auto designs_val = _apvts->getRawParameterValue(designs_param_id);
    
    // Convert the value to an unsigned long and assert that it is within the valid range.
    auto selected_design = static_cast<unsigned long>(*designs_val);
    jassert(selected_design < _tuningParamIDsForFavorites.size());
    
    // Get the design key and the design parameters.
    auto design_key = _tuningDesignKeys[selected_design];
    auto design_params = _tuningParamIDsForFavorites[selected_design](); // call lambda
    
    // Add the favorite to the favorites model.
    auto const design_name = _designsNames[static_cast<int>(selected_design)];
    
    // get npo based on whether the favorite saves the npo override, AND if the npo override is enabled
    auto const npo = (_processor.restoreFavoritesStoreNPOOverride()
                      && static_cast<bool>(_processor.getAppTuningModel()->uiGetNPOOverride()))
    ? current_tuning->getProcessedArrayNPOCount()
    : current_tuning->getProcessedArrayCount();
    auto const tuning_description = "";
    auto const tuning_param_description = current_tuning->getParameterDescription();
    _favoritesModelV2->uiAddNewFavorite
    (selected_design,
     design_name,
     npo,
     tuning_description,
     tuning_param_description,
     design_params,
     current_tuning);
}

/**
 * @brief Stores the current design as a Scala file.
 */
void DesignsModel::uiStoreScala() {
    // Get the current tuning.
    auto const t = _appTuningModel->getTuning();
    jassert(t != nullptr);
    // Check if the current tuning supports creating Scala files.
    if (! t->getCanScala()) {
        // If it does not support creating Scala files, log a message and return.
        DBG("DesignsModel::uiStoreScala: current tuning does not support creating Scala files: NOP");
        
        return;
    }
    
    // Add the tuning to the Scala user library.
    auto const success = _scalaModel->addTuningToScalaUserLibrary(t);
    if (! success) {
        // If adding the tuning to the Scala user library fails, log a message and return.
        DBG("DesignsModel::uiStoreScala: current tuning errored creating Scala: NOP");
        
        return;
    }
}

/**
 * @brief ActionListener section
 * @details Every design can receive automation. They send their update messages here.
 * To update the global tuning table we filter for the source of truth selected design.
 */

/**
 * @brief Callback function for action listener.
 * @param message The message received from the action listener.
 */
void DesignsModel::actionListenerCallback(const String& message) {
    jassert(_apvts != nullptr);
    
    // Get the design index from apvts (source of truth)
    auto& design = *_apvts->getRawParameterValue(DesignsModel::getDesignsParameterID().getParamID());
    
    // Check if the design index is valid.
    jassert(design >= 0);
    jassert(design < _tuningChangedActionMessage.size());
    
    // Get the design name.
    auto designName = _tuningChangedActionMessage[static_cast<int>(design)];
    
    // If the received message matches the design name, update the app tuning.
    if (message == designName) {
        auto updateAppTuning = _tuningChangedFunctionNames[static_cast<unsigned long>(design)];
        if (updateAppTuning != nullptr) {
            updateAppTuning();
        }
    } else {
        // If the received message does not match the design name, you can add logging here to observe messages from the other tunings.
    }
}

/**
 * @brief Processor processBlock section
 * @details This section is called only once: on construction of processor.
 */

unique_ptr<AudioProcessorParameterGroup> DesignsModel::createParams() {
    // Check if the designs names array is not empty and its size matches the function names array size.
    jassert(_designsNames.size() > 0);
    jassert(static_cast<unsigned long>(_designsNames.size()) == _functionNames.size());
    
    // Create a group of audio processor parameters for the designs.
    auto designsParamGroup = make_unique<AudioProcessorParameterGroup>
    (getGroupID(), getGroupName(), getSubgroupSeparator(),
     make_unique<AudioParameterChoice>(getDesignsParameterID(), getDesignsParameterName(), getDesignsNames(), 0)
     );
    
    return designsParamGroup;
}

String DesignsModel::getGroupID() {
    return "Designs";
}

String DesignsModel::getGroupName() {
    return "Designs";
}

String DesignsModel::getSubgroupSeparator() {
    return " | ";
}

ParameterID DesignsModel::getDesignParameterID() {
    return ParameterID("DESIGN_PARAMETERID_DESIGNS", AppVersion::getVersionHint());
}

StringArray DesignsModel::getFavoritesParameterIDs() {
    return StringArray(getDesignsParameterID().getParamID());
}

void DesignsModel::attachParameterListeners() {
    jassert(_apvts != nullptr);
    _apvts->addParameterListener(getDesignsParameterID().getParamID(), this);
}

void DesignsModel::detachParameterListeners() {
    jassert(_apvts != nullptr);
    _apvts->removeParameterListener(getDesignsParameterID().getParamID(), this);
}

/**
 * @brief Callback function for parameter changes.
 * @param parameterID The ID of the changed parameter.
 * @param newValue The new value of the changed parameter.
 */
void DesignsModel::parameterChanged(const String& parameterID, float newValue) {
    if (parameterID == getDesignsParameterID().getParamID()) {
        _selectDesign(static_cast<unsigned long>(newValue));
    } else {
        // If the changed parameter is not the designs parameter, assert false.
        jassertfalse;
    }
}

void DesignsModel::updateProperties() {
    _brun2Model->updateProperties();
    _coPrimeModel->updateProperties();
    _cpsModel->updateProperties();
    _diamondsModel->updateProperties();
    _equalTemperamentModel->updateProperties();
    _eulerGenusModel->updateProperties();
    _persian17NorthIndianModel->updateProperties();
    _presetsModel->updateProperties();
    _recurrenceRelationModel->updateProperties();
    _scalaModel->updateProperties();
    _tritriadicModel->updateProperties();
    _favoritesModelV2->updateProperties();
    _morphModel->updateProperties();
    _partchModel->updateProperties();
    _appTuningModel->updateProperties();
}

shared_ptr<Tuning> DesignsModel::getTuning() {
    return nullptr;
}

#pragma mark - Get

// ADD NEW SCALE DESIGN HERE

shared_ptr<AppTuningModel> DesignsModel::getAppTuningModel() {
    return _appTuningModel;
}

shared_ptr<Brun2Model> DesignsModel::getBrun2Model() {
    return _brun2Model;
}

shared_ptr<CoPrimeModel> DesignsModel::getCoPrimeModel() {
    return _coPrimeModel;
}

shared_ptr<CPSModel> DesignsModel::getCPSModel() {
    return _cpsModel;
}

shared_ptr<DiamondsModel> DesignsModel::getDiamondsModel() {
    return _diamondsModel;
}

shared_ptr<EqualTemperamentModel> DesignsModel::getEqualTemperamentModel() {
    return _equalTemperamentModel;
}

shared_ptr<EulerGenusModel> DesignsModel::getEulerGenusModel() {
    return _eulerGenusModel;
}

shared_ptr<MorphModel> DesignsModel::getMorphModel() {
    return _morphModel;
}

shared_ptr<PartchModel> DesignsModel::getPartchModel() {
    return _partchModel;
}
shared_ptr<Persian17NorthIndianModel> DesignsModel::getPersian17NorthIndianModel() {
    return _persian17NorthIndianModel;
}

shared_ptr<PresetsModel> DesignsModel::getPresetsModel() {
    return _presetsModel;
}

shared_ptr<RecurrenceRelationModel> DesignsModel::getRecurrenceRelationModel() {
    return _recurrenceRelationModel;
}

shared_ptr<ScalaModel> DesignsModel::getScalaModel() {
    return _scalaModel;
}

shared_ptr<TritriadicModel> DesignsModel::getTritriadicModel() {
    return _tritriadicModel;
}

shared_ptr<FavoritesModelV2> DesignsModel::getFavoritesModelV2() {
    return _favoritesModelV2;
}

// ADD NEW SCALE DESIGN HERE

#pragma mark - Show

void DesignsModel::showBrunTuning() {
    sendActionMessage(getShowBrunTuningMessage());
}

void DesignsModel::showCoPrimeTuning() {
    sendActionMessage(getShowCoPrimeTuningMessage());
}

void DesignsModel::showCPSTuning() {
    sendActionMessage(getShowCPSTuningMessage());
}

void DesignsModel::showDiamondsTuning() {
    sendActionMessage(getShowDiamondsTuningMessage());
}

void DesignsModel::showEqualTemperamentTuning() {
    sendActionMessage(getShowEqualTemperamentTuningMessage());
}

void DesignsModel::showEulerGenusV2Tuning() {
    sendActionMessage(getShowEulerGenusTuningMessage());
}

void DesignsModel::showMorphTuning() {
    sendActionMessage(getShowMorphTuningMessage());
}

void DesignsModel::showPartchTuning() {
    sendActionMessage(getShowPartchTuningMessage());
}

void DesignsModel::showPersian17NorthIndianTuning() {
    sendActionMessage(getShowPersian17NorthIndianTuningMessage());
}

void DesignsModel::showPresetsTuning() {
    sendActionMessage(getShowPresetsTuningMessage());
}

void DesignsModel::showRecurrenceRelationTuning() {
    sendActionMessage(getShowRecurrenceRelationTuningMessage());
}

void DesignsModel::showScalaTuning() {
    sendActionMessage(getShowScalaTuningMessage());
}

void DesignsModel::showTritriadicTuning() {
    sendActionMessage(getShowTritriadicTuningMessage());
}

#pragma mark - update UI

void DesignsModel::_tuningChangedUpdateUI() {
    // NOP
}
