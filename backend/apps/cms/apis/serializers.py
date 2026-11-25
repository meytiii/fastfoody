"""CMS response shapes shared by Storefront and Backoffice schema docs."""

from __future__ import annotations

from rest_framework import serializers


class SiteSectionResponseSerializer(serializers.Serializer):
    key = serializers.CharField()
    content = serializers.JSONField()


class SiteSectionMapResponseSerializer(serializers.Serializer):
    """The merged map returned by the site-sections list endpoints."""

    hero = serializers.JSONField()
    header = serializers.JSONField()
    footer = serializers.JSONField()
    announcement = serializers.JSONField()
    lucky_wheel = serializers.JSONField()
    about_us = serializers.JSONField()
