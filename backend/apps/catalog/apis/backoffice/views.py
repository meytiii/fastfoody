from __future__ import annotations

from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from common.views import BackofficeAPIView

from apps.catalog import selectors, services
from common.permissions import IsStaffUser

from .serializers import (
    AddOnSerializer,
    AddOnUpdateSerializer,
    AddOnWriteSerializer,
    AddonLinksWriteSerializer,
    CategoryReadSerializer,
    CategoryUpdateSerializer,
    CategoryWriteSerializer,
    ImageUploadSerializer,
    ProductDetailReadSerializer,
    ProductReadSerializer,
    ProductUpdateSerializer,
    ProductWriteSerializer,
)


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class CategoryListCreateView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        is_active_param = request.query_params.get("is_active")
        is_active = (
            None
            if is_active_param is None
            else is_active_param.lower() == "true"
        )
        qs = selectors.list_categories_backoffice(is_active=is_active)

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            CategoryReadSerializer(page, many=True).data
        )

    def post(self, request: Request) -> Response:
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = services.create_category(data=dict(serializer.validated_data))
        return Response(
            CategoryReadSerializer(category).data,
            status=status.HTTP_201_CREATED,
        )


class CategoryDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request, pk: int) -> Response:
        category = selectors.get_category_backoffice(pk)
        return Response(CategoryReadSerializer(category).data)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = CategoryUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = services.update_category(
            category_id=pk, data=dict(serializer.validated_data)
        )
        return Response(CategoryReadSerializer(category).data)

    def delete(self, request: Request, pk: int) -> Response:
        services.delete_category(category_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryImageUploadView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser]

    def post(self, request: Request, pk: int) -> Response:
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = services.update_category(
            category_id=pk,
            data={"image": serializer.validated_data["image"]},
        )
        return Response(CategoryReadSerializer(category).data)


# ---------------------------------------------------------------------------
# AddOn
# ---------------------------------------------------------------------------
class AddOnListCreateView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        is_available_param = request.query_params.get("is_available")
        is_available = (
            None
            if is_available_param is None
            else is_available_param.lower() == "true"
        )
        qs = selectors.list_addons_backoffice(is_available=is_available)

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            AddOnSerializer(page, many=True).data
        )

    def post(self, request: Request) -> Response:
        serializer = AddOnWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        addon = services.create_addon(data=dict(serializer.validated_data))
        return Response(
            AddOnSerializer(addon).data,
            status=status.HTTP_201_CREATED,
        )


class AddOnDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request, pk: int) -> Response:
        addon = selectors.get_addon_backoffice(pk)
        return Response(AddOnSerializer(addon).data)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = AddOnUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        addon = services.update_addon(
            addon_id=pk, data=dict(serializer.validated_data)
        )
        return Response(AddOnSerializer(addon).data)

    def delete(self, request: Request, pk: int) -> Response:
        services.delete_addon(addon_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class ProductListCreateView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        category_id_raw = request.query_params.get("category_id")
        is_main_dish_raw = request.query_params.get("is_main_dish")
        qs = selectors.list_products_backoffice(
            category_id=int(category_id_raw) if category_id_raw else None,
            status=request.query_params.get("status"),
            is_main_dish=(
                None
                if is_main_dish_raw is None
                else is_main_dish_raw.lower() == "true"
            ),
            search=request.query_params.get("search"),
        )

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            ProductReadSerializer(page, many=True).data
        )

    def post(self, request: Request) -> Response:
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = services.create_product(data=dict(serializer.validated_data))
        product = selectors.get_product_backoffice(product.pk)
        return Response(
            ProductDetailReadSerializer(product).data,
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request, pk: int) -> Response:
        product = selectors.get_product_backoffice(pk)
        return Response(ProductDetailReadSerializer(product).data)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = ProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        services.update_product(
            product_id=pk, data=dict(serializer.validated_data)
        )
        product = selectors.get_product_backoffice(pk)
        return Response(ProductDetailReadSerializer(product).data)

    def delete(self, request: Request, pk: int) -> Response:
        services.delete_product(product_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductImageUploadView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser]

    def post(self, request: Request, pk: int) -> Response:
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.set_product_image(
            product_id=pk, image=serializer.validated_data["image"]
        )
        product = selectors.get_product_backoffice(pk)
        return Response(ProductDetailReadSerializer(product).data)


class ProductAddonsView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser]

    def get(self, request: Request, pk: int) -> Response:
        product = selectors.get_product_backoffice(pk)
        return Response(ProductDetailReadSerializer(product).data)

    def put(self, request: Request, pk: int) -> Response:
        serializer = AddonLinksWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.set_product_addons(
            product_id=pk,
            addon_links=list(serializer.validated_data["addons"]),
        )
        product = selectors.get_product_backoffice(pk)
        return Response(ProductDetailReadSerializer(product).data)