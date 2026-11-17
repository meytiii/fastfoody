from __future__ import annotations

from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.accounts import selectors, services
from common.permissions import IsStaffUser

from .serializers import (
    CustomerDetailSerializer,
    CustomerListSerializer,
    CustomerNoteCreateSerializer,
    CustomerNoteSerializer,
    CustomerUpdateSerializer,
    StaffLoginSerializer,
    StaffProfileSerializer,
)




from django.contrib.auth import login, logout
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny

from apps.accounts.throttles import StaffLoginThrottle


class CustomerListView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request) -> Response:
        search = request.query_params.get("search")
        is_blocked_param = request.query_params.get("is_blocked")
        is_blocked: bool | None = None
        if is_blocked_param is not None:
            is_blocked = is_blocked_param.lower() == "true"

        qs = selectors.list_customers(search=search, is_blocked=is_blocked)

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = CustomerListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CustomerDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request, pk: int) -> Response:
        data = selectors.get_customer_360(pk)
        return Response(CustomerDetailSerializer(data).data)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = CustomerUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        customer = services.update_customer(
            customer_id=pk,
            data=dict(serializer.validated_data),
        )
        return Response(CustomerListSerializer(customer).data)


class CustomerNoteListCreateView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request, pk: int) -> Response:
        notes = selectors.list_customer_notes(pk)
        return Response(CustomerNoteSerializer(notes, many=True).data)

    def post(self, request: Request, pk: int) -> Response:
        serializer = CustomerNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = services.create_customer_note(
            author=request.user,
            customer_id=pk,
            text=serializer.validated_data["text"],
        )
        return Response(
            CustomerNoteSerializer(note).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerNoteDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def delete(self, request: Request, pk: int, note_id: int) -> Response:
        services.delete_customer_note(customer_id=pk, note_id=note_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    



@ensure_csrf_cookie
def backoffice_csrf_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"csrf_token": get_token(request)})


class StaffLoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [StaffLoginThrottle]

    def post(self, request: Request) -> Response:
        serializer = StaffLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = services.staff_login(
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
        )
        login(
            request._request,
            customer,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        return Response(
            {
                "user": StaffProfileSerializer(customer).data,
                "csrf_token": get_token(request._request),
            }
        )


class StaffLogoutView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffMeView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request) -> Response:
        return Response(StaffProfileSerializer(request.user).data)

