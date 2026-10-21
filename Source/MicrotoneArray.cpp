/**
 * @file MicrotoneArray.cpp
 * @author Marcus W. Hobbs
 * @date 14 Feb 2021
 * @brief This file contains the implementation of the MicrotoneArray class.
 */

#include <algorithm>
#include "MicrotoneArray.h"
#include "Tuning.h"

#pragma mark - Lifecycle

/**
 * @brief Default constructor for the MicrotoneArray class.
 */
MicrotoneArray::MicrotoneArray() {
}

/**
 * @brief Copy constructor for the MicrotoneArray class.
 * @param m The MicrotoneArray object to be copied.
 */
MicrotoneArray::MicrotoneArray(const MicrotoneArray& m) {
    const ScopedLock sl(_lock);
    for(auto mt : m._array) {
        Microtone_p mtn = mt->clone();
        _array.push_back(mtn);
    }
    _period = m._period;
}

MicrotoneArray::~MicrotoneArray() {
}

MicrotoneArray& MicrotoneArray::operator=(const MicrotoneArray& other) {
    if(this != &other) {
        const ScopedLock sl(_lock);
        _period = other._period;
        // Copy the data from 'other' to 'this'
        _array.clear();
        for(auto mt : other._array) {
            Microtone_p mtn = mt->clone();
            _array.push_back(mtn);
        }
    }
    
    return *this;
}

/*

MicrotoneArray::MicrotoneArray(MicrotoneArray&& other) noexcept
: _array(std::move(other._array))
, _period(other._period) {
    
}

MicrotoneArray& MicrotoneArray::operator=(MicrotoneArray&& other) noexcept {
    if (this != &other) {
        _array = std::move(other._array);
        _period = other._period;
    }
    
    return *this;
}
*/

/**
 * @brief Constructor for the MicrotoneArray class that deep-copies a vector of Microtone_p objects.
 * @param a The vector of Microtone_p objects.
 */
MicrotoneArray::MicrotoneArray(vector<Microtone_p> a) {
    for(auto mt : a) {
        Microtone_p mtn = mt->clone();
        _array.push_back(mtn);
    }
}

/**
 * @brief Constructor for the MicrotoneArray class that takes a vector of float values.
 * @param harmonics The vector of float values.
 */
MicrotoneArray::MicrotoneArray(vector<float> harmonics) {
    for(auto f : harmonics) {
        jassert(f > 0.f);
        jassert(!std::isnan(f));
        jassert(!std::isinf(f));
        auto mf = make_shared<Microtone>(f);
        _array.push_back(mf);
    }
}

/**
 * @brief Constructor for the MicrotoneArray class that takes a vector of unsigned long values.
 * @param numeratorDenominatorPairs The vector of unsigned long values.
 */
MicrotoneArray::MicrotoneArray(vector<unsigned long> numeratorDenominatorPairs) {
    // must be a multiple of 2
    jassert(numeratorDenominatorPairs.size() > 0 && numeratorDenominatorPairs.size() % 2 == 0);
    
    auto first = numeratorDenominatorPairs.begin();
    auto last = numeratorDenominatorPairs.begin() + static_cast<long>(numeratorDenominatorPairs.size());
    for(auto it = first; it != last; ++it) {
        auto numerator = *it;
        ++it;
        auto denominator = *it;
        auto delta = make_shared<Microtone>(numerator, denominator, "", Microtone::Space::Linear, TuningConstants::defaultPeriod);
        addMicrotoneDelta(delta);
    }
}

/**
 * @brief Static method that creates a MicrotoneArray object from a vector of float values.
 * @param inputArray The vector of float values.
 * @return A MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::microtoneArrayFromArrayOfFloats(vector<float> inputArray) {
    jassert(inputArray.size() > 0);
    auto ma = MicrotoneArray();
    for(auto f : inputArray) {
        jassert(f > 0.f);
        jassert(!std::isnan(f));
        jassert(!std::isinf(f));
        auto mt = make_shared<Microtone>(f);
        ma.addMicrotone(mt);
    }
    
    return ma;
}

/**
 * @brief Static method that creates a MicrotoneArray object from a vector of int values.
 * @param numeratorDenominatorPairs The vector of int values.
 * @return A MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::microtoneArrayFromArrayOfNumDenPairs(vector<int> numeratorDenominatorPairs) {
    // must be a multiple of 2
    jassert(numeratorDenominatorPairs.size() > 0 && numeratorDenominatorPairs.size() % 2 == 0);
    
    auto first = numeratorDenominatorPairs.begin();
    auto last = numeratorDenominatorPairs.begin() + static_cast<long>(numeratorDenominatorPairs.size());
    auto ma = MicrotoneArray();
    for(auto it = first; it != last; ++it) {
        auto numerator = *it;
        jassert(numerator > 0);
        ++it;
        auto denominator = *it;
        jassert(denominator > 0);
        auto rational = make_shared<Microtone>(numerator, denominator);
        ma.addMicrotone(rational);
    }
    return ma;
}

#pragma mark - static

/**
 * @brief Static method that creates a MicrotoneArray object.
 * @return A MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::microtoneArray() {
    return MicrotoneArray();
}

/**
 * @brief Static method that creates a MicrotoneArray object with a harmonic limit.
 * @param limit The harmonic limit.
 * @param period The period.
 * @return A MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::microtoneArrayHarmonicLimit(int limit, float period) {
    jassert(limit > 0);
    MicrotoneArray retVal = MicrotoneArray();
    for(auto b = 1; b <= limit; b++) {
        for(auto a = 1; a <= limit; a++) {
            if(a > b) {
                retVal.addMicrotone(make_shared<Microtone>(a, b));
            }
        }
    }
    
    retVal = retVal.octaveReduce(period);
    retVal = retVal.sort();
    retVal = retVal.uniquify();
    retVal = retVal.removePowersOf2();
    
    return retVal;
}

/**
 * @brief Static method that creates a MicrotoneArray object from a vector of Microtone_p objects.
 * @param inputArray The vector of Microtone_p objects.
 * @return A MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::microtoneArrayFromArray(vector<Microtone_p> inputArray) {
    MicrotoneArray retVal = MicrotoneArray();
    for(auto tone : inputArray) {
        retVal.addMicrotone(tone);
    }
    
    return retVal;
}

#pragma mark - instance methods

/**
 * @brief Method that adds a Microtone_p object to the MicrotoneArray object.
 * @param microtone The Microtone_p object to be added.
 */
void MicrotoneArray::addMicrotone(Microtone_p microtone) {
    const ScopedLock sl(_lock);
    _array.push_back(microtone);
}

/**
 * @brief Method that inserts a Microtone_p object at a specific index in the MicrotoneArray object.
 * @param microtone The Microtone_p object to be inserted.
 * @param index The index at which the Microtone_p object is to be inserted.
 */
void MicrotoneArray::insertMicrotone(Microtone_p microtone, unsigned long index) {
    const ScopedLock sl(_lock);
    auto it = _array.begin();
    _array.insert(it + static_cast<long>(index), microtone);
}

/**
 * @brief Method that adds a Microtone_p object as a delta to the MicrotoneArray object.
 * @param delta The Microtone_p object to be added as a delta.
 */
void MicrotoneArray::addMicrotoneDelta(Microtone_p delta) {
    const ScopedLock sl(_lock);
    auto const f = delta->getFrequencyValue();
    jassert(f > 1.f);
    jassert(f < _period);
    
    // must have a 1/1 to begin
    if(_array.size() == 0) {
        addMicrotone(make_shared<Microtone>(1, 1)) ;
    }
    
    auto const lastTone = _array.back();
    auto newTone = lastTone->multiply(delta);
    auto const newFreq = newTone->getFrequencyValue();
    
    if(newFreq > _period) {
        // warning: adding a delta that results in greater than 2
        jassertfalse;
    } else if(fabsf(newFreq - _period) < 0.00001f) {
        // if last tone is close to octave don't add it.
        // can still add logging
        // this is useful for adding every tone as a delta but not failing on the expected octave as an error
    } else {
        _array.push_back(newTone);
    }
}

/**
 * @brief Method that checks if a Microtone_p object is contained in the MicrotoneArray object.
 * @param microtone The Microtone_p object to be checked.
 * @return A boolean value indicating whether the Microtone_p object is contained in the MicrotoneArray object.
 */
bool MicrotoneArray::containsMicrotone(Microtone_p microtone) {
    const ScopedLock sl(_lock);
    bool retVal = false;
    for(auto m : _array) {
        if(WilsonicMath::floatsAreEqual(m->getFrequencyValue(), microtone->getFrequencyValue())) {
            retVal = true;
            break;
        }
    }
    
    return retVal;
}

/**
 * @brief Method that returns the count of Microtone_p objects in the MicrotoneArray object.
 * @return The count of Microtone_p objects in the MicrotoneArray object.
 */
const unsigned long MicrotoneArray::count() {
    const ScopedLock sl(_lock);
    return _array.size();
}

/**
 * @brief Method that removes all Microtone_p objects from the MicrotoneArray object.
 */
void MicrotoneArray::removeAllMicrotones() {
    const ScopedLock sl(_lock);
    _array.clear();
}

/**
 * @brief Method that returns the Microtone_p object at a specific index in the MicrotoneArray object.
 * @param index The index at which the Microtone_p object is to be returned.
 * @return The Microtone_p object at the specified index.
 */
Microtone_p MicrotoneArray::microtoneAtIndex(unsigned long index) {
    const ScopedLock sl(_lock);
    jassert(index < _array.size());
    auto retVal = _array.at(index);
    
    return retVal;
}

/**
 * @brief Method that sets a Microtone_p object at a specific index in the MicrotoneArray object.
 * @param m The Microtone_p object to be set.
 * @param index The index at which the Microtone_p object is to be set.
 */
void MicrotoneArray::setMicrotone(Microtone_p m, unsigned long index) {
    const ScopedLock sl(_lock);
    jassert(index < _array.size());
    _array[index] = m;
}

/**
 * @brief Method that returns the first Microtone_p object in the MicrotoneArray object.
 * @return The first Microtone_p object in the MicrotoneArray object.
 */
Microtone_p MicrotoneArray::firstMicrotone() {
    const ScopedLock sl(_lock);
    jassert(_array.size() > 0);
    return _array.front();
}

/**
 * @brief Method that returns the last Microtone_p object in the MicrotoneArray object.
 * @return The last Microtone_p object in the MicrotoneArray object.
 */
Microtone_p MicrotoneArray::lastMicrotone() {
    const ScopedLock sl(_lock);
    jassert(_array.size() > 0);
    return _array.back();
}

/**
 * @brief Method that returns a subarray of the MicrotoneArray object with a specific range.
 * @param offset The offset of the range.
 * @param num_terms The number of terms in the range.
 * @return A MicrotoneArray object that is a subarray of the original MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::subarrayWithRange(unsigned long offset, unsigned long num_terms) {
    const ScopedLock sl(_lock);
    // empty array
    auto retVal = MicrotoneArray();
    if(_array.size() == 0) {
        
        return retVal;
    }
    
    // return as much of _array as you can
    auto const i0 = offset;
    auto i1 = offset + num_terms;
    for(auto i = i0; i < i1; i++) {
        if(i < _array.size()) {
            auto mt = _array[i]->clone(); // copy
            retVal.addMicrotone(mt);
        } else {
            break;
        }
    }
    
    return retVal;
}

/**
 * @brief Method that returns a period-reduced deep copy of MicrotoneArray object.
 * @param period The period.
 * @return A MicrotoneArray object with a reduced octave/period.
 */
MicrotoneArray MicrotoneArray::octaveReduce(float period) {
    const ScopedLock sl(_lock);
    // deep copy
    MicrotoneArray retVal {};
    for(auto m : _array) {
        Microtone_p deep_copy = m->clone();
        deep_copy->octaveReduce(period);
        retVal.addMicrotone(deep_copy);
    }
    
    return retVal;
}

/**
 * @brief Method that sorts the MicrotoneArray object.
 * @return A sorted MicrotoneArray object.
 */
MicrotoneArray MicrotoneArray::sort() {
    const ScopedLock sl(_lock);
    MicrotoneArray retVal {};
    vector<Microtone_p> mta(_array);
    
    // sorts tmp array...does not affect _array or the microtones in it
    std::sort(mta.begin(), mta.end(), [](Microtone_p a, Microtone_p b) {
        return a->getFrequencyValue() < b->getFrequencyValue();
    });
    
    // deep copy
    for(auto m : mta) {
        auto deep_copy = m->clone();
        retVal.addMicrotone(deep_copy);
    }
    
    return retVal;
}

/**
 * @brief Method that sorts the MicrotoneArray object by short description.
 * @return A MicrotoneArray object sorted by short description.
 */
MicrotoneArray MicrotoneArray::sortByShortDescription() {
    const ScopedLock sl(_lock);
    MicrotoneArray retVal {};
    vector<Microtone_p> mta(_array);
    
    // sorts tmp array...does not affect _array or the microtones in it
    std::sort(mta.begin(), mta.end(), [](Microtone_p a, Microtone_p b) {
        return a->getShortDescriptionText() < b->getShortDescriptionText();
    });
    
    // deep copy
    for(auto m : mta) {
        auto deep_copy = m->clone();
        retVal.addMicrotone(deep_copy);
    }
    
    return retVal;
}

/**
 * @brief Method that uniquifies the MicrotoneArray object.
 * @return A MicrotoneArray object with unique elements.
 */
MicrotoneArray MicrotoneArray::uniquify() {
    const ScopedLock sl(_lock);
    // use map/dictionary to uniquify
    auto unique = map<float, Microtone_p>();

    // degree names of merged duplicates are joined with "|" in array order
    // (Ableton's own files write "C♯|D♭"); equal names are not repeated.
    auto mergedNames = map<float, vector<string>>();
    for(auto const& m : _array) {
        auto const& name = m->getDegreeName();
        if(name.empty()) {
            continue;
        }
        auto& names = mergedNames[m->getFrequencyValue()];
        if(std::find(names.begin(), names.end(), name) == names.end()) {
            names.push_back(name);
        }
    }
    
    // iterate through array
    auto rit = _array.rbegin();
    for(; rit != _array.rend(); ++rit) {
        const float f = (*rit)->getFrequencyValue();
        unique.insert(pair<float, Microtone_p>(f, *rit));
    }
    
    // update array with unique microtones
    MicrotoneArray retVal {};
    for(pair<float, Microtone_p> element : unique) {
        auto m = element.second;
        auto deep_copy = m->clone();
        auto const names = mergedNames.find(element.first);
        if(names != mergedNames.end() && names->second.size() > 1) {
            string joined;
            for(auto const& n : names->second) {
                joined += (joined.empty() ? "" : "|") + n;
            }
            deep_copy->setDegreeName(joined);
        }
        retVal.addMicrotone(deep_copy);
    }
    
    return retVal;
}

/**
 * @brief Method that removes powers of 2 from the MicrotoneArray object.
 * @return A MicrotoneArray object with powers of 2 removed.
 */
MicrotoneArray MicrotoneArray::removePowersOf2() { // useful even for non-octave
    const ScopedLock sl(_lock);
    MicrotoneArray retVal {};
    
    // deep copy
    for(auto m : _array) {
        if(!m->frequencyValueIsPowerOf2()) {
            auto deep_copy = m->clone();
            retVal.addMicrotone(deep_copy);
        }
    }
    
    return retVal;
}

/// duplicates/removes items as neccessary to return a microtone array of size newNPO
tuple<MicrotoneArray, map<int, int>> MicrotoneArray::npoOverride(int newNPO) {
    const ScopedLock sl(_lock);
    jassert(newNPO >= Tuning::npoOverrideMin);
    jassert(newNPO <= Tuning::npoOverrideMax);
    auto const npo = _array.size();
    jassert(npo >= Tuning::npoOverrideMin);
    jassert(npo <= Tuning::npoOverrideMax);
    MicrotoneArray retVal {};
    map<int, int> retValMap {};
    auto const npo_fac = static_cast<float>(npo) / static_cast<float>(newNPO);
    for(auto i = 0; i < newNPO; i++) {
        auto const npo_f = static_cast<float>(i) * npo_fac;
        auto const npo_i = static_cast<size_t>(npo_f);
        auto const npo_int = static_cast<int>(npo_f);
        auto m = _array[npo_i];
        auto deep_copy = m->clone();
        retVal.addMicrotone(deep_copy);
        auto npoik = retValMap.find(npo_int);
        if(npoik == retValMap.end()) {
            retValMap[npo_int] = i;
        }
    }
    
    return make_tuple(retVal, retValMap);
}

#pragma mark - description

/**
 * @brief Method that returns a debug description of the MicrotoneArray object.
 * @return A string containing the debug description of the MicrotoneArray object.
 */
const string MicrotoneArray::getDebugDescription() {
    const ScopedLock sl(_lock);
    string retVal = "(";
    for(unsigned long i = 0; i < _array.size(); i++) {
        auto mt = microtoneAtIndex(i);
        retVal += mt->getDebugDescription();
        if(i < _array.size() - 1)
            retVal += ", ";
    }
    retVal += ")";
    
    return retVal;
}

/**
 * @brief Overloaded operator that outputs the MicrotoneArray object to an ostream object.
 * @param os The ostream object.
 * @param m The MicrotoneArray object.
 * @return The ostream object.
 */
ostream& operator << (ostream& os, MicrotoneArray& m) {
    for(unsigned long i = 0; i < m.count(); i++) {
        Microtone_p mt = m.microtoneAtIndex(i);
        os << mt;
        if(i < m.count() - 1) {
            os << ", ";
        }
    }
    
    return os;
}
