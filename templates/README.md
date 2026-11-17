Parametric layout templates referenced by `spec.layout.template_id`. Each file stores only
parameters (canvas size, font path, ink/background color, motif choice) — never another
work's geometry.

## monogram-v1

The only template so far, for `design_basis: "names"`. Drawing logic lives in
`wedding_visual/render/svg.py`: it places the two initials via `layout/monogram.py`, then
adds one decorative motif chosen by `layout.monogram_arrangement` — a ring around a
`circular-badge` monogram, or a rule-and-diamond flourish centered beneath the letters for
the other three arrangements (skipped if there isn't enough vertical clearance to draw it
without colliding with the letters).
