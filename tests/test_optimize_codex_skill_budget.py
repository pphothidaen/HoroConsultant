import json
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.optimize_codex_skill_budget import (
    account_homes,
    apply_skill_policy,
    configured_skill_states,
    policy_paths,
)
from scripts import sync_codex_account_configs as sync


SHORTENED_DESCRIPTION_WARNING = (
    "Skill descriptions were shortened to fit the skills context budget"
)


def _write_canonical_role(agents_dir: Path, role: str, tools: list[str]) -> None:
    role_dir = agents_dir / role
    role_dir.mkdir(parents=True, exist_ok=True)
    (role_dir / "agent.json").write_text(
        json.dumps(
            {
                "name": role,
                "model": "gpt-test",
                "reasoning_effort": "medium",
                "tools": tools,
            }
        ),
        encoding="utf-8",
    )


def _write_skill_source(skills_dir: Path, skill: str) -> Path:
    source = skills_dir / skill / "SKILL.md"
    source.parent.mkdir(parents=True)
    source.write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")
    return source


def _plugin_enabled(config_text: str, plugin: str) -> bool:
    return tomllib.loads(config_text)["plugins"][plugin]["enabled"]


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


def test_discovered_remote_curated_plugins_are_disabled_except_superpowers(tmp_path):
    cache_root = tmp_path / "cache" / "openai-curated-remote"
    for plugin in ("app-media-shaped", "arbitrary-analysis", "superpowers"):
        (cache_root / plugin / "1.0.0").mkdir(parents=True)

    media_plugin = "app-media-shaped@openai-curated-remote"
    analysis_plugin = "arbitrary-analysis@openai-curated-remote"
    config_only_plugin = "config-only@openai-curated-remote"
    original = "\n".join(
        (
            f'[plugins."{media_plugin}"]\nenabled = true',
            f'[plugins."{analysis_plugin}"]\nenabled = true',
            f'[plugins."{config_only_plugin}"]\nenabled = true',
            '[plugins."superpowers"]\nenabled = true',
            "",
        )
    )

    discovered = sync.discover_remote_curated_plugins([cache_root], original)

    assert {
        media_plugin,
        analysis_plugin,
        config_only_plugin,
        "superpowers",
    } <= discovered

    updated = sync.apply_remote_curated_plugin_policy(original, discovered)

    assert _plugin_enabled(updated, media_plugin) is False
    assert _plugin_enabled(updated, analysis_plugin) is False
    assert _plugin_enabled(updated, config_only_plugin) is False
    assert _plugin_enabled(updated, "superpowers") is True


def test_preserved_browser_and_canonical_horo_skills_are_not_disabled(tmp_path):
    skill_source = _write_skill_source(tmp_path / "skills", "ui-visual-auditor")
    browser_plugins = (
        "browser@openai-bundled",
        "chrome@openai-bundled",
        "computer-use@openai-bundled",
        "unified-computer-use@openai-bundled",
    )
    original = "\n".join(
        [
            *(f'[plugins."{plugin}"]\nenabled = true' for plugin in browser_plugins),
            '[plugins."superpowers"]\nenabled = true',
            "[[skills.config]]",
            f'path = "{skill_source}"',
            "enabled = true",
            "",
        ]
    )

    discovered = sync.discover_remote_curated_plugins([], original)
    disabled = sync.remote_curated_plugins_to_disable(discovered)
    updated = sync.apply_remote_curated_plugin_policy(original, discovered)

    assert disabled.isdisjoint(browser_plugins)
    assert "superpowers" not in disabled
    assert all(_plugin_enabled(updated, plugin) is True for plugin in browser_plugins)
    assert _plugin_enabled(updated, "superpowers") is True
    assert str(skill_source) not in disabled
    assert tomllib.loads(updated)["skills"]["config"][0]["enabled"] is True


def test_profile_bindings_are_derived_from_canonical_agent_json_and_skill_sources(tmp_path):
    agents_dir = tmp_path / "agents"
    skills_dir = tmp_path / "skills"
    _write_canonical_role(agents_dir, "qa_fixture", ["qa-skill", "visual-skill"])
    qa_source = _write_skill_source(skills_dir, "qa-skill")
    visual_source = _write_skill_source(skills_dir, "visual-skill")

    profiles = sync.derive_role_profiles(agents_dir, skills_dir)

    assert profiles["qa_fixture"].bound_skill_paths == (str(qa_source), str(visual_source))

    _write_canonical_role(agents_dir, "qa_fixture", ["visual-skill"])
    changed_profiles = sync.derive_role_profiles(agents_dir, skills_dir)
    assert changed_profiles["qa_fixture"].bound_skill_paths == (str(visual_source),)

    _write_canonical_role(agents_dir, "broken_fixture", ["missing-skill"])
    with pytest.raises(ValueError, match="missing-skill"):
        sync.derive_role_profiles(agents_dir, skills_dir)


def test_generated_profile_is_non_activating_until_new_session_launch(tmp_path, monkeypatch):
    agents_dir = tmp_path / "agents"
    skills_dir = tmp_path / "skills"
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    _write_canonical_role(agents_dir, "qa_fixture", ["qa-skill"])
    skill_source = _write_skill_source(skills_dir, "qa-skill")
    base_config = profile_dir / "config.toml"
    original_base_config = '[plugins."app-optional@openai-curated-remote"]\nenabled = true\n'
    base_config.write_text(original_base_config, encoding="utf-8")

    def codex_must_not_run(*args, **kwargs):
        raise AssertionError("profile generation must not launch Codex or activate a session")

    monkeypatch.setattr(sync.subprocess, "run", codex_must_not_run)

    generated = sync.generate_role_profiles(profile_dir, agents_dir, skills_dir)
    profile_path = profile_dir / "qa_fixture.config.toml"

    assert generated == [profile_path]
    assert profile_path.is_file()
    assert profile_path.name == "qa_fixture.config.toml"
    assert base_config.read_text(encoding="utf-8") == original_base_config
    profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    assert profile["skills"]["config"] == [{"path": str(skill_source), "enabled": True}]


@pytest.mark.parametrize(
    ("stdout", "stderr", "returncode", "expected_reason"),
    (
        ("", "codex unavailable", 1, "measurement"),
        ("not-json", "", 0, "measurement"),
        (json.dumps([{ "content": [{"text": "no skills here"}]}]), "", 0, "measurement"),
        (
            json.dumps(
                [
                    {
                        "content": [
                            {
                                "text": (
                                    "<skills_instructions>\n"
                                    f"{SHORTENED_DESCRIPTION_WARNING}\n"
                                    "</skills_instructions>"
                                )
                            }
                        ]
                    }
                ]
            ),
            "",
            0,
            SHORTENED_DESCRIPTION_WARNING,
        ),
    ),
)
def test_budget_measurement_failure_or_shortening_warning_is_not_zero_zero(
    monkeypatch, stdout, stderr, returncode, expected_reason
):
    monkeypatch.setattr(
        sync.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=stdout, stderr=stderr, returncode=returncode
        ),
    )

    result = sync.measure_prompt_budget("default")

    assert result.prompt_chars is None
    assert result.truncated_skills == 0
    assert (result.prompt_chars, result.truncated_skills) != (0, 0)
    assert result.measurement_error
    assert expected_reason in result.measurement_error


@pytest.mark.parametrize(
    ("measurement", "expected_reason"),
    (
        (SimpleNamespace(prompt_chars=None, truncated_skills=0, measurement_error="command failed"), "command failed"),
        (SimpleNamespace(prompt_chars=8001, truncated_skills=0, measurement_error=None), "over budget"),
        (SimpleNamespace(prompt_chars=7999, truncated_skills=1, measurement_error=None), "truncated"),
        (
            SimpleNamespace(
                prompt_chars=7999,
                truncated_skills=0,
                measurement_error=SHORTENED_DESCRIPTION_WARNING,
            ),
            SHORTENED_DESCRIPTION_WARNING,
        ),
    ),
)
def test_check_account_config_rejects_unmeasured_over_budget_truncated_or_shortened_prompt(
    tmp_path, monkeypatch, measurement, expected_reason
):
    config_path = tmp_path / "config.toml"
    config_path.write_text('model = "gpt-test"\n', encoding="utf-8")
    monkeypatch.setattr(sync, "measure_prompt_budget", lambda *args, **kwargs: measurement)

    status = sync.check_account_config("default", config_path, check_budget=True)

    assert status.is_ok is False
    assert status.measurement_error
    assert expected_reason in status.measurement_error


def test_main_check_requires_all_four_expected_accounts(tmp_path, monkeypatch):
    account_configs = {
        name: tmp_path / name / "config.toml"
        for name in ("default", "codex1", "codex2", "codex3")
    }
    for name, path in account_configs.items():
        if name != "codex3":
            path.parent.mkdir(parents=True)
            path.write_text('model = "gpt-test"\n', encoding="utf-8")

    checked: list[tuple[str, bool]] = []

    def fake_check(name, path, check_budget=False):
        checked.append((name, check_budget))
        return SimpleNamespace(
            exists=path.exists(),
            missing_disabled_skills=[],
            missing_disabled_plugins=[],
            missing_profiles=[],
            prompt_chars=8000 if path.exists() else None,
            truncated_skills=0,
            measurement_error=None if path.exists() else "missing config",
            is_ok=path.exists(),
        )

    monkeypatch.setattr(sync, "ACCOUNT_CONFIGS", account_configs)
    monkeypatch.setattr(sync, "check_account_config", fake_check)
    monkeypatch.setattr(sys, "argv", ["sync_codex_account_configs.py", "--check", "--budget"])

    assert sync.main() == 1
    assert checked == [(name, True) for name in account_configs]

    missing_path = account_configs["codex3"]
    missing_path.parent.mkdir(parents=True)
    missing_path.write_text('model = "gpt-test"\n', encoding="utf-8")
    checked.clear()

    assert sync.main() == 0
    assert checked == [(name, True) for name in account_configs]


def test_check_rejects_missing_stale_or_malformed_profiles_and_canonical_source_errors(
    tmp_path, monkeypatch
):
    agents_dir = tmp_path / "agents"
    skills_dir = tmp_path / "skills"
    profile_dir = tmp_path / "account"
    profile_dir.mkdir()
    _write_canonical_role(agents_dir, "qa_fixture", ["qa-skill"])
    _write_skill_source(skills_dir, "qa-skill")
    config_path = profile_dir / "config.toml"
    config_path.write_text('model = "gpt-test"\n', encoding="utf-8")

    monkeypatch.setattr(sync, "CANONICAL_AGENTS_DIR", agents_dir)
    monkeypatch.setattr(sync, "CANONICAL_SKILLS_DIR", skills_dir)
    monkeypatch.setattr(sync, "get_expected_disabled_skills", lambda name: [])
    monkeypatch.setattr(sync, "_remote_cache_roots", lambda account_home: [])

    expected_profile = sync.render_role_profile(
        sync.derive_role_profiles(agents_dir, skills_dir)["qa_fixture"]
    )
    profile_path = profile_dir / "qa_fixture.config.toml"
    profile_path.write_text(expected_profile, encoding="utf-8")
    assert sync.check_account_config("default", config_path).is_ok is True

    profile_path.write_text(expected_profile.replace("enabled = true", "enabled = false"), encoding="utf-8")
    assert sync.check_account_config("default", config_path).is_ok is False

    profile_path.write_text("not valid = [toml\n", encoding="utf-8")
    assert sync.check_account_config("default", config_path).is_ok is False

    profile_path.unlink()
    assert sync.check_account_config("default", config_path).is_ok is False

    _write_canonical_role(agents_dir, "qa_fixture", ["missing-skill"])
    source_error = sync.check_account_config("default", config_path)
    assert source_error.is_ok is False
    assert "missing-skill" in (source_error.measurement_error or "")


@pytest.mark.parametrize(
    "original",
    (
        'plugins = { "app-inline@openai-curated-remote" = { enabled = true } }\n',
        'plugins."app-dotted@openai-curated-remote".enabled = true\n',
    ),
)
def test_remote_plugin_policy_reparses_or_fails_before_writing_alternate_toml_registration(original):
    discovered = sync.discover_remote_curated_plugins([], original)

    try:
        updated = sync.apply_remote_curated_plugin_policy(original, discovered)
    except tomllib.TOMLDecodeError:
        return

    parsed = tomllib.loads(updated)
    for plugin in sync.remote_curated_plugins_to_disable(discovered):
        assert parsed["plugins"][plugin]["enabled"] is False
    assert sync.apply_remote_curated_plugin_policy(updated, discovered) == updated


def test_rendered_profiles_contain_only_canonical_skill_bindings():
    rendered = sync.render_role_profile(
        sync.RoleProfile(
            name="qa_fixture",
            model="legacy-model-must-not-propagate",
            reasoning_effort="high",
            bound_skill_paths=("/canonical/qa-skill/SKILL.md",),
        )
    )

    parsed = tomllib.loads(rendered)

    assert set(parsed) == {"skills"}
    assert "model" not in rendered
    assert "model_reasoning_effort" not in rendered
    assert parsed["skills"]["config"] == [
        {"path": "/canonical/qa-skill/SKILL.md", "enabled": True}
    ]


def test_real_canonical_agent_corpus_derives_all_role_profiles():
    profiles = sync.derive_role_profiles(
        sync.CANONICAL_AGENTS_DIR, sync.CANONICAL_SKILLS_DIR
    )

    assert profiles
    assert profiles["prediction_validator"].bound_skill_paths == (
        str(
            sync.CANONICAL_SKILLS_DIR
            / "metaphysical-hitl-scope-gate"
            / "SKILL.md"
        ),
        str(sync.CANONICAL_SKILLS_DIR / "qa-regression-provenance" / "SKILL.md"),
        str(sync.CANONICAL_SKILLS_DIR / "bazi-calculator" / "SKILL.md"),
        str(sync.CANONICAL_SKILLS_DIR / "rag-search" / "SKILL.md"),
    )


@pytest.mark.parametrize(
    "measurement",
    (
        SimpleNamespace(prompt_chars="8000", truncated_skills=0, measurement_error=None),
        SimpleNamespace(prompt_chars=8000, truncated_skills="0", measurement_error=None),
        SimpleNamespace(prompt_chars=float("nan"), truncated_skills=0, measurement_error=None),
        SimpleNamespace(prompt_chars=True, truncated_skills=0, measurement_error=None),
    ),
)
def test_check_account_config_rejects_nonnumeric_or_nonintegral_measurement_values(
    tmp_path, monkeypatch, measurement
):
    config_path = tmp_path / "config.toml"
    config_path.write_text('model = "gpt-test"\n', encoding="utf-8")
    monkeypatch.setattr(sync, "get_expected_disabled_skills", lambda name: [])
    monkeypatch.setattr(sync, "_canonical_role_names", lambda: [])
    monkeypatch.setattr(sync, "measure_prompt_budget", lambda *args, **kwargs: measurement)

    status = sync.check_account_config("default", config_path, check_budget=True)

    assert status.is_ok is False
    assert "numeric" in (status.measurement_error or "").lower()


def test_remote_plugin_policy_is_idempotent_for_already_disabled_stale_cache_registration(tmp_path):
    cache_root = tmp_path / "cache" / "openai-curated-remote"
    cache_root.mkdir(parents=True)
    plugin = "stale-cache-registration@openai-curated-remote"
    (cache_root / "stale-cache-registration" / "1.0.0").mkdir(parents=True)
    original = f'[plugins."{plugin}"]\nenabled = false\n'

    discovered = sync.discover_remote_curated_plugins([cache_root], original)
    updated = sync.apply_remote_curated_plugin_policy(original, discovered)

    assert updated == original
    assert updated.count(f'[plugins."{plugin}"]') == 1
    assert sync.apply_remote_curated_plugin_policy(updated, discovered) == original


def test_budget_measurement_rejects_unclosed_skills_instructions_boundary(monkeypatch):
    payload = json.dumps(
        [
            {
                "content": [
                    {
                        "text": (
                            "<skills_instructions>\n"
                            "- incomplete skill metadata must never be accepted\n"
                        )
                    }
                ]
            }
        ]
    )
    monkeypatch.setattr(
        sync.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=payload, stderr="", returncode=0
        ),
    )

    result = sync.measure_prompt_budget("default")

    assert result.prompt_chars is None
    assert result.truncated_skills == 0
    assert result.measurement_error
    assert any(
        marker in result.measurement_error.lower()
        for marker in ("malformed", "boundary", "closing", "missing")
    )


def test_canonical_profile_derivation_rejects_empty_sources_and_zero_profile_check_false_green(
    tmp_path, monkeypatch
):
    absent_agents_dir = tmp_path / "absent-agents"
    empty_agents_dir = tmp_path / "empty-agents"
    empty_agents_dir.mkdir()
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    def derivation_error(agents_dir: Path) -> str | None:
        try:
            sync.derive_role_profiles(agents_dir, skills_dir)
        except ValueError as error:
            return str(error)
        return None

    absent_error = derivation_error(absent_agents_dir)
    empty_error = derivation_error(empty_agents_dir)

    account_dir = tmp_path / "account"
    account_dir.mkdir()
    config_path = account_dir / "config.toml"
    config_path.write_text('model = "gpt-test"\n', encoding="utf-8")
    monkeypatch.setattr(sync, "CANONICAL_AGENTS_DIR", empty_agents_dir)
    monkeypatch.setattr(sync, "CANONICAL_SKILLS_DIR", skills_dir)
    monkeypatch.setattr(sync, "get_expected_disabled_skills", lambda name: [])
    monkeypatch.setattr(sync, "_remote_cache_roots", lambda account_home: [])

    status = sync.check_account_config("default", config_path)

    assert absent_error
    assert empty_error
    assert status.is_ok is False
    assert "canonical" in (status.measurement_error or "").lower()


@pytest.mark.parametrize(
    ("directory_name", "declared_name"),
    (
        ("bad.role", "bad.role"),
        ("fixture", "../escape"),
        ("fixture", "nested/role"),
        ("fixture", "nested\\role"),
        ("fixture", "."),
        ("fixture", ".."),
        ("fixture", "/absolute-role"),
    ),
)
def test_profile_derivation_rejects_unsafe_canonical_role_directories_and_names(
    tmp_path, directory_name, declared_name
):
    agents_dir = tmp_path / "agents"
    skills_dir = tmp_path / "skills"
    _write_canonical_role(agents_dir, directory_name, ["safe-skill"])
    _write_skill_source(skills_dir, "safe-skill")
    agent_json = agents_dir / directory_name / "agent.json"
    agent = json.loads(agent_json.read_text(encoding="utf-8"))
    agent["name"] = declared_name
    agent_json.write_text(json.dumps(agent), encoding="utf-8")

    with pytest.raises(ValueError):
        sync.derive_role_profiles(agents_dir, skills_dir)


@pytest.mark.parametrize(
    "unsafe_tool",
    (
        "../outside-skill",
        "nested/skill",
        "nested\\skill",
        ".",
        "..",
        "__absolute_tool__",
    ),
)
def test_profile_derivation_rejects_unsafe_tool_identifiers_before_profile_write(
    tmp_path, unsafe_tool
):
    agents_dir = tmp_path / "agents"
    skills_dir = tmp_path / "skills"
    profile_dir = tmp_path / "profiles"
    agents_dir.mkdir()
    skills_dir.mkdir()
    profile_dir.mkdir()
    tool = str(tmp_path / "absolute-skill") if unsafe_tool == "__absolute_tool__" else unsafe_tool
    _write_canonical_role(agents_dir, "qa_fixture", [tool])
    unsafe_source = skills_dir / tool / "SKILL.md"
    unsafe_source.parent.mkdir(parents=True, exist_ok=True)
    unsafe_source.write_text("---\nname: unsafe\n---\n", encoding="utf-8")

    with pytest.raises(ValueError):
        sync.generate_role_profiles(profile_dir, agents_dir, skills_dir)

    assert list(profile_dir.iterdir()) == []


def test_profile_derivation_accepts_slugged_role_and_tool_with_contained_skill_path(tmp_path):
    agents_dir = tmp_path / "agents"
    skills_dir = tmp_path / "skills"
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    _write_canonical_role(agents_dir, "qa-fixture_2", ["qa-skill_2"])
    skill_source = _write_skill_source(skills_dir, "qa-skill_2")

    profiles = sync.derive_role_profiles(agents_dir, skills_dir)
    generated = sync.generate_role_profiles(profile_dir, agents_dir, skills_dir)

    assert profiles["qa-fixture_2"].bound_skill_paths == (str(skill_source.resolve()),)
    assert Path(profiles["qa-fixture_2"].bound_skill_paths[0]).is_relative_to(
        skills_dir.resolve()
    )
    assert generated == [profile_dir / "qa-fixture_2.config.toml"]
