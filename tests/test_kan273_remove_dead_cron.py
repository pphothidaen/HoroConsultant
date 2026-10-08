"""
KAN-273: The Worker cron targeted an endpoint that does not exist.

`scheduled()` POSTed to `<primary>/api/v1/sync`. That path is not in the backend
route table at all — the OpenAPI document lists 87 paths and none contain "sync".
`ctx.waitUntil` swallowed the 404, so the cron fired twice a day and silently did
nothing while looking healthy in the dashboard (triggers registered, invocations
succeeding).

The sync itself is not missing: `project/main.py` runs its own APScheduler job
(`midnight_gdrive_sync`, cron from `AUTO_SYNC_CRON`, gated on `AUTO_SYNC_ENABLED`)
inside the backend process. The Worker cron was a redundant duplicate pointed at
a route that was never built.

So the honest fix is to remove the dead trigger, not to invent an endpoint.

Assertions read the *parsed* TOML rather than raw text, because these files carry
commented-out reference blocks for other workers that legitimately mention crons.
"""
import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
WORKER = "project/static/_worker.js"
WRANGLER_FILES = ["wrangler.toml", "wrangler.hermes.toml"]


def read(relative_path):
    return (REPO_ROOT / relative_path).read_text()


def parsed(relative_path):
    with open(REPO_ROOT / relative_path, "rb") as handle:
        return tomllib.load(handle)


def test_worker_scheduled_does_not_call_a_nonexistent_sync_route():
    """The Worker must not POST to a route the backend does not serve."""
    content = read(WORKER)
    assert "/api/v1/sync" not in content, (
        "the Worker must not call /api/v1/sync — it is not in the backend route "
        "table, so the cron has been silently 404ing"
    )


@pytest.mark.parametrize("wrangler_file", WRANGLER_FILES)
def test_worker_declares_no_cron_triggers(wrangler_file):
    """No registered cron may exist that cannot do its job.

    The backend schedules its own sync (`midnight_gdrive_sync` in project/main.py,
    gated on AUTO_SYNC_ENABLED / AUTO_SYNC_CRON), so a Worker-side cron is a
    duplicate with nothing to call.
    """
    config = parsed(wrangler_file)
    triggers = config.get("triggers") or {}
    assert not triggers.get("crons"), (
        f"{wrangler_file} must not register cron triggers while the Worker has no "
        f"valid cron target"
    )


def test_worker_has_no_scheduled_handler():
    """With no triggers, a scheduled() handler is dead code."""
    content = read(WORKER)
    assert not re.search(r"async\s+scheduled\s*\(", content), (
        "the scheduled() handler must be removed along with the triggers"
    )


def test_backend_owns_the_sync_schedule():
    """Guard the premise: the backend really does self-schedule the sync.

    If this ever stops being true, removing the Worker cron needs revisiting.
    """
    main_py = read("project/main.py")
    assert "AUTO_SYNC_ENABLED" in main_py, "backend auto-sync gate must still exist"
    assert "midnight_gdrive_sync" in main_py, (
        "the backend's own sync job must still be scheduled — it is the reason the "
        "Worker cron is redundant"
    )
