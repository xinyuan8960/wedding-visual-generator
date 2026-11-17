"""Small axis-aligned bounding-box helpers shared by layout, rendering, and QA."""
from __future__ import annotations

Bbox = tuple[float, float, float, float]  # x0, y0, x1, y1


def union_bbox(boxes: list[Bbox] | list[list[float]]) -> Bbox:
    xs0 = [b[0] for b in boxes]
    ys0 = [b[1] for b in boxes]
    xs1 = [b[2] for b in boxes]
    ys1 = [b[3] for b in boxes]
    return min(xs0), min(ys0), max(xs1), max(ys1)


def bbox_overlap(a: Bbox | list[float], b: Bbox | list[float]) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1
