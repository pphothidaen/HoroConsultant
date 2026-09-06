"""Security contract for Google Admin ID-token storage in both UI mirrors."""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADMIN_MIRRORS = (
    Path("public/admin.html"),
    Path("project/static/admin.html"),
)
TOKEN_KEY = "admin_id_token"


@pytest.mark.parametrize("relative_path", ADMIN_MIRRORS, ids=str)
def test_admin_id_token_is_session_scoped(relative_path: Path) -> None:
    """A tab close must discard the bearer credential in either deployed mirror."""
    html = (ROOT / relative_path).read_text(encoding="utf-8")

    assert f"sessionStorage.getItem('{TOKEN_KEY}')" in html
    assert f"sessionStorage.setItem('{TOKEN_KEY}', response.credential)" in html
    assert f"sessionStorage.removeItem('{TOKEN_KEY}')" in html
    assert not re.search(
        r"localStorage\.(?:getItem|setItem)\(['\"](?:google_id_token|admin_id_token)['\"]",
        html,
    )


@pytest.mark.parametrize("relative_path", ADMIN_MIRRORS, ids=str)
def test_admin_auth_purges_legacy_persistent_tokens(relative_path: Path) -> None:
    """Upgrading must delete bearer credentials persisted by older releases."""
    html = (ROOT / relative_path).read_text(encoding="utf-8")

    for legacy_key in ("google_id_token", "admin_id_token"):
        purge = f"localStorage.removeItem('{legacy_key}')"
        assert purge in html
        assert html.index(purge) < html.index(f"sessionStorage.getItem('{TOKEN_KEY}')")


@pytest.mark.parametrize("relative_path", ADMIN_MIRRORS, ids=str)
def test_admin_id_token_still_guards_protected_requests(relative_path: Path) -> None:
    """Session scoping must not weaken the in-memory Authorization boundary."""
    html = (ROOT / relative_path).read_text(encoding="utf-8")

    assert "State.adminIdToken = response.credential" in html
    assert "Authorization: `Bearer ${State.adminIdToken}`" in html
    assert re.search(
        r"if\s*\(endpoint\.startsWith\('/admin/'\).*?!State\.adminIdToken",
        html,
        re.DOTALL,
    )
