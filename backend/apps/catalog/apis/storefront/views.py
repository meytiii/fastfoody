from __future__ import annotations

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog import selectors
from apps.catalog.cache import (
    build_search_cache_key,
    get_cached_response,
    set_cached_response,
)
from apps.catalog.search import (
    MAX_PRICE_FILTER,
    MAX_SEARCH_LENGTH,
    SORT_CHOICES,
    normalize_search_query,
)
from apps.catalog.throttles import ProductSearchThrottle, ProductSuggestionThrottle

from common.serializers import ErrorEnvelopeSerializer
from common.views import StorefrontAPIView

from .serializers import (
    LuckyWheelResponseSerializer,
    MenuResponseSerializer,
    ProductDetailPublicSerializer,
    ProductListResponseSerializer,
    ProductSearchQuerySerializer,
    ProductSuggestionListResponseSerializer,
    ProductSuggestionPublicSerializer,
    ProductSuggestionQuerySerializer,
    ProductSummaryPublicSerializer,
    UpsellResponseSerializer,
)

class CatalogPagination(LimitOffsetPagination):
    """Bound page size so a single request cannot materialize the whole catalog."""

    max_limit = 100


_SEARCH_PARAMETERS = [
    OpenApiParameter(
        "q",
        OpenApiTypes.STR,
        description=(
            "Free-text search (max 100 chars). Words are matched with weighted "
            "PostgreSQL full-text search over product name, category name and "
            "description, plus trigram similarity for partial/fuzzy matches. "
            "Persian/Arabic letter variants and the synonym groups are handled "
            "server-side."
        ),
    ),
    OpenApiParameter(
        "category",
        OpenApiTypes.STR,
        description="Category slug; unknown or inactive → 404 CATEGORY_NOT_FOUND.",
    ),
    OpenApiParameter(
        "category_id",
        OpenApiTypes.INT,
        description="Category id; unknown or inactive → 404 CATEGORY_NOT_FOUND.",
    ),
    OpenApiParameter(
        "min_price",
        OpenApiTypes.INT,
        description=f"Inclusive minimum selling price (0…{MAX_PRICE_FILTER}).",
    ),
    OpenApiParameter(
        "max_price",
        OpenApiTypes.INT,
        description=(
            f"Inclusive maximum selling price (0…{MAX_PRICE_FILTER}); must be "
            "greater than or equal to min_price."
        ),
    ),
    OpenApiParameter(
        "available",
        OpenApiTypes.BOOL,
        description=(
            "Raw status flag: true → AVAILABLE, false → OUT_OF_STOCK, omitted → "
            "both (HIDDEN is never returned)."
        ),
    ),
    OpenApiParameter(
        "discount",
        OpenApiTypes.BOOL,
        description=(
            "true → only products with compare_at_price > price; false → only "
            "non-discounted products."
        ),
    ),
    OpenApiParameter(
        "is_main_dish",
        OpenApiTypes.BOOL,
        description="Filter by the is_main_dish flag.",
    ),
    OpenApiParameter(
        "sort",
        OpenApiTypes.STR,
        enum=list(SORT_CHOICES),
        description=(
            "Ordering strategy. Popularity is computed from PAID order items; "
            "relevance is implicit when q is present and sort is omitted."
        ),
    ),
    OpenApiParameter(
        "limit",
        OpenApiTypes.INT,
        description="Page size (default 20, clamped to 100).",
    ),
    OpenApiParameter(
        "offset", OpenApiTypes.INT, description="Page offset (LimitOffsetPagination)."
    ),
]


class MenuView(StorefrontAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — Catalog"],
        operation_id="storefront_catalog_menu",
        summary="Return the cached storefront menu",
        responses={200: MenuResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(selectors.get_storefront_menu())


class LuckyWheelView(StorefrontAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — Catalog"],
        operation_id="storefront_catalog_lucky_wheel",
        summary="Return products for the lucky wheel",
        parameters=[
            OpenApiParameter(
                "category",
                OpenApiTypes.STR,
                description="Optional category slug; unknown/inactive → 404.",
            )
        ],
        responses={
            200: LuckyWheelResponseSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        category_slug = request.query_params.get("category")
        return Response(
            selectors.get_lucky_wheel_products(category_slug=category_slug)
        )


class UpsellView(StorefrontAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — Catalog"],
        operation_id="storefront_catalog_upsell",
        summary="Suggested sides and drinks for the cart",
        responses={200: UpsellResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(selectors.get_upsell_products())


class ProductListView(StorefrontAPIView):
    """
    Public product discovery: search, filters and sorting in one pipeline.

    Uses the project-wide ``LimitOffsetPagination``; the paginator rebuilds
    ``next``/``previous`` links from the request, so every filter and sort
    parameter survives pagination.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ProductSearchThrottle]

    @extend_schema(
        tags=["Storefront — Catalog"],
        operation_id="storefront_catalog_products_list",
        summary="Search and filter public products",
        description=(
            "Returns paginated, publicly visible products (not HIDDEN, active "
            "category). Search uses weighted PostgreSQL full-text search "
            "(name/category/description) combined with pg_trgm similarity for "
            "partial and fuzzy matches; Persian/Arabic letter variants and "
            "synonym groups are applied server-side. An empty result set "
            "includes did_you_mean when a close product or category name exists. "
            "Responses are cached per query/filter/sort/page and invalidated by "
            "catalog writes. Invalid parameters return 400 with the standard "
            "error envelope."
        ),
        parameters=_SEARCH_PARAMETERS,
        responses={
            200: ProductListResponseSerializer,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            429: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        # A plain dict (not QueryDict) keeps DRF from applying HTML-form
        # semantics, which would turn absent booleans into False.
        serializer = ProductSearchQuerySerializer(data=request.query_params.dict())
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        paginator = CatalogPagination()
        ttl = getattr(settings, "CATALOG_SEARCH_CACHE_TTL", 60)
        cache_enabled = (
            getattr(settings, "CATALOG_SEARCH_CACHE_ENABLED", True) and ttl > 0
        )
        cache_key = None
        if cache_enabled:
            cache_key = build_search_cache_key(
                "products",
                {
                    "q": normalize_search_query(params.get("q")),
                    "category": params.get("category"),
                    "category_id": params.get("category_id"),
                    "min_price": params.get("min_price"),
                    "max_price": params.get("max_price"),
                    "available": params.get("available"),
                    "discount": params.get("discount"),
                    "is_main_dish": params.get("is_main_dish"),
                    "sort": params.get("sort"),
                    "limit": paginator.get_limit(request),
                    "offset": paginator.get_offset(request),
                    "host": request.get_host(),
                    "scheme": request.scheme,
                },
            )
            cached = get_cached_response(cache_key)
            if cached is not None:
                return Response(cached)

        queryset = selectors.search_public_products(
            query=params.get("q"),
            category_slug=params.get("category"),
            category_id=params.get("category_id"),
            min_price=params.get("min_price"),
            max_price=params.get("max_price"),
            available=params.get("available"),
            discount=params.get("discount"),
            is_main_dish=params.get("is_main_dish"),
            sort=params.get("sort"),
        )

        page = paginator.paginate_queryset(queryset, request)
        payload = dict(
            paginator.get_paginated_response(
                ProductSummaryPublicSerializer(page, many=True).data
            ).data
        )
        query = params.get("q")
        if query and paginator.count == 0:
            did_you_mean = selectors.get_did_you_mean(query)
            if did_you_mean:
                payload["did_you_mean"] = did_you_mean
        if cache_enabled and cache_key:
            set_cached_response(cache_key, payload, timeout=ttl)
        return Response(payload)


class ProductSuggestionsView(StorefrontAPIView):
    """
    Autocomplete backend. Reuses the same search pipeline as ProductListView.

    A blank/whitespace query returns an empty result set (not the whole
    catalog); the requested ``limit`` is clamped to the configured maximum.
    Name prefix and trigram matching are both index-backed. When the query has
    no match, the closest product/category name is reported as
    ``did_you_mean`` (PostgreSQL trigram similarity).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ProductSuggestionThrottle]

    @extend_schema(
        tags=["Storefront — Catalog"],
        operation_id="storefront_catalog_suggestions",
        summary="Autocomplete product suggestions",
        description=(
            "Minimal product rows ordered by trigram relevance and popularity. "
            "Blank q returns an empty list. Prefix matching and trigram "
            "similarity use the catalog GIN indexes; if no row matches, the "
            "closest product or category name is returned in did_you_mean "
            "(null when nothing is close enough)."
        ),
        parameters=[
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                description=f"Partial product name (max {MAX_SEARCH_LENGTH} chars).",
            ),
            OpenApiParameter(
                "limit",
                OpenApiTypes.INT,
                description=(
                    "Requested number of rows; clamped to "
                    "PRODUCT_SUGGESTIONS_MAX_LIMIT (10 by default)."
                ),
            ),
        ],
        responses={
            200: ProductSuggestionListResponseSerializer,
            400: ErrorEnvelopeSerializer,
            429: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        serializer = ProductSuggestionQuerySerializer(
            data=request.query_params.dict()
        )
        serializer.is_valid(raise_exception=True)

        max_limit = getattr(settings, "PRODUCT_SUGGESTIONS_MAX_LIMIT", 10)
        default_limit = getattr(settings, "PRODUCT_SUGGESTIONS_DEFAULT_LIMIT", 5)
        limit = min(serializer.validated_data.get("limit", default_limit), max_limit)
        query = serializer.validated_data.get("q")

        ttl = getattr(settings, "CATALOG_SUGGEST_CACHE_TTL", 120)
        cache_enabled = (
            getattr(settings, "CATALOG_SUGGEST_CACHE_ENABLED", True) and ttl > 0
        )
        cache_key = None
        if cache_enabled:
            cache_key = build_search_cache_key(
                "suggestions",
                {
                    "q": normalize_search_query(query),
                    "limit": limit,
                },
            )
            cached = get_cached_response(cache_key)
            if cached is not None:
                return Response(cached)

        queryset, did_you_mean = selectors.suggest_public_products_with_correction(
            query=query,
            limit=limit,
        )
        payload = {
            "results": ProductSuggestionPublicSerializer(queryset, many=True).data,
            "did_you_mean": did_you_mean,
        }
        if cache_enabled and cache_key:
            set_cached_response(cache_key, payload, timeout=ttl)
        return Response(payload)


class ProductDetailView(StorefrontAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — Catalog"],
        operation_id="storefront_catalog_product_detail",
        summary="Retrieve a public product by slug",
        responses={
            200: ProductDetailPublicSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, slug: str) -> Response:
        product = selectors.get_storefront_product(slug)
        return Response(ProductDetailPublicSerializer(product).data)