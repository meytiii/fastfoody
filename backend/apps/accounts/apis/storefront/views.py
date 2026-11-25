from __future__ import annotations

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenRefreshView as _SimpleJWTRefreshView

from apps.accounts import services, selectors, tokens
from apps.accounts.throttles import OTPRequestThrottle, OTPVerifyThrottle
from common.serializers import CSRFResponseSerializer, ErrorEnvelopeSerializer

from .serializers import (
    CustomerAddressSerializer,
    CustomerProfileSerializer,
    OTPRequestResponseSerializer,
    OTPRequestSerializer,
    OTPVerifyResponseSerializer,
    OTPVerifySerializer,
    TokenLogoutSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
)


class CSRFTokenView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_csrf",
        summary="Return a CSRF token and set the cookie",
        responses={200: CSRFResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response({"csrf_token": get_token(request)})


# Keep the response decorator on the resolved view so the cookie is always set.
csrf_token_view = ensure_csrf_cookie(CSRFTokenView.as_view())


class OTPRequestView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    @extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_otp_request",
        summary="Request an OTP code",
        request=OTPRequestSerializer,
        responses={
            200: OTPRequestResponseSerializer,
            400: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
            429: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_otp_verify",
        summary="Verify an OTP and start a session / issue JWTs",
        request=OTPVerifySerializer,
        responses={
            200: OTPVerifyResponseSerializer,
            400: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
            429: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_session_logout",
        summary="End the browser session",
        request=None,
        responses={
            204: OpenApiResponse(description="Session cleared."),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_me",
        summary="Return the authenticated customer profile",
        responses={
            200: CustomerProfileSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        return Response(CustomerProfileSerializer(request.user).data)


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Addresses"],
        operation_id="storefront_addresses_list",
        summary="List the customer's addresses",
        responses={
            200: CustomerAddressSerializer(many=True),
            401: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        addresses = selectors.list_addresses_for_customer(request.user)
        return Response(CustomerAddressSerializer(addresses, many=True).data)

    @extend_schema(
        tags=["Storefront — Addresses"],
        operation_id="storefront_addresses_create",
        summary="Create an address",
        request=CustomerAddressSerializer,
        responses={
            201: CustomerAddressSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Storefront — Addresses"],
        operation_id="storefront_address_detail",
        summary="Retrieve one address",
        responses={
            200: CustomerAddressSerializer,
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        address = selectors.get_address_for_customer(request.user, pk)
        return Response(CustomerAddressSerializer(address).data)

    @extend_schema(
        tags=["Storefront — Addresses"],
        operation_id="storefront_address_update",
        summary="Partially update one address",
        request=CustomerAddressSerializer,
        responses={
            200: CustomerAddressSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request: Request, pk: int) -> Response:
        serializer = CustomerAddressSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        address = services.update_address(
            customer=request.user,
            address_id=pk,
            data=dict(serializer.validated_data),
        )
        return Response(CustomerAddressSerializer(address).data)

    @extend_schema(
        tags=["Storefront — Addresses"],
        operation_id="storefront_address_delete",
        summary="Delete one address",
        responses={
            204: OpenApiResponse(description="Address deleted."),
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request: Request, pk: int) -> Response:
        services.delete_address(customer=request.user, address_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)




@extend_schema_view(
    post=extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_token_refresh",
        summary="Exchange a refresh token for a new access token",
        request=TokenRefreshRequestSerializer,
        responses={
            200: TokenRefreshResponseSerializer,
            401: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
)
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

    @extend_schema(
        tags=["Storefront — Auth"],
        operation_id="storefront_auth_token_logout",
        summary="Blacklist a refresh token",
        request=TokenLogoutSerializer,
        responses={
            204: OpenApiResponse(description="Token blacklisted."),
            400: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = TokenLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens.blacklist_refresh_token(serializer.validated_data["refresh"])

        # Best-effort session cleanup (no error if not authenticated)
        if request.user and request.user.is_authenticated:
            logout(request._request)

        return Response(status=status.HTTP_204_NO_CONTENT)