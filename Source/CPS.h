/*
 ==============================================================================
 
 CPS.h
 Created: 8 Aug 2021 9:48:43am
 Author:  Marcus W. Hobbs
 
 // helpers for CPS computations
 
 ==============================================================================
 */

#pragma once

#include <JuceHeader.h>
#include "Microtone.h"
#include "MicrotoneArray.h"
#include "Tuning_Include.h"

// when you add enums you must also update __cpsTuningClassMap

enum class CPS_Class
{
    CPS_1_1,
    
    CPS_2_1,
    CPS_2_2,
    
    CPS_3_1,
    Triad,
    CPS_3_2,
    CPS_3_3,
    TriadicDiamond,
    
    CPS_4_1,
    Tetrad,
    CPS_4_2,
    CPS_4_3,
    CPS_4_4,
    TetradicDiamond,
    Mandala,
    
    CPS_5_1,
    Pentad,
    CPS_5_2,
    CPS_5_3,
    CPS_5_4,
    CPS_5_5,
    PentadicDiamond,
    
    CPS_6_1,
    Hexad,
    CPS_6_2,
    CPS_6_3,
    CPS_6_4,
    CPS_6_5,
    CPS_6_6,
    HexadicDiamond,
    
    CPS_7_1,
    Heptad,
    HeptadicDiamond,
    
    CPS_8_1,
    Ogdoad,
    OgdoadicDiamond,
    
    EulerGenus_1,
    EulerGenus_2,
    EulerGenus_3,
    EulerGenus_4,
    EulerGenus_5,
    EulerGenus_6,
    
    UNDEFINED
};

using CPSTuningClassMap = unordered_map<CPS_Class, string>;

struct CPS
{
public:
    
    static constexpr int __MAX_NUM_EULER_GENUS_6_SUBSETS {6};
    
    static CPSTuningClassMap __cpsTuningClassMap;
    
    
    // factory: given a float return a microtone with frequency f, short desc as "A", "B", and short desc2 as "f"
    
    static Microtone_p one();
    static Microtone_p A(float f);
    static Microtone_p B(float f);
    static Microtone_p C(float f);
    static Microtone_p D(float f);
    static Microtone_p E(float f);
    static Microtone_p F(float f);
    static Microtone_p G(float f);
    static Microtone_p H(float f);
    
    // given two microtones A and B return their product AB with updated short description
    
    static Microtone_p AB(Microtone_p A,
                           Microtone_p B);
    
    // etc
    
    static Microtone_p ABC(Microtone_p A,
                           Microtone_p B,
                           Microtone_p C);
    
    static Microtone_p ABCD(Microtone_p A,
                            Microtone_p B,
                            Microtone_p C,
                            Microtone_p D);
    
    static Microtone_p ABCDE(Microtone_p A,
                             Microtone_p B,
                             Microtone_p C,
                             Microtone_p D,
                             Microtone_p E);
    
    static Microtone_p ABCDEF(Microtone_p A,
                              Microtone_p B,
                              Microtone_p C,
                              Microtone_p D,
                              Microtone_p E,
                              Microtone_p F);
    
    static Microtone_p ABCDEFG(Microtone_p A,
                               Microtone_p B,
                               Microtone_p C,
                               Microtone_p D,
                               Microtone_p E,
                               Microtone_p F,
                               Microtone_p G);
    
    static Microtone_p ABCDEFGH(Microtone_p A,
                                Microtone_p B,
                                Microtone_p C,
                                Microtone_p D,
                                Microtone_p E,
                                Microtone_p F,
                                Microtone_p G,
                                Microtone_p H);
    
    static Microtone_p A_div_B(Microtone_p A,
                               Microtone_p B);
    
private:
    
    // private helper
    
    static Microtone_p _X(float f, string sd);
    static string _sortedLetters(string letters); // degree name helper: "CA" -> "AC"
};
