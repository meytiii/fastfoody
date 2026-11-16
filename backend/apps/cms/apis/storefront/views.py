from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cms.selectors import (
    get_all_site_sections,
    get_restaurant_status,
    get_site_section,
    list_media_assets,
)

from .serializers import (
    MediaAssetPublicSerializer,
    RestaurantStatusSerializer,
    SiteSectionPublicSerializer,
)


class RestaurantStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = RestaurantStatusSerializer(get_restaurant_status())
        return Response(serializer.data)


class SiteSectionListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(get_all_site_sections())


class SiteSectionDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, key: str) -> Response:
        content = get_site_section(key)
        serializer = SiteSectionPublicSerializer({"key": key, "content": content})
        return Response(serializer.data)


class MediaAssetListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        kind = request.query_params.get("kind")
        assets = list_media_assets(kind=kind)
        return Response(MediaAssetPublicSerializer(assets, many=True).data)