from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.accounts.models import Customer, CustomerAddress


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)


class OTPRequestResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="OTP lifetime in seconds.")


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=8)


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "phone",
            "full_name",
            "is_blocked",
            "date_joined",
            "created_at",
        )
        read_only_fields = fields


class CustomerAddressSerializer(serializers.ModelSerializer):
    #: Optional: when the customer already has the maximum number of addresses,
    #: replace this existing address instead of failing.
    replace_address_id = serializers.IntegerField(
        required=False, write_only=True, min_value=1
    )

    class Meta:
        model = CustomerAddress
        fields = (
            "id",
            "title",
            "address_text",
            "recipient_name",
            "recipient_phone",
            "is_out_of_zone",
            "is_default",
            "replace_address_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_address_text(self, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("آدرس نمی‌تواند خالی باشد.")
        return cleaned


class OTPVerifyResponseSerializer(serializers.Serializer):
    """Shape documented for OpenAPI — actual response is built in the view."""

    user = CustomerProfileSerializer()
    access = serializers.CharField()
    refresh = serializers.CharField()


class TokenLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()