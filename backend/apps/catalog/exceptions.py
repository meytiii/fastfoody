from __future__ import annotations

from common.exceptions import NotFoundError, ValidationError


class CategoryNotFoundError(NotFoundError):
    default_code = "CATEGORY_NOT_FOUND"
    default_message = "دسته‌بندی یافت نشد."


class ProductNotFoundError(NotFoundError):
    default_code = "PRODUCT_NOT_FOUND"
    default_message = "محصول یافت نشد."


class AddOnNotFoundError(NotFoundError):
    default_code = "ADDON_NOT_FOUND"
    default_message = "افزودنی یافت نشد."


class SlugAlreadyExistsError(ValidationError):
    default_code = "SLUG_ALREADY_EXISTS"
    default_message = "این نامک (slug) قبلاً استفاده شده است."


class CategoryHasProductsError(ValidationError):
    default_code = "CATEGORY_HAS_PRODUCTS"
    default_message = "این دسته‌بندی دارای محصول فعال است و قابل حذف نیست."


class CategoryHasChildrenError(ValidationError):
    default_code = "CATEGORY_HAS_CHILDREN"
    default_message = (
        "این دسته‌بندی دارای زیردسته فعال است؛ ابتدا زیردسته‌ها را حذف یا جابه‌جا کنید."
    )


class CategoryHierarchyError(ValidationError):
    default_code = "INVALID_CATEGORY_HIERARCHY"
    default_message = "ساختار دسته‌بندی نامعتبر است."