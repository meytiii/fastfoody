from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from .models import Payment


def get_payment_by_authority(authority: str) -> Payment:
    return Payment.objects.select_related("order").get(authority=authority)


def get_pending_payment_for_order(order_id: int) -> Payment | None:
    return (
        Payment.objects.filter(
            order_id=order_id, status=Payment.Status.PENDING
        )
        .order_by("-created_at")
        .first()
    )


def list_payments_for_order(order_id: int) -> QuerySet[Payment]:
    return Payment.objects.filter(order_id=order_id).order_by("-created_at")


def list_payments_needing_reverify() -> QuerySet[Payment]:
    """Payments that are old enough and still PENDING (network failure mid-verify)."""
    from datetime import timedelta

    from django.utils import timezone

    cutoff = timezone.now() - timedelta(minutes=3)
    return Payment.objects.filter(
        status=Payment.Status.PENDING,
        created_at__lt=cutoff,
    )