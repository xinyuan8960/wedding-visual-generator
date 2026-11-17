# wedding-visual-generator

A deterministic wedding logo generator. A model's only job is turning questionnaire
answers into a structured `spec.json`; everything after that — layout, template
application, rendering, quality checks — is plain, tested Python. The same `spec.json`
and seed always produce the same output; there is no "generate → look → regenerate"
loop anywhere in the pipeline.

This README is partial — it covers what's built so far (through the evaluation set). The
full version (cost comparison against the naive "model draws SVG directly" approach,
architecture diagram, font/license sourcing) is still to come, once the photo-silhouette
pipeline (`design_basis: "photo"`) exists alongside the names pipeline below.

## Status

| Phase | What | Status |
|---|---|---|
| 1 | Research (`docs/research.md`) | done |
| 2 | Scaffold, JSON schemas, test harness | done |
| 3 | Questionnaire → spec mapping (zero model calls) | done |
| 4 | fontTools monogram typography | done |
| 5 | First parametric template + SVG/PNG/PDF export | done |
| 6 | QA module (overflow, overlap, contrast, bleed) | done |
| 7 | **Evaluation set (this phase)** | done |
| 8 | Photo-silhouette pipeline (`design_basis: "photo"`) | not started |
| 9 | SKILL.md / AGENTS.md | not started |

## Quickstart

```bash
pip install -e ".[dev]"

# No model involved anywhere below this line.
python -m wedding_visual questionnaire-to-spec questionnaire.json --seed 0 -o spec.json
python -m wedding_visual render spec.json -o logo.svg --png logo.png   # --png needs resvg/rsvg-convert/inkscape
python -m wedding_visual qa spec.json
python -m wedding_visual eval   # run the 10-case evaluation set below
```

## Evaluation set

`eval/cases/` holds 10 fictional name pairs (placeholder names only — see the project's
copyright constraints), chosen to spread across all four `monogram_arrangement` values,
include descender-heavy initials (J, Q, Y, a struck-through Ø), a same-initial pair, an
accented initial, every print usage target at least once, and one case with no
`style_sliders` at all (exercises the neutral defaults). Each runs the full pipeline —
questionnaire → `questionnaire_to_spec` → render plan → `qa.checks.audit` — with no manual
intervention.

Regenerate this table with `python -m wedding_visual eval`.

| Case | Names | Arrangement | FAIL | WARN | INFO |
|---|---|---|---|---|---|
| 01-mira-daniel | Mira Chen & Daniel Osei | side-by-side | 0 | 0 | 1 |
| 02-priya-jonas | Priya Nair & Jonas Falk | interlocking | 0 | 0 | 1 |
| 03-yusuf-elena | Yusuf Demir & Elena Petrova | circular-badge | 0 | 0 | 1 |
| 04-quincy-wren | Quincy Adebayo & Wren Sato | stacked | 0 | 0 | 1 |
| 05-amara-aiden | Amara Osei & Aiden Cole | side-by-side | 0 | 0 | 1 |
| 06-oyvind-noor | Øyvind Berg & Noor Haddad | interlocking | 0 | 0 | 1 |
| 07-jing-marcus | Jing Lu & Marcus Villanueva | interlocking | 0 | 1 | 1 |
| 08-fatima-lucas | Fatima Zahra & Lucas Meyer | side-by-side | 0 | 0 | 1 |
| 09-grace-henrik | Grace Kim & Henrik Voss | circular-badge | 0 | 0 | 1 |
| 10-ibrahim-chloe | Ibrahim Osei & Chloe Dubois | stacked | 0 | 0 | 1 |

**Pass rate: 100% (10/10)** — zero FAIL findings. The one WARN (case 07) is a genuine
near-miss: that case's decorative rule would render at 0.70px at favicon size, just under
the 0.75px minimum — not a bug, a real signal about that parameter combination. The INFO
on every row is expected: `monogram-v1`'s `background` is `"none"` by default, so the
contrast check can't evaluate against a real background until one is composited in.

This set also did its job once already during development: it caught a real geometry bug
(the `circular-badge` ring's stroke could overlap the letters it encircles, because the
letters were being fit to the ring's full radius instead of its inner edge) that the
earlier targeted unit tests for `layout/monogram.py` didn't exercise, since none of them
combined a large `stroke_width_ratio` with the `circular-badge` arrangement the way a real
eastern-leaning, bold-style questionnaire answer does. Fixed in `render/plan.py`; see its
comments and `qa/checks.py`'s `check_motif_glyph_overlap` for how the fix is verified.
