"""Serializers shared by OpenAPI documentation (no business behaviour)."""

from __future__ import annotations

from rest_framework import serializers


class CSRFResponseSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()


class ErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField(help_text="Stable machine-readable error code.")
    message = serializers.CharField(help_text="Human-readable (Persian) message.")
    details = serializers.JSONField(
        allow_null=True,
        help_text="Field errors or additional context; shape depends on the error.",
    )


class ErrorEnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    error = ErrorDetailSerializer()
