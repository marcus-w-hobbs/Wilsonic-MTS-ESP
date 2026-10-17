/*
 ==============================================================================
 
 ScalaTuningImp.cpp
 Created: 17 Sep 2022 4:16:35pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "ScalaTuningImp.h"
#include "WilsonicProcessor.h"
#include "WilsonicProcessorConstants.h"

// static factory

shared_ptr<ScalaTuningImp> ScalaTuningImp::createScalaTuningFromSclKbm(String full_path_to_scl, String full_path_to_kbm) {
    // validate path
    auto scl = File(full_path_to_scl);
    if(! scl.existsAsFile()) {
        DBG("ScalaTuningImp::createScalaTuning: Scala file does not exist: " + full_path_to_scl);
        
        return nullptr;
    }
    
    auto kbm = File(full_path_to_kbm);
    if(! kbm.existsAsFile()) {
        DBG("ScalaTuningImp::createScalaTuning: KBM file does not exist: " + full_path_to_kbm);
        // TODO: actually handle kbm
    }
    
    // parse
    ifstream ifs;
    ifs.open(full_path_to_scl.toRawUTF8()); // read file as a string
    auto scl_file = ScalaFileScl(ifs);
    ifs.close();
    size_t const scale_length = scl_file.get_scale_length();
    
    // we can only handle WilsonicProcessorConstants::numMidiNotes notes
    if(scale_length > WilsonicProcessorConstants::numMidiNotes) {
        DBG("ScalaTuningImp::createScalaTuning: Invalid Scala file: " + full_path_to_scl);
        DBG("ScalaTuningImp::createScalaTuning: Must have <= 128 notes per octave: " + String(scale_length));
        
        return nullptr;
    }
    
    // validate repeating interval
    auto const repeating_interval =(float)scl_file.get_period();
    if(repeating_interval <= 0) {
        DBG("ScalaTuningImp::createScalaTuning: Invalid repeating interval(" + String(repeating_interval) + ") in Scala file: " + full_path_to_scl);
        
        return nullptr;
    }
    
    // we are all validated, now create return value
    auto st = make_shared<ScalaTuningImp>();
    st->_scalaFile.scl = scl_file;
    // st->scalaFile.kbm = kbm_file; // TODO: implement kbm
    st->setScalaContent(scl_file.get_scala_content());
    st->setTuningDescription(scl_file.get_description());
    
    // configure return value
    st->setScalaFilename(scl.getFileName().toStdString());
    if(scale_length == 1) { // only one degree: 1.0{
        auto const repeatingInterval = 2.f; // default to 2...a period of 1 is problematic
        st->setRepeatingInterval(repeatingInterval);
        Microtone_p mt = make_shared<Microtone>(1, 1, "1", Microtone::Space::Linear, repeatingInterval);
        auto ma = MicrotoneArray();
        ma.addMicrotone(mt);
        st->setMicrotoneArray(ma);
    } else {
        st->setRepeatingInterval(repeating_interval);
        auto ma = MicrotoneArray();
        for(size_t i = 0; i < scale_length - 1; i++) {
            auto const d = scl_file.get_ratio(i);
            auto desc = scl_file.get_desc(i);
            Microtone_p d_mt = make_shared<Microtone>((float)d, desc, Microtone::Space::Linear, repeating_interval);
            ma.addMicrotone(d_mt);
        }
        
        // deep copy; calls _update
        st->setMicrotoneArray(ma);
    }
    
    //
    return st;
}

shared_ptr<ScalaTuningImp> ScalaTuningImp::createScalaTuningFromSclString(String scl_string) {
    auto scl_file = ScalaFileScl(scl_string);
    size_t const scale_length = scl_file.get_scale_length();
    
    // we can only handle WilsonicProcessorConstants::numMidiNotes notes
    if(scale_length > WilsonicProcessorConstants::numMidiNotes) {
        DBG("ScalaTuningImp::createScalaTuning: Invalid Scala file: \n" + scl_string);
        DBG("ScalaTuningImp::createScalaTuning: Must have <= 128 notes per octave: " + String(scale_length));
        
        return nullptr;
    }
    
    // validate repeating interval
    auto const repeating_interval =(float)scl_file.get_period();
    if(repeating_interval <= 0) {
        DBG("ScalaTuningImp::createScalaTuning: Invalid repeating interval(" + String(repeating_interval) + ") in Scala file: \n" + scl_string);
        
        return nullptr;
    }
    
    // we are all validated, now create return value
    auto st = make_shared<ScalaTuningImp>();
    st->_scalaFile.scl = scl_file;
    st->setScalaContent(scl_file.get_scala_content());
    st->setTuningDescription(scl_file.get_description());
    
    // configure return value
    st->setScalaFilename(scl_file.get_filename());
    if(scale_length == 1) { // only one degree: 1.0 {
        auto const repeatingInterval = 2.f; // default to 2...a period of 1 is problematic
        st->setRepeatingInterval(repeatingInterval);
        Microtone_p mt = make_shared<Microtone>(1, 1, "1", Microtone::Space::Linear, repeatingInterval);
        auto ma = MicrotoneArray();
        ma.addMicrotone(mt);
        st->setMicrotoneArray(ma);
    } else {
        st->setRepeatingInterval(repeating_interval);
        auto ma = MicrotoneArray();
        for(size_t i = 0; i < scale_length - 1; i++) {
            auto const d = scl_file.get_ratio(i);
            auto desc = scl_file.get_desc(i);
            Microtone_p d_mt = make_shared<Microtone>((float)d, desc, Microtone::Space::Linear, repeating_interval);
            ma.addMicrotone(d_mt);
        }
        
        // deep copy; calls _update
        st->setMicrotoneArray(ma);
    }
    
    //
    return st;
}

// lifecycle

ScalaTuningImp::ScalaTuningImp() {
    auto mta = MicrotoneArray(); // default to 12ET
    for(auto i = 0; i < 12; i++) {
        Microtone_p mt = make_shared<Microtone>(exp2(i/12));
        mta.addMicrotone(mt);
    }
    setMicrotoneArray(mta); // calls update
}


ScalaTuningImp::ScalaTuningImp(const ScalaTuningImp& t)
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
,_npoOverride(t._npoOverride)
,_npoOverrideMin(t._npoOverrideMin)
,_npoOverrideMax(t._npoOverrideMax)
,_npoOverrideEnable(t._npoOverrideEnable)
,_octave(t._octave)
,_octaveMin(t._octaveMin)
,_octaveMax(t._octaveMax)
,_repeatingInterval(t._repeatingInterval)
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
,_completionBlock(t._completionBlock)
,_tuningTable(t._tuningTable)
{
    _update();
}


#pragma mark - TuningTable

void ScalaTuningImp::setTuningTable(float frequency, unsigned long index) {
    _tuningTable.setTuningTable(frequency, index);
}

const float ScalaTuningImp::getTuningTableFrequency(unsigned long index) {
    return _tuningTable.getTuningTableFrequency(index);
}

#pragma mark - getters setters

int ScalaTuningImp::getMode() {
    return _mode;
}

void ScalaTuningImp::setMode(int newMode) {
    if(newMode >= -1 && newMode <(int)_processedArray.count()) {// -1 = nop
        _mode = newMode;
        _update();
    } else {
        DBG("ScalaTuningImp::setMode:" + String(newMode));
    }
}

unsigned long ScalaTuningImp::getNoteNumberMiddleC() {
    return _noteNumberMiddleC;
}

void ScalaTuningImp::setNoteNumberMiddleC(unsigned long nn) {
    if(nn != _noteNumberMiddleC && nn >= _noteNumberMiddleCMin && nn <= _noteNumberMiddleCMax) {
        _noteNumberMiddleC = nn;
        _update();
    } else {
        // log this?
    }
}

unsigned long ScalaTuningImp::getNoteNumberMiddleCMin() {
    return _noteNumberMiddleCMin;
}

unsigned long ScalaTuningImp::getNoteNumberMiddleCMax() {
    return _noteNumberMiddleCMax;
}

float ScalaTuningImp::getFrequencyMiddleC() {
    return _frequencyMiddleC;
}

void ScalaTuningImp::setFrequencyMiddleC(float f) {
    jassert(f > 0.f);
    jassert(! std::isnan(f));
    jassert(! std::isinf(f));
    
    if(f < _frequencyMiddleCMin || f > _frequencyMiddleCMax) {
        DBG("ScalaTuningImp::setFrequencyMiddleC: NOP because f is out of range: " + String(f));
    } else if(WilsonicMath::floatsAreNotEqual(f, _frequencyMiddleC)) {
        _frequencyMiddleC = f;
        _update();
    }
}

float ScalaTuningImp::getFrequencyMiddleCMin() {
    return _frequencyMiddleCMin;
}

float ScalaTuningImp::getFrequencyMiddleCMax() {
    return _frequencyMiddleCMax;
}

int ScalaTuningImp::getOctaveMiddleC() {
    return _octaveMiddleC;
}

void ScalaTuningImp::setOctaveMiddleC(int o) {
    if(o != _octaveMiddleC && o >= _octaveMiddleCMin && o <= _octaveMiddleCMax) {
        _octaveMiddleC = o;
        _update();
    } else {
        // log this?
    }
}

int ScalaTuningImp::getOctaveMiddleCMin() {
    return _octaveMiddleCMin;
}

int ScalaTuningImp::getOctaveMiddleCMax() {
    return _octaveMiddleCMax;
}

// does tuning support npo override?
bool ScalaTuningImp::getCanNPOOverride() {
    return _canNPOOverride;
}

void ScalaTuningImp::setCanNPOOverride(bool shouldOverride) {
    _canNPOOverride = shouldOverride;
    _update();
}

// notes per octave "npo" override
int ScalaTuningImp::getNPOOverride() {
    return _npoOverride;
}

void ScalaTuningImp::setNPOOverride(int npoOverride) {
    auto const newOverride = jlimit(Tuning::npoOverrideMin, Tuning::npoOverrideMax, npoOverride);
    if(_npoOverride != npoOverride) {
        _npoOverride = newOverride;
        _update();
    }
}

int ScalaTuningImp::getNPOOverrideMin() {
    return _npoOverride;
}

int ScalaTuningImp::getNPOOverrideMax() {
    return Tuning::npoOverrideMax;
}

bool ScalaTuningImp::getNPOOverrideEnable() {
    return _npoOverrideEnable;
}

void ScalaTuningImp::setNPOOverrideEnable(bool enable) {
    if(!_canNPOOverride) {
        _npoOverrideEnable = false;
    } else {
        _npoOverrideEnable = enable;
    }
    _update();
}

float ScalaTuningImp::getOctave() {
    return _octave;
}

void ScalaTuningImp::setOctave(float o) {
    jassert(o > 0.f);
    jassert(!std::isnan(o));
    jassert(!std::isinf(o));
    if(WilsonicMath::floatsAreNotEqual(_octave, o) && (o >= _octaveMin) && (o <= _octaveMax)) {
        _octave = o;
        _update();
    } else {
        DBG("ScalaTuningImp::setOctave: NOP because o is out of range: " + String(o));
    }
}

float ScalaTuningImp::getOctaveMin() {
    return _octaveMin;
}

float ScalaTuningImp::getOctaveMax() {
    return _octaveMax;
}

float ScalaTuningImp::getRepeatingInterval() {
    return _repeatingInterval;
}

void ScalaTuningImp::setRepeatingInterval(float ri) {
    _repeatingInterval = ri;
}

bool ScalaTuningImp::getOctaveReduce() {
    return _octaveReduce;
}

void ScalaTuningImp::setOctaveReduce(bool o) {
    if( _octaveReduce != o )
    {
        _octaveReduce = o;
        _update();
    }
}

// unused for Scala files...use repeatingInterval instead

bool ScalaTuningImp::getOctaveRepeat() {
    return _octaveRepeat;
}

// unused for Scala files...use repeatingInterval instead

void ScalaTuningImp::setOctaveRepeat(bool o) {
    if( _octaveRepeat != o) {
        _octaveRepeat = o;
        _update();
    }
}

bool ScalaTuningImp::getSort() {
    return _sort;
}

void ScalaTuningImp::setSort(bool s) {
    if(s != _sort) {
        _sort = s;
        _update();
    }
}

bool ScalaTuningImp::getCanSort() {
    return _canSort;
}

void ScalaTuningImp::setCanSort(bool s) {
    if(s != _canSort) {
        _canSort = s;
        _update();
    }
}

bool ScalaTuningImp::getUniquify() {
    return _uniquify;
}

void ScalaTuningImp::setUniquify(bool u) {
    if( _uniquify != u ) {
        _uniquify = u;
        _update();
    }
}

bool ScalaTuningImp::getCanUniquify() {
    return _canUniquify;
}

void ScalaTuningImp::setCanUniquify(bool u) {
    if( _canUniquify != u ) {
        _canUniquify = u;
        _update();
    }
}

const string ScalaTuningImp::getTuningName() {
    return _tuningName;
}

void ScalaTuningImp::setTuningName(string name) {
    _tuningName = name;
}

const string ScalaTuningImp::getTuningDescription() {
    return _tuningDescription;
}

void ScalaTuningImp::setTuningDescription(string description) {
    _tuningDescription = description;
}

const string ScalaTuningImp::getScalaContent() {
    return _scalaContent;
}

void ScalaTuningImp::setScalaContent(string sc) {
    _scalaContent = sc;
}

const string ScalaTuningImp::getScalaFileName() {
    return _scalaFileName;
}

void ScalaTuningImp::setScalaFilename(string fn) {
    _scalaFileName = fn;
}

const string ScalaTuningImp::getDebugDescription() {
    string retVal = "(\n";
    retVal += "n: " + getTuningName() + "\n";
    retVal += "m: " + _microtoneArray.getDebugDescription() + "\n";
    retVal += "p: " + _processedArray.getDebugDescription() + "\n";
    retVal += ")\n";
    
    return retVal;
}

const string ScalaTuningImp::getUserDescription() {
    return _tuningUserDescription;
}

void ScalaTuningImp::setUserDescription(string comment) {
    _tuningUserDescription = comment;
}

const string ScalaTuningImp::getParameterDescription() {
    return getDebugDescription();
}

bool ScalaTuningImp::getCanFavorite() {
    return _canFavorite;
}

#pragma mark - scala

bool ScalaTuningImp::getCanScala() {
    return _canScala;
}

void ScalaTuningImp::setCanScala(bool can_scala) {
    _canScala = can_scala;
}

ScalaFile ScalaTuningImp::tuningAsScala() {
    return _scalaFile;
}

String ScalaTuningImp::defaultScalaName() {
    return String(_scalaFile.fileName);
}

String ScalaTuningImp::scalaComments() {
    return String(_scalaFile.scl.get_description());
}

#pragma mark - drawing

// default is false because a tuning must implement a custom paint method(below)

bool ScalaTuningImp::canPaintTuning() {
    return false;
}

// if one were to set canPaintTuning to true, but not provide a custom paint method, this default would be called
// i.e., fallback
void ScalaTuningImp::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    // TODO: flesh this out
    
    // BG
    g.fillAll(processor.getAppSkin().getBgColor());
    
    // default is tuning name in center
    g.setColour(Colours::grey);
    g.drawText(getTuningName(), bounds, Justification::centred);
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
void ScalaTuningImp::_update() {
    // Lock to prevent other threads from accessing the same data simultaneously
    const ScopedLock sl(_lock);

    // Create a deep copy of the microtone array before processing
    _processedArray = MicrotoneArray(_microtoneArray);

    // Perform octave reduction if the flag is set
    if (_octaveReduce) {
        _processedArray = _processedArray.octaveReduce(_octave);
    }

    // Sort the array if the flag is set
    if (_canSort && _sort) {
        _processedArray = _processedArray.sort();
    }

    // Remove duplicate microtones if the flag is set
    if (_canUniquify && _uniquify) {
        _processedArray = _processedArray.uniquify();
    }

    // count of the processed/processedNPO array
    auto const count = (_canNPOOverride && _npoOverrideEnable) ? static_cast<unsigned long>(_npoOverride) : _processedArray.count();
    
    // npo override (no override ==> count = npo)
    auto [processedArrayNPO, processedArrayNPOMap] = _processedArray.npoOverride(static_cast<int>(count));
    _processedArrayNPO = processedArrayNPO;
    _processedArrayNPOMap = processedArrayNPOMap;

    if(count > 0) {
        // Loop through each MIDI note number
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

            // Set the frequency in the tuning table
            _tuningTable.setTuningTable(f, static_cast<unsigned long>(i)); // this is asserting on nyquist
            
            // Set the microtone at each note number
            setMicrotoneAtNoteNumber(tone, static_cast<unsigned long>(i));
        }

        // Perform scale analysis
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
            _tuningTable.setTuningTable(f, i );
            
            // Set the microtone at each note number to middle C
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
void ScalaTuningImp::setPostProcessPreTuningUpdate(function<void()> postProcessBlock) {
    _postProcessBlock = postProcessBlock;
}

void ScalaTuningImp::callPostProcessBlock() {
    if(_postProcessBlock != nullptr) {
        _postProcessBlock();
    }
}

void ScalaTuningImp::setOnTuningUpdate(function<void()> completionBlock) {
    _completionBlock = completionBlock;
}

void ScalaTuningImp::callOnTuningUpdate() {
    if(_completionBlock != nullptr) {
        _completionBlock();
    }
}

void ScalaTuningImp::setMicrotoneArrayFromHarmonics(vector<float> harmonics) {
    const ScopedLock sl(_lock);
    _microtoneArray.removeAllMicrotones();
    for(auto f : harmonics) {
        if(f > 0.f && !std::isnan(f)) {
            _microtoneArray.addMicrotone(make_shared<Microtone>(f));
        }
    }
    _update();
}

void ScalaTuningImp::setMicrotoneArray(MicrotoneArray ma) {
    const ScopedLock sl(_lock);
    _microtoneArray = MicrotoneArray(ma);
    _update();
}

MicrotoneArray ScalaTuningImp::getMicrotoneArray() {
    auto retVal = MicrotoneArray(_microtoneArray);
    
    return retVal;
}

MicrotoneArray ScalaTuningImp::getProcessedArray() {
    auto retVal = MicrotoneArray(_processedArray); // return copy
    
    return retVal;
}

MicrotoneArray ScalaTuningImp::getProcessedArrayNPO() {
    auto retVal = MicrotoneArray(_processedArrayNPO); // return copy
    
    return retVal;
}

unsigned long ScalaTuningImp::getMicrotoneArrayCount() {
    
    return _microtoneArray.count();
}

unsigned long ScalaTuningImp::getProcessedArrayCount() {
    
    return _processedArray.count();
}

unsigned long ScalaTuningImp::getProcessedArrayNPOCount() {
    
    return _processedArrayNPO.count();
}

const vector<PythagoreanMeans> ScalaTuningImp::getProportionalTriads() { // "major", sum tones
    
    return _proportionalTriads;
}

const vector<PythagoreanMeans> ScalaTuningImp::getGeometricTriads() {
    
    return _geometricTriads;
}

const vector<PythagoreanMeans> ScalaTuningImp::getSubcontraryTriads() { // "minor"
    
    return _subcontraryTriads;
}

const vector<PythagoreanMeans> ScalaTuningImp::getAllTriads() {
    
    return _allTriads;
}

void ScalaTuningImp::setMicrotoneAtNoteNumber(Microtone_p microtone, unsigned long nn) {
    jassert(nn >= 0 && nn < WilsonicProcessorConstants::numMidiNotes);
    const ScopedLock sl(_lock);
    _microtoneNN[nn] = microtone;
}

Microtone_p ScalaTuningImp::microtoneAtNoteNumber(unsigned long nn) {
    jassert(nn >= 0 && nn < WilsonicProcessorConstants::numMidiNotes);
    const ScopedLock sl(_lock);
    return _microtoneNN[nn];
}

const float ScalaTuningImp::getSampleRate() {
    
    return _tuningTable.getSampleRate();
}

void ScalaTuningImp::setSampleRate(float sampleRate) {
    const ScopedLock sl(_lock);
    
    // only doing this here because we want to update tuningTable if samplerate changes
    if(WilsonicMath::floatsAreNotEqual(sampleRate, _tuningTable.getSampleRate())) {
        _tuningTable.setSampleRate(sampleRate);
        _update();
    }
}

// only works for scales with rational microtones
void ScalaTuningImp::_analyzeIntervals() {
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
     NSUInteger r =(index+delta)%count;
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

#pragma mark - _analyzeProportionalTriads

// works for any microtones
// assumes sorted
// assumes degree 0 = normalized frequency of 1

/// report proportional major triads and subcontrary minor triads
/// proportional major triads = (a+b)/2
/// geometric triads = sqrt(ab), i.e. b^2 = ac; harmonic < geometric < arithmetic
/// subcontrary minor triads = (2ab)/(a+b)
/// fibonacci triplets a, b, a+b...this is merely octave reducing the term (a+b) -> (a+b)/2

/**
 * @brief Analyzes the proportional triads of the tuning.
 *
 * This function analyzes the proportional triads of the tuning. It calculates the proportional (arithmetic mean), geometric (geometric mean), and subcontrary (harmonic mean) triads for each note in the tuning and stores them in the respective member variables; _allTriads holds proportional, then subcontrary, then geometric.
 * The function also checks for duplicate triads and skips them. The function uses a tolerance value to determine if a note is part of a triad.
 *
 * Note that this method uses _processedArray, NOT _processedArrayNPO
 *
 * @note This helper function is called during the update process of the tuning.
 */
void ScalaTuningImp::_analyzeProportionalTriads() {
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
    vector<PythagoreanMeans> geometricTriads;
    vector<PythagoreanMeans> subcontraryTriads;
    vector<PythagoreanMeans> allTriads;

    // Clear the reported lists first so a scale that shrinks below three
    // notes does not keep the previous scale's triads
    _proportionalTriads.clear();
    _geometricTriads.clear();
    _subcontraryTriads.clear();
    _allTriads.clear();

    // Trivial NOP
    if (npo < 3) {
        //DBG ("Can NOT analyze proportional triads because # terms is less than 3");
        return;
    }

    // TODO: make this a continuous fn so that we ease in/out of the ui
    //    auto const tolerance = 0.0001;
    //    auto const tolerance = 0.001;
    auto const tolerance = 0.0005;

    // i.e., Triad (i, k, j)
    for (unsigned long i = 0; i < npo; i++) { // root
        auto const im = _processedArray.microtoneAtIndex(i);
        auto const imf = im->getFrequencyValue();
        for (unsigned long j = i + 2; j < npo + 2; j++) { // fifth {
            auto const ji = j % npo;
            auto const jfac = (ji < j) ? _octave : 1;
            auto const jm = _processedArray.microtoneAtIndex(ji);
            auto const jmf = jfac * jm->getFrequencyValue();
            auto const major = (imf + jmf) / 2;              // arithmetic mean: proportional
            auto const geometric = sqrtf(imf * jmf);          // geometric mean:  b^2 = ac
            auto const minor = 2 * (imf * jmf) / (imf + jmf); // harmonic mean:   subcontrary
            constexpr float major_2nd = 9.f/8.f;
            constexpr float fourth = 4.f/3.f;
            // the same lower-interval window gates all three types
            auto const majorInLimits = (major / imf > major_2nd && major / imf < fourth);
            auto const geometricInLimits = (geometric / imf > major_2nd && geometric / imf < fourth);
            auto const minorInLimits = (minor / imf > major_2nd && minor / imf < fourth);
            for (unsigned long k = i + 1; k < j; k++) { // third {
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

                // geometric
                if (geometricInLimits && fabsf(geometric - kmf) < tolerance) {
                    // dedup dedup
                    SUL mt = {i, ki, ji};
                    if (gmt.find(mt) == gmt.end()) {
                        gmt[mt] = 1UL; // add to dedup list
                        auto geometricTriad = PythagoreanMeans(i, k, j, PythagoreanMeans::Type::Geometric);
                        geometricTriads.push_back(geometricTriad);
                        allTriads.push_back(geometricTriad);
                    }
                }
            }
        }
    }
    
    // filter/transform by npo override

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

    for(auto& triad : geometricTriads) {
        if(isTriadInNPOOverride(triad)) {
            auto convertedTriad = xfmTriad(triad);
            _geometricTriads.push_back(convertedTriad);
            _allTriads.push_back(convertedTriad);
        }
    }
}

#pragma mark - description

ostream& operator <<(ostream& os, ScalaTuningImp& m) {
    os << "n: " << m.getTuningName() << "\n";
    os << "d: " << m.getTuningDescription() << "\n";
    os << "c: " << m.getUserDescription() << "\n";
    os << "m: " << m._microtoneArray << "\n";
    os << "p: " << m._processedArray << "\n";
    
    return os;
}
