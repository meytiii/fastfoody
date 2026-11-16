from __future__ import annotations

OTP_TTL_SECONDS: int = 120
OTP_LENGTH: int = 6
OTP_CACHE_AREA: str = "otp"
OTP_CACHE_SCOPE: str = "code"

CUSTOMER_EDITABLE_FIELDS: frozenset[str] = frozenset(
    {"full_name", "is_blocked", "is_active"}
)