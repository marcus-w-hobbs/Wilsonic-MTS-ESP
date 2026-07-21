/*
  ==============================================================================

    EulerGenusMorphModel.cpp
    Created: 17 Dec 2023 1:35:01pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "EulerGenusMorphModel.h"
#include "EulerGenusViewModel.h"
#include "WilsonicProcessor.h"

EulerGenusMorphModel::EulerGenusMorphModel(WilsonicProcessor& processor)
: _processor(processor)
, _A(CPS::A(1))
, _B(CPS::B(3))
, _C(CPS::C(5))
, _D(CPS::D(7))
, _E(CPS::E(9))
, _F(CPS::F(11))
{
    // caches
    _viewModelCache = make_unique<ViewModelCache>();
    _tuningCache = make_unique<TuningCache>();

    // we will use EulerGenusModel DAW keys
    
    // lambda maps
    _createViewModelConstructorMap();
    _createTuningConstructorMap();
    _createTuningUpdateMap();
    _createTuningSelectionMap();

    //TODO: RACE CONDITION
/*
    // initial state
    auto egm = _processor.getEulerGenusModel();
    _selectDAWKey(egm->dawKeyAtIndex(2)); // EG6 CPS_6_3
 */
}

EulerGenusMorphModel::~EulerGenusMorphModel() {
    
}


void EulerGenusMorphModel::parameterChanged(const String& parameterID, float newValue) {
    const ScopedLock sl(_lock);
    if(parameterID == EulerGenusModel::getEulerGenus6ParameterID().getParamID()) {
        auto egm = _processor.getEulerGenusModel();
        auto daw_key = egm->dawKeyAtIndex(static_cast<int>(newValue));
        _selectDAWKey(daw_key);
    } else if(parameterID == EulerGenusModel::getEulerGenus6AParameterID().getParamID()) {
        _A->setFrequencyValue(newValue);
        _A->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _A->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == EulerGenusModel::getEulerGenus6BParameterID().getParamID()) {
        _B->setFrequencyValue(newValue);
        _B->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _B->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == EulerGenusModel::getEulerGenus6CParameterID().getParamID()) {
        _C->setFrequencyValue(newValue);
        _C->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _C->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == EulerGenusModel::getEulerGenus6DParameterID().getParamID()) {
        _D->setFrequencyValue(newValue);
        _D->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _D->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == EulerGenusModel::getEulerGenus6EParameterID().getParamID()) {
        _E->setFrequencyValue(newValue);
        _E->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _E->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == EulerGenusModel::getEulerGenus6FParameterID().getParamID()) {
        _F->setFrequencyValue(newValue);
        _F->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _F->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if (parameterID == AppTuningModel::getAppTuningNoteNumberMiddleCParameterID().getParamID()) {
        _noteNumberMiddleC = static_cast<unsigned long>(newValue);
    } else if (parameterID == AppTuningModel::getAppTuningFrequencyMiddleCParameterID().getParamID()) {
        _frequencyMiddleC = newValue;
    } else if (parameterID == AppTuningModel::getAppTuningOctaveMiddleCParameterID().getParamID()) {
        _octaveMiddleC = static_cast<int>(newValue);
    } else if(parameterID == AppTuningModel::getAppTuningNPOOverrideParameterID().getParamID()) {
    _npoOverride = static_cast<int>(newValue);
    } else if(parameterID == AppTuningModel::getAppTuningNPOOverrideEnableParameterID().getParamID()) {
        _npoOverrideEnable = static_cast<bool>(newValue);
    } else if(parameterID == EulerGenusModel::getEulerGenus6GenusSpaceParameterID().getParamID()) {
        _genusSpace = newValue > 0.5f;
        if(_currentViewModel != nullptr) {
            _selectDAWKey(_currentViewModel->dawKey); // re-resolve sounding tuning under the new mode
        }

        return;
    } else {
        jassertfalse;
    }
    
    // update
    _updateCurrentViewModelTuning();

    // Genus Space: the sounding tuning is the drill-path root, which may not be
    // the current page's parent, so refresh it with the new seeds too
    if(_genusSpace && _currentViewModel != nullptr) {
        auto const root = _genusSpaceRootTuning();
        if(root != nullptr) {
            _setTuning(root);
        }
    }
}

shared_ptr<Tuning> EulerGenusMorphModel::getTuning() {
    return _currentTuning;
}

// this is the heavy lifter...host calls this, no UI calls this
void EulerGenusMorphModel::_selectDAWKey(DAWKey daw_key) {
    // Lock
    const ScopedLock sl(_lock);

    // leaf nodes are NOP
    if(daw_key == String(EulerGenusModel::__daw_key_null)) {
        return;
    }

    // lazy-load daw_key's view model
    auto vm = _getViewModel(daw_key);
    _currentViewModel = vm;
    jassert(_currentViewModel != nullptr);

    // update parent tuning of currentViewModel(using vm daw key) with ABCDEF
    _updateCurrentViewModelTuning();

    // update selection state of parent/children tunings(using vm daw key)
    _updateCurrentViewModelTuningSelectionState();

    // update currentTuning based on tuning selection state
    auto const parentTuning = _currentViewModel->parentTuning;
    if(parentTuning->getIsSelected()) {
        _setTuning(parentTuning);
    } else {
        for(auto s0 : parentTuning->getSubsets0()) {
            if(s0->getIsSelected()) {
                _setTuning(s0);
                break;
            }
        }
        for(auto s1 : parentTuning->getSubsets1()) {
            if(s1->getIsSelected()) {
                _setTuning(s1);
                break;
            }
        }
    }

    // Genus Space: the drill-path root CPS(6,k) remains the sounding tuning
    if(_genusSpace) {
        auto const root = _genusSpaceRootTuning();
        if(root != nullptr) {
            _setTuning(root);
        }
    }
}

// resolves the drill-path root CPS(6,k) page master for the current view model,
// refreshing it with the current seeds when it isn't the current page's parent
shared_ptr<CPSTuningBase> EulerGenusMorphModel::_genusSpaceRootTuning() {
    jassert(_currentViewModel != nullptr);
    auto isRank6 = [](CPS_Class type) {
        return type == CPS_Class::CPS_6_1 || type == CPS_Class::CPS_6_2 ||
               type == CPS_Class::CPS_6_3 || type == CPS_Class::CPS_6_4 ||
               type == CPS_Class::CPS_6_5 || type == CPS_Class::CPS_6_6;
    };
    auto vm = _currentViewModel;

    // at the Euler Genus page the drill target page's master is the root
    if(vm->parentTuning->isEulerGenusTuningType()) {
        vm = _getViewModel(vm->dawDrillKey);
    }

    // walk "back" until the page master is a rank-level CPS(6,k)
    auto guard = 0;
    while(vm != nullptr && !isRank6(vm->parentTuning->getTuningType()) && guard++ < 8) {
        vm = _getViewModel(vm->dawBackKey);
    }
    if(vm == nullptr || !isRank6(vm->parentTuning->getTuningType())) {
        jassertfalse; // every drill path descends from a CPS(6,k) page

        return nullptr;
    }

    // refresh the root with the current seeds when it isn't the current page's parent
    if(vm != _currentViewModel) {
        auto updateRoot = (*_tuningUpdateMap)[vm->parentTuningKey];
        jassert(updateRoot != nullptr);
        updateRoot();
    }

    return vm->parentTuning;
}

// CODEGEN
// updates the current view model's tuning with ABCDEF
void EulerGenusMorphModel::_updateCurrentViewModelTuning() {
    // update parent tuning, and all subsets
    auto parentTuningKey = _currentViewModel->parentTuningKey;
    auto ptkf =(*_tuningUpdateMap)[parentTuningKey];
    jassert(ptkf != nullptr);
    ptkf();
}

// trivial helper
void EulerGenusMorphModel::_setTuning(shared_ptr<Tuning> tuning) {
    _currentTuning = tuning;
}

shared_ptr<EulerGenusViewModel> EulerGenusMorphModel::_getViewModel(DAWKey daw_key) {
    jassert(daw_key.length() > 0);
    ViewModelCache::const_iterator iter = _viewModelCache->find(daw_key);
    if(iter != _viewModelCache->end()) {
        // if view model exists return it
        auto view_model = iter->second;
        jassert(view_model != nullptr);
        
        return view_model;
    } else {
        // else create ViewModel and store in cache
        auto view_model_constructor =(*_viewModelConstructorMap) [daw_key];
        jassert(view_model_constructor != nullptr);
        auto view_model = view_model_constructor(); // execute creation lambda
        jassert(view_model != nullptr);
        (*_viewModelCache)[daw_key] = view_model; // store in cache
        
        return view_model;
    }

    // bad
    jassertfalse;
    return nullptr;
}

// CODEGEN
// updates the current view model's tuning's selection state
void EulerGenusMorphModel::_updateCurrentViewModelTuningSelectionState() {
    // update selection state of current view model's parent tuning
    auto dawKey = _currentViewModel->dawKey;
    auto ucvtss =(*_tuningSelectionMap)[dawKey];
    jassert(ucvtss != nullptr);
    ucvtss();
}


// CACHE
// ONLY _getTuning calls this member function via lambda when there is no entry in _tuningCache
shared_ptr<CPSTuningBase> EulerGenusMorphModel::_create_tuning(CPS_Class tuning_class_name,
                                                           vector<Microtone_p> master_set,
                                                           vector<Microtone_p> common_terms,
                                                           DAWKey parent_key,
                                                           vector<DAWKey> s0_daw_keys,
                                                           vector<DAWKey> s1_daw_keys)
{
    shared_ptr<CPSTuningBase> cps = nullptr;
    switch(tuning_class_name)
    {
        case CPS_Class::CPS_1_1:
            cps = make_shared<CPS_1_1>(master_set, common_terms);
            break;
        case CPS_Class::CPS_2_1:
            cps = make_shared<CPS_2_1>(master_set, common_terms);
            break;
        case CPS_Class::CPS_2_2:
            cps = make_shared<CPS_2_2>(master_set, common_terms);
            break;
        case CPS_Class::CPS_3_1:
            cps = make_shared<CPS_3_1>(master_set, common_terms);
            break;
        case CPS_Class::CPS_3_2:
            cps = make_shared<CPS_3_2>(master_set, common_terms);
            break;
        case CPS_Class::CPS_3_3:
            cps = make_shared<CPS_3_3>(master_set, common_terms);
            break;
        case CPS_Class::CPS_4_1:
            cps = make_shared<CPS_4_1>(master_set, common_terms);
            break;
        case CPS_Class::CPS_4_2:
            cps = make_shared<CPS_4_2>(master_set, common_terms);
            break;
        case CPS_Class::CPS_4_3:
            cps = make_shared<CPS_4_3>(master_set, common_terms);
            break;
        case CPS_Class::CPS_4_4:
            cps = make_shared<CPS_4_4>(master_set, common_terms);
            break;
        case CPS_Class::CPS_5_1:
            cps = make_shared<CPS_5_1>(master_set, common_terms);
            break;
        case CPS_Class::CPS_5_2:
            cps = make_shared<CPS_5_2>(master_set, common_terms);
            break;
        case CPS_Class::CPS_5_3:
            cps = make_shared<CPS_5_3>(master_set, common_terms);
            break;
        case CPS_Class::CPS_5_4:
            cps = make_shared<CPS_5_4>(master_set, common_terms);
            break;
        case CPS_Class::CPS_5_5:
            cps = make_shared<CPS_5_5>(master_set, common_terms);
            break;
        case CPS_Class::CPS_6_1:
            cps = make_shared<CPS_6_1>(master_set, common_terms);
            break;
        case CPS_Class::CPS_6_2:
            cps = make_shared<CPS_6_2>(master_set, common_terms);
            break;
        case CPS_Class::CPS_6_3:
            cps = make_shared<CPS_6_3>(master_set, common_terms);
            break;
        case CPS_Class::CPS_6_4:
            cps = make_shared<CPS_6_4>(master_set, common_terms);
            break;
        case CPS_Class::CPS_6_5:
            cps = make_shared<CPS_6_5>(master_set, common_terms);
            break;
        case CPS_Class::CPS_6_6:
            cps = make_shared<CPS_6_6>(master_set, common_terms);
            break;
        case CPS_Class::EulerGenus_1:
            cps = make_shared<EulerGenus_1>(master_set, common_terms);
            break;
        case CPS_Class::EulerGenus_2:
            cps = make_shared<EulerGenus_2>(master_set, common_terms);
            break;
        case CPS_Class::EulerGenus_3:
            cps = make_shared<EulerGenus_3>(master_set, common_terms);
            break;
        case CPS_Class::EulerGenus_4:
            cps = make_shared<EulerGenus_4>(master_set, common_terms);
            break;
        case CPS_Class::EulerGenus_5:
            cps = make_shared<EulerGenus_5>(master_set, common_terms);
            break;
        case CPS_Class::EulerGenus_6:
            cps = make_shared<EulerGenus_6>(master_set, common_terms);
            break;
        case CPS_Class::UNDEFINED :
        case CPS_Class::Triad:
        case CPS_Class::TriadicDiamond:
        case CPS_Class::Mandala:
        case CPS_Class::Tetrad:
        case CPS_Class::TetradicDiamond:
        case CPS_Class::Pentad:
        case CPS_Class::PentadicDiamond:
        case CPS_Class::Hexad:
        case CPS_Class::HexadicDiamond:
        case CPS_Class::CPS_7_1:
        case CPS_Class::Heptad:
        case CPS_Class::HeptadicDiamond:
        case CPS_Class::CPS_8_1:
        case CPS_Class::Ogdoad:
        case CPS_Class::OgdoadicDiamond:
        default:
            jassertfalse;
            break;
    }

    // subsets sizes and daw keys sizes must match
    jassert(cps != nullptr);
    cps->setShouldComputeSubsets(true); cps->update(); cps->selectParent();
    jassert(cps->getSubsets0().size() == s0_daw_keys.size());
    jassert(cps->getSubsets1().size() == s1_daw_keys.size());

    // set the daw keys for the parent and every subset
    jassert(parent_key.length() > 0);
    cps->setDAWKey(parent_key);
    for(unsigned long index = 0; index < cps->getSubsets0().size(); index++) {
        auto s0_daw_key = s0_daw_keys[index];
        cps->getSubsets0()[index]->setDAWKey(s0_daw_key);
    }
    
    for(unsigned long index = 0; index < cps->getSubsets1().size(); index++) {
        auto s1_daw_key = s1_daw_keys[index];
        cps->getSubsets1()[index]->setDAWKey(s1_daw_key);
    }

    return cps;
}

// CACHE
// ONLY _getViewModel calls this member function via lambda when there is no entry in _tuningCache
shared_ptr<EulerGenusViewModel> EulerGenusMorphModel::_create_view_model(string daw_key, string tuning_key, string back_key, string select_key) {
    auto retVal = make_shared<EulerGenusViewModel>();
    retVal->dawKey = daw_key;
    retVal->parentTuningKey = tuning_key;
    retVal->parentTuning = _getTuning(retVal->parentTuningKey);
    retVal->dawBackKey = back_key;
    retVal->dawDrillKey = select_key;
    jassert(retVal != nullptr);
    
    return retVal;
}

// CODEGEN
// lazy loading: return value if key exists, else create, store, and return new value
shared_ptr<CPSTuningBase> EulerGenusMorphModel::_getTuning(TuningKey tuning_key)
{
    TuningCache::const_iterator iter = _tuningCache->find(tuning_key);

    if(iter != _tuningCache->end()) {
        // if tuning exists return it
        shared_ptr<CPSTuningBase> tuning = nullptr;
        tuning = iter->second;
        jassert(tuning != nullptr);
        // update app tuning model params
        tuning->setNoteNumberMiddleC(_noteNumberMiddleC);
        tuning->setOctaveMiddleC(_octaveMiddleC);
        tuning->setFrequencyMiddleC(_frequencyMiddleC);
        tuning->setNPOOverride(_npoOverride);
        tuning->setNPOOverrideEnable(_npoOverrideEnable);

        return tuning;
    } else {
        // else create tuning and store it
        auto tuning_constructor =(*_tuningConstructorMap)[tuning_key];
        jassert(tuning_constructor != nullptr);
        auto t = tuning_constructor();
        jassert(t != nullptr);
        (*_tuningCache)[tuning_key] = t;
        // update app tuning model params
        t->setNoteNumberMiddleC(_noteNumberMiddleC);
        t->setOctaveMiddleC(_octaveMiddleC);
        t->setFrequencyMiddleC(_frequencyMiddleC);
        t->setNPOOverride(_npoOverride);
        t->setNPOOverrideEnable(_npoOverrideEnable);

        return t;
    }

    // bad
    jassertfalse;
    return nullptr;
}
