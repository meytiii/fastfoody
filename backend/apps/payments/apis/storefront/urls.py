from __future__ import annotations

from django.urls import path

from .views import (
    PaymentStatusView,
    RetryPaymentView,
    StartPaymentView,
    ZarinpalCallbackView,
)

urlpatterns = [
    path("request/", StartPaymentView.as_view(), name="storefront-payments-request"),
    path("retry/", RetryPaymentView.as_view(), name="storefront-payments-retry"),
    path("callback/", ZarinpalCallbackView.as_view(), name="storefront-payments-callback"),
    path(
        "status/<str:authority>/",
        PaymentStatusView.as_view(),
        name="storefront-payments-status",
    ),
]