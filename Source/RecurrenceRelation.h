/*
  ==============================================================================

    RecurrenceRelation.h
    Created: 21 Mar 2022 8:45:37pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "MicrotoneArray.h"
#include "Tuning_Include.h"
#include "TuningImp.h"
#include "WilsonicProcessorConstants.h"

class RecurrenceRelation
: public TuningImp
{
public:

    // **if you ever change these you will break automation**

    // types
    using IndexTuple = tuple<String, unsigned long, unsigned long>;
    using CoefficientTuple = tuple<String, float>;
    enum class Coefficient
    {
        _1_8 = 0,
        _1_4 = 1,
        _1_2 = 2,
        _1   = 3,
        _2   = 4,
        _4   = 5,
        _8   = 6
    };

    // Sum type for recurrence calculation
    enum class SumType
    {
        Arithmetic = 0,  // H[n] = a + b      (proportional triads)
        Harmonic   = 1   // H[n] = ab/(a+b)   (subcontrary triads)
    };

    // Seed space transformation
    enum class SeedSpace
    {
        Frequency = 0,  // Seeds used as-is: s
        Period    = 1   // Seeds inverted: 1/s
    };

    // 1/8, 1/4, 1/2, 1, 2, 4, 8
    static float constexpr getCoefficientMin() { return 1/8.f; }
    static float constexpr getCoefficientMax() { return 8; }
    static float constexpr getCoefficientDefault() { return 3; }
    static StringArray getCoefficientsDescription() { return __coefficientsDescription; }

    // seeds are floats
    static float constexpr getSeedMin() { return 1; }
    static float constexpr getSeedMax() { return 16383; }
    static float constexpr getSeedDefault() { return 1; }
    static float constexpr getSeedIntervalValue() { return 1; }

    // pre-determined H[n] = C[n-i] * H[n-i] + C[n-j] * H[n-j]
    static StringArray getIndicesDescription() { return __indicesDescription; }

    // Sum Type: Arithmetic or Harmonic
    static StringArray getSumTypeDescription() { return __sumTypeDescription; }
    static constexpr int getSumTypeDefault() { return 0; } // Arithmetic

    // Seed Space: Frequency or Period
    static StringArray getSeedSpaceDescription() { return __seedSpaceDescription; }
    static constexpr int getSeedSpaceDefault() { return 0; } // Frequency

    // 0 <= offset <= 127 // magic, not based on midi nn
    static int constexpr getOffsetMin() { return 0; }
    static int constexpr getOffsetMax() { return 127; }
    static int constexpr getOffsetDefault() { return 0; }

    // 1 <= number of terms <= 128 based on midi nn
    static int constexpr getNumberOfTermsMin() { return 1; }
    static int constexpr getNumberOfTermsMax() { return WilsonicProcessorConstants::numMidiNotes; }
    static int constexpr getNumberOfTermsDefault() { return 7; }
    
    // **if you ever change these you will break automation**

private:
    // private static members
    static vector<IndexTuple> __indices;
    static StringArray __indicesDescription;
    static vector<CoefficientTuple> __coefficients;
    static StringArray __coefficientsDescription; // for combo box
    static int constexpr __maxNumUpdateIterations {500};
    static unordered_map<Coefficient, string> __coefficientsDescriptionMap; // for log
    static StringArray __sumTypeDescription;
    static StringArray __seedSpaceDescription;

public:
    // lifecycle
    RecurrenceRelation();
    ~RecurrenceRelation() override;

    // public methods
    void setIndices (unsigned long indices); // selects from pre-computed list of indices...i.e, (i=1, j=9)
    unsigned long getIndices(); // returns selected index into indices
    unsigned long getIndexI(); // 1 <= I, I < J, I <= 8
    unsigned long getIndexJ(); // 2 <= J, J > I, J <= 9
    void setSeeds (float s1, float s2, float s3, float s4, float s5, float s6, float s7, float s8, float s9);
    void setSeed (float s, unsigned long i_1_9); // index is 1-9, not 0-8
    float getSeed (unsigned long i_1_9);
    void setCoefficients (Coefficient c1, Coefficient c2, Coefficient c3, Coefficient c4, Coefficient c5, Coefficient c6, Coefficient c7, Coefficient c8, Coefficient c9);
    void setCoefficient (Coefficient c, unsigned long i_1_9); // index is 1-9, not 0-8
    void setCoefficientByIndex (unsigned long ci, unsigned long i_1_9); // index is 1-9, not 0-8, ci supports automation by DAWs
    Coefficient getCoefficient (unsigned long i_1_9);
    float getCoefficientValue (unsigned long i_1_9);
    static float getValueForCoefficient (Coefficient c); // given enum return float value
    void setNumberOfTerms (unsigned long num_terms);
    unsigned long getNumberOfTerms();
    void setOffset (unsigned long offset);
    unsigned long getOffset();
    const string getLog(); // description of raw and filtered sequence, including non-convergence
    
    // block will be called if the series diverges...can be used to update UI
    void setOnDivergence (function<void()> completionBlock);

    // Sum Type
    void setSumType(SumType sumType);
    SumType getSumType();
    void setSumTypeByIndex(unsigned long index);
    unsigned long getSumTypeIndex();

    // Seed Space
    void setSeedSpace(SeedSpace seedSpace);
    SeedSpace getSeedSpace();
    void setSeedSpaceByIndex(unsigned long index);
    unsigned long getSeedSpaceIndex();

    // drawing
    bool canPaintTuning() override;
    void paint (WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) override;

    // Scala
    String defaultScalaName() override;
    String scalaComments() override;

private:
    // private methods
    void _updateRecurrenceRelation();

    // private members
    unsigned long _indices {0}; // the index into the set of indices
    unsigned long _i {1}, _j {2}; // set internally by setIndices(), NOT automatable, not manipulated any where else
    MicrotoneArray _seeds; // automatable
    vector<Coefficient> _coefficients {Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1, Coefficient::_1}; // 0, 1-9, automatable
    unsigned long _numberOfTerms {7}; // automatable.  1 <= _numberOfTerms < WilsonicProcessorConstants::numMidiNotes
    unsigned long _offset {0}; // automatable
    string _log;
    function<void()> _divergenceCompletionBlock;
    SumType _sumType = SumType::Arithmetic;
    SeedSpace _seedSpace = SeedSpace::Frequency;
};
