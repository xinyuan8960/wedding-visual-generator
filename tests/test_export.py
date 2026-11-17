import shutil

import pytest

from wedding_visual.render.export import RendererNotFoundError, export_pdf, export_png


def test_export_png_raises_a_helpful_error_when_no_tool_is_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RendererNotFoundError) as exc_info:
        export_png(tmp_path / "in.svg", tmp_path / "out.png")
    assert "brew install" in str(exc_info.value)


def test_export_pdf_raises_a_helpful_error_when_no_tool_is_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RendererNotFoundError):
        export_pdf(tmp_path / "in.svg", tmp_path / "out.pdf")


def test_export_png_prefers_resvg_when_multiple_tools_are_present(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    import wedding_visual.render.export as export_mod

    monkeypatch.setattr(export_mod, "_run_png", lambda tool, *a: calls.append(tool))
    tool = export_png(tmp_path / "in.svg", tmp_path / "out.png")
    assert tool == "resvg"
    assert calls == ["resvg"]


@pytest.mark.skipif(shutil.which("resvg") is None, reason="resvg not installed")
def test_export_png_with_real_resvg_produces_a_file(tmp_path):
    svg = tmp_path / "in.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                    '<rect width="10" height="10" fill="black"/></svg>')
    png = tmp_path / "out.png"
    export_png(svg, png, size=32)
    assert png.exists()
    assert png.stat().st_size > 0


@pytest.mark.skipif(
    shutil.which("rsvg-convert") is None and shutil.which("inkscape") is None,
    reason="no PDF-capable renderer installed",
)
def test_export_pdf_with_real_tool_produces_a_file(tmp_path):
    svg = tmp_path / "in.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                    '<rect width="10" height="10" fill="black"/></svg>')
    pdf = tmp_path / "out.pdf"
    export_pdf(svg, pdf)
    assert pdf.exists()
    assert pdf.stat().st_size > 0
