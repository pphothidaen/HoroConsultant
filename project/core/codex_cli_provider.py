"""
project/core/codex_cli_provider.py
====================================
Centralized Codex CLI invocation provider.

Uses the codex1/codex2/codex3 shell wrappers (isolated HOME under
~/.ai-accounts/codex/account{N}) for all OpenAI-compatible inference,
replacing direct OpenAI SDK / httpx calls to api.openai.com.

The wrappers are defined in ~/.zshrc and delegate to the real `codex`
binary with CODEX_HOME pointed at the per-account directory so auth
credentials stay isolated.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

logger = logging.getLogger("CodexCLIProvider")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CODEX_ALIASES: list[str] = ["codex1", "codex2", "codex3"]

DEFAULT_MODEL: str = "gpt-4o-mini"

# Timeout for a single Codex CLI invocation (seconds).
TIMEOUT_S: float = 30.0


def check_codex_installation() -> bool:
    """Return True if at least one codex{N} wrapper is available on PATH."""
    for alias in CODEX_ALIASES:
        if shutil.which(alias):
            return True
    return False


def _resolve_alias(alias: Optional[str] = None) -> str:
    """Resolve alias: use provided, or first available from CODEX_ALIASES."""
    if alias and alias not in CODEX_ALIASES:
        raise ValueError(f"unsupported Codex alias: {alias}")
    if alias and shutil.which(alias):
        return alias
    for a in CODEX_ALIASES:
        if shutil.which(a):
            return a
    raise RuntimeError(
        f"No codex CLI wrapper found on PATH. Looked for: {CODEX_ALIASES}"
    )


def _build_command(
    alias: str,
    prompt: str,
    system_instruction: str = "",
    model: str = DEFAULT_MODEL,
) -> list[str]:
    """Build the shell command for codex exec.

    We write the prompt to a temp file so we avoid shell-escaping issues
    with multi-line prompts, then pass it via stdin.
    """
    cmd = [
        alias, "exec",
        "-s", "read-only",
        "--model", model,
        "--json",
        "--skip-git-repo-check",
        "--ephemeral",
    ]
    if system_instruction:
        # Prepend system instruction as a context block
        full_prompt = f"<system>\n{system_instruction}\n</system>\n\n{prompt}"
    else:
        full_prompt = prompt
    cmd.append(full_prompt)
    return cmd


def call_codex_cli(
    prompt: str,
    system_instruction: str = "",
    alias: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    timeout_s: float = TIMEOUT_S,
) -> str:
    """
    Invoke a Codex CLI wrapper and return the generated text.

    Parameters
    ----------
    prompt : str
        The user prompt to send.
    system_instruction : str
        Optional system-level instruction prepended to the prompt.
    alias : str, optional
        Which wrapper to use (codex1/codex2/codex3). Auto-resolved if None.
    model : str
        Model identifier passed to codex exec --model.
    timeout_s : float
        Maximum seconds to wait for the command.

    Returns
    -------
    str
        The generated text response.

    Raises
    ------
    RuntimeError
        If the codex CLI invocation fails or produces no output.
    subprocess.TimeoutExpired
        If the command exceeds *timeout_s* seconds.
    """
    resolved_alias = _resolve_alias(alias)
    cmd = _build_command(resolved_alias, prompt, system_instruction, model)

    logger.info(
        "[CodexCLI] Invoking %s (model=%s, prompt_len=%d)",
        resolved_alias, model, len(prompt),
    )

    t0 = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.error("[CodexCLI] %s timed out after %.1fs", resolved_alias, timeout_s)
        raise

    elapsed = time.monotonic() - t0
    logger.info("[CodexCLI] %s finished in %.2fs (exit=%d)", resolved_alias, elapsed, result.returncode)

    if result.returncode != 0:
        stderr_tail = result.stderr.strip().splitlines()[-3:] if result.stderr else []
        logger.warning("[CodexCLI] %s stderr: %s", resolved_alias, stderr_tail)
        raise RuntimeError(
            f"Codex CLI '{resolved_alias}' exited with code {result.returncode}"
        )

    # Parse JSONL output — extract the final assistant message text
    text = _parse_codex_jsonl(result.stdout)
    if not text:
        raise RuntimeError(
            f"Codex CLI '{resolved_alias}' produced no parseable text output"
        )
    return text


def _parse_codex_jsonl(stdout: str) -> str:
    """
    Parse codex exec --json (JSONL) output and extract the final message text.

    The JSONL stream contains event objects. We look for the last
    'assistant_message' or 'message' event with non-empty text.
    """
    if not stdout:
        return ""

    lines = stdout.strip().splitlines()
    last_text = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        # codex --json emits various event shapes; capture text from any
        # event that carries a 'text' or 'message' field.
        if isinstance(event, dict):
            # Direct text field
            if "text" in event and isinstance(event["text"], str):
                last_text = event["text"]
            # Nested message.content structure
            msg = event.get("message") or event.get("content")
            if isinstance(msg, dict):
                content = msg.get("content") or msg.get("text")
                if isinstance(content, str) and content:
                    last_text = content
            item = event.get("item")
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                last_text = item["text"]
            # Some events carry delta fragments
            delta = event.get("delta")
            if isinstance(delta, str) and delta:
                last_text += delta

    return last_text.strip()


def call_codex_cli_round_robin(
    prompt: str,
    system_instruction: str = "",
    model: str = DEFAULT_MODEL,
    timeout_s: float = TIMEOUT_S,
) -> tuple[str, str]:
    """
    Try each codex alias in round-robin order until one succeeds.

    Returns
    -------
    (text, alias) : The successful response text and which alias produced it.
    """
    errors: list[str] = []
    for alias in CODEX_ALIASES:
        if not shutil.which(alias):
            continue
        try:
            text = call_codex_cli(
                prompt,
                system_instruction=system_instruction,
                alias=alias,
                model=model,
                timeout_s=timeout_s,
            )
            return text, alias
        except Exception as exc:
            errors.append(f"{alias}: {exc}")
            logger.warning("[CodexCLI] Round-robin: %s failed: %s", alias, exc)
            continue

    raise RuntimeError(
        f"All Codex CLI aliases failed: {'; '.join(errors)}"
    )
