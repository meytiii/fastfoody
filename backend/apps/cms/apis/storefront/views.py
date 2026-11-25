from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cms.apis.serializers import (
    SiteSectionMapResponseSerializer,
    SiteSectionResponseSerializer,
)
from apps.cms.selectors import (
    get_all_site_sections,
    get_restaurant_status,
    get_site_section,
    list_media_assets,
)
from common.serializers import ErrorEnvelopeSerializer

from .serializers import (
    MediaAssetPublicSerializer,
    RestaurantStatusSerializer,
)


class RestaurantStatusView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — CMS"],
        operation_id="storefront_cms_restaurant_status",
        summary="Current open/closed status and delivery fees",
        responses={200: RestaurantStatusSerializer},
    )
    def get(self, request: Request) -> Response:
        serializer = RestaurantStatusSerializer(get_restaurant_status())
        return Response(serializer.data)


class SiteSectionListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — CMS"],
        operation_id="storefront_cms_site_sections_list",
        summary="Return every site section merged with defaults",
        responses={200: SiteSectionMapResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(get_all_site_sections())


class SiteSectionDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — CMS"],
        operation_id="storefront_cms_site_section_detail",
        summary="Return one site section",
        responses={
            200: SiteSectionResponseSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, key: str) -> Response:
        content = get_site_section(key)
        serializer = SiteSectionResponseSerializer({"key": key, "content": content})
        return Response(serializer.data)


class MediaAssetListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Storefront — CMS"],
        operation_id="storefront_cms_media_assets_list",
        summary="List public media assets",
        parameters=[
            OpenApiParameter(
                "kind",
                OpenApiTypes.STR,
                enum=["logo", "banner", "gallery"],
                description="Optional media kind filter.",
            )
        ],
        responses={200: MediaAssetPublicSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        kind = request.query_params.get("kind")
        assets = list_media_assets(kind=kind)
        return Response(MediaAssetPublicSerializer(assets, many=True).data)