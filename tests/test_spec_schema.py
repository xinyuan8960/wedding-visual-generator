from pathlib import Path

import pytest

from wedding_visual.spec import load_spec
from wedding_visual.validation import ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name", ["valid_spec_names.json", "valid_spec_photo.json"])
def test_valid_specs_load(name):
    spec = load_spec(FIXTURES / name)
    assert spec["version"] == "0.1"
    assert isinstance(spec["seed"], int)


def test_photo_basis_without_photo_silhouette_is_rejected():
    with pytest.raises(ValidationError):
        load_spec(FIXTURES / "invalid_spec_missing_photo_silhouette.json")


def test_style_slider_out_of_range_is_rejected():
    with pytest.raises(ValidationError):
        load_spec(FIXTURES / "invalid_spec_bad_style_range.json")


def test_missing_required_field_is_rejected(tmp_path):
    import json

    data = json.loads((FIXTURES / "valid_spec_names.json").read_text())
    del data["layout"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        load_spec(bad)


def test_unknown_property_is_rejected(tmp_path):
    import json

    data = json.loads((FIXTURES / "valid_spec_names.json").read_text())
    data["totally_made_up_field"] = True
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        load_spec(bad)
