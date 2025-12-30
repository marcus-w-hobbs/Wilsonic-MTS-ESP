# Wilson MOS/CPS Bridge: Research Notes

**Date:** December 3, 2025  
**Participants:** Marcus Hobbs, Claude  
**Context:** Extracted from extended conversation exploring Erv Wilson's scale design theories, the melody/harmony problem, and potential bridges between MOS and CPS architectures.

---

## Executive Summary

This document captures research-grade insights from collaborative sessions exploring:

1. The fundamental tension between melodic and harmonic scale design
2. Wilson's solution via optimized MOS generators that produce proportional triads
3. The algebraic structure underlying Wilson's "hot spot" generators
4. A novel proposal for bridging CPS (harmonic) and MOS (melodic) systems via recurrence relation seeding
5. **[New: Dec 30, 2025]** The arithmetic/harmonic duality in recurrence relations—a structural switch between proportional and subcontrary triads

**Key Thesis:** Scale design systems that offer BOTH melody AND harmony represent Wilson's core contribution to microtonality. MOS provides melody; CPS provides harmony. The bridge between them is the next frontier.

**Key Discovery:** Recurrence relations can operate in either arithmetic (frequency) or harmonic (period) space. The arithmetic sum yields proportional triads; the harmonic sum yields subcontrary triads. Their generators are reciprocals, producing mirror MOS structures. Combined with a seed-space parameter (frequency vs. period), this creates a 2×2 experimental matrix yielding four distinct scale families from identical seeds and indices.

---

## Part 1: The Melody/Harmony Problem

### The Fundamental Tension

Scale design faces an inherent conflict:

- **Melodic resources** require stepwise patterns, voice leading, scalar continuity - the *horizontal* dimension of music
- **Harmonic resources** require chord relationships, consonance, reinforcing overtones - the *vertical* dimension

Most scale systems optimize for one at the expense of the other.

### Two Architectural Approaches

**MOS (Moment of Symmetry):**
- Construction: Iterate a generator interval, fold into period
- Produces: Two-interval patterns (Large, small), nested recursive structure
- Guarantees: Stepwise motion always available, natural voice leading
- Melody: **Native**
- Harmony: **Accidental** (requires optimized generator)

**CPS (Combination Product Sets):**
- Construction: Take k-subsets of n harmonic factors, multiply, octave-reduce
- Produces: Rich harmonic lattice where every note shares factors with others
- Guarantees: Harmonic relationships by construction
- Melody: **Absent** (no privileged stepwise paths)
- Harmony: **Native**

### The Critical Observation

Marcus Hobbs, after decades of working with CPS:

> "I never found a melody amongst them all."

This is data, not failure. CPS architecture may be **fundamentally non-melodic**. The combinatorial construction doesn't accidentally produce stepwise structure - ever.

---

## Part 2: Wilson's Proportional Triad Discovery

### The Space Problem

MOS is constructed in **logarithmic pitch space** (generator iteration), but harmonic reinforcement happens in **linear frequency space** (sum/difference tones). These spaces don't naturally align.

### Wilson's Insight

Find generators where arithmetic and geometric structures *accidentally* coincide. For such generators, the MOS scale contains triads where:

- **Proportional (major):** Middle note is approximately the arithmetic mean of outer notes: `(a + b) / 2`
- **Subcontrary (minor):** Middle note is approximately the harmonic mean of outer notes: `2ab / (a + b)`

When these conditions are met, sum and difference tones land *on other scale degrees*, creating harmonic reinforcement rather than interference.

### Implementation in Wilsonic

The `TuningImp::_analyzeProportionalTriads()` function (in `TuningImp.cpp`) implements this analysis:

```cpp
auto const major = (imf + jmf) / 2;           // Arithmetic mean
auto const minor = 2 * (imf * jmf) / (imf + jmf);  // Harmonic mean

// Search for scale degrees within tolerance of these means
if (fabsf(major - kmf) < tolerance) {
    // Found a proportional (major) triad
}
if (fabsf(minor - kmf) < tolerance) {
    // Found a subcontrary (minor) triad
}
```

The tolerance threshold (currently 0.0005 in unit pitch space) represents perceptual threshold - human pitch discrimination is roughly 5-10 cents.

### Mathematical Relationships

```
Arithmetic mean (proportional/major):  (a + b) / 2
Geometric mean (neutral):              sqrt(a * b)
Harmonic mean (subcontrary/minor):     2ab / (a + b)

Relationship: harmonic < geometric < arithmetic (for a != b)
```

The geometric mean falls between arithmetic and harmonic, so "neutral" triads come "for free" if you have good major and minor triads.

---

## Part 3: Wilson's "Hot Spot" Generators

### The Algebraic Structure

Wilson's optimal generators aren't arbitrary - they're solutions to self-referential algebraic equations.

**Example: Generator 0.238186...**

From Wilson's handwritten notes (27 Jul 97, P.21a):

```
G = (4 - 2G)^(1/3) = 1.17950902460

Log2(G) = 0.23818645689
```

This satisfies: G^3 + 2G - 4 = 0

Equivalent form: G = (2 + G^2)^(1/3)

**Continued fraction:** [0; 4, 5, 24, 1, 2, 74, 1, 3, 3, ...]

**MOS sequence (denominators):** 1, 4, 5, 21, 26, 47, 73, ...

**Produces triads like:** 14:17:20, 32:39:46, 9:11:13

**Example: Generator 0.418934...**

From Wilson's notes (16 Jul 97, P.4a):

```
L = fourth_root((L^3 + 4)/2) = 1.3369394609

Log2 = 0.418934662571

Similar to 1/5 comma meantone
```

**MOS sequence:** 1/1, 1/2, 1/3, 2/5, 3/7, **5/12**, 8/19, 13/31...

Note: Passes through 5/12 (pentatonic) and 7/12 (diatonic) - the familiar landmarks.

### Wilson's Methodology

Based on analysis of his papers:

1. **Source:** Sloane's integer sequences (OEIS), particularly recurrence relations
2. **Process:** Identify recurrences with interesting convergent behavior
3. **Skill:** "Integer log2 mods" - seeing sum/difference tone patterns in sequences
4. **Output:** Generators where MOS structure produces proportional triads

Wilson was essentially performing optimization search by hand, using number-theoretic intuition to identify algebraically special generators.

---

## Part 4: The Optimization Landscape

### Current Implementation (Binary)

```cpp
if (fabsf(major - kmf) < tolerance)  // Binary: in or out
```

### Proposed Enhancement (Continuous)

```cpp
float triad_quality = 1.0f / (fabsf(major - kmf) + epsilon);  // Continuous: closer = better
```

Sum quality over all triads for a smooth landscape instead of step function.

### Visualization Concept

**Axes:**
- X: Generator (0 to 1)
- Y: Level (0 to 9)

**Value:** Triad quality sum at each point

**Expected features:**
- Dead zones (most of the space)
- Hot spots (Wilson's generators as peaks)
- Ridges (families of related generators)

### Research Questions

1. Do optimal generators cluster around specific algebraic families?
2. How does the landscape change with tolerance parameter?
3. Is there a closed-form relationship between CF expansion and triad density?

---

## Part 5: The CPS/MOS Bridge Proposal

### The Two-Layer Architecture

Rather than seeking a single unified scale, treat melody and harmony as cooperating systems:

1. **CPS defines harmonic "gravity wells"** - where you want to land (chord tones)
2. **MOS defines local paths** - how you move between gravity wells (melodic connections)
3. **The MOS is local, not global** - different paths for different harmonic motions

### The Seeding Insight

MOS generators have associated recurrence relations:

```
Fibonacci: A_n = A_{n-1} + A_{n-2}       -> phi generator
Pell:      A_n = 2*A_{n-1} + A_{n-2}     -> silver ratio
Wilson:    A_n = 4*A_{n-4} + A_{n-1}     -> 0.418... generator
```

**Key property:** Recurrence relations converge to their generator (attractor), but **seeds determine initial tones**.

### The Recipe

1. Pick a CPS you love harmonically (e.g., Eikosany = 20 tones)
2. Pick an MOS cardinality you love melodically (e.g., 7 tones for diatonic feel)
3. Find a generator/level combination where level accommodates your seed count
4. **Use CPS pitches as seeds** for the recurrence relation
5. Let recurrence run - it converges toward MOS structure
6. Extract scale at target level

### What This Achieves

- **Harmonic DNA** comes from CPS (seeds)
- **Melodic structure** comes from MOS (attractor)
- **Level controls blend:** Low = more CPS flavor, high = more MOS flavor

### Critical Clarification

We are NOT claiming CPS and MOS are secretly the same mathematics. We are NOT deriving one from the other.

We are saying: Humans need melody AND harmony. These systems each solve one brilliantly. We graft them together via the seeding mechanism - a pragmatic bridge, not a theoretical unification.

### Implementation Requirements

1. **Generator to Recurrence translator:** Given g, derive recurrence coefficients (Erv could do this by reading continued fractions; needs formalization)

2. **Seed injector:** Accept arbitrary pitches as initial conditions

3. **Level scrubber:** Interactive control over recurrence depth

4. **Overlay visualization:** CPS lattice with MOS-covered notes highlighted

---

## Part 6: Relevant Code Architecture

### Core Files

- `Brun.cpp/h` - MOS generation via Brun algorithm
- `TuningImp.cpp` - Base tuning class with `_analyzeProportionalTriads()`
- `CPS.cpp/h` - Combination Product Set implementation
- `RecurrenceRelation.cpp/h` - Recurrence relation tuning (needs enhancement for arbitrary seeding)

### Key Functions

**MOS Generation:**
```cpp
Brun::brunArray(level, generator)  // Generate MOS at given level
Brun::brun(level, generator)       // Get MOS cardinality info
```

**Triad Analysis:**
```cpp
TuningImp::_analyzeProportionalTriads()  // Find major/minor triads
TuningImp::getProportionalTriads()       // Access results
TuningImp::getSubcontraryTriads()
```

**Gral Keyboard:**
```cpp
Brun::_mapGralToBrunMicrotones()  // Map MOS to isomorphic keyboard
```

---

## Part 7: Wilson's Original Sources

### Documents Referenced

1. **"Study for Difference-Tone Continuum"** (1993)
   - Horogram showing pitch evolution across generator space
   - Key equation: `(A+B)/2 = sqrt(B/A)` (where arithmetic mean equals geometric mean)

2. **"Proportional Triads in MOS"** (13 Jul 1997)
   - After Callum Johnston's bagpipe scale
   - Shows L/s patterns with triad brackets
   - Explicitly marks arithmetic and harmonic mean positions

3. **"Secondary Series"** (16 Aug 1997, P.4a-4b)
   - Generator derived from `L = fourth_root((L^3+4)/2)`
   - Shows convergence iteration
   - Notes similarity to 1/5 comma meantone

4. **"On Complementary Proportional Triads"** (1995)
   - Two generators: Meta-Mavila and Meta-Meantone
   - Different recurrence relations producing complementary triads
   - 7-tone system diagram

### Archive Location

Wilson Archive PDFs (image-based, require manual transcription for full extraction)

---

## Part 8: Research Directions

### Immediate (Implementable Now)

1. **Continuous triad quality function** - Replace binary threshold with continuous error measure
2. **Generator landscape visualization** - Heatmap of triad quality vs generator vs level
3. **CPS pitch extraction** - Export CPS as frequency list for seeding experiments

### Medium-Term (Requires New Code)

4. **Recurrence relation seeding** - Parameterize `RecurrenceRelation` class to accept arbitrary initial conditions
5. **Generator to recurrence derivation** - Formalize Erv's CF-reading technique
6. **Real-time CPS to MOS suggestions** - Given current/target CPS tones, suggest connecting MOS fragments

### Long-Term (Research Questions)

7. **Algebraic classification of hot-spot generators** - Are they all noble numbers? Metallic means?
8. **Perceptual validation** - Do computed "high quality" triads correlate with listener preference?
9. **Cross-cultural analysis** - Do traditional microtonal systems cluster near Wilson's generators?

---

## Part 9: The Arithmetic/Harmonic Duality in Recurrence Relations

**Date:** December 30, 2025  
**Discovery:** Marcus Hobbs and Claude

### The Origin: Revoicing Recurrence Sequences

The standard recurrence relation produces a sequence: a, b, a+b, ...

When we "revoice" the sum term by dropping an octave (÷2), we get:

```
a, (a+b)/2, b
```

The middle term is the **arithmetic mean** of the outer terms. This is precisely the condition for a **proportional triad** (see Part 2: Wilson's Proportional Triad Discovery).

### The Question

Can we do something similar for **subcontrary triads**, where the middle term is the **harmonic mean**?

```
Harmonic mean = 2ab / (a + b)
```

### The Answer: Work in Reciprocal Space

The key insight: arithmetic and harmonic means are **duals under reciprocation**.

1. Take reciprocals of a and b: 1/a, 1/b
2. Apply additive recurrence: 1/a + 1/b = (a+b)/ab
3. Take reciprocal back: ab/(a+b)
4. This is **half** the harmonic mean
5. Revoice **up** (×2) instead of down: 2ab/(a+b) = harmonic mean ✓

So the dual operations are:

| Triad Type | Space | Recurrence | Revoicing |
|------------|-------|------------|----------|
| Proportional (major) | Frequency | a + b | Drop octave (÷2) |
| Subcontrary (minor) | Period (1/f) | ab/(a+b) | Raise octave (×2) |

### The Harmonic Sum

Define the **harmonic sum** of a and b:

```
a ⊕ b = ab / (a + b)
```

This is also called the "parallel sum" (from electrical engineering: resistors in parallel).

The harmonic sum is to subcontrary triads what arithmetic sum is to proportional triads.

### Convergence Analysis

**Arithmetic Fibonacci:**

```
H[n] = H[n-1] + H[n-2]
Characteristic equation: r² = r + 1
Solution: r = φ = (1 + √5)/2 ≈ 1.618
```

**Harmonic Fibonacci:**

```
H[n] = H[n-1] · H[n-2] / (H[n-1] + H[n-2])
```

Let consecutive ratio converge to r. Normalize so H[n-1] = 1, then H[n-2] = 1/r:

```
H[n] = 1 · (1/r) / (1 + 1/r)
     = (1/r) / ((r+1)/r)
     = 1/(r+1)
```

For convergence, H[n]/H[n-1] = r, so:

```
r = 1/(r+1)
r² + r = 1
r² + r - 1 = 0
```

Solution: **r = (-1 + √5)/2 ≈ 0.618 = 1/φ**

### The Reciprocal Relationship

**The arithmetic and harmonic generators are reciprocals of each other.**

Numerical verification with seeds = 1, 1:

| n | Arithmetic | Harmonic |
|---|------------|----------|
| 0 | 1 | 1 |
| 1 | 1 | 1 |
| 2 | 2 | 1/2 |
| 3 | 3 | 1/3 |
| 4 | 5 | 1/5 |
| 5 | 8 | 1/8 |
| 6 | 13 | 1/13 |

The harmonic Fibonacci sequence produces **1/Fₙ** — reciprocals of Fibonacci numbers.

### Generalization to All Recurrences

For any recurrence H[n] = H[n-i] + H[n-j]:

| Sum Type | Characteristic Equation | Generator |
|----------|------------------------|----------|
| Arithmetic | rʲ = rʲ⁻ⁱ + 1 | r |
| Harmonic | rⁱ + rʲ = 1 | 1/r |

These are **dual equations** with **reciprocal solutions**.

### Generator Pairs

| Recurrence | Arith. ratio | Harm. ratio | Arith. gen | Harm. gen |
|------------|--------------|-------------|------------|-----------|
| H[n-1]+H[n-2] | φ ≈ 1.618 | 1/φ ≈ 0.618 | log₂(φ) ≈ 0.694 | **0.306** |
| H[n-1]+H[n-3] | ≈ 1.466 | ≈ 0.682 | ≈ 0.552 | **0.448** |
| H[n-1]+H[n-4] | ≈ 1.380 | ≈ 0.725 | ≈ 0.465 | **0.535** |

The harmonic generator is the **octave complement** (1 - g) of the arithmetic generator.

### Musical Consequence: Mirror MOS

Because the generators are octave complements, the resulting MOS scales have **swapped L and s intervals**.

If arithmetic gives you 5L+2s (major scale pattern), harmonic gives you 5s+2L (the "anti-diatonic" where small steps become large).

This is not just a different scale — it's the **structural mirror**.

### Triad Distribution

| Sum Type | Native Triads | Generator | MOS Pattern |
|----------|---------------|-----------|-------------|
| Arithmetic | Proportional (major) | g | L/s standard |
| Harmonic | Subcontrary (minor) | 1-g | s/L inverted |

Flipping between arithmetic and harmonic sum types gives you:
1. Different triad types (proportional vs. subcontrary)
2. Mirror MOS structure (L↔s swap)
3. Reciprocally related convergent ratios

### Implementation

The `RecurrenceRelation` class in Wilsonic can be extended with a `SumType` enum:

```cpp
enum class SumType
{
    Arithmetic,  // H[n] = a + b      → proportional triads
    Harmonic     // H[n] = ab/(a+b)   → subcontrary triads
};
```

The core calculation in `_updateRecurrenceRelation()` becomes:

```cpp
auto const a = ci * mti->getFrequencyValue();
auto const b = cj * mtj->getFrequencyValue();
float f;
if (_sumType == SumType::Arithmetic)
{
    f = a + b;           // Standard: yields proportional triads
}
else // SumType::Harmonic
{
    f = (a * b) / (a + b);  // Reciprocal space: yields subcontrary triads
}
```

### The Seed Space Question

A subtle question arises: should seeds be treated the same way in both modes?

In the current arithmetic implementation, seeds are simply initial conditions—they aren't subjected to coefficients or the recurrence operation itself. But if we're truly working in reciprocal space for harmonic mode, should we also *invert the seeds*?

**Two valid approaches:**

1. **Same seeds (Frequency space):** If I set seed = 3/2 because I want a fifth, I probably want a fifth in both modes. The operation changes, but my musical intent for the starting pitches doesn't.

2. **Inverted seeds (Period space):** For complete mathematical duality, transform everything. The overtone series (1, 2, 3, 4, 5...) becomes the undertone series (1, 1/2, 1/3, 1/4, 1/5...). These are musical duals—major vs minor in JI terms.

Both are musically valid and produce different results.

### The 2×2 Experimental Matrix

This leads to a second parameter:

```cpp
enum class SeedSpace
{
    Frequency,  // Seeds used as-is: s
    Period      // Seeds inverted: 1/s
};
```

Combining `SumType` and `SeedSpace` yields four distinct scale families from the same indices and seed values:

| SumType | SeedSpace | Character |
|---------|-----------|----------|
| Arithmetic | Frequency | **Classic Erv** (current behavior) |
| Arithmetic | Period | Undertone seeds, overtone growth |
| Harmonic | Frequency | Overtone seeds, undertone growth |
| Harmonic | Period | **Full dual** (undertone everything) |

**Prediction:** The "Full dual" (Harmonic + Period) should be the complete structural mirror of the Classic case.

### Seed Transformation Implementation

In `_updateRecurrenceRelation()`, when planting seeds:

```cpp
for (auto j = _j; j > 0; j--)
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
    // ... rest of loop
}
```

### Edge Cases and Predictions

**Symmetric seeds (1, 1):** Since 1/1 = 1, seed inversion is identity. All four quadrants collapse to two distinct behaviors (Arithmetic vs Harmonic sum only).

**Asymmetric seeds (e.g., 1, 2 or 3, 5):** The four quadrants diverge meaningfully. This is where the experimental matrix becomes musically interesting.

**Historical note:** For MOS (where there are no seeds), Erv leveraged inverting the generator constantly. But he never conceived of a "harmonic recurrence sequence"—this is new territory. The 2×2 matrix extends Wilson's generator-inversion intuition to the seeded recurrence domain.

### Significance

This duality suggests that Wilson's proportional/subcontrary triad distinction (see Part 2) is not just an analytical observation but reflects a **deep structural symmetry** in recurrence-based scale generation.

The same seeds and indices produce dual scales: one optimized for major-type harmony, one for minor-type harmony, with mirrored melodic structure.

**This may be the switch Erv was circling but never explicitly formalized.**

---

## Appendix A: Key Equations

### MOS Generator from Cubic

```
G^3 + 2G - 4 = 0  ->  G = 1.17950902460  ->  log2(G) = 0.238186
```

### Proportional Triad Conditions

```
Major: (a + b) / 2 = c  (c is a scale degree)
Minor: 2ab / (a + b) = c
Neutral: sqrt(ab) = c
```

### Recurrence Relation General Form

```
A_n = c1*A_{n-1} + c2*A_{n-2} + ... + ck*A_{n-k}

Convergent ratio A_n/A_{n-1} -> generator (attractor)
```

### Arithmetic/Harmonic Duality (Part 9)

```
Arithmetic sum:  a + b           -> proportional triads
Harmonic sum:    ab / (a + b)    -> subcontrary triads

For H[n] = H[n-i] + H[n-j]:
  Arithmetic characteristic: r^j = r^(j-i) + 1    -> generator g
  Harmonic characteristic:   r^i + r^j = 1        -> generator 1-g

Fibonacci case (i=1, j=2):
  Arithmetic: r = φ ≈ 1.618      -> g = log₂(φ) ≈ 0.694
  Harmonic:   r = 1/φ ≈ 0.618    -> g = 1 - 0.694 = 0.306
```

---

## Appendix B: Glossary

**CPS (Combination Product Set):** Scale constructed by taking k-subsets of n harmonic factors, multiplying each subset, and octave-reducing.

**Eikosany:** A (3,6) CPS - 20 notes from all 3-factor products of 6 harmonics.

**Generator:** The interval that, when iterated and octave-reduced, produces an MOS scale.

**Gral:** Wilson's isomorphic keyboard layout for MOS scales.

**Harmonic Sum:** The operation a ⊕ b = ab/(a+b), also called "parallel sum." Produces subcontrary triads when used in recurrence relations, dual to the arithmetic sum which produces proportional triads. (See Part 9)

**Hexany:** A (2,4) CPS - 6 notes from all 2-factor products of 4 harmonics.

**Level:** Depth of MOS recursion; higher level = more notes.

**MOS (Moment of Symmetry):** Scale with exactly two step sizes whose counts are coprime.

**Murchana:** Mode rotation within an MOS.

**Noble Number:** Irrational number whose continued fraction eventually becomes all 1s.

**Period:** The interval of equivalence (typically octave = 2).

**Proportional Triad:** Three pitches where middle = arithmetic mean of outer two.

**SeedSpace:** Parameter controlling whether recurrence relation seeds are used as-is (Frequency) or inverted (Period). Combined with SumType, creates a 2×2 experimental matrix of scale families. (See Part 9)

**Subcontrary Triad:** Three pitches where middle = harmonic mean of outer two.

**SumType:** Parameter controlling whether recurrence relations use arithmetic sum (a + b, yields proportional triads) or harmonic sum (ab/(a+b), yields subcontrary triads). Arithmetic and harmonic generators are reciprocals. (See Part 9)

---

## Appendix C: Historical Context

Erv Wilson (1928-2016) developed these theories largely without computational tools. Marcus Hobbs worked directly with Wilson from 1995-2005, implementing his designs in software during real-time coding sessions. Much of Wilson's work exists only in hand-drawn diagrams.

The Wilsonic-MTS-ESP codebase represents the most complete computational implementation of Wilson's scale design theories.

**The melody/harmony bridge problem - finding scale systems that serve both dimensions - represents unfinished work in Wilson's legacy and the next frontier for microtonal theory.**

---

*Document generated from conversations between Marcus Hobbs and Claude*  
*Initial session: December 3, 2025*  
*Updated: December 30, 2025 (Part 9: Arithmetic/Harmonic Duality)*
