from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Max, Prefetch
from django.utils import timezone
from redis.exceptions import RedisError

from apps.accounts.models import Customer, CustomerAddress
from apps.accounts.services import set_default_address
from apps.catalog.models import Product, ProductAddOn
from apps.cms.selectors import get_restaurant_settings
from common.exceptions import NotFoundError, ValidationError
from common.redis_client import get_redis

from .exceptions import OrderNotFoundError
from .models import (
    Order,
    OrderItem,
    OrderItemAddOn,
    PromoCode,
    PromoCodeUsage,
    normalize_promo_code,
)
from .sse import publish_order_event
from .tasks import (
    send_order_ready_sms,
    send_order_registered_sms,
    send_prep_time_changed_sms,
)

logger = logging.getLogger(__name__)

PAYMENT_TIMEOUT_MINUTES = 15
MAX_DAILY_NUMBER_RETRIES = 10


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _resolve_address(
    customer: Customer, address_id: int | None
) -> CustomerAddress | None:
    if not address_id:
        return None
    try:
        return CustomerAddress.objects.get(pk=address_id, customer=customer)
    except CustomerAddress.DoesNotExist:
        raise NotFoundError(
            message="آدرس یافت نشد.",
            code="ADDRESS_NOT_FOUND",
        )


def _ensure_restaurant_is_open() -> None:
    settings_obj = get_restaurant_settings()
    if not settings_obj.is_open():
        from common.exceptions import RestaurantClosedError

        raise RestaurantClosedError()


def _build_order_items(
    order: Order,
    raw_items: list[dict[str, Any]],
) -> int:
    """
    Validate items & addons, create OrderItem/OrderItemAddOn rows, and
    return the computed subtotal.

    Each `addons[i].quantity` is the per-line total number of add-on units.
    Bounds are `0 <= quantity <= ProductAddOn.max_quantity` (per line).
    """
    if not raw_items:
        raise ValidationError(
            message="سبد خرید خالی است.",
            details={"items": "حداقل یک آیتم لازم است."},
        )

    product_ids = [item["product_id"] for item in raw_items]
    products = {
        p.pk: p
        for p in Product.objects.select_related("category").filter(
            pk__in=product_ids
        )
    }

    missing = sorted(set(product_ids) - set(products.keys()))
    if missing:
        raise ValidationError(
            message="برخی محصولات یافت نشدند.",
            details={"missing_product_ids": missing},
        )

    for product in products.values():
        if product.status == Product.Status.HIDDEN:
            raise ValidationError(
                message=f"محصول «{product.name}» در دسترس نیست.",
                details={"product_id": product.pk},
            )
        if product.status != Product.Status.AVAILABLE:
            raise ValidationError(
                message=f"محصول «{product.name}» در حال حاضر موجود نیست.",
                details={"product_id": product.pk, "status": product.status},
            )
        if not product.category.is_active:
            raise ValidationError(
                message=f"دسته‌بندی محصول «{product.name}» غیرفعال است.",
                details={"product_id": product.pk},
            )

    product_addon_links: dict[int, dict[int, ProductAddOn]] = {}
    for product_id in products:
        links = ProductAddOn.objects.select_related("addon").filter(
            product_id=product_id
        )
        product_addon_links[product_id] = {link.addon_id: link for link in links}

    subtotal = 0

    for raw_item in raw_items:
        product = products[raw_item["product_id"]]
        quantity = int(raw_item["quantity"])
        if quantity <= 0:
            raise ValidationError(
                message="تعداد محصول باید بزرگ‌تر از صفر باشد.",
                details={"product_id": product.pk},
            )

        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot=product.name,
            unit_price_snapshot=product.price,
            quantity=quantity,
            addons_total=0,
            line_total=0,
        )

        addon_sum = 0
        for raw_addon in raw_item.get("addons", []) or []:
            addon_id = int(raw_addon["addon_id"])
            addon_quantity = int(raw_addon["quantity"])

            link = product_addon_links[product.pk].get(addon_id)
            if link is None:
                raise ValidationError(
                    message=f"افزودنی برای محصول «{product.name}» تعریف نشده است.",
                    details={"product_id": product.pk, "addon_id": addon_id},
                )
            addon = link.addon
            if not addon.is_available:
                raise ValidationError(
                    message=f"افزودنی «{addon.name}» در حال حاضر موجود نیست.",
                    details={"addon_id": addon.pk},
                )
            if addon_quantity < 0 or addon_quantity > link.max_quantity:
                raise ValidationError(
                    message=f"تعداد افزودنی «{addon.name}» نامعتبر است.",
                    details={
                        "addon_id": addon.pk,
                        "min_quantity": link.min_quantity,
                        "max_quantity": link.max_quantity,
                        "provided": addon_quantity,
                    },
                )
            if addon_quantity == 0:
                continue

            addon_line = addon_quantity * addon.price
            addon_sum += addon_line
            OrderItemAddOn.objects.create(
                order_item=item,
                addon=addon,
                addon_name_snapshot=addon.name,
                unit_price_snapshot=addon.price,
                quantity=addon_quantity,
                line_total=addon_line,
            )

        item.addons_total = addon_sum
        item.line_total = (product.price * quantity) + addon_sum
        item.save(update_fields=["addons_total", "line_total", "updated_at"])

        subtotal += item.line_total

    return subtotal


def _compute_prep_time(
    raw_items: list[dict[str, Any]],
    product_by_id: dict[int, Product],
) -> int:
    max_prep = 0
    for raw_item in raw_items:
        product = product_by_id.get(raw_item["product_id"])
        if product is not None:
            max_prep = max(max_prep, product.prep_time_minutes)

    buffer = get_restaurant_settings().prep_time_buffer_minutes
    return max_prep + buffer


# ---------------------------------------------------------------------------
# Promo codes
# ---------------------------------------------------------------------------
def _validate_promo_window(promo: PromoCode) -> None:
    """Reject inactive or out-of-window codes with a Persian message."""
    if not promo.is_active:
        raise ValidationError(
            message="این کد تخفیف فعال نیست.",
            code="PROMO_CODE_INACTIVE",
            details={"code": promo.code},
        )

    now = timezone.now()
    if promo.valid_from is not None and now < promo.valid_from:
        raise ValidationError(
            message="زمان استفاده از این کد تخفیف هنوز شروع نشده است.",
            code="PROMO_CODE_NOT_STARTED",
            details={"code": promo.code},
        )
    if promo.valid_until is not None and now > promo.valid_until:
        raise ValidationError(
            message="این کد تخفیف منقضی شده است.",
            code="PROMO_CODE_EXPIRED",
            details={"code": promo.code},
        )


def _get_promo_code(raw_code: str | None) -> PromoCode | None:
    """Fetch an existing promo code and validate its active window."""
    normalized = normalize_promo_code(raw_code or "")
    if not normalized:
        return None

    try:
        promo = PromoCode.objects.get(code=normalized)
    except PromoCode.DoesNotExist:
        raise ValidationError(
            message="کد تخفیف یافت نشد.",
            code="PROMO_CODE_NOT_FOUND",
            details={"code": normalized},
        )

    _validate_promo_window(promo)
    return promo


def _lock_promo_code(raw_code: str | None) -> PromoCode | None:
    """Lock the promo row so concurrent checkouts cannot exceed usage limits."""
    normalized = normalize_promo_code(raw_code or "")
    if not normalized:
        return None

    try:
        promo = PromoCode.objects.select_for_update().get(code=normalized)
    except PromoCode.DoesNotExist:
        raise ValidationError(
            message="کد تخفیف یافت نشد.",
            code="PROMO_CODE_NOT_FOUND",
            details={"code": normalized},
        )

    _validate_promo_window(promo)
    return promo


def _promo_discount_amount(
    *,
    customer: Customer,
    promo: PromoCode,
    subtotal: int,
) -> int:
    """Validate eligibility and return the discount in toman."""
    if subtotal < promo.min_order_amount:
        raise ValidationError(
            message=(
                "حداقل مبلغ سفارش برای استفاده از این کد تخفیف "
                f"{promo.min_order_amount:,} تومان است."
            ),
            code="PROMO_CODE_MIN_ORDER",
            details={
                "min_order_amount": promo.min_order_amount,
                "subtotal": subtotal,
            },
        )

    # Unpaid cancellations soft-delete their usage row, so every alive row
    # still represents a consumed use (including paid orders later canceled).
    usages = PromoCodeUsage.objects.filter(promo_code=promo)

    if promo.max_total_uses is not None:
        if usages.count() >= promo.max_total_uses:
            raise ValidationError(
                message="ظرفیت استفاده از این کد تخفیف تکمیل شده است.",
                code="PROMO_CODE_TOTAL_LIMIT",
                details={"code": promo.code},
            )

    if usages.filter(customer=customer).count() >= promo.max_uses_per_customer:
        raise ValidationError(
            message="شما به سقف استفاده از این کد تخفیف رسیده‌اید.",
            code="PROMO_CODE_CUSTOMER_LIMIT",
            details={"code": promo.code},
        )

    if promo.first_order_only:
        # ``paid_at`` also covers orders that were later canceled or refunded.
        has_paid_order = Order.objects.filter(
            customer=customer,
            paid_at__isnull=False,
        ).exists()
        if has_paid_order:
            raise ValidationError(
                message="این کد تخفیف فقط برای اولین سفارش قابل استفاده است.",
                code="PROMO_CODE_FIRST_ORDER_ONLY",
                details={"code": promo.code},
            )

    if promo.discount_type == PromoCode.DiscountType.PERCENTAGE:
        discount = subtotal * promo.discount_value // 100
        if promo.max_discount_amount is not None:
            discount = min(discount, promo.max_discount_amount)
    else:
        discount = promo.discount_value

    return max(0, min(discount, subtotal))


def validate_promo_code(
    *,
    customer: Customer,
    code: str,
    subtotal: int,
) -> dict[str, Any]:
    """Validate a code for checkout and return the resulting discount."""
    promo = _get_promo_code(code)
    assert promo is not None

    discount = _promo_discount_amount(
        customer=customer,
        promo=promo,
        subtotal=subtotal,
    )
    return {
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": promo.discount_value,
        "discount_amount": discount,
        "subtotal": subtotal,
        "discounted_subtotal": subtotal - discount,
    }


# ---------------------------------------------------------------------------
# Order creation
# ---------------------------------------------------------------------------
@transaction.atomic
def create_order(
    *,
    customer: Customer,
    delivery_type: str,
    address_id: int | None,
    items: list[dict[str, Any]],
    notes_to_kitchen: str = "",
    promo_code: str | None = None,
) -> Order:
    _ensure_restaurant_is_open()

    if delivery_type not in {
        Order.DeliveryType.PICKUP,
        Order.DeliveryType.DELIVERY,
    }:
        raise ValidationError(
            message="نوع تحویل نامعتبر است.",
            details={"delivery_type": delivery_type},
        )

    address = _resolve_address(customer, address_id)

    if delivery_type == Order.DeliveryType.DELIVERY and address is None:
        raise ValidationError(
            message="برای ارسال، انتخاب آدرس الزامی است.",
            details={"address_id": "این فیلد برای سفارش ارسالی الزامی است."},
        )

    settings_obj = get_restaurant_settings()
    if delivery_type == Order.DeliveryType.DELIVERY:
        assert address is not None
        delivery_fee = (
            settings_obj.out_zone_delivery_fee
            if address.is_out_of_zone
            else settings_obj.in_zone_delivery_fee
        )
        # Selecting an address for an order makes it the customer's default.
        set_default_address(customer=customer, address_id=address.pk)
    else:
        delivery_fee = 0

    packaging_fee = settings_obj.packaging_fee

    # Lock before any order rows are written so two simultaneous checkouts
    # cannot both consume the final use of a limited code.
    promo = _lock_promo_code(promo_code)

    product_by_id = {
        p.pk: p
        for p in Product.objects.filter(pk__in=[i["product_id"] for i in items])
    }
    prep_time = _compute_prep_time(items, product_by_id)

    now = timezone.now()
    order = Order.objects.create(
        customer=customer,
        delivery_type=delivery_type,
        delivery_address=address,
        delivery_address_snapshot=(address.address_text if address else ""),
        delivery_recipient_name=(address.recipient_name if address else ""),
        delivery_recipient_phone=(address.recipient_phone if address else ""),
        delivery_fee=delivery_fee,
        packaging_fee=packaging_fee,
        promo_code_snapshot=(promo.code if promo is not None else ""),
        notes_to_kitchen=notes_to_kitchen or "",
        prep_time_minutes=prep_time,
        status=Order.Status.PENDING_PAYMENT,
        payment_status=Order.PaymentStatus.UNPAID,
        expires_at=now + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES),
    )

    subtotal = _build_order_items(order, items)

    min_delivery_amount = settings_obj.min_delivery_order_amount
    if (
        delivery_type == Order.DeliveryType.DELIVERY
        and subtotal < min_delivery_amount
    ):
        raise ValidationError(
            message=(
                "حداقل مبلغ سفارش برای ارسال "
                f"{min_delivery_amount} تومان است."
            ),
            code="MIN_DELIVERY_ORDER_AMOUNT",
            details={
                "min_delivery_order_amount": min_delivery_amount,
                "subtotal": subtotal,
            },
        )

    discount_amount = 0
    if promo is not None:
        discount_amount = _promo_discount_amount(
            customer=customer,
            promo=promo,
            subtotal=subtotal,
        )
        PromoCodeUsage.objects.create(
            promo_code=promo,
            customer=customer,
            order=order,
            discount_amount=discount_amount,
        )

    order.subtotal = subtotal
    order.discount_amount = discount_amount
    order.total_amount = (
        max(0, subtotal - discount_amount) + delivery_fee + packaging_fee
    )
    order.save(
        update_fields=[
            "subtotal",
            "discount_amount",
            "total_amount",
            "updated_at",
        ]
    )

    logger.info(
        "Order %s created (customer=%s total=%s prep=%s)",
        order.pk,
        customer.pk,
        order.total_amount,
        prep_time,
    )
    return order


# ---------------------------------------------------------------------------
# Payment success (called by Phase 6 payment verification)
# ---------------------------------------------------------------------------
def _next_daily_number_from_db(today: Any) -> int:
    """Database fallback used when Redis is unavailable (e.g. fresh dev box)."""
    latest = Order.objects.filter(daily_number_date=today).aggregate(
        latest=Max("daily_number")
    )["latest"]
    return (latest or 0) + 1


def _assign_daily_number(order: Order) -> None:
    """
    Assign the per-day order number, tolerating a missing Redis instance.

    Redis is preferred (atomic ``INCR``), but a payment must not roll back just
    because the cache server is down: the database ``MAX(daily_number)`` is a
    safe fallback for a single-location restaurant. Each save runs in its own
    savepoint, so an ``IntegrityError`` from a concurrent duplicate does not
    poison the outer transaction and the retry loop can actually retry.
    """
    today = timezone.localdate()
    key = f"order_seq:{today.isoformat()}"

    try:
        redis = get_redis()
    except (RedisError, OSError, ValueError):
        redis = None
        logger.warning(
            "Redis client unavailable; falling back to DB daily numbering.",
            exc_info=True,
        )

    for attempt in range(1, MAX_DAILY_NUMBER_RETRIES + 1):
        if redis is not None:
            try:
                number = int(redis.incr(key))
                if number == 1:
                    redis.expire(key, 60 * 60 * 48)
            except (RedisError, OSError, ValueError):
                logger.warning(
                    "Redis daily-number counter unavailable; using DB fallback.",
                    exc_info=True,
                )
                redis = None
                number = _next_daily_number_from_db(today)
        else:
            number = _next_daily_number_from_db(today)

        order.daily_number = number
        order.daily_number_date = today
        try:
            with transaction.atomic():
                order.save(
                    update_fields=[
                        "daily_number",
                        "daily_number_date",
                        "updated_at",
                    ]
                )
            return
        except IntegrityError:
            logger.warning(
                "Daily number collision for order %s (number=%s attempt=%s); retrying.",
                order.pk,
                number,
                attempt,
            )
            continue

    raise RuntimeError(
        f"Could not assign daily_number for order {order.pk} after "
        f"{MAX_DAILY_NUMBER_RETRIES} attempts."
    )


@transaction.atomic
def mark_order_paid(*, order_id: int, paid_at: Any = None) -> Order:
    """Transition PENDING_PAYMENT -> PROCESSING with daily_number assignment."""
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.status != Order.Status.PENDING_PAYMENT:
        from common.exceptions import OrderStateError

        raise OrderStateError(
            message="سفارش در وضعیت مناسب برای پرداخت نیست.",
            details={"status": order.status},
        )

    now = paid_at or timezone.now()

    order.paid_at = now
    order.status = Order.Status.PROCESSING
    order.payment_status = Order.PaymentStatus.PAID
    order.expected_ready_at = now + timedelta(minutes=order.prep_time_minutes)
    order.is_printed = False
    order.save(
        update_fields=[
            "paid_at",
            "status",
            "payment_status",
            "expected_ready_at",
            "is_printed",
            "updated_at",
        ]
    )

    _assign_daily_number(order)

    transaction.on_commit(lambda: send_order_registered_sms.delay(order.pk))

    logger.info(
        "Order %s marked PAID (daily_number=%s)", order.pk, order.daily_number
    )
    return order


def revalidate_order_for_payment(order: Order) -> None:
    """
    Called by Phase 6 before retrying Zarinpal: ensure restaurant open,
    products AVAILABLE, add-ons available.
    """
    _ensure_restaurant_is_open()

    for item in order.items.select_related("product").all():
        if item.product.status != Product.Status.AVAILABLE:
            raise ValidationError(
                message=f"محصول «{item.product_name_snapshot}» دیگر موجود نیست.",
                details={"product_id": item.product.pk},
            )

    for item in order.items.all():
        for addon_row in item.addons.select_related("addon").all():
            if not addon_row.addon.is_available:
                raise ValidationError(
                    message=f"افزودنی «{addon_row.addon_name_snapshot}» دیگر موجود نیست.",
                    details={"addon_id": addon_row.addon.pk},
                )


# ---------------------------------------------------------------------------
# Manager-driven transitions
# ---------------------------------------------------------------------------
@transaction.atomic
def mark_order_ready(*, order_id: int) -> Order:
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.status != Order.Status.PROCESSING:
        from common.exceptions import OrderStateError

        raise OrderStateError(
            message="سفارش در وضعیت پردازش نیست.",
            details={"status": order.status},
        )

    order.status = Order.Status.READY
    order.save(update_fields=["status", "updated_at"])

    transaction.on_commit(lambda: send_order_ready_sms.delay(order.pk))
    transaction.on_commit(
        lambda: publish_order_event(order, "order.status_changed")
    )
    return order


@transaction.atomic
def mark_order_completed(*, order_id: int) -> Order:
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.status != Order.Status.READY:
        from common.exceptions import OrderStateError

        raise OrderStateError(
            message="سفارش در وضعیت آماده نیست.",
            details={"status": order.status},
        )

    order.status = Order.Status.COMPLETED
    order.save(update_fields=["status", "updated_at"])

    transaction.on_commit(
        lambda: publish_order_event(order, "order.status_changed")
    )
    return order


@transaction.atomic
def cancel_order_by_manager(
    *,
    order_id: int,
    manager: Customer,
    reason: str = "",
) -> Order:
    from common.exceptions import OrderStateError

    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.status in {Order.Status.CANCELED, Order.Status.COMPLETED}:
        raise OrderStateError(
            message="این سفارش قابل لغو نیست.",
            details={"status": order.status},
        )
    if order.payment_status == Order.PaymentStatus.AWAITING_REFUND:
        raise OrderStateError(
            message="این سفارش قبلاً لغو شده و در انتظار بازگشت وجه است."
        )
    if order.payment_status == Order.PaymentStatus.REFUNDED:
        raise OrderStateError(message="این سفارش قبلاً بازپرداخت شده است.")

    order.status = Order.Status.CANCELED
    order.canceled_at = timezone.now()
    order.canceled_by = manager
    order.cancellation_reason = reason or ""

    if order.payment_status == Order.PaymentStatus.UNPAID:
        _release_promo_usage(order)
    elif order.payment_status == Order.PaymentStatus.PAID:
        order.payment_status = Order.PaymentStatus.AWAITING_REFUND

    order.save(
        update_fields=[
            "status",
            "canceled_at",
            "canceled_by",
            "cancellation_reason",
            "payment_status",
            "updated_at",
        ]
    )
    transaction.on_commit(
        lambda: publish_order_event(order, "order.status_changed")
    )
    return order


@transaction.atomic
def request_cancellation(
    *,
    customer: Customer,
    order_id: int,
    reason: str = "",
) -> Order:
    """
    Let a customer ask the manager to cancel their own paid order.

    Only PAID orders that are still PROCESSING or READY are eligible, and a
    request can be recorded once. The manager still performs the actual
    cancellation (and any manual refund).
    """
    from common.exceptions import OrderStateError

    try:
        order = Order.objects.select_for_update().get(
            pk=order_id, customer=customer
        )
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.payment_status != Order.PaymentStatus.PAID:
        raise OrderStateError(
            message="فقط سفارش‌های پرداخت‌شده قابل درخواست لغو هستند.",
            details={"payment_status": order.payment_status},
        )
    if order.status not in {Order.Status.PROCESSING, Order.Status.READY}:
        raise OrderStateError(
            message="در وضعیت فعلی سفارش امکان درخواست لغو وجود ندارد.",
            details={"status": order.status},
        )
    if order.cancellation_requested:
        raise OrderStateError(
            message="درخواست لغو این سفارش قبلاً ثبت شده است.",
            details={"order_id": order.pk},
        )

    order.cancellation_requested = True
    order.cancellation_request_reason = (reason or "").strip()
    order.cancellation_requested_at = timezone.now()
    order.save(
        update_fields=[
            "cancellation_requested",
            "cancellation_request_reason",
            "cancellation_requested_at",
            "updated_at",
        ]
    )
    transaction.on_commit(
        lambda: publish_order_event(order, "order.cancellation_requested")
    )
    return order


def _release_promo_usage(order: Order) -> None:
    """Soft-delete the usage row so an unpaid cancellation restores the quota."""
    try:
        usage = order.promo_usage
    except PromoCodeUsage.DoesNotExist:
        return
    if usage.deleted_at is None:
        usage.delete()


@transaction.atomic
def cancel_expired_unpaid_orders() -> int:
    now = timezone.now()
    expired = list(
        Order.objects.select_for_update().filter(
            status=Order.Status.PENDING_PAYMENT,
            expires_at__lt=now,
        )
    )
    for order in expired:
        order.status = Order.Status.CANCELED
        order.canceled_at = now
        order.cancellation_reason = "auto: payment timeout"
        order.save(
            update_fields=[
                "status",
                "canceled_at",
                "cancellation_reason",
                "updated_at",
            ]
        )
        _release_promo_usage(order)
        transaction.on_commit(
            lambda order=order: publish_order_event(
                order, "order.status_changed"
            )
        )
    return len(expired)


@transaction.atomic
def record_refund(
    *,
    order_id: int,
    manager: Customer,
    card_number: str,
    tracking_code: str,
) -> Order:
    from common.exceptions import OrderStateError

    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.payment_status != Order.PaymentStatus.AWAITING_REFUND:
        raise OrderStateError(
            message="این سفارش در وضعیت انتظار بازگشت وجه نیست.",
            details={"payment_status": order.payment_status},
        )

    order.payment_status = Order.PaymentStatus.REFUNDED
    order.refund_card_number = card_number
    order.refund_tracking_code = tracking_code
    order.refunded_at = timezone.now()
    order.refunded_by = manager
    order.save(
        update_fields=[
            "payment_status",
            "refund_card_number",
            "refund_tracking_code",
            "refunded_at",
            "refunded_by",
            "updated_at",
        ]
    )
    return order


@transaction.atomic
def update_prep_time(
    *,
    order_id: int,
    new_prep_time_minutes: int,
) -> Order:
    from common.exceptions import OrderStateError

    if new_prep_time_minutes <= 0:
        raise ValidationError(
            message="زمان آماده‌سازی باید بزرگ‌تر از صفر باشد.",
            details={"prep_time_minutes": new_prep_time_minutes},
        )

    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.status not in {Order.Status.PROCESSING, Order.Status.READY}:
        raise OrderStateError(
            message="فقط سفارش‌های در حال پردازش یا آماده قابل ویرایش هستند.",
            details={"status": order.status},
        )
    if order.paid_at is None:
        raise OrderStateError(message="سفارش پرداخت نشده است.")

    order.prep_time_minutes = new_prep_time_minutes
    order.expected_ready_at = order.paid_at + timedelta(minutes=new_prep_time_minutes)
    order.save(
        update_fields=["prep_time_minutes", "expected_ready_at", "updated_at"]
    )

    transaction.on_commit(
        lambda: send_prep_time_changed_sms.delay(order.pk, new_prep_time_minutes)
    )
    transaction.on_commit(
        lambda: publish_order_event(order, "order.prep_time_updated")
    )
    return order


@transaction.atomic
def mark_order_printed(*, order_id: int) -> Order:
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    if order.is_printed:
        return order

    order.is_printed = True
    order.printed_at = timezone.now()
    order.save(update_fields=["is_printed", "printed_at", "updated_at"])
    return order


# ---------------------------------------------------------------------------
# Promo code administration (Backoffice)
# ---------------------------------------------------------------------------
PROMO_EDITABLE_FIELDS = (
    "code",
    "discount_type",
    "discount_value",
    "max_discount_amount",
    "min_order_amount",
    "valid_from",
    "valid_until",
    "max_total_uses",
    "max_uses_per_customer",
    "first_order_only",
    "is_active",
)


def _apply_promo_data(promo: PromoCode, data: dict[str, Any]) -> None:
    for field in PROMO_EDITABLE_FIELDS:
        if field in data:
            setattr(promo, field, data[field])
    promo.code = normalize_promo_code(promo.code)


def _validate_promo_instance(promo: PromoCode) -> None:
    if not promo.code:
        raise ValidationError(
            message="وارد کردن کد تخفیف الزامی است.",
            details={"code": "این فیلد الزامی است."},
        )

    if promo.discount_type not in PromoCode.DiscountType.values:
        raise ValidationError(
            message="نوع تخفیف نامعتبر است.",
            details={"discount_type": promo.discount_type},
        )

    if promo.discount_type == PromoCode.DiscountType.PERCENTAGE:
        if promo.discount_value is None or not 1 <= promo.discount_value <= 100:
            raise ValidationError(
                message="درصد تخفیف باید بین ۱ تا ۱۰۰ باشد.",
                details={"discount_value": promo.discount_value},
            )
    elif promo.discount_value is None or promo.discount_value <= 0:
        raise ValidationError(
            message="مبلغ تخفیف باید بزرگ‌تر از صفر باشد.",
            details={"discount_value": promo.discount_value},
        )

    if (
        promo.valid_from is not None
        and promo.valid_until is not None
        and promo.valid_until <= promo.valid_from
    ):
        raise ValidationError(
            message="زمان پایان اعتبار باید بعد از زمان شروع باشد.",
            details={
                "valid_from": promo.valid_from,
                "valid_until": promo.valid_until,
            },
        )


@transaction.atomic
def create_promo_code(*, data: dict[str, Any]) -> PromoCode:
    promo = PromoCode()
    _apply_promo_data(promo, data)
    _validate_promo_instance(promo)

    if PromoCode.objects.filter(code=promo.code).exists():
        raise ValidationError(
            message="کد تخفیف تکراری است.",
            code="PROMO_CODE_DUPLICATE",
            details={"code": promo.code},
        )

    try:
        with transaction.atomic():
            promo.save()
    except IntegrityError:
        raise ValidationError(
            message="کد تخفیف تکراری است.",
            code="PROMO_CODE_DUPLICATE",
            details={"code": promo.code},
        )
    return promo


@transaction.atomic
def update_promo_code(
    *,
    promo_code_id: int,
    data: dict[str, Any],
) -> PromoCode:
    try:
        promo = PromoCode.objects.select_for_update().get(pk=promo_code_id)
    except PromoCode.DoesNotExist:
        from .exceptions import PromoCodeNotFoundError

        raise PromoCodeNotFoundError()

    _apply_promo_data(promo, data)
    _validate_promo_instance(promo)

    if (
        PromoCode.objects.filter(code=promo.code)
        .exclude(pk=promo.pk)
        .exists()
    ):
        raise ValidationError(
            message="کد تخفیف تکراری است.",
            code="PROMO_CODE_DUPLICATE",
            details={"code": promo.code},
        )

    try:
        with transaction.atomic():
            promo.save()
    except IntegrityError:
        raise ValidationError(
            message="کد تخفیف تکراری است.",
            code="PROMO_CODE_DUPLICATE",
            details={"code": promo.code},
        )
    return promo


@transaction.atomic
def delete_promo_code(*, promo_code_id: int) -> None:
    try:
        promo = PromoCode.objects.select_for_update().get(pk=promo_code_id)
    except PromoCode.DoesNotExist:
        from .exceptions import PromoCodeNotFoundError

        raise PromoCodeNotFoundError()
    promo.delete()


# ---------------------------------------------------------------------------
# One-click reorder
# ---------------------------------------------------------------------------
def _warn(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def prepare_reorder_payload(
    customer: Customer,
    order_id: int,
) -> dict[str, Any]:
    """
    Rebuild a cart from a past order against the current catalog.

    Unavailable products/add-ons are dropped with a Persian warning, add-on
    quantities are clamped to the current maximum, and price changes are
    reported so the customer never gets a surprise at checkout.
    """
    try:
        order = (
            Order.objects.select_related("customer")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related(
                        "product__category"
                    ).prefetch_related(
                        Prefetch(
                            "addons",
                            queryset=OrderItemAddOn.objects.select_related(
                                "addon"
                            ),
                        )
                    ),
                )
            )
            .get(pk=order_id, customer=customer)
        )
    except Order.DoesNotExist:
        raise OrderNotFoundError()

    product_ids = [item.product_id for item in order.items.all()]
    links_by_product: dict[int, dict[int, ProductAddOn]] = {}
    for link in ProductAddOn.objects.filter(product_id__in=product_ids):
        links_by_product.setdefault(link.product_id, {})[link.addon_id] = link

    items: list[dict[str, Any]] = []
    warnings: list[str] = []

    for order_item in order.items.all():
        product = order_item.product
        if (
            product.deleted_at is not None
            or product.status != Product.Status.AVAILABLE
        ):
            _warn(
                warnings,
                f"محصول «{order_item.product_name_snapshot}» در حال حاضر "
                "موجود نیست و از سبد حذف شد.",
            )
            continue

        category = product.category
        if category.deleted_at is not None or not category.is_active:
            _warn(
                warnings,
                f"دسته‌بندی محصول «{order_item.product_name_snapshot}» غیرفعال "
                "است و محصول از سبد حذف شد.",
            )
            continue

        if product.price != order_item.unit_price_snapshot:
            _warn(
                warnings,
                f"قیمت محصول «{product.name}» تغییر کرده است.",
            )

        addon_lines: list[dict[str, Any]] = []
        addons_total = 0
        links = links_by_product.get(product.pk, {})

        for order_addon in order_item.addons.all():
            addon = order_addon.addon
            link = links.get(addon.pk)
            if (
                addon.deleted_at is not None
                or not addon.is_available
                or link is None
            ):
                _warn(
                    warnings,
                    f"افزودنی «{order_addon.addon_name_snapshot}» برای محصول "
                    f"«{product.name}» در دسترس نیست و حذف شد.",
                )
                continue

            quantity = order_addon.quantity
            if quantity > link.max_quantity:
                quantity = link.max_quantity
                _warn(
                    warnings,
                    f"تعداد افزودنی «{addon.name}» به حداکثر مجاز "
                    f"({link.max_quantity}) کاهش یافت.",
                )
            if quantity <= 0:
                continue

            if addon.price != order_addon.unit_price_snapshot:
                _warn(
                    warnings,
                    f"قیمت افزودنی «{addon.name}» تغییر کرده است.",
                )

            line_total = quantity * addon.price
            addons_total += line_total
            addon_lines.append(
                {
                    "addon_id": addon.pk,
                    "name": addon.name,
                    "quantity": quantity,
                    "unit_price": addon.price,
                    "line_total": line_total,
                }
            )

        line_total = (product.price * order_item.quantity) + addons_total
        items.append(
            {
                "product_id": product.pk,
                "name": product.name,
                "quantity": order_item.quantity,
                "unit_price": product.price,
                "addons": addon_lines,
                "line_total": line_total,
            }
        )

    return {"items": items, "warnings": warnings}