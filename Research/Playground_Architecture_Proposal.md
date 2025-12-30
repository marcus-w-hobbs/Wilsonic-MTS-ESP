# Wilson Research Playground - Architecture Proposal

## The Problem

Wilsonic-MTS-ESP is a production audio plugin with:
- JUCE dependencies throughout (`<JuceHeader.h>` in most files)
- Paint/UI code mixed with computational code
- Real-time audio constraints
- DAW automation compatibility requirements
- Heavy build process (Xcode, JUCE Projucer)

This makes it painful for research/exploration.

## The Insight

Looking at the codebase, there's a separation already emerging:
- **Computational core**: `Microtone`, `MicrotoneArray`, `WilsonicMath`, recurrence relations, triad analysis
- **UI/Plugin layer**: Paint methods, JUCE components, DAW integration

The computational core *could* be extracted with relatively surgical changes.

## Proposed Architecture

```
wilson-research/                    # New repo - the playground
├── core/                           # Extracted from Wilsonic, JUCE-free
│   ├── Microtone.h/cpp            # Pitch representation
│   ├── MicrotoneArray.h/cpp       # Scale representation  
│   ├── WilsonicMath.h/cpp         # Utilities (already JUCE-free!)
│   ├── Fraction.h/cpp             # Rational numbers
│   ├── TuningConstants.h          # Constants
│   ├── Brun_Core.h/cpp            # MOS generation (no paint methods)
│   ├── CPS_Core.h/cpp             # Combination product sets (no paint)
│   ├── RecurrenceRelation_Core.h  # Recurrence machinery
│   └── ProportionalTriads.h/cpp   # Triad analysis (extracted from TuningImp)
│
├── playground/                     # New exploratory code
│   ├── GeneratorLandscape.cpp     # Sweep generator space, compute triad quality
│   ├── CPSMOSBridge.cpp           # Seeding experiments
│   ├── CFExpansion.cpp            # Continued fraction utilities
│   └── main.cpp                   # CLI or simple test harness
│
├── python/                         # Python bindings via pybind11
│   ├── wilson_core.cpp            # Bindings to core/
│   └── notebooks/
│       ├── generator_landscape.ipynb
│       ├── cps_mos_bridge.ipynb
│       └── wilson_documents.ipynb
│
├── web/                            # Optional: web visualization
│   └── (React/TypeScript later)
│
└── Makefile                        # Simple build, no JUCE
```

## The Extraction Process

### Phase 1: Identify JUCE Dependencies in Core Classes

From my analysis:
- `Microtone.h`: Uses `Point<float>`, `Path` (JUCE types) for Gral visualization
- `Brun.h`: Uses `Graphics`, `Rectangle`, `StringArray`, `String`
- `TuningImp.h`: Heavy JUCE for paint methods

### Phase 2: Create JUCE-Free Core Versions

**Option A: Preprocessor guards**
```cpp
#ifdef WILSON_STANDALONE
    // Use std:: types
    using Point2D = std::pair<float, float>;
#else
    #include <JuceHeader.h>
    using Point2D = juce::Point<float>;
#endif
```

**Option B: Extract computational methods only**
```cpp
// Brun_Core.h - NO paint methods, NO JUCE
class BrunCore {
public:
    static MicrotoneArray generateMOS(unsigned long level, float generator);
    static std::vector<float> getContinuedFraction(float generator, int depth);
    static std::vector<int> getMOSSequence(float generator, int maxLevel);
};
```

Option B is cleaner - we're not trying to make Wilsonic JUCE-free, we're extracting the math.

### Phase 3: Build System

Simple Makefile (like your existing `tests/Makefile`):
```makefile
CXX = clang++
CXXFLAGS = -std=c++17 -O2 -I./core

CORE_SRCS = core/Microtone.cpp core/MicrotoneArray.cpp core/WilsonicMath.cpp \
            core/Brun_Core.cpp core/CPS_Core.cpp core/ProportionalTriads.cpp

playground: $(CORE_SRCS) playground/main.cpp
    $(CXX) $(CXXFLAGS) $^ -o playground
```

### Phase 4: Python Bindings (Optional but Powerful)

Using pybind11:
```cpp
#include <pybind11/pybind11.h>
#include "Brun_Core.h"

PYBIND11_MODULE(wilson_core, m) {
    m.def("generate_mos", &BrunCore::generateMOS);
    m.def("analyze_triads", &ProportionalTriads::analyze);
    m.def("cf_expansion", &CFExpansion::expand);
}
```

Then in Jupyter:
```python
import wilson_core as wc
import matplotlib.pyplot as plt

# Sweep generator space
generators = np.linspace(0, 1, 1000)
triad_quality = [wc.analyze_triads(wc.generate_mos(5, g)) for g in generators]

plt.plot(generators, triad_quality)
plt.title("Triad Quality Landscape at Level 5")
```

## What I Can Do

1. **Extract the core classes** - I can read through Brun.cpp, CPS.cpp, TuningImp.cpp and pull out the computational methods into JUCE-free versions.

2. **Create the Makefile** - Simple build system that compiles in seconds.

3. **Write the initial playground experiments** - Generator landscape sweep, CPS/MOS bridge prototype.

4. **Set up pybind11 bindings** - If you want Python/Jupyter for visualization.

## Path Back to Wilsonic

When something in the playground graduates to "this should be playable":

1. The core algorithm is already C++ 
2. Wrap it in JUCE UI components
3. Add to Wilsonic's existing Model/Tuning pattern
4. The research informs the plugin, not the other way around

## Decision Points for You

1. **Do you want Python bindings?** (Jupyter is great for visualization)
2. **Do you want web visualization?** (Shareable with community)
3. **Which experiments first?** Generator landscape? CPS seeding?
4. **Where should the repo live?** Separate repo, or `Wilsonic-MTS-ESP/research/`?

---

If you say "go," I can start extracting the core classes right now.
