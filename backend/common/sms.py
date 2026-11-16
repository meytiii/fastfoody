from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

SMS_IR_BULK_URL = "https://api.sms.ir/v1/send/bulk"


def send_sms(*, phone: str, message: str) -> bool:
    """
    Send a single SMS via sms.ir bulk endpoint.

    Returns True if the SMS was accepted by the provider (or, in development
    when credentials are absent, if the message was logged instead).
    """
    api_key = getattr(settings, "SMS_IR_API_KEY", "") or ""
    sender = getattr(settings, "SMS_IR_SENDER", "") or ""

    if not api_key or not sender:
        logger.warning(
            "SMS_IR credentials are missing; message logged instead. "
            "phone=%s message=%r",
            phone,
            message,
        )
        return True

    payload = {
        "lineNumber": sender,
        "messageText": message,
        "mobiles": [phone],
        "sendDateTime": None,
    }

    request = urllib.request.Request(
        SMS_IR_BULK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            if data.get("status") == 1:
                return True
            logger.error("sms.ir rejected SMS: %s", body)
            return False
    except urllib.error.HTTPError as exc:
        logger.error(
            "sms.ir returned HTTP %s for phone=%s: %s",
            exc.code,
            phone,
            exc.read().decode("utf-8", errors="ignore"),
        )
        return False
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send SMS via sms.ir for phone=%s", phone)
        return False