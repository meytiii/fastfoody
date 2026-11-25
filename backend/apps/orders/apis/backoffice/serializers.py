from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import CustomerNote
from apps.orders.models import Order, OrderItem, OrderItemAddOn


class CustomerNoteSnapshotSerializer(serializers.ModelSerializer):
    author_phone = serializers.CharField(
        source="author.phone", allow_null=True, required=False
    )
    author_name = serializers.CharField(
        source="author.full_name", allow_null=True, required=False
    )

    class Meta:
        model = CustomerNote
        fields = ("text", "author_phone", "author_name", "created_at")
        read_only_fields = fields


class CustomerSnapshotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    phone = serializers.CharField()
    full_name = serializers.CharField(allow_blank=True)


class OrderItemAddOnBackofficeSerializer(serializers.ModelSerializer):
    addon_id = serializers.IntegerField(source="addon.id")

    class Meta:
        model = OrderItemAddOn
        fields = (
            "addon_id",
            "addon_name_snapshot",
            "unit_price_snapshot",
            "quantity",
            "line_total",
        )
        read_only_fields = fields


class OrderItemBackofficeSerializer(serializers.ModelSerializer):
    addons = OrderItemAddOnBackofficeSerializer(many=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product_name_snapshot",
            "unit_price_snapshot",
            "quantity",
            "addons_total",
            "line_total",
            "addons",
        )
        read_only_fields = fields


class OrderListBackofficeSerializer(serializers.ModelSerializer):
    customer_phone = serializers.CharField(source="customer.phone")
    customer_full_name = serializers.CharField(
        source="customer.full_name", allow_blank=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "daily_number",
            "status",
            "payment_status",
            "delivery_type",
            "customer_phone",
            "customer_full_name",
            "total_amount",
            "prep_time_minutes",
            "expected_ready_at",
            "is_printed",
            "created_at",
            "paid_at",
        )
        read_only_fields = fields


class OrderDetailBackofficeSerializer(serializers.ModelSerializer):
    customer = CustomerSnapshotSerializer()
    items = OrderItemBackofficeSerializer(many=True)
    customer_notes = CustomerNoteSnapshotSerializer(
        source="customer.notes", many=True, read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "daily_number",
            "daily_number_date",
            "status",
            "payment_status",
            "delivery_type",
            "delivery_address_snapshot",
            "delivery_recipient_name",
            "delivery_recipient_phone",
            "customer",
            "subtotal",
            "delivery_fee",
            "packaging_fee",
            "total_amount",
            "prep_time_minutes",
            "expected_ready_at",
            "paid_at",
            "is_printed",
            "printed_at",
            "notes_to_kitchen",
            "expires_at",
            "canceled_at",
            "canceled_by_id",
            "cancellation_reason",
            "cancellation_requested",
            "cancellation_request_reason",
            "cancellation_requested_at",
            "refund_card_number",
            "refund_tracking_code",
            "refunded_at",
            "created_at",
            "items",
            "customer_notes",
        )
        read_only_fields = fields


class LiveOrderSerializer(serializers.ModelSerializer):
    customer_phone = serializers.CharField(source="customer.phone")
    items = OrderItemBackofficeSerializer(many=True)
    customer_notes = CustomerNoteSnapshotSerializer(
        source="customer.notes", many=True, read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "daily_number",
            "status",
            "delivery_type",
            "customer_phone",
            "delivery_address_snapshot",
            "total_amount",
            "prep_time_minutes",
            "expected_ready_at",
            "paid_at",
            "is_printed",
            "printed_at",
            "notes_to_kitchen",
            "cancellation_requested",
            "cancellation_request_reason",
            "cancellation_requested_at",
            "created_at",
            "items",
            "customer_notes",
        )
        read_only_fields = fields


class BackofficeOrderListResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = OrderListBackofficeSerializer(many=True)


class PrepTimeUpdateSerializer(serializers.Serializer):
    prep_time_minutes = serializers.IntegerField(min_value=1)


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class RecordRefundSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=32)
    tracking_code = serializers.CharField(max_length=64)