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

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.bazi_engine import BaZiEngine
from project.core.svg_generator import generate_bazi_svg, generate_zodiac_wheel_svg
from project.api_router        import HybridRouter
from project.validator         import PredictionValidator
from project.rag.vector_store  import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mcp_server")

engine    = BaZiEngine()
router    = HybridRouter()
validator = PredictionValidator()
vector_store = get_vector_store()
CHARTS_DIR = ROOT / "project" / "static" / "charts"


class HoroMCPTools:
    """MCP Tool Definitions for thClaws and AGY Integration."""

    @staticmethod
    def bazi_calculate(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0) -> Dict[str, Any]:
        """Compute BaZi chart with True Solar Time adjustment."""
        dt = datetime.strptime(birth_datetime, "%Y-%m-%d %H:%M:%S")
        return engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=utc_offset_hours)

    @staticmethod
    def render_bazi_svg(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0) -> Dict[str, Any]:
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
    def render_zodiac_svg(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0) -> Dict[str, Any]:
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
    def rag_search(query: str, top_k: int = 3) -> Dict[str, Any]:
        """Search classical BaZi texts & Thai astrology books in FAISS vector store."""
        results = vector_store.search(query, top_k=top_k)
        total_count = len(getattr(vector_store, "_chunks", []))
        return {"query": query, "matches": results, "total_vectors": total_count}

    @staticmethod
    def bazi_interpret(birth_datetime: str, longitude: float = 100.493, utc_offset_hours: float = 7.0, query: str = "") -> Dict[str, Any]:
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
    def bazi_validate(bazi_chart: Dict[str, Any], initial_interpretation: str, query: str = "") -> Dict[str, Any]:
        """Validate astrological chart calculation and interpretation via Gemini Cloud API."""
        return validator.validate(bazi_chart=bazi_chart, initial_interpretation=initial_interpretation, user_query=query)


def get_mcp_manifest() -> Dict[str, Any]:
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
