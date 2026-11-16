from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.cms.constants import ALLOWED_SITE_SECTION_KEYS
from apps.cms.models import MediaAsset, RestaurantSettings, SiteSection


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    open_time = serializers.TimeField(
        format="%H:%M",
        input_formats=["%H:%M", "%H:%M:%S", "iso-8601"],
    )
    close_time = serializers.TimeField(
        format="%H:%M",
        input_formats=["%H:%M", "%H:%M:%S", "iso-8601"],
    )

    class Meta:
        model = RestaurantSettings
        fields = (
            "open_time",
            "close_time",
            "is_temporarily_closed",
            "in_zone_delivery_fee",
            "out_zone_delivery_fee",
            "prep_time_buffer_minutes",
            "updated_at",
        )
        read_only_fields = ("updated_at",)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance = self.instance
        if instance is None:
            return attrs
        open_time = attrs.get("open_time", instance.open_time)
        close_time = attrs.get("close_time", instance.close_time)
        if open_time == close_time:
            raise serializers.ValidationError(
                {
                    "close_time": "زمان باز و بسته شدن نمی‌تواند یکسان باشد.",
                }
            )
        return attrs


class SiteSectionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = ("key", "content", "updated_at")
        read_only_fields = ("key", "content", "updated_at")


class SiteSectionWriteSerializer(serializers.Serializer):
    content = serializers.JSONField()

    def validate_content(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("محتوای بخش باید یک آبجکت JSON باشد.")
        return value


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = (
            "id",
            "kind",
            "title",
            "alt_text",
            "file",
            "webp_file",
            "created_at",
        )
        read_only_fields = ("webp_file", "created_at")

    def validate_file(self, value: Any) -> Any:
        max_bytes = 10 * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError("حجم فایل نباید بیش از ۱۰ مگابایت باشد.")
        return value

    def validate_kind(self, value: str) -> str:
        if value not in dict(MediaAsset._meta.get_field("kind").choices):
            raise serializers.ValidationError("نوع فایل نامعتبر است.")
        return value


__all__ = [
    "ALLOWED_SITE_SECTION_KEYS",
    "MediaAssetSerializer",
    "RestaurantSettingsSerializer",
    "SiteSectionReadSerializer",
    "SiteSectionWriteSerializer",
]