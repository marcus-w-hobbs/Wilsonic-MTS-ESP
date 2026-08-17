/*
  ==============================================================================

    WilsonicAppSkin.h
    Created: 11 Apr 2021 11:05:57pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "Tuning_Include.h"
#include "WilsonicLookAndFeel.h"

class WilsonicAppSkin final 
: public ActionBroadcaster
{
    using Colour = Colour;
public:
    // static members
    static const String getAppSkinChangedMessage() { return "AppSkinChangedMessage";}

    // margin for all tuning components
    static constexpr float tuningComponentInteriorMargin {10};

    // default dimensions
    static constexpr float seedSliderHeight {70};
    static constexpr float comboBoxHeight {30};
    static constexpr float comboBoxFontSize {20.f};
    static constexpr float messageBusFontSize {12.f};
    static constexpr float tableViewFontSize {14.f};
    static constexpr float comboBoxWidth {400};
    static constexpr float sliderHeight {25};
    static constexpr float labelHeight {24};
    static constexpr float verticalSpacing {20};
    static constexpr float minHitPointSize {25};
    static constexpr float defaultPitchWheelFontScale {1.5};

    // lifecycle
    WilsonicAppSkin();
    ~WilsonicAppSkin()=default;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (WilsonicAppSkin)

public:
    // public methods
    shared_ptr<WilsonicLookAndFeel> getLookAndFeel();

    // broadcast that the skin has changed
    void skinDidChange();

    // default BG color
    static Colour getBgColor();
    Colour getSelectedComponentColor();

    // default text colours
    static Colour getTextColor();

    // default font
    static Font const getDefaultFont(float font_size) {return Font(FontOptions(font_size, Font::FontStyleFlags::plain));}

    // default tuning render line width
    float getDefaultLineWidth();

    // default tuning render dot radius
    float getSmallDotRadius();
    float getLargeDotRadius();

    // default tuning render cps line segment color
    Colour getCPSIntervalColour();

    // default harmonic and subharmonic triad color
    Colour getProportionalTriadDotColour();
    Colour getSubcontraryTriadDotColour();

    // Favorites
    Colour getTableListBoxBGColour()   { return Colour {0xff393f62}; }
    Colour getTableListBoxRow0Colour() { return Colour {0xff1d1d22}; }
    Colour getTableListBoxRow1Colour() { return Colour {0xff08090a}; }

    // window
    int getWindowWidth();
    int getWindowHeight();

    // global font minimum" plugins and standalones,
    float getFontHeightMin();

    // global font horizontal scale
    float getFontHorizontalScale();

    // string manipulation
    static void replaceAll(string& str, const string& from, const string& to);
    static string const floatDescription(float f, int places = 1);

private:
    // private members
    shared_ptr<WilsonicLookAndFeel> _lookAndFeel;

    // private methods
    int _getWindowWidthSD();
    int _getWindowHeightSD();
    int _getWindowWidthHD();
    int _getWindowHeightHD();
    int _getWindowWidthRetina();
    int _getWindowHeightRetina();
};
