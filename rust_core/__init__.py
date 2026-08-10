"""
rust_core Python Package Initialiser
Loads and re-exports the standard package-local Rust PyO3 extension.
"""

from __future__ import annotations

from importlib import import_module
import os
from types import ModuleType
from typing import Any


PYTHON_FALLBACK_ALLOWED = os.environ.get("HORO_ALLOW_PYTHON_FALLBACK") == "1"
RUST_AVAILABLE = False
__native_origin__: str | None = None
_native: ModuleType | None = None

try:
    _native = import_module("._native", __name__)
except ImportError as exc:
    if not PYTHON_FALLBACK_ALLOWED:
        raise ImportError(
            "rust_core._native is required in production; install the platform wheel "
            "or set HORO_ALLOW_PYTHON_FALLBACK=1 for explicit development fallback"
        ) from exc
else:
    for _name in dir(_native):
        if not _name.startswith("_"):
            globals()[_name] = getattr(_native, _name)
    RUST_AVAILABLE = True
    __native_origin__ = _native.__file__


def runtime_backend() -> dict[str, Any]:
    """Return deterministic, secret-free native runtime identity metadata."""
    if _native is None:
        return {
            "rust_available": False,
            "rust_version": None,
            "kernels": [],
        }
    return {
        "rust_available": True,
        "rust_version": getattr(_native, "__version__", None),
        "kernels": list(getattr(_native, "__kernels__", ())),
    }


__all__ = sorted(
    [
        name
        for name in globals()
        if not name.startswith("_")
        and name not in {"Any", "ModuleType", "import_module", "os"}
    ]
)
