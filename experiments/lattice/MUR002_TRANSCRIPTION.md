# MUR-002 — transcription anchors from LatticingRagaScales.pdf (derived work; scan read in place, never vendored)

Source: `~/Documents/scans by Kraig/2010_02_24/Hanson/LatticingRagaScales.pdf`
(37 pp; a 25-pp duplicate sits at the archive root). Read 2026-08-18,
pp. 1–26 (pp. 27–35 unread; INDEX.md covers pp. 36–37: tree-notation and
19/72 keyboard sheets). Per the archive rule only derived anchors are
recorded here, with page citations; no image, no copy. Every ratio below
is what the hex on the figure says; the 53-degree numbers are the
figure's own and were machine-checked against 31·e3 + 17·e5 mod 53
(`tests/test_mur002.py`, all pass).

## The constant background (every page 1–23)

"Figure #1 — Major-Minor Triadic Lattice for 53 (redrawn from 1942
original)"; p.20 adds "From L. A. Hanson's Development of a 53-Tone
Keyboard Layout 1989" (Xenharmonikon XII — see INDEX.md, item
Hanson53TKbdLayout.pdf). Hexagonal 5-limit lattice: rows are chains of
fifths, the row above is a 5/4 up, so each hex has six neighbours
{3/2, 2/3, 5/4, 4/5, 6/5, 5/6}. Note names carry `/` (+81/80) and `\`
(−81/80) relative to a 5-limit spelling in which C = 1/1, E = 5/4,
A = 5/3, B = 15/8; every hex shows name, exact ratio, 53-EDO degree.
Nine rows are drawn (5⁻⁴ … 5⁺⁴); the 1/1 row runs \\Gb 1024/729 (26) …
//C# 2187/2048 (5); the 5-row \\Eb 2560/2187 (12) … //E# 10935/8192
(22); the 1/5-row \\Ebb 4096/3645 (9) … //E 6561/5120 (19). Bold zigzag
outlines mark a 53-tone fundamental region (not transcribed cell by
cell). Signed "E.W." at lower right of every sheet.

## p.20 — the 22-śruti set (the H-R2 / H-R5 object)

Margin, red ink: "Outlined in red is the theoretical scale of 22 steps,
of modern India. Note that 135/128 is minutely larger in magnitude than
256/243 (schismatically equivalent) as are 405/256 to 128/81, 1215/1024
to 32/27 and so forth. E.W. 1997". Red outline encloses 22 hexes with
red śruti numerals (0/22 at C); read left→right per row:

| row | hexes (name ratio [53-degree] {śruti}) |
|---|---|
| 5·3ᵏ | \D 10/9 [8] {3}, A 5/3 [39] {16}, E 5/4 [17] {7}, B 15/8 [48] {20}, /F# 45/32 [26] {11} |
| 3ᵏ | \Db 256/243 [4] {1}, \Ab 128/81 [35] {14}, \Eb 32/27 [13] {5}, \Bb 16/9 [44] {18}, F 4/3 [22] {9}, C 1/1 [0] {0/22}, G 3/2 [31] {13}, D 9/8 [9] {4}, /A 27/16 [40] {17}, /E 81/64 [18] {8}, /B 243/128 [49] {21}, //F# 729/512 [27] {12} |
| 3ᵏ/5 | \Db 16/15 [5] {2}, Ab 8/5 [36] {15}, Eb 6/5 [14] {6}, Bb 9/5 [45] {19}, /F 27/20 [23] {10} |

Sorted: 1/1, 256/243, 16/15, 10/9, 9/8, 32/27, 6/5, 5/4, 81/64, 4/3,
27/20, 45/32, 729/512, 3/2, 128/81, 8/5, 5/3, 27/16, 16/9, 9/5, 15/8,
243/128 (śruti 0–21; the red numerals agree with sorted rank wherever
legible). Derived, checked in the receipts: the 53-degrees are exactly
{31k mod 53 : k = −10..11}, i.e. modulo the schisma the set is a chain
of 22 fifths, positions −10..+11.

## pp. 2–19 — eighteen ragas as red dots (one hex each; C 1/1 always dotted)

Dots sit at the upper right of the note name inside the hex. Numbering
is Wilson's (18 down to 1). Ratios as placed (schismatic 5-limit
spellings kept exactly as drawn):

| # | raga | p. | hexes dotted (label ratio) |
|---|---|---|---|
| 18 | Nat Bhairav | 2 | C 1/1, D 9/8, E 5/4, F 4/3, G 3/2, /G# 405/256, B 15/8 |
| 17 | Madhubanti | 3 | C, D 9/8, /D# 1215/1024, /F# 45/32, G, /A 27/16, B 15/8 |
| 16 | Jogiya Todi | 4 | C, /C# 135/128, /D# 1215/1024, F 4/3, G, /G# 405/256, B |
| 15 | Bhairav | 5 | C, /C# 135/128, E 5/4, F, G, /G# 405/256, B |
| 14 | Anand Bhairav | 6 | C, /C# 135/128, E, F, G, A 5/3, B |
| 13 | No Name | 7 | C, /C# 135/128, /D# 1215/1024, /F# 45/32, G, /G# 405/256, //A# 3645/2048 |
| 12 | Lalit | 8 | C, /C# 135/128, E, F, /F# 45/32, /G# 405/256, B |
| 11 | Todi | 9 | C, /C# 135/128, /D# 1215/1024, /F# 45/32, G, /G# 405/256, B |
| 10 | Lalit₂ | 10 | C, /C# 135/128, E, F, /F# 45/32, A 5/3, B |
| 9 | Purvi | 11 | C, /C# 135/128, E, /F# 45/32, G, /G# 405/256, B |
| 8 | Marwa | 12 | C, /C# 135/128, E, /F# 45/32, G, A 5/3, B |
| 7 | Bhairavi | 13 | C, \Db 256/243, \Eb 32/27, F, G, \Ab 128/81, \Bb 16/9 |
| 6 | Asawari | 14 | C, D 9/8, \Eb 32/27, F, G, \Ab 128/81, \Bb 16/9 |
| 5 | Kafi | 15 | C, D 9/8, \Eb 32/27, F, G, /A 27/16, \Bb 16/9 |
| 4 | **Old Kafi** | 16 | C, \D 10/9, \Eb 32/27, F, G, A 5/3, \Bb 16/9 |
| 3 | Khamaj | 17 | C, D 9/8, E 5/4, F, G, A 5/3, \Bb 16/9 |
| 2 | Bilawal | 18 | C, D 9/8, E 5/4, F, G, /A 27/16, B 15/8 |
| 1 | Kalyan | 19 | C, D 9/8, E 5/4, /F# 45/32, G, A 5/3, B 15/8 |

Reading notes. (i) Every raga is a union of at most two fifth-chain
segments a 5/4 apart (the 3ᵏ row and the 5·3ᵏ row) — Wilson's
placements never leave those two rows; the flat-side thaats (Bhairavi,
Asawari, Kafi) are single Pythagorean chains. (ii) "Old Kafi" is the
ṣaḍja-grāma read on the 22-śruti set (śruti pattern 4-3-2-4-4-3-2:
0, 3, 5, 9, 13, 16, 18); modern Kafi (p.15) is the same shape with Ri
and Dha each a comma higher (9/8, 27/16). (iii) The madhyama-grāma is
NOT drawn on pp. 1–26; MUR-002 derives it (Pa → 40/27) and labels it so.
(iv) 135/128, 405/256, 1215/1024, 3645/2048 are the schisma-twins of the
22-śruti tones 256/243, 128/81, 32/27, 16/9 (Wilson's own p.20 note).

## pp. 21–23 — Boomsliter & Creel "extended reference patterns" (context)

p.21: "Outlined in red is the major extended reference pattern. See
Boomsliter & Creel, Organization in Auditory Perception, page 16. E.W.
1997" — the 1/1 row C…//C# with "etc". p.22: "…the minor extended
reference pattern…" — C, then the 1/5-row Eb…//A with "etc". p.23:
"Boomsliter & Creel, the blue extended reference pattern, see p.17.
Compare this with independently derived ratios for Marwa, Purvi, Lalit₂,
Todi, Lalit. Ref 17-Persian Version N. Indian Raga scales 1996 Erv
Wilson" — red outline = 1/1 row C…//C# ∪ 5-row E…//E# ("etc"): two
fifth-chains a 5/4 apart, exactly the raga-placement rule of note (i).

## pp. 24–26 — not raga material

p.24 "19-Tone Basic Set for Hanson Kbd Geometry, digital design by Erv
Wilson Feb 27, 1978" (5-limit hexes: 9/8, 5/4, 4/3, 27/25, 6/5, 144/125,
15/8, 25/24, 9/5, 1/1, 25/16, one hex labelled both Bbb 216/125 and
A# 125/72, 48/25, 3/2, 5/3, 125/96,
36/25, 8/5, 25/18, 6/5, 4/3). p.25 "19-Tone Tubulongs on a 4-11-4
Geometry, Design ©1978 by Erv Wilson, built by Glen Prior in 1978 for
Larry Hanson … scale & notation suggested by Larry Hanson" (53-degree
labels on the tubes). p.26 keyboard-geometry sheet: (3/11) Hanson 1942
Design A, (1/4), (1/3) Davis 1986, (4/15) Hanson Design B, (2/7)
"Wilson's variation on Hanson, 1978", over a 5-limit hex diamond
(1/1, 6/5, 5/4, 3/2, 5/3, 8/5, 4/3, 9/8, 15/8, 9/5).

## Related item, not Wilson (archive root, `BilawalDiamond22.jpg`)

"BILAWAL DIAMOND 22 — centered on 5-limit diamonds on tones of Bilawal
with each tone thus has 6 triads (3 harmonic 3 subharmonic) as possible
harmony. 7 transpositions of Bilawal, 3 transpositions of Pythagorean
diatonic. K. GRADY 20-10-23". A square 5-limit lattice with 23 labelled
nodes (label "10." appears at both 25/18 and 27/20): 1/1, 25/24, 16/15,
10/9, 9/8, 75/64, 6/5, 5/4, 81/64, 4/3, 27/20, 45/32, 729/512, 3/2,
25/16, 8/5, 5/3, 27/16, 16/9, 9/5, 15/8, 243/128, 25/18. Since 45/32
carries "11.", the consistent reading of the 22 numbered members is
Wilson's p.20 set minus {256/243, 32/27, 128/81, 27/20} plus {25/24,
75/64, 25/16, 25/18} (18 tones shared with Wilson's 22; the 27/20 node
is drawn but its "10." collides with 25/18 — an ambiguity of the
drawing, left as read). Recorded for context only; not scored in
MUR-002.
