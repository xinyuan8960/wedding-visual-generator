"""Deterministic two-initial monogram composition.

Takes two glyphs (already loaded via layout.glyphs.Font) and an arrangement, and
computes where each glyph goes in a square canvas: a scale shared by both letters
(monograms use one consistent type size, not independently-stretched letters), and a
translation per letter. No randomness here -- the seed in spec.json is reserved for
choosing between layout *variants* once more than one exists per arrangement (phase 4+);
today there is exactly one deterministic result per (chars, arrangement, style ratios).

Geometry walkthrough for the two horizontal arrangements (side-by-side, interlocking)
and the one vertical arrangement (stacked) below: everything is computed in font units
first (y-up, baseline at 0), as a "pair-local" box anchored at (0, 0), and only
converted to canvas pixels (y-down, origin top-left) in the last step. circular-badge
reuses the side-by-side math and then additionally shrinks the scale if the pair's
bounding box doesn't fit inside the canvas's inscribed circle.
"""
from __future__ import annotations

from dataclasses import dataclass

from fontTools.misc.transform import Transform

from .glyphs import Bounds, Font

# Gap between the two letters, as a fraction of their average extent along the layout
# axis. Interlocking uses a *negative* gap (controlled overlap) instead.
_GAP_RATIO = 0.18
_INTERLOCK_OVERLAP_RATIO = 0.32
_CIRCULAR_GAP_RATIO = 0.10

ARRANGEMENTS = ("interlocking", "stacked", "circular-badge", "side-by-side")


class InitialsError(ValueError):
    pass


def initial_of(name: str) -> str:
    """First alphabetic character of a (Latin) name, uppercased."""
    for ch in name:
        if ch.isalpha():
            return ch.upper()
    raise InitialsError(f"No alphabetic character found in name {name!r}")


@dataclass(frozen=True)
class _PairLayout:
    """Pair-local placement, pre-scale, pre-canvas. Font units, y-up."""

    width: float
    height: float
    y_min: float  # lets callers recover the pair-local vertical center
    shift_a: tuple[float, float]  # (tx, ty) to add to glyph A's own font-space coords
    shift_b: tuple[float, float]


def _horizontal_pair(bounds_a: Bounds, bounds_b: Bounds, gap_ratio: float) -> _PairLayout:
    ax0, ay0, ax1, ay1 = bounds_a
    bx0, by0, bx1, by1 = bounds_b
    width_a, width_b = ax1 - ax0, bx1 - bx0
    gap = gap_ratio * ((width_a + width_b) / 2)

    shift_a = (-ax0, 0.0)
    shift_b = (width_a + gap - bx0, 0.0)

    y_min = min(ay0, by0)
    y_max = max(ay1, by1)
    width = width_a + gap + width_b
    return _PairLayout(width=width, height=y_max - y_min, y_min=y_min, shift_a=shift_a, shift_b=shift_b)


def _vertical_pair(bounds_a: Bounds, bounds_b: Bounds, gap_ratio: float) -> _PairLayout:
    """A stacked above B."""
    ax0, ay0, ax1, ay1 = bounds_a
    bx0, by0, bx1, by1 = bounds_b
    width_a, width_b = ax1 - ax0, bx1 - bx0
    height_a, height_b = ay1 - ay0, by1 - by0
    width = max(width_a, width_b)
    gap = gap_ratio * ((height_a + height_b) / 2)

    shift_b = ((width - width_b) / 2 - bx0, -by0)
    bottom_of_b_top = height_b + gap
    shift_a = ((width - width_a) / 2 - ax0, bottom_of_b_top - ay0)

    height = height_a + gap + height_b
    return _PairLayout(width=width, height=height, y_min=0.0, shift_a=shift_a, shift_b=shift_b)


def _fit_scale_to_box(pair: _PairLayout, box_size: float) -> float:
    if pair.width <= 0 or pair.height <= 0:
        raise InitialsError("Degenerate pair bounding box; check the glyphs have outlines")
    return min(box_size / pair.width, box_size / pair.height)


def _fit_scale_to_circle(pair: _PairLayout, scale: float, radius: float) -> float:
    """Shrink `scale` if the scaled pair bbox's corners would land outside the circle
    of `radius` centred on the pair's own center. Exact for a bbox whose center
    coincides with the circle's center (true here, since we center on the pair bbox)."""
    half_diagonal = ((pair.width / 2) ** 2 + (pair.height / 2) ** 2) ** 0.5 * scale
    if half_diagonal <= radius or half_diagonal == 0:
        return scale
    return scale * (radius / half_diagonal)


def _place(
    font: Font,
    char_a: str,
    char_b: str,
    pair: _PairLayout,
    scale: float,
    canvas_size: float,
) -> list[dict]:
    cx = cy = canvas_size / 2
    pair_center_y = pair.y_min + pair.height / 2
    tx_center = cx - scale * pair.width / 2
    ty_center = cy + scale * pair_center_y

    glyphs = []
    for char, (shift_x, shift_y) in ((char_a, pair.shift_a), (char_b, pair.shift_b)):
        dx = scale * shift_x + tx_center
        dy = -scale * shift_y + ty_center
        transform = Transform(scale, 0, 0, -scale, dx, dy)
        bx0, by0, bx1, by1 = font.bounds(char)
        canvas_bounds = (
            round(scale * bx0 + dx, 3),
            round(-scale * by1 + dy, 3),
            round(scale * bx1 + dx, 3),
            round(-scale * by0 + dy, 3),
        )
        glyphs.append(
            {
                "char": char,
                "d": font.path_d(char, transform),
                "bbox": list(canvas_bounds),
            }
        )
    return glyphs


def compose_monogram(
    char_a: str,
    char_b: str,
    arrangement: str,
    whitespace_ratio: float,
    canvas_size: float = 512.0,
    font: Font | None = None,
) -> dict:
    """Place two initials on a `canvas_size` x `canvas_size` canvas.

    Returns a dict with the overall canvas size, the arrangement used, and one entry per
    glyph (character, SVG path 'd' already in canvas coordinates, and its bounding box in
    canvas coordinates) -- everything downstream (template rendering, QA) needs is here,
    nothing is implicit.
    """
    if arrangement not in ARRANGEMENTS:
        raise ValueError(f"Unknown arrangement {arrangement!r}; expected one of {ARRANGEMENTS}")
    font = font or Font()
    bounds_a, bounds_b = font.bounds(char_a), font.bounds(char_b)
    content_box = canvas_size * (1 - whitespace_ratio)

    if arrangement == "stacked":
        pair = _vertical_pair(bounds_a, bounds_b, _GAP_RATIO)
        scale = _fit_scale_to_box(pair, content_box)
    elif arrangement == "interlocking":
        pair = _horizontal_pair(bounds_a, bounds_b, -_INTERLOCK_OVERLAP_RATIO)
        scale = _fit_scale_to_box(pair, content_box)
    elif arrangement == "circular-badge":
        pair = _horizontal_pair(bounds_a, bounds_b, _CIRCULAR_GAP_RATIO)
        scale = _fit_scale_to_box(pair, content_box)
        scale = _fit_scale_to_circle(pair, scale, radius=content_box / 2)
    else:  # side-by-side
        pair = _horizontal_pair(bounds_a, bounds_b, _GAP_RATIO)
        scale = _fit_scale_to_box(pair, content_box)

    glyphs = _place(font, char_a, char_b, pair, scale, canvas_size)
    return {
        "canvas_size": canvas_size,
        "arrangement": arrangement,
        "glyphs": glyphs,
    }
