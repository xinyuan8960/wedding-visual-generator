"""Deterministic glyph outline extraction via fontTools.

Reading a glyph's outline out of a font file is already deterministic (same bytes in,
same contours out) -- this module just exposes that in the shape the monogram layout
needs: a glyph's bounding box in font units, and its outline as an SVG path 'd' string
after an arbitrary affine transform (so a caller can place it directly into canvas
space without a second drawing pass).

Font units are y-up with the baseline at y=0, which is the opposite convention from
SVG (y-down, origin top-left) -- callers are responsible for building a transform that
accounts for that; see layout/monogram.py.
"""
from __future__ import annotations

from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from ..repo_paths import repo_root

Bounds = tuple[float, float, float, float]  # xMin, yMin, xMax, yMax, in font units

DEFAULT_FONT_RELATIVE_PATH = "fonts/EBGaramond/EBGaramond-VariableFont_wght.ttf"


class GlyphNotFoundError(ValueError):
    pass


def default_font_path() -> Path:
    return repo_root(marker_dir="fonts") / DEFAULT_FONT_RELATIVE_PATH


class Font:
    """A loaded font, read once and reused for every glyph lookup.

    Note: this reads the font's default outline directly from the 'glyf'/'CFF ' table.
    For a variable font that means the default named instance (whatever weight/width the
    font's designer set as the non-variable fallback) -- we do not instantiate other
    points on the design space. Fine for monogram initials, which don't need weight
    variation yet.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else default_font_path()
        self._ttfont = TTFont(str(self.path))
        self._glyph_set = self._ttfont.getGlyphSet()
        self._cmap = self._ttfont.getBestCmap()
        self.units_per_em: int = self._ttfont["head"].unitsPerEm

    def _glyph_name(self, char: str) -> str:
        try:
            return self._cmap[ord(char)]
        except KeyError as exc:
            raise GlyphNotFoundError(f"Font {self.path.name} has no glyph for {char!r}") from exc

    def bounds(self, char: str) -> Bounds:
        pen = BoundsPen(self._glyph_set)
        self._glyph_set[self._glyph_name(char)].draw(pen)
        if pen.bounds is None:
            raise GlyphNotFoundError(f"Glyph for {char!r} has no outline (e.g. a space)")
        return pen.bounds

    def path_d(self, char: str, transform: Transform) -> str:
        """SVG path 'd' data for this glyph's outline after applying `transform`."""
        svg_pen = SVGPathPen(self._glyph_set)
        pen = TransformPen(svg_pen, transform)
        self._glyph_set[self._glyph_name(char)].draw(pen)
        return svg_pen.getCommands()
