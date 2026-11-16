from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpRequest, JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"success": True, "data": {"status": "ok"}})


urlpatterns = [
    path("health/", health_view, name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/storefront/", include("config.api_urls_storefront")),
    path("api/v1/backoffice/", include("config.api_urls_backoffice")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)