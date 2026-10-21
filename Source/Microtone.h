/**
 * @file Microtone.h
 * @author Marcus W. Hobbs
 * @date 14 Feb 2021
 * @brief This file contains the Microtone class.
 */

#pragma once

#include "Tuning_Include.h"
#include "Fraction.h"
#include "TuningConstants.h"

class Microtone;
using Microtone_p = shared_ptr<Microtone>;

class Microtone {
public:
    enum class Space {
        Undefined, /**< Undefined space */
        LogPeriod, /**< Logarithmic space */
        Linear /**< Linear space */
    };

    Microtone(); /**< Default constructor. */
    Microtone(unsigned long num, unsigned long den); /**< Rational constructor. */
    Microtone(unsigned long num, unsigned long den, string shortDescriptionText, Space space); /**< Rational constructor. */
    Microtone(unsigned long num, unsigned long den, string shortDescriptionText, Space space, float period, bool should_reduce = true); /**< Rational constructor. */
    Microtone(float f); /**< Float constructor. */
    Microtone(float f, string shortDescriptionText); /**< Float constructor. */
    Microtone(float f, string shortDescriptionText, Space space); /**< Float constructor. */
    Microtone(float f, string shortDescriptionText, Space space, float period); /**< Float constructor. */

    Microtone(const Microtone& m); /**< Do not use this directly in other classes, use clone() */
    virtual Microtone_p clone() const; /**< Use this to clone a Microtone */
    virtual ~Microtone() noexcept = default; /**< Must have at least one virtual function to be polymorphic */

    /**
     * @brief Getters and setters.
     */
    Space getSpace(); /**< Returns the space of the microtone. */
    float getPitchValue01(); /**< Log Period modulus 1 */
    void setPitchValue01(float); /**< Log Period */
    float getFrequencyValue(); /**< Linear */
    void setFrequencyValue(float); /**< Linear */
    const string getFrequencyValueDescription(); /**< Truncates "integer" values: "3.000000" -> "3" */
    const string getPitchValueDescription(); /**< Truncates "integer" values: "3.000000" -> "3" */
    const string getCentsValueDescription();
    static const string getFrequencyValueDescription(float f); /**< Truncates "integer" values: "3.000000" -> "3" */
    bool isRational(); /**< Returns true if the microtone is rational. */
    const string& getShortDescriptionText();
    void setShortDescriptionText(string desc);
    /** Stable per-degree display name (e.g. "AB", "5/4", "3\\12", "0"). Designs set it;
        it survives octave reduction, sort, uniquify and NPO override via clone().
        Empty means "derive a fallback" (see AbletonAscl::degreeName). Never
        overwritten by updateShortDescriptionText(). */
    const string& getDegreeName();
    void setDegreeName(string name);
    const string& getShortDescriptionText2();
    void setShortDescriptionText2(string desc);
    const string& getShortDescriptionText3();
    void setShortDescriptionText3(string desc);
    const string getDebugDescription();
    unsigned long getNumerator(); /**< Returns the numerator of the microtone. */
    unsigned long getDenominator(); /**< Returns the denominator of the microtone. */
    void octaveReduce(); /**< In-place: uses the period defined upon construction */
    void octaveReduce(float period); /**< In-place: replace period with the argument "period" */
    Point<float> getGralErvPoint(); /**< Returns the point in the ERV space. */
    void setGralErvPoint(Point<float>); /**< Sets the point in the ERV space. */
    Point<float> getGralErvPointFinal(); /**< Returns the final point in the ERV space. */
    void setGralErvPointFinal(Point<float>); /**< Sets the final point in the ERV space. */
    Point<float> getGralErvOctaveVector();
    void setGralErvOctaveVector(Point<float>);
    Point<float> getGralHexPoint();
    void setGralHexPoint(Point<float>);
    Point<float> getGralHexPointFinal();
    void setGralHexPointFinal(Point<float>);
    Point<float> getHexOctaveVector();
    void setHexOctaveVector(Point<float>);
    Path getTouchPointPath();
    void setTouchPointPath(Path);
    void setFilterNote(bool doFilter); // filter from MTS-ESP
    bool getFilterNote();
    void setShouldRender(bool shouldRender); // should render this tone in _paint, default true
    bool getShouldRender();
    
    // Operators
    Microtone_p multiply(Microtone_p multipland); /**< Multiplies two microtones. */
    Microtone_p divide(Microtone_p divisor); /**< Divides two microtones. */
    Microtone_p add(Microtone_p rightHand); /**< Adds two microtones. */
    Microtone_p subtract(Microtone_p term); /**< Subtracts two microtones. */
    static Microtone_p freshmanSum(Microtone_p left, Microtone_p right);
    bool frequencyValueIsPowerOf2(); /**< Useful for all periods, not just 2 */
    void setMidiNoteNumber(unsigned long nn);
    unsigned long getMidiNoteNumber();
    void setMidiRegister(int registerNumber); /**< The octave register, approx -4 to 5 for 12ET. 0 = middle C register */
    int getMidiRegister();
    friend ostream& operator<<(ostream&, Microtone_p m);
    void updateShortDescriptionText();

protected:
    string _shortDescriptionText { "" };
    string _shortDescriptionText2 { "" };
    string _shortDescriptionText3 { "" };
    string _degreeName { "" };

private:
    Space _space = Space::Linear;
    bool _isRational = false;
    bool _doFilter = false; // if true, MTS will Filter Note, and the keyboard will be disabled for this note.
    Fraction _microtoneRational { 1, 1 }; /**< Frequency */
    float _microtoneNumber = 1.f; /**< Frequency */
    float _period = TuningConstants::defaultPeriod; /**< Frequency */
    unsigned long _midiNoteNumber = 60; /**< MIDI note number */
    int _midiRegister = 0; /**< MIDI register */
    Point<float> _gralErvPoint {0, 0}; ///< The Gral Erv point of the microtone.
    Point<float> _gralErvPointFinal {0, 0}; ///< The final Gral Erv point of the microtone.
    Point<float> _gralErvOctaveVector {1,1}; ///< The Gral Erv octave vector of the microtone.
    Point<float> _gralHexPoint {0.f, 0.f}; ///< The Gral Hex point of the microtone.
    Point<float> _gralHexPointFinal {0.f, 0.f}; ///< The final Gral Hex point of the microtone.
    Point<float> _gralHexOctaveVector {0, 0}; ///< The Gral Hex octave vector of the microtone.
    Path _touchPointPath; ///< The touch point path of the microtone, in screen coordinates.
    bool _shouldRender = true;
};


