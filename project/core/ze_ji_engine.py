"""
Date Selection (擇吉學 & 建除十二神) Core Calculation Engine
============================================================
Deterministic calculation of Date Selection suitability:
- Twelve Duty Officers (建除十二神: 建, 除, 滿, 平, 定, 執, 破, 危, 成, 收, 開, 閉)
- Year Breaker (歲破) & Month Breaker (月破) checks
- Activity suitability matrix (Marriage, Moving, Opening, Travel, Construction)
"""

from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

DUTY_OFFICERS = [
    "建日", "除日", "滿日", "平日", "定日", "執日",
    "破日", "危日", "成日", "收日", "開日", "閉日"
]

OFFICER_DESCRIPTIONS = {
    "建日": "健旺之日。宜開創、上任、祈福；忌動土、開倉。",
    "除日": "掃除惡氣。宜沐浴、求醫、解除、清潔；忌求官、開張。",
    "滿日": "圓滿豐收。宜開市、立券、祭祀；忌動土、服藥。",
    "平日": "平正和洽。宜修路、塗泥、平基；忌爭執、祈福。",
    "定日": "安定不動。宜冠帶、立券、訂婚、安床；忌出行、詞訟。",
    "執日": "執持固守。宜捕捉、結婚、建造；忌搬家、遠行。",
    "破日": "衝破不和。宜破屋、壞垣、求醫；忌辦喜事、開張。",
    "危日": "高危警惕。宜祭祀、祈福；忌登高、乘船、冒險。",
    "成日": "成就成功。宜結婚、開市、入學、赴任；忌爭端、詞訟。",
    "收日": "收藏收穫。宜收帳、進人口、置產；忌安葬、出行。",
    "開日": "開放光明。宜開市、結婚、出行、建造；忌安葬、破土。",
    "閉日": "堅閉收斂。宜築堤、補垣、埋穴；忌開光、求醫。"
}

# Conflict mapping (Clash branches)
BRANCH_CLASH = {
    "子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥",
    "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"
}


class ZeJiEngine(AbstractAstrologyEngine):
    """Core Date Selection engine."""

    @property
    def engine_name(self) -> str:
        return "Imperial Calendar Date Selection Engine"

    @property
    def system_type(self) -> str:
        return "ze_ji"

    def calculate_duty_officer(self, month_branch: str, day_branch: str) -> str:
        """
        Calculate 12 Duty Officer.
        Officer = Starts with 'Jian' on the day matching Month Branch, then steps clockwise.
        """
        month_idx = BRANCHES.index(month_branch)
        day_idx = BRANCHES.index(day_branch)
        offset = (day_idx - month_idx) % 12
        return DUTY_OFFICERS[offset]

    def check_suitability(
        self,
        year_branch: str,
        month_branch: str,
        day_branch: str,
        user_birth_branch: str | None = None
    ) -> dict[str, Any]:
        """
        Evaluate date suitability for key life events.
        """
        officer = self.calculate_duty_officer(month_branch, day_branch)
        
        is_year_breaker = (BRANCH_CLASH.get(year_branch) == day_branch)
        is_month_breaker = (BRANCH_CLASH.get(month_branch) == day_branch)
        is_user_clash = (user_birth_branch and BRANCH_CLASH.get(user_birth_branch) == day_branch)

        # Base rating (1 to 5 stars)
        if is_year_breaker or is_month_breaker or officer == "破日":
            rating = 1
            status = "凶 - 大事不宜 (歲破/月破/破日)"
        elif is_user_clash:
            rating = 2
            status = "平凶 - 衝剋個人生肖"
        elif officer in ["成日", "開日", "滿日"]:
            rating = 5
            status = "吉 - 百事大吉"
        elif officer in ["建日", "除日", "定日"]:
            rating = 4
            status = "吉 - 宜開創求醫"
        else:
            rating = 3
            status = "平 - 諸事平順"

        activities = {
            "結婚訂婚": "宜" if officer in ["成日", "開日", "定日", "執日"] and not is_year_breaker else "忌",
            "開市開業": "宜" if officer in ["成日", "開日", "滿日", "建日"] and not is_year_breaker else "忌",
            "搬家入宅": "宜" if officer in ["成日", "開日", "定日"] and not is_year_breaker else "忌",
            "出行遠遊": "宜" if officer in ["開日", "成日"] and officer != "定日" else "忌",
            "求醫治病": "宜" if officer in ["除日", "破日"] else "平"
        }

        raw = {
            "engine": "ZeJiEngine",
            "duty_officer": officer,
            "duty_description": OFFICER_DESCRIPTIONS.get(officer, ""),
            "rating_stars": rating,
            "overall_status": status,
            "is_year_breaker": is_year_breaker,
            "is_month_breaker": is_month_breaker,
            "is_user_clash": is_user_clash,
            "activities_suitability": activities
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.check_suitability(*args, **kwargs)


if __name__ == "__main__":
    zj = ZeJiEngine()
    result = zj.check_suitability("午", "申", "寅", "子")
    print(result)
