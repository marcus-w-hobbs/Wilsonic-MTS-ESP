#include "WilsonicMidiKeyboardComponent.h"
#include "AppTuningModel.h"
#include "AppExperiments.h"
#include "WilsonicProcessor.h"

#pragma mark - UpDownButton

struct WilsonicMidiKeyboardComponent::UpDownButton
: public Button
{
    UpDownButton(WilsonicMidiKeyboardComponent& c, int d)
    : Button({})
    , owner(c)
    , delta(d)
    {

    }

    void clicked() override {
        auto note = owner.getLowestVisibleKey();
        if (delta < 0)
            note = (note - 1) / 12;
        else
            note = note / 12 + 1;
        owner.setLowestVisibleKey(note * 12);
    }

    using Button::clicked;
    void paintButton(Graphics& g,
                      bool shouldDrawButtonAsHighlighted,
                      bool shouldDrawButtonAsDown) override {
        owner.drawUpDownButton(g,
                                getWidth(),
                                getHeight(),
                                shouldDrawButtonAsHighlighted,
                                shouldDrawButtonAsDown,
                                delta > 0);
    }

private:
    WilsonicMidiKeyboardComponent& owner;
    const int delta;
    JUCE_DECLARE_NON_COPYABLE(UpDownButton)
};

#pragma mark - WilsonicMidiKeyboardComponent lifecycle

WilsonicMidiKeyboardComponent::WilsonicMidiKeyboardComponent
(
WilsonicProcessor& processor,
Orientation orientation
)
: _processor(processor)
, _orientation(orientation)
, _displayMode(microtonal) // linear
{
    _scrollDown.reset(new UpDownButton(*this, -1));
    _scrollUp.reset(new UpDownButton(*this, 1));

    addChildComponent(_scrollDown.get());
    addChildComponent(_scrollUp.get());

    // initialise with a default set of qwerty key-mappings..
    int note = 0;

    for (char c : "awsedftgyhujkolp;")
        setKeyPressForNote(KeyPress(c, 0, 0), note++);

    _mouseOverNotes.insertMultiple(0, -1, 32);
    _mouseDownNotes.insertMultiple(0, -1, 32);

    colourChanged();
    setWantsKeyboardFocus(true);

    // listen for keyboard state changes
    _processor.getKeyboardState()->addListener(this);

    // listen for tuning changes
    _processor.getAppTuningModel()->addActionListener(this);

    // listen for skin changes
    _processor.getAppSkin().addActionListener(this);

    // timer
    if (AppExperiments::renderSynthKeyboard) {
        startTimerHz(AppExperiments::defaultTimerFrameRate);
    }

    //
    _keyWidthFactor = jlimit(__keyWidthFactorMin, __keyWidthFactorMax, _processor.restoreKeyboardWidthFactor());
}

WilsonicMidiKeyboardComponent::~WilsonicMidiKeyboardComponent() {
    if (AppExperiments::renderSynthKeyboard) {
        stopTimer();
    }
    _processor.getKeyboardState()->removeListener(this);
    _processor.getAppTuningModel()->removeActionListener(this);
    _processor.getAppSkin().removeActionListener(this);
}

#pragma mark - Display Parameters

void WilsonicMidiKeyboardComponent::setKeyWidth(float widthInPixels) {
    jassert(widthInPixels > 0);
    if (WilsonicMath::floatsAreNotEqual(_keyWidth, widthInPixels, WilsonicMath::Epsilon::UI)) { // Prevent infinite recursion if the width is being computed in a 'resized()' call-back
        _keyWidth = widthInPixels;
        resized();
    }
}

void WilsonicMidiKeyboardComponent::setScrollButtonWidth(int widthInPixels) {
    jassert(widthInPixels > 0);
    if (_scrollButtonWidth != widthInPixels) {
        _scrollButtonWidth = widthInPixels;
        resized();
    }
}

void WilsonicMidiKeyboardComponent::setDisplayMode(DisplayMode newDisplayMode) {
    if (_displayMode != newDisplayMode) {
        _displayMode = newDisplayMode;
        resized();
    }
}

void WilsonicMidiKeyboardComponent::setOrientation(Orientation newOrientation) {
    if (_orientation != newOrientation) {
        _orientation = newOrientation;
        resized();
    }
}

void WilsonicMidiKeyboardComponent::setAvailableRange(int lowestNote, int highestNote) {
    jassert(lowestNote >= 0 && lowestNote < static_cast<int>(WilsonicProcessorConstants::numMidiNotes));
    jassert(highestNote >= 0 && highestNote < static_cast<int>(WilsonicProcessorConstants::numMidiNotes));
    jassert(lowestNote <= highestNote);
    if (_rangeStart != lowestNote || _rangeEnd != highestNote) {
        _rangeStart = jlimit(0, static_cast<int>(WilsonicProcessorConstants::numMidiNotes) - 1, lowestNote);
        _rangeEnd = jlimit(0, static_cast<int>(WilsonicProcessorConstants::numMidiNotes) - 1, highestNote);
        _firstKey = jlimit(static_cast<float>(_rangeStart), static_cast<float>(_rangeEnd), _firstKey);
        resized();
    }
}

// delta is in pixels, and can be negative
void WilsonicMidiKeyboardComponent::adjustKeySizeFactorByDelta(int delta) {
    if (delta == 0) {
        return;
    }

    float ddelta = static_cast<float>(delta)/100.f;
    _keyWidthFactor = jlimit(__keyWidthFactorMin, __keyWidthFactorMax, _keyWidthFactor + ddelta);
    _processor.saveKeyboardWidthFactor(_keyWidthFactor);
    resized();
}

void WilsonicMidiKeyboardComponent::setLowestVisibleKey(int noteNumber) {
    _setLowestVisibleKeyFloat(static_cast<float>(noteNumber));
}

void WilsonicMidiKeyboardComponent::_setLowestVisibleKeyFloat(float noteNumber) {
    noteNumber = jlimit(static_cast<float>(_rangeStart), static_cast<float>(_rangeEnd), noteNumber);
    if (WilsonicMath::floatsAreNotEqual(noteNumber, _firstKey, WilsonicMath::Epsilon::UI)) {
        bool hasMoved = (static_cast<int>(_firstKey) != static_cast<int>(noteNumber));
        _firstKey = noteNumber;
        if (hasMoved)
            sendChangeMessage();
        resized();
    }
}

void WilsonicMidiKeyboardComponent::setScrollButtonsVisible(bool newCanScroll) {
    if (_canScroll != newCanScroll) {
        _canScroll = newCanScroll;
        resized();
    }
}

void WilsonicMidiKeyboardComponent::colourChanged() {
    setOpaque(findColour(whiteNoteColourId).isOpaque());
    repaint();
}

#pragma mark - MIDI

void WilsonicMidiKeyboardComponent::setMidiChannel(int midiChannelNumber) {
    jassert(midiChannelNumber > 0 && midiChannelNumber <= 16);
    if (_midiChannel != midiChannelNumber) {
        _resetAnyKeysInUse();
        _midiChannel = jlimit(1, 16, midiChannelNumber);
    }
}

void WilsonicMidiKeyboardComponent::setMidiChannelsToDisplay(int midiChannelMask) {
    _midiInChannelMask = midiChannelMask;
    _shouldCheckState = true;
}

void WilsonicMidiKeyboardComponent::setVelocity(float v, bool useMousePosition) {
    _velocity = jlimit(0.0f, 1.0f, v);
    _useMousePositionForVelocity = useMousePosition;
}

#pragma mark - Key Coordinates

Range<float> WilsonicMidiKeyboardComponent::getKeyPosition(int midiNoteNumber, float targetKeyWidth) const {
    jassert(midiNoteNumber >= 0 && midiNoteNumber < static_cast<int>(WilsonicProcessorConstants::numMidiNotes));

    switch (_displayMode) {
        case microtonal:
            return _getKeyPositionMicrotonal(midiNoteNumber, targetKeyWidth);
        case linear : case linearDarkMode : default :
            return _getKeyPositionLinear(midiNoteNumber, targetKeyWidth);
    }

    // pre-emptive defensiveness
    return { 0, 1 };
}

// Genus Space: the keyboard operates in "slot" space; when a keyboard subset is
// active a slot maps to its note number in the full table, otherwise identity
int WilsonicMidiKeyboardComponent::_slotToMidiNote(int slot) const {
    if (slot < 0) {
        return slot;
    }

    return _processor.getAppTuningModel()->keyboardSlotToNoteNumber(slot);
}

Range<float> WilsonicMidiKeyboardComponent::_getKeyPositionMicrotonal(int midiNoteNumber, float targetKeyWidth) const {
    jassert(midiNoteNumber >= 0 && midiNoteNumber < static_cast<int>(WilsonicProcessorConstants::numMidiNotes));
    auto npo = static_cast<int>(_processor.getAppTuningModel()->getKeyboardNPO());
    jassert(npo > 0);
    auto const octave = midiNoteNumber / npo;
    auto const note   = midiNoteNumber % npo;
    auto const start = octave * npo * targetKeyWidth + note * targetKeyWidth;
    auto const width = targetKeyWidth;

    return { start, start + width };
}

Range<float> WilsonicMidiKeyboardComponent::_getKeyPositionLinear(int midiNoteNumber, float targetKeyWidth) const {
    jassert(midiNoteNumber >= 0 && midiNoteNumber < static_cast<int>(WilsonicProcessorConstants::numMidiNotes));
    static const float notePos[] = { 0.0f, 1 - _blackNoteWidthRatio * 0.6f,
        1.0f, 2 - _blackNoteWidthRatio * 0.4f,
        2.0f,
        3.0f, 4 - _blackNoteWidthRatio * 0.7f,
        4.0f, 5 - _blackNoteWidthRatio * 0.5f,
        5.0f, 6 - _blackNoteWidthRatio * 0.3f,
        6.0f };
    auto octave = midiNoteNumber / 12;
    auto note   = midiNoteNumber % 12;
    auto start = static_cast<float>(octave) * 7.0f * targetKeyWidth + notePos[note] * targetKeyWidth;
    auto width = MidiMessage::isMidiNoteBlack(note) ? _blackNoteWidthRatio * targetKeyWidth : targetKeyWidth;

    return { start, start + width };
}

Range<float> WilsonicMidiKeyboardComponent::_getKeyPos(int midiNoteNumber) const {
    return getKeyPosition(midiNoteNumber, _keyWidth)
    - _xOffset
    - getKeyPosition(_rangeStart, _keyWidth).getStart();
}

Rectangle<float> WilsonicMidiKeyboardComponent::getRectangleForKey(int note) const {
    switch (_displayMode) {
        case microtonal:
            return _getRectangleForKeyMicrotonal(note);
        case linear:
        case linearDarkMode:
        default:
            return _getRectangleForKeyLinear(note);
    }
    
    return {};
}

Rectangle<float> WilsonicMidiKeyboardComponent::_getRectangleForKeyLinear(int note) const {
    jassert(note >= _rangeStart && note <= _rangeEnd);
    auto pos = _getKeyPos(note);
    auto x = pos.getStart();
    auto w = pos.getLength();
    if (MidiMessage::isMidiNoteBlack(note)) {
        auto blackNoteLength = getBlackNoteLength();
        switch (_orientation) {
            case horizontalKeyboard:            return { x, 0, w, blackNoteLength };
            case verticalKeyboardFacingLeft:    return { (float) getWidth() - blackNoteLength, x, blackNoteLength, w };
            case verticalKeyboardFacingRight:   return { 0, (float) getHeight() - x - w, blackNoteLength, w };
            default:                            jassertfalse; break;
        }
    } else {
        switch (_orientation) {
            case horizontalKeyboard:            return { x, 0, w, (float) getHeight() };
            case verticalKeyboardFacingLeft:    return { 0, x, (float) getWidth(), w };
            case verticalKeyboardFacingRight:   return { 0, (float) getHeight() - x - w, (float) getWidth(), w };
            default:                            jassertfalse; break;
        }
    }
}

Rectangle<float> WilsonicMidiKeyboardComponent::_getRectangleForKeyMicrotonal(int note) const {
    jassert(note >= _rangeStart && note <= _rangeEnd);
    auto pos = _getKeyPos(note);
    auto x = pos.getStart();
    auto w = pos.getLength();
    switch (_orientation) {
        case horizontalKeyboard:            return { x, 0, w, (float) getHeight() };
        case verticalKeyboardFacingLeft:    return { 0, x, (float) getWidth(), w };
        case verticalKeyboardFacingRight:   return { 0, (float) getHeight() - x - w, (float) getWidth(), w };
        default:                            jassertfalse; break;
    }
}

float WilsonicMidiKeyboardComponent::getKeyStartPosition(int midiNoteNumber) const {
    return _getKeyPos(midiNoteNumber).getStart();
}

float WilsonicMidiKeyboardComponent::getTotalKeyboardWidth() const noexcept {
    return _getKeyPos(_rangeEnd).getEnd();
}

int WilsonicMidiKeyboardComponent::getNoteAtPosition(Point<float> p) {
    float v = 0;
    
    return _xyToNote(p, v);
}

int WilsonicMidiKeyboardComponent::_xyToNote(Point<float> pos, float& mousePositionVelocity) {
    if (! reallyContains(pos.toInt(), false))
        return -1;
    auto p = pos;
    if (_orientation != horizontalKeyboard) {
        p = { p.y, p.x };
        if (_orientation == verticalKeyboardFacingLeft)
            p = { p.x, (float) getWidth() - p.y };
        else
            p = { (float) getHeight() - p.x, p.y };
    }

    return _remappedXYToNote(p + Point<float>(_xOffset, 0), mousePositionVelocity);
}

int WilsonicMidiKeyboardComponent::_remappedXYToNote(Point<float> pos, float& mousePositionVelocity) const {
    switch (_displayMode) {
        case microtonal:
            return _remappedXYToNoteMicrotonal(pos, mousePositionVelocity);
        case linear : case linearDarkMode : default :
            return _remappedXYToNoteLinear(pos, mousePositionVelocity);
    }
}

int WilsonicMidiKeyboardComponent::_remappedXYToNoteMicrotonal(Point<float> pos, float& mousePositionVelocity) const {
    auto const npo = static_cast<int>(_processor.getAppTuningModel()->getKeyboardNPO());
    for (int octaveStart = npo * (_rangeStart / npo); octaveStart <= _rangeEnd; octaveStart += npo) {
        for (int i = 0; i < npo; ++i) {
            auto const note = octaveStart + i;
            if (note >= _rangeStart && note <= _rangeEnd && _slotToMidiNote(note) >= 0) {
                if (_getKeyPos(note).contains(pos.x - _xOffset)) {
                    auto const whiteNoteLength = (_orientation == horizontalKeyboard) ? getHeight() : getWidth();
                    mousePositionVelocity = jmax(0.f, pos.y / (float) whiteNoteLength);
                    return note;
                }
            }
        }
    }

    mousePositionVelocity = 0;
    return -1;
}

int WilsonicMidiKeyboardComponent::_remappedXYToNoteLinear(Point<float> pos, float& mousePositionVelocity) const {
    auto blackNoteLength = getBlackNoteLength();
    if (pos.getY() < blackNoteLength) {
        for (int octaveStart = 12 * (_rangeStart / 12); octaveStart <= _rangeEnd; octaveStart += 12) {
            for (int i = 0; i < 5; ++i) {
                auto note = octaveStart + blackNotes[i];
                if (note >= _rangeStart && note <= _rangeEnd) {
                    if (_getKeyPos(note).contains(pos.x - _xOffset)) {
                        mousePositionVelocity = jmax(0.0f, pos.y / blackNoteLength);
                        return note;
                    }
                }
            }
        }
    }

    for (int octaveStart = 12 * (_rangeStart / 12); octaveStart <= _rangeEnd; octaveStart += 12) {
        for (int i = 0; i < 7; ++i) {
            auto note = octaveStart + whiteNotes[i];
            if (note >= _rangeStart && note <= _rangeEnd) {
                if (_getKeyPos(note).contains(pos.x - _xOffset)) {
                    auto whiteNoteLength = (_orientation == horizontalKeyboard) ? getHeight() : getWidth();
                    mousePositionVelocity = jmax(0.0f, pos.y / (float) whiteNoteLength);
                    return note;
                }
            }
        }
    }

    mousePositionVelocity = 0;
    return -1;
}

#pragma mark - Misc

void WilsonicMidiKeyboardComponent::setOctaveForMiddleC(int octaveNum) {
    _octaveNumForMiddleC = octaveNum;
    repaint();
}

String WilsonicMidiKeyboardComponent::getNoteDescription(int midiNoteNumber) {
    String retVal = {};
    switch (_displayMode) {
        case microtonal:
            return _getNoteTextMicrotonal(midiNoteNumber);
        case linear : case linearDarkMode : default:
            return _getNoteTextLinear(midiNoteNumber);
    }

    return retVal;
}

String WilsonicMidiKeyboardComponent::getNoteDescription2(int midiNoteNumber) {
    String retVal = {};
    switch (_displayMode) {
        case microtonal:
            return _getNoteTextMicrotonal2(midiNoteNumber);
        case linear : case linearDarkMode : default:
            return _getNoteTextLinear(midiNoteNumber);
    }

    return retVal;
}


String WilsonicMidiKeyboardComponent::_getNoteTextLinear(int midiNoteNumber) {
    String retVal = {};
    if (midiNoteNumber % 12 == 0) {
        retVal = MidiMessage::getMidiNoteName(midiNoteNumber, true, true, _octaveNumForMiddleC);
    }

    return retVal;
}

String WilsonicMidiKeyboardComponent::_getNoteTextMicrotonal(int midiNoteNumber) {
    String retVal = {};
    auto md = _processor.getAppTuningModel()->getTuningTableShortDescription(static_cast<unsigned long>(midiNoteNumber));
    retVal = String(md);

    return retVal;
}

String WilsonicMidiKeyboardComponent::_getNoteTextMicrotonal2(int midiNoteNumber) {
    String retVal = {};
    auto md = _processor.getAppTuningModel()->getTuningTableShortDescription2(static_cast<unsigned long>(midiNoteNumber));
    retVal = String(md);

    return retVal;
}

String WilsonicMidiKeyboardComponent::_getNoteCentsDescription(int midiNoteNumber) {
    String retVal = {};
    auto md = _processor.getAppTuningModel()->getTuningTableCentsDescription(static_cast<unsigned long>(midiNoteNumber));
    retVal = String(md);

    return retVal;
}


void WilsonicMidiKeyboardComponent::drawUpDownButton
(
  Graphics& g,
  int w,
  int h,
  bool mouseOver,
  bool buttonDown,
  bool movesOctavesUp
  )
{
    g.fillAll(findColour(upDownButtonBackgroundColourId));
    float angle = 0;
    switch (_orientation) {
        case horizontalKeyboard:            angle = movesOctavesUp ? 0.0f  : 0.5f;  break;
        case verticalKeyboardFacingLeft:    angle = movesOctavesUp ? 0.25f : 0.75f; break;
        case verticalKeyboardFacingRight:   angle = movesOctavesUp ? 0.75f : 0.25f; break;
        default:                            jassertfalse; break;
    }

    Path path;
    path.addTriangle(0.f, 0.f, 0.f, 1.f, 1.f, 0.5f);
    path.applyTransform(AffineTransform::rotation(MathConstants<float>::twoPi * angle, 0.5f, 0.5f));
    g.setColour(findColour(upDownButtonArrowColourId)
                 .withAlpha(buttonDown ? 1.f : (mouseOver ? 0.6f : 0.4f)));
    g.fillPath(path, path.getTransformToScaleToFit(1.f, 1.f, (float) w - 2.f, (float) h - 2.f, true));
}

void WilsonicMidiKeyboardComponent::setBlackNoteLengthProportion(float ratio) noexcept {
    jassert(ratio >= 0.f && ratio <= 1.f);
    if(WilsonicMath::floatsAreNotEqual(_blackNoteLengthRatio, ratio, WilsonicMath::Epsilon::UI)) {
        _blackNoteLengthRatio = ratio;
        resized();
    }
}

float WilsonicMidiKeyboardComponent::getBlackNoteLength() const noexcept {
    auto whiteNoteLength = _orientation == horizontalKeyboard ? getHeight() : getWidth();
    return (float) whiteNoteLength * _blackNoteLengthRatio;
}

void WilsonicMidiKeyboardComponent::setBlackNoteWidthProportion(float ratio) noexcept {
    jassert(ratio >= 0.0f && ratio <= 1.0f);
    if (WilsonicMath::floatsAreNotEqual(_blackNoteWidthRatio, ratio, WilsonicMath::Epsilon::UI)) {
        _blackNoteWidthRatio = ratio;
        resized();
    }
}

#pragma mark - RESIZED

void WilsonicMidiKeyboardComponent::resized() {
    auto w = getWidth();
    auto h = getHeight();
    auto const wf = _displayMode == microtonal ? _keyWidthFactor : 1.f;// key width
    auto kw = wf * w / (float)WilsonicProcessorConstants::numMidiNotes;
    if (kw < __minimum_keyWidth) kw = __minimum_keyWidth;
    _keyWidth = kw;
    if (w > 0 && h > 0) {
        if (_orientation != horizontalKeyboard)
            swap (w, h);
        auto kx2 = _getKeyPos(_rangeEnd).getEnd();
        if (static_cast<int>(_firstKey) != _rangeStart) {
            auto kx1 = _getKeyPos(_rangeStart).getStart();
            if (kx2 - kx1 <= (float) w) {
                _firstKey = (float) _rangeStart;
                sendChangeMessage();
                repaint();
            }
        }
        _scrollDown->setVisible(_canScroll && _firstKey > (float) _rangeStart);
        _xOffset = 0;
        if (_canScroll) {
            auto scrollButtonW = jmin(_scrollButtonWidth, w / 2);
            auto r = getLocalBounds();
            if (_orientation == horizontalKeyboard) {
                _scrollDown->setBounds(r.removeFromLeft (scrollButtonW));
                _scrollUp  ->setBounds(r.removeFromRight(scrollButtonW));
            } else if (_orientation == verticalKeyboardFacingLeft) {
                _scrollDown->setBounds(r.removeFromTop   (scrollButtonW));
                _scrollUp  ->setBounds(r.removeFromBottom(scrollButtonW));
            } else {
                _scrollDown->setBounds(r.removeFromBottom(scrollButtonW));
                _scrollUp  ->setBounds(r.removeFromTop   (scrollButtonW));
            }

            auto endOfLastKey = _getKeyPos(_rangeEnd).getEnd();
            float mousePositionVelocity;
            auto spaceAvailable = w;
            auto lastStartKey = _remappedXYToNote({ endOfLastKey - (float) spaceAvailable, 0 }, mousePositionVelocity) + 1;
            if (lastStartKey >= 0 && static_cast<int>(_firstKey) > lastStartKey) {
                _firstKey = (float) jlimit(_rangeStart, _rangeEnd, lastStartKey);
                sendChangeMessage();
            }

            _xOffset = _getKeyPos(static_cast<int>(_firstKey)).getStart();
        } else {
            _firstKey = (float) _rangeStart;
        }

        _scrollUp->setVisible(_canScroll && _getKeyPos(_rangeEnd).getStart() > (float) w);
        repaint();
    }
}

#pragma mark - Handle Note On/Off

void WilsonicMidiKeyboardComponent::handleNoteOn(MidiKeyboardState* keyboardState, int midiChannel, int midiNoteNumber, float velocity) {
    ignoreUnused(keyboardState);
    ignoreUnused(midiChannel);
    ignoreUnused(midiNoteNumber);
    ignoreUnused(velocity);
    _shouldCheckState = true; // (probably being called from the audio thread, so avoid blocking in here)
}

void WilsonicMidiKeyboardComponent::handleNoteOff(MidiKeyboardState* keyboardState, int midiChannel, int midiNoteNumber, float velocity) {
    ignoreUnused(keyboardState);
    ignoreUnused(midiChannel);
    ignoreUnused(midiNoteNumber);
    ignoreUnused(velocity);
    _shouldCheckState = true; // (probably being called from the audio thread, so avoid blocking in here)
}

#pragma mark - Mouse Events

void WilsonicMidiKeyboardComponent::_resetAnyKeysInUse() {
    if (!_keysPressed.isZero()) {
        for (int i = static_cast<int>(WilsonicProcessorConstants::numMidiNotes); --i >= 0;) {
            if (_keysPressed[i]) {
                _processor.getKeyboardState()->noteOff(_midiChannel, i, 0.0f);
            }
        }
        _keysPressed.clear();
    }

    for (int i = _mouseDownNotes.size(); --i >= 0;) {
        auto noteDown = _mouseDownNotes.getUnchecked(i);
        if (noteDown >= 0) {
            _processor.getKeyboardState()->noteOff(_midiChannel, _slotToMidiNote(noteDown), 0.0f);
            _mouseDownNotes.set(i, -1);
        }
        _mouseOverNotes.set(i, -1);
    }
}

void WilsonicMidiKeyboardComponent::_updateNoteUnderMouse(const MouseEvent& e, bool isDown) {
    _updateNoteUnderMouse(e.getEventRelativeTo(this).position, isDown, e.source.getIndex());
}

void WilsonicMidiKeyboardComponent::_updateNoteUnderMouse(Point<float> pos, bool isDown, int fingerNum) {
    float mousePositionVelocity = 0.0f;
    auto const newNote = _xyToNote(pos, mousePositionVelocity);
    auto const oldNote = _mouseOverNotes.getUnchecked(fingerNum);
    auto const oldNoteDown = _mouseDownNotes.getUnchecked(fingerNum);
    auto const eventVelocity = _useMousePositionForVelocity ? mousePositionVelocity * _velocity : _velocity;

    if (oldNote != newNote) {
        _repaintNote(oldNote);
        _repaintNote(newNote);
        _mouseOverNotes.set(fingerNum, newNote);
    }

    if (isDown) {
        if (newNote != oldNoteDown) {
            if (oldNoteDown >= 0) {
                _mouseDownNotes.set(fingerNum, -1);
                if (!_mouseDownNotes.contains(oldNoteDown))
                    _processor.getKeyboardState()->noteOff(_midiChannel, _slotToMidiNote(oldNoteDown), eventVelocity);
            }

            if (newNote >= 0 && !_mouseDownNotes.contains(newNote) && _slotToMidiNote(newNote) >= 0) {
                _processor.getKeyboardState()->noteOn(_midiChannel, _slotToMidiNote(newNote), eventVelocity);
                _mouseDownNotes.set(fingerNum, newNote);
            }
        }
    } else if (oldNoteDown >= 0) {
        _mouseDownNotes.set(fingerNum, -1);
        if (!_mouseDownNotes.contains(oldNoteDown))
            _processor.getKeyboardState()->noteOff(_midiChannel, _slotToMidiNote(oldNoteDown), eventVelocity);
    }
}

void WilsonicMidiKeyboardComponent::mouseMove(const MouseEvent& e) {
    _updateNoteUnderMouse(e, false);
}

void WilsonicMidiKeyboardComponent::mouseDrag(const MouseEvent& e) {
    float mousePositionVelocity;
    auto newNote = _xyToNote(e.position, mousePositionVelocity);
    if (newNote >= 0 && mouseDraggedToKey(newNote, e))
        _updateNoteUnderMouse(e, true);
}

bool WilsonicMidiKeyboardComponent::mouseDownOnKey(int, const MouseEvent&) {
    return true;
}

bool WilsonicMidiKeyboardComponent::mouseDraggedToKey(int, const MouseEvent&) {
    return true;
}

void WilsonicMidiKeyboardComponent::mouseUpOnKey(int, const MouseEvent&) {
}

void WilsonicMidiKeyboardComponent::mouseDown(const MouseEvent& e) {
    float mousePositionVelocity;
    auto newNote = _xyToNote(e.position, mousePositionVelocity);
    if (newNote >= 0 && mouseDownOnKey(newNote, e))
        _updateNoteUnderMouse(e, true);
}

void WilsonicMidiKeyboardComponent::mouseUp(const MouseEvent& e) {
    _updateNoteUnderMouse(e, false);
    float mousePositionVelocity;
    auto note = _xyToNote(e.position, mousePositionVelocity);
    if (note >= 0)
        mouseUpOnKey(note, e);
}

void WilsonicMidiKeyboardComponent::mouseEnter(const MouseEvent& e) {
    _updateNoteUnderMouse(e, false);
}

void WilsonicMidiKeyboardComponent::mouseExit(const MouseEvent& e) {
    _updateNoteUnderMouse(e, false);
}

void WilsonicMidiKeyboardComponent::mouseWheelMove(const MouseEvent&, const MouseWheelDetails& wheel) {
    auto const amount = (_orientation == horizontalKeyboard && WilsonicMath::floatsAreNotEqual(wheel.deltaX, 0, WilsonicMath::Epsilon::UI))
    ? wheel.deltaX : (_orientation == verticalKeyboardFacingLeft ? wheel.deltaY
                      : -wheel.deltaY);
    _setLowestVisibleKeyFloat(_firstKey - amount * _keyWidth);
}

#pragma mark - Timer Callback

void WilsonicMidiKeyboardComponent::timerCallback() {
    if (! AppExperiments::renderSynthKeyboard) {
        return;
    }

    //
    if (_shouldCheckState) {
        _shouldCheckState = false;
        for (int i = _rangeStart; i <= _rangeEnd; ++i) {
            auto const midiNote = _slotToMidiNote(i);
            bool const isOn = midiNote >= 0 && _processor.getKeyboardState()->isNoteOnForChannels(_midiInChannelMask, midiNote);
            if (_keysCurrentlyDrawnDown[i] != isOn) {
                _keysCurrentlyDrawnDown.setBit(i, isOn);
                _repaintNote(i);
            }
        }
    }
}

#pragma mark - Key Mappings

void WilsonicMidiKeyboardComponent::clearKeyMappings() {
    _resetAnyKeysInUse();
    _keyPressNotes.clear();
    _keyPresses.clear();
}

void WilsonicMidiKeyboardComponent::setKeyPressForNote(const KeyPress& key, int midiNoteOffsetFromC) {
    removeKeyPressForNote(midiNoteOffsetFromC);
    _keyPressNotes.add(midiNoteOffsetFromC);
    _keyPresses.add(key);
}

void WilsonicMidiKeyboardComponent::removeKeyPressForNote(int midiNoteOffsetFromC) {
    for (int i = _keyPressNotes.size(); --i >= 0;) {
        if (_keyPressNotes.getUnchecked(i) == midiNoteOffsetFromC) {
            _keyPressNotes.remove(i);
            _keyPresses.remove(i);
        }
    }
}

void WilsonicMidiKeyboardComponent::setKeyPressBaseOctave(int newOctaveNumber) {
    jassert(newOctaveNumber >= 0 && newOctaveNumber <= 10);
    _keyMappingOctave = newOctaveNumber;
}

bool WilsonicMidiKeyboardComponent::keyStateChanged(bool /*isKeyDown*/) {
    bool keyPressUsed = false;
    for (int i = _keyPresses.size(); --i >= 0;) {
        auto const note = 12 * _keyMappingOctave + _keyPressNotes.getUnchecked(i);
        if (_keyPresses.getReference(i).isCurrentlyDown()) {
            if (! _keysPressed[note]) {
                _keysPressed.setBit(note);
                _processor.getKeyboardState()->noteOn(_midiChannel, note, _velocity);
                keyPressUsed = true;
            }
        } else {
            if (_keysPressed[note]) {
                _keysPressed.clearBit(note);
                _processor.getKeyboardState()->noteOff(_midiChannel, note, 0.0f);
                keyPressUsed = true;
            }
        }
    }

    return keyPressUsed;
}

bool WilsonicMidiKeyboardComponent::keyPressed(const KeyPress& key) {
    return _keyPresses.contains(key);
}

void WilsonicMidiKeyboardComponent::focusLost(FocusChangeType) {
    _resetAnyKeysInUse();
}

#pragma mark - ActionListener

void WilsonicMidiKeyboardComponent::actionListenerCallback(const String& message) {
    if (message == AppTuningModel::getAppTuningModelChangedMessage()) {
        repaint();
    } else if (message == WilsonicAppSkin::getAppSkinChangedMessage()) {
        repaint();
    }
}
