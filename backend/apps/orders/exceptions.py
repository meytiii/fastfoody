from __future__ import annotations

from common.exceptions import NotFoundError


class OrderNotFoundError(NotFoundError):
    default_code = "ORDER_NOT_FOUND"
    default_message = "سفارش یافت نشد."


class PromoCodeNotFoundError(NotFoundError):
    default_code = "PROMO_CODE_NOT_FOUND"
    default_message = "کد تخفیف یافت نشد."