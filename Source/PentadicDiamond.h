/*
 ==============================================================================

 PentadicDiamond.h
 Created: 6 Jun 2023 4:32:22pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#pragma once

#include "Seed5.h"
#include "Pentad.h"

// Pentadic Diamond
// D'Alessandro, Like A Hurricane, Erv Wilson, (c) 1989

class PentadicDiamond 
: public Seed5
{
public:
    // lifecycle
    PentadicDiamond(Microtone_p A, Microtone_p B, Microtone_p C, Microtone_p D, Microtone_p E);
    PentadicDiamond(vector<Microtone_p> master_set, vector<Microtone_p> common_tones);
    ~PentadicDiamond() override;

    // public member functions
    void update() override;
    bool canPaintTuning() override;
    const string getShortDescriptionText();
    bool isEulerGenusTuningType() override;

    // select subsets
    void selectS0_0() override;
    void selectS0_1() override;
    void selectS0_2() override;
    void selectS0_3() override;
    void selectS0_4() override;
    void selectS0_5() override;
    void selectS0_6() override;
    void selectS0_7() override;
    void selectS1_0() override;
    void selectS1_1() override;
    void selectS1_2() override;
    void selectS1_3() override;
    void selectS1_4() override;
    void selectS1_5() override;
    void selectS1_6() override;
    void selectS1_7() override;

private:
    CPSMicrotone _A_B;
    CPSMicrotone _A_C;
    CPSMicrotone _A_D;
    CPSMicrotone _A_E;
    CPSMicrotone _B_A;
    CPSMicrotone _B_C;
    CPSMicrotone _B_D;
    CPSMicrotone _B_E;
    CPSMicrotone _C_A;
    CPSMicrotone _C_B;
    CPSMicrotone _C_D;
    CPSMicrotone _C_E;
    CPSMicrotone _D_A;
    CPSMicrotone _D_B;
    CPSMicrotone _D_C;
    CPSMicrotone _D_E;
    CPSMicrotone _E_A;
    CPSMicrotone _E_B;
    CPSMicrotone _E_C;
    CPSMicrotone _E_D;
    CPSMicrotone _one;
    shared_ptr<Pentad> _harmonic_subset_0;
    shared_ptr<Pentad> _harmonic_subset_1;
    shared_ptr<Pentad> _harmonic_subset_2;
    shared_ptr<Pentad> _harmonic_subset_3;
    shared_ptr<Pentad> _harmonic_subset_4;
    shared_ptr<Pentad> _subharmonic_subset_0;
    shared_ptr<Pentad> _subharmonic_subset_1;
    shared_ptr<Pentad> _subharmonic_subset_2;
    shared_ptr<Pentad> _subharmonic_subset_3;
    shared_ptr<Pentad> _subharmonic_subset_4;

    // private member functions
    void _allocateSubsets() override;
    void _commonConstructorHelper(); // called only at construction
};
