/*
  ==============================================================================

    BrunLevelComponent.cpp
    Created: 1 Apr 2021 8:29:50pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include <JuceHeader.h>
#include "Brun2Model.h"
#include "BrunLevelComponent.h"

BrunLevelComponent::BrunLevelComponent(WilsonicProcessor& processor, function<unsigned long()> getSelectedIndex, function<void(float)> setLevel01)
: WilsonicComponentBase(processor)
, _getSelectedIndex(getSelectedIndex)
, _setLevel01(setLevel01)
{

}

BrunLevelComponent::~BrunLevelComponent() {
}

void BrunLevelComponent::paint(Graphics& g) {
    // BG
    g.fillAll(_processor.getAppSkin().getBgColor());

    // DEBUG
    if (AppExperiments::showDebugBoundingBox) {
        // DEBUG
        g.setColour(Colours::green);
        g.drawRect(getLocalBounds(), 2);
    }

    // area, fill bg
    auto const area = getLocalBounds();
    g.setColour(Colours::mediumpurple);
    g.drawRect(area, 1);

    // get the array of level labels...i.e., 1/1, 1/2, ..., 1/5, 2/9, 3/13, etc.
    auto const la = _processor.getBrun2Model()->uiGetLabelArray();
    auto const n = la.size();
    jassert(n > 0);

    // create vertical cells for each level label
    auto const x0 = 0;
    auto const x1 = area.getWidth();
    auto const ch = getHeight() / static_cast<float>(n);
    auto const level = _getSelectedIndex();
    for (unsigned long i = 0; i < n; i++) {
        // this cell
        auto const y0 = i * ch;
        auto const y1 = (i + 1) * ch;
        auto const r = Rectangle<int>::leftTopRightBottom(x0, static_cast<int>(y0), x1, static_cast<int>(y1));

        // outline
        auto outlineColor = (i == level) ? Colours::white : Colours::grey;
        g.setColour(outlineColor);
        g.drawRect(r);

        // level label
        auto l = la[i];
        auto text = String(l);
        if (text.isNotEmpty()) {
            auto fontColor = _processor.getAppSkin().getSelectedComponentColor();
            if (i != level) {
                fontColor = fontColor.darker().darker();
            }
            g.setColour(fontColor);
            auto minFontHeight = (i == level) ? 36.f : 18.f;
            auto fontHeight = jmin(minFontHeight, ch * 0.9f);
            auto font = Font(FontOptions(fontHeight)).withHorizontalScale(0.8f);
            if (i == level) font = font.boldened();
            g.setFont(font);
            g.drawText(text, r, Justification::centred, false);
        }
    }
}

void BrunLevelComponent::resized() {
    // no child components
}

#pragma mark - MouseListener

void BrunLevelComponent::mouseDown(const MouseEvent& event) {
    _mouseHelper(event);
}

void BrunLevelComponent::mouseUp(const MouseEvent& event) {
    _mouseHelper(event);
}

void BrunLevelComponent::mouseDrag(const MouseEvent& event) {
    _mouseHelper(event);
}

void BrunLevelComponent::mouseEnter(const MouseEvent& /* event */) {
//    _mouseHelper(event);
}

void BrunLevelComponent::mouseExit(const MouseEvent& /*event*/) {
//    _mouseHelper(event);
}

void BrunLevelComponent::mouseMove(const MouseEvent& /*event*/) {
//    _mouseHelper(event);
}

void BrunLevelComponent::_mouseHelper(const MouseEvent& event) {
    auto const y = float(event.getPosition().getY());
    auto const y01 = y / float(getHeight());
    _setLevel01(y01);

    // must always repaint because some params are not automatable in the daw and don't send notifications
    repaint();
}
