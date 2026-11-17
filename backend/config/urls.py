from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpRequest, JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication

from common.permissions import IsStaffUser


def health_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"success": True, "data": {"status": "ok"}})


urlpatterns = [
    path("health/", health_view, name="health"),

    # Combined docs (convenience / backward compat)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Storefront-only docs (public)
    path(
        "api/v1/storefront/schema/",
        SpectacularAPIView.as_view(urlconf="config.api_urls_storefront_schema"),
        name="storefront-schema",
    ),
    path(
        "api/v1/storefront/docs/",
        SpectacularSwaggerView.as_view(url_name="storefront-schema"),
        name="storefront-swagger-ui",
    ),

    # Backoffice-only docs (staff only)
    path(
        "api/v1/backoffice/schema/",
        SpectacularAPIView.as_view(
            urlconf="config.api_urls_backoffice_schema",
            permission_classes=[IsStaffUser],
            authentication_classes=[SessionAuthentication],
        ),
        name="backoffice-schema",
    ),
    path(
        "api/v1/backoffice/docs/",
        SpectacularSwaggerView.as_view(
            url_name="backoffice-schema",
            permission_classes=[IsStaffUser],
            authentication_classes=[SessionAuthentication],
        ),
        name="backoffice-swagger-ui",
    ),

    # API mounts
    path("api/v1/storefront/", include("config.api_urls_storefront")),
    path("api/v1/backoffice/", include("config.api_urls_backoffice")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)