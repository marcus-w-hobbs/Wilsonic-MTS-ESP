/*
  ==============================================================================

    MorphFavoritesBComponent.h
    Created: 30 Jan 2024 7:33:19pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "AppExperiments.h"
#include "FavoritesIconRenderer.h"
#include "Tuning_Include.h"
#include "WilsonicComponentBase.h"

class MorphFavoritesBComponent  
: public WilsonicComponentBase
, public TableListBoxModel
, public ActionBroadcaster
, private ActionListener
{
public:
    MorphFavoritesBComponent(WilsonicProcessor&);
    ~MorphFavoritesBComponent() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MorphFavoritesBComponent)

public:
    // drawing
    void paint(juce::Graphics&) override;
    void resized() override;
    
    // TableListBoxModel
    String getCellTooltip(int rowNumber, int columnId) override;
    void returnKeyPressed(int lastRowSelected) override;
    void cellDoubleClicked(int rowNumber, int columnNumber, const MouseEvent&) override;
    int getNumRows() override;
    int getColumnAutoSizeWidth(int columnId) override;
    void sortOrderChanged(int newSortColumnId, bool isForwards) override;
    Component* refreshComponentForCell(int rowNumber,
                                       int columnId,
                                       bool /*isRowSelected*/,
                                       Component* existingComponentToUpdate) override;
    void paintRowBackground(Graphics&,
                            int rowNumber,
                            int width, int height,
                            bool rowIsSelected) override;
    void paintCell(Graphics&,
                   int rowNumber,
                   int columnId,
                   int width, int height,
                   bool rowIsSelected) override;
    Font getFont();
    String getText(int rowNumber, int columnId);
    void setText(const int columnNumber, const int rowNumber, const String& newText);
    int getSelection(const int rowNumber) const;
    void setSelection(const int rowNumber, const int newSelection);
    shared_ptr<Image> getIcon(int rowNumber);

    // action listener
    void actionListenerCallback(const String& message) override;

private:
    // private members
    unique_ptr<TableListBox> _table;
    
    // private helper classes
    
    //
    class TextCustomComponent : public Label
    {
    public:
        TextCustomComponent(MorphFavoritesBComponent& td)
        : _owner(td)
        {
            setEditable(false, false, false);
            setInterceptsMouseClicks(false, false);
        }

        void setRowAndColumn(const int newRow, const int newColumn)
        {
            _row = newRow;
            _columnId = newColumn;
            auto t = _owner.getText(_row, _columnId);
            setText(_owner.getText(_row, _columnId), dontSendNotification);
        }

        void paint(Graphics& g) override
        {
            auto& lf = getLookAndFeel();
            if(! dynamic_cast<LookAndFeel_V4*>(&lf))
                lf.setColour(textColourId, Colours::black);

            Label::paint(g);

            if(AppExperiments::showDebugBoundingBox)
            {
                // DEBUG
                g.setColour(Colours::lightgreen);
                g.drawRect(getLocalBounds(), 1);
            }
        }

    private:
        MorphFavoritesBComponent& _owner;
        int _row, _columnId;
    };

    //
    class FavoritesIcon : public ImageComponent  // JUCE 9: Drawable is no longer a Component
    {
    public:
        FavoritesIcon(MorphFavoritesBComponent& td)
        :_owner(td)
        {
            setInterceptsMouseClicks(false, false);
            // match the old DrawableImage behaviour: native size, anchored top-left
            setImagePlacement(RectanglePlacement::xLeft | RectanglePlacement::yTop | RectanglePlacement::doNotResize);
        }

        // don't need to override resized()

        void setRowAndColumn(int newRow, int newColumn)
        {
            _row = newRow;
            _columnId = newColumn;
            auto ip = _owner.getIcon(_row);
            if(ip != nullptr)
            {
                auto rs = ip->rescaled(FavoritesIconRenderer::tableviewHeight, FavoritesIconRenderer::tableviewHeight);
                setImage(rs);
            }
            else
            {
                // TODO: set default image
                jassertfalse;
            }
        }

    private:
        MorphFavoritesBComponent& _owner;
        int _row, _columnId;
    };
};
