/*
 ==============================================================================
 
 WilsonicMenuComponent.cpp
 Created: 7 Mar 2021 4:44:01pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include <JuceHeader.h>
#include "AbletonAscl.h"
#include "AppExperiments.h"
#include "AppVersion.h"
#include "DesignsModel.h"
#include "FavoritesModelV2.h"
#include "WilsonicEditor.h"
#include "WilsonicMenuComponent.h"
#include "WilsonicProcessor.h"

#pragma mark - lifecycle

WilsonicMenuComponent::WilsonicMenuComponent(WilsonicProcessor& processor)
: WilsonicComponentBase(processor)
, _redWarningImage(ImageCache::getFromMemory(BinaryData::warningred96_png, BinaryData::warningred96_pngSize))
, _yellowWarningImage(ImageCache::getFromMemory(BinaryData::warningyellow96_png, BinaryData::warningyellow96_pngSize))
, _greenImage(ImageCache::getFromMemory(BinaryData::successgreen96_png, BinaryData::successgreen96_pngSize))
{
    // scale design combo box
    auto designs = _processor.getDesignsModel();
    _scaleDesignComboBox = make_unique<DeltaComboBox>(_processor, true);
    _scaleDesignComboBox->addItemList(designs->getDesignsNames(), 1);
    _scaleDesignComboBox->setToolTip("Wilsonic Scale Designs");

    // set new preset
    auto onChange = [this]()
    {
        auto const selectedItemIndex = static_cast<unsigned long>(_scaleDesignComboBox->getSelectedItemIndex());
        _processor.getDesignsModel()->uiSetDesign(selectedItemIndex);
    };
    _scaleDesignComboBox->setOnChange(onChange);
    
    // order is important...setting the attachment calls the callback to properly init
    _scaleDesignComboBox->setComboBoxAttachment(_processor.getApvts(), DesignsModel::getDesignsParameterID().getParamID());
    
    // Scale Design Combo Box
    addAndMakeVisible(*_scaleDesignComboBox);


    // previous Favorite
    _previousFavoritesButton = make_unique<TextButton>("<");
    _previousFavoritesButton->setTooltip("Go to previous Favorite");
    _previousFavoritesButton->setToggleState(false, dontSendNotification);
    _previousFavoritesButton->addListener(this);
    addAndMakeVisible(*_previousFavoritesButton);

    // favorites menu button...toggles Favorites table
    DrawablePath normal, over;
    Path p;
    p.addStar({}, 5, 20.f, 50.f, 0.f);
    normal.setPath(p);
    normal.setFill(Colours::lightblue);
    normal.setStrokeFill(Colours::black);
    normal.setStrokeThickness(4.f);
    over.setPath(p);
    over.setFill(Colours::blue);
    over.setStrokeFill(Colours::black);
    over.setStrokeThickness(4.f);
    _favoritesButton = make_shared<DrawableButton>("Favorites", DrawableButton::ImageFitted);
    _favoritesButton->setImages(&normal, &over, nullptr);
    _favoritesButton->setClickingTogglesState(true);
    _favoritesButton->setTooltip("Manage your Favorites:\n * Add current tuning as Favorite\n * Add current tuning to your Scala User Library");
    _favoritesButton->setToggleState(false, dontSendNotification);
    _favoritesButton->onClick = [this] {sendActionMessage(getToggleFavoritesMessage());};
    addAndMakeVisible(*_favoritesButton);

    // next Favorite
    _nextFavoritesButton = make_unique<TextButton>(">");
    _nextFavoritesButton->setTooltip("Go to next Favorite");
    _nextFavoritesButton->setToggleState(false, dontSendNotification);
    _nextFavoritesButton->addListener(this);
    addAndMakeVisible(*_nextFavoritesButton);

    // status label
    addAndMakeVisible(_statusLabel);
    _statusLabel.setText(WilsonicMenuComponentMessageBus::getInstance().getMessage(), dontSendNotification);
    _statusLabel.setJustificationType(Justification::Flags::right);
    _statusLabel.setTooltip(WilsonicMenuComponentMessageBus::getInstance().getMessages());    
    auto const labelFontSize = WilsonicAppSkin::messageBusFontSize;
    auto const font = Font::plain;
    _statusLabel.setFont(Font(FontOptions(labelFontSize, font)));
        
    // MTS-ESP status indicator
    _mtsEspStatusIndicator = make_shared<ImageButton>("MTSESPINDICATOR");
    _mtsEspStatusIndicator->onClick = [&]
    {
        _popupMenuHelper();
    };
    _mtsEspHelper();  // updates indicator based on status
    addAndMakeVisible(*_mtsEspStatusIndicator);
    
    // Register as the listener to the [only] WilsonicMenuComponentMessageBus
    WilsonicMenuComponentMessageBus::getInstance().setMenuMessageListener(this);

    // listeners
    _processor.addActionListener(this);
}

WilsonicMenuComponent::~WilsonicMenuComponent()
{
    _processor.removeActionListener(this);
    WilsonicMenuComponentMessageBus::getInstance().setMenuMessageListener(nullptr);
}

#pragma mark - drawing

void WilsonicMenuComponent::paint(Graphics& g)
{
    // BG
    g.fillAll(_processor.getAppSkin().getBgColor());
    
    if(AppExperiments::showDebugBoundingBox)
    {
        // DEBUG
        g.setColour(Colours::lightyellow);
        g.drawRect(getLocalBounds(), 2);
        g.drawRect(_statusLabel.getBounds(), 2);
        
        // counter
        g.drawText(String(_debug_paint_counter++), getLocalBounds(), Justification::topRight);
    }
}

void WilsonicMenuComponent::resized()
{
    auto const margin = static_cast<int>(WilsonicAppSkin::tuningComponentInteriorMargin);
    auto const menu_width = 350;
    auto area = getLocalBounds();
    auto const button_width = jlimit(static_cast<int>(WilsonicAppSkin::minHitPointSize),
                                     static_cast<int>(area.getHeight() - 5),
                                     static_cast<int>(area.getHeight()));
    auto const min_hitpoint = static_cast<int>(WilsonicAppSkin::minHitPointSize);

    // menu area
    auto menu_area = area.removeFromLeft(menu_width);
    _scaleDesignComboBox->setBounds(menu_area);

#if JUCE_IOS || JUCE_ANDROID
    // Mobile needs it's own menu icon
    //
#else
    // mts-esp status indicator
    auto mts_esp_area = area.removeFromRight(button_width);
    mts_esp_area.reduce(5, 5);
    _mtsEspStatusIndicator->setBounds(mts_esp_area);
    
    // margin (if you put something to the left of the mts indicator
    area.removeFromRight(margin);
#endif

    // don't modify the area as you layout the favorites
    auto const favorites_area = getLocalBounds().toNearestInt();

    // previous favorite
    _previousFavoritesButton->setBounds(static_cast<int>(favorites_area.getX() + 0.5f * favorites_area.getWidth() - 2.5f * min_hitpoint),
                                        static_cast<int>(favorites_area.getY() + 0.5f * (favorites_area.getHeight() - min_hitpoint)),
                                        min_hitpoint,
                                        min_hitpoint);

    // Favorites button, centered
    _favoritesButton->setBounds(static_cast<int>(favorites_area.getX() + 0.5f * favorites_area.getWidth() - 0.5f * button_width),
                                favorites_area.getY(),
                                button_width,
                                button_width);

    // next favorite
    _nextFavoritesButton->setBounds(static_cast<int>(favorites_area.getX() + 0.5f * favorites_area.getWidth() + 1.5f * min_hitpoint),
                                    static_cast<int>(favorites_area.getY() + 0.5f * (favorites_area.getHeight() - min_hitpoint)),
                                    min_hitpoint,
                                    min_hitpoint);
    
    // mts status icon
    _mtsEspHelper();
    
    // status label area
    auto const x = _nextFavoritesButton->getX() + _nextFavoritesButton->getWidth() + margin;
    auto sla = Rectangle<int>(x,
                              favorites_area.getY(),
#if JUCE_IOS || JUCE_ANDROID
                              area.getX() - margin - x,
#else
                              mts_esp_area.getX() - margin - x,
#endif
                              favorites_area.getHeight());
    _statusLabel.setBounds(sla);
}

#pragma mark - private methods

void WilsonicMenuComponent::handleMessage(const String& message)
{
    // Update the status label with the received message
    _statusLabel.setText(message, dontSendNotification);
    _statusLabel.setTooltip(WilsonicMenuComponentMessageBus::getInstance().getMessages());
    resized();
}

void WilsonicMenuComponent::_mtsEspHelper()
{
#if JUCE_IOS || JUCE_ANDROID
    // NOP
#else
    if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::Registered)
    {
        _mtsEspStatusIndicator->setImages(false, true, true,
                                           _greenImage, 1.f, {},
                                           _greenImage, 1.f, {},
                                           _greenImage, 1.f, {});
    }
    else if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::Failed)
    {
        _mtsEspStatusIndicator->setImages(false, true, true,
                                           _redWarningImage, 1.f, {},
                                           _redWarningImage, 1.f, {},
                                           _redWarningImage, 1.f, {});
        DBG("MTS-ESP: RED");
    }
    else if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::NeedToReregister)
    {
        _mtsEspStatusIndicator->setImages(false, true, true,
                                           _yellowWarningImage, 1.f, {},
                                           _yellowWarningImage, 1.f, {},
                                           _yellowWarningImage, 1.f, {});
        DBG("MTS-ESP: YELLOW");
    }
    else
    {
        //NotRegistered, // at start up we're not yet registered
        //NotSupported // ios, android, etc
        _mtsEspStatusIndicator->setImages(false, true, true,
                                           _redWarningImage, 1.f, {},
                                           _redWarningImage, 1.f, {},
                                           _redWarningImage, 1.f, {});
        DBG("MTS-ESP: RED");
    }
#endif
}

void WilsonicMenuComponent::_popupMenuHelper()
{
    _menu.clear();
    int const disabledID = -1;
    int const registerMtsEspID = 1;
    int const documentationID = 2;
    int const outOfBandMuteID = 3;
    int const outOfBandPlayID = 4;
    int const exportAsclID = 5;

    // version
    String appName = AppVersion::getAppName();
    String version = appName + " " + AppVersion::getAppVersion();
    _menu.addItem(disabledID, version, false);

    // by Marcus Satellite
    _menu.addItem(disabledID, "(c) 2023 Marcus Satellite", false);

    // --
    _menu.addSeparator();

    // mts status indicator
    // mts status desc (not selectable)
    if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::Registered)
    {
        DBG("MTS-ESP: GREEN");
        _menu.addItem(disabledID, "MTS-ESP Status", false, false, _greenImage);
        auto num_clients = _processor.getMtsEspNumberOfClients();
        _menu.addItem(disabledID, appName + " is registered as the MTS-ESP Source", false, false);
        _menu.addItem(disabledID, "Connected to " + String(num_clients) + " clients.", false, false);
    }
    else if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::Failed)
    {
        DBG("MTS-ESP: RED");
        _menu.addItem(disabledID, "MTS-ESP Status", false, false, _redWarningImage);
        _menu.addItem(disabledID, appName + " is NOT registered as the MTS-ESP Source", false, false);
        _menu.addItem(disabledID, "because you already have a Source,", false, false);
        _menu.addItem(disabledID, "or the MTS-ESP library installation was unsuccessful.", false, false);
        _menu.addItem(registerMtsEspID, "Register Wilsonic as MTS-ESP Source", true, false);
    }
    else if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::NeedToReregister)
    {
        DBG("MTS-ESP: YELLOW");
        _menu.addItem(disabledID, "MTS-ESP Status", false, false, _yellowWarningImage);
        _menu.addItem(disabledID, appName + " is NOT registered as the MTS-ESP Source", false, false);
        _menu.addItem(disabledID, "This is likely because it did not shut down properly.", false, false);
        _menu.addItem(registerMtsEspID, "Register " + appName + " as MTS-ESP Source", true, false);
    }
    else
    {
        // TODO: Why?  why not handle every case
        jassertfalse;
    }

    _menu.addSeparator();

    // Out-of-range keys: per-machine preference (WilsonicProcessor+Properties.cpp),
    // applied by the output stage (TuningOutput.h) to MTS-ESP, the synth and the keyboard
    {
        auto const policy = _processor.getAppTuningModel()->getOutOfBandPolicy();
        PopupMenu outOfBandMenu;
        outOfBandMenu.addItem(outOfBandMuteID, "Mute", true, policy == OutOfBandPolicy::Filter);
        outOfBandMenu.addItem(outOfBandPlayID, "Play anyway", true, policy == OutOfBandPolicy::PassThrough);
        _menu.addSubMenu("Out-of-range keys (below 4 Hz or above 21 kHz)", outOfBandMenu);
    }

    _menu.addSeparator();

    // --
    // Simple Synth (check)
    // Synth One (check)
    // --
    // Animations (let's do later)
    // --

    // Documentation (url button)
    _menu.addItem(documentationID, "Documentation", true, false);
    _menu.addItem(disabledID, "(opens in your browser)", false, false);

#if ! (JUCE_IOS || JUCE_ANDROID)
    // Export the current tuning as an Ableton Live 12 tuning file (no MTS-ESP needed in Live)
    _menu.addSeparator();
    _menu.addItem(exportAsclID, "Export for Ableton Live (.ascl)" + String(CharPointer_UTF8("\xe2\x80\xa6")), true, false);
    _menu.addItem(disabledID, "(snapshot of the current tuning for a Live Set without MTS-ESP)", false, false);
#endif

    //
    auto callback = [&](int selectedID)
    {
        if(selectedID == registerMtsEspID)
        {
            if(_processor.getMtsEspStatus() == WilsonicProcessor::MTS_ESP_Status::NeedToReregister)
            {
                _showResetMtsEspAlert();
            }
        }
        else if(selectedID == exportAsclID)
        {
            _exportAscl();
        }
        else if(selectedID == documentationID)
        {
            URL url(AppVersion::getDocumentationURL());
            bool success = url.launchInDefaultBrowser();
            if(!success)
            {
                DBG("error opening documentation url");
            }
        }
        else if(selectedID == outOfBandMuteID || selectedID == outOfBandPlayID)
        {
            auto const policy = (selectedID == outOfBandMuteID) ? OutOfBandPolicy::Filter : OutOfBandPolicy::PassThrough;
            _processor.getAppTuningModel()->setOutOfBandPolicy(policy);
        }
        else if(selectedID == disabledID)
        {
            // NOP
        }
        else if(selectedID == 0)
        {
            // Nothing was selected;
        }
        else
        {
            jassertfalse;
        }
    };

    _menu.showMenuAsync(PopupMenu::Options{}.withTargetComponent(*_mtsEspStatusIndicator), callback);
}

#pragma mark - Export for Ableton Live (.ascl)

// Writes the current tuning as a Live 12 .ascl file: every MIDI key 0-127 at the
// frequency Wilsonic's tuning table gives it, with Wilsonic degree names in the
// piano roll. The file is a snapshot; MTS-ESP behaviour is untouched.
void WilsonicMenuComponent::_exportAscl()
{
#if JUCE_IOS || JUCE_ANDROID
    return;
#else
    auto tuning = _processor.getAppTuningModel()->getTuning();
    if(tuning == nullptr)
    {
        jassertfalse;
        return;
    }

    // design name from the Scale Design combo box; the tuning's own name as fallback
    auto const designNames = _processor.getDesignsModel()->getDesignsNames();
    auto const designIndex = _scaleDesignComboBox->getSelectedItemIndex();
    auto const designName = (designIndex >= 0 && designIndex < designNames.size())
        ? designNames[designIndex].toStdString()
        : tuning->getTuningName();
    auto const defaultName = AbletonAscl::defaultFileName(designName, tuning->getParameterDescription());
    auto const startFile = File::getSpecialLocation(File::userDocumentsDirectory).getChildFile(String(defaultName));
    _asclFileChooser = make_unique<FileChooser>("Export for Ableton Live (.ascl)", startFile, "*.ascl");
    auto const flags = FileBrowserComponent::saveMode
                     | FileBrowserComponent::canSelectFiles
                     | FileBrowserComponent::warnAboutOverwriting;
    _asclFileChooser->launchAsync(flags, [tuning, designName](const FileChooser& chooser)
    {
        auto file = chooser.getResult();
        if(file == File())
        {
            return; // cancelled
        }
        if(! file.hasFileExtension("ascl"))
        {
            file = file.withFileExtension("ascl");
        }

        AsclOptions options;
        options.fileName = file.getFileName().toStdString();
        options.exportDate = Time::getCurrentTime().toISO8601(false).substring(0, 10).toStdString();
        options.designName = designName;
        options.appVersion = AppVersion::getAppVersion();
        options.linkUrl = AppVersion::getProjectURL().toStdString();
        options.includeScaleDirectives = false; // SCALE directives are undocumented and untested in Live

        vector<string> warnings;
        auto const text = AbletonAscl::makeAscl(*tuning, options, warnings);
        String details;
        for(auto const& w : warnings)
        {
            details += String(CharPointer_UTF8("\xe2\x80\xa2 ")) + String::fromUTF8(w.c_str()) + "\n";
        }

        if(text.empty())
        {
            WilsonicMenuComponentMessageBus::getInstance().broadcastMessage("Ableton export failed");
            NativeMessageBox::showAsync(MessageBoxOptions()
                                        .withIconType(MessageBoxIconType::WarningIcon)
                                        .withTitle("Export for Ableton Live failed")
                                        .withMessage(details)
                                        .withButton("OK"), nullptr);
            return;
        }

        // UTF-8, no BOM, LF line endings (text already uses LF; pass it through unchanged)
        auto const ok = file.replaceWithText(String::fromUTF8(text.c_str()), false, false, "\n");
        if(! ok)
        {
            WilsonicMenuComponentMessageBus::getInstance().broadcastMessage("Ableton export failed: could not write " + file.getFileName());
            NativeMessageBox::showAsync(MessageBoxOptions()
                                        .withIconType(MessageBoxIconType::WarningIcon)
                                        .withTitle("Export for Ableton Live failed")
                                        .withMessage("Could not write " + file.getFullPathName())
                                        .withButton("OK"), nullptr);
            return;
        }

        WilsonicMenuComponentMessageBus::getInstance().broadcastMessage("Exported " + file.getFileName() + (warnings.empty() ? "" : " with warnings"));
        if(! warnings.empty())
        {
            NativeMessageBox::showAsync(MessageBoxOptions()
                                        .withIconType(MessageBoxIconType::InfoIcon)
                                        .withTitle("Exported " + file.getFileName() + " with warnings")
                                        .withMessage(details)
                                        .withButton("OK"), nullptr);
        }
    });
#endif
}

#pragma mark - Alert

void WilsonicMenuComponent::_showResetMtsEspAlert()
{
    AlertWindow::showOkCancelBox
    (MessageBoxIconType::WarningIcon,
     "Reset MTS-ESP?",
     "This will make " + AppVersion::getAppName() + " the MTS-ESP Source",
     "Reset",
     "Cancel",
     this,
     ModalCallbackFunction::forComponent(_resetMtsEspModalCallback, this)
     );
}

void WilsonicMenuComponent::_resetMtsEspModalCallback(int modalResult, WilsonicMenuComponent* t)
{
    if(t == nullptr)
    {
        return;
    }
    
    if(modalResult == 1)
    {
        t->_processor.resetMtsEsp();
    }
    
    // resize/repaint no matter what
    t->resized();
}


#pragma mark - ActionListener

void WilsonicMenuComponent::actionListenerCallback(const String& message)
{
    if(message == WilsonicProcessor::getMtsEspStatusDidChangeMessage())
    {
        _mtsEspHelper();
        resized();
    }
}

#pragma mark - Button handler

void WilsonicMenuComponent::buttonClicked(Button* button)
{
    // "<" previous
    auto pfb = dynamic_cast<Button*>(_previousFavoritesButton.get());
    if(pfb == button)
    {
        _processor.getFavoritesModelV2()->uiRecallPreviousFavorite();
        return;
    }

    // ">" next
    auto nfb = dynamic_cast<Button*>(_nextFavoritesButton.get());
    if(nfb == button)
    {
        _processor.getFavoritesModelV2()->uiRecallNextFavorite();
        return;
    }

    //
    jassertfalse;
}
