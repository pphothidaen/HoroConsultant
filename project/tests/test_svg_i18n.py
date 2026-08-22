"""Focused SVG-language contract tests referenced by the i18n plan."""

from project.core.svg_generator import generate_bazi_svg, generate_mianxiang_svg


def test_bazi_svg_has_localized_titles():
    chart = {"day_master": {"stem": "甲", "element": "Wood"}, "pillars": {}}
    expected = {
        "th": "ผังดวงชะตา BaZi 4 เสา",
        "en": "BaZi Four Pillars of Destiny Chart",
        "zh": "四柱八字命盤",
    }
    for language, title in expected.items():
        assert title in generate_bazi_svg(chart, lang=language)


def test_mian_xiang_svg_supports_all_supported_languages():
    chart = {"face_element": "Water (水形)", "twelve_palaces": {}, "five_officials": {}}
    for language in ("th", "en", "zh"):
        svg = generate_mianxiang_svg(chart, lang=language)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
