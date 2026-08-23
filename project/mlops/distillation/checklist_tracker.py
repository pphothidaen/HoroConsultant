"""
project/mlops/distillation/checklist_tracker.py
===============================================
Persistent Checklist & Deduplication State Tracker for NotebookLM Distillation.
Guarantees idempotent knowledge mining across text topics and multimodal diagrams,
preventing redundant API consumption and duplicate dataset records.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("checklist_tracker")

DEFAULT_CHECKLIST_PATH = Path(__file__).resolve().parents[3] / "project" / "data" / "distillation_checklist.json"


class DistillationChecklistTracker:
    """Persistent Checklist State Tracker for NotebookLM knowledge extraction."""

    def __init__(self, checklist_path: Optional[Path | str] = None):
        self.path = Path(checklist_path) if checklist_path else DEFAULT_CHECKLIST_PATH
        self.state: Dict[str, Any] = self._load()

    def _generate_topic_key(self, domain: str, topic: str, notebook_id: Optional[str] = None) -> str:
        """Generate normalized unique hash key for topic."""
        norm_topic = "".join(topic.strip().lower().split())
        h = hashlib.sha256(f"{domain}:{notebook_id or ''}:{norm_topic}".encode("utf-8")).hexdigest()[:16]
        return f"{domain}:{h}"

    def _load(self) -> Dict[str, Any]:
        """Load state from JSON file or initialize default schema."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "topics" in data:
                    return data
            except Exception as e:
                logger.warning(f"[CHECKLIST] Failed to read checklist from {self.path}: {e}")

        return {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "topics": {},
            "stats": {
                "total_recorded": 0,
                "completed": 0,
                "in_progress": 0,
                "failed": 0,
                "diagrams_count": 0
            }
        }

    def save(self) -> None:
        """Persist state to disk safely with atomic write."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._refresh_stats()
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(self.path)

    def _refresh_stats(self) -> None:
        """Update summary stats counters."""
        topics = self.state.get("topics", {})
        completed = sum(1 for t in topics.values() if t.get("status") == "COMPLETED")
        in_progress = sum(1 for t in topics.values() if t.get("status") == "IN_PROGRESS")
        failed = sum(1 for t in topics.values() if t.get("status") == "FAILED")
        diagrams = sum(1 for t in topics.values() if t.get("has_diagram", False))
        self.state["stats"] = {
            "total_recorded": len(topics),
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "diagrams_count": diagrams
        }

    def is_completed(self, domain: str, topic: str, notebook_id: Optional[str] = None) -> bool:
        """Check if topic has already been successfully distilled."""
        key = self._generate_topic_key(domain, topic, notebook_id)
        topic_data = self.state.get("topics", {}).get(key)
        return bool(topic_data and topic_data.get("status") == "COMPLETED")

    def mark_in_progress(self, domain: str, topic: str, notebook_id: Optional[str] = None) -> None:
        """Flag a topic as currently being processed."""
        key = self._generate_topic_key(domain, topic, notebook_id)
        self.state.setdefault("topics", {})[key] = {
            "key": key,
            "domain": domain,
            "notebook_id": notebook_id or "",
            "topic": topic,
            "status": "IN_PROGRESS",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.save()

    def mark_completed(
        self,
        domain: str,
        topic: str,
        notebook_id: str,
        sample_ids: List[str],
        content_hash: str,
        has_diagram: bool = False,
        diagram_type: Optional[str] = None,
        diagram_path: Optional[str] = None
    ) -> None:
        """Mark a topic as successfully completed with associated sample metadata."""
        key = self._generate_topic_key(domain, topic, notebook_id)
        self.state.setdefault("topics", {})[key] = {
            "key": key,
            "domain": domain,
            "notebook_id": notebook_id,
            "topic": topic,
            "status": "COMPLETED",
            "sample_ids": sample_ids,
            "content_hash": content_hash,
            "has_diagram": has_diagram,
            "diagram_type": diagram_type,
            "diagram_path": diagram_path,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        self.save()
        logger.info(f"[CHECKLIST] Marked '{topic[:40]}...' as COMPLETED ({len(sample_ids)} samples).")

    def mark_failed(self, domain: str, topic: str, notebook_id: Optional[str] = None, error: str = "") -> None:
        """Mark topic extraction as failed."""
        key = self._generate_topic_key(domain, topic, notebook_id)
        self.state.setdefault("topics", {})[key] = {
            "key": key,
            "domain": domain,
            "notebook_id": notebook_id or "",
            "topic": topic,
            "status": "FAILED",
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat()
        }
        self.save()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Return summary statistics by domain and status."""
        self._refresh_stats()
        topics = self.state.get("topics", {})
        by_domain: Dict[str, Dict[str, int]] = {}
        for t in topics.values():
            dom = t.get("domain", "unknown")
            by_domain.setdefault(dom, {"completed": 0, "failed": 0, "total": 0, "diagrams": 0})
            by_domain[dom]["total"] += 1
            if t.get("status") == "COMPLETED":
                by_domain[dom]["completed"] += 1
            elif t.get("status") == "FAILED":
                by_domain[dom]["failed"] += 1
            if t.get("has_diagram"):
                by_domain[dom]["diagrams"] += 1

        return {
            **self.state["stats"],
            "by_domain": by_domain,
            "last_updated": self.state.get("last_updated")
        }

    def list_topics(self, domain: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered topic records with optional domain/status filtering."""
        results = []
        for t in self.state.get("topics", {}).values():
            if domain and t.get("domain") != domain:
                continue
            if status and t.get("status") != status:
                continue
            results.append(t)
        return results

    def reset(self, domain: Optional[str] = None) -> int:
        """Reset checklist entries for all or specific domain."""
        if not domain:
            count = len(self.state.get("topics", {}))
            self.state["topics"] = {}
            self.save()
            return count
        else:
            to_delete = [k for k, v in self.state.get("topics", {}).items() if v.get("domain") == domain]
            for k in to_delete:
                del self.state["topics"][k]
            self.save()
            return len(to_delete)
