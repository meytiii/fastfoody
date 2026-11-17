from __future__ import annotations

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenRefreshView as _SimpleJWTRefreshView

from apps.accounts import services, selectors, tokens
from apps.accounts.throttles import OTPRequestThrottle, OTPVerifyThrottle

from .serializers import (
    CustomerAddressSerializer,
    CustomerProfileSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    TokenLogoutSerializer,
)


# Django view (not DRF) so @ensure_csrf_cookie actually sets the cookie.
@ensure_csrf_cookie
def csrf_token_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"csrf_token": get_token(request)})


class OTPRequestView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request: Request) -> Response:
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expires_in = services.request_otp(phone=serializer.validated_data["phone"])
        return Response(
            {"message": "کد تایید ارسال شد.", "expires_in": expires_in}
        )


class OTPVerifyView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request: Request) -> Response:
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = services.verify_otp(
            phone=serializer.validated_data["phone"],
            code=serializer.validated_data["code"],
        )

        # Session (backward compatibility + browser flows)
        login(
            request._request,
            customer,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        # JWT (for SPA / mobile)
        token_pair = tokens.issue_tokens_for_customer(customer)

        return Response(
            {
                "user": CustomerProfileSerializer(customer).data,
                "access": token_pair["access"],
                "refresh": token_pair["refresh"],
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(CustomerProfileSerializer(request.user).data)


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        addresses = selectors.list_addresses_for_customer(request.user)
        return Response(CustomerAddressSerializer(addresses, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = CustomerAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = services.create_address(
            customer=request.user,
            data=dict(serializer.validated_data),
        )
        return Response(
            CustomerAddressSerializer(address).data,
            status=status.HTTP_201_CREATED,
        )


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        address = selectors.get_address_for_customer(request.user, pk)
        return Response(CustomerAddressSerializer(address).data)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = CustomerAddressSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        address = services.update_address(
            customer=request.user,
            address_id=pk,
            data=dict(serializer.validated_data),
        )
        return Response(CustomerAddressSerializer(address).data)

    def delete(self, request: Request, pk: int) -> Response:
        services.delete_address(customer=request.user, address_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)




class TokenRefreshView(_SimpleJWTRefreshView):
    """Public: exchange a refresh token for a fresh access (and rotated refresh)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]


class TokenLogoutView(APIView):
    """
    Public: blacklist the provided refresh token.

    Also clears an active session if one exists, so the same endpoint can be
    used by both JWT and Session clients.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = TokenLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens.blacklist_refresh_token(serializer.validated_data["refresh"])

        # Best-effort session cleanup (no error if not authenticated)
        if request.user and request.user.is_authenticated:
            logout(request._request)

        return Response(status=status.HTTP_204_NO_CONTENT)