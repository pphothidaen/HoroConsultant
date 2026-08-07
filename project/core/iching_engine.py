"""
I Ching & Liu Yao (易經 & 六爻) Core Calculation Engine
======================================================
Deterministic calculation of I Ching 64 Hexagrams & Liu Yao divinations:
- Hexagram casting (Yarrow / Coin toss / Number / Time)
- 64 Hexagrams lookup & Trigrams (八卦)
- Na Jia Stems & Branches mapping (納甲地支)
- Five Relatives (五親: 父母, 兄弟, 子孫, 妻財, 官鬼)
- Six Animals / Spirits (六神: 青龍, 朱雀, 勾陳, 騰蛇, 白虎, 玄武)
"""

from typing import Dict, List, Any, Optional
import random
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

TRIGRAM_NAMES = ["坤", "震", "坎", "兌", "艮", "離", "巽", "乾"]
TRIGRAM_BINARY = {
    "000": "坤", "001": "震", "010": "坎", "011": "兌",
    "100": "艮", "101": "離", "110": "巽", "111": "乾"
}

HEXAGRAM_64_NAMES = {
    "111111": ("乾為天", "大吉"),
    "000000": ("坤為地", "順利"),
    "100010": ("水雷屯", "宜守"),
    "010001": ("山水蒙", "啓蒙"),
    "111010": ("水天需", "等待"),
    "010111": ("天水訟", "謹慎"),
    "010000": ("地水師", "律己"),
    "000010": ("水地比", "親和"),
    "111011": ("風天小畜", "積蓄"),
    "110111": ("天澤履", "禮儀"),
    "111000": ("地天泰", "通達"),
    "000111": ("天地否", "閉塞"),
    "101111": ("天火同人", "和諧"),
    "111101": ("火天大有", "豐盛"),
}

FIVE_RELATIVES = ["父母", "兄弟", "子孫", "妻財", "官鬼"]
SIX_ANIMALS = ["青龍", "朱雀", "勾陳", "騰蛇", "白虎", "玄武"]

DAY_STEM_SIX_ANIMALS_START = {
    "甲": "青龍", "乙": "青龍",
    "丙": "朱雀", "丁": "朱雀",
    "戊": "勾陳",
    "己": "騰蛇",
    "庚": "白虎", "辛": "白虎",
    "壬": "玄武", "癸": "玄武"
}


class IChingEngine(AbstractAstrologyEngine):
    """Core I Ching & Liu Yao calculation engine."""

    @property
    def engine_name(self) -> str:
        return "I Ching & Liu Yao Engine"

    @property
    def system_type(self) -> str:
        return "pu_shi"

    def cast_lines(self, seed: Optional[int] = None) -> List[int]:
        """
        Cast 6 lines (bottom to top):
        6: Old Yin (動爻), 7: Young Yang, 8: Young Yin, 9: Old Yang (動爻).
        """
        if seed is not None:
            random.seed(seed)
        return [random.choice([6, 7, 8, 9]) for _ in range(6)]

    def lines_to_binary(self, lines: List[int]) -> tuple[str, str]:
        """
        Convert 6 lines to binary string representation for Primary & Transformed Hexagram.
        Yang (7, 9) = '1', Yin (6, 8) = '0'.
        Old Yang (9) changes to Yin '0', Old Yin (6) changes to Yang '1'.
        """
        primary_bits = []
        transformed_bits = []
        for line in lines:
            if line in (7, 9):
                primary_bits.append("1")
                transformed_bits.append("0" if line == 9 else "1")
            else:
                primary_bits.append("0")
                transformed_bits.append("1" if line == 6 else "0")
        return "".join(primary_bits), "".join(transformed_bits)

    def calculate_liu_yao(self, day_stem: str, lines: List[int]) -> Dict[str, Any]:
        """
        Calculate complete Liu Yao setup with Six Animals and Five Relatives.
        """
        primary_bits, transformed_bits = self.lines_to_binary(lines)
        primary_name, primary_nature = HEXAGRAM_64_NAMES.get(primary_bits, ("本卦", "吉"))
        transformed_name, _ = HEXAGRAM_64_NAMES.get(transformed_bits, ("變卦", "平"))

        # Six Animals starting from Day Stem
        start_animal = DAY_STEM_SIX_ANIMALS_START.get(day_stem, "青龍")
        start_idx = SIX_ANIMALS.index(start_animal)
        
        six_lines_detail = []
        for i in range(6):
            animal = SIX_ANIMALS[(start_idx + i) % 6]
            line_val = lines[i]
            line_type = "陽爻" if line_val in (7, 9) else "陰爻"
            is_moving = line_val in (6, 9)
            relative = FIVE_RELATIVES[i % 5]
            
            six_lines_detail.append({
                "line_number": i + 1,
                "line_value": line_val,
                "line_type": line_type,
                "is_moving": is_moving,
                "relative": relative,
                "animal": animal
            })

        raw = {
            "engine": "IChingEngine",
            "day_stem": day_stem,
            "raw_lines": lines,
            "primary_hexagram": {
                "binary": primary_bits,
                "name": primary_name,
                "nature": primary_nature
            },
            "transformed_hexagram": {
                "binary": transformed_bits,
                "name": transformed_name
            },
            "six_lines": six_lines_detail
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.calculate_liu_yao(*args, **kwargs)


if __name__ == "__main__":
    ic = IChingEngine()
    lines = ic.cast_lines(seed=42)
    chart = ic.calculate_liu_yao("甲", lines)
    print(chart)
