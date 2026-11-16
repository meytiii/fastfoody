from __future__ import annotations

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class _BaseOTPThrottle(SimpleRateThrottle):
    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if request.method != "POST":
            return None
        phone = (request.data or {}).get("phone", "")
        phone = str(phone).strip()
        if not phone:
            return None
        ident = f"{phone}:{self.get_ident(request)}"
        return self.cache_format % {"scope": self.scope, "ident": ident}


class OTPRequestThrottle(_BaseOTPThrottle):
    scope = "otp_request"


class OTPVerifyThrottle(_BaseOTPThrottle):
    scope = "otp_verify"