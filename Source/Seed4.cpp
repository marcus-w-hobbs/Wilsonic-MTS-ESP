/*
  ==============================================================================

    Seed4.cpp
    Created: 15 Aug 2021 12:03:12pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "Seed4.h"

#pragma mark - lifecycle

Seed4::Seed4()
{
    // properties
    setCanUniquify(false);
    setCanSort(true);
    setSort(true);
    setTuningName ("Seed 4");
}

Seed4::Seed4(Microtone_p A, Microtone_p B, Microtone_p C, Microtone_p D)
: Seed4()
{
    _A = A;
    _B = B;
    _C = C;
    _D = D;
}

Seed4::Seed4(vector<Microtone_p> master_set, vector<Microtone_p> common_tones)
: Seed4()
{
    // can't use "set" because it calls update...so duplicate code here
    jassert(master_set.size() == 4);
    _A = master_set[0];
    _B = master_set[1];
    _C = master_set[2];
    _D = master_set[3];
    clearCommonTones();
    for(auto ct : common_tones)
    {
        addCommonTone(ct);
    }
}

#pragma mark - member functions

void Seed4::set(vector<Microtone_p> master_set, vector<Microtone_p> common_tones)
{
    // if you change this code you need to update the constructor
    jassert(master_set.size() >= 4);
    _A = master_set[0];
    _B = master_set[1];
    _C = master_set[2];
    _D = master_set[3];
    clearCommonTones();
    for(auto ct : common_tones)
    {
        addCommonTone(ct);
    }
    update();
}

const vector<Microtone_p> Seed4::getMasterSet()
{
    return vector<Microtone_p> {_A, _B, _C, _D};
}

void Seed4::setA(Microtone_p A)
{
    _A = A;
    update();
}

void Seed4::setA(float f)
{
    _A->setFrequencyValue(f);
    auto fsdt = Microtone::getFrequencyValueDescription(f);
    _A->setShortDescriptionText2(fsdt);
    update();
}

const Microtone_p Seed4::getA()
{
    return _A;
}

void Seed4::setB(Microtone_p B)
{
    _B = B;
    update();
}

void Seed4::setB(float f)
{
    _B->setFrequencyValue(f);
    auto fsdt = Microtone::getFrequencyValueDescription(f);
    _B->setShortDescriptionText2(fsdt);
    update();
}

const Microtone_p Seed4::getB()
{
    return _B;
}

void Seed4::setC(Microtone_p C)
{
    _C = C;
    update();
}

void Seed4::setC(float f)
{
    _C->setFrequencyValue(f);
    auto fsdt = Microtone::getFrequencyValueDescription(f);
    _C->setShortDescriptionText2(fsdt);
    update();
}

const Microtone_p Seed4::getC()
{
    return _C;
}

void Seed4::setD(Microtone_p D)
{
    _D = D;
    update();
}

void Seed4::setD(float f)
{
    _D->setFrequencyValue(f);
    auto fsdt = Microtone::getFrequencyValueDescription(f);
    _D->setShortDescriptionText2(fsdt);
    update();
}

const Microtone_p Seed4::getD()
{
    return _D;
}

void Seed4::setABCD(Microtone_p A, Microtone_p B, Microtone_p C, Microtone_p D)
{
    _A = A;
    _B = B;
    _C = C;
    _D = D;

    update();
}

const string Seed4::getTuningName()
{
    auto basename = TuningImp::getTuningName();
    auto retVal = basename + "(" +
    _A->getFrequencyValueDescription() + "," +
    _B->getFrequencyValueDescription() + "," +
    _C->getFrequencyValueDescription() + "," +
    _D->getFrequencyValueDescription() +
    ")";

    // TODO: fix this

    if(getCommonTones().size() > 0)
    {
        auto t = multiplyByCommonTones(vector<Microtone_p> {});
        retVal += "*" + t->getShortDescriptionText2();
    }

    return retVal;
}

const string Seed4::getTuningNameAsSymbols()
{
    auto basename = TuningImp::getTuningName();
    auto retVal = basename + "(" +
    _A->getShortDescriptionText() + "," +
    _B->getShortDescriptionText() + "," +
    _C->getShortDescriptionText() + "," +
    _D->getShortDescriptionText() +
    ")";

    sort(_commonTones.begin(), _commonTones.end(), less_than_key());
    for(auto ct : _commonTones)
    {
        retVal += "*" + ct->getShortDescriptionText();
    }

    return retVal;
}

const string Seed4::getTuningNameAsUnderscores()
{
    auto basename = TuningImp::getTuningName();
    auto retVal = basename + "_" +
    _A->getShortDescriptionText() + "_" +
    _B->getShortDescriptionText() + "_" +
    _C->getShortDescriptionText() + "_" +
    _D->getShortDescriptionText();
    if(_commonTones.size() > 0)
    {
        retVal += "__X";
    }

    sort(_commonTones.begin(), _commonTones.end(), less_than_key());
    for(auto ct : _commonTones)
    {
        retVal += "_" + ct->getShortDescriptionText();
    }

    return retVal;
}

const string Seed4::getTuningCreationCodegen(string parent_key, vector<string> s0_keys, vector<string> s1_keys)
{
    // common tones
    string ctstr = "";
    if(_commonTones.size() > 0)
    {
        ctstr = "{";
        sort(_commonTones.begin(), _commonTones.end(), less_than_key());
        for(auto ct : _commonTones)
        {
            ctstr += "_" + ct->getShortDescriptionText() + ",";
        }
        ctstr.pop_back(); // remove last ","
        ctstr += "}";
    }
    else
    {
        ctstr = "{}";
    }

    // s0
    string s0str = "";
    if(s0_keys.size() > 0)
    {
        s0str = "{";
        for(auto ct : s0_keys)
        {
            s0str += "\"" + ct + "\"" + ",";
        }
        s0str.pop_back(); // remove last ","
        s0str += "}";
    }
    else
    {
        s0str = "{}";
    }

    // s1
    string s1str = "";
    if(s1_keys.size() > 0)
    {
        s1str = "{";
        for(auto ct : s1_keys)
        {
            s1str += "\"" + ct + "\"" + ",";
        }
        s1str.pop_back(); // remove last ","
        s1str += "}";
    }
    else
    {
        s1str = "{}";
    }

    auto a = _A->getShortDescriptionText();
    auto b = _B->getShortDescriptionText();
    auto c = _C->getShortDescriptionText();
    auto d = _D->getShortDescriptionText();

    //shared_ptr<CPSTuningBase> _create_tuning (
    //CPS_Class tuning_class_name,
    //vector<Microtone_p> master_set,
    //vector<Microtone_p>,
    //common_terms,
    //string parent_key,
    //vector<string> s0_keys,
    //vector<string> s1_keys);

    // tuning class
    string tuning_class_name = TuningImp::getTuningName();
    string retVal = "[this](){ return _create_tuning(CPS_Class::" + tuning_class_name + ", ";

    // master set
    retVal += "{_" + a + ",_" + b + ",_" + c + ",_" + d + "},";

    // common tones {}
    retVal += ctstr + ", ";

    // parent daw key
    retVal += "\"" + parent_key + "\", ";

    // s0 daw keys
    retVal += s0str + ", ";

    // s1 daw keys
    retVal += s1str;

    //
    retVal +=  + ");}";
    return retVal;
}

// used by codegen to create the string used to update this type of tuning:
//    cps->set ({_A,_B,_C,_D}, {_E,_F});
const string Seed4::getTuningUpdateCodegen()
{
    string ctstr = "";
    //bool hasCommonTones = false;
    if(_commonTones.size() > 0)
    {
        //hasCommonTones = true;
        ctstr = "{";
        sort(_commonTones.begin(), _commonTones.end(), less_than_key());
        for(auto ct : _commonTones)
        {
            ctstr += "_" + ct->getShortDescriptionText() + ",";
        }
        ctstr.pop_back(); // remove last ","
        ctstr += "}";
    }
    else
    {
        ctstr = "{}";
    }

    auto a = _A->getShortDescriptionText();
    auto b = _B->getShortDescriptionText();
    auto c = _C->getShortDescriptionText();
    auto d = _D->getShortDescriptionText();

    string retVal = "cps->set ({_" + a + ",_" + b + ",_" + c + ",_" + d + "}," + ctstr + ");";

    return retVal;
}
