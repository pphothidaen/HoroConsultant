"""
Zi Wei Dou Shu (紫微斗數) Core Calculation Engine
==================================================
Deterministic calculation of Chinese Zi Wei Dou Shu birth charts:
- 12 Palaces (十二宮) & Earthly Branch mapping
- Ming Gong (命宮) & Shen Gong (身宮) calculation
- Five Element Bureau (五行局: 水二局, 木三局, 金四局, 土五局, 火六局)
- 14 Primary Stars (十四主星: 紫微, 天機, 太陽, 武曲, 天同, 廉貞, 天府, 太陰, 貪狼, 巨門, 天相, 天梁, 七殺, 破軍)
- Assistant Stars (六吉星, 六煞星, 祿存, 天馬)
- Four Transformative Mutators (四化: 化祿, 化權, 化科, 化忌)
- Decade Luck Periods (大限步數) & Transits
"""

from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

PALACE_NAMES = [
    "命宮", "兄弟宮", "夫妻宮", "子女宮", "財帛宮", "疾厄宮",
    "遷移宮", "交友宮", "官祿宮", "田宅宮", "福德宮", "父母宮"
]

# Five Element Bureau names & numbers
FIVE_ELEMENT_BUREAUS = {
    "水二局": 2,
    "木三局": 3,
    "金四局": 4,
    "土五局": 5,
    "火六局": 6
}

# Si Hua Matrix based on Year Stem (四化星陣)
SI_HUA_MATRIX = {
    "甲": {"化祿": "廉貞", "化權": "破軍", "化科": "武曲", "化忌": "太陽"},
    "乙": {"化祿": "天機", "化權": "天梁", "化科": "紫微", "化忌": "太陰"},
    "丙": {"化祿": "天同", "化權": "天機", "化科": "文昌", "化忌": "廉貞"},
    "丁": {"化祿": "太陰", "化權": "天同", "化科": "天機", "化忌": "巨門"},
    "戊": {"化祿": "貪狼", "化權": "太陰", "化科": "右弼", "化忌": "天機"},
    "己": {"化祿": "武曲", "化權": "貪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化祿": "太陽", "化權": "武曲", "化科": "太陰", "化忌": "天同"},
    "辛": {"化祿": "巨門", "化權": "太陽", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化祿": "天梁", "化權": "紫微", "化科": "左輔", "化忌": "武曲"},
    "癸": {"化祿": "破軍", "化權": "巨門", "化科": "太陰", "化忌": "貪狼"},
}

# Lucun Star placement by Year Stem (祿存)
LUCUN_BRANCH_MAP = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子"
}

# Tian Ma placement by Year Branch (天馬: 寅午戌在申, 申子辰在寅, 巳酉丑在亥, 亥卯未在巳)
TIAN_MA_MAP = {
    "寅": "申", "午": "申", "戌": "申",
    "申": "寅", "子": "寅", "辰": "寅",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳"
}


class ZiWeiEngine(AbstractAstrologyEngine):
    """Core Zi Wei Dou Shu engine."""

    @property
    def engine_name(self) -> str:
        return "Zi Wei Dou Shu Engine"

    @property
    def system_type(self) -> str:
        return "ming_xue"

    @staticmethod
    def _get_year_stem_branch(year: int) -> tuple[str, str]:
        stem_idx = (year - 4) % 10
        branch_idx = (year - 4) % 12
        return STEMS[stem_idx], BRANCHES[branch_idx]

    @staticmethod
    def _get_hour_branch(hour: int) -> str:
        idx = ((hour + 1) // 2) % 12
        return BRANCHES[idx]

    @staticmethod
    def calculate_ming_shen_gong(lunar_month: int, hour_branch: str) -> tuple[str, str, int, int]:
        """
        Calculate Ming Gong (命宮) and Shen Gong (身宮) branch & index.
        Ming Gong = Starts at Yin (idx 2), moves clockwise by (lunar_month - 1), counter-clockwise by hour_branch_idx.
        Shen Gong = Starts at Yin (idx 2), moves clockwise by (lunar_month - 1), clockwise by hour_branch_idx.
        """
        hour_idx = BRANCHES.index(hour_branch)
        ming_idx = (2 + (lunar_month - 1) - hour_idx) % 12
        shen_idx = (2 + (lunar_month - 1) + hour_idx) % 12
        return BRANCHES[ming_idx], BRANCHES[shen_idx], ming_idx, shen_idx

    @staticmethod
    def calculate_five_element_bureau(year_stem: str, ming_branch: str) -> str:
        """
        Determine Five Element Bureau (五行局) based on Year Stem & Ming Gong Branch.
        Uses Five Tiger Chase (五虎遁) stem on Ming Gong branch, then Na Yin element.
        """
        tiger_stems = {
            "甲": "丙", "己": "丙", "乙": "戊", "庚": "戊",
            "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬",
            "戊": "甲", "癸": "甲"
        }
        start_stem = tiger_stems.get(year_stem, "丙")
        start_stem_idx = STEMS.index(start_stem)
        
        ming_branch_idx = BRANCHES.index(ming_branch)
        offset_from_yin = (ming_branch_idx - 2) % 12
        ming_stem = STEMS[(start_stem_idx + offset_from_yin) % 10]

        pair = f"{ming_stem}{ming_branch}"
        water_bureau = ["甲寅", "乙卯", "壬戌", "癸亥", "丙午", "丁未", "甲申", "乙酉", "壬辰", "癸巳"]
        wood_bureau = ["戊辰", "己巳", "壬午", "癸未", "庚寅", "辛卯", "戊戌", "己亥", "壬子", "癸丑"]
        metal_bureau = ["甲子", "乙丑", "壬申", "癸酉", "庚辰", "辛巳", "甲午", "乙未", "壬寅", "癸卯"]
        earth_bureau = ["丙辰", "丁巳", "庚午", "辛未", "戊申", "己酉", "丙戌", "丁亥", "庚子", "辛丑"]
        
        if pair in water_bureau:
            return "水二局"
        elif pair in wood_bureau:
            return "木三局"
        elif pair in metal_bureau:
            return "金四局"
        elif pair in earth_bureau:
            return "土五局"
        else:
            return "火六局"

    @staticmethod
    def calculate_zi_wei_star_branch(bureau_number: int, lunar_day: int) -> str:
        """Calculate Zi Wei Star branch position based on Bureau Number and Lunar Day."""
        quotient = lunar_day // bureau_number
        remainder = lunar_day % bureau_number
        if remainder != 0:
            add_count = bureau_number - remainder
            total = lunar_day + add_count
            quotient = total // bureau_number
            if add_count % 2 == 1:
                branch_idx = (2 + quotient - 1 - add_count) % 12
            else:
                branch_idx = (2 + quotient - 1 + add_count) % 12
        else:
            branch_idx = (2 + quotient - 1) % 12
        return BRANCHES[branch_idx]

    def calculate_assistant_stars(
        self,
        year_stem: str,
        year_branch: str,
        lunar_month: int,
        hour_branch: str
    ) -> dict[str, list[str]]:
        """
        Calculate key assistant stars (六吉星, 六煞星, 祿存, 天馬) across branches.
        """
        hour_idx = BRANCHES.index(hour_branch)
        branch_assistants: dict[str, list[str]] = {b: [] for b in BRANCHES}

        # 1. Zuo Fu / You Bi (左輔: 辰 + (month-1), 右弼: 戌 - (month-1))
        zuo_fu_branch = BRANCHES[(4 + (lunar_month - 1)) % 12]
        you_bi_branch = BRANCHES[(10 - (lunar_month - 1)) % 12]
        branch_assistants[zuo_fu_branch].append("左輔")
        branch_assistants[you_bi_branch].append("右弼")

        # 2. Wen Chang / Wen Qu (文昌: 戌 - hour_idx, 文曲: 辰 + hour_idx)
        wen_chang_branch = BRANCHES[(10 - hour_idx) % 12]
        wen_qu_branch = BRANCHES[(4 + hour_idx) % 12]
        branch_assistants[wen_chang_branch].append("文昌")
        branch_assistants[wen_qu_branch].append("文曲")

        # 3. Lucun & Qing Yang / Tuo Luo (祿存, 擎羊 is Lucun+1, 陀羅 is Lucun-1)
        lucun_branch = LUCUN_BRANCH_MAP.get(year_stem, "寅")
        lucun_idx = BRANCHES.index(lucun_branch)
        branch_assistants[lucun_branch].append("祿存")
        branch_assistants[BRANCHES[(lucun_idx + 1) % 12]].append("擎羊")
        branch_assistants[BRANCHES[(lucun_idx - 1) % 12]].append("陀羅")

        # 4. Tian Ma (天馬)
        tian_ma_branch = TIAN_MA_MAP.get(year_branch, "申")
        branch_assistants[tian_ma_branch].append("天馬")

        return branch_assistants

    def calculate_chart(self, year: int, month: int, day: int, hour: int, gender: str = "male") -> dict[str, Any]:
        """
        Calculate complete Zi Wei Dou Shu Chart.
        """
        year_stem, year_branch = self._get_year_stem_branch(year)
        hour_branch = self._get_hour_branch(hour)
        
        lunar_month = max(1, min(12, month))
        lunar_day = max(1, min(30, day))
        
        ming_branch, shen_branch, ming_idx, shen_idx = self.calculate_ming_shen_gong(lunar_month, hour_branch)
        bureau_name = self.calculate_five_element_bureau(year_stem, ming_branch)
        bureau_num = FIVE_ELEMENT_BUREAUS[bureau_name]
        
        zi_wei_branch = self.calculate_zi_wei_star_branch(bureau_num, lunar_day)
        zi_wei_idx = BRANCHES.index(zi_wei_branch)
        tian_fu_branch = BRANCHES[(4 + 12 - (zi_wei_idx % 12)) % 12]

        from project.core.fast_math import fast_ziwei_stars
        branch_stars_map = dict(fast_ziwei_stars(zi_wei_idx))

        si_hua = SI_HUA_MATRIX.get(year_stem, {})
        assistant_map = self.calculate_assistant_stars(year_stem, year_branch, lunar_month, hour_branch)

        # Decade Luck Direction:
        # Yang Male / Yin Female -> Clockwise (+1)
        # Yin Male / Yang Female -> Counter-Clockwise (-1)
        is_male = gender.lower() in ("male", "m")
        is_yang_year = (STEMS.index(year_stem) % 2 == 0)
        is_forward = (is_male and is_yang_year) or (not is_male and not is_yang_year)

        # Construct 12 Palaces list
        palaces = []
        for i, palace_name in enumerate(PALACE_NAMES):
            palace_branch_idx = (ming_idx - i) % 12
            branch_name = BRANCHES[palace_branch_idx]
            
            # Primary stars in this palace
            stars_in_palace = list(branch_stars_map.get(palace_branch_idx, []))
            assistants_in_palace = assistant_map.get(branch_name, [])
            
            # Check if any star has Si Hua mutator
            mutators = []
            for mutator_type, star in si_hua.items():
                if star in stars_in_palace:
                    mutators.append(f"{star}{mutator_type}")

            # Decade Luck (大限) start age
            decay_step = i if is_forward else (12 - i) % 12
            decade_start = bureau_num + (decay_step * 10)
            decade_end = decade_start + 9
            decade_luck_label = f"{decade_start}-{decade_end} 歲"

            palaces.append({
                "palace_name": palace_name,
                "earth_branch": branch_name,
                "stars": stars_in_palace,
                "primary_stars": stars_in_palace,
                "assistant_stars": assistants_in_palace,
                "mutators": mutators,
                "decade_luck": decade_luck_label,
                "is_ming_gong": (branch_name == ming_branch),
                "is_shen_gong": (branch_name == shen_branch)
            })

        raw = {
            "engine": "ZiWeiEngine",
            "birth_solar": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "year_stem_branch": f"{year_stem}{year_branch}",
            "hour_branch": hour_branch,
            "ming_gong_branch": ming_branch,
            "shen_gong_branch": shen_branch,
            "five_element_bureau": bureau_name,
            "zi_wei_star_branch": zi_wei_branch,
            "tian_fu_star_branch": tian_fu_branch,
            "si_hua": si_hua,
            "gender": gender,
            "is_forward_decade": is_forward,
            "palaces": palaces
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.calculate_chart(*args, **kwargs)


if __name__ == "__main__":
    engine = ZiWeiEngine()
    chart = engine.calculate_chart(1990, 5, 15, 14, "male")
    print(chart)
