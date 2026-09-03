#!/usr/bin/env bash
# Codex adapter - Codex does not have native PreToolUse hooks
# This file exists for parity but is not registered in .codex/hooks.json
echo '{"decision":"allow","reason":"CODEX_NO_NATIVE_PRETOOLUSE"}'
exit 0
