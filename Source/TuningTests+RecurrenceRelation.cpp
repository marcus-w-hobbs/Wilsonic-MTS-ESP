/*
  ==============================================================================

    TuningTests+RecurrenceRelation.cpp
    Created: 21 Mar 2022 10:18:38pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "TuningTests.h"
#include "RecurrenceRelation.h"

void TuningTests::testRecurrenceRelation()
{
    cout << "BEGIN TEST: RecurrenceRelation() ---------------------" << endl;

    RecurrenceRelation scale {};

    cout << "END TEST: RecurrenceRelation() ---------------------" << endl;
}

#pragma mark - Harmonic Sum Tests

void TuningTests::testRecurrenceRelationHarmonicFibonacci()
{
    cout << "BEGIN TEST: RecurrenceRelationHarmonicFibonacci() ---------------------" << endl;

    // Test: Harmonic Fibonacci with seeds 1,1 should produce 1, 1, 0.5, 0.333..., 0.2, ...
    auto rr = make_shared<RecurrenceRelation>();
    rr->setSeeds(1, 1, 1, 1, 1, 1, 1, 1, 1);
    rr->setIndices(0); // H[n-1] + H[n-2]
    rr->setSumType(RecurrenceRelation::SumType::Harmonic);
    rr->setSeedSpace(RecurrenceRelation::SeedSpace::Frequency);
    rr->setNumberOfTerms(7);

    auto log = rr->getLog();
    cout << "Harmonic Fibonacci log: " << log << endl;

    // Verify mode info is in log
    jassert(log.find("Harmonic") != string::npos);
    jassert(log.find("Freq Seeds") != string::npos);

    cout << "END TEST: RecurrenceRelationHarmonicFibonacci() ---------------------" << endl;
}

void TuningTests::testRecurrenceRelationPeriodSeeds()
{
    cout << "BEGIN TEST: RecurrenceRelationPeriodSeeds() ---------------------" << endl;

    // Test: Period space should invert seeds
    auto rr = make_shared<RecurrenceRelation>();
    rr->setSeeds(1, 2, 1, 1, 1, 1, 1, 1, 1);
    rr->setIndices(0); // H[n-1] + H[n-2]
    rr->setSumType(RecurrenceRelation::SumType::Arithmetic);
    rr->setSeedSpace(RecurrenceRelation::SeedSpace::Period);
    rr->setNumberOfTerms(5);

    // With Period seeds, 1 and 2 become 1 and 0.5
    // So sequence starts: 1, 0.5, 1.5, 2, 3.5, ...
    auto log = rr->getLog();
    cout << "Period Seeds log: " << log << endl;

    // Verify mode info is in log
    jassert(log.find("Arithmetic") != string::npos);
    jassert(log.find("Period Seeds") != string::npos);
    // Verify seed inversion is working (0.5 should appear in the log)
    jassert(log.find("0.5") != string::npos);

    cout << "END TEST: RecurrenceRelationPeriodSeeds() ---------------------" << endl;
}

void TuningTests::testRecurrenceRelationBackwardCompatibility()
{
    cout << "BEGIN TEST: RecurrenceRelationBackwardCompatibility() ---------------------" << endl;

    // Test: Default mode (Arithmetic, Frequency) should match original behavior
    auto rr_new = make_shared<RecurrenceRelation>();

    rr_new->setSeeds(1, 1, 1, 1, 1, 1, 1, 1, 1);
    rr_new->setIndices(0);
    rr_new->setNumberOfTerms(7);

    // New should default to Arithmetic/Frequency
    jassert(rr_new->getSumType() == RecurrenceRelation::SumType::Arithmetic);
    jassert(rr_new->getSeedSpace() == RecurrenceRelation::SeedSpace::Frequency);

    // Verify indices work correctly
    jassert(rr_new->getSumTypeIndex() == 0);
    jassert(rr_new->getSeedSpaceIndex() == 0);

    // Test setByIndex methods
    rr_new->setSumTypeByIndex(1);
    jassert(rr_new->getSumType() == RecurrenceRelation::SumType::Harmonic);
    rr_new->setSumTypeByIndex(0);
    jassert(rr_new->getSumType() == RecurrenceRelation::SumType::Arithmetic);

    rr_new->setSeedSpaceByIndex(1);
    jassert(rr_new->getSeedSpace() == RecurrenceRelation::SeedSpace::Period);
    rr_new->setSeedSpaceByIndex(0);
    jassert(rr_new->getSeedSpace() == RecurrenceRelation::SeedSpace::Frequency);

    cout << "END TEST: RecurrenceRelationBackwardCompatibility() ---------------------" << endl;
}

void TuningTests::recurrenceRelationCodeGen()
{
    for (auto i = 1; i<10; i++)
    {
        for (auto j = 1; j<10; j++)
        {
            if (j<=i) continue;
//            cout << "make_tuple<String, int, int> (\"i:" << i << ", j:" << j << "\", " << i << ", " << j << ")," << endl;
//            cout << "make_tuple<String, int, int> (\"H[n] = H[n - " << i << "] + H[n - " << j << "]\", " << i << ", " << j << ")," << endl;
//            cout << "i:" << i << ", j:" << j << endl;
            cout << "\"H[n] = H[n - " << i << "] + H[n - " << j << "]\", " << endl;
        }
    }
//i:1, j:2
//i:1, j:3
//i:1, j:4
//i:1, j:5
//i:1, j:6
//i:1, j:7
//i:1, j:8
//i:1, j:9
//i:2, j:3
//i:2, j:4
//i:2, j:5
//i:2, j:6
//i:2, j:7
//i:2, j:8
//i:2, j:9
//i:3, j:4
//i:3, j:5
//i:3, j:6
//i:3, j:7
//i:3, j:8
//i:3, j:9
//i:4, j:5
//i:4, j:6
//i:4, j:7
//i:4, j:8
//i:4, j:9
//i:5, j:6
//i:5, j:7
//i:5, j:8
//i:5, j:9
//i:6, j:7
//i:6, j:8
//i:6, j:9
//i:7, j:8
//i:7, j:9
//i:8, j:9
}
