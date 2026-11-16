from __future__ import annotations

import logging

from celery import shared_task

from common.sms import send_sms

logger = logging.getLogger(__name__)


@shared_task(name="apps.accounts.tasks.send_otp_sms")
def send_otp_sms(phone: str, code: str) -> bool:
    message = (
        f"کد تایید شما: {code}\n"
        f"این کد ۲ دقیقه اعتبار دارد.\n"
        f"اگر این درخواست را شما نداده‌اید، نادیده بگیرید."
    )
    return send_sms(phone=phone, message=message)