from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog import selectors

from .serializers import ProductDetailPublicSerializer


class MenuView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(selectors.get_storefront_menu())


class LuckyWheelView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        category_slug = request.query_params.get("category")
        return Response(
            selectors.get_lucky_wheel_products(category_slug=category_slug)
        )


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, slug: str) -> Response:
        product = selectors.get_storefront_product(slug)
        return Response(ProductDetailPublicSerializer(product).data)