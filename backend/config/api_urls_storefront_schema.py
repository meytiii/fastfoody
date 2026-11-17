from django.urls import include, path

urlpatterns = [
    path("api/v1/storefront/", include("config.api_urls_storefront")),
]