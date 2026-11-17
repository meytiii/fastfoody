from __future__ import annotations

from typing import Any

from django.core.cache import cache

from common.cache import make_cache_key

from .constants import ALLOWED_SITE_SECTION_KEYS
from .exceptions import SiteSectionNotFoundError
from .models import MediaAsset, RestaurantSettings, SiteSection

SETTINGS_CACHE_KEY = make_cache_key("cms", "restaurant_settings")
ALL_SITE_SECTIONS_CACHE_KEY = make_cache_key("cms", "site_sections_all")
_CACHE_TIMEOUT = 60 * 60


def _site_section_cache_key(key: str) -> str:
    return make_cache_key("cms", f"site_section_{key}")


def get_restaurant_settings() -> RestaurantSettings:
    """Return the singleton settings, cached for one hour."""
    cached = cache.get(SETTINGS_CACHE_KEY)
    if cached is not None:
        return cached
    instance = RestaurantSettings.objects.get(pk=1)
    cache.set(SETTINGS_CACHE_KEY, instance, timeout=_CACHE_TIMEOUT)
    return instance


def get_restaurant_status() -> dict[str, Any]:
    """Return a serializable status snapshot (used by the Storefront)."""
    settings = get_restaurant_settings()
    return {
        "is_open": settings.is_open(),
        "is_temporarily_closed": settings.is_temporarily_closed,
        "open_time": settings.open_time.strftime("%H:%M"),
        "close_time": settings.close_time.strftime("%H:%M"),
        "in_zone_delivery_fee": settings.in_zone_delivery_fee,
        "out_zone_delivery_fee": settings.out_zone_delivery_fee,
        "prep_time_buffer_minutes": settings.prep_time_buffer_minutes,
    }


def get_site_section(key: str) -> dict[str, Any]:
    """Return the content of a single CMS section, with default fallback."""
    if key not in ALLOWED_SITE_SECTION_KEYS:
        raise SiteSectionNotFoundError()

    cached = cache.get(_site_section_cache_key(key))
    if cached is not None:
        return cached

    try:
        section = SiteSection.objects.get(key=key)
        content: dict[str, Any] = section.content
    except SiteSection.DoesNotExist:
        content = SiteSection.get_default_content(key)

    cache.set(_site_section_cache_key(key), content, timeout=_CACHE_TIMEOUT)
    return content


def get_all_site_sections() -> dict[str, dict[str, Any]]:
    """Return all six allowed sections merged with defaults."""
    cached = cache.get(ALL_SITE_SECTIONS_CACHE_KEY)
    if cached is not None:
        return cached

    result: dict[str, dict[str, Any]] = {
        key: SiteSection.get_default_content(key)
        for key in ALLOWED_SITE_SECTION_KEYS
    }
    for section in SiteSection.objects.all():
        result[section.key] = section.content

    cache.set(ALL_SITE_SECTIONS_CACHE_KEY, result, timeout=_CACHE_TIMEOUT)
    return result


def list_media_assets(kind: str | None = None) -> list[MediaAsset]:
    """List alive media assets, optionally filtered by kind."""
    qs = MediaAsset.objects.all()
    if kind is not None:
        qs = qs.filter(kind=kind)
    return list(qs)


def get_media_asset(asset_id: int) -> MediaAsset:
    from .exceptions import MediaAssetConversionError  # reuse a 404-style error

    try:
        return MediaAsset.objects.get(pk=asset_id)
    except MediaAsset.DoesNotExist:
        from common.exceptions import NotFoundError

        raise NotFoundError(
            message="رسانه یافت نشد.",
            code="MEDIA_ASSET_NOT_FOUND",
        )