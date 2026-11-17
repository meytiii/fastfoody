from __future__ import annotations

import hmac
import logging
import re
from typing import Any

from django.db import transaction
from django.utils import timezone

from common.cache import make_cache_key
from common.exceptions import NotFoundError, PermissionDeniedError, ValidationError

from . import otp as otp_service
from .constants import CUSTOMER_EDITABLE_FIELDS
from .exceptions import (
    AccountBlockedError,
    AccountInactiveError,
    OTPExpiredError,
    OTPInvalidError,
)
from .models import Customer, CustomerAddress, CustomerNote
from .tasks import send_otp_sms

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phone normalization
# ---------------------------------------------------------------------------
def normalize_phone(phone: str) -> str:
    if not phone:
        raise ValidationError(
            message="شماره موبایل الزامی است.",
            details={"phone": "این فیلد الزامی است."},
        )

    digits = re.sub(r"\D", "", str(phone))

    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits

    if len(digits) != 11 or not digits.startswith("09"):
        raise ValidationError(
            message="فرمت شماره موبایل نامعتبر است.",
            details={"phone": "شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود."},
        )
    return digits


# ---------------------------------------------------------------------------
# OTP flow
# ---------------------------------------------------------------------------
def request_otp(*, phone: str) -> int:
    """Generate OTP, store in Redis, dispatch SMS task. Return TTL seconds."""
    normalized = normalize_phone(phone)

    code = otp_service.generate_code()
    ttl = otp_service.store_otp(phone=normalized, code=code)

    send_otp_sms.delay(normalized, code)

    logger.info("OTP dispatched for %s", normalized)
    return ttl


def verify_otp(*, phone: str, code: str) -> Customer:
    """Validate OTP, get-or-create customer, block inactive/blocked accounts."""
    normalized = normalize_phone(phone)

    stored = otp_service.get_otp_code(phone=normalized)
    if stored is None:
        raise OTPExpiredError()

    if not hmac.compare_digest(stored, code or ""):
        raise OTPInvalidError()

    otp_service.delete_otp(phone=normalized)

    customer, created = Customer.objects.get_or_create(phone=normalized)
    if created:
        customer.set_unusable_password()
        customer.save(update_fields=["password"])

    if customer.is_blocked:
        raise AccountBlockedError()
    if not customer.is_active:
        raise AccountInactiveError()

    return customer


# ---------------------------------------------------------------------------
# Customer addresses
# ---------------------------------------------------------------------------
@transaction.atomic
def create_address(
    *,
    customer: Customer,
    data: dict[str, Any],
) -> CustomerAddress:
    if data.get("is_default"):
        CustomerAddress.objects.filter(
            customer=customer, is_default=True
        ).update(is_default=False, updated_at=timezone.now())

    return CustomerAddress.objects.create(customer=customer, **data)


@transaction.atomic
def update_address(
    *,
    customer: Customer,
    address_id: int,
    data: dict[str, Any],
) -> CustomerAddress:
    try:
        address = CustomerAddress.objects.select_for_update().get(
            pk=address_id, customer=customer
        )
    except CustomerAddress.DoesNotExist:
        raise NotFoundError(
            message="آدرس یافت نشد.",
            code="ADDRESS_NOT_FOUND",
        )

    if data.get("is_default") is True:
        CustomerAddress.objects.filter(
            customer=customer, is_default=True
        ).exclude(pk=address.pk).update(
            is_default=False, updated_at=timezone.now()
        )

    for field, value in data.items():
        setattr(address, field, value)

    address.save(update_fields=list(data.keys()) + ["updated_at"])
    return address


@transaction.atomic
def delete_address(*, customer: Customer, address_id: int) -> None:
    try:
        address = CustomerAddress.objects.get(pk=address_id, customer=customer)
    except CustomerAddress.DoesNotExist:
        raise NotFoundError(
            message="آدرس یافت نشد.",
            code="ADDRESS_NOT_FOUND",
        )
    address.soft_delete()


# ---------------------------------------------------------------------------
# Customer CRM
# ---------------------------------------------------------------------------
@transaction.atomic
def update_customer(
    *,
    customer_id: int,
    data: dict[str, Any],
) -> Customer:
    try:
        customer = Customer.objects.select_for_update().get(pk=customer_id)
    except Customer.DoesNotExist:
        raise NotFoundError(
            message="مشتری یافت نشد.",
            code="CUSTOMER_NOT_FOUND",
        )

    for field in data:
        if field not in CUSTOMER_EDITABLE_FIELDS:
            raise ValidationError(
                message=f"فیلد قابل ویرایش نیست: {field}",
                details={field: "این فیلد قابل ویرایش نیست."},
            )
        setattr(customer, field, data[field])

    customer.save(update_fields=list(data.keys()) + ["updated_at"])
    return customer


def create_customer_note(
    *,
    author: Customer,
    customer_id: int,
    text: str,
) -> CustomerNote:
    if not customer_id:
        raise ValidationError(
            message="شناسه‌ی مشتری الزامی است.",
            details={"customer_id": "این فیلد الزامی است."},
        )
    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        raise NotFoundError(
            message="مشتری یافت نشد.",
            code="CUSTOMER_NOT_FOUND",
        )

    cleaned = (text or "").strip()
    if not cleaned:
        raise ValidationError(
            message="متن یادداشت خالی است.",
            details={"text": "این فیلد الزامی است."},
        )

    return CustomerNote.objects.create(
        customer=customer,
        author=author,
        text=cleaned,
    )


@transaction.atomic
def delete_customer_note(*, customer_id: int, note_id: int) -> None:
    try:
        note = CustomerNote.objects.get(pk=note_id, customer_id=customer_id)
    except CustomerNote.DoesNotExist:
        raise NotFoundError(
            message="یادداشت یافت نشد.",
            code="NOTE_NOT_FOUND",
        )
    note.soft_delete()


@transaction.atomic
def staff_login(*, phone: str, password: str) -> Customer:
    """
    Password-based staff login.

    - Normalizes phone; wrong format → InvalidCredentialsError.
    - Wrong phone/password → InvalidCredentialsError (no info leak).
    - Blocked/inactive/non-staff → raises their specific errors.
    """
    from .exceptions import (
        AccountBlockedError,
        AccountInactiveError,
        InvalidCredentialsError,
        NotStaffError,
    )

    try:
        normalized = normalize_phone(phone)
    except ValidationError:
        raise InvalidCredentialsError()

    try:
        customer = Customer.objects.select_for_update().get(phone=normalized)
    except Customer.DoesNotExist:
        raise InvalidCredentialsError()

    if customer.is_blocked:
        raise AccountBlockedError()
    if not customer.is_active:
        raise AccountInactiveError()
    if not customer.is_staff:
        raise NotStaffError()
    if not customer.check_password(password or ""):
        raise InvalidCredentialsError()

    customer.last_login = timezone.now()
    customer.save(update_fields=["last_login"])

    return customer