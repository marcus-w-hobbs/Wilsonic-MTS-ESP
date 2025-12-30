# Implementation Prompt: Harmonic Sum & Seed Space for RecurrenceRelation

## Overview

Extend the `RecurrenceRelation` class to support two new parameters that create a 2×2 matrix of scale generation modes. This implements a duality discovered between arithmetic and harmonic recurrence operations, extending Erv Wilson's scale design theories into new territory.

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

## Functional Requirements

### FR1: SumType Parameter

Add a parameter to switch between arithmetic and harmonic sum operations.

**Behavior:**
- `Arithmetic`: Current behavior — `f = a + b`
- `Harmonic`: New behavior — `f = (a * b) / (a + b)`

**Constraints:**
- Default to `Arithmetic` to preserve backward compatibility
- Must trigger `_updateRecurrenceRelation()` on change
- Must be exposed for DAW automation (like existing parameters)

### FR2: SeedSpace Parameter

Add a parameter to control whether seeds are used as-is or inverted.

**Behavior:**
- `Frequency`: Use seeds as-is (current behavior)
- `Period`: Invert seeds (use 1/seed)

**Constraints:**
- Default to `Frequency` to preserve backward compatibility
- Seed inversion happens ONLY during the seed-planting phase, NOT during recurrence iteration
- Must handle edge case: if seed ≤ 0, skip inversion (avoid division by zero)
- Must trigger `_updateRecurrenceRelation()` on change
- Must be exposed for DAW automation

### FR3: Logging

Update the `_log` string to reflect the current mode.

**Format suggestion:**
```
! H[n] = H[n-1] + H[n-2] [Arithmetic, Frequency Seeds]
```
or
```
! H[n] = H[n-1] ⊕ H[n-2] [Harmonic, Period Seeds]
```

(The ⊕ symbol represents harmonic sum, but ASCII fallback is fine)

### FR4: Convergence Reporting

The convergence calculation at the end of `_updateRecurrenceRelation()` should still work correctly. Harmonic sequences converge to the reciprocal ratio, which is valid.

---

## Product Requirements

### PR1: UI Integration

The two new parameters should appear in the RecurrenceRelation UI, likely as:
- A dropdown or toggle for SumType: "Arithmetic" / "Harmonic"
- A dropdown or toggle for SeedSpace: "Frequency" / "Period"

### PR2: Preset Compatibility

Existing presets should load with default values (Arithmetic, Frequency) to maintain backward compatibility.

### PR3: Scala Export

The Scala comments (via `scalaComments()` which returns `getLog()`) should accurately reflect the mode used to generate the scale.

---

## Implementation Code Snippets

### Header Additions (RecurrenceRelation.h)

```cpp
// New enums
enum class SumType
{
    Arithmetic,  // H[n] = a + b      → proportional triads
    Harmonic     // H[n] = ab/(a+b)   → subcontrary triads
};

enum class SeedSpace
{
    Frequency,  // Seeds used as-is: s
    Period      // Seeds inverted: 1/s
};

// New static description arrays (for UI/automation)
static StringArray __sumTypeDescription;
static StringArray __seedSpaceDescription;

// New member variables (private)
private:
    SumType _sumType = SumType::Arithmetic;
    SeedSpace _seedSpace = SeedSpace::Frequency;

// New accessors (public)
public:
    void setSumType(SumType sumType);
    SumType getSumType();
    void setSumTypeByIndex(unsigned long index);  // For DAW automation
    
    void setSeedSpace(SeedSpace seedSpace);
    SeedSpace getSeedSpace();
    void setSeedSpaceByIndex(unsigned long index);  // For DAW automation
```

### Static Descriptions (RecurrenceRelation.cpp)

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

### Accessor Implementations

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

### Modified _updateRecurrenceRelation() — Seed Planting Phase

Find the seed-planting loop and modify to apply seed space transformation:

```cpp
// plant seeds (seeds are the initial conditions so don't use coefficients)
for (auto j = _j; j > 0; j--) // _j > _i > 0
{
    auto seed = _seeds.microtoneAtIndex(j - 1);
    auto seedValue = seed->getFrequencyValue();
    
    // Transform seed if in Period space
    if (_seedSpace == SeedSpace::Period && seedValue > 0.f)
    {
        seedValue = 1.f / seedValue;
    }
    
    auto transformedSeed = make_shared<Microtone>(seedValue);
    raw_ma.addMicrotone(transformedSeed);
    _log += transformedSeed->getFrequencyValueDescription();
    
    // ... rest of existing loop (filtering, etc.)
}
```

### Modified _updateRecurrenceRelation() — Recurrence Calculation

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

### Modified _updateRecurrenceRelation() — Log String

Update the log initialization to include mode information:

```cpp
// After building the recurrence description, add mode info:
_log += (_sumType == SumType::Arithmetic) ? " [Arithmetic" : " [Harmonic";
_log += (_seedSpace == SeedSpace::Frequency) ? ", Frequency Seeds]" : ", Period Seeds]";
```

---

## Testing Checklist

1. **Backward compatibility:** With defaults (Arithmetic, Frequency), output should be identical to current behavior
2. **Harmonic Fibonacci:** Seeds 1,1 with H[n-1]+H[n-2] in Harmonic mode should produce 1, 1, 1/2, 1/3, 1/5, 1/8, 1/13...
3. **Seed inversion:** Seeds 1, 2 in Period mode should become 1, 0.5 internally
4. **Convergence:** Harmonic mode should report convergent ratio ≈ 0.618 for Fibonacci indices
5. **Edge cases:** Zero or negative seeds should not crash when SeedSpace::Period is selected
6. **UI round-trip:** Changing modes via UI should update scale and log correctly
7. **DAW automation:** Parameters should be automatable and recall correctly with project

---

## Reference Document

For full theoretical background, see:
`/Research/Wilson_MOS_CPS_Bridge_Research.md` — particularly Part 9: "The Arithmetic/Harmonic Duality in Recurrence Relations"

---

*Prompt generated: December 30, 2025*
*For use with Claude Code implementation session*
