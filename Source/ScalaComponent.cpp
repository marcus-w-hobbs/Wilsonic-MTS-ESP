/*
 ==============================================================================
 
 ScalaComponent.cpp
 Created: 24 Sep 2022 3:57:57pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include <JuceHeader.h>
#include "DesignsModel.h"
#include "ScalaComponent.h"
#include "ScalaIconRenderer.h"
#include "ScalaModel.h"
#include "WilsonicMenuComponent.h"

#pragma mark - Life cycle

ScalaComponent::ScalaComponent(WilsonicProcessor& processor)
: WilsonicAppTuningComponent(processor)
{
    // scala model
    auto const sm = _processor.getScalaModel();
    
    // configure table
    _table = make_unique<TableListBox>("Scala", this); // TableListBoxModel is "this"
    addAndMakeVisible(*_table);
    _table->setRowHeight(ScalaIconRenderer::tableviewHeight);
    _table->setColour(ListBox::outlineColourId, Colours::grey);
    _table->setOutlineThickness(1);
    _table->setMultipleSelectionEnabled(false);
    _table->getHeader().setStretchToFitActive(true);
    
    // configure columns for table (bundled and user are identical)
    bool found_first_sortable_column = false;
    auto columns = sm->getColumns();
    for(auto c : columns)
    {
        // this is lame...overwrite the column's propertyflags if visible == 0
        // the logic for columns is spread across the model, component, xml
        if(!c.visible)
        {
            c.propertyFlags = 0;
        }
        
        // default sort order to first sortable column
        if(c.sortable == 1)
        {
            if(found_first_sortable_column == false)
            {
                found_first_sortable_column = true;
                _table->getHeader().setSortColumnId(c.columnId, true);
            }
        }
        
        // add visible columns to header
        _table->getHeader().addColumn(c.columnName,
                                      c.columnId,
                                      c.width,
                                      c.minimumWidth,
                                      c.maximumWidth,
                                      c.propertyFlags,//could be overwritten above
                                      c.insertIndex);
    }
    
    // library combo box
    _libraryComboBox = make_unique<ComboBox>();
    _libraryComboBox->addItemList(ScalaModel::getLibraryChoices(), 1);
    //_libraryComboBox->setToolTip("Toggle between the Bundled Scala Library, and your User Scala Library.\n\nPlease see the Scala archives at:\n\nhttp://www.huygens-fokker.org/docs/scalesdir.txt");
    auto const selectedLibraryIndex = sm->uiGetLibrary();
    _libraryComboBox->setSelectedItemIndex(static_cast<int>(selectedLibraryIndex), dontSendNotification);
    auto onChange = [this, sm]()
    {
        auto const selectedItemIndex = static_cast<ScalaModel::Library>(_libraryComboBox->getSelectedItemIndex());
        DBG("library: " + String(static_cast<int>(selectedItemIndex)));
        sm->uiSetLibrary(selectedItemIndex);
    };
    _libraryComboBox->onChange = onChange;
    addAndMakeVisible(*_libraryComboBox);
    
    // previous Scala button
    _previousScalaButton = make_unique<TextButton>("<");
    _previousScalaButton->setClickingTogglesState(false);
    _previousScalaButton->setTooltip("Go to previous Scala file");
    _previousScalaButton->setToggleState(false, dontSendNotification);
    _previousScalaButton->addListener(this);
    addAndMakeVisible(*_previousScalaButton);
    
    // next Scala
    _nextScalaButton = make_unique<TextButton>(">");
    _nextScalaButton->setClickingTogglesState(false);
    _nextScalaButton->setTooltip("Go to next Scala file");
    _nextScalaButton->setToggleState(false, dontSendNotification);
    _nextScalaButton->addListener(this);
    addAndMakeVisible(*_nextScalaButton);
    
    // add user scala file
    _addUserScalaButton = make_unique<TextButton>("+");
    _addUserScalaButton->setClickingTogglesState(false);
    _addUserScalaButton->setTooltip("Add Scala File\n(enabled when User tab is selected)");
    _addUserScalaButton->setToggleState(false, dontSendNotification);
    _addUserScalaButton->addListener(this);
    addAndMakeVisible(*_addUserScalaButton);
    
    // status label
    addAndMakeVisible(_statusLabel);
    _statusLabel.setText(ScalaComponentMessageBus::getInstance().getMessage(), dontSendNotification);
    _statusLabel.setJustificationType(Justification::Flags::right);
    _statusLabel.setTooltip(ScalaComponentMessageBus::getInstance().getMessages());
    auto const labelFontSize = WilsonicAppSkin::messageBusFontSize;
    auto const font = Font::plain;
    _statusLabel.setFont(Font(FontOptions(labelFontSize, font)));

    // file chooser
    _fileChooser = make_unique<FileChooser>("Select .scl file",
                                            File::getSpecialLocation(File::userHomeDirectory),
                                            "*.scl");
    
    // Register as the listener to the [only] WilsonicMenuComponentMessageBus
    ScalaComponentMessageBus::getInstance().setMenuMessageListener(this);

    // updates state of buttons, and loads table
    _tuningChangedUpdateUI();
    
    // add this as listener to model
    sm->addActionListener(this);
}

ScalaComponent::~ScalaComponent()
{
    ScalaComponentMessageBus::getInstance().setMenuMessageListener(nullptr);
    _processor.getScalaModel()->removeActionListener(this);
    _previousScalaButton->removeListener(this);
    _nextScalaButton->removeListener(this);
    _addUserScalaButton->removeListener(this);
}

#pragma mark - drawing

void ScalaComponent::paint(juce::Graphics& g)
{
    g.fillAll(_processor.getAppSkin().getBgColor());
    
    if(_filesAreBeingDragged)
    {
        g.setColour(Colours::skyblue);
        g.drawRect(getLocalBounds(), 3);
        g.setColour(Colours::white);
        g.drawText("Drag and drop Scala file(*.scl) here\nto import into your User library", getLocalBounds(), Justification::centred);
    }
    
    if(AppExperiments::showDebugBoundingBox)
    {
        // DEBUG
        g.setColour(Colours::red);
        g.drawRect(getLocalBounds(), 2);
        
        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
}

void ScalaComponent::resized()
{
    auto const sm = _processor.getScalaModel();
    auto const margin = static_cast<int>(WilsonicAppSkin::tuningComponentInteriorMargin);
    auto area = getLocalBounds().reduced(margin, margin);
    auto const combo_box_height = static_cast<int>(WilsonicAppSkin::comboBoxHeight);
    auto const min_hitpoint = static_cast<int>(WilsonicAppSkin::minHitPointSize);
    int const library_width = static_cast<int>(0.5f*WilsonicAppSkin::comboBoxWidth);
    auto button_area = area.removeFromTop(combo_box_height);
    auto const width = button_area.getWidth();
    int const x = button_area.getX();
    int const y = button_area.getY();
    // |- library - ID -- "<" C ">" -- "+" -|
    
    // bundled|user Combobox
    auto bundled_area = Rectangle<int>(x, y, library_width, combo_box_height);
    _libraryComboBox->setBounds(bundled_area);
    
    // <
    auto previous_button_area = Rectangle<int>(static_cast<int>(x + 0.5f * width - min_hitpoint - 0.5f * margin), y, min_hitpoint, min_hitpoint);
    _previousScalaButton->setBounds(previous_button_area);
    
    // >
    auto next_button_area = Rectangle<int>(static_cast<int>(x + 0.5f * width + 0.5f * margin), y, min_hitpoint, min_hitpoint);
    _nextScalaButton->setBounds(next_button_area);
    
    // +
    auto add_scala_area = Rectangle<int>(static_cast<int>(x + width - min_hitpoint), y, min_hitpoint, min_hitpoint);
    _addUserScalaButton->setBounds(add_scala_area);

    // status label
    auto const slax = static_cast<int>(next_button_area.getX() + next_button_area.getWidth() + margin);
    auto const slaw = static_cast<int>(add_scala_area.getX() - margin - slax);
    auto status_label_area = Rectangle<int>(jmax(slax, 0), y, jmax(slaw, 1), min_hitpoint);
    _statusLabel.setBounds(status_label_area);

    // spacer
    area.removeFromTop(static_cast<int>(margin));
    
    // finally, the Scala table
    _table->setBounds(area);
}

void ScalaComponent::handleMessage(const String& message)
{
    // Update the status label with the received message
    _statusLabel.setText(message, dontSendNotification);
    _statusLabel.setTooltip(ScalaComponentMessageBus::getInstance().getMessages());
    resized();
}

const string ScalaComponent::getAppTuningTitle()
{
    return "Scala";
}

#pragma mark - private methods

void ScalaComponent::_previousScala()
{
    _processor.getScalaModel()->recallPreviousScala();
}

void ScalaComponent::_nextScala()
{
    _processor.getScalaModel()->recallNextScala();
}

void ScalaComponent::_chooseScalaFile()
{
    auto const sm = _processor.getScalaModel();
    if(sm->uiGetLibrary() == ScalaModel::Library::Bundled)
    {
        DBG("ScalaComponent::_chooseScalaFile: bundled is active...not opening file chooser");
        return;
    }
    
    // launch the file chooser
    auto const folderChooserFlags =
    FileBrowserComponent::openMode |
    FileBrowserComponent::canSelectFiles |
    FileBrowserComponent::canSelectMultipleItems;
    _fileChooser->launchAsync(folderChooserFlags, [sm] (const FileChooser& chooser) {
        auto results = chooser.getResults();
        for(auto f : results)
        {
            DBG("selected file: " + f.getFullPathName());
        }
        sm->importUserScalaFiles(results);
    });
}

#pragma mark - _tuningChangedUpdateUI

void ScalaComponent::_tuningChangedUpdateUI()
{
    // scala model
    auto const sm = _processor.getScalaModel();
    
    //
    _libraryComboBox->setSelectedItemIndex(static_cast<int>(_processor.getScalaModel()->uiGetLibrary()), dontSendNotification);
    
    // buttons
    _previousScalaButton->setToggleState(false, dontSendNotification);
    _nextScalaButton->setToggleState(false, dontSendNotification);
    
    // reload table
    auto const index = sm->getSelectedRowNumber();
    _table->updateContent();
    _table->selectRow(index);
    _table->scrollToEnsureRowIsOnscreen(index);
    _table->repaint();
}

#pragma mark - buttonClicked

void ScalaComponent::buttonClicked(Button* button)
{
    // previous
    auto pfb = dynamic_cast<Button*>(_previousScalaButton.get());
    if(pfb == button)
    {
        _previousScala();
        return;
    }
    
    // next
    auto nfb = dynamic_cast<Button*>(_nextScalaButton.get());
    if(nfb == button)
    {
        _nextScala();
        return;
    }
    
    // add user scala
    auto ausb = dynamic_cast<Button*>(_addUserScalaButton.get());
    if(ausb == button)
    {
        _chooseScalaFile();
        return;
    }
    
    //
    jassertfalse;
}

#pragma mark - ActionListener

void ScalaComponent::actionListenerCallback(const String& message)
{
    if(message == DesignsModel::getScalaTuningChangedActionMessage())
    {
        _tuningChangedUpdateUI();
    }
}
