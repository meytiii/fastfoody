from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsStaffUser(BasePermission):
    """Allow access only to authenticated staff users (Backoffice)."""

    message = "دسترسی فقط برای کارکنان مجاز است."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_staff", False)
        )