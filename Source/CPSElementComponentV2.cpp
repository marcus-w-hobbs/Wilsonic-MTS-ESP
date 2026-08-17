/*
  ==============================================================================

    CPSElementComponentV2.cpp
    Created: 8 Jan 2022 12:21:08pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "CPSElementComponentV2.h"
#include "AppExperiments.h"

#pragma mark - lifecycle

CPSElementComponentV2::CPSElementComponentV2(WilsonicProcessor& processor)
: WilsonicAppTuningComponent(processor)
{
    // pitch wheel
    _tuningRenderer = make_unique<TuningRendererComponent> (_processor, AppExperiments::tuningRendererPlayingNotes);
    _tuningRenderer->setTuning(_tuning);
    _tuningRenderer->setInterceptsMouseClicks(false, false); // pass mouse events up the chain
    addAndMakeVisible (*_tuningRenderer);

    // label on top of pitch wheel
    _tuningNameLabel = make_unique<Label> ("tuning_name", "");
    _tuningNameLabel->setJustificationType(Justification::topLeft);
    _tuningNameLabel->setInterceptsMouseClicks(false, false);
    addAndMakeVisible (*_tuningNameLabel);

    // label below name label which shows the number of notes per octave
    _tuningNPOLabel = make_unique<Label> ("tuning_npo", "");
    _tuningNPOLabel->setJustificationType(Justification::topLeft);
    _tuningNPOLabel->setInterceptsMouseClicks(false, false);
    addAndMakeVisible (*_tuningNPOLabel);

    // default window size
    setSize(_processor.getAppSkin().getWindowWidth(), _processor.getAppSkin().getWindowHeight());

    // add this as listener of the global app tuning(for color offset changes)
    _processor.getAppTuningModel()->addActionListener(this);
}

CPSElementComponentV2::~CPSElementComponentV2() {
    _processor.getAppTuningModel()->removeActionListener(this);
}

#pragma mark - drawing

void CPSElementComponentV2::paint(Graphics& g) {
    // BG
    g.fillAll(_processor.getAppSkin().getBgColor());

    if(AppExperiments::showDebugBoundingBox) {
        // DEBUG
        g.setColour(Colours::darkgrey);
        g.drawRect(getLocalBounds(), 1);

        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }

    if(_isSelected) {
        g.setColour(_processor.getAppSkin().getSelectedComponentColor());
        g.drawRect(getLocalBounds(), 2);
    }

    // null tuning = NOP
    if(_tuning == nullptr) {
        return;
    }

    // "pitch wheel"
    _tuningRenderer->repaint();
}

void CPSElementComponentV2::resized() {
    if(_tuning == nullptr) {
        return;
    }

    // Global
    auto area = getLocalBounds().reduced(4); // so selected outline shows

    // pitch wheel
    _tuningRenderer->setBounds(area);

    // font height as proportion of square window height
    auto const fH = static_cast<int>(jmax(18.f, 0.025f * area.getHeight()));

    // tuning name label
    _tuningNameLabel->setFont(Font(FontOptions(fH)).withHorizontalScale(0.9f));
    auto nameLabelArea = Rectangle<int>(area.getX() + (!_labelIsHidden ? 0 : area.getWidth()),
                                         area.getY(),
                                         area.getWidth(), fH);
    _tuningNameLabel->setBounds(nameLabelArea);

    // tuning NPO label
    _tuningNPOLabel->setFont(Font(FontOptions(2.f * fH)).withHorizontalScale(0.9f));
    auto npoLabelArea = Rectangle<int>(area.getX() + (!_npoLabelIsHidden ? 0 : area.getWidth()),
                                        nameLabelArea.getY() + nameLabelArea.getHeight(),
                                        static_cast<int>(0.5f * area.getWidth()), static_cast<int>(2.f * fH));
    _tuningNPOLabel->setBounds(npoLabelArea);
}

// 1 = default logic
void CPSElementComponentV2::setCustomFontScale(float scale01) {
    _tuningRenderer->setCustomFontScale(scale01);
}

void CPSElementComponentV2::setHideNPOLabel(bool shouldHide) {
    _npoLabelIsHidden = shouldHide;
    resized();
}

void CPSElementComponentV2::setHideLabel(bool shouldHide) {
    _labelIsHidden = shouldHide;
    resized();
}

#pragma mark - Tuning

void CPSElementComponentV2::setTuning(shared_ptr<CPSTuningBase> inputTuning) {
    _tuning = inputTuning;
    if(_tuning == nullptr) {
        return;
    }

    _tuningRenderer->setTuning(_tuning);
    _tuningNameLabel->setText(_tuning->getTuningName(), NotificationType::dontSendNotification);
    _tuningNPOLabel->setText(String(_tuning->getProcessedArrayCount()), NotificationType::dontSendNotification);
    repaint();
}

const shared_ptr<CPSTuningBase> CPSElementComponentV2::getTuning() {
    return _tuning;
}

#pragma mark - completion handler

void CPSElementComponentV2::setSingleClickCompletionBlock(function<void()> completionBlock) {
    _singleClickCompletionBlock = completionBlock;
}

void CPSElementComponentV2::setControlClickCompletionBlock(function<void()> completionBlock) {
    _controlClickCompletionBlock = completionBlock;
}

void CPSElementComponentV2::setCommandClickCompletionBlock(function<void()> completionBlock) {
    _commandClickCompletionBlock = completionBlock;
}

#pragma mark - App Tuning Title

const string CPSElementComponentV2::getAppTuningTitle() {
    return "invalid";
}

#pragma mark - selection

const bool CPSElementComponentV2::getIsSelected() {
    return _isSelected;
}

void CPSElementComponentV2::setIsSelected(bool newValue) {
    _isSelected = newValue;
    repaint();
}

#pragma mark - click handlers

void CPSElementComponentV2::mouseEnter(const MouseEvent& event) {
    auto const shiftDown = event.mods.isShiftDown();
    if(shiftDown) {
        _mouseHelper(event);
    }
}

void CPSElementComponentV2::mouseDown(const MouseEvent& event) {
    _mouseHelper(event);
}

void CPSElementComponentV2::mouseDoubleClick(const MouseEvent& event) {
    _mouseHelper(event);
}

void CPSElementComponentV2::_mouseHelper(const MouseEvent& event) {
    // no tuning = this component is a nop
    if(_tuning == nullptr) {
        return;
    }

    // give priority to shift, per componentid
    auto const shiftDown = event.mods.isShiftDown();
    if(shiftDown) {
        if(_singleClickCompletionBlock != nullptr) {
            _singleClickCompletionBlock();
            return;
        }
    }

    // then ctrl, per component id
    auto const ctrlDown = event.mods.isCtrlDown();
    if(ctrlDown) {
        if(_controlClickCompletionBlock != nullptr) {
            _controlClickCompletionBlock();
            return;
        }
    }

    // then "any" modifier, which on a mac equals "command"...not keyed off element
    auto const commandDown = event.mods.isAnyModifierKeyDown();
    if(commandDown) {
        if(_commandClickCompletionBlock != nullptr) {
            _commandClickCompletionBlock();
            return;
        }
    }
}

#pragma mark - ActionListener

void CPSElementComponentV2::actionListenerCallback(const String& message) {
    if(message == AppTuningModel::getAppTuningModelChangedMessage()) { // pitch color changed
        repaint();
    }
}
