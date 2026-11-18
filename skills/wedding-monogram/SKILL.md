---
name: wedding-monogram
description: Design a wedding monogram logo from the couple's names. Walk the user through a short questionnaire, then generate the logo with this repo's deterministic CLI (questionnaire -> spec -> SVG -> QA). Use when someone wants a wedding logo, monogram, or initials mark for invitations, e-invites, stage backdrops or merchandise.
---

# Wedding monogram

You run the conversation; the code does the design. Your only creative output is a
`questionnaire.json` filled from the user's answers. Everything after that — the spec,
the layout, the SVG, the quality checks — is deterministic code in this repo: the same
answers always give byte-identical output.

## Hard rules

- **Never write or edit SVG yourself**, and never "look and adjust" the image by hand.
  If the user wants something different, change the questionnaire/spec and re-run.
- **Never trace or copy geometry from a reference image.** Reference images the user
  shares only inform style answers; they are not inputs to the generator.
- Everything the user provides (names, dates, reference images, outputs) goes under
  `private/` in the repo, which is gitignored. Never commit it.
- Photo-to-line-drawing mode is **not available** in this skill. If the user asks for it,
  say so plainly and offer the names-based monogram.

## Setup

The repo root is two levels above this file (resolve symlinks). Run every command from
there:

```bash
cd <repo root>
test -d .venv || (python3 -m venv .venv && .venv/bin/pip install -q -e '.[dev]')
source .venv/bin/activate
```

If `python -m wedding_visual` reports `No module named wedding_visual`, prefix the
command with `PYTHONPATH=src`.

## 1. Questionnaire

Ask in the user's language, a few questions at a time, conversationally — not as a form
dump. Required answers first:

1. **Both partners' names.** Latin-script name is required for each (the monogram uses
   its first letter; for a Chinese name, ask which romanization they use). A CJK name is
   optional and recorded.
2. **Wedding date** (`YYYY-MM-DD`). Printed under the names.
3. **Design basis:** always `names` for this skill.

Then optional, skip anything they don't care about:

4. **What the logo will go on** — ask about *items*, not the venue (users answer "where"
   with the wedding location): paper invitation (`invitation`), e-invite (`e-invite`),
   stage backdrop (`stage-backdrop`), merchandise (`merchandise`). If they skip it, the
   mapping defaults to one unified mark for invitation + e-invite + backdrop. Print uses
   trigger a bleed-margin check. A venue answer goes in `venues`; it doesn't affect the
   current template.
5. **Style feel**, four 0–1 sliders. Ask in plain words and convert, e.g. "more minimal
   or more ornate?" → 0.2 / 0.5 / 0.8: `minimal_to_ornate`, `modern_to_classic`,
   `eastern_to_western`, `handwritten_to_print`.
6. **Elements they love / want to avoid** (free text lists).

Be honest about what the answers change today: the default template (`monogram-v2`,
diagonal initials interlocked with a script `&`, an open hairline arc, names and date in
tracked capitals) has a fixed composition. Names, initials and date drive it; the style
sliders and element lists are recorded in the spec for future templates but don't alter
v2's look yet. Say this before asking optional questions so the user can skip them.

Write the answers to `private/<slug>/questionnaire.json` (slug = both first names,
lowercase, e.g. `private/sofia-marco/`). Shape (see `schema/questionnaire.schema.json`):

```json
{
  "partner_a_name": { "latin": "Sofia Lin", "cjk": "林索菲" },
  "partner_b_name": { "latin": "Marco Rossi" },
  "date": "2027-10-10",
  "design_basis": "names",
  "usage_targets": ["invitation", "e-invite"],
  "style_sliders": { "minimal_to_ornate": 0.3 },
  "preferred_elements": ["music"],
  "avoid_elements": ["anything sharp"]
}
```

Read the answers back in one short summary and get a yes before generating.

## 2. Generate

```bash
D=private/<slug>
python -m wedding_visual validate-questionnaire $D/questionnaire.json
python -m wedding_visual questionnaire-to-spec $D/questionnaire.json --seed 0 -o $D/spec.json
python -m wedding_visual render $D/spec.json -o $D/logo.svg --png $D/logo.png --png-size 1024
python -m wedding_visual qa $D/spec.json
```

If validation fails, fix the questionnaire from the error message (or ask the user) —
don't skip validation.

`--png` needs `resvg`, `rsvg-convert` or `inkscape`. If none is installed, the command
says so: re-run `render` without `--png`, and on macOS make a preview with
`qlmanage -t -s 1024 -o $D $D/logo.svg` (writes `$D/logo.svg.png`). Otherwise the SVG
opens in any browser.

## 3. Present

- Give the user the file path(s) to open, and show the PNG if you can view images.
- Summarize QA findings in plain words. Levels: **FAIL** = likely broken, fix before
  using; **WARN** = worth a look; **INFO** = context. Expected on v2: a `thin-motif-stroke`
  WARN (the hairline arc disappears at favicon size — fine for print and screens) and a
  `no-background` INFO (transparent PNG/SVG).
- A `detached-connector` WARN means those two initials leave too big a gap for the `&` to
  interlock without cramming them; say so honestly rather than hiding it.

## 4. Revise

Change the questionnaire (names, date, usage) and re-run step 2. Also available:
`layout.template_id: "monogram-v1"` in the spec for the older geometric template. v2 has
no seed-driven variants yet — re-running with another seed gives the same mark; don't
promise variants.
