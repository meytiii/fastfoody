from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch, Q, QuerySet

from .constants import (
    CACHE_KEY_LUCKY_WHEEL,
    CACHE_KEY_MENU,
    CACHE_KEY_SEARCH_VOCAB,
    CACHE_TIMEOUT_SECONDS,
)
from .exceptions import CategoryNotFoundError, ProductNotFoundError
from .models import AddOn, Category, Product, ProductAddOn
from .search import (
    apply_filters,
    apply_ordering,
    build_relevance_ordering,
    build_search_filter,
    correct_search_term,
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
        .order_by("display_order", "name")
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


def _category_subtree_ids(root: Category) -> set[int]:
    """
    Return ``root`` plus all of its active descendants.

    The category table is small, so one flat query + an in-memory traversal is
    cheaper and more portable than a recursive CTE (works identically on SQLite
    and PostgreSQL). Inactive children are excluded: filtering a parent must
    never reveal products of a hidden category.
    """
    edges: dict[int | None, list[int]] = {}
    for pk, parent_id in Category.objects.filter(is_active=True).values_list(
        "id", "parent_id"
    ):
        edges.setdefault(parent_id, []).append(pk)

    result: set[int] = set()
    stack = [root.pk]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(edges.get(current, ()))
    return result


def search_public_products(
    *,
    query: str | None = None,
    category_slug: str | None = None,
    category_id: int | None = None,
    include_subcategories: bool = True,
    min_price: int | None = None,
    max_price: int | None = None,
    available: bool | None = None,
    in_stock: bool | None = None,
    discount: bool | None = None,
    is_main_dish: bool | None = None,
    sort: str | None = None,
) -> QuerySet[Product]:
    """
    Apply the public visibility rules, then search, filters and ordering.

    Shared by the storefront product listing (paginated) and the autocomplete
    endpoint (limited), so both always agree on what is discoverable. Filtering
    by a parent category includes its active descendants by default; pass
    ``include_subcategories=False`` to address exactly one category.
    """
    category_ids: set[int] | None = None
    if category_slug or category_id is not None:
        category = _get_public_category(
            category_slug=category_slug, category_id=category_id
        )
        category_ids = (
            _category_subtree_ids(category)
            if include_subcategories
            else {category.pk}
        )

    term = normalize_search_query(query)
    qs = get_public_product_queryset()
    qs = apply_filters(
        qs,
        category_ids=category_ids,
        min_price=min_price,
        max_price=max_price,
        available=available,
        in_stock=in_stock,
        discount=discount,
        is_main_dish=is_main_dish,
    )
    if term:
        qs = qs.filter(build_search_filter(term))
    return apply_ordering(qs, sort=sort, term=term)


def get_search_vocabulary() -> list[str]:
    """
    Distinct product-name words used by the typo-tolerance fallback.

    Built once per cache window (1 hour) and invalidated with the rest of the
    catalog cache, so a new product does not stay invisible to autocomplete.
    """
    cached = cache.get(CACHE_KEY_SEARCH_VOCAB)
    if cached is not None:
        return cached

    limit = getattr(settings, "CATALOG_SEARCH_VOCAB_LIMIT", 2000)
    names = get_public_product_queryset().values_list("name", flat=True)[:limit]
    vocabulary = sorted(
        {
            word.lower()
            for name in names
            for word in normalize_search_query(name).split()
            if len(word) >= 3 and not word.isdigit()
        }
    )
    cache.set(CACHE_KEY_SEARCH_VOCAB, vocabulary, timeout=CACHE_TIMEOUT_SECONDS)
    return vocabulary


def _suggestion_queryset(term: str, limit: int) -> QuerySet[Product]:
    # ``only()`` cannot be combined with ``select_related("category")`` (the
    # joined FK would be both deferred and traversed), so the suggestion query
    # drops the join and selects exactly the columns it returns.
    qs = (
        get_public_product_queryset()
        .select_related(None)
        .filter(build_search_filter(term))
    )
    qs = qs.order_by(*build_relevance_ordering(term))
    return qs.only(
        "id",
        "name",
        "slug",
        "price",
        "compare_at_price",
        "stock_quantity",
        "status",
        "image",
        "webp_image",
    )[:limit]


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
    Autocomplete with a bounded typo-tolerance fallback.

    The normal path is exactly one query. Only when that query yields nothing
    (and fuzzy search is enabled) is the vocabulary consulted, and the result
    is a single corrected term — never a per-row scan of the catalog. Returns
    ``(queryset, did_you_mean)``; ``did_you_mean`` is ``None`` when no correction
    produced results.
    """
    term = normalize_search_query(query)
    if not term:
        return Product.objects.none(), None

    queryset = _suggestion_queryset(term, limit)
    if not getattr(settings, "CATALOG_SEARCH_FUZZY_ENABLED", False):
        return queryset, None
    if queryset.exists():
        return queryset, None

    corrected = correct_search_term(term, get_search_vocabulary())
    if not corrected:
        return queryset, None

    corrected_queryset = _suggestion_queryset(corrected, limit)
    if not corrected_queryset.exists():
        return queryset, None
    return corrected_queryset, corrected


# ---------------------------------------------------------------------------
# Backoffice reads
# ---------------------------------------------------------------------------
def list_categories_backoffice(
    *, is_active: bool | None = None
) -> QuerySet[Category]:
    qs = Category.objects.all().order_by("display_order", "name")
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