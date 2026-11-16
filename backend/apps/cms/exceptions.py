from __future__ import annotations

from common.exceptions import NotFoundError, ValidationError


class SiteSectionNotFoundError(NotFoundError):
    default_code = "SITE_SECTION_NOT_FOUND"
    default_message = "بخش مورد نظر یافت نشد."


class InvalidSiteSectionKeyError(ValidationError):
    default_code = "INVALID_SITE_SECTION_KEY"
    default_message = "کلید بخش نامعتبر است."


class MediaAssetConversionError(ValidationError):
    default_code = "MEDIA_ASSET_CONVERSION_ERROR"
    default_message = "پردازش تصویر با خطا مواجه شد."