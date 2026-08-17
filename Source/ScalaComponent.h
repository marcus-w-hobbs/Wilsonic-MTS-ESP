/*
 ==============================================================================
 
 ScalaComponent.h
 Created: 24 Sep 2022 3:57:57pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#pragma once

#include <JuceHeader.h>
#include "AppTuningModel.h"
#include "BubbleDrawable.h"
#include "DeltaComboBox.h"
#include "Microtone.h"
#include "ScalaComponentMessageBus.h"
#include "ScalaIconRenderer.h"
#include "Tuning_Include.h"
#include "WilsonicAppSkin.h"
#include "WilsonicAppTuningComponent.h"
#include "WilsonicComponentBase.h"
#include "WilsonicIntervalMatrixComponent.h"
#include "WilsonicPitchWheelComponent.h"
#include "WilsonicProcessor.h"

class ScalaComponent
: public WilsonicAppTuningComponent
, public ActionBroadcaster
, public FileDragAndDropTarget
, public TableListBoxModel
, private ActionListener
, private Button::Listener
, private ScalaComponentMessageListener
{
    
public:
    // lifecycle
    ScalaComponent(WilsonicProcessor&);
    ~ScalaComponent() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ScalaComponent)
    
public:
    // drawing
    void paint(juce::Graphics&) override;
    void resized() override;
    
    // MessageListener
    void handleMessage(const String& message) override;

    // tuning title
    const string getAppTuningTitle() override;
    
    // ActionListener
    void actionListenerCallback(const String& message) override;
    
    // FileDragAndDropTarget
    bool isInterestedInFileDrag(const StringArray& files) override;
    void fileDragEnter(const StringArray& files, int x, int y) override;
    void fileDragMove(const StringArray& files, int x, int y) override;
    void fileDragExit(const StringArray& files) override;
    void filesDropped(const StringArray& files, int x, int y) override;
    
private:
    // private members
    bool _filesAreBeingDragged {false};
    unique_ptr<TableListBox> _table;
    unique_ptr<ComboBox> _libraryComboBox;
    unique_ptr<TextButton> _previousScalaButton;
    unique_ptr<TextButton> _nextScalaButton;
    unique_ptr<TextButton> _addUserScalaButton;
    unique_ptr<FileChooser> _fileChooser;
    Label _statusLabel;

    // private methods
    static void _deleteKeyModalCallback(int modalResult, ScalaComponent* t, int lastRowSelected);
    void _deleteScalaAtRow(int row);
    void _previousScala();
    void _nextScala();
    void _tuningChangedUpdateUI();
    void _chooseScalaFile();
    
    // TableListBoxModel
    String getCellTooltip(int rowNumber, int columnId) override;
    void deleteKeyPressed(int lastRowSelected) override;
    void returnKeyPressed(int lastRowSelected) override;
    void cellDoubleClicked(int rowNumber, int columnId, const MouseEvent&) override;
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
    
    // private helper classes
    //==============================================================================
    class EditableTextCustomComponent
    : public Label
    {
        
    public:
        EditableTextCustomComponent(ScalaComponent& td)
        : _owner(td)
        {
            setEditable(false, true, false);
        }
        
        void mouseDown(const MouseEvent& event) override
        {
            _owner._table->selectRowsBasedOnModifierKeys(_row, event.mods, false);
            Label::mouseDown(event);
        }
        
        void textWasEdited() override
        {
            _owner.setText(_columnId, _row, getText());
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
            if (! dynamic_cast<LookAndFeel_V4*> (&lf))
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
        ScalaComponent& _owner;
        int _row, _columnId;
    };
    
    //==============================================================================
    class TextCustomComponent
    : public Label
    {
        
    public:
        TextCustomComponent(ScalaComponent& td)
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
            if (! dynamic_cast<LookAndFeel_V4*> (&lf))
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
        ScalaComponent& _owner;
        int _row, _columnId;
    };
    
    //==============================================================================
    class ScalaIcon
    : public ImageComponent  // JUCE 9: Drawable is no longer a Component
    {

    public:
        ScalaIcon(ScalaComponent& td)
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
                auto rs = ip->rescaled(ScalaIconRenderer::tableviewHeight, ScalaIconRenderer::tableviewHeight);
                setImage(rs);
            }
            else
            {
                // TODO: set default image
                jassertfalse;
            }
        }
        
    private:
        ScalaComponent& _owner;
        int _row, _columnId;
    };
};
