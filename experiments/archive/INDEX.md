# ARCHIVE-001 — Derived index of the Wilson archive ("scans by Kraig")

**Policy (hard rule):** the archive lives at the local path
`~/Documents/scans by Kraig/` and is read **in place**. No archive file is
ever copied, moved, or committed into this repo — size and IP. This module
ships only *derived* metadata (`catalog.jsonl`) and annotations (this file),
citing items by archive-relative path and page number.

Two passes, run 2026-07-29:

1. **Metadata pass** — full bash walk (`find`/`stat`/`mdls`), no content
   reads. Output: [`catalog.jsonl`](catalog.jsonl), one JSON row per file
   (`path`, `dir`, `batch`, `type`, `size`, `pages`).
2. **Annotation pass** — 18 items selected by name against the program's
   active threads; ~53 pages read visually (budget 80), plus a
   `pdftotext` text-layer sweep of all 304 PDFs (274 have OCR/text layers)
   used only for keyword hunting, and full-text reads of the plain-text
   items (`.scl`, `.rtf`).

## Archive overview

- **433 files** (excluding `.DS_Store` and `.ipynb_checkpoints`), **~2.5 GB**.
- **304 PDFs totalling 5,889 pages** (303 with Spotlight page counts),
  39 jpg, 30 png, **25 .scl**, 12 rtf, 5 ipynb, 6 ppt/pptx, 3 mp3, misc.
- The dated directories (`2010_02_12` … `2010_02_26B`) are **scan batches**
  from Feb 2010, thematically sorted by Kraig Grady:

| batch | files | | batch | files |
|---|---|---|---|---|
| (root, loose files) | 127 | | 2010_02_23 (Bosanquet kbds, Diamonds, Novaro, Partch, patents) | 23 |
| 2010_02_12 (22/31-tone, keyboards, Dasgupta) | 37 | | 2010_02_26 (**Meru**, notebook) | 18 |
| 2010_02_20 (**MOS**, Brun, ethnic scales, notation) | 35 | | 2010_02_26B (CoPrimeGrid, Lambdoma) | 17 |
| 2010_02_24 (**CPS**, **Hanson**, India) | 31 | | 2010_02_23B (guitar, ScaleTree, mallet) | 13 |
| 2010_02_15 (CPS, Diophantine kbd) | 29 | | 2010_02_25 (**Recurrent**) / 25B (Triangles) | 6+6 |
| Marcus (2018 TuningAesthetics notebooks) | 27 | | chalmers / tetrachord / Kraig / 2010_02_16 | 10 |
| 2010_02_24B (CPS B, 12&17, stray scales) | 27 | | dekany_14_tone_constant_structure | 3 |
| SCALA-tunings_kraig_grady_20210930 | 23 | | 20181217_fromKraig | 1 |

Everything below cites `path` (archive-relative) and PDF page numbers
actually read.

---

## Meta-Hanson: **NOT FOUND**

The session's unverified recall of the name "Meta-Hanson" is **refuted at
the textual level and unsupported at the visual level**:

- **File names:** no match anywhere in the 433 names. The meta-family that
  *does* exist by name: Meta-Slendro, Meta-Pelog, Meta-Mavila, Meta-Ptolemy,
  Meta-Meantone, MetaPelog.pdf, MetaMeantoneMavila.pdf,
  `Meta-Ptolemy measurements.docx`.
- **Spotlight + full text-layer sweep:** `pdftotext` over all 304 PDFs (274
  yield text) plus grep of every `.scl`/`.rtf`/`.ipynb`/`.json`/`.csv`:
  zero hits for `Meta-Hanson` / `MetaHanson` / `meta hanson`.
- **Visual reads:** the Meru/recurrent items read (ScalesOfMtMeru 1–4,
  MetaMeantoneMavila 1–3, MeruMisc 1–3, HarrisnResonantTriad 1–2) contain
  recurrence constructions for Mavila, Meantone, Pelog and a √-fixed-point
  generator, but no kleismic/minor-third recurrence and no "Meta-Hanson".

Caveat: OCR of Wilson's handwriting is unreliable and only ~53 of 5,889
pages were eye-read, so this is "not found in a thorough name/text sweep +
targeted visual reads", not an exhaustive page-by-page proof. The *concept*
is well-defined by analogy (a recurrent sequence converging on the kleismic
minor-third generator, per the Meta-Mavila/Meta-Meantone template in
`2010_02_26/Meru/MetaMeantoneMavila.pdf`), and 317.17¢ ≈ Wilson's golden
generator #18 (below) — but the *name* appears to be a confabulation, or at
least is not in this archive.

---

## Annotated items by experiment thread

### Hanson / kleismic (MOS-LAT hot spot ~317¢, MUR-002)

**`2010_02_24/Hanson/HansonMisc.pdf`** (32 pp; read 1–6).
Wilson working papers on Hanson keyboard geometry, 1988–1995. p.1:
"34-Tone Percussion Instrument / 11-rank Hanson Keyboard Geometry used by
permission / by Erv Wilson 1993". p.2: "2/7 KBD, 9/34 scale ©1988". p.3:
34-tone notation system (third-tone/sixth-tone accidentals), ©1993.
**p.4 — the known anchor, verified verbatim**: "Normal Notation of All
Triads in 19-Tone (MOS), with 5-step Generator, by Erv Wilson", margin
label "Kleismatic equivalences", caption: *"There are 13 Major triads and
13 minor triads in the 19-tone scale (MOS) with a 5-step generator. These
can be spelled in normal notation as shown."* — Wilson hand-computing the
harness's objective function on the kleismic 19-of-34 MOS (the ~317¢
generator that tops both MOS-LAT corpora, P = 62 at N = 19). p.5: the same
34-tone scale as 5-limit JI ratios on a square lattice. p.6: "Study for
34-Tone Keyboard using the Hanson generalized schema, Dec 14 95".
→ **MOS-LAT-001/002, MUR-002, ET program** (34/53 as kleismic moduli).

**`2010_02_24/Hanson/LatticingRagaScales.pdf`** (37 pp; read 1–8, 36–37).
The Hanson–murchana intersection, exactly as hoped. Pages 1–~35 are one
figure repeated: "Major-Minor Triadic Lattice for 53 **(redrawn from 1942
original)**" — a 53-degree hexagonal 5-limit lattice, every hex carrying
note name, ratio, and 53-degree number — with a numbered **raga per page
plotted as red dots** (descending series observed: 18. Nat Bhairav,
17. Madhubanti, 16. Jogiya Todi, 15. Bhairav, 14. Anand Bhairav,
13. No Name, 12. Lalit …). The "1942 original" is Larry Hanson's lattice
(see Xenharmonikon XII below). p.36: "Notes on Tree Notation shown ref.
Hanson Keyboard, done in 1989 by Erv Wilson" — Ogham tree-alphabet note
names on the Hanson layout. p.37: "19/72 scale on 4/15 Keyboard (Hanson kbd
geometry) ©1992". Ragas as dot-patterns on a fixed 53-tone kleismic lattice
= murchana/mode-selection inside a constant background structure.
→ **MUR-002** (primary source for raga-as-subset-selection),
**MOS-LAT** (53 = kleismic convergent), **SUBSET-MEL**.
Note: root-level `LatticingRagaScales.pdf` (25 pp) is a shorter duplicate
of this batch item.

**`2010_02_24/Hanson/Hanson53TKbdLayout.pdf`** (18 pp; read 1–2).
This is **Xenharmonikon XII (1989, ed. Daniel Wolf)** — contents page:
Erv Wilson, "**D'ALESSANDRO, LIKE A HURRICANE**" p.1; John Chalmers,
"Tritriadic Scales and Complexes, Part Three" p.39; **Larry A. Hanson,
"Development of a 53-Tone Keyboard Layout"** p.68. Hanson's own origin
story (p.2 of the scan, verbatim): *"In the late summer of 1942 I decided
to numerically compare the tones of the 53-tone scale to those of just
intonation. Lacking a list of just intonation tones to use in such a
comparison, I constructed what I now call the 'Major-Minor Triadic
Lattice'"* — Caltech senior, fiancée Evelyn Olmsted the musician. So the
BRIDGE-000 primary source (D'Alessandro) and the kleismic primary source
(Hanson 53) are the **same journal issue**, physically bound together in
this archive item.
→ **BRIDGE-000/001, MOS-LAT, MUR-002**.

**`2010_02_24/Hanson/HnsnGralGeomStrrGrid.pdf`** (14 pp; read 1–2).
"Starr-Switch Grid, Showing Hanson's 15-row Geometry, and the 7-tone &
11-tone scales (with alternate fingerings) ©2000 Ervin M. Wilson"; p.2 same
grid with the 34-tone scale, ©1994. The kleismic MOS cardinality ladder
(7, 11, …, 34) laid onto physical key-switch hardware; Gral-adjacent.
→ **MOS-LAT** (kleismic MOS levels), **Gral keyboard code** (`Brun+Gral.cpp`).

### Meru / recurrent sequences (meta-tunings)

**`2010_02_26/Meru/ScalesOfMtMeru.pdf`** (24 pp; read 1–4).
"The Scales of Mt. Meru ©1993 by Erv Wilson (work in progress)." p.1:
Colin McPhee quote on the Meru mountain symbol (the name's origin). p.2:
"Matrix; with Piṅgala's Meru Prastāra, and Uath Gral Keyboard, ©2001" —
includes the **"Evangelina" keyboard setting** (17-degree Gral hexagons
with ratios; cf. `Wilson_Evangelina22.scl` below) and cites A.N. Singh,
"On the use of series in Hindu mathematics", *Osiris* 1936. p.3 (Fig 1):
Pascal's triangle with Fibonacci diagonals, "Aₙ = Aₙ₋₂ + Aₙ₋₁, Aₙ/Aₙ₋₁
converges on 1.618033989". p.4 (Fig 2): "Bₙ = Bₙ₋₃ + Bₙ₋₁ converges on
1.465571232", annotated "Pelog". The engine of every Meta-tuning: diagonal
recurrences of Mt. Meru → limit ratios → generators.
→ **MOS-LAT** (noble/metallic generators as recurrence limits), **ET program**.

**`2010_02_26/Meru/MetaMeantoneMavila.pdf`** (22 pp; read 1–3). **The find
of the pass.** p.1: "**On Complementary Proportional Triads** ©1995 by Erv
Wilson" — defines Meta-Mavila (Pₙ = 2Pₙ₋₄ + Pₙ₋₃, → 1.35320996420, i.e.
generator log₂ = .436385705396) and Meta-Meantone (Hₙ = 2(Hₙ₋₄ + Hₙ₋₃),
→ 1.49453018048, log₂ = .579692031034) **as the recurrent sequences whose
limits make a proportional triad recur inside the 7-tone MOS** — one
sequence per triad orientation, "complementary". p.2 (dated June 10, 1995):
*"This is the recurrent sequence for 4-'5'-'6' arith. mean (−3=5)"*, with
HP-calculator program, ref. "Linear Tuning of 4-'5'-'6' arithmetic mean
(−3=5) by Erv Wilson 1989" and "Ref: Chopi Scale from Mavila". p.3:
Meta-Mavila CF zigzag (1/2, 1/3, 2/5, 3/7, 4/9, 7/16, 10/23, 17/39, 24/55,
31/71 …). This is Wilson stating, in 1995, the exact objective the triad
harness scores: **pick the generator so the arithmetic-mean (proportional)
triad lands on scale degrees**. The Meta-tunings are fixed points of the
harness's P-count.
→ **MOS-LAT** (hot spots = these fixed points), **PARETO**, scorer
calibration targets; the natural "Meta-Hanson" template — unnamed by Wilson.

**`2010_02_26/Meru/MeruMisc.pdf`** (20 pp; read 1–3).
"Peirce–Novaro–Fibonacci Triaxial Grid ©2002 by Ervin M. Wilson"
(27 Apr 02): one triangular grid carrying three recurrences on three axes
(Fibonacci Fₙ = Fₙ₋₂+Fₙ₋₁, Novaro Hₙ = Hₙ₋₁+(Hₙ₋₁−Hₙ₋₂), Peirce); p.2 the
Novaro–Fibonacci grid as a full number table (22 Apr 02); p.3 golden-section
and ¼-comma-meantone-fifth (.576002) zigzag comparisons (18 Jul 2003).
Late-period Wilson systematizing generator arithmetic — the same "organize
hot spots by generator arithmetic" program MOS-LAT-002's null pointed to.
→ **MOS-LAT-002 follow-up** (CF digit statistics).

**`2010_02_25/Recurrent/HarrisnResonantTriad.pdf`** (30 pp; read 1–2).
Cover letter, Wilson to John [Chalmers], Nov 28 1992, verbatim: *"In these
Harrisonian resonant triads I am attempting to set a rigorous format from
which all the remaining sets can be readily inferred and calculated. I find
that even up to a 5-tone chain context a number of important relationships
have been broadly overlooked. The acoustic gold value (1.618…) crops up in
some of these, in the calculations — I would guess that gold lies just
below the surface in all, altho I cannot prove it."* p.2: coupled
fixed-point iteration A = √B, B = (A+2)/2 → generator 1.2807764064
(log₂ = .357018636 ≈ 428.4¢), with MOS zigzag 1/2, 1/3, 2/5, 3/8, 4/11,
5/14, 6/17, 11/31. Wilson's 1992 conjecture — **φ underlies resonant-triad
structure generally** — is precisely the noble-generator hot-spot
phenomenon MOS-LAT measures (and could now be graded against moslat002's
corpus-wide data).
→ **MOS-LAT, PARETO**; candidate H for a follow-up run.

### MOS / 3-gap (LAT-MEL, H-L4)

**`2010_02_20/MOS/GoldenGenerators.pdf`** (3 pp; read all).
"**64 Golden Generators for Two-Interval Patterns (MOS)** ©1993 by Erv
Wilson": a table of 64 noble generators as octave fractions, each with its
"pre-gold" and "gold" zigzag of convergents, plus (p.3) the HP-calculator
program "to calculate all golden sections". **This is the MOS-LAT corpus,
hand-computed in 1993.** Spot-checks: #18 = .264308496 → 317.17¢ — the
noble minor third that tops both MOS-LAT corpora; #43 = .381966011 = 1/φ²
→ 458.36¢; #22 = .276393202 (complement 868.33¢); #54 = .419821271 →
503.79¢. All four MOS-LAT-001 generators are rows of Wilson's table (up to
octave complement).
→ **MOS-LAT-001/002** (the corpus's primary source), **PARETO**.

**`2010_02_20/MOS/MOSMisc.pdf`** (12 pp; read 1–2).
p.1: "**The 3-gap theorem (Steinhaus conjecture) revisited** ©2005 by Ervin
M. Wilson, work in progress" — spiral diagram + 2GP/3GP gap-pattern table
for the 12-of-Pythagorean chain, annotated "Bilawal Tonic", noting
2187/2048 vs 16/15 skhisma (1.95¢). p.2: "Moments of Symmetry (MOS), where
the Octave has 19 steps and the Generator has 11 steps ©1998", with refs:
*"see wilson, letter to John Chalmers 26 April, 1975"* and *"The Three Gap
Theorem (Steinhaus Conjecture), Tony van Ravenstein, J. Austral. Math. Soc.
(Series A) 45 (1988), 360–370"* — **the identical citation SPEC.md's H-L4
carries**. Wilson was still working the rank–gap question in 1998–2005;
the archive holds his own paper trail for H-L4 (the 21 Aug 1965 Chalmers
letter is the earlier end; this cites a 26 Apr 1975 letter — likely in
`2010_02_24B/CPS B/CPSLetterToChalmers.pdf` or the Brun folders, unread).
→ **LAT-MEL / H-L4**, **MUR-002** (murchana of Bilawal).

### CPS / eikosany / dekany (CS-EIK, SHADOW, SUBSET-MEL, BRIDGE)

**`2010_02_24B/CPS B/Eikosany.pdf`** (34 pp; read 1–3).
p.1: "**THE EIKOSAKTY** shown as a basis for pitch tables, issued by Erv
Wilson **23 June 1967**" — the eikosany under its earliest name, with
frequency tables (240–495), "double linkage members" circled, and
"*members of 3·5·7·11 hexany alternate or complementary set*" starred —
embedded-hexany addressing in 1967. p.2: "Pre-issue by Erv Wilson Aug 1968"
— a **{1,3,7,9,11,15} eikosany** pitch table whose degree column contains
parenthesized collision/alternate entries ((3·9·33), (1·7·5), 373.33,
513.33) — Wilson hand-marking the val-tie/collision phenomenon that
LAT-MEL-001 machine-verified 58 years later. p.3: the Euler-genus
double-cube lattice of the same set.
→ **CS-EIK-001** (the {1,3,7,9,11,15} seed! see 22-tone templates below),
**LAT-MEL-001** (collisions), **SUBSET-MEL** (hexany addressing).

**`22-eikosany-templates.pdf`** (root, 27 pp; read 1–2).
Kraig Grady, dated 29-7-21, with Praveen Venkataramana. Verbatim: *"22 tone
represents the most compact constant structure scale to house the 20 tone
Eikosany"*; Wilson had found **two** articulate housings ("each member has
it own scale degree") and used them for the **1-3-7-9-11-15** and
**1-5-7-9-11-15** eikosanies; Venkataramana proved there are **only 16**
articulate 22-tone templates (P1–P16 listed on p.2; Wilson's two are P16
and P8). **Machine cross-check run against `../lattice/results/cseik001.jsonl`
(2026-07-29): both Wilson seeds are true 20-tone eikosanies but NOT bare
constant structures (24 and 20 CS violations respectively)** — yet they are
injectively addressable at N = 22. That is the G-007/BRIDGE premise in
primary-source form: the bare CPS fails melodically; the embedding modulus
rescues it. Note both Wilson seeds contain composites (9, 15), matching
CS-EIK-001's "composites necessary"; the CS-EIK flagship {1,7,9,11,15,29}
is Wilson's {1,3,7,9,11,15} with 3 → 29.
→ **BRIDGE-002** (eikosany embedding, modulus 22), **CS-EIK-001**,
**SUBSET-MEL**. High-value unread: pp.3–27 (the 16 templates + harmonic sets).

**`2010_02_24B/CPS B/CPSLetterToChalmers.pdf`** (52 pp; read 1–2).
"Letter to John Chalmers from Erv Wilson, Apr 4 1971." Constructs the
{1,3,5,7}×{1,3,5,7} cross-set A, its point-for-point complement B, shows
A∩B = the 2)4 hexany and A∪B = the "Mandala"/stellate hexany. Verbatim:
*"The fact that A and B are complements, and share, in common, the hexany,
provides the aesthetic justification for uniting all members of A and B
into a single set"*; closes by defining the **stellate eikosany** via the
3-dimensional {1,3,5,7,9,11}³ cross-set intersecting its complement at the
eikosany. 50 more pages unread — likely the mother lode for CPS derivation
history (and possibly the 1975/1965 letters H-L4 cites).
→ **SHADOW-001** (shared-factor connectivity as Wilson's own "aesthetic
justification"), **SUBSET-MEL**, **CS-EIK**.

**`2010_02_24/CPS/DAlessandroFull.pdf`** (12 pp; read 1–3).
Clean drafting-quality plates: pp.1–2 the stacked-cube 3D lattice of the
D'Alessandro/EG6 genus; p.3 the complete 2⁶ power-set of {1,3,5,7,9,11}
arranged by Pascal level — point, hexad, 15 dyads, **eikosany (center
star)**, 15 tetrads, 6 pentads, apex. The geometric companion to fig 24.
→ **BRIDGE-000/002**, **EG6 root-mapping feature** (the subset-keyboard
family in one picture).

**`1-3-5-7-9-11dekanyCS.jpg`** (root; read).
A matrix chart: rows = the twelve dekanies 2)5/3)5 of each 5-subset of
{1,3,5,7,9,11} (labels "2)5 1-3-5-7-9" … "3)5 1-3-5-7-9"); columns = a
shared degree axis labeled by product tones (1, 1·3·7·9·11, 3·5·9, (7·11/9),
9, …, with some parenthesized alternates); black dots = tones present,
red dots marking a distinguished subset per row. Filename says "dekany CS":
the family of dekanies referred to one common constant-structure grid.
→ **SUBSET-MEL** (dekany-in-eikosany addressing), **CS-EIK**.

**`dekany_14_tone_constant_structure/`** (rtf + 2 gif).
A letter from Kraig **to Marcus**: *"Here is one chart that shows how we
figured out the constant structure of the 1-3-7-9-15 dekany"* — a
hand-executed **CS-completion algorithm**: scan interval sizes by layer
(16/15, 15/14, 9/8, 8/7, 7/6, 5/4…), find size-classes subtending unequal
step counts, insert tones ("+1") until every size-class is
step-consistent — 10 tones → 14, "the new intervals have to be consistent
too with other examples of like intervals." This is a constructive
CS-repair operator, by hand — the exact inverse of `melodic.py`'s CS
checker, and an obvious candidate experiment (minimal CS completion of
CPS scales; cf. `Wilson-Grady_1-3-5-7-9 doubledekany.scl`, 14 tones,
"Constant structure scale of the 2)5 and 3)5 1-3-5-7-9 dekanies").
→ **SUBSET-MEL / CS-EIK follow-up** (CS-completion as an operator),
**MUR-002**.

### Keyboards / Gral / ET program

**`Pages_from_xen2_8_31_4_7_gral_mapping.jpg`** (root; read).
A Xenharmonikon 2 page: "A. Changing the Shape — 1. Eliminates dead-space &
increases tactile ratio. 2. Major/Minor scales convenient in all keys.
Meantone suggested. 3. Just scales possible, but less convenient (in
parentheses)… Digitals are identified with Pythagorean & Fokker's 31-tone
symbols." Elongated-hex 31-tone Bosanquet/Gral key layout with JI ratios in
parentheses on the naturals. The 31-tone keyboard template BRIDGE-000's
val ⟨31,49,72,87,107⟩ addresses.
→ **BRIDGE-000/001**, **Gral** (`Brun+Gral.cpp`), **ET program**.

### Scala tunings (named Wilson/Grady exports, 2021-09-30)

**`SCALA-tunings_kraig_grady_20210930/`** — 23 `.scl` + 2 root-level
duplicates (`Grady_Mirror_Meta-Slendro12/17.scl`). Full inventory, with
description lines read from each file:

| file | N | description (from file) |
|---|---|---|
| Grady_Beebalm12-Grady | 12 | 17-limit 12-tone scale |
| Grady_Centaura | 12 | 11-limit variation on Centaur (Grady 2019) |
| Grady_Mirror_Meta-Pelog7/9/20 | 7/9/20 | pelog from 'fourth'-based recurrent series |
| Grady_Mirror_Meta-Slendro12/17 | 12/17 | slendro from 'fifth'-based recurrent series |
| Poole17 | 17 | Rod Poole's 17-note guitar tuning |
| **Wilson-Grady_1-3-5-7-9 doubledekany** | **14** | **"Constant structure scale of the 2)5 and 3)5 1-3-5-7-9 dekanies"** |
| Wilson-Grady_Meta-Mavila7/9/16 | 7/9/16 | Mavila + rotation supersets |
| Wilson-Grady_Meta-Ptolemy7/10/17 | 7/10/17 | Meta-Ptolemy ("starting on 49") + rotation supersets |
| Wilson_11 limit pelog 9 | 9 | modulates 5- and 7-tone pelogs in all keys |
| **Wilson_Dalessandro_filled_keyboard** | **38** | **"Dalessandro with two 1-3-7-9-11-15 eikosanies with filled blanks for keyboard"** — first degree 2079/2048, a BRIDGE-000 kernel comma |
| Wilson_Dual11tone11-limit | 22 | harmonic+subharmonic 11-limit pairs a 3/2 apart |
| **Wilson_Evangelina22** | **22** | "22-tone helix-like favorite of Erv Wilson" (the Uath/Gral "Evangelina" setting, cf. ScalesOfMtMeru p.2) |
| Wilson_Helixsong10/14/24 | 10/14/24 | interlocked harmonic-series pairs a 3/2 apart |
| Wilson_Meta-Meantone19 | 19 | "Wilson's Meta-Meantone seeded with just diatonic. Good for 5, 7 and 12 tone subsets." |

Cross-reference notes: (a) the meta-family here is
{Mavila, Ptolemy, Pelog, Slendro, Meantone} — **no Meta-Hanson**, again;
(b) `Wilson_Dalessandro_filled_keyboard.scl` is a 38-tone ground truth to
diff against `results/bridge000.json`'s 38-tone reproduction — a free
BIT-EXACT check; (c) the doubledekany answers "which 14-tone CS did Kraig
mean" in the `dekany_14_tone_constant_structure` letter; (d) the Meta-*
supersets ("good for rotating…") are murchana carriers → MUR-002 ear-check
stock; every `.scl` here is implicitly a standing ear-check gate.

---

## Connections found (the top table)

1. **HansonMisc.pdf p.4** — Wilson's hand count "13 Major triads and 13
   minor triads in the 19-tone scale (MOS) with a 5-step generator", with
   "Kleismatic equivalences": the harness objective computed by hand at the
   generator (~317¢) both MOS-LAT runs found as the global hot spot.
2. **GoldenGenerators.pdf (all 3 pp)** — Wilson's 1993 table of **64 noble
   generators with zigzags is the MOS-LAT corpus**; entry #18
   (.264308496 = 317.17¢) is the hot-spot generator; all four MOS-LAT-001
   nobles appear (up to complement). His HP-calc program is on p.3.
3. **MetaMeantoneMavila.pdf pp.1–3** — "On Complementary Proportional
   Triads" (1995): Meta-tunings **defined** as recurrences whose limits make
   proportional (arithmetic-mean) triads recur — Wilson stating the triad
   harness's objective function as a design principle; plus
   HarrisnResonantTriad.pdf p.1 (1992): "gold lies just below the surface
   in all, altho I cannot prove it" — the noble hot-spot conjecture,
   testable today against moslat002.
4. **22-eikosany-templates.pdf pp.1–2 + cseik001.jsonl cross-check** —
   Wilson's two 22-tone eikosany housings ({1,3,7,9,11,15}, {1,5,7,9,11,15},
   both composite-bearing) are **not bare constant structures (24/20
   violations) yet are injectively articulate at N = 22**: the
   G-007/BRIDGE "embedding rescues melody" premise, in primary sources,
   with Venkataramana's completeness result (only 16 templates) attached.
   The 1968 pre-issue of the same seed (Eikosany.pdf p.2) already marks
   collision degrees in parentheses.
5. **Hanson53TKbdLayout.pdf pp.1–2** — Xenharmonikon XII binds Wilson's
   "D'Alessandro, Like a Hurricane" (BRIDGE-000's source) and Hanson's
   "Development of a 53-Tone Keyboard Layout" (the 1942 Major-Minor
   Triadic Lattice origin) in one issue; LatticingRagaScales.pdf then
   plots **ragas as red-dot subsets on that 1942 lattice redrawn at 53** —
   the murchana program (MUR-002) and the kleismic program are one thread
   in Wilson's own practice.
6. *(bonus)* **MOSMisc.pdf p.2** — Wilson's 1998 MOS sheet cites van
   Ravenstein 1988 and a 26 Apr 1975 Chalmers letter: the archive-side
   paper trail for SPEC.md H-L4.

## High-value unread (names say relevant; not in this page budget)

- `2010_02_24B/CPS B/CPSLetterToChalmers.pdf` pp.3–52 — more 1971(+?)
  letters; hunt for the 21 Aug 1965 and 26 Apr 1975 letters H-L4 cites.
- `22-eikosany-templates.pdf` pp.3–27 — the 16 templates + Venkataramana's
  harmonic sets (BRIDGE-002 ground truth).
- `2010_02_25/Recurrent/ZigZags.pdf` (80 pp) + `CommaZigZags(2).pdf`
  (13+38 pp) — generator zigzag arithmetic at scale (MOS-LAT-002 follow-up:
  CF digit statistics).
- `2010_02_26/Meru/PrimarySecondary.pdf` (74 pp) + `SecondarySeries.pdf`
  (58 pp) + `MountainSeedlings.pdf` (32 pp) — the full recurrence zoo; if a
  kleismic ("Meta-Hanson"-shaped) recurrence exists anywhere, it is here.
- `2010_02_24B/CPS B/Hebdomekontany.pdf` (44 pp), `LargerCPS.pdf` (45/46 pp
  two copies), `PreEiko.pdf` (42 pp), `HexanyRelated1.pdf` (53 pp),
  `eikosanystructures.pdf` (49 pp), `HexanyStellatesExpansions.pdf` (48 pp)
  — CPS beyond 6 factors; SUBSET-MEL source material.
- `2010_02_15/DiophantineKbd.pdf` (40 pp) — keyboard/val addressing.
- `2010_02_20/MOS/SecndMOS(afterLtoJC).pdf` (11 pp) — "after Letter to
  J[ohn] C[halmers]" — possibly the MOS letter itself, redrawn.
- `2010_02_12/HansonKeyboard.pdf` + `HansonKeyboardB(lge).pdf` (11+8 pp),
  `2010_02_23/BosanquetNonHex/HansonDots.pdf` (10 pp) — more kleismic
  keyboard geometry.
- `Marcus/` (27 files) — Marcus's own 2018 TuningAesthetics notebooks
  (`hexany_triads_tunings.json`, ipynb) — pre-harness prior art by the PI.
- `chalmers/`, `tetrachord/DivisionsOfTheTetrachord.pdf` — Chalmers-side
  context; `PhDThesisFINALREVISIONSmirrored.pdf` (root) — unidentified
  thesis, OCR layer mentions Hanson and slendro/mavila.

## Method + reproducibility

- Catalog: `find`/`stat -f %z`/`mdls -raw -name kMDItemNumberOfPages`,
  emitted as JSONL; `.DS_Store` and `.ipynb_checkpoints` excluded.
- Text sweep: `pdftotext` (poppler) over all PDFs to a scratch dir
  (discarded; no archive-derived bulk text is committed), used for
  name/keyword hunting only. 274/304 PDFs carry a text layer; handwriting
  OCR quality is poor, so absence-of-hits is evidence, not proof.
- Visual reads: 18 items, ~53 pages, cited above per item.
- CS cross-check: pure read of `experiments/lattice/results/cseik001.jsonl`
  (seed lookup + winner filter); no scorer code executed, no frozen file
  touched.
