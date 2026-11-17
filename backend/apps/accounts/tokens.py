from __future__ import annotations

from typing import Any

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer


def issue_tokens_for_customer(customer: Customer) -> dict[str, str]:
    """Return {'access': ..., 'refresh': ...} for a customer."""
    refresh = RefreshToken.for_user(customer)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def blacklist_refresh_token(refresh_token: str) -> bool:
    """
    Attempt to blacklist a refresh token.

    Returns True if the token was successfully blacklisted, False if it was
    already invalid/blacklisted/expired. Raises nothing.
    """
    if not refresh_token:
        return False
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return True
    except TokenError:
        return False