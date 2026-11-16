from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.accounts.models import Customer, CustomerAddress


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)


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
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_address_text(self, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("آدرس نمی‌تواند خالی باشد.")
        return cleaned