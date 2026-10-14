"""Brun3 — Viggo Brun's three-term algorithm on (O, G0, G1), a port of the iOS
Wilsonic implementation (Wilsonic_v_1_8_6/Wilsonic/Brun/Brun3.m, Marcus Hobbs
2016; see Erv Wilson, "Viggo Rhythm", anaphoria.com/ViggoRhythm.pdf).

Inputs are intervals in octaves with O > G0 > G1 > 0. Level 0 is the single
interval O. At each level the three current intervals are sorted large to
small, the largest A is replaced by A - B (calc "AB") or A - C (calc "AC"),
and in the step list every copy of the old largest step is replaced by its
two pieces, with the iOS "balance" rule: the piece B (or C) goes first
unless the previous step already equals it. Steps are integer triples over
(O, G0, G1), so every degree is an exact integer combination
a*O + b*G0 + c*G1 and a fitted lattice has a three-row val.

Stdlib only. RANK3-001 (LOG.md 2026-10-12) uses it; the frozen scorers are
not touched.
"""

from __future__ import annotations

MAX_LEVEL = 7   # iOS ABSOLUTE_MAX_BRUN3_LEVEL = 6 - 1 + 2 + 1 - 1
CALCS = ("AB", "AC")


def _value(co: tuple[int, int, int], O: float, g0: float, g1: float) -> float:
    return co[0] * O + co[1] * g0 + co[2] * g1


def brun3_levels(O: float, g0: float, g1: float, calc: str = "AB",
                 max_level: int = MAX_LEVEL) -> list[list[tuple[int, int, int]]]:
    """Step lists per level, each step an integer triple over (O, G0, G1)."""
    if not (O > g0 > g1 > 0):
        raise ValueError("require O > G0 > G1 > 0")
    if calc not in CALCS:
        raise ValueError("calc must be AB or AC")
    H: list[list] = [[O, (1, 0, 0)], [g0, (0, 1, 0)], [g1, (0, 0, 1)]]
    H.sort(key=lambda h: -h[0])
    scale: list[tuple[int, int, int]] = [H[0][1]]
    levels = [list(scale)]
    j = 1 if calc == "AB" else 2
    it = 0
    noop = 0
    while it < max_level:
        interval0 = H[0][1]
        newco = tuple(x - y for x, y in zip(H[0][1], H[j][1]))
        H[0] = [H[0][0] - H[j][0], newco]
        piece_new, piece_old = newco, H[j][1]
        out: list[tuple[int, int, int]] = []
        replaced = False
        for st in scale:
            if st == interval0:
                if out and out[-1] == piece_old:
                    out.extend([piece_new, piece_old])
                else:
                    out.extend([piece_old, piece_new])
                replaced = True
            else:
                out.append(st)
        scale = out
        if replaced:
            it += 1
            levels.append(list(scale))
        else:
            noop += 1
            if noop > 10:
                raise RuntimeError("Brun3: no step to subtend")
        H.sort(key=lambda h: -h[0])
    return levels


def degrees(steps: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Coefficient triples of the degrees from 1/1 (the first is (0, 0, 0))."""
    out = [(0, 0, 0)]
    acc = (0, 0, 0)
    for st in steps[:-1]:
        acc = tuple(x + y for x, y in zip(acc, st))
        out.append(acc)
    return out


def scale_cents(steps: list[tuple[int, int, int]], O: float, g0: float, g1: float,
                mode: int = 0) -> list[float]:
    """Pitch classes in cents of the scale rotated so that degree `mode` is 0."""
    cos = degrees(steps)
    base = _value(cos[mode], O, g0, g1)
    return [((_value(c, O, g0, g1) - base) * 1200.0) % (O * 1200.0) for c in cos]


def step_sizes(steps: list[tuple[int, int, int]], O: float, g0: float, g1: float,
               tol: float = 1e-9) -> list[float]:
    """Distinct step sizes in cents, ascending."""
    sizes: list[float] = []
    for st in steps:
        v = _value(st, O, g0, g1) * 1200.0
        if not any(abs(v - s) <= tol for s in sizes):
            sizes.append(v)
    return sorted(sizes)
