from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.db.models import Avg, Count, Prefetch, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce, ExtractHour, TruncDate
from django.utils import timezone

from apps.accounts.models import CustomerNote
from apps.catalog.models import Product
from common.exceptions import ValidationError

from .exceptions import OrderNotFoundError, PromoCodeNotFoundError
from .models import Order, OrderItem, OrderItemAddOn, PromoCode

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

#: Money was captured: still held, pending refund, or already refunded.
REPORTING_PAYMENT_STATUSES = (
    Order.PaymentStatus.PAID,
    Order.PaymentStatus.AWAITING_REFUND,
    Order.PaymentStatus.REFUNDED,
)
#: Captured and not refunded; used for AOV and product sales.
NON_REFUNDED_PAYMENT_STATUSES = (
    Order.PaymentStatus.PAID,
    Order.PaymentStatus.AWAITING_REFUND,
)


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


# ---------------------------------------------------------------------------
# Promo codes (Backoffice)
# ---------------------------------------------------------------------------
def _promo_usage_count_annotation() -> Count:
    return Count(
        "usages",
        filter=Q(usages__deleted_at__isnull=True),
    )


def list_promo_codes(
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> QuerySet[PromoCode]:
    """List promo codes with a non-deleted usage count annotation."""
    qs = PromoCode.objects.annotate(
        usage_count=_promo_usage_count_annotation()
    ).order_by("-created_at")
    if search:
        qs = qs.filter(code__icontains=search.strip())
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def get_promo_code(promo_code_id: int) -> PromoCode:
    try:
        return PromoCode.objects.annotate(
            usage_count=_promo_usage_count_annotation()
        ).get(pk=promo_code_id)
    except PromoCode.DoesNotExist:
        raise PromoCodeNotFoundError()


# ---------------------------------------------------------------------------
# Sales analytics (Backoffice)
# ---------------------------------------------------------------------------
def _resolve_date_range(
    period: str,
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    today = timezone.localdate()

    if period == "custom" or date_from is not None or date_to is not None:
        if date_from is None or date_to is None:
            raise ValidationError(
                message="برای بازه دلخواه، تاریخ شروع و پایان الزامی است.",
                code="INVALID_DATE_RANGE",
                details={
                    "date_from": date_from,
                    "date_to": date_to,
                },
            )
        if date_from > date_to:
            raise ValidationError(
                message="تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.",
                code="INVALID_DATE_RANGE",
                details={
                    "date_from": date_from,
                    "date_to": date_to,
                },
            )
        return date_from, date_to

    if period == "today":
        return today, today
    if period == "7d":
        return today - timedelta(days=6), today
    if period == "30d":
        return today - timedelta(days=29), today

    raise ValidationError(
        message="بازه زمانی نامعتبر است.",
        code="INVALID_PERIOD",
        details={"period": period},
    )


def _range_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    start_dt = timezone.make_aware(
        datetime.combine(start, time.min), TEHRAN_TZ
    )
    end_dt = timezone.make_aware(
        datetime.combine(end + timedelta(days=1), time.min), TEHRAN_TZ
    )
    return start_dt, end_dt


def get_sales_analytics(
    period: str = "7d",
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, Any]:
    """Aggregate paid-order KPIs, product performance and time breakdowns."""
    start_date, end_date = _resolve_date_range(period, date_from, date_to)
    start_dt, end_dt = _range_bounds(start_date, end_date)

    paid_orders = Order.objects.filter(
        payment_status__in=REPORTING_PAYMENT_STATUSES,
        created_at__gte=start_dt,
        created_at__lt=end_dt,
    )
    non_refunded_orders = paid_orders.filter(
        payment_status__in=NON_REFUNDED_PAYMENT_STATUSES
    )

    totals = paid_orders.aggregate(
        gross_sales=Coalesce(Sum("total_amount"), Value(0)),
        refunded_count=Count(
            "id",
            filter=Q(payment_status=Order.PaymentStatus.REFUNDED),
        ),
        refunded_amount=Coalesce(
            Sum(
                "total_amount",
                filter=Q(payment_status=Order.PaymentStatus.REFUNDED),
            ),
            Value(0),
        ),
        total_delivery_fees=Coalesce(Sum("delivery_fee"), Value(0)),
        total_packaging_fees=Coalesce(Sum("packaging_fee"), Value(0)),
        total_discounts=Coalesce(Sum("discount_amount"), Value(0)),
    )

    paid_orders_count = non_refunded_orders.count()
    average_order_value = (
        non_refunded_orders.aggregate(value=Avg("total_amount"))["value"]
        or 0
    )

    top_products = list(
        OrderItem.objects.filter(order__in=non_refunded_orders)
        .values("product_id", "product__name")
        .annotate(
            quantity=Sum("quantity"),
            revenue=Sum("line_total"),
        )
        .order_by("-quantity", "product__name")[:10]
    )

    least_selling_products = list(
        Product.objects.filter(
            status=Product.Status.AVAILABLE,
            category__is_active=True,
            category__deleted_at__isnull=True,
        )
        .annotate(
            quantity_sold=Coalesce(
                Sum(
                    "order_items__quantity",
                    filter=Q(order_items__order__in=non_refunded_orders),
                ),
                Value(0),
            )
        )
        .values("id", "name", "quantity_sold")
        .order_by("quantity_sold", "name")[:5]
    )

    peak_rows = (
        paid_orders.annotate(hour=ExtractHour("created_at", tzinfo=TEHRAN_TZ))
        .values("hour")
        .annotate(
            order_count=Count("id"),
            revenue=Sum("total_amount"),
        )
        .order_by("hour")
    )
    peak_by_hour = {
        row["hour"]: row for row in peak_rows if row["hour"] is not None
    }
    peak_hours = [
        {
            "hour": hour,
            "order_count": peak_by_hour.get(hour, {}).get("order_count", 0),
            "revenue": peak_by_hour.get(hour, {}).get("revenue", 0) or 0,
        }
        for hour in range(24)
    ]

    daily_rows = (
        paid_orders.annotate(day=TruncDate("created_at", tzinfo=TEHRAN_TZ))
        .values("day")
        .annotate(
            order_count=Count("id"),
            gross=Coalesce(Sum("total_amount"), Value(0)),
            refunded=Coalesce(
                Sum(
                    "total_amount",
                    filter=Q(payment_status=Order.PaymentStatus.REFUNDED),
                ),
                Value(0),
            ),
        )
        .order_by("day")
    )
    daily_by_date = {row["day"]: row for row in daily_rows}

    daily_trend: list[dict[str, Any]] = []
    current = start_date
    while current <= end_date:
        row = daily_by_date.get(current, {})
        daily_trend.append(
            {
                "date": current.isoformat(),
                "order_count": row.get("order_count", 0),
                "revenue": (row.get("gross", 0) or 0)
                - (row.get("refunded", 0) or 0),
            }
        )
        current += timedelta(days=1)

    gross_sales = int(totals["gross_sales"] or 0)
    refunded_amount = int(totals["refunded_amount"] or 0)

    return {
        "period": period,
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "gross_sales": gross_sales,
        "refunded_count": int(totals["refunded_count"] or 0),
        "refunded_amount": refunded_amount,
        "net_sales": gross_sales - refunded_amount,
        "paid_orders_count": paid_orders_count,
        "average_order_value": int(round(average_order_value)),
        "total_delivery_fees": int(totals["total_delivery_fees"] or 0),
        "total_packaging_fees": int(totals["total_packaging_fees"] or 0),
        "total_discounts": int(totals["total_discounts"] or 0),
        "top_products": [
            {
                "product_id": row["product_id"],
                "product_name": row["product__name"],
                "quantity": row["quantity"],
                "revenue": row["revenue"],
            }
            for row in top_products
        ],
        "least_selling_products": least_selling_products,
        "peak_hours": peak_hours,
        "daily_trend": daily_trend,
    }