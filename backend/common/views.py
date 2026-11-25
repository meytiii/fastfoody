from __future__ import annotations

from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.permissions import IsActiveCustomer, IsStaffUser


class StorefrontAPIView(APIView):
    """
    Base class for every Storefront endpoint.

    Uses JWTAuthentication only, so a staff session cookie is never accepted
    here and DRF does not enforce CSRF on these endpoints. Public views
    override ``permission_classes`` with ``AllowAny`` but keep JWT-only auth.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsActiveCustomer]


class BackofficeAPIView(APIView):
    """
    Base class for every Backoffice endpoint.

    Enforces SessionAuthentication only — JWT issued for the Storefront
    is intentionally rejected here, preserving decision D4.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsStaffUser]