from __future__ import annotations

from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView

from common.permissions import IsStaffUser


class BackofficeAPIView(APIView):
    """
    Base class for every Backoffice endpoint.

    Enforces SessionAuthentication only — JWT issued for the Storefront
    is intentionally rejected here, preserving decision D4.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsStaffUser]