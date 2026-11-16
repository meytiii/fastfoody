from __future__ import annotations

from common.exceptions import PaymentError


class ZarinpalRequestError(PaymentError):
    default_code = "ZARINPAL_REQUEST_FAILED"
    default_message = "ایجاد تراکنش در درگاه پرداخت با خطا مواجه شد."


class ZarinpalVerifyError(PaymentError):
    default_code = "ZARINPAL_VERIFY_FAILED"
    default_message = "تأیید پرداخت در درگاه با خطا مواجه شد."


class PaymentAlreadyVerifiedError(PaymentError):
    default_code = "PAYMENT_ALREADY_VERIFIED"
    default_message = "این تراکنش قبلاً تأیید شده است."
    status_code = 409


class PaymentNotVerifiableError(PaymentError):
    default_code = "PAYMENT_NOT_VERIFIABLE"
    default_message = "این تراکنش در وضعیت قابل تأیید نیست."
    status_code = 409