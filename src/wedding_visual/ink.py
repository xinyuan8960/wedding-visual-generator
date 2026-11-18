"""Ink coverage of filled outlines, computed exactly per scanline (no raster library).

An outline is flattened to polygons, then each horizontal scanline is cut into the spans
the nonzero winding rule fills. Overlap between two shapes is the summed length of their
spans' intersections -- an area estimate whose resolution is the scanline step. Used by
the layout to make the connecting '&' actually touch both initials, and by QA to verify
it from the rendered path strings.
"""
from __future__ import annotations

from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path

Point = tuple[float, float]
Spans = list[tuple[float, float]]

_SAMPLES_PER_CURVE = 16


class FlattenPen(BasePen):
    """Collects each contour as a polyline, sampling curves at fixed parameter steps."""

    def __init__(self) -> None:
        super().__init__(glyphSet=None)
        self.contours: list[list[Point]] = []
        self._current: list[Point] = []

    def _moveTo(self, pt):
        self._current = [pt]

    def _lineTo(self, pt):
        self._current.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._current[-1]
        for i in range(1, _SAMPLES_PER_CURVE + 1):
            t = i / _SAMPLES_PER_CURVE
            u = 1 - t
            self._current.append(
                (
                    u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
                )
            )

    def _qCurveToOne(self, p1, p2):
        p0 = self._current[-1]
        for i in range(1, _SAMPLES_PER_CURVE + 1):
            t = i / _SAMPLES_PER_CURVE
            u = 1 - t
            self._current.append(
                (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])
            )

    def _closePath(self):
        if len(self._current) > 2:
            self.contours.append(self._current)
        self._current = []

    _endPath = _closePath


def flatten_svg_path(d: str) -> list[list[Point]]:
    pen = FlattenPen()
    parse_path(d, pen)
    return pen.contours


def row_spans(contours: list[list[Point]], y: float) -> Spans:
    """Filled x-intervals of the outline on scanline y (nonzero winding)."""
    crossings: list[tuple[float, int]] = []
    for contour in contours:
        n = len(contour)
        for i in range(n):
            (x0, y0), (x1, y1) = contour[i], contour[(i + 1) % n]
            if y0 == y1:
                continue
            if y0 <= y < y1 or y1 <= y < y0:
                x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                crossings.append((x, 1 if y1 > y0 else -1))
    crossings.sort()
    spans: Spans = []
    winding = 0
    start = 0.0
    for x, direction in crossings:
        before = winding
        winding += direction
        if before == 0 and winding != 0:
            start = x
        elif before != 0 and winding == 0 and x > start:
            spans.append((start, x))
    return spans


def rasterize(contours: list[list[Point]], step: float) -> dict[int, Spans]:
    """Spans for every scanline y = (k + 0.5) * step crossing the outline, keyed by k."""
    ys = [p[1] for c in contours for p in c]
    rows: dict[int, Spans] = {}
    for k in range(int(min(ys) // step), int(max(ys) // step) + 1):
        spans = row_spans(contours, (k + 0.5) * step)
        if spans:
            rows[k] = spans
    return rows


def spans_overlap(a: Spans, b: Spans, b_dx: float = 0.0) -> float:
    total = 0.0
    i = j = 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0] + b_dx)
        hi = min(a[i][1], b[j][1] + b_dx)
        if hi > lo:
            total += hi - lo
        if a[i][1] < b[j][1] + b_dx:
            i += 1
        else:
            j += 1
    return total


def area(rows: dict[int, Spans], step: float) -> float:
    return step * sum(x1 - x0 for spans in rows.values() for x0, x1 in spans)


def overlap_area(
    a: dict[int, Spans], b: dict[int, Spans], step: float, b_dx: float = 0.0, b_drows: int = 0
) -> float:
    """Shared ink of `a` and `b`, with `b` shifted by b_dx and by b_drows scanlines."""
    total = 0.0
    for k, spans_a in a.items():
        spans_b = b.get(k - b_drows)
        if spans_b:
            total += spans_overlap(spans_a, spans_b, b_dx)
    return total * step
