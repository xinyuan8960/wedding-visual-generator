"""A procedural olive sprig in line art, growing out of the open end of the hairline arc.

Olive is the classic wedding/peace motif and suits the mark's hairline style. Nothing here
is traced: the stem continues the arc's own circle, and every leaf is the same parametric
lanceolate outline (two cubic sides plus a midrib), placed along the stem alternating
sides and angled toward the tip. `seed` jitters leaf angles and lengths slightly, so
different seeds give sibling variants of one design; the same seed is byte-identical.

Leaves that would touch a glyph's ink are dropped rather than drawn over the letters.
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable

Point = tuple[float, float]

LEAF_HALF_WIDTH = 0.2  # of leaf length -- narrow, olive-like (not a round laurel leaf)
LEAF_SPREAD_DEG = 38.0  # angle between a leaf and the stem's direction of growth
ANGLE_JITTER_DEG = 7.0
LENGTH_JITTER = 0.12
OLIVE_RADII = (0.16, 0.11)  # of leaf length: a small oval fruit
_SAMPLES = 24


def _fmt(p: Point) -> str:
    return f"{p[0]:.2f} {p[1]:.2f}"


def _cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
    )


def _leaf(base: Point, angle: float, length: float) -> tuple[str, list[Point]]:
    """Path 'd' and sample points of one leaf whose base is at `base`, pointing `angle`."""
    ca, sa = math.cos(angle), math.sin(angle)

    def to_canvas(x: float, y: float) -> Point:
        return base[0] + x * ca - y * sa, base[1] + x * sa + y * ca

    w = LEAF_HALF_WIDTH * length * 1.33  # control offset giving ~LEAF_HALF_WIDTH max width
    tip = to_canvas(length, 0)
    up = (to_canvas(0.28 * length, w), to_canvas(0.72 * length, 0.7 * w))
    down = (to_canvas(0.72 * length, -0.7 * w), to_canvas(0.28 * length, -w))
    rib_end = to_canvas(0.72 * length, 0)
    d = (
        f"M{_fmt(base)} C{_fmt(up[0])} {_fmt(up[1])} {_fmt(tip)} "
        f"C{_fmt(down[0])} {_fmt(down[1])} {_fmt(base)} Z M{_fmt(base)} L{_fmt(rib_end)}"
    )
    samples = [_cubic(base, *up, tip, i / _SAMPLES) for i in range(_SAMPLES + 1)]
    samples += [_cubic(tip, *down, base, i / _SAMPLES) for i in range(_SAMPLES + 1)]
    return d, samples


def _olive(center: Point, angle: float, leaf_length: float) -> tuple[str, list[Point]]:
    rx, ry = OLIVE_RADII[0] * leaf_length, OLIVE_RADII[1] * leaf_length
    ca, sa = math.cos(angle), math.sin(angle)
    a = (center[0] + rx * ca, center[1] + rx * sa)
    b = (center[0] - rx * ca, center[1] - rx * sa)
    rot = math.degrees(angle)
    d = f"M{_fmt(a)} A{rx:.2f} {ry:.2f} {rot:.2f} 1 1 {_fmt(b)} A{rx:.2f} {ry:.2f} {rot:.2f} 1 1 {_fmt(a)} Z"
    samples = [
        (center[0] + rx * math.cos(t) * ca - ry * math.sin(t) * sa, center[1] + rx * math.cos(t) * sa + ry * math.sin(t) * ca)
        for t in (2 * math.pi * i / _SAMPLES for i in range(_SAMPLES))
    ]
    return d, samples


def olive_sprig(
    cx: float,
    cy: float,
    radius: float,
    start_deg: float,
    span_deg: float,
    leaf_pairs: int,
    leaf_length: float,
    stroke_width: float,
    seed: int,
    blocked: Callable[[float, float], bool],
) -> dict:
    """Sprig along the circle (cx, cy, radius) from start_deg, growing by +span_deg.

    `blocked(x, y)` says whether a canvas point is too close to existing ink; any leaf or
    olive with a blocked sample point is left out.
    """
    rng = random.Random(seed)
    direction = 1 if span_deg > 0 else -1

    def on_stem(t: float) -> tuple[Point, float]:
        a = math.radians(start_deg + t * span_deg)
        point = (cx + radius * math.cos(a), cy + radius * math.sin(a))
        heading = a + direction * math.pi / 2  # tangent, pointing toward the tip
        return point, heading

    stem_samples = [on_stem(i / _SAMPLES)[0] for i in range(_SAMPLES + 1)]
    end = stem_samples[-1]
    large = 1 if abs(span_deg) > 180 else 0
    sweep = 1 if direction > 0 else 0
    parts = [f"M{_fmt(stem_samples[0])} A{radius:.2f} {radius:.2f} 0 {large} {sweep} {_fmt(end)}"]
    all_samples = list(stem_samples)
    dropped = 0

    def place(d_and_samples: tuple[str, list[Point]]) -> None:
        nonlocal dropped
        d, samples = d_and_samples
        if any(blocked(x, y) for x, y in samples):
            dropped += 1
            return
        parts.append(d)
        all_samples.extend(samples)

    # Leaf pairs from the base toward the tip, shrinking slightly as the sprig tapers.
    for i in range(leaf_pairs):
        t = 0.18 + 0.68 * i / max(1, leaf_pairs - 1)
        point, heading = on_stem(t)
        taper = 1.0 - 0.25 * t
        for side in (-1, 1):
            spread = math.radians(LEAF_SPREAD_DEG + rng.uniform(-ANGLE_JITTER_DEG, ANGLE_JITTER_DEG))
            length = leaf_length * taper * (1 + rng.uniform(-LENGTH_JITTER, LENGTH_JITTER))
            place(_leaf(point, heading + side * spread, length))
    # Terminal leaf continuing the stem.
    _, tip_heading = on_stem(1.0)
    place(_leaf(end, tip_heading, leaf_length * 0.8))
    # Two olives hanging on the outer side near the middle of the stem.
    for t in (0.42, 0.62):
        point, heading = on_stem(t + rng.uniform(-0.03, 0.03))
        outward = heading - direction * math.pi / 2
        offset = OLIVE_RADII[0] * leaf_length * 2.0
        center = (point[0] + offset * math.cos(outward), point[1] + offset * math.sin(outward))
        place(_olive(center, heading, leaf_length))

    xs, ys = [p[0] for p in all_samples], [p[1] for p in all_samples]
    pad = stroke_width / 2
    return {
        "type": "olive-sprig",
        "d": " ".join(parts),
        "stroke_width": stroke_width,
        "dropped_leaves": dropped,
        "bbox": [round(min(xs) - pad, 3), round(min(ys) - pad, 3), round(max(xs) + pad, 3), round(max(ys) + pad, 3)],
    }
