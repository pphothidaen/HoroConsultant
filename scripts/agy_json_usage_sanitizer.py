#!/usr/bin/env python3
"""Sanitize structured JSON output from AGY usage quota probe behind a fail-closed boundary.

Executes only literal `agy --output-format json -p /usage` under strict environment
normalization. In-memory output is parsed as JSON (strictly requiring root type dict).
Inspects both the top-level envelope and the inner `response` field (which contains
the slash command output). Distinguishes between per-session command token overhead
and true account quota limits/remaining balances.

If account quota metrics are found in `response` or top-level, status is `observed`.
If only session token telemetry exists without account quota limits, status is `unknown`.
Raw stdout, JSON dumps, and unapproved fields are never persisted.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence
from zoneinfo import ZoneInfo


SANITIZER_VERSION = "agy-json-usage-sanitizer-v1.4.0"
SANITIZER_VERSION_SHA256 = hashlib.sha256(SANITIZER_VERSION.encode("ascii")).hexdigest()
TIMEZONE = "Asia/Bangkok"
DEFAULT_TIMEOUT_SECONDS = 60.0
ALLOWED_COMMANDS = (
    ("agy", "--output-format", "json", "-p", "/usage"),
    ("agy", "-p", "/usage", "--output-format", "json"),
)

ALLOWLISTED_QUOTA_STEMS = frozenset(
    {
        "quota",
        "remaining",
        "limit",
        "limit_total",
        "percent",
        "percentage",
        "fraction",
        "ratio",
        "bucket",
        "category",
        "used",
        "total",
        "available",
        "reset",
        "reset_time",
        "reset_seconds",
        "window",
        "window_seconds",
        "requests",
        "tokens",
        "credits",
        "fast_queries",
        "standard_queries",
        "model_quota",
    }
)

_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+")
_PATH_RE = re.compile(
    r"(?i)(?:\b[a-z]:\\[^\r\n\t ]+|(?<![\w.])/(?:users|home|root|private|tmp|var|etc|opt)/[^\r\n\t ]+|file://|~[/\\]|\.\.[/\\]|\./)"
)
_CREDENTIAL_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|"
    r"authorization|bearer|password|passwd|cookie|session[_ -]?token|private[_ -]?key)\b"
)
_TOKEN_LIKE_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_+/=-]{32,}(?![A-Za-z0-9_+/=-]))"
    r"(?=[A-Za-z0-9_+/=-]*[A-Za-z])(?=[A-Za-z0-9_+/=-]*\d)[A-Za-z0-9_+/=-]+"
)
_SAFE_KEY_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,48}$")

_PROGRESS_BAR_CHARS = r"█▉▊▋▌▍▎▏░▒▓■□▪▫=#"
_PROGRESS_BAR_RE = re.compile(
    rf"(?i)(?:[\[(]?[{_PROGRESS_BAR_CHARS}=\-> ]{{3,}}[\])]?\s*(?P<pct>\d{{1,3}}(?:\.\d{{1,6}})?)%|(?P<pct2>\d{{1,3}}(?:\.\d{{1,6}})?)%\s*[\[(]?[{_PROGRESS_BAR_CHARS}=\-> ]{{3,}}[\])]?)"
)
_EMBEDDED_PCT_RE = re.compile(r"(?i)(?P<pct>\d{1,3}(?:\.\d{1,6})?)\s*%")
_RATIO_RE = re.compile(
    r"(?i)(?:[\[(]|\b)(?P<num>\d{1,3}(?:,\d{3})+|\d+)\s*(?:/|\bof\b)\s*(?P<den>\d{1,3}(?:,\d{3})+|\d+)(?:[\])]|\s+remaining|\s+used|\s+requests|\b)"
)
_KV_LINE_RE = re.compile(r"^(?P<key>[a-zA-Z0-9_ -]{1,40})\s*[:=]\s*(?P<val>.+)$")
_DOCUMENTED_QUOTA_FIELDS = frozenset(
    {"remaining_fraction", "remaining_percent", "remaining_ratio", "reset_time", "reset_in_seconds", "disabled"}
)
_COMMAND_BUCKET_METADATA_FIELDS = frozenset({"id", "name", "description", "window"})
_RESET_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class _SanitizeFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _timestamp() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")


def _reject_sensitive_text(text: str) -> None:
    if _EMAIL_RE.search(text):
        raise _SanitizeFailure("rejected_pii")
    if _PATH_RE.search(text):
        raise _SanitizeFailure("rejected_path")
    if _CREDENTIAL_RE.search(text) or _TOKEN_LIKE_RE.search(text):
        raise _SanitizeFailure("rejected_credential_like")


def _is_safe_bucket_label(val: str) -> bool:
    if not isinstance(val, str) or len(val) > 40:
        return False
    if any(bad in val for bad in ("/", "\\", "~", "@", ".")):
        return False
    return bool(re.fullmatch(r"^[a-zA-Z0-9_ -]+$", val))


def _clean_numeric(val: Any) -> float | int | None:
    # ``bool`` is an ``int`` subclass in Python, but it is never an
    # unambiguous quota value.
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        if any(bad in val for bad in ("/", "\\", "~", "@")):
            return None
        val_clean = val.strip().rstrip("%").replace(",", "")
        try:
            if "." in val_clean:
                return float(val_clean)
            return int(val_clean)
        except ValueError:
            return None
    return None


def _documented_quota_metric(bucket: str, value: Mapping[str, Any], source: str) -> dict[str, Any] | None:
    """Extract one explicitly unit-bearing AGY status-line quota bucket."""
    if not _is_safe_bucket_label(bucket) or not isinstance(value, Mapping):
        return None

    metric: dict[str, Any] = {"bucket": bucket, "source": source}
    fraction = value.get("remaining_fraction")
    if fraction is not None:
        fraction_num = _clean_numeric(fraction)
        if fraction_num is None or not 0 <= float(fraction_num) <= 1:
            return None
        metric["remaining_fraction"] = fraction_num

    percent = value.get("remaining_percent")
    if percent is not None:
        percent_num = _clean_numeric(percent)
        if percent_num is None or not 0 <= float(percent_num) <= 100:
            return None
        metric["remaining_percent"] = percent_num

    ratio = value.get("remaining_ratio")
    if ratio is not None:
        ratio_num = _clean_numeric(ratio)
        if ratio_num is None or not 0 <= float(ratio_num) <= 1:
            return None
        metric["remaining_ratio"] = ratio_num

    reset_time = value.get("reset_time")
    if reset_time is not None:
        if not isinstance(reset_time, str) or not _RESET_TIME_RE.fullmatch(reset_time):
            return None
        metric["reset_time"] = reset_time

    reset_seconds = value.get("reset_in_seconds")
    if reset_seconds is not None:
        reset_num = _clean_numeric(reset_seconds)
        if reset_num is None or float(reset_num) < 0:
            return None
        metric["reset_in_seconds"] = reset_num

    disabled = value.get("disabled")
    if disabled is not None:
        if not isinstance(disabled, bool):
            return None
        metric["disabled"] = disabled

    quota_fields = _DOCUMENTED_QUOTA_FIELDS & set(value)
    remaining_fields = quota_fields & {"remaining_fraction", "remaining_percent", "remaining_ratio"}
    if len(remaining_fields) != 1:
        return None
    if set(value) - _DOCUMENTED_QUOTA_FIELDS:
        return None
    return metric


def _extract_documented_quota(value: Any, source: str) -> list[dict[str, Any]]:
    """Extract only nested ``quota.<bucket>`` objects from a JSON mapping."""
    if not isinstance(value, Mapping) or not isinstance(value.get("quota"), Mapping):
        return []
    metrics: list[dict[str, Any]] = []
    for bucket, bucket_value in value["quota"].items():
        metric = _documented_quota_metric(str(bucket), bucket_value, source)
        if metric is not None:
            metrics.append(metric)
    return metrics


def _extract_command_quota(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract AGY's machine-readable command.data.groups[].buckets[] payload."""
    command = data.get("command")
    if not isinstance(command, Mapping) or not isinstance(command.get("data"), Mapping):
        return []
    groups = command["data"].get("groups")
    if not isinstance(groups, list):
        return []

    metrics: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, Mapping) or not isinstance(group.get("buckets"), list):
            continue
        for bucket in group["buckets"]:
            if not isinstance(bucket, Mapping):
                continue
            bucket_id = bucket.get("id")
            if not isinstance(bucket_id, str):
                continue
            if set(bucket) - _DOCUMENTED_QUOTA_FIELDS - _COMMAND_BUCKET_METADATA_FIELDS:
                continue
            fields = {key: bucket[key] for key in _DOCUMENTED_QUOTA_FIELDS if key in bucket}
            metric = _documented_quota_metric(bucket_id, fields, "command_data_groups")
            if metric is not None:
                metrics.append(metric)
    return metrics


def _parse_response_string_for_quota(text: str) -> list[dict[str, Any]]:
    """Parse text response body for structured quota lines (ratios, percents, buckets)."""
    metrics: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        m_kv = _KV_LINE_RE.match(line)
        if m_kv:
            k = m_kv.group("key").strip().lower()
            v = m_kv.group("val").strip()

            # Progress bar percent
            m_pb = _PROGRESS_BAR_RE.search(v)
            if m_pb:
                pct_str = m_pb.group("pct") or m_pb.group("pct2")
                try:
                    metrics.append({"bucket": k, "remaining_percent": float(pct_str), "source": "response_text"})
                    continue
                except ValueError:
                    pass

            # Ratio: e.g. 120/1500
            m_rat = _RATIO_RE.search(v)
            if m_rat:
                num_str = m_rat.group("num").replace(",", "")
                den_str = m_rat.group("den").replace(",", "")
                try:
                    num = int(num_str) if "." not in num_str else float(num_str)
                    den = int(den_str) if "." not in den_str else float(den_str)
                    metrics.append({"bucket": k, "used_or_remaining": num, "limit": den, "source": "response_text"})
                    continue
                except ValueError:
                    pass

            # Embedded percent: e.g. 80%
            m_pct = _EMBEDDED_PCT_RE.search(v)
            if m_pct:
                try:
                    metrics.append({"bucket": k, "remaining_percent": float(m_pct.group("pct")), "source": "response_text"})
                    continue
                except ValueError:
                    pass

            # Explicit documented scalar fields retain their units.
            if k in {"remaining_fraction", "remaining_ratio", "remaining_percent"}:
                num = _clean_numeric(v)
                upper = 100 if k == "remaining_percent" else 1
                if num is not None and 0 <= float(num) <= upper:
                    metrics.append({"bucket": k, k: num, "source": "response_text"})
                    continue

            # Clean numeric if key is allowlisted
            if any(stem in k for stem in ALLOWLISTED_QUOTA_STEMS):
                num = _clean_numeric(v)
                if num is not None:
                    metrics.append({"bucket": k, "value": num, "source": "response_text"})

    return metrics


def sanitize_json_usage_payload(
    raw_payload: str,
    target_cmd: Sequence[str],
    *,
    account_alias: str | None = None,
    captured_at: str | None = None,
    stream_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse in-memory JSON usage payload, inspect response body, and extract true quota metrics."""
    captured_at = captured_at or _timestamp()
    stream_meta = dict(stream_metadata or {})
    default_fp = {
        "root_type": "none",
        "top_level_keys": [],
        "key_count": 0,
        "response_type": "none",
        "has_session_overhead_usage": False,
        "has_account_quota_metrics": False,
        "account_quota_buckets_count": 0,
        "stdout_nonempty": stream_meta.get("stdout_nonempty", False),
        "stderr_nonempty": stream_meta.get("stderr_nonempty", False),
        "combined_stream_bytes": stream_meta.get("combined_stream_bytes", 0),
        "capture_boundary": "stdout_stderr_in_memory",
    }

    if not isinstance(raw_payload, str) or not raw_payload.strip():
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(target_cmd),
            "transport_status": "parse_failure:empty_payload",
            "exit_status": 0,
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": "unknown",
            "account_quota_metrics": [],
            "session_token_usage": {},
            "structural_fingerprint": default_fp,
            "required_human_review": True,
        }

    try:
        _reject_sensitive_text(raw_payload)
        text = _ANSI_RE.sub("", raw_payload).strip()
        _reject_sensitive_text(text)

        # Parse JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Check if JSON is wrapped in text lines
            json_candidate = None
            for line in text.splitlines():
                line_s = line.strip()
                if line_s.startswith("{") and line_s.endswith("}"):
                    try:
                        json_candidate = json.loads(line_s)
                        break
                    except json.JSONDecodeError:
                        continue
            if json_candidate is None:
                raise _SanitizeFailure("invalid_json_syntax")
            data = json_candidate

        # Strict requirement: root type MUST be a dict
        if not isinstance(data, dict):
            raise _SanitizeFailure("unsupported_root_json_type_requires_dict")

        top_level_keys = sorted([str(k) for k in data.keys() if _SAFE_KEY_RE.match(str(k))])

        # 1. Extract per-session command token overhead (telemetry, not quota)
        session_token_usage: dict[str, int] = {}
        if isinstance(data.get("usage"), dict):
            for tk, tv in data["usage"].items():
                if isinstance(tv, int) and _SAFE_KEY_RE.match(str(tk)):
                    session_token_usage[str(tk)] = tv

        # 2. Extract true account quota metrics from inner `response` or top-level quota keys
        account_quota_metrics: list[dict[str, Any]] = []
        account_quota_metrics.extend(_extract_documented_quota(data, "top_level_quota_schema"))
        account_quota_metrics.extend(_extract_command_quota(data))
        response_val = data.get("response")
        response_type = "none"

        if response_val is not None:
            if isinstance(response_val, str):
                response_type = "string"
                _reject_sensitive_text(response_val)
                resp_text = _ANSI_RE.sub("", response_val).strip()
                _reject_sensitive_text(resp_text)
                account_quota_metrics.extend(_parse_response_string_for_quota(resp_text))

            elif isinstance(response_val, dict):
                response_type = "dict"
                account_quota_metrics.extend(_extract_documented_quota(response_val, "response_quota_schema"))
                for rk, rv in response_val.items():
                    rk_l = str(rk).lower().strip()
                    if rk_l == "quota":
                        continue
                    if _SAFE_KEY_RE.match(rk_l) and any(stem in rk_l for stem in ALLOWLISTED_QUOTA_STEMS):
                        num = _clean_numeric(rv)
                        if num is not None:
                            account_quota_metrics.append({"bucket": rk_l, "value": num, "source": "response_dict"})

            elif isinstance(response_val, list):
                response_type = "list"
                for idx, item in enumerate(response_val):
                    if isinstance(item, dict):
                        sub_m: dict[str, Any] = {"bucket": f"item_{idx}", "source": "response_list"}
                        for rk, rv in item.items():
                            rk_l = str(rk).lower().strip()
                            if _SAFE_KEY_RE.match(rk_l) and any(stem in rk_l for stem in ALLOWLISTED_QUOTA_STEMS):
                                num = _clean_numeric(rv)
                                if num is not None:
                                    sub_m[rk_l] = num
                        if len(sub_m) > 2:
                            account_quota_metrics.append(sub_m)

        # Also check top-level keys for quota metrics (excluding 'usage' overhead)
        for key, val in data.items():
            k_str = str(key).lower().strip()
            if k_str in ("usage", "command", "conversation_id", "status", "num_turns", "duration_seconds", "response", "quota"):
                continue
            if _SAFE_KEY_RE.match(k_str) and any(stem in k_str for stem in ALLOWLISTED_QUOTA_STEMS):
                num = _clean_numeric(val)
                if num is not None:
                    account_quota_metrics.append({"bucket": k_str, "value": num, "source": "top_level_dict"})

        has_account_quota = bool(account_quota_metrics)
        quota_status = "observed" if has_account_quota else "unknown"

        fp = {
            "root_type": "dict",
            "top_level_keys": top_level_keys,
            "key_count": len(top_level_keys),
            "response_type": response_type,
            "has_session_overhead_usage": bool(session_token_usage),
            "has_account_quota_metrics": has_account_quota,
            "account_quota_buckets_count": len(account_quota_metrics),
            "stdout_nonempty": stream_meta.get("stdout_nonempty", False),
            "stderr_nonempty": stream_meta.get("stderr_nonempty", False),
            "combined_stream_bytes": stream_meta.get("combined_stream_bytes", len(raw_payload.encode("utf-8"))),
            "capture_boundary": "stdout_stderr_in_memory",
        }

        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(target_cmd),
            "transport_status": "completed",
            "exit_status": 0,
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": quota_status,
            "account_quota_metrics": account_quota_metrics,
            "session_token_usage": session_token_usage,
            "structural_fingerprint": fp,
            "required_human_review": True,
        }

    except _SanitizeFailure as failure:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(target_cmd),
            "transport_status": f"parse_failure:{failure.code}",
            "exit_status": 0,
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": "unknown",
            "account_quota_metrics": [],
            "session_token_usage": {},
            "structural_fingerprint": default_fp,
            "required_human_review": True,
        }


def run_json_usage_probe(
    cmd: Sequence[str] = ("agy", "--output-format", "json", "-p", "/usage"),
    *,
    account_alias: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Execute JSON usage command and sanitize directly in memory."""
    captured_at = _timestamp()
    cmd_tuple = tuple(cmd)
    if cmd_tuple not in ALLOWED_COMMANDS:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(cmd),
            "transport_status": "invalid_command",
            "exit_status": "not_started",
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": "unknown",
            "account_quota_metrics": [],
            "session_token_usage": {},
            "required_human_review": True,
        }

    execute = subprocess.run if runner is None else runner
    try:
        completed = execute(
            list(cmd),
            capture_output=True,
            check=False,
            shell=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(cmd),
            "transport_status": "timeout",
            "exit_status": None,
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": "unknown",
            "account_quota_metrics": [],
            "session_token_usage": {},
            "required_human_review": True,
        }
    except Exception:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(cmd),
            "transport_status": "runner_error",
            "exit_status": "not_started",
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": "unknown",
            "account_quota_metrics": [],
            "session_token_usage": {},
            "required_human_review": True,
        }

    return_code = getattr(completed, "returncode", None)
    if return_code != 0:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "account_alias": account_alias,
            "target_command": list(cmd),
            "transport_status": "nonzero_exit",
            "exit_status": return_code,
            "sanitizer_version": SANITIZER_VERSION,
            "quota_status": "unknown",
            "account_quota_metrics": [],
            "session_token_usage": {},
            "required_human_review": True,
        }

    stdout_bytes = getattr(completed, "stdout", b"") or b""
    stderr_bytes = getattr(completed, "stderr", b"") or b""
    if isinstance(stdout_bytes, str):
        stdout_bytes = stdout_bytes.encode("utf-8", errors="replace")
    if isinstance(stderr_bytes, str):
        stderr_bytes = stderr_bytes.encode("utf-8", errors="replace")

    stdout_nonempty = bool(stdout_bytes and stdout_bytes.strip())
    stderr_nonempty = bool(stderr_bytes and stderr_bytes.strip())
    combined_bytes = stdout_bytes if stdout_nonempty else stderr_bytes
    combined_text = combined_bytes.decode("utf-8", errors="replace")

    stream_meta = {
        "stdout_nonempty": stdout_nonempty,
        "stderr_nonempty": stderr_nonempty,
        "combined_stream_bytes": len(combined_bytes),
        "capture_boundary": "stdout_stderr_in_memory",
    }

    return sanitize_json_usage_payload(
        combined_text,
        cmd,
        account_alias=account_alias,
        captured_at=captured_at,
        stream_metadata=stream_meta,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    alias = None
    if "--alias" in args:
        idx = args.index("--alias")
        if idx + 1 < len(args):
            alias = args[idx + 1]

    cmd = ("agy", "--output-format", "json", "-p", "/usage")
    res = run_json_usage_probe(cmd, account_alias=alias, timeout_seconds=DEFAULT_TIMEOUT_SECONDS)
    sys.stdout.write(json.dumps(res, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0 if res["transport_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
