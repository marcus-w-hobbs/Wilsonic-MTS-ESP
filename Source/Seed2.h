/*
  ==============================================================================

    Seed2.h
    Created: 15 Aug 2021 12:03:51pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include "CPSTuningBase.h"
#include "Microtone.h"

class Seed2 
: public CPSTuningBase
{

public:
    // lifecycle
    Seed2();
    Seed2(Microtone_p A, Microtone_p B);
    Seed2(vector<Microtone_p> master_set, vector<Microtone_p> common_tones);
    ~Seed2() override;

    // member functions
    void set(vector<Microtone_p> master_set, vector<Microtone_p> common_tones) override;
    void setA(Microtone_p A);
    void setA(float a);
    const Microtone_p getA();
    void setB(Microtone_p B);
    void setB(float a);
    const Microtone_p getB();
    void setAB(Microtone_p A, Microtone_p B);
    const vector<Microtone_p> getMasterSet() override;
    const string getTuningName() override;
    const string getTuningNameAsSymbols() override;
    const string getTuningNameAsUnderscores() override;
    const string getTuningCreationCodegen(string, vector<string>, vector<string>) override;
    const string getTuningUpdateCodegen() override;

protected:
    // properties
    Microtone_p _A;
    Microtone_p _B;
};
