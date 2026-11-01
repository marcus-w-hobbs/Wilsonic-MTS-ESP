/**
 * @file SnapshotMode.h
 * @brief Offscreen screenshot mode for the Wilsonic standalone app.
 *
 * Launching the standalone as
 *
 *     Wilsonic --snapshot <manifest.json> <output-dir>
 *
 * renders one PNG per manifest entry and exits (nonzero if any entry failed).
 * Each entry names an output file, a scale design (a "DESIGNS" choice name),
 * and APVTS parameter values to apply — the same parameter addressing the
 * research harness records in its "RECREATE IN WILSONIC" comment blocks.
 *
 * Manifest format (docs/manual/screenshots.json):
 *
 *     {
 *       "defaults": { "width": 1024, "height": 709, "scale": 2.0, "settleMs": 1500 },
 *       "entries": [
 *         { "output": "equal-temperament.png",
 *           "design": "Equal Temperament",
 *           "params": { "EQUALTEMPERAMENTNPO": 13, "EQUALTEMPERAMENTPERIOD": 3.0 } }
 *       ]
 *     }
 *
 * This lives entirely in the standalone/app layer: normal launches (no
 * --snapshot flag) and plugin builds are unaffected.
 */

#pragma once

#include <JuceHeader.h>

// forward
class WilsonicProcessor;
class WilsonicEditor;

/**
 * @class SnapshotMode
 * @brief Drives the editor through manifest entries and writes PNG snapshots.
 */
class SnapshotMode : private Timer {
public:
    /**
     * @brief Starts snapshot mode if the standalone was launched with --snapshot.
     * @details Called at the end of the WilsonicEditor constructor. A NOP for
     * plugin builds, for non-standalone wrappers, and when the flag is absent.
     */
    static void startIfRequested(WilsonicProcessor&, WilsonicEditor&);

    /**
     * @brief True while a snapshot run is in progress.
     * @details Used to suppress side effects of normal app teardown, such as
     * persisting the window bounds that snapshot mode forced.
     */
    static bool isActive();

    ~SnapshotMode() override;

private:
    SnapshotMode(WilsonicProcessor&, WilsonicEditor&, const File& manifestFile, const File& outputDirectory);

    void timerCallback() override;
    bool _applyEntry(const var& entry); // returns false if the entry is malformed
    bool _captureEntry(const var& entry);
    void _logEntryError(const String& message);
    void _finish();

    static std::unique_ptr<SnapshotMode> __instance;
    static bool __active;

    WilsonicProcessor& _processor;
    WilsonicEditor& _editor;
    File _outputDirectory;
    var _defaults;
    Array<var> _entries;
    int _entryIndex = 0;
    int _settleTicksRemaining = 0;
    bool _entryApplied = false;
    int _failureCount = 0;

    static constexpr int __timerIntervalMs = 50;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SnapshotMode)
};
