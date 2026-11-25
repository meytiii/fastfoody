from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import Customer, CustomerAddress, CustomerNote


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "phone",
            "full_name",
            "is_blocked",
            "is_active",
            "date_joined",
            "created_at",
        )
        read_only_fields = fields


class CustomerAddressBackofficeSerializer(serializers.ModelSerializer):
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
        )
        read_only_fields = fields


class CustomerNoteSerializer(serializers.ModelSerializer):
    author_phone = serializers.CharField(source="author.phone", read_only=True, default=None)

    class Meta:
        model = CustomerNote
        fields = (
            "id",
            "text",
            "author_phone",
            "created_at",
        )
        read_only_fields = fields


class CustomerNoteCreateSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CustomerDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="customer.id")
    phone = serializers.CharField(source="customer.phone")
    full_name = serializers.CharField(source="customer.full_name")
    is_blocked = serializers.BooleanField(source="customer.is_blocked")
    is_active = serializers.BooleanField(source="customer.is_active")
    date_joined = serializers.DateTimeField(source="customer.date_joined")
    created_at = serializers.DateTimeField(source="customer.created_at")

    addresses = CustomerAddressBackofficeSerializer(many=True)
    notes = CustomerNoteSerializer(many=True)

    orders_count = serializers.IntegerField()
    completed_orders_count = serializers.IntegerField()
    lifetime_value = serializers.IntegerField()
    last_order_at = serializers.DateTimeField(allow_null=True)


class CustomerUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    is_blocked = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)


class StaffLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length=128, write_only=True)


class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "phone",
            "full_name",
            "is_staff",
            "is_superuser",
            "date_joined",
        )
        read_only_fields = fields


class StaffLoginResponseSerializer(serializers.Serializer):
    user = StaffProfileSerializer()
    csrf_token = serializers.CharField()


class CustomerListResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = CustomerListSerializer(many=True)