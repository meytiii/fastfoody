from __future__ import annotations

from typing import Any


class BusinessException(Exception):
    default_code = "BUSINESS_ERROR"
    default_message = "خطای عملیاتی رخ داده است."
    status_code = 400

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        details: Any = None,
        status_code: int | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.details = details
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class NotFoundError(BusinessException):
    default_code = "NOT_FOUND"
    default_message = "مورد درخواستی یافت نشد."
    status_code = 404


class PermissionDeniedError(BusinessException):
    default_code = "PERMISSION_DENIED"
    default_message = "شما مجاز به انجام این عملیات نیستید."
    status_code = 403


class ValidationError(BusinessException):
    default_code = "VALIDATION_ERROR"
    default_message = "داده‌های ورودی نامعتبر است."
    status_code = 422


class RestaurantClosedError(BusinessException):
    default_code = "RESTAURANT_CLOSED"
    default_message = "رستوران در حال حاضر سفارش نمی‌پذیرد."
    status_code = 409


class OrderStateError(BusinessException):
    default_code = "INVALID_ORDER_STATE"
    default_message = "وضعیت سفارش برای این عملیات معتبر نیست."
    status_code = 409


class PaymentError(BusinessException):
    default_code = "PAYMENT_ERROR"
    default_message = "خطا در فرآیند پرداخت رخ داده است."
    status_code = 402