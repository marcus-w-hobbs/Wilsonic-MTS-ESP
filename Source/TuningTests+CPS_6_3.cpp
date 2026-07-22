/*
 ==============================================================================

 TuningTests+CPS_6_3.h
 Created: 16 Aug 2021 10:56:02pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include "TuningTests.h"
#include "CPS_6_3.h"
#include "AppTuningModel.h"
#include "EulerGenusModel.h"
#include "EulerGenusViewModel.h"
#include "WilsonicProcessor.h"

void TuningTests::testCPS_6_3()
{
    // Test EulerGenus_1
    cout << "BEGIN TEST: CPS_6_3() ---------------------\n\n";

    // construct 
    cout << "CPS_6_3 constructor:-----------------\n";
    auto time = logRelativeTime ("start", nullptr);
    auto cps_6_3 = CPS_6_3 (CPS::A (3), CPS::B (5), CPS::C (7), CPS::D (11), CPS::E (13), CPS::F (17));
    time  = logRelativeTime ("constructor complete", time);

    // description (takes time)
    cout << "CPS_6_3 description:-----------------\n";
    cout << "CPS_6_3 getTuningDescription: " << cps_6_3.getTuningDescription() << endl;
    cout << "CPS_6_3 getDebugDescription: " << cps_6_3.getDebugDescription() << endl;
    time  = logRelativeTime ("description complete", time);

    // modify seeds
    cout << "CPS_6_3 setABCEDF:-----------------\n";
    cps_6_3.setABCDEF(CPS::A (19), CPS::B (23), CPS::C (29), CPS::D (31), CPS::E (37), CPS::F (41));
    time  = logRelativeTime ("modify seeds complete", time);

    // description (takes time)
    cout << "CPS_6_3 description:-----------------\n";
    cout << "CPS_6_3 getTuningDescription: " << cps_6_3.getTuningDescription() << endl;
    cout << "CPS_6_3 getDebugDescription: " << cps_6_3.getDebugDescription() << endl;
    time  = logRelativeTime ("description complete", time);

    //
    cout << "END TEST: CPS_6_3() ---------------------\n\n";
}

#pragma mark - Genus Space

// Genus Space: with the toggle ON, drilling into subsets keeps the drill-path
// root CPS(6,k) as the sounding tuning; the selected subset becomes a keyboard
// view into the root's MIDI space.
void TuningTests::testGenusSpace(WilsonicProcessor& processor)
{
    cout << "BEGIN TEST: testGenusSpace() ---------------------\n\n";
    int numPass = 0;
    int numFail = 0;
    auto check = [&](bool condition, string message) {
        if(condition) {
            numPass++;
        } else {
            numFail++;
            cout << "FAIL: " << message << endl;
            jassertfalse;
        }
    };

    auto const egm = processor.getEulerGenusModel();
    auto const atm = processor.getAppTuningModel();
    auto const eg6ID = EulerGenusModel::getEulerGenus6ParameterID().getParamID();
    auto const genusSpaceID = EulerGenusModel::getEulerGenus6GenusSpaceParameterID().getParamID();

    auto selectDAWKey = [&](DAWKey daw_key) {
        auto found = false;
        for(int i = 0; i < egm->getNumDAWKeys(); i++) {
            if(egm->dawKeyAtIndex(i) == daw_key) {
                egm->parameterChanged(eg6ID, static_cast<float>(i));
                found = true;
                break;
            }
        }
        check(found, ("daw key not found: " + daw_key).toStdString());
    };

    auto descriptionsOf = [](shared_ptr<Tuning> tuning) {
        set<string> retVal {};
        auto processedArray = tuning->getProcessedArray();
        for(unsigned long i = 0; i < processedArray.count(); i++) {
            retVal.insert(processedArray.microtoneAtIndex(i)->getShortDescriptionText());
        }
        return retVal;
    };

    // navigate to the CPS_6_3 page with the parent (eikosany) selected
    String const cps63PageKey = "||EulerGenus_6_A_B_C_D_E_F||CPS_6_3_A_B_C_D_E_F__CPS_6_3_A_B_C_D_E_F";
    egm->parameterChanged(genusSpaceID, 0.f); // baseline: toggle OFF
    selectDAWKey(cps63PageKey);
    auto const root = egm->getTuning();
    check(root != nullptr, "root tuning is null");
    check(root->getProcessedArrayCount() == 20, "eikosany should have 20 tones");
    check(egm->getGenusSpaceSubsetDescriptions().empty(), "toggle OFF: no subset descriptions");
    auto const rootDescriptions = descriptionsOf(root);
    check(rootDescriptions.size() == 20, "eikosany should have 20 unique formal products");

    // select the first S0 subset (CPS_5_2 x common tone): toggle OFF keeps today's behavior
    auto const vm = egm->getViewModel();
    check(vm != nullptr, "view model is null");
    auto const s0 = vm->parentTuning->getSubsets0()[0];
    auto const s1 = vm->parentTuning->getSubsets1()[0];
    selectDAWKey(s0->getDAWKey());
    check(egm->getTuning()->getProcessedArrayCount() == 10, "toggle OFF: subset selection sounds the 10-tone subset");
    check(egm->getGenusSpaceSubsetDescriptions().empty(), "toggle OFF: no subset descriptions");

    // toggle ON: the sounding tuning must be the drill-path root; the subset becomes the keyboard view
    egm->parameterChanged(genusSpaceID, 1.f);
    check(egm->getTuning()->getProcessedArrayCount() == 20, "toggle ON: subset selection sounds the 20-tone root");
    auto const s0Descriptions = egm->getGenusSpaceSubsetDescriptions();
    check(s0Descriptions.size() == 10, "toggle ON: subset view has 10 tones");
    for(auto& description : s0Descriptions) {
        check(rootDescriptions.count(description) == 1, "subset tone must be a root tone: " + description);
    }

    // complementation: S0[0] and S1[0] partition the root's 20 tones (Pascal's rule made audible)
    selectDAWKey(s1->getDAWKey());
    check(egm->getTuning()->getProcessedArrayCount() == 20, "toggle ON: complement selection sounds the 20-tone root");
    auto const s1Descriptions = egm->getGenusSpaceSubsetDescriptions();
    check(s1Descriptions.size() == 10, "toggle ON: complement view has 10 tones");
    set<string> unionDescriptions {};
    for(auto& description : s0Descriptions) unionDescriptions.insert(description);
    for(auto& description : s1Descriptions) unionDescriptions.insert(description);
    check(unionDescriptions.size() == 20, "S0[0] and S1[0] must be disjoint and partition the root");

    // drill one level down: root must not change
    auto const s0ViewModel = egm->_getViewModel(s0->getDAWKey());
    auto const drillKey = s0ViewModel->dawDrillKey;
    selectDAWKey(drillKey);
    check(egm->getTuning()->getProcessedArrayCount() == 20, "drilled one level: still sounds the 20-tone root");
    for(auto& description : egm->getGenusSpaceSubsetDescriptions()) {
        check(rootDescriptions.count(description) == 1, "drilled subset tone must be a root tone: " + description);
    }

    // toggle OFF at depth: reverts to today's behavior (selection sounds itself)
    egm->parameterChanged(genusSpaceID, 0.f);
    check(egm->getTuning()->getProcessedArrayCount() != 20 || egm->getViewModel()->parentTuning->getIsSelected(),
          "toggle OFF at depth: selection sounds itself again");
    check(egm->getGenusSpaceSubsetDescriptions().empty(), "toggle OFF: no subset descriptions");

    // keyboard mapping: subset slots map into the root's MIDI space
    egm->parameterChanged(genusSpaceID, 1.f);
    selectDAWKey(s0->getDAWKey());
    atm->setTuning(egm->getTuning());
    atm->setKeyboardSubset(egm->getGenusSpaceSubsetDescriptions());
    check(atm->getKeyboardNPO() == 10, "keyboard shows 10 keys per octave");
    check(atm->getTuningTableNPO() == 20, "tuning table stays 20 notes per octave");
    auto previousNN = -1;
    set<string> subsetDescriptionSet {};
    for(auto& description : egm->getGenusSpaceSubsetDescriptions()) subsetDescriptionSet.insert(description);
    for(unsigned long slot = 0; slot < atm->getKeyboardNumSlots(); slot++) {
        auto const nn = atm->keyboardSlotToNoteNumber(static_cast<int>(slot));
        check(nn >= 0 && nn < 128, "mapped note number in MIDI range");
        check(nn > previousNN, "mapped note numbers strictly ascend");
        previousNN = nn;
        check(atm->noteNumberToKeyboardSlot(nn) == static_cast<int>(slot), "slot -> nn -> slot round trip");
        auto const description = atm->getTuningTableShortDescription(static_cast<unsigned long>(nn));
        check(subsetDescriptionSet.count(description) == 1, "mapped key sounds a subset tone: " + description);
    }

    // keyboard mapping clears when the subset is empty
    atm->setKeyboardSubset(vector<string>{});
    check(atm->getKeyboardNPO() == atm->getTuningTableNPO(), "empty subset: keyboard reverts to tuning table NPO");
    check(atm->noteNumberToKeyboardSlot(60) == 60, "empty subset: slot mapping is identity");

    // restore default state
    egm->parameterChanged(genusSpaceID, 0.f);
    egm->parameterChanged(eg6ID, 2.f); // default: EG6 CPS_6_3
    atm->setTuning(egm->getTuning());

    cout << "testGenusSpace: PASS: " << numPass << " FAIL: " << numFail << endl;
    check(numFail == 0, "testGenusSpace had failures");
    cout << "END TEST: testGenusSpace() ---------------------\n\n";
}
