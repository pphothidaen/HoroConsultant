"""
Unit Tests for Date Selection (擇吉學 & 建除十二神) Core Calculation Engine
========================================================================
Deterministic verification of:
- Twelve Duty Officers (建除十二神: 建, 除, 滿, 平, 定, 執, 破, 危, 成, 收, 開, 閉)
- Year Breaker (歲破) & Month Breaker (月破) clash detection across all 12 Earthly Branches
- User personal zodiac clash detection (生肖相衝)
- Activity suitability ratings (Marriage, Business, Moving, Travel, Medical)
- 1-to-5 star rating hierarchy and deterministic status mappings
- EngineChartResult contract invariants, dictionary indexing, and JSON serialization
"""

import json
import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.ze_ji_engine import (
    BRANCHES,
    BRANCH_CLASH,
    DUTY_OFFICERS,
    OFFICER_DESCRIPTIONS,
    ZeJiEngine,
)


class TestZeJiEngineMetadata:
    """Verify engine metadata, protocol conformity, and data dictionary completeness."""

    def test_engine_identity(self):
        engine = ZeJiEngine()
        assert isinstance(engine, AbstractAstrologyEngine)
        assert engine.engine_name == "Imperial Calendar Date Selection Engine"
        assert engine.system_type == "ze_ji"

    def test_constants_completeness(self):
        assert len(BRANCHES) == 12
        assert len(DUTY_OFFICERS) == 12
        assert len(OFFICER_DESCRIPTIONS) == 12
        assert len(BRANCH_CLASH) == 12


class TestZeJi12DutyOfficers:
    """Verify 12 Duty Officers cyclical progression starting from Month Branch."""

    @pytest.mark.parametrize("offset,expected_officer", [
        (0, "建日"), (1, "除日"), (2, "滿日"), (3, "平日"),
        (4, "定日"), (5, "執日"), (6, "破日"), (7, "危日"),
        (8, "成日"), (9, "收日"), (10, "開日"), (11, "閉日"),
    ])
    def test_duty_officers_from_month_zi(self, offset, expected_officer):
        engine = ZeJiEngine()
        day_branch = BRANCHES[offset]
        officer = engine.calculate_duty_officer(month_branch="子", day_branch=day_branch)
        assert officer == expected_officer

    @pytest.mark.parametrize("month_branch,day_branch,expected_officer", [
        ("寅", "寅", "建日"),
        ("寅", "卯", "除日"),
        ("寅", "辰", "滿日"),
        ("寅", "申", "破日"),
        ("寅", "戌", "成日"),
        ("午", "午", "建日"),
        ("午", "子", "破日"),
        ("酉", "酉", "建日"),
        ("酉", "卯", "破日"),
        ("亥", "亥", "建日"),
        ("亥", "巳", "破日"),
    ])
    def test_duty_officers_various_months(self, month_branch, day_branch, expected_officer):
        engine = ZeJiEngine()
        officer = engine.calculate_duty_officer(month_branch, day_branch)
        assert officer == expected_officer

    def test_all_144_month_day_combinations_valid(self):
        engine = ZeJiEngine()
        for m_idx, m_branch in enumerate(BRANCHES):
            for d_idx, d_branch in enumerate(BRANCHES):
                officer = engine.calculate_duty_officer(m_branch, d_branch)
                expected_offset = (d_idx - m_idx) % 12
                assert officer == DUTY_OFFICERS[expected_offset]
                assert officer in OFFICER_DESCRIPTIONS


class TestZeJiClashDetection:
    """Verify Year Breaker (歲破), Month Breaker (月破), and Personal Clash."""

    @pytest.mark.parametrize("branch1,branch2", [
        ("子", "午"), ("丑", "未"), ("寅", "申"),
        ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
    ])
    def test_six_clashes_bidirectional(self, branch1, branch2):
        assert BRANCH_CLASH[branch1] == branch2
        assert BRANCH_CLASH[branch2] == branch1

    def test_year_breaker_detection(self):
        engine = ZeJiEngine()
        # Year: 子, Month: 寅, Day: 午 -> Day clashes with Year (Year Breaker / 歲破)
        res = engine.check_suitability(year_branch="子", month_branch="寅", day_branch="午")
        assert res["is_year_breaker"] is True
        assert res["is_month_breaker"] is False
        assert res["rating_stars"] == 1
        assert "歲破" in res["overall_status"]

    def test_month_breaker_detection(self):
        engine = ZeJiEngine()
        # Year: 寅, Month: 子, Day: 午 -> Day clashes with Month (Month Breaker / 月破)
        res = engine.check_suitability(year_branch="寅", month_branch="子", day_branch="午")
        assert res["is_month_breaker"] is True
        assert res["duty_officer"] == "破日"
        assert res["rating_stars"] == 1
        assert "月破" in res["overall_status"]

    def test_user_personal_clash_detection(self):
        engine = ZeJiEngine()
        # User birth branch: 午, Day: 子 (User clash)
        # Year: 辰, Month: 申, Day: 子 (Day is 滿日, not breaker)
        res = engine.check_suitability(
            year_branch="辰",
            month_branch="申",
            day_branch="子",
            user_birth_branch="午"
        )
        assert res["is_user_clash"] is True
        assert res["is_year_breaker"] is False
        assert res["is_month_breaker"] is False
        assert res["rating_stars"] == 2
        assert "衝剋個人生肖" in res["overall_status"]

    def test_no_clash_auspicious_day(self):
        engine = ZeJiEngine()
        # Year: 子, Month: 寅, Day: 戌 -> Day 戌 is 成日 of Month 寅 (offset 8)
        res = engine.check_suitability(
            year_branch="子",
            month_branch="寅",
            day_branch="戌",
            user_birth_branch="寅"
        )
        assert res["is_year_breaker"] is False
        assert res["is_month_breaker"] is False
        assert res["is_user_clash"] is False
        assert res["duty_officer"] == "成日"
        assert res["rating_stars"] == 5
        assert "百事大吉" in res["overall_status"]


class TestZeJiActivitySuitabilityAndRatings:
    """Verify ratings hierarchy and activity suitability matrix."""

    def test_auspicious_5_star_activities(self):
        engine = ZeJiEngine()
        # Month 寅, Day 戌 -> 成日
        res = engine.check_suitability(year_branch="子", month_branch="寅", day_branch="戌")
        assert res["rating_stars"] == 5
        activities = res["activities_suitability"]
        assert activities["結婚訂婚"] == "宜"
        assert activities["開市開業"] == "宜"
        assert activities["搬家入宅"] == "宜"
        assert activities["出行遠遊"] == "宜"

    def test_medical_day_chu_ri(self):
        engine = ZeJiEngine()
        # Month 寅, Day 卯 -> 除日 (Rating 4)
        res = engine.check_suitability(year_branch="子", month_branch="寅", day_branch="卯")
        assert res["rating_stars"] == 4
        assert res["duty_officer"] == "除日"
        assert res["activities_suitability"]["求醫治病"] == "宜"

    def test_year_breaker_blocks_major_activities(self):
        engine = ZeJiEngine()
        # Year 午, Month 辰, Day 子 -> Day clashes with Year (Year Breaker)
        res = engine.check_suitability(year_branch="午", month_branch="辰", day_branch="子")
        assert res["is_year_breaker"] is True
        activities = res["activities_suitability"]
        assert activities["結婚訂婚"] == "忌"
        assert activities["開市開業"] == "忌"
        assert activities["搬家入宅"] == "忌"


class TestZeJiEngineChartResultInvariants:
    """Verify EngineChartResult contract invariants and serialization."""

    def test_check_suitability_payload_structure(self):
        engine = ZeJiEngine()
        res = engine.check_suitability("午", "申", "寅", "子")

        assert isinstance(res, EngineChartResult)
        assert isinstance(res, dict)
        assert res.engine_name == "Imperial Calendar Date Selection Engine"
        assert res.system_type == "ze_ji"
        assert res["engine"] == "ZeJiEngine"
        assert "duty_officer" in res
        assert "duty_description" in res
        assert "rating_stars" in res
        assert 1 <= res["rating_stars"] <= 5
        assert "overall_status" in res
        assert "is_year_breaker" in res
        assert "is_month_breaker" in res
        assert "is_user_clash" in res
        assert "activities_suitability" in res

        for act in ["結婚訂婚", "開市開業", "搬家入宅", "出行遠遊", "求醫治病"]:
            assert act in res["activities_suitability"]
            assert res["activities_suitability"][act] in ("宜", "忌", "平")

    def test_generic_calculate_interface(self):
        engine = ZeJiEngine()
        res1 = engine.calculate("午", "申", "寅", "子")
        res2 = engine.check_suitability("午", "申", "寅", "子")
        assert res1["duty_officer"] == res2["duty_officer"]
        assert res1["rating_stars"] == res2["rating_stars"]

    def test_json_serialization(self):
        engine = ZeJiEngine()
        res = engine.check_suitability("巳", "酉", "丑", "亥")
        serialized = json.dumps(res)
        deserialized = json.loads(serialized)

        assert deserialized["engine_name"] == "Imperial Calendar Date Selection Engine"
        assert deserialized["system_type"] == "ze_ji"
        assert "calculation_timestamp" in deserialized
        assert deserialized["rating_stars"] == 4

    def test_to_dict_method(self):
        engine = ZeJiEngine()
        res = engine.check_suitability("子", "丑", "寅")
        d = res.to_dict()
        assert isinstance(d, dict)
        assert d["engine"] == "ZeJiEngine"
        assert "duty_officer" in d
