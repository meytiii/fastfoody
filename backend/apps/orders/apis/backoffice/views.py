from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.orders import selectors, services
from apps.orders.models import Order
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
    RecordRefundSerializer,
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