from pathlib import Path

from wedding_visual.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_validate_spec_ok(capsys):
    rc = main(["validate-spec", str(FIXTURES / "valid_spec_names.json")])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_validate_spec_failure(capsys):
    rc = main(["validate-spec", str(FIXTURES / "invalid_spec_bad_style_range.json")])
    assert rc == 1
    assert "failed schema validation" in capsys.readouterr().err


def test_validate_questionnaire_ok(capsys):
    rc = main(["validate-questionnaire", str(FIXTURES / "valid_questionnaire.json")])
    assert rc == 0
    assert "OK" in capsys.readouterr().out
