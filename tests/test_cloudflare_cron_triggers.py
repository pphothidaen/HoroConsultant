import pytest
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"


def read_wrangler():
    """Read wrangler.toml content."""
    return WRANGLER_PATH.read_text()


class TestCronTriggers:
    """Test that wrangler.toml has cron triggers for scheduled sync."""

    def test_wrangler_file_exists(self):
        """wrangler.toml must exist."""
        assert WRANGLER_PATH.exists(), f"wrangler.toml not found at {WRANGLER_PATH}"

    def test_triggers_section_exists(self):
        """wrangler.toml must have [triggers] section."""
        content = read_wrangler()
        assert "[triggers]" in content, "Missing [triggers] section in wrangler.toml"

    def test_cron_triggers_defined(self):
        """wrangler.toml must define cron triggers."""
        content = read_wrangler()
        assert "crons" in content, "Missing crons definition in [triggers]"

    def test_midnight_sync_cron_exists(self):
        """wrangler.toml must have a midnight cron trigger (0 0 * * *)."""
        content = read_wrangler()
        assert "0 0 * * *" in content, "Missing midnight cron trigger (0 0 * * *) in wrangler.toml"

    def test_midnight_sync_cron_is_quoted(self):
        """Cron triggers must be quoted strings in the crons array."""
        content = read_wrangler()
        assert '"0 0 * * *"' in content, "Midnight cron trigger must be a quoted string"
