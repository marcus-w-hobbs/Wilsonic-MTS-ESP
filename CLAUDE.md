# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

### macOS (Primary Development Platform)
```bash
# Build standalone app and plugins using Xcode
open Builds/MacOSX/Wilsonic.xcodeproj
# Select target (Standalone, AU, VST3) and build

# Or build WilsonicController
open Builds/MacOSX/WilsonicController.xcodeproj
```

### Cross-Platform Build via Command Line
```bash
# Linux/CI build (using makefiles)
cd Builds/LinuxMakefile
make -j4 CONFIG=Release

# Run unit tests
make -C tests
./tests/test_wilsonicmath
```

### Windows
```bash
# Open in Visual Studio 2022
Builds/VisualStudio2022/Wilsonic.sln
```

## Architecture Overview

This is a JUCE-based audio plugin implementing Erv Wilson's microtuning theories via MTS-ESP.

### Core Design Pattern
- **Processor** (WilsonicProcessor) owns all state via AudioProcessorValueTreeState (APVTS)
- **Models** bind Tuning objects to APVTS parameters and provide UI interfaces
- **Tunings** generate MTS-ESP data and know how to draw themselves
- **Editor** only renders UI; may not exist (headless operation)
- **Components** delegate drawing to Models → Tunings

### Key Components

1. **Tuning System** (`Source/Tuning*`)
   - Base classes: `Tuning.h`, `TuningImp.h`
   - Microtone representation: `Microtone.h` (pitch/frequency calculations)
   - Implementations: CPS, Brun, EulerGenus, Diamonds, etc.

2. **Model Layer** (`Source/*Model.cpp`)
   - AppTuningModel: Main tuning model orchestrator
   - Design-specific models: CPSModel, BrunModel, EulerGenusModel, etc.
   - MorphModel: Handles interpolation between tunings

3. **MTS-ESP Integration**
   - Located in `Source/MTS-ESP/`
   - Broadcasts microtuning to all MTS-ESP compatible synths in DAW

4. **UI Components** (`Source/*Component.cpp`)
   - Custom JUCE components for each tuning type
   - Keyboard visualization: WilsonicMidiKeyboardComponent
   - Pitch wheel and interval matrix displays

## Testing

### Unit Tests
- Test framework: Custom test runner in `Source/TuningTests.h`
- Run via: `processor.runTests()` or individual test methods
- Test files: `Source/TuningTests+*.cpp`

### Simple Math Tests
```bash
make -C tests
./tests/test_wilsonicmath
```

## Development Guidelines

### Adding New Scale Designs (Tuning Systems)

**⚠️ WARNING: Adding a new scale design BREAKS existing DAW automation and user presets!**

The design index order in `DesignsModel` is critical and must never change. New designs must be added at the END of the list to preserve backward compatibility.

#### Example: Equal Temperament Implementation

Using Equal Temperament as a concrete example, here are all the files that need modification:

##### 1. Core Tuning Implementation
- `EqualTemperament.h/cpp` - Inherits from `TuningImp`, implements the tuning logic
- Key methods: `setNPO()`, `setPeriod()`, `paint()`, `defaultScalaName()`

##### 2. Model Layer (APVTS Binding)
- `EqualTemperamentModel.h/cpp` - Manages parameters and UI state
- Defines parameter IDs: `EQUALTEMPERAMENTNPO`, `EQUALTEMPERAMENTPERIOD`
- `EqualTemperamentMorphModel.h/cpp` - Enables morphing between instances

##### 3. UI Component
- `EqualTemperamentComponent.h/cpp` - Visual representation and user interaction

##### 4. Registration in DesignsModel (`DesignsModel.cpp`)
```cpp
// In constructor, add at END of list (index 6 in this case):
_designsNames.add("Equal Temperament");
_tuningDesignKeys.push_back(_equalTemperamentModel->getDesignParameterID().getParamID());
_functionNames.push_back([this](){showEqualTemperamentTuning();});
_tuningChangedActionMessage.add(getEqualTemperamentTuningChangedActionMessage());
_tuningChangedFunctionNames.push_back([this]() {
    _appTuningModel->setTuning(_equalTemperamentModel->getTuning());
});
_tuningParamIDsForFavorites.push_back([this]() {
    return _equalTemperamentModel->getFavoritesParameterIDs();
});
_equalTemperamentModel->addActionListener(this);
_equalTemperamentModel->setDesignIndex(designIndex);
```

##### 5. Protocol Methods (`DesignsProtocol.h`)
Add virtual method: `virtual void showEqualTemperamentTuning() = 0;`

##### 6. Implementation Chain
Each of these files needs the show method implementation:
- `DesignsModel.h/cpp` - Add static message getters and implementation
- `WilsonicProcessor.h/cpp` - Forward to editor
- `WilsonicEditor.h/cpp` - Forward to app root
- `AppRootComponent.h/cpp` - Forward to root component
- `WilsonicRootComponent.h/cpp` - Create and display the component

##### 7. Parameter Group Registration (`WilsonicProcessor+Params.cpp`)
```cpp
auto etParamGroup = _designsModel->getEqualTemperamentModel()->createParams();
// Add to wilsonicParamGroup constructor IN ORDER
```

##### 8. Action Message Handling
- Add message constants in `DesignsModel.h`
- Handle in `actionListenerCallback` implementations

##### 9. Additional Updates
- Update `MorphABModel` if morphing is supported
- Add to factory maps if using factory pattern (e.g., in EulerGenusModel)
- Create unit tests in `TuningTests+EqualTemperament.cpp`

#### File Modification Checklist

Every new scale design requires changes to these files (search for "ADD NEW SCALE DESIGN HERE"):
- [ ] `DesignsModel.h` - Add forward declaration, message getters
- [ ] `DesignsModel.cpp` - Register in constructor, add implementation
- [ ] `DesignsProtocol.h` - Add virtual show method
- [ ] `WilsonicProcessor.h/cpp` - Add show method implementation
- [ ] `WilsonicProcessor+Params.cpp` - Add parameter group
- [ ] `WilsonicEditor.h/cpp` - Add show method implementation
- [ ] `WilsonicRootComponent.h/cpp` - Add component member and show method
- [ ] `AppRootComponent.h/cpp` - Add show method implementation
- [ ] `MorphABModel.cpp` (if morphing supported)

#### Impact on Users
- **DAW Automation**: Parameter indices shift, breaking existing automation
- **Presets**: Design selection index changes invalidate saved states
- **Favorites**: May reference wrong designs after update

#### Best Practices
1. Always add new designs at the END of the list
2. Never reorder existing designs
3. Test parameter automation after adding
4. Document the design index in release notes
5. Consider versioning strategy for major changes

### Parameter Automation
- All tuning parameters must be registered in APVTS
- See `daw_automated_params.txt` for parameter list
- Parameters are created in `WilsonicProcessor+Params.cpp`

### Code Style
- Use JUCE conventions (camelCase, etc.)
- Prefer `shared_ptr` for Tuning objects
- Always validate floating point calculations with appropriate epsilon checks
- Use `jassert` for debug assertions

## Important Files

- `Wilsonic.jucer` - Main plugin project
- `WilsonicController.jucer` - MIDI controller variant
- `Source/WilsonicProcessor.cpp` - Core audio processor
- `Source/AppTuningModel.cpp` - Main tuning orchestrator
- `Source/Tuning_Include.h` - Common tuning headers
- `all_tunings.json` - Tuning preset definitions

---

## Conceptual Framework: Erv Wilson's Scale Design Philosophy

This section captures the theoretical foundations underlying Wilsonic. Understanding these concepts is essential for meaningful contributions to the codebase.

### The Melody/Harmony Problem

Scale design faces a fundamental tension:

- **Melodic resources** require stepwise patterns, voice leading, scalar continuity—the *horizontal* dimension of music
- **Harmonic resources** require chord relationships, consonance, reinforcing overtones—the *vertical* dimension

Most scale systems optimize for one at the expense of the other. Wilson's genius was finding structures that solve both simultaneously.

### MOS (Moment of Symmetry) Scales

Implemented in `Brun.cpp`, `Brun.h`, and related files.

**Core algorithm**: Iterate a generator interval, fold into a period (typically octave), producing a two-interval pattern (Large, small). The Brun algorithm (`brunArray()`) computes this via continued fraction approximation.

**Key insight**: MOS scales have a nested recursive structure. Each "level" contains the previous level's pitches plus new ones. This creates natural hierarchies of stability—lower-level pitches feel more "anchored."

**Why MOS solves melody**: The two-interval constraint guarantees stepwise motion is always available. The nested structure provides voice-leading paths. Murchana (mode rotation) gives you modal variety for free.

### The Proportional Triad Discovery

Implemented in `TuningImp::_analyzeProportionalTriads()`.

**The problem**: MOS is constructed in *logarithmic* pitch space (generator iteration), but harmonic reinforcement happens in *linear* frequency space (sum/difference tones). These spaces don't naturally align.

**Wilson's solution**: Find generators where the arithmetic and geometric structures *accidentally* coincide. For such generators, the MOS scale contains triads where:

- **Proportional (major)**: The middle note ≈ arithmetic mean of outer notes: `(a + b) / 2`
- **Subcontrary (minor)**: The middle note ≈ harmonic mean of outer notes: `2ab / (a + b)`

When these conditions are met, sum and difference tones land *on other scale degrees*, creating harmonic reinforcement rather than interference.

**The code**: `_analyzeProportionalTriads()` iterates all pitch pairs, computes both means, and searches for scale degrees within tolerance (currently 0.0005 in unit pitch space). Results populate `_proportionalTriads` and `_subcontraryTriads` vectors.

### The Optimization Landscape

Not all generators are equal. The space of generators (0 to 1) contains:

- **Dead zones**: Most generators produce scales with zero or few proportional triads
- **Hot spots**: Certain generators (often related to noble numbers, metallic means) produce anomalously many triads
- **Level dependence**: Triad count varies with MOS depth; humans can meaningfully perceive ~9 levels max

**Research opportunity**: Plotting triad *quality* (not just count) as a function of generator and level would reveal Wilson's generators as peaks in this landscape. Quality could be defined as sum of `1/error` for all near-coincidences, giving a continuous rather than discrete measure.

### CPS (Combination Product Sets)

Implemented in `CPS.cpp`, `CPS_*.cpp` files.

**Different architecture**: While MOS iterates one generator, CPS derives from Pascal's triangle. Given N harmonic factors, take all k-combinations, multiply each combination, octave-reduce.

**Example**: The Eikosany uses 6 factors (1, 3, 5, 7, 9, 11), taking all 2-combinations and 4-combinations, yielding 20 notes.

**Trade-off**: CPS guarantees harmonic relationships by construction but lacks MOS's melodic continuity. Scales can have "gaps" that feel unscalar.

### The Gral Keyboard

Implemented in `Brun+Gral.cpp`.

**Wilson's isomorphic keyboard design**: Maps MOS structure to a 2D hexagonal grid where:
- One axis = generator stacking
- Other axis = period offset
- Co-prime factors ensure playability for human hands

**Key function**: `_mapGralToBrunMicrotones()` transforms abstract generator/period relationships into physical keyboard coordinates.

### Human Auditory Cognition

**Pitch perception**: Approximately logarithmic (hence log-frequency = pitch)

**Combination tones**: When two pitches sound simultaneously, humans perceive sum and difference frequencies. These are *linear* operations on frequency, not pitch.

**The bridge**: Wilson's optimized generators find points where log-space structures (MOS) produce linear-space coincidences (proportional triads). This is why the code works in both spaces—`Microtone` stores both `pitchValue01` (log) and `frequencyValue` (linear).

### Tolerance and Perception

The magic number `0.0005` in `_analyzeProportionalTriads()` represents a perceptual threshold. Human pitch discrimination is roughly 5-10 cents in musically relevant registers. The tolerance allows "near misses" that are perceptually equivalent to exact coincidences.

**Note**: This could be parameterized. Lower tolerance = stricter matching, fewer triads. Higher tolerance = more triads but weaker reinforcement.

### Key Mathematical Relationships

```
Arithmetic mean (proportional/major):  (a + b) / 2
Geometric mean (neutral):              sqrt(a * b)
Harmonic mean (subcontrary/minor):     2ab / (a + b)

Relationship: harmonic < geometric < arithmetic (for a ≠ b)
```

The geometric mean falls between arithmetic and harmonic, so "neutral" triads come "for free" if you have good major and minor triads.

### Research Directions

1. **Generator landscape visualization**: Plot triad quality vs. generator vs. level as a heatmap
2. **Tolerance sensitivity**: How does triad count change with tolerance? Is there a phase transition?
3. **Cross-system bridges**: Can CPS harmonic richness be combined with MOS melodic continuity?
4. **Continued fraction properties**: What properties of a generator's CF expansion predict triad density?

### Historical Context

Erv Wilson (1928-2016) developed these theories largely without computational tools. Marcus Hobbs worked directly with Wilson from 1995-2005, implementing his designs in software during real-time sessions. Much of Wilson's work exists only in hand-drawn diagrams; this codebase represents the most complete computational implementation of his theories.

### For AI Collaborators

When working on this codebase:

1. **Understand both spaces**: Many bugs come from confusing log-pitch and linear-frequency operations
2. **Respect the tolerance**: The 0.0005 threshold is empirically tuned; changes have cascading effects
3. **Test with extreme generators**: Edge cases near 0, 0.5, and 1 reveal algorithmic assumptions
4. **Visualize everything**: Wilson thought visually; the `paint()` methods are as important as the math
5. **Remember the goal**: Scales that serve both melody AND harmony—this is the Wilson criterion