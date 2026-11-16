from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class BusinessException(Exception):
    def __init__(self, message: str, code: str = "BUSINESS_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def custom_exception_handler(exc, context):
    if isinstance(exc, BusinessException):
        return Response(
            {
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is not None:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_OR_HTTP_ERROR",
                    "message": "خطا در پردازش درخواست.",
                    "details": response.data,
                },
            },
            status=response.status_code,
        )
    return None