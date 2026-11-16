from __future__ import annotations

from typing import Any

from django.core.cache import cache
from django.db.models import Prefetch, Q, QuerySet

from .constants import CACHE_KEY_LUCKY_WHEEL, CACHE_KEY_MENU, CACHE_TIMEOUT_SECONDS
from .exceptions import CategoryNotFoundError, ProductNotFoundError
from .models import AddOn, Category, Product, ProductAddOn


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