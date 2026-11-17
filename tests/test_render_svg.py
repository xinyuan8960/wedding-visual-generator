import xml.etree.ElementTree as ET

import pytest

from wedding_visual.layout.glyphs import Font
from wedding_visual.render.svg import UnsupportedDesignBasisError, render_monogram_svg
from wedding_visual.templates import load_template

SVG_NS = "{http://www.w3.org/2000/svg}"


def _spec(arrangement: str, whitespace_ratio: float = 0.2, stroke_width_ratio: float = 0.03) -> dict:
    return {
        "version": "0.1",
        "seed": 1,
        "design_basis": "names",
        "names": {"partner_a": {"latin": "Alex Rivera"}, "partner_b": {"latin": "Jordan Lee"}},
        "layout": {
            "template_id": "monogram-v1",
            "monogram_arrangement": arrangement,
            "whitespace_ratio": whitespace_ratio,
            "stroke_width_ratio": stroke_width_ratio,
        },
    }


@pytest.fixture(scope="module")
def font():
    return Font()


@pytest.fixture(scope="module")
def template():
    return load_template("monogram-v1")


def test_uses_the_real_on_disk_template_by_default():
    # No `template=` passed: exercises templates.load_template + resolve_font_path for real.
    svg = render_monogram_svg(_spec("side-by-side"))
    assert svg.startswith("<svg")


def test_output_is_well_formed_xml_with_expected_viewbox(template):
    svg = render_monogram_svg(_spec("side-by-side"), template=template)
    root = ET.fromstring(svg)
    assert root.tag == f"{SVG_NS}svg"
    assert root.get("viewBox") == f"0 0 {template['canvas_size']:g} {template['canvas_size']:g}"
    title = root.find(f"{SVG_NS}title")
    assert title is not None
    assert "Alex Rivera" in title.text
    assert "Jordan Lee" in title.text


def test_rejects_photo_basis(template):
    spec = _spec("side-by-side")
    spec["design_basis"] = "photo"
    with pytest.raises(UnsupportedDesignBasisError):
        render_monogram_svg(spec, template=template)


def test_circular_badge_draws_a_ring(template):
    svg = render_monogram_svg(_spec("circular-badge"), template=template)
    root = ET.fromstring(svg)
    circles = root.findall(f"{SVG_NS}circle")
    assert len(circles) == 1
    assert float(circles[0].get("r")) > 0


def test_non_circular_arrangements_draw_no_ring(template):
    for arrangement in ("side-by-side", "stacked", "interlocking"):
        svg = render_monogram_svg(_spec(arrangement), template=template)
        root = ET.fromstring(svg)
        assert root.findall(f"{SVG_NS}circle") == []


def test_generous_whitespace_gets_a_rule_and_diamond_motif(template):
    # Plenty of vertical clearance below the letters at this whitespace ratio.
    svg = render_monogram_svg(_spec("side-by-side", whitespace_ratio=0.3), template=template)
    root = ET.fromstring(svg)
    assert len(root.findall(f"{SVG_NS}line")) == 1
    # the diamond is a <path> alongside the two glyph <path>s
    assert len(root.findall(f"{SVG_NS}path")) == 3


def test_tight_whitespace_skips_the_motif_rather_than_colliding(template):
    svg = render_monogram_svg(_spec("stacked", whitespace_ratio=0.2), template=template)
    root = ET.fromstring(svg)
    assert root.findall(f"{SVG_NS}line") == []
    assert len(root.findall(f"{SVG_NS}path")) == 2  # just the two glyphs, no diamond


def test_deterministic_same_spec_same_output(template):
    a = render_monogram_svg(_spec("interlocking"), template=template)
    b = render_monogram_svg(_spec("interlocking"), template=template)
    assert a == b


def test_special_characters_in_names_are_escaped_and_still_valid_xml(template):
    spec = _spec("side-by-side")
    spec["names"]["partner_a"]["latin"] = "A & Z – O'Rourke"
    svg = render_monogram_svg(spec, template=template)
    root = ET.fromstring(svg)  # raises if not well-formed
    title = root.find(f"{SVG_NS}title")
    assert "A & Z" in title.text
