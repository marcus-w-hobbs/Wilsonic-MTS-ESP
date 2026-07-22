"""Scala (.scl) export so archive entries are playable in Wilsonic.

Convention: the scale's lowest canonical degree becomes the implicit 1/1
(Scala never lists 1/1); remaining degrees are expressed relative to it
and the 2/1 octave is appended. This matches how the plugin maps degree 0
of the processed array to middle C (TuningImp::_update), so a hexany with
no absolute 1/1 still round-trips to the same sounding scale.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Iterable, Union

from scorer import RationalLike, canonical_rational_scale


def to_scala(
    description: str,
    ratios: Iterable[RationalLike],
    provenance: Iterable[str] = (),
) -> str:
    """Render a canonical JI scale as .scl text (exact ratios, no cents).

    `provenance` lines are written as Scala comments in the header block.
    Every file this harness emits MUST carry enough there to rebuild the
    tuning in the Wilsonic UI from scratch -- design name, the scale/subset
    selection, and every seed parameter -- so a .scl found on disk months
    later is never a dead end. See families.cps.wilsonic_recreation_lines.
    """
    scale = canonical_rational_scale(ratios)
    root = scale[0]
    relative = [degree / root for degree in scale[1:]] + [Fraction(2)]
    lines = [f"! {description}", "!"]
    for line in provenance:
        lines.append(f"! {line}")
    if provenance:
        lines.append("!")
    lines += [description, f" {len(relative)}", "!"]
    for r in relative:
        lines.append(f" {r.numerator}/{r.denominator}")
    return "\n".join(lines) + "\n"


def write_scl(
    path: Union[str, Path],
    description: str,
    ratios: Iterable[RationalLike],
    provenance: Iterable[str] = (),
) -> Path:
    """Write a .scl file and return its path."""
    out = Path(path)
    out.write_text(to_scala(description, ratios, provenance), encoding="ascii")
    return out
