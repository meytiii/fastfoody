from __future__ import annotations

from django.urls import path

from .views import (
    MediaAssetDetailView,
    MediaAssetListCreateView,
    RestaurantSettingsView,
    SiteSectionDetailView,
    SiteSectionListView,
)

urlpatterns = [
    path(
        "restaurant-settings/",
        RestaurantSettingsView.as_view(),
        name="backoffice-cms-restaurant-settings",
    ),
    path(
        "site-sections/",
        SiteSectionListView.as_view(),
        name="backoffice-cms-site-sections",
    ),
    path(
        "site-sections/<str:key>/",
        SiteSectionDetailView.as_view(),
        name="backoffice-cms-site-section-detail",
    ),
    path(
        "media-assets/",
        MediaAssetListCreateView.as_view(),
        name="backoffice-cms-media-assets",
    ),
    path(
        "media-assets/<int:pk>/",
        MediaAssetDetailView.as_view(),
        name="backoffice-cms-media-asset-detail",
    ),
]