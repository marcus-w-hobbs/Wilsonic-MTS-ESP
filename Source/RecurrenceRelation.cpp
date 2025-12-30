/*
 ==============================================================================

 RecurrenceRelation.cpp
 Created: 21 Mar 2022 8:45:37pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "RecurrenceRelation.h"
#include "Microtone.h"
#include "WilsonicProcessor.h"

#pragma mark - static members

// __indices and __indicesDescription must contain identical entries,
// and should never change after release or automation will break

vector<RecurrenceRelation::IndexTuple> RecurrenceRelation::__indices =
{
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 2]", 1, 2),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 3]", 1, 3),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 4]", 1, 4),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 5]", 1, 5),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 6]", 1, 6),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 7]", 1, 7),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 8]", 1, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 1] + H[n - 9]", 1, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 3]", 2, 3),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 4]", 2, 4),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 5]", 2, 5),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 6]", 2, 6),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 7]", 2, 7),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 8]", 2, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 2] + H[n - 9]", 2, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 3] + H[n - 4]", 3, 4),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 3] + H[n - 5]", 3, 5),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 3] + H[n - 6]", 3, 6),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 3] + H[n - 7]", 3, 7),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 3] + H[n - 8]", 3, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 3] + H[n - 9]", 3, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 4] + H[n - 5]", 4, 5),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 4] + H[n - 6]", 4, 6),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 4] + H[n - 7]", 4, 7),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 4] + H[n - 8]", 4, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 4] + H[n - 9]", 4, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 5] + H[n - 6]", 5, 6),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 5] + H[n - 7]", 5, 7),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 5] + H[n - 8]", 5, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 5] + H[n - 9]", 5, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 6] + H[n - 7]", 6, 7),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 6] + H[n - 8]", 6, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 6] + H[n - 9]", 6, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 7] + H[n - 8]", 7, 8),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 7] + H[n - 9]", 7, 9),
    make_tuple<String, unsigned long, unsigned long>("H[n] = H[n - 8] + H[n - 9]", 8, 9),
};

// __indices and __indicesDescription must contain identical entries,
// and should never change after release or automation will break

StringArray RecurrenceRelation::__indicesDescription =
{
    "H[n] = H[n - 1] + H[n - 2]",
    "H[n] = H[n - 1] + H[n - 3]",
    "H[n] = H[n - 1] + H[n - 4]",
    "H[n] = H[n - 1] + H[n - 5]",
    "H[n] = H[n - 1] + H[n - 6]",
    "H[n] = H[n - 1] + H[n - 7]",
    "H[n] = H[n - 1] + H[n - 8]",
    "H[n] = H[n - 1] + H[n - 9]",
    "H[n] = H[n - 2] + H[n - 3]",
    "H[n] = H[n - 2] + H[n - 4]",
    "H[n] = H[n - 2] + H[n - 5]",
    "H[n] = H[n - 2] + H[n - 6]",
    "H[n] = H[n - 2] + H[n - 7]",
    "H[n] = H[n - 2] + H[n - 8]",
    "H[n] = H[n - 2] + H[n - 9]",
    "H[n] = H[n - 3] + H[n - 4]",
    "H[n] = H[n - 3] + H[n - 5]",
    "H[n] = H[n - 3] + H[n - 6]",
    "H[n] = H[n - 3] + H[n - 7]",
    "H[n] = H[n - 3] + H[n - 8]",
    "H[n] = H[n - 3] + H[n - 9]",
    "H[n] = H[n - 4] + H[n - 5]",
    "H[n] = H[n - 4] + H[n - 6]",
    "H[n] = H[n - 4] + H[n - 7]",
    "H[n] = H[n - 4] + H[n - 8]",
    "H[n] = H[n - 4] + H[n - 9]",
    "H[n] = H[n - 5] + H[n - 6]",
    "H[n] = H[n - 5] + H[n - 7]",
    "H[n] = H[n - 5] + H[n - 8]",
    "H[n] = H[n - 5] + H[n - 9]",
    "H[n] = H[n - 6] + H[n - 7]",
    "H[n] = H[n - 6] + H[n - 8]",
    "H[n] = H[n - 6] + H[n - 9]",
    "H[n] = H[n - 7] + H[n - 8]",
    "H[n] = H[n - 7] + H[n - 9]",
    "H[n] = H[n - 8] + H[n - 9]"
};

// __coefficients and __coefficientsDescription must contain identical entries,
// and should never change after release or automation will break

vector<RecurrenceRelation::CoefficientTuple> RecurrenceRelation::__coefficients =
{
    make_tuple<String, float>("1/8", 1.f/8),
    make_tuple<String, float>("1/4", 1.f/4),
    make_tuple<String, float>("1/2", 1.f/2),
    make_tuple<String, float>("1", 1.f),
    make_tuple<String, float>("2", 2.f),
    make_tuple<String, float>("4", 4.f),
    make_tuple<String, float>("8", 8.f),
};

StringArray RecurrenceRelation::__coefficientsDescription =
{
    "1/8",
    "1/4",
    "1/2",
    " 1 ",
    " 2 ",
    " 4 ",
    " 8 "
};

unordered_map<RecurrenceRelation::Coefficient, string> RecurrenceRelation::__coefficientsDescriptionMap {
    {RecurrenceRelation::Coefficient::_1_8, "(1/8)"},
    {RecurrenceRelation::Coefficient::_1_4, "(1/4)"},
    {RecurrenceRelation::Coefficient::_1_2, "(1/2)"},
    {RecurrenceRelation::Coefficient::_1  , ""     },
    {RecurrenceRelation::Coefficient::_2  , "2"    },
    {RecurrenceRelation::Coefficient::_4  , "4"    },
    {RecurrenceRelation::Coefficient::_8  , "8"    }
};

StringArray RecurrenceRelation::__sumTypeDescription = {
    "Arithmetic",
    "Harmonic"
};

StringArray RecurrenceRelation::__seedSpaceDescription = {
    "Frequency",
    "Period"
};

#pragma mark - lifecycle

RecurrenceRelation::RecurrenceRelation()
{
    // properties
    setCanNPOOverride(true);
    setCanUniquify(true); // static and defined as unique
    setCanSort(true); // static and defined as sorted
    setSort(true);

    // seed defaults
    for(auto i = 1; i < 10; i++)
    {
        _seeds.addMicrotone(make_shared<Microtone>(1.f, "", Microtone::Space::Linear, TuningConstants::defaultPeriod));
    }
    setSeeds(1, 1, 1, 1, 1, 1, 1, 1, 1);// calls _updateRecurrenceRelation()

    // coefficients
    auto const c = Coefficient::_1;
    setCoefficients(c, c, c, c, c, c, c, c, c); // calls _updateRecurrenceRelation()

    // default
    setIndices(0); // calls _updateRecurrenceRelation()
}

RecurrenceRelation::~RecurrenceRelation()
{

}

#pragma mark - drawing

bool RecurrenceRelation::canPaintTuning()
{
    return false;
}

void RecurrenceRelation::paint(WilsonicProcessor& , Graphics& , Rectangle<int> )
{
    // not used
}

#pragma mark - Scala

String RecurrenceRelation::defaultScalaName()
{
    return "recurrence_relation.scl"; // too complex to embed params in filename
}

String RecurrenceRelation::scalaComments()
{
    return String(getLog());
}

#pragma mark - update

void RecurrenceRelation::setIndices(unsigned long indices)
{
    jassert(indices < __indices.size());
    const ScopedLock sl(_lock);

    _indices = indices;
    auto const index = __indices[_indices];
    _i = get<1>(index);
    _j = get<2>(index);

    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getIndices()
{
    return _indices;
}

// 1 <= I, I < J, I <= 8
unsigned long RecurrenceRelation::getIndexI()
{
    return _i;
}

// 2 <= J, J > I, J <= 9
unsigned long RecurrenceRelation::getIndexJ()
{
    return _j;
}

void RecurrenceRelation::setSeeds(float s1, float s2, float s3, float s4, float s5, float s6, float s7, float s8, float s9)
{
    jassert(s1 >= getSeedMin() && s1 <= getSeedMax() &&
            s2 >= getSeedMin() && s2 <= getSeedMax() &&
            s3 >= getSeedMin() && s3 <= getSeedMax() &&
            s4 >= getSeedMin() && s4 <= getSeedMax() &&
            s5 >= getSeedMin() && s5 <= getSeedMax() &&
            s6 >= getSeedMin() && s6 <= getSeedMax() &&
            s7 >= getSeedMin() && s7 <= getSeedMax() &&
            s8 >= getSeedMin() && s8 <= getSeedMax() &&
            s9 >= getSeedMin() && s9 <= getSeedMax()    );
    const ScopedLock sl(_lock);
    auto m1 = _microtoneArray.microtoneAtIndex(0); m1->setFrequencyValue(s1); m1->updateShortDescriptionText();
    auto m2 = _microtoneArray.microtoneAtIndex(1); m2->setFrequencyValue(s2); m2->updateShortDescriptionText();
    auto m3 = _microtoneArray.microtoneAtIndex(2); m3->setFrequencyValue(s3); m3->updateShortDescriptionText();
    auto m4 = _microtoneArray.microtoneAtIndex(3); m4->setFrequencyValue(s4); m4->updateShortDescriptionText();
    auto m5 = _microtoneArray.microtoneAtIndex(4); m5->setFrequencyValue(s5); m5->updateShortDescriptionText();
    auto m6 = _microtoneArray.microtoneAtIndex(5); m6->setFrequencyValue(s6); m6->updateShortDescriptionText();
    auto m7 = _microtoneArray.microtoneAtIndex(6); m7->setFrequencyValue(s7); m7->updateShortDescriptionText();
    auto m8 = _microtoneArray.microtoneAtIndex(7); m8->setFrequencyValue(s8); m8->updateShortDescriptionText();
    auto m9 = _microtoneArray.microtoneAtIndex(8); m9->setFrequencyValue(s9); m9->updateShortDescriptionText();
    _updateRecurrenceRelation();
}

// index is 1-9, not 0-8
void RecurrenceRelation::setSeed(float s, unsigned long i_1_9)
{
    jassert(i_1_9 > 0 && i_1_9 < 10);
    jassert(s >= getSeedMin() && s <= getSeedMax());
    const ScopedLock sl(_lock);
    auto mt = _seeds.microtoneAtIndex(i_1_9 - 1);
    mt->setFrequencyValue(s); mt->updateShortDescriptionText();
    _updateRecurrenceRelation();
}

float RecurrenceRelation::getSeed(unsigned long i_1_9)
{
    jassert(i_1_9 > 0 && i_1_9 < 10);
    const ScopedLock sl(_lock);
    auto m = _seeds.microtoneAtIndex(i_1_9 - 1);
    return m->getFrequencyValue();
}

void RecurrenceRelation::setCoefficients(Coefficient c1, Coefficient c2, Coefficient c3, Coefficient c4, Coefficient c5, Coefficient c6, Coefficient c7, Coefficient c8, Coefficient c9)
{
    const ScopedLock sl(_lock);
    _coefficients[0] = c1;
    _coefficients[1] = c2;
    _coefficients[2] = c3;
    _coefficients[3] = c4;
    _coefficients[4] = c5;
    _coefficients[5] = c6;
    _coefficients[6] = c7;
    _coefficients[7] = c8;
    _coefficients[8] = c9;
    _updateRecurrenceRelation();
}

// index is 1-9, not 0-8
void RecurrenceRelation::setCoefficient(Coefficient c, unsigned long i_1_9)
{
    jassert(i_1_9 > 0 && i_1_9 < 10);
    const ScopedLock sl(_lock);
    _coefficients[i_1_9 - 1] = c;
    _updateRecurrenceRelation();
}

// supports automation by DAWs 
void RecurrenceRelation::setCoefficientByIndex(unsigned long ci, unsigned long i_1_9)
{
    jassert(ci >= 0 && ci < static_cast<unsigned long>(__coefficientsDescription.size()));
    jassert(i_1_9 > 0 && i_1_9 < 10);
    auto c = Coefficient::_1;
    switch(ci)
    {
        case 0:
            c = Coefficient::_1_8;
            break;
        case 1:
            c = Coefficient::_1_4;
            break;
        case 2:
            c = Coefficient::_1_2;
            break;
        case 3:
            c = Coefficient::_1;
            break;
        case 4:
            c = Coefficient::_2;
            break;
        case 5:
            c = Coefficient::_4;
            break;
        case 6:
            c = Coefficient::_8;
            break;
        default:
            jassertfalse;
            break;
    }
    _coefficients[i_1_9 - 1] = c;
    _updateRecurrenceRelation();
}

RecurrenceRelation::Coefficient RecurrenceRelation::getCoefficient(unsigned long i_1_9)
{
    jassert(i_1_9 > 0 && i_1_9 < 10);
    return _coefficients[i_1_9 - 1];
}

float RecurrenceRelation::getCoefficientValue(unsigned long i_1_9)
{
    jassert(i_1_9 > 0 && i_1_9 < 10);
    const ScopedLock sl(_lock);
    auto c = getCoefficient(i_1_9);
    return getValueForCoefficient(c);
}

float RecurrenceRelation::getValueForCoefficient(Coefficient c)
{
    switch(c)
    {
        case Coefficient::_1_8:
            return 1.f/8;
            break;
        case Coefficient::_1_4:
            return 1.f/4;
            break;
        case Coefficient::_1_2:
            return 1.f/2;
            break;
        case Coefficient::_1:
            return 1.f;
            break;
        case Coefficient::_2:
            return 2.f;
            break;
        case Coefficient::_4:
            return 4.f;
            break;
        case Coefficient::_8:
            return 8.f;
            break;
        default:
            jassertfalse;
            break;
    }
}

void RecurrenceRelation::setNumberOfTerms(unsigned long num_terms)
{
    jassert(num_terms >= RecurrenceRelation::getNumberOfTermsMin());
    jassert(num_terms <= RecurrenceRelation::getNumberOfTermsMax());
    const ScopedLock sl(_lock);
    _numberOfTerms = num_terms;
    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getNumberOfTerms()
{
    const ScopedLock sl(_lock);
    return _numberOfTerms;
}

void RecurrenceRelation::setOffset(unsigned long offset)
{
    jassert(offset >= RecurrenceRelation::getOffsetMin());
    jassert(offset <= RecurrenceRelation::getOffsetMax());
    const ScopedLock sl(_lock);
    _offset = offset;
    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getOffset()
{
    const ScopedLock sl(_lock);
    return _offset;
}

const string RecurrenceRelation::getLog()
{
    return _log;
}

// block will be called if the series diverges...can be used to update UI
void RecurrenceRelation::setOnDivergence(function<void()> completionBlock)
{
    _divergenceCompletionBlock = completionBlock;
}

#pragma mark - Sum Type

void RecurrenceRelation::setSumType(SumType sumType)
{
    const ScopedLock sl(_lock);
    _sumType = sumType;
    _updateRecurrenceRelation();
}

RecurrenceRelation::SumType RecurrenceRelation::getSumType()
{
    return _sumType;
}

void RecurrenceRelation::setSumTypeByIndex(unsigned long index)
{
    jassert(index < 2);
    const ScopedLock sl(_lock);
    _sumType = static_cast<SumType>(index);
    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getSumTypeIndex()
{
    return static_cast<unsigned long>(_sumType);
}

#pragma mark - Seed Space

void RecurrenceRelation::setSeedSpace(SeedSpace seedSpace)
{
    const ScopedLock sl(_lock);
    _seedSpace = seedSpace;
    _updateRecurrenceRelation();
}

RecurrenceRelation::SeedSpace RecurrenceRelation::getSeedSpace()
{
    return _seedSpace;
}

void RecurrenceRelation::setSeedSpaceByIndex(unsigned long index)
{
    jassert(index < 2);
    const ScopedLock sl(_lock);
    _seedSpace = static_cast<SeedSpace>(index);
    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getSeedSpaceIndex()
{
    return static_cast<unsigned long>(_seedSpace);
}

// note the _log doubles as the scalaComments, so preprend "! " to each newline
void RecurrenceRelation::_updateRecurrenceRelation()
{
    // lock
    const ScopedLock sl(_lock);

    // lambda for filtering
    auto reap = [this](MicrotoneArray field)
    {
        if(field.count() == 0)
            return field;

        auto retVal = MicrotoneArray(field); // copy
        retVal = retVal.octaveReduce(getOctave());
        retVal = retVal.sort();
        retVal = retVal.uniquify();
        return retVal;
    };

    // working variables
    auto raw_ma      = MicrotoneArray(); // init with seeds to term, then accumulates a new term every iteration
    auto filtered_ma = MicrotoneArray(); // filters raw_ma(octave reduce, sort, uniquify) every iteration
    auto final_ma    = MicrotoneArray(); // takes final slice(offset, num_terms) of filtered_ma, then does final filter
    auto log_final_scale = [this](MicrotoneArray ma)
    {
        _log += "\n!\n! Final Scale:\n!  ";
        for(unsigned long ii = 0; ii < ma.count(); ii++)
        {
            auto mt = ma.microtoneAtIndex(ii);
            _log += mt->getShortDescriptionText();
            if(ii != ma.count() - 1)
            {
                _log += ", ";
            }
        }
        _log += "\n! ";
    };

    // init _log with sum type indicator
    string sumOp = (_sumType == SumType::Arithmetic) ? " + " : " @ ";  // @ = harmonic sum
    _log = "! H[n] = ";
    if(_coefficients[_i - 1] == Coefficient::_1)
    {
        _log += "H[n-";
    }
    else
    {
        auto c = _coefficients[_i - 1];
        _log += __coefficientsDescriptionMap[c];
        _log += " * H[n-";
    }
    _log += to_string(_i);
    _log += "]";
    _log += sumOp;
    if(_coefficients[_j - 1] == Coefficient::_1)
    {
        _log += "H[n-";
    }
    else
    {
        auto c = _coefficients[_j - 1];
        _log += __coefficientsDescriptionMap[c];
        _log += " * H[n-";
    }
    _log += to_string(_j);
    _log += "]";

    // Add mode info
    _log += (_sumType == SumType::Arithmetic) ? " [Arithmetic" : " [Harmonic";
    _log += (_seedSpace == SeedSpace::Frequency) ? ", Freq Seeds]" : ", Period Seeds]";
    _log += "\n! \n! Integer Sequence, including seeds:\n!  ";

    // plant seeds (seeds are the initial conditions so don't use coefficients)
    // Apply seed space transformation if needed
    for(auto j = _j; j > 0; j--) // _j > _i > 0
    {
        auto seed = _seeds.microtoneAtIndex(j - 1);
        auto seedValue = seed->getFrequencyValue();

        // Transform seed if in Period space (invert)
        if (_seedSpace == SeedSpace::Period && seedValue > 0.f)
        {
            seedValue = 1.f / seedValue;
        }

        // Create transformed seed for the working array
        auto transformedSeed = make_shared<Microtone>(seedValue);
        raw_ma.addMicrotone(transformedSeed);
        _log += transformedSeed->getFrequencyValueDescription();

        // filtering initial seeds lets you do cool things
        filtered_ma = reap(raw_ma);
        final_ma = MicrotoneArray(filtered_ma); // copy
        final_ma = final_ma.subarrayWithRange(_offset, _numberOfTerms);
        final_ma = final_ma.octaveReduce(getOctave());
        final_ma = final_ma.sort();
        final_ma = final_ma.uniquify();
        auto const numTerms = final_ma.count();
        if(numTerms >= _numberOfTerms)
        {
            // calls super update
            log_final_scale(final_ma);
            setMicrotoneArray(final_ma);
            return;
        }
        else
        {
            if(j > 0)
            {
                _log += ", ";
            }
        }
    }

    // if you made it here then _numberOfTerms >= _j << check

    // now that raw_ma has the seeds, iterate the recurrence relation(grow raw_ma and filter)
    auto num_iterations = 0;
    auto index = static_cast<unsigned long>(raw_ma.count());
    for(num_iterations = 0; num_iterations < __maxNumUpdateIterations; num_iterations++)
    {
        auto const i   = index - _i;
        auto const j   = index - _j;
        auto const ci  = getValueForCoefficient(_coefficients[_i - 1]);
        auto const cj  = getValueForCoefficient(_coefficients[_j - 1]);
        auto const mti = raw_ma.microtoneAtIndex(i);
        auto const mtj = raw_ma.microtoneAtIndex(j);

        // Calculate next term based on sum type
        auto const a = ci * mti->getFrequencyValue();
        auto const b = cj * mtj->getFrequencyValue();
        float f;
        if (_sumType == SumType::Arithmetic)
        {
            // Standard arithmetic sum: a + b
            f = a + b;
        }
        else // SumType::Harmonic
        {
            // Harmonic sum: ab/(a+b) — the parallel resistance formula
            auto const sum = a + b;
            f = (sum > 1e-10f) ? (a * b) / sum : 0.f;
        }
        if(std::isnan(f) || std::isinf(f) || f < 0)
        {
            _log += "\n! \n! Sequence did not converge.\n";
            if(_divergenceCompletionBlock != nullptr)
            {
                _divergenceCompletionBlock();
                return;
            }
            else
            {
                jassertfalse;
            }
        }
        auto const mtf = make_shared<Microtone>(f);
        raw_ma.addMicrotone(mtf);
        _log += mtf->getFrequencyValueDescription();

        filtered_ma = reap(raw_ma);
        final_ma = MicrotoneArray(filtered_ma); // copy
        final_ma = final_ma.subarrayWithRange(_offset, _numberOfTerms);
        final_ma = final_ma.octaveReduce(getOctave());
        final_ma = final_ma.sort();
        final_ma = final_ma.uniquify();
        auto const numTerms = final_ma.count();
        if(numTerms >= _numberOfTerms)
        {
            break;
        }
        else
        {
            _log += ", ";
        }

        index++;
    }

    if(num_iterations >= __maxNumUpdateIterations)
    {
        _log += "\n! \n! Sequence did not converge.\n";
        if(_divergenceCompletionBlock != nullptr)
        {
            _divergenceCompletionBlock();
            return;
        }
        else
        {
            jassertfalse;
        }
    }
    else
    {
        if(raw_ma.count() > 1)
        {
            raw_ma = raw_ma.sort();
            auto const mt1 = raw_ma.microtoneAtIndex(raw_ma.count()-1);
            auto const mt2 = raw_ma.microtoneAtIndex(raw_ma.count()-2);
            auto const f1 = mt1->getFrequencyValue();
            auto const f2 = mt2->getFrequencyValue();
            auto const f =(f1 > f2) ? f1/f2 : f2/f1;
            auto const p = log2f(f);
            _log += "\n! \n! Sequence converges to: \n!  Ratio = ";
            _log += to_string(f);
            if (_sumType == SumType::Harmonic)
            {
                _log += " (1/phi for Fibonacci)";
            }
            _log += "\n!  Generator = ";
            _log += to_string(p);
        }
    }

    //
    log_final_scale(final_ma);

    // calls super update
    setMicrotoneArray(final_ma);
}

