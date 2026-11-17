import pytest

from wedding_visual.qa.color import contrast_ratio, parse_hex_color, relative_luminance


def test_parse_hex_color_long_and_short_form():
    assert parse_hex_color("#ff0000") == (255, 0, 0)
    assert parse_hex_color("#f00") == (255, 0, 0)
    assert parse_hex_color("000000") == (0, 0, 0)


def test_parse_hex_color_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_hex_color("#ff00")


def test_relative_luminance_black_and_white():
    assert relative_luminance("#000000") == pytest.approx(0.0, abs=1e-9)
    assert relative_luminance("#ffffff") == pytest.approx(1.0, abs=1e-9)


def test_contrast_ratio_black_on_white_is_21_to_1():
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.01)


def test_contrast_ratio_is_symmetric():
    assert contrast_ratio("#1a1a1a", "#f2f1ec") == pytest.approx(contrast_ratio("#f2f1ec", "#1a1a1a"))


def test_contrast_ratio_same_color_is_one():
    assert contrast_ratio("#3d6fa5", "#3d6fa5") == pytest.approx(1.0, abs=1e-9)
