from __future__ import annotations

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class _ClientIPThrottle(SimpleRateThrottle):
    """
    Rate-limit anonymous storefront reads per client IP.

    Scopes and rates are declared in ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]``
    (``catalog_search``, ``catalog_suggest``) so operations can tune them without
    touching code.
    """

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class ProductSearchThrottle(_ClientIPThrottle):
    scope = "catalog_search"


class ProductSuggestionThrottle(_ClientIPThrottle):
    scope = "catalog_suggest"
