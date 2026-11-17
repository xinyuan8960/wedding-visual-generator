import pytest

from wedding_visual.qa.checks import (
    audit,
    check_bleed_margin,
    check_contrast,
    check_min_stroke_width,
    check_motif_glyph_overlap,
    check_overflow,
)
from wedding_visual.render.plan import build_render_plan
from wedding_visual.spec import load_spec
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _base_plan(**overrides) -> dict:
    plan = {
        "canvas_size": 512.0,
        "ink": "#1a1a1a",
        "background": None,
        "glyphs": [
            {"char": "A", "bbox": [50.0, 50.0, 200.0, 300.0]},
            {"char": "J", "bbox": [250.0, 60.0, 400.0, 400.0]},
        ],
        "motif": {"type": None, "bbox": None, "stroke_width": None},
        "usage_targets": [],
    }
    plan.update(overrides)
    return plan


def test_check_overflow_passes_for_in_bounds_content():
    assert check_overflow(_base_plan()) == []


def test_check_overflow_fails_when_a_glyph_exceeds_the_canvas():
    plan = _base_plan(glyphs=[{"char": "A", "bbox": [-10.0, 0.0, 200.0, 300.0]}])
    findings = check_overflow(plan)
    assert len(findings) == 1
    assert findings[0]["level"] == "FAIL"
    assert findings[0]["code"] == "overflow"


def test_check_motif_glyph_overlap_passes_when_disjoint():
    plan = _base_plan(motif={"type": "ring", "bbox": [0.0, 420.0, 512.0, 512.0], "stroke_width": 10.0})
    assert check_motif_glyph_overlap(plan) == []


def test_check_motif_glyph_overlap_fails_when_overlapping():
    plan = _base_plan(motif={"type": "ring", "bbox": [100.0, 100.0, 300.0, 300.0], "stroke_width": 10.0})
    findings = check_motif_glyph_overlap(plan)
    assert len(findings) == 1
    assert findings[0]["level"] == "FAIL"
    assert findings[0]["code"] == "motif-overlap"


def test_check_motif_glyph_overlap_skips_when_no_motif():
    assert check_motif_glyph_overlap(_base_plan()) == []


def test_check_min_stroke_width_warns_for_a_hairline_on_a_large_canvas():
    plan = _base_plan(
        canvas_size=4096.0,
        motif={"type": "ring", "bbox": [0, 0, 1, 1], "stroke_width": 2.0},  # tiny vs. 4096 canvas
    )
    findings = check_min_stroke_width(plan)
    assert len(findings) == 1
    assert findings[0]["level"] == "WARN"
    assert findings[0]["code"] == "thin-motif-stroke"


def test_check_min_stroke_width_passes_for_a_bold_stroke():
    plan = _base_plan(motif={"type": "ring", "bbox": [0, 0, 1, 1], "stroke_width": 20.0})
    assert check_min_stroke_width(plan) == []


def test_check_min_stroke_width_skips_when_no_motif():
    assert check_min_stroke_width(_base_plan()) == []


def test_check_contrast_info_when_no_background():
    findings = check_contrast(_base_plan())
    assert len(findings) == 1
    assert findings[0]["level"] == "INFO"


def test_check_contrast_fails_for_near_identical_colors():
    findings = check_contrast(_base_plan(background="#1b1b1b"))
    assert findings[0]["level"] == "FAIL"
    assert findings[0]["code"] == "low-contrast"


def test_check_contrast_warns_for_borderline_ratio():
    # ~3.9:1 -- passes the 3:1 floor but not the preferred 4.5:1
    findings = check_contrast(_base_plan(ink="#818181", background="#ffffff"))
    assert findings[0]["level"] == "WARN"
    assert findings[0]["code"] == "borderline-contrast"


def test_check_contrast_passes_for_black_on_white():
    assert check_contrast(_base_plan(ink="#000000", background="#ffffff")) == []


def test_check_bleed_margin_skipped_without_print_usage_targets():
    plan = _base_plan(usage_targets=["e-invite"], glyphs=[{"char": "A", "bbox": [0.0, 0.0, 512.0, 512.0]}])
    assert check_bleed_margin(plan) == []


def test_check_bleed_margin_warns_when_content_touches_the_edge():
    plan = _base_plan(usage_targets=["invitation"], glyphs=[{"char": "A", "bbox": [0.0, 0.0, 512.0, 300.0]}])
    findings = check_bleed_margin(plan)
    assert len(findings) == 1
    assert findings[0]["level"] == "WARN"
    assert findings[0]["code"] == "insufficient-bleed-margin"


def test_check_bleed_margin_passes_with_generous_margin():
    plan = _base_plan(usage_targets=["invitation"], glyphs=[{"char": "A", "bbox": [50.0, 50.0, 460.0, 460.0]}])
    assert check_bleed_margin(plan) == []


def test_audit_sorts_fail_before_warn_before_info():
    plan = _base_plan(
        background=None,  # INFO: no-background
        glyphs=[{"char": "A", "bbox": [-10.0, 0.0, 200.0, 300.0]}],  # FAIL: overflow
        motif={"type": "ring", "bbox": [0, 0, 1, 1], "stroke_width": 5.0},  # WARN: thin-motif-stroke
    )
    findings = audit(plan)
    levels = [f["level"] for f in findings]
    assert levels == sorted(levels, key={"FAIL": 0, "WARN": 1, "INFO": 2}.get)
    assert "FAIL" in levels


def test_audit_on_a_real_generated_plan_does_not_crash():
    spec = load_spec(FIXTURES / "valid_spec_names.json")
    plan = build_render_plan(spec)
    findings = audit(plan)
    assert isinstance(findings, list)
    assert all({"level", "code", "message"} <= f.keys() for f in findings)
