from __future__ import annotations

from django.urls import path

from .views import LuckyWheelView, MenuView, ProductDetailView

urlpatterns = [
    path("menu/", MenuView.as_view(), name="storefront-catalog-menu"),
    path(
        "lucky-wheel/",
        LuckyWheelView.as_view(),
        name="storefront-catalog-lucky-wheel",
    ),
    path(
        "products/<slug:slug>/",
        ProductDetailView.as_view(),
        name="storefront-catalog-product-detail",
    ),
]