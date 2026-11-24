from __future__ import annotations

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog import selectors
from apps.catalog.search import MAX_PRICE_FILTER, MAX_SEARCH_LENGTH, SORT_CHOICES
from apps.catalog.throttles import ProductSearchThrottle, ProductSuggestionThrottle

from .serializers import (
    ProductDetailPublicSerializer,
    ProductListResponseSerializer,
    ProductSearchQuerySerializer,
    ProductSuggestionListResponseSerializer,
    ProductSuggestionPublicSerializer,
    ProductSuggestionQuerySerializer,
    ProductSummaryPublicSerializer,
)

_SEARCH_PARAMETERS = [
    OpenApiParameter(
        "q",
        OpenApiTypes.STR,
        description=(
            "Free-text search (max 100 chars). Every word must match the name, "
            "slug, description or category name. Persian/Arabic letter variants "
            "and the built-in synonym groups are handled server-side."
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
        "include_subcategories",
        OpenApiTypes.BOOL,
        description=(
            "Default true: filtering a parent category also returns products of "
            "its active descendants."
        ),
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
        "in_stock",
        OpenApiTypes.BOOL,
        description=(
            "Effective purchasability: AVAILABLE and (stock not tracked or "
            "stock_quantity > 0)."
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
        "limit", OpenApiTypes.INT, description="Page size (LimitOffsetPagination)."
    ),
    OpenApiParameter(
        "offset", OpenApiTypes.INT, description="Page offset (LimitOffsetPagination)."
    ),
]


class MenuView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(selectors.get_storefront_menu())


class LuckyWheelView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        category_slug = request.query_params.get("category")
        return Response(
            selectors.get_lucky_wheel_products(category_slug=category_slug)
        )


class ProductListView(APIView):
    """
    Public product discovery: search, filters and sorting in one pipeline.

    Uses the project-wide ``LimitOffsetPagination``; the paginator rebuilds
    ``next``/``previous`` links from the request, so every filter and sort
    parameter survives pagination.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ProductSearchThrottle]

    @extend_schema(
        tags=["storefront-catalog"],
        summary="Search and filter public products",
        description=(
            "Returns paginated, publicly visible products (not HIDDEN, active "
            "category). Search words are AND-ed across name, slug, description "
            "and category name; Persian/Arabic letter variants and synonym "
            "groups are applied server-side. Invalid parameters return 400 with "
            "the standard error envelope."
        ),
        parameters=_SEARCH_PARAMETERS,
        responses={200: ProductListResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        # A plain dict (not QueryDict) keeps DRF from applying HTML-form
        # semantics, which would turn absent booleans into False.
        serializer = ProductSearchQuerySerializer(data=request.query_params.dict())
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        queryset = selectors.search_public_products(
            query=params.get("q"),
            category_slug=params.get("category"),
            category_id=params.get("category_id"),
            include_subcategories=params.get("include_subcategories", True),
            min_price=params.get("min_price"),
            max_price=params.get("max_price"),
            available=params.get("available"),
            in_stock=params.get("in_stock"),
            discount=params.get("discount"),
            is_main_dish=params.get("is_main_dish"),
            sort=params.get("sort"),
        )

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            ProductSummaryPublicSerializer(page, many=True).data
        )


class ProductSuggestionsView(APIView):
    """
    Autocomplete backend. Reuses the same search pipeline as ProductListView.

    A blank/whitespace query returns an empty result set (not the whole
    catalog); the requested ``limit`` is clamped to the configured maximum.
    When the query has no match and typo tolerance is enabled, one bounded
    correction is attempted and reported as ``did_you_mean``.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ProductSuggestionThrottle]

    @extend_schema(
        tags=["storefront-catalog"],
        summary="Autocomplete product suggestions",
        description=(
            "Minimal product rows ordered by relevance. Blank q returns an "
            "empty list. If no row matches and typo tolerance is enabled, the "
            "closest product words are tried once and returned in "
            "did_you_mean (null when no correction matched)."
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
        responses={200: ProductSuggestionListResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        serializer = ProductSuggestionQuerySerializer(
            data=request.query_params.dict()
        )
        serializer.is_valid(raise_exception=True)

        max_limit = getattr(settings, "PRODUCT_SUGGESTIONS_MAX_LIMIT", 10)
        default_limit = getattr(settings, "PRODUCT_SUGGESTIONS_DEFAULT_LIMIT", 5)
        limit = min(serializer.validated_data.get("limit", default_limit), max_limit)

        queryset, did_you_mean = selectors.suggest_public_products_with_correction(
            query=serializer.validated_data.get("q"),
            limit=limit,
        )
        return Response(
            {
                "results": ProductSuggestionPublicSerializer(
                    queryset, many=True
                ).data,
                "did_you_mean": did_you_mean,
            }
        )


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["storefront-catalog"],
        summary="Retrieve a public product by slug",
        responses={200: ProductDetailPublicSerializer},
    )
    def get(self, request: Request, slug: str) -> Response:
        product = selectors.get_storefront_product(slug)
        return Response(ProductDetailPublicSerializer(product).data)