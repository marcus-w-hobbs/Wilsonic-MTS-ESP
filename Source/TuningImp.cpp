/*
 ==============================================================================

 TuningImp.cpp
 Created: 14 Feb 2021 3:39:57pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include <limits.h>
#include "Microtone.h"
#include "MicrotoneArray.h"
#include "TuningImp.h"
#include "WilsonicMath.h"

#pragma mark - Lifecycle 

TuningImp::TuningImp() {
    // default to 12ET
    auto mta = MicrotoneArray();
    for(auto i = 0; i < 12; i++) {
        Microtone_p mt = make_shared<Microtone>(exp2(i/12));
        mta.addMicrotone(mt);
    }

    //
    setMicrotoneArray(mta); // calls update
}

/**
 * @brief Copy constructor for the TuningImp class.
 * 
 * This constructor creates a new instance of the TuningImp class, copying all the properties
 * from the provided TuningImp instance.
 * 
 * @param t The TuningImp instance to copy from.
 */
TuningImp::TuningImp(const TuningImp& t)
:_mode(t._mode)
,_noteNumberMiddleC(t._noteNumberMiddleC)
,_noteNumberMiddleCMin(t._noteNumberMiddleCMin)
,_noteNumberMiddleCMax(t._noteNumberMiddleCMax)
,_frequencyMiddleC(t._frequencyMiddleC)
,_frequencyMiddleCMin(t._frequencyMiddleCMin)
,_frequencyMiddleCMax(t._frequencyMiddleCMax)
,_octaveMiddleC(t._octaveMiddleC)
,_octaveMiddleCMin(t._octaveMiddleCMin)
,_octaveMiddleCMax(t._octaveMiddleCMax)
,_canNPOOverride(t._canNPOOverride)
,_npoOverride(t._npoOverride)
,_npoOverrideMin(t._npoOverrideMin)
,_npoOverrideMax(t._npoOverrideMax)
,_npoOverrideEnable(t._npoOverrideEnable)
,_octave(t._octave)
,_octaveMin(t._octaveMin)
,_octaveMax(t._octaveMax)
,_octaveReduce(t._octaveReduce)
,_octaveRepeat(t._octaveRepeat)
,_sort(t._sort)
,_canSort(t._canSort)
,_uniquify(t._uniquify)
,_canUniquify(t._canUniquify)
,_tuningName(t._tuningName)
,_tuningDescription(t._tuningDescription)
,_tuningUserDescription(t._tuningUserDescription)
,_canFavorite(t._canFavorite)
,_canScala(t._canScala)
,_microtoneArray(t._microtoneArray)
,_processedArray(t._processedArray)
,_microtoneNN(t._microtoneNN)
,_postProcessBlock(t._postProcessBlock)
,_completionBlock(t._completionBlock)
,_tuningTable(t._tuningTable)
{
    // Update the tuning implementation
    _update();
}

#pragma mark - TuningTable

void TuningImp::setTuningTable(float frequency, unsigned long index) {
    _tuningTable.setTuningTable(frequency, index);
}

const float TuningImp::getTuningTableFrequency(unsigned long index) {
    return _tuningTable.getTuningTableFrequency(index);
}

#pragma mark - getters setters

int TuningImp::getMode() {
    return _mode;
}

void TuningImp::setMode(int newMode) {
    // -1 = nop
    if (newMode >= -1 && newMode < static_cast<int>(_processedArray.count())) {
        _mode = newMode;
        _update();
    } else {
        DBG ("TuningImp::setMode: out of range" + String(newMode));
    }
}

unsigned long TuningImp::getNoteNumberMiddleC() {
    return _noteNumberMiddleC;
}

void TuningImp::setNoteNumberMiddleC(unsigned long nn) {
    jassert(nn >= _noteNumberMiddleCMin && nn <= _noteNumberMiddleCMax);
    if (nn != _noteNumberMiddleC) {
        _noteNumberMiddleC = nn;
        _update();
    }
}

unsigned long TuningImp::getNoteNumberMiddleCMin() {
    return _noteNumberMiddleCMin;
}

unsigned long TuningImp::getNoteNumberMiddleCMax() {
    return _noteNumberMiddleCMax;
}

float TuningImp::getFrequencyMiddleC() {
    return _frequencyMiddleC;
}

void TuningImp::setFrequencyMiddleC(float f) {
    jassert(f >= _frequencyMiddleCMin && f <= _frequencyMiddleCMax);
    if(WilsonicMath::floatsAreNotEqual(f, _frequencyMiddleC)) {
        _frequencyMiddleC = f;
        _update();
    }
}

float TuningImp::getFrequencyMiddleCMin() {
    return _frequencyMiddleCMin;
}

float TuningImp::getFrequencyMiddleCMax() {
    return _frequencyMiddleCMax;
}

int TuningImp::getOctaveMiddleC() {
    return _octaveMiddleC;
}

void TuningImp::setOctaveMiddleC(int o) {
    jassert(o >= _octaveMiddleCMin && o <= _octaveMiddleCMax);
    if (o != _octaveMiddleC) {
        _octaveMiddleC = o;
        _update();
    }
}

int TuningImp::getOctaveMiddleCMin() {
    return _octaveMiddleCMin;
}

int TuningImp::getOctaveMiddleCMax() {
    return _octaveMiddleCMax;
}

// does tuning support npo override?
bool TuningImp::getCanNPOOverride() {
    return _canNPOOverride;
}

void TuningImp::setCanNPOOverride(bool shouldOverride) {
    _canNPOOverride = shouldOverride;
    _update();
}

// notes per octave "npo" override
int TuningImp::getNPOOverride() {
    return _npoOverride;
}

void TuningImp::setNPOOverride(int npoOverride) {
    // set this, even if the tuning can't npo override.
    // because _processedArrayNPO is the end of the chain
    auto const newOverride = jlimit(Tuning::npoOverrideMin, Tuning::npoOverrideMax, npoOverride);
    _npoOverride = newOverride;
    _update();
}

int TuningImp::getNPOOverrideMin() {
    return _npoOverride;
}

int TuningImp::getNPOOverrideMax() {
    return Tuning::npoOverrideMax;
}

bool TuningImp::getNPOOverrideEnable() {
    return _npoOverrideEnable;
}

void TuningImp::setNPOOverrideEnable(bool enable) {
    if(!_canNPOOverride) {
        _npoOverrideEnable = false;
    } else {
        _npoOverrideEnable = enable;
    }
    
    _update();
}

float TuningImp::getOctave() {
    return _octave;
}

void TuningImp::setOctave(float o) {
    jassert(o > 0.f);
    jassert(!std::isnan(o));
    jassert(!std::isinf(o));
    if(WilsonicMath::floatsAreNotEqual(_octave, o) && (o >= _octaveMin) && (o <= _octaveMax)) {
        _octave = o;
        _update();
    } else {
        //DBG("TuningImp::setOctave: NOP because o is out of range: " + String(o));
    }
}

float TuningImp::getOctaveMin() {
    return _octaveMin;
}

float TuningImp::getOctaveMax() {
    return _octaveMax;
}

bool TuningImp::getOctaveReduce() {
    return _octaveReduce;
}

void TuningImp::setOctaveReduce(bool o) {
    if (_octaveReduce != o) {
        _octaveReduce = o;
        _update();
    }
}

bool TuningImp::getOctaveRepeat() {
    return _octaveRepeat;
}

void TuningImp::setOctaveRepeat(bool o) {
    if ( _octaveRepeat != o) {
        _octaveRepeat = o;
        _update();
    }
}

bool TuningImp::getSort() {
    return _sort;
}

void TuningImp::setSort(bool s) {
    if (s != _sort) {
        _sort = s;
        _update();
    }
}

bool TuningImp::getCanSort() {
    return _canSort;
}

void TuningImp::setCanSort(bool s) {
    if (s != _canSort) {
        _canSort = s;
        _update();
    }
}

bool TuningImp::getUniquify() {
    return _uniquify;
}

void TuningImp::setUniquify(bool u) {
    if ( _uniquify != u ) {
        _uniquify = u;
        _update();
    }
}

bool TuningImp::getCanUniquify() {
    return _canUniquify;
}

void TuningImp::setCanUniquify(bool u) {
    if ( _canUniquify != u ) {
        _canUniquify = u;
        _update();
    }
}

const string TuningImp::getTuningName() {
    return _tuningName;
}

void TuningImp::setTuningName(string name) {
    _tuningName = name;
}

const string TuningImp::getTuningDescription() {
    return _tuningDescription;
}

void TuningImp::setTuningDescription(string description) {
    _tuningDescription = description;
}

const string TuningImp::getDebugDescription() {
    string retVal = "(\n";
    retVal += "n: " + getTuningName() + "\n";
    retVal += "m: " + _microtoneArray.getDebugDescription() + "\n";
    retVal += "p: " + _processedArray.getDebugDescription() + "\n";
    retVal += ")\n";

    return retVal;
}

const string TuningImp::getUserDescription() {
    return _tuningUserDescription;
}

void TuningImp::setUserDescription(string comment) {
    _tuningUserDescription = comment;
}

const string TuningImp::getParameterDescription() {
    return getDebugDescription();
}

bool TuningImp::getCanFavorite() {
    return _canFavorite;
}

#pragma mark - Scala

bool TuningImp::getCanScala() {
    return _canScala;
}

void TuningImp::setCanScala(bool can_scala) {
    _canScala = can_scala;
}

/**
 * @brief Converts the current tuning to a Scala file.
 * 
 * This function converts the current tuning to a Scala file, which is a common format for representing microtonal tunings.
 * The function first checks if the tuning can be represented as a Scala file. If not, it asserts false.
 * Then, it updates the tuning and creates a deep copy of the processed array of microtones.
 * It then sets up the layout for the KBM and SCL files, which are components of a Scala file.
 * The function also handles special cases, such as when the first degree of the scale is not 1/1.
 * Finally, it returns the Scala file.
 * 
 * @return A ScalaFile object representing the current tuning.
 */
ScalaFile TuningImp::tuningAsScala() {
    if (! _canScala) {
        // for now assert, but make this more graceful
        jassertfalse;
    }

    // update tuning
    _update();
    auto deep_copy = MicrotoneArray(_processedArray);
    auto const pac = deep_copy.count();
    auto scalaFile = ScalaFile();

    // layout kbm file: note reference frequency is scaled by normalizing factor f0
    auto kbm = scalaFile.kbm;
    kbm.reference_frequency = getFrequencyMiddleC();
    kbm.map_size = static_cast<int>(pac);
    kbm.first_note = 0;
    kbm.last_note = WilsonicProcessorConstants::numMidiNotes - 1;
    kbm.middle_note = static_cast<int>(getNoteNumberMiddleC());
    kbm.reference_note = static_cast<int>(getNoteNumberMiddleC());
    kbm.octave_degree = static_cast<int>(pac);
    for (int nn = 0; nn < static_cast<int>(pac); nn++) {
        kbm.add_mapping(nn);
    }

    // layout scl file
    auto scl = scalaFile.scl;
    scl.add_description(getTuningDescription());

    // the scl has a 1/1: normalize each degree by the first of ours
    auto const f0 = deep_copy.microtoneAtIndex(0)->getFrequencyValue();
    jassert(f0 > 0.0f);

    // special handling for 1/1
    if (f0 != 1.0f) {
        kbm.reference_frequency *= f0;
        scl.get_degree(0).set_desc ("! normalized by: " + to_string(f0));
    }

    // add degrees
    for (unsigned long i = 1; i < pac; i++) { // skip 1/1
        auto mt = deep_copy.microtoneAtIndex(i);
        auto const f_d = mt->getFrequencyValue();
        auto d = ScalaFileDegree(f_d/f0);
        d.set_desc ("! " + to_string(f_d) + "/" + to_string(f0));
        scl.add_degree(d);
    }

    // add octave/repeating interval
    auto r = ScalaFileDegree(_octave);
    r.set_desc ("! repeating interval: " + to_string(_octave));
    scl.add_degree(r);

    // set description
    scl.set_desc(scalaComments().toStdString());
    
    //
    return scalaFile;
}

String TuningImp::defaultScalaName() {
    return "default.scl";
}

String TuningImp::scalaComments() {
    String retVal = "!\n";
    auto const count = _processedArray.count();
    for (unsigned long i = 0; i < count; i++) {
        auto mt = _processedArray.microtoneAtIndex(i);
        auto mt_f = mt->getFrequencyValue();
        auto mt_desc = mt->getShortDescriptionText();
        retVal += "! " + String(i) + ": " + String(mt_f) + " # " + String(mt_desc);
    }
    retVal += "! Created with Wilsonic MTS-ESP by Marcus Hobbs\n";

    return retVal;
}

#pragma mark - drawing

// default is false because a tuning must implement a custom paint method
// paint() and _paintHelper() live in TuningImp+paint.cpp so that this
// file's tuning numerics compile without WilsonicProcessor

bool TuningImp::canPaintTuning() {
    return false;
}

#pragma mark - nnForDeviceSpace

// This function returns the note number for a given device space.
int TuningImp::nnForDeviceSpace(Point<int> xy) {
    auto retVal = -1;
    auto xfm_xy = xy.toFloat();

    // iterate over MIDI notes
    for(unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
        auto note_mt = microtoneAtNoteNumber(i);
        jassert(note_mt != nullptr);
        // get the touch point path for the microtone
        auto tp = note_mt->getTouchPointPath(); // stored in screen coords by paint method
        if (tp.contains(xfm_xy)) {
            retVal = static_cast<int>(note_mt->getMidiNoteNumber());
            break; // for overlapping rects this returns the first note
        }
    }

    return retVal;
}


#pragma mark - Update

/**
 * @brief This method updates the tuning implementation.
 * 
 * This method is one of the most important methods for the application. It is responsible for updating the tuning implementation.
 * It starts by creating a deep copy of the microtone array before processing. Then, it performs octave reduction if the flag is set.
 * After that, it sorts the array if the flag is set. It also removes duplicate microtones if the flag is set.
 * 
 * The method then calculates the frequency for each MIDI note number and sets it in the tuning table. It also sets the microtone at each note number.
 * 
 * If the count of the processed array is zero, it sets the frequency for each MIDI note number to the frequency of middle C and sets the microtone at each note number to middle C.
 * 	
 * Finally, it calls the post-process block and the completion block.
 */
void TuningImp::_update() {
    const ScopedLock sl(_lock);
    _processedArray = MicrotoneArray(_microtoneArray);
    if (_octaveReduce) {
        _processedArray = _processedArray.octaveReduce(_octave);
    }
    if (_canSort && _sort) {
        _processedArray = _processedArray.sort();
    }
    if (_canUniquify && _uniquify) {
        _processedArray = _processedArray.uniquify();
    }
    
    auto const count = (_canNPOOverride && _npoOverrideEnable) ? static_cast<unsigned long>(_npoOverride) : _processedArray.count();
    auto [processedArrayNPO, processedArrayNPOMap] = _processedArray.npoOverride(static_cast<int>(count));
    _processedArrayNPO = processedArrayNPO;
    _processedArrayNPOMap = processedArrayNPOMap;
    
    if(count > 0) {
        for(int i = 0; i < static_cast<int>(WilsonicProcessorConstants::numMidiNotes); i++) { // keep as int
            // Calculate the frequency for each MIDI note number
            auto const ff = static_cast<float>(i - static_cast<int>(_noteNumberMiddleC)) / static_cast<float>(count);
            auto finc = truncf(ff);
            if(ff < 0.f) {
                finc -= 1.f;
            }
            auto frac = fabsf(finc - ff);
            if(frac == 1.f) {
                frac = 0.f;
                finc += 1.f;
            }
            auto const index = static_cast<unsigned long>(roundf(frac * static_cast<float>(count)));
            auto tone = _processedArrayNPO.microtoneAtIndex(index)->clone();
            tone->setMidiNoteNumber(static_cast<unsigned long>(i));
            tone->setMidiRegister(static_cast<int>(finc));
            tone->setFilterNote(false);
            auto const lp2 = powf(_octave, finc);
            auto const octaveFactor = powf(_octave, _octaveMiddleC);
            auto const nf = tone->getFrequencyValue();
            auto const f = nf * lp2 * _frequencyMiddleC * octaveFactor;
            _tuningTable.setTuningTable(f, static_cast<unsigned long>(i)); // this is asserting on nyquist
            setMicrotoneAtNoteNumber(tone, static_cast<unsigned long>(i));
        }
        _analyzeProportionalTriads();
    } else { // count == 0 ==> UNITY
        // If the count of the processed array is zero, set the frequency for each MIDI note number to the frequency of middle C
        auto middleC = make_shared<Microtone>(1,1);
        middleC->setMidiNoteNumber(_noteNumberMiddleC);
        middleC->setMidiRegister(0);
        middleC->setFilterNote(false);
        for (unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
            auto const octaveFactor = powf(_octave, _octaveMiddleC);
            auto const f = _frequencyMiddleC * octaveFactor;
            _tuningTable.setTuningTable(f, i);
            setMicrotoneAtNoteNumber(middleC->clone(), i);
        }
        // No scale analysis for this case
    }

    // Call the post-process block
    callPostProcessBlock();

    // Call the completion block
    callOnTuningUpdate();
}

// block will be called after microtones are processed, but before onTuningUpdate
void TuningImp::setPostProcessPreTuningUpdate(function<void()> postProcessBlock) {
    _postProcessBlock = postProcessBlock;
}

void TuningImp::callPostProcessBlock() {
    if (_postProcessBlock != nullptr) {
        _postProcessBlock();
    }
}

void TuningImp::setOnTuningUpdate(function<void()> completionBlock) {
    _completionBlock = completionBlock;
    _update(); // which calls the completion block
}

void TuningImp::callOnTuningUpdate() {
    if (_completionBlock != nullptr) {
        _completionBlock();
    }
}

void TuningImp::setMicrotoneArrayFromHarmonics(vector<float> harmonics) {
    const ScopedLock sl(_lock);
    _microtoneArray.removeAllMicrotones();
    for (auto f : harmonics) {
        if (f > 0.f && !std::isnan(f) && !std::isinf(f)) {
            _microtoneArray.addMicrotone(make_shared<Microtone>(f));
        }
    }

    _update();
}

void TuningImp::setMicrotoneArray(MicrotoneArray ma) {
    const ScopedLock sl(_lock);
    _microtoneArray = MicrotoneArray(ma);
    _update();
}

MicrotoneArray TuningImp::getMicrotoneArray() {
    const ScopedLock sl(_lock);
    return MicrotoneArray(_microtoneArray); // return copy
}

MicrotoneArray TuningImp::getProcessedArray() {
    const ScopedLock sl(_lock);
    return MicrotoneArray(_processedArray); // return copy
}

MicrotoneArray TuningImp::getProcessedArrayNPO() {
    const ScopedLock sl(_lock);
    return MicrotoneArray(_processedArrayNPO); // return copy
}

unsigned long TuningImp::getMicrotoneArrayCount() {
    const ScopedLock sl(_lock);
    return _microtoneArray.count();
}

unsigned long TuningImp::getProcessedArrayCount() {
    const ScopedLock sl(_lock);
    return _processedArray.count();
}

unsigned long TuningImp::getProcessedArrayNPOCount() {
    const ScopedLock sl(_lock);
    return _processedArrayNPO.count();
}

const vector<PythagoreanMeans> TuningImp::getProportionalTriads() { // "major", sum tones
    const ScopedLock sl(_lock);
    return _proportionalTriads;
}

const vector<PythagoreanMeans> TuningImp::getGeometricTriads() {
    const ScopedLock sl(_lock);
    return _geometricTriads;
}

const vector<PythagoreanMeans> TuningImp::getSubcontraryTriads() { // "minor"
    const ScopedLock sl(_lock);
    return _subcontraryTriads;
}

const vector<PythagoreanMeans> TuningImp::getAllTriads() {
    const ScopedLock sl(_lock);
    return _allTriads;
}

void TuningImp::setMicrotoneAtNoteNumber(Microtone_p microtone, unsigned long nn) {
    jassert(nn >= 0 && nn < WilsonicProcessorConstants::numMidiNotes);
    const ScopedLock sl(_lock);
    _microtoneNN[nn] = microtone;
}

Microtone_p TuningImp::microtoneAtNoteNumber(unsigned long nn) {
    jassert(nn >= 0 && nn < WilsonicProcessorConstants::numMidiNotes);
    const ScopedLock sl(_lock);
    return _microtoneNN[nn];
}

const float TuningImp::getSampleRate() {
    return _tuningTable.getSampleRate();
}

void TuningImp::setSampleRate(float sampleRate) {
    const ScopedLock sl(_lock);
    // only doing this here because we want to update tuningTable if samplerate changes
    if(WilsonicMath::floatsAreNotEqual(sampleRate, _tuningTable.getSampleRate())) {
        _tuningTable.setSampleRate(sampleRate);
        _update();
    }
}

#pragma mark - analyzeIntervals

// only works for scales with rational microtones
void TuningImp::_analyzeIntervals() { 
    /*
     [self update];

     NSMutableArray<MicrotoneArray*>* allAnalysis = [@[] mutableCopy];
     const NSUInteger count = _processedArray.count;
     for(NSUInteger delta = 1; delta < count; delta++)
     {
     //ALog(@"-------delta: %@ -------",@(delta));
     MicrotoneArray* analysis = [MicrotoneArray microtoneArray];
     for(NSUInteger index = 0; index < count; index++)
     {
     // Left microtone
     NSUInteger l = index;
     Microtone *lm = [_processedArray microtoneAtIndex:l];
     WilsonicAssert(lm.frequencyValue != 0, @"frequency must be non-zero");

     // right microtone
     NSUInteger r = (index+delta)%count;
     Microtone* rm = [_processedArray microtoneAtIndex:r];
     WilsonicAssert(rm.frequencyValue != 0, @"frequency must be non-zero");

     // if right is less than left: double.
     while(rm.frequencyValue < lm.frequencyValue) {
     if(rm.isRational) {
     rm = [Microtone microtoneWithNumerator:2*rm.numerator denominator:rm.denominator shortDescriptionText:nil space:MicrotoneSpaceLinear];
     } else {
     rm = [Microtone microtoneWithNumber:_octave*rm.frequencyValue shortDescriptionText:nil space:MicrotoneSpaceLinear];
     }
     }

     //
     Microtone* interval = [rm divide:lm];
     //ALog(@"index: %@, r: %@, l: %@, i: %@, f: %@",@(index),rm,lm,interval,@([interval frequencyValue]));
     //ALog(@"i:%@, i:%@, f: %@",@(index),interval,@([interval frequencyValue]));
     if(interval)
     {
     [analysis addMicroTone:interval];
     //ALog(@"i:%@, i:%@, f:%@",@(index),interval.shortDescriptionText,@([interval frequencyValue]));
     }
     else
     {
     //ALog(@"i:%@, i:%@, f:%@",@(index),interval.shortDescriptionText,@([interval frequencyValue]));
     interval = [rm divide:lm]; // just here to step in if result is nil
     }

     //ALog(@"interval: %@",interval);
     }
     analysis = [analysis uniquify];
     analysis = [analysis sort];
     //ALog(@"analysis: %@",analysis);
     [allAnalysis addObject:analysis];
     }
     //ALog(@"all analysis: %@",allAnalysis);
     //ALog(@"---------Final delta analysis--------");
     NSUInteger acount = 1;
     for(MicrotoneArray* a in allAnalysis) {
     ALog(@"--------delta: %@------",@(acount));
     const NSUInteger count = [a count];
     for(NSUInteger index = 0; index<count; index++)
     {
     Microtone* m = [a microtoneAtIndex:index];
     ALog(@"%@ = %@",m.shortDescriptionText,@(m.frequencyValue));
     }
     acount++;
     }

     */
}

#pragma mark - analyzeProportionalTriads

// works for any microtones
// assumes sorted
// assumes degree 0 = normalized frequency of 1

/// report proportional major triads and subcontrary minor triads
/// proportional major triads = (a+b)/2
/// subcontrary minor triads = (2ab)/(a+b)
/// fibonacci triplets a, b, a+b...this is merely octave reducing the term (a+b) -> (a+b)/2

/**
 * @brief Analyzes the proportional triads of the tuning.
 * 
 * This function analyzes the proportional triads of the tuning. It calculates the major and minor triads for each note in the tuning and stores them in the respective member variables.
 * The function also checks for duplicate triads and skips them. The function uses a tolerance value to determine if a note is part of a triad.
 *
 * Note that this method uses _processedArray, NOT _processedArrayNPO
 *
 * @note This helper function is called during the update process of the tuning.
 */
void TuningImp::_analyzeProportionalTriads() {
    // Enable logging
    //constexpr bool logging_enabled = false;

    // Definitions for de-duping triads
    typedef set<unsigned long> SUL;
    typedef map<SUL, unsigned long> TM;
    TM pmt, gmt, smt;

    // Lock to prevent other threads from accessing the same data simultaneously
    const ScopedLock sl(_lock);

    // Get the count of the processed array (NOT the _processedArrayNPO!)
    auto const npo = _processedArray.count();
    vector<PythagoreanMeans> proportionalTriads;
    vector<PythagoreanMeans> subcontraryTriads;
    vector<PythagoreanMeans> allTriads;

    // Trivial NOP
    if(npo < 3) {
        //DBG ("Can NOT analyze proportional triads because # terms is less than 3");
        return;
    }

    // TODO: make this a continuous fn so that we ease in/out of the ui
    //    auto const tolerance = 0.0001;
    //    auto const tolerance = 0.001;
    auto const tolerance = 0.0005;

    // i.e., Triad (i, k, j)
    for(unsigned long i = 0; i < npo; i++) { // root
        auto const im = _processedArray.microtoneAtIndex(i);
        auto const imf = im->getFrequencyValue();
        for(unsigned long j = i + 2; j < npo + 2; j++) { // fifth
            auto const ji = j % npo;
            auto const jfac = (ji < j) ? _octave : 1;
            auto const jm = _processedArray.microtoneAtIndex(ji);
            auto const jmf = jfac * jm->getFrequencyValue();
            auto const major = (imf + jmf) / 2;
            auto const minor = 2 * (imf * jmf) / (imf + jmf);
            constexpr float major_2nd = 9.f/8.f;
            constexpr float fourth = 4.f/3.f;
            auto const majorInLimits = (major / imf > major_2nd && major / imf < fourth);
            auto const minorInLimits = (minor / imf > major_2nd && minor / imf < fourth);
            for(unsigned long k = i + 1; k < j; k++) { // third
                auto const ki = k % npo;
                auto const kfac = (ki < k) ? _octave : 1;
                auto const km = _processedArray.microtoneAtIndex(ki);
                auto const kmf = kfac * km->getFrequencyValue();

                // major
                if (majorInLimits && fabsf(major - kmf) < tolerance) {
                    // dedup dedup
                    SUL mt = {i, ki, ji};
                    if (pmt.find(mt) == pmt.end()) {
                        pmt[mt] = 1UL; // add to dedup list
                        auto majorTriad = PythagoreanMeans(i, k, j, PythagoreanMeans::Type::Proportional);
                        proportionalTriads.push_back(majorTriad);
                        allTriads.push_back(majorTriad);
                    }
                }

                // minor
                if (minorInLimits && fabsf(minor - kmf) < tolerance) {
                    // dedup dedup
                    SUL mt = {i, ki, ji};
                    if (smt.find(mt) == smt.end()) {
                        smt[mt] = 1UL; // add to dedup list
                        auto minorTriad = PythagoreanMeans(i, k, j, PythagoreanMeans::Type::Subcontrary);
                        subcontraryTriads.push_back(minorTriad);
                        allTriads.push_back(minorTriad);
                    }
                }
            }
        }
    }
    
    // filter/transform by npo override
    _proportionalTriads.clear();
    _geometricTriads.clear();
    _subcontraryTriads.clear();
    _allTriads.clear();

    auto isTriadInNPOOverride = [&](auto& triad) -> bool {
        auto isDegreeInMap = [&](auto const degree) -> bool {
            auto it = _processedArrayNPOMap.find(static_cast<int>(degree));
            return it != _processedArrayNPOMap.end();
        };
        
        return isDegreeInMap(triad.getRoot()) &&
               isDegreeInMap(triad.getThird()) &&
               isDegreeInMap(triad.getFifth());
    };
    
    auto xfmTriad = [&](PythagoreanMeans& triad) -> PythagoreanMeans {
        auto const root = _processedArrayNPOMap[static_cast<int>(triad.getRoot())];
        auto const third = _processedArrayNPOMap[static_cast<int>(triad.getThird())];
        auto const fifth = _processedArrayNPOMap[static_cast<int>(triad.getFifth())];
        auto retTriad = PythagoreanMeans(static_cast<unsigned long>(root), static_cast<unsigned long>(third), static_cast<unsigned long>(fifth), triad.getType());
        
        return retTriad;
    };
    
    for(auto& triad : proportionalTriads) {
        if(isTriadInNPOOverride(triad)) {
            auto convertedTriad = xfmTriad(triad);
            _proportionalTriads.push_back(convertedTriad);
            _allTriads.push_back(convertedTriad);
        }
    }
    
    for(auto& triad : subcontraryTriads) {
        if(isTriadInNPOOverride(triad)) {
            auto convertedTriad = xfmTriad(triad);
            _subcontraryTriads.push_back(convertedTriad);
            _allTriads.push_back(convertedTriad);
        }
    }
}

#pragma mark - description

ostream& operator << (ostream& os, TuningImp& m) {
    os << "n: " << m.getTuningName() << "\n";
    os << "d: " << m.getTuningDescription() << "\n";
    os << "c: " << m.getUserDescription() << "\n";
    os << "m: " << m._microtoneArray << "\n";
    os << "p: " << m._processedArray << "\n";

    return os;
}

#pragma mark - _cartesian2HexTransform

// This function transforms unit cartesian coordinates into unit hex coordinates.
// It includes scaling by the size of the hex, and translating.
// It does not include rotation or shearing, which is in _gralPaintTransform()
AffineTransform TuningImp::_cartesian2HexTransform(Point<float> hp) {
    float const hexMargin  = _getHexMargin();
    float const hexWidth   = _getHexWidth();
    float const hexHeight  = _getHexHeight();

    // equivalent to "odd-q vertical layout shoves odd columns down"
    // https://www.redblobgames.com/grids/hexagons/#coordinates-offset
    // calculate the x and y coordinates for the transformation
    float const x = hexMargin + (hp.getX() * 3.f * hexWidth) / 4.f;
    float const y = hexMargin + (hp.getY() * hexHeight) + (fmodf(fabsf(hp.getX()), 2.f) * hexHeight / 2.f);
    auto transform = AffineTransform::translation(x, y).translated(_gralHexOrigin); // create a translation transformation

    return transform;
}

// This section of the code is dedicated to the transformation from Gral to hexagonal coordinates
#pragma mark - _transformGral2Hex

// This function transforms a Gral point to a hexagonal "odd-q vertical layout"
Point<float> TuningImp::transformGral2Hex(Point<float> gralPoint) {
    float y = 0.5f * gralPoint.getX() - 0.5f * gralPoint.getY(); // y coordinate for the transformation
    if (y < 0.f) y -= 0.5f; // compensate for truncf on negative numbers

    return Point<float>(gralPoint.getX() + gralPoint.getY(), truncf(y));
}

#pragma mark - _octaveReduceGralPoint

// This function reduces a Gral point to within an octave.
Point<float> TuningImp::_octaveReduceGralPoint(Point<float> inPoint, Point<float> octavePoint, bool degreeIsPositive) {
    // x + y = column of the generator
    auto const x = inPoint.getX();
    auto const y = inPoint.getY();

    // ox + oy = column of the octave
    auto const ox = octavePoint.getX();
    auto const oy = octavePoint.getY();

    // ensure the coordinates are not infinity or NaN
    jassert(!std::isinf(x) && !std::isinf(y) && !std::isinf(ox) && !std::isinf(oy));
    jassert(!std::isnan(x) && !std::isnan(y) && !std::isnan(ox) && !std::isnan(oy));
    // 1/1 is the only layout where x == y
    jassert(WilsonicMath::floatsAreNotEqual(ox, oy) || (WilsonicMath::floatsAreEqual(ox, 1.f) && WilsonicMath::floatsAreEqual(oy, 1.f)));

    auto retVal = inPoint;
    unsigned long safety_counter = 0;
    unsigned long const safety_limit = 200; // way too big

    // if note exceeds the octave, subtract the octave
    while(((retVal.x + retVal.y) > (ox + oy + (degreeIsPositive ? -1 : 0)))) {
        retVal -= octavePoint;
        if (safety_counter++ > safety_limit) {
            jassertfalse;
        }
    }

    // note is less than the root, add the octave
    safety_counter = 0;
    // while the sum of the x and y coordinates of the return value is less than 0 or 1, depending on the degree
    while (((retVal.x + retVal.y) < (degreeIsPositive ? 0 : 1))) {
        retVal += octavePoint;
        if (safety_counter++ > safety_limit) {
            jassertfalse;
        }
    }

    // if the sum of the x and y coordinates of the return value is greater than the sum of the x and y coordinates of the octave, or less than 0
    if (((retVal.x + retVal.y) > (ox + oy)) || ((retVal.x + retVal.y) < 0)) {
        jassertfalse; // if we're here it means that our octave reduction didn't work
    }

    // return the reduced point
    return retVal;
}

#pragma mark - _postProcessBlockImp

// Function to post-process the block
void TuningImp::_gralPostProcessBlockImp() {
    // Clear the debug gral point map
    _debugGralPointMap.clear();

    // Iterate over the sorted scale, calculate gral and hex points
    for (unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
        Microtone* note_mt = dynamic_cast<Microtone*>(microtoneAtNoteNumber(i).get());
        jassert(note_mt != nullptr);
        // for now, calculate every gral point, even if the microtone is filtered.  let paint decide whether to draw filtered notes or not
        auto gral_erv_point = note_mt->getGralErvPoint();
        auto gral_erv_octave_vector = note_mt->getGralErvOctaveVector();
        auto midi_register = static_cast<float>(note_mt->getMidiRegister());
        auto gral_erv_point_final = gral_erv_point + (gral_erv_octave_vector * midi_register);
        note_mt->setGralErvPointFinal(gral_erv_point_final);
        auto gral_hex_point_final = transformGral2Hex(gral_erv_point_final);
        note_mt->setGralHexPointFinal(gral_hex_point_final);
        // note that touchPoint is set in the paint method, which has the graphics context
#if 0
        // debug: report duplicates via an unordered map
        auto i_nn_string = to_string(i);
        if (_debugGralPointMap.count(gral_hex_point_final) > 0) {
            auto nn_string = _debugGralPointMap[gral_hex_point_final];
            cout << "WARNING: DUPLICATE: i:" << i_nn_string << ", duplicate nn:" << nn_string << ", gral_note:" << gral_erv_point_final.toString() << ", hex_point:" << gral_hex_point_final.toString() << endl;
            jassertfalse;
        } else {
            _debugGralPointMap[gral_hex_point_final] = i_nn_string;
        }
#endif
    }
}

#pragma mark - _gralPaintTransform

// AffineTransform of the Gral display.
AffineTransform TuningImp::_gralPaintTransform() {
    auto const p0 = microtoneAtNoteNumber(0); // any note will do, just need the hex octave vector
    jassert(p0 != nullptr);
    auto octave_vec = p0->getHexOctaveVector();
    auto octave_vec_transform = _cartesian2HexTransform(octave_vec);
    auto xfmd_octave_vec = octave_vec.transformedBy(octave_vec_transform);
    auto origin = Point<float>(0.f, 0.f);
    auto origin_transform = _cartesian2HexTransform(origin);
    auto xfmd_origin = origin.transformedBy(origin_transform);
    // calculate the angle between the origin and the transformed octave vector
    // 12 o'clock = 0, 3 o'clock = Pi/2, 6 o'clock = Pi, 9 o'clock = -Pi/2
    auto const angle = xfmd_origin.getAngleToPoint(xfmd_octave_vec);
    constexpr float pi_2 = 0.5f * 3.14159265358979323846f;
    // calculate the rotation adjustment based on the level of the Gral and the angle
    // the absoluteMinLevel/1/1 mapping is vertical
    auto const rotation_adjustment = pi_2 - angle;
    // shear and rotate entire plane
    auto shear = AffineTransform::shear(_gralHexShearX, 0.f);
    auto plane_rotation = AffineTransform::rotation(rotation_adjustment + _gralHexRotationRadians, _gralHexOrigin.getX(), _gralHexOrigin.getY());
    auto final_transform = shear.followedBy(plane_rotation);

    return final_transform;
}
