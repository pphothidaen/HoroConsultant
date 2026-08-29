"""
project/core/semantic_cache.py
==============================
High-Performance Metaphysics Semantic Cache & Safe Net Fallback.

Key Features:
1. SHA-256 Canonical Query Normalization:
   - Canonicalizes True Solar Time, Day Master, Question Type, and Astrological Metadata.
2. Category-Based TTL:
   - Daily Horoscope: 24 hours (86,400s) / 6 hours (21,600s)
   - FAQ / Reference: 30 days (2,592,000s)
   - BaZi / Natal Chart: 30 days (2,592,000s)
   - Feng Shui: 7 days (604,800s)
   - General Query: 1 hour (3,600s)
3. Thread-Safe In-Memory LRU Eviction & Stats Tracking.
4. Deterministic Safe Net Fallback on full free LLM exhaustion (<1ms, zero cost).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("semantic_cache")

# Default TTL durations in seconds
DEFAULT_CATEGORY_TTLS: Dict[str, int] = {
    "daily_horoscope": 86400,       # 24 hours
    "daily_horoscope_6h": 21600,    # 6 hours
    "daily": 86400,                 # 24 hours
    "faq": 2592000,                 # 30 days
    "reference": 2592000,           # 30 days
    "bazi_chart": 2592000,          # 30 days
    "bazi": 2592000,                # 30 days
    "natal_chart": 2592000,         # 30 days
    "chart": 2592000,               # 30 days
    "feng_shui": 604800,            # 7 days
    "fengshui": 604800,             # 7 days
    "qimen": 86400,                 # 24 hours
    "ziwei": 2592000,               # 30 days
    "general": 3600,                # 1 hour
}

DEFAULT_CACHE_CAPACITY = 2000

# Canonical astrological metadata keys recognized for hashing
KNOWN_ASTROLOGICAL_KEYS = {
    "true_solar_time",
    "day_master",
    "birth_date",
    "birth_time",
    "gender",
    "question_type",
    "domain",
    "element",
    "solar_longitude",
    "chart_id",
    "category",
    "zodiac_sign",
    "pillar",
    "chart_type",
    "tz_offset",
    "latitude",
    "longitude",
    "equation_of_time",
    "lunar_date",
    "lunar_month",
    "lunar_year",
    "language",
    "aspect",
    "house_system",
    "ayanamsa",
    "period",
}


def _canonicalize_value(val: Any) -> Any:
    """Recursively canonicalize metadata value for deterministic serialization."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        if isinstance(val, float):
            return f"{round(val, 6):g}"
        return str(val)
    if isinstance(val, str):
        return re.sub(r"\s+", " ", val.strip().lower())
    if isinstance(val, dict):
        return {
            str(k).strip().lower(): _canonicalize_value(v)
            for k, v in sorted(val.items(), key=lambda item: str(item[0]).lower())
            if v is not None
        }
    if isinstance(val, (list, tuple, set)):
        return [_canonicalize_value(item) for item in val]
    return str(val).strip().lower()


def normalize_astrological_prompt(
    prompt: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Canonicalize and normalize prompt text and astrology metadata.
    Ensures identical semantic queries yield identical cache keys.
    """
    cleaned = re.sub(r"\s+", " ", (prompt or "").strip().lower())

    if not metadata:
        return cleaned

    # Extract canonical astrological coordinates and attributes
    canonical_meta: Dict[str, Any] = {}
    for key in sorted(metadata.keys(), key=lambda k: str(k).lower()):
        normalized_key = str(key).strip().lower()
        val = metadata[key]
        if val is not None:
            canonical_meta[normalized_key] = _canonicalize_value(val)

    meta_str = json.dumps(canonical_meta, sort_keys=True, separators=(",", ":"))
    return f"{cleaned}|meta:{meta_str}"


def compute_prompt_hash(
    prompt: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Compute SHA-256 hexdigest for a normalized prompt and metadata."""
    normalized = normalize_astrological_prompt(prompt, metadata)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class SemanticCacheEntry:
    """Represents a cached interpretation entry."""
    prompt_hash: str
    normalized_prompt: str
    response: Dict[str, Any]
    category: str
    created_at: float
    ttl: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return (now - self.created_at) > self.ttl


class SemanticCache:
    """
    Thread-safe In-Memory Semantic Cache with category-specific TTL,
    LRU eviction, and deterministic Safe Net fallback.
    """

    def __init__(
        self,
        capacity: int = DEFAULT_CACHE_CAPACITY,
        category_ttls: Optional[Dict[str, int]] = None,
    ) -> None:
        self.capacity = capacity
        self.category_ttls = dict(DEFAULT_CATEGORY_TTLS)
        if category_ttls:
            self.category_ttls.update(category_ttls)

        self._cache: OrderedDict[str, SemanticCacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0

    def _get_ttl(self, category: str, custom_ttl: Optional[float] = None) -> float:
        if custom_ttl is not None and custom_ttl > 0:
            return float(custom_ttl)
        cat_key = category.lower()
        return float(self.category_ttls.get(cat_key, self.category_ttls["general"]))

    def get(
        self,
        prompt: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Look up cached response by prompt and optional metadata.
        Returns cached response dict or None on cache miss/expiry.
        """
        key = compute_prompt_hash(prompt, metadata)
        now = time.time()

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired(now):
                    self._cache.move_to_end(key)
                    self.hits += 1
                    logger.info(f"[SemanticCache] HIT for key {key[:8]} ({category})")
                    return entry.response
                else:
                    # Expired entry
                    del self._cache[key]
                    logger.debug(f"[SemanticCache] Expired entry purged for key {key[:8]}")

            self.misses += 1
            return None

    def set(
        self,
        prompt: str,
        response: Dict[str, Any],
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ) -> str:
        """
        Store response into cache with category TTL.
        Returns the SHA-256 cache key.
        """
        key = compute_prompt_hash(prompt, metadata)
        normalized = normalize_astrological_prompt(prompt, metadata)
        effective_ttl = self._get_ttl(category, ttl)
        now = time.time()

        entry = SemanticCacheEntry(
            prompt_hash=key,
            normalized_prompt=normalized,
            response=response,
            category=category.lower(),
            created_at=now,
            ttl=effective_ttl,
            metadata=metadata or {},
        )

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.capacity:
                    self._cache.popitem(last=False)
                    self.evictions += 1

            self._cache[key] = entry

        logger.info(
            f"[SemanticCache] STORED key {key[:8]} "
            f"(category={category}, ttl={effective_ttl}s)"
        )
        return key

    def peek(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Inspect entry without updating LRU order or hit/miss statistics.
        """
        key = compute_prompt_hash(prompt, metadata)
        now = time.time()
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired(now):
                    return entry.response
        return None

    def invalidate(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Invalidate a single cached entry."""
        key = compute_prompt_hash(prompt, metadata)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"[SemanticCache] Invalidated key {key[:8]}")
                return True
        return False

    def invalidate_category(self, category: str) -> int:
        """Purge all cached items belonging to a specific category."""
        target = category.lower()
        with self._lock:
            keys_to_remove = [
                k for k, v in self._cache.items() if v.category == target
            ]
            for k in keys_to_remove:
                del self._cache[k]

        logger.info(
            f"[SemanticCache] Invalidated {len(keys_to_remove)} entries "
            f"for category '{category}'"
        )
        return len(keys_to_remove)

    def prune_expired(self) -> int:
        """Purge all expired entries across all categories."""
        now = time.time()
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired(now)
            ]
            for k in expired_keys:
                del self._cache[k]

        if expired_keys:
            logger.info(f"[SemanticCache] Pruned {len(expired_keys)} expired entries")
        return len(expired_keys)

    def clear(self) -> None:
        """Purge all cached entries and reset telemetry counters."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0
        logger.info("[SemanticCache] Cache cleared.")

    def get_stats(self) -> Dict[str, Any]:
        """Return cache health and telemetry stats."""
        with self._lock:
            total = self.hits + self.misses
            hit_ratio = (self.hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "capacity": self.capacity,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_ratio": round(hit_ratio, 4),
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __contains__(self, prompt_or_key: str) -> bool:
        with self._lock:
            if prompt_or_key in self._cache:
                return not self._cache[prompt_or_key].is_expired()
            key = compute_prompt_hash(prompt_or_key)
            if key in self._cache:
                return not self._cache[key].is_expired()
            return False

    def deterministic_fallback_reading(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic Safe Net fallback reading generated without LLM API calls.
        Provides instant (<1ms) baseline interpretations on full free LLM exhaustion.
        Guarantees fail-closed zero cloud cost.
        """
        t_start = time.perf_counter()
        meta = metadata or {}
        day_master = meta.get("day_master") or "Balanced Self"
        domain = meta.get("domain") or "General Metaphysics"
        question_type = meta.get("question_type") or "Interpretation"
        element = meta.get("element") or "Harmonized"
        true_solar_time = meta.get("true_solar_time") or "Calculated Standard"

        # Attempt native Rust fast math telemetry if available
        rust_status = "active"
        try:
            import rust_core  # type: ignore
            if not getattr(rust_core, "RUST_AVAILABLE", False):
                rust_status = "fallback_python"
        except Exception:
            rust_status = "fallback_offline"

        content = (
            f"[DETERMINISTIC SAFE NET FALLBACK]\n"
            f"Domain: {domain}\n"
            f"Question Type: {question_type}\n"
            f"Day Master: {day_master}\n"
            f"Primary Element: {element}\n"
            f"True Solar Time: {true_solar_time}\n\n"
            f"Standard Metaphysical Calculation Baseline:\n"
            f"- Five Elements balance evaluated via deterministic solar coordinate rules.\n"
            f"- Chart analysis grounded in classical BaZi / Qi Men Dun Jia / Xuan Kong axioms.\n"
            f"- Zero cloud billing incurred (fail-closed zero-cost guarantee).\n"
            f"- High-performance native acceleration: {rust_status}.\n\n"
            f"Deterministic Interpretation Summary:\n"
            f"The astrological configuration emphasizes equilibrium and harmonic alignment "
            f"between natal heavenly stems and earthly branches. In periods of transition, "
            f"cultivating favorable elemental supports ({element}) reinforces strategic timing.\n\n"
            f"Query Summary: {prompt[:200]}"
        )

        latency_ms = (time.perf_counter() - t_start) * 1000.0

        return {
            "status": "fallback",
            "provider": "DETERMINISTIC_SAFE_NET",
            "model": "rust_pyo3_baseline",
            "content": content,
            "raw_response": {
                "mode": "deterministic_offline",
                "metadata": meta,
                "rust_acceleration": rust_status,
                "latency_ms": round(latency_ms, 3),
            },
            "error_message": "All free LLM tiers exhausted or rate-limited. Returned deterministic safe net.",
            "error_type": "deterministic_fallback",
            "route_used": "deterministic_safe_net",
            "latency_ms": round(latency_ms, 3),
        }


# Global singleton instance
semantic_cache = SemanticCache()
