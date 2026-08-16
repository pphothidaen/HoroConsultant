"""
test_bazi_replication.py — Fengshuix.com BaZi Chart Replication Tests
=====================================================================
Validates 100% field accuracy for the reference test case:
  ป๋อง กพล (Male, 1985-08-26 23:03, Ratchaburi 99.91°E, UTC+7, Ravi formula)
as specified in implementation_plan.md.
"""

from __future__ import annotations

from datetime import datetime
import pytest

from project.core.bazi_engine import BaZiEngine, ten_god, pillar_phase
from project.core.bazi_display import generate_bazi_html


class TestBaziFengshuixReplication:
    """Validate full replication of reference test case against fengshuix.com ground truth."""

    @pytest.fixture(scope="class")
    def engine(self) -> BaZiEngine:
        return BaZiEngine()

    @pytest.fixture(scope="class")
    def reference_chart(self, engine: BaZiEngine) -> dict:
        result = engine.calculate(
            dt=datetime(1985, 8, 26, 23, 3, 0),
            longitude=99.91,
            utc_offset_hours=7.0,
            gender="male",
            name="ป๋อง",
            surname="กพล",
            dayun_formula="ravi",
        )
        return result.chart_data

    # -----------------------------------------------------------------------
    # 1. Four Pillars Validation
    # -----------------------------------------------------------------------
    def test_four_pillars_exact_characters(self, reference_chart: dict):
        pillars = reference_chart["pillars"]
        
        # Hour pillar: 辛亥
        assert pillars["hour"]["stem"]["char"] == "辛"
        assert pillars["hour"]["branch"]["char"] == "亥"
        assert pillars["hour"]["ten_god"] == "IW"
        assert pillars["hour"]["branch"]["animal"] == "Pig"
        
        # Day pillar: 丁酉
        assert pillars["day"]["stem"]["char"] == "丁"
        assert pillars["day"]["branch"]["char"] == "酉"
        assert pillars["day"]["ten_god"] == "DM"
        assert pillars["day"]["branch"]["animal"] == "Rooster"
        
        # Month pillar: 甲申
        assert pillars["month"]["stem"]["char"] == "甲"
        assert pillars["month"]["branch"]["char"] == "申"
        assert pillars["month"]["ten_god"] == "DR"
        assert pillars["month"]["branch"]["animal"] == "Monkey"
        
        # Year pillar: 乙丑
        assert pillars["year"]["stem"]["char"] == "乙"
        assert pillars["year"]["branch"]["char"] == "丑"
        assert pillars["year"]["ten_god"] == "IR"
        assert pillars["year"]["branch"]["animal"] == "Ox"

    def test_hidden_stems_and_ten_gods(self, reference_chart: dict):
        pillars = reference_chart["pillars"]
        
        # Hour hidden stems: 壬 (DO), 甲 (DR)
        hour_hs = {h["stem"]: h["ten_god"] for h in pillars["hour"]["hidden_stems"]}
        assert "壬" in hour_hs and hour_hs["壬"] == "DO"
        assert "甲" in hour_hs and hour_hs["甲"] == "DR"
        
        # Month hidden stems: 庚 (DW), 壬 (DO), 戊 (HO)
        month_hs = {h["stem"]: h["ten_god"] for h in pillars["month"]["hidden_stems"]}
        assert "庚" in month_hs and month_hs["庚"] == "DW"
        assert "壬" in month_hs and month_hs["壬"] == "DO"
        assert "戊" in month_hs and month_hs["戊"] == "HO"
        
        # Year hidden stems: 己 (EG), 癸 (7K), 辛 (IW)
        year_hs = {h["stem"]: h["ten_god"] for h in pillars["year"]["hidden_stems"]}
        assert "己" in year_hs and year_hs["己"] == "EG"
        assert "癸" in year_hs and year_hs["癸"] == "7K"
        assert "辛" in year_hs and year_hs["辛"] == "IW"

    # -----------------------------------------------------------------------
    # 2. Ming Gua Validation
    # -----------------------------------------------------------------------
    def test_ming_gua(self, reference_chart: dict):
        mg = reference_chart["ming_gua"]
        assert mg["kua_number"] == 6
        assert mg["trigram_zh"] == "乾"
        assert mg["trigram_name"] == "Qian"
        assert mg["direction"] == "NORTHWEST"
        assert mg["element"] == "Metal"

    # -----------------------------------------------------------------------
    # 3. Day Master & Favorable / Unfavorable Elements
    # -----------------------------------------------------------------------
    def test_day_master_strength_and_favorable(self, reference_chart: dict):
        dm = reference_chart["day_master"]
        assert dm["stem"] == "丁"
        assert dm["element"] == "Fire"
        assert dm["polarity"] == "Yin"
        assert reference_chart["day_master_strength"] == "WEAK"
        
        fav = reference_chart["favorable_elements"]
        assert fav["favorable"] == ["Wood", "Water", "Fire"]
        assert fav["unfavorable"] == ["Metal", "Earth"]

    # -----------------------------------------------------------------------
    # 4. 10 Profiles Proportions Validation
    # -----------------------------------------------------------------------
    def test_ten_profiles_proportions(self, reference_chart: dict):
        tp = reference_chart["ten_profiles"]
        assert tp["IW"]["percentage"] == pytest.approx(23.33, abs=0.5)
        assert tp["DO"]["percentage"] == pytest.approx(14.44, abs=0.5)
        assert tp["DR"]["percentage"] == pytest.approx(14.44, abs=0.5)
        assert tp["FR"]["percentage"] == pytest.approx(13.33, abs=0.5)
        assert tp["DW"]["percentage"] == pytest.approx(13.33, abs=0.5)
        assert tp["IR"]["percentage"] == pytest.approx(11.11, abs=0.5)
        assert tp["EG"]["percentage"] == pytest.approx(11.11, abs=0.5)
        assert tp["7K"]["percentage"] == pytest.approx(6.67, abs=0.5)
        assert tp["HO"]["percentage"] == pytest.approx(2.22, abs=0.5)
        assert tp["RW"]["percentage"] == pytest.approx(0.00, abs=0.1)

    # -----------------------------------------------------------------------
    # 5. 5 Structures Proportions Validation
    # -----------------------------------------------------------------------
    def test_five_structures_proportions(self, reference_chart: dict):
        structs = reference_chart["five_structures"]
        assert structs["Wealth"]["percentage"] == pytest.approx(36.67, abs=1.0)
        assert structs["Resource"]["percentage"] == pytest.approx(25.56, abs=1.0)
        assert structs["Influence"]["percentage"] == pytest.approx(21.11, abs=1.0)
        assert structs["Companion"]["percentage"] == pytest.approx(13.33, abs=1.0)
        assert structs["Output"]["percentage"] == pytest.approx(13.33, abs=1.0)

    # -----------------------------------------------------------------------
    # 6. Da Yun Cycles Validation
    # -----------------------------------------------------------------------
    def test_dayun_cycles(self, reference_chart: dict):
        dayun = reference_chart["dayun"]
        assert dayun["direction"] == "backward"
        assert dayun["start_age_years"] == 6
        
        cycles = dayun["cycles"]
        assert len(cycles) >= 10
        
        # Cycle 1: 癸未 (6-15, 1991-2000)
        assert cycles[0]["stem"] == "癸"
        assert cycles[0]["branch"] == "未"
        assert cycles[0]["age_start"] == 6
        assert cycles[0]["year_start"] == 1991
        assert cycles[0]["ten_god_stem"] == "7K"
        assert cycles[0]["pillar_phase"]["phase"] == "Guan Dai"
        
        # Cycle 2: 壬午 (16-25, 2001-2010)
        assert cycles[1]["stem"] == "壬"
        assert cycles[1]["branch"] == "午"
        assert cycles[1]["age_start"] == 16
        assert cycles[1]["year_start"] == 2001
        assert cycles[1]["ten_god_stem"] == "DO"
        assert cycles[1]["pillar_phase"]["phase"] == "Lin Guan"
        
        # Cycle 3: 辛巳 (26-35, 2011-2020)
        assert cycles[2]["stem"] == "辛"
        assert cycles[2]["branch"] == "巳"
        assert cycles[2]["age_start"] == 26
        assert cycles[2]["year_start"] == 2011
        assert cycles[2]["ten_god_stem"] == "IW"
        assert cycles[2]["pillar_phase"]["phase"] == "Di Wang"

        # Pre Da Yun
        pre = dayun["pre_cycle"]
        assert pre["cycle_num"] == 0
        assert pre["age_start"] == 0
        assert pre["age_end"] == 5
        assert pre["year_start"] == 1985
        assert pre["year_end"] == 1990

    # -----------------------------------------------------------------------
    # 7. Symbolic & General Stars
    # -----------------------------------------------------------------------
    def test_stars_matrices(self, reference_chart: dict):
        sym = reference_chart["symbolic_stars"]
        assert "Nobleman" in sym
        assert "亥" in sym["Nobleman"]["branches"] or "酉" in sym["Nobleman"]["branches"]
        assert "Intelligence" in sym
        assert "Kong Wang" in sym
        
        gen = reference_chart["general_stars"]
        assert "Travelling Horse" in gen
        assert "General" in gen
        assert "Talent" in gen

    # -----------------------------------------------------------------------
    # 8. HTML Display Generator Verification
    # -----------------------------------------------------------------------
    def test_generate_bazi_html(self, reference_chart: dict):
        html_content = generate_bazi_html(reference_chart)
        
        assert "<!DOCTYPE html>" in html_content
        assert "BAZI.FENGSHUIX" in html_content
        assert "ระบบสมผุสท้องถิ่น" in html_content
        assert "Bazi Chart" in html_content
        assert "四柱八字" in html_content
        assert "ป๋อง กพล" in html_content
        assert "5 Structures" in html_content
        assert "10 Profiles Proportions" in html_content
        assert "Symbolic Stars" in html_content
        assert "General Stars" in html_content
        assert "Da Yun" in html_content
        assert "Pre Da Yun" in html_content
        assert "癸未" in html_content or ("癸" in html_content and "未" in html_content)
        assert len(html_content) > 5000
