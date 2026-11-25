from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.accounts import selectors, services
from common.openapi import pagination_parameters
from common.permissions import IsStaffUser
from common.serializers import CSRFResponseSerializer, ErrorEnvelopeSerializer

from .serializers import (
    CustomerDetailSerializer,
    CustomerListResponseSerializer,
    CustomerListSerializer,
    CustomerNoteCreateSerializer,
    CustomerNoteSerializer,
    CustomerUpdateSerializer,
    StaffLoginResponseSerializer,
    StaffLoginSerializer,
    StaffProfileSerializer,
)




from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny

from apps.accounts.throttles import StaffLoginThrottle


class CustomerListView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — CRM"],
        operation_id="backoffice_customers_list",
        summary="List customers",
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                description="Case-insensitive match on phone or full name.",
            ),
            OpenApiParameter(
                "is_blocked",
                OpenApiTypes.BOOL,
                description="Filter by blocked state.",
            ),
            *pagination_parameters(),
        ],
        responses={
            200: CustomerListResponseSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Backoffice — CRM"],
        operation_id="backoffice_customer_detail",
        summary="Customer 360 view",
        responses={
            200: CustomerDetailSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        data = selectors.get_customer_360(pk)
        return Response(CustomerDetailSerializer(data).data)

    @extend_schema(
        tags=["Backoffice — CRM"],
        operation_id="backoffice_customer_update",
        summary="Update customer flags / display name",
        request=CustomerUpdateSerializer,
        responses={
            200: CustomerListSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Backoffice — CRM"],
        operation_id="backoffice_customer_notes_list",
        summary="List a customer's notes",
        responses={
            200: CustomerNoteSerializer(many=True),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        notes = selectors.list_customer_notes(pk)
        return Response(CustomerNoteSerializer(notes, many=True).data)

    @extend_schema(
        tags=["Backoffice — CRM"],
        operation_id="backoffice_customer_notes_create",
        summary="Add a note to a customer",
        request=CustomerNoteCreateSerializer,
        responses={
            201: CustomerNoteSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Backoffice — CRM"],
        operation_id="backoffice_customer_notes_delete",
        summary="Delete a customer note",
        responses={
            204: OpenApiResponse(description="Note deleted."),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request: Request, pk: int, note_id: int) -> Response:
        services.delete_customer_note(customer_id=pk, note_id=note_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    



class BackofficeCSRFView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Backoffice — Auth"],
        operation_id="backoffice_auth_csrf",
        summary="Return a CSRF token and set the cookie",
        responses={200: CSRFResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response({"csrf_token": get_token(request)})


backoffice_csrf_view = ensure_csrf_cookie(BackofficeCSRFView.as_view())


class StaffLoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [StaffLoginThrottle]

    @extend_schema(
        tags=["Backoffice — Auth"],
        operation_id="backoffice_auth_login",
        summary="Staff login (creates a session)",
        request=StaffLoginSerializer,
        responses={
            200: StaffLoginResponseSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
            429: ErrorEnvelopeSerializer,
        },
    )
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

    @extend_schema(
        tags=["Backoffice — Auth"],
        operation_id="backoffice_auth_logout",
        summary="Staff logout",
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


class StaffMeView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — Auth"],
        operation_id="backoffice_auth_me",
        summary="Return the logged-in staff profile",
        responses={
            200: StaffProfileSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        return Response(StaffProfileSerializer(request.user).data)

