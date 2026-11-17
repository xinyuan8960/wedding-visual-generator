"""Deterministic questionnaire -> spec transformer.

Per the project's core design decision, a model's only allowed job is turning raw
questionnaire answers into a structured spec.json. In practice, once the questionnaire
answers are already schema-validated JSON (see questionnaire.py), nearly all of that
"structuring" is mechanical: most fields pass straight through, and the remaining ones
(stroke width, whitespace, monogram arrangement, silhouette simplification) are small
numeric/enum choices that a fixed formula can make just as well as a model can, and with
the advantage of being testable and reproducible. So this module does the whole transform
in plain code, with zero model calls. A model is still useful upstream of this (running the
interactive interview that produces the questionnaire.json in the first place, or inferring
style_sliders from free-text/reference-image descriptions the user gives instead of moving a
slider) and potentially downstream once templates/ holds more than one template per
design_basis and template SELECTION becomes a real judgment call rather than the only option.

The numeric formulas below (stroke width ratio, whitespace ratio, silhouette tolerance, the
monogram-arrangement rule) are initial heuristics, not design authority: they encode a
reasonable first guess at how a style slider should affect layout, written down explicitly so
they can be inspected, tested, and tuned once a real renderer exists (phase 4+) to look at the
result against. Treat a surprising output as a reason to revisit the formula, not as a bug in
the questionnaire.
"""
from __future__ import annotations

from typing import Any

SPEC_VERSION = "0.1"

DEFAULT_SLIDERS: dict[str, float] = {
    "minimal_to_ornate": 0.5,
    "modern_to_classic": 0.5,
    "eastern_to_western": 0.5,
    "handwritten_to_print": 0.5,
}

# One template per design_basis for now (only template we build in phase 4). Once
# templates/ holds more than one candidate per basis, this becomes a lookup/scoring
# function over a template catalog instead of a constant.
_TEMPLATE_ID_BY_BASIS = {
    "names": "monogram-interlocking-v1",
    "photo": "silhouette-badge-v1",
}


def _lerp(lo: float, hi: float, t: float) -> float:
    return lo + (hi - lo) * t


def _sliders(questionnaire: dict[str, Any]) -> dict[str, float]:
    sliders = dict(DEFAULT_SLIDERS)
    sliders.update(questionnaire.get("style_sliders", {}))
    return sliders


def _monogram_arrangement(sliders: dict[str, float]) -> str:
    """Pick a monogram arrangement from the eastern/western and modern/classic sliders.

    Heuristic, not a visual judgment: a strong eastern preference favours a circular
    seal/stamp aesthetic; otherwise classic leans toward the traditional interlocking
    monogram, modern toward a clean side-by-side layout, and the middle ground toward a
    stacked lockup as a neutral default.
    """
    if sliders["eastern_to_western"] < 0.35:
        return "circular-badge"
    if sliders["modern_to_classic"] >= 0.6:
        return "interlocking"
    if sliders["modern_to_classic"] <= 0.4:
        return "side-by-side"
    return "stacked"


def _layout_params(sliders: dict[str, float]) -> dict[str, float]:
    ornate = sliders["minimal_to_ornate"]
    # More ornate -> thinner relative strokes (delicate flourish); more minimal -> bolder
    # strokes (impact and small-size legibility).
    stroke_width_ratio = _lerp(0.06, 0.02, ornate)
    # More ornate -> fills more of the canvas (less raw whitespace); more minimal -> more
    # breathing room.
    whitespace_ratio = _lerp(0.30, 0.15, ornate)
    return {
        "stroke_width_ratio": round(stroke_width_ratio, 4),
        "whitespace_ratio": round(whitespace_ratio, 4),
    }


def _photo_silhouette_params(questionnaire: dict[str, Any], sliders: dict[str, float]) -> dict[str, Any]:
    ornate = sliders["minimal_to_ornate"]
    # More ornate -> keep more contour detail (lower simplification tolerance, thinner
    # stroke); more minimal -> simplify harder and draw bolder.
    simplify_tolerance = _lerp(4.0, 1.0, ornate)
    stroke_width = _lerp(4.0, 2.0, ornate)
    return {
        "source_ref": questionnaire["photo_ref"],
        "simplify_tolerance": round(simplify_tolerance, 2),
        "stroke_width": round(stroke_width, 2),
    }


def questionnaire_to_spec(questionnaire: dict[str, Any], seed: int) -> dict[str, Any]:
    """Deterministically derive a spec.json dict from validated questionnaire answers.

    `questionnaire` must already satisfy schema/questionnaire.schema.json (call
    wedding_visual.questionnaire.load_questionnaire first). The result satisfies
    schema/spec.schema.json; this function does not validate it itself so callers can
    choose whether to pay that cost, but every caller in this codebase does.
    """
    # questionnaire["venues"] is intentionally dropped here: nothing in spec.schema.json
    # consumes a venue yet (no template sizes or composes against a specific location).
    # Revisit if a future template (e.g. a stage backdrop) needs it.
    sliders = _sliders(questionnaire)
    design_basis = questionnaire["design_basis"]

    names: dict[str, Any] = {
        "partner_a": dict(questionnaire["partner_a_name"]),
        "partner_b": dict(questionnaire["partner_b_name"]),
    }
    if "date" in questionnaire:
        names["date"] = questionnaire["date"]

    spec: dict[str, Any] = {
        "version": SPEC_VERSION,
        "seed": seed,
        "design_basis": design_basis,
        "names": names,
        "style": {k: round(v, 4) for k, v in sliders.items()},
        "layout": {
            "template_id": _TEMPLATE_ID_BY_BASIS[design_basis],
            **_layout_params(sliders),
        },
    }

    if design_basis == "names":
        spec["layout"]["monogram_arrangement"] = _monogram_arrangement(sliders)
    else:
        spec["photo_silhouette"] = _photo_silhouette_params(questionnaire, sliders)

    if questionnaire.get("usage_targets"):
        spec["usage_targets"] = list(questionnaire["usage_targets"])
    if questionnaire.get("preferred_elements"):
        spec["preferred_elements"] = list(questionnaire["preferred_elements"])
    if questionnaire.get("avoid_elements"):
        spec["avoid_elements"] = list(questionnaire["avoid_elements"])

    return spec
