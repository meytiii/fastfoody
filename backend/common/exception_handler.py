from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from common.exceptions import BusinessException

logger = logging.getLogger(__name__)


def _error_response(
    *,
    code: str,
    message: str,
    details: Any,
    status_code: int,
) -> Response:
    return Response(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
        },
        status=status_code,
    )


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    if isinstance(exc, BusinessException):
        return _error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            status_code=exc.status_code,
        )

    if isinstance(exc, DjangoValidationError):
        details = getattr(exc, "message_dict", None)
        if details is None:
            details = list(exc.messages)
        return _error_response(
            code="VALIDATION_ERROR",
            message="داده‌های ورودی نامعتبر است.",
            details=details,
            status_code=422,
        )

    response = drf_exception_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "API_ERROR").upper()
        return _error_response(
            code=code,
            message="درخواست نامعتبر است.",
            details=response.data,
            status_code=response.status_code,
        )

    logger.exception("Unhandled exception", exc_info=exc)
    return _error_response(
        code="INTERNAL_ERROR",
        message="خطای داخلی سرور رخ داده است.",
        details=None,
        status_code=500,
    )