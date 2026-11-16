from __future__ import annotations

from django.urls import path

from .views import OrderDetailView, OrderListCreateView

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="storefront-orders"),
    path("<int:pk>/", OrderDetailView.as_view(), name="storefront-order-detail"),
]