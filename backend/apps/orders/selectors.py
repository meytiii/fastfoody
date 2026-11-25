from __future__ import annotations

from typing import Any

from django.db.models import Prefetch, Q, QuerySet

from apps.accounts.models import CustomerNote

from .exceptions import OrderNotFoundError
from .models import Order, OrderItem, OrderItemAddOn


def _customer_notes_prefetch() -> Prefetch:
    """Prefetch CRM notes so the POS/receipt payload has no N+1 queries."""
    return Prefetch(
        "customer__notes",
        queryset=CustomerNote.objects.select_related("author").order_by(
            "-created_at"
        ),
    )


def _with_details() -> QuerySet[Order]:
    return Order.objects.select_related(
        "customer", "delivery_address"
    ).prefetch_related(
        Prefetch(
            "items",
            queryset=OrderItem.objects.prefetch_related(
                Prefetch("addons", queryset=OrderItemAddOn.objects.all())
            ),
        ),
        _customer_notes_prefetch(),
    )


def get_order_for_customer(order_id: int, customer_id: int) -> Order:
    try:
        return _with_details().get(pk=order_id, customer_id=customer_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()


def list_orders_for_customer(customer_id: int) -> QuerySet[Order]:
    return Order.objects.filter(customer_id=customer_id).order_by("-created_at")


def get_order_backoffice(order_id: int) -> Order:
    try:
        return _with_details().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()


def list_orders_backoffice(
    *,
    status: str | None = None,
    payment_status: str | None = None,
    delivery_type: str | None = None,
    search: str | None = None,
    date_from: Any = None,
    date_to: Any = None,
) -> QuerySet[Order]:
    qs = (
        Order.objects.select_related("customer", "delivery_address")
        .order_by("-created_at")
    )
    if status:
        qs = qs.filter(status=status)
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    if delivery_type:
        qs = qs.filter(delivery_type=delivery_type)
    if search:
        qs = qs.filter(
            Q(daily_number__icontains=search)
            | Q(customer__phone__icontains=search)
            | Q(customer__full_name__icontains=search)
        )
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    return qs


def get_live_orders() -> QuerySet[Order]:
    """PROCESSING + READY orders sorted by expected_ready_at (for Live POS)."""
    return (
        _with_details()
        .filter(status__in=[Order.Status.PROCESSING, Order.Status.READY])
        .order_by("expected_ready_at", "created_at")
    )