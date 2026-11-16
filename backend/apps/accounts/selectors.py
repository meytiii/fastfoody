from __future__ import annotations

from typing import Any

from django.apps import apps as django_apps
from django.db.models import QuerySet, Sum , Q

from .models import Customer, CustomerAddress, CustomerNote


def get_customer_by_id(customer_id: int) -> Customer:
    return Customer.objects.get(pk=customer_id)



def list_customers(
    *,
    search: str | None = None,
    is_blocked: bool | None = None,
) -> QuerySet[Customer]:
    qs = Customer.objects.all().order_by("-created_at")
    if search:
        qs = qs.filter(Q(phone__icontains=search) | Q(full_name__icontains=search))
    if is_blocked is not None:
        qs = qs.filter(is_blocked=is_blocked)
    return qs


def models_q_phone_or_name(search: str) -> Any:
    from django.db.models import Q

    return Q(phone__icontains=search) | Q(full_name__icontains=search)


def list_addresses_for_customer(customer: Customer) -> list[CustomerAddress]:
    return list(
        CustomerAddress.objects.filter(customer=customer).order_by(
            "-is_default", "-created_at"
        )
    )


def get_address_for_customer(customer: Customer,address_id: int,) -> CustomerAddress:
    from common.exceptions import NotFoundError
    try:
        return CustomerAddress.objects.get(pk=address_id, customer=customer)
    except CustomerAddress.DoesNotExist:
        raise NotFoundError(message="آدرس یافت نشد.", code="ADDRESS_NOT_FOUND")

def list_customer_notes(customer_id: int) -> list[CustomerNote]:
    return list(
        CustomerNote.objects.filter(customer_id=customer_id)
        .select_related("author")
        .order_by("-created_at")
    )


def get_customer_note(customer_id: int, note_id: int) -> CustomerNote:
    return CustomerNote.objects.get(pk=note_id, customer_id=customer_id)


def get_order_stats_for_customer(customer: Customer) -> dict[str, Any]:
    """
    Aggregate order-related stats for Customer 360.

    Returns zeros until the orders module exists (Phase 5), at which point
    this function will start returning real data automatically.
    """
    try:
        Order = django_apps.get_model("orders", "Order")
    except LookupError:
        return {
            "orders_count": 0,
            "completed_orders_count": 0,
            "lifetime_value": 0,
            "last_order_at": None,
        }

    base_qs = Order.objects.filter(customer=customer, deleted_at__isnull=True)
    orders_count = base_qs.count()
    completed_orders_count = base_qs.filter(status="COMPLETED").count()

    paid_qs = base_qs.filter(payment_status="PAID")
    lifetime_value = (
        paid_qs.aggregate(total=Sum("total_amount"))["total"] or 0
    )

    last = base_qs.order_by("-created_at").values("created_at").first()
    last_order_at = last["created_at"] if last else None

    return {
        "orders_count": orders_count,
        "completed_orders_count": completed_orders_count,
        "lifetime_value": lifetime_value,
        "last_order_at": last_order_at,
    }


def get_customer_360(customer_id: int) -> dict[str, Any]:
    customer = Customer.objects.get(pk=customer_id)
    addresses = list_addresses_for_customer(customer)
    notes = list_customer_notes(customer_id)

    return {
        "customer": customer,
        "addresses": addresses,
        "notes": notes,
        **get_order_stats_for_customer(customer),
    }