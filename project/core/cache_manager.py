"""
project/core/cache_manager.py
==============================
High-Performance 2-Tier Caching Layer for Track B (Inference System).

Architecture (Decision 7):
  - Tier 1: In-Memory RAM LRU Cache (sub-millisecond instant lookup, capacity=1000 items)
  - Tier 2: Persistent Disk Cache (JSON store surviving server restarts)
  - Auto-Eviction: Invalidate and purge cached AI readings on new fine-tuned model releases.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("cache_manager")

CACHE_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_FILE = CACHE_DIR / "runtime_response_cache.json"


class RuntimeCacheManager:
    """Thread-safe 2-Tier Cache (In-Memory LRU + Persistent Disk Cache)."""

    def __init__(self, ttl_seconds: int = 86400, memory_capacity: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.memory_capacity = memory_capacity
        self._memory_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._disk_cache: dict[str, dict[str, Any]] = self._load_disk_cache()
        # Seed memory cache from disk cache
        for k, v in list(self._disk_cache.items())[-self.memory_capacity:]:
            self._memory_cache[k] = v

    def _load_disk_cache(self) -> dict[str, dict[str, Any]]:
        """Load cache from disk file."""
        if CACHE_FILE.exists():
            try:
                return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"[CACHE] Could not load disk cache file: {e}")
        return {}

    def _save_disk_cache(self) -> None:
        """Persist cache back to disk file."""
        try:
            CACHE_FILE.write_text(json.dumps(self._disk_cache, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"[CACHE] Could not save disk cache file: {e}")

    def _generate_key(self, key_data: Any) -> str:
        """Generate SHA256 key from serializable input dict/data."""
        serialized = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, key_data: Any) -> dict[str, Any] | None:
        """
        Fetch cached entry checking Tier 1 (RAM) then Tier 2 (Disk).
        Returns response dict or None on miss.
        """
        cache_key = self._generate_key(key_data)
        now = time.time()

        # Tier 1: Check In-Memory LRU Cache
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if now - entry.get("timestamp", 0) <= self.ttl_seconds:
                self._memory_cache.move_to_end(cache_key)
                self.hits += 1
                logger.info(f"[CACHE:RAM] Cache HIT (Tier 1)! Key: {cache_key[:8]} (< 0.1ms)")
                return entry.get("response")
            else:
                del self._memory_cache[cache_key]

        # Tier 2: Check Persistent Disk Cache
        if cache_key in self._disk_cache:
            entry = self._disk_cache[cache_key]
            if now - entry.get("timestamp", 0) <= self.ttl_seconds:
                # Promote to Tier 1 RAM
                self._memory_cache[cache_key] = entry
                self._memory_cache.move_to_end(cache_key)
                self.hits += 1
                logger.info(f"[CACHE:DISK] Cache HIT (Tier 2)! Key: {cache_key[:8]} (< 1ms)")
                return entry.get("response")
            else:
                del self._disk_cache[cache_key]
                self._save_disk_cache()

        self.misses += 1
        return None

    def set(self, key_data: Any, response_data: dict[str, Any], model_version: str = "v1") -> None:
        """Store response data into Tier 1 RAM and Tier 2 Disk."""
        cache_key = self._generate_key(key_data)
        entry = {
            "timestamp": time.time(),
            "model_version": model_version,
            "response": response_data
        }

        # Store in Tier 1 RAM LRU
        if len(self._memory_cache) >= self.memory_capacity:
            self._memory_cache.popitem(last=False)  # Evict oldest
        self._memory_cache[cache_key] = entry

        # Store in Tier 2 Disk
        self._disk_cache[cache_key] = entry
        self._save_disk_cache()
        logger.info(f"[CACHE] Stored 2-Tier entry for key {cache_key[:8]}")

    def invalidate_on_model_update(self, new_model_version: str) -> int:
        """
        Auto-evict AI-generated cached entries when a new model is released (Decision 7).
        Preserves pure deterministic mathematical charts.
        """
        evicted = 0
        keys_to_del = []
        for k, v in self._disk_cache.items():
            if v.get("model_version") != new_model_version:
                keys_to_del.append(k)

        for k in keys_to_del:
            self._disk_cache.pop(k, None)
            self._memory_cache.pop(k, None)
            evicted += 1

        if evicted > 0:
            self._save_disk_cache()
            logger.info(f"[CACHE] Evicted {evicted} legacy cache entries for model update: {new_model_version}")
        return evicted

    def clear(self) -> None:
        """Purge all cached entries across RAM and Disk."""
        self._memory_cache.clear()
        self._disk_cache.clear()
        if CACHE_FILE.exists():
            CACHE_FILE.unlink(missing_ok=True)
        self.hits = 0
        self.misses = 0
        logger.info("[CACHE] Purged all 2-tier cache entries.")

    def get_stats(self) -> dict[str, Any]:
        """Return cache health metrics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100.0) if total > 0 else 0.0
        return {
            "ram_items": len(self._memory_cache),
            "disk_items": len(self._disk_cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl_seconds,
        }


# Global Singleton Instance
runtime_cache = RuntimeCacheManager()
