"""Render plan for layout "diagonal-ampersand" (template monogram-v2).

Composition, top to bottom: a square block holding the diagonal initials joined by a
script ampersand, encircled by an open hairline arc that breaks wherever it meets ink;
then the couple's first names in widely tracked light caps; then the date. Every size and
position comes from the template's parameters as a fraction of canvas_size.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Any

from ..layout.diagonal import compose_diagonal
from ..layout.glyphs import Font
from ..layout.monogram import initial_of
from ..layout.text import set_line
from ..templates import resolve_repo_path
from .arc import _blocked, open_arc
from .sprig import olive_sprig


def _font(spec: dict[str, Any]) -> Font:
    return _cached_font(spec["path"], tuple(sorted(spec.get("variations", {}).items())))


@lru_cache(maxsize=None)
def _cached_font(path: str, variations: tuple[tuple[str, float], ...]) -> Font:
    # Instancing a variable font is ~95% of a render's cost and its result never changes
    # for the same (file, axis values), so build each one once per process.
    return Font(resolve_repo_path(path), dict(variations) or None)


def _first_name(full: str) -> str:
    return full.split()[0]


def _format_date(iso: str, fmt: str) -> str:
    d = date.fromisoformat(iso)
    return fmt.replace("MM", f"{d.month:02d}").replace("DD", f"{d.day:02d}").replace("YYYY", f"{d.year:04d}")


def build_diagonal_plan(spec: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    canvas = float(template["canvas_size"])
    fonts = template["fonts"]
    initials_font = _font(fonts["initials"])
    caption_font = _font(fonts["caption"])

    names = spec["names"]
    latin_a, latin_b = names["partner_a"]["latin"], names["partner_b"]["latin"]

    block = template["block"]
    block_size = block["size"] * canvas
    block_x = (canvas - block_size) / 2
    block_y = block["top"] * canvas

    placements = compose_diagonal(
        initial_of(latin_a),
        initial_of(latin_b),
        initials_font,
        _font(fonts["ampersand"]),
        block_x,
        block_y,
        block_size,
    )

    arc_params = template["arc"]
    motif = open_arc(
        cx=block_x + arc_params["center"][0] * block_size,
        cy=block_y + arc_params["center"][1] * block_size,
        radius=arc_params["radius"] * block_size,
        start_deg=arc_params["start_deg"],
        end_deg=arc_params["end_deg"],
        stroke_width=arc_params["hairline_ratio"] * canvas,
        obstacles=placements,
        clearance=arc_params["clearance_ratio"] * canvas,
    )

    ornaments = []
    if spec["layout"].get("ornament", "none") == "olive-sprig":
        sp = template["sprig"]
        boxes = [pl.bbox() for pl in placements]
        pad = arc_params["clearance_ratio"] * canvas
        ornaments.append(
            olive_sprig(
                cx=block_x + arc_params["center"][0] * block_size,
                cy=block_y + arc_params["center"][1] * block_size,
                radius=arc_params["radius"] * block_size,
                start_deg=arc_params["end_deg"],  # grows out of the arc's open end
                span_deg=sp["span_deg"],
                leaf_pairs=sp["leaf_pairs"],
                leaf_length=sp["leaf_length_ratio"] * arc_params["radius"] * block_size,
                stroke_width=sp["stroke_ratio"] * canvas,
                seed=spec["seed"],
                blocked=lambda x, y: _blocked(x, y, placements, boxes, pad),
            )
        )

    name_params = template["names"]
    names_line = set_line(
        caption_font,
        f"{_first_name(latin_a)} & {_first_name(latin_b)}".upper(),
        cap_height_px=name_params["cap_height"] * canvas,
        tracking_em=name_params["tracking_em"],
        center_x=canvas / 2,
        baseline_y=block_y + block_size + name_params["gap_below_block"] * canvas,
        max_width=name_params["max_width"] * canvas,
    )
    captions = [names_line]

    if names.get("date"):
        date_params = template["date"]
        captions.append(
            set_line(
                caption_font,
                _format_date(names["date"], date_params["format"]),
                cap_height_px=date_params["cap_height"] * canvas,
                tracking_em=date_params["tracking_em"],
                center_x=canvas / 2,
                baseline_y=names_line["bbox"][3] + date_params["gap_below_names"] * canvas,
            )
        )

    glyphs = [p.to_dict() for p in placements]
    glyphs[1]["role"] = "connector"  # the ampersand, between the two initials

    return {
        "canvas_size": canvas,
        "ink": template["ink_color"],
        "background": None if template.get("background") in (None, "none") else template["background"],
        "arrangement": template["layout"],
        "title": f"Monogram for {latin_a} & {latin_b}",
        "glyphs": glyphs,
        "captions": captions,
        "motif": motif,
        "ornaments": ornaments,
        "usage_targets": spec.get("usage_targets", []),
    }
