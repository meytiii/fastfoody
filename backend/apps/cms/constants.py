from __future__ import annotations

from typing import Any

ALLOWED_SITE_SECTION_KEYS: frozenset[str] = frozenset(
    {
        "hero",
        "header",
        "footer",
        "announcement",
        "lucky_wheel",
        "about_us",
    }
)

MEDIA_ASSET_KIND_CHOICES: tuple[tuple[str, str], ...] = (
    ("logo", "Logo"),
    ("banner", "Banner"),
    ("gallery", "Gallery"),
)

DEFAULT_SITE_SECTION_CONTENT: dict[str, dict[str, Any]] = {
    "hero": {
        "title": "",
        "subtitle": "",
        "cta_text": "سفارش آنلاین",
        "cta_link": "/menu",
        "background_image_url": "",
    },
    "header": {
        "logo_url": "",
        "restaurant_name": "",
        "tagline": "",
        "phone": "",
        "social_links": [],
    },
    "footer": {
        "copyright_text": "",
        "address": "",
        "phone": "",
        "working_hours_text": "",
        "social_links": [],
    },
    "announcement": {
        "text": "",
        "is_active": False,
        "link": "",
    },
    "lucky_wheel": {
        "title": "",
        "subtitle": "",
        "is_active": True,
    },
    "about_us": {
        "title": "",
        "body": "",
        "image_url": "",
    },
}