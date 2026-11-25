"""Versioned caching helpers for catalog search responses.

Search result keys include:

* the normalized query,
* every filter and the sort strategy,
* the effective pagination window,
* the request host (DRF builds absolute next/previous links),
* a global catalog version.

Catalog writes bump the version instead of trying to delete every possible key.
Old entries become unreachable and expire through their TTL.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from django.core.cache import cache

from common.cache import make_cache_key

logger = logging.getLogger(__name__)

SEARCH_VERSION_KEY = make_cache_key("catalog", "search_version")


def get_search_cache_version() -> int:
    """Return the current catalog cache generation (created lazily).

    Cache outages must not break search: on a backend error the generation is
    reported as 0 and the response is served uncached.
    """
    try:
        version = cache.get(SEARCH_VERSION_KEY)
        if version is None:
            cache.add(SEARCH_VERSION_KEY, 1, timeout=None)
            version = cache.get(SEARCH_VERSION_KEY) or 1
        return int(version)
    except Exception:  # noqa: BLE001 - cache is an optimization, never fatal
        logger.warning("Search cache unavailable; serving uncached.", exc_info=True)
        return 0


def bump_search_cache_version() -> None:
    """Invalidate every cached search response by moving to a new generation."""
    try:
        cache.incr(SEARCH_VERSION_KEY)
    except ValueError:
        # Key absent (first write after a cache flush) or backend without incr.
        cache.set(SEARCH_VERSION_KEY, 1, timeout=None)
    except Exception:  # noqa: BLE001 - never fail a catalog write for cache
        logger.warning("Could not bump search cache version.", exc_info=True)


def get_cached_response(key: str) -> Any | None:
    """Best-effort read; returns None when the cache backend is unavailable."""
    try:
        return cache.get(key)
    except Exception:  # noqa: BLE001
        logger.warning("Search cache read failed; serving uncached.", exc_info=True)
        return None


def set_cached_response(key: str, value: Any, *, timeout: int) -> None:
    """Best-effort write; cache failures never break a successful response."""
    try:
        cache.set(key, value, timeout=timeout)
    except Exception:  # noqa: BLE001
        logger.warning("Search cache write failed.", exc_info=True)


def build_search_cache_key(scope: str, payload: dict[str, Any]) -> str:
    """Build a bounded, deterministic key from the canonical request shape."""
    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"catalog:{scope}:v{get_search_cache_version()}:{digest}"
