"""A glyph placed on the canvas by a uniform scale + translation (with the y flip from
font space to SVG space), plus the operations every layout needs on it."""
from __future__ import annotations

from dataclasses import dataclass

from fontTools.misc.transform import Transform

from .glyphs import Font


@dataclass(frozen=True)
class Placement:
    font: Font
    char: str
    scale: float
    dx: float
    dy: float

    @classmethod
    def centered(cls, font: Font, char: str, scale: float, cx: float, cy: float) -> Placement:
        """Place `char` so its bounding-box center lands on canvas point (cx, cy)."""
        x0, y0, x1, y1 = font.bounds(char)
        return cls(font, char, scale, cx - scale * (x0 + x1) / 2, cy + scale * (y0 + y1) / 2)

    @property
    def transform(self) -> Transform:
        return Transform(self.scale, 0, 0, -self.scale, self.dx, self.dy)

    def bbox(self) -> list[float]:
        x0, y0, x1, y1 = self.font.bounds(self.char)
        s = self.scale
        return [round(s * x0 + self.dx, 3), round(-s * y1 + self.dy, 3), round(s * x1 + self.dx, 3), round(-s * y0 + self.dy, 3)]

    def contains_canvas_point(self, x: float, y: float) -> bool:
        return self.font.contains(self.char, (x - self.dx) / self.scale, (self.dy - y) / self.scale)

    def to_dict(self) -> dict:
        return {"char": self.char, "d": self.font.path_d(self.char, self.transform), "bbox": self.bbox()}
