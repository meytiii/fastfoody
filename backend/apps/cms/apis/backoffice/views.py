from __future__ import annotations

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser


from apps.cms.selectors import (
    get_all_site_sections,
    get_restaurant_settings,
    get_site_section,
    list_media_assets,
    get_media_asset,
)
from apps.cms.services import (
    create_media_asset,
    soft_delete_media_asset,
    update_restaurant_settings,
    upsert_site_section,
    update_media_asset,
)
from common.permissions import IsStaffUser

from .serializers import (
    MediaAssetSerializer,
    RestaurantSettingsSerializer,
    SiteSectionWriteSerializer,
    MediaAssetUpdateSerializer,
)





class RestaurantSettingsView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request) -> Response:
        instance = get_restaurant_settings()
        return Response(RestaurantSettingsSerializer(instance).data)

    def patch(self, request: Request) -> Response:
        instance = get_restaurant_settings()
        serializer = RestaurantSettingsSerializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        updated = update_restaurant_settings(data=serializer.validated_data)
        return Response(RestaurantSettingsSerializer(updated).data)


class SiteSectionListView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request) -> Response:
        return Response(get_all_site_sections())


class SiteSectionDetailView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request: Request, key: str) -> Response:
        content = get_site_section(key)
        return Response({"key": key, "content": content})

    def put(self, request: Request, key: str) -> Response:
        serializer = SiteSectionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section = upsert_site_section(
            key=key,
            content=serializer.validated_data["content"],
        )
        return Response({"key": section.key, "content": section.content})


class MediaAssetListCreateView(APIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request: Request) -> Response:
        kind = request.query_params.get("kind")
        assets = list_media_assets(kind=kind)
        return Response(MediaAssetSerializer(assets, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = MediaAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = create_media_asset(
            kind=serializer.validated_data["kind"],
            file=serializer.validated_data["file"],
            title=serializer.validated_data.get("title", ""),
            alt_text=serializer.validated_data.get("alt_text", ""),
        )
        return Response(
            MediaAssetSerializer(asset).data,
            status=status.HTTP_201_CREATED,
        )


class MediaAssetDetailView(APIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request: Request, pk: int) -> Response:
        asset = get_media_asset(pk)
        return Response(MediaAssetSerializer(asset).data)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = MediaAssetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        asset = update_media_asset(
            asset_id=pk, data=dict(serializer.validated_data)
        )
        return Response(MediaAssetSerializer(asset).data)

    def delete(self, request: Request, pk: int) -> Response:
        soft_delete_media_asset(asset_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
