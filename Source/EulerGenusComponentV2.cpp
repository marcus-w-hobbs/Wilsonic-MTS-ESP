/*
  ==============================================================================

    EulerGenus6Component.cpp
    Created: 27 Nov 2021 6:37:37pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "CPS.h"
#include "BubbleDrawable.h"
#include "DesignsModel.h"
#include "EulerGenusComponentV2.h"

String const EulerGenusComponentV2::__mainElementBubbleText = "Master Set:\nThe subsets to the right are\nall contained in this structure.\n\n* Selected scale is outlined in blue\n* Shift-Mouse-Hover selects scale\n* Ctrl-Click navigates down into subset\n* Command-Click navigates up into superset\n* Cursor Left-Right-Up-Down selects scale";
String const EulerGenusComponentV2::__eg6BubbleText = "Master Sets:\nIf each of the six seeds are co-prime,\nthen each of these master sets\nwill contain unique notes not present\nin the others.\n\n* Selected scale is outlined in blue\n* Shift-Mouse-Hover selects scale\n* Cursor Left-Right selects scale\n* Ctrl-Click drills into Subset page";
String const EulerGenusComponentV2::__subsetsBubbleText = "Subsets:\nEach of these tunings is\ncontained in the master set to the left.\n\n* Shift-Mouse-Hover selects scale\n* Ctrl-Click navigates down into subset\n* Command-Click navigates up into superset\n* Cursor Left-Right-Up-Down selects scale";

EulerGenusComponentV2::EulerGenusComponentV2(WilsonicProcessor& processor)
: WilsonicAppTuningComponent(processor)
, _mainElementBubble(BubblePlacement::below, "M", __mainElementBubbleText)
, _subsetsBubble(BubblePlacement::below, "S", __subsetsBubbleText)
{
    // model
    auto const egm = _processor.getEulerGenusModel();

    // bubbles
    addAndMakeVisible(_mainElementBubble);
    addAndMakeVisible(_subsetsBubble);

    // seed slider
    _seedSliderComponent = make_unique<SeedSliderComponent>(_processor);
    addAndMakeVisible(*_seedSliderComponent);
    _seedSliderComponent->setSliderAtIndex(0, "A", egm->uiGetA(), [egm] (float f) {egm->uiSetA(f);});
    _seedSliderComponent->setSliderAtIndex(1, "B", egm->uiGetB(), [egm] (float f) {egm->uiSetB(f);});
    _seedSliderComponent->setSliderAtIndex(2, "C", egm->uiGetC(), [egm] (float f) {egm->uiSetC(f);});
    _seedSliderComponent->setSliderAtIndex(3, "D", egm->uiGetD(), [egm] (float f) {egm->uiSetD(f);});
    _seedSliderComponent->setSliderAtIndex(4, "E", egm->uiGetE(), [egm] (float f) {egm->uiSetE(f);});
    _seedSliderComponent->setSliderAtIndex(5, "F", egm->uiGetF(), [egm] (float f) {egm->uiSetF(f);});
    _seedSliderComponent->setSliderAtIndex(6, "G", 1.f, [] (float) {;});
    _seedSliderComponent->setSliderAtIndex(7, "H", 1.f, [] (float) {;});

    // Genus Space toggle: automatable; when on, the drill-path root CPS(6,k)
    // remains the global tuning table/MIDI mapping while drilling into subsets
    _genusSpaceToggle.setButtonText("Genus Space");
    _genusSpaceToggle.setTooltip("Keep the master set as the global tuning table and MIDI mapping while exploring subsets.\nThe keyboard shows the selected subset mapped into the master's MIDI space.");
    addAndMakeVisible(_genusSpaceToggle);
    _genusSpaceAttachment = make_unique<AudioProcessorValueTreeState::ButtonAttachment>
    (*_processor.getApvts(),
     EulerGenusModel::getEulerGenus6GenusSpaceParameterID().getParamID(),
     _genusSpaceToggle);

    // parent and subsets
    _mainElement = make_shared<CPSElementComponentV2>(_processor);
    addAndMakeVisible(*_mainElement);
    for (auto i = 0; i < CPS::__MAX_NUM_EULER_GENUS_6_SUBSETS; i++)
    {
        auto s0cpse = make_shared<CPSElementComponentV2>(_processor);
        _subsets0.push_back(s0cpse);
        addAndMakeVisible(*s0cpse);

        auto s1cpse = make_shared<CPSElementComponentV2>(_processor);
        _subsets1.push_back(s1cpse);
        addAndMakeVisible(*s1cpse);
    }

    // default window size
    setSize(_processor.getAppSkin().getWindowWidth(), _processor.getAppSkin().getWindowHeight());

    // initialize the ui. [confirmed we need this here]
    _tuningChangedUpdateUI();

    // add self as action listener to model
    egm->addActionListener(this);

    // add this as listener of the global app tuning (for color offset changes)
    _processor.getAppTuningModel()->addActionListener(this);

    // Component's "key listener"
    setWantsKeyboardFocus(true);
}

EulerGenusComponentV2::~EulerGenusComponentV2()
{
    _processor.getAppTuningModel()->removeActionListener(this);
    _processor.getEulerGenusModel()->removeActionListener(this);
}

#pragma mark - draw

void EulerGenusComponentV2::paint(Graphics& g)
{
    // BG
    g.fillAll(_processor.getAppSkin().getBgColor());

    if (AppExperiments::showDebugBoundingBox)
    {
        // DEBUG
        g.setColour(Colours::lightgreen);
        g.drawRect(getLocalBounds(), 1);

        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
}



// chatgpt suggestion
/*
 You can expand a component's bounds in JUCE by using the `Component::setBounds()` method in conjunction with the `Rectangle::expanded()` method.

 Here is an example where a parent component expands the bounds of a child component:

 ```cpp
 void ParentComponent::resized()
 {
 juce::Rectangle<int> childBounds = childComponent.getBounds();
 childComponent.setBounds(childBounds.expanded(10));  // Expand the child's bounds by 10 units on all sides
 }
 ```

 In this example, `childComponent` is a member of `ParentComponent`. The `resized()` method is called whenever the `ParentComponent` is resized. This method gets the current bounds of the `childComponent`, expands those bounds by 10 units on all sides, and then sets the `childComponent`'s bounds to the expanded rectangle.

 The `Rectangle::expanded()` method returns a new `Rectangle` that is larger than the original. The argument to `expanded()` is the amount to expand the rectangle on all sides. So `expanded(10)` will return a rectangle that is 20 units wider and 20 units taller than the original, and whose center is at the same position as the center of the original rectangle.

 Please replace `childComponent` with the actual name of your child component and `10` with the actual number of units you want to expand the child's bounds.

 */

void EulerGenusComponentV2::resized()
{
    // design pattern:
    // optimize for constant computation, including view hierarchy.
    // allocate a main component and 6x2 subset components
    // never modify the view hiearchy...just resize components
    // resize offscreen if neccessary.
    // i.e., resize 3 subsets on screen, and 3 off screen

    // VV just seeds for now...no eg presets combo box
    // | - seeds                                            - |

    // Keep the main area the same size even if there are no subsets
    auto const margin = WilsonicAppSkin::tuningComponentInteriorMargin;
    auto area = getLocalBounds().reduced(static_cast<int>(margin));

    // Seeds, with the Genus Space toggle on the right
    auto seedsArea = area.removeFromTop(static_cast<int>(WilsonicAppSkin::seedSliderHeight));
    auto const genusSpaceToggleWidth = 140;
    _genusSpaceToggle.setBounds(seedsArea.removeFromRight(genusSpaceToggleWidth));
    _seedSliderComponent->setBounds(seedsArea);

    // y margin between combo box and seeds
    area.removeFromTop(static_cast<int>(margin));

    // which tuning type?  euler genus or cps
    const bool isEulerGenus = _processor.getEulerGenusModel()->uiIsTuningEulerGenus();
    if (isEulerGenus)
    {
        _resizedEulerGenus(area);
    }
    else
    {
        _resizedCPS(area);
    }
}

// resize the Euler Genus tuning
void EulerGenusComponentV2::_resizedEulerGenus(Rectangle<int> a)
{
    // get view model
    const auto egm = _processor.getEulerGenusModel();
    const shared_ptr<EulerGenusViewModel> vm = egm->getViewModel();
    const shared_ptr<CPSTuningBase> parent_tuning = vm->parentTuning;
    jassert(parent_tuning != nullptr);

    // euler genus: only subsets0 is on screen
    auto const local_bounds = getLocalBounds();
    auto const offscreen_rect = Rectangle<int> (local_bounds.getWidth() + 1, local_bounds.getHeight() + 1, 100, 100);
    auto move_offscreen = [offscreen_rect] (shared_ptr<CPSElementComponentV2> element)
    {
        element->setBounds(offscreen_rect);
        element->setIsSelected(false);
    };
    move_offscreen(_mainElement);
    for (auto element : _subsets1)
    {
        move_offscreen(element);
    }

    // root EG layout
    // | subset 0 | subset 1 | ... | subset n               - |
    auto area = a;
    auto const bubble_width = static_cast<int>(WilsonicAppSkin::minHitPointSize);
    auto bubbleArea = area.removeFromTop(bubble_width);
    bubbleArea.reduce(static_cast<int>(0.5f * bubbleArea.getWidth() - 2 * bubble_width), 0);
    _mainElementBubble.setBounds(bubbleArea);
    _mainElementBubble.setDescription(__eg6BubbleText);
    _subsetsBubble.setBounds(offscreen_rect); // hide this bubble
    auto const numberOfColumns = float(_subsets0.size());
    auto const num_s0 = parent_tuning->getSubsets0().size();
    auto const columnWidth = area.getWidth() / numberOfColumns;

    // TODO: add the selected subset sizing
    for (unsigned long i = 0; i < CPS::__MAX_NUM_EULER_GENUS_6_SUBSETS; i++)
    {
        // bounds
        auto subset_area = area.removeFromLeft(static_cast<int>(columnWidth));
        auto element = _subsets0[i];
        auto tuning = parent_tuning->getSubsets0()[i];
        if (i < num_s0)
        {
            element->setBounds(subset_area);
            element->setIsSelected(tuning->getIsSelected());
            element->setCustomFontScale(WilsonicAppSkin::defaultPitchWheelFontScale);
            element->repaint();
        }
        else
        {
            move_offscreen(element);
        }
    }
}

// Resize the CPS parent tuning and it's subsets
void EulerGenusComponentV2::_resizedCPS(Rectangle<int> a) {
    // get view model
    const auto egm = _processor.getEulerGenusModel();
    const shared_ptr<EulerGenusViewModel> vm = egm->getViewModel();
    auto parent_tuning = vm->parentTuning;
    jassert(parent_tuning != nullptr);

    // LAYOUT

    // vertical orientation of the subsets:
    // | main element area 80% | subset0 10% | subset1 10% |
    //
    auto area = a;
    auto const mainWidthProportion = 0.5f;
    auto const bubble_width = static_cast<int>(WilsonicAppSkin::minHitPointSize);
    auto const singleSubsetWidthProportion = 0.5f * (1.f - mainWidthProportion);
    auto const columnWidth = area.getWidth() * singleSubsetWidthProportion; // calc first
    auto const subsetPitchWheelFontSizeMagic = 0.55f;
    auto const local_bounds = getLocalBounds();
    auto const offscreen_rect = Rectangle<int>(local_bounds.getWidth() + 1, local_bounds.getHeight()+1, 100, 100);
    auto move_offscreen = [offscreen_rect](shared_ptr<CPSElementComponentV2> element) {
        element->setBounds(offscreen_rect);
        element->setIsSelected(false);
    };

    // main element area
    auto mainArea = area.removeFromLeft(static_cast<int>(area.getWidth() * mainWidthProportion));
    auto bubbleAreaMain = mainArea.removeFromTop(bubble_width);
    bubbleAreaMain.reduce(static_cast<int>(0.5f * bubbleAreaMain.getWidth() - 2 * bubble_width), 0);
    _mainElementBubble.setBounds(bubbleAreaMain);
    _mainElementBubble.setDescription(__mainElementBubbleText);
    _mainElement->setIsSelected(parent_tuning->getIsSelected());
    _mainElement->setBounds(mainArea);
    _mainElement->setCustomFontScale(WilsonicAppSkin::defaultPitchWheelFontScale);
    _mainElement->repaint();

    // subset columns
    auto const num_s0 = parent_tuning->getSubsets0().size();
    auto const num_s1 = parent_tuning->getSubsets1().size();
    auto const numSubsetColumns = (num_s0 > 0 ? 1 : 0) + (num_s1 > 0 ? 1 : 0);

    // no subsets
    if (numSubsetColumns == 0) {
        for (auto element : _subsets0) {
            move_offscreen(element);
        }
        for (auto element : _subsets1) {
            move_offscreen(element);
        }
        return;
    }

    // bubble
    auto subsetBubbleArea = area.removeFromTop(bubble_width);
    subsetBubbleArea.reduce(static_cast<int>(0.5f * subsetBubbleArea.getWidth() - 2 * bubble_width), 0);
    _subsetsBubble.setBounds(subsetBubbleArea);

    // number of rows in subsets
    auto const numSubsetRows = static_cast<float>(num_s0); // subsets 0 and 1 are the same count
    auto const rowHeight = area.getHeight() / numSubsetRows;

    // if there is 1 set of subsets it will be in subset 0, and subset 1 will be empty
    if (numSubsetColumns == 1) {
        for (unsigned long i = 0; i < CPS::__MAX_NUM_EULER_GENUS_6_SUBSETS; i++) {
            auto subset_area = area.removeFromTop(static_cast<int>(rowHeight));
            auto element = _subsets0[i];
            if (i < num_s0) {
                auto tuning = parent_tuning->getSubsets0()[i];
                element->setBounds(subset_area);
                element->setIsSelected(tuning->getIsSelected());
                element->setCustomFontScale(subsetPitchWheelFontSizeMagic);
                element->repaint();
            } else {
                move_offscreen(element);
            }
        }
        for (auto element : _subsets1) {
            move_offscreen(element);
        }
    } else if (numSubsetColumns == 2) {
        for (unsigned long i = 0; i < CPS::__MAX_NUM_EULER_GENUS_6_SUBSETS; i++) {
            auto sa = area.removeFromTop(static_cast<int>(rowHeight));
            auto s0Area = sa.withTrimmedRight(static_cast<int>(columnWidth)).reduced(3);
            auto s1Area = sa.withTrimmedLeft(static_cast<int>(columnWidth)).reduced(3);

            // subset0
            auto s0 = _subsets0[i];
            if (i < num_s0) {
                auto tuning0 = parent_tuning->getSubsets0()[i];
                s0->setBounds(s0Area);
                s0->setIsSelected(tuning0->getIsSelected());
                s0->setCustomFontScale(subsetPitchWheelFontSizeMagic);
                s0->repaint();
            } else {
                move_offscreen(s0);
            }

            // subset1
            auto s1 = _subsets1[i];
            if (i < num_s1) {
                auto tuning1 = parent_tuning->getSubsets1()[i];
                s1->setBounds(s1Area);
                s1->setIsSelected(tuning1->getIsSelected());
                s1->setCustomFontScale(subsetPitchWheelFontSizeMagic);
                s1->repaint();
            } else {
                move_offscreen(s1);
            }
        }
    } else {
        // numSubsetColumns can only be 0, 1, or 2
        jassertfalse;
    }
}

#pragma mark - App Tuning Title

const string EulerGenusComponentV2::getAppTuningTitle() {
    return "Euler Genus 6";
}

#pragma mark - tuning changed

void EulerGenusComponentV2::_tuningChangedUpdateUI() {
    // tuning model is updated...need to update UI
    // do NOT send notifications to update the model
    const auto egm = _processor.getEulerGenusModel();

    // seed slider
    _seedSliderComponent->showNumberOfSliders(egm->getNumberOfSeeds()); // always 6 for eg6
    _seedSliderComponent->setABCDEF(egm->uiGetA(), egm->uiGetB(), egm->uiGetC(), egm->uiGetD(), egm->uiGetE(), egm->uiGetF(), dontSendNotification);

    // get view model
    const shared_ptr<EulerGenusViewModel> vm = egm->getViewModel();
    jassert(vm != nullptr);
    auto parent_tuning = vm->parentTuning;
    jassert(parent_tuning != nullptr);

    // main element tuning
    _mainElement->setTuning(parent_tuning);

    // this doesn't make sense for the EulerGenus level, but it makes sense for all others
    _mainElement->setSingleClickCompletionBlock([this,vm]() {singleClickDAWKey(vm->dawBackKey);} ); // main is back for subsets
    _mainElement->setControlClickCompletionBlock([this,vm]() {controlClickDAWKey(vm->dawDrillKey);} );
    _mainElement->setCommandClickCompletionBlock([this,vm]() {commandClickDAWKey(vm->dawBackKey);} );

    // subset tunings

    // clear subset components
    for(auto s0_element_component : _subsets0) {
        s0_element_component->setTuning(nullptr);
        s0_element_component->setSingleClickCompletionBlock(nullptr);
        s0_element_component->setControlClickCompletionBlock(nullptr);
        s0_element_component->setCommandClickCompletionBlock(nullptr);
    }
    for(auto s1_element_component : _subsets1) {
        s1_element_component->setTuning(nullptr);
        s1_element_component->setSingleClickCompletionBlock(nullptr);
        s1_element_component->setControlClickCompletionBlock(nullptr);
        s1_element_component->setCommandClickCompletionBlock(nullptr);
    }

    unsigned long index = 0;
    for(auto s0_tuning : parent_tuning->getSubsets0()) {
        auto s0_element_component = _subsets0[index];
        s0_element_component->setTuning(s0_tuning);
        const shared_ptr<EulerGenusViewModel> vm_s0 = egm->_getViewModel(s0_tuning->getDAWKey());
        s0_element_component->setSingleClickCompletionBlock([this,vm_s0]() {singleClickDAWKey(vm_s0->dawKey);} );
        s0_element_component->setControlClickCompletionBlock([this,vm_s0]() {controlClickDAWKey(vm_s0->dawDrillKey);} );
        s0_element_component->setCommandClickCompletionBlock([this,vm_s0]() {commandClickDAWKey(vm_s0->dawBackKey);} );
        index++;
    }
    index = 0;
    for(auto s1_tuning : parent_tuning->getSubsets1()) {
        auto s1_element_component = _subsets1[index];
        s1_element_component->setTuning(s1_tuning);
        const shared_ptr<EulerGenusViewModel> vm_s1 = egm->_getViewModel(s1_tuning->getDAWKey());
        s1_element_component->setSingleClickCompletionBlock([this,vm_s1]() {singleClickDAWKey(vm_s1->dawKey);} );
        s1_element_component->setControlClickCompletionBlock([this,vm_s1]() {controlClickDAWKey(vm_s1->dawDrillKey);} );
        s1_element_component->setCommandClickCompletionBlock([this,vm_s1]() {commandClickDAWKey(vm_s1->dawBackKey);} );
        index++;
    }

    resized();
    repaint();
}

#pragma mark - ActionListener

void EulerGenusComponentV2::actionListenerCallback(const String& message) {
    if (message == DesignsModel::getEulerGenusTuningChangedActionMessage()) {
        _tuningChangedUpdateUI();
    } else if (message == AppTuningModel::getAppTuningModelChangedMessage()) {
        // CPSElementComponentV2 are listening to this message and will repaint themselves
    }
}

#pragma mark - Event handling

// click...element components call with their tuning's daw key

// "select"

void EulerGenusComponentV2::singleClickDAWKey(DAWKey daw_key) {
    const auto egm = _processor.getEulerGenusModel();
    egm->uiSelectDAWKey(daw_key);
}

// "drill"

void EulerGenusComponentV2::controlClickDAWKey(DAWKey daw_key) {
    const auto egm = _processor.getEulerGenusModel();
    egm->uiSelectDAWKey(daw_key);
}

// "back button"

void EulerGenusComponentV2::commandClickDAWKey(DAWKey daw_key) {
    const auto egm = _processor.getEulerGenusModel();
    egm->uiSelectDAWKey(daw_key);
}

#pragma mark - key listener

bool EulerGenusComponentV2::keyPressed(const KeyPress& key) {
    auto const model = _processor.getEulerGenusModel();
    if (key.isKeyCode(KeyPress::leftKey)) {
        // "select"
        model->uiLeftArrowKeyPressed();
        return true;
    } else if (key.isKeyCode(KeyPress::rightKey)) {
        // "select"
        model->uiRightArrowKeyPressed();
        return true;
    } else if (key.isKeyCode(KeyPress::upKey)) {
        // "select"
        model->uiUpArrowKeyPressed();
        return true;
    } else if (key.isKeyCode(KeyPress::downKey)) {
        // "select"
        model->uiDownArrowKeyPressed();
        return true;
    } else if (key == KeyPress(KeyPress::returnKey, ModifierKeys::ctrlModifier, 0) ) {
        // "drill"
        model->uiControlReturnPressed();
        return true;
    } else if (key == KeyPress(KeyPress::returnKey, ModifierKeys::commandModifier, 0) ) {
        // "back button"
        model->uiCommandReturnPressed();
        return true;
    }

    return false;
}

