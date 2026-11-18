import xml.etree.ElementTree as ET

import pytest

from wedding_visual.evaluation import run_eval_set
from wedding_visual.qa.checks import check_motif_glyph_overlap
from wedding_visual.render.plan import build_render_plan
from wedding_visual.render.svg import render_monogram_svg

SVG_NS = "{http://www.w3.org/2000/svg}"


def _spec(a="Sofia Lin", b="Marco Rossi", date="2027-10-10"):
    names = {"partner_a": {"latin": a}, "partner_b": {"latin": b}}
    if date:
        names["date"] = date
    return {
        "version": "0.1",
        "seed": 0,
        "design_basis": "names",
        "names": names,
        "layout": {"template_id": "monogram-v2", "whitespace_ratio": 0.2, "stroke_width_ratio": 0.03},
    }


@pytest.fixture(scope="module")
def plan():
    return build_render_plan(_spec())


def test_paints_initial_ampersand_initial_in_order(plan):
    assert [g["char"] for g in plan["glyphs"]] == ["S", "&", "M"]


def test_first_initial_upper_left_second_lower_right(plan):
    a, _, b = (g["bbox"] for g in plan["glyphs"])
    assert (a[0] + a[2]) / 2 < (b[0] + b[2]) / 2
    assert (a[1] + a[3]) / 2 < (b[1] + b[3]) / 2


def test_captions_are_first_names_and_formatted_date(plan):
    assert [c["text"] for c in plan["captions"]] == ["SOFIA & MARCO", "10.10.2027"]
    names_box, date_box = plan["captions"][0]["bbox"], plan["captions"][1]["bbox"]
    assert names_box[3] < date_box[1]  # date sits below the names


def test_date_caption_omitted_without_a_date():
    plan = build_render_plan(_spec(date=None))
    assert [c["text"] for c in plan["captions"]] == ["SOFIA & MARCO"]


def test_long_names_shrink_to_fit_max_width():
    plan = build_render_plan(_spec(a="Maximiliana Rivera", b="Bartholomew Lee"))
    x0, _, x1, _ = plan["captions"][0]["bbox"]
    assert x1 - x0 <= 0.86 * plan["canvas_size"] + 1


def test_arc_is_broken_where_it_meets_ink(plan):
    assert plan["motif"]["type"] == "open-arc"
    assert len(plan["motif"]["segments"]) >= 2


def test_arc_passes_the_independent_overlap_check(plan):
    assert check_motif_glyph_overlap(plan) == []


def test_overlap_check_catches_an_arc_forced_through_a_glyph(plan):
    a = plan["glyphs"][0]
    # Find a point actually inside the first initial's outline and route the arc through it.
    from wedding_visual.qa.checks import _point_in_path

    x0, y0, x1, y1 = a["bbox"]
    inside = next(
        (x, y)
        for x in range(int(x0), int(x1))
        for y in range(int(y0), int(y1))
        if _point_in_path(a["d"], x + 0.5, y + 0.5)
    )
    bad = dict(plan, motif=dict(plan["motif"], segments=[[(inside[0] + 0.5, inside[1] + 0.5)] * 2]))
    findings = check_motif_glyph_overlap(bad)
    assert findings and findings[0]["code"] == "motif-overlap"


def test_svg_is_well_formed_and_deterministic():
    a = render_monogram_svg(_spec())
    assert a == render_monogram_svg(_spec())
    root = ET.fromstring(a)
    # 3 monogram glyphs + 2 caption lines + 1 arc path
    assert len(root.findall(f"{SVG_NS}path")) == 6


def test_eval_set_has_no_fail_on_v2():
    results = run_eval_set(template_id="monogram-v2")
    assert all(r["passed"] for r in results), [r for r in results if not r["passed"]]
