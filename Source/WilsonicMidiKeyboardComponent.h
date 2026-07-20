/**
 * @file WilsonicMidiKeyboardComponent.h
 * @brief Contains the declaration of the WilsonicMidiKeyboardComponent class.
 */

#pragma once

#include <JuceHeader.h>
#include "AppTuningModel.h"
#include "WilsonicAppSkin.h"
#include "WilsonicProcessorConstants.h"

// forward
class WilsonicProcessor;

/**
 * @class WilsonicMidiKeyboardComponent
 * @brief A class that represents a MIDI keyboard component.
 *
 * This class is responsible for handling MIDI keyboard input and displaying the keyboard on the screen. It provides methods for setting and getting various properties of the keyboard, such as the MIDI channel, key width, display mode, orientation, and range. It also provides methods for handling mouse and key events, and for drawing the keyboard.
 */
class WilsonicMidiKeyboardComponent
: public Component
, public MidiKeyboardState::Listener
, public ChangeBroadcaster
, public ActionListener
, private Timer
{
public:
    /**
     * @enum DisplayMode
     * @brief An enumeration of the different display modes for the keyboard.
     */
    enum DisplayMode
    {
        linear, /**< A linear display mode. */
        linearDarkMode, /**< A linear display mode with a dark theme. */
        microtonal, /**< A microtonal display mode. */
    };

    /**
     * @enum Orientation
     * @brief An enumeration of the different orientations for the keyboard.
     */
    enum Orientation
    {
        horizontalKeyboard, /**< A horizontal keyboard orientation. */
        verticalKeyboardFacingLeft, /**< A vertical keyboard orientation facing left. */
        verticalKeyboardFacingRight, /**< A vertical keyboard orientation facing right. */
    };

    /**
     * @brief Constructs a WilsonicMidiKeyboardComponent object.
     *
     * @param processor A reference to the WilsonicProcessor object.
     * @param orientation The orientation of the keyboard.
     */
    WilsonicMidiKeyboardComponent(WilsonicProcessor& processor, Orientation orientation);

    /**
     * @brief Destroys the WilsonicMidiKeyboardComponent object.
     */
    ~WilsonicMidiKeyboardComponent() override;

public:

#pragma mark -

    // whiteNotes and blackNotes are used for linear and linearDarkMode display modes, not microtonal
    const int whiteNotes[7] = { 0, 2, 4, 5, 7, 9, 11 };
    const int blackNotes[5] = { 1, 3, 6, 8, 10 };

    // https://gmcerveny.medium.com/midi-note-number-chart-for-ios-music-apps-b3c01df3cb19
    const bool ivory_key[WilsonicProcessorConstants::numMidiNotes] = {
        true, false, true, false, true, true, false, true, false, true, false, true, // -1
        true, false, true, false, true, true, false, true, false, true, false, true, // 0
        true, false, true, false, true, true, false, true, false, true, false, true, // 1
        true, false, true, false, true, true, false, true, false, true, false, true, // 2
        true, false, true, false, true, true, false, true, false, true, false, true, // 3
        true, false, true, false, true, true, false, true, false, true, false, true, // 4 (60 = middle c)
        true, false, true, false, true, true, false, true, false, true, false, true, // 5
        true, false, true, false, true, true, false, true, false, true, false, true, // 6
        true, false, true, false, true, true, false, true, false, true, false, true, // 7
        true, false, true, false, true, true, false, true, false, true, false, true, // 8
        true, false, true, false, true, true, false, true                            // 9
    };

    void setVelocity(float velocity, bool useMousePositionForVelocity);

    /**
     * @brief Sets the MIDI channel of the keyboard.
     *
     * @param midiChannelNumber The MIDI channel number to set.
     */
    void setMidiChannel(int midiChannelNumber);

    /**
     * @brief Returns the MIDI channel of the keyboard.
     *
     * @return The MIDI channel of the keyboard.
     */
    int getMidiChannel() const noexcept                             { return _midiChannel; }

    /**
     * @brief Sets the MIDI channels to display on the keyboard.
     *
     * @param midiChannelMask The MIDI channel mask to set.
     */
    void setMidiChannelsToDisplay(int midiChannelMask);

    /**
     * @brief Returns the MIDI channels to display on the keyboard.
     *
     * @return The MIDI channels to display on the keyboard.
     */
    int getMidiChannelsToDisplay() const noexcept                   { return _midiInChannelMask; }

    /**
     * @brief Sets the key width of the keyboard.
     *
     * @param widthInPixels The key width in pixels to set.
     */
    void setKeyWidth(float widthInPixels);

    /**
     * @brief Returns the key width of the keyboard.
     *
     * @return The key width of the keyboard.
     */
    float getKeyWidth() const noexcept                              { return _keyWidth; }

    /**
     * @brief Sets the scroll button width of the keyboard.
     *
     * @param widthInPixels The scroll button width in pixels to set.
     */
    void setScrollButtonWidth(int widthInPixels);

    /**
     * @brief Returns the scroll button width of the keyboard.
     *
     * @return The scroll button width of the keyboard.
     */
    int getScrollButtonWidth() const noexcept                       { return _scrollButtonWidth; }

    /**
     * @brief Sets the display mode of the keyboard.
     *
     * @param newDisplayMode The new display mode to set.
     */
    void setDisplayMode(DisplayMode newDisplayMode);

    /**
     * @brief Returns the display mode of the keyboard.
     *
     * @return The display mode of the keyboard.
     */
    DisplayMode getDisplayMode() const noexcept                     { return _displayMode; }

    /**
     * @brief Sets the orientation of the keyboard.
     *
     * @param newOrientation The new orientation to set.
     */
    void setOrientation(Orientation newOrientation);

    /**
     * @brief Returns the orientation of the keyboard.
     *
     * @return The orientation of the keyboard.
     */
    Orientation getOrientation() const noexcept                     { return _orientation; }

    /**
     * @brief Sets the available range of the keyboard.
     *
     * @param lowestNote The lowest note to set.
     * @param highestNote The highest note to set.
     */
    void setAvailableRange(int lowestNote, int highestNote);

    /**
     * @brief Adjusts the key size factor by a delta.
     *
     * @param delta The delta to adjust by. Can be negative.
     */
    void adjustKeySizeFactorByDelta(int delta);

    /**
     * @brief Returns the start of the range of the keyboard.
     *
     * @return The start of the range of the keyboard.
     */
    int getRangeStart() const noexcept                              { return _rangeStart; }

    /**
     * @brief Returns the end of the range of the keyboard.
     *
     * @return The end of the range of the keyboard.
     */
    int getRangeEnd() const noexcept                                { return _rangeEnd; }

    /**
     * @brief Sets the lowest visible key of the keyboard.
     *
     * @param noteNumber The note number to set as the lowest visible key.
     */
    void setLowestVisibleKey(int noteNumber);

    /**
     * @brief Returns the lowest visible key of the keyboard.
     *
     * @return The lowest visible key of the keyboard.
     */
    int getLowestVisibleKey() const noexcept                        { return static_cast<int>(_firstKey); }

    /**
     * @brief Sets the black note length proportion of the keyboard.
     *
     * @param ratio The ratio to set.
     */
    void setBlackNoteLengthProportion(float ratio) noexcept;

    /**
     * @brief Returns the black note length proportion of the keyboard.
     *
     * @return The black note length proportion of the keyboard.
     */
    float getBlackNoteLengthProportion() const noexcept             { return _blackNoteLengthRatio; }

    /**
     * @brief Returns the black note length of the keyboard.
     *
     * @return The black note length of the keyboard.
     */
    float getBlackNoteLength() const noexcept;

    /**
     * @brief Sets the black note width proportion of the keyboard.
     *
     * @param ratio The ratio to set.
     */
    void setBlackNoteWidthProportion(float ratio) noexcept;

    /**
     * @brief Returns the black note width proportion of the keyboard.
     *
     * @return The black note width proportion of the keyboard.
     */
    float getBlackNoteWidthProportion() const noexcept             { return _blackNoteWidthRatio; }

    /**
     * @brief Returns the black note width of the keyboard.
     *
     * @return The black note width of the keyboard.
     */
    float getBlackNoteWidth() const noexcept                       { return _keyWidth * _blackNoteWidthRatio; }

    /**
     * @brief Sets whether the scroll buttons are visible on the keyboard.
     *
     * @param canScroll A boolean indicating whether the scroll buttons can be visible.
     */
    void setScrollButtonsVisible(bool canScroll);

    /**
     * @enum ColourIds
     * @brief An enumeration of the different colour IDs for the keyboard.
     */
    enum ColourIds
    {
        whiteNoteColourId               = 0x1005000, /**< The colour ID for white notes. */
        blackNoteColourId               = 0x1005001, /**< The colour ID for black notes. */
        keySeparatorLineColourId        = 0x1005002, /**< The colour ID for the key separator line. */
        mouseOverKeyOverlayColourId     = 0x1005003, /**< The colour ID for the mouse over key overlay. */
        keyDownOverlayColourId          = 0x1005004, /**< The colour ID for the key down overlay. */
        textLabelColourId               = 0x1005005, /**< The colour ID for the text label. */
        shadowColourId                  = 0x1005006, /**< The colour ID for the shadow. */
        upDownButtonBackgroundColourId  = 0x1004000, /**< The colour ID for the up/down button background. */
        upDownButtonArrowColourId       = 0x1004001 /**< The colour ID for the up/down button arrow. */
    };

    /**
     * @brief Returns the start position of a key on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the key.
     * @return The start position of the key.
     */
    float getKeyStartPosition(int midiNoteNumber) const;

    /**
     * @brief Returns the total width of the keyboard.
     *
     * @return The total width of the keyboard.
     */
    float getTotalKeyboardWidth() const noexcept;

    /**
     * @brief Returns the note at a given position on the keyboard.
     *
     * @param position The position to get the note at.
     * @return The note at the given position.
     */
    int getNoteAtPosition(Point<float> position);

    /**
     * @brief Clears the key mappings of the keyboard.
     */
    void clearKeyMappings();

    /**
     * @brief Sets a key press for a note on the keyboard.
     *
     * @param key The key press to set.
     * @param midiNoteOffsetFromC The MIDI note offset from C to set the key press for.
     */
    void setKeyPressForNote(const KeyPress& key, int midiNoteOffsetFromC);

    /**
     * @brief Removes a key press for a note on the keyboard.
     *
     * @param midiNoteOffsetFromC The MIDI note offset from C to remove the key press for.
     */
    void removeKeyPressForNote(int midiNoteOffsetFromC);

    /**
     * @brief Sets the base octave for key presses on the keyboard.
     *
     * @param newOctaveNumber The new base octave number to set.
     */
    void setKeyPressBaseOctave(int newOctaveNumber);

    /**
     * @brief Sets the octave for middle C on the keyboard.
     *
     * @param octaveNumForMiddleC The octave number for middle C to set.
     */
    void setOctaveForMiddleC(int octaveNumForMiddleC);

    /**
     * @brief Returns the octave for middle C on the keyboard.
     *
     * @return The octave for middle C on the keyboard.
     */
    int getOctaveForMiddleC() const noexcept            { return _octaveNumForMiddleC; }

    //==============================================================================
    /**
     * @brief Paints the keyboard.
     *
     * @param g The Graphics object to use for painting.
     */
    void paint(Graphics&) override;

    /**
     * @brief Resizes the keyboard.
     */
    void resized() override;

    /**
     * @brief Handles mouse move events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     */
    void mouseMove(const MouseEvent&) override;

    /**
     * @brief Handles mouse drag events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     */
    void mouseDrag(const MouseEvent&) override;

    /**
     * @brief Handles mouse down events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     */
    void mouseDown(const MouseEvent&) override;

    /**
     * @brief Handles mouse up events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     */
    void mouseUp(const MouseEvent&) override;

    /**
     * @brief Handles mouse enter events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     */
    void mouseEnter(const MouseEvent&) override;

    /**
     * @brief Handles mouse exit events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     */
    void mouseExit(const MouseEvent&) override;

    /**
     * @brief Handles mouse wheel move events on the keyboard.
     *
     * @param e The MouseEvent object containing the details of the event.
     * @param wheel The MouseWheelDetails object containing the details of the wheel movement.
     */
    void mouseWheelMove(const MouseEvent&, const MouseWheelDetails&) override;

    /**
     * @brief Handles timer callbacks for the keyboard.
     */
    void timerCallback() override;

    /**
     * @brief Handles key state changes on the keyboard.
     *
     * @param isKeyDown A boolean indicating whether a key is down.
     * @return A boolean indicating whether the key state change was handled.
     */
    bool keyStateChanged(bool isKeyDown) override;

    /**
     * @brief Handles key presses on the keyboard.
     *
     * @param key The KeyPress object containing the details of the key press.
     * @return A boolean indicating whether the key press was handled.
     */
    bool keyPressed(const KeyPress&) override;

    /**
     * @brief Handles focus loss events on the keyboard.
     *
     * @param cause The FocusChangeType object indicating the cause of the focus loss.
     */
    void focusLost(FocusChangeType) override;

    /**
     * @brief Handles note on events on the keyboard.
     *
     * @param source The MidiKeyboardState object that is the source of the event.
     * @param midiChannel The MIDI channel of the note.
     * @param midiNoteNumber The MIDI note number of the note.
     * @param velocity The velocity of the note.
     */
    void handleNoteOn(MidiKeyboardState*, int midiChannel, int midiNoteNumber, float velocity) override;

    /**
     * @brief Handles note off events on the keyboard.
     *
     * @param source The MidiKeyboardState object that is the source of the event.
     * @param midiChannel The MIDI channel of the note.
     * @param midiNoteNumber The MIDI note number of the note.
     * @param velocity The velocity of the note.
     */
    void handleNoteOff(MidiKeyboardState*, int midiChannel, int midiNoteNumber, float velocity) override;

    /**
     * @brief Handles colour changes on the keyboard.
     */
    void colourChanged() override;

protected:
    /**
     * @brief Draws a white note on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the note.
     * @param g The Graphics object to use for drawing.
     * @param area The area to draw in.
     * @param isDown A boolean indicating whether the note is down.
     * @param isOver A boolean indicating whether the mouse is over the note.
     * @param lineColour The colour of the line.
     * @param textColour The colour of the text.
     */
    virtual void drawWhiteNote(int midiNoteNumber,
                                Graphics& g,
                                Rectangle<float> area,
                                bool isDown,
                                bool isOver,
                                Colour lineColour,
                                Colour textColour);

    /**
     * @brief Draws a black note on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the note.
     * @param g The Graphics object to use for drawing.
     * @param area The area to draw in.
     * @param isDown A boolean indicating whether the note is down.
     * @param isOver A boolean indicating whether the mouse is over the note.
     * @param noteFillColour The fill colour of the note.
     */
    virtual void drawBlackNote(int midiNoteNumber,
                                Graphics& g,
                                Rectangle<float> area,
                                bool isDown,
                                bool isOver,
                                Colour noteFillColour);

    /**
     * @brief Draws a microtonal note on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the note.
     * @param g The Graphics object to use for drawing.
     * @param area The area to draw in.
     * @param isDown A boolean indicating whether the note is down.
     * @param isOver A boolean indicating whether the mouse is over the note.
     * @param lineColour The colour of the line.
     * @param textColour The colour of the text.
     */
    virtual void drawMicrotonalNote(int midiNoteNumber,
                                     Graphics& g,
                                     Rectangle<float> area,
                                     bool isDown,
                                     bool isOver,
                                     Colour lineColour,
                                     Colour textColour);

    /**
     * @brief Returns a description of a note on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the note.
     * @return A string containing the description of the note.
     */
    virtual String getNoteDescription(int midiNoteNumber);

    /**
     * @brief Returns a second description of a note on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the note.
     * @return A string containing the second description of the note.
     */
    virtual String getNoteDescription2(int midiNoteNumber);

    /**
     * @brief Draws an up/down button on the keyboard.
     *
     * @param g The Graphics object to use for drawing.
     * @param w The width of the button.
     * @param h The height of the button.
     * @param isMouseOver A boolean indicating whether the mouse is over the button.
     * @param isButtonPressed A boolean indicating whether the button is pressed.
     * @param movesOctavesUp A boolean indicating whether the button moves octaves up.
     */
    virtual void drawUpDownButton(Graphics& g,
                                   int w,
                                   int h,
                                   bool isMouseOver,
                                   bool isButtonPressed,
                                   bool movesOctavesUp);

    /**
     * @brief Handles mouse down events on a key on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the key.
     * @param e The MouseEvent object containing the details of the event.
     * @return A boolean indicating whether the mouse down event was handled.
     */
    virtual bool mouseDownOnKey(int midiNoteNumber, const MouseEvent& e);

    /**
     * @brief Handles mouse dragged events to a key on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the key.
     * @param e The MouseEvent object containing the details of the event.
     * @return A boolean indicating whether the mouse dragged event was handled.
     */
    virtual bool mouseDraggedToKey(int midiNoteNumber, const MouseEvent& e);

    /**
     * @brief Handles mouse up events on a key on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the key.
     * @param e The MouseEvent object containing the details of the event.
     */
    virtual void mouseUpOnKey(int midiNoteNumber,const MouseEvent& e);

    /**
     * @brief Returns the position of a key on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the key.
     * @param keyWidth The width of the key.
     * @return A Range object containing the position of the key.
     */
    virtual Range<float> getKeyPosition(int midiNoteNumber, float keyWidth) const;

    /**
     * @brief Returns the rectangle for a key on the keyboard.
     *
     * @param midiNoteNumber The MIDI note number of the key.
     * @return A Rectangle object containing the rectangle for the key.
     */
    Rectangle<float> getRectangleForKey(int midiNoteNumber) const;

private:
    // Private members
    static constexpr float __minimum_keyWidth = 16.f; ///< Minimum width of a key
    WilsonicProcessor& _processor; ///< Reference to the WilsonicProcessor
    struct UpDownButton; ///< Structure for UpDownButton
    float _blackNoteLengthRatio = 0.7f; ///< Ratio of black note length
    float _blackNoteWidthRatio = 0.7f; ///< Ratio of black note width
    float _xOffset = 0; ///< Offset in x direction
    float _keyWidth = 32.f; ///< Width of a key
    float _keyWidthFactor = 6.f; ///< Factor for key width
    static constexpr float __keyWidthFactorMin = 4.f; ///< Minimum key width factor
    static constexpr float __keyWidthFactorMax = 8.f; ///< Maximum key width factor
    int _scrollButtonWidth = 12; ///< Width of scroll button
    Orientation _orientation = horizontalKeyboard; ///< Orientation of keyboard
    DisplayMode _displayMode = microtonal; ///< Display mode of keyboard
    int _midiChannel = 1; ///< MIDI channel
    int _midiInChannelMask = 0xffff; ///< Mask for MIDI input channel
    float _velocity = 1.0f; ///< Velocity of MIDI note
    Array<int> _mouseOverNotes; ///< Array of notes over which mouse is hovering
    Array<int> _mouseDownNotes; ///< Array of notes which are being pressed
    BigInteger _keysPressed; ///< Bitset representing keys being pressed
    BigInteger _keysCurrentlyDrawnDown; ///< Bitset representing keys currently drawn down
    bool _shouldCheckState = false; ///< Flag to check state
    int _rangeStart = 0; ///< Start of MIDI note range
    int _rangeEnd = 127; ///< End of MIDI note range
    float _firstKey = 12 * 4.0f; ///< First key on the keyboard
    bool _canScroll = true; ///< Flag to enable scrolling
    bool _useMousePositionForVelocity = true; ///< Flag to use mouse position for velocity
    unique_ptr<Button> _scrollDown; ///< Unique pointer to scroll down button
    unique_ptr<Button> _scrollUp; ///< Unique pointer to scroll up button
    Array<KeyPress> _keyPresses; ///< Array of key presses
    Array<int> _keyPressNotes; ///< Array of notes corresponding to key presses
    int _keyMappingOctave = 6; ///< Octave for key mapping
    int _octaveNumForMiddleC = 3; ///< Octave number for Middle C
    unsigned long _debug_paint_counter = 0; ///< Counter for debug paint

    // Private member functions
    Rectangle<float> _getRectangleForKeyLinear(int note) const; ///< Get rectangle for key in linear mode
    Rectangle<float> _getRectangleForKeyMicrotonal(int note) const; ///< Get rectangle for key in microtonal mode
    Range<float> _getKeyPos(int midiNoteNumber) const; ///< Get position of key
    Range<float> _getKeyPositionLinear(int midiNoteNumber, float targetKeyWidth) const; ///< Get position of key in linear mode
    Range<float> _getKeyPositionMicrotonal(int midiNoteNumber, float targetKeyWidth) const; ///< Get position of key in microtonal mode
    int _xyToNote(Point<float>, float& mousePositionVelocity); ///< Convert x,y coordinates to note
    int _remappedXYToNote(Point<float>, float& mousePositionVelocity) const; ///< Remap x,y coordinates to note
    int _remappedXYToNoteLinear(Point<float> pos, float& mousePositionVelocity) const; ///< Remap x,y coordinates to note in linear mode
    int _remappedXYToNoteMicrotonal(Point<float> pos, float& mousePositionVelocity) const; ///< Remap x,y coordinates to note in microtonal mode
    int _slotToMidiNote(int slot) const; ///< Genus Space: map a drawn key slot to its MIDI note number (identity when no keyboard subset is active)
    void _resetAnyKeysInUse(); ///< Reset any keys in use
    void _updateNoteUnderMouse(Point<float>, bool isDown, int fingerNum); ///< Update note under mouse
    void _updateNoteUnderMouse(const MouseEvent&, bool isDown); ///< Update note under mouse
    void _repaintNote(int midiNoteNumber); ///< Repaint a note
    void _paint_microtonal(Graphics& g); ///< Paint in microtonal mode
    void _paint_linear(Graphics& g); ///< Paint in linear mode
    void _setLowestVisibleKeyFloat(float noteNumber); ///< Set lowest visible key
    String _getNoteTextLinear(int midiNoteNumber); ///< Get note text in linear mode
    String _getNoteTextMicrotonal(int midiNoteNumber); ///< Get note text in microtonal mode
    String _getNoteTextMicrotonal2(int midiNoteNumber); ///< Get note text in microtonal mode (alternative)
    String _getNoteCentsDescription(int midiNoteNumber);

    // ActionListener callback
    void actionListenerCallback(const String&) override; ///< ActionListener callback
};

