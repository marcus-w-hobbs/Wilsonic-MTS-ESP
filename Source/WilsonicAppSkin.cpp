/*
  ==============================================================================

    WilsonicAppSkin.cpp
    Created: 11 Apr 2021 11:05:57pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "WilsonicAppSkin.h"

#pragma mark - Lifecycle

WilsonicAppSkin::WilsonicAppSkin() {
    _lookAndFeel = make_shared<WilsonicLookAndFeel>();
}

#pragma mark - public methods

shared_ptr<WilsonicLookAndFeel> WilsonicAppSkin::getLookAndFeel() {
    return _lookAndFeel;
}

#pragma mark - ActionBroadcaster

// broadcast that the skin has changed

void WilsonicAppSkin::skinDidChange() {
    sendActionMessage(getAppSkinChangedMessage());
}

#pragma mark - Colour

Colour WilsonicAppSkin::getBgColor() {
    return Colours::black;
}

Colour WilsonicAppSkin::getSelectedComponentColor() {
    return Colours::cornflowerblue;
}

Colour WilsonicAppSkin::getTextColor() {
    return Colours::white;
}

// default tuning render line width

float WilsonicAppSkin::getDefaultLineWidth() {
    return 1.5;
}

// default tuning render dot radius

float WilsonicAppSkin::getSmallDotRadius() {
    return 13;
}

float WilsonicAppSkin::getLargeDotRadius() {
    return 13 * 16;
}

// default tuning render cps line segment color

Colour WilsonicAppSkin::getCPSIntervalColour() {
    return Colour {0xff777777}; // brighter grey
}

Colour WilsonicAppSkin::getProportionalTriadDotColour() {
    return Colours::darkolivegreen;
}

Colour WilsonicAppSkin::getGeometricTriadDotColour() {
    return Colours::darkcyan;
}

Colour WilsonicAppSkin::getSubcontraryTriadDotColour() {
    return Colours::darkmagenta;
}

#pragma mark - font size minimum

float WilsonicAppSkin::getFontHorizontalScale() {
    return 0.8f;
}

float WilsonicAppSkin::getFontHeightMin() {
    return 9.f;
}

#pragma mark - Window Size

int WilsonicAppSkin::getWindowWidth() {
    return _getWindowWidthHD();
}

int WilsonicAppSkin::getWindowHeight() {
    return _getWindowHeightHD();
}

#pragma mark - window size helpers

int WilsonicAppSkin::_getWindowWidthSD() {
    return 800;
}

int WilsonicAppSkin::_getWindowHeightSD() {
    return 600;
}

int WilsonicAppSkin::_getWindowWidthHD() {
    return 1080;
}

int WilsonicAppSkin::_getWindowHeightHD() {
    return 720;
}

int WilsonicAppSkin::_getWindowWidthRetina() {
    return 2325;
}

int WilsonicAppSkin::_getWindowHeightRetina() {
    return 1145;
}

#pragma mark - string

void WilsonicAppSkin::replaceAll(string& str, const string& from, const string& to) {
    if(from.empty()) {
        return;
    }

    size_t start_pos = 0;
    while((start_pos = str.find(from, start_pos)) != string::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length(); // In case 'to' contains 'from', like replacing 'x' with 'yx'
    }
}

string const WilsonicAppSkin::floatDescription(float f, int places) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(places) << f;
    std::string s = out.str();

    // Remove trailing zeros
    s.erase(s.find_last_not_of('0') + 1, std::string::npos);
    // Remove trailing dot if necessary
    if (s.back() == '.') {
        s.pop_back();
    }

    return s;
}
