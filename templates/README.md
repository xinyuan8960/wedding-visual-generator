Parametric layout templates referenced by `spec.layout.template_id`. Each file stores only
parameters (canvas size, font path, ink/background color, motif choice) — never another
work's geometry.

## monogram-v2

`layout: "diagonal-ampersand"`, for `design_basis: "names"`. First initial upper-left,
second lower-right, joined by a script `&` across the opposite diagonal; an open hairline
arc that breaks wherever it meets a glyph's ink; then the first names in widely tracked
light caps and the date. Ignores `layout.monogram_arrangement`. The style direction came
from a reference image the user supplied (kept in gitignored `private/`); only layout
conventions and proportions were taken from it, expressed as the parameters in this file
— no glyph or ornament geometry was traced. Drawing logic: `render/plan_diagonal.py`.

The `&` is placed by a search that makes it interlock with both initials
(`layout/diagonal.py`). With `layout.ornament: "olive-sprig"` (the questionnaire default) a
procedural line-art olive branch grows from the arc's open end into the empty lower-left
(`render/sprig.py`): parametric leaves, no traced shapes; `spec.seed` jitters the leaves,
and any leaf that would touch a letter is dropped.

## monogram-v1

The first template, for `design_basis: "names"`. Drawing logic lives in
`wedding_visual/render/svg.py`: it places the two initials via `layout/monogram.py`, then
adds one decorative motif chosen by `layout.monogram_arrangement` — a ring around a
`circular-badge` monogram, or a rule-and-diamond flourish centered beneath the letters for
the other three arrangements (skipped if there isn't enough vertical clearance to draw it
without colliding with the letters).
