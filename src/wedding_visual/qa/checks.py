"""Deterministic quality checks on a render plan (see render/plan.py).

Modeled on kaankiziltug/logo-design-skill's svg_audit.py checklist approach (see
docs/research.md): a list of {level, code, message} findings, not a single pass/fail --
code checks geometry and color math, never "looks right." Unlike that tool, these checks
run on the structured plan dict our own renderer produces, not on parsed SVG text, since we
already have exact numbers rather than strings to re-parse.

Covers the four things the project brief calls out explicitly: minimum (effective) stroke
width, element overlap, contrast, and bleed margin for print use targets. Findings are
advice with a severity, same as kaankiziltug's tool: a FAIL means "this is probably wrong,"
a WARN means "worth a second look," not "reject this spec."
"""
from __future__ import annotations

import math
from typing import Any

from ..geometry import bbox_overlap, union_bbox
from .color import contrast_ratio

# Sub-pixel tolerance for the ring/overlap checks below: an exact circle-fit or box-fit
# touches its constraint boundary by construction, and float arithmetic on that boundary
# can land a few thousandths of a pixel on either side. That's not a visible defect.
_OVERLAP_TOLERANCE_PX = 0.5

# Below this, a stroke scaled down to REFERENCE_SMALL_SIZE_PX would render thinner than one
# device pixel on an ordinary (non-retina) display and effectively disappear.
MIN_VISIBLE_STROKE_PX_AT_REFERENCE_SIZE = 0.75
REFERENCE_SMALL_SIZE_PX = 32  # the standard "does it survive a favicon" check size

MIN_CONTRAST_LARGE_GRAPHIC = 3.0  # WCAG AA, large-scale graphical objects
MIN_CONTRAST_PREFERRED = 4.5  # WCAG AA, normal text -- aim higher, don't require it

PRINT_USAGE_TARGETS = {"invitation", "stage-backdrop", "merchandise"}
MIN_BLEED_MARGIN_RATIO = 0.02  # 2% of canvas size on every side, for a target meant to be printed


def _finding(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def check_overflow(plan: dict[str, Any]) -> list[dict[str, str]]:
    canvas = plan["canvas_size"]
    boxes = [g["bbox"] for g in plan["glyphs"]]
    if plan["motif"]["bbox"]:
        boxes.append(plan["motif"]["bbox"])
    x0, y0, x1, y1 = union_bbox(boxes)
    if x0 < -0.5 or y0 < -0.5 or x1 > canvas + 0.5 or y1 > canvas + 0.5:
        return [
            _finding(
                "FAIL",
                "overflow",
                f"Drawn content [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}] extends outside the "
                f"{canvas:g}x{canvas:g} canvas -- this is a renderer bug, not a style choice.",
            )
        ]
    return []


def check_motif_glyph_overlap(plan: dict[str, Any]) -> list[dict[str, str]]:
    motif = plan["motif"]
    if not motif["bbox"]:
        return []
    glyph_box = union_bbox([g["bbox"] for g in plan["glyphs"]])

    if motif["type"] == "ring":
        # A ring's own bounding box is a square circumscribing the circle, which will
        # always intersect the bbox of anything inscribed near that circle -- a plain
        # bbox-vs-bbox test would FAIL every circular-badge monogram, overlap or not. The
        # geometrically meaningful question is whether the letters' farthest corner from
        # the ring's center reaches past the ring's *inner* edge (radius - stroke/2).
        cx, cy = motif["center"]
        x0, y0, x1, y1 = glyph_box
        half_diagonal = math.hypot(max(cx - x0, x1 - cx), max(cy - y0, y1 - cy))
        if half_diagonal > motif["inner_radius"] + _OVERLAP_TOLERANCE_PX:
            return [
                _finding(
                    "FAIL",
                    "motif-overlap",
                    f"The letters reach {half_diagonal:.1f}px from the ring's center, past its "
                    f"inner edge at {motif['inner_radius']:.1f}px -- they will visibly collide "
                    "with the ring's stroke.",
                )
            ]
        return []

    if bbox_overlap(motif["bbox"], glyph_box):
        return [
            _finding(
                "FAIL",
                "motif-overlap",
                f"The {motif['type']} motif's bounding box overlaps the letters' bounding "
                "box -- they will visibly collide.",
            )
        ]
    return []


def check_min_stroke_width(plan: dict[str, Any]) -> list[dict[str, str]]:
    stroke_width = plan["motif"].get("stroke_width")
    if not stroke_width:
        return []
    scale = REFERENCE_SMALL_SIZE_PX / plan["canvas_size"]
    at_small_size = stroke_width * scale
    if at_small_size < MIN_VISIBLE_STROKE_PX_AT_REFERENCE_SIZE:
        return [
            _finding(
                "WARN",
                "thin-motif-stroke",
                f"The {plan['motif']['type']} motif's stroke would render at only "
                f"{at_small_size:.2f}px when scaled to a {REFERENCE_SMALL_SIZE_PX}px size "
                f"(minimum recommended: {MIN_VISIBLE_STROKE_PX_AT_REFERENCE_SIZE}px) -- it will "
                "effectively vanish at small sizes.",
            )
        ]
    return []


def check_contrast(plan: dict[str, Any]) -> list[dict[str, str]]:
    background = plan["background"]
    if not background:
        return [
            _finding(
                "INFO",
                "no-background",
                "Template has no background color; contrast depends on wherever this gets "
                "composited. Re-run this check with the real background once known.",
            )
        ]
    ratio = contrast_ratio(plan["ink"], background)
    if ratio < MIN_CONTRAST_LARGE_GRAPHIC:
        return [
            _finding(
                "FAIL",
                "low-contrast",
                f"Ink {plan['ink']} on background {background} is {ratio:.1f}:1, below the "
                f"{MIN_CONTRAST_LARGE_GRAPHIC:g}:1 minimum for large graphical elements.",
            )
        ]
    if ratio < MIN_CONTRAST_PREFERRED:
        return [
            _finding(
                "WARN",
                "borderline-contrast",
                f"Ink {plan['ink']} on background {background} is {ratio:.1f}:1 -- passes the "
                f"{MIN_CONTRAST_LARGE_GRAPHIC:g}:1 minimum but not the preferred "
                f"{MIN_CONTRAST_PREFERRED:g}:1.",
            )
        ]
    return []


def check_bleed_margin(plan: dict[str, Any]) -> list[dict[str, str]]:
    print_targets = sorted(PRINT_USAGE_TARGETS & set(plan.get("usage_targets", [])))
    if not print_targets:
        return []

    canvas = plan["canvas_size"]
    boxes = [g["bbox"] for g in plan["glyphs"]]
    if plan["motif"]["bbox"]:
        boxes.append(plan["motif"]["bbox"])
    x0, y0, x1, y1 = union_bbox(boxes)
    min_margin = min(x0, y0, canvas - x1, canvas - y1)
    required = canvas * MIN_BLEED_MARGIN_RATIO
    if min_margin < required:
        return [
            _finding(
                "WARN",
                "insufficient-bleed-margin",
                f"Only {min_margin:.1f}px of margin to the nearest canvas edge, below the "
                f"{required:.1f}px ({MIN_BLEED_MARGIN_RATIO:.0%} of canvas) recommended for "
                f"print use targets: {', '.join(print_targets)}.",
            )
        ]
    return []


ALL_CHECKS = (
    check_overflow,
    check_motif_glyph_overlap,
    check_min_stroke_width,
    check_contrast,
    check_bleed_margin,
)


def audit(plan: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for check in ALL_CHECKS:
        findings.extend(check(plan))
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    return sorted(findings, key=lambda f: order[f["level"]])
