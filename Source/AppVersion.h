/*
  ==============================================================================

    AppVersion.h
    Created: 1 Oct 2021 8:41:23pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include "version.h"
#include <JuceHeader.h>
#include "WilsonicAppSkin.h"
#include "WilsonicProcessorConstants.h"


class AppVersion
{
public:

    static const string getAppVersion()
    {
        // From: version.h:
        //#define VERSION_MAJOR 0
        //#define VERSION_MINOR 1
        //#define VER_NUM 0.01
        //#define BETA 1
        string retVal = "v";
        retVal += to_string (VER_NUM);
        vector<string> zeros = {"000000", "00000", "0000", "000", "00"};
        for (auto z : zeros)
        {
            WilsonicAppSkin::replaceAll (retVal, z, "");
        }

        if (BETA == 1)
        {
            retVal += ".";
            retVal += "beta";
        }

        return retVal;
    }

    static const int getVersionHint()
    {
        int const hint_int = VERSION_HINT;

        return hint_int;
    }
    
    static const String getAppName()
    {
        return String(WilsonicProcessorConstants::identifier);
    }

    static const String getDocumentationURL()
    {
        return String ("https://wilsonic.co/documentation/documentation-mts-esp/");
    }

    // project repository (written into exported tuning files as the LINK directive)
    static const String getProjectURL()
    {
        return String ("https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP");
    }
};
