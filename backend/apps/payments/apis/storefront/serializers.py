from __future__ import annotations

from rest_framework import serializers

from apps.payments.models import Payment


class PaymentRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class PaymentPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "amount",
            "status",
            "ref_id",
            "verified_at",
            "created_at",
        )
        read_only_fields = fields