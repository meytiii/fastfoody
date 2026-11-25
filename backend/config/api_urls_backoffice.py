from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.urls import include, path


def backoffice_root(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {"success": True, "data": {"message": "Backoffice API placeholder"}}
    )


urlpatterns = [
    path("", backoffice_root, name="backoffice-root"),
    path("cms/", include("apps.cms.apis.backoffice.urls")),
    path("catalog/", include("apps.catalog.apis.backoffice.urls")),
    path("orders/", include("apps.orders.apis.backoffice.urls")),
    # Accounts owns /auth/... and /crm/customers/... itself.
    path("", include("apps.accounts.apis.backoffice.urls")),
    # Payments exposes /orders/<order_id>/payments/ (nested under orders).
    path("", include("apps.payments.apis.backoffice.urls")),
]