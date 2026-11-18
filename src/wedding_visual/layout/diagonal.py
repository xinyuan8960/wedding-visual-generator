"""Diagonal two-initial monogram joined by a script ampersand.

The first initial sits upper-left, the second lower-right, and a tall script '&' runs
across the opposite diagonal between them, overlapping both -- a common wedding-stationery
lockup. Positions and sizes start from fixed fractions of a square block, expressed below
as named constants rather than derived from any reference artwork's geometry.

The three must read as one interlocked mark, not three pieces side by side: the '&' has to
physically cross into each initial's ink. Fixed positions can't guarantee that -- an 'S'
and an 'I' leave very different gaps -- so `interlock` searches small, deterministic
adjustments (pull the initials toward the center, nudge the '&') for the least movement
that gives both initials a real but legible contact. See CONTACT_MIN / CONTACT_MAX.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..ink import area, flatten_svg_path, overlap_area, rasterize
from .glyphs import Font
from .placement import Placement

# Tuned by eye against rendered output: a taller ampersand (0.80) let its thick stroke
# swamp both initials; a shorter one (0.52) read as clutter between them.
INITIAL_CAP_HEIGHT = 0.34  # of block side
INITIAL_A_CENTER = (0.25, 0.25)  # (x, y) as fractions of the block, y down
INITIAL_B_CENTER = (0.73, 0.74)
AMPERSAND_HEIGHT = 0.62
AMPERSAND_CENTER = (0.50, 0.50)

# Contact = ink shared by the '&' and one initial, as a fraction of the '&''s own ink.
# Below CONTACT_MIN the '&' merely sits in the gap (reads as three separate pieces);
# above CONTACT_MAX it starts to bury the letter. Tuned by eye on rendered pairs.
CONTACT_MIN = 0.03
CONTACT_MAX = 0.10
# Search space, in scanline steps of block_size / RASTER_STEPS_PER_BLOCK.
RASTER_STEPS_PER_BLOCK = 160
MAX_PULL_STEPS = 12  # each initial toward the center (both axes). Capped: pulling P+J far enough
# to touch (20 steps) crammed the pair into a knot -- worse than an honest QA warning.
MAX_NUDGE_STEPS = 24  # how far the '&' may move from its nominal center (each axis)
SEARCH_STRIDE = 2


@dataclass(frozen=True)
class Interlock:
    pull: int  # steps each initial moved toward the center
    nudge: tuple[int, int]  # steps the '&' moved (x, y)
    contact_a: float
    contact_b: float
    found: bool  # False: no candidate met the contact band; nominal layout kept


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

    nominal = [
        Placement.centered(initials_font, char_a, initial_scale, *at(INITIAL_A_CENTER)),
        Placement.centered(ampersand_font, "&", amp_scale, *at(AMPERSAND_CENTER)),
        Placement.centered(initials_font, char_b, initial_scale, *at(INITIAL_B_CENTER)),
    ]
    step = block_size / RASTER_STEPS_PER_BLOCK
    fit = interlock(nominal, step)
    a, amp, b = nominal
    p = fit.pull * step
    return [
        replace(a, dx=a.dx + p, dy=a.dy + p),
        replace(amp, dx=amp.dx + fit.nudge[0] * step, dy=amp.dy + fit.nudge[1] * step),
        replace(b, dx=b.dx - p, dy=b.dy - p),
    ]


def interlock(nominal: list[Placement], step: float) -> Interlock:
    """Least-movement adjustment putting both contacts inside [CONTACT_MIN, CONTACT_MAX].

    Every shift is a whole number of scanline steps, so each candidate is just an index
    offset into rows rasterized once -- exact, deterministic, and fast. Cost: total
    movement, plus a penalty for lopsided contact (one initial gripped, the other barely
    touched). Ties break on the candidate order, which is fixed.
    """
    rows_a, rows_amp, rows_b = (rasterize(flatten_svg_path(p.to_dict()["d"]), step) for p in nominal)
    amp_ink = area(rows_amp, step)
    best: tuple[float, Interlock] | None = None
    for pull in range(0, MAX_PULL_STEPS + 1, SEARCH_STRIDE):
        # Initial B moves by -pull relative to the canvas, i.e. -2*pull relative to A.
        if overlap_area(rows_a, rows_b, step, b_dx=-2 * pull, b_drows=-2 * pull) > 0:
            break  # the initials themselves would collide; pulling further only worsens it
        for nx in range(-MAX_NUDGE_STEPS, MAX_NUDGE_STEPS + 1, SEARCH_STRIDE):
            for ny in range(-MAX_NUDGE_STEPS, MAX_NUDGE_STEPS + 1, SEARCH_STRIDE):
                ca = overlap_area(rows_a, rows_amp, step, b_dx=(nx - pull) * step, b_drows=ny - pull) / amp_ink
                if not CONTACT_MIN <= ca <= CONTACT_MAX:
                    continue
                cb = overlap_area(rows_b, rows_amp, step, b_dx=(nx + pull) * step, b_drows=ny + pull) / amp_ink
                if not CONTACT_MIN <= cb <= CONTACT_MAX:
                    continue
                cost = (abs(nx) + abs(ny) + 2 * pull) / MAX_NUDGE_STEPS + 4 * abs(ca - cb) / CONTACT_MAX
                if best is None or cost < best[0]:
                    best = (cost, Interlock(pull, (nx, ny), round(ca, 4), round(cb, 4), True))
    if best is None:
        ca = overlap_area(rows_a, rows_amp, step) / amp_ink
        cb = overlap_area(rows_b, rows_amp, step) / amp_ink
        return Interlock(0, (0, 0), round(ca, 4), round(cb, 4), False)
    return best[1]
