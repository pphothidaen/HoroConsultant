from __future__ import annotations

"""
Active Model Registry.

Tracks the currently active model artifact used for inference metadata and training
handoff. The registry is lightweight and local-file based so it can be queried by
API, Telegram, and MLOps controllers without requiring external state.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from project.core.config import Config
from project.core.cache_manager import runtime_cache

STATE_PATH = Path(__file__).resolve().parents[1] / "data" / "active_model_state.json"
STATE_VERSION = "1"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _new_model_version(tag: Optional[str] = None) -> str:
    base = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    if tag:
        return f"{tag}-{base}"
    return f"run-{base}"


def _load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return dict(__import__("json").loads(STATE_PATH.read_text(encoding="utf-8")))
        except Exception:
            return {}
    return {}


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(__import__("json").dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def get_active_model_state() -> dict[str, Any]:
    state = _load_state()
    return {
        "active_model": state.get("active_model", Config.HF_REPO_ID),
        "model_version": state.get("model_version", "v1.0.0"),
        "status": state.get("status", "active"),
        "updated_at": state.get("updated_at", _now_iso()),
        "source": state.get("source", "bootstrap"),
        "notes": state.get("notes", "Initialized default model context"),
        "last_training_job": state.get("last_training_job"),
        "history": state.get("history", []),
    }


def get_active_model() -> str:
    return get_active_model_state()["active_model"]


def get_active_model_version() -> str:
    return get_active_model_state()["model_version"]


def _append_history(state: dict[str, Any], entry: dict[str, Any]) -> list[dict[str, Any]]:
    history = list(state.get("history") or [])
    history.insert(0, entry)
    if len(history) > 20:
        history = history[:20]
    return history


def update_active_model(
    model_id: str,
    *,
    status: str = "active",
    source: str = "kaggle_orchestrator",
    model_version: Optional[str] = None,
    notes: Optional[str] = None,
    training_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    state = get_active_model_state()
    previous_version = state.get("model_version")
    resolved_version = model_version or _new_model_version()

    state["active_model"] = model_id
    state["model_version"] = resolved_version
    state["status"] = status
    state["source"] = source
    state["updated_at"] = _now_iso()
    if notes:
        state["notes"] = notes
    if training_metadata is not None:
        state["last_training_job"] = training_metadata

    if previous_version != resolved_version:
        evicted = runtime_cache.invalidate_on_model_update(resolved_version)
        state["cache_evicted"] = evicted

    state["history"] = _append_history(
        state,
        {
            "active_model": model_id,
            "model_version": resolved_version,
            "status": status,
            "source": source,
            "updated_at": state["updated_at"],
            "notes": notes,
            "training_metadata": training_metadata,
        },
    )

    _save_state(state)
    return state
