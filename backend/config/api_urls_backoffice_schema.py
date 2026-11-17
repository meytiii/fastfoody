from django.urls import include, path

urlpatterns = [
    path("api/v1/backoffice/", include("config.api_urls_backoffice")),
]