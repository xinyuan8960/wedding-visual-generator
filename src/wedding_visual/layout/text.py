"""Set a single line of letter-spaced text, centered, as outlined paths (no live <text>)."""
from __future__ import annotations

from .glyphs import Font
from .placement import Placement


def set_line(
    font: Font,
    text: str,
    cap_height_px: float,
    tracking_em: float,
    center_x: float,
    baseline_y: float,
    max_width: float | None = None,
) -> dict:
    """Lay out `text` centered on `center_x`, sitting on `baseline_y`.

    Sized by cap height rather than em size so lines set in different fonts line up
    visually. If `max_width` is given and the line would exceed it, the whole line is
    scaled down to fit -- long names shrink rather than run off the canvas.
    """
    scale = cap_height_px / font.cap_height()

    def width_at(s: float) -> float:
        advances = sum(font.advance(ch) for ch in text) * s
        return advances + tracking_em * font.units_per_em * s * (len(text) - 1)

    width = width_at(scale)
    if max_width is not None and width > max_width:
        scale *= max_width / width
        width = max_width

    x = center_x - width / 2
    glyphs = []
    for ch in text:
        if not ch.isspace():
            glyphs.append(Placement(font, ch, scale, x, baseline_y).to_dict())
        x += font.advance(ch) * scale + tracking_em * font.units_per_em * scale

    xs0 = [g["bbox"][0] for g in glyphs]
    ys0 = [g["bbox"][1] for g in glyphs]
    xs1 = [g["bbox"][2] for g in glyphs]
    ys1 = [g["bbox"][3] for g in glyphs]
    return {
        "text": text,
        "d": " ".join(g["d"] for g in glyphs),
        "bbox": [min(xs0), min(ys0), max(xs1), max(ys1)],
    }
