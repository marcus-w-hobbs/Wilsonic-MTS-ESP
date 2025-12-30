# Implementation Plan: Harmonic Sum & Seed Space for RecurrenceRelation

## Overview

Extend the `RecurrenceRelation` class to support two new parameters that create a 2×2 matrix of scale generation modes. This implements a duality discovered between arithmetic and harmonic recurrence operations, extending Erv Wilson's scale design theories into new territory.

**Reviewed by:** Claude Opus 4.5 (December 30, 2025)

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

Combining SumType with SeedSpace yields four distinct scale families:

| SumType | SeedSpace | Character |
|---------|-----------|----------|
| Arithmetic | Frequency | **Classic** (current behavior) |
| Arithmetic | Period | Undertone seeds, overtone growth |
| Harmonic | Frequency | Overtone seeds, undertone growth |
| Harmonic | Period | **Full dual** |

---

## Files to Modify

### Core Implementation
1. `Source/RecurrenceRelation.h` — Add enums, static descriptions, member variables, accessors
2. `Source/RecurrenceRelation.cpp` — Implement accessors, modify `_updateRecurrenceRelation()`

### Model Layer (APVTS Integration)
3. `Source/RecurrenceRelationModel.h` — Add parameter IDs, UI method declarations
4. `Source/RecurrenceRelationModel.cpp` — Add params to `createParams()`, `parameterChanged()`, `getFavoritesParameterIDs()`, UI methods

### UI Layer
5. `Source/RecurrenceRelationComponent.h` — Add combo box members
6. `Source/RecurrenceRelationComponent.cpp` — Add UI widgets, update `resized()`, update `_tuningChangedUpdateUI()`

### Tests
7. `Source/TuningTests+RecurrenceRelation.cpp` — Add test cases for new modes

---

## Step 1: RecurrenceRelation.h

### 1.1 Add Enums (after line 38, inside the class)

```cpp
    // Sum type for recurrence calculation
    enum class SumType
    {
        Arithmetic = 0,  // H[n] = a + b      (proportional triads)
        Harmonic   = 1   // H[n] = ab/(a+b)   (subcontrary triads)
    };

    // Seed space transformation
    enum class SeedSpace
    {
        Frequency = 0,  // Seeds used as-is: s
        Period    = 1   // Seeds inverted: 1/s
    };
```

### 1.2 Add Static Accessors (after line 53, in public section)

```cpp
    // Sum Type: Arithmetic or Harmonic
    static StringArray getSumTypeDescription() { return __sumTypeDescription; }
    static constexpr int getSumTypeDefault() { return 0; } // Arithmetic

    // Seed Space: Frequency or Period
    static StringArray getSeedSpaceDescription() { return __seedSpaceDescription; }
    static constexpr int getSeedSpaceDefault() { return 0; } // Frequency
```

### 1.3 Add Static Member Declarations (after line 74, in private static section)

```cpp
    static StringArray __sumTypeDescription;
    static StringArray __seedSpaceDescription;
```

### 1.4 Add Public Accessors (after line 98, before `private:`)

```cpp
    // Sum Type
    void setSumType(SumType sumType);
    SumType getSumType();
    void setSumTypeByIndex(unsigned long index);
    unsigned long getSumTypeIndex();

    // Seed Space
    void setSeedSpace(SeedSpace seedSpace);
    SeedSpace getSeedSpace();
    void setSeedSpaceByIndex(unsigned long index);
    unsigned long getSeedSpaceIndex();
```

### 1.5 Add Private Member Variables (after line 124, in private members section)

```cpp
    SumType _sumType = SumType::Arithmetic;
    SeedSpace _seedSpace = SeedSpace::Frequency;
```

---

## Step 2: RecurrenceRelation.cpp

### 2.1 Add Static Definitions (after line 136, with other static members)

```cpp
StringArray RecurrenceRelation::__sumTypeDescription = {
    "Arithmetic",
    "Harmonic"
};

StringArray RecurrenceRelation::__seedSpaceDescription = {
    "Frequency",
    "Period"
};
```

### 2.2 Add Accessor Implementations (after line 406, before `_updateRecurrenceRelation`)

```cpp
#pragma mark - Sum Type

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
    _sumType = static_cast<SumType>(index);
    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getSumTypeIndex()
{
    return static_cast<unsigned long>(_sumType);
}

#pragma mark - Seed Space

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
    _seedSpace = static_cast<SeedSpace>(index);
    _updateRecurrenceRelation();
}

unsigned long RecurrenceRelation::getSeedSpaceIndex()
{
    return static_cast<unsigned long>(_seedSpace);
}
```

### 2.3 Modify _updateRecurrenceRelation() — Log Initialization

**Find (around line 453):**
```cpp
    // init _log
    _log = "! H[n] = ";
```

**Replace the entire log initialization block (lines 453-477) with:**
```cpp
    // init _log with sum type indicator
    string sumOp = (_sumType == SumType::Arithmetic) ? " + " : " @ ";  // @ = harmonic sum
    _log = "! H[n] = ";
    if(_coefficients[_i - 1] == Coefficient::_1)
    {
        _log += "H[n-";
    }
    else
    {
        auto c = _coefficients[_i - 1];
        _log += __coefficientsDescriptionMap[c];
        _log += " * H[n-";
    }
    _log += to_string(_i);
    _log += "]";
    _log += sumOp;
    if(_coefficients[_j - 1] == Coefficient::_1)
    {
        _log += "H[n-";
    }
    else
    {
        auto c = _coefficients[_j - 1];
        _log += __coefficientsDescriptionMap[c];
        _log += " * H[n-";
    }
    _log += to_string(_j);
    _log += "]";

    // Add mode info
    _log += (_sumType == SumType::Arithmetic) ? " [Arithmetic" : " [Harmonic";
    _log += (_seedSpace == SeedSpace::Frequency) ? ", Freq Seeds]" : ", Period Seeds]";
    _log += "\n! \n! Integer Sequence, including seeds:\n!  ";
```

### 2.4 Modify _updateRecurrenceRelation() — Seed Planting Phase

**Find (around line 479-508):**
```cpp
    // plant seeds(seeds are the initial conditions so don't use coefficients)
    for(auto j = _j; j > 0; j--) // _j > _i > 0
    {
        auto seed = _seeds.microtoneAtIndex(j - 1);
        raw_ma.addMicrotone(seed);
        _log += seed->getFrequencyValueDescription();
```

**Replace with:**
```cpp
    // plant seeds (seeds are the initial conditions so don't use coefficients)
    // Apply seed space transformation if needed
    for(auto j = _j; j > 0; j--) // _j > _i > 0
    {
        auto seed = _seeds.microtoneAtIndex(j - 1);
        auto seedValue = seed->getFrequencyValue();

        // Transform seed if in Period space (invert)
        if (_seedSpace == SeedSpace::Period && seedValue > 0.f)
        {
            seedValue = 1.f / seedValue;
        }

        // Create transformed seed for the working array
        auto transformedSeed = make_shared<Microtone>(seedValue);
        raw_ma.addMicrotone(transformedSeed);
        _log += transformedSeed->getFrequencyValueDescription();
```

**Note:** The rest of the seed planting loop (filtering, early exit check) remains unchanged.

### 2.5 Modify _updateRecurrenceRelation() — Recurrence Calculation

**Find (around line 523):**
```cpp
        auto const f   = ci * mti->getFrequencyValue() + cj * mtj->getFrequencyValue();
```

**Replace with:**
```cpp
        // Calculate next term based on sum type
        auto const a = ci * mti->getFrequencyValue();
        auto const b = cj * mtj->getFrequencyValue();
        float f;
        if (_sumType == SumType::Arithmetic)
        {
            // Standard arithmetic sum: a + b
            f = a + b;
        }
        else // SumType::Harmonic
        {
            // Harmonic sum: ab/(a+b) — the parallel resistance formula
            auto const sum = a + b;
            f = (sum > 1e-10f) ? (a * b) / sum : 0.f;
        }
```

### 2.6 Modify _updateRecurrenceRelation() — Convergence Reporting

**Find (around line 584-588):**
```cpp
            _log += "\n! \n! Sequence converges to: \n!  F = ";
            _log += to_string(f);
            _log += "\n!  P = ";
            _log += to_string(p);
```

**Replace with:**
```cpp
            _log += "\n! \n! Sequence converges to: \n!  Ratio = ";
            _log += to_string(f);
            if (_sumType == SumType::Harmonic)
            {
                _log += " (1/phi for Fibonacci)";
            }
            _log += "\n!  Generator = ";
            _log += to_string(p);
```

---

## Step 3: RecurrenceRelationModel.h

### 3.1 Add Parameter ID Declarations (after line 91, before `// lifecycle`)

```cpp
    // Sum Type parameter
    static const ParameterID getRecurrenceRelationSumTypeParameterID() {
        return ParameterID("RECURRENCERELATIONSUMTYPE", AppVersion::getVersionHint());
    }
    static const String getRecurrenceRelationSumTypeParameterName() {
        return "Recurrence Relation|Sum Type";
    }

    // Seed Space parameter
    static const ParameterID getRecurrenceRelationSeedSpaceParameterID() {
        return ParameterID("RECURRENCERELATIONSEEDSPACE", AppVersion::getVersionHint());
    }
    static const String getRecurrenceRelationSeedSpaceParameterName() {
        return "Recurrence Relation|Seed Space";
    }
```

### 3.2 Add UI Method Declarations (after line 125, before `protected:`)

```cpp
    // Sum Type UI methods
    void uiSetSumType(unsigned long index);
    unsigned long uiGetSumType();

    // Seed Space UI methods
    void uiSetSeedSpace(unsigned long index);
    unsigned long uiGetSeedSpace();
```

---

## Step 4: RecurrenceRelationModel.cpp

### 4.1 Add Parameters to createParams() (after line 297, before the closing parenthesis)

```cpp
     // Sum Type
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationSumTypeParameterID(),
      getRecurrenceRelationSumTypeParameterName(),
      RecurrenceRelation::getSumTypeDescription(),
      RecurrenceRelation::getSumTypeDefault()
      ),

     // Seed Space
     make_unique<AudioParameterChoice>
     (getRecurrenceRelationSeedSpaceParameterID(),
      getRecurrenceRelationSeedSpaceParameterName(),
      RecurrenceRelation::getSeedSpaceDescription(),
      RecurrenceRelation::getSeedSpaceDefault()
      )
```

### 4.2 Add to getFavoritesParameterIDs() (after line 344, before the closing parenthesis)

```cpp
                       getRecurrenceRelationSumTypeParameterID().getParamID(),
                       getRecurrenceRelationSeedSpaceParameterID().getParamID()
```

### 4.3 Add to parameterChanged() (after line 383, before `// Seeds`)

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

### 4.4 Add UI Method Implementations (after line 510, at end of file)

```cpp
#pragma mark - Sum Type UI

void RecurrenceRelationModel::uiSetSumType(unsigned long value) {
    jassert(value < 2);
    auto key = getRecurrenceRelationSumTypeParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(static_cast<float>(value));
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetSumType() {
    auto& param = *_apvts->getRawParameterValue(getRecurrenceRelationSumTypeParameterID().getParamID());
    return static_cast<unsigned long>(param.load());
}

#pragma mark - Seed Space UI

void RecurrenceRelationModel::uiSetSeedSpace(unsigned long value) {
    jassert(value < 2);
    auto key = getRecurrenceRelationSeedSpaceParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(static_cast<float>(value));
    param->setValueNotifyingHost(value01);
}

unsigned long RecurrenceRelationModel::uiGetSeedSpace() {
    auto& param = *_apvts->getRawParameterValue(getRecurrenceRelationSeedSpaceParameterID().getParamID());
    return static_cast<unsigned long>(param.load());
}
```

---

## Step 5: RecurrenceRelationComponent.h

### 5.1 Add Private Members (after line 58, with other members)

```cpp
    BubbleDrawable _sumTypeBubble;
    unique_ptr<DeltaComboBox> _sumTypeComboBox;
    BubbleDrawable _seedSpaceBubble;
    unique_ptr<DeltaComboBox> _seedSpaceComboBox;
```

---

## Step 6: RecurrenceRelationComponent.cpp

### 6.1 Update Constructor Initializer List (around line 17)

**Find:**
```cpp
, _numTermsBubble(BubblePlacement::left, "T", "The number of terms in the final scale, i.e., the number of notes per octave")
```

**Add after:**
```cpp
, _sumTypeBubble(BubblePlacement::left, "A/H", "Sum Type: Arithmetic (a+b) or Harmonic (ab/(a+b))")
, _seedSpaceBubble(BubblePlacement::left, "F/P", "Seed Space: Frequency (as-is) or Period (inverted)")
```

### 6.2 Add UI Widget Creation (after line 68, before `// Pitch Wheel`)

```cpp
    // Bubble: Sum Type
    addAndMakeVisible(_sumTypeBubble);

    // Sum Type ComboBox
    _sumTypeComboBox = make_unique<DeltaComboBox>(_processor, false);
    _sumTypeComboBox->addItemList(RecurrenceRelation::getSumTypeDescription(), 1);
    _sumTypeComboBox->setToolTip("Sum Type: Arithmetic or Harmonic");
    _sumTypeComboBox->setSelectedItemIndex(static_cast<int>(rrm->uiGetSumType()), NotificationType::dontSendNotification);
    auto onSumTypeChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_sumTypeComboBox->getSelectedItemIndex());
        rrm->uiSetSumType(selectedItemIndex);
    };
    _sumTypeComboBox->setOnChange(onSumTypeChange);
    addAndMakeVisible(*_sumTypeComboBox);

    // Bubble: Seed Space
    addAndMakeVisible(_seedSpaceBubble);

    // Seed Space ComboBox
    _seedSpaceComboBox = make_unique<DeltaComboBox>(_processor, false);
    _seedSpaceComboBox->addItemList(RecurrenceRelation::getSeedSpaceDescription(), 1);
    _seedSpaceComboBox->setToolTip("Seed Space: Frequency or Period");
    _seedSpaceComboBox->setSelectedItemIndex(static_cast<int>(rrm->uiGetSeedSpace()), NotificationType::dontSendNotification);
    auto onSeedSpaceChange = [rrm, this]() {
        auto const selectedItemIndex = static_cast<unsigned long>(_seedSpaceComboBox->getSelectedItemIndex());
        rrm->uiSetSeedSpace(selectedItemIndex);
    };
    _seedSpaceComboBox->setOnChange(onSeedSpaceChange);
    addAndMakeVisible(*_seedSpaceComboBox);
```

### 6.3 Update resized() Method

**Find the section that handles `to_area` (around lines 132-157).**

This section currently divides the top area into thirds for Index, Terms, and Offset. We need to expand to five sections or add a second row.

**Option A: Add a second row for the new controls**

**After line 157 (after offset layout), add:**
```cpp
    // y margin
    area.removeFromTop(margin);

    // Sum Type and Seed Space row
    auto mode_area = area.removeFromTop(static_cast<int>(WilsonicAppSkin::comboBoxHeight));
    auto mode_left_area = mode_area.withTrimmedRight(static_cast<int>(0.5f * mode_area.getWidth()));
    auto mode_right_area = mode_area.withTrimmedLeft(static_cast<int>(0.5f * mode_area.getWidth()));

    // Sum Type (left)
    auto stba = mode_left_area.removeFromLeft(bubble_width);
    _sumTypeBubble.setBounds(stba);
    mode_left_area.removeFromRight(margin);
    _sumTypeComboBox->setBounds(mode_left_area);

    // Seed Space (right)
    auto ssba = mode_right_area.removeFromLeft(bubble_width);
    _seedSpaceBubble.setBounds(ssba);
    mode_right_area.removeFromRight(margin);
    _seedSpaceComboBox->setBounds(mode_right_area);
```

### 6.4 Update _tuningChangedUpdateUI() (after line 226, before `// draw`)

```cpp
    // Update Sum Type and Seed Space combo boxes
    _sumTypeComboBox->setSelectedItemIndex(
        static_cast<int>(rrm->uiGetSumType()),
        NotificationType::dontSendNotification);
    _seedSpaceComboBox->setSelectedItemIndex(
        static_cast<int>(rrm->uiGetSeedSpace()),
        NotificationType::dontSendNotification);
```

### 6.5 Update paint() Debug Bounds (optional, after line 119)

```cpp
        g.drawRect(_sumTypeBubble.getBounds(), 1);
        g.drawRect(_sumTypeComboBox->getBounds(), 1);
        g.drawRect(_seedSpaceBubble.getBounds(), 1);
        g.drawRect(_seedSpaceComboBox->getBounds(), 1);
```

---

## Step 7: Unit Tests

### Add to TuningTests+RecurrenceRelation.cpp

```cpp
#pragma mark - Harmonic Sum Tests

void TuningTests::testRecurrenceRelationHarmonicFibonacci()
{
    // Test: Harmonic Fibonacci with seeds 1,1 should produce 1, 1, 0.5, 0.333..., 0.2, ...
    auto rr = make_shared<RecurrenceRelation>();
    rr->setSeeds(1, 1, 1, 1, 1, 1, 1, 1, 1);
    rr->setIndices(0); // H[n-1] + H[n-2]
    rr->setSumType(RecurrenceRelation::SumType::Harmonic);
    rr->setSeedSpace(RecurrenceRelation::SeedSpace::Frequency);
    rr->setNumberOfTerms(7);

    auto tuning = rr->getTuning();
    // Verify convergence ratio is approximately 1/phi = 0.618
    auto log = rr->getLog();
    jassert(log.find("0.618") != string::npos || log.find("0.617") != string::npos);
}

void TuningTests::testRecurrenceRelationPeriodSeeds()
{
    // Test: Period space should invert seeds
    auto rr = make_shared<RecurrenceRelation>();
    rr->setSeeds(1, 2, 1, 1, 1, 1, 1, 1, 1);
    rr->setIndices(0); // H[n-1] + H[n-2]
    rr->setSumType(RecurrenceRelation::SumType::Arithmetic);
    rr->setSeedSpace(RecurrenceRelation::SeedSpace::Period);
    rr->setNumberOfTerms(5);

    // With Period seeds, 1 and 2 become 1 and 0.5
    // So sequence starts: 1, 0.5, 1.5, 2, 3.5, ...
    auto log = rr->getLog();
    jassert(log.find("0.5") != string::npos);
}

void TuningTests::testRecurrenceRelationBackwardCompatibility()
{
    // Test: Default mode (Arithmetic, Frequency) should match original behavior
    auto rr_new = make_shared<RecurrenceRelation>();
    auto rr_orig = make_shared<RecurrenceRelation>();

    rr_new->setSeeds(1, 1, 1, 1, 1, 1, 1, 1, 1);
    rr_orig->setSeeds(1, 1, 1, 1, 1, 1, 1, 1, 1);

    rr_new->setIndices(0);
    rr_orig->setIndices(0);

    rr_new->setNumberOfTerms(7);
    rr_orig->setNumberOfTerms(7);

    // New should default to Arithmetic/Frequency
    jassert(rr_new->getSumType() == RecurrenceRelation::SumType::Arithmetic);
    jassert(rr_new->getSeedSpace() == RecurrenceRelation::SeedSpace::Frequency);

    // Output should be identical
    auto ma_new = rr_new->getMicrotoneArray();
    auto ma_orig = rr_orig->getMicrotoneArray();
    jassert(ma_new.count() == ma_orig.count());
}
```

---

## Testing Checklist

### Functional Tests

- [ ] **Backward compatibility:** With defaults (Arithmetic, Frequency), output identical to current behavior
- [ ] **Harmonic Fibonacci:** Seeds 1,1 with H[n-1]+H[n-2] in Harmonic mode produces convergence ratio ≈ 0.618
- [ ] **Seed inversion:** Seeds 1, 2 in Period mode internally become 1, 0.5
- [ ] **Edge cases:** Zero or negative seeds don't crash in Period mode
- [ ] **All four combinations:** Each of the 2×2 matrix modes produces distinct output

### UI Tests

- [ ] **Combo boxes appear:** Sum Type and Seed Space dropdowns visible in UI
- [ ] **Selection persists:** Changing selection updates the scale
- [ ] **Log updates:** Text editor shows correct mode in log header
- [ ] **Pitch wheel updates:** Visual representation changes with mode

### DAW Integration Tests

- [ ] **Automation:** Parameters automatable in DAW
- [ ] **Preset save/load:** New parameters saved and restored correctly
- [ ] **Project recall:** Closing and reopening project preserves settings

---

## Implementation Order

1. **RecurrenceRelation.h** — Add all declarations
2. **RecurrenceRelation.cpp** — Add static arrays, accessors, modify `_updateRecurrenceRelation()`
3. **Build and test** — Verify core logic works via unit tests
4. **RecurrenceRelationModel.h** — Add parameter IDs and UI method declarations
5. **RecurrenceRelationModel.cpp** — Add params, handlers, UI methods
6. **Build and test** — Verify parameters work via APVTS
7. **RecurrenceRelationComponent.h** — Add UI members
8. **RecurrenceRelationComponent.cpp** — Add widgets, layout, update handlers
9. **Build and test** — Full integration test
10. **TuningTests** — Add and run unit tests

---

## Reference Document

For full theoretical background, see:
`/prompts/Wilson_MOS_CPS_Bridge_Research.md` — particularly Part 9: "The Arithmetic/Harmonic Duality in Recurrence Relations"

---

*Plan revised: December 30, 2025*
*Reviewed by: Claude Opus 4.5*
*Original draft by: Claude Haiku*
*For use with Claude Code implementation session*
