/*
  ==============================================================================

    EulerGenusMorphModel.h
    Created: 17 Dec 2023 1:35:01pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "EulerGenusModel.h"
#include "MorphModelBase.h"

// shared types
#include "EulerGenusModelTypes.h"

//
class EulerGenusMorphModel final
: public MorphModelBase
{
public:
    EulerGenusMorphModel(WilsonicProcessor& processor);
    ~EulerGenusMorphModel() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(EulerGenusMorphModel)

public:
    /**
     * @brief Public methods.
     */
    void parameterChanged(const String& parameterID, float newValue) override;
    shared_ptr<Tuning> getTuning() override;

private:
    /**
     * @brief Private members and methods.
     */
    WilsonicProcessor& _processor;
    
    //uses EulerGenusModel DAWKeys, so doesn't create its own
    
    void _createViewModelConstructorMap(); // helper called only once on construction
    void _createTuningConstructorMap(); // helper called only once on construction
    void _createTuningUpdateMap(); // helper called only once on construction
    void _createTuningSelectionMap(); // helper called only once on construction
    void _tuningChangedUpdateUI(); // sends notification to UI Component to query current ViewModel
    void _selectDAWKey(DAWKey); // heavy lifter...called in host callback
    void _setTuning(shared_ptr<Tuning>); // helper called by _selectDAWKey
    shared_ptr<CPSTuningBase> _genusSpaceRootTuning(); // mirrors EulerGenusModel::_genusSpaceRootTuning
    void _updateCurrentViewModelTuning(); // update current view model's parent tuning when the host changes ABCDEF
    void _updateCurrentViewModelTuningSelectionState(); // update current view model's tuning's selection state

public:
    // IMPORTANT: if you rename this you need to update and rerun codegen
    shared_ptr<EulerGenusViewModel> _getViewModel(DAWKey); // helper for lazy loading of ViewModels into the cache

private:
    shared_ptr<CPSTuningBase> _getTuning(TuningKey); // helper for lazy loading of parent tunings into the cache

    // keys
    // we share EulerGenusModel's keys
    
    // view models
    shared_ptr<EulerGenusViewModel> _currentViewModel = nullptr; // current view model getter, mostly for Components
    unique_ptr<ViewModelCache> _viewModelCache = nullptr; // lazy load ViewModels
    unique_ptr<ViewModelConstructorMap> _viewModelConstructorMap = nullptr; // key, lambda for creating view model

    // tunings
    shared_ptr<Tuning> _currentTuning = nullptr; // current tuning getter, mostly for AppTuningModel
    unique_ptr<TuningCache> _tuningCache = nullptr; // lazy load parent tunings, which own/update subsets
    unique_ptr<TuningConstructorMap> _tuningConstructorMap = nullptr; // called once on construction
    unique_ptr<TuningUpdateFunctionMap> _tuningUpdateMap = nullptr; // called once on construction
    unique_ptr<TuningSelectionFunctionMap> _tuningSelectionMap = nullptr; // called once on construction

    // stores of automation state of master set...all tunings are updated based on these
    Microtone_p _A = nullptr;
    Microtone_p _B = nullptr;
    Microtone_p _C = nullptr;
    Microtone_p _D = nullptr;
    Microtone_p _E = nullptr;
    Microtone_p _F = nullptr;

    // app tuning model
    unsigned long _noteNumberMiddleC = 60;
    float _frequencyMiddleC = 261.f;
    int _octaveMiddleC = 0.f;
    int _npoOverride = 12;
    bool _npoOverrideEnable = false;

    // Genus Space (mirrors EulerGenusModel so favorites morph what was heard)
    bool _genusSpace = false;

    // codegen

    // create tuning
    shared_ptr<CPSTuningBase> _create_tuning(CPS_Class tuning_class_name, vector<Microtone_p> master_set, vector<Microtone_p> common_terms, DAWKey parent_key, vector<DAWKey> s0_daw_keys, vector<DAWKey> s1_daw_keys);

    // update tuning is handled by inline lambdas
    // select tuning is handled by inline lambdas

    // create view model
    shared_ptr<EulerGenusViewModel> _create_view_model(string daw_key, string tuning_key, string back_key, string select_key);

    // codegen declarations
//#include "./EulerGenusMorphModelCodegen/EulerGenusMorphModel+_createDAWKeys_include.txt"
#include "./EulerGenusMorphModelCodegen/EulerGenusMorphModel+_createTuningConstructorMap_include.txt"
#include "./EulerGenusMorphModelCodegen/EulerGenusMorphModel+_createTuningSelectionMap_include.txt"
#include "./EulerGenusMorphModelCodegen/EulerGenusMorphModel+_createTuningUpdateMap_include.txt"
#include "./EulerGenusMorphModelCodegen/EulerGenusMorphModel+_createViewModelConstructorMap_include.txt"
};
