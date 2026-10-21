/*
  ==============================================================================

    TuningOutput.h
    Created: 18 Oct 2026
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

/**
 * @file TuningOutput.h
 * @brief The out-of-band output stage: what Wilsonic sends for a key whose raw
 * tuning-table frequency is outside the playable band or is not a usable number.
 *
 * This file is JUCE-free so tests/Makefile can compile it.
 *
 * The tuning itself (TuningImp, TuningTableImp, getTuningTableFrequency()) stays
 * raw: Morph interpolates raw tables, the analyses and the .ascl exporter read raw
 * values. computeTuningOutput() runs only on the way out, to MTS-ESP, the built-in
 * synth and the keyboard.
 *
 * The band is Ableton Live's: 4 Hz .. 21 kHz inclusive (TuningConstants).
 * Keys never move. An out-of-band key keeps its key number and gets a stand-in
 * frequency following the MTS-ESP master guidance (libMTSMaster.h): the frequency
 * of the nearest lower in-band KEY NUMBER, else the nearest higher, else the raw
 * value clamped to the band.
 */

#pragma once

#include "TuningConstants.h"
#include "WilsonicProcessorConstants.h"

/**
 * @enum OutOfBandPolicy
 * @brief Per-machine preference for keys outside the playable band.
 *
 * Stored as an int in the PropertiesFile (WilsonicProcessor+Properties.cpp), so
 * the values must never change.
 */
enum class OutOfBandPolicy : int
{
    Filter = 0,      ///< Live-aligned: mark the key filtered, send a stand-in frequency.
    PassThrough = 1  ///< Send raw sub-audio / ultrasonic values; only NaN, inf and <= 0 are replaced.
};

/**
 * @struct TuningOutput
 * @brief The 128-key table that reaches MTS-ESP, the synth and the keyboard.
 */
struct TuningOutput
{
    static constexpr unsigned long numKeys = WilsonicProcessorConstants::numMidiNotes;
    double hz[numKeys];      ///< always finite and > 0; in band in Filter mode
    bool filtered[numKeys];  ///< true => MTS_FilterNote(true, key, -1), synth mute, grey key
};

/// A value MTS-ESP and the synth can take at all: finite and > 0.
bool isUsableFrequency(double hz);

/// Inside Live's band, both ends inclusive (implies usable).
bool isFrequencyInBand(double hz);

/**
 * @brief Compute the output table for one raw 128-key tuning table.
 * @param raw The raw tuning-table frequencies, key order = MIDI note order.
 * @param policy Filter (default) or PassThrough.
 * @param preFiltered Optional: keys the tuning itself marks unmapped
 * (Microtone::getFilterNote()). They are filtered under BOTH policies, never
 * stand in for other keys, and take a stand-in themselves. nullptr = none.
 */
TuningOutput computeTuningOutput(const float raw[TuningOutput::numKeys],
                                 OutOfBandPolicy policy,
                                 const bool preFiltered[TuningOutput::numKeys] = nullptr);
