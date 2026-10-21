/*
  ==============================================================================

    WilsonicMenuComponent.h
    Created: 7 Mar 2021 4:44:01pm
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#pragma once

#include <JuceHeader.h>
#include "BubbleDrawable.h"
#include "DeltaComboBox.h"
#include "Tuning_Include.h"
#include "WilsonicComponentBase.h"
#include "WilsonicMenuComponentMessageBus.h"

class WilsonicMenuComponent
: public WilsonicComponentBase
, public ActionBroadcaster
, private ActionListener
, private Button::Listener
, private WilsonicMenuComponentMessageListener
{
public:
    // static favorites action messages
    static const String getToggleFavoritesMessage() {return "toggleFavorites";}

public:
    // lifecycle
    WilsonicMenuComponent (WilsonicProcessor&);
    ~WilsonicMenuComponent() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (WilsonicMenuComponent)

public:
    // drawing
    void paint (Graphics&) override;
    void resized() override;

    // MessageListener
    void handleMessage(const String& message) override;

private:
    // private properties
    unique_ptr<DeltaComboBox>  _scaleDesignComboBox;
    unique_ptr<TextButton> _previousFavoritesButton;
    shared_ptr<DrawableButton> _favoritesButton;
    unique_ptr<TextButton> _nextFavoritesButton;
    Label _statusLabel;
    const String _linkText = "Documentation";
    shared_ptr<ImageButton> _mtsEspStatusIndicator;
    Image _redWarningImage;
    Image _yellowWarningImage;
    Image _greenImage;
    PopupMenu _menu {};
    unique_ptr<FileChooser> _asclFileChooser; // Export for Ableton Live (.ascl)

    // private methods
    static void _resetMtsEspModalCallback(int modalResult, WilsonicMenuComponent* t);
    void _showResetMtsEspAlert();
    void _mtsEspHelper();
    void _popupMenuHelper();
    void _exportAscl(); // desktop only: save the current tuning as an Ableton Live .ascl file
    void actionListenerCallback(const String& message) override;
    void buttonClicked(Button*) override;
};
