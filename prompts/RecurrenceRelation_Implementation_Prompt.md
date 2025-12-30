# Implementation Prompt: Harmonic Sum & Seed Space for RecurrenceRelation

## Overview

Extend the `RecurrenceRelation` class with two new automatable DAW parameters that create a 2×2 matrix of scale generation modes. This implements a duality discovered between arithmetic and harmonic recurrence operations, extending Erv Wilson's scale design theories into new territory.

**Scope**: Adding parameters to an existing tuning type. No new tuning class is needed.

---

## Conceptual Background

### The Duality

Standard recurrence relations use arithmetic sum: `H[n] = H[n-i] + H[n-j]`

When revoiced (÷2), this produces **proportional triads** where the middle note is the arithmetic mean of the outer notes.

The dual operation uses harmonic sum: `H[n] = H[n-i] · H[n-j] / (H[n-i] + H[n-j])`

When revoiced (×2), this produces **subcontrary triads** where the middle note is the harmonic mean of the outer notes.

### Key Mathematical Properties

- Arithmetic Fibonacci converges to φ ≈ 1.618 (generator ≈ 0.694)
- Harmonic Fibonacci converges to 1/φ ≈ 0.618 (generator ≈ 0.306)
- The generators are **octave complements** (sum to 1.0)
- This produces **mirror MOS** structures (L and s intervals swap)

### The 2×2 Matrix

| SumType | SeedSpace | Musical Character |
|---------|-----------|------------------|
| Arithmetic | Frequency | **Classic** (current behavior) |
| Arithmetic | Period | Undertone seeds, overtone growth |
| Harmonic | Frequency | Overtone seeds, undertone growth |
| Harmonic | Period | **Full dual** (mirror MOS) |

---

## Functional Requirements

### FR1: SumType Parameter

Add an automatable parameter to switch between arithmetic and harmonic sum operations.

**Behavior:**
- `Arithmetic` (index 0): Current behavior — `f = a + b`
- `Harmonic` (index 1): New behavior — `f = (a * b) / (a + b)`

**Constraints:**
- Default to `Arithmetic` to preserve backward compatibility
- Must be `AudioParameterChoice` for DAW automation
- Must trigger recurrence calculation on change via `parameterChanged()` callback
- Must be included in `getFavoritesParameterIDs()` for preset recall
- Must be thread-safe via existing `_lock` pattern

### FR2: SeedSpace Parameter

Add an automatable parameter to control whether seeds are used as-is or inverted.

**Behavior:**
- `Frequency` (index 0): Use seeds as-is (current behavior)
- `Period` (index 1): Invert seeds (use 1/seed)

**Constraints:**
- Default to `Frequency` to preserve backward compatibility
- Seed inversion happens **ONLY during the seed-planting phase**, NOT during recurrence iteration
- Must handle edge case: if seed ≤ 0, skip inversion (avoid division by zero)
- Must be `AudioParameterChoice` for DAW automation
- Must trigger recurrence calculation on change
- Must be included in `getFavoritesParameterIDs()` for preset recall
- Must be thread-safe via existing `_lock` pattern

### FR3: Logging

Update the `_log` string to always reflect the current mode, appearing at the end of the recurrence description line.

**Format:**
```
! H[n] = H[n-1] + H[n-2] [Arithmetic, Frequency]
```
or
```
! H[n] = H[n-1] ⊕ H[n-2] [Harmonic, Period]
```

Note: Use ASCII characters (`+` for arithmetic sum, `⊕` for harmonic sum is nice-to-have but not required).

### FR4: Convergence Reporting

The convergence calculation should work correctly for both modes. Harmonic sequences converge to the reciprocal ratio, which is mathematically valid.

---

## Product Requirements

### PR1: UI Integration

Two new dropdown controls in `RecurrenceRelationComponent`, positioned **below the Index selector**:
- Dropdown 1: SumType (Arithmetic / Harmonic)
- Dropdown 2: SeedSpace (Frequency / Period)

**Layout pattern**: Match existing Index dropdown styling and spacing. Use `DeltaComboBox` for consistency with Index parameter.

**Tooltips** (with `setToolTip()` on each dropdown):
- **SumType**: "Sum Type: Arithmetic (a+b) produces proportional triads. Harmonic (ab/(a+b)) produces subcontrary triads with harmonic mean relationships."
- **SeedSpace**: "Seed Space: Frequency uses seeds as-is. Period inverts seeds (1/s) to explore undertone/overtone duality and mirror MOS structures."

### PR2: Preset Compatibility

Existing presets load with defaults (Arithmetic, Frequency) automatically. No special migration code needed—APVTS handles missing parameters.

### PR3: Scala Export

The Scala file comments (via `scalaComments()` → `getLog()`) always include mode information so exported scales document their generation method.

---

## Implementation Details

### File: RecurrenceRelation.h

**Add enums after line ~38 (after existing `Coefficient` enum):**

```cpp
enum class SumType
{
    Arithmetic,  // H[n] = a + b
    Harmonic     // H[n] = ab/(a+b)
};

enum class SeedSpace
{
    Frequency,   // Seeds used as-is: s
    Period       // Seeds inverted: 1/s
};
```

**Add static description arrays after line ~44:**

```cpp
static StringArray getSumTypeDescription() { return __sumTypeDescription; }
static StringArray getSeedSpaceDescription() { return __seedSpaceDescription; }
```

**Add private static members after line ~72:**

```cpp
private:
    static StringArray __sumTypeDescription;
    static StringArray __seedSpaceDescription;
```

**Add private member variables after line ~124:**

```cpp
private:
    SumType _sumType = SumType::Arithmetic;
    SeedSpace _seedSpace = SeedSpace::Frequency;
```

**Add public accessor methods before line ~100 (near existing getLog()):**

```cpp
public:
    void setSumType(SumType sumType);
    SumType getSumType();
    void setSumTypeByIndex(unsigned long index);  // For DAW automation

    void setSeedSpace(SeedSpace seedSpace);
    SeedSpace getSeedSpace();
    void setSeedSpaceByIndex(unsigned long index);  // For DAW automation
```

### File: RecurrenceRelation.cpp

**Add static descriptions after line ~136 (after `__coefficientsDescriptionMap`):**

```cpp
StringArray RecurrenceRelation::__sumTypeDescription =
{
    "Arithmetic",
    "Harmonic"
};

StringArray RecurrenceRelation::__seedSpaceDescription =
{
    "Frequency",
    "Period"
};
```

**Add accessor implementations after line ~372 (after `getValueForCoefficient()`):**

```cpp
void RecurrenceRelation::setSumType(SumType sumType)
{
    const ScopedLock sl(_lock);
    _sumType = sumType;
    _updateRecurrenceRelation();
}

RecurrenceRelation::SumType RecurrenceRelation::getSumType()
{
    return _sumType;
}

void RecurrenceRelation::setSumTypeByIndex(unsigned long index)
{
    jassert(index < 2);
    const ScopedLock sl(_lock);
    _sumType = (index == 0) ? SumType::Arithmetic : SumType::Harmonic;
    _updateRecurrenceRelation();
}

void RecurrenceRelation::setSeedSpace(SeedSpace seedSpace)
{
    const ScopedLock sl(_lock);
    _seedSpace = seedSpace;
    _updateRecurrenceRelation();
}

RecurrenceRelation::SeedSpace RecurrenceRelation::getSeedSpace()
{
    return _seedSpace;
}

void RecurrenceRelation::setSeedSpaceByIndex(unsigned long index)
{
    jassert(index < 2);
    const ScopedLock sl(_lock);
    _seedSpace = (index == 0) ? SeedSpace::Frequency : SeedSpace::Period;
    _updateRecurrenceRelation();
}
```

**Modify `_updateRecurrenceRelation()` — Seed Planting Phase (around line ~480):**

Find the seed-planting loop:
```cpp
// plant seeds(seeds are the initial conditions so don't use coefficients)
for(auto j = _j; j > 0; j--) // _j > _i > 0
{
    auto seed = _seeds.microtoneAtIndex(j - 1);
    raw_ma.addMicrotone(seed);
    _log += seed->getFrequencyValueDescription();
```

Replace with:
```cpp
// plant seeds(seeds are the initial conditions so don't use coefficients)
for(auto j = _j; j > 0; j--) // _j > _i > 0
{
    auto seed = _seeds.microtoneAtIndex(j - 1);
    auto seedValue = seed->getFrequencyValue();

    // Transform seed if in Period space
    if (_seedSpace == SeedSpace::Period && seedValue > 0.f)
    {
        seedValue = 1.f / seedValue;
    }

    auto transformedSeed = (_seedSpace == SeedSpace::Period && seed->getFrequencyValue() > 0.f)
                          ? make_shared<Microtone>(seedValue)
                          : seed;
    raw_ma.addMicrotone(transformedSeed);
    _log += transformedSeed->getFrequencyValueDescription();
```

**Modify `_updateRecurrenceRelation()` — Recurrence Calculation (around line ~523):**

Find this line:
```cpp
auto const f = ci * mti->getFrequencyValue() + cj * mtj->getFrequencyValue();
```

Replace with:
```cpp
auto const a = ci * mti->getFrequencyValue();
auto const b = cj * mtj->getFrequencyValue();
float f;
if (_sumType == SumType::Arithmetic)
{
    // Standard: a + b
    f = a + b;
}
else // SumType::Harmonic
{
    // Harmonic sum: ab/(a+b)
    // Guard against division by zero
    auto const sum = a + b;
    f = (sum > 0.f) ? (a * b) / sum : 0.f;
}
```

**Modify `_updateRecurrenceRelation()` — Log String Initialization (around line ~453):**

Find:
```cpp
// init _log
_log = "! H[n] = ";
```

Keep this, but find the end of the recurrence description building (around line ~477), and before the seed listing, add mode information. Locate where it says:
```cpp
_log += "]\n! \n! Integer Sequence, including seeds:\n!  ";
```

Replace with:
```cpp
_log += "]";
_log += (_sumType == SumType::Arithmetic) ? " [Arithmetic" : " [Harmonic";
_log += (_seedSpace == SeedSpace::Frequency) ? ", Frequency]\n! \n! Integer Sequence, including seeds:\n!  " : ", Period]\n! \n! Integer Sequence, including seeds:\n!  ";
```

---

## File: RecurrenceRelationModel.h

**Add parameter ID accessors after line ~91 (after `getRecurrenceRelationNumTermsParameterID()`):**

```cpp
static const ParameterID getRecurrenceRelationSumTypeParameterID() { return ParameterID("RECURRENCERELATIONSUMTYPE", AppVersion::getVersionHint()); }
static const String getRecurrenceRelationSumTypeParameterName() { return "Recurrence Relation|Sum Type"; }

static const ParameterID getRecurrenceRelationSeedSpaceParameterID() { return ParameterID("RECURRENCERELATIONSEEDSPACE", AppVersion::getVersionHint()); }
static const String getRecurrenceRelationSeedSpaceParameterName() { return "Recurrence Relation|Seed Space"; }
```

---

## File: RecurrenceRelationModel.cpp

**Add parameters in `createParams()` (around line ~298, before the closing of `paramGroup`):**

```cpp
     // Sum Type
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationSumTypeParameterID(),
      getRecurrenceRelationSumTypeParameterName(),
      RecurrenceRelation::getSumTypeDescription(),
      0  // default to Arithmetic
      ),

     // Seed Space
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationSeedSpaceParameterID(),
      getRecurrenceRelationSeedSpaceParameterName(),
      RecurrenceRelation::getSeedSpaceDescription(),
      0  // default to Frequency
      )
```

**Update `getFavoritesParameterIDs()` (around line ~345):**

Add these two parameter IDs to the StringArray returned:
```cpp
getRecurrenceRelationSumTypeParameterID().getParamID(),
getRecurrenceRelationSeedSpaceParameterID().getParamID(),
```

**Add handlers in `parameterChanged()` (after the "Number of terms" handler, around line ~382):**

```cpp
    // Sum Type
    else if(parameterID == getRecurrenceRelationSumTypeParameterID().getParamID()) {
        _recurrenceRelation->setSumTypeByIndex(static_cast<unsigned long>(newValue));
        return;
    }

    // Seed Space
    else if(parameterID == getRecurrenceRelationSeedSpaceParameterID().getParamID()) {
        _recurrenceRelation->setSeedSpaceByIndex(static_cast<unsigned long>(newValue));
        return;
    }
```

---

## File: RecurrenceRelationComponent.h

**Add member variables after line ~57 (after `_numTermsBubble`):**

```cpp
private:
    BubbleDrawable _sumTypeBubble;
    unique_ptr<DeltaComboBox> _sumTypeComboBox;
    BubbleDrawable _seedSpaceBubble;
    unique_ptr<DeltaComboBox> _seedSpaceComboBox;
```

---

## File: RecurrenceRelationComponent.cpp

**Add initialization in constructor (after Index setup, around line ~54):**

```cpp
    // Bubble: Sum Type
    addAndMakeVisible(_sumTypeBubble);

    // Sum Type dropdown
    _sumTypeComboBox = make_unique<DeltaComboBox>(_processor, false);
    _sumTypeComboBox->addItemList(RecurrenceRelation::getSumTypeDescription(), 1);
    _sumTypeComboBox->setToolTip("Sum Type: Arithmetic (a+b) produces proportional triads. Harmonic (ab/(a+b)) produces subcontrary triads with harmonic mean relationships.");
    _sumTypeComboBox->setSelectedItemIndex(0, NotificationType::dontSendNotification);
    auto onSumTypeChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_sumTypeComboBox->getSelectedItemIndex());
        rrm->uiSetSumType(selectedItemIndex);
    };
    _sumTypeComboBox->setOnChange(onSumTypeChange);
    addAndMakeVisible(*_sumTypeComboBox);

    // Bubble: Seed Space
    addAndMakeVisible(_seedSpaceBubble);

    // Seed Space dropdown
    _seedSpaceComboBox = make_unique<DeltaComboBox>(_processor, false);
    _seedSpaceComboBox->addItemList(RecurrenceRelation::getSeedSpaceDescription(), 1);
    _seedSpaceComboBox->setToolTip("Seed Space: Frequency uses seeds as-is. Period inverts seeds (1/s) to explore undertone/overtone duality and mirror MOS structures.");
    _seedSpaceComboBox->setSelectedItemIndex(0, NotificationType::dontSendNotification);
    auto onSeedSpaceChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_seedSpaceComboBox->getSelectedItemIndex());
        rrm->uiSetSeedSpace(selectedItemIndex);
    };
    _seedSpaceComboBox->setOnChange(onSeedSpaceChange);
    addAndMakeVisible(*_seedSpaceComboBox);
```

**Add UI helper methods in RecurrenceRelationModel:**

```cpp
// In RecurrenceRelationModel.h (public methods section)
void uiSetSumType(unsigned long index);
void uiSetSeedSpace(unsigned long index);

// In RecurrenceRelationModel.cpp (after uiGetOffset())
void RecurrenceRelationModel::uiSetSumType(unsigned long index)
{
    _recurrenceRelation->setSumTypeByIndex(index);
}

void RecurrenceRelationModel::uiSetSeedSpace(unsigned long index)
{
    _recurrenceRelation->setSeedSpaceByIndex(index);
}
```

**Update paint() method in RecurrenceRelationComponent.cpp (add debug rects around line ~118):**

```cpp
    if (AppExperiments::showDebugBoundingBox) {
        // ... existing code ...
        g.drawRect(_sumTypeBubble.getBounds(), 1);
        g.drawRect(_sumTypeComboBox->getBounds(), 1);
        g.drawRect(_seedSpaceBubble.getBounds(), 1);
        g.drawRect(_seedSpaceComboBox->getBounds(), 1);
    }
```

**Update resized() layout:**

Add two rows after the Index section (after line ~145):

```cpp
    // Sum Type and Seed Space rows (below Index)
    // Layout: two dropdowns arranged horizontally, similar to Index
    auto ss_area = area.removeFromTop(static_cast<int>(WilsonicAppSkin::seedSliderHeight));
    auto ss_left_area = ss_area.withTrimmedRight(static_cast<int>(0.5f * ss_area.getWidth()));
    auto ss_right_area = ss_area.withTrimmedLeft(static_cast<int>(0.5f * ss_area.getWidth()));

    // Sum Type (left half)
    ss_left_area.removeFromTop(15);
    ss_left_area.removeFromBottom(15);
    auto st_bubble_area = ss_left_area.removeFromLeft(bubble_width);
    _sumTypeBubble.setBounds(st_bubble_area);
    ss_left_area.removeFromRight(50);
    _sumTypeComboBox->setBounds(ss_left_area);

    // Seed Space (right half)
    ss_right_area.removeFromTop(15);
    ss_right_area.removeFromBottom(15);
    auto sp_bubble_area = ss_right_area.removeFromLeft(bubble_width);
    _seedSpaceBubble.setBounds(sp_bubble_area);
    ss_right_area.removeFromRight(50);
    _seedSpaceComboBox->setBounds(ss_right_area);
```

**Initialize bubbles in constructor:**

Find where bubbles are initialized (around line ~17), add:

```cpp
    , _sumTypeBubble(BubblePlacement::right, "S", "Sum Type: Choose between arithmetic (a+b) or harmonic (ab/(a+b)) sum operations")
    , _seedSpaceBubble(BubblePlacement::right, "P", "Seed Space: Choose between frequency (seeds as-is) or period (inverted 1/s) seed interpretation")
```

---

## Testing Checklist

1. **Backward compatibility**: With defaults (Arithmetic, Frequency), output is identical to current behavior ✓
2. **Harmonic Fibonacci**: Seeds 1,1 with H[n-1]+H[n-2] in Harmonic mode produces 1, 1, 0.5, 0.333, 0.2, 0.125, ...
3. **Seed inversion**: Seeds 1, 2 in Period mode internally become 1, 0.5
4. **Convergence**: Harmonic mode reports convergent ratio ≈ 0.618 for Fibonacci indices
5. **Edge cases**: Zero or negative seeds don't crash when SeedSpace::Period is selected
6. **UI round-trip**: Changing modes via dropdowns updates scale and log correctly
7. **DAW automation**: Parameters are automatable and recall correctly with project
8. **Preset compatibility**: Loading presets created before this feature defaults to Arithmetic/Frequency
9. **Scala export**: Exported .scl files include mode information in comments
10. **Log format**: `_log` always shows mode in format `[Arithmetic/Harmonic, Frequency/Period]`

---

## Reference Document

For full theoretical background, see:
`/prompts/Wilson_MOS_CPS_Bridge_Research.md` — particularly Part 9: "The Arithmetic/Harmonic Duality in Recurrence Relations"

Original research prompt: `/prompts/RecurrenceRelation_Harmonic_Implementation_Prompt.md`

---

*Implementation prompt generated: December 30, 2025*
*For use with Claude Code implementation session*
