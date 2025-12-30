/*
  ==============================================================================

    RecurrenceRelationModel.h
    Created: 21 Mar 2022 8:44:44pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "AppVersion.h"
#include "ModelBase.h"
#include "RecurrenceRelation.h"
#include "TuningImp.h"
#include "Tuning_Include.h"

class AppTuningModel;

class RecurrenceRelationModel final
: public ModelBase
, public ActionBroadcaster
{

public:

    // static

    static const ParameterID getRecurrenceRelationHn1ParameterID() { return ParameterID("RECURRENCERELATIONHN1", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn1ParameterName() { return "Recurrence Relation|Hn_1"; }
    static const ParameterID getRecurrenceRelationCn1ParameterID() { return ParameterID("RECURRENCERELATIONCN1", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn1ParameterName() { return "Recurrence Relation|Cn_1"; }

    static const ParameterID getRecurrenceRelationHn2ParameterID() { return ParameterID("RECURRENCERELATIONHN2", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn2ParameterName() { return "Recurrence Relation|Hn_2"; }
    static const ParameterID getRecurrenceRelationCn2ParameterID() { return ParameterID("RECURRENCERELATIONCN2", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn2ParameterName() { return "Recurrence Relation|Cn_2"; }

    static const ParameterID getRecurrenceRelationHn3ParameterID() { return ParameterID("RECURRENCERELATIONHN3", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn3ParameterName() { return "Recurrence Relation|Hn_3"; }
    static const ParameterID getRecurrenceRelationCn3ParameterID() { return ParameterID("RECURRENCERELATIONCN3", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn3ParameterName() { return "Recurrence Relation|Cn_3"; }

    static const ParameterID getRecurrenceRelationHn4ParameterID() { return ParameterID("RECURRENCERELATIONHN4", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn4ParameterName() { return "Recurrence Relation|Hn_4"; }
    static const ParameterID getRecurrenceRelationCn4ParameterID() { return ParameterID("RECURRENCERELATIONCN4", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn4ParameterName() { return "Recurrence Relation|Cn_4"; }

    static const ParameterID getRecurrenceRelationHn5ParameterID() { return ParameterID("RECURRENCERELATIONHN5", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn5ParameterName() { return "Recurrence Relation|Hn_5"; }
    static const ParameterID getRecurrenceRelationCn5ParameterID() { return ParameterID("RECURRENCERELATIONCN5", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn5ParameterName() { return "Recurrence Relation|Cn_5"; }

    static const ParameterID getRecurrenceRelationHn6ParameterID() { return ParameterID("RECURRENCERELATIONHN6", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn6ParameterName() { return "Recurrence Relation|Hn_6"; }
    static const ParameterID getRecurrenceRelationCn6ParameterID() { return ParameterID("RECURRENCERELATIONCN6", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn6ParameterName() { return "Recurrence Relation|Cn_6"; }

    static const ParameterID getRecurrenceRelationHn7ParameterID() { return ParameterID("RECURRENCERELATIONHN7", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn7ParameterName() { return "Recurrence Relation|Hn_7"; }
    static const ParameterID getRecurrenceRelationCn7ParameterID() { return ParameterID("RECURRENCERELATIONCN7", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn7ParameterName() { return "Recurrence Relation|Cn_7"; }

    static const ParameterID getRecurrenceRelationHn8ParameterID() { return ParameterID("RECURRENCERELATIONHN8", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn8ParameterName() { return "Recurrence Relation|Hn_8"; }
    static const ParameterID getRecurrenceRelationCn8ParameterID() { return ParameterID("RECURRENCERELATIONCN8", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn8ParameterName() { return "Recurrence Relation|Cn_8"; }

    static const ParameterID getRecurrenceRelationHn9ParameterID() { return ParameterID("RECURRENCERELATIONHN9", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationHn9ParameterName() { return "Recurrence Relation|Hn_9"; }
    static const ParameterID getRecurrenceRelationCn9ParameterID() { return ParameterID("RECURRENCERELATIONCN9", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationCn9ParameterName() { return "Recurrence Relation|Cn_9"; }

    //TODO: wrap these
public:
    // helpers
    static const StringArray __HnParameterIDs;
    static const StringArray __CnParameterIDs;

public:

    static const ParameterID getRecurrenceRelationIndexParameterID() { return ParameterID("RECURRENCERELATIONINDEX", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationIndexParameterName() { return "Recurrence Relation|Index"; }

    static const ParameterID getRecurrenceRelationOffsetParameterID() { return ParameterID("RECURRENCERELATIONOFFSET", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationOffsetParameterName() { return "Recurrence Relation|Offset"; }

    static const ParameterID getRecurrenceRelationNumTermsParameterID() { return ParameterID("RECURRENCERELATIONNUMTERMS", AppVersion::getVersionHint()); }
    static const String getRecurrenceRelationNumTermsParameterName() { return "Recurrence Relation|Terms"; }

    // Sum Type parameter
    static const ParameterID getRecurrenceRelationSumTypeParameterID() {
        return ParameterID("RECURRENCERELATIONSUMTYPE", AppVersion::getVersionHint());
    }
    static const String getRecurrenceRelationSumTypeParameterName() {
        return "Recurrence Relation|Sum Type";
    }

    // Seed Space parameter
    static const ParameterID getRecurrenceRelationSeedSpaceParameterID() {
        return ParameterID("RECURRENCERELATIONSEEDSPACE", AppVersion::getVersionHint());
    }
    static const String getRecurrenceRelationSeedSpaceParameterName() {
        return "Recurrence Relation|Seed Space";
    }

    // lifecycle
public:
    RecurrenceRelationModel();
    ~RecurrenceRelationModel() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(RecurrenceRelationModel)

public:
    // public methods
    shared_ptr<Tuning> getTuning() override;

    // called only once: on construction of processor
    unique_ptr<AudioProcessorParameterGroup> createParams() override;
    String getGroupID() override;
    String getGroupName() override;
    String getSubgroupSeparator() override;
    ParameterID getDesignParameterID() override; // key for this design's Favorites array
    StringArray getFavoritesParameterIDs() override; // used for Favorites
    // called only once: when assigning _avpts
    void attachParameterListeners() override;
    void parameterChanged(const String& parameterID, float newValue) override;
    void updateProperties() override;

    void uiSetSeed(float s, unsigned long i_1_9); // index is 1-9, not 0-8
    float uiGetSeed(unsigned long i_1_9); // index is 1-9, not 0-8
    void uiSetCoefficient(unsigned long c, unsigned long i_1_9); // c is index into Coefficient list, index is 1-9, not 0-8
    unsigned long uiGetCoefficient(unsigned long i_1_9); // returns index into coefficient list, index is 1-9, not 0-8
    void uiSetIndices(unsigned long indices); // selects from pre-computed list of indices...i.e,(i=1, j=9)
    unsigned long uiGetIndices(); // to update combo box of i,j combinations
    void uiSetNumberOfTerms(unsigned long num_terms);
    unsigned long uiGetNumberOfTerms();
    void uiSetOffset(unsigned long offset);
    unsigned long uiGetOffset();
    const string getLog();

    // Sum Type UI methods
    void uiSetSumType(unsigned long index);
    unsigned long uiGetSumType();

    // Seed Space UI methods
    void uiSetSeedSpace(unsigned long index);
    unsigned long uiGetSeedSpace();

protected:
    void detachParameterListeners() override;

private:
    // private members
    shared_ptr<RecurrenceRelation> _recurrenceRelation;

    // private methods
    void _tuningChangedUpdateUI() override;
    void _tuningDivergedUpdateUI();
};

