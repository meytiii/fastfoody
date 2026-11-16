from __future__ import annotations

import json
import secrets
from typing import Any

from django.core.cache import cache

from common.cache import make_cache_key

from .constants import OTP_CACHE_AREA, OTP_CACHE_SCOPE, OTP_LENGTH, OTP_TTL_SECONDS


def _otp_key(phone: str) -> str:
    return make_cache_key(OTP_CACHE_AREA, f"{OTP_CACHE_SCOPE}:{phone}")


def generate_code() -> str:
    """Return a cryptographically secure numeric OTP."""
    upper = 10**OTP_LENGTH
    return str(secrets.randbelow(upper)).zfill(OTP_LENGTH)


def store_otp(*, phone: str, code: str) -> int:
    """Store the OTP in Redis with TTL; return TTL seconds."""
    payload: dict[str, Any] = {"code": code}
    cache.set(_otp_key(phone), json.dumps(payload), timeout=OTP_TTL_SECONDS)
    return OTP_TTL_SECONDS


def get_otp_code(*, phone: str) -> str | None:
    raw = cache.get(_otp_key(phone))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    code = data.get("code")
    return code if isinstance(code, str) else None


def delete_otp(*, phone: str) -> None:
    cache.delete(_otp_key(phone))