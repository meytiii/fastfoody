from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

from .exceptions import ZarinpalRequestError, ZarinpalVerifyError

logger = logging.getLogger(__name__)


class ZarinpalClient:
    """
    Minimal Zarinpal v4 REST client.

    Docs: https://www.zarinpal.com/docs/paymentGateway/
    """

    def __init__(
        self,
        merchant_id: str | None = None,
        sandbox: bool | None = None,
    ) -> None:
        self.merchant_id = merchant_id or settings.ZARINPAL_MERCHANT_ID
        self.sandbox = settings.ZARINPAL_SANDBOX if sandbox is None else sandbox

        if not self.merchant_id:
            raise ZarinpalRequestError(
                message="ZARINPAL_MERCHANT_ID تنظیم نشده است.",
            )

        base = "sandbox" if self.sandbox else "payment"
        self.request_url = f"https://{base}.zarinpal.com/pg/v4/payment/request.json"
        self.verify_url = f"https://{base}.zarinpal.com/pg/v4/payment/verify.json"
        self.startpay_url = f"https://{base}.zarinpal.com/pg/StartPay"

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
            logger.error("Zarinpal HTTP %s: %s", exc.code, raw)
            raise ZarinpalRequestError(
                message="درگاه پرداخت پاسخ معتبری برنگرداند.",
                details={"http_status": exc.code},
            )
        except Exception:
            logger.exception("Zarinpal network failure")
            raise ZarinpalRequestError(
                message="ارتباط با درگاه پرداخت برقرار نشد.",
            )

        try:
            data = json.loads(raw)
        except ValueError:
            logger.error("Zarinpal non-JSON response: %s", raw)
            raise ZarinpalRequestError(
                message="پاسخ درگاه قابل پردازش نیست.",
            )

        return data

    def request_payment(
        self,
        *,
        amount: int,
        description: str,
        callback_url: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "description": description,
            "callback_url": callback_url or settings.ZARINPAL_CALLBACK_URL,
        }
        data = self._post(self.request_url, payload)

        if data.get("data", {}).get("code") != 100:
            error_code = data.get("errors", {}).get("code")
            logger.error("Zarinpal request failed: %s", data)
            raise ZarinpalRequestError(
                message="درگاه پرداخت درخواست را رد کرد.",
                details={"zarinpal_code": error_code},
            )

        return data["data"]

    def verify_payment(
        self,
        *,
        amount: int,
        authority: str,
    ) -> dict[str, Any]:
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority,
        }
        data = self._post(self.verify_url, payload)

        result = data.get("data", {})
        code = result.get("code")

        # 100 = fresh success; 101 = already verified (idempotent success)
        if code not in (100, 101):
            logger.error("Zarinpal verify rejected: %s", data)
            raise ZarinpalVerifyError(
                message="تأیید پرداخت ناموفق بود.",
                details={"zarinpal_code": code},
            )

        return result

    def build_redirect_url(self, authority: str) -> str:
        return f"{self.startpay_url}/{authority}"