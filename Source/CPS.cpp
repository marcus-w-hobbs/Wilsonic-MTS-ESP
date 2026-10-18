/*
 ==============================================================================
 
 CPS.cpp
 Created: 8 Aug 2021 9:48:43am
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include <algorithm>
#include "CPS.h"
#include "TuningConstants.h"

#pragma mark - static

CPSTuningClassMap CPS::__cpsTuningClassMap =
{
    {CPS_Class::CPS_1_1,         "CPS_1_1"},
    
    {CPS_Class::CPS_2_1,         "CPS_2_1"},
    {CPS_Class::CPS_2_2,         "CPS_2_2"},
    
    {CPS_Class::CPS_3_1,         "CPS_3_1"},
    {CPS_Class::Triad,           "Triad"},
    {CPS_Class::CPS_3_2,         "CPS_3_2"},
    {CPS_Class::CPS_3_3,         "CPS_3_3"},
    {CPS_Class::TriadicDiamond,  "TriadicDiamond"},
    
    {CPS_Class::CPS_4_1,         "CPS_4_1"},
    {CPS_Class::Tetrad,          "Tetrad"},
    {CPS_Class::CPS_4_2,         "CPS_4_2"},
    {CPS_Class::CPS_4_3,         "CPS_4_3"},
    {CPS_Class::CPS_4_4,         "CPS_4_4"},
    {CPS_Class::TetradicDiamond, "TetradicDiamond"},
    {CPS_Class::Mandala,         "Mandala"},
    
    {CPS_Class::CPS_5_1,         "CPS_5_1"},
    {CPS_Class::Pentad,          "Pentad"},
    {CPS_Class::CPS_5_2,         "CPS_5_2"},
    {CPS_Class::CPS_5_3,         "CPS_5_3"},
    {CPS_Class::CPS_5_4,         "CPS_5_4"},
    {CPS_Class::CPS_5_5,         "CPS_5_5"},
    {CPS_Class::PentadicDiamond, "PentadicDiamond"},
    
    {CPS_Class::CPS_6_1,         "CPS_6_1"},
    {CPS_Class::Hexad,           "Hexad"},
    {CPS_Class::CPS_6_2,         "CPS_6_2"},
    {CPS_Class::CPS_6_3,         "CPS_6_3"},
    {CPS_Class::CPS_6_4,         "CPS_6_4"},
    {CPS_Class::CPS_6_5,         "CPS_6_5"},
    {CPS_Class::CPS_6_6,         "CPS_6_6"},
    {CPS_Class::HexadicDiamond,  "HexadicDiamond"},
    
    {CPS_Class::CPS_7_1,         "CPS_7_1"},
    {CPS_Class::Heptad,          "Heptad"},
    {CPS_Class::HeptadicDiamond, "HeptadicDiamond"},
    
    {CPS_Class::CPS_8_1,         "CPS_8_1"},
    {CPS_Class::Ogdoad,           "Ogdoad"},
    {CPS_Class::OgdoadicDiamond, "OgdoadicDiamond"},
    
    {CPS_Class::EulerGenus_1,    "EulerGenus_1"},
    {CPS_Class::EulerGenus_2,    "EulerGenus_2"},
    {CPS_Class::EulerGenus_3,    "EulerGenus_3"},
    {CPS_Class::EulerGenus_4,    "EulerGenus_4"},
    {CPS_Class::EulerGenus_5,    "EulerGenus_5"},
    {CPS_Class::EulerGenus_6,    "EulerGenus_6"},
    
    {CPS_Class::UNDEFINED,       "UNDEFINED"}
};


// private helpers
string CPS::_sortedLetters(string letters)
{
    sort(letters.begin(), letters.end());
    return letters;
}

Microtone_p CPS::_X(float f, string sd)
{
    Microtone_p retVal = make_shared<Microtone>(f, sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    retVal->setShortDescriptionText2(retVal->getFrequencyValueDescription());
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

// given a float return a microtone as "A", "B", etc.
Microtone_p CPS::one()       { return _X(1, "1"); }
Microtone_p CPS::A(float f) { return _X(f, "A"); }
Microtone_p CPS::B(float f) { return _X(f, "B"); }
Microtone_p CPS::C(float f) { return _X(f, "C"); }
Microtone_p CPS::D(float f) { return _X(f, "D"); }
Microtone_p CPS::E(float f) { return _X(f, "E"); }
Microtone_p CPS::F(float f) { return _X(f, "F"); }
Microtone_p CPS::G(float f) { return _X(f, "G"); }
Microtone_p CPS::H(float f) { return _X(f, "H"); }

// given two microtones A and B return their product AB with updated short description

Microtone_p CPS::AB(Microtone_p A,
                    Microtone_p B)
{
    auto const ab_f = A->getFrequencyValue() * B->getFrequencyValue();
    auto const ab_sd = A->getShortDescriptionText() + B->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(ab_f, ab_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto ab_fd = A->getFrequencyValueDescription() + "*" + B->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(ab_fd);
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    retVal->setDegreeName(_sortedLetters(ab_sd));
    
    return retVal;
}

Microtone_p CPS::ABC(Microtone_p A,
                     Microtone_p B,
                     Microtone_p C)
{
    auto mtAB = AB(A, B);
    auto abc_f = mtAB->getFrequencyValue() * C->getFrequencyValue();
    auto abc_sd = mtAB->getShortDescriptionText() + C->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(abc_f, abc_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto abc_fd = mtAB->getShortDescriptionText2() + "*" + C->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(abc_fd);
    retVal->setDegreeName(_sortedLetters(abc_sd));
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

Microtone_p CPS::ABCD(Microtone_p A,
                      Microtone_p B,
                      Microtone_p C,
                      Microtone_p D)
{
    auto mtABC = ABC(A, B, C);
    auto abcd_f = mtABC->getFrequencyValue() * D->getFrequencyValue();
    auto abcd_sd = mtABC->getShortDescriptionText() + D->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(abcd_f, abcd_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto abcd_fd = mtABC->getShortDescriptionText2() + "*" + D->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(abcd_fd);
    retVal->setDegreeName(_sortedLetters(abcd_sd));
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

Microtone_p CPS::ABCDE(Microtone_p A,
                       Microtone_p B,
                       Microtone_p C,
                       Microtone_p D,
                       Microtone_p E)
{
    auto mtABCD = ABCD(A, B, C, D);
    auto abcde_f = mtABCD->getFrequencyValue() * E->getFrequencyValue();
    auto abcde_sd = mtABCD->getShortDescriptionText() + E->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(abcde_f, abcde_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto abcde_fd = mtABCD->getShortDescriptionText2() + "*" + E->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(abcde_fd);
    retVal->setDegreeName(_sortedLetters(abcde_sd));
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

Microtone_p CPS::ABCDEF(Microtone_p A,
                        Microtone_p B,
                        Microtone_p C,
                        Microtone_p D,
                        Microtone_p E,
                        Microtone_p F)
{
    auto mtABCDE = ABCDE(A, B, C, D, E);
    auto abcdef_f = mtABCDE->getFrequencyValue() * F->getFrequencyValue();
    auto abcdef_sd = mtABCDE->getShortDescriptionText() + F->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(abcdef_f, abcdef_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto abcdef_fd = mtABCDE->getShortDescriptionText2() + "*" + F->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(abcdef_fd);
    retVal->setDegreeName(_sortedLetters(abcdef_sd));
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

Microtone_p CPS::ABCDEFG(Microtone_p A,
                         Microtone_p B,
                         Microtone_p C,
                         Microtone_p D,
                         Microtone_p E,
                         Microtone_p F,
                         Microtone_p G)
{
    auto mtABCDEF = ABCDEF(A, B, C, D, E, F);
    auto abcdefg_f = mtABCDEF->getFrequencyValue() * G->getFrequencyValue();
    auto abcdefg_sd = mtABCDEF->getShortDescriptionText() + G->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(abcdefg_f, abcdefg_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto abcdefg_fd = mtABCDEF->getShortDescriptionText2() + "*" + G->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(abcdefg_fd);
    retVal->setDegreeName(_sortedLetters(abcdefg_sd));
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

Microtone_p CPS::ABCDEFGH(Microtone_p A,
                          Microtone_p B,
                          Microtone_p C,
                          Microtone_p D,
                          Microtone_p E,
                          Microtone_p F,
                          Microtone_p G,
                          Microtone_p H)
{
    auto mtABCDEFG = ABCDEFG(A, B, C, D, E, F, G);
    auto abcdefg_f = mtABCDEFG->getFrequencyValue() * H->getFrequencyValue();
    auto abcdefg_sd = mtABCDEFG->getShortDescriptionText() + H->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(abcdefg_f, abcdefg_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto abcdefgh_fd = mtABCDEFG->getShortDescriptionText2() + "*" + H->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(abcdefgh_fd);
    retVal->setDegreeName(_sortedLetters(abcdefg_sd));
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}

// given two microtones A and B return the dividend A/B with updated short description

Microtone_p CPS::A_div_B(Microtone_p A,
                         Microtone_p B)
{
    jassert(B->getFrequencyValue() > 0.00001f);
    auto ab_f = A->getFrequencyValue() / B->getFrequencyValue();
    auto ab_sd = A->getShortDescriptionText() + "/" + B->getShortDescriptionText();
    Microtone_p retVal = make_shared<Microtone>(ab_f, ab_sd, Microtone::Space::Linear, TuningConstants::defaultPeriod);
    auto ab_fd = A->getFrequencyValueDescription() + "/" + B->getFrequencyValueDescription();
    retVal->setShortDescriptionText2(ab_fd);
    retVal->setShortDescriptionText3(retVal->getFrequencyValueDescription());
    
    return retVal;
}
