/*
 ==============================================================================

 FavoritesComponent.h
 Created: 9 Jul 2022 7:20:23pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#pragma once

#include <JuceHeader.h>
#include "FavoritesComponentMessageBus.h"
#include "FavoritesIconRenderer.h"
#include "Tuning_Include.h"
#include "WilsonicComponentBase.h"

class FavoritesComponent
: public WilsonicComponentBase
, public TableListBoxModel
, public ActionBroadcaster
, private ActionListener
, private Button::Listener
, private FavoritesComponentMessageBusListener
{
    
    // lifecycle
public:
    FavoritesComponent(WilsonicProcessor&);
    ~FavoritesComponent() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(FavoritesComponent)

public:
    // drawing
    void paint(Graphics&) override;
    void resized() override;

    // MessageListener
    void handleMessage(const String& message) override;

    // ActionListener
    void actionListenerCallback(const String& message) override;

private:
    // private methods
    static void _deleteKeyModalCallback(int modalResult, FavoritesComponent* t, int lastRowSelected);
    void _deleteFavoriteAtRow(int row);
    void _previousFavorites();
    void _nextFavorites();

    // private members
    unique_ptr<TableListBox> _table;
    unique_ptr<TextButton>   _addScalaButton;
    unique_ptr<TextButton>   _addFavoritesButton;
    unique_ptr<ToggleButton> _favoritesStoreNPOOverride;
    unique_ptr<ToggleButton> _favoritesStorePeriodMiddleC;
    unique_ptr<ToggleButton> _favoritesStoreNNMiddleC;
    unique_ptr<ToggleButton> _favoritesStoreFreqMiddleC;
    unique_ptr<Label>        _favoritesIDLabel;
    Label                    _statusLabel;

    // TableListBoxModel
    String getCellTooltip(int rowNumber, int columnId) override;
    void deleteKeyPressed(int lastRowSelected) override;
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
    void buttonClicked(Button*) override;
    shared_ptr<Image> getIcon(int rowNumber);

    // KeyListener
    bool keyPressed(const KeyPress& key) override;

    // Label
    void _validateLabelInput();

    // update ui
    void _tuningChangedUpdateUI();

    // private helper classes
    //==============================================================================
    class EditableTextCustomComponent : public Label {
    public:
        EditableTextCustomComponent(FavoritesComponent& td)
        : _owner(td) {
            setEditable(false, true, false);
        }

        void mouseDown(const MouseEvent& event) override {
            _owner._table->selectRowsBasedOnModifierKeys(_row, event.mods, false);
            Label::mouseDown(event);
        }

        void textWasEdited() override {
            _owner.setText(_columnId, _row, getText());
        }

        void setRowAndColumn(const int newRow, const int newColumn) {
            _row = newRow;
            _columnId = newColumn;
            auto t = _owner.getText(_row, _columnId);
            setText(_owner.getText(_row, _columnId), dontSendNotification);
        }

        void paint(Graphics& g) override {
            auto& lf = getLookAndFeel();
            if(! dynamic_cast<LookAndFeel_V4*>(&lf))
                lf.setColour(textColourId, Colours::black);
            Label::paint(g);

            // DEBUG
            if(AppExperiments::showDebugBoundingBox) {
                g.setColour(Colours::lightgreen);
                g.drawRect(getLocalBounds(), 1);
            }
        }

    private:
        FavoritesComponent& _owner;
        int _row, _columnId;
    };

    //==============================================================================
    class TextCustomComponent : public Label
    {
    public:
        TextCustomComponent(FavoritesComponent& td)
        : _owner(td) {
            setEditable(false, false, false);
            setInterceptsMouseClicks(false, false);
        }

        void setRowAndColumn(const int newRow, const int newColumn) {
            _row = newRow;
            _columnId = newColumn;
            auto t = _owner.getText(_row, _columnId);
            setText(_owner.getText(_row, _columnId), dontSendNotification);
        }

        void paint(Graphics& g) override {
            auto& lf = getLookAndFeel();
            if(! dynamic_cast<LookAndFeel_V4*>(&lf))
                lf.setColour(textColourId, Colours::black);
            Label::paint(g);

            // DEBUG
            if(AppExperiments::showDebugBoundingBox) {
                g.setColour(Colours::lightgreen);
                g.drawRect(getLocalBounds(), 1);
            }
        }

    private:
        FavoritesComponent& _owner;
        int _row, _columnId;
    };

    //==============================================================================
    class FavoritesIcon : public ImageComponent  // JUCE 9: Drawable is no longer a Component
    {
    public:
        FavoritesIcon(FavoritesComponent& td)
        :_owner(td) {
            setInterceptsMouseClicks(false, false);
            // match the old DrawableImage behaviour: native size, anchored top-left
            setImagePlacement(RectanglePlacement::xLeft | RectanglePlacement::yTop | RectanglePlacement::doNotResize);
        }

        // don't need to override resized()

        void setRowAndColumn(int newRow, int newColumn) {
            _row = newRow;
            _columnId = newColumn;
            auto ip = _owner.getIcon(_row);
            if(ip != nullptr) {
                auto rs = ip->rescaled(FavoritesIconRenderer::tableviewHeight, FavoritesIconRenderer::tableviewHeight);
                setImage(rs);
            } else {
                // TODO: set default image
                jassertfalse;
            }
        }

    private:
        FavoritesComponent& _owner;
        int _row, _columnId;
    };
};
