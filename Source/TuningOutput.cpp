/*
  ==============================================================================

    TuningOutput.cpp
    Created: 18 Oct 2026
    Author:  Marcus W. Hobbs

  ==============================================================================
*/

#include "TuningOutput.h"

#include <cmath>

namespace
{
constexpr unsigned long kNumKeys = TuningOutput::numKeys;
constexpr double kMinHz = TuningConstants::kPlayableMinHz;
constexpr double kMaxHz = TuningConstants::kPlayableMaxHz;

/// Clamp one raw value into the band when no neighbour can stand in for it.
/// NaN and anything <= 0 (including -inf) go to the low edge; +inf to the high edge.
double clampToBand(double raw)
{
    if (std::isnan(raw) || raw <= 0.0) {
        return kMinHz;
    }
    if (raw < kMinHz) {
        return kMinHz;
    }
    if (raw > kMaxHz) {
        return kMaxHz;
    }
    return raw;
}

/// The MTS-ESP neighbour rule over the keys flagged eligible: nearest lower key
/// number, else nearest higher, else clamp the key's own raw value.
double standIn(const double raw[kNumKeys], const bool eligible[kNumKeys], unsigned long key)
{
    for (unsigned long k = key; k-- > 0;) {
        if (eligible[k]) {
            return raw[k];
        }
    }
    for (unsigned long k = key + 1; k < kNumKeys; ++k) {
        if (eligible[k]) {
            return raw[k];
        }
    }
    return clampToBand(raw[key]);
}
} // namespace

bool isUsableFrequency(double hz)
{
    return std::isfinite(hz) && hz > 0.0;
}

bool isFrequencyInBand(double hz)
{
    return isUsableFrequency(hz) && hz >= kMinHz && hz <= kMaxHz;
}

TuningOutput computeTuningOutput(const float raw[TuningOutput::numKeys],
                                 OutOfBandPolicy policy,
                                 const bool preFiltered[TuningOutput::numKeys])
{
    TuningOutput out {};
    double rawd[kNumKeys];
    bool eligible[kNumKeys];

    // Filter: a key may stand in for others only when it is in band.
    // PassThrough: any usable value may, sub-audio and ultrasonic included.
    bool const filterMode = (policy == OutOfBandPolicy::Filter);
    for (unsigned long k = 0; k < kNumKeys; ++k) {
        rawd[k] = static_cast<double>(raw[k]);
        bool const unmapped = (preFiltered != nullptr) && preFiltered[k];
        eligible[k] = !unmapped && (filterMode ? isFrequencyInBand(rawd[k]) : isUsableFrequency(rawd[k]));
    }

    for (unsigned long k = 0; k < kNumKeys; ++k) {
        bool const unmapped = (preFiltered != nullptr) && preFiltered[k];
        if (eligible[k]) {
            out.hz[k] = rawd[k];
            out.filtered[k] = false;
        } else {
            out.hz[k] = standIn(rawd, eligible, k);
            // PassThrough replaces an unusable value but never filters it;
            // an unmapped key is filtered under both policies
            out.filtered[k] = filterMode || unmapped;
        }
    }

    return out;
}
