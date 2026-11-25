from __future__ import annotations

from django.urls import path

from .views import (
    LuckyWheelView,
    MenuView,
    ProductDetailView,
    ProductListView,
    ProductSuggestionsView,
    UpsellView,
)

urlpatterns = [
    path("menu/", MenuView.as_view(), name="storefront-catalog-menu"),
    path(
        "lucky-wheel/",
        LuckyWheelView.as_view(),
        name="storefront-catalog-lucky-wheel",
    ),
    path(
        "products/",
        ProductListView.as_view(),
        name="storefront-catalog-products",
    ),
    path(
        "suggestions/",
        ProductSuggestionsView.as_view(),
        name="storefront-catalog-suggestions",
    ),
    path(
        "upsell/",
        UpsellView.as_view(),
        name="storefront-catalog-upsell",
    ),
    path(
        "products/<slug:slug>/",
        ProductDetailView.as_view(),
        name="storefront-catalog-product-detail",
    ),
]