/**
 * @file SnapshotMode.cpp
 * @brief Offscreen screenshot mode for the Wilsonic standalone app.
 */

#include "SnapshotMode.h"
#include "DesignsModel.h"
#include "WilsonicEditor.h"
#include "WilsonicProcessor.h"
#include <iostream>

std::unique_ptr<SnapshotMode> SnapshotMode::__instance = nullptr;
bool SnapshotMode::__active = false;

#pragma mark - static entry points

void SnapshotMode::startIfRequested(WilsonicProcessor& processor, WilsonicEditor& editor) {
    // Only one run per process.
    if (__instance != nullptr) {
        return;
    }

    // Only the standalone app has a JUCEApplication and a command line.
    if (JUCEApplicationBase::getInstance() == nullptr) {
        return;
    }
    if (processor.wrapperType != AudioProcessor::wrapperType_Standalone) {
        return;
    }

    auto args = JUCEApplicationBase::getCommandLineParameterArray();
    auto const flagIndex = args.indexOf("--snapshot");
    if (flagIndex < 0) {
        return; // normal launch: snapshot mode stays inert
    }

    if (flagIndex + 2 >= args.size()) {
        std::cerr << "SnapshotMode: usage: Wilsonic --snapshot <manifest.json> <output-dir>" << std::endl;
        JUCEApplicationBase::getInstance()->setApplicationReturnValue(2);
        JUCEApplicationBase::quit();
        return;
    }

    auto const cwd = File::getCurrentWorkingDirectory();
    auto const manifestFile = cwd.getChildFile(args[flagIndex + 1]);
    auto const outputDirectory = cwd.getChildFile(args[flagIndex + 2]);
    __active = true;
    __instance.reset(new SnapshotMode(processor, editor, manifestFile, outputDirectory));
}

bool SnapshotMode::isActive() {
    // Stays true through app teardown so the editor destructor can tell a
    // snapshot run forced the window bounds.
    return __active;
}

#pragma mark - lifecycle

SnapshotMode::SnapshotMode(WilsonicProcessor& processor, WilsonicEditor& editor, const File& manifestFile, const File& outputDirectory)
: _processor(processor)
, _editor(editor)
, _outputDirectory(outputDirectory) {
    auto quitWithError = [](const String& message) {
        std::cerr << "SnapshotMode: " << message << std::endl;
        JUCEApplicationBase::getInstance()->setApplicationReturnValue(2);
        JUCEApplicationBase::quit();
    };

    if (!manifestFile.existsAsFile()) {
        quitWithError("manifest not found: " + manifestFile.getFullPathName());
        return;
    }

    auto const manifest = JSON::parse(manifestFile.loadFileAsString());
    if (manifest.isVoid()) {
        quitWithError("manifest is not valid JSON: " + manifestFile.getFullPathName());
        return;
    }

    _defaults = manifest.getProperty("defaults", var());
    auto const entries = manifest.getProperty("entries", var());
    if (entries.getArray() == nullptr || entries.getArray()->isEmpty()) {
        quitWithError("manifest has no \"entries\" array: " + manifestFile.getFullPathName());
        return;
    }
    _entries = *entries.getArray();

    auto const dirResult = _outputDirectory.createDirectory();
    if (dirResult.failed()) {
        quitWithError("cannot create output dir: " + _outputDirectory.getFullPathName());
        return;
    }

    std::cout << "SnapshotMode: " << _entries.size() << " entries -> " << _outputDirectory.getFullPathName() << std::endl;

    // Drive the run from the message loop so layout, ActionBroadcaster
    // messages, and repaints settle between applying params and capturing.
    startTimer(__timerIntervalMs);
}

SnapshotMode::~SnapshotMode() {
    stopTimer();
}

#pragma mark - state machine

void SnapshotMode::timerCallback() {
    if (_entryIndex >= _entries.size()) {
        _finish();
        return;
    }

    auto const entry = _entries[_entryIndex];

    if (!_entryApplied) {
        if (_applyEntry(entry)) {
            auto const settleMs = static_cast<int>(entry.getProperty("settleMs", _defaults.getProperty("settleMs", 1500)));
            _settleTicksRemaining = jmax(1, settleMs / __timerIntervalMs);
            _entryApplied = true;
        } else {
            _failureCount++;
            _entryIndex++;
        }
        return;
    }

    if (_settleTicksRemaining > 0) {
        _settleTicksRemaining--;
        return;
    }

    if (!_captureEntry(entry)) {
        _failureCount++;
    }
    _entryApplied = false;
    _entryIndex++;
}

bool SnapshotMode::_applyEntry(const var& entry) {
    auto const output = entry.getProperty("output", var()).toString();
    if (output.isEmpty()) {
        _logEntryError("entry has no \"output\" filename");
        return false;
    }
    std::cout << "SnapshotMode: [" << (_entryIndex + 1) << "/" << _entries.size() << "] " << output << std::endl;

    auto apvts = _processor.getApvts();
    jassert(apvts != nullptr);

    // Select the scale design by its "DESIGNS" choice name, e.g. "Equal
    // Temperament". This triggers the same navigation as the design menu.
    auto const designName = entry.getProperty("design", var()).toString();
    if (designName.isNotEmpty()) {
        auto* designParam = apvts->getParameter(DesignsModel::getDesignsParameterID().getParamID());
        jassert(designParam != nullptr);
        auto const designIndex = designParam->getAllValueStrings().indexOf(designName);
        if (designIndex < 0) {
            _logEntryError("unknown design \"" + designName + "\"; valid names: " + designParam->getAllValueStrings().joinIntoString(", "));
            return false;
        }
        designParam->setValueNotifyingHost(designParam->convertTo0to1(static_cast<float>(designIndex)));
    }

    // Apply APVTS parameter values. Keys are parameter IDs (CPSCALE, CPSA,
    // EQUALTEMPERAMENTNPO, APPTUNINGNOTENUMBERMIDDLEC, ...). Strings go
    // through the parameter's own text conversion, so choice parameters
    // accept choice names ("4_2") and numbers are denormalized values.
    if (auto* params = entry.getProperty("params", var()).getDynamicObject()) {
        for (auto& param : params->getProperties()) {
            auto const paramID = param.name.toString();
            auto* p = apvts->getParameter(paramID);
            if (p == nullptr) {
                _logEntryError("unknown parameter ID \"" + paramID + "\"");
                return false;
            }
            if (param.value.isString()) {
                // Catch misspelled choice names, which getValueForText would
                // silently map to index 0.
                auto const choices = p->getAllValueStrings();
                if (!choices.isEmpty() && choices.indexOf(param.value.toString()) < 0) {
                    _logEntryError("unknown value \"" + param.value.toString() + "\" for \"" + paramID + "\"; valid values: " + choices.joinIntoString(", "));
                    return false;
                }
                p->setValueNotifyingHost(p->getValueForText(param.value.toString()));
            } else {
                p->setValueNotifyingHost(p->convertTo0to1(static_cast<float>(static_cast<double>(param.value))));
            }
        }
    }

    // Force a fixed logical size on the whole window so captures are
    // reproducible. Existing manual captures are 2048px wide at 2x scale.
    auto const width = static_cast<int>(entry.getProperty("width", _defaults.getProperty("width", 1024)));
    auto const height = static_cast<int>(entry.getProperty("height", _defaults.getProperty("height", 709)));
    if (auto* topLevel = _editor.getTopLevelComponent()) {
        topLevel->setSize(width, height);
    }

    return true;
}

bool SnapshotMode::_captureEntry(const var& entry) {
    auto const output = entry.getProperty("output", var()).toString();
    auto const scale = static_cast<float>(static_cast<double>(entry.getProperty("scale", _defaults.getProperty("scale", 2.0))));

    auto* topLevel = _editor.getTopLevelComponent();
    jassert(topLevel != nullptr);
    auto const image = topLevel->createComponentSnapshot(topLevel->getLocalBounds(), true, scale);
    if (image.isNull() || image.getWidth() == 0) {
        _logEntryError("snapshot render failed for " + output);
        return false;
    }

    auto const outputFile = _outputDirectory.getChildFile(output);
    outputFile.deleteFile();
    FileOutputStream stream(outputFile);
    if (stream.failedToOpen()) {
        _logEntryError("cannot write " + outputFile.getFullPathName());
        return false;
    }

    PNGImageFormat pngFormat;
    if (!pngFormat.writeImageToStream(image, stream)) {
        _logEntryError("PNG encode failed for " + outputFile.getFullPathName());
        return false;
    }
    stream.flush();

    std::cout << "SnapshotMode: wrote " << outputFile.getFullPathName()
              << " (" << image.getWidth() << "x" << image.getHeight() << ")" << std::endl;
    return true;
}

void SnapshotMode::_logEntryError(const String& message) {
    std::cerr << "SnapshotMode: entry " << (_entryIndex + 1) << ": " << message << std::endl;
}

void SnapshotMode::_finish() {
    stopTimer();
    auto const failures = _failureCount;
    auto const total = _entries.size();
    std::cout << "SnapshotMode: done, " << (total - failures) << "/" << total << " succeeded" << std::endl;
    JUCEApplicationBase::getInstance()->setApplicationReturnValue(failures > 0 ? 1 : 0);
    // Destroy this instance from the message loop (not from inside its own
    // timer callback) before quitting, so JUCE's shutdown leak detector
    // doesn't see it outliving the application.
    MessageManager::callAsync([] {
        __instance.reset();
        JUCEApplicationBase::quit();
    });
}
