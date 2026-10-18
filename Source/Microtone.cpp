/*
 ==============================================================================

 Microtone.cpp
 Created: 14 Feb 2021 3:53:19pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "Microtone.h"
#include "WilsonicAppSkin.h"
#include "WilsonicMath.h"

#pragma mark - Lifecycle

Microtone::Microtone()
: Microtone(1, 1, "", Space::Linear, TuningConstants::defaultPeriod) {
    
}

// rational constructors
Microtone::Microtone(unsigned long num, unsigned long den)
: Microtone(num, den, "", Space::Linear, TuningConstants::defaultPeriod) {

}

Microtone::Microtone(unsigned long num,
                      unsigned long den,
                      string shortDescriptionText,
                      Space space,
                      float period,
                      bool should_reduce) {
    _isRational = true;
    _space = space;
    _period = period;
    _microtoneRational = Fraction(num, den, should_reduce);

    // update description
    if( shortDescriptionText.size() == 0 ) {
        ostringstream stringStream;
        if(den == 1) {
            stringStream << num;
        } else {
            stringStream << num << "/" << den;
        }
        _shortDescriptionText = stringStream.str();
    } else {
        _shortDescriptionText = shortDescriptionText;
    }
}

Microtone::Microtone(float f)
: Microtone(f, "", Space::Linear, TuningConstants::defaultPeriod) {

}

Microtone::Microtone(float f, string shortDescription)
: Microtone(f, shortDescription, Space::Linear, TuningConstants::defaultPeriod) {

}

Microtone::Microtone(float f, string shortDescription, Space space)
    : Microtone(f, shortDescription, space, TuningConstants::defaultPeriod) {

}

Microtone::Microtone(float f,
                      string shortDescriptionText,
                      Space space,
                      float period) {
    jassert(! std::isnan(f));
    jassert((space == Space::LogPeriod && f >= 0.f) || (space == Space::Linear && f > 0.f));
    jassert(period >= TuningConstants::minPeriod);
    jassert(period <= TuningConstants::maxPeriod);
    _isRational = false;
    _space = space;
    _microtoneNumber = f;
    _period = period;

    // update description
    if( shortDescriptionText.size() == 0 ) {
        ostringstream stringStream;
        stringStream << f;
        _shortDescriptionText = stringStream.str();
    } else {
        _shortDescriptionText = shortDescriptionText;
    }
}

Microtone::Microtone(const Microtone& other) {
    _space = other._space;
    _isRational = other._isRational;
    _microtoneRational = other._microtoneRational;
    _microtoneNumber = other._microtoneNumber;
    _period = other._period;
    _gralErvPoint = other._gralErvPoint;
    _gralErvPointFinal = other._gralErvPointFinal;
    _gralErvOctaveVector = other._gralErvOctaveVector;
    _gralHexPoint = other._gralHexPoint;
    _gralHexPointFinal = other._gralHexPointFinal;
    _gralHexOctaveVector = other._gralHexOctaveVector;
    _touchPointPath = other._touchPointPath;
    _midiNoteNumber = other._midiNoteNumber;
    _midiRegister = other._midiRegister;
    _shortDescriptionText = other._shortDescriptionText;
    _shortDescriptionText2 = other._shortDescriptionText2;
    _shortDescriptionText3 = other._shortDescriptionText3;
    _degreeName = other._degreeName;
    _doFilter = other._doFilter;
    _shouldRender = other._shouldRender;
}

Microtone_p Microtone::clone() const {
    return make_shared<Microtone>(*this);
}

#pragma mark - getters/setters

Microtone::Space Microtone::getSpace() {
    return _space;
}

bool Microtone::isRational() {
    return _isRational;
}

const string& Microtone::getShortDescriptionText() {
    return _shortDescriptionText;
}

void Microtone::setShortDescriptionText(string desc) {
    _shortDescriptionText = string {desc}; // copy
}

const string& Microtone::getDegreeName() {
    return _degreeName;
}

void Microtone::setDegreeName(string name) {
    _degreeName = string {name}; // copy
}

const string& Microtone::getShortDescriptionText2() {
    return _shortDescriptionText2;
}

void Microtone::setShortDescriptionText2(string desc) {
    _shortDescriptionText2 = string {desc}; // copy
}

const string& Microtone::getShortDescriptionText3() {
    return _shortDescriptionText3;
}

void Microtone::setShortDescriptionText3(string desc) {
    _shortDescriptionText3 = string {desc}; // copy
}

const string Microtone::getDebugDescription() {
    ostringstream stringStream;
    stringStream << getShortDescriptionText();
    stringStream << getShortDescriptionText2();
    stringStream << getShortDescriptionText3();
    stringStream << "(";
    stringStream << getFrequencyValueDescription();
    stringStream << ")";
    return stringStream.str();
}

// TODO: need to return float
unsigned long Microtone::getNumerator() {
    if( _isRational ) {
        return _microtoneRational.numerator();
    } else {
        return static_cast<unsigned long>(_microtoneNumber);
    }
}

// TODO: need to return float
unsigned long Microtone::getDenominator() {
    if( _isRational ) {
        return _microtoneRational.denominator();
    } else {
        return 1;
    }
}

/**
 * @brief Get the pitch value in the range of 0 to 1.
 *
 * This function calculates the pitch value based on the microtone number or the rational value of the microtone.
 * The calculation is done differently based on the space (_space) of the microtone.
 *
 * @return float The pitch value in the range of 0 to 1.
 */
float Microtone::getPitchValue01() {
    // Determine the base value for the pitch calculation
    auto const f = _isRational ? _microtoneRational.floatValue() : _microtoneNumber;

    // Calculate the pitch value based on the space of the microtone
    switch(_space) {
        case Space::Linear: {
            // Assert that the base value and the period are valid
            jassert(f > 0.f);
            jassert(_period >= TuningConstants::minPeriod);

            // If the period is the minimum period, return the base-2 logarithm of the base value
            if(WilsonicMath::floatsAreEqual(_period, TuningConstants::minPeriod)) {
                return log2f(f);
            } else {
                // Calculate the pitch value based on the logarithm of the base value and the period
                auto retVal = logf(f) / logf(_period);
                float intPart = 1;
                retVal = modf(retVal, &intPart);

                // Adjust the pitch value if it is negative
                if(retVal < 0.f) {
                    retVal = 1.f + retVal;
                }

                // Ensure the pitch value is in the range of 0 to 1
                retVal = fmodf(retVal, 1.f);

                // Assert that the pitch value is a valid number
                jassert(!std::isnan(retVal));
                jassert(!std::isinf(retVal));

                return retVal;
            }
        }
            break;

        // If the space is Log2, return the base value
        case Space::LogPeriod:
            return f;
            break;

        // If the space is undefined or any other value, assert false and return 0
        case Space::Undefined : default:
            jassertfalse;
            return 0.0f;
            break;
    }
}

/**
 * @brief Sets the pitch value of the Microtone object.
 *
 * This function sets the pitch value of the Microtone object. The pitch value is a float between 0 and 1.
 * The function first checks if the Microtone object is rational and if the pitch value is within the valid range.
 * Then, depending on the space of the Microtone object, it calculates the microtone number.
 *
 * @param p The pitch value to be set. It should be a float between 0 and 1.
 */
void Microtone::setPitchValue01(float p) {
    // Assert that the Microtone object is not rational
    jassert(_isRational == false);

    // Assert that the pitch value is within the valid range
    if(p < 0.f || p > 1.f) {
        jassertfalse;
    }

    // Switch case depending on the space of the Microtone object
    switch(_space) {
        // If the space is Linear, calculate the microtone number using the period and the pitch value
        case Space::Linear:
            _microtoneNumber = pow(_period, p);
            break;

        // If the space is Log2, set the microtone number to the pitch value
        case Space::LogPeriod:
            _microtoneNumber = p;
            break;

        // If the space is Undefined or any other value, assert false
        case Space::Undefined : default:
            // error
            jassertfalse;
            break;
    }
}

/**
 * @brief Gets the frequency value of the Microtone object.
 *
 * This function retrieves the frequency value of the Microtone object.
 * If the Microtone object is rational, it returns the float value of the microtone rational.
 * Otherwise, it returns the microtone number.
 * Depending on the space of the Microtone object, it calculates the frequency value.
 *
 * @return The frequency value of the Microtone object.
 */
float Microtone::getFrequencyValue() {
    // Determine the frequency value based on whether the Microtone object is rational or not
    auto f = _isRational ? _microtoneRational.floatValue() : _microtoneNumber;

    // Switch case depending on the space of the Microtone object
    switch(_space) {
        // If the space is Linear, return the frequency value
        case Space::Linear:
            return f;
            break;

        // If the space is Log2, calculate and return the frequency value using the period and the frequency value
        case Space::LogPeriod:
            return pow(_period, f);
            break;

        // If the space is Undefined or any other value, assert false and return 0
        case Space::Undefined : default:
            // error
            jassertfalse;
            return 0.0f;
            break;
    }
}

/**
 * @brief Sets the frequency value of the Microtone object.
 *
 * This function sets the frequency value of the Microtone object.
 * It asserts that the Microtone object is not rational and that the frequency value is greater than 0.
 * Depending on the space of the Microtone object, it calculates and sets the microtone number.
 *
 * @param f The frequency value to set.
 */
void Microtone::setFrequencyValue(float f) {
    // Assert that the Microtone object is not rational and that the frequency value is greater than 0
    jassert(_isRational == false);
    jassert(f > 0);

    // Switch case depending on the space of the Microtone object
    switch(_space) {
        // If the space is Linear, set the microtone number to the frequency value
        case Space::Linear:
            _microtoneNumber = f;
            break;

        // If the space is Log2, calculate and set the microtone number using the frequency value and the period
        case Space::LogPeriod:
            _microtoneNumber = log2(f) / log2(_period);
            break;

        // If the space is Undefined or any other value, assert false
        case Space::Undefined:
        default:
            // error
            jassertfalse;
            break;
    }
}

// truncates "integer" values: "3.000000" -> "3"
const string Microtone::getFrequencyValueDescription() {
    auto const f = getFrequencyValue();
    return Microtone::getFrequencyValueDescription(f);
}

const string Microtone::getPitchValueDescription() {
    auto const p = getPitchValue01();
    return WilsonicAppSkin::floatDescription(p, 6);
}

const string Microtone::getCentsValueDescription() {
    auto const p = 1200.f * getPitchValue01();
    return WilsonicAppSkin::floatDescription(p, 2);
}

const string Microtone::getFrequencyValueDescription(float f) {
    auto s = WilsonicAppSkin::floatDescription(f, 3);
    return s;
}

Point<float> Microtone::getGralErvPoint() {
    return _gralErvPoint;
}

void Microtone::setGralErvPoint(Point<float> p) {
    _gralErvPoint = p;
}

Point<float> Microtone::getGralErvPointFinal() {
    return _gralErvPointFinal;
}

void Microtone::setGralErvPointFinal(Point<float> p) {
    _gralErvPointFinal = p;
}

Point<float> Microtone::getGralErvOctaveVector() {
    return _gralErvOctaveVector;
}

void Microtone::setGralErvOctaveVector(Point<float> octave) {
    _gralErvOctaveVector = octave;
}

Point<float> Microtone::getGralHexPoint() {
    return _gralHexPoint;
}

void Microtone::setGralHexPoint(Point<float> p) {
    _gralHexPoint = p;
}

Point<float> Microtone::getGralHexPointFinal() {
    return _gralHexPointFinal;
}

void Microtone::setGralHexPointFinal(Point<float> p) {
    _gralHexPointFinal = p;
}

Point<float> Microtone::getHexOctaveVector() {
    return _gralHexOctaveVector;
}

void Microtone::setHexOctaveVector(Point<float> p) {
    _gralHexOctaveVector = p;
}

Path Microtone::getTouchPointPath() {
    return _touchPointPath;
}

void Microtone::setTouchPointPath(Path t) {
    _touchPointPath = t;
}

void Microtone::setFilterNote(bool doFilter) {
    _doFilter = doFilter;
}

bool Microtone::getFilterNote() {
    return _doFilter;
}

// should render this tone in _paint, default true
void Microtone::setShouldRender(bool shouldRender) {
    _shouldRender = shouldRender;
}

bool Microtone::getShouldRender() {
    return _shouldRender;
}

#pragma mark - methods

void Microtone::updateShortDescriptionText() {
    if(_isRational) {
        ostringstream stringStream;
        if(getDenominator() == 1) {
            stringStream << getNumerator();
        } else {
            stringStream << getNumerator() << "/" << getDenominator();
        }
        _shortDescriptionText = stringStream.str();
    } else {
        _shortDescriptionText = getFrequencyValueDescription();
    }
}

// in-place: uses the period defined upon construction
void Microtone::octaveReduce() {
    octaveReduce(_period);
}

/**
 * @brief In-place octave reduction using a specified period.
 *
 * This function performs an octave reduction on the Microtone object using a specified period.
 * It first checks if the provided period is different from the current period of the Microtone object.
 * If it is, it asserts that the period is within the valid range and then replaces the current period with the provided one.
 *
 * If the Microtone object is rational and the period is non-integer, the function converts the Microtone object to a non-rational one.
 *
 * If the Microtone object is rational, it performs an octave reduction based on the space of the Microtone object.
 * If the Microtone object is not rational, it performs an octave reduction based on the space of the Microtone object.
 *
 * @param period The period to be used for the octave reduction. It should be a float.
 */
void Microtone::octaveReduce(float period) {
    // Replace the current period with the provided one if they are different
    if(WilsonicMath::floatsAreNotEqual(period, _period)) {
        jassert(period >= TuningConstants::minPeriod);
        jassert(period <= TuningConstants::maxPeriod);
        _period = period;
    }

    // Convert the Microtone object to a non-rational one if it is rational and the period is non-integer
    if(_isRational) {
        auto const r = fmodf(_period, 1.f);
        if(r != 0.f) {
            _microtoneNumber = _microtoneRational.floatValue();
            _isRational = false;
        }
    }

    // Perform an octave reduction if the Microtone object is rational
    if(_isRational) {
        // If the period is the minimum period, set the microtone rational to the period and return
        if(WilsonicMath::floatsAreEqual(_period, TuningConstants::minPeriod)) {
            _microtoneRational = Fraction(static_cast<unsigned long>(_period), 1);
            return;
        }

        // Assert that the float value of the microtone rational is valid
        jassert(!std::isnan(_microtoneRational.floatValue()));
        jassert(!std::isinf(_microtoneRational.floatValue()));
        auto one = Fraction(1, 1);
        auto period_r = Fraction(static_cast<unsigned long>(_period), 1); // the fmodf above says this is an int
        
        // Perform an octave reduction based on the space of the Microtone object
        float microtoneValue = _microtoneRational.floatValue();
        if(_space == Space::Linear) {
            jassert(microtoneValue > 0.f);
            while(_microtoneRational.floatValue() >= _period)
                _microtoneRational = _microtoneRational / period_r;
            while(_microtoneRational.floatValue() < 1.f)
                _microtoneRational = _microtoneRational * period_r;
            jassert(_microtoneRational.floatValue() >= 1.f);
            jassert(_microtoneRational.floatValue() < _period);
        } else if(_space == Space::LogPeriod) {
            while(microtoneValue < 1.f)
                microtoneValue += 1.f;
            while(microtoneValue >= 1.f)
                microtoneValue -= 1.f;
            jassert(microtoneValue >= 0.f);
            jassert(microtoneValue < 1.f);
        } else {
            jassertfalse; // error
        }
    } else { // _microtoneNumber (float)
        // If the period is the minimum period, set the microtone number to the period and return
        if(WilsonicMath::floatsAreEqual(_period, TuningConstants::minPeriod)) {
            _microtoneNumber = _period;
            return;
        }

        // Assert that the microtone number is valid
        jassert(!std::isnan(_microtoneNumber));
        jassert(!std::isinf(_microtoneNumber));
        
        // Perform an octave reduction based on the space of the Microtone object
        if(_space == Space::Linear) {
            jassert(_microtoneNumber > 0.0f);
            while(_microtoneNumber < 1.f)
                _microtoneNumber *= _period;
            while(_microtoneNumber >= _period)
                _microtoneNumber /= _period;
            jassert(_microtoneNumber >= 1.f);
            jassert(_microtoneNumber < _period);
        } else if(_space == Space::LogPeriod) {// really Log-base-period
            while(_microtoneNumber < 0.f)
                _microtoneNumber += 1.f;
            _microtoneNumber = fmod(_microtoneNumber, 1.f);
            jassert(_microtoneNumber >= 0.f);
            jassert(_microtoneNumber < 1.f);
        } else {
            jassertfalse; // error
        }
    }
}

/**
 * @brief Checks if the frequency value of the Microtone object is a power of 2.
 *
 * This function is valuable for both octave and non-octave use cases. It asserts that the space of the Microtone object is either Linear or Log2.
 * It retrieves the frequency value of the Microtone object and asserts that it is greater than 0 and is not NaN or infinity.
 * It then calculates the base 2 logarithm of the frequency value and performs a modulo operation with 1.
 * If the result is 0 or 1, it sets the return value to true, indicating that the frequency value is a power of 2.
 *
 * @return A boolean value indicating whether the frequency value of the Microtone object is a power of 2.
 */
bool Microtone::frequencyValueIsPowerOf2() {
    jassert(_space == Space::Linear || _space == Space::LogPeriod);
    auto p = getFrequencyValue();
    jassert(p > 0.f);
    jassert(!std::isnan(p));
    jassert(!std::isinf(p));
    p = log2f(p);
    p = fmodf(p, 1.f);
    return(p == 0.f || p == 1.f);
}

void Microtone::setMidiNoteNumber(unsigned long nn) {
    _midiNoteNumber = nn;
}

unsigned long Microtone::getMidiNoteNumber() {
    return _midiNoteNumber;
}

void Microtone::setMidiRegister(int registerNumber) {
    _midiRegister = registerNumber;
}

int Microtone::getMidiRegister() {
    return _midiRegister;
}

#pragma mark - operators

/**
 * @brief Multiplies the current Microtone object with another Microtone object.
 *
 * If both Microtone objects are rational, it preserves the rational type and multiplies their rational values.
 * Otherwise, it falls back to multiplying their frequency values.
 *
 * @param multipland The Microtone object to multiply with.
 * @return A pointer to the resulting Microtone object.
 */
Microtone_p Microtone::multiply(Microtone_p multipland) {
    // if both are rational preserve rational type
    if(_isRational && multipland->isRational()) {
        Fraction result = _microtoneRational * Fraction(multipland->getNumerator(), multipland->getDenominator() );
        auto retVal = Microtone(result.numerator(), result.denominator(), "", _space, _period);

        return retVal.clone();
    }

    // fall back to float value
    auto result = _microtoneNumber * multipland->getFrequencyValue();
    auto retVal = Microtone(result);

    return retVal.clone();
}

/**
 * @brief Divides the current Microtone object by another Microtone object.
 *
 * If both Microtone objects are rational, it preserves the rational type and divides their rational values.
 * Otherwise, it falls back to dividing their frequency values.
 *
 * @param divisor The Microtone object to divide by.
 * @return A pointer to the resulting Microtone object.
 */
Microtone_p Microtone::divide(Microtone_p divisor) {
    // if both are rational preserve rational type
    if(_isRational && divisor->isRational()) {
        Fraction result = _microtoneRational / Fraction(divisor->getNumerator(), divisor->getDenominator());
        auto retVal = Microtone(result.numerator(), result.denominator(), "", _space, _period);

        return retVal.clone();
    }

    // fall back to float value
    auto result = _microtoneNumber / divisor->getFrequencyValue();
    auto retVal = Microtone(result);

    return retVal.clone();
}

/**
 * @brief Adds another Microtone object to the current Microtone object.
 *
 * If both Microtone objects are rational, it preserves the rational type and adds their rational values.
 * Otherwise, it falls back to adding their frequency values.
 *
 * @param rightHand The Microtone object to add.
 * @return A pointer to the resulting Microtone object.
 */
Microtone_p Microtone::add(Microtone_p rightHand) {
    // if both are rational preserve rational type
    if( _isRational && rightHand->isRational() ) {
        Fraction result = _microtoneRational + Fraction(rightHand->getNumerator(), rightHand->getDenominator() );
        auto retVal = Microtone(result.numerator(), result.denominator(), "", _space, _period);

        return retVal.clone();
    }

    // else fall back to float value
    auto result = _microtoneNumber + rightHand->getFrequencyValue();
    auto retVal = Microtone(result);

    return retVal.clone();
}

/**
 * @brief Subtracts another Microtone object from the current Microtone object.
 *
 * If both Microtone objects are rational, it preserves the rational type and subtracts their rational values.
 * Otherwise, it falls back to subtracting their frequency values.
 *
 * @param term The Microtone object to subtract.
 * @return A pointer to the resulting Microtone object.
 */
Microtone_p Microtone::subtract(Microtone_p term) {
    // if both are rational preserve rational type
    if( _isRational && term->isRational() ) {
        Fraction result = _microtoneRational - Fraction(term->getNumerator(), term->getDenominator() );
        auto retVal = Microtone(result.numerator(), result.denominator(), "", _space, _period);

        return retVal.clone();
    }

    // else fall back to float value
    auto result = _microtoneNumber - term->getFrequencyValue();
    auto retVal = Microtone(result);

    return retVal.clone();
}

/**
 * @brief Calculates the freshman sum of two Microtone objects.
 *
 * The freshman sum is the sum of the numerators over the sum of the denominators.
 * This function asserts that both Microtone objects are rational.
 *
 * @param left The first Microtone object.
 * @param right The second Microtone object.
 * @return A pointer to the resulting Microtone object.
 */
Microtone_p Microtone::freshmanSum(Microtone_p left, Microtone_p right) {
    jassert(left->isRational() && right->isRational());
    auto const numerator = left->getNumerator() + right->getNumerator();
    auto const denominator = left->getDenominator() + right->getDenominator();

    return Microtone(numerator, denominator).clone();
}


#pragma mark - print

ostream& operator << (ostream& os, Microtone_p m) {
    os << m->getShortDescriptionText();
    return os;
}

