/**
 * @file WilsonicMidiKeyboardComponent+paint.cpp
 * @brief Source file for the WilsonicMidiKeyboardComponent class's paint methods.
 * @date Created: 11 Apr 2023 4:54:54pm
 * @author Marcus W. Hobbs
 */

#include "AppTuningModel.h"
#include "AppExperiments.h"
#include "WilsonicMidiKeyboardComponent.h"
#include "WilsonicProcessor.h"
#include "WilsonicProcessorConstants.h"

#pragma mark - Paint

/**
 * @brief Repaints a specific note on the MIDI keyboard.
 * 
 * This function repaints a specific note on the MIDI keyboard if the note is within the range of the keyboard.
 * 
 * @param noteNum The MIDI note number of the note to be repainted.
 */
void WilsonicMidiKeyboardComponent::_repaintNote(int noteNum) {
    // Check if the note is within the range of the keyboard
    if (noteNum >= _rangeStart && noteNum <= _rangeEnd) {
        // Repaint the note
        repaint(getRectangleForKey(noteNum).getSmallestIntegerContainer());
    }
}

/**
 * @brief Paints the MIDI keyboard component.
 * 
 * This function is responsible for painting the MIDI keyboard component. If the debug bounding box is enabled, it will draw a light green rectangle around the component and display a counter at the top right corner. Depending on the display mode, it will either paint the keyboard in microtonal mode or linear mode.
 * 
 * @param g The Graphics object that should be used to do the drawing operations.
 */
void WilsonicMidiKeyboardComponent::paint(Graphics& g) {
    // If the debug bounding box is enabled
    if (AppExperiments::showDebugBoundingBox) {
        // Set the colour to light green
        g.setColour(Colours::lightgreen);
        // Draw a rectangle around the component
        g.drawRect(getLocalBounds(), 1);
        // Display a counter at the top right corner
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }

    // Depending on the display mode
    switch (_displayMode) {
        // If it's microtonal mode
        case microtonal:
            // Paint the keyboard in microtonal mode
            _paint_microtonal(g);
            break;
        // If it's linear mode or any other mode
        case linear : case linearDarkMode : default :
            // Paint the keyboard in linear mode
            _paint_linear(g);
            break;
    }
}

#pragma mark - paint microtonal

/**
 * @brief Paints the MIDI keyboard component in microtonal mode.
 * 
 * This function is responsible for painting the MIDI keyboard component in microtonal mode.
 * It first fills the background with the colour of white notes. Then it iterates over all the notes and draws the microtonal notes.
 * Depending on the orientation of the keyboard, it adjusts the shadow and line colours.
 * If the proportional triads are to be shown, it draws the dots and lines of all triads on the keyboard.
 * 
 * @param g The Graphics object that should be used to do the drawing operations.
 */
void WilsonicMidiKeyboardComponent::_paint_microtonal(Graphics& g) {
    // Fill the background with the colour of white notes
    g.fillAll(findColour(whiteNoteColourId));

    // Define the colours for the lines and text
    auto lineColour = findColour(keySeparatorLineColourId); // Colour for the lines
    auto textColour = findColour(textLabelColourId); // Colour for the text

    // Iterate over all the keyboard slots (slot == note number unless a Genus
    // Space keyboard subset maps slots into the full table's note numbers)
    for (int noteNum = 0; noteNum < static_cast<int>(WilsonicProcessorConstants::numMidiNotes); noteNum++) {
        // If the slot is within the range and maps to a note, draw the microtonal note
        auto const midiNote = _slotToMidiNote(noteNum);
        if (noteNum >= _rangeStart && noteNum <= _rangeEnd && midiNote >= 0) {
            drawMicrotonalNote(noteNum,
                                g,
                                getRectangleForKey(noteNum),
                                _processor.getKeyboardState()->isNoteOnForChannels(_midiInChannelMask, midiNote),
                                _mouseOverNotes.contains(noteNum),
                                lineColour,
                                textColour);
        }
    }

    // Define the coordinates for the shadow and line colours
    float x1 = 0, y1 = 0, x2 = 0, y2 = 0;
    auto width = getWidth(); // Width of the keyboard
    auto height = getHeight(); // Height of the keyboard
    if (_orientation == verticalKeyboardFacingLeft) {
        x1 = (float) width - 1.0f;
        x2 = (float) width - 5.0f;
    } else if (_orientation == verticalKeyboardFacingRight) {
        x2 = 5.0f;
    } else {
        y2 = 5.0f;
    }

    // Define the shadow colour
    auto x = _getKeyPos(_rangeEnd).getEnd();
    auto shadowCol = findColour(shadowColourId);
    if (!shadowCol.isTransparent()) {
        g.setGradientFill(ColourGradient(shadowCol, x1, y1, shadowCol.withAlpha(0.0f), x2, y2, false));
        switch (_orientation) {
            case horizontalKeyboard:            g.fillRect(0.0f, 0.0f, x, 5.0f); break;
            case verticalKeyboardFacingLeft:    g.fillRect((float)width - 5.0f, 0.0f, 5.0f, x); break;
            case verticalKeyboardFacingRight:   g.fillRect(0.0f, 0.0f, 5.0f, x); break;
            default: break;
        }
    }

    // If the line colour is not transparent, set the line colour
    if (!lineColour.isTransparent()) {
        g.setColour(lineColour);
        switch (_orientation) {
            case horizontalKeyboard:            g.fillRect(0.0f, (float)height - 1.0f, x, 1.0f); break;
            case verticalKeyboardFacingLeft:    g.fillRect(0.0f, 0.0f, 1.0f, x); break;
            case verticalKeyboardFacingRight:   g.fillRect((float)width - 1.0f, 0.0f, 1.0f, x); break;
            default: break;
        }
    }

    // If the proportional triads are to be shown, draw the dots and lines of all triads on the keyboard
    // (skipped while a Genus Space keyboard subset is active: triad positions
    // are computed in full-table note numbers, not compacted slots)
    if (_processor.restoreShowProportionalTriads() && !_processor.getAppTuningModel()->keyboardSubsetActive()) {
        auto const atm = _processor.getAppTuningModel();
        
        // Assume numProportional + numSubcontrary = numAllTriads.  i.e., no geometric triads
        auto const numTriads = atm->getTuning()->getProportionalTriads().size() + atm->getTuning()->getSubcontraryTriads().size();
        auto const numAllTriads = atm->getTuning()->getAllTriads().size();
        jassert(numTriads == numAllTriads);
        if (numTriads < 1)
            return;

        // Proportional and subcontrary triads (no geometric for now)
        auto const nnMiddleC = atm->uiGetNoteNumberMiddleC();
        auto const npo = atm->getTuningTableNPO();
        auto const dotSmallRadius = 13.f;

        // Drawing lambda based on each scale's note mod npo, around middle c
        auto drawTriad = [&](auto const nn60) {
            // Lambda for drawing a dot for a degree of a triad
            auto drawTriadDot = [&](auto scaleDegree, auto triadNum) {
                auto const nnRoot = nn60 + scaleDegree;
                auto keyRect = getRectangleForKey(static_cast<int>(nnRoot));
                keyRect = keyRect.withSizeKeepingCentre(keyRect.getWidth(), 0.5f * keyRect.getHeight());
                auto y01 = 1.f * (triadNum + 1.f) / (numTriads + 1.f);
                auto centre = Point<float>(keyRect.getCentreX(), keyRect.getY() + y01 * keyRect.getHeight());
                Rectangle<float> rect = {dotSmallRadius, dotSmallRadius};
                rect.setCentre(centre);
                g.fillEllipse(rect);
                g.saveState();
                g.setColour(Colours::white);
                float const strokeThickness = 1.f;
                g.drawEllipse(rect, strokeThickness);
                g.restoreState();

                return centre;
            };

            // Initialize the triad number
            auto triadNum = 0;
            auto const lineThickness = 2.0f;
            for (auto triad : atm->getTuning()->getAllTriads()) {
                // Skip if the root, third, or fifth of the triad is out of the MIDI note range
                if (nn60 + triad.getRoot()  >= WilsonicProcessorConstants::numMidiNotes) continue;
                if (nn60 + triad.getThird() >= WilsonicProcessorConstants::numMidiNotes) continue;
                if (nn60 + triad.getFifth() >= WilsonicProcessorConstants::numMidiNotes) continue;
                // Set the color of the triad dot based on the type of the triad
                if (triad.getType() == PythagoreanMeans::Type::Proportional) {
                    g.setColour(_processor.getAppSkin().getProportionalTriadDotColour());
                } else if (triad.getType() == PythagoreanMeans::Type::Subcontrary) {
                    g.setColour(_processor.getAppSkin().getSubcontraryTriadDotColour());
                } else {
                    // This should never happen, as there are only two types of triads
                    jassertfalse;
                }
                // Draw the dots for the root, third, and fifth of the triad
                auto pt0 = drawTriadDot(triad.getRoot(), triadNum);
                auto pt1 = drawTriadDot(triad.getThird(), triadNum);
                auto pt2 = drawTriadDot(triad.getFifth(), triadNum);
                // Draw the lines connecting the dots of the triad
                g.drawLine(Line<float>(pt0, pt1), lineThickness);
                g.drawLine(Line<float>(pt1, pt2), lineThickness);
                // Redraw the dots over the lines for better visibility
                drawTriadDot(triad.getRoot(), triadNum);
                drawTriadDot(triad.getThird(), triadNum);
                drawTriadDot(triad.getFifth(), triadNum);

                // Increment the triad number
                triadNum++;
            }
        };

        // Iterate over all MIDI notes
        for (int i = 0; i < static_cast<int>(WilsonicProcessorConstants::numMidiNotes); i++) {
            // Calculate the index for centering the note about middle C
            auto ff = static_cast<float>(i - static_cast<int>(nnMiddleC)) / static_cast<float>(npo);
            auto finc = truncf(ff);
            if (ff < 0.f) {
                finc -= 1.f;
            }
            auto frac = fabsf(finc - ff);
            if (frac == 1.f) {
                frac = 0.f;
            }
            auto const index = static_cast<unsigned long>(roundf(frac * static_cast<float>(npo)));
            // Draw the triad if the index is zero
            if (index == 0) {
                drawTriad(static_cast<unsigned long>(i));
            }
        }
    }
}

#pragma mark - paint linear

void WilsonicMidiKeyboardComponent::_paint_linear(Graphics& g) {
    // Bottom up

    // BG
    g.fillAll(findColour(whiteNoteColourId));

    // White keys
    auto lineColour = findColour(keySeparatorLineColourId);
    auto textColour = findColour(textLabelColourId);
    for (int noteNum = _rangeStart; noteNum <= _rangeEnd; ++noteNum) {
        if (noteNum % 12 == 0 || noteNum % 12 == 2 || noteNum % 12 == 4 || noteNum % 12 == 5 || noteNum % 12 == 7 || noteNum % 12 == 9 || noteNum % 12 == 11) {
            drawWhiteNote(noteNum,
                           g,
                           getRectangleForKey(noteNum),
                           _processor.getKeyboardState()->isNoteOnForChannels(_midiInChannelMask, noteNum),
                           _mouseOverNotes.contains(noteNum),
                           lineColour,
                           textColour);
        }
    }

    float x1 = 0.0f, y1 = 0.0f, x2 = 0.0f, y2 = 0.0f;
    auto width = getWidth();
    auto height = getHeight();
    if (_orientation == verticalKeyboardFacingLeft) {
        x1 = (float) width - 1.0f;
        x2 = (float) width - 5.0f;
    } else if (_orientation == verticalKeyboardFacingRight) {
        x2 = 5.0f;
    } else {
        y2 = 5.0f;
    }

    auto x = _getKeyPos(_rangeEnd).getEnd();
    auto shadowCol = findColour(shadowColourId);
    if (! shadowCol.isTransparent()) {
        g.setGradientFill(ColourGradient(shadowCol, x1, y1, shadowCol.withAlpha(0.0f), x2, y2, false));
        switch (_orientation) {
            case horizontalKeyboard:            g.fillRect(0.0f, 0.0f, x, 5.0f); break;
            case verticalKeyboardFacingLeft:    g.fillRect((float) width - 5.0f, 0.0f, 5.0f, x); break;
            case verticalKeyboardFacingRight:   g.fillRect(0.0f, 0.0f, 5.0f, x); break;
            default: break;
        }
    }

    if (! lineColour.isTransparent()) {
        g.setColour(lineColour);
        switch (_orientation) {
            case horizontalKeyboard:            g.fillRect(0.0f, (float) height - 1.0f, x, 1.0f); break;
            case verticalKeyboardFacingLeft:    g.fillRect(0.0f, 0.0f, 1.0f, x); break;
            case verticalKeyboardFacingRight:   g.fillRect((float) width - 1.0f, 0.0f, 1.0f, x); break;
            default: break;
        }
    }

    // Black keys
    auto blackNoteColour = findColour(blackNoteColourId);
    for (int octave = 0; octave < static_cast<int>(WilsonicProcessorConstants::numMidiNotes); octave += 12) {
        for (int black = 0; black < 5; ++black) {
            auto noteNum = octave + blackNotes[black];
            if (noteNum >= _rangeStart && noteNum <= _rangeEnd)
                drawBlackNote(noteNum,
                               g,
                               getRectangleForKey(noteNum),
                               _processor.getKeyboardState()->isNoteOnForChannels(_midiInChannelMask, noteNum),
                               _mouseOverNotes.contains(noteNum),
                               blackNoteColour);
        }
    }
}

/**
 * @brief Draws a white note on the MIDI keyboard.
 * 
 * @param midiNoteNumber The MIDI note number of the note to be drawn.
 * @param g The Graphics object that should be used to do the drawing operations.
 * @param area The area where the note should be drawn.
 * @param isDown A boolean indicating whether the note is currently being pressed.
 * @param isOver A boolean indicating whether the mouse is currently hovering over the note.
 * @param lineColour The colour of the lines.
 * @param textColour The colour of the text.
 */
void WilsonicMidiKeyboardComponent::drawWhiteNote
(int midiNoteNumber,
  Graphics& g,
  Rectangle<float> area,
  bool isDown,
  bool isOver,
  Colour lineColour,
  Colour textColour
  )
{
    // Set the colour of the note
    auto c = Colours::transparentWhite;
    if (isDown) {
        // If the note is being pressed, overlay the colour with the key down colour
        c = findColour(keyDownOverlayColourId);
    }
    if (isOver) {
        // If the mouse is hovering over the note, overlay the colour with the mouse over colour
        c = c.overlaidWith(findColour(mouseOverKeyOverlayColourId));
    }
    // Fill the area of the note with the colour
    g.setColour(c);
    g.fillRect(area);

    // Get the description of the note
    auto text = getNoteDescription(midiNoteNumber);
    if (text.isNotEmpty()) {
        // If the description is not empty, draw it on the note
        auto fontHeight = jmin(12.0f, _keyWidth * 0.9f);
        g.setColour(textColour);
        g.setFont(Font(fontHeight).withHorizontalScale(0.8f));
        switch (_orientation) {
            case horizontalKeyboard:            g.drawText(text, area.withTrimmedLeft(1.0f).withTrimmedBottom(2.0f), Justification::centredBottom, false); break;
            case verticalKeyboardFacingLeft:    g.drawText(text, area.reduced(2.0f), Justification::centredLeft,   false); break;
            case verticalKeyboardFacingRight:   g.drawText(text, area.reduced(2.0f), Justification::centredRight,  false); break;
            default: break;
        }
    }

    // Draw the lines of the note
    if (! lineColour.isTransparent()) {
        g.setColour(lineColour);
        switch (_orientation) {
            case horizontalKeyboard:            g.fillRect(area.withWidth(1.0f)); break;
            case verticalKeyboardFacingLeft:    g.fillRect(area.withHeight(1.0f)); break;
            case verticalKeyboardFacingRight:   g.fillRect(area.removeFromBottom(1.0f)); break;
            default: break;
        }

        // If the note is the last one in the range, draw an additional line
        if (midiNoteNumber == _rangeEnd) {
            switch (_orientation) {
                case horizontalKeyboard:            g.fillRect(area.expanded(1.0f, 0).removeFromRight(1.0f)); break;
                case verticalKeyboardFacingLeft:    g.fillRect(area.expanded(0, 1.0f).removeFromBottom(1.0f)); break;
                case verticalKeyboardFacingRight:   g.fillRect(area.expanded(0, 1.0f).removeFromTop(1.0f)); break;
                default: break;
            }
        }
    }
}

/**
 * @brief Draws a black note on the MIDI keyboard.
 * 
 * @param midiNoteNumber The MIDI note number of the note to be drawn.
 * @param g The Graphics object that should be used to do the drawing operations.
 * @param area The area where the note should be drawn.
 * @param isDown A boolean indicating whether the note is currently being pressed.
 * @param isOver A boolean indicating whether the mouse is currently hovering over the note.
 * @param noteFillColour The colour that should be used to fill the note.
 */
void WilsonicMidiKeyboardComponent::drawBlackNote
 (
  int /* midiNoteNumber */,
  Graphics& g,
  Rectangle<float> area,
  bool isDown,
  bool isOver,
  Colour noteFillColour
  )
{
    // Set the colour of the note
    auto c = noteFillColour;
    if (isDown) {
        // If the note is being pressed, overlay the colour with the key down colour
        c = c.overlaidWith(findColour(keyDownOverlayColourId));
    }
    if (isOver) {
        // If the mouse is hovering over the note, overlay the colour with the mouse over colour
        c = c.overlaidWith(findColour(mouseOverKeyOverlayColourId));
    }
    // Fill the area of the note with the colour
    g.setColour(c);
    g.fillRect(area);

    if (isDown) {
        // If the note is being pressed, draw a rectangle around it
        g.setColour(noteFillColour);
        g.drawRect(area);
    } else {
        // If the note is not being pressed, draw a brighter rectangle around it
        g.setColour(c.brighter());
        auto sideIndent = 1.f / 8.f;
        auto topIndent = 7.f / 8.f;
        auto w = area.getWidth();
        auto h = area.getHeight();

        switch (_orientation) {
            case horizontalKeyboard:          g.fillRect(area.reduced(w * sideIndent, 0).removeFromTop  (h * topIndent)); break;
            case verticalKeyboardFacingLeft:  g.fillRect(area.reduced(0, h * sideIndent).removeFromRight(w * topIndent)); break;
            case verticalKeyboardFacingRight: g.fillRect(area.reduced(0, h * sideIndent).removeFromLeft (w * topIndent)); break;
            default: break;
        }
    }
}

/**
 * @brief Draws a microtonal note on the MIDI keyboard.
 * 
 * @param midiNoteNumber The MIDI note number of the note to be drawn.
 * @param g The Graphics object that should be used to do the drawing operations.
 * @param area The area where the note should be drawn.
 * @param isDown A boolean indicating whether the note is currently being pressed.
 * @param isOver A boolean indicating whether the mouse is currently hovering over the note.
 * @param lineColor The color of the lines.
 * @param textColor The color of the text.
 */
void WilsonicMidiKeyboardComponent::drawMicrotonalNote
(
  int midiNoteNumber,
  Graphics& g,
  Rectangle<float> area,
  bool isDown,
  bool isOver,
  Colour lineColor,
  Colour textColor
  )
{
    // Genus Space: the incoming value is a keyboard slot; all tuning-table
    // lookups below use its mapped note number (identity when no subset)
    auto const mappedNoteNumber = _slotToMidiNote(midiNoteNumber);
    if (mappedNoteNumber < 0) {
        return;
    }
    midiNoteNumber = mappedNoteNumber;

    // Define layout parameters
    auto const horizontalScale = 1.f; // Scale factor for horizontal dimension
    auto const globalMargin = 2.f; // Global margin for all elements
    auto const globalFontHeightMin = _processor.getAppSkin().getFontHeightMin(); // Minimum font height
    auto const nn_area_factor = 0.2f; // Proportion (from bottom) of area for NN
    auto const text_area_factor = 1.f - nn_area_factor; // inverse

    // Draw the background rectangle with the color corresponding to the pitch
    auto c = _processor.getAppTuningModel()->getTuningTableColor(static_cast<unsigned long>(midiNoteNumber));
    if(isDown) c = c.brighter(0.6f); // If the note is being pressed, make the color brighter
    if(isOver) c = c.brighter(0.4f); // If the mouse is hovering over the note, make the color brighter
    g.setColour(c);
    g.fillRect(area);

    // Determine whether the note is a black or white key
    auto const ivory = ivory_key[midiNoteNumber]; // True if the note is a white key, false if it's a black key
    auto const ivory_color = ivory ? Colours::black : Colours::white; // The color of the note (black for white keys, white for black keys)
    auto twelveArea = area.withTrimmedTop(area.getHeight() * text_area_factor).reduced(globalMargin);
    g.setColour(ivory ? Colours::white : Colours::black); // Set the color of the note
    g.fillRect(twelveArea); // Draw the note

    // If debugging, draw a bounding box around the note
    if (AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::lightgreen); // Set the color for the bounding box
        g.drawRect(twelveArea, 1); // Draw the bounding box
}

    // Get the descriptions of the note
    auto topText = getNoteDescription(midiNoteNumber); // The description of the note
    auto middleText = getNoteDescription2(midiNoteNumber); // The secondary description of the note
    auto bottomText = _getNoteCentsDescription(midiNoteNumber); // cents as string
    auto nnText = String(midiNoteNumber); // The MIDI note number as a string

    // Define the areas for the labels
    auto const h = area.getHeight();
    auto textArea = area.withTrimmedBottom(h * nn_area_factor).reduced(globalMargin);
    auto const h_t = textArea.getHeight();
    auto topArea = textArea.withTrimmedBottom(h_t * 0.6666666666f);
    auto middleArea = textArea.withTrimmedTop(h_t * 0.3333333333f).withTrimmedBottom(h_t * 0.333333333f);
    auto bottomArea = textArea.withTrimmedTop(h_t * 0.6666666666f);
    auto nnArea = area.withTrimmedTop(h * text_area_factor).reduced(globalMargin);

    // If debugging, draw bounding boxes around the label areas
    if (AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::lightgreen);
        g.drawRect(topArea, 1);
        g.drawRect(middleArea, 1);
        g.drawRect(bottomArea, 1);
        g.drawRect(nnArea, 1);
    }

    // Define a lambda function to draw the text labels
    auto drawText = [&](auto in_text, auto minLen, auto in_area, auto justification, auto text_color) {
        if (in_text.isEmpty()) {
            return;
        }

        // Define parameters for the text size
        auto const magicNumerator = 1.3f; // Numerator for the text size calculation
        auto const magicDenominator = 0.75f; // Denominator for the text size calculation
        auto strLen = jmax(in_text.length(), minLen); // The length of the text
        auto w = jmax(in_area.getWidth(), globalFontHeightMin); // The width of the area
        auto fontHeight = jmax(globalFontHeightMin, (w / (strLen * magicDenominator)) * magicNumerator); // The height of the font

        // Set the font and color for the text
        g.setFont(Font(fontHeight).withHorizontalScale(horizontalScale));
        g.setColour(text_color);

        // Draw the text
        g.drawText(in_text, in_area, justification, true);
    };

    // The minimum length of the text strings
    auto const minStrLen = 4;

    // Draw the text labels depending on the orientation of the keyboard
    switch (_orientation) {
        case horizontalKeyboard:
            drawText(topText,     minStrLen, topArea,    Justification::centred,      textColor  ); // Draw the description
            drawText(middleText,  minStrLen, middleArea, Justification::centred,      textColor  ); // Draw the secondary description
            drawText(bottomText,          4, bottomArea, Justification::centred,      textColor  ); // Draw the cents description
            drawText(nnText,              3, nnArea,     Justification::centred,      ivory_color); // Draw the MIDI note number
            break;
        case verticalKeyboardFacingLeft:
            drawText(topText,     minStrLen, topArea,    Justification::centredLeft,  textColor  ); // Draw the description
            drawText(middleText,  minStrLen, middleArea, Justification::centredLeft,  textColor  ); // Draw the secondary description
            drawText(bottomText,          4, bottomArea, Justification::centredLeft,  textColor  ); // Draw the cents description
            drawText(nnText,              3, nnArea,     Justification::centredLeft,  ivory_color); // Draw the MIDI note number
            break;
        case verticalKeyboardFacingRight:
            drawText(topText,     minStrLen, topArea,    Justification::centredRight, textColor  ); // Draw the description
            drawText(middleText,  minStrLen, middleArea, Justification::centredRight, textColor  ); // Draw the secondary description
            drawText(bottomText,          4, bottomArea, Justification::centredRight, textColor  ); // Draw the cents description
            drawText(nnText,              3, nnArea,     Justification::centredRight, ivory_color); // Draw the MIDI note number
            break;
        default: break;
    }

    // If the line color is not transparent, draw the lines
    if (!lineColor.isTransparent()) {
        g.setColour(lineColor); // Set the color for the lines

        // Draw the lines depending on the orientation of the keyboard
        switch (_orientation) {
            case horizontalKeyboard:          g.fillRect(area.withWidth(1.f)); break;
            case verticalKeyboardFacingLeft:  g.fillRect(area.withHeight(1.f)); break;
            case verticalKeyboardFacingRight: g.fillRect(area.removeFromBottom(1.f)); break;
            default: break;
        }

        // If the note is the last one in the range, draw an additional line
        if (midiNoteNumber == _rangeEnd) {
            switch (_orientation) {
                case horizontalKeyboard:          g.fillRect(area.expanded(1.f, 0).removeFromRight(1.f)); break;
                case verticalKeyboardFacingLeft:  g.fillRect(area.expanded(0, 1.f).removeFromBottom(1.f)); break;
                case verticalKeyboardFacingRight: g.fillRect(area.expanded(0, 1.f).removeFromTop(1.f)); break;
                default: break;
            }
        }
    }
}
