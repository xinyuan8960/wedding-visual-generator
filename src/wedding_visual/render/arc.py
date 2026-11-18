"""An open hairline arc that breaks wherever it would run into a glyph.

Gaps are found by sampling the arc and testing each sample against the glyphs' actual
filled outlines (fontTools' PointInsidePen), padded by a small clearance -- not against
their bounding boxes, which would cut far wider gaps than the ink requires (a K's
diagonal tail has a huge, mostly empty bbox).
"""
from __future__ import annotations

import math
from typing import Any

from ..layout.placement import Placement

_STEP_DEG = 0.5
_PAD_DIRECTIONS = [(math.cos(a), math.sin(a)) for a in (i * math.pi / 4 for i in range(8))]


def _blocked(x: float, y: float, obstacles: list[Placement], boxes: list[list[float]], pad: float) -> bool:
    for placement, (x0, y0, x1, y1) in zip(obstacles, boxes):
        if not (x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad):
            continue
        if placement.contains_canvas_point(x, y):
            return True
        if any(placement.contains_canvas_point(x + pad * dx, y + pad * dy) for dx, dy in _PAD_DIRECTIONS):
            return True
    return False


def open_arc(
    cx: float,
    cy: float,
    radius: float,
    start_deg: float,
    end_deg: float,
    stroke_width: float,
    obstacles: list[Placement],
    clearance: float,
) -> dict[str, Any]:
    """Arc from start_deg to end_deg (SVG convention: 0 = +x, 90 = down), clockwise."""
    boxes = [p.bbox() for p in obstacles]
    pad = clearance + stroke_width / 2

    segments: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    steps = int(round((end_deg - start_deg) / _STEP_DEG))
    for i in range(steps + 1):
        a = math.radians(start_deg + i * _STEP_DEG)
        x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
        if _blocked(x, y, obstacles, boxes, pad):
            if len(current) > 1:
                segments.append(current)
            current = []
        else:
            current.append((round(x, 2), round(y, 2)))
    if len(current) > 1:
        segments.append(current)

    d = " ".join("M" + " L".join(f"{x:g} {y:g}" for x, y in seg) for seg in segments)
    pts = [p for seg in segments for p in seg]
    half = stroke_width / 2
    bbox = (
        [min(p[0] for p in pts) - half, min(p[1] for p in pts) - half, max(p[0] for p in pts) + half, max(p[1] for p in pts) + half]
        if pts
        else None
    )
    return {"type": "open-arc", "d": d, "segments": segments, "stroke_width": stroke_width, "clearance": clearance, "bbox": bbox}
