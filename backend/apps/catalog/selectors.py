from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.core.cache import cache
from django.db.models import Prefetch, Q, QuerySet

from .constants import (
    CACHE_KEY_LUCKY_WHEEL,
    CACHE_KEY_MENU,
    CACHE_KEY_UPSELL,
    CACHE_TIMEOUT_SECONDS,
)
from .exceptions import CategoryNotFoundError, ProductNotFoundError
from .models import AddOn, Category, Product, ProductAddOn
from .search import (
    AUTOCOMPLETE_ORDERING,
    annotate_sales_count,
    apply_autocomplete,
    apply_filters,
    apply_ordering,
    apply_search,
    normalize_search_query,
)


# ---------------------------------------------------------------------------
# Helpers — build dicts for cache-safe serialization
# ---------------------------------------------------------------------------
def _image_url(image: Any, webp: Any) -> str | None:
    if webp:
        return webp.url
    if image:
        return image.url
    return None


def _product_menu_dict(product: Product) -> dict[str, Any]:
    return {
        "id": product.pk,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "status": product.status,
        "is_main_dish": product.is_main_dish,
        "prep_time_minutes": product.prep_time_minutes,
        "image_url": _image_url(product.image, product.webp_image),
    }


def _category_menu_dict(category: Category) -> dict[str, Any]:
    return {
        "id": category.pk,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "image_url": _image_url(category.image, category.webp_image),
        "products": [_product_menu_dict(p) for p in category.products.all()],
    }


def _alive_addons_prefetch() -> Prefetch:
    return Prefetch(
        "addon_links",
        queryset=ProductAddOn.objects.select_related("addon")
        .filter(
            addon__is_available=True,
            addon__deleted_at__isnull=True,
        )
        .order_by("addon__name"),
    )


# ---------------------------------------------------------------------------
# Storefront — cached menu & lucky wheel
# ---------------------------------------------------------------------------
def get_storefront_menu() -> dict[str, Any]:
    cached = cache.get(CACHE_KEY_MENU)
    if cached is not None:
        return cached

    categories_qs = (
        Category.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.exclude(
                    status=Product.Status.HIDDEN
                ).order_by("display_order", "name"),
            )
        )
        .order_by("display_order", "id")
    )

    payload = {"categories": [_category_menu_dict(c) for c in categories_qs]}
    cache.set(CACHE_KEY_MENU, payload, timeout=CACHE_TIMEOUT_SECONDS)
    return payload


def get_lucky_wheel_products(*, category_slug: str | None = None) -> dict[str, Any]:
    cache_key = (
        CACHE_KEY_LUCKY_WHEEL
        if not category_slug
        else f"{CACHE_KEY_LUCKY_WHEEL}:{category_slug}"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = Product.objects.filter(
        status=Product.Status.AVAILABLE,
        is_main_dish=True,
        category__is_active=True,
    ).select_related("category")

    if category_slug:
        if not Category.objects.filter(
            slug=category_slug, is_active=True
        ).exists():
            raise CategoryNotFoundError()
        qs = qs.filter(category__slug=category_slug)

    products = [
        {
            "id": p.pk,
            "name": p.name,
            "slug": p.slug,
            "price": p.price,
            "category_id": p.category_id,
            "image_url": _image_url(p.image, p.webp_image),
        }
        for p in qs
    ]

    payload = {"products": products}
    cache.set(cache_key, payload, timeout=CACHE_TIMEOUT_SECONDS)
    return payload


UPSELL_LIMIT = 8


def get_upsell_products() -> dict[str, Any]:
    """
    Cached cart-upsell list: available sides and drinks, most ordered first.

    Only products that are AVAILABLE, not main dishes, and in an active
    category qualify. Ordering uses the paid-order quantity aggregated by
    ``annotate_sales_count`` and then ``display_order``.
    """
    cached = cache.get(CACHE_KEY_UPSELL)
    if cached is not None:
        return cached

    queryset = (
        annotate_sales_count(get_public_product_queryset())
        .filter(
            status=Product.Status.AVAILABLE,
            is_main_dish=False,
        )
        .order_by("-sales_count", "display_order", "name", "pk")[:UPSELL_LIMIT]
    )

    products = [
        {
            "id": product.pk,
            "name": product.name,
            "slug": product.slug,
            "price": product.price,
            "compare_at_price": product.compare_at_price,
            "discount_percent": product.discount_percent,
            "status": product.status,
            "image_url": _image_url(product.image, product.webp_image),
            "category_id": product.category_id,
        }
        for product in queryset
    ]

    payload = {"products": products}
    cache.set(CACHE_KEY_UPSELL, payload, timeout=CACHE_TIMEOUT_SECONDS)
    return payload


# ---------------------------------------------------------------------------
# Storefront — product detail (uncached; cheap single query)
# ---------------------------------------------------------------------------
def get_storefront_product(slug: str) -> Product:
    try:
        return (
            Product.objects.exclude(status=Product.Status.HIDDEN)
            .select_related("category")
            .prefetch_related(_alive_addons_prefetch())
            .get(slug=slug)
        )
    except Product.DoesNotExist:
        raise ProductNotFoundError()


# ---------------------------------------------------------------------------
# Storefront — public product discovery (search / filter / sort)
# ---------------------------------------------------------------------------
def get_public_product_queryset() -> QuerySet[Product]:
    """
    Single source of truth for publicly discoverable products.

    Mirrors the storefront menu rules: the product must be alive (default
    manager), not HIDDEN, and belong to an active, non-deleted category.
    HIDDEN products can therefore never be reached through search or filters.
    """
    return (
        Product.objects.select_related("category")
        .filter(
            category__is_active=True,
            category__deleted_at__isnull=True,
        )
        .exclude(status=Product.Status.HIDDEN)
    )


def _get_public_category(
    *,
    category_slug: str | None = None,
    category_id: int | None = None,
) -> Category:
    """Return the active, alive category addressed by slug and/or id, else 404."""
    lookup: dict[str, Any] = {}
    if category_slug:
        lookup["slug"] = category_slug
    if category_id is not None:
        lookup["pk"] = category_id
    try:
        return Category.objects.get(is_active=True, **lookup)
    except Category.DoesNotExist:
        raise CategoryNotFoundError()


def search_public_products(
    *,
    query: str | None = None,
    category_slug: str | None = None,
    category_id: int | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    available: bool | None = None,
    discount: bool | None = None,
    is_main_dish: bool | None = None,
    sort: str | None = None,
) -> QuerySet[Product]:
    """
    Apply the public visibility rules, then PostgreSQL search, filters, ordering.

    Shared by the storefront product listing (paginated) and the autocomplete
    endpoint (limited), so both always agree on what is discoverable.
    Categories are flat, so filtering addresses exactly one category.
    """
    if category_slug or category_id is not None:
        category = _get_public_category(
            category_slug=category_slug, category_id=category_id
        )
        category_id = category.pk
        category_slug = None

    term = normalize_search_query(query)
    qs = get_public_product_queryset()
    qs = apply_filters(
        qs,
        category_slug=category_slug,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        available=available,
        discount=discount,
        is_main_dish=is_main_dish,
    )
    if term:
        qs = apply_search(qs, term)
    return apply_ordering(qs, sort=sort, term=term)


def _suggestion_queryset(term: str, limit: int) -> QuerySet[Product]:
    # ``only()`` cannot be combined with ``select_related("category")`` (the
    # joined FK would be both deferred and traversed), so the suggestion query
    # drops the join and selects exactly the columns it returns.
    qs = apply_autocomplete(
        get_public_product_queryset().select_related(None), term
    )
    qs = annotate_sales_count(qs).order_by(*AUTOCOMPLETE_ORDERING)
    return qs.only(
        "id",
        "name",
        "slug",
        "price",
        "compare_at_price",
        "status",
        "image",
        "webp_image",
    )[:limit]


def get_did_you_mean(term: str) -> str | None:
    """
    Closest product or category name for a query that returned no rows.

    ``TrigramSimilarity`` runs in PostgreSQL over product and category names;
    only the single best candidate is returned, and the function is intended
    for the empty-result path so the normal search stays one query.
    """
    normalized = normalize_search_query(term)
    if len(normalized) < 2:
        return None

    threshold = float(getattr(settings, "CATALOG_DID_YOU_MEAN_THRESHOLD", 0.25))
    product_candidate = (
        get_public_product_queryset()
        .exclude(name__iexact=normalized)
        .annotate(similarity=TrigramSimilarity("name", normalized))
        .filter(similarity__gte=threshold)
        .order_by("-similarity", "name")
        .values("name", "similarity")
        .first()
    )
    category_candidate = (
        Category.objects.filter(is_active=True)
        .exclude(name__iexact=normalized)
        .annotate(similarity=TrigramSimilarity("name", normalized))
        .filter(similarity__gte=threshold)
        .order_by("-similarity", "name")
        .values("name", "similarity")
        .first()
    )

    candidates = [row for row in (product_candidate, category_candidate) if row]
    if not candidates:
        return None
    best = max(candidates, key=lambda row: row["similarity"])
    return str(best["name"])


def suggest_public_products(
    *,
    query: str | None,
    limit: int,
) -> QuerySet[Product]:
    """
    Relevance-ordered suggestion candidates for autocomplete.

    Loads only the columns the suggestion serializer returns; an empty or
    whitespace-only query yields an empty queryset instead of the whole catalog.
    """
    term = normalize_search_query(query)
    if not term:
        return Product.objects.none()
    return _suggestion_queryset(term, limit)


def suggest_public_products_with_correction(
    *,
    query: str | None,
    limit: int,
) -> tuple[QuerySet[Product], str | None]:
    """
    Autocomplete with PostgreSQL-backed "did you mean" correction.

    The normal path is a single trigram/prefix query. Only when it yields no
    rows is ``get_did_you_mean`` consulted, which returns the closest product
    or category name (or ``None``). Returns ``(queryset, did_you_mean)``.
    """
    term = normalize_search_query(query)
    if not term:
        return Product.objects.none(), None

    queryset = _suggestion_queryset(term, limit)
    if queryset.exists():
        return queryset, None

    return queryset, get_did_you_mean(term)


# ---------------------------------------------------------------------------
# Backoffice reads
# ---------------------------------------------------------------------------
def list_categories_backoffice(
    *, is_active: bool | None = None
) -> QuerySet[Category]:
    qs = Category.objects.all().order_by("display_order", "id")
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def get_category_backoffice(category_id: int) -> Category:
    try:
        return Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        raise CategoryNotFoundError()


def list_products_backoffice(
    *,
    category_id: int | None = None,
    status: str | None = None,
    is_main_dish: bool | None = None,
    search: str | None = None,
) -> QuerySet[Product]:
    qs = (
        Product.objects.all()
        .select_related("category")
        .order_by("display_order", "name")
    )
    if category_id is not None:
        qs = qs.filter(category_id=category_id)
    if status is not None:
        qs = qs.filter(status=status)
    if is_main_dish is not None:
        qs = qs.filter(is_main_dish=is_main_dish)
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))
    return qs


def get_product_backoffice(product_id: int) -> Product:
    try:
        return (
            Product.objects.select_related("category")
            .prefetch_related(
                Prefetch(
                    "addon_links",
                    queryset=ProductAddOn.objects.select_related("addon").order_by(
                        "addon__name"
                    ),
                )
            )
            .get(pk=product_id)
        )
    except Product.DoesNotExist:
        raise ProductNotFoundError()


def list_addons_backoffice(
    *, is_available: bool | None = None
) -> QuerySet[AddOn]:
    qs = AddOn.objects.all().order_by("name")
    if is_available is not None:
        qs = qs.filter(is_available=is_available)
    return qs


def get_addon_backoffice(addon_id: int) -> AddOn:
    try:
        return AddOn.objects.get(pk=addon_id)
    except AddOn.DoesNotExist:
        from .exceptions import AddOnNotFoundError

        raise AddOnNotFoundError()