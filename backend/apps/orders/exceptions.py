from __future__ import annotations

from common.exceptions import NotFoundError


class OrderNotFoundError(NotFoundError):
    default_code = "ORDER_NOT_FOUND"
    default_message = "سفارش یافت نشد."