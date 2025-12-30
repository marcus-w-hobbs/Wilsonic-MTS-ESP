/*
  ==============================================================================

    TuningTests.h
    Created: 22 Feb 2021 7:35:01pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include "Tuning_Include.h"
#include <JuceHeader.h>
#include "CPS.h"
#include "CPSTuningBase.h"

class WilsonicProcessor;

struct TuningTests
{
    //
    static void runTests (WilsonicProcessor& processor);

    // Microtone
    
    static void testMicrotone();

    // MicrotoneArray

    static void testMicrotoneArray();

    // Tuning Table

    static void testTuningTableImp();

    // Tuning

    static void testTuningImp();

    // Brun

    static void testBrun();
    static void test_brun_level_array();
    static void test_brun_level_array01();
    static void test_brun_array_infinity();
    static void test_brun_generator_setters_getters();
    static void test_brun_g_l_m();
    static void test_brun_terumi_gral_disjunction();
    static void test_brun_gral_mapping();

    // BrunMicrotone

    static void testBrunMicrotone();
    static void testBrunMicrotoneCollection();

    // CPS

    static void testCPS();
    
    // EulerGenus_1

    static void testEulerGenus_1();

    // CPS_1_1

    static void testCPS_1_1();

    // CPS_2_k

    static void testCPS_2_1();
    static void testCPS_2_2();

    // CPS_3_k
//    static void testCPS_3_1();
//    static void testCPS_3_2();
//    static void testCPS_3_3();

    // CPS_4_k
//    static void testCPS_4_1();
    static void testCPS_4_2();
//    static void testCPS_4_3();
//    static void testCPS_4_4();

    // CPS_5_k
//    static void testCPS_5_1();
//    static void testCPS_5_2();
//    static void testCPS_5_3();
//    static void testCPS_5_4();
//    static void testCPS_5_5();


    // CPS_4_k

    static void testCPS_4_1_DAW_Automation();

    static void testCPS_4_2_DAW_Automation();

    static void testCPS_4_3_DAW_Automation();

    static void testCPS_4_4_DAW_Automation();

    // CPS_6_k

    static void testCPS_6_3();

    static void testEulerGenus6_DAW_Automation();

    static void testCPS_6_1_DAW_Automation();

    static void testCPS_6_2_DAW_Automation();

    static void testCPS_6_3_DAW_Automation();

    static void testCPS_6_4_DAW_Automation();

    static void testCPS_6_5_DAW_Automation();

    static void testCPS_6_6_DAW_Automation();

    // recursive (n, k) on subsets 0+1

    static void walkCPSTuningBase (shared_ptr<CPSTuningBase>);

    static void walkCPSTuningBase2 (shared_ptr<CPSTuningBase>);//variant

    static void walkCPSTuningBase3 (shared_ptr<CPSTuningBase>, const string);//variant

    static void walkCPSTuningBase4 (shared_ptr<CPSTuningBase>, const string);//variant

    static void walkCPSTuningBase5 (shared_ptr<CPSTuningBase>, const string);//variant

    static void walkCPSTuningBase6 (shared_ptr<CPSTuningBase>, const string);//variant

    static void walkCPSTuningBase7 (shared_ptr<CPSTuningBase>, const string);//variant

    static void walkCPSTuningBase8 (shared_ptr<CPSTuningBase>, const string);//variant

    // code gen...creates code for 13 files

    static void testEulerGenus6CodeGen();

    // Eighth Octave Overtone Tuning
    
    static void testEighthOctaveOvertone();

    static void testOctaveOvertone(); // HARMONIC

    static void testOctaveUndertone();  // SUBHARMONIC

    // Persian 17 North Indian

    static void testPersian17NorthIndian();

    static void persian17NorthIndianCodeGen();

    // Recurrence Relation

    static void testRecurrenceRelation();
    static void testRecurrenceRelationHarmonicFibonacci();
    static void testRecurrenceRelationPeriodSeeds();
    static void testRecurrenceRelationBackwardCompatibility();

    static void recurrenceRelationCodeGen();

    // Scala

    static void testScalaFileRW();

    // CoPrime

    static void testCoPrime();
    
    // Pentatonic Flutes
    
    static void testPentatonicFlutes(WilsonicProcessor& processor);
    
    // Diamonds
    
    static void testDiamonds();

    // time: for logging

    static string timeDescription(Time time);

    static string relativeTimeDescription(RelativeTime relativeTime);

    static string currentTime();

    static void logCurrentTime();

    static shared_ptr<Time> logRelativeTime(string desc, shared_ptr<Time> previousTime);
};
