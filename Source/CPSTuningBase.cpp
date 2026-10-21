/*
 ==============================================================================
 
 CPSTuningBase.cpp
 Created: 29 Aug 2021 10:06:04am
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "CPSTuningBase.h"
#include "WilsonicProcessor.h"

#pragma mark - lifecycle

CPSTuningBase::CPSTuningBase() {
    setCanNPOOverride(true);
    setCanUniquify(false);
    setCanSort(true);
    setSort(true);
    setTuningName("CPS_N_K");
    
    // subclasses will reassign this to their origin
    _p0 = CPSMicrotone_t::create_center(Point<float>(0,0));
}

CPSTuningBase::CPSTuningBase(vector<Microtone_p> , vector<Microtone_p> )
: CPSTuningBase() {
    jassertfalse;
}

#pragma mark - Scala

String CPSTuningBase::defaultScalaName() {
    return String(getTuningNameAsUnderscores() + ".scl");
}

CPS_Class CPSTuningBase::getTuningType() {
    return _tuningType;
}

String CPSTuningBase::scalaComments() {
    return TuningImp::scalaComments();
}

#pragma mark -

void CPSTuningBase::setDAWKey(DAWKey dawKey) {
    _dawKey = dawKey;
}

const DAWKey CPSTuningBase::getDAWKey() {
    return _dawKey;
}

void CPSTuningBase::clearCommonTones() {
    const ScopedLock sl(_lock);
    _commonTones.clear();
}

void CPSTuningBase::addCommonTone(Microtone_p commonTone) {
    const ScopedLock sl(_lock);
    _commonTones.push_back(commonTone);
}

const vector<Microtone_p> CPSTuningBase::getCommonTones() {
    const ScopedLock sl(_lock);
    
    return _commonTones;
}

void CPSTuningBase::setCommonTones(Microtone_p commonTone, vector<Microtone_p> commonTones)
{
    const ScopedLock sl(_lock);
    clearCommonTones();
    for(auto t : commonTones) {
        addCommonTone(t);
    }
    if(commonTone != nullptr) {
        addCommonTone(commonTone);
    }
}

/**
 * @brief Multiplies the input tones by the common tones.
 * 
 * This function takes a vector of input tones, combines it with the common tones,
 * sorts them, and then multiplies them together. The result is a new tone that is
 * the product of all the input and common tones.
 * 
 * @param inputTones A vector of input tones to be multiplied by the common tones.
 * @return A shared pointer to the resulting tone after multiplication.
 */
Microtone_p CPSTuningBase::multiplyByCommonTones(vector<Microtone_p> inputTones) {
    const ScopedLock sl(_lock);
    
    // Create a new vector that combines the input tones and the common tones.
    vector<Microtone_p> combined;
    combined.reserve(inputTones.size() + _commonTones.size());
    combined.insert(combined.end(), inputTones.begin(), inputTones.end());
    combined.insert(combined.end(), _commonTones.begin(), _commonTones.end());
    
    // Sort the combined vector.
    sort(combined.begin(), combined.end(), less_than_key());
    
    // Concatenate the descriptions of the tones and multiply their frequency values.
    auto f = 1.f;
    auto sd = string {""};
    auto sd2 = string {""};
    for(auto t : combined) {
        f *= t->getFrequencyValue();
        sd += t->getShortDescriptionText();
        sd2 += t->getShortDescriptionText2();
        if(t != combined.back()) {
            sd2 += "*";
        }
    }
    
    // Create the resulting tone.
    Microtone_p retVal = make_shared<Microtone>(f, sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    retVal->setShortDescriptionText2(sd2);
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    retVal->setDegreeName(sd); // seed letters, sorted (less_than_key sorted by short description above)
    
    return retVal;
}

const vector<shared_ptr<CPSTuningBase>> CPSTuningBase::getSubsets0() {
    
    return _subsets0;
}

const vector<shared_ptr<CPSTuningBase>> CPSTuningBase::getSubsets1() {
    
    return _subsets1;
}

void CPSTuningBase::_clearSelection() {
    _isSelected = false;
    for(auto s0 : _subsets0) {
        s0->_clearSelection();
    }
    
    for(auto s1: _subsets1) {
        s1->_clearSelection();
    }
}

void CPSTuningBase::setIsSelected(bool newValue) {
    _isSelected = newValue;
}

const bool CPSTuningBase::getIsSelected() {
    
    return _isSelected;
}

const shared_ptr<CPSTuningBase> CPSTuningBase::getSelectedSubset() {
    if(_isSelected) {
        
        return nullptr;
    }

    for(auto s0 : _subsets0) {
        if(s0->getIsSelected()) {
            
            return s0;
        }
    }
    
    for(auto s1: _subsets1) {
        if(s1->getIsSelected()) {
            
            return s1;
        }
    }

    jassertfalse;
    return nullptr;
}

void CPSTuningBase::selectParent() {
    _clearSelection();
    _isSelected = true;
}

const string CPSTuningBase::getTuningName() {
    return TuningImp::getTuningName();
}

const string CPSTuningBase::getDebugDescription() {
    string retVal = getTuningName();
    
    return retVal;
}

const string CPSTuningBase::getParameterDescription() {
    string retVal = getTuningName();
    
    return retVal;
}

#pragma mark - subsets

const bool CPSTuningBase::getShouldComputeSubsets() {
    
    return _shouldComputeSubsets;
}

void CPSTuningBase::setShouldComputeSubsets(bool should) {
    if(_shouldComputeSubsets != should) {
        const ScopedLock sl(_lock);
        _shouldComputeSubsets = should;
        update();
    }
}

const bool CPSTuningBase::_getDidAllocateSubsets() {
    return _didAllocateSubsets;
}

void CPSTuningBase::_setDidAllocateSubsets(bool didAllocate) {
    const ScopedLock sl(_lock);
    _didAllocateSubsets = didAllocate;
}
