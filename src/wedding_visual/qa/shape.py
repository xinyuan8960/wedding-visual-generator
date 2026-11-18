"""Measure how blade-like an outline is.

- straight_ratio: the longest stretch of outline that runs diagonally (20-70 degrees)
  while staying within a hair of a straight line, divided by the shape's height. A
  script '&' whose dominant stroke is one long straight diagonal (reads as a blade or a
  sword) scores high; a looping, music-note-like one scores low. Horizontal runs are
  ignored: long flat exit swashes are an ordinary, graceful calligraphic flourish.

Deliberately no "curl" score from total turning angle: that is exactly 360 degrees for
every convex outline, so it measures compactness, not curl.

Measured on the geometry itself (flattened bezier outline), so it works the same on a
font glyph or on a rendered SVG path 'd' string.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path

_SAMPLES_PER_CURVE = 16
STRAIGHT_TOLERANCE = 0.012  # max deviation from the chord, as a fraction of height
# Only diagonal runs count as blade-like. A long *horizontal* straight run is usually a
# calligraphic exit swash (graceful); a long straight *diagonal* reads as a blade.
DIAGONAL_MIN_DEG = 20.0
DIAGONAL_MAX_DEG = 70.0


class _FlattenPen(BasePen):
    def __init__(self) -> None:
        super().__init__(glyphSet=None)
        self.contours: list[list[tuple[float, float]]] = []
        self._current: list[tuple[float, float]] = []

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


@dataclass(frozen=True)
class ShapeMetrics:
    straight_ratio: float


def _deviation(p, a, b) -> float:
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length == 0:
        return math.hypot(px - ax, py - ay)
    return abs(dy * (px - ax) - dx * (py - ay)) / length


def _is_diagonal(a, b) -> bool:
    angle = math.degrees(math.atan2(abs(b[1] - a[1]), abs(b[0] - a[0])))
    return DIAGONAL_MIN_DEG <= angle <= DIAGONAL_MAX_DEG


def _longest_straight_diagonal_run(points: list[tuple[float, float]], tol: float) -> float:
    n = len(points)
    ring = points + points  # allow runs that wrap past the contour's start point
    best = 0.0
    for i in range(n):
        j = i + 2
        while j < i + n:
            a, b = ring[i], ring[j]
            if any(_deviation(ring[k], a, b) > tol for k in range(i + 1, j)):
                break
            if _is_diagonal(a, b):
                best = max(best, math.hypot(b[0] - a[0], b[1] - a[1]))
            j += 1
    return best



def _dedupe(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = [points[0]]
    for p in points[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return out


def measure_contours(contours: list[list[tuple[float, float]]]) -> ShapeMetrics:
    contours = [_dedupe(c) for c in contours if len(c) > 2]
    ys = [p[1] for c in contours for p in c]
    height = max(ys) - min(ys)
    tol = STRAIGHT_TOLERANCE * height
    longest = max(_longest_straight_diagonal_run(c, tol) for c in contours)
    return ShapeMetrics(straight_ratio=round(longest / height, 3))


def measure_glyph(glyph_set, glyph_name: str) -> ShapeMetrics:
    pen = _FlattenPen()
    glyph_set[glyph_name].draw(pen)
    return measure_contours(pen.contours)


def measure_svg_path(d: str) -> ShapeMetrics:
    pen = _FlattenPen()
    parse_path(d, pen)
    return measure_contours(pen.contours)
