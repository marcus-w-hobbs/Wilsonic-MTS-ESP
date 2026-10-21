/*
 ==============================================================================

 Brun+Tuning.cpp
 Created: 27 Feb 2021 2:29:37pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

// Include necessary header files
#include "Brun.h"
#include "BrunMicrotone.h"
#include "MicrotoneArray.h"
#include "TuningImp.h"
#include "WilsonicAppSkin.h"
#include "WilsonicProcessorConstants.h"

// Define getters and setters
#pragma mark - getters setters

// Function to get a debug description of the Brun object
const string Brun::getDebugDescription() {
    string retVal = "";
    retVal += "(Brun: ";
    retVal += "G: " + to_string(_generator) + ", "; // Generator
    retVal += "L: " + to_string(_level) + ", "; // Level
    retVal += "P: " + to_string(getOctave()) + ", "; // Octave
    retVal += "M: " + to_string(_murchana) + " "; // Murchana
    retVal += TuningImp::getDebugDescription(); // Tuning implementation debug description
    retVal += ")";

    return retVal;
}

// Function to get a parameter description of the Brun object
const string Brun::getParameterDescription() {
    string retVal = "";
    retVal += "G: " + to_string(_generator) + ", "; // Generator
    retVal += "L: " + to_string(_level) + ", "; // Level
    retVal += "P: " + to_string(getOctave()) + ", "; // Octave
    retVal += "M: " + to_string(_murchana); // Murchana

    return retVal;
}

// Function to get the default Scala name
String Brun::defaultScalaName() {
    // 0.5833 ==> 5833
    auto g = to_string(_generator); // Generator
    WilsonicAppSkin::replaceAll(g, "0.", "");

    // period
    auto p = WilsonicAppSkin::floatDescription(getOctave(), 3); // Octave
    WilsonicAppSkin::replaceAll(p, ".", "_");

    // mos_g58333_npo12_p2_m0.scl
    auto n = "mos_g" + g + "_npo" + to_string(getProcessedArrayNPOCount()) + "_m" + to_string(_murchana) + ".scl"; // Scala name

    return String(n);
}

// Function to get Scala comments
String Brun::scalaComments() {
    String retVal = "! " + getDebugDescription() + "\n"; // Debug description
    retVal += "! " + TuningImp::scalaComments(); // Tuning implementation comments

    return retVal;
}

#pragma mark - Update

// MOS degree names: the 0-based scale degree in the processed (reduced, sorted)
// array, so the tonic is "0". Runs before NPO override, so repeated degrees
// keep their source name. Consumed by the Ableton .ascl export (AbletonAscl).
void Brun::_assignDegreeNames() {
    auto const count = _processedArray.count();
    for (unsigned long i = 0; i < count; i++) {
        _processedArray.microtoneAtIndex(i)->setDegreeName(to_string(i));
    }
}

// Function to reduce a pitch value to the range [0, 1)
float Brun::_octaveReduceP01(float p) {
    // Ensure the input is not NaN nor infinity
    jassert(!std::isnan(p));
    jassert(!std::isinf(p));

    // If the pitch is greater than 1, subtract 1 until it is less than 1
    while (p > 1.f)
        p -= 1.f;

    // If the pitch is less than 0, add 1 until it is greater than or equal to 0
    while (p < 0.f)
        p += 1.f;

    // Return the reduced pitch value
    return p;
}

// Function to update the Brun tuning system
void Brun::_brunUpdate() {
    // Lock
    const ScopedLock sl(_lock);

    // Brun Array.  i.e., 0/1,1/2,2/3,3/5,4/7,7/12,...
    _brunArray = make_shared<MicrotoneArray>(Brun::brunArray(_maxLevel, _generator));
    
    // brun scale at the current level, to clamp murchana
    auto microtoneArray = _microtoneArrayBrun(_level, _generator, _murchana); // clamps _murchana
    
    // npo is the count of microtones in the array
    auto const npo = static_cast<int>(microtoneArray.count());
    jassert(npo > 0);

    // microtoneArrayBrun calculates properly with _murchana via an internal working variable.  updated on range here
    _murchana = _murchana % microtoneArray.count();
    
    // now calculate brun scale at max level
    auto microtoneArrayAll = _microtoneArrayBrun(Brun::absoluteMaxLevel, _generator, _murchana); // _murchana mod is <= than at _level
    
    // create empty level arrays
    for (auto l = Brun::absoluteMinLevel; l <= Brun::absoluteMaxLevel; l++) {
        _microtoneArrayBrunAllLevels[l] = make_shared<MicrotoneArray>();
    }

    // populate the level arrays from the max level array
    for (unsigned long i = 0; i < microtoneArrayAll.count(); i++) {
        auto mt = microtoneArrayAll.microtoneAtIndex(i);
        auto mtb = static_pointer_cast<BrunMicrotone>(mt);
        jassert(mtb != nullptr);
        
        // populate the level arrays
        for (auto l = Brun::absoluteMinLevel; l <= Brun::absoluteMaxLevel; l++) {
            auto const level = mtb->getLevel();
            if (level <= l) {
                _microtoneArrayBrunAllLevels[l]->addMicrotone(mtb);
            }
        }
    }

    // Label Array
    _labelArray.clear();
    for (unsigned long index = 0; index < _brunArray->count(); index++) {
        auto const t = _brunArray->microtoneAtIndex(index);
        _labelArray.push_back(t->getShortDescriptionText());
    }

    // The microtoneArray is an array of BrunMicrotones. Calculate their gral mapping here.
    // Declare variables for the first, second, and third microtones
    Microtone_p mt_0, mt_1, mt_2;
    
    // Declare variables for the generator and octave vectors
    Point<float> generator_vector, octave_vector;
    
    // Set the levelGral to a valid level
    _levelGral = _validLevelGral(_levelGral);

    // Calculate the gral octave and generator vectors
    if (_levelGral == absoluteMinLevel) {
        // If the levelGral is the absolute minimum level, set the octave vector to (1, 0) and the generator vector to (0, 1)
        octave_vector = Point<float>(1, 0);
        generator_vector = Point<float>(0, 1);
    } else {
        // If the levelGral is not the absolute minimum level, calculate the octave and generator vectors
        // Get the microtones at the current level and the previous level
        mt_0 = _brunArray->microtoneAtIndex(_levelGral - 0);
        mt_1 = _brunArray->microtoneAtIndex(_levelGral - 1);
        
        // Calculate the numerator and denominator of the third microtone
        auto mt_2num = static_cast<unsigned long>(abs(static_cast<int>(mt_0->getNumerator()) - static_cast<int>(mt_1->getNumerator())));
        auto mt_2den = static_cast<unsigned long>(abs(static_cast<int>(mt_0->getDenominator()) - static_cast<int>(mt_1->getDenominator())));
        
        // Create the third microtone
        mt_2 = make_shared<Microtone>(mt_2num, mt_2den);

        // Account for the zig zag pattern of the scale tree
        if (mt_2->getFrequencyValue() < mt_1->getFrequencyValue()) {
            // If the frequency value of the third microtone is less than that of the second, set the octave and generator vectors accordingly
            octave_vector = Point<float>(static_cast<int>(mt_2->getDenominator()), static_cast<float>(mt_1->getDenominator()));
            generator_vector = Point<float>(static_cast<int>(mt_2->getNumerator()), static_cast<float>(mt_1->getNumerator()));
        } else {
            // If the frequency value of the third microtone is not less than that of the second, set the octave and generator vectors accordingly
            octave_vector = Point<float>(static_cast<float>(mt_1->getDenominator()), static_cast<float>(mt_2->getDenominator()));
            generator_vector = Point<float>(static_cast<int>(mt_1->getNumerator()), static_cast<float>(mt_2->getNumerator()));
        }
    }

    // Map the gral to the BrunMicrotones in the microtone array
    _mapGralToBrunMicrotones(microtoneArray, generator_vector, octave_vector);

    // The postProcess block is set in the constructor helper: _gralPostProcessBlockImp
    // setMicrotoneArray calls TuningImp::_update,
    // which calls the postProcess block,
    // and THEN the tuningUpdated callback
    setMicrotoneArray(microtoneArray);

    // Create the tuning description
    std::ostringstream stringStream;
    stringStream << "Generator = " << std::to_string(_generator) << " ";
    stringStream << "Notes Per Period = " << std::to_string(microtoneArray.count()) << " ";
    stringStream << "Period = " << std::to_string(getOctave()) << " ";
    stringStream << "Murchana = " << std::to_string(_murchana) << " ";
    setTuningDescription(stringStream.str());
}

#pragma mark - description

// Function to print the Brun object
ostream& operator << (ostream& os, Brun& m) {
    os << "n: " << m.getTuningName() << endl; // Tuning name
    os << "d: " << m.getTuningDescription() << endl; // Tuning description
    os << "g: " << m.getGenerator() << endl; // Generator
    os << "l: " << m.getLevel() << endl; // Level
    auto ma = m.getMicrotoneArray(); // Microtone array
    os << "m: " << ma << endl;
    auto pa = m.getProcessedArrayNPO(); // Processed array
    os << "p: " << pa << endl;

    return os;
}
