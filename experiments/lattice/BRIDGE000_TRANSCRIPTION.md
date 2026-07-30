# BRIDGE-000 — transcription anchors from dal.PDF (derived work; scan read in place, never vendored)

Source: "D'Alessandro, Like a Hurricane", scan `…/ERV/scans by Kraig/Marcus/anaphoria/dal.PDF`
(39 pp). Figures read 2026-07-29. Per the archive rule, only derived
anchors are recorded here, with figure citations; the scan stays in iCloud.

## Figure 24 ("D'Alessandro", issued 1975, © 1989 by Erv Wilson)
"1.3.5.7.9.11 Combination-Product Set series mapped to modulus 31 & the
Bosanquet Keyboard." Eye-verified anchors:

| anchor | fig 24 shows | code reproduces |
|---|---|---|
| template: 1 | position 0, degree 0/31 | ✓ |
| template: 3 (circled) | +1, degree 18 | ✓ |
| template: 9 (circled) | +2, degree 5 | ✓ |
| template: 5 (circled) | +4, degree 10 | ✓ |
| template: 7 (circled) | +10, degree 25 | ✓ |
| template: 11 (circled) | +18, degree 14 | ✓ |
| Ø/1 at both edges | 0/31 and 31/0 (degree 0 duplicated) | ✓ |
| +31 hex | 3.7.9.11 / 1.3.7.9.11 at degree 0/31 | ✓ (2079/2048 with 1) |
| pigtail +9 | (7/3) | ✓ |
| pigtail +8 | (3².5.9) = 3⁴·5 | ✓ |
| pigtail +27 | (7.11/3) | ✓ |
| pigtail +36 | (11²) | ✓ |
| pigtail −1 | (3.5.7.9/11), "or 3̄" spelling | ✓ |

Degree arithmetic throughout: degree(p) = 18·p mod 31. The four pigtails
+8, +9, +26, +27 fill exactly the four holes in the EG6 subset-sum
positions {sums of {1,2,4,10,18}}, so the huygens chain −1..+36 is 38
CONSECUTIVE positions — visible in fig 24 as the unbroken hex array.

## Figures 26–27 (inverted "D'Alessandro", © 1989)
Same degree val; 11 lifted to −13 (≡ 18·18 ≡ −13·18 mod 31 → same degree
14). Fig 26's own legend marks the kernel commas on the keyboard:
"+ = 2079/2048, ✻ = 385/384" — Wilson annotated the comma pairs himself.
Fig 27 template eye-anchors: 1 at 0/31, 11 (circled) at −13 / degree 14.

## Out of scope (confirmed present, deferred to BRIDGE-000b)
Fig 23 + "Fig 23 continued" (© 1980): "Genus 3³.5.7.11² (& 8 pigtails)
mapped to Bosanquet pattern using negative (31-like) template" — the 1980
version. Fig 25: "The D'Alessandro Tuning" CPS-series chart, incl. "2
closely related Eikosanies" (1.3.7.9.11.15) — primary source for the
1968-style melodic-compatibility claims; relevant to SUBSET-MEL-001.

Machine-derived (not eye-checked cell-by-cell): the remaining EG6 hex
labels of fig 24. They are forced by the template + subset-sum arithmetic
the anchors pin down; any single-cell transcription doubt is dominated by
the seven-collision + comma-census match.
