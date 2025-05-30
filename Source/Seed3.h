/*
 ==============================================================================

 Seed3.h
 Created: 15 Aug 2021 12:03:35pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#pragma once

#include "CPSTuningBase.h"
#include "Microtone.h"

class Seed3 
: public CPSTuningBase
{
public:
    // lifecycle
    Seed3();
    Seed3(Microtone_p A, Microtone_p B, Microtone_p C);
    Seed3(vector<Microtone_p> master_set, vector<Microtone_p> common_tones);
    ~Seed3() override;

    // member functions
    void set(vector<Microtone_p> master_set, vector<Microtone_p> common_tones) override;
    void setA(Microtone_p A);
    void setA(float a);
    const Microtone_p getA();
    void setB(Microtone_p B);
    void setB(float a);
    const Microtone_p getB();
    void setC(Microtone_p C);
    void setC(float a);
    const Microtone_p getC();
    void setABC(Microtone_p A, Microtone_p B, Microtone_p C);
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
    Microtone_p _C;
};
