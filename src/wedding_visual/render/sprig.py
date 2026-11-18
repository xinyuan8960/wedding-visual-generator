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

LEAF_HALF_WIDTH = 0.24  # of leaf length -- narrow, olive-like (not a round laurel leaf)
LEAF_SPREAD_DEG = (46.0, 28.0)  # leaf-to-stem angle at the base, at the tip: leaves close up toward the tip
PETIOLE = 0.12  # short leaf stalk, as a fraction of leaf length
LEAF_BEND = 0.07  # sideways curve of each blade, as a fraction of its length
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


def _leaf(stem_point: Point, angle: float, length: float, bend: float) -> tuple[str, list[Point]]:
    """One leaf on a short stalk from `stem_point`, pointing `angle`, its blade curving
    sideways by `bend` (fraction of length, signed) -- real leaves are rarely straight."""
    ca, sa = math.cos(angle), math.sin(angle)

    def to_canvas(x: float, y: float) -> Point:
        return stem_point[0] + x * ca - y * sa, stem_point[1] + x * sa + y * ca

    stalk = PETIOLE * length
    w = LEAF_HALF_WIDTH * length * 1.33  # control offset giving ~LEAF_HALF_WIDTH max width
    b = bend * length
    base = to_canvas(stalk, 0)
    tip = to_canvas(stalk + length, b)
    # Asymmetric sides: the outer edge of the curve is fuller than the inner one.
    up = (to_canvas(stalk + 0.25 * length, w + 0.3 * b), to_canvas(stalk + 0.7 * length, 0.75 * w + b))
    down = (to_canvas(stalk + 0.7 * length, -0.6 * w + b), to_canvas(stalk + 0.25 * length, -0.9 * w + 0.3 * b))
    rib_ctrl = to_canvas(stalk + 0.4 * length, 0.45 * b)
    rib_end = to_canvas(stalk + 0.78 * length, 0.75 * b)
    d = (
        f"M{_fmt(stem_point)} L{_fmt(base)} "
        f"C{_fmt(up[0])} {_fmt(up[1])} {_fmt(tip)} C{_fmt(down[0])} {_fmt(down[1])} {_fmt(base)} Z "
        f"M{_fmt(base)} Q{_fmt(rib_ctrl)} {_fmt(rib_end)}"
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
    olives: bool = False,
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

    # Alternate leaves (not opposite pairs, which look stiff) from the base toward the
    # tip, shrinking and closing up toward the stem as the sprig tapers.
    n = 2 * leaf_pairs
    for i in range(n):
        t = 0.1 + 0.8 * i / (n - 1)
        point, heading = on_stem(t)
        side = 1 if i % 2 else -1
        spread_deg = LEAF_SPREAD_DEG[0] + (LEAF_SPREAD_DEG[1] - LEAF_SPREAD_DEG[0]) * t
        spread = math.radians(spread_deg + rng.uniform(-ANGLE_JITTER_DEG, ANGLE_JITTER_DEG))
        length = leaf_length * (1.0 - 0.4 * t) * (1 + rng.uniform(-LENGTH_JITTER, LENGTH_JITTER))
        # Each blade curves back toward the direction of growth.
        place(_leaf(point, heading + side * spread, length, -side * LEAF_BEND))
    # Terminal leaf continuing the stem.
    _, tip_heading = on_stem(1.0)
    place(_leaf(end, tip_heading, leaf_length * 0.55, LEAF_BEND))
    # Optional fruit. Off by default: free-floating ovals beside the stem read as odd
    # circles rather than olives in user review.
    for t in (0.42, 0.62) if olives else ():
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
