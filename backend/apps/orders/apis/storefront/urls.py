from __future__ import annotations

from django.urls import path

from .views import (
    OrderDetailView,
    OrderListCreateView,
    OrderReorderView,
    OrderRequestCancellationView,
    OrderTrackingStreamView,
    ValidatePromoView,
)

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="storefront-orders"),
    path(
        "validate-promo/",
        ValidatePromoView.as_view(),
        name="storefront-orders-validate-promo",
    ),
    path("<int:pk>/", OrderDetailView.as_view(), name="storefront-order-detail"),
    path(
        "<int:pk>/reorder/",
        OrderReorderView.as_view(),
        name="storefront-order-reorder",
    ),
    path(
        "<int:pk>/stream/",
        OrderTrackingStreamView.as_view(),
        name="storefront-order-stream",
    ),
    path(
        "<int:pk>/request-cancellation/",
        OrderRequestCancellationView.as_view(),
        name="storefront-order-request-cancellation",
    ),
]