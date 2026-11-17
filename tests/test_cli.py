import json
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


def test_questionnaire_to_spec_to_stdout(capsys):
    rc = main(
        ["questionnaire-to-spec", str(FIXTURES / "valid_questionnaire.json"), "--seed", "3"]
    )
    assert rc == 0
    spec = json.loads(capsys.readouterr().out)
    assert spec["seed"] == 3
    assert spec["design_basis"] == "names"


def test_questionnaire_to_spec_to_file(tmp_path, capsys):
    out_path = tmp_path / "spec.json"
    rc = main(
        [
            "questionnaire-to-spec",
            str(FIXTURES / "valid_questionnaire.json"),
            "--seed",
            "3",
            "-o",
            str(out_path),
        ]
    )
    assert rc == 0
    assert "OK" in capsys.readouterr().out
    spec = json.loads(out_path.read_text())
    assert spec["seed"] == 3


def test_questionnaire_to_spec_rejects_invalid_questionnaire(capsys):
    rc = main(
        [
            "questionnaire-to-spec",
            str(FIXTURES / "invalid_questionnaire_missing_photo_ref.json"),
            "--seed",
            "0",
        ]
    )
    assert rc == 1
    assert "failed schema validation" in capsys.readouterr().err


def test_monogram_layout_for_names_basis(capsys):
    rc = main(["monogram-layout", str(FIXTURES / "valid_spec_names.json")])
    assert rc == 0
    layout = json.loads(capsys.readouterr().out)
    assert layout["arrangement"] == "interlocking"
    assert {g["char"] for g in layout["glyphs"]} == {"A", "J"}


def test_monogram_layout_rejects_photo_basis(capsys):
    rc = main(["monogram-layout", str(FIXTURES / "valid_spec_photo.json")])
    assert rc == 1
    assert "only handles 'names'" in capsys.readouterr().err


def test_render_to_stdout(capsys):
    rc = main(["render", str(FIXTURES / "valid_spec_names.json")])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("<svg")
    assert "<title>" in out


def test_render_to_svg_file(tmp_path, capsys):
    out_path = tmp_path / "logo.svg"
    rc = main(["render", str(FIXTURES / "valid_spec_names.json"), "-o", str(out_path)])
    assert rc == 0
    assert "OK" in capsys.readouterr().out
    assert out_path.read_text().startswith("<svg")


def test_render_rejects_photo_basis(capsys):
    rc = main(["render", str(FIXTURES / "valid_spec_photo.json")])
    assert rc == 1
    assert "got 'photo'" in capsys.readouterr().err


def test_render_png_reports_missing_renderer_clearly(monkeypatch, tmp_path, capsys):
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: None)
    rc = main(
        [
            "render",
            str(FIXTURES / "valid_spec_names.json"),
            "--png",
            str(tmp_path / "logo.png"),
        ]
    )
    assert rc == 1
    assert "brew install" in capsys.readouterr().err


def test_qa_passes_cleanly_for_the_fixture_spec(capsys):
    rc = main(["qa", str(FIXTURES / "valid_spec_names.json")])
    assert rc == 0


def test_qa_json_output_is_a_list_of_findings(capsys):
    rc = main(["qa", str(FIXTURES / "valid_spec_names.json"), "--json"])
    assert rc == 0
    findings = json.loads(capsys.readouterr().out)
    assert isinstance(findings, list)


def test_qa_rejects_photo_basis(capsys):
    rc = main(["qa", str(FIXTURES / "valid_spec_photo.json")])
    assert rc == 1
    assert "got 'photo'" in capsys.readouterr().err
