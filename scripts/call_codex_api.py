#!/usr/bin/env python3
"""
scripts/call_codex_api.py
=========================
Standalone CLI Tool & Subagent Entrypoint for CODEX_CHATGPT provider (`codex exec`).
Uses local ChatGPT Pro Codex subscription quota via non-interactive Codex CLI execution.

Usage:
  python3 scripts/call_codex_api.py --prompt "Refactor fast_math.py BaZi calculation for Rust PyO3" --agent developer
  python3 scripts/call_codex_api.py --file project/core/fast_math.py --agent code_reviewer
  cat prompt.txt | python3 scripts/call_codex_api.py --agent orchestrator
  python3 scripts/call_codex_api.py --health
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from project.core.ai_provider_router import ai_router, is_dev_environment
from project.core.codex_client import PROX5_AGENT_MODEL_MAP


def main():
    parser = argparse.ArgumentParser(description="CODEX_CHATGPT CLI Assistant for HoroConsultant (Dev-Only)")
    parser.add_argument("--prompt", "-p", type=str, help="Prompt text for Codex AI Provider")
    parser.add_argument("--file", "-f", type=str, help="File path to read input code/content from")
    parser.add_argument("--agent", "-a", type=str, choices=list(PROX5_AGENT_MODEL_MAP.keys()), help="Target agent role (orchestrator, developer, code_reviewer, etc.)")
    parser.add_argument("--system", "-s", type=str, default="You are an expert Python 3.14 & Rust PyO3 Senior Developer.", help="System prompt context")
    parser.add_argument("--health", action="store_true", help="Print AI Provider Health Check status")

    args = parser.parse_args()

    if args.health:
        health = ai_router.get_provider_health()
        print(json.dumps(health, indent=2, ensure_ascii=False))
        sys.exit(0)

    if not is_dev_environment():
        print("[ERROR] Safety Guard: Codex CLI is restricted to Development Environment only.", file=sys.stderr)
        sys.exit(1)

    prompt_content = ""
    if args.prompt:
        prompt_content = args.prompt
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        prompt_content = f"Analyze and process file: {file_path.name}\n\n```\n{file_path.read_text(encoding='utf-8')}\n```"
    elif not sys.stdin.isatty():
        prompt_content = sys.stdin.read().strip()

    if not prompt_content:
        print("[ERROR] No prompt provided. Use --prompt, --file, or pipe input via stdin.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Invoking CODEX_CHATGPT Provider (Role: {args.agent or 'custom'})...", file=sys.stderr)
    res = ai_router.call_ai(
        prompt=prompt_content,
        system_prompt=args.system,
        timeout_seconds=45,
    )

    if res["status"] == "success":
        print(f"[OK] Response received from {res['provider']} ({res['model']}):\n", file=sys.stderr)
        print(res["content"])
    elif res["status"] == "fallback":
        print(f"[WARNING] Fallback activated ({res['provider']} / {res['model']}): {res['error_message']}\n", file=sys.stderr)
        print(res["content"])
    else:
        print(f"[ERROR] Provider call failed: {res['error_message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
