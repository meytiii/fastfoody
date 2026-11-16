from __future__ import annotations

from functools import lru_cache

import redis
from django.conf import settings


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    """Return a shared Redis client using the same URL as the cache backend."""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)