/*
  ==============================================================================

    MorphComponent.cpp
    Created: 17 Dec 2023 1:42:18pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "DesignsModel.h"
#include "FavoritesModelV2.h"
#include "Morph.h"
#include "MorphComponent.h"
#include "MorphFavoritesAComponent.h"
#include "MorphFavoritesBComponent.h"
#include "MorphModel.h"
#include "MorphTuningComponent.h"
#include "WilsonicAppSkin.h"

MorphComponent::MorphComponent(WilsonicProcessor& processor)
: WilsonicAppTuningComponent(processor)
{
    // models
    auto mm = _processor.getMorphModel();
    auto fm = _processor.getFavoritesModelV2();
    
    // favorites A
    _tableA = make_unique<MorphFavoritesAComponent>(_processor);
    addAndMakeVisible(*_tableA);

    // swap button
    _swapButton = make_unique<TextButton>("S", "Swap the two tunings");
    _swapButton->setToggleState(false, dontSendNotification);
    addAndMakeVisible(*_swapButton);
    _swapButton->addListener(this);

    // favorites B
    _tableB = make_unique<MorphFavoritesBComponent>(_processor);
    addAndMakeVisible(*_tableB);

    // morph tuning component
    _tuningComponent = make_unique<MorphTuningComponent>(_processor);
    addAndMakeVisible(*_tuningComponent);
    
    // interpolation type
    _interpolationTypeComboBox = make_unique<DeltaComboBox>(_processor, true);
    _interpolationTypeComboBox->addItemList(Morph::getInterpolationTypeNames(), 1);
    auto const selectedInterpolationTypeIndex = mm->uiGetInterpolationTypeIndex();
    _interpolationTypeComboBox->setSelectedItemIndex(selectedInterpolationTypeIndex, NotificationType::dontSendNotification);
    _interpolationTypeComboBox->setToolTip("Morph Interpolation Type");
    auto onChange = [this, mm]()
    {
        // Get the selected item index from the combo box
        auto const selectedItemIndex = _interpolationTypeComboBox->getSelectedItemIndex();
        
        // Set the scale in the scales object
        mm->uiSetInterpolationTypeIndex(selectedItemIndex);
    };
    _interpolationTypeComboBox->setOnChange(onChange);
    addAndMakeVisible(*_interpolationTypeComboBox);

    // Slider: Generator
    addAndMakeVisible(_interpolationValueSlider);
    _interpolationValueSlider.setRange(Morph::getInterpolationMin(), Morph::getInterpolationMax(), 0);
    _interpolationValueSlider.setValue(mm->uiGetInterpolationValue());
    _interpolationValueSlider.setTooltip("Interpolation");
    _interpolationValueSlider.setNumDecimalPlacesToDisplay(6);
    _interpolationValueSlider.onValueChange = [this, mm]
    {
        mm->uiSetInterpolationValue(static_cast<float>(_interpolationValueSlider.getValue()));
    };

    // status label
    addAndMakeVisible(_statusLabel);
    _statusLabel.setText(MorphComponentMessageBus::getInstance().getMessage(), dontSendNotification);
    _statusLabel.setJustificationType(Justification::Flags::right);
    _statusLabel.setTooltip(MorphComponentMessageBus::getInstance().getMessages());
    auto const labelFontSize = WilsonicAppSkin::messageBusFontSize;
    auto const font = Font::plain;
    _statusLabel.setFont(Font(FontOptions(labelFontSize, font)));

    // Register as the listener to the [only] MorphComponentMessageBus
    MorphComponentMessageBus::getInstance().setMenuMessageListener(this);

    // Add this as a listener to the model in the processor
    mm->addActionListener(this);

    // Add this as a listener to the global app tuning (for color offset changes)
    _processor.getAppTuningModel()->addActionListener(this);
}

MorphComponent::~MorphComponent()
{
    _processor.getMorphModel()->removeActionListener(this);
    _processor.getAppTuningModel()->removeActionListener(this);
    _swapButton->removeListener(this);
    MorphComponentMessageBus::getInstance().setMenuMessageListener(nullptr);
}

void MorphComponent::paint(juce::Graphics& g)
{
    // BG
    g.fillAll(_processor.getAppSkin().getBgColor());

    if (AppExperiments::showDebugBoundingBox)
    {
        // DEBUG
        g.setColour(Colours::lightgreen);
        g.drawRect(getLocalBounds(), 1);
        g.drawRect(_interpolationValueSlider.getBounds(), 1);

        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
    
    _tuningComponent->repaint();
}

void MorphComponent::resized()
{
    // local bounds minus margin
    auto const margin = static_cast<int>(WilsonicAppSkin::tuningComponentInteriorMargin);
    Rectangle<int> area = getLocalBounds().reduced(margin);

    // slider+combobox
    auto sliderArea = area.removeFromBottom(static_cast<int>(WilsonicAppSkin::sliderHeight));
    auto interpTypeArea = sliderArea.removeFromRight(160);
    _interpolationValueSlider.setBounds(sliderArea);
    _interpolationTypeComboBox->setBounds(interpTypeArea);
    
    // proportion of favorite boxes to morph tuning drawing
    auto const prop = 0.5f;
    auto const fbmtdp = jmax(static_cast<int>(prop*(area.getHeight() - margin)), 1);
    auto const mtd = area.removeFromBottom(fbmtdp);
    _tuningComponent->setBounds(mtd);
    
    // status label
    auto sla = area.removeFromTop(static_cast<int>(WilsonicAppSkin::comboBoxHeight));
    sla.removeFromRight(margin + static_cast<int>(WilsonicAppSkin::minHitPointSize));
    _statusLabel.setBounds(sla);
    
    // favorite boxes, swap button
    auto const fbw = static_cast<int>(0.5f*(area.getWidth() - 3.f * margin));
    auto const fba = area.removeFromLeft(fbw);
    auto const fbb = area.removeFromRight(fbw);
    _tableA->setBounds(fba.withTrimmedRight(margin));
    _tableB->setBounds(fbb.withTrimmedLeft(margin));
    
    // swap button
    auto const sh = static_cast<int>(0.5f * (area.getHeight() - 2.f * margin));
    _swapButton->setBounds(area.withTrimmedTop(sh).withTrimmedBottom(sh));
}

void MorphComponent::handleMessage(const String& message)
{
    // Update the status label with the received message
    _statusLabel.setText(message, dontSendNotification);
    _statusLabel.setTooltip(MorphComponentMessageBus::getInstance().getMessages());
    resized();
}

/**
 * @brief Get the app tuning title.
 * @return The app tuning title.
 */
#pragma mark - App Tuning Title

const string MorphComponent::getAppTuningTitle()
{
    return "Morph";
}

/**
 * @brief Update the UI when the tuning has changed.
 */
#pragma mark - tuning changed

void MorphComponent::_tuningChangedUpdateUI()
{
    //
    auto const mtm = _processor.getMorphModel();
    _interpolationValueSlider.setValue(mtm->uiGetInterpolationValue(), dontSendNotification);
    
    // combo box
    auto const mode = static_cast<int>(mtm->uiGetInterpolationTypeIndex());
    _interpolationTypeComboBox->setSelectedItemIndex(mode, dontSendNotification);

    // Resize the component
    resized();
    
    // Repaint the component
    repaint();
}

/**
 * @brief ActionListener methods for the Persian17NorthIndianComponent class.
 */
#pragma mark - ActionListener

/**
 * @brief Callback for the ActionListener.
 * @param message The action message.
 */
void MorphComponent::actionListenerCallback(const String& message)
{
    // If the message is that the tuning has changed
    if (message == DesignsModel::getMorphTuningChangedActionMessage())
    {
        // Update the UI
        _tuningChangedUpdateUI();
    }
    // If the message is that the app tuning model has changed
    else if (message == AppTuningModel::getAppTuningModelChangedMessage()) // color changed
    {
        // Repaint the component
        repaint();
    }
}

#pragma mark - Button handler

void MorphComponent::buttonClicked(Button* button)
{
    // "<->" swap tunings
    auto sb = dynamic_cast<Button*>(_swapButton.get());
    if(sb == button)
    {
        _processor.getMorphModel()->uiSwapTunings();
        
        return;
    }

    //
    jassertfalse;
}
