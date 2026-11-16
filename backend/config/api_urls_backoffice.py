from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.urls import path


def backoffice_root(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "success": True,
            "data": {"message": "Backoffice API placeholder"},
        }
    )


urlpatterns = [
    path("", backoffice_root, name="backoffice-root"),
]