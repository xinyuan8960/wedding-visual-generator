import pytest

from wedding_visual.layout.glyphs import Font, GlyphNotFoundError
from wedding_visual.layout.monogram import (
    InitialsError,
    compose_monogram,
    initial_of,
)

CANVAS = 512.0


@pytest.fixture(scope="module")
def font():
    return Font()


def test_initial_of_picks_first_alpha_char_uppercased():
    assert initial_of("Alex Rivera") == "A"
    assert initial_of("jordan Lee") == "J"
    assert initial_of("  Émile") == "É"


def test_initial_of_rejects_names_without_letters():
    with pytest.raises(InitialsError):
        initial_of("123")


def test_unknown_arrangement_is_rejected(font):
    with pytest.raises(ValueError):
        compose_monogram("A", "J", "diagonal", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)


@pytest.mark.parametrize("arrangement", ["side-by-side", "stacked", "interlocking", "circular-badge"])
def test_result_shape(font, arrangement):
    result = compose_monogram("A", "J", arrangement, whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    assert result["canvas_size"] == CANVAS
    assert result["arrangement"] == arrangement
    assert {g["char"] for g in result["glyphs"]} == {"A", "J"}
    for g in result["glyphs"]:
        assert g["d"]  # non-empty SVG path data
        x0, y0, x1, y1 = g["bbox"]
        assert x0 < x1 and y0 < y1


@pytest.mark.parametrize("arrangement", ["side-by-side", "stacked", "interlocking", "circular-badge"])
def test_glyphs_stay_within_canvas(font, arrangement):
    result = compose_monogram("A", "J", arrangement, whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    for g in result["glyphs"]:
        x0, y0, x1, y1 = g["bbox"]
        assert -0.5 <= x0 and x1 <= CANVAS + 0.5
        assert -0.5 <= y0 and y1 <= CANVAS + 0.5


def test_side_by_side_does_not_overlap(font):
    result = compose_monogram("A", "J", "side-by-side", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    by_char = {g["char"]: g["bbox"] for g in result["glyphs"]}
    assert by_char["A"][2] <= by_char["J"][0]  # A's right edge left of J's left edge


def test_interlocking_overlaps(font):
    result = compose_monogram("A", "J", "interlocking", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    by_char = {g["char"]: g["bbox"] for g in result["glyphs"]}
    assert by_char["A"][2] > by_char["J"][0]  # A's right edge intrudes into J's box


def test_stacked_places_a_above_b_and_centers_each_horizontally(font):
    result = compose_monogram("A", "J", "stacked", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    by_char = {g["char"]: g["bbox"] for g in result["glyphs"]}
    assert by_char["A"][3] <= by_char["J"][1]  # A's bottom above J's top
    a_center_x = (by_char["A"][0] + by_char["A"][2]) / 2
    j_center_x = (by_char["J"][0] + by_char["J"][2]) / 2
    assert a_center_x == pytest.approx(CANVAS / 2, abs=0.1)
    assert j_center_x == pytest.approx(CANVAS / 2, abs=0.1)


def test_circular_badge_is_not_larger_than_side_by_side(font):
    side = compose_monogram("A", "J", "side-by-side", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    circ = compose_monogram("A", "J", "circular-badge", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)

    def union_width(result):
        xs = [x for g in result["glyphs"] for x in (g["bbox"][0], g["bbox"][2])]
        return max(xs) - min(xs)

    assert union_width(circ) <= union_width(side) + 0.1


def test_deterministic_same_inputs_same_output(font):
    a = compose_monogram("A", "J", "side-by-side", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    b = compose_monogram("A", "J", "side-by-side", whitespace_ratio=0.2, canvas_size=CANVAS, font=font)
    assert a == b


def test_more_whitespace_shrinks_the_result(font):
    tight = compose_monogram("A", "J", "side-by-side", whitespace_ratio=0.05, canvas_size=CANVAS, font=font)
    loose = compose_monogram("A", "J", "side-by-side", whitespace_ratio=0.5, canvas_size=CANVAS, font=font)

    def union_area(result):
        xs = [x for g in result["glyphs"] for x in (g["bbox"][0], g["bbox"][2])]
        ys = [y for g in result["glyphs"] for y in (g["bbox"][1], g["bbox"][3])]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    assert union_area(loose) < union_area(tight)


def test_missing_glyph_raises(font):
    with pytest.raises(GlyphNotFoundError):
        font.bounds("")  # Private Use Area: no font maps this
