from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.orders.models import Order, OrderItem, OrderItemAddOn


class OrderItemAddOnReadSerializer(serializers.ModelSerializer):
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


class OrderItemReadSerializer(serializers.ModelSerializer):
    addons = OrderItemAddOnReadSerializer(many=True)

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


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "daily_number",
            "status",
            "payment_status",
            "delivery_type",
            "delivery_address_snapshot",
            "delivery_recipient_name",
            "delivery_recipient_phone",
            "subtotal",
            "delivery_fee",
            "packaging_fee",
            "total_amount",
            "prep_time_minutes",
            "expected_ready_at",
            "paid_at",
            "notes_to_kitchen",
            "expires_at",
            "canceled_at",
            "cancellation_reason",
            "cancellation_requested",
            "cancellation_request_reason",
            "cancellation_requested_at",
            "created_at",
            "items",
        )
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Write serializers (input validation only)
# ---------------------------------------------------------------------------
class OrderItemAddOnWriteSerializer(serializers.Serializer):
    addon_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0)


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    addons = OrderItemAddOnWriteSerializer(many=True, required=False, default=list)


class OrderListResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = OrderReadSerializer(many=True)


class CancellationRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class OrderCreateSerializer(serializers.Serializer):
    delivery_type = serializers.ChoiceField(choices=Order.DeliveryType.choices)
    address_id = serializers.IntegerField(required=False, allow_null=True)
    notes_to_kitchen = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    items = OrderItemWriteSerializer(many=True)

    def validate_items(self, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not value:
            raise serializers.ValidationError("حداقل یک آیتم لازم است.")
        return value