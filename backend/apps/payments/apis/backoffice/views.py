from __future__ import annotations

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.selectors import list_payments_for_order
from common.permissions import IsStaffUser

from .serializers import PaymentBackofficeSerializer


class OrderPaymentListView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request, order_id: int) -> Response:
        qs = list_payments_for_order(order_id)
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PaymentBackofficeSerializer(page, many=True).data
        )