from __future__ import annotations

from django.http import HttpResponseRedirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.selectors import get_order_for_customer
from apps.payments import services
from apps.payments.selectors import get_payment_by_authority
from common.serializers import ErrorEnvelopeSerializer

from .serializers import (
    PaymentPublicSerializer,
    PaymentRequestSerializer,
    PaymentStartResponseSerializer,
)


class StartPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Payments"],
        operation_id="storefront_payments_start",
        summary="Create a payment and return the gateway URL",
        request=PaymentRequestSerializer,
        responses={
            201: PaymentStartResponseSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            402: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = get_order_for_customer(
            serializer.validated_data["order_id"], request.user.pk
        )
        payload = services.start_payment_for_order(order=order)
        return Response(payload, status=status.HTTP_201_CREATED)


class RetryPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Payments"],
        operation_id="storefront_payments_retry",
        summary="Retry payment for an unpaid order",
        request=PaymentRequestSerializer,
        responses={
            201: PaymentStartResponseSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            402: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        get_order_for_customer(
            serializer.validated_data["order_id"], request.user.pk
        )
        payload = services.retry_payment(order_id=serializer.validated_data["order_id"])
        return Response(payload, status=status.HTTP_201_CREATED)


class ZarinpalCallbackView(APIView):
    """
    Public endpoint Zarinpal redirects to.

    Accepts GET ?Authority=...&Status=OK|NOK, verifies, and redirects the
    browser to a frontend URL (or returns JSON when `?format=json`).
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(
        tags=["Storefront — Payments"],
        operation_id="storefront_payments_callback",
        summary="Zarinpal browser callback",
        description=(
            "Zarinpal redirects the customer here. The payment is verified "
            "idempotently and the browser is redirected to the frontend result "
            "page, unless `format=json` is requested (JSON response instead)."
        ),
        parameters=[
            OpenApiParameter("Authority", OpenApiTypes.STR, required=True),
            OpenApiParameter(
                "Status",
                OpenApiTypes.STR,
                enum=["OK", "NOK"],
                required=True,
            ),
            OpenApiParameter(
                "format",
                OpenApiTypes.STR,
                enum=["json"],
                description="Return JSON instead of redirecting.",
            ),
        ],
        responses={
            200: PaymentPublicSerializer,
            302: OpenApiResponse(description="Redirect to the frontend result page."),
            402: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        authority = request.query_params.get("Authority", "")
        status_param = request.query_params.get("Status", "")

        try:
            payment = services.verify_payment(authority=authority, status=status_param)
        except Exception:
            # Always redirect; the frontend can show the failure to the user.
            frontend = getattr(
                __import__("django.conf", fromlist=["settings"]).settings,
                "PAYMENT_FRONTEND_RESULT_URL",
                "",
            )
            if frontend:
                return HttpResponseRedirect(
                    f"{frontend}?status=failed&authority={authority}"
                )
            return Response(
                {"success": False, "error": {"code": "PAYMENT_FAILED"}},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        if request.query_params.get("format") == "json":
            return Response(PaymentPublicSerializer(payment).data)

        frontend = getattr(
            __import__("django.conf", fromlist=["settings"]).settings,
            "PAYMENT_FRONTEND_RESULT_URL",
            "",
        )
        if frontend:
            return HttpResponseRedirect(
                f"{frontend}?status=success&authority={payment.authority}"
            )
        return Response(PaymentPublicSerializer(payment).data)


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Payments"],
        operation_id="storefront_payments_status",
        summary="Return the status of one payment",
        responses={
            200: PaymentPublicSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, authority: str) -> Response:
        payment = get_payment_by_authority(authority)
        if payment.order.customer_id != request.user.pk:
            from common.exceptions import PermissionDeniedError

            raise PermissionDeniedError(
                message="این تراکنش متعلق به شما نیست.",
            )
        return Response(PaymentPublicSerializer(payment).data)