from __future__ import annotations

from django.urls import path

from .views import OrderPaymentListView

urlpatterns = [
    path(
        "orders/<int:order_id>/payments/",
        OrderPaymentListView.as_view(),
        name="backoffice-order-payments",
    ),
]