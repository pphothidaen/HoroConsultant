"""
Zi Wei Dou Shu (紫微斗數) Core Calculation Engine
==================================================
Deterministic calculation of Chinese Zi Wei Dou Shu birth charts:
- 12 Palaces (十二宮) & Branch mapping
- Ming Gong (命宮) & Shen Gong (身宮) calculation
- Five Element Bureau (五行局: 水二局, 木三局, 金四局, 土五局, 火六局)
- 14 Primary Stars (十四主星) placement
- Four Transformative Mutators (四化: 化祿, 化權, 化科, 化忌)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


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

# Si Hua Matrix based on Year Stem
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


class ZiWeiEngine:
    """Core Zi Wei Dou Shu engine."""

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
        # Yin branch is index 2
        ming_idx = (2 + (lunar_month - 1) - hour_idx) % 12
        shen_idx = (2 + (lunar_month - 1) + hour_idx) % 12
        return BRANCHES[ming_idx], BRANCHES[shen_idx], ming_idx, shen_idx

    @staticmethod
    def calculate_five_element_bureau(year_stem: str, ming_branch: str) -> str:
        """
        Determine Five Element Bureau (五行局) based on Year Stem & Ming Gong Branch.
        Uses Five Tiger Chase (五虎遁) stem on Ming Gong branch, then Na Yin element.
        """
        # Five tiger chase starting stem for Yin branch
        tiger_stems = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊",
                       "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬",
                       "戊": "甲", "癸": "甲"}
        start_stem = tiger_stems.get(year_stem, "丙")
        start_stem_idx = STEMS.index(start_stem)
        
        ming_branch_idx = BRANCHES.index(ming_branch)
        offset_from_yin = (ming_branch_idx - 2) % 12
        ming_stem = STEMS[(start_stem_idx + offset_from_yin) % 10]

        # Combination of ming_stem and ming_branch maps to Bureau
        pair = f"{ming_stem}{ming_branch}"
        # Standard Na Yin Bureau Mapping
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
                # Odd adjustment: step backward
                branch_idx = (2 + quotient - 1 - add_count) % 12
            else:
                # Even adjustment: step forward
                branch_idx = (2 + quotient - 1 + add_count) % 12
        else:
            branch_idx = (2 + quotient - 1) % 12
        return BRANCHES[branch_idx]

    def calculate_chart(self, year: int, month: int, day: int, hour: int, gender: str = "male") -> Dict[str, Any]:
        """
        Calculate complete Zi Wei Dou Shu Chart.
        """
        year_stem, year_branch = self._get_year_stem_branch(year)
        hour_branch = self._get_hour_branch(hour)
        
        # Approximate Lunar Month & Day if not provided as lunar
        lunar_month = max(1, min(12, month))
        lunar_day = max(1, min(30, day))
        
        ming_branch, shen_branch, ming_idx, shen_idx = self.calculate_ming_shen_gong(lunar_month, hour_branch)
        bureau_name = self.calculate_five_element_bureau(year_stem, ming_branch)
        bureau_num = FIVE_ELEMENT_BUREAUS[bureau_name]
        
        zi_wei_branch = self.calculate_zi_wei_star_branch(bureau_num, lunar_day)
        zi_wei_idx = BRANCHES.index(zi_wei_branch)
        
        # Tian Fu star position relative to Zi Wei star (symmetric placement across Chen-Xu axis)
        tian_fu_idx = (4 - zi_wei_idx) % 12
        tian_fu_branch = BRANCHES[tian_fu_idx]
        
        # Zi Wei Group Placement relative to Zi Wei Star:
        # Zi Wei (0), Tian Ji (-1), Tai Yang (-3), Wu Qu (-4), Tian Tong (-5), Lian Zhen (-8)
        zi_wei_stars = {
            "紫微": BRANCHES[zi_wei_idx],
            "天機": BRANCHES[(zi_wei_idx - 1) % 12],
            "太陽": BRANCHES[(zi_wei_idx - 3) % 12],
            "武曲": BRANCHES[(zi_wei_idx - 4) % 12],
            "天同": BRANCHES[(zi_wei_idx - 5) % 12],
            "廉貞": BRANCHES[(zi_wei_idx - 8) % 12],
        }
        
        # Tian Fu Group Placement relative to Tian Fu Star:
        # Tian Fu (0), Tai Yin (+1), Tan Lang (+2), Ju Men (+3), Tian Xiang (+4), Tian Liang (+5), Qi Sha (+6), Po Jun (+10)
        tian_fu_stars = {
            "天府": BRANCHES[tian_fu_idx],
            "太陰": BRANCHES[(tian_fu_idx + 1) % 12],
            "貪狼": BRANCHES[(tian_fu_idx + 2) % 12],
            "巨門": BRANCHES[(tian_fu_idx + 3) % 12],
            "天相": BRANCHES[(tian_fu_idx + 4) % 12],
            "天梁": BRANCHES[(tian_fu_idx + 5) % 12],
            "七殺": BRANCHES[(tian_fu_idx + 6) % 12],
            "破軍": BRANCHES[(tian_fu_idx + 10) % 12],
        }
        
        all_main_stars = {**zi_wei_stars, **tian_fu_stars}
        si_hua = SI_HUA_MATRIX.get(year_stem, {})
        
        # Construct 12 Palaces list
        palaces = []
        for i, palace_name in enumerate(PALACE_NAMES):
            palace_branch_idx = (ming_idx - i) % 12
            branch_name = BRANCHES[palace_branch_idx]
            
            # Find stars in this palace
            stars_in_palace = [star for star, b in all_main_stars.items() if b == branch_name]
            
            # Check if any star has Si Hua mutator
            mutators = []
            for mutator_type, star in si_hua.items():
                if star in stars_in_palace:
                    mutators.append(f"{star}{mutator_type}")
                    
            palaces.append({
                "palace_name": palace_name,
                "earth_branch": branch_name,
                "stars": stars_in_palace,
                "mutators": mutators,
                "is_ming_gong": (branch_name == ming_branch),
                "is_shen_gong": (branch_name == shen_branch)
            })

        return {
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
            "palaces": palaces
        }


# Quick CLI test
if __name__ == "__main__":
    engine = ZiWeiEngine()
    chart = engine.calculate_chart(1990, 5, 15, 14, "male")
    print(chart)
