import tomllib
from pathlib import Path

from scripts.optimize_codex_skill_budget import (
    account_homes,
    apply_skill_policy,
    configured_skill_states,
    policy_paths,
)


def test_apply_skill_policy_preserves_config_and_is_idempotent():
    existing_path = "/tmp/existing/SKILL.md"
    new_path = "/tmp/new/SKILL.md"
    original = (
        'model = "gpt-test"\n\n'
        "[[skills.config]]\n"
        f'path = "{existing_path}"\n'
        "enabled = false\n"
    )

    updated = apply_skill_policy(original, [existing_path, new_path])
    parsed = tomllib.loads(updated)

    assert parsed["model"] == "gpt-test"
    assert configured_skill_states(updated) == {
        existing_path: False,
        new_path: False,
    }
    assert apply_skill_policy(updated, [existing_path, new_path]) == updated


def test_apply_skill_policy_turns_an_existing_enabled_entry_off():
    skill_path = "/tmp/unused/SKILL.md"
    original = (
        "[[skills.config]]\n"
        f'path = "{skill_path}"\n'
        "enabled = true\n"
    )

    updated = apply_skill_policy(original, [skill_path])

    assert configured_skill_states(updated) == {skill_path: False}
    assert updated.count(skill_path) == 1


def test_apply_skill_policy_handles_missing_enabled_without_shifting_later_blocks():
    first_path = "/tmp/first/SKILL.md"
    second_path = "/tmp/second/SKILL.md"
    original = (
        "[[skills.config]]\n"
        f'path = "{first_path}"\n\n'
        "[[skills.config]]\n"
        f'path = "{second_path}"\n'
        "enabled = true\n"
    )

    updated = apply_skill_policy(original, [first_path, second_path])

    assert configured_skill_states(updated) == {
        first_path: False,
        second_path: False,
    }


def test_account_homes_discovers_every_configured_alias(tmp_path):
    default_home = tmp_path / ".codex"
    account_root = tmp_path / "accounts"
    default_home.mkdir()
    (default_home / "config.toml").touch()
    for name in ("account1", "account4"):
        home = account_root / name
        home.mkdir(parents=True)
        (home / "config.toml").touch()
    (account_root / "not-an-account").mkdir()

    discovered = account_homes(default_home=default_home, account_root=account_root)

    assert discovered == [
        ("default", default_home),
        ("codex1", account_root / "account1"),
        ("codex4", account_root / "account4"),
    ]


def test_policy_paths_disables_optional_system_skills_for_lean_aliases(tmp_path):
    account_home = tmp_path / "account1"

    paths = set(policy_paths(account_home, Path("/workspace")))

    assert {
        str(account_home / "skills/.system/imagegen/SKILL.md"),
        str(account_home / "skills/.system/openai-docs/SKILL.md"),
        str(account_home / "skills/.system/plugin-creator/SKILL.md"),
        str(account_home / "skills/.system/skill-creator/SKILL.md"),
        str(account_home / "skills/.system/skill-installer/SKILL.md"),
    } <= paths
