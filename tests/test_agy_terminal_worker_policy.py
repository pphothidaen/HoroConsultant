"""Pure candidate configuration contract; no enforcement or admission proof.

The new module is absent at RED baseline. Import failure is reported inside each
test as an explicit missing-interface failure, never a collection/setup error.
Builder denial order is canonical; validator accepts any duplicate-free ordering
of the exact semantic denial set, with no other configuration fields.
"""
from __future__ import annotations

import copy
import importlib
import json

import pytest

DENIES = (
    "read_file(*)", "write_file(*)", "read_url(*)", "execute_url(*)",
    "command(*)", "unsandboxed(*)", "mcp(*)",
)
CANDIDATE_BYTES = (
    b'{"permissions":{"allow":[],"deny":["read_file(*)","write_file(*)",'
    b'"read_url(*)","execute_url(*)","command(*)","unsandboxed(*)","mcp(*)"]}}'
)


def api():
    try:
        module = importlib.import_module("scripts.agy_terminal_worker_policy")
    except ModuleNotFoundError as exc:
        if exc.name != "scripts.agy_terminal_worker_policy":
            raise
        pytest.fail("CANDIDATE_POLICY_INTERFACE_MISSING: pure builder/validator not implemented")
    assert callable(getattr(module, "build_candidate_policy", None)), "CANDIDATE_BUILDER_MISSING"
    assert callable(getattr(module, "validate_candidate_policy", None)), "CANDIDATE_VALIDATOR_MISSING"
    return module


def candidate():
    return {"permissions": {"allow": [], "deny": list(DENIES)}}


def test_builder_returns_exact_candidate_and_unverified_status():
    module = api()
    assert module.POLICY_STATUS == "CANDIDATE_UNVERIFIED"
    built = module.build_candidate_policy()
    assert type(built) is dict and built == candidate()
    assert json.dumps(built, sort_keys=True, separators=(",", ":")).encode() == CANDIDATE_BYTES


def test_builder_has_no_shared_mutable_results():
    module = api()
    first, second = module.build_candidate_policy(), module.build_candidate_policy()
    first["permissions"]["allow"].append("command(*)")
    first["permissions"]["deny"].clear()
    first["unexpected"] = True
    assert second == candidate()
    assert module.build_candidate_policy() == candidate()


def test_validator_accepts_exact_policy_and_returns_independent_copy():
    module = api()
    original = candidate()
    validated = module.validate_candidate_policy(original)
    assert type(validated) is dict and validated == original
    validated["permissions"]["deny"].clear()
    validated["permissions"]["allow"].append("read_file(*)")
    assert original == candidate(), "VALIDATOR_RETURN_ALIASES_CALLER"
    assert module.validate_candidate_policy(candidate()) == candidate()


def test_validator_accepts_denial_set_in_different_order_without_mutation():
    module = api()
    original = candidate()
    original["permissions"]["deny"].reverse()
    before = copy.deepcopy(original)
    validated = module.validate_candidate_policy(original)
    assert original == before, "VALIDATOR_MUTATED_CALLER"
    assert set(validated) == {"permissions"}
    assert set(validated["permissions"]) == {"allow", "deny"}
    assert validated["permissions"]["allow"] == []
    assert sorted(validated["permissions"]["deny"]) == sorted(DENIES)


def test_every_required_denial_is_individually_mandatory():
    module = api()
    for rule in DENIES:
        value = candidate()
        value["permissions"]["deny"].remove(rule)
        with pytest.raises(ValueError):
            module.validate_candidate_policy(value)


@pytest.mark.parametrize("mutation", ["allow", "extra-deny", "missing-key", "root-key", "nested-key",
                                      "duplicate", "alias", "malformed-rule"])
def test_validator_rejects_policy_expansion_and_ambiguity_without_mutation(mutation):
    module = api()
    value = candidate()
    if mutation == "allow":
        value["permissions"]["allow"] = ["read_file(*)"]
    elif mutation == "extra-deny":
        value["permissions"]["deny"].append("unknown(*)")
    elif mutation == "missing-key":
        del value["permissions"]["allow"]
    elif mutation == "root-key":
        value["admission_pass"] = True
    elif mutation == "nested-key":
        value["permissions"]["enforcement_verified"] = True
    elif mutation == "duplicate":
        value["permissions"]["deny"].append(DENIES[0])
    elif mutation == "alias":
        value["permissions"]["deny"].append("read_file( * )")
    else:
        value["permissions"]["deny"][0] = "read_file(**)"
    before = copy.deepcopy(value)
    with pytest.raises(ValueError):
        module.validate_candidate_policy(value)
    assert value == before, "REJECTION_MUTATED_CALLER"


@pytest.mark.parametrize("value", [None, [], {"permissions": []},
                                   {"permissions": {"allow": (), "deny": list(DENIES)}},
                                   {"permissions": {"allow": [], "deny": "read_file(*)"}},
                                   {"permissions": {"allow": [], "deny": [None]}}])
def test_validator_rejects_malformed_types(value):
    module = api()
    with pytest.raises(ValueError):
        module.validate_candidate_policy(value)
