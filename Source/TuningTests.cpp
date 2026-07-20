/*
 ==============================================================================
 
 TuningTests.cpp
 Created: 22 Feb 2021 7:35:01pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "TuningTests.h"
#include "AppTuningModel.h"
#include "Microtone.h"
#include "WilsonicProcessor.h"

#pragma mark - test suite

void TuningTests::runTests(WilsonicProcessor& processor)
{
    // header
    
    cout << endl;
    cout << endl;
    cout << "BEGIN: Running Wilsonic Test Suite -------------" << endl;
    cout << endl;
    
    /*
     // list of 31-limit coprimes
     auto const limit = 31;
     map<float,string> coprime = {};
     // reverse order is so that key is clobbered by smallest i,j.  i.e., 3/2 instead of 30/20
     for (auto i = limit; i > 0; i--)
     {
     for (auto j = limit; j > 0; j--)
     {
     auto f = (float)i/(float)j;
     if (f < 2.f)
     {
     string rational = to_string(i) + "/" + to_string(j);
     coprime[f] = rational;
     }
     }
     }
     for (const auto& kv : coprime)
     {
     cout << kv.first << " = " << kv.second << endl;
     }
     */
    
    // Microtones
    //TuningTests::testMicrotone();
    //TuningTests::testMicrotoneArray();
    
    // Tuning Tables, Tunings
    //TuningTests::testTuningTableImp();
    //TuningTests::testTuningImp();
    
    // Brun2
    //TuningTests::testBrun();
    //TuningTests::testBrunMicrotone();
    //TuningTests::testBrunMicrotoneCollection();
    
    // CPS, euler genus
    //TuningTests::testCPS();
    //TuningTests::testEulerGenus_1();
    //TuningTests::testCPS_1_1();
    //TuningTests::testCPS_2_1();
    //TuningTests::testCPS_2_2();
    //TuningTests::testCPS_4_2();
    //TuningTests::testCPS_6_3();
    
    //    TuningTests::testCPS_4_1_DAW_Automation();
    //    TuningTests::testCPS_4_2_DAW_Automation();
    //    TuningTests::testCPS_4_3_DAW_Automation();
    //    TuningTests::testCPS_4_4_DAW_Automation();
    
    //    TuningTests::testCPS_6_1_DAW_Automation();
    //    TuningTests::testCPS_6_2_DAW_Automation();
    //    TuningTests::testCPS_6_3_DAW_Automation();
    //    TuningTests::testCPS_6_4_DAW_Automation();
    //    TuningTests::testCPS_6_5_DAW_Automation();
    //    TuningTests::testCPS_6_6_DAW_Automation();
    
    //    TuningTests::testEulerGenus6_DAW_Automation();

    // Genus Space
    TuningTests::testGenusSpace(processor);
    
    
    //    TuningTests::testEulerGenus6CodeGen();
    
    // TODO: create eighth octave overtone test files
    // MU: eighth octave overtone
    //TuningTests::testEighthOctaveOvertone();
    //cout << "BEGIN: Running Wilsonic Test testOctaveOvertone -------------" << endl;
    //TuningTests::testOctaveOvertone();
    //cout << "END: Running Wilsonic Test testOctaveOvertone -------------" << endl;
    //cout << endl << endl;
    
    //    cout << "BEGIN: Running Wilsonic Test testOctaveUndertone -------------" << endl;
    //    TuningTests::testOctaveUndertone();
    //    cout << "END: Running Wilsonic Test testOctaveUndertone -------------" << endl;
    
    //TuningTests::testPersian17NorthIndian();
    
    //TuningTests::testRecurrenceRelation();
    //TuningTests::recurrenceRelationCodeGen();
    
#if 0
    // TODO: make this a Scala test
    // print 19edo scl file
    cout << "! 19edo.scl" << endl;
    cout << "!" << endl;
    cout << "19 equal divisions of the octave.  Hobbs" << endl;
    cout << "19" << endl;
    cout << "!" << endl;
    for (auto i = 0; i < 19; i++)
    {
        auto c = 1200.f * i / 19.f;
        cout << to_string (c) << endl;
    }
    cout << "2/1" << endl;
    cout << endl << endl;
#endif
    
    // CoPrime
    //testCoPrime();
    
    // Pentatonic Flutes
    //testPentatonicFlutes (processor);
    
    // Diamonds
    //testDiamonds();
    
    
    // Tests Footer
    
    cout << endl;
    cout << "END: Running Wilsonic Test Suite -------------" << endl;
    cout << endl;
}

#pragma mark - Scala

void TuningTests::testScalaFileRW()
{
    
}

#pragma mark - time logging

string TuningTests::currentTime()
{
    auto time = Time::getCurrentTime();
    auto dateStr = time.toString(true, true, true, false);
    auto millis = time.currentTimeMillis(); // not high-res enough
    auto millisStr = String(millis);
    auto retVal = dateStr + " " + millisStr;
    auto retValStr = retVal.toStdString();
    return retValStr;
}

string TuningTests::timeDescription(Time time)
{
    auto dateStr = time.toString(true, true, true, false);
    auto millis = time.currentTimeMillis(); // not high-res enough
    auto millisStr = String(millis);
    auto retVal = dateStr + " " + millisStr;
    auto retValStr = retVal.toStdString();
    return retValStr;
}

string TuningTests::relativeTimeDescription(RelativeTime relativeTime)
{
    auto millis = relativeTime.inMilliseconds();
    auto millisStr = String(millis);
    auto retValStr = millisStr.toStdString();
    return retValStr;
}

void TuningTests::logCurrentTime()
{
    cout << currentTime() << endl;
}

// returns current time, logs relative time to previousTime
// if "previousTime" is nullptr create it as current time
shared_ptr<Time> TuningTests::logRelativeTime(string desc, shared_ptr<Time> previousTime)
{
    auto currentTime = make_shared<Time> (Time::getCurrentTime());
    if (previousTime == nullptr)
    {
        cout << desc << ": 0 ms" << endl; 
    }
    else
    {
        auto relativeTime = *currentTime - *previousTime;
        auto rdesc = relativeTimeDescription (relativeTime);
        cout << desc << ": " << rdesc << " ms" << endl;
    }
    
    return currentTime;
}


