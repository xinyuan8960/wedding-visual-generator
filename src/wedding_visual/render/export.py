"""SVG -> PNG/PDF export via whichever converter is actually installed.

No single SVG-to-raster tool is a safe assumption across dev machines (see
docs/research.md's survey of neonwatty/logo-designer-skill and
kaankiziltug/logo-design-skill, which both hit this same problem and both solve it the
same way): detect what's available and use it, rather than hard-depending on one tool.
`resvg` is the preferred PNG renderer (accurate, fast, single static binary); `rsvg-convert`
and `inkscape` are the fallbacks, and also the only ones here that can produce a PDF.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class RendererNotFoundError(RuntimeError):
    pass


_PNG_TOOLS = ("resvg", "rsvg-convert", "inkscape")
_PDF_TOOLS = ("rsvg-convert", "inkscape")  # resvg does not produce PDF

_INSTALL_HINT = (
    "No SVG renderer found. Install one of:\n"
    "  brew install resvg        (recommended for PNG)\n"
    "  brew install librsvg      (provides rsvg-convert; also does PDF)\n"
    "  brew install inkscape     (does both, heaviest install)"
)


def _find_tool(candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        if shutil.which(name):
            return name
    return None


def _run_png(tool: str, svg_path: Path, png_path: Path, size: int | None) -> None:
    if tool == "resvg":
        cmd = ["resvg", str(svg_path), str(png_path)]
        if size:
            cmd += ["--width", str(size), "--height", str(size)]
    elif tool == "rsvg-convert":
        cmd = ["rsvg-convert", "-o", str(png_path)]
        if size:
            cmd += ["-w", str(size), "-h", str(size)]
        cmd.append(str(svg_path))
    elif tool == "inkscape":
        cmd = [
            "inkscape",
            str(svg_path),
            "--export-type=png",
            f"--export-filename={png_path}",
        ]
        if size:
            cmd += ["-w", str(size), "-h", str(size)]
    else:  # pragma: no cover - _find_tool only returns names from _PNG_TOOLS
        raise AssertionError(f"unhandled tool {tool!r}")
    subprocess.run(cmd, check=True, capture_output=True)


def _run_pdf(tool: str, svg_path: Path, pdf_path: Path) -> None:
    if tool == "rsvg-convert":
        cmd = ["rsvg-convert", "-f", "pdf", "-o", str(pdf_path), str(svg_path)]
    elif tool == "inkscape":
        cmd = [
            "inkscape",
            str(svg_path),
            "--export-type=pdf",
            f"--export-filename={pdf_path}",
        ]
    else:  # pragma: no cover - _find_tool only returns names from _PDF_TOOLS
        raise AssertionError(f"unhandled tool {tool!r}")
    subprocess.run(cmd, check=True, capture_output=True)


def export_png(svg_path: str | Path, png_path: str | Path, size: int | None = None) -> str:
    """Render `svg_path` to a PNG at `png_path`. Returns the name of the tool used."""
    tool = _find_tool(_PNG_TOOLS)
    if tool is None:
        raise RendererNotFoundError(_INSTALL_HINT)
    _run_png(tool, Path(svg_path), Path(png_path), size)
    return tool


def export_pdf(svg_path: str | Path, pdf_path: str | Path) -> str:
    """Render `svg_path` to a PDF at `pdf_path`. Returns the name of the tool used."""
    tool = _find_tool(_PDF_TOOLS)
    if tool is None:
        raise RendererNotFoundError(_INSTALL_HINT)
    _run_pdf(tool, Path(svg_path), Path(pdf_path))
    return tool
