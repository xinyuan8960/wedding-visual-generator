"""Build a structured, serialization-independent description of a rendered monogram.

Splitting this out from svg.py matters for QA (qa/checks.py): auditing geometry by
re-parsing the SVG text we just generated would be redundant and fragile (regexing XML to
recover numbers we already had as floats). Instead both svg.py and qa/checks.py consume
this same plan dict -- one source of truth for "what got drawn and where."
"""
from __future__ import annotations

from typing import Any

from ..geometry import union_bbox
from ..layout.glyphs import Font
from ..layout.monogram import compose_monogram, initial_of
from ..templates import load_template, resolve_font_path

_MIN_MOTIF_CLEARANCE_PX = 3  # skip the rule/diamond entirely below this much vertical clearance


class UnsupportedDesignBasisError(ValueError):
    pass


def _ring_motif(canvas_size: float, whitespace_ratio: float, stroke_width: float) -> dict[str, Any]:
    radius = canvas_size * (1 - whitespace_ratio) / 2
    c = canvas_size / 2
    bbox = [c - radius - stroke_width / 2, c - radius - stroke_width / 2, c + radius + stroke_width / 2, c + radius + stroke_width / 2]
    return {
        "type": "ring",
        "center": (c, c),
        "radius": radius,
        "inner_radius": radius - stroke_width / 2,
        "stroke_width": stroke_width,
        "bbox": bbox,
    }


def _rule_and_diamond_motif(
    glyph_boxes: list[list[float]], canvas_size: float, whitespace_ratio: float, stroke_width: float
) -> dict[str, Any]:
    margin = canvas_size * whitespace_ratio / 2
    content_bottom = canvas_size - margin
    x0, _y0, x1, y1 = union_bbox(glyph_boxes)

    available = content_bottom - y1
    if available < _MIN_MOTIF_CLEARANCE_PX:
        return {"type": None, "bbox": None, "stroke_width": None}

    # Scale the motif to whatever gap actually exists below the letters, rather than using a
    # fixed size and sometimes skipping it outright -- a visibly tight whitespace_ratio should
    # still get a (smaller) flourish, not no flourish.
    rule_y = (y1 + content_bottom) / 2
    stroke_width = min(stroke_width, available * 0.35)
    r = min(stroke_width * 2.2, available * 0.4)
    cx = canvas_size / 2
    half_len = min((x1 - x0) * 0.55 / 2, cx - margin)
    half_height = max(stroke_width / 2, r)
    return {
        "type": "rule-and-diamond",
        "rule_y": rule_y,
        "cx": cx,
        "half_len": half_len,
        "diamond_r": r,
        "stroke_width": stroke_width,
        "bbox": [cx - half_len, rule_y - half_height, cx + half_len, rule_y + half_height],
    }


def build_render_plan(spec: dict[str, Any], template: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compute everything needed to either serialize an SVG or audit one, without doing either."""
    if spec["design_basis"] != "names":
        raise UnsupportedDesignBasisError(
            f"build_render_plan only handles design_basis='names', got {spec['design_basis']!r}"
        )

    template = template or load_template(spec["layout"]["template_id"])
    font = Font(resolve_font_path(template))

    canvas_size = float(template["canvas_size"])
    ink = template["ink_color"]
    layout_params = spec["layout"]
    whitespace_ratio = layout_params["whitespace_ratio"]
    stroke_width = layout_params["stroke_width_ratio"] * canvas_size
    arrangement = layout_params["monogram_arrangement"]

    names = spec["names"]
    char_a = initial_of(names["partner_a"]["latin"])
    char_b = initial_of(names["partner_b"]["latin"])

    # For circular-badge, the ring is drawn at the same radius the letters were fitted to,
    # but a stroke extends stroke_width/2 to *each* side of that radius -- fitting the letters
    # to the mathematical radius leaves no room for the inward half of the stroke, so they'd
    # overlap it. Inflate the whitespace fed to the glyph layout (circular-badge only) by
    # that half-stroke, in canvas_size units, so letters fit inside radius - stroke_width/2
    # while the ring itself still gets drawn at the original, visually-intended radius.
    layout_whitespace_ratio = whitespace_ratio
    if arrangement == "circular-badge":
        layout_whitespace_ratio = whitespace_ratio + stroke_width / canvas_size

    monogram = compose_monogram(
        char_a, char_b, arrangement, layout_whitespace_ratio, canvas_size=canvas_size, font=font
    )
    glyph_boxes = [g["bbox"] for g in monogram["glyphs"]]

    if arrangement == "circular-badge":
        motif = _ring_motif(canvas_size, whitespace_ratio, stroke_width)
    else:
        motif = _rule_and_diamond_motif(glyph_boxes, canvas_size, whitespace_ratio, stroke_width)

    bg_color = template.get("background")
    background = None if (not bg_color or bg_color == "none") else bg_color

    return {
        "canvas_size": canvas_size,
        "ink": ink,
        "background": background,
        "arrangement": arrangement,
        "whitespace_ratio": whitespace_ratio,
        "title": f"Monogram for {names['partner_a'].get('latin', '')} & {names['partner_b'].get('latin', '')}",
        "glyphs": monogram["glyphs"],
        "motif": motif,
        "usage_targets": spec.get("usage_targets", []),
    }
