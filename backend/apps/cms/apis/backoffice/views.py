from __future__ import annotations

from common.views import BackofficeAPIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser


from apps.cms.apis.serializers import (
    SiteSectionMapResponseSerializer,
    SiteSectionResponseSerializer,
)
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
from common.serializers import ErrorEnvelopeSerializer

from .serializers import (
    MediaAssetSerializer,
    MediaAssetUpdateSerializer,
    RestaurantSettingsSerializer,
    SiteSectionWriteSerializer,
)





class RestaurantSettingsView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_restaurant_settings_get",
        summary="Read restaurant settings",
        responses={
            200: RestaurantSettingsSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        instance = get_restaurant_settings()
        return Response(RestaurantSettingsSerializer(instance).data)

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_restaurant_settings_update",
        summary="Update restaurant settings",
        request=RestaurantSettingsSerializer,
        responses={
            200: RestaurantSettingsSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
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


class SiteSectionListView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_site_sections_list",
        summary="List all site sections",
        responses={
            200: SiteSectionMapResponseSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        return Response(get_all_site_sections())


class SiteSectionDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_site_section_get",
        summary="Read one site section",
        responses={
            200: SiteSectionResponseSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, key: str) -> Response:
        content = get_site_section(key)
        return Response({"key": key, "content": content})

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_site_section_upsert",
        summary="Create or replace one site section",
        request=SiteSectionWriteSerializer,
        responses={
            200: SiteSectionResponseSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def put(self, request: Request, key: str) -> Response:
        serializer = SiteSectionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section = upsert_site_section(
            key=key,
            content=serializer.validated_data["content"],
        )
        return Response({"key": section.key, "content": section.content})


class MediaAssetListCreateView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_media_assets_list",
        summary="List media assets",
        parameters=[
            OpenApiParameter(
                "kind",
                OpenApiTypes.STR,
                enum=["logo", "banner", "gallery"],
            )
        ],
        responses={
            200: MediaAssetSerializer(many=True),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        kind = request.query_params.get("kind")
        assets = list_media_assets(kind=kind)
        return Response(MediaAssetSerializer(assets, many=True).data)

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_media_assets_create",        summary="Upload a media asset",
        request=MediaAssetSerializer,
        responses={
            201: MediaAssetSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
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


class MediaAssetDetailView(BackofficeAPIView):
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_media_asset_detail",
        summary="Retrieve a media asset",
        responses={
            200: MediaAssetSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request: Request, pk: int) -> Response:
        asset = get_media_asset(pk)
        return Response(MediaAssetSerializer(asset).data)

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_media_asset_update",
        summary="Update media asset metadata",
        request=MediaAssetUpdateSerializer,
        responses={
            200: MediaAssetSerializer,
            400: ErrorEnvelopeSerializer,
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
            422: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request: Request, pk: int) -> Response:
        serializer = MediaAssetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        asset = update_media_asset(
            asset_id=pk, data=dict(serializer.validated_data)
        )
        return Response(MediaAssetSerializer(asset).data)

    @extend_schema(
        tags=["Backoffice — CMS"],
        operation_id="backoffice_cms_media_asset_delete",
        summary="Soft-delete a media asset",
        responses={
            204: OpenApiResponse(description="Media asset deleted."),
            401: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request: Request, pk: int) -> Response:
        soft_delete_media_asset(asset_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
