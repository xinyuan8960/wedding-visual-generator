from wedding_visual.mapping import questionnaire_to_spec
from wedding_visual.qa.checks import audit, check_ornament_glyph_overlap
from wedding_visual.render.plan import build_render_plan
from wedding_visual.render.svg import render_monogram_svg

PAIRS = [("Sofia", "Marco"), ("Michelle", "Kevin"), ("Amara", "Wren"), ("Ingrid", "Leo"), ("Priya", "Jonas")]


def _spec(a: str, b: str, seed: int = 0, ornament: str | None = "olive-sprig") -> dict:
    layout = {"template_id": "monogram-v2"}
    if ornament:
        layout["ornament"] = ornament
    return {
        "version": "0.1",
        "seed": seed,
        "design_basis": "names",
        "names": {"partner_a": {"latin": a}, "partner_b": {"latin": b}, "date": "2027-10-10"},
        "layout": layout,
        "usage_targets": ["invitation", "e-invite", "stage-backdrop"],
    }


def test_sprig_never_crosses_a_letter_and_passes_qa():
    for a, b in PAIRS:
        plan = build_render_plan(_spec(a, b))
        assert check_ornament_glyph_overlap(plan) == [], (a, b)
        assert not [f for f in audit(plan) if f["level"] == "FAIL"], (a, b)


def test_same_seed_is_byte_identical_and_seed_makes_a_variant():
    assert render_monogram_svg(_spec("Sofia", "Marco", seed=3)) == render_monogram_svg(_spec("Sofia", "Marco", seed=3))
    assert render_monogram_svg(_spec("Sofia", "Marco", seed=3)) != render_monogram_svg(_spec("Sofia", "Marco", seed=4))


def test_ornament_is_optional():
    for ornament in (None, "none"):
        plan = build_render_plan(_spec("Sofia", "Marco", ornament=ornament))
        assert plan["ornaments"] == []


def test_questionnaire_defaults_to_the_sprig_and_can_decline_it():
    q = {"partner_a_name": {"latin": "Ana"}, "partner_b_name": {"latin": "Ben"}, "date": "2027-01-01", "design_basis": "names"}
    assert questionnaire_to_spec(q, seed=0)["layout"]["ornament"] == "olive-sprig"
    q["ornament"] = "none"
    assert questionnaire_to_spec(q, seed=0)["layout"]["ornament"] == "none"
