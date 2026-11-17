"""Render a names-basis spec + the 'monogram-v1' template into a standalone SVG document.

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

from ..layout.glyphs import Font
from ..layout.monogram import compose_monogram, initial_of
from ..templates import load_template, resolve_font_path

_MIN_MOTIF_CLEARANCE_PX = 3  # skip the rule/diamond entirely below this much vertical clearance


class UnsupportedDesignBasisError(ValueError):
    pass


def _union_bbox(glyphs: list[dict]) -> tuple[float, float, float, float]:
    xs0 = [g["bbox"][0] for g in glyphs]
    ys0 = [g["bbox"][1] for g in glyphs]
    xs1 = [g["bbox"][2] for g in glyphs]
    ys1 = [g["bbox"][3] for g in glyphs]
    return min(xs0), min(ys0), max(xs1), max(ys1)


def _ring_motif(canvas_size: float, whitespace_ratio: float, stroke_width: float, ink: str) -> str:
    radius = canvas_size * (1 - whitespace_ratio) / 2
    c = canvas_size / 2
    return f'<circle cx="{c:g}" cy="{c:g}" r="{radius:g}" fill="none" stroke="{ink}" stroke-width="{stroke_width:g}"/>'


def _rule_and_diamond_motif(
    glyphs: list[dict], canvas_size: float, whitespace_ratio: float, stroke_width: float, ink: str
) -> str:
    margin = canvas_size * whitespace_ratio / 2
    content_bottom = canvas_size - margin
    x0, _y0, x1, y1 = _union_bbox(glyphs)

    available = content_bottom - y1
    if available < _MIN_MOTIF_CLEARANCE_PX:
        return ""  # letters already reach (or overflow) the content edge; nothing fits cleanly

    # Scale the motif to whatever gap actually exists below the letters, rather than using a
    # fixed size and sometimes skipping it outright -- a visibly tight whitespace_ratio should
    # still get a (smaller) flourish, not no flourish.
    rule_y = (y1 + content_bottom) / 2
    stroke_width = min(stroke_width, available * 0.35)
    r = min(stroke_width * 2.2, available * 0.4)
    cx = canvas_size / 2
    half_len = min((x1 - x0) * 0.55 / 2, cx - margin)
    return (
        f'<line x1="{cx - half_len:g}" y1="{rule_y:g}" x2="{cx + half_len:g}" y2="{rule_y:g}" '
        f'stroke="{ink}" stroke-width="{stroke_width:g}"/>\n'
        f'  <path d="M {cx - r:g} {rule_y:g} L {cx:g} {rule_y - r:g} L {cx + r:g} {rule_y:g} '
        f'L {cx:g} {rule_y + r:g} Z" fill="{ink}"/>'
    )


def render_monogram_svg(spec: dict[str, Any], template: dict[str, Any] | None = None) -> str:
    """Build a complete SVG document for a names-basis spec.

    `template` defaults to loading spec["layout"]["template_id"] from templates/; pass one
    explicitly (e.g. in tests) to avoid touching the filesystem or to try a variant.
    """
    if spec["design_basis"] != "names":
        raise UnsupportedDesignBasisError(
            f"render_monogram_svg only handles design_basis='names', got {spec['design_basis']!r}"
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

    monogram = compose_monogram(char_a, char_b, arrangement, whitespace_ratio, canvas_size=canvas_size, font=font)
    glyph_paths = "\n  ".join(f'<path d="{g["d"]}" fill="{ink}"/>' for g in monogram["glyphs"])

    if arrangement == "circular-badge":
        motif = _ring_motif(canvas_size, whitespace_ratio, stroke_width, ink)
    else:
        motif = _rule_and_diamond_motif(monogram["glyphs"], canvas_size, whitespace_ratio, stroke_width, ink)

    background = ""
    bg_color = template.get("background")
    if bg_color and bg_color != "none":
        background = f'<rect x="0" y="0" width="{canvas_size:g}" height="{canvas_size:g}" fill="{bg_color}"/>\n  '

    title = escape(f"Monogram for {names['partner_a'].get('latin', '')} & {names['partner_b'].get('latin', '')}")
    body = "\n  ".join(part for part in (background + glyph_paths, motif) if part)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_size:g} {canvas_size:g}">\n'
        f"  <title>{title}</title>\n"
        f"  {body}\n"
        f"</svg>\n"
    )
