from __future__ import annotations

import logging
from typing import Any

from django.core.cache import cache
from django.db import transaction

from common.exceptions import ValidationError
from common.images import generate_webp_for_field

from .cache import bump_search_cache_version
from .constants import (
    CACHE_KEY_LUCKY_WHEEL,
    CACHE_KEY_MENU,
    CACHE_KEY_SEARCH_VOCAB,
    CACHE_KEY_UPSELL,
)
from .exceptions import (
    AddOnNotFoundError,
    CategoryHasProductsError,
    CategoryNotFoundError,
    ProductNotFoundError,
    SlugAlreadyExistsError,
)
from .indexing import refresh_product_search_index, refresh_products_search_index
from .models import AddOn, Category, Product, ProductAddOn, ProductSearchToken

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------
def _invalidate_catalog_cache() -> None:
    cache.delete(CACHE_KEY_MENU)
    cache.delete(CACHE_KEY_LUCKY_WHEEL)
    cache.delete(CACHE_KEY_SEARCH_VOCAB)
    cache.delete(CACHE_KEY_UPSELL)
    # ``get_lucky_wheel_products`` writes one key per category; those derived
    # keys must be cleared too or they stay stale until the timeout expires.
    for slug in Category.all_objects.values_list("slug", flat=True):
        cache.delete(f"{CACHE_KEY_LUCKY_WHEEL}:{slug}")
    # Cached list/search pages include filters, sorting and pagination. Bumping
    # the generation is cheaper and safer than enumerating every key.
    bump_search_cache_version()


def _validate_pricing(*, price: int, compare_at_price: int | None) -> None:
    """Guard the DB check constraint with a proper API error."""
    if compare_at_price is not None and compare_at_price <= price:
        raise ValidationError(
            message="قیمت قبل از تخفیف باید بیشتر از قیمت فروش باشد.",
            code="INVALID_PRICE",
            details={
                "compare_at_price": "قیمت قبل از تخفیف باید بیشتر از قیمت فروش باشد."
            },
        )


def _schedule_invalidation() -> None:
    transaction.on_commit(_invalidate_catalog_cache)


# ---------------------------------------------------------------------------
# Category services
# ---------------------------------------------------------------------------
@transaction.atomic
def create_category(*, data: dict[str, Any]) -> Category:
    if Category.objects.filter(slug=data["slug"]).exists():
        raise SlugAlreadyExistsError()

    image = data.pop("image", None)

    category = Category(**data)
    if image:
        category.image = image
    category.save()

    if image:
        generate_webp_for_field(category)

    _schedule_invalidation()
    return category


@transaction.atomic
def update_category(*, category_id: int, data: dict[str, Any]) -> Category:
    try:
        category = Category.objects.select_for_update().get(pk=category_id)
    except Category.DoesNotExist:
        raise CategoryNotFoundError()

    image = data.pop("image", None)
    searchable_category_change = any(
        field in data and data[field] != getattr(category, field)
        for field in ("name", "slug")
    )

    if "slug" in data and data["slug"] != category.slug:
        if Category.objects.filter(slug=data["slug"]).exclude(pk=category.pk).exists():
            raise SlugAlreadyExistsError()

    for field, value in data.items():
        setattr(category, field, value)
    if data:
        category.save(update_fields=list(data.keys()) + ["updated_at"])

    if image is not None:
        category.image = image
        category.save(update_fields=["image", "updated_at"])
        generate_webp_for_field(category)

    if searchable_category_change:
        # Category names are part of every product's search index.
        refresh_products_search_index(
            Product.objects.filter(category=category).select_related("category")
        )

    _schedule_invalidation()
    return category


@transaction.atomic
def delete_category(*, category_id: int) -> None:
    try:
        category = Category.objects.select_for_update().get(pk=category_id)
    except Category.DoesNotExist:
        raise CategoryNotFoundError()

    if Product.objects.filter(category=category).exists():
        raise CategoryHasProductsError()

    category.soft_delete()
    _schedule_invalidation()


# ---------------------------------------------------------------------------
# AddOn services
# ---------------------------------------------------------------------------
@transaction.atomic
def create_addon(*, data: dict[str, Any]) -> AddOn:
    addon = AddOn.objects.create(**data)
    _schedule_invalidation()
    return addon


@transaction.atomic
def update_addon(*, addon_id: int, data: dict[str, Any]) -> AddOn:
    try:
        addon = AddOn.objects.select_for_update().get(pk=addon_id)
    except AddOn.DoesNotExist:
        raise AddOnNotFoundError()

    for field, value in data.items():
        setattr(addon, field, value)
    addon.save(update_fields=list(data.keys()) + ["updated_at"])

    _schedule_invalidation()
    return addon


@transaction.atomic
def delete_addon(*, addon_id: int) -> None:
    try:
        addon = AddOn.objects.select_for_update().get(pk=addon_id)
    except AddOn.DoesNotExist:
        raise AddOnNotFoundError()

    ProductAddOn.objects.filter(addon=addon).delete()
    addon.soft_delete()
    _schedule_invalidation()


# ---------------------------------------------------------------------------
# Product services
# ---------------------------------------------------------------------------
def _resolve_category(*, category_id: int) -> Category:
    try:
        return Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        raise CategoryNotFoundError()


def _set_product_addons(
    product: Product,
    addon_links: list[dict[str, Any]],
) -> None:
    ProductAddOn.objects.filter(product=product).delete()

    if not addon_links:
        return

    addon_ids = [link["addon_id"] for link in addon_links]
    if len(set(addon_ids)) != len(addon_ids):
        raise ValidationError(
            message="افزودنی تکراری در لیست وجود دارد.",
            details={"addons": "هر افزودنی فقط یک بار مجاز است."},
        )

    existing = set(
        AddOn.objects.filter(pk__in=addon_ids).values_list("pk", flat=True)
    )
    missing = sorted(set(addon_ids) - existing)
    if missing:
        raise AddOnNotFoundError(
            message=f"افزودنی‌های زیر یافت نشدند: {missing}",
            details={"addon_ids": missing},
        )

    for link in addon_links:
        ProductAddOn.objects.create(
            product=product,
            addon_id=link["addon_id"],
            min_quantity=link.get("min_quantity", 0),
            max_quantity=link.get("max_quantity", 5),
        )


@transaction.atomic
def create_product(*, data: dict[str, Any]) -> Product:
    addon_links = data.pop("addons", None) or []
    image = data.pop("image", None)

    category = _resolve_category(category_id=data.pop("category_id"))

    if Product.objects.filter(slug=data["slug"]).exists():
        raise SlugAlreadyExistsError()

    _validate_pricing(
        price=data["price"], compare_at_price=data.get("compare_at_price")
    )

    product = Product(category=category, **data)
    if image:
        product.image = image
    product.save()

    if image:
        generate_webp_for_field(product)

    _set_product_addons(product, addon_links)
    refresh_product_search_index(product)
    _schedule_invalidation()
    return product


@transaction.atomic
def update_product(*, product_id: int, data: dict[str, Any]) -> Product:
    addon_links_provided = "addons" in data
    addon_links = data.pop("addons", None) or []
    image = data.pop("image", None)

    if "category_id" in data:
        category = _resolve_category(category_id=data.pop("category_id"))
        data["category"] = category

    try:
        product = Product.objects.select_for_update().get(pk=product_id)
    except Product.DoesNotExist:
        raise ProductNotFoundError()

    if "slug" in data and data["slug"] != product.slug:
        if Product.objects.filter(slug=data["slug"]).exclude(pk=product.pk).exists():
            raise SlugAlreadyExistsError()

    _validate_pricing(
        price=data.get("price", product.price),
        compare_at_price=data.get("compare_at_price", product.compare_at_price),
    )

    if data:
        for field, value in data.items():
            setattr(product, field, value)
        product.save(update_fields=list(data.keys()) + ["updated_at"])

    if image is not None:
        product.image = image
        product.save(update_fields=["image", "updated_at"])
        generate_webp_for_field(product)

    if addon_links_provided:
        _set_product_addons(product, addon_links)

    refresh_product_search_index(product)
    _schedule_invalidation()
    return product


@transaction.atomic
def delete_product(*, product_id: int) -> None:
    try:
        product = Product.objects.select_for_update().get(pk=product_id)
    except Product.DoesNotExist:
        raise ProductNotFoundError()

    ProductAddOn.objects.filter(product=product).delete()
    ProductSearchToken.objects.filter(product=product).delete()
    product.soft_delete()
    _schedule_invalidation()


@transaction.atomic
def set_product_image(*, product_id: int, image: Any) -> Product:
    try:
        product = Product.objects.select_for_update().get(pk=product_id)
    except Product.DoesNotExist:
        raise ProductNotFoundError()

    product.image = image
    product.save(update_fields=["image", "updated_at"])
    generate_webp_for_field(product)

    _schedule_invalidation()
    return product


@transaction.atomic
def set_product_addons(
    *, product_id: int, addon_links: list[dict[str, Any]]
) -> Product:
    try:
        product = Product.objects.select_for_update().get(pk=product_id)
    except Product.DoesNotExist:
        raise ProductNotFoundError()

    _set_product_addons(product, addon_links)
    _schedule_invalidation()
    return product