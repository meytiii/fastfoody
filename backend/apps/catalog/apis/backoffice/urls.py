from __future__ import annotations

from django.urls import path

from .views import (
    AddOnDetailView,
    AddOnListCreateView,
    CategoryDetailView,
    CategoryImageUploadView,
    CategoryListCreateView,
    ProductAddonsView,
    ProductDetailView,
    ProductImageUploadView,
    ProductListCreateView,
)

urlpatterns = [
    # Categories
    path(
        "categories/",
        CategoryListCreateView.as_view(),
        name="backoffice-catalog-categories",
    ),
    path(
        "categories/<int:pk>/",
        CategoryDetailView.as_view(),
        name="backoffice-catalog-category-detail",
    ),
    path(
        "categories/<int:pk>/image/",
        CategoryImageUploadView.as_view(),
        name="backoffice-catalog-category-image",
    ),
    # Add-ons
    path(
        "addons/",
        AddOnListCreateView.as_view(),
        name="backoffice-catalog-addons",
    ),
    path(
        "addons/<int:pk>/",
        AddOnDetailView.as_view(),
        name="backoffice-catalog-addon-detail",
    ),
    # Products
    path(
        "products/",
        ProductListCreateView.as_view(),
        name="backoffice-catalog-products",
    ),
    path(
        "products/<int:pk>/",
        ProductDetailView.as_view(),
        name="backoffice-catalog-product-detail",
    ),
    path(
        "products/<int:pk>/image/",
        ProductImageUploadView.as_view(),
        name="backoffice-catalog-product-image",
    ),
    path(
        "products/<int:pk>/addons/",
        ProductAddonsView.as_view(),
        name="backoffice-catalog-product-addons",
    ),
]