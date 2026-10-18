/**
 * @file Brun.h
 * @brief Definition of the Brun class.
 * @details This class represents a Moment of Symmetry (MOS) scale. A MOS scale consists of a generator (of any size, for example a 3/2 or a fifth in 12 equal temperament) which is repeatedly superimposed but reduced within an Interval of Equivalence commonly called a period (of any size, for example most commonly an octave). A MOS is formed where each scale degree or scale unit size will be represented by no more than two sizes and two sizes only (Large = L and small = s). The relative number of L and s intervals is coprime, i.e. they share no common factors other than 1. The numerator (generator) and denominator (period) representing MOS are also co-prime. This class implements Brun's algorithm, a mathematical method for generating MOS scales.
 * @date Created: 14 Feb 2021 3:01:54pm
 * @author Marcus W. Hobbs
 */

#pragma once

#include <JuceHeader.h>
#include "Tuning_Include.h"
#include "Microtone.h"
#include "MicrotoneArray.h"
#include "Tuning.h"
#include "TuningImp.h"
#include "TuningTableImp.h"

class WilsonicProcessor;

/**
 * @class Brun
 * @brief Represents a Moment of Symmetry (MOS) scale.
 * @details This class provides methods for manipulating and displaying MOS scales. It implements Brun's algorithm, a mathematical method for generating MOS scales. The algorithm works by repeatedly superimposing a generator (a musical interval) and reducing it within a period (another musical interval), forming a scale where each scale degree is represented by no more than two sizes. The algorithm ensures that the relative number of large and small intervals is coprime, meaning they share no common factors other than 1. This results in a scale that is maximally even, meaning the scale degrees are spread out as evenly as possible.
 * @extends TuningImp
 */
class Brun final : public TuningImp
{
public:
    // MOS display modes
    enum class DisplayMode {
        Cartesian = 0, // Cartesian coordinate system.
        Horogram = 1, // horogram, polar coordinates
        HorogramInverse = 2, // inverse horogram.
        Gral = 3 // Gral (hexagonal)
    };

    // these must be indexed by DisplayMode, and the order should never change
    static const StringArray __displayModeNames;
    static constexpr int num_display_modes = 3;

    // constants
    static constexpr unsigned long absoluteMinLevel {0};
    static constexpr unsigned long absoluteMaxLevel {9};
    static constexpr unsigned long defaultLevel {4};
    static constexpr float minGenerator {0.f}; // can never change
    static constexpr float maxGenerator {1.f}; // can never change
    static constexpr float defaultGenerator {0.58333333f};
    static constexpr float defaultPeriod {TuningConstants::defaultOctave}; // period = octave in Tuning/TuningImp
    static constexpr unsigned long minMurchana {0};
    static constexpr unsigned long maxMurchana {89}; // max npo at max level 9
    static constexpr unsigned long defaultMurchana {0};

    // lifecycle
    Brun();
    Brun(unsigned long maxLevel, unsigned long level, float generator, float period);
    ~Brun() noexcept override = default;

    // public methods
    unsigned long getMaxLevel(); // Returns the maximum level of the Brun object.
    void setMaxLevel(unsigned long newMaxLevel); // Sets the maximum level of the Brun object.
    unsigned long getLevel(); // Returns the current level of the Brun object.
    void setLevel(unsigned long newLevel); // Sets the current level of the Brun object.
    unsigned long getLevelGral(); // Returns the current Gral level of the Brun object.
    void setLevelGral(unsigned long newLevel); // Sets the current Gral level of the Brun object.
    vector<string> getLabelArray(); // Returns an array of labels for the scale degrees.
    unsigned long getNotesPerOctave(); // Returns the number of notes per octave in the scale.
    DisplayMode getDisplayMode(); // Returns the current display mode of the Brun object.
    void setDisplayMode(DisplayMode newDisplayMode); // Sets the display mode of the Brun object.
    float getGenerator(); // Returns the generator of the Brun object.
    void setGenerator(float newGenerator); // Sets the generator of the Brun object.
    float getGeneratorWithFrequency(); // Returns the generator of the Brun object in terms of frequency.
    float getGeneratorGivenFrequency(float frequency); // Returns the generator corresponding to a given frequency.
    void setGeneratorWithFrequency(float newGenerator); // Sets the generator of the Brun object in terms of frequency.
    float getGeneratorWithCents(); // Returns the generator of the Brun object in terms of cents.
    float getGeneratorGivenCents(float cents); // Returns the generator corresponding to a given number of cents.
    void setGeneratorWithCents(float newGenerator); // Sets the generator of the Brun object in terms of cents.
    unsigned long getMurchana(); // Returns the current Murchana of the Brun object.
    void setMurchana(unsigned long newMurchana); // Sets the Murchana of the Brun object.
    bool getAutoMurchana(); // Returns whether the Murchana is set automatically.
    void setAutoMurchana(bool autoMurchana); // Sets whether the Murchana is set automatically.
    void setGralHexScale(float newScale); // Sets the scale of the Gral hexagon.
    float getGralHexScale(); // Returns the scale of the Gral hexagon.
    void setGralHexRotationRadians(float newRotationRadians); // Sets the rotation of the Gral hexagon in radians.
    float getGralHexRotationRadians(); // Returns the rotation of the Gral hexagon in radians.
    void setGralHexShearX(float newShearX); // Sets the shear of the Gral hexagon in the x direction.
    float getGralHexShearX(); // Returns the shear of the Gral hexagon in the x direction.
    void setGralHexOriginOffsetFactorX(float newOffsetX); // Sets the offset of the Gral hexagon origin in the x direction.
    float getGralHexOriginOffsetFactorX(); // Returns the offset of the Gral hexagon origin in the x direction.
    void setGralHexOriginOffsetFactorY(float newOffsetX); // Sets the offset of the Gral hexagon origin in the y direction.
    float getGralHexOriginOffsetFactorY(); // Returns the offset of the Gral hexagon origin in the y direction.

    // public static methods
    static vector<vector<Microtone_p>> brunArray(unsigned long minLevel, unsigned long maxLevel, Microtone_p zero, Microtone_p one); // Returns a 2D array of Microtone pointers representing a Brun array.
    static vector<vector<Microtone_p>> getLevelArray(); // Returns a 2D array of Microtone pointers representing the levels of the Brun object.
    static MicrotoneArray getHarmonicLimitCartesian(float period); // Returns a MicrotoneArray representing the harmonic limit in Cartesian coordinates.
    static MicrotoneArray getHarmonicLimitHorogram(float period); // Returns a MicrotoneArray representing the harmonic limit in a horogram.
    static MicrotoneArray getHarmonicLimitHorogramInverse(float period); // Returns a MicrotoneArray representing the harmonic limit in an inverse horogram.
    static Microtone_p brun(unsigned long level, float generator); // Returns a Microtone pointer representing a Brun object.
    static MicrotoneArray brunArray(unsigned long level, float g); // Returns a MicrotoneArray representing a Brun array.
    static MicrotoneArray brunArray(unsigned long level, float g, unsigned long minBrunLevel, unsigned long maxBrunLevel); // Returns a MicrotoneArray representing a Brun array with a specified minimum and maximum level.

    friend ostream& operator << (ostream&, Brun& m); // Overloads the << operator for outputting a Brun object.
    const string getDebugDescription() override; // Returns a string representing the debug description of the Brun object.
    const string getParameterDescription() override; // Returns a string representing the parameter description of the Brun object.
    
    // Scala
    String defaultScalaName() override; // Returns the default Scala name of the Brun object.
    String scalaComments() override; // Returns the Scala comments of the Brun object.
    
    // Drawing
    bool canPaintTuning() override; // Returns whether the Brun object can be painted.
    void paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) override; // Paints the Brun object.

private:
    // statics
    static vector<vector<Microtone_p>> __levelArray; // A 2D array of Microtone pointers representing the levels of the Brun object.
    static MicrotoneArray __harmonicLimitCartesian; // A MicrotoneArray representing the harmonic limit in Cartesian coordinates.
    static MicrotoneArray __harmonicLimitHorogram; // A MicrotoneArray representing the harmonic limit in a horogram.
    static MicrotoneArray __harmonicLimitHorogramInverse; // A MicrotoneArray representing the harmonic limit in an inverse horogram.

    // Brun implementation parameters
    unsigned long _maxLevel = 6; // The maximum level of the Brun object.
    unsigned long _level = 5; // The current level of the Brun object.
    unsigned long _levelGral = 5; // The current Gral level of the Brun object.
    float _generator = defaultGenerator; // The generator of the Brun object.
    unsigned long _murchana = 0; // The current Murchana of the Brun object.
    bool _autoSetMurchana = false; // Whether the Murchana is set automatically.
    DisplayMode _displayMode = DisplayMode::Cartesian; // The current display mode of the Brun object.
    shared_ptr<MicrotoneArray> _brunArray = nullptr; // A pointer to a MicrotoneArray representing the Brun array.
    vector<shared_ptr<MicrotoneArray>> _microtoneArrayBrunAllLevels {10, nullptr}; // A vector of pointers to MicrotoneArrays representing all levels of the Brun object.
    vector<string> _labelArray {}; // An array of labels for the scale degrees.
    shared_ptr<vector<int>> _gral_column_pattern; // A pointer to a vector representing the column pattern of the Gral display.
    
    // private methods
    void _assignDegreeNames() override; // MOS degree names "0".."N-1" by processed-array index (tonic = 0)
    void _brunUpdate(); // Updates gral after a change in parameters, before TuningImp::update
    MicrotoneArray _microtoneArrayBrun(unsigned long level, float generator, unsigned long murchana); // Returns a MicrotoneArray representing a Brun array for a given level, generator, and Murchana.
    void _paintCartesian(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds); // Paints the Brun object in Cartesian coordinates.
    void _paintHorogram(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds); // Paints the Brun object in a horogram.
    void _paintInverseHorogram(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds); // Paints the Brun object in an inverse horogram.
    void _paintGral(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds); // Paints the Brun object in a Gral.
    void _paintGralNPOOverride(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds); // does not paint the Brun object in a Gral, because NPO override is enabled
    unsigned long _validLevelGral(unsigned long newLevelGral); // Returns a valid Gral level for a given level.
    float _octaveReduceP01(float p); // Reduces a pitch to within an octave.
    void _mapGralToBrunMicrotones(MicrotoneArray& inArray, Point<float> generator_vector, Point<float> octave_vector); // Maps Gral points to Brun microtones.
    AffineTransform _gralPaintTransform() override; // Returns an AffineTransform representing the transformation of the Gral display.
};
