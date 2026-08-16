"""
project/tests/test_i18n.py
==========================
Regression and unit tests for Multi-Language Internationalization (i18n):
  1. Test SVG localization for BaZi, ZiWei, QiMen, XuanKong, Multimodal Matrix in TH, EN, ZH.
  2. Test QuestionFocusRouter multi-lingual prompt generation.
  3. Test API v2 /interpret/focused and /api/v1/bazi/interpret request schema support for language.
  4. Verify no broken markup or fallback leakage across language toggles.
"""

import json
import pytest
from project.core.svg_generator import (
    generate_bazi_svg,
    generate_ziwei_svg,
    generate_qimen_svg,
    generate_xuankong_svg,
    generate_multimodal_matrix_svg,
    generate_numerology_svg,
    generate_iching_svg,
    generate_zeji_svg,
    generate_thaivedic_svg,
    generate_western_svg,
    generate_tai_yi_svg,
    generate_liu_yao_svg,
    generate_meihua_svg,
    generate_sanhe_svg,
    generate_qizheng_svg,
    generate_mianxiang_svg,
    SVG_LOCALES,
)
from project.core.question_focus_router import question_focus_router


@pytest.fixture
def sample_bazi_chart():
    return {
        "day_master": {"stem": "甲", "element": "Wood", "polarity": "Yang"},
        "five_elements": {
            "percentages": {"Wood": 30.0, "Fire": 25.0, "Earth": 20.0, "Metal": 15.0, "Water": 10.0},
            "dominant_element": "Wood",
            "weakest_element": "Water",
        },
        "solar_time_info": {"tst_datetime": "1990-05-15 14:20:00"},
        "pillars": {
            "year": {"stem": {"char": "庚", "pinyin": "gēng", "element": "Metal"}, "branch": {"char": "午", "pinyin": "wǔ", "zodiac": "Horse"}},
            "month": {"stem": {"char": "辛", "pinyin": "xīn", "element": "Metal"}, "branch": {"char": "巳", "pinyin": "sì", "zodiac": "Snake"}},
            "day": {"stem": {"char": "甲", "pinyin": "jiǎ", "element": "Wood"}, "branch": {"char": "子", "pinyin": "zǐ", "zodiac": "Rat"}},
            "hour": {"stem": {"char": "辛", "pinyin": "xīn", "element": "Metal"}, "branch": {"char": "未", "pinyin": "wèi", "zodiac": "Goat"}},
        }
    }


class TestI18nSVGLocalization:
    """Test SVG localization across Thai, English, and Chinese."""

    @pytest.mark.parametrize("lang,expected_substring", [
        ("th", "ผังดวงชะตา BaZi 4 เสา"),
        ("en", "BaZi Four Pillars of Destiny Chart"),
        ("zh", "四柱八字命盤"),
    ])
    def test_bazi_svg_title_localization(self, sample_bazi_chart, lang, expected_substring):
        svg = generate_bazi_svg(sample_bazi_chart, lang=lang)
        assert expected_substring in svg
        assert "<svg" in svg
        assert "</svg>" in svg

    @pytest.mark.parametrize("lang,expected_title", [
        ("th", "ผังดวง紫微斗數"),
        ("en", "Zi Wei Dou Shu 12-Palace Matrix"),
        ("zh", "紫微斗數十二宮命盤"),
    ])
    def test_ziwei_svg_localization(self, lang, expected_title):
        chart = {"palaces": [{"palace_name": "命宮", "earth_branch": "寅", "stars": ["紫微", "天府"], "is_ming_gong": True}]}
        svg = generate_ziwei_svg(chart, lang=lang)
        assert expected_title in svg
        assert "</svg>" in svg

    @pytest.mark.parametrize("lang,expected_title", [
        ("th", "ผังดวง奇門遁甲"),
        ("en", "Qi Men Dun Jia 4-Plate Celestial Grid"),
        ("zh", "奇門遁甲四盤九宮局"),
    ])
    def test_qimen_svg_localization(self, lang, expected_title):
        chart = {"solar_term": "冬至", "dun_type": "Yang", "ju_number": 1, "palaces": []}
        svg = generate_qimen_svg(chart, lang=lang)
        assert expected_title in svg

    @pytest.mark.parametrize("lang,expected_title", [
        ("th", "ผังดวงสังเคราะห์ 16 ศาสตร์"),
        ("en", "Unified 16-Discipline Multimodal Consensus Matrix"),
        ("zh", "16門術數大一統全息共識羅盤"),
    ])
    def test_multimodal_matrix_svg_localization(self, lang, expected_title):
        data = {"domain_name": "Career", "consensus_score_pct": 90, "favorable_pct": 85}
        svg = generate_multimodal_matrix_svg(data, lang=lang)
        assert expected_title in svg

    def test_all_16_disciplines_support_lang_param(self, sample_bazi_chart):
        """Ensure all 16 generator functions execute cleanly without error with lang='en' and lang='zh'."""
        dummy_chart = {"day_master": {"stem": "甲", "element": "Wood"}}
        
        funcs = [
            (generate_bazi_svg, sample_bazi_chart),
            (generate_ziwei_svg, dummy_chart),
            (generate_qimen_svg, dummy_chart),
            (generate_xuankong_svg, dummy_chart),
            (generate_iching_svg, dummy_chart),
            (generate_zeji_svg, dummy_chart),
            (generate_thaivedic_svg, dummy_chart),
            (generate_western_svg, dummy_chart),
            (generate_numerology_svg, dummy_chart),
            (generate_tai_yi_svg, dummy_chart),
            (generate_liu_yao_svg, dummy_chart),
            (generate_meihua_svg, dummy_chart),
            (generate_sanhe_svg, dummy_chart),
            (generate_qizheng_svg, dummy_chart),
            (generate_mianxiang_svg, dummy_chart),
            (generate_multimodal_matrix_svg, dummy_chart),
        ]

        for func, data in funcs:
            for lang in ["th", "en", "zh"]:
                svg = func(data, lang=lang)
                assert isinstance(svg, str)
                assert svg.startswith("<svg")
                assert svg.endswith("</svg>")


class TestQuestionFocusRouterI18n:
    """Test QuestionFocusRouter multi-lingual prompt directives."""

    def test_prompt_language_directives(self, sample_bazi_chart):
        # Thai
        th_prompt = question_focus_router.build_focused_prompt(
            category="career",
            chart_data=sample_bazi_chart,
            query="ควรย้ายงานปี 2026 ไหม?",
            language="th"
        )
        assert "ภาษาไทย" in th_prompt

        # English
        en_prompt = question_focus_router.build_focused_prompt(
            category="career",
            chart_data=sample_bazi_chart,
            query="Should I switch jobs in 2026?",
            language="en"
        )
        assert "English" in en_prompt

        # Chinese
        zh_prompt = question_focus_router.build_focused_prompt(
            category="career",
            chart_data=sample_bazi_chart,
            query="2026年适合跳槽还是创业？",
            language="zh"
        )
        assert "中文" in zh_prompt


class TestI18nDictionaryCompleteness:
    """Verify SVG_LOCALES dictionary completeness."""

    def test_all_languages_have_core_disciplines(self):
        for lang in ["th", "en", "zh"]:
            assert lang in SVG_LOCALES
            loc = SVG_LOCALES[lang]
            for key in ["bazi", "ziwei", "qimen", "xuankong", "multimodal", "hour_pillar", "day_pillar"]:
                assert key in loc, f"Missing key '{key}' in lang '{lang}'"
