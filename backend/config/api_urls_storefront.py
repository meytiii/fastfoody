from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.urls import include, path


def storefront_root(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {"success": True, "data": {"message": "Storefront API placeholder"}}
    )


urlpatterns = [
    path("", storefront_root, name="storefront-root"),
    path("auth/", include("apps.accounts.apis.storefront.urls")),
    path("cms/", include("apps.cms.apis.storefront.urls")),
    path("catalog/", include("apps.catalog.apis.storefront.urls")),
    path("orders/", include("apps.orders.apis.storefront.urls")),

]