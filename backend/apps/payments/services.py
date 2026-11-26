from __future__ import annotations

import logging
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import mark_order_paid, revalidate_order_for_payment
from apps.orders.sse import publish_order_event
from common.exceptions import NotFoundError, OrderStateError

from .exceptions import (
    PaymentAlreadyVerifiedError,
    PaymentNotVerifiableError,
    ZarinpalRequestError,
    ZarinpalVerifyError,
)
from .models import Payment
from .selectors import get_payment_by_authority
from .zarinpal import ZarinpalClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Initiate payment
# ---------------------------------------------------------------------------
def start_payment_for_order(*, order: Order) -> dict[str, Any]:
    """Create a Payment row and return the gateway redirect URL."""
    if order.status != Order.Status.PENDING_PAYMENT:
        raise OrderStateError(
            message="سفارش در وضعیت قابل پرداخت نیست.",
            details={"status": order.status},
        )
    if order.payment_status != Order.PaymentStatus.UNPAID:
        raise OrderStateError(
            message="این سفارش قبلاً پرداخت شده است.",
        )
    if order.expires_at and timezone.now() > order.expires_at:
        raise OrderStateError(
            message="مهلت پرداخت این سفارش به پایان رسیده است.",
        )

    revalidate_order_for_payment(order)

    client = ZarinpalClient()
    description = f"پرداخت سفارش #{order.pk}"

    try:
        gateway_data = client.request_payment(
            amount=order.total_amount,
            description=description,
        )
    except ZarinpalRequestError:
        logger.exception("Zarinpal request failed for order %s", order.pk)
        raise

    authority = gateway_data.get("authority")
    if not authority:
        raise ZarinpalRequestError(
            message="پاسخ درگاه فاقد شناسه تراکنش است.",
        )

    try:
        Payment.objects.create(
            order=order,
            amount=order.total_amount,
            status=Payment.Status.PENDING,
            authority=authority,
        )
    except IntegrityError:
        logger.warning(
            "Duplicate authority %s for order %s; treating as idempotent.",
            authority,
            order.pk,
        )

    return {
        "payment_url": client.build_redirect_url(authority),
        "authority": authority,
        "amount": order.total_amount,
    }


# ---------------------------------------------------------------------------
# Verify callback
# ---------------------------------------------------------------------------
@transaction.atomic
def verify_payment(*, authority: str, status: str) -> Payment:
    """
    Idempotent verification.

    - Locks the Payment row.
    - If already SUCCEEDED → returns it (safe re-delivery).
    - If already FAILED / CANCELED → raises PaymentNotVerifiableError.
    - Calls Zarinpal verify (100 = success, 101 = already verified).
    - On success, transitions the order via `mark_order_paid`.
    """
    try:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .get(authority=authority)
        )
    except Payment.DoesNotExist:
        raise NotFoundError(
            message="تراکنش یافت نشد.",
            code="PAYMENT_NOT_FOUND",
        )

    if payment.status == Payment.Status.SUCCEEDED:
        logger.info("Payment %s already succeeded; returning idempotently.", payment.pk)
        return payment

    if payment.status in {Payment.Status.FAILED, Payment.Status.CANCELED}:
        raise PaymentNotVerifiableError(
            message="این تراکنش در وضعیت قابل تأیید نیست.",
            details={"status": payment.status},
        )

    if status != "OK":
        payment.status = Payment.Status.FAILED
        payment.failed_at = timezone.now()
        payment.gateway_response_message = f"callback status={status}"
        payment.save(
            update_fields=[
                "status",
                "failed_at",
                "gateway_response_message",
                "updated_at",
            ]
        )
        return payment

    client = ZarinpalClient()
    try:
        verify_data = client.verify_payment(
            amount=payment.amount,
            authority=payment.authority,
        )
    except ZarinpalVerifyError as exc:
        payment.status = Payment.Status.FAILED
        payment.failed_at = timezone.now()
        payment.gateway_response_message = str(exc.details)
        payment.save(
            update_fields=[
                "status",
                "failed_at",
                "gateway_response_message",
                "updated_at",
            ]
        )
        raise

    payment.status = Payment.Status.SUCCEEDED
    payment.ref_id = str(verify_data.get("ref_id", ""))
    payment.gateway_response_code = verify_data.get("code")
    payment.gateway_response_message = "verified"
    payment.verified_at = timezone.now()
    payment.save(
        update_fields=[
            "status",
            "ref_id",
            "gateway_response_code",
            "gateway_response_message",
            "verified_at",
            "updated_at",
        ]
    )

    order = mark_order_paid(
        order_id=payment.order_id, paid_at=payment.verified_at
    )
    # Publish only after the payment/order transaction commits.
    transaction.on_commit(
        lambda: publish_order_event(order, "order.created_or_paid")
    )
    logger.info(
        "Payment %s verified (ref_id=%s) for order %s",
        payment.pk,
        payment.ref_id,
        payment.order_id,
    )
    return payment


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------
def retry_payment(*, order_id: int) -> dict[str, Any]:
    order = Order.objects.get(pk=order_id)
    if order.status != Order.Status.PENDING_PAYMENT:
        raise OrderStateError(
            message="سفارش در وضعیت قابل پرداخت مجدد نیست.",
            details={"status": order.status},
        )
    if order.expires_at and timezone.now() > order.expires_at:
        raise OrderStateError(
            message="مهلت پرداخت این سفارش به پایان رسیده است.",
        )
    return start_payment_for_order(order=order)


# ---------------------------------------------------------------------------
# Re-verify pending payments (Celery task)
# ---------------------------------------------------------------------------
def reverify_pending_payments() -> int:
    from .selectors import list_payments_needing_reverify

    count = 0
    for payment in list_payments_needing_reverify():
        try:
            verify_payment(authority=payment.authority, status="OK")
            count += 1
        except Exception:
            logger.warning(
                "Re-verify failed for payment %s; will retry next cycle.",
                payment.pk,
                exc_info=True,
            )
    return count