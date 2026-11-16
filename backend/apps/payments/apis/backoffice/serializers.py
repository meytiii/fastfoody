from __future__ import annotations

from rest_framework import serializers

from apps.payments.models import Payment


class PaymentBackofficeSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField()
    customer_phone = serializers.CharField(source="order.customer.phone")

    class Meta:
        model = Payment
        fields = (
            "id",
            "order_id",
            "customer_phone",
            "amount",
            "status",
            "authority",
            "ref_id",
            "gateway_response_code",
            "verified_at",
            "failed_at",
            "created_at",
        )
        read_only_fields = fields