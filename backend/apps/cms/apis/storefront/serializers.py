from __future__ import annotations

from rest_framework import serializers

from apps.cms.models import MediaAsset


class RestaurantStatusSerializer(serializers.Serializer):
    is_open = serializers.BooleanField()
    is_temporarily_closed = serializers.BooleanField()
    open_time = serializers.CharField()
    close_time = serializers.CharField()
    in_zone_delivery_fee = serializers.IntegerField()
    out_zone_delivery_fee = serializers.IntegerField()
    min_delivery_order_amount = serializers.IntegerField()
    packaging_fee = serializers.IntegerField()
    prep_time_buffer_minutes = serializers.IntegerField()


class SiteSectionPublicSerializer(serializers.Serializer):
    key = serializers.CharField()
    content = serializers.JSONField()


class MediaAssetPublicSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = ("kind", "title", "alt_text", "url")

    def get_url(self, obj: MediaAsset) -> str | None:
        if obj.webp_file:
            return obj.webp_file.url
        if obj.file:
            return obj.file.url
        return None