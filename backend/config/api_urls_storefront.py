from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.urls import path


def storefront_root(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "success": True,
            "data": {"message": "Storefront API placeholder"},
        }
    )


urlpatterns = [
    path("", storefront_root, name="storefront-root"),
]