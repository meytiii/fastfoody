from __future__ import annotations

from common.exceptions import PermissionDeniedError, ValidationError


class OTPExpiredError(ValidationError):
    default_code = "OTP_EXPIRED"
    default_message = "کد تایید منقضی شده است. لطفاً کد جدید دریافت کنید."
    status_code = 400


class OTPInvalidError(ValidationError):
    default_code = "OTP_INVALID"
    default_message = "کد تایید نادرست است."
    status_code = 400


class AccountBlockedError(PermissionDeniedError):
    default_code = "ACCOUNT_BLOCKED"
    default_message = "حساب کاربری شما مسدود شده است. لطفاً با پشتیبانی تماس بگیرید."
    status_code = 403


class AccountInactiveError(PermissionDeniedError):
    default_code = "ACCOUNT_INACTIVE"
    default_message = "حساب کاربری شما فعال نیست."
    status_code = 403