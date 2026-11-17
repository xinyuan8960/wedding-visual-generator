"""Serialize a render plan (see plan.py) into a standalone SVG document.

This is the one template the project scope calls for: it takes the glyph placement from
layout/monogram.py and adds exactly one piece of decorative treatment, chosen by
arrangement -- a ring around a circular-badge monogram (completing the seal/stamp shape
the arrangement was already fitted to), or a rule-and-diamond flourish centered beneath
the letters for the other three arrangements (a conventional wedding-monogram motif).
Everything here is plain geometry derived from spec/template parameters; no other
project's artwork is referenced or traced, per the project's copyright constraint.

`stroke_width_ratio` governs the *decorative motif's* line weight, not the letterforms
themselves (those are filled glyph outlines at the font's natural weight, not strokes) --
the "thinner when ornate, bolder when minimal" reasoning from mapping.py still holds for a
flourish line, just not for the letters.
"""
from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape

from .plan import UnsupportedDesignBasisError, build_render_plan

__all__ = ["UnsupportedDesignBasisError", "render_monogram_svg"]


def _motif_svg(motif: dict[str, Any], ink: str) -> str:
    if motif["type"] == "ring":
        c = motif["center"]
        return (
            f'<circle cx="{c[0]:g}" cy="{c[1]:g}" r="{motif["radius"]:g}" fill="none" '
            f'stroke="{ink}" stroke-width="{motif["stroke_width"]:g}"/>'
        )
    if motif["type"] == "rule-and-diamond":
        cx, rule_y, half_len, r, stroke_width = (
            motif["cx"],
            motif["rule_y"],
            motif["half_len"],
            motif["diamond_r"],
            motif["stroke_width"],
        )
        return (
            f'<line x1="{cx - half_len:g}" y1="{rule_y:g}" x2="{cx + half_len:g}" y2="{rule_y:g}" '
            f'stroke="{ink}" stroke-width="{stroke_width:g}"/>\n'
            f'  <path d="M {cx - r:g} {rule_y:g} L {cx:g} {rule_y - r:g} L {cx + r:g} {rule_y:g} '
            f'L {cx:g} {rule_y + r:g} Z" fill="{ink}"/>'
        )
    return ""


def render_monogram_svg(spec: dict[str, Any], template: dict[str, Any] | None = None) -> str:
    """Build a complete SVG document for a names-basis spec.

    `template` defaults to loading spec["layout"]["template_id"] from templates/; pass one
    explicitly (e.g. in tests) to avoid touching the filesystem or to try a variant.
    """
    plan = build_render_plan(spec, template)

    canvas_size, ink = plan["canvas_size"], plan["ink"]
    glyph_paths = "\n  ".join(f'<path d="{g["d"]}" fill="{ink}"/>' for g in plan["glyphs"])
    motif_svg = _motif_svg(plan["motif"], ink)

    background = ""
    if plan["background"]:
        background = f'<rect x="0" y="0" width="{canvas_size:g}" height="{canvas_size:g}" fill="{plan["background"]}"/>\n  '

    title = escape(plan["title"])
    body = "\n  ".join(part for part in (background + glyph_paths, motif_svg) if part)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_size:g} {canvas_size:g}">\n'
        f"  <title>{title}</title>\n"
        f"  {body}\n"
        f"</svg>\n"
    )
