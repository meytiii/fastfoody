from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings

from common.sms import send_sms

logger = logging.getLogger(__name__)


def _manager_phone() -> str:
    return getattr(settings, "MANAGER_PHONE", "") or ""


@shared_task(name="apps.orders.tasks.send_order_registered_sms")
def send_order_registered_sms(order_id: int) -> bool:
    from .models import Order

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return False

    phone = _manager_phone()
    if not phone:
        logger.warning(
            "MANAGER_PHONE not configured; skipping manager SMS for order %s.",
            order_id,
        )
        return False

    delivery_label = "پیک" if order.delivery_type == Order.DeliveryType.DELIVERY else "حضوری"
    message = (
        f"سفارش جدید #{order.daily_number or order.pk}\n"
        f"مبلغ: {order.total_amount:,} تومان\n"
        f"نوع: {delivery_label}"
    )
    return send_sms(phone=phone, message=message)


@shared_task(name="apps.orders.tasks.send_order_ready_sms")
def send_order_ready_sms(order_id: int) -> bool:
    from .models import Order

    try:
        order = Order.objects.select_related("customer").get(pk=order_id)
    except Order.DoesNotExist:
        return False

    message = (
        f"سفارش شما #{order.daily_number or order.pk} آماده است.\n"
        f"با تشکر از انتخاب شما."
    )
    return send_sms(phone=order.customer.phone, message=message)


@shared_task(name="apps.orders.tasks.send_prep_time_changed_sms")
def send_prep_time_changed_sms(order_id: int, new_minutes: int) -> bool:
    from .models import Order

    try:
        order = Order.objects.select_related("customer").get(pk=order_id)
    except Order.DoesNotExist:
        return False

    message = (
        f"زمان آماده‌سازی سفارش #{order.daily_number or order.pk} "
        f"به {new_minutes} دقیقه تغییر یافت."
    )
    return send_sms(phone=order.customer.phone, message=message)


@shared_task(name="apps.orders.tasks.cancel_expired_unpaid_orders")
def cancel_expired_unpaid_orders() -> int:
    from .services import cancel_expired_unpaid_orders as _cancel

    count = _cancel()
    if count:
        logger.info("Auto-canceled %s expired unpaid orders.", count)
    return count