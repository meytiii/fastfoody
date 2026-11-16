from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_WEBP_QUALITY = 85


def convert_image_to_webp(
    image_field: Any,
    quality: int = DEFAULT_WEBP_QUALITY,
) -> ContentFile:
    """Return a ContentFile holding the WebP version of an ImageField's file."""
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


def generate_webp_for_field(
    instance: Any,
    *,
    source_field: str = "image",
    target_field: str = "webp_image",
    quality: int = DEFAULT_WEBP_QUALITY,
) -> bool:
    """Best-effort: convert source image to WebP and save on target field."""
    source = getattr(instance, source_field)
    if not source:
        return False
    try:
        content = convert_image_to_webp(source, quality=quality)
        target = getattr(instance, target_field)
        target.save(content.name, content, save=False)
        instance.save(update_fields=[target_field, "updated_at"])
        return True
    except Exception:  # noqa: BLE001
        logger.warning(
            "WebP conversion failed for %s.%s (pk=%s); original kept.",
            instance.__class__.__name__,
            source_field,
            instance.pk,
            exc_info=True,
        )
        return False