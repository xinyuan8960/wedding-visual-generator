"""Run every case in eval/cases/ through questionnaire -> spec -> render plan -> QA.

This is the project's regression net for the names-basis pipeline: 10 fictional name
pairs (see eval/cases/*.json) chosen to spread across the four monogram arrangements,
descender-heavy initials (J, Q, Y, O with a stroke through it), a same-initial pair, an
accented initial, every print usage target at least once, and one case with no
style_sliders at all to exercise the neutral defaults. A seed is required for
questionnaire_to_spec but, as of this phase, doesn't change any geometry (nothing in the
pipeline yet consumes randomness) -- it's threaded through so results stay reproducible
once it does.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .mapping import questionnaire_to_spec
from .qa.checks import audit
from .questionnaire import load_questionnaire
from .render.plan import build_render_plan
from .repo_paths import repo_root


def default_cases_dir() -> Path:
    return repo_root(marker_dir="eval") / "eval" / "cases"


def run_eval_set(
    cases_dir: str | Path | None = None, seed: int = 0, template_id: str | None = None
) -> list[dict[str, Any]]:
    """`template_id` overrides the one questionnaire_to_spec picks, to evaluate any template."""
    cases_dir = Path(cases_dir) if cases_dir else default_cases_dir()
    results = []
    for path in sorted(cases_dir.glob("*.json")):
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        questionnaire = load_questionnaire(path)
        spec = questionnaire_to_spec(questionnaire, seed=seed)
        if template_id:
            spec["layout"]["template_id"] = template_id
        plan = build_render_plan(spec)
        findings = audit(plan)

        counts = {"FAIL": 0, "WARN": 0, "INFO": 0}
        for f in findings:
            counts[f["level"]] += 1

        results.append(
            {
                "case": path.stem,
                "partner_a": raw["partner_a_name"].get("latin"),
                "partner_b": raw["partner_b_name"].get("latin"),
                "arrangement": plan["arrangement"],
                "findings": findings,
                "counts": counts,
                "passed": counts["FAIL"] == 0,
            }
        )
    return results


def pass_rate(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if r["passed"]) / len(results)
