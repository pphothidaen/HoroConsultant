#!/usr/bin/env python3
"""Fail closed when the supported AGY alias contract is changed partially."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIRED_AGY_ALIASES = ("agy1", "agy2", "agy3", "agy4")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        loaded = json.load(source)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.relative_to(ROOT_DIR)} must contain a JSON object")
    return loaded


def _load_guard() -> ModuleType:
    path = ROOT_DIR / ".agents" / "hooks" / "full_capacity_guard.py"
    spec = importlib.util.spec_from_file_location("alias_contract_capacity_guard", path)
    if spec is None or spec.loader is None:
        raise ValueError("unable to load .agents/hooks/full_capacity_guard.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect_exact(label: str, actual: object, expected: object, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label} must be {expected!r}, found {actual!r}")


def main() -> int:
    errors: list[str] = []
    expected_list = list(REQUIRED_AGY_ALIASES)
    config = _load_json(ROOT_DIR / ".agents" / "config" / "full_capacity_guard.v2.json")
    _expect_exact("config provider_aliases", config.get("provider_aliases"), expected_list, errors)

    guard = _load_guard()
    _expect_exact("guard EXPECTED_ALIASES", getattr(guard, "EXPECTED_ALIASES", None), REQUIRED_AGY_ALIASES, errors)
    governed = getattr(guard, "GOVERNED_ALIASES", frozenset())
    if not set(REQUIRED_AGY_ALIASES).issubset(governed):
        errors.append("guard GOVERNED_ALIASES must include every AGY alias")

    schema = _load_json(ROOT_DIR / ".agents" / "schemas" / "full-capacity-governance-v2.schema.json")
    defs = schema.get("$defs", {})
    try:
        _expect_exact(
            "schema provider authorization AGY aliases",
            [alias for alias in defs["providerAuthorization"]["properties"]["account_alias"]["enum"] if alias.startswith("agy")],
            expected_list,
            errors,
        )
        _expect_exact(
            "schema dispatch AGY aliases",
            [alias for alias in defs["dispatch"]["properties"]["execution_alias"]["enum"] if alias.startswith("agy")],
            expected_list,
            errors,
        )
        _expect_exact(
            "schema alias evaluation aliases",
            defs["aliasEvaluation"]["properties"]["alias"]["enum"],
            expected_list,
            errors,
        )
        fairness = defs["fairness"]["properties"]["last_served_sequence"]
        _expect_exact("schema fairness required aliases", fairness["required"], expected_list, errors)
        _expect_exact("schema fairness property aliases", list(fairness["properties"]), expected_list, errors)
        evaluations = defs["governanceRecord"]["properties"]["alias_evaluations"]
        _expect_exact("schema alias_evaluations minItems", evaluations["minItems"], len(expected_list), errors)
        _expect_exact("schema alias_evaluations maxItems", evaluations["maxItems"], len(expected_list), errors)
        prefixes = [item["allOf"][1]["properties"]["alias"]["const"] for item in evaluations["prefixItems"]]
        _expect_exact("schema alias_evaluations order", prefixes, expected_list, errors)
    except (KeyError, TypeError, IndexError) as exc:
        errors.append(f"schema alias contract path is missing or malformed: {exc}")

    fixture = (ROOT_DIR / "project" / "tests" / "test_full_capacity_governance.py").read_text(encoding="utf-8")
    for required_fixture in (
        "{alias: None for alias in guard.EXPECTED_ALIASES}",
        "{alias: 0 for alias in guard.EXPECTED_ALIASES}",
    ):
        if required_fixture not in fixture:
            errors.append(f"capacity fixture must derive aliases from guard.EXPECTED_ALIASES: {required_fixture}")

    if errors:
        for error in errors:
            print(f"[ERROR] alias contract: {error}")
        return 1
    print(f"[OK] alias contract: {','.join(REQUIRED_AGY_ALIASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
