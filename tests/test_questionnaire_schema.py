from pathlib import Path

import pytest

from wedding_visual.questionnaire import load_questionnaire
from wedding_visual.validation import ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_questionnaire_loads():
    answers = load_questionnaire(FIXTURES / "valid_questionnaire.json")
    assert answers["design_basis"] == "names"


def test_photo_basis_without_photo_ref_is_rejected():
    with pytest.raises(ValidationError):
        load_questionnaire(FIXTURES / "invalid_questionnaire_missing_photo_ref.json")
