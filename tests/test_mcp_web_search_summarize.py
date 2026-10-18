"""
tests/test_mcp_web_search_summarize.py — Contract tests for MCP web_search and summarize tools
==============================================================================================
Ticket: KAN-171
Verifies:
1. Manifest exposure for web_search and summarize with RFC parameter schemas.
2. call_tool("web_search", ...) execution and structured response.
3. call_tool("summarize", ...) execution using gemini-3.5-flash-lite.
4. Error containment on invalid/empty arguments.
5. HybridRouter preferred_model route prioritization.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from project.api_router import HybridRouter
from project.mcp_server import HoroMCPTools, _get_router, call_tool, get_mcp_manifest
from project.schemas.mcp_tools_v1 import (
    MCP_TOOL_REGISTRY,
    get_full_mcp_manifest,
)


class TestMCPWebSearchSummarizeContract(unittest.TestCase):
    def test_tools_registered_in_schema_registry(self):
        """MCP_TOOL_REGISTRY must register web_search and summarize."""
        self.assertIn("web_search", MCP_TOOL_REGISTRY)
        self.assertIn("summarize", MCP_TOOL_REGISTRY)

        ws_spec = MCP_TOOL_REGISTRY["web_search"]
        self.assertIn("param_model", ws_spec)
        self.assertIn("result_model", ws_spec)

        sum_spec = MCP_TOOL_REGISTRY["summarize"]
        self.assertIn("param_model", sum_spec)
        self.assertIn("result_model", sum_spec)

    def test_tools_present_in_manifests(self):
        """Both get_full_mcp_manifest and get_mcp_manifest must expose web_search and summarize."""
        full_manifest = get_full_mcp_manifest().model_dump()
        full_tool_names = [t["name"] for t in full_manifest.get("tools", [])]
        self.assertIn("web_search", full_tool_names)
        self.assertIn("summarize", full_tool_names)

        server_manifest = get_mcp_manifest()
        server_tool_names = [t["name"] for t in server_manifest.get("tools", [])]
        self.assertIn("web_search", server_tool_names)
        self.assertIn("summarize", server_tool_names)

    def test_web_search_execution(self):
        """call_tool('web_search', ...) should return structured results."""
        resp = call_tool("web_search", {"query": "AI astrology trends 2026", "max_results": 3})
        self.assertTrue(resp.get("success"), f"web_search call failed: {resp}")
        res = resp.get("result", {})
        self.assertIn("query", res)
        self.assertEqual(res["query"], "AI astrology trends 2026")
        self.assertIn("results", res)
        self.assertIsInstance(res["results"], list)
        self.assertIn("total_results", res)

    def test_summarize_execution_with_gemini_flash_lite(self):
        """call_tool('summarize', ...) should call router with gemini-3.5-flash-lite."""
        mock_res = {
            "text": "This is a concise summary.",
            "model_used": "gemini-3.5-flash-lite",
            "route": "cloud:gemini-3.5-flash-lite[...key1]",
            "latency_ms": 120,
        }

        router = _get_router()
        with patch.object(router, "generate", return_value=mock_res) as mock_gen:
            resp = call_tool(
                "summarize",
                {
                    "text": "Extensive research on BaZi and planetary alignments in 2026 indicates strong fire energy.",
                    "style": "bullet",
                    "max_tokens": 150,
                    "model": "gemini-3.5-flash-lite",
                },
            )
            self.assertTrue(resp.get("success"), f"summarize call failed: {resp}")
            res = resp.get("result", {})
            self.assertEqual(res.get("summary"), "This is a concise summary.")
            self.assertEqual(res.get("model_used"), "gemini-3.5-flash-lite")

            # Verify mock call parameters
            mock_gen.assert_called_once()
            _, kwargs = mock_gen.call_args
            self.assertEqual(kwargs.get("preferred_model"), "gemini-3.5-flash-lite")

    def test_summarize_default_model_is_gemini_flash_lite(self):
        """HoroMCPTools.summarize default model must be gemini-3.5-flash-lite."""
        mock_res = {
            "text": "Default summary",
            "model_used": "gemini-3.5-flash-lite",
            "route": "cloud:gemini-3.5-flash-lite",
        }
        router = _get_router()
        with patch.object(router, "generate", return_value=mock_res) as mock_gen:
            res = HoroMCPTools.summarize("Short sample text")
            self.assertEqual(res.get("model_used"), "gemini-3.5-flash-lite")
            mock_gen.assert_called_once()
            _, kwargs = mock_gen.call_args
            self.assertEqual(kwargs.get("preferred_model"), "gemini-3.5-flash-lite")

    def test_web_search_error_containment(self):
        """Invalid tool parameters should return error dictionary without crash."""
        resp = call_tool("web_search", {"query": "", "max_results": -1})
        self.assertFalse(resp.get("success"))
        self.assertIsNotNone(resp.get("error"))


if __name__ == "__main__":
    unittest.main()
