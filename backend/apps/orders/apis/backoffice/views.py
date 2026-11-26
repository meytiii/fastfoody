from __future__ import annotations

from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.orders import selectors, services
from apps.orders.models import Order
from apps.orders.sse import POS_CHANNEL, make_sse_response
from common.openapi import pagination_parameters
from common.permissions import IsStaffUser
from common.serializers import ErrorEnvelopeSerializer

from .serializers import (
    CancelOrderSerializer,
    LiveOrderSerializer,
    OrderDetailBackofficeSerializer,
    OrderListBackofficeSerializer,
    BackofficeOrderListResponseSerializer,
    PrepTimeUpdateSerializer,
    PromoCodeListResponseSerializer,
    PromoCodeSerializer,
    RecordRefundSerializer,
    SalesAnalyticsQuerySerializer,
    SalesAnalyticsSerializer,
)


class OrderListView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_orders_list",
        summary="List orders with filters",
        parameters=[
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                enum=[choice for choice, _ in Order.Status.choices],
            ),
            OpenApiParameter(
                "payment_status",
                OpenApiTypes.STR,
                enum=[choice for choice, _ in Order.PaymentStatus.choices],
            ),
            OpenApiParameter(
                "delivery_type",
                OpenApiTypes.STR,
                enum=[choice for choice, _ in Order.DeliveryType.choices],
            ),
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                description="Order number, customer phone or name.",
            ),
            OpenApiParameter(
                "date_from",
                OpenApiTypes.DATE,
                description="Inclusive lower bound (ISO date).",
            ),
            OpenApiParameter(
                "date_to",
                OpenApiTypes.DATE,
                description="Inclusive upper bound (ISO date).",
            ),
            *pagination_parameters(),
        ],
        responses={
            200: BackofficeOrderListResponseSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        qs = selectors.list_orders_backoffice(
            status=request.query_params.get("status"),
            payment_status=request.query_params.get("payment_status"),
            delivery_type=request.query_params.get("delivery_type"),
            search=request.query_params.get("search"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            OrderListBackofficeSerializer(page, many=True).data
        )


class OrderDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_detail",
        summary="Retrieve an order",
        responses={
            200: OrderDetailBackofficeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class LiveOrdersView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_orders_live",
        summary="Orders currently in the kitchen",
        responses={
            200: LiveOrderSerializer(many=True),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        qs = selectors.get_live_orders()
        return Response(LiveOrderSerializer(qs, many=True).data)


class MarkReadyView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_mark_ready",
        summary="Mark an order ready",
        request=None,
        responses={
            200: OrderDetailBackofficeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        services.mark_order_ready(order_id=pk)
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class MarkCompletedView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_mark_completed",
        summary="Mark an order completed",
        request=None,
        responses={
            200: OrderDetailBackofficeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        services.mark_order_completed(order_id=pk)
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class MarkPrintedView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_mark_printed",
        summary="Mark an order printed",
        request=None,
        responses={
            200: OrderDetailBackofficeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        services.mark_order_printed(order_id=pk)
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class CancelOrderView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_cancel",
        summary="Cancel an order",
        request=CancelOrderSerializer,
        responses={
            200: OrderDetailBackofficeSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.cancel_order_by_manager(
            order_id=pk,
            manager=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class UpdatePrepTimeView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_prep_time",
        summary="Change the preparation time",
        request=PrepTimeUpdateSerializer,
        responses={
            200: OrderDetailBackofficeSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request: Request, pk: int) -> Response:
        serializer = PrepTimeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_prep_time(
            order_id=pk,
            new_prep_time_minutes=serializer.validated_data["prep_time_minutes"],
        )
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class RecordRefundView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_refund",
        summary="Record a manual refund",
        request=RecordRefundSerializer,
        responses={
            200: OrderDetailBackofficeSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        serializer = RecordRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.record_refund(
            order_id=pk,
            manager=request.user,
            card_number=serializer.validated_data["card_number"],
            tracking_code=serializer.validated_data["tracking_code"],
        )
        order = selectors.get_order_backoffice(pk)
        return Response(
            OrderDetailBackofficeSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class LiveOrdersStreamView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_orders_live_stream",
        summary="Stream kitchen order events (SSE)",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="text/event-stream",
            ),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Any:
        return make_sse_response([POS_CHANNEL])


# ---------------------------------------------------------------------------
# Promo codes
# ---------------------------------------------------------------------------
def _parse_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


class PromoCodeListCreateView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Promo Codes"],
        operation_id="backoffice_promo_codes_list",
        summary="List promo codes",
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                description="Case-insensitive code search.",
            ),
            OpenApiParameter(
                "is_active",
                OpenApiTypes.BOOL,
                description="Filter by active status.",
            ),
            *pagination_parameters(),
        ],
        responses={
            200: PromoCodeListResponseSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        active_param = request.query_params.get(
            "is_active", request.query_params.get("active")
        )
        qs = selectors.list_promo_codes(
            search=request.query_params.get("search"),
            is_active=_parse_bool(active_param),
        )
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PromoCodeSerializer(page, many=True).data
        )

    @extend_schema(
        tags=["Backoffice — Promo Codes"],
        operation_id="backoffice_promo_codes_create",
        summary="Create a promo code",
        request=PromoCodeSerializer,
        responses={
            201: PromoCodeSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PromoCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        promo = services.create_promo_code(
            data=dict(serializer.validated_data)
        )
        return Response(
            PromoCodeSerializer(promo).data,
            status=status.HTTP_201_CREATED,
        )


class PromoCodeDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Promo Codes"],
        operation_id="backoffice_promo_codes_detail",
        summary="Retrieve a promo code",
        responses={
            200: PromoCodeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        promo = selectors.get_promo_code(pk)
        return Response(PromoCodeSerializer(promo).data)

    @extend_schema(
        tags=["Backoffice — Promo Codes"],
        operation_id="backoffice_promo_codes_update",
        summary="Update a promo code",
        request=PromoCodeSerializer,
        responses={
            200: PromoCodeSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request: Request, pk: int) -> Response:
        promo = selectors.get_promo_code(pk)
        serializer = PromoCodeSerializer(
            promo, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        promo = services.update_promo_code(
            promo_code_id=pk,
            data=dict(serializer.validated_data),
        )
        promo = selectors.get_promo_code(promo.pk)
        return Response(PromoCodeSerializer(promo).data)

    @extend_schema(
        tags=["Backoffice — Promo Codes"],
        operation_id="backoffice_promo_codes_delete",
        summary="Delete a promo code",
        responses={
            204: None,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request: Request, pk: int) -> Response:
        services.delete_promo_code(promo_code_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Sales analytics
# ---------------------------------------------------------------------------
class SalesAnalyticsView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Analytics"],
        operation_id="backoffice_analytics_sales",
        summary="Sales and product analytics",
        parameters=[
            OpenApiParameter(
                "period",
                OpenApiTypes.STR,
                enum=["today", "7d", "30d", "custom"],
            ),
            OpenApiParameter(
                "date_from",
                OpenApiTypes.DATE,
                description="Required with date_to for a custom range.",
            ),
            OpenApiParameter(
                "date_to",
                OpenApiTypes.DATE,
                description="Inclusive upper bound for a custom range.",
            ),
        ],
        responses={
            200: SalesAnalyticsSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        serializer = SalesAnalyticsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = selectors.get_sales_analytics(
            period=data.get("period", "7d"),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
        )
        return Response(result)