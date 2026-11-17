from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image

from common.cache import make_cache_key

from .constants import ALLOWED_SITE_SECTION_KEYS
from .exceptions import InvalidSiteSectionKeyError
from .models import MediaAsset, RestaurantSettings, SiteSection
from .selectors import (
    ALL_SITE_SECTIONS_CACHE_KEY,
    SETTINGS_CACHE_KEY,
    _site_section_cache_key,
)

logger = logging.getLogger(__name__)

_WEBP_QUALITY = 85


# ---------------------------------------------------------------------------
# RestaurantSettings
# ---------------------------------------------------------------------------
_EDITABLE_SETTINGS_FIELDS: frozenset[str] = frozenset(
    {
        "open_time",
        "close_time",
        "is_temporarily_closed",
        "in_zone_delivery_fee",
        "out_zone_delivery_fee",
        "prep_time_buffer_minutes",
    }
)


@transaction.atomic
def update_restaurant_settings(*, data: dict[str, Any]) -> RestaurantSettings:
    """Update the singleton settings; validate then persist."""
    if not data:
        return RestaurantSettings.objects.get(pk=1)

    for field in data:
        if field not in _EDITABLE_SETTINGS_FIELDS:
            raise InvalidSiteSectionKeyError(
                message=f"فیلد قابل ویرایش نیست: {field}",
                details={field: "این فیلد قابل ویرایش نیست."},
            )

    instance = RestaurantSettings.objects.select_for_update().get(pk=1)

    for field, value in data.items():
        setattr(instance, field, value)

    if instance.open_time == instance.close_time:
        raise InvalidSiteSectionKeyError(
            message="زمان باز و بسته شدن نمی‌تواند یکسان باشد.",
            details={"close_time": "زمان بسته شدن نباید با زمان باز شدن برابر باشد."},
        )

    update_fields = list(data.keys())
    if "updated_at" not in update_fields:
        update_fields.append("updated_at")
    instance.save(update_fields=update_fields)

    transaction.on_commit(lambda: cache.delete(SETTINGS_CACHE_KEY))
    return instance


# ---------------------------------------------------------------------------
# SiteSection
# ---------------------------------------------------------------------------
@transaction.atomic
def upsert_site_section(*, key: str, content: dict[str, Any]) -> SiteSection:
    """Create or replace a CMS section, then invalidate its caches."""
    if key not in ALLOWED_SITE_SECTION_KEYS:
        raise InvalidSiteSectionKeyError(
            message=f"کلید بخش نامعتبر است: {key}",
            details={"key": f"'{key}' مجاز نیست."},
        )

    section, _ = SiteSection.objects.update_or_create(
        key=key,
        defaults={"content": content},
    )

    transaction.on_commit(lambda: cache.delete(_site_section_cache_key(key)))
    transaction.on_commit(lambda: cache.delete(ALL_SITE_SECTIONS_CACHE_KEY))
    return section


# ---------------------------------------------------------------------------
# MediaAsset
# ---------------------------------------------------------------------------
def _convert_to_webp(image_field: Any, quality: int = _WEBP_QUALITY) -> ContentFile:
    """Return a ContentFile holding the WebP version of an ImageField file."""
    image_field.open()
    try:
        image = Image.open(image_field)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        buffer = BytesIO()
        image.save(buffer, format="WEBP", quality=quality)
        buffer.seek(0)

        original_name = Path(image_field.name).name
        webp_name = f"{Path(original_name).stem}.webp"
        return ContentFile(buffer.getvalue(), name=webp_name)
    finally:
        image_field.close()


@transaction.atomic
def create_media_asset(
    *,
    kind: str,
    file: Any,
    title: str = "",
    alt_text: str = "",
) -> MediaAsset:
    """Create a MediaAsset and generate the WebP version (best-effort)."""
    asset = MediaAsset(kind=kind, title=title, alt_text=alt_text)
    asset.file = file
    asset.save()

    try:
        webp_content = _convert_to_webp(asset.file)
        asset.webp_file.save(webp_content.name, webp_content, save=False)
        asset.save(update_fields=["webp_file", "updated_at"])
    except Exception:  # noqa: BLE001 - conversion is best-effort
        logger.warning(
            "WebP conversion failed for media asset %s; original file kept.",
            asset.pk,
            exc_info=True,
        )

    return asset


@transaction.atomic
def soft_delete_media_asset(*, asset_id: int) -> None:
    """Soft-delete a MediaAsset (idempotent)."""
    MediaAsset.objects.filter(pk=asset_id).delete()

@transaction.atomic
def update_media_asset(
    *,
    asset_id: int,
    data: dict[str, Any],
) -> MediaAsset:
    from common.exceptions import NotFoundError

    try:
        asset = MediaAsset.objects.select_for_update().get(pk=asset_id)
    except MediaAsset.DoesNotExist:
        raise NotFoundError(
            message="رسانه یافت نشد.",
            code="MEDIA_ASSET_NOT_FOUND",
        )

    editable = {"title", "alt_text"}
    for field, value in data.items():
        if field in editable:
            setattr(asset, field, value)

    asset.save(update_fields=list(data.keys()) + ["updated_at"])
    return asset