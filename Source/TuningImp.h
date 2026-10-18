/**
 * @file TuningImp.h
 * @author Marcus W. Hobbs
 * @date 14 Feb 2021
 * @brief This file contains the TuningImp class.
 */

#pragma once

#include <JuceHeader.h>
#include "AppExperiments.h"
#include "Microtone.h"
#include "MicrotoneArray.h"
#include "Tuning.h"
#include "TuningTableImp.h"
#include "WilsonicProcessorConstants.h"

class WilsonicProcessor;

/**
 * @class TuningImp
 * @brief This class is an implementation of the Tuning class.
 * 
 * The TuningImp class provides the functionality for tuning implementation.
 * It includes methods for setting and getting various tuning parameters,
 * as well as methods for analyzing intervals and proportional triads.
 */
class TuningImp
: public Tuning
{
public:
    TuningImp();
    TuningImp(const TuningImp& t);
    ~TuningImp() noexcept override = default;

protected:
    void _update() override;
    virtual void _assignDegreeNames(); // hook: runs on _processedArray after reduce/sort/uniquify, before NPO override
    void _analyzeIntervals();
    void _analyzeProportionalTriads();
    void _paintHelper(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds);
    AffineTransform _cartesian2HexTransform(Point<float> hp); // Returns an AffineTransform representing the transformation from Cartesian to hexagonal coordinates.
    Point<float> _octaveReduceGralPoint(Point<float> inPoint, Point<float> octavePoint, bool degreeIsPositive); // Reduces a Gral point to within an octave.
    unsigned long _debug_paint_counter = 0; // A counter for debugging painting
    virtual AffineTransform _gralPaintTransform(); // Returns an AffineTransform representing the transformation of the Gral display.


public:
    const float getSampleRate() override;
    void setSampleRate(float sampleRate) override;
    
    void setTuningTable(float frequency, unsigned long index) override;
    const float getTuningTableFrequency(unsigned long index) override;
    void setMicrotoneArrayFromHarmonics(vector<float> harmonics) override;
    void setMicrotoneArray(MicrotoneArray ma) override; // calls update
    MicrotoneArray getMicrotoneArray() override;
    unsigned long getMicrotoneArrayCount() override;
    MicrotoneArray getProcessedArray() override;
    unsigned long getProcessedArrayCount() override;
    MicrotoneArray getProcessedArrayNPO() override;
    unsigned long getProcessedArrayNPOCount() override;

    const vector<PythagoreanMeans> getProportionalTriads() override; // "major", sum tones
    const vector<PythagoreanMeans> getGeometricTriads() override; // geometric mean
    const vector<PythagoreanMeans> getSubcontraryTriads() override; // "minor"  harmonic mean
    const vector<PythagoreanMeans> getAllTriads() override; // all of them
    
    void setMicrotoneAtNoteNumber(Microtone_p microtone, unsigned long nn) override;
    Microtone_p microtoneAtNoteNumber(unsigned long nn) override;

    void setPostProcessPreTuningUpdate(function<void()> postProcessBlock) override;
    void callPostProcessBlock() override;
    void setOnTuningUpdate(function<void()> completionBlock) override;
    void callOnTuningUpdate() override;
    
    // experiment currently off
    int getMode() override;
    void setMode(int mode) override;

    unsigned long getNoteNumberMiddleC() override;
    void setNoteNumberMiddleC(unsigned long nn) override;
    unsigned long getNoteNumberMiddleCMin() override;
    unsigned long getNoteNumberMiddleCMax() override;
    
    float getFrequencyMiddleC() override;
    void setFrequencyMiddleC(float f) override;
    float getFrequencyMiddleCMin() override;
    float getFrequencyMiddleCMax() override;
    
    int getOctaveMiddleC() override;
    void setOctaveMiddleC(int o) override;
    int getOctaveMiddleCMin() override;
    int getOctaveMiddleCMax() override;

    // does tuning support npo override?
    bool getCanNPOOverride() override;
    void setCanNPOOverride(bool) override;

    // notes per octave "npo" override
    int getNPOOverride() override;
    void setNPOOverride(int) override;
    int getNPOOverrideMin() override;
    int getNPOOverrideMax() override;
    bool getNPOOverrideEnable() override;
    void setNPOOverrideEnable(bool) override;
    
    float getOctave() override;
    void setOctave(float o) override;
    float getOctaveMin() override;
    float getOctaveMax() override;
    bool getOctaveReduce() override;
    void setOctaveReduce(bool o) override;
    bool getOctaveRepeat() override;
    void setOctaveRepeat(bool o) override;

    bool getSort() override;
    void setSort(bool s) override;
    bool getCanSort() override;
    void setCanSort(bool s) override;

    bool getUniquify() override;
    void setUniquify(bool u) override;
    bool getCanUniquify() override;
    void setCanUniquify(bool u) override;

    const string getTuningName() override;
    void setTuningName(string name) override;
    const string getTuningDescription() override;
    void setTuningDescription(string description) override;
    const string getDebugDescription() override;
    const string getUserDescription() override;
    void setUserDescription(string comment) override;
    const string getParameterDescription() override;

    bool getCanFavorite() override;

    bool getCanScala() override;
    void setCanScala(bool can_scala) override;
    ScalaFile tuningAsScala() override;
    String defaultScalaName() override;
    String scalaComments() override;

    bool canPaintTuning() override;
    void paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) override;
    virtual int nnForDeviceSpace(Point<int> xy); // Returns the note number for a given device space, usually updated by paint
    Point<float> transformGral2Hex(Point<float> gralPoint); // Transforms a Gral point to a hexagonal coordinate system.

    /**
     * @brief Overloads the << operator for the TuningImp class.
     * @param ostream The ostream to use.
     * @param m The TuningImp object to print.
     * @return The ostream with the TuningImp object printed.
     */
    friend ostream& operator << (ostream&, TuningImp& m);

private:
    // keep as int
    int _mode = -1; // _mode=-1=NOP, _mode >= 0: normalize by processedArray[mode]

    //
    unsigned long _noteNumberMiddleC = Tuning::noteNumberMiddleCDefault;
    unsigned long _noteNumberMiddleCMin = Tuning::noteNumberMiddleCMin;
    unsigned long _noteNumberMiddleCMax = Tuning::noteNumberMiddleCMax;

    // frequency at middle c
    float _frequencyMiddleC = Tuning::frequencyMiddleCDefault;
    float _frequencyMiddleCMin = Tuning::frequencyMiddleCMin;
    float _frequencyMiddleCMax = Tuning::frequencyMiddleCMax;

    // keep as int
    int _octaveMiddleC = Tuning::octaveMiddleCDefault;
    int _octaveMiddleCMin = Tuning::octaveMiddleCMin;
    int _octaveMiddleCMax = Tuning::octaveMiddleCMax;
    
    // keep as int
    // notes per octave "npo" override
    bool _canNPOOverride = false;
    int _npoOverride = Tuning::npoOverrideDefault;
    int _npoOverrideMin = Tuning::npoOverrideMin;
    int _npoOverrideMax = Tuning::npoOverrideMax;
    bool _npoOverrideEnable = Tuning::npoOverrideEnableDefault;

    float _octave = TuningConstants::defaultOctave;
    float _octaveMin = TuningConstants::minPeriod;
    float _octaveMax = TuningConstants::maxPeriod;

    bool _octaveReduce = true;
    bool _octaveRepeat = true;

    bool _sort = true;
    bool _canSort = true;

    bool _uniquify = false;
    bool _canUniquify = true;

    // note: need to encode UTF8...no special characters.
    // *short* human-readable title...i.e., "MOS", "Hexany", "Co-Prime Grid"
    string _tuningName {""};

    // *short* human-readable desc.., i.e., "G=0.5833", "A=3,B=5,C=7,D=9"
    string _tuningDescription {""};

    // 140 char limit...utf8 encoded.
    string _tuningUserDescription {""};

    // Some tunings cannot be represented by Favorites...i.e., arbitrary scala files
    bool _canFavorite = true;

    // some tunings cannot be represented by scala, i.e., CPG, Lambdoma Pascal
    bool _canScala = true; // default is true because TuningImp implements it

protected:
    // pitch class
    MicrotoneArray _microtoneArray;

    // pitch class after being reduced, sorted, and uniquified
    MicrotoneArray _processedArray {};
    MicrotoneArray _processedArrayNPO {};
    map<int, int> _processedArrayNPOMap {}; // npo override indices -> original npo indices
    void _gralPostProcessBlockImp(); // updates Gral after tuning update

    // lock
    CriticalSection _lock;
    
    // Gral
    static constexpr float __hexWidth = 60.f; // The width of the hexagon in the Gral display.
    static constexpr float __hexHeight = 66.f; // The height of the hexagon in the Gral display.
    static constexpr float __hexMargin = 4.f; // The margin of the hexagon in the Gral display.
    Point<float> _gralHexOrigin {0.f, 100.f}; // The origin of the Gral hexagon.
    float _gralHexScale = 0.75f * 1.f; // The scale of the Gral hexagon.
    float _gralHexRotationRadians = 0.f; // The rotation of the Gral hexagon in radians.
    float _gralHexShearX = 0.f; // The shear of the Gral hexagon in the x direction.
    float _gralHexOriginOffsetFactorX = 0.f; // The offset of the Gral hexagon origin in the x direction.
    float _gralHexOriginOffsetFactorY = 0.f; // The offset of the Gral hexagon origin in the y direction.
    float const _getHexMargin() {return __hexMargin * _gralHexScale;} // Returns the margin of the Gral hexagon.
    float const _getHexWidth() {return __hexWidth * _gralHexScale;} // Returns the width of the Gral hexagon.
    float const _getHexHeight() {return __hexHeight * _gralHexScale;} // Returns the height of the Gral hexagon.
    struct PointHash { // for the debug map
        std::size_t operator()(const juce::Point<float>& p) const noexcept {
            return hash<float>()(p.x) ^ hash<float>()(p.y); // Hashes a point for use in a map.
        }
    };
    std::unordered_map<Point<float>, string, PointHash> _debugGralPointMap {}; // A map for debugging Gral points.


private:
    // arrays of triads from this processed master set
    vector<PythagoreanMeans> _proportionalTriads {};
    vector<PythagoreanMeans> _geometricTriads {};
    vector<PythagoreanMeans> _subcontraryTriads {};
    vector<PythagoreanMeans> _allTriads {};

    // Maps midi note numbers to the source microtone
    array<Microtone_p, WilsonicProcessorConstants::numMidiNotes> _microtoneNN {};

    // completion handlers
    function<void()> _postProcessBlock;
    function<void()> _completionBlock;

    // "has-a" TuningTable
    TuningTableImp _tuningTable;
};
