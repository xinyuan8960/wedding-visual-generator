"""Diagonal two-initial monogram joined by a script ampersand.

The first initial sits upper-left, the second lower-right, and a tall script '&' runs
across the opposite diagonal between them, overlapping both -- a common wedding-stationery
lockup. Positions and sizes are fixed fractions of a square block, expressed below as
named constants rather than derived from any reference artwork's geometry.
"""
from __future__ import annotations

from .glyphs import Font
from .placement import Placement

# Tuned by eye against rendered output: a taller ampersand (0.80) let its thick stroke
# swamp both initials; a shorter one (0.52) read as clutter between them.
INITIAL_CAP_HEIGHT = 0.34  # of block side
INITIAL_A_CENTER = (0.25, 0.25)  # (x, y) as fractions of the block, y down
INITIAL_B_CENTER = (0.73, 0.74)
AMPERSAND_HEIGHT = 0.62
AMPERSAND_CENTER = (0.50, 0.50)


def compose_diagonal(
    char_a: str,
    char_b: str,
    initials_font: Font,
    ampersand_font: Font,
    block_x: float,
    block_y: float,
    block_size: float,
) -> list[Placement]:
    """Return placements for [initial A, ampersand, initial B], in paint order."""

    def at(frac: tuple[float, float]) -> tuple[float, float]:
        return block_x + frac[0] * block_size, block_y + frac[1] * block_size

    initial_scale = INITIAL_CAP_HEIGHT * block_size / initials_font.cap_height()
    _, ay0, _, ay1 = ampersand_font.bounds("&")
    amp_scale = AMPERSAND_HEIGHT * block_size / (ay1 - ay0)

    return [
        Placement.centered(initials_font, char_a, initial_scale, *at(INITIAL_A_CENTER)),
        Placement.centered(ampersand_font, "&", amp_scale, *at(AMPERSAND_CENTER)),
        Placement.centered(initials_font, char_b, initial_scale, *at(INITIAL_B_CENTER)),
    ]
