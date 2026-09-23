"""
Hermes Agent Resource Manager
Prevents resource exhaustion in subagent delegation pipeline.
"""
import shutil
import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ResourceLimits:
    """Resource quotas enforced before delegation."""
    max_disk_usage_gb: int = 10
    max_concurrent_subagents: int = 6
    per_agent_timeout_minutes: int = 15
    max_manifest_size_mb: int = 50


class ResourceGovernor:
    """
    Central resource enforcement point.
    Called by Orchestrator before spawning any subagent.
    """

    def __init__(self, cache_root: str = "/Users/kimlenglim/.hermes/cache"):
        self.cache_root = cache_root
        self.limits = ResourceLimits()
        self._active_agents: Dict[str, float] = {}  # delegation_id -> start_time

    def can_delegate(self, delegation_id: str) -> bool:
        """
        Check ALL resource constraints before allowing new subagent.
        Raises ResourceExhausted on violation.
        """
        # 1. Count active agents
        active_count = len(self._active_agents)
        if active_count >= self.limits.max_concurrent_subagents:
            raise ResourceExhausted(
                f"Max concurrent subagents ({self.limits.max_concurrent_subagents}) reached. "
                f"Active: {list(self._active_agents.keys())}"
            )

        # 2. Check disk space
        disk_used_gb = self._get_disk_usage_gb()
        if disk_used_gb > self.limits.max_disk_usage_gb:
            raise ResourceExhausted(
                f"Cache disk usage {disk_used_gb:.1f}GB exceeds limit "
                f"{self.limits.max_disk_usage_gb}GB"
            )

        return True

    def register_agent(self, delegation_id: str) -> None:
        """Track a newly spawned subagent."""
        import time
        self._active_agents[delegation_id] = time.time()

    def unregister_agent(self, delegation_id: str) -> None:
        """Remove subagent from active tracking."""
        self._active_agents.pop(delegation_id, None)

    def _get_disk_usage_gb(self) -> float:
        """Return disk usage of cache_root in GB."""
        try:
            total_size = 0
            for dirpath, _, filenames in os.walk(self.cache_root):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            return total_size / (1024 ** 3)
        except Exception:
            return 0.0


class ResourceExhausted(Exception):
    """Raised when resource limits prevent delegation."""
    pass


# Module-level singleton
governor = None

def get_governor(cache_root: str = "/Users/kimlenglim/.hermes/cache") -> ResourceGovernor:
    global governor
    if governor is None:
        governor = ResourceGovernor(cache_root)
    return governor
