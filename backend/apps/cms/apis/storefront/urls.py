from __future__ import annotations

from django.urls import path

from .views import (
    MediaAssetListView,
    RestaurantStatusView,
    SiteSectionDetailView,
    SiteSectionListView,
)

urlpatterns = [
    path(
        "restaurant-status/",
        RestaurantStatusView.as_view(),
        name="storefront-cms-restaurant-status",
    ),
    path(
        "site-sections/",
        SiteSectionListView.as_view(),
        name="storefront-cms-site-sections",
    ),
    path(
        "site-sections/<str:key>/",
        SiteSectionDetailView.as_view(),
        name="storefront-cms-site-section-detail",
    ),
    path(
        "media-assets/",
        MediaAssetListView.as_view(),
        name="storefront-cms-media-assets",
    ),
]