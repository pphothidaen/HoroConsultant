# project/core/universal_runtime_bridge.py
# ===========================================================================
# Computational Metaphysics Engine — Universal Production Runtime Bridge
# ===========================================================================
# Bridges thClaws (ThaiGPT Local Harness) and AGY Subagent (MCP Protocol)
# with Hybrid execution and automatic failover routing.
# ===========================================================================

from __future__ import annotations

import logging
from typing import Any

from project.mcp_server import HoroMCPTools

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("universal_runtime_bridge")


class UniversalMetaphysicsBridge:
    """Universal Metaphysics Engine Bridge.
    
    Supports 3 execution modes:
      1. 'thclaws': Local-first thClaws harness pipeline (qwen2.5:7b + FAISS RAG)
      2. 'agy_subagent': Cloud-first AGY Subagent MCP pipeline (Gemini API Validator)
      3. 'hybrid': Local generation (thClaws) + Cloud Audit (AGY Subagent) with auto-failover
    """

    def __init__(self, default_mode: str = "hybrid"):
        self.default_mode = default_mode.lower()

    def execute_thclaws_mode(self, birth_datetime: str, query: str) -> dict[str, Any]:
        """Runs native thClaws harness pipeline."""
        log.info("🤖 [thClaws Harness Mode] Invoking Local Pipeline...")
        
        # 1. Deterministic BaZi calculation
        chart = HoroMCPTools.bazi_calculate(birth_datetime=birth_datetime)
        
        # 2. FAISS Vector search
        rag_res = HoroMCPTools.rag_search(query=query, top_k=2)
        
        # 3. Local LLM interpretation
        interp_res = HoroMCPTools.bazi_interpret(birth_datetime=birth_datetime, query=query)
        
        return {
            "runtime_harness": "thClaws (Local-First Ollama qwen2.5:7b)",
            "mode": "thclaws",
            "chart": chart,
            "rag_matches": rag_res.get("matches", []),
            "interpretation": interp_res.get("interpretation", ""),
            "route_used": interp_res.get("route", "thclaws_local")
        }

    def execute_agy_subagent_mode(self, birth_datetime: str, query: str) -> dict[str, Any]:
        """Runs native AGY Subagent MCP pipeline with Gemini Cloud Validator."""
        log.info("🤖 [AGY Subagent Mode] Invoking MCP Server & Gemini Validator Pipeline...")
        
        # 1. Deterministic BaZi calculation via MCP
        chart = HoroMCPTools.bazi_calculate(birth_datetime=birth_datetime)
        
        # 2. RAG Search via MCP
        rag_res = HoroMCPTools.rag_search(query=query, top_k=3)
        
        # 3. BaZi interpretation
        interp_res = HoroMCPTools.bazi_interpret(birth_datetime=birth_datetime, query=query)
        interpretation = interp_res.get("interpretation", "")
        
        # 4. Cloud validation via Gemini API
        val_report = HoroMCPTools.bazi_validate(
            bazi_chart=chart,
            initial_interpretation=interpretation,
            query=query
        )
        
        return {
            "runtime_harness": "AGY Subagent (MCP Protocol + Gemini Cloud Validator)",
            "mode": "agy_subagent",
            "chart": chart,
            "rag_matches": rag_res.get("matches", []),
            "interpretation": val_report.get("refined_analysis", interpretation),
            "validation_report": val_report,
            "route_used": "agy_mcp_gemini"
        }

    def execute_hybrid_mode(self, birth_datetime: str, query: str) -> dict[str, Any]:
        """Runs Hybrid pipeline: thClaws local generation + AGY Subagent cloud validation with failover."""
        log.info("⚡ [Hybrid Mode] Executing thClaws Local Generation + AGY Subagent Audit...")
        
        try:
            # Step 1: Run thClaws local generation
            local_res = self.execute_thclaws_mode(birth_datetime=birth_datetime, query=query)
            chart = local_res["chart"]
            local_interp = local_res["interpretation"]
            
            # Step 2: Pass draft to AGY Subagent for Cloud Audit & Refinement
            log.info("🛡️ [Hybrid Mode] Handing off local draft to AGY Subagent Validator...")
            val_report = HoroMCPTools.bazi_validate(
                bazi_chart=chart,
                initial_interpretation=local_interp,
                query=query
            )
            
            return {
                "runtime_harness": "Hybrid (thClaws Local Engine + AGY Subagent Cloud Auditor)",
                "mode": "hybrid",
                "status": "SUCCESS",
                "chart": chart,
                "rag_matches": local_res["rag_matches"],
                "initial_local_reading": local_interp,
                "final_audited_reading": val_report.get("refined_analysis", local_interp),
                "validation_report": val_report,
                "route_used": "hybrid_thclaws_and_agy_mcp"
            }
        except Exception as e:
            log.warning(f"⚠️ Hybrid primary route hit exception ({e}). Failing over to AGY Subagent Cloud Route...")
            return self.execute_agy_subagent_mode(birth_datetime=birth_datetime, query=query)

    def run(self, birth_datetime: str, query: str = "วิเคราะห์ภาพรวมดวงชะตา", mode: str | None = None) -> dict[str, Any]:
        """Main entry point for universal runtime execution."""
        exec_mode = (mode or self.default_mode).lower()
        
        if exec_mode == "thclaws":
            return self.execute_thclaws_mode(birth_datetime=birth_datetime, query=query)
        elif exec_mode == "agy_subagent" or exec_mode == "agy":
            return self.execute_agy_subagent_mode(birth_datetime=birth_datetime, query=query)
        else:
            return self.execute_hybrid_mode(birth_datetime=birth_datetime, query=query)


# Global singleton instance for easy import across endpoints
universal_bridge = UniversalMetaphysicsBridge(default_mode="hybrid")
