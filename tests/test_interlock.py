from wedding_visual.layout import diagonal
from wedding_visual.qa.checks import check_connector_contact
from wedding_visual.render.plan import build_render_plan
from wedding_visual.render.svg import render_monogram_svg

PAIRS = [("Sofia", "Marco"), ("Ingrid", "Leo"), ("Quincy", "Theo"), ("Amara", "Wren"), ("Jing", "Yusuf")]


def _spec(a: str, b: str) -> dict:
    return {
        "version": "0.1",
        "seed": 0,
        "design_basis": "names",
        "names": {"partner_a": {"latin": a}, "partner_b": {"latin": b}},
        "layout": {"template_id": "monogram-v2", "whitespace_ratio": 0.2, "stroke_width_ratio": 0.03},
    }


def test_every_pair_interlocks_and_passes_the_contact_check():
    # 'S'+'M' and 'I'+'L' had zero contact with the '&' at the fixed nominal positions.
    for a, b in PAIRS:
        plan = build_render_plan(_spec(a, b))
        assert check_connector_contact(plan) == [], (a, b)


def test_initials_never_collide_with_each_other():
    from wedding_visual.ink import flatten_svg_path, overlap_area, rasterize

    for a, b in PAIRS:
        g = build_render_plan(_spec(a, b))["glyphs"]
        ra, rb = (rasterize(flatten_svg_path(x["d"]), 1.0) for x in (g[0], g[2]))
        assert overlap_area(ra, rb, 1.0) == 0, (a, b)


def test_contact_check_warns_when_the_connector_floats(monkeypatch):
    # Disable the search: the nominal layout leaves 'S' and '&' apart.
    monkeypatch.setattr(diagonal, "MAX_PULL_STEPS", -1)
    plan = build_render_plan(_spec("Sofia", "Marco"))
    assert [f["code"] for f in check_connector_contact(plan)] == ["detached-connector"]


def test_interlocked_render_is_byte_identical():
    assert render_monogram_svg(_spec("Sofia", "Marco")) == render_monogram_svg(_spec("Sofia", "Marco"))
