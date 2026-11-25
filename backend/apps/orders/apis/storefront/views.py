from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders import selectors, services
from common.openapi import pagination_parameters
from common.serializers import ErrorEnvelopeSerializer

from .serializers import (
    OrderCreateSerializer,
    OrderListResponseSerializer,
    OrderReadSerializer,
)


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_list",
        summary="List the customer's orders",
        parameters=pagination_parameters(),
        responses={
            200: OrderListResponseSerializer,
            401: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        qs = selectors.list_orders_for_customer(request.user.pk)
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            OrderReadSerializer(page, many=True).data
        )

    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_create",
        summary="Place an order",
        request=OrderCreateSerializer,
        responses={
            201: OrderReadSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = services.create_order(
            customer=request.user,
            delivery_type=serializer.validated_data["delivery_type"],
            address_id=serializer.validated_data.get("address_id"),
            items=list(serializer.validated_data["items"]),
            notes_to_kitchen=serializer.validated_data.get("notes_to_kitchen", ""),
        )
        order = selectors.get_order_for_customer(order.pk, request.user.pk)
        return Response(
            OrderReadSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_detail",
        summary="Retrieve one of the customer's orders",
        responses={
            200: OrderReadSerializer,
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        order = selectors.get_order_for_customer(pk, request.user.pk)
        return Response(OrderReadSerializer(order).data)