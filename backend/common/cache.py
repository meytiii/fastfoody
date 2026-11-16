from __future__ import annotations

CACHE_VERSION = "v1"


def make_cache_key(area: str, scope: str, version: str = CACHE_VERSION) -> str:
    """Build a cache key following the fastfood:<area>:<scope>:<version> convention."""
    return f"{area}:{scope}:{version}"