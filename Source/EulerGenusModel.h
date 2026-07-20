/*
 ==============================================================================

 EulerGenusModel.h
 Created: 3 Nov 2021 8:27:18pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#pragma once

#include <JuceHeader.h>
#include "CodegenStream.h"
#include "EulerGenus_1.h"
#include "EulerGenus_2.h"
#include "EulerGenus_3.h"
#include "EulerGenus_4.h"
#include "EulerGenus_5.h"
#include "EulerGenus_6.h"
#include "ModelBase.h"
#include "Tuning.h"
#include "Tuning_Include.h"
#include "TuningImp.h"

// shared types
#include "EulerGenusModelTypes.h"

// class
class EulerGenusModel final 
: public ModelBase
, public ActionBroadcaster
{
public:
    // static public members
    static constexpr float rangeMin = 1.f; // A,B,C,D,E,F
    static constexpr float rangeMax = 16384.f; // A,B,C,D,E,F
    static constexpr float rangeStep = 1.f; // A,B,C,D,E,F

    // static public methods
    static const ParameterID getEulerGenus6ParameterID() { return ParameterID("EULERGENUS6", AppVersion::getVersionHint()); }
    static const String getEulerGenus6ParameterName() { return "Euler Genus 6|Preset"; }
    static const ParameterID getEulerGenus6AParameterID() { return ParameterID("EULERGENUS6A", AppVersion::getVersionHint()); }
    static const String getEulerGenus6AParameterName() { return "Euler Genus 6|A"; }
    static const ParameterID getEulerGenus6BParameterID() { return ParameterID("EULERGENUS6B", AppVersion::getVersionHint()); }
    static const String getEulerGenus6BParameterName() { return "Euler Genus 6|B"; }
    static const ParameterID getEulerGenus6CParameterID() { return ParameterID("EULERGENUS6C", AppVersion::getVersionHint()); }
    static const String getEulerGenus6CParameterName() { return "Euler Genus 6|C"; }
    static const ParameterID getEulerGenus6DParameterID() { return ParameterID("EULERGENUS6D", AppVersion::getVersionHint()); }
    static const String getEulerGenus6DParameterName() { return "Euler Genus 6|D"; }
    static const ParameterID getEulerGenus6EParameterID() { return ParameterID("EULERGENUS6E", AppVersion::getVersionHint()); }
    static const String getEulerGenus6EParameterName() { return "Euler Genus 6|E"; }
    static const ParameterID getEulerGenus6FParameterID() { return ParameterID("EULERGENUS6F", AppVersion::getVersionHint()); }
    static const String getEulerGenus6FParameterName() { return "Euler Genus 6|F"; }
    // Genus Space: when enabled the drill-path root CPS(6,k) remains the global
    // tuning table/MIDI mapping while subset selection windows the keyboard.
    // IMPORTANT: appended after F to preserve DAW automation of existing params.
    static const ParameterID getEulerGenus6GenusSpaceParameterID() { return ParameterID("EULERGENUS6GENUSSPACE", AppVersion::getVersionHint()); }
    static const String getEulerGenus6GenusSpaceParameterName() { return "Euler Genus 6|Genus Space"; }

    // creates static code for 13+ files
    static void eulerGenusCodeGen();
    static void codegenWalkCPSTuningBase(shared_ptr<CPSTuningBase> cpst, const string back, const string prefix);
    static unique_ptr<CodegenStream> __stream_daw_keys_cpp;
    static unique_ptr<CodegenStream> __stream_tuning_constructor_map_cpp;
    static unique_ptr<CodegenStream> __stream_tuning_selection_map_cpp;
    static unique_ptr<CodegenStream> __stream_tuning_update_map_cpp;
    static unique_ptr<CodegenStream> __stream_view_model_constructor_map_cpp;
    // 3 ~ 13K strings === too many for DAWs
    // 4 ~ 3.5K strings === balance between perfection and DAW
    static constexpr int __cps_parent_as_leaf_min_size {4}; // parent npo on root component should be greater than equal
    static string __daw_key_null; // DAWKey for do-not-select
    static constexpr int __num_entries_limit {256};

    // lifecycle
public:
    EulerGenusModel();
    ~EulerGenusModel() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(EulerGenusModel)

    // public methods
public:
    shared_ptr<Tuning> getTuning() override;
    const shared_ptr<EulerGenusViewModel> getViewModel();

    // called only once: on construction of processor
    unique_ptr<AudioProcessorParameterGroup> createParams() override;
    String getGroupID() override;
    String getGroupName() override;
    String getSubgroupSeparator() override;
    ParameterID getDesignParameterID() override; // key for this design's Favorites array
    StringArray getFavoritesParameterIDs() override; // used for Favorites
    unsigned long getNumberOfSeeds(); // for SeedSlider
    void attachParameterListeners() override;
    void parameterChanged(const String& parameterID, float newValue) override;
    void updateProperties() override;

    // daw keys
    const int getNumDAWKeys();
    const DAWKey dawKeyAtIndex(int index); // used for morph

    // UI methods:
    // UI notifies host that param has changed, host updates state, host notifies model, model updates tuning, model sends notification to update UI.  This handles the cold start flow too.
    bool uiIsTuningEulerGenus(); // is current tuning EG or CPS?
    bool uiIsTuningCPS(); // helper: simply inverse of uiIsTuningEulerGenus()
    void uiSelectDAWKey(DAWKey);
    void uiSetA(float);
    void uiSetB(float);
    void uiSetC(float);
    void uiSetD(float);
    void uiSetE(float);
    void uiSetF(float);
    float uiGetA();
    float uiGetB();
    float uiGetC();
    float uiGetD();
    float uiGetE();
    float uiGetF();
    void uiLeftArrowKeyPressed();
    void uiRightArrowKeyPressed();
    void uiUpArrowKeyPressed();
    void uiDownArrowKeyPressed();
    void uiControlReturnPressed();
    void uiCommandReturnPressed();

    // Genus Space
    bool uiGetGenusSpace();
    void uiSetGenusSpace(bool shouldEnable);
    // formal product identities ("ABF", etc.) of the selected subset's tones,
    // for the keyboard's subset-of-root display; empty when inactive
    const vector<string> getGenusSpaceSubsetDescriptions();

private:
    void _EGUILeftRightKeyPressedHelper(int x_delta); // i.e., -1 or +1 for left, right
    void _CPSArrowKeyPressedHelper(int x_delta, int y_delta); //(-1,0), (1,0), (0,-1), (0,1)

protected:
    void detachParameterListeners() override;

private:
    // private methods
    void _createDAWKeys(); // helper called only once on construction
    void _createViewModelConstructorMap(); // helper called only once on construction
    void _createTuningConstructorMap(); // helper called only once on construction
    void _createTuningUpdateMap(); // helper called only once on construction
    void _createTuningSelectionMap(); // helper called only once on construction
    void _tuningChangedUpdateUI() override; // sends notification to UI Component to query current ViewModel
    void _selectDAWKey(DAWKey); // heavy lifter...called in host callback
    void _setTuning(shared_ptr<Tuning>); // helper called by _selectDAWKey
    shared_ptr<CPSTuningBase> _genusSpaceRootTuning(); // drill-path root CPS(6,k) of the current view model
    void _updateCurrentViewModelTuning(); // update current view model's parent tuning when the host changes ABCDEF
    void _updateCurrentViewModelTuningSelectionState(); // update current view model's tuning's selection state

public:
    // IMPORTANT: if you rename this you need to update and rerun codegen
    shared_ptr<EulerGenusViewModel> _getViewModel(DAWKey); // helper for lazy loading of ViewModels into the cache

private:
    shared_ptr<CPSTuningBase> _getTuning(TuningKey); // helper for lazy loading of parent tunings into the cache

    // keys
    unique_ptr<DAWKeys> _dawKeys = nullptr; // keys hard coded at compile time: so big we split out in a codegen file

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

    // Genus Space state: derived from the automatable params, never persisted directly
    bool _genusSpace {false};
    vector<string> _genusSpaceSubsetDescriptions {};

    // stores of automation state of master set...all tunings are updated based on these
    Microtone_p _A = nullptr;
    Microtone_p _B = nullptr;
    Microtone_p _C = nullptr;
    Microtone_p _D = nullptr;
    Microtone_p _E = nullptr;
    Microtone_p _F = nullptr;

    // codegen

    // create tuning
    shared_ptr<CPSTuningBase> _create_tuning(CPS_Class tuning_class_name, vector<Microtone_p> master_set, vector<Microtone_p> common_terms, DAWKey parent_key, vector<DAWKey> s0_daw_keys, vector<DAWKey> s1_daw_keys);

    // update tuning is handled by inline lambdas
    // select tuning is handled by inline lambdas

    // create view model
    shared_ptr<EulerGenusViewModel> _create_view_model(string daw_key, string tuning_key, string back_key, string select_key);

    // codegen declarations
#include "./EulerGenusModelCodegen/EulerGenusModel+_createDAWKeys_include.txt"
#include "./EulerGenusModelCodegen/EulerGenusModel+_createTuningConstructorMap_include.txt"
#include "./EulerGenusModelCodegen/EulerGenusModel+_createTuningSelectionMap_include.txt"
#include "./EulerGenusModelCodegen/EulerGenusModel+_createTuningUpdateMap_include.txt"
#include "./EulerGenusModelCodegen/EulerGenusModel+_createViewModelConstructorMap_include.txt"
};
