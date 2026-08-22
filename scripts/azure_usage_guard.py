#!/usr/bin/env python3
"""Fail-closed Azure Container Apps free-grant usage guard.

The current Azure Container Apps Consumption monthly grants are subscription
wide: 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2,000,000 requests.  This
guard deliberately stops at a configurable fraction of the smallest remaining
grant and also stops when Cost Management reports any non-zero actual cost.

Use ``--usage-json`` for a deterministic/offline decision.  Without it, the
script collects current-month Cost Management and Azure Monitor data by calling
``az`` without a shell.  Collection failures produce a DENY decision.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FREE_GRANTS = {
    "vcpu_seconds": 180_000.0,
    "gib_seconds": 360_000.0,
    "requests": 2_000_000.0,
}
DEFAULT_THRESHOLD = 0.70
COST_GUARD_TAG = "horoCostGuardSuspendedPeriod"


class UsageDecision:
    """Immutable-enough decision payload with JSON-safe serialization."""

    def __init__(
        self,
        *,
        allowed: bool,
        ratios: Mapping[str, float] | None = None,
        reasons: list[str] | tuple[str, ...] | None = None,
        period: str = "unknown",
        actual_cost: float | None = None,
        currency: str = "unknown",
    ) -> None:
        self.allowed = bool(allowed)
        self.ratios = dict(ratios or {})
        self.reasons = tuple(reasons or ())
        self.period = period
        self.actual_cost = actual_cost
        self.currency = currency

    @property
    def highest_ratio(self) -> float:
        """Return the largest grant ratio, or one for incomplete data."""
        return max(self.ratios.values(), default=1.0)

    def to_dict(self) -> dict[str, Any]:
        """Render only non-sensitive policy data for logs and artifacts."""
        return {
            "decision": "ALLOW" if self.allowed else "DENY",
            "period": self.period,
            "actual_cost": self.actual_cost,
            "currency": self.currency,
            "ratios": self.ratios,
            "highest_ratio": self.highest_ratio,
            "reasons": list(self.reasons),
        }


def _finite_nonnegative(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("value must be finite and non-negative")
    return number


def evaluate_usage(
    snapshot: Mapping[str, Any], *, threshold: float = DEFAULT_THRESHOLD
) -> UsageDecision:
    """Evaluate a normalized current-month usage snapshot.

    Invalid, stale, or incomplete data is denied rather than treated as zero.
    The threshold is inclusive: exactly 70 percent is already denied.
    """
    reasons: list[str] = []
    ratios: dict[str, float] = {}
    period = str(snapshot.get("period", "unknown"))
    currency = str(snapshot.get("currency", "unknown"))
    actual_cost: float | None = None

    try:
        threshold_value = float(threshold)
        if not 0 < threshold_value <= 1:
            raise ValueError("threshold outside (0, 1]")
    except (TypeError, ValueError):
        threshold_value = DEFAULT_THRESHOLD
        reasons.append("invalid threshold")

    current_period = datetime.now(timezone.utc).strftime("%Y-%m")
    if period != current_period:
        reasons.append(f"period is not current UTC month ({current_period})")
    if snapshot.get("complete") is not True:
        reasons.append("usage snapshot is incomplete")
    collection_errors = snapshot.get("collection_errors", [])
    if isinstance(collection_errors, list):
        reasons.extend(
            f"collection error: {str(error)[:240]}"
            for error in collection_errors
            if error
        )

    try:
        actual_cost = _finite_nonnegative(snapshot["actual_cost"])
        if actual_cost > 0:
            reasons.append("actual_cost is greater than zero")
    except (KeyError, TypeError, ValueError):
        reasons.append("actual_cost is missing or invalid")

    for key, grant in FREE_GRANTS.items():
        try:
            usage = _finite_nonnegative(snapshot[key])
        except (KeyError, TypeError, ValueError):
            reasons.append(f"{key} is missing or invalid")
            continue
        ratio = usage / grant
        ratios[key] = ratio
        if ratio >= threshold_value:
            reasons.append(
                f"{key} ratio {ratio:.6f} reached threshold {threshold_value:.6f}"
            )

    return UsageDecision(
        allowed=not reasons,
        ratios=ratios,
        reasons=reasons,
        period=period,
        actual_cost=actual_cost,
        currency=currency,
    )


def evaluate_file(
    path: Path, *, threshold: float = DEFAULT_THRESHOLD
) -> UsageDecision:
    """Read and evaluate a normalized snapshot, denying malformed JSON."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("snapshot root must be an object")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        payload = {}
    return evaluate_usage(payload, threshold=threshold)


def _run_json(
    command: list[str], runner: Callable[..., Any] = subprocess.run
) -> Any:
    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = " ".join((result.stderr or "").split())[:400]
        suffix = f": {stderr}" if stderr else ""
        raise RuntimeError(
            f"Azure CLI command failed: {command[0]} {command[1]} "
            f"(exit {result.returncode}){suffix}"
        )
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Azure CLI returned invalid JSON") from exc


def _sum_metric(metric: Mapping[str, Any], field: str) -> float:
    total = 0.0
    for series in metric.get("timeseries", []):
        for point in series.get("data", []):
            value = point.get(field)
            if value is not None:
                total += float(value)
    return total


def _memory_gib(value: Any) -> float:
    raw = str(value).strip().lower()
    if raw.endswith("gi"):
        return float(raw[:-2])
    if raw.endswith("mi"):
        return float(raw[:-2]) / 1024.0
    raise ValueError("unsupported Azure memory unit")


def _container_resources(app: Mapping[str, Any]) -> tuple[float, float]:
    containers = app["properties"]["template"]["containers"]
    cpu = 0.0
    memory = 0.0
    for container in containers:
        resources = container["resources"]
        cpu += float(resources["cpu"])
        memory += _memory_gib(resources["memory"])
    if cpu <= 0 or memory <= 0:
        raise ValueError("container resources must be positive")
    return cpu, memory


def _extract_cost(payload: Mapping[str, Any]) -> tuple[float, str]:
    properties = payload.get("properties", {})
    columns = [column.get("name") for column in properties.get("columns", [])]
    rows = properties.get("rows", [])
    cost_index = next(
        (columns.index(name) for name in ("PreTaxCost", "Cost", "totalCost") if name in columns),
        None,
    )
    currency_index = columns.index("Currency") if "Currency" in columns else None
    if cost_index is None:
        raise ValueError("Cost Management response omitted cost")
    cost = sum(float(row[cost_index]) for row in rows)
    currency = (
        str(rows[0][currency_index])
        if rows and currency_index is not None
        else "unknown"
    )
    return cost, currency


def collect_azure_usage(
    *,
    subscription: str,
    resource_group: str,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Collect a conservative subscription-wide Container Apps snapshot."""
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_iso = start.isoformat().replace("+00:00", "Z")
    end_iso = now.isoformat().replace("+00:00", "Z")
    period = now.strftime("%Y-%m")
    scope = f"/subscriptions/{subscription}/resourceGroups/{resource_group}"
    cost_body = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {"from": start_iso, "to": end_iso},
        "dataset": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {"name": "PreTaxCost", "function": "Sum"}
            },
        },
    }

    snapshot: dict[str, Any] = {
        "period": period,
        "actual_cost": None,
        "currency": "unknown",
        "vcpu_seconds": 0.0,
        "gib_seconds": 0.0,
        "requests": 0.0,
        "collection_errors": [],
        "complete": False,
    }
    try:
        cost_payload = _run_json(
            [
                "az",
                "rest",
                "--method",
                "post",
                "--url",
                f"https://management.azure.com{scope}/providers/Microsoft.CostManagement/query?api-version=2023-03-01",
                "--body",
                json.dumps(cost_body, separators=(",", ":")),
                "--only-show-errors",
                "--output",
                "json",
            ],
            runner,
        )
        snapshot["actual_cost"], snapshot["currency"] = _extract_cost(cost_payload)

        resource_ids = _run_json(
            [
                "az",
                "resource",
                "list",
                "--subscription",
                subscription,
                "--resource-type",
                "Microsoft.App/containerApps",
                "--query",
                "[].id",
                "--only-show-errors",
                "--output",
                "json",
            ],
            runner,
        )
        if not isinstance(resource_ids, list):
            raise TypeError("container app resource list is not an array")

        for resource_id in resource_ids:
            app = _run_json(
                [
                    "az",
                    "containerapp",
                    "show",
                    "--ids",
                    str(resource_id),
                    "--only-show-errors",
                    "--output",
                    "json",
                ],
                runner,
            )
            cpu, memory = _container_resources(app)
            metrics = _run_json(
                [
                    "az",
                    "monitor",
                    "metrics",
                    "list",
                    "--resource",
                    str(resource_id),
                    "--metric",
                    "Replicas",
                    "Requests",
                    "--start-time",
                    start_iso,
                    "--end-time",
                    end_iso,
                    "--interval",
                    "PT1H",
                    "--aggregation",
                    "Average",
                    "Total",
                    "--only-show-errors",
                    "--output",
                    "json",
                ],
                runner,
            )
            values = metrics.get("value", [])
            by_name = {
                item.get("name", {}).get("value"): item
                for item in values
                if isinstance(item, dict)
            }
            if "Replicas" not in by_name or "Requests" not in by_name:
                raise ValueError("Azure Monitor response omitted required metrics")
            replica_hours = _sum_metric(by_name["Replicas"], "average")
            snapshot["vcpu_seconds"] += replica_hours * 3600.0 * cpu
            snapshot["gib_seconds"] += replica_hours * 3600.0 * memory
            snapshot["requests"] += _sum_metric(by_name["Requests"], "total")

        snapshot["complete"] = True
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        snapshot["collection_errors"].append(str(exc))
        snapshot["complete"] = False
    return snapshot


def enforce_decision(
    decision: UsageDecision,
    *,
    resource_group: str,
    app_name: str,
    subscription: str | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> None:
    """Disable denied ingress and mark guard-owned suspensions when possible."""
    if decision.allowed:
        return
    command = [
        "az",
        "containerapp",
        "ingress",
        "disable",
        "--resource-group",
        resource_group,
        "--name",
        app_name,
        "--only-show-errors",
    ]
    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("failed to disable Azure Container App ingress")
    if subscription:
        resource_id = (
            f"/subscriptions/{subscription}/resourceGroups/{resource_group}"
            f"/providers/Microsoft.App/containerApps/{app_name}"
        )
        tag_result = runner(
            [
                "az",
                "tag",
                "update",
                "--resource-id",
                resource_id,
                "--operation",
                "Merge",
                "--tags",
                f"{COST_GUARD_TAG}={decision.period}",
                "--only-show-errors",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if tag_result.returncode != 0:
            raise RuntimeError("ingress disabled but suspension tag could not be recorded")


def resume_after_reset(
    decision: UsageDecision,
    *,
    subscription: str,
    resource_group: str,
    app_name: str,
    runner: Callable[..., Any] = subprocess.run,
) -> bool:
    """Re-enable only a guard-tagged suspension from an earlier UTC month."""
    if not decision.allowed:
        return False
    resource_id = (
        f"/subscriptions/{subscription}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.App/containerApps/{app_name}"
    )
    tags_payload = _run_json(
        [
            "az",
            "tag",
            "list",
            "--resource-id",
            resource_id,
            "--only-show-errors",
            "--output",
            "json",
        ],
        runner,
    )
    tags = tags_payload.get("properties", {}).get("tags") or {}
    suspended_period = tags.get(COST_GUARD_TAG)
    if not suspended_period or suspended_period == decision.period:
        return False

    enable_result = runner(
        [
            "az",
            "containerapp",
            "ingress",
            "enable",
            "--resource-group",
            resource_group,
            "--name",
            app_name,
            "--type",
            "external",
            "--target-port",
            "8000",
            "--transport",
            "auto",
            "--only-show-errors",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if enable_result.returncode != 0:
        raise RuntimeError("failed to resume Azure Container App ingress")
    delete_result = runner(
        [
            "az",
            "tag",
            "update",
            "--resource-id",
            resource_id,
            "--operation",
            "Delete",
            "--tags",
            f"{COST_GUARD_TAG}={suspended_period}",
            "--only-show-errors",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if delete_result.returncode != 0:
        raise RuntimeError("ingress resumed but suspension tag could not be cleared")
    return True


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usage-json", type=Path)
    parser.add_argument(
        "--subscription", default=os.getenv("AZURE_SUBSCRIPTION_ID", "")
    )
    parser.add_argument(
        "--resource-group",
        default=os.getenv("AZURE_RESOURCE_GROUP", "rg-horoconsult"),
    )
    parser.add_argument(
        "--app-name",
        default=os.getenv("AZURE_CONTAINER_APP", "horoconsult-env-new"),
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--enforce", action="store_true")
    parser.add_argument("--resume-after-reset", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.usage_json:
        decision = evaluate_file(args.usage_json, threshold=args.threshold)
    elif args.subscription:
        snapshot = collect_azure_usage(
            subscription=args.subscription,
            resource_group=args.resource_group,
        )
        decision = evaluate_usage(snapshot, threshold=args.threshold)
    else:
        decision = evaluate_usage({}, threshold=args.threshold)

    print(json.dumps(decision.to_dict(), sort_keys=True, separators=(",", ":")))
    if args.enforce:
        if decision.allowed and args.resume_after_reset and args.subscription:
            resume_after_reset(
                decision,
                subscription=args.subscription,
                resource_group=args.resource_group,
                app_name=args.app_name,
            )
        elif not decision.allowed:
            enforce_decision(
                decision,
                subscription=args.subscription or None,
                resource_group=args.resource_group,
                app_name=args.app_name,
            )
    return 0 if decision.allowed else 3


if __name__ == "__main__":
    sys.exit(main())
