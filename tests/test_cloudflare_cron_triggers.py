"""KAN-273: the Worker must not register a cron it cannot service.

Previously this file asserted wrangler.toml had a [triggers] section with a
midnight cron. That cron POSTed to /api/v1/sync, which the backend does not
serve — the route is absent from its 87-path OpenAPI document — so the trigger
fired twice daily and silently 404'd behind ctx.waitUntil.

The sync is owned by the backend: project/main.py registers an APScheduler job
"midnight_gdrive_sync" driven by AUTO_SYNC_CRON and gated on AUTO_SYNC_ENABLED.
The Worker cron was a redundant duplicate, so the contract is inverted here:
no triggers, and no scheduled() handler to service them.

Assertions parse the TOML rather than grepping it, because wrangler.hermes.toml
carries a commented reference block for a different worker that mentions crons.
"""
import re
from pathlib import Path

# tomllib is stdlib in Python 3.11+; tomli is the backport for 3.9-3.10
try:
    import tomllib
except ImportError:
    import tomli as tomllib

REPO_ROOT = Path(__file__).parent.parent
WRANGLER_PATH = REPO_ROOT / "wrangler.toml"
WORKER_PATH = REPO_ROOT / "project/static/_worker.js"


def parsed_wrangler():
    with open(WRANGLER_PATH, "rb") as handle:
        return tomllib.load(handle)


def read_worker():
    return WORKER_PATH.read_text()


class TestNoDeadCronTriggers:
    """The Worker must not declare a cron it cannot service."""

    def test_wrangler_file_exists(self):
        assert WRANGLER_PATH.exists(), f"wrangler.toml not found at {WRANGLER_PATH}"

    def test_no_cron_triggers_declared(self):
        """No [triggers].crons — the previous target did not exist."""
        triggers = parsed_wrangler().get("triggers") or {}
        assert not triggers.get("crons"), (
            "wrangler.toml must not register crons: the Worker has no valid cron target"
        )

    def test_worker_has_no_scheduled_handler(self):
        """With no triggers, a scheduled() handler is dead code."""
        assert not re.search(r"async\s+scheduled\s*\(", read_worker()), (
            "scheduled() must be removed along with the triggers"
        )

    def test_worker_does_not_call_the_missing_sync_route(self):
        """/api/v1/sync is not served by the backend."""
        assert "/api/v1/sync" not in read_worker(), (
            "the Worker must not call a route the backend does not serve"
        )

    def test_backend_owns_the_sync_schedule(self):
        """Premise guard: the backend really does self-schedule the sync.

        If this stops being true, removing the Worker cron needs revisiting.
        """
        main_py = (REPO_ROOT / "project/main.py").read_text()
        assert "AUTO_SYNC_ENABLED" in main_py
        assert "midnight_gdrive_sync" in main_py
