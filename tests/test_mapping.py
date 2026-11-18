import copy
import json
from pathlib import Path

import pytest

from wedding_visual.mapping import questionnaire_to_spec
from wedding_visual.spec import load_spec
from wedding_visual.validation import validate_document

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_names_basis_produces_a_valid_spec(tmp_path):
    questionnaire = _load("valid_questionnaire.json")
    spec = questionnaire_to_spec(questionnaire, seed=42)

    validate_document(spec, "spec.schema.json", "<test>")
    assert spec["seed"] == 42
    assert spec["design_basis"] == "names"
    assert spec["names"]["partner_a"] == questionnaire["partner_a_name"]
    assert spec["names"]["partner_b"] == questionnaire["partner_b_name"]
    assert spec["names"]["date"] == questionnaire["date"]
    assert "venues" not in spec  # dropped deliberately, see mapping.py
    assert spec["layout"]["template_id"] == "monogram-v2"
    assert spec["layout"]["monogram_arrangement"] in {
        "interlocking",
        "stacked",
        "circular-badge",
        "side-by-side",
    }
    assert "photo_silhouette" not in spec


def test_photo_basis_produces_a_valid_spec_with_silhouette_params():
    questionnaire = {
        "partner_a_name": {"latin": "Alex Rivera"},
        "partner_b_name": {"latin": "Jordan Lee"},
        "date": "2027-05-01",
        "design_basis": "photo",
        "photo_ref": "private/couple-01.jpg",
    }
    spec = questionnaire_to_spec(questionnaire, seed=7)

    validate_document(spec, "spec.schema.json", "<test>")
    assert spec["photo_silhouette"]["source_ref"] == "private/couple-01.jpg"
    assert spec["photo_silhouette"]["simplify_tolerance"] > 0
    assert spec["photo_silhouette"]["stroke_width"] > 0
    assert "monogram_arrangement" not in spec["layout"]


def test_missing_style_sliders_fall_back_to_neutral_defaults():
    questionnaire = {
        "partner_a_name": {"latin": "Alex Rivera"},
        "partner_b_name": {"latin": "Jordan Lee"},
        "date": "2027-05-01",
        "design_basis": "names",
    }
    spec = questionnaire_to_spec(questionnaire, seed=1)
    assert spec["style"] == {
        "minimal_to_ornate": 0.5,
        "modern_to_classic": 0.5,
        "eastern_to_western": 0.5,
        "handwritten_to_print": 0.5,
    }


def test_same_input_and_seed_is_byte_identical():
    questionnaire = _load("valid_questionnaire.json")
    a = questionnaire_to_spec(copy.deepcopy(questionnaire), seed=5)
    b = questionnaire_to_spec(copy.deepcopy(questionnaire), seed=5)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_different_seed_only_changes_the_seed_field():
    questionnaire = _load("valid_questionnaire.json")
    a = questionnaire_to_spec(copy.deepcopy(questionnaire), seed=1)
    b = questionnaire_to_spec(copy.deepcopy(questionnaire), seed=2)
    a.pop("seed")
    b.pop("seed")
    assert a == b


@pytest.mark.parametrize(
    "ornate,expected_stroke,expected_whitespace",
    [(0.0, 0.06, 0.30), (1.0, 0.02, 0.15)],
)
def test_minimal_to_ornate_drives_stroke_and_whitespace_linearly(
    ornate, expected_stroke, expected_whitespace
):
    questionnaire = {
        "partner_a_name": {"latin": "A"},
        "partner_b_name": {"latin": "B"},
        "date": "2027-05-01",
        "design_basis": "names",
        "style_sliders": {"minimal_to_ornate": ornate},
    }
    spec = questionnaire_to_spec(questionnaire, seed=0)
    assert spec["layout"]["stroke_width_ratio"] == pytest.approx(expected_stroke)
    assert spec["layout"]["whitespace_ratio"] == pytest.approx(expected_whitespace)


def test_preferred_and_avoid_elements_pass_through():
    questionnaire = _load("valid_questionnaire.json")
    spec = questionnaire_to_spec(questionnaire, seed=0)
    assert spec["preferred_elements"] == questionnaire["preferred_elements"]
    assert spec["avoid_elements"] == questionnaire["avoid_elements"]


def test_generated_spec_round_trips_through_load_spec(tmp_path):
    questionnaire = _load("valid_questionnaire.json")
    spec = questionnaire_to_spec(questionnaire, seed=0)
    out = tmp_path / "spec.json"
    out.write_text(json.dumps(spec))
    reloaded = load_spec(out)
    assert reloaded == spec


def test_usage_targets_default_to_one_unified_mark():
    from wedding_visual.mapping import questionnaire_to_spec

    q = {
        "partner_a_name": {"latin": "Ana"},
        "partner_b_name": {"latin": "Ben"},
        "date": "2027-01-01",
        "design_basis": "names",
    }
    assert questionnaire_to_spec(q, seed=0)["usage_targets"] == ["invitation", "e-invite", "stage-backdrop"]
    q["usage_targets"] = ["merchandise"]
    assert questionnaire_to_spec(q, seed=0)["usage_targets"] == ["merchandise"]
