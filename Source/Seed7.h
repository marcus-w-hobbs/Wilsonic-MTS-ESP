/*
  ==============================================================================

    Seed7.h
    Created: 6 Jun 2023 4:09:56pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include "CPSTuningBase.h"
#include "Microtone.h"

class Seed7 
: public CPSTuningBase
{
public:
    // lifecycle
    Seed7();
    Seed7(Microtone_p A, Microtone_p B, Microtone_p C, Microtone_p D, Microtone_p E, Microtone_p F, Microtone_p G);
    Seed7(vector<Microtone_p> master_set, vector<Microtone_p> common_tones);
    ~Seed7() override;

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
    void setD(Microtone_p D);
    void setD(float a);
    const Microtone_p getD();
    void setE(Microtone_p E);
    void setE(float a);
    const Microtone_p getE();
    void setF(Microtone_p F);
    void setF(float a);
    const Microtone_p getF();
    void setG(Microtone_p G);
    void setG(float a);
    const Microtone_p getG();
    void setABCDEFG(Microtone_p A, Microtone_p B, Microtone_p C, Microtone_p D, Microtone_p E, Microtone_p F, Microtone_p G);
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
    Microtone_p _D;
    Microtone_p _E;
    Microtone_p _F;
    Microtone_p _G;
};
