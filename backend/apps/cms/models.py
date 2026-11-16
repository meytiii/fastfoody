from __future__ import annotations

from datetime import time
from typing import Any

from django.db import models
from django.utils import timezone

from common.models import BaseModel

from .constants import (
    ALLOWED_SITE_SECTION_KEYS,
    DEFAULT_SITE_SECTION_CONTENT,
    MEDIA_ASSET_KIND_CHOICES,
)


class RestaurantSettings(models.Model):
    """Singleton model (pk=1). Not soft-deletable by design."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)

    open_time = models.TimeField(default=time(11, 0))
    close_time = models.TimeField(default=time(1, 0))
    is_temporarily_closed = models.BooleanField(default=False)

    in_zone_delivery_fee = models.PositiveIntegerField(default=50_000)
    out_zone_delivery_fee = models.PositiveIntegerField(default=100_000)
    prep_time_buffer_minutes = models.PositiveSmallIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restaurant Settings"
        verbose_name_plural = "Restaurant Settings"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Force singleton semantics.
        self.pk = 1
        super().save(*args, **kwargs)

    def is_open(self, now: time | None = None) -> bool:
        """Check whether the restaurant is currently accepting orders."""
        if self.is_temporarily_closed:
            return False

        current = now if now is not None else timezone.localtime().time()

        if self.open_time == self.close_time:
            # Ambiguous; treat as closed.
            return False

        if self.open_time < self.close_time:
            # Same-day window (e.g. 09:00 – 22:00).
            return self.open_time <= current < self.close_time

        # Overnight window (e.g. 11:00 – 01:00).
        return current >= self.open_time or current < self.close_time


class SiteSection(BaseModel):
    key = models.CharField(
        max_length=32,
        choices=[(k, k) for k in sorted(ALLOWED_SITE_SECTION_KEYS)],
    )
    content = models.JSONField(default=dict)

    class Meta:
        ordering = ("key",)
        constraints = [
            models.UniqueConstraint(
                fields=["key"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_alive_site_section_key",
            ),
        ]
        verbose_name = "Site Section"
        verbose_name_plural = "Site Sections"

    @classmethod
    def get_default_content(cls, key: str) -> dict[str, Any]:
        return dict(DEFAULT_SITE_SECTION_CONTENT.get(key, {}))

    def __str__(self) -> str:
        return self.key


class MediaAsset(BaseModel):
    kind = models.CharField(max_length=16, choices=MEDIA_ASSET_KIND_CHOICES)
    title = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    file = models.ImageField(upload_to="cms/%Y/%m/")
    webp_file = models.ImageField(
        upload_to="cms/webp/%Y/%m/",
        blank=True,
        null=True,
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Media Asset"
        verbose_name_plural = "Media Assets"

    def __str__(self) -> str:
        return f"{self.kind}: {self.title or self.file.name}"