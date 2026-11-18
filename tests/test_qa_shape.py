from wedding_visual.qa.checks import MAX_CONNECTOR_STRAIGHT_RATIO, check_connector_shape
from wedding_visual.qa.shape import measure_svg_path
from wedding_visual.render.plan import build_render_plan

BLADE = "M0 0 L10 0 L110 100 L100 100 Z"  # thin 45-degree parallelogram, height 100
CIRCLE = "M0 50 A50 50 0 1 0 100 50 A50 50 0 1 0 0 50 Z"
FLAT_BAR = "M0 0 H200 V10 H0 Z"  # long, but horizontal: a swash, not a blade


def test_blade_scores_far_above_threshold():
    assert measure_svg_path(BLADE).straight_ratio > 1.0


def test_circle_scores_well_below_threshold():
    assert measure_svg_path(CIRCLE).straight_ratio < 0.3


def test_horizontal_runs_do_not_count_as_blade_like():
    assert measure_svg_path(FLAT_BAR).straight_ratio == 0


def test_metric_is_scale_and_flip_invariant():
    # The same blade scaled 3x and flipped vertically (as glyphs are, font -> SVG space).
    flipped = "M0 0 L30 0 L330 -300 L300 -300 Z"
    assert abs(measure_svg_path(flipped).straight_ratio - measure_svg_path(BLADE).straight_ratio) < 0.02


def _plan_with_connector(d: str) -> dict:
    return {"glyphs": [{"char": "A", "d": BLADE}, {"char": "&", "role": "connector", "d": d}]}


def test_connector_check_warns_on_blade_connector():
    findings = check_connector_shape(_plan_with_connector(BLADE))
    assert [f["code"] for f in findings] == ["blade-like-connector"]
    assert findings[0]["level"] == "WARN"


def test_connector_check_ignores_non_connector_glyphs():
    # The initial 'A' here is blade-shaped too, but only the connector is judged.
    assert check_connector_shape(_plan_with_connector(CIRCLE)) == []


def test_v2_ampersand_passes_the_connector_check():
    spec = {
        "version": "0.1",
        "seed": 0,
        "design_basis": "names",
        "names": {"partner_a": {"latin": "Sofia Lin"}, "partner_b": {"latin": "Marco Rossi"}},
        "layout": {"template_id": "monogram-v2", "whitespace_ratio": 0.2, "stroke_width_ratio": 0.03},
    }
    plan = build_render_plan(spec)
    connector = next(g for g in plan["glyphs"] if g.get("role") == "connector")
    assert measure_svg_path(connector["d"]).straight_ratio < MAX_CONNECTOR_STRAIGHT_RATIO
    assert check_connector_shape(plan) == []
