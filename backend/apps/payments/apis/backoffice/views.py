from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.payments.selectors import list_payments_for_order
from common.openapi import pagination_parameters
from common.permissions import IsStaffUser
from common.serializers import ErrorEnvelopeSerializer

from .serializers import (
    PaymentBackofficeSerializer,
    PaymentListResponseSerializer,
)


class OrderPaymentListView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Orders"],
        operation_id="backoffice_order_payments_list",
        summary="List payments of an order",
        parameters=pagination_parameters(),
        responses={
            200: PaymentListResponseSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, order_id: int) -> Response:
        qs = list_payments_for_order(order_id)
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PaymentBackofficeSerializer(page, many=True).data
        )