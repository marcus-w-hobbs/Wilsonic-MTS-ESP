/*
  ==============================================================================

    RecurrenceRelationComponent.cpp
    Created: 21 Mar 2022 9:28:45pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "DesignsModel.h"
#include "RecurrenceRelationComponent.h"
#include "RecurrenceRelationModel.h"

RecurrenceRelationComponent::RecurrenceRelationComponent(WilsonicProcessor& processor)
: WilsonicAppTuningComponent(processor)
, _coefficientBubble(BubblePlacement::right, "C", "Coefficients: The coefficient for the term above")
, _seedBubble(BubblePlacement::right, "S", "Seeds: The initial conditions of the recurrence relation")
, _indexBubble(BubblePlacement::right, "I", "Index: The recurrence relations from H[n-1]+H[n-2] to H[n-8]+H[n-9]")
, _offsetBubble(BubblePlacement::left, "O", "Skip this number of terms to start the scale")
, _numTermsBubble(BubblePlacement::left, "T", "The number of terms in the final scale, i.e., the number of notes per octave")
, _sumTypeBubble(BubblePlacement::left, "+", "Sum Type: Arithmetic (a+b) or Harmonic (ab/(a+b))")
, _seedSpaceBubble(BubblePlacement::left, "~", "Seed Space: Frequency (as-is) or Period (inverted)")
{
    // model
    auto const rrm = _processor.getRecurrenceRelationModel();
    auto const rrt = static_pointer_cast<RecurrenceRelation>(rrm->getTuning());

    // Bubble: Seeds
    addAndMakeVisible(_seedBubble);

    // seed slider
    _seedSliderComponent = make_unique<RecurrenceRelationSeedComponent>(_processor);
    addAndMakeVisible(*_seedSliderComponent);

    // Bubble: Coefficient
    addAndMakeVisible(_coefficientBubble);

    // coefficient combobox
    _coefficientSliderComponent = make_unique<RecurrenceRelationCoefficientComponent>(_processor);
    addAndMakeVisible(*_coefficientSliderComponent);

    // Bubble: Index
    addAndMakeVisible(_indexBubble);

    // index slider
    _indexComboBox = make_unique<DeltaComboBox>(_processor, false);
    _indexComboBox->addItemList(RecurrenceRelation::getIndicesDescription(), 1);
    _indexComboBox->setToolTip("Recurrence Relation Indices");
    _indexComboBox->setSelectedItemIndex(0, NotificationType::dontSendNotification);
    auto onChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_indexComboBox->getSelectedItemIndex());
        rrm->uiSetIndices(selectedItemIndex);
    };
    _indexComboBox->setOnChange(onChange);
    addAndMakeVisible(*_indexComboBox);

    // Bubble: number of terms
    addAndMakeVisible(_numTermsBubble);

    // number of terms slider
    _numTermsSlider = make_unique<SeedSlider>(_processor, "Terms", RecurrenceRelation::getNumberOfTermsMin(), rrm->uiGetNumberOfTerms(), RecurrenceRelation::getNumberOfTermsMax(), 1, [rrm] (float n) {rrm->uiSetNumberOfTerms(static_cast<unsigned long>(n));});
    addAndMakeVisible(*_numTermsSlider);

    // Bubble: Offset
    addAndMakeVisible(_offsetBubble);

    // Offset
    _offsetSlider = make_unique<SeedSlider>(_processor, "Offset", RecurrenceRelation::getOffsetMin(), rrm->uiGetOffset(), RecurrenceRelation::getOffsetMax(), 1, [rrm] (float o) {rrm->uiSetOffset(static_cast<unsigned long>(o));});
    addAndMakeVisible(*_offsetSlider);

    // Bubble: Sum Type
    addAndMakeVisible(_sumTypeBubble);

    // Sum Type ComboBox
    _sumTypeComboBox = make_unique<DeltaComboBox>(_processor, false);
    _sumTypeComboBox->addItemList(RecurrenceRelation::getSumTypeDescription(), 1);
    _sumTypeComboBox->setToolTip("Sum Type: Arithmetic or Harmonic");
    _sumTypeComboBox->setSelectedItemIndex(static_cast<int>(rrm->uiGetSumType()), NotificationType::dontSendNotification);
    auto onSumTypeChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_sumTypeComboBox->getSelectedItemIndex());
        rrm->uiSetSumType(selectedItemIndex);
    };
    _sumTypeComboBox->setOnChange(onSumTypeChange);
    addAndMakeVisible(*_sumTypeComboBox);

    // Bubble: Seed Space
    addAndMakeVisible(_seedSpaceBubble);

    // Seed Space ComboBox
    _seedSpaceComboBox = make_unique<DeltaComboBox>(_processor, false);
    _seedSpaceComboBox->addItemList(RecurrenceRelation::getSeedSpaceDescription(), 1);
    _seedSpaceComboBox->setToolTip("Seed Space: Frequency or Period");
    _seedSpaceComboBox->setSelectedItemIndex(static_cast<int>(rrm->uiGetSeedSpace()), NotificationType::dontSendNotification);
    auto onSeedSpaceChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_seedSpaceComboBox->getSelectedItemIndex());
        rrm->uiSetSeedSpace(selectedItemIndex);
    };
    _seedSpaceComboBox->setOnChange(onSeedSpaceChange);
    addAndMakeVisible(*_seedSpaceComboBox);

    // Pitch Wheel
    _pitchWheelComponent = make_unique<WilsonicPitchWheelComponent>(_processor, AppExperiments::tuningRendererPlayingNotes);
    _pitchWheelComponent->setTuning(rrt);
    _pitchWheelComponent->setCustomFontScale(WilsonicAppSkin::defaultPitchWheelFontScale);
    addAndMakeVisible(*_pitchWheelComponent);

    // Text Editor
    _textEditor = make_unique<TextEditor>();
    _textEditor->setReadOnly(true);
    _textEditor->setMultiLine(true);
    _textEditor->setText(rrt->getLog());
    _textEditor->setColour(TextEditor::ColourIds::backgroundColourId, _processor.getAppSkin().getBgColor());
    addAndMakeVisible(*_textEditor);

    // default window size
    setSize(_processor.getAppSkin().getWindowWidth(), _processor.getAppSkin().getWindowHeight());

    // initialize the ui. [confirmed we need this here]
    _tuningChangedUpdateUI();

    // add this as listener to model
    _processor.getRecurrenceRelationModel()->addActionListener(this);
}

RecurrenceRelationComponent::~RecurrenceRelationComponent() {
    _processor.getRecurrenceRelationModel()->removeActionListener(this);
}

void RecurrenceRelationComponent::paint(Graphics& g) {
    g.fillAll(_processor.getAppSkin().getBgColor());

    // DEBUG
    if (AppExperiments::showDebugBoundingBox) {
        g.setColour(Colours::lightgreen);
        g.drawRect(getLocalBounds(), 1);

        g.drawRect(_coefficientBubble.getBounds(), 1);
        g.drawRect(_coefficientSliderComponent->getBounds(), 1);

        g.drawRect(_seedBubble.getBounds(), 1);
        g.drawRect(_seedSliderComponent->getBounds(), 1);

        g.drawRect(_indexBubble.getBounds(), 1);
        g.drawRect(_indexComboBox->getBounds(), 1);

        g.drawRect(_offsetBubble.getBounds(), 1);
        g.drawRect(_offsetSlider->getBounds(), 1);

        g.drawRect(_numTermsBubble.getBounds(), 1);
        g.drawRect(_numTermsSlider->getBounds(), 1);

        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
}

void RecurrenceRelationComponent::resized() {
    auto const margin = static_cast<int>(WilsonicAppSkin::tuningComponentInteriorMargin);
    auto const bubble_width = static_cast<int>(WilsonicAppSkin::minHitPointSize);
    auto const seed_slider_width = static_cast<int>(WilsonicAppSkin::seedSliderHeight);
    auto area = getLocalBounds().reduced(margin);

    // indices, terms, offset
    auto to_area = area.removeFromTop(static_cast<int>(WilsonicAppSkin::seedSliderHeight));
    auto to_left_area = to_area.withTrimmedRight(static_cast<int>(0.666f * to_area.getWidth()));
    auto to_middle_area = to_area.withTrimmedRight(static_cast<int>(0.666f * to_area.getWidth()));
    to_middle_area.setX(static_cast<int>(to_middle_area.getX() + 0.333f * to_area.getWidth()));
    auto to_right_area = to_area.withTrimmedLeft(static_cast<int>(0.666f * to_area.getWidth()));

    // left area: indices
    to_left_area.removeFromTop(15); // combo box is shorter than sliders
    to_left_area.removeFromBottom(15);
    auto iba = to_left_area.removeFromLeft(bubble_width);
    _indexBubble.setBounds(iba);
    to_left_area.removeFromRight(50); // tweak the right side
    _indexComboBox->setBounds(to_left_area);

    // middle area: number of terms
    auto ma = to_middle_area.withSizeKeepingCentre(seed_slider_width + bubble_width, to_middle_area.getHeight());
    auto tba = ma.removeFromLeft(bubble_width);
    _numTermsBubble.setBounds(tba);
    _numTermsSlider->setBounds(ma);

    // right area: offset
    auto ra = to_right_area.withSizeKeepingCentre(seed_slider_width + bubble_width, to_right_area.getHeight());
    auto oba = ra.removeFromLeft(bubble_width);
    _offsetBubble.setBounds(oba);
    _offsetSlider->setBounds(ra);

    // y margin
    area.removeFromTop(margin);

    // Sum Type and Seed Space row
    auto mode_area = area.removeFromTop(static_cast<int>(WilsonicAppSkin::comboBoxHeight));
    auto mode_left_area = mode_area.withTrimmedRight(static_cast<int>(0.5f * mode_area.getWidth()));
    auto mode_right_area = mode_area.withTrimmedLeft(static_cast<int>(0.5f * mode_area.getWidth()));

    // Sum Type (left)
    auto stba = mode_left_area.removeFromLeft(bubble_width);
    _sumTypeBubble.setBounds(stba);
    mode_left_area.removeFromRight(margin);
    _sumTypeComboBox->setBounds(mode_left_area);

    // Seed Space (right)
    auto ssba = mode_right_area.removeFromLeft(bubble_width);
    _seedSpaceBubble.setBounds(ssba);
    mode_right_area.removeFromRight(margin);
    _seedSpaceComboBox->setBounds(mode_right_area);

    // y margin, top
    area.removeFromTop(static_cast<int>(margin));

    // Seeds
    auto seedsArea = area.removeFromTop(static_cast<int>(WilsonicAppSkin::seedSliderHeight));
    auto sba = seedsArea.removeFromLeft(bubble_width);
    _seedBubble.setBounds(sba);
    _seedSliderComponent->setBounds(seedsArea);

    // y margin, top
    area.removeFromTop(margin);

    // Coefficients
    auto coefficientArea = area.removeFromTop(static_cast<int>(WilsonicAppSkin::comboBoxHeight));
    auto cba = coefficientArea.removeFromLeft(bubble_width);
    _coefficientBubble.setBounds(cba);
    _coefficientSliderComponent->setBounds(coefficientArea);

    // y margin, top
    area.removeFromTop(margin);

    // left right
    auto const left_right_01 = 0.5f; //0.75f;
    auto p_area = area.withTrimmedRight(static_cast<int>(left_right_01 * area.getWidth()));
    auto l_area = area.withTrimmedLeft(static_cast<int>((1 - left_right_01) * area.getWidth()));

    // pitch wheel
    _pitchWheelComponent->setBounds(p_area);

    // text editor
    _textEditor->setBounds(l_area);
}

#pragma mark - App Tuning Title

const string RecurrenceRelationComponent::getAppTuningTitle() {
    return "Recurrence Relation";
}

#pragma mark - tuning changed

void RecurrenceRelationComponent::_tuningChangedUpdateUI() {
    const auto rrm = _processor.getRecurrenceRelationModel();
    auto const rrt = static_pointer_cast<RecurrenceRelation>(rrm->getTuning());
    _coefficientSliderComponent->selectIJ(rrt->getIndexI(), rrt->getIndexJ());
    _seedSliderComponent->selectIJ(rrt->getIndexI(), rrt->getIndexJ());
    _indexComboBox->setSelectedItemIndex(static_cast<int>(rrm->uiGetIndices()), NotificationType::dontSendNotification);
    _textEditor->setText(rrt->getLog());
    _coefficientSliderComponent->setC_1_9(rrm->uiGetCoefficient(1),
                                          rrm->uiGetCoefficient(2),
                                          rrm->uiGetCoefficient(3),
                                          rrm->uiGetCoefficient(4),
                                          rrm->uiGetCoefficient(5),
                                          rrm->uiGetCoefficient(6),
                                          rrm->uiGetCoefficient(7),
                                          rrm->uiGetCoefficient(8),
                                          rrm->uiGetCoefficient(9),
                                          dontSendNotification);
    _seedSliderComponent->setH_1_9(rrm->uiGetSeed(1),
                                   rrm->uiGetSeed(2),
                                   rrm->uiGetSeed(3),
                                   rrm->uiGetSeed(4),
                                   rrm->uiGetSeed(5),
                                   rrm->uiGetSeed(6),
                                   rrm->uiGetSeed(7),
                                   rrm->uiGetSeed(8),
                                   rrm->uiGetSeed(9),
                                   dontSendNotification);

    // Update Sum Type and Seed Space combo boxes
    _sumTypeComboBox->setSelectedItemIndex(
        static_cast<int>(rrm->uiGetSumType()),
        NotificationType::dontSendNotification);
    _seedSpaceComboBox->setSelectedItemIndex(
        static_cast<int>(rrm->uiGetSeedSpace()),
        NotificationType::dontSendNotification);

    // draw
    resized();
}

#pragma mark - ActionListener

void RecurrenceRelationComponent::actionListenerCallback(const String& message) {
    if (message == DesignsModel::getRecurrenceRelationTuningChangedActionMessage()) {
        _tuningChangedUpdateUI();
    } else if (message == DesignsModel::getRecurrenceRelationTuningDivergedActionMessage()) {
        // custom components need intervention
        const auto rrm = _processor.getRecurrenceRelationModel();
        auto const rrt = static_pointer_cast<RecurrenceRelation>(rrm->getTuning());
        _textEditor->setText(rrt->getLog());
        jassertfalse;
    } else {
        jassertfalse;
    }
}
