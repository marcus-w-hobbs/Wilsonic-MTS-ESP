# Epimore and Mediant: research memo

**Analyst:** Claude (Anthropic)  
**Collaborator:** Marcus Hobbs  
**Date:** October 15, 2026  
**Purpose:** Pure research reading of Erv Wilson's March 1996 Epimore / Mediant notes and letters to Barbara Hero, and what they mean for psychoacoustics, the proportional-triad analyzer, and Wilsonic MTS-ESP. No code changes.

---


Source: Erv Wilson, "Epimore Tree (work in progress)", "Mediant & Epimore", Farey/Lambdoma notes, and four letters to Barbara Hero dated 16, 18, 21 and 23 March 1996, written after her "A Brief History of the Lambdoma" in Xenharmonikôn 16 (1995). 33 scanned pages.

Numerical claims below were checked with `docs/research-epimore-mediant-verify.py` (exact rational arithmetic).

## 1. What the PDF says

**Definitions (Wilson's, pages 2, 3, 4, 7).**
- Two fractions a/b and c/d are *consecutive* (Farey neighbours) when `bc - ad = 1`.
- The *epimore* between them is `bc/ad = (ad+1)/ad`, always superparticular, "a ratio whose numerator exceeds its denominator by 1". Example: 5/4 and 4/3 give 16/15.
- The *mediant* inserted between them is `(a+c)/(b+d)`. Inserting it splits the epimore into two new epimores `b(a+c)/a(b+d)` and `c(b+d)/d(a+c)`. Example: 1/1 and 4/3 (epimore 4/3) take the mediant 5/4 and the cascade yields 5/4 and 16/15.
- The three-term form: if a/b, c/d, e/f are consecutive then `(a+e)/(b+f) = c/d` reduced; 4/3, 11/8, 7/5 give (4+7)/(3+5) = 11/8.
- Two conditions "release a cascade of epimoria": the initial pair must be epimore-capable (det = 1) and the inserted term must be their mediant (page 6).

**The discovery (letters).** On 2 March 1996 Wilson ran the reduced terms of the Lambdoma, sorted in pitch order, against the Farey series and found "exact fits". A table of gear ratios or a Lambdoma capped at integer N, sorted and reduced, *is* the Farey series of order N extended from 0/1 to 1/0. He cites Neville's *Farey Series of Order 1025* (1950) as a 1025-cap Lambdoma that Neville never recognised as such. He stresses the 0/1 to 1/0 symmetric form, with 1/1 at the centre, for musical use.

**Epimore Tree (page 1).** The Stern-Brocot tree from 0/1 to 1/0 with every branch labelled by its epimore. This is Wilson's Scale Tree with epimores written on the edges.

**Greek tetrachords (pages 9, 12, 14).** The Olympos trichord 1/1, 5/4, 4/3 is one mediant insertion. Archytas's enharmonic read downward from 4/3 is 4/3, 9/7, 5/4, 1/1, i.e. two mediant insertions, giving epimores 28/27, 36/35, 5/4. Verified: inserting 5/4 then 9/7 into [1/1, 4/3] produces exactly those steps. Wilson asks whether Archytas was "saying I know the secrets of the Lambdoma" and answers "I suspect that is so", while conceding he cannot prove it.

**Partch's Diamond versus Farey (pages 18, 22, 23).** He lists the 43-tone scale with the mediant of each neighbour pair and the reduced epimore between them. Many rows are marked x because Partch's 43 is not a pure Farey series (the 3-limit extensions such as 81/80, 32/27, 27/20, 21/16 break the det = 1 chain). Marginal notes: "definitely ragged around the edges", "Diamond does not specify 8ve", "doesn't work?". He also notes that 81/80 "will appear 60 times in the scale tree" (4·3·5) and that "there are other epimoric pairs than consecutive terms in the scale tree".

**Fibonacci rationals and backtracking (pages 6, 15, 26, 27).** The Fibonacci rational zig-zag sequence sorted by magnitude, noble-number ladders out to 1,346,269/832,040, and a page showing that a single term a/b contains enough information to recover all its ancestors by the Euclidean algorithm (87/53 worked through), with the resulting A/B step pattern. That page is the MOS/Brun connection.

**Caps on factors (page 24).** "There is a way to put an arbitrary cap on the factors of the epimore." This is a prime-limit cap rather than an integer cap, which is Størmer's territory (finitely many superparticulars for a given prime limit; the 5-limit has exactly ten: 2/1, 3/2, 4/3, 5/4, 6/5, 9/8, 10/9, 16/15, 25/24, 81/80).

**Side-and-diagonal (page 32).** 17/12 and 24/17 differ by 289/288. These are consecutive approximants to √2 from Theon of Smyrna's side-and-diagonal numbers.

## 2. Psychoacoustics: are epimores a sonic phenomenon?

Partly. The arithmetic fact has one clean sonic consequence and it fades with n.

- **Difference tone equals periodicity pitch.** A dyad with frequencies p·f and q·f in lowest terms has periodicity pitch f and first-order difference tone (p − q)·f. These coincide exactly when p − q = 1. For 5/4 the difference tone is the fundamental two octaves below the root; for 3/2 it is the octave below; for 5/3 it is 2f and for 7/4 it is 3f, neither of which is the virtual fundamental. All higher-order difference tones k·f fill the whole harmonic series of f. This is the mechanism CLAUDE.md calls "harmonic reinforcement rather than interference", stated for dyads.
- **Local simplicity.** Between two Farey neighbours there is no fraction with smaller denominator, so the epimore between them is the simplest interval of its size. Tenney height is n(n + 1). Harmonic-entropy minima at small n are superparticulars for this reason.
- **The fade.** 81/80 and 289/288 are superparticular and no one hears them as consonances. The property is number-theoretic; the audible effect requires small n, where periodicity detection and difference tones work. So an epimore is an arithmetic property with a sonic shadow, not a perceptual category.
- **Relation to the 0.0005 tolerance.** The analyzer's tolerance is far below pitch discrimination, so in practice it is an exactness test. On a JI scale the triads it finds are exactly the rational coincidences described in section 3.

## 3. Epimores and the three triads

This is the strongest link and it lands in the code.

**Proportional and subcontrary triads are stacked epimores.** In lowest terms a proportional triad is n : n+1 : n+2, which is the two consecutive epimores (n+1)/n · (n+2)/(n+1). A subcontrary triad is 1/(n+2) : 1/(n+1) : 1/n, the same two epimores in reverse order. 4:5:6 = 5/4 · 6/5; 10:12:15 = 6/5 · 5/4. The general form n : n+k : n+2k reduces to this when k divides n.

**The mediant is both means at once.** The mediant (a+c)/(b+d) is the denominator-weighted arithmetic mean of a/b and c/d and also the numerator-weighted harmonic mean. Verified for 5/4 and 4/3: both weightings give 9/7. Consequences on the Lambdoma:
- along a row (fixed denominator) the mediant is the plain arithmetic mean, so 4/4, 5/4, 6/4 is a proportional triad;
- along a column (fixed numerator) the mediant is the plain harmonic mean, so 6/4, 6/5, 6/6 is a subcontrary triad;
- the Farey mediant is the diagonal case where the two weightings agree.

So Wilson's Lambdoma = Farey equivalence says: proportional triads are row mediants, subcontrary triads are column mediants, and `_analyzeProportionalTriads()` on a diamond or lambdoma scale is enumerating mediants. For exact rationals the test "middle = (a+c)/(b+d) with matching denominators" could replace the float tolerance entirely.

**Geometric triads cannot be rational over an epimore.** Archytas proved, and Euclid's *Sectio Canonis* prop. 3 repeats, that no superparticular ratio has a rational mean proportional. Every adjacent step in a Farey or Lambdoma scale is epimoric, so a geometric (neutral) triad whose outer interval is an epimore is never in the scale. Geometric triads only arise with irrational generators, i.e. MOS. The code agrees: `_geometricTriads` is declared and cleared in `TuningImp.cpp` but never populated, and `scorer.py` counts G but never rewards it. The place where arithmetic and geometric means coincide is Wilson's 1993 note (A+B)/2 = √(B/A), the metallic-mean generators. That identity is the bridge between the log-space MOS structure and the linear-space epimore lattice, and it is why the optimised generators sit where they do.

## 4. Wilsonic MTS-ESP: what exists, what does not

**Mediants: present, in generator space.** `Brun::brunArray()` (`Source/Brun.cpp:91-99`) builds the scale tree by inserting `Microtone::freshmanSum` (`Source/Microtone.cpp:707`), which is exactly the mediant, between adjacent fractions. That is the Stern-Brocot tree, i.e. Wilson's Epimore Tree without the edge labels. Consecutive tree entries satisfy det = 1, so each MOS level's generator fractions are Farey neighbours. The research harness uses Farey intervals explicitly (`experiments/lattice/gold001.py:125`, CPSFIT-003).

**Epimores: absent.** Nothing computes bc − ad or flags superparticular steps. Nothing labels the scale tree edges.

**The Lambdoma is present as data and as drawing, not as a construction.**
- `scl/lambdoma5_12.scl`, `scl/lambdoma_prim.scl`, `scl/farey3.scl`, `farey4.scl`, `farey5.scl`, `farey12_*.scl` in the Scala bundle.
- `PartchComponent.cpp:33` offers "Partch 43 and Partch Lambdoma".
- Diamonds (triadic through ogdoadic) are odd-limit Lambdoma subsets.
- The CoPrime Grid (`Source/CoPrime.*`) draws coprime (n, d) pairs with Harmonic / Subharmonic / Triangle modes. It is the reduced Lambdoma on screen; the epimore between neighbours is never shown.

**Research-side leverage (no code changes made).**
1. Epimoric-step annotation in the interval matrix: det = 1 test on adjacent degrees of `_processedArray`; cheap, exact for rationals.
2. Exact triad test for JI tunings: proportional iff the middle is the common-denominator mediant; removes the register-dependent float tolerance for rational scales.
3. An epimore-weighted triad quality: triads whose two steps are epimores with small n are the ones with audible difference-tone reinforcement. This refines "sum of 1/error" with a Tenney-height term.
4. A Farey cascade design (Greek tetrachord builder): choose two Farey neighbours, insert mediants, cap by integer or by prime limit. Would be a new design at the END of the DesignsModel list.
5. Scale tree edge labels with the epimore bc/ad, which is Wilson's page 1 drawn live.

## 5. Gear ratios

- **Brocot.** Achille Brocot, a Paris clockmaker, published "Calcul des rouages par approximation, nouvelle méthode" in 1861 and a 97-page monograph in 1862. His problem was approximating a target ratio with gear trains of limited tooth counts; taking mediants between an upper and lower bound gives the best approximations with the smallest terms. Stern had published the same tree in 1858 as number theory. This is the gear-ratio origin of the Stern-Brocot tree.
- **Farey history.** Haros published a table of fractions in 1802 for decimal conversion; Farey noted the mediant property in 1816; Cauchy proved it. Neville's 1950 volume is subtitled "Displaying Solutions of the Diophantine Equation bx − ay = 1", which is Wilson's det = 1 condition on every page. Wilson's claim that the Farey series "has its roots in earlier tables of gear ratios" is right for Brocot and not established for Haros or Farey.
- **Epimores in gears.** Tooth counts n and n + 1 are automatically coprime, which is the hunting-tooth design rule: every tooth of one wheel eventually meets every tooth of the other, so wear is spread evenly. A pair n : n + 1 is also the finest possible ratio step available to a train with those tooth counts, the Farey-neighbour property again.
- **Ancient gearing.** The Antikythera mechanism realises astronomical ratios such as 254 : 19 with gear trains, showing ratio approximation by gears about 100 BCE. That is evidence for the practice Wilson imagines, not for any Lambdoma knowledge.

## 6. Ancient applications

- **Greek tetrachord theory.** Archytas (c. 400 BCE) built tetrachords from epimoric steps; his enharmonic is Wilson's two-step mediant cascade exactly. Ptolemy's *Harmonics* makes the epimoric principle a rule for melodic intervals, giving divisions such as 9/8, 10/9, 16/15. Euclid's *Sectio Canonis* and Boethius transmit Archytas's theorem that an epimore has no rational half.
- **Archytas fragment 2** defines the three means and renames the "subcontrary" mean "harmonic", which is where the code's `Subcontrary` type gets its name.
- **Plato's Timaeus** fills the double interval 1 : 2 with the arithmetic mean 3/2 and the harmonic mean 4/3, leaving the tone 9/8. The result 1/1, 4/3, 3/2, 2/1 is the Farey series of order 3 on the octave, verified.
- **Theon of Smyrna's side-and-diagonal numbers** approximate √2 by 1/1, 3/2, 7/5, 17/12, 41/29; consecutive pairs differ by epimores, as Wilson's 289/288 shows.
- **Chinese sanfen sunyi** generates pitches by alternating 3/2 and 4/3, both epimores.
- **Egypt.** Wilson's suggestion that priests computed on the Lambdoma is his own speculation, flagged by him as unprovable. Egyptian unit fractions are a different system; no document links them to mediants.

## 7. Is it a scale construction tool?

Yes, in two spaces that meet at the same condition.
- In frequency space the mediant cascade is the Greek tetrachord method and the Lambdoma; every step it produces is epimoric.
- In generator space the mediant cascade is the Scale Tree and MOS, which Wilsonic already implements.
The det = 1 condition is the same in both. Wilson's letters are him noticing that the lattice he had been drawing as the Lambdoma for years and the tree he had been drawing as the Scale Tree are the same object read in two spaces.
