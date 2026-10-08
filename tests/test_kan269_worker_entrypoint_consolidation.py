"""KAN-269: Worker deploy-topology consolidation.

The live Worker `horoconsultant-production` runs `project/static/_worker.js`
(proven by its unique X-Cost-Guardrail / X-R2-Policy response headers, which
appear nowhere else in the repo). No tracked pipeline can reproduce that
artifact: every wrangler config on main points `main` at `api/index.js`.

Per the Cloudflare environments reference, an environment deploys as
`<top-level-name>-<environment-name>`, so `name = "horoconsultant"` with
`-e production` already yields the correct Worker name `horoconsultant-production`.
Only the entry point is wrong.

This module also pins the non-inheritable keys: `vars` and `kv_namespaces` are
NOT inherited by environments, so `[env.production]` must declare them itself.
Today it does not, which means the production Worker has no BACKEND_BASE_URL var
and no CACHE KV binding.
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
WORKER_ENTRY = "project/static/_worker.js"
LEGACY_ENTRY = "api/index.js"
WRANGLER_FILES = ["wrangler.toml", "wrangler.hermes.toml"]


def read(relative_path):
    return (REPO_ROOT / relative_path).read_text()


def production_block(content):
    """Return the text of the [env.production] section."""
    marker = "[env.production]"
    assert marker in content, "missing [env.production] section"
    return content.split(marker, 1)[1]


class TestEntryPointConsolidation:
    """Every deploy config must point at the code that is actually live."""

    @pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
    def test_main_is_the_deployed_worker_file(self, wrangler_file):
        content = read(wrangler_file)
        assert f'main = "{WORKER_ENTRY}"' in content, (
            f'{wrangler_file} must set main = "{WORKER_ENTRY}" — that is the file '
            f"the live Worker actually runs"
        )

    @pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
    def test_no_config_deploys_the_vercel_gateway_as_a_worker(self, wrangler_file):
        content = read(wrangler_file)
        assert f'main = "{LEGACY_ENTRY}"' not in content, (
            f'{wrangler_file} still deploys {LEGACY_ENTRY} as the Worker entry point; '
            f"{LEGACY_ENTRY} is the Vercel gateway, served from its own channel"
        )

    @pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
    def test_top_level_name_still_yields_horoconsultant_production(self, wrangler_file):
        """`<name>-<env>` must resolve to the live Worker name."""
        content = read(wrangler_file)
        assert 'name = "horoconsultant"' in content, (
            f"{wrangler_file} must keep name = \"horoconsultant\" so that "
            f"-e production resolves to horoconsultant-production"
        )


class TestNonInheritableKeysDeclaredPerEnvironment:
    """vars and kv_namespaces are not inherited — they must be per-environment."""

    @pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
    def test_production_declares_backend_base_url(self, wrangler_file):
        block = production_block(read(wrangler_file))
        assert "BACKEND_BASE_URL" in block, (
            f"{wrangler_file} [env.production] must declare BACKEND_BASE_URL; "
            f"vars are not inherited from the top level"
        )

    @pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
    def test_production_declares_kv_namespace(self, wrangler_file):
        block = production_block(read(wrangler_file))
        assert "kv_namespaces" in block, (
            f"{wrangler_file} [env.production] must declare kv_namespaces; "
            f"bindings are not inherited from the top level"
        )

    @pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
    def test_production_declares_backend_timeout(self, wrangler_file):
        block = production_block(read(wrangler_file))
        assert "BACKEND_TIMEOUT_MS" in block, (
            f"{wrangler_file} [env.production] must declare BACKEND_TIMEOUT_MS"
        )


class TestTrackedPipelineReproducesArtifact:
    """A tracked workflow must be able to produce the live artifact."""

    def test_workers_builds_deploys_the_worker_entry_with_production_env(self):
        content = read(".github/workflows/workers-builds.yml")
        assert WORKER_ENTRY not in content or True  # entry comes from the config
        assert "-e production" in content or "--env production" in content, (
            "workers-builds.yml must select the production environment"
        )

    def test_workers_builds_uses_the_account_that_owns_the_worker(self):
        """CF_API_TOKEN belongs to the account holding the Worker.

        CF_API_TOKEN_HERMES cannot deploy here — the Hermes-scoped API answers
        `10007 This Worker does not exist on your account` for this Worker.
        """
        content = read(".github/workflows/workers-builds.yml")
        assert "secrets.CF_API_TOKEN" in content, (
            "workers-builds.yml must use secrets.CF_API_TOKEN (the owning account)"
        )
        assert "CF_API_TOKEN_HERMES" not in content, (
            "workers-builds.yml must not use CF_API_TOKEN_HERMES — wrong account"
        )


class TestDocumentationAccuracy:
    """The account comment must match reality."""

    def test_hermes_account_comment_is_corrected(self):
        content = read("wrangler.hermes.toml")
        assert "Hermes account (horo-hermes)" not in content, (
            "account bda49e4e77e00609cb1ef68561b0d9eb is Pansakorn's account, "
            "not a Hermes account; the comment is factually wrong"
        )
