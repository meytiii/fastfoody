from __future__ import annotations

from typing import Any

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self) -> "SoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> "SoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=False)

    def delete(self) -> tuple[int, dict[str, int]]:
        updated = self.update(deleted_at=timezone.now())
        return updated, {}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().alive()

    def dead(self) -> SoftDeleteQuerySet:
        """Return soft-deleted rows explicitly; ``objects`` stays alive-only."""
        return super().get_queryset().dead()


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def delete(self, *args: Any, **kwargs: Any) -> None:
        self.soft_delete()