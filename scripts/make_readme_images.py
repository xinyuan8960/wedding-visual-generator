"""Regenerate the images under docs/images/ that the README shows.

    python scripts/make_readme_images.py

Every image is produced by the pipeline itself from placeholder names (never real
couples), so they double as a visual regression check: re-running this must not change
any file unless the rendering code changed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wedding_visual.layout import diagonal  # noqa: E402
from wedding_visual.render.svg import render_monogram_svg  # noqa: E402

OUT = ROOT / "docs" / "images"
CELL = 512


def spec(a: str, b: str, date: str = "2027-10-10", seed: int = 0, ornament: str = "olive-sprig") -> dict:
    return {
        "version": "0.1",
        "seed": seed,
        "design_basis": "names",
        "names": {"partner_a": {"latin": a}, "partner_b": {"latin": b}, "date": date},
        "layout": {"template_id": "monogram-v2", "ornament": ornament},
        "usage_targets": ["invitation", "e-invite", "stage-backdrop"],
    }


def _inner(svg: str) -> str:
    return re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)


def sheet(svgs: list[str], columns: int) -> str:
    """Lay rendered logos out in a grid on a white card (readable in GitHub dark mode)."""
    rows = -(-len(svgs) // columns)
    w, h = columns * CELL, rows * CELL
    cells = "".join(
        f'<g transform="translate({(i % columns) * CELL},{(i // columns) * CELL})">{_inner(s)}</g>'
        for i, s in enumerate(svgs)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="{w}" height="{h}" rx="16" fill="#ffffff"/>{cells}</svg>\n'
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    images = {
        "hero.svg": sheet([render_monogram_svg(spec("Sofia Lin", "Marco Rossi"))], 1),
        "gallery.svg": sheet(
            [
                render_monogram_svg(spec("Amara Osei", "Wren Sato", "2027-05-01")),
                render_monogram_svg(spec("Ingrid Berg", "Leo Haddad", "2027-08-14")),
                render_monogram_svg(spec("Quincy Adebayo", "Theo Falk", "2028-02-29")),
                render_monogram_svg(spec("Mira Chen", "Daniel Osei", "2027-06-12", ornament="none")),
            ],
            2,
        ),
        "seeds.svg": sheet([render_monogram_svg(spec("Sofia Lin", "Marco Rossi", seed=s)) for s in (0, 1, 2)], 3),
    }
    # Before/after for the interlock search: same spec, search disabled vs enabled.
    plain = spec("Sofia Lin", "Marco Rossi", ornament="none")
    saved = diagonal.MAX_PULL_STEPS
    diagonal.MAX_PULL_STEPS = -1  # empty search range -> nominal fixed positions
    try:
        before = render_monogram_svg(plain)
    finally:
        diagonal.MAX_PULL_STEPS = saved
    images["interlock.svg"] = sheet([before, render_monogram_svg(plain)], 2)

    for name, svg in images.items():
        (OUT / name).write_text(svg)
        print(f"wrote docs/images/{name}")


if __name__ == "__main__":
    main()
