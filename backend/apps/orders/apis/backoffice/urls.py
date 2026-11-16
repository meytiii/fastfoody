from __future__ import annotations

from django.urls import path

from .views import (
    CancelOrderView,
    LiveOrdersView,
    MarkCompletedView,
    MarkPrintedView,
    MarkReadyView,
    OrderDetailView,
    OrderListView,
    RecordRefundView,
    UpdatePrepTimeView,
)

urlpatterns = [
    path("orders/", OrderListView.as_view(), name="backoffice-orders"),
    path("orders/live/", LiveOrdersView.as_view(), name="backoffice-orders-live"),
    path(
        "orders/<int:pk>/",
        OrderDetailView.as_view(),
        name="backoffice-order-detail",
    ),
    path(
        "orders/<int:pk>/mark-ready/",
        MarkReadyView.as_view(),
        name="backoffice-order-mark-ready",
    ),
    path(
        "orders/<int:pk>/mark-completed/",
        MarkCompletedView.as_view(),
        name="backoffice-order-mark-completed",
    ),
    path(
        "orders/<int:pk>/mark-printed/",
        MarkPrintedView.as_view(),
        name="backoffice-order-mark-printed",
    ),
    path(
        "orders/<int:pk>/cancel/",
        CancelOrderView.as_view(),
        name="backoffice-order-cancel",
    ),
    path(
        "orders/<int:pk>/prep-time/",
        UpdatePrepTimeView.as_view(),
        name="backoffice-order-prep-time",
    ),
    path(
        "orders/<int:pk>/refund/",
        RecordRefundView.as_view(),
        name="backoffice-order-refund",
    ),
]