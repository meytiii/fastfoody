from __future__ import annotations

from django.urls import path

from .views import PromoCodeDetailView, PromoCodeListCreateView

urlpatterns = [
    path("", PromoCodeListCreateView.as_view(), name="backoffice-promo-codes"),
    path(
        "<int:pk>/",
        PromoCodeDetailView.as_view(),
        name="backoffice-promo-code-detail",
    ),
]
