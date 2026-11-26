from __future__ import annotations

from django.http import StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orders import selectors, services
from apps.orders.sse import make_sse_response, order_channel
from common.openapi import pagination_parameters
from common.serializers import ErrorEnvelopeSerializer
from common.views import StorefrontAPIView

from .serializers import (
    CancellationRequestSerializer,
    OrderCreateSerializer,
    OrderListResponseSerializer,
    OrderReadSerializer,
    ReorderResponseSerializer,
    ValidatePromoResponseSerializer,
    ValidatePromoSerializer,
)


class OrderListCreateView(StorefrontAPIView):
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
            promo_code=serializer.validated_data.get("promo_code"),
        )
        order = selectors.get_order_for_customer(order.pk, request.user.pk)
        return Response(
            OrderReadSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(StorefrontAPIView):
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


class ValidatePromoView(StorefrontAPIView):
    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_validate_promo",
        summary="Validate a promo code for checkout",
        request=ValidatePromoSerializer,
        responses={
            200: ValidatePromoResponseSerializer,
            401: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ValidatePromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.validate_promo_code(
            customer=request.user,
            code=serializer.validated_data["code"],
            subtotal=serializer.validated_data["subtotal"],
        )
        return Response(result)


class OrderReorderView(StorefrontAPIView):
    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_reorder",
        summary="Rebuild a cart from a past order",
        request=None,
        responses={
            200: ReorderResponseSerializer,
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        payload = services.prepare_reorder_payload(request.user, pk)
        return Response(payload)


class OrderTrackingStreamView(StorefrontAPIView):
    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_stream",
        summary="Stream live status updates for one order (SSE)",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="text/event-stream",
            ),
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> StreamingHttpResponse:
        order = selectors.get_order_for_customer(pk, request.user.pk)
        return make_sse_response([order_channel(order.pk)])


class OrderRequestCancellationView(StorefrontAPIView):
    @extend_schema(
        tags=["Storefront — Orders"],
        operation_id="storefront_orders_request_cancellation",
        summary="Ask the restaurant to cancel a paid order",
        request=CancellationRequestSerializer,
        responses={
            200: OrderReadSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            409: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request: Request, pk: int) -> Response:
        serializer = CancellationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_cancellation(
            customer=request.user,
            order_id=pk,
            reason=serializer.validated_data.get("reason", ""),
        )
        order = selectors.get_order_for_customer(pk, request.user.pk)
        return Response(OrderReadSerializer(order).data)