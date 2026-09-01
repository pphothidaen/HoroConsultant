#!/usr/bin/env python3
"""Run one AGY quota observation behind a fail-closed in-memory boundary.

This module intentionally invokes only the literal argument vector
``agy -p /usage``.  It does not use a shell, JSON/stream-JSON mode, a model
task, a retry, or a fallback.  The child-owned PTY supplies the account-bound
``AGY_HOME`` through the inherited environment; its value is never emitted or
persisted here.  Provider stdout and stderr exist only in subprocess memory.

The public JSON is deliberately smaller than the provider response.  A parse
or transport failure returns typed, content-free metadata with a safe
structural fingerprint (including value_shapes) and an empty bucket list, so
raw provider text can never cross the sanitizer boundary.
"""
from __future__ import annotations

import json
import hashlib
import math
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence
from zoneinfo import ZoneInfo


PARSER_VERSION = "agy-usage-sanitizer-v1.6.0"
PARSER_VERSION_SHA256 = hashlib.sha256(PARSER_VERSION.encode("ascii")).hexdigest()
TIMEZONE = "Asia/Bangkok"
DEFAULT_TIMEOUT_SECONDS = 60.0
ALLOWED_ALIASES = frozenset({"agy1", "agy2", "agy3", "agy4"})
COMMAND = ("agy", "-p", "/usage")

_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+")
_PATH_RE = re.compile(
    r"(?i)(?:\b[a-z]:\\[^\r\n\t ]+|(?<![\w.])/(?:users|home|root|private|tmp|var|etc|opt)/[^\r\n\t ]+|file://|~/)"
)
_CREDENTIAL_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|"
    r"authorization|bearer|password|passwd|cookie|session[_ -]?token|private[_ -]?key)\b"
)
_AUTH_PROMPT_RE = re.compile(
    r"(?i)\b(?:sign[ -]?in|log[ -]?in|authenticate|authentication required|oauth|device code|"
    r"open (?:a )?browser|enter (?:the )?(?:verification|authorization) code)\b"
)
_TOKEN_LIKE_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_+/=-]{32,}(?![A-Za-z0-9_+/=-]))"
    r"(?=[A-Za-z0-9_+/=-]*[A-Za-z])(?=[A-Za-z0-9_+/=-]*\d)[A-Za-z0-9_+/=-]+"
)

_BOX_CHARS = r"╭╮╰╯│┃┏┓┗┛━─┄┅┈┉┊┋+┼┴┬├┤┌┐└┘═║╒╕╘╛╞╡╠╣╦╩╬|\\-_="
_KNOWN_DECORATION_RE = re.compile(
    rf"^(?:[\s{_BOX_CHARS}]+|[>❯•*]+|\.\.\.|[-=]{{3,}})$"
)
_KNOWN_DECORATIVE_PROMPTS = frozenset(
    {
        "press esc to close",
        "esc to close",
        "q to close",
        "↑ ↓ to navigate",
        "press enter to exit",
        "enter to exit",
        "use arrow keys to navigate",
        "[esc] close",
        "[q] quit",
    }
)
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()+/\-]{0,63}$")
_COMPACT_MODEL_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()+/\-]{0,63}$")
_RESET_TIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})$"
)
_HEADINGS = frozenset(
    {
        "usage",
        "quota",
        "usage quota",
        "model usage",
        "model quota",
        "remaining quota",
        "quota usage",
        "available models",
        "available models & remaining quota",
        "account usage",
        "rate limits",
    }
)
_TABLE_HEADER_RE = re.compile(
    r"(?i)^(?:[|│]\s*)?(?:model(?:_name|_family)?|name|service|tier|item)\s*"
    r"(?:[|│]|\s{2,})\s*(?:remaining(?:_quota|_percent)?|quota|usage|status|available|percent)\s*"
    r"(?:(?:[|│]|\s{2,})\s*(?:reset(?:_time|_in|_at)?|resets?|limit|window)\s*)?(?:[|│])?$"
)
_SAFE_BANDS = frozenset({"healthy", "constrained", "below_10_percent", "exhausted", "normal", "high", "low"})
_NON_QUOTA_METADATA_VALUES = frozenset(
    {
        "pro", "flash", "active", "free", "standard", "plus", "5h", "1d", "24h",
        "--", "n/a", "none", "unlimited", "ok", "ready", "enabled", "disabled", "true", "false",
        "∞", "quota exceeded", "5 hours", "5 hour", "24 hours", "1 day", "2 req/s", "2 requests/sec",
        "2 req/sec", "2/s"
    }
)

_PROGRESS_BAR_CHARS = r"█▉▊▋▌▍▎▏░▒▓■□▪▫=#"
_PROGRESS_BAR_RE = re.compile(
    rf"(?i)(?:[\[(]?[{_PROGRESS_BAR_CHARS}=\-> ]{{3,}}[\])]?\s*(?P<pct>\d{{1,3}}(?:\.\d{{1,6}})?)%|(?P<pct2>\d{{1,3}}(?:\.\d{{1,6}})?)%\s*[\[(]?[{_PROGRESS_BAR_CHARS}=\-> ]{{3,}}[\])]?)"
)
_EMBEDDED_PCT_RE = re.compile(
    r"(?i)(?P<pct>\d{1,3}(?:\.\d{1,6})?)\s*%"
)
_BRACKETED_METRIC_RE = re.compile(
    r"\[\s*(?P<pct>\d{1,3}(?:\.\d{1,6})?)%\s*\]"
)
_RATIO_RE = re.compile(
    r"(?i)(?:[\[(]|\b)(?P<num>\d{1,3}(?:,\d{3})+|\d+)\s*(?:/|\bof\b)\s*(?P<den>\d{1,3}(?:,\d{3})+|\d+)(?:[\])]|\s+remaining|\s+used|\s+requests|\b)"
)


class _ParseFailure(Exception):
    """Internal failure carrying only a stable, content-free type."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _timestamp() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")


def _is_non_quota_value(val_str: str) -> bool:
    val_clean = val_str.strip().lower()
    if _EMBEDDED_PCT_RE.search(val_str) or _RATIO_RE.search(val_str) or _PROGRESS_BAR_RE.search(val_str):
        return False
    if val_clean in _NON_QUOTA_METADATA_VALUES:
        return True
    if re.fullmatch(r"(?i)(?:tier|plan|status|window|account|mode|model_family|region|session|reset|resets|rate|rate_limit)\s*[:=]?\s*.*", val_clean):
        return True
    if re.fullmatch(r"(?i)(?:in\s+)?\d+\s*(?:d|h|m|s|days?|hours?|minutes?|seconds?)(?:\s*(?:window|reset))?", val_clean):
        return True
    if re.fullmatch(r"(?i)\d+\s*(?:req|requests?)/(?:s|sec|second|d|day|m|min|minute)", val_clean):
        return True
    return False


def _classify_value_shape(val_str: str) -> str:
    """Classify value shape without retaining actual data."""
    val = val_str.strip()
    if _PROGRESS_BAR_RE.search(val):
        return "progress_bar_percentage"
    if _BRACKETED_METRIC_RE.search(val):
        return "bracketed_metric"
    if _EMBEDDED_PCT_RE.search(val):
        return "embedded_percentage"
    if _RATIO_RE.search(val):
        return "count_ratio"
    if re.fullmatch(r"(?i)(?:0(?:\.\d{1,9})?|1(?:\.0{1,9})?)(?:\s+remaining(?:\s+fraction)?)?", val):
        return "fraction_text"
    if val.lower().replace("-", "_").replace(" ", "_") in _SAFE_BANDS:
        return "safe_band"
    if _is_non_quota_value(val):
        return "non_quota_value"
    return "unclassified_value"


def _classify_line_structure(line: str) -> tuple[str, str, str]:
    """Classify structure safely without retaining text values.

    Returns (line_structure, first_token_type, value_shape).
    """
    line_clean = line.strip()
    if not line_clean:
        return "blank", "blank", "none"
    if _KNOWN_DECORATION_RE.fullmatch(line_clean):
        return "box_border", "border", "none"
    if line_clean.casefold().rstrip(":") in _HEADINGS:
        return "heading", "heading", "none"
    if _TABLE_HEADER_RE.fullmatch(line_clean):
        return "table_header", "heading", "none"
    if line_clean.casefold() in _KNOWN_DECORATIVE_PROMPTS or line_clean.strip("[]").casefold() in _KNOWN_DECORATIVE_PROMPTS:
        return "prompt", "prompt", "none"
    if line_clean.startswith(("•", "*", "- ")) and ":" in line_clean:
        parts = line_clean.split(":", 1)
        val_shape = _classify_value_shape(parts[1]) if len(parts) > 1 else "unclassified_value"
        return "bullet_item", "bullet", val_shape
    if "|" in line_clean or "│" in line_clean:
        return "pipe_table_row", "table_cell", "table_values"
    if ":" in line_clean or "=" in line_clean:
        parts = re.split(r"[:=]", line_clean, maxsplit=1)
        val_shape = _classify_value_shape(parts[1]) if len(parts) > 1 else "unclassified_value"
        return "key_value", "key", val_shape
    if re.search(r"\d{1,3}%\s+remaining", line_clean, re.I):
        return "human_quota", "label", "percentage"
    if re.search(r"\s{2,}\d{1,3}%", line_clean):
        return "space_table_row", "label", "percentage"
    return "unclassified", "unclassified", "unclassified_value"


def _compute_structural_fingerprint(raw_text: str, has_ansi: bool) -> dict[str, Any]:
    """Compute content-free structural fingerprint of output."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    line_structures: list[str] = []
    first_token_types: list[str] = []
    value_shapes: list[str] = []
    for line in lines:
        struct_type, token_type, val_shape = _classify_line_structure(line)
        line_structures.append(struct_type)
        first_token_types.append(token_type)
        value_shapes.append(val_shape)

    if any(st in {"pipe_table_row", "space_table_row", "table_header"} for st in line_structures):
        layout = "table"
    elif any(st == "key_value" for st in line_structures):
        layout = "key_value"
    elif any(st == "compact_metadata" for st in line_structures):
        layout = "compact_metadata"
    elif any(st == "human_quota" for st in line_structures):
        layout = "human_readable"
    elif any(st == "bullet_item" for st in line_structures):
        layout = "bullet_list"
    else:
        layout = "unclassified"

    return {
        "line_count": len(lines),
        "has_ansi_escape": has_ansi,
        "detected_layout": layout,
        "line_structures": line_structures,
        "first_token_types": first_token_types,
        "value_shapes": value_shapes,
    }


def _result(
    *,
    alias: str | None,
    captured_at: str,
    buckets: list[dict[str, Any]],
    exit_status: int | None | str,
    transport_status: str,
    structural_fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct the sole public schema; do not add provider-derived fields."""
    res: dict[str, Any] = {
        "alias": alias,
        "captured_at": captured_at,
        "timezone": TIMEZONE,
        "buckets": buckets,
        "exit_status": exit_status,
        "transport_status": transport_status,
        "parser_version": PARSER_VERSION,
        "required_human_review": True,
    }
    if structural_fingerprint is not None:
        res["structural_fingerprint"] = structural_fingerprint
    return res


def _failure(
    alias: str | None,
    code: str,
    *,
    captured_at: str | None = None,
    exit_status: int | None | str = None,
    structural_fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _result(
        alias=alias if alias in ALLOWED_ALIASES else None,
        captured_at=captured_at or _timestamp(),
        buckets=[],
        exit_status=exit_status,
        transport_status=code,
        structural_fingerprint=structural_fingerprint,
    )


def _reject_sensitive_or_auth_text(text: str) -> None:
    if _EMAIL_RE.search(text):
        raise _ParseFailure("rejected_pii")
    if _PATH_RE.search(text):
        raise _ParseFailure("rejected_path")
    if _CREDENTIAL_RE.search(text) or _TOKEN_LIKE_RE.search(text):
        raise _ParseFailure("rejected_credential_like")
    if _AUTH_PROMPT_RE.search(text):
        raise _ParseFailure("rejected_auth_prompt")


def _parse_reset(value: str, field: str) -> tuple[str, str | int]:
    value = value.strip()
    if field == "reset_time":
        if not _RESET_TIME_RE.fullmatch(value):
            raise _ParseFailure("invalid_reset_time")
        return field, value
    if not re.fullmatch(r"\d{1,9}", value):
        raise _ParseFailure("invalid_reset_duration")
    seconds = int(value)
    if seconds < 0:
        raise _ParseFailure("invalid_reset_duration")
    return field, seconds


def _duration_seconds(value: str) -> int:
    value = value.strip().lower()
    if re.fullmatch(r"\d{1,9}", value):
        return int(value)
    parts = re.findall(r"(\d+)\s*(d|h|m|s|days?|hours?|minutes?|seconds?)\b", value)
    if not parts:
        raise _ParseFailure("invalid_reset_duration")
    residue = re.sub(r"\d+\s*(?:d|h|m|s|days?|hours?|minutes?|seconds?)\b", "", value).strip()
    if residue and residue not in {"in", "at", "resets in", "resets at"}:
        raise _ParseFailure("invalid_reset_duration")
    factors = {
        "d": 86400,
        "day": 86400,
        "days": 86400,
        "h": 3600,
        "hour": 3600,
        "hours": 3600,
        "m": 60,
        "minute": 60,
        "minutes": 60,
        "s": 1,
        "second": 1,
        "seconds": 1,
    }
    seconds = sum(int(number) * factors[unit] for number, unit in parts)
    if seconds > 999_999_999:
        raise _ParseFailure("invalid_reset_duration")
    return seconds


def _validate_label(label: str) -> str:
    label = " ".join(label.strip().strip("•*- []()").split())
    if not _LABEL_RE.fullmatch(label):
        raise _ParseFailure("invalid_bucket_label")
    return label


def _extract_reset_info(text: str) -> dict[str, Any]:
    """Safely extract reset_time or reset_in_seconds if present."""
    m_time = re.search(r"(?i)resets?\s+(?:in|at)\s+(?P<val>[0-9T:Z+\-.]+)", text)
    if m_time:
        raw_val = m_time.group("val").strip("() ,")
        if _RESET_TIME_RE.fullmatch(raw_val):
            return {"reset_time": raw_val}
    m_dur = re.search(r"(?i)resets?\s+in\s+(?P<val>\d+\s*(?:d|h|m|s|days?|hours?|minutes?|seconds?)(?:\s*\d+\s*(?:d|h|m|s|days?|hours?|minutes?|seconds?))*)", text)
    if m_dur:
        try:
            return {"reset_in_seconds": _duration_seconds(m_dur.group("val"))}
        except _ParseFailure:
            pass
    return {}


def _parse_value_driven_key_value(line: str) -> dict[str, Any] | None | str:
    """Parse key: value or key = value based on safe anchored quota semantics.

    Returns:
    - dict: parsed quota bucket
    - None: line is non-quota auxiliary metadata (safely ignored)
    - "unclassified": line could not be parsed as key-value
    """
    if ":" not in line and "=" not in line:
        return "unclassified"
    parts = re.split(r"[:=]", line, maxsplit=1)
    if len(parts) != 2:
        return "unclassified"
    raw_label, raw_val = parts[0].strip(), parts[1].strip()
    if not raw_label or not raw_val:
        return "unclassified"
    try:
        label = _validate_label(raw_label)
    except _ParseFailure:
        return "unclassified"

    # 1. Non-quota metadata (e.g. Tier: Pro, Status: Active, Window: 5h, quota exceeded, --, N/A, ∞) -> safely ignore
    if _is_non_quota_value(raw_val):
        return None

    # 2. Progress bar percentage: e.g. [██████░░] 88% or [░░░░░░░░░░] 0% or [██████████] 100%
    pb_m = _PROGRESS_BAR_RE.search(raw_val)
    if pb_m:
        pct_str = pb_m.group("pct") or pb_m.group("pct2")
        val = float(pct_str)
        if 0 <= val <= 100:
            fields: dict[str, Any] = {"remaining_percent": int(val) if val.is_integer() else val}
            fields.update(_extract_reset_info(raw_val))
            return _finish_bucket(label, fields)

    # 3. Bracketed metric: e.g. OK [88%]
    bracket_m = _BRACKETED_METRIC_RE.search(raw_val)
    if bracket_m:
        val = float(bracket_m.group("pct"))
        if 0 <= val <= 100:
            fields = {"remaining_percent": int(val) if val.is_integer() else val}
            fields.update(_extract_reset_info(raw_val))
            return _finish_bucket(label, fields)

    # 4. Embedded percentage: e.g. Available (88%), 88% of daily limit, Resets at 15:00 (88%), 88% remaining
    embed_m = _EMBEDDED_PCT_RE.search(raw_val)
    if embed_m:
        val = float(embed_m.group("pct"))
        if 0 <= val <= 100:
            fields = {"remaining_percent": int(val) if val.is_integer() else val}
            fields.update(_extract_reset_info(raw_val))
            return _finish_bucket(label, fields)

    # 5. Count ratio: e.g. 1,500 / 1,500 or 1500 / 2000 or 12 of 20 remaining
    ratio_m = _RATIO_RE.search(raw_val)
    if ratio_m:
        num = float(ratio_m.group("num").replace(",", ""))
        den = float(ratio_m.group("den").replace(",", ""))
        if den > 0 and 0 <= num <= den:
            pct = round((num / den) * 100, 2)
            fields = {"remaining_percent": int(pct) if pct.is_integer() else pct}
            fields.update(_extract_reset_info(raw_val))
            return _finish_bucket(label, fields)

    # 6. Fraction text: e.g. 0.88 or 0.88 remaining fraction
    frac_m = re.fullmatch(
        r"(?i)(?P<frac>0(?:\.\d{1,9})?|1(?:\.0{1,9})?)(?:\s+remaining(?:\s+fraction)?)?",
        raw_val,
    )
    if frac_m:
        return _finish_bucket(label, {"remaining_fraction": float(frac_m.group("frac"))})

    # 7. Safe band
    band = raw_val.lower().replace("-", "_").replace(" ", "_")
    if band in _SAFE_BANDS:
        return _finish_bucket(label, {"safe_band": band})

    return "unclassified"


def _parse_compact_metadata_line(line: str) -> tuple[str, str] | tuple[str, float] | None:
    model_match = re.fullmatch(
        r"(?i)(model_family|model)\s*[:=]\s*(?P<value>.+)", line
    )
    if model_match:
        value = model_match.group("value").strip()
        if not _COMPACT_MODEL_VALUE_RE.fullmatch(value):
            raise _ParseFailure("invalid_model_metadata")
        return "model", value

    percent_match = re.fullmatch(
        r"(?i)(?:remaining_percent|remaining)\s*[:=]\s*(?P<value>\d{1,3}(?:\.\d{1,6})?)%",
        line,
    )
    if percent_match:
        value = float(percent_match.group("value"))
        if not 0 <= value <= 100:
            raise _ParseFailure("invalid_remaining_percent")
        return "remaining_percent", int(value) if value.is_integer() else value
    return None


def _parse_table_row(line: str) -> dict[str, Any] | None:
    """Parse pipe-separated or space-aligned table rows."""
    line_clean = line.strip().strip("│|").strip()
    if not line_clean:
        return None

    # 1. Pipe-separated row: e.g. "Gemini Pro | 63% | in 2h 5m"
    if "|" in line or "│" in line:
        parts = [p.strip() for p in re.split(r"[|│]", line) if p.strip()]
        if len(parts) >= 2:
            try:
                label = _validate_label(parts[0])
            except _ParseFailure:
                return None
            pct_m = re.search(r"(\d{1,3}(?:\.\d{1,6})?)%", parts[1])
            if pct_m:
                val = float(pct_m.group(1))
                if not 0 <= val <= 100:
                    raise _ParseFailure("invalid_remaining_percent")
                fields: dict[str, Any] = {"remaining_percent": int(val) if val.is_integer() else val}
                if len(parts) >= 3:
                    raw_reset = parts[2].strip()
                    if _RESET_TIME_RE.fullmatch(raw_reset):
                        fields["reset_time"] = raw_reset
                    else:
                        fields["reset_in_seconds"] = _duration_seconds(raw_reset)
                return _finish_bucket(label, fields)

    # 2. Space-columnar: "Gemini 2.5 Pro    88%    2h 15m"
    space_m = re.match(
        r"^(?P<label>[A-Za-z0-9][A-Za-z0-9 ._()+/\-]{0,63}?)\s{2,}"
        r"(?P<pct>\d{1,3}(?:\.\d{1,6})?)%"
        r"(?:\s{2,}|\s*\(?resets?\s+(?:in|at)\s+|\s*,\s*resets?\s+(?:in|at)\s+)?(?P<reset>.*)?$",
        line_clean,
        re.I,
    )
    if space_m:
        try:
            label = _validate_label(space_m.group("label"))
        except _ParseFailure:
            return None
        val = float(space_m.group("pct"))
        if not 0 <= val <= 100:
            raise _ParseFailure("invalid_remaining_percent")
        fields = {"remaining_percent": int(val) if val.is_integer() else val}
        reset_raw = (space_m.group("reset") or "").strip("() ,")
        if reset_raw:
            if _RESET_TIME_RE.fullmatch(reset_raw):
                fields["reset_time"] = reset_raw
            else:
                fields["reset_in_seconds"] = _duration_seconds(reset_raw)
        return _finish_bucket(label, fields)

    # 3. Simple space-separated: "gemini-flash    100%"
    simple_space_m = re.match(
        r"^(?P<label>[A-Za-z0-9][A-Za-z0-9 ._()+/\-]{0,63}?)\s{2,}(?P<pct>\d{1,3}(?:\.\d{1,6})?)%$",
        line_clean,
    )
    if simple_space_m:
        try:
            label = _validate_label(simple_space_m.group("label"))
        except _ParseFailure:
            return None
        val = float(simple_space_m.group("pct"))
        if not 0 <= val <= 100:
            raise _ParseFailure("invalid_remaining_percent")
        return _finish_bucket(label, {"remaining_percent": int(val) if val.is_integer() else val})

    return None


def _finish_bucket(label: str, fields: Mapping[str, Any]) -> dict[str, Any]:
    quota_fields = [field for field in ("remaining_fraction", "remaining_percent", "safe_band") if field in fields]
    if len(quota_fields) != 1:
        raise _ParseFailure("ambiguous_or_missing_metric")
    allowed = set(quota_fields) | {"reset_time", "reset_in_seconds"}
    if set(fields) - allowed:
        raise _ParseFailure("unexpected_field")
    if "reset_time" in fields and "reset_in_seconds" in fields:
        raise _ParseFailure("ambiguous_reset")
    bucket: dict[str, Any] = {"label": label, quota_fields[0]: fields[quota_fields[0]]}
    if "reset_time" in fields:
        bucket["reset_time"] = fields["reset_time"]
    if "reset_in_seconds" in fields:
        bucket["reset_in_seconds"] = fields["reset_in_seconds"]
    return bucket


def sanitize_usage_output(
    raw_output: str,
    alias: str,
    *,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Return allowlisted quota metadata with structural fingerprint."""
    captured_at = captured_at or _timestamp()
    if alias not in ALLOWED_ALIASES:
        return _failure(None, "invalid_alias", captured_at=captured_at, exit_status="not_started")
    if not isinstance(raw_output, str) or not raw_output:
        return _failure(alias, "parse_failure:empty_output", captured_at=captured_at, exit_status=0)

    has_ansi = bool(_ANSI_RE.search(raw_output))
    fingerprint: dict[str, Any] | None = None
    try:
        _reject_sensitive_or_auth_text(raw_output)
        text = _ANSI_RE.sub("", raw_output)
        _reject_sensitive_or_auth_text(text)
        fingerprint = _compute_structural_fingerprint(text, has_ansi=has_ansi)

        buckets: list[dict[str, Any]] = []
        labels: set[str] = set()
        saw_nonempty = False
        compact_model: str | None = None
        compact_metric: float | int | None = None
        compact_metric_field: str | None = None

        for original_line in text.splitlines():
            line = original_line.strip()
            if not line:
                continue
            saw_nonempty = True
            if (
                _KNOWN_DECORATION_RE.fullmatch(line)
                or line.casefold() in _KNOWN_DECORATIVE_PROMPTS
                or line.strip("[]").casefold() in _KNOWN_DECORATIVE_PROMPTS
                or line.casefold().rstrip(":") in _HEADINGS
                or _TABLE_HEADER_RE.fullmatch(line)
            ):
                continue

            compact = _parse_compact_metadata_line(line)
            if compact is not None:
                if buckets:
                    raise _ParseFailure("mixed_output_formats")
                field, value = compact
                if field == "model":
                    if compact_model is not None:
                        raise _ParseFailure("duplicate_model_metadata")
                    compact_model = value  # type: ignore[assignment]
                else:
                    if compact_metric_field is not None:
                        raise _ParseFailure("duplicate_field")
                    compact_metric_field = field
                    compact_metric = value  # type: ignore[assignment]
                continue

            # Value-driven key-value parsing
            kv_result = _parse_value_driven_key_value(line)
            if kv_result is None:
                # Line is safe auxiliary non-quota metadata (e.g. Tier: Pro, Status: Active, Window: 5h)
                continue
            if isinstance(kv_result, dict):
                bucket = kv_result
            else:
                # Try table row
                bucket = _parse_table_row(line)

            if bucket is None:
                struct_type, _, _ = _classify_line_structure(line)
                if struct_type in {"pipe_table_row", "space_table_row"}:
                    raise _ParseFailure("unexpected_table_row")
                if struct_type == "key_value":
                    raise _ParseFailure("unexpected_key_value")
                if struct_type == "heading":
                    raise _ParseFailure("unexpected_header")
                if struct_type == "box_border":
                    raise _ParseFailure("unexpected_box_decoration")
                raise _ParseFailure("unexpected_line")

            label_key = bucket["label"].casefold()
            if label_key in labels:
                raise _ParseFailure("duplicate_bucket")
            labels.add(label_key)
            buckets.append(bucket)

        if not saw_nonempty:
            raise _ParseFailure("empty_output")
        if compact_model is not None or compact_metric_field is not None:
            if compact_model is None or compact_metric_field is None or compact_metric is None:
                raise _ParseFailure("missing_bucket")
            buckets.append(
                _finish_bucket(
                    _validate_label(compact_model),
                    {compact_metric_field: compact_metric},
                )
            )
        if not buckets:
            raise _ParseFailure("missing_bucket")

    except _ParseFailure as failure:
        return _failure(
            alias,
            f"parse_failure:{failure.code}",
            captured_at=captured_at,
            exit_status=0,
            structural_fingerprint=fingerprint,
        )

    return _result(
        alias=alias,
        captured_at=captured_at,
        buckets=buckets,
        exit_status=0,
        transport_status="completed",
        structural_fingerprint=fingerprint,
    )


def _decode_in_memory(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
    if value is None:
        return ""
    raise UnicodeError("unsupported in-memory subprocess output type")


def run_usage_probe(
    alias: str,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    runner: Callable[..., Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Invoke the one allowed command and sanitize it directly in memory.

    Subprocess inherits environment (including NO_COLOR=1, TERM=dumb, LC_ALL=C).
    AGY_HOME is never emitted or persisted.
    """
    captured_at = _timestamp()
    if alias not in ALLOWED_ALIASES:
        return _failure(None, "invalid_alias", captured_at=captured_at, exit_status="not_started")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        return _failure(alias, "invalid_timeout", captured_at=captured_at, exit_status="not_started")
    timeout_value = float(timeout_seconds)
    if not math.isfinite(timeout_value) or not 1 <= timeout_value <= 300:
        return _failure(alias, "invalid_timeout", captured_at=captured_at, exit_status="not_started")
    inherited_environment = os.environ if environ is None else environ
    if not inherited_environment.get("AGY_HOME"):
        return _failure(alias, "environment_missing", captured_at=captured_at, exit_status="not_started")

    execute = subprocess.run if runner is None else runner
    try:
        completed = execute(
            list(COMMAND),
            capture_output=True,
            check=False,
            shell=False,
            timeout=timeout_value,
        )
    except subprocess.TimeoutExpired:
        return _failure(alias, "timeout", captured_at=captured_at, exit_status=None)
    except FileNotFoundError:
        return _failure(alias, "executable_missing", captured_at=captured_at, exit_status="not_started")
    except Exception:
        return _failure(alias, "runner_error", captured_at=captured_at, exit_status="not_started")

    return_code = getattr(completed, "returncode", None)
    if not isinstance(return_code, int):
        return _failure(alias, "invalid_exit_status", captured_at=captured_at, exit_status=None)
    if return_code != 0:
        return _failure(alias, "nonzero_exit", captured_at=captured_at, exit_status=return_code)
    try:
        stdout = _decode_in_memory(getattr(completed, "stdout", None))
    except UnicodeError:
        return _failure(alias, "decode_failure", captured_at=captured_at, exit_status=0)
    return sanitize_usage_output(stdout, alias, captured_at=captured_at)


def _parse_cli_args(argv: Sequence[str]) -> tuple[str | None, float]:
    if len(argv) not in {2, 4} or argv[0] != "--alias":
        return None, DEFAULT_TIMEOUT_SECONDS
    alias = argv[1]
    timeout = DEFAULT_TIMEOUT_SECONDS
    if len(argv) == 4:
        if argv[2] != "--timeout-seconds":
            return None, DEFAULT_TIMEOUT_SECONDS
        try:
            timeout = float(argv[3])
        except ValueError:
            return alias, float("nan")
    return alias, timeout


def main(argv: Sequence[str] | None = None) -> int:
    """Emit exactly one compact JSON object; stderr remains content-free."""
    alias, timeout = _parse_cli_args(list(sys.argv[1:] if argv is None else argv))
    result = run_usage_probe(alias or "", timeout_seconds=timeout)
    sys.stdout.write(json.dumps(result, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0 if result["transport_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
