# Analysis of Erv Wilson's Handwritten Documents

**Analyst:** Claude (Anthropic)  
**Collaborator:** Marcus Hobbs  
**Date:** December 3, 2025  
**Purpose:** Detailed interpretation of Wilson's original documents, demonstrating computational understanding of his scale design methodology

---

## Document 1: "Study for Difference-Tone Continuum" (1993)

### Source Description
Hand-drawn horogram on lined paper, showing pitch relationships across generator space. Signed "© 1993 by Erv Wilson" with notation "a work in progress."

### What Wilson Drew

The image shows a **polar coordinate representation** (horogram) where:
- The horizontal axis represents pitch space (marked 1/4, 1/2, 1, 2)
- Vertical lines drop from a curved upper boundary, representing scale degrees at different generator values
- Numbers annotate the dots: scale degree indices and harmonic identities
- The diagonal curve traces how pitches evolve as the generator changes

### The Key Equations (Top Left)

Wilson wrote a **recurrence relation**:
```
2 + 6 = 8
3 + 8 = 11
4 + 11 = 15
5.5 + 15 = 20.5
7.5 + 20.5 = 28
10.25 + 28 = 38.25
```

And the critical identity:
```
(A + B) / 2 = √(B/A)
```

This equation describes **where arithmetic mean equals geometric mean**. This is profound: Wilson was identifying the precise condition where the proportional triad (arithmetic mean) and neutral triad (geometric mean) collapse to the same point.

He also wrote:
```
B/A = ((A+B)/B)²
```

This is the algebraic rearrangement showing the self-referential structure.

### Musical Significance

The horogram visualizes what I would call the **"difference-tone continuum"** - how sum and difference tone relationships change continuously as you move through generator space. The vertical lines show that at certain generators, pitches align in ways that create reinforcing combination tones.

This document is Wilson exploring the *landscape* before identifying specific optimal generators. He's mapping the territory.

### Connection to Wilsonic Codebase

The horogram visualization is implemented in `Brun+Paint.cpp`:
- `_paintHorogram()` - draws the polar representation
- `_paintInverseHorogram()` - draws the inverse (center-out) version

Wilson's hand-drawn version shows the *conceptual* structure that the code now renders in real-time.

---

## Document 2: "Proportional Triads in MOS" (13 Jul 1997)

### Source Description
Lined paper showing scale degree layouts with L/s (Large/small) interval patterns, bracketed triads, and mean calculations. Notation: "after Callum Johnston's bagpipe scale © 1997 by Erv Wilson"

### What Wilson Drew

**First Scale (18-tone MOS):**
```
Scale degrees:  0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17
Murchana:      +4 +1    +5 +2    +6    +3       0            +4
L/s pattern:   |s |  L  |s |  L  |  s  |  s  |     L        |
```

**Triad bracket showing Proportional Major:**
```
        a -------- (a+b)/2 -------- b
```

**Second Scale (same structure, different voicing):**
```
Scale degrees:  0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18
Murchana:      +4 +1    +5    +2    +6    +3       0            +4
L/s pattern:   | L | s | L |  L  | s |  L  |  L  |     s       |
```

**Triad bracket showing Subcontrary (Minor):**
```
        a -------- 2ab/(a+b) -------- b
```

### The Insight

Wilson is showing that **the same outer notes (a and b) can support BOTH types of triads** depending on which inner scale degree you choose:
- Pick the arithmetic mean → major triad
- Pick the harmonic mean → minor triad

The L/s pattern determines which options are available. The murchana numbers (+4, +1, +5, etc.) show the **generator stack position** of each note - how many generator iterations from the origin.

### Why "Callum Johnston's Bagpipe Scale"?

This suggests Wilson was analyzing an existing traditional scale and discovering its proportional triad structure. The bagpipe connection implies this is a scale that evolved culturally to have these properties - evidence that humans have been intuitively finding these optimal generators for centuries.

### Connection to Wilsonic Codebase

The murchana values correspond directly to `BrunMicrotone::getScaleDegree()` in the code. The L/s pattern is what `Brun::_microtoneArrayBrun()` generates. Wilson's hand analysis is exactly what `_analyzeProportionalTriads()` now computes automatically.

---

## Document 3: "Secondary Series" Page 4a (16 Jul 1997)

### Source Description
Lined paper showing a generator derivation with continued fraction expansion, convergence iteration, and MOS sequence. Part of a larger document on "Secondary Series."

### What Wilson Wrote

**The Scale Pattern:**
```
0  +1  +2    +3    +4
0 1 2 3 4 5 6 7  1 2 3 4 5 6 7  1 2 3 4 5 6 7
|L |s|L |s|s| L |s|L | s|s| L |s| L |s|s|
```

Pattern notation: **LSLSS** - a 5-element pattern that repeats.

**The Defining Equation:**
```
L = ⁴√((L³+4)/2)
```

**The Iteration (showing convergence):**
```
1.334839854  guess
1.336351425...
1.336774913...
1.336893659...
1.336926963...
1.336936305...
1.336938925...
1.336939660...
1.336939866...
1.336939924...
1.336939940...
1.336939944...
1.336939946...
1.3369399459...
1.33693994606...
1.33693994609   (converged)
```

**The Generator:**
```
Log₂ = 0.418984662571
```

**Wilson's Note:**
```
(like ⅕ comma meantone)!
```

**The Continued Fraction (1/x Pattern):**
```
.418...
← 2  .387
→ 2  .583   0/1
← 1  .712      \
→ 1  .403   1/2 \
← 2  .478       1/3
→ 2  .089          \
  11 .180   2/5     3/7
   5 .544       \
   1 .836   5/12 \
   1 .194       8/19
 ? 5 .131          \
              13/31 \
                   18/43
                       \
                    31/74
                        \
                     44/105
```

**The Zig-Zag Pattern (MOS denominators):**
```
0/1 → 1/2 → 1/3 → 2/5 → 3/7 → 5/12 → 8/19 → 13/31 → 18/43 → 31/74 → 44/105
```

### The Deep Structure

Wilson is showing **how to derive a generator from a target triad structure**. The equation L = ⁴√((L³+4)/2) isn't arbitrary - it encodes the condition for specific proportional triads.

The continued fraction shows the **approximation pathway**: each convergent gives an MOS cardinality. Notice **5/12** appears in the sequence - this generator passes through the familiar 12-note territory, which is why Wilson notes it's "like ⅕ comma meantone."

The arrows (← →) in the CF column indicate the **direction of the zigzag** in the Stern-Brocot tree - whether you're taking a left or right branch at each level.

### Connection to Wilsonic Codebase

The zigzag pattern is exactly what `Brun::brunArray()` computes. The convergents (1/2, 1/3, 2/5, 3/7, 5/12...) are the MOS cardinalities at each level. Wilson's hand-computed iteration is what modern floating-point arithmetic gives us instantly.

The insight about "⅕ comma meantone" explains why this generator sounds familiar to Western ears - it's in the neighborhood of historical European tuning.

---

## Document 4: "Secondary Series" Page 4b (16 Aug 1997)

### Source Description
Continuation of the Secondary Series analysis, showing the recurrence relation, example seeds, and a tree diagram of triad relationships.

### What Wilson Wrote

**The Recurrence Relation:**
```
4A_{n-4} + A_{n-1} = A_n
```

**The Generator Equation:**
```
G = ((4 + G³)/2)^(1/4) = 1.3369394609...
Log₂ = 0.418934662571...
```

**Example Seeds:**
```
A_{n-4}  A_{n-1}  A_n
  54      72      96    128    172
```

**Wilson's Note:**
```
Similar to 2/9-comma tuning
```

**Extended Sequence:**
```
(30)(40) 54 72 96 128 172 230 307 409.5 548.75 734.375 981.1875
         1,309.59375  1,752.296875
```

**Tree Diagram Annotations:**
```
        40        30    ← 22.5        17
          \      /  \      /  \      /
          128   96   72   54   (40)
            \    |    |    /
           409.5  307  230  172  (128)
              \    |    |    /
          1,309.59375  981.1875  734.375  548.75  (409.5)
```

**Triad Types Identified:**
```
Fibonacci (like 3,5,8)
Proportional triad (like 3:4:5)
```

**Scale Description:**
```
19-Tone Scale where 4A_{n-4} + A_{n-1} = A_n
© 1997 by Ervin M. Wilson
```

### The Breakthrough Insight

Wilson is showing that **the same recurrence relation produces BOTH Fibonacci-like structures AND proportional triads**. The tree diagram shows how:
- Going up the tree: Fibonacci ratios (each number ≈ φ × previous)
- Going across branches: Proportional triads (arithmetic mean relationships)

The seeds (54, 72, 96, 128, 172) aren't arbitrary - they're chosen to produce specific harmonic relationships while the recurrence drives toward the generator attractor.

### Why 19 Tones?

The recurrence 4A_{n-4} + A_{n-1} = A_n has a **characteristic polynomial** whose root determines the generator. At level 4 (where the -4 subscript matters), you get a 19-note MOS. This is a "sweet spot" where the triad density is high and the scale is still playable.

### Connection to Our CPS/MOS Bridge Proposal

This document is the **proof of concept** for seeding. Wilson is showing that:
1. You can choose seeds that encode harmonic relationships
2. The recurrence will preserve those relationships in early terms
3. The generator attractor provides melodic (MOS) structure
4. The result has BOTH harmonic richness AND scalar continuity

This is exactly the CPS/MOS bridge we proposed - Wilson was already doing it, just not with CPS specifically as the seed source.

---

## Document 5: "On Complementary Proportional Triads" (1995)

### Source Description
A comparison of two generators with their recurrence relations, showing how different algebraic structures produce complementary triad types. Includes a 7-tone circle diagram.

### What Wilson Wrote

**The 7-Tone Circle:**
A circular diagram showing pitches C, D, E♭, F, G, A, B♭ with:
- Inner connections labeled "-3 = 5" 
- Outer markings showing generator positions: -1, -2, -3, +1, +2, +3, +4

**Meta-Mavila System:**
```
ω, Proportional Triad
P_n = (2P_{n-4}) + P_{n-3}
P_n / P_{n-1} converges at: 1.35320996420
Log₂ = 0.436385705396

Example of recurrence sequence:
4.5, 6, 8, 11, 15, 20, 27, 37, 50,
67, 91, 124, 167, 225, 306, 415,
559, 756, 1027, 1389, 1874, 2539,
3443, 4652, 6287, 8521, 11538,
15591, 21095 etc.

MOS at: 1/1, 1/2, 1/3, 2/5, 3/7,
        7/16, 10/23, 17/39, 24/55, 31/71 etc.
```

**Meta-Meantone System:**
```
ω Proportional Triad
H_n = 2(H_{n-4} + H_{n-3})
H_n / H_{n-1} converges at: 1.49453018048
Log₂ = 0.579692031034

Example of Recurrence Sequence:
1, 2.5, 3, 5, 7, 11, 16, 24, 36, 54, 80,
120, 180, 268, 400, 600, 896, 1336, 2000,
2992, 4464, 6672, 9984, 14912, 22272,
33312, 49792, 74368, 111168, 166208,
248320, 371072, 554752, 829056, 1238784 etc.

MOS at: 1/1, 1/2, 2/3, 3/5, 4/7, 7/12, 11/19,
        18/31, 29/50, 40/69, 51/88 etc.
```

**The Key Label:**
```
+4 = "5" → Meta-meantone ω proportional triad
```

### The Complementarity

Wilson is showing that these two systems produce **complementary triads**:
- Meta-Mavila: Triad at "-3 = 5" position (subcontrary/minor character)
- Meta-Meantone: Triad at "+4 = 5" position (proportional/major character)

The "5" refers to scale degree 5 (the "dominant" in Western terms). Both systems produce a triad involving the fifth scale degree, but with different intervallic content.

### Why "Meta"?

"Meta-Mavila" and "Meta-Meantone" suggest these are **generalizations** of the traditional Mavila and Meantone tunings. Wilson found the underlying algebraic structure (the recurrence relation) that generates each family, then explored the parameter space.

### The Recurrence Structures

**Meta-Mavila:** P_n = 2P_{n-4} + P_{n-3}
- Looks back 4 steps (doubled) and 3 steps
- Converges to generator 0.436... (≈ 524 cents, a sharp fourth)

**Meta-Meantone:** H_n = 2(H_{n-4} + H_{n-3})
- Same structure but with factor of 2 outside
- Converges to generator 0.580... (≈ 696 cents, a meantone fifth)

The different placements of the "2" coefficient produce dramatically different generators and triad types.

### Connection to Wilsonic Codebase

The MOS sequences Wilson lists match what `Brun::brunArray()` would produce for these generators. The Meta-Meantone sequence (7/12, 11/19, 18/31...) shows the familiar 12-tone landmark, explaining its "meantone" character.

---

## Synthesis: What Wilson Was Doing

Across these documents, Wilson's methodology emerges:

### 1. Start with Algebraic Structure
He begins with self-referential equations (cubics, quartics) or recurrence relations. These aren't arbitrary - they encode specific harmonic conditions.

### 2. Derive the Generator
Through iteration or continued fraction analysis, he finds the generator (attractor) that the algebra implies.

### 3. Map the MOS Sequence
The continued fraction convergents give him the MOS cardinalities at each level. He identifies "sweet spots" where scale size is practical.

### 4. Analyze Triad Content
He checks which proportional and subcontrary triads exist at each level, often drawing bracketed diagrams to show the relationships.

### 5. Connect to Cultural Reference Points
Notes like "like ⅕ comma meantone" or "after Callum Johnston's bagpipe scale" show he was grounding abstract mathematics in musical reality.

### 6. Explore Variations
By changing seeds, coefficients, or initial conditions, he could explore families of related generators - the "Meta-" prefix indicates this kind of generalization.

---

## Implications for Computational Research

### What Can Now Be Automated

1. **Generator → Triad Analysis:** Given any generator, compute all proportional/subcontrary triads at any level. (Already implemented in Wilsonic)

2. **Recurrence → Generator:** Given recurrence coefficients, compute the attractor. (Standard numerical methods)

3. **Generator → Continued Fraction:** Extract the CF expansion to understand MOS structure. (Straightforward algorithm)

4. **Landscape Mapping:** Sweep generator space and plot triad quality. (Computationally trivial)

### What Requires Human Insight

1. **Which triads matter musically?** Wilson's constraint (between major 2nd and fourth) reflects cultural judgment.

2. **Which seeds produce interesting results?** The CPS/MOS bridge proposal requires choosing harmonically meaningful seeds.

3. **What makes a generator "beautiful"?** Wilson's aesthetic judgment (his favorite vs. 12ET-adjacent) isn't captured by triad count alone.

### The Open Problem

**Formalizing Wilson's intuition for deriving recurrence relations from target triad structures.** He could look at a desired harmonic outcome and work backwards to the algebra. This reverse-engineering skill is not yet algorithmic.

---

## Conclusion

These documents reveal Wilson as a mathematical artist - someone who could see deep structure in numbers and hear musical meaning in algebra. His handwritten work is dense, systematic, and far ahead of its time.

The fact that a computational system can now parse these images, understand the mathematics, connect them to implemented code, and identify open research questions represents a significant advance. But it also reveals how much of Wilson's intuition remains to be formalized.

The next step is clear: use computational tools to explore the spaces Wilson mapped by hand, while preserving the musical judgment that made his discoveries meaningful.

---

*Analysis conducted December 3, 2025*  
*Claude (Anthropic) in collaboration with Marcus Hobbs*  
*For the microtonal music theory community*
