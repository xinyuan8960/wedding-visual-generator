"""Deterministic glyph outline extraction via fontTools.

Reading a glyph's outline out of a font file is already deterministic (same bytes in,
same contours out) -- this module just exposes that in the shape the layouts need: a
glyph's bounding box and advance width in font units, its outline as an SVG path 'd'
string after an arbitrary affine transform (so a caller can place it directly into canvas
space without a second drawing pass), and a point-in-outline test.

Font units are y-up with the baseline at y=0, which is the opposite convention from
SVG (y-down, origin top-left) -- callers are responsible for building a transform that
accounts for that; see layout/monogram.py.
"""
from __future__ import annotations

from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from ..repo_paths import repo_root

Bounds = tuple[float, float, float, float]  # xMin, yMin, xMax, yMax, in font units

DEFAULT_FONT_RELATIVE_PATH = "fonts/EBGaramond/EBGaramond-VariableFont_wght.ttf"


class GlyphNotFoundError(ValueError):
    pass


def default_font_path() -> Path:
    return repo_root(marker_dir="fonts") / DEFAULT_FONT_RELATIVE_PATH


class Font:
    """A loaded font, read once and reused for every glyph lookup.

    `variations` pins a variable font to one point on its design space (e.g.
    {"wght": 300}) via fontTools' instancer, which is deterministic. Without it, a
    variable font is read at its default instance.
    """

    def __init__(self, path: str | Path | None = None, variations: dict[str, float] | None = None):
        self.path = Path(path) if path is not None else default_font_path()
        ttfont = TTFont(str(self.path))
        if variations:
            ttfont = instantiateVariableFont(ttfont, variations)
        self._ttfont = ttfont
        self._glyph_set = ttfont.getGlyphSet()
        self._cmap = ttfont.getBestCmap()
        self.units_per_em: int = ttfont["head"].unitsPerEm

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

    def advance(self, char: str) -> float:
        return self._ttfont["hmtx"][self._glyph_name(char)][0]

    def cap_height(self) -> float:
        return self.bounds("H")[3]

    def contains(self, char: str, x: float, y: float) -> bool:
        """Whether font-space point (x, y) falls inside the glyph's filled outline."""
        pen = PointInsidePen(self._glyph_set, (x, y))
        self._glyph_set[self._glyph_name(char)].draw(pen)
        return pen.getResult()

    def path_d(self, char: str, transform: Transform) -> str:
        """SVG path 'd' data for this glyph's outline after applying `transform`."""
        svg_pen = SVGPathPen(self._glyph_set)
        pen = TransformPen(svg_pen, transform)
        self._glyph_set[self._glyph_name(char)].draw(pen)
        return svg_pen.getCommands()
