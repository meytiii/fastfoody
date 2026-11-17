from __future__ import annotations

from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.orders import selectors, services
from common.permissions import IsStaffUser

from .serializers import (
    CancelOrderSerializer,
    LiveOrderSerializer,
    OrderDetailBackofficeSerializer,
    OrderListBackofficeSerializer,
    PrepTimeUpdateSerializer,
    RecordRefundSerializer,
)


class OrderListView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

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

    def get(self, request: Request, pk: int) -> Response:
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class LiveOrdersView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request) -> Response:
        qs = selectors.get_live_orders()
        return Response(LiveOrderSerializer(qs, many=True).data)


class MarkReadyView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def post(self, request: Request, pk: int) -> Response:
        services.mark_order_ready(order_id=pk)
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class MarkCompletedView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def post(self, request: Request, pk: int) -> Response:
        services.mark_order_completed(order_id=pk)
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class MarkPrintedView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def post(self, request: Request, pk: int) -> Response:
        services.mark_order_printed(order_id=pk)
        order = selectors.get_order_backoffice(pk)
        return Response(OrderDetailBackofficeSerializer(order).data)


class CancelOrderView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

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