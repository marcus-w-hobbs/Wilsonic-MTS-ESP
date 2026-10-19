/*
  ==============================================================================

    WilsonicProcessor+Properties.cpp
    Created: 15 Apr 2023 12:08:50pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

/**
 * @file WilsonicProcessor+Properties.cpp
 * @brief This file contains the implementation of the WilsonicProcessor's properties.
 */

#include "WilsonicProcessor.h"
#include <algorithm>

/**
 * @def WINDOW_BOUNDS
 * @brief The key for the window bounds property.
 */
#define WINDOW_BOUNDS "lastWindowBounds"
/**
 * @def PITCH_WHEEL_IN_KEYBOARD
 * @brief The key for the pitch wheel in keyboard property.
 */
#define PITCH_WHEEL_IN_KEYBOARD "pitchWheelInKeyboard"
/**
 * @def PITCH_COLOR_OFFSET
 * @brief The key for the pitch color offset property.
 */
#define PITCH_COLOR_OFFSET "pitchColorOffset"
/**
 * @def KEYBOARD_HEIGHT
 * @brief The key for the keyboard height property.
 */
#define KEYBOARD_HEIGHT "keyboardHeight"
/**
 * @def KEYBOARD_WIDTH_FACTOR
 * @brief The key for the keyboard width factor property.
 */
#define KEYBOARD_WIDTH_FACTOR "keyboardWidthFactor"
/**
 * @def BRUN_DISPLAY_MODE
 * @brief The key for the Brun display mode property.
 */
#define BRUN_DISPLAY_MODE "brunDisplayMode"
/**
 * @def SHOW_PROPORTIONAL_TRIADS
 * @brief The key for the show proportional triads property.
 */
#define SHOW_PROPORTIONAL_TRIADS "showProportionalTriads"
/**
 * @def SHOW_GEOMETRIC_TRIADS
 * @brief The key for the show geometric triads property.
 */
#define SHOW_GEOMETRIC_TRIADS "showGeometricTriads"
/**
 * @def SHOW_LINEAR_KEYBOARD
 * @brief The key for the show linear keyboard property.
 */
#define SHOW_LINEAR_KEYBOARD "showLinearKeyboard"
/**
 * @def OUT_OF_BAND_POLICY
 * @brief The key for the out-of-band policy property (TuningOutput.h).
 * Stored as the OutOfBandPolicy int: 0 = Filter (mute, Live-aligned), 1 = Pass through.
 */
#define OUT_OF_BAND_POLICY "outOfBandPolicy"

#define FAVORITES_STORE_NPO_OVERRIDE       "favoritesStoreNPOOverride"
#define FAVORITES_STORE_PERIOD_MIDDLE_C    "favoritesStorePeriodMiddleC"
#define FAVORITES_STORE_NN_MIDDLE_C        "favoritesStoreNNMiddleC"
#define FAVORITES_STORE_FREQUENCY_MIDDLE_C "favoritesStoreFrequencyMiddleC"

#define PARTCH_O1 "partchO1"
#define PARTCH_U1 "partchU1"
#define PARTCH_O3 "partchO3"
#define PARTCH_U3 "partchU3"
#define PARTCH_O5 "partchO5"
#define PARTCH_U5 "partchU5"
#define PARTCH_O7 "partchO7"
#define PARTCH_U7 "partchU7"
#define PARTCH_O9 "partchO9"
#define PARTCH_U9 "partchU9"
#define PARTCH_O11 "partchO11"
#define PARTCH_U11 "partchU11"


/**
 * @brief Saves the window bounds to the properties.
 * @param bounds The window bounds to save.
 * @note This function is not yet working. The bounds are saved/recalled correctly,
 * but the standalone is hosted in a document window that manages size,
 * and the plugin's size is managed by the host.
 */
void WilsonicProcessor::saveWindowBounds(Rectangle<int> bounds)
{
    _properties->setValue(WINDOW_BOUNDS, bounds.toString());
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the window bounds from the properties.
 * @return The restored window bounds.
 */
Rectangle<int> WilsonicProcessor::restoreWindowBounds()
{
    Rectangle<int> bounds;
    bounds.fromString(_properties->getValue(WINDOW_BOUNDS, ""));

    return bounds;
}

/**
 * @brief Saves the pitch wheel in keyboard setting to the properties.
 * @param should_show Whether the pitch wheel should be shown in the keyboard.
 */
void WilsonicProcessor::savePitchWheelInKeyboard(bool should_show)
{
    String show = String(should_show ? 1 : 0);
    _properties->setValue(PITCH_WHEEL_IN_KEYBOARD, show);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the pitch wheel in keyboard setting from the properties.
 * @return Whether the pitch wheel should be shown in the keyboard.
 */
bool WilsonicProcessor::restorePitchWheelInKeyboard()
{
    String val = _properties->getValue(PITCH_WHEEL_IN_KEYBOARD, "0");
    int const val_int = val.getIntValue();
    bool const retVal =(val_int == 0) ? false : true;

    return retVal;
}

/**
 * @brief Saves the pitch color offset to the properties.
 * @param offset The pitch color offset to save.
 */
void WilsonicProcessor::savePitchColorOffset(float offset)
{
    float const offset01 = jlimit(0.f, 1.f, offset);
    String val = String(offset01);
    _properties->setValue(PITCH_COLOR_OFFSET, val);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the pitch color offset from the properties.
 * @return The restored pitch color offset.
 */
float WilsonicProcessor::restorePitchColorOffset()
{
    String val = _properties->getValue(PITCH_COLOR_OFFSET, "0");
    float const val_float = val.getFloatValue();

    return val_float;
}

/**
 * @brief Saves the keyboard height to the properties.
 * @param height The keyboard height to save.
 */
void WilsonicProcessor::saveKeyboardHeight(float height)
{
    String val = String(height);
    _properties->setValue(KEYBOARD_HEIGHT, val);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the keyboard height from the properties.
 * @return The restored keyboard height.
 */
float WilsonicProcessor::restoreKeyboardHeight()
{
    String val = _properties->getValue(KEYBOARD_HEIGHT, "60");
    float const val_float = val.getFloatValue();

    return val_float;
}

/**
 * @brief Saves the keyboard width factor to the properties.
 * @param factor The keyboard width factor to save.
 */
void WilsonicProcessor::saveKeyboardWidthFactor(float factor)
{
    String val = String(factor);
    _properties->setValue(KEYBOARD_WIDTH_FACTOR, val);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the keyboard width factor from the properties.
 * @return The restored keyboard width factor.
 */
float WilsonicProcessor::restoreKeyboardWidthFactor()
{
    String val = _properties->getValue(KEYBOARD_WIDTH_FACTOR, "4");
    float const val_float = val.getFloatValue();

    return val_float;
}

/**
 * @brief Saves the Brun display mode to the properties.
 * @param mode The Brun display mode to save.
 */
void WilsonicProcessor::saveBrunDisplayMode(int mode)
{
    String val = String(mode);
    _properties->setValue(BRUN_DISPLAY_MODE, val);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the Brun display mode from the properties.
 * @return The restored Brun display mode.
 */
int WilsonicProcessor::restoreBrunDisplayMode()
{
    String val = _properties->getValue(BRUN_DISPLAY_MODE, "0");
    int const val_int = val.getIntValue();

    return val_int;
}

/**
 * @brief Saves the show proportional triads setting to the properties.
 * @param should_show Whether proportional triads should be shown.
 */
void WilsonicProcessor::saveShowProportionalTriads(bool should_show)
{
    String show = String(should_show ? 1 : 0);
    _properties->setValue(SHOW_PROPORTIONAL_TRIADS, show);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the show proportional triads setting from the properties.
 * @return Whether proportional triads should be shown.
 */
bool WilsonicProcessor::restoreShowProportionalTriads()
{
    String val = _properties->getValue(SHOW_PROPORTIONAL_TRIADS, "1");
    int const val_int = val.getIntValue();
    bool const retVal =(val_int == 0) ? false : true;

    return retVal;
}

/**
 * @brief Saves the show geometric triads setting to the properties.
 * @param should_show Whether geometric triads should be shown.
 */
void WilsonicProcessor::saveShowGeometricTriads(bool should_show)
{
    String show = String(should_show ? 1 : 0);
    _properties->setValue(SHOW_GEOMETRIC_TRIADS, show);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the show geometric triads setting from the properties.
 * Defaults to hidden so the keyboard looks exactly as it did before
 * geometric triads were computed; the toggle opts in.
 * @return Whether geometric triads should be shown.
 */
bool WilsonicProcessor::restoreShowGeometricTriads()
{
    String val = _properties->getValue(SHOW_GEOMETRIC_TRIADS, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

/**
 * @brief Saves the keyboard visible setting to the properties.
 * @param should_show Whether the keyboard should be visible.
 */
void WilsonicProcessor::saveKeyboardVisible(bool should_show)
{
    String show = String(should_show ? 1 : 0);
    _properties->setValue(SHOW_LINEAR_KEYBOARD, show);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the keyboard visible setting from the properties.
 * @return Whether the keyboard should be visible.
 */
bool WilsonicProcessor::restoreKeyboardVisible()
{
    String val = _properties->getValue(SHOW_LINEAR_KEYBOARD, "1");
    int const val_int = val.getIntValue();
    bool const retVal =(val_int == 0) ? false : true;

    return retVal;
}

/**
 * @brief Saves the out-of-band policy to the properties (per machine, not APVTS).
 * @param policy What to do with keys below 4 Hz or above 21 kHz.
 */
void WilsonicProcessor::saveOutOfBandPolicy(OutOfBandPolicy policy)
{
    String val = String(static_cast<int>(policy));
    _properties->setValue(OUT_OF_BAND_POLICY, val);
    _properties->saveIfNeeded();
}

/**
 * @brief Restores the out-of-band policy from the properties.
 * Defaults to Filter, the Ableton Live-aligned behaviour; any unknown
 * stored value also reads as Filter.
 * @return The out-of-band policy.
 */
OutOfBandPolicy WilsonicProcessor::restoreOutOfBandPolicy()
{
    String val = _properties->getValue(OUT_OF_BAND_POLICY, "0");
    int const val_int = val.getIntValue();
    if (val_int == static_cast<int>(OutOfBandPolicy::PassThrough)) {
        return OutOfBandPolicy::PassThrough;
    }

    return OutOfBandPolicy::Filter;
}

void WilsonicProcessor::saveFavoritesStoreNPOOverride(bool should_store)
{
    String show = String(should_store ? 1 : 0);
    _properties->setValue(FAVORITES_STORE_NPO_OVERRIDE, should_store);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restoreFavoritesStoreNPOOverride()
{
    String val = _properties->getValue(FAVORITES_STORE_NPO_OVERRIDE, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::saveFavoritesStorePeriodMiddleC(bool should_store)
{
    String show = String(should_store ? 1 : 0);
    _properties->setValue(FAVORITES_STORE_PERIOD_MIDDLE_C, should_store);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restoreFavoritesStorePeriodMiddleC()
{
    String val = _properties->getValue(FAVORITES_STORE_PERIOD_MIDDLE_C, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::saveFavoritesStoreNNMiddleC(bool should_store)
{
    String show = String(should_store ? 1 : 0);
    _properties->setValue(FAVORITES_STORE_NN_MIDDLE_C, should_store);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restoreFavoritesStoreNNMiddleC()
{
    String val = _properties->getValue(FAVORITES_STORE_NN_MIDDLE_C, "0");
    int const val_int = val.getIntValue();
    bool const retVal =(val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::saveFavoritesStoreFrequencyMiddleC(bool should_store)
{
    String show = String(should_store ? 1 : 0);
    _properties->setValue(FAVORITES_STORE_FREQUENCY_MIDDLE_C, should_store);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restoreFavoritesStoreFrequencyMiddleC()
{
    String val = _properties->getValue(FAVORITES_STORE_FREQUENCY_MIDDLE_C, "0");
    int const val_int = val.getIntValue();
    bool const retVal =(val_int == 0) ? false : true;

    return retVal;
}


void WilsonicProcessor::savePartchO1(bool o1) {
    String show = String(o1 ? 1 : 0);
    _properties->setValue(PARTCH_O1, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchO1() {
    String val = _properties->getValue(PARTCH_O1, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchU1(bool u1) {
    String show = String(u1 ? 1 : 0);
    _properties->setValue(PARTCH_U1, show);
    _properties->saveIfNeeded();
}
        
bool WilsonicProcessor::restorePartchU1() {
    String val = _properties->getValue(PARTCH_U1, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}
            
void WilsonicProcessor::savePartchO3(bool o3) {
    String show = String(o3 ? 1 : 0);
    _properties->setValue(PARTCH_O3, show);
    _properties->saveIfNeeded();
}
                
bool WilsonicProcessor::restorePartchO3() {
    String val = _properties->getValue(PARTCH_O3, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}
                    
void WilsonicProcessor::savePartchU3(bool u3) {
    String show = String(u3 ? 1 : 0);
    _properties->setValue(PARTCH_U3, show);
    _properties->saveIfNeeded();
}
                        
bool WilsonicProcessor::restorePartchU3() {
    String val = _properties->getValue(PARTCH_U3, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchO5(bool o5) {
    String show = String(o5 ? 1 : 0);
    _properties->setValue(PARTCH_O5, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchO5() {
    String val = _properties->getValue(PARTCH_O5, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchU5(bool u5) {
    String show = String(u5 ? 1 : 0);
    _properties->setValue(PARTCH_U5, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchU5() {
    String val = _properties->getValue(PARTCH_U5, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchO7(bool o7) {
    String show = String(o7 ? 1 : 0);
    _properties->setValue(PARTCH_O7, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchO7() {
    String val = _properties->getValue(PARTCH_O7, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchU7(bool u7) {
    String show = String(u7 ? 1 : 0);
    _properties->setValue(PARTCH_U7, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchU7() {
    String val = _properties->getValue(PARTCH_U7, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchO9(bool o9) {
    String show = String(o9 ? 1 : 0);
    _properties->setValue(PARTCH_O9, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchO9() {
    String val = _properties->getValue(PARTCH_O9, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchU9(bool u9) {
    String show = String(u9 ? 1 : 0);
    _properties->setValue(PARTCH_U9, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchU9() {
    String val = _properties->getValue(PARTCH_U9, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchO11(bool o11) {
    String show = String(o11 ? 1 : 0);
    _properties->setValue(PARTCH_O11, show);
    _properties->saveIfNeeded();
}

bool WilsonicProcessor::restorePartchO11() {
    String val = _properties->getValue(PARTCH_O11, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}

void WilsonicProcessor::savePartchU11(bool u11) {
    String show = String(u11 ? 1 : 0);
    _properties->setValue(PARTCH_U11, show);
    _properties->saveIfNeeded();
}
                 
bool WilsonicProcessor::restorePartchU11() {
    String val = _properties->getValue(PARTCH_U11, "0");
    int const val_int = val.getIntValue();
    bool const retVal = (val_int == 0) ? false : true;

    return retVal;
}
