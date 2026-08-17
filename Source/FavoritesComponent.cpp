/*
 ==============================================================================

 FavoritesComponent.cpp
 Created: 9 Jul 2022 7:20:23pm
 Author:  Marcus W. Hobbs

 ==============================================================================
 */

#include <JuceHeader.h>
#include "DesignsModel.h"
#include "FavoritesComponent.h"
#include "FavoritesIconRenderer.h"
#include "FavoritesModelV2.h"
#include "WilsonicMenuComponent.h"

#pragma mark - Life cycle

FavoritesComponent::FavoritesComponent(WilsonicProcessor& processor)
: WilsonicComponentBase(processor)
{
    // favorites model
    auto const fm = _processor.getFavoritesModelV2();

    // configure table
    _table = make_unique<TableListBox>("Favorites", this); // TableListBoxModel is this
    addAndMakeVisible(*_table);
    _table->setRowHeight(FavoritesIconRenderer::tableviewHeight);
    _table->setColour(ListBox::outlineColourId, Colours::grey);
    _table->setOutlineThickness(1);
    _table->setMultipleSelectionEnabled(false);
    _table->getHeader().setStretchToFitActive(true);

    // configure columns for table
    bool found_first_sortable_column = false;
    auto columns = fm->getColumns();
    for(auto c : columns) {
        // this is lame...overwrite the column's propertyflags if visible == 0
        // the logic for columns is spread across the model, component, xml
        if(! c.visible) {
            c.propertyFlags = 0;
        }

        // default sort order to first sortable column
        if(c.sortable == 1) {
            if(found_first_sortable_column == false) {
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

    // back to front UX
    
    // add Scala button (not used yet)
    _addScalaButton = make_unique<TextButton>("S", "Add the current tuning to your Scala User Library");
    _addScalaButton->setToggleState(false, dontSendNotification);
    addAndMakeVisible(*_addScalaButton);
    _addScalaButton->addListener(this);

    // right to left
    // ID Label
    _favoritesIDLabel = make_unique<Label>();
    _favoritesIDLabel->setEditable(true);
    _favoritesIDLabel->setJustificationType(Justification::centred);
    _favoritesIDLabel->onTextChange = [this] {_validateLabelInput();};
    addAndMakeVisible(*_favoritesIDLabel);

    // status label
    addAndMakeVisible(_statusLabel);
    _statusLabel.setText(FavoritesComponentMessageBus::getInstance().getMessage(), dontSendNotification);
    _statusLabel.setJustificationType(Justification::Flags::right);
    _statusLabel.setTooltip(FavoritesComponentMessageBus::getInstance().getMessages());
    auto const labelFontSize = WilsonicAppSkin::messageBusFontSize;
    auto const font = Font::plain;
    _statusLabel.setFont(Font(FontOptions(labelFontSize, font)));

    // left to right
    
    // add Favorite button
    _addFavoritesButton = make_unique<TextButton>("+", "Add the current tuning to your Favorites");
    _addFavoritesButton->setToggleState(false, dontSendNotification);
    addAndMakeVisible(*_addFavoritesButton);
    _addFavoritesButton->addListener(this);

    // store npo override
    _favoritesStoreNPOOverride = make_unique<ToggleButton>("NPO Override");
    _favoritesStoreNPOOverride->setToggleState(_processor.restoreFavoritesStoreNPOOverride(), dontSendNotification);
    _favoritesStoreNPOOverride->setTooltip("Favorites: store the NPO Override settings");
    addAndMakeVisible(*_favoritesStoreNPOOverride);
    _favoritesStoreNPOOverride->addListener(this);

    // store period
    _favoritesStorePeriodMiddleC = make_unique<ToggleButton>("Period");
    _favoritesStorePeriodMiddleC->setToggleState(_processor.restoreFavoritesStorePeriodMiddleC(), dontSendNotification);
    _favoritesStorePeriodMiddleC->setTooltip("Favorites: store the Period number at Middle C");
    addAndMakeVisible(*_favoritesStorePeriodMiddleC);
    _favoritesStorePeriodMiddleC->addListener(this);
    
    // store note number
    _favoritesStoreNNMiddleC = make_unique<ToggleButton>("Note Number");
    _favoritesStoreNNMiddleC->setToggleState(_processor.restoreFavoritesStoreNNMiddleC(), dontSendNotification);
    _favoritesStoreNNMiddleC->setTooltip("Favorites: store the MIDI note number at Middle C");
    addAndMakeVisible(*_favoritesStoreNNMiddleC);
    _favoritesStoreNNMiddleC->addListener(this);

    // store frequency
    _favoritesStoreFreqMiddleC = make_unique<ToggleButton>("Frequency");
    _favoritesStoreFreqMiddleC->setToggleState(_processor.restoreFavoritesStoreFrequencyMiddleC(), dontSendNotification);
    _favoritesStoreFreqMiddleC->setTooltip("Favorites: store the frequency at Middle C");
    addAndMakeVisible(*_favoritesStoreFreqMiddleC);
    _favoritesStoreFreqMiddleC->addListener(this);

    // layout and draw
    resized();
    _tuningChangedUpdateUI();

    // Register as the listener to the [only] FavoritesComponentMessageBus
    FavoritesComponentMessageBus::getInstance().setMenuMessageListener(this);

    // Add self as listener for model changes
    fm->addActionListener(this);
}

FavoritesComponent::~FavoritesComponent() {
    _table->setModel(nullptr);
    auto const fm = _processor.getFavoritesModelV2();
    fm->removeActionListener(this);
    _addScalaButton->removeListener(this);
    _addFavoritesButton->removeListener(this);
    _favoritesStorePeriodMiddleC->removeListener(this);
    _favoritesStoreNNMiddleC->removeListener(this);
    _favoritesStoreFreqMiddleC->removeListener(this);
    FavoritesComponentMessageBus::getInstance().setMenuMessageListener(nullptr);
}

#pragma mark - drawing

void FavoritesComponent::paint(juce::Graphics& g) {
    g.saveState();
    g.fillAll(_processor.getAppSkin().getTableListBoxRow0Colour());
    
    // DEBUG
    if(AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::red);
        g.drawRect(getLocalBounds(), 2);
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
    
    // label
    g.setColour(Colours::grey);
    g.drawRect(_favoritesIDLabel->getBounds(), 1);

    //
    g.restoreState();
}

void FavoritesComponent::resized() {
    // | - "+" -|
    auto const margin = static_cast<int>(WilsonicAppSkin::tuningComponentInteriorMargin);
    auto area = getLocalBounds().reduced(margin, margin);
    auto const min_hitpoint = static_cast<int>(WilsonicAppSkin::minHitPointSize);
    auto const button_area = area.removeFromTop(min_hitpoint);
    auto const width = button_area.getWidth();
    int const x = button_area.getX();
    int const y = button_area.getY();

    // TODO: Add favorite as Scala
#if 0
    // Scala
    auto scala_button_area = Rectangle<int>(static_cast<int>(x + width - 2 * min_hitpoint - margin), y, min_hitpoint, min_hitpoint);
    _addScalaButton->setBounds(scala_button_area);
#endif
    
    // weird layout: center +, right, left
    
    // +
    auto const pbaxi = static_cast<int>(x + 0.5f * width + 0.5f * min_hitpoint);
    auto plus_button_area = Rectangle<int>(pbaxi, y, min_hitpoint, min_hitpoint);
    _addFavoritesButton->setBounds(plus_button_area);

    // Calculate width for _favoritesIDSlider
    auto const id_label_width = min_hitpoint * 3;
    
    // _favoritesIDLabel (to the right of the status label)
    auto id_label_area = Rectangle<int>(width - id_label_width, y, id_label_width, min_hitpoint);
    _favoritesIDLabel->setBounds(id_label_area);

    // status label (to the right of the + button, hugging the left of the slider)
    auto slb = Rectangle<int>(pbaxi, y, id_label_area.getX() - margin - pbaxi, min_hitpoint);
    _statusLabel.setBounds(slb);
                    
    // all the checkboxes to the left of the + button
    auto checkbox_area = Rectangle<int>(x,
                                        plus_button_area.getY(),
                                        plus_button_area.getX() - margin - x,
                                        min_hitpoint
                                        );
    auto checkbox_width = static_cast<int>(0.25f * checkbox_area.getWidth());

    // _favoritesStoreNPOOverride
    auto afsno = checkbox_area.removeFromLeft(checkbox_width + margin);
    _favoritesStoreNPOOverride->setBounds(afsno);

    // _favoritesStorePeriodMiddleC
    auto afspmc = checkbox_area.removeFromLeft(checkbox_width + margin);
    _favoritesStorePeriodMiddleC->setBounds(afspmc);
    
    // _favoritesStoreNNMiddleC
    auto afsnnmc = checkbox_area.removeFromLeft(checkbox_width + margin);
    _favoritesStoreNNMiddleC->setBounds(afsnnmc);
    
    // _favoritesStoreFreqMiddleC
    auto afsfmc = checkbox_area;
    _favoritesStoreFreqMiddleC->setBounds(afsfmc);
    
    // spacer
    area.removeFromTop(static_cast<int>(margin));

    // finally, the favorites table
    _table->setBounds(area);
}

void FavoritesComponent::handleMessage(const String& message) {
    // Update the status label with the received message
    _statusLabel.setText(message, dontSendNotification);
    _statusLabel.setTooltip(FavoritesComponentMessageBus::getInstance().getMessages());
    resized();
}

#pragma mark - ActionListener

void FavoritesComponent::actionListenerCallback(const String& message) {
    if(message == FavoritesModelV2::getFavoritesModelV2UpdateUIMessage()) {
        _tuningChangedUpdateUI();
        return;
    }

    jassertfalse;
}

void FavoritesComponent::_tuningChangedUpdateUI() {
    auto const fm = _processor.getFavoritesModelV2();
    auto const index = fm->getFavoriteRowNumber(FavoritesModelV2::DataList::Favorites);
    _table->updateContent();
    _table->selectRow(index);
    _table->scrollToEnsureRowIsOnscreen(index);
    _table->repaint();
    auto const currentID = fm->uiGetFavoriteID();
    _favoritesIDLabel->setText(String(currentID), juce::NotificationType::dontSendNotification);
    _favoritesIDLabel->repaint();
}

#pragma mark - TableListBoxModel

String FavoritesComponent::getCellTooltip(int row_number, int /* columnId */) {
    auto const desc = getText(row_number, 5);
    auto const params = getText(row_number, 6);
    auto tip = String();
    if(desc.isNotEmpty()) {
        tip += "Description:\n" + desc + "\n\n";
    }
    tip += "Parameters:\n" + params;

    return tip;
}

int FavoritesComponent::getNumRows() {
    return _processor.getFavoritesModelV2()->getNumRows(FavoritesModelV2::DataList::Favorites);
}

void FavoritesComponent::deleteKeyPressed(int lastRowSelected) {
    AlertWindow::showOkCancelBox
    (MessageBoxIconType::WarningIcon,
     "Delete Favorite?",
     "This cannot be undone!",
     "Delete",
     "Cancel",
     this,
     ModalCallbackFunction::forComponent(_deleteKeyModalCallback, this, lastRowSelected)
     );
}

void FavoritesComponent::returnKeyPressed(int lastRowSelected) {
    _processor.getFavoritesModelV2()->uiRecallFavoriteAtRowNumber(lastRowSelected);
}

void FavoritesComponent::cellDoubleClicked(int rowNumber, int columnNumber, const MouseEvent&) {
    if(columnNumber != 5) {
        _processor.getFavoritesModelV2()->uiRecallFavoriteAtRowNumber(rowNumber);
    }
}

int FavoritesComponent::getColumnAutoSizeWidth(int columnId) {
    return _processor.getFavoritesModelV2()->getColumnAutoSizeWidth(columnId);
}

void FavoritesComponent::sortOrderChanged(int newSortColumnId, bool isForwards) {
    _processor.getFavoritesModelV2()->sortOrderChanged(newSortColumnId, isForwards, FavoritesModelV2::DataList::Favorites);
    _table->updateContent();
}

// This is overloaded from TableListBoxModel, and must update any custom components that we're using
Component* FavoritesComponent::refreshComponentForCell
 (int rowNumber,
  int columnId,
  bool /*isRowSelected*/,
  Component* existingComponentToUpdate
  ) {
    // non-editable, non-icon
    // columns that have TextCustomComponent
    if(columnId == 1 ||
       columnId == 3 ||
       columnId == 4 ||
       columnId == 6 ||
       columnId == 7) {
        auto* staticLabel = static_cast<TextCustomComponent*>(existingComponentToUpdate);
        if(staticLabel == nullptr) {
            staticLabel = new TextCustomComponent(*this);
        }
        staticLabel->setRowAndColumn(rowNumber, columnId);
        staticLabel->setInterceptsMouseClicks(false, false);
        return staticLabel;
    } else if(columnId == 2) {
        // icon
        auto* icon = static_cast<FavoritesIcon*>(existingComponentToUpdate);
        if(icon == nullptr) {
            icon = new FavoritesIcon(*this);
        }
        icon->setRowAndColumn(rowNumber, columnId);
        return icon;
    } else if(columnId == 5) {
        // editable column
        auto* textLabel = static_cast<EditableTextCustomComponent*>(existingComponentToUpdate);
        if(textLabel == nullptr) {
            textLabel = new EditableTextCustomComponent(*this);
        }
        textLabel->setRowAndColumn(rowNumber, columnId);

        return textLabel;
    } else {
        DBG("WARNING: leftover columnID: " + String(columnId));
    }

    jassert(existingComponentToUpdate == nullptr);
    return nullptr;
}

void FavoritesComponent::paintRowBackground(Graphics& g,
                                            int rowNumber,
                                            int /* width */,
                                            int /* height */ ,
                                            bool rowIsSelected) {
    if(rowIsSelected) {
        g.fillAll( _processor.getAppSkin().getTableListBoxBGColour());
    } else {
        // alternates rows for easy reading
        g.fillAll((rowNumber % 2)
                  ? _processor.getAppSkin().getTableListBoxRow1Colour()
                  : _processor.getAppSkin().getTableListBoxRow0Colour()
                  );
    }
}

void FavoritesComponent::paintCell(Graphics& g,
                                   int rowNumber,
                                   int columnId,
                                   int width,
                                   int height,
                                   bool rowIsSelected) {
    g.setColour(rowIsSelected ? Colours::white : Colours::white);
    auto fm = _processor.getFavoritesModelV2();
    g.setFont(fm->getFont());
    auto text = fm->getText(rowNumber, columnId, FavoritesModelV2::DataList::Favorites);
    g.drawText(text, 2, 0, width - 4, height, Justification::centredLeft, true);
    g.setColour(Colours::black);
    g.fillRect(width - 1, 0, 1, height); // rightmost vertical line
}

Font FavoritesComponent::getFont() {
    return _processor.getFavoritesModelV2()->getFont();
}

String FavoritesComponent::getText(int rowNumber, int columnId) {
    return _processor.getFavoritesModelV2()->getText(rowNumber, columnId, FavoritesModelV2::DataList::Favorites);
}

void FavoritesComponent::setText(const int columnNumber, const int rowNumber, const String& newText) {
    const auto& columnName = _table->getHeader().getColumnName(columnNumber);
    _processor.getFavoritesModelV2()->setText(columnName, rowNumber, newText);
}

int FavoritesComponent::getSelection(const int rowNumber) const {
    return _processor.getFavoritesModelV2()->getSelection(rowNumber, FavoritesModelV2::DataList::Favorites);
}

void FavoritesComponent::setSelection(const int rowNumber, const int newSelection) {
    _processor.getFavoritesModelV2()->setSelection(rowNumber, newSelection, FavoritesModelV2::DataList::Favorites);
}

#pragma mark - Button handler

void FavoritesComponent::buttonClicked(Button* button) {
    // "S" add current tuning as Scala
    auto asb = dynamic_cast<Button*>(_addScalaButton.get());
    if(asb == button) {
        _processor.getDesignsModel()->uiStoreScala();
        return;
    }

    // "+" add current tuning as Favorite
    auto afb = dynamic_cast<Button*>(_addFavoritesButton.get());
    if(afb == button) {
        _processor.getFavoritesModelV2()->uiStoreCurrentTuningAsFavorite();
        return;
    }

    // assumes tunings have already been updated, 
    // and that params stored before updated tunings don't matter.

    // npo override
    auto fsnob = dynamic_cast<ToggleButton*>(_favoritesStoreNPOOverride.get());
    if(fsnob == button) {
        auto const state = fsnob->getToggleState();
        _processor.saveFavoritesStoreNPOOverride(state);
        return;
    }
    
    // period at middle c
    auto fspmcb = dynamic_cast<ToggleButton*>(_favoritesStorePeriodMiddleC.get());
    if(fspmcb == button) {
        auto const state = fspmcb->getToggleState();
        _processor.saveFavoritesStorePeriodMiddleC(state);
        return;
    }
    
    //
    auto fsnnmcb = dynamic_cast<ToggleButton*>(_favoritesStoreNNMiddleC.get());
    if(fsnnmcb == button) {
        auto const state = fsnnmcb->getToggleState();
        _processor.saveFavoritesStoreNNMiddleC(state);
        return;
    }

    //
    auto fsfmcb = dynamic_cast<ToggleButton*>(_favoritesStoreFreqMiddleC.get());
    if(fsfmcb == button) {
        auto const state = fsfmcb->getToggleState();
        _processor.saveFavoritesStoreFrequencyMiddleC(state);
        return;
    }
    
    //
    jassertfalse;
}

shared_ptr<Image> FavoritesComponent::getIcon(int rowNumber) {
    return _processor.getFavoritesModelV2()->getIcon(rowNumber, FavoritesModelV2::DataList::Favorites);
}

#pragma mark - key listener

bool FavoritesComponent::keyPressed(const KeyPress& key) {
    if(key.isKeyCode(KeyPress::leftKey) || key.isKeyCode(KeyPress::upKey)) {
        _previousFavorites();
        return true;
    } else if(key.isKeyCode(KeyPress::rightKey) || key.isKeyCode(KeyPress::downKey)) {
        _nextFavorites();
        return true;
    }
    return false;
}

void FavoritesComponent::_validateLabelInput() {
    auto const text = _favoritesIDLabel->getText();
    if (!text.retainCharacters("0123456789.").isEmpty()) {
        auto const numeric = text.getFloatValue();
        _processor.getFavoritesModelV2()->uiSetFavoriteID(numeric);
    } else {
        auto const currentID = _processor.getFavoritesModelV2()->uiGetFavoriteID();
        _favoritesIDLabel->setText(String(currentID), juce::NotificationType::dontSendNotification);
    }
}

#pragma mark - helpers

void FavoritesComponent::_previousFavorites() {
    auto selected_row = _table->getLastRowSelected();
    if(selected_row == -1) {
        // no selection?  NOP
        return;
    }
    auto num_rows = getNumRows();
    if(num_rows == 0 || num_rows == 1) {
        // NOP
        return;
    }

    auto previous_row =(selected_row + num_rows - 1) % num_rows;
    _table->selectRow(previous_row);
    _processor.getFavoritesModelV2()->uiRecallFavoriteAtRowNumber(previous_row);
}

void FavoritesComponent::_nextFavorites() {
    auto selected_row = _table->getLastRowSelected();
    if(selected_row == -1) {
        // no selection?  NOP
        return;
    }
    auto num_rows = getNumRows();
    if(num_rows == 0 || num_rows == 1) {
        // NOP
        return;
    }

    auto next_row = (selected_row + 1) % num_rows;
    _table->selectRow(next_row);
    _processor.getFavoritesModelV2()->uiRecallFavoriteAtRowNumber(next_row);
}

void FavoritesComponent::_deleteKeyModalCallback(int modalResult, FavoritesComponent* t, int lastRowSelected) {
    if(modalResult == 1 && t != nullptr) {
        t->_deleteFavoriteAtRow(lastRowSelected);
    }
}

void FavoritesComponent::_deleteFavoriteAtRow(int row) {
    _processor.getFavoritesModelV2()->uiDeleteFavoriteAtRowNumber(row);
}
