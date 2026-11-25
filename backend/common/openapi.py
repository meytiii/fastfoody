"""Small helpers shared by the API schema annotations."""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from common.serializers import ErrorEnvelopeSerializer


def pagination_parameters() -> list[OpenApiParameter]:
    """The project-wide LimitOffsetPagination parameters."""
    return [
        OpenApiParameter(
            "limit",
            OpenApiTypes.INT,
            description="Maximum number of rows in this page (default 20).",
        ),
        OpenApiParameter(
            "offset",
            OpenApiTypes.INT,
            description="Number of rows to skip before this page.",
        ),
    ]


def error_responses(*status_codes: int) -> dict[int, type]:
    """Map status codes to the standard error envelope for schema output."""
    return {status: ErrorEnvelopeSerializer for status in status_codes}
