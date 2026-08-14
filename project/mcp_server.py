"""
project/mcp_server.py — Model Context Protocol (MCP) Server for thClaws & AGY
=============================================================================
Exposes the Computational Metaphysics Engine tools via standard MCP protocol
for seamless integration with thClaws (Rust Agent Harness) and AGY Subagents.

Exposed Tools:
  - bazi_calculate : Compute Four Pillars, TST, and Five Elements scores
  - rag_search     : Search classical texts (FAISS 3,132 vectors)
  - bazi_interpret : Generate AI interpretation via local qwen2.5:7b
  - bazi_validate  : Cross-validate prediction via Gemini Prediction Validator

Usage:
  python project/mcp_server.py
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.api_router import HybridRouter
from project.core.bazi_engine import BaZiEngine
from project.core.iching_engine import IChingEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.san_he_engine import SanHeEngine
from project.core.svg_generator import generate_bazi_svg, generate_zodiac_wheel_svg
from project.core.tai_yi_engine import TaiYiEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.rag.vector_store import get_vector_store
from project.validator import PredictionValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mcp_server")

engine          = BaZiEngine()
ziwei_engine    = ZiWeiEngine()
qimen_engine    = QiMenEngine()
liuren_engine   = LiuRenEngine()
iching_engine   = IChingEngine()
xuankong_engine = XuanKongEngine()
zeji_engine     = ZeJiEngine()
thaivedic_engine = ThaiVedicEngine()
western_engine  = WesternUranianEngine()
numerology_engine = NumerologyEngine()
tai_yi_engine   = TaiYiEngine()
liu_yao_engine_ = LiuYaoEngine()
mei_hua_engine  = MeiHuaEngine()
san_he_engine   = SanHeEngine()
qi_zheng_engine = QiZhengSiYuEngine()
mian_xiang_engine = MianXiangEngine()


router       = HybridRouter()
validator    = PredictionValidator()
vector_store = get_vector_store()
CHARTS_DIR   = ROOT / "project" / "static" / "charts"


class HoroMCPTools:
    """MCP Tool Definitions for thClaws and AGY Integration."""

    @staticmethod
    def bazi_calculate(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0) -> dict[str, Any]:
        """Compute BaZi chart with True Solar Time adjustment."""
        dt = datetime.strptime(birth_datetime, "%Y-%m-%d %H:%M:%S")
        return engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=utc_offset_hours)

    @staticmethod
    def render_bazi_svg(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0) -> dict[str, Any]:
        """Generate BaZi 4 Pillars SVG Chart and save to static/charts/."""
        dt = datetime.strptime(birth_datetime, "%Y-%m-%d %H:%M:%S")
        chart = engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=utc_offset_hours)
        svg_content = generate_bazi_svg(chart)
        
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        out_file = CHARTS_DIR / "bazi_chart.svg"
        out_file.write_text(svg_content, encoding="utf-8")
        
        return {
            "svg_file": str(out_file.relative_to(ROOT)),
            "svg_length": len(svg_content),
            "svg_snippet": svg_content[:200] + "..."
        }

    @staticmethod
    def render_zodiac_svg(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0) -> dict[str, Any]:
        """Generate 12 Zodiac Wheel SVG Chart and save to static/charts/."""
        dt = datetime.strptime(birth_datetime, "%Y-%m-%d %H:%M:%S")
        chart = engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=utc_offset_hours)
        svg_content = generate_zodiac_wheel_svg(chart)
        
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        out_file = CHARTS_DIR / "zodiac_wheel.svg"
        out_file.write_text(svg_content, encoding="utf-8")
        
        return {
            "svg_file": str(out_file.relative_to(ROOT)),
            "svg_length": len(svg_content),
            "svg_snippet": svg_content[:200] + "..."
        }

    @staticmethod
    def rag_search(query: str, top_k: int = 3) -> dict[str, Any]:
        """Search classical BaZi texts & Thai astrology books in FAISS vector store."""
        results = vector_store.search(query, top_k=top_k)
        total_count = len(getattr(vector_store, "_chunks", []))
        return {"query": query, "matches": results, "total_vectors": total_count}

    @staticmethod
    def bazi_interpret(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0, query: str = "") -> dict[str, Any]:
        """Generate full AI interpretation using Local Ollama (qwen2.5:7b)."""
        dt = datetime.strptime(birth_datetime, "%Y-%m-%d %H:%M:%S")
        chart = engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=utc_offset_hours)

        dm   = chart["day_master"]
        fe   = chart.get("five_elements", {}).get("percentages", {})
        prompt = (
            f"BaZi Chart for birth: {birth_datetime} "
            f"Day Master: {dm['stem']} ({dm['element']}, {dm['polarity']})\n"
            f"Five Elements: {json.dumps(fe, ensure_ascii=False)}\n"
            f"User Query: {query or 'Provide a comprehensive life reading.'}"
        )

        res = router.generate(
            prompt=prompt,
            system_instruction="You are a master BaZi consultant. Provide insightful reading."
        )
        return {"chart": chart, "interpretation": res.get("text"), "route": res.get("route")}

    @staticmethod
    def bazi_validate(bazi_chart: dict[str, Any], initial_interpretation: str, query: str = "") -> dict[str, Any]:
        """Validate astrological chart calculation and interpretation via Gemini Cloud API."""
        return validator.validate(bazi_chart=bazi_chart, initial_interpretation=initial_interpretation, user_query=query)

    @staticmethod
    def ziwei_calculate(year: int = 1990, month: int = 5, day: int = 15, hour: int = 14, gender: str = "male") -> dict[str, Any]:
        """Compute Zi Wei Dou Shu chart (12 Palaces, 14 Stars, Si Hua)."""
        return ziwei_engine.calculate_chart(year, month, day, hour, gender)

    @staticmethod
    def qimen_calculate(year: int = 2026, month: int = 8, day: int = 7, hour: int = 14) -> dict[str, Any]:
        """Compute Qi Men Dun Jia 4-Plate chart."""
        return qimen_engine.calculate_chart(year, month, day, hour)

    @staticmethod
    def liuren_calculate(day_stem: str = "甲", day_branch: str = "子", month_general: str = "正月", hour_branch: str = "午") -> dict[str, Any]:
        """Compute Da Liu Ren 3-Transmission & 4-Lesson chart."""
        return liuren_engine.calculate_chart(day_stem, day_branch, month_general, hour_branch)

    @staticmethod
    def iching_calculate(day_stem: str = "甲", seed: Optional[int] = None) -> dict[str, Any]:
        """Cast I Ching Hexagram and compute Liu Yao setup."""
        lines = iching_engine.cast_lines(seed=seed)
        return iching_engine.calculate_liu_yao(day_stem, lines)

    @staticmethod
    def xuankong_calculate(facing_degree: float = 180.0, period: int = 9) -> dict[str, Any]:
        """Compute Xuan Kong Flying Stars 9-Grid chart."""
        return xuankong_engine.calculate_chart(facing_degree, period)

    @staticmethod
    def zeji_calculate(year_branch: str = "午", month_branch: str = "申", day_branch: str = "寅", user_birth_branch: Optional[str] = "子") -> dict[str, Any]:
        """Compute Date Selection suitability via 12 Duty Officers."""
        return zeji_engine.check_suitability(year_branch, month_branch, day_branch, user_birth_branch)

    @staticmethod
    def thaivedic_calculate(year: int = 1990, month: int = 5, day: int = 15, hour: int = 14, day_of_week: int = 2) -> dict[str, Any]:
        """Compute Thai Suriyayart 10 Lagna, Maha Thaksa & Vimshottari Dasha."""
        return thaivedic_engine.calculate_chart(year, month, day, hour, day_of_week)

    @staticmethod
    def western_calculate(year: int = 1990, month: int = 5, day: int = 15, hour: int = 14) -> dict[str, Any]:
        """Compute Western Tropical Aspects, Uranian 8 TNPs & Midpoints."""
        return western_engine.calculate_chart(year, month, day, hour)

    @staticmethod
    def numerology_calculate(text: str = "0812345678", day_num: int = 2, lunar_month: int = 6, year_zodiac_num: int = 7) -> dict[str, Any]:
        """Compute Satta-Lek 7-Base 4-Row Matrix & Chaldean Numerology Scoring."""
        satta_lek = numerology_engine.calculate_satta_lek(day_num, lunar_month, year_zodiac_num)
        score = numerology_engine.score_text_or_number(text)
        return {"satta_lek": satta_lek, "chaldean_score": score}

    @staticmethod
    def tai_yi_calculate(year: int = 2026, month: int = 5, day: int = 15, hour: int = 14) -> dict[str, Any]:
        """Compute Tai Yi Shen Shu 16-path star and 8-direction matrix."""
        res = tai_yi_engine.calculate(year, month, day, hour)
        return res.chart_data

    @staticmethod
    def liu_yao_calculate(lines: list[int] = [7, 7, 7, 7, 7, 7], day_stem_idx: int = 0) -> dict[str, Any]:
        """Compute Liu Yao 6-lines divination with Na Jia and Five Relatives."""
        res = liu_yao_engine_.calculate(lines, day_stem_idx=day_stem_idx)
        return res.chart_data

    @staticmethod
    def mei_hua_calculate(year: int = 2026, month: int = 5, day: int = 15, hour: int = 14) -> dict[str, Any]:
        """Compute Mei Hua Plum Blossom Numerology Body/Function analysis."""
        res = mei_hua_engine.calculate(year, month, day, hour)
        return res.chart_data

    @staticmethod
    def san_he_calculate(sitting_degree: float = 0.0, facing_degree: float = 180.0) -> dict[str, Any]:
        """Compute San He 12 Life Stages Water Method and 24 Mountains."""
        res = san_he_engine.calculate(sitting_degree, facing_degree)
        return res.chart_data

    @staticmethod
    def qi_zheng_calculate(year: int = 2026, month: int = 5, day: int = 15, hour: int = 14) -> dict[str, Any]:
        """Compute Qi Zheng Si Yu 7 planets + 4 shadow stars on 28 lunar mansions."""
        res = qi_zheng_engine.calculate(year, month, day, hour)
        return res.chart_data

    @staticmethod
    def mian_xiang_analyze(features: dict[str, Any]) -> dict[str, Any]:
        """Analyze 12 Face Palaces and 5 Facial Features using classical physiognomy rules."""
        res = mian_xiang_engine.analyze(features)
        return res.chart_data



def get_mcp_manifest() -> dict[str, Any]:
    """Return MCP Server Tool Manifest for thClaws."""
    return {
        "name": "horo-consultant-mcp",
        "version": "1.0.0",
        "description": "Computational Metaphysics & BaZi Engine MCP Server for thClaws Harness",
        "tools": [
            {
                "name": "bazi_calculate",
                "description": "Compute BaZi 4 pillars chart with True Solar Time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birth_datetime": {"type": "string", "description": "YYYY-MM-DD HH:MM:SS"},
                        "longitude": {"type": "number", "default": 100.493},
                        "utc_offset_hours": {"type": "number", "default": 7.0}
                    },
                    "required": ["birth_datetime"]
                }
            },
            {
                "name": "rag_search",
                "description": "Search 3,132 vectors of classical BaZi & Thai astrology books",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 3}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "bazi_interpret",
                "description": "Generate natural language interpretation with local qwen2.5:7b",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birth_datetime": {"type": "string"},
                        "query": {"type": "string"}
                    },
                    "required": ["birth_datetime"]
                }
            },
            {
                "name": "bazi_validate",
                "description": "Cross-validate interpretation via Gemini Prediction Validator Agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bazi_chart": {"type": "object"},
                        "initial_interpretation": {"type": "string"},
                        "query": {"type": "string"}
                    },
                    "required": ["bazi_chart", "initial_interpretation"]
                }
            }
        ]
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manifest":
        print(json.dumps(get_mcp_manifest(), indent=2, ensure_ascii=False))
    else:
        log.info("🚀 Starting Model Context Protocol (MCP) Server for thClaws...")
        print(json.dumps(get_mcp_manifest(), indent=2, ensure_ascii=False))
