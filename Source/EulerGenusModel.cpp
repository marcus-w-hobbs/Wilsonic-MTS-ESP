/*
 ==============================================================================

 EulerGenusModel.cpp
 Created: 3 Nov 2021 8:27:18pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "EulerGenusModel.h"
#include "DesignsModel.h"
#include "EulerGenusViewModel.h"

#pragma mark - lifecycle

EulerGenusModel::EulerGenusModel()
: _A(CPS::A(1))
, _B(CPS::B(3))
, _C(CPS::C(5))
, _D(CPS::D(7))
, _E(CPS::E(9))
, _F(CPS::F(11))
{
    // caches
    _viewModelCache = make_unique<ViewModelCache>();
    _tuningCache = make_unique<TuningCache>();

    // keys
    _createDAWKeys();

    // lambda maps
    _createViewModelConstructorMap();
    _createTuningConstructorMap();
    _createTuningUpdateMap();
    _createTuningSelectionMap();

    // initial state
    _selectDAWKey(dawKeyAtIndex(2)); // EG6 CPS_6_3
}

EulerGenusModel::~EulerGenusModel() {
    removeAllActionListeners();
    detachParameterListeners();
}

#pragma mark - processor processBlock

// called only once: after assigning _avpts
void EulerGenusModel::attachParameterListeners() {
    jassert(_apvts != nullptr);
    for(auto pid : getFavoritesParameterIDs()) {
        _apvts->addParameterListener(pid, this);
    }
}

void EulerGenusModel::detachParameterListeners() {
    jassert(_apvts != nullptr);
    for(auto pid : getFavoritesParameterIDs()) {
        _apvts->removeParameterListener(pid, this);
    }
}

// DAW callback when apvts changes
void EulerGenusModel::parameterChanged(const String& parameterID, float newValue) {
    const ScopedLock sl(_lock);
    if(parameterID == getEulerGenus6ParameterID().getParamID()) {
        auto daw_key =(*_dawKeys)[static_cast<int>(newValue)];
        _selectDAWKey(daw_key);

        // _selectDAWKey() calls _updateCurrentViewModelTuning() and _tuningChangedUpdateUI() so return
        return;
    } else if(parameterID == getEulerGenus6AParameterID().getParamID()) {
        _A->setFrequencyValue(newValue);
        _A->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _A->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == getEulerGenus6BParameterID().getParamID()) {
        _B->setFrequencyValue(newValue);
        _B->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _B->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == getEulerGenus6CParameterID().getParamID()) {
        _C->setFrequencyValue(newValue);
        _C->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _C->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == getEulerGenus6DParameterID().getParamID()) {
        _D->setFrequencyValue(newValue);
        _D->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _D->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == getEulerGenus6EParameterID().getParamID()) {
        _E->setFrequencyValue(newValue);
        _E->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _E->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == getEulerGenus6FParameterID().getParamID()) {
        _F->setFrequencyValue(newValue);
        _F->setShortDescriptionText2(Microtone::getFrequencyValueDescription(newValue));
        _F->setShortDescriptionText3(Microtone::getFrequencyValueDescription(newValue));
    } else if(parameterID == getEulerGenus6GenusSpaceParameterID().getParamID()) {
        _genusSpace = newValue > 0.5f;
        if(_currentViewModel != nullptr) {
            _selectDAWKey(_currentViewModel->dawKey); // re-resolve sounding tuning under the new mode
        }

        // _selectDAWKey() calls _updateCurrentViewModelTuning() and uiNeedsUpdate() so return
        return;
    } else {
        jassertfalse;
    }

    // lazily update the right tuning
    _updateCurrentViewModelTuning();

    // Genus Space: the sounding tuning is the drill-path root, which may not be
    // the current page's parent, so refresh it with the new seeds too
    if(_genusSpace && _currentViewModel != nullptr) {
        auto const root = _genusSpaceRootTuning();
        if(root != nullptr) {
            _setTuning(root);
        }
    }

    // mark UI needs updating
    uiNeedsUpdate();
}

void EulerGenusModel::updateProperties() {
}

#pragma mark - public methods

// for SeedSlider
unsigned long EulerGenusModel::getNumberOfSeeds()
{
    return 6;
}

const int EulerGenusModel::getNumDAWKeys()
{
    // immutable, so no need to lock
    jassert(_dawKeys != nullptr); // should never happen
    return _dawKeys->size();
}

const DAWKey EulerGenusModel::dawKeyAtIndex(int index)
{
    // "immutable" after construction so no need to lock
    jassert(_dawKeys != nullptr); // should never happen
    jassert(index >= 0);
    jassert(index < _dawKeys->size());
    
    return (*_dawKeys)[index];
}

// this is the heavy lifter...host calls this, no UI calls this
void EulerGenusModel::_selectDAWKey(DAWKey daw_key) {
    // Lock
    const ScopedLock sl(_lock);

    // leaf nodes are NOP
    if(daw_key == String(__daw_key_null)) {
        
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

    // Genus Space: the drill-path root CPS(6,k) remains the sounding tuning;
    // the selection above becomes a keyboard view into the root's MIDI space
    _genusSpaceSubsetDescriptions.clear();
    if(_genusSpace) {
        auto const root = _genusSpaceRootTuning();
        if(root != nullptr) {
            auto const selected = _currentTuning;
            if(selected != nullptr && selected != root &&
               selected->getProcessedArrayCount() < root->getProcessedArrayCount()) {
                auto selectedArray = selected->getProcessedArray();
                for(unsigned long i = 0; i < selectedArray.count(); i++) {
                    _genusSpaceSubsetDescriptions.push_back(selectedArray.microtoneAtIndex(i)->getShortDescriptionText());
                }
            }
            _setTuning(root);
        }
    }

    // mark UI needs update
    uiNeedsUpdate();
}

// the design here is that the host will send the parameterChanged
// message, which will update _A, _B, etc., and then update UI w no notif

// is current tuning EG or CPS?
bool EulerGenusModel::uiIsTuningEulerGenus()
{
    const auto vm = getViewModel();
    const auto tuning = vm->parentTuning;
    const auto type = tuning->getTuningType();
    const bool isEulerGenus =(type == CPS_Class::EulerGenus_6 ||
                               type == CPS_Class::EulerGenus_5 ||
                               type == CPS_Class::EulerGenus_4 ||
                               type == CPS_Class::EulerGenus_3 ||
                               type == CPS_Class::EulerGenus_2 ||
                               type == CPS_Class::EulerGenus_1);
    return isEulerGenus;
}

bool EulerGenusModel::uiIsTuningCPS()
{
    return !uiIsTuningEulerGenus();
}

void EulerGenusModel::uiSelectDAWKey(DAWKey daw_key)
{
    // Lock
    const ScopedLock sl(_lock);

    // leaf node
    if(daw_key == String(__daw_key_null))
    {
        // NOP
        return;
    }

    // key not found
    auto index = _dawKeys->indexOf(daw_key);
    if(index == -1)
    {
        // the only time this happens is for the EulerGenus page when you hit "back".
        return;
    }

    // update host with new daw_key
    auto key = getEulerGenus6ParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(index);
    param->setValueNotifyingHost(value01);
}

void EulerGenusModel::uiSetA(float value)
{
    auto key = getEulerGenus6AParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

void EulerGenusModel::uiSetB(float value)
{
    auto key = getEulerGenus6BParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

void EulerGenusModel::uiSetC(float value)
{
    auto key = getEulerGenus6CParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

void EulerGenusModel::uiSetD(float value)
{
    auto key = getEulerGenus6DParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

void EulerGenusModel::uiSetE(float value)
{
    auto key = getEulerGenus6EParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

void EulerGenusModel::uiSetF(float value)
{
    auto key = getEulerGenus6FParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(value);
    param->setValueNotifyingHost(value01);
}

// param = atomic float

float EulerGenusModel::uiGetA()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6AParameterID().getParamID());
    return param.load();
}

float EulerGenusModel::uiGetB()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6BParameterID().getParamID());
    return param.load();
}

float EulerGenusModel::uiGetC()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6CParameterID().getParamID());
    return param.load();
}

float EulerGenusModel::uiGetD()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6DParameterID().getParamID());
    return param.load();
}

float EulerGenusModel::uiGetE()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6EParameterID().getParamID());
    return param.load();
}

float EulerGenusModel::uiGetF()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6FParameterID().getParamID());
    return param.load();
}

bool EulerGenusModel::uiGetGenusSpace()
{
    auto& param = *_apvts->getRawParameterValue(getEulerGenus6GenusSpaceParameterID().getParamID());
    return param.load() > 0.5f;
}

void EulerGenusModel::uiSetGenusSpace(bool shouldEnable)
{
    auto key = getEulerGenus6GenusSpaceParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    param->setValueNotifyingHost(shouldEnable ? 1.f : 0.f);
}

const vector<string> EulerGenusModel::getGenusSpaceSubsetDescriptions()
{
    const ScopedLock sl(_lock);
    return _genusSpaceSubsetDescriptions;
}

// "select"
void EulerGenusModel::uiLeftArrowKeyPressed()
{
    // Lock
    const ScopedLock sl(_lock);

    //
    auto parentTuning = _currentViewModel->parentTuning;
    auto const isEG = uiIsTuningEulerGenus();
    if(isEG)
    {
        _EGUILeftRightKeyPressedHelper(-1);
    }
    else
    {
        _CPSArrowKeyPressedHelper(-1, 0);
    }
}

// "select"
void EulerGenusModel::uiRightArrowKeyPressed()
{
    // Lock
    const ScopedLock sl(_lock);

    //
    auto parentTuning = _currentViewModel->parentTuning;
    auto const isEG = uiIsTuningEulerGenus();
    if(isEG)
    {
        _EGUILeftRightKeyPressedHelper(+1);
    }
    else
    {
        _CPSArrowKeyPressedHelper(+1, 0);
    }
}

// i.e., -1 or +1 for left, right
void EulerGenusModel::_EGUILeftRightKeyPressedHelper(int x_delta)
{
    jassert(x_delta == -1 || x_delta == +1);

    auto parentTuning = _currentViewModel->parentTuning;
    auto const numSubsets = parentTuning->getSubsets0().size(); // should be 6
    for(unsigned long i = 0; i < numSubsets; i++)
    {
        if(parentTuning->getSubsets0()[i]->getIsSelected())
        {
            auto index =(i + static_cast<unsigned long>(x_delta) + numSubsets) %(numSubsets);
            auto const subset_tuning = parentTuning->getSubsets0()[index];
            auto const subset_dawkey = subset_tuning->getDAWKey();
            uiSelectDAWKey(subset_dawkey);
            break;
        }
    }
}

// "select": EG is a NOP
void EulerGenusModel::uiUpArrowKeyPressed()
{
    auto parentTuning = _currentViewModel->parentTuning;
    auto const isCPS = !uiIsTuningEulerGenus();
    if(isCPS)
    {
        _CPSArrowKeyPressedHelper(0, +1);
    }
}

// "select": EG is a NOP
void EulerGenusModel::uiDownArrowKeyPressed()
{
    auto parentTuning = _currentViewModel->parentTuning;
    auto const isCPS = !uiIsTuningEulerGenus();
    if(isCPS)
    {
        _CPSArrowKeyPressedHelper(0, -1);
    }
}

//(-1,0),(1,0),(0,-1),(0,1)
void EulerGenusModel::_CPSArrowKeyPressedHelper(int x_delta, int y_delta)
{
    jassert(abs(x_delta) + abs(y_delta) == 1); //(-1,0),(1,0),(0,-1),(0,1)

    auto const parentTuning = _currentViewModel->parentTuning;
    auto const numS0 = parentTuning->getSubsets0().size();
    auto const numS1 = parentTuning->getSubsets1().size();

    // if parent is selected and right-key pressed: select subset0[0]
    if(parentTuning->getIsSelected())
    {
        if(x_delta == 1)
        {
            if(numS0 > 0)
            {
                auto const subset_tuning = parentTuning->getSubsets0()[0]; // biased to this subset
                auto const subset_dawkey = subset_tuning->getDAWKey();
                uiSelectDAWKey(subset_dawkey);
                
                return;
            }
        }
    }

    // one column: only S0, never only S1
    if(numS1 == 0)
    {
        // up/down keypress for S0
        if(abs(y_delta) == 1)
        {
            for(unsigned long i = 0; i < numS0; i++)
            {
                if(parentTuning->getSubsets0()[i]->getIsSelected())
                {
                    auto index = static_cast<unsigned long>(static_cast<int>(i) - y_delta + static_cast<int>(numS0)) % numS0;
                    auto const subset_tuning = parentTuning->getSubsets0()[index];
                    auto const subset_dawkey = subset_tuning->getDAWKey();
                    uiSelectDAWKey(subset_dawkey);
                    
                    break;
                }
            }
        }
        else
        {
            // no left/right key press for one column
            return;
        }
    }
    // S0 and S1
    else
    {
        // up/down keypress
        if(abs(y_delta) == 1)
        {
            // numS0 == numS1
            for(unsigned long i = 0; i < numS0; i++)
            {
                //S0
                if(parentTuning->getSubsets0()[i]->getIsSelected())
                {
                    auto index = static_cast<unsigned long>(static_cast<int>(i) - y_delta + static_cast<int>(numS0)) % numS0;
                    auto const subset_tuning = parentTuning->getSubsets0()[index];
                    auto const subset_dawkey = subset_tuning->getDAWKey();
                    uiSelectDAWKey(subset_dawkey);
                    
                    break;
                }
                //S1
                else if(parentTuning->getSubsets1()[i]->getIsSelected())
                {
                    auto index = static_cast<unsigned long>(static_cast<int>(i) - y_delta + static_cast<int>(numS1)) % numS1;
                    auto const subset_tuning = parentTuning->getSubsets1()[index];
                    auto const subset_dawkey = subset_tuning->getDAWKey();
                    uiSelectDAWKey(subset_dawkey);
                    
                    break;
                }
            }
        }
        // left/right keypress
        else if(abs(x_delta) == 1)
        {
            // numS0 == numS1
            for(unsigned long i = 0; i < numS0; i++)
            {
                //S0
                if(parentTuning->getSubsets0()[i]->getIsSelected())
                {
                    auto const subset_tuning = parentTuning->getSubsets1()[i]; // S0: get S1
                    auto const subset_dawkey = subset_tuning->getDAWKey();
                    uiSelectDAWKey(subset_dawkey);
                    
                    break;
                }
                //S1
                else if(parentTuning->getSubsets1()[i]->getIsSelected())
                {
                    auto const subset_tuning = parentTuning->getSubsets0()[i]; // S1: get S0
                    auto const subset_dawkey = subset_tuning->getDAWKey();
                    uiSelectDAWKey(subset_dawkey);
                    
                    break;
                }
            }
        }
    }
}

// "drill"
void EulerGenusModel::uiControlReturnPressed()
{
    // for both EG and CPS
    auto const parentTuning = _currentViewModel->parentTuning;
    auto const numS0 = parentTuning->getSubsets0().size();
    auto const numS1 = parentTuning->getSubsets1().size();

    // if parent is select, then select first tuning of subsets0; yes: biased
    if(parentTuning->getIsSelected())
    {
        if(numS0 > 0)
        {
            auto const subset_tuning = parentTuning->getSubsets0()[0];
            auto const subset_dawkey = subset_tuning->getDAWKey();
            uiSelectDAWKey(subset_dawkey);
            
            return;
        }
    }

    if(uiIsTuningCPS()) { // CPS
        for(unsigned long i = 0; i < numS0; i++) {
            //S0
            auto const s0 = parentTuning->getSubsets0()[i];
            if(s0->getIsSelected()) {
                auto const subset_dawkey = s0->getDAWKey();
                auto const subset_vm = _getViewModel(subset_dawkey);
                auto const subset_vm_dawkey = subset_vm->dawDrillKey;
                uiSelectDAWKey(subset_vm_dawkey);
                
                break;
            }
            
            //S1
            if(numS1 > 0) {
                auto const s1 = parentTuning->getSubsets1()[i];
                if(s1->getIsSelected()) {
                    auto const subset_dawkey = s1->getDAWKey();
                    auto const subset_vm = _getViewModel(subset_dawkey);
                    auto const subset_vm_dawkey = subset_vm->dawDrillKey;
                    uiSelectDAWKey(subset_vm_dawkey);
                    break;
                }
            }
        }
    } else { // uiIsTuningEulerGenus
        auto daw_drill_key = _currentViewModel->dawDrillKey;
        uiSelectDAWKey(daw_drill_key);
    }
}

// "back button"
void EulerGenusModel::uiCommandReturnPressed() {
    // "back" on Euler Genus is a NOP
    if(uiIsTuningEulerGenus()) {
        
        return;
    }
    // from here on: CPS

    // CPS "back" key
    auto const parentTuning = _currentViewModel->parentTuning;
    auto const daw_back_key = _currentViewModel->dawBackKey;
    uiSelectDAWKey(daw_back_key);
}

shared_ptr<Tuning> EulerGenusModel::getTuning() {
    return _currentTuning;
}

const shared_ptr<EulerGenusViewModel> EulerGenusModel::getViewModel() {
    return _currentViewModel;
}

#pragma mark - update Designs model

// broadcast that tuning has changed: receivers(Components) will use getViewModel() to update UI state

void EulerGenusModel::_tuningChangedUpdateUI() {
    sendActionMessage(DesignsModel::getEulerGenusTuningChangedActionMessage());
}

#pragma mark - private methods

// trivial helper
void EulerGenusModel::_setTuning(shared_ptr<Tuning> tuning) {
    _currentTuning = tuning;
}

// resolves the drill-path root CPS(6,k) page master for the current view model,
// refreshing it with the current seeds when it isn't the current page's parent
shared_ptr<CPSTuningBase> EulerGenusModel::_genusSpaceRootTuning() {
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
void EulerGenusModel::_updateCurrentViewModelTuning() {
    // update parent tuning, and all subsets
    auto parentTuningKey = _currentViewModel->parentTuningKey;
    auto ptkf =(*_tuningUpdateMap)[parentTuningKey];
    jassert(ptkf != nullptr);
    ptkf();
}

// CODEGEN
// updates the current view model's tuning's selection state
void EulerGenusModel::_updateCurrentViewModelTuningSelectionState() {
    // update selection state of current view model's parent tuning
    auto dawKey = _currentViewModel->dawKey;
    auto ucvtss =(*_tuningSelectionMap)[dawKey];
    jassert(ucvtss != nullptr);
    ucvtss();
}

// CODEGEN
// lazy loading: return value if key exists, else create, store, and return new value
shared_ptr<EulerGenusViewModel> EulerGenusModel::_getViewModel(DAWKey daw_key) {
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
// lazy loading: return value if key exists, else create, store, and return new value
shared_ptr<CPSTuningBase> EulerGenusModel::_getTuning(TuningKey tuning_key) {
    TuningCache::const_iterator iter = _tuningCache->find(tuning_key);
    if(iter != _tuningCache->end()) {
        // if tuning exists return it
        shared_ptr<CPSTuningBase> tuning = nullptr;
        tuning = iter->second;
        jassert(tuning != nullptr);
        
        return tuning;
    } else {
        // else create tuning and store it
        auto tuning_constructor =(*_tuningConstructorMap) [tuning_key];
        jassert(tuning_constructor != nullptr);
        auto t = tuning_constructor();
        jassert(t != nullptr);
       (*_tuningCache)[tuning_key] = t;
        
        return t;
    }

    // bad
    jassertfalse;
    return nullptr;
}

// CACHE
// ONLY _getTuning calls this member function via lambda when there is no entry in _tuningCache
shared_ptr<CPSTuningBase> EulerGenusModel::_create_tuning(CPS_Class tuning_class_name,
                                                           vector<Microtone_p> master_set,
                                                           vector<Microtone_p> common_terms,
                                                           DAWKey parent_key,
                                                           vector<DAWKey> s0_daw_keys,
                                                           vector<DAWKey> s1_daw_keys)
{
    shared_ptr<CPSTuningBase> cps = nullptr;
    switch(tuning_class_name) {
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
shared_ptr<EulerGenusViewModel> EulerGenusModel::_create_view_model(string daw_key, string tuning_key, string back_key, string select_key) {
    auto retVal = make_shared<EulerGenusViewModel>();
    retVal->dawKey = daw_key;
    retVal->parentTuningKey = tuning_key;
    retVal->parentTuning = _getTuning(retVal->parentTuningKey);
    retVal->dawBackKey = back_key;
    retVal->dawDrillKey = select_key;
    jassert(retVal != nullptr);
    
    return retVal;
}
