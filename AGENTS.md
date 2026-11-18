# AGENTS.md

Instructions for any coding agent (Codex, Claude Code, Cursor, ...) working in this repo.

## Using the generator for someone

Follow [`skills/wedding-monogram/SKILL.md`](skills/wedding-monogram/SKILL.md) -- it is
agent-agnostic despite the frontmatter: ask the questionnaire, write
`private/<slug>/questionnaire.json`, then run the CLI. Your model is used only to turn
the conversation into that JSON. Never hand-write or hand-edit SVG, and never trace a
reference image.

## Developing

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'
python -m pytest -q                      # must stay green
python -m wedding_visual eval            # pass rate over eval/cases/, reported in README
```

- Same spec -> byte-identical output. Any randomness must come from `spec.seed`.
- Templates store parameters only (layout type, font, ratios, motif type), never
  geometry taken from someone else's artwork.
- Fonts: open licenses only (OFL etc.), each listed with source and license in
  `fonts/README.md`.
- `private/` and `refs/` are gitignored: user photos, reference images, real names and
  outputs live there. Examples in the repo use placeholder names.
- Taste that can be measured goes into `src/wedding_visual/qa/` as a check (e.g.
  `blade-like-connector`, `detached-connector`), not into a comment.
- Small commits, one decision or feature each, message explaining why.
