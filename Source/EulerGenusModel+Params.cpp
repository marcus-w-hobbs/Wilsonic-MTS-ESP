/*
  ==============================================================================

    EulerGenusModel+Params.cpp
    Created: 25 Nov 2021 3:46:46pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "EulerGenusModel.h"

#pragma mark - processor processBlock

// called only once: on construction of processor

unique_ptr<AudioProcessorParameterGroup> EulerGenusModel::createParams()
{
    // Tuning Params
    auto presetNames = *_dawKeys;
    auto presetParamGroup = make_unique<AudioProcessorParameterGroup>
    (getGroupID(), getGroupName(), getSubgroupSeparator(),

     // combo box
     make_unique<AudioParameterChoice>
     (
      EulerGenusModel::getEulerGenus6ParameterID(),
      EulerGenusModel::getEulerGenus6ParameterName(),
      presetNames,
      0)
     ,

     // A
     make_unique<AudioParameterFloat>
     (getEulerGenus6AParameterID(),
      getEulerGenus6AParameterName(),
      NormalisableRange<float> (rangeMin, rangeMax, rangeStep),
      _A->getFrequencyValue(),
      getEulerGenus6AParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int maxLength) { return String (value).substring (0, maxLength); },
[](const String& text) { return text.getFloatValue(); })
     ,

     // B
     make_unique<AudioParameterFloat>
     (getEulerGenus6BParameterID(),
      getEulerGenus6BParameterName(),
      NormalisableRange<float> (rangeMin, rangeMax, rangeStep),
      _B->getFrequencyValue(),
      getEulerGenus6BParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int maxLength) { return String (value).substring (0, maxLength); },
[](const String& text) { return text.getFloatValue(); })
     ,

     // C
     make_unique<AudioParameterFloat>
     (getEulerGenus6CParameterID(),
      getEulerGenus6CParameterName(),
      NormalisableRange<float> (rangeMin, rangeMax, rangeStep),
      _C->getFrequencyValue(),
      getEulerGenus6CParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int maxLength) { return String (value).substring (0, maxLength); },
[](const String& text) { return text.getFloatValue(); })
     ,

     // D
     make_unique<AudioParameterFloat>
     (getEulerGenus6DParameterID(),
      getEulerGenus6DParameterName(),
      NormalisableRange<float> (rangeMin, rangeMax, rangeStep),
      _D->getFrequencyValue(),
      getEulerGenus6DParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int maxLength) { return String (value).substring (0, maxLength); },
[](const String& text) { return text.getFloatValue(); })
     ,

     // E
     make_unique<AudioParameterFloat>
     (getEulerGenus6EParameterID(),
      getEulerGenus6EParameterName(),
      NormalisableRange<float> (rangeMin, rangeMax, rangeStep),
      _E->getFrequencyValue(),
      getEulerGenus6EParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int maxLength) { return String (value).substring (0, maxLength); },
[](const String& text) { return text.getFloatValue(); })
     ,

     // F
     make_unique<AudioParameterFloat>
     (getEulerGenus6FParameterID(),
      getEulerGenus6FParameterName(),
      NormalisableRange<float> (rangeMin, rangeMax, rangeStep),
      _F->getFrequencyValue(),
      getEulerGenus6FParameterName(),
      AudioProcessorParameter::genericParameter,
[](float value, int maxLength) { return String (value).substring (0, maxLength); },
[](const String& text) { return text.getFloatValue(); })
     ,

     // Genus Space: MUST remain appended after F to preserve DAW automation
     make_unique<AudioParameterBool>
     (getEulerGenus6GenusSpaceParameterID(),
      getEulerGenus6GenusSpaceParameterName(),
      false)


     );

    return presetParamGroup;
}

String EulerGenusModel::getGroupID()
{
    return "Euler Genus 6";
}

String EulerGenusModel::getGroupName()
{
    return "Euler Genus 6";
}

String EulerGenusModel::getSubgroupSeparator()
{
    return " | ";
}

// key for this design's Favorites array
ParameterID EulerGenusModel::getDesignParameterID()
{
    return ParameterID ("EULERGENUS6_PARAMETERID_DESIGNS", AppVersion::getVersionHint());
}

// used for Favorites
StringArray EulerGenusModel::getFavoritesParameterIDs()
{
    return StringArray (getEulerGenus6ParameterID().getParamID(),
                        getEulerGenus6AParameterID().getParamID(),
                        getEulerGenus6BParameterID().getParamID(),
                        getEulerGenus6CParameterID().getParamID(),
                        getEulerGenus6DParameterID().getParamID(),
                        getEulerGenus6EParameterID().getParamID(),
                        getEulerGenus6FParameterID().getParamID(),
                        getEulerGenus6GenusSpaceParameterID().getParamID()
                        );
}
