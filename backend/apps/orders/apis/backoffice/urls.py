from __future__ import annotations

from django.urls import path

from .views import (
    CancelOrderView,
    LiveOrdersStreamView,
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
    path("", OrderListView.as_view(), name="backoffice-orders"),
    path(
        "live/stream/",
        LiveOrdersStreamView.as_view(),
        name="backoffice-orders-live-stream",
    ),
    path("live/", LiveOrdersView.as_view(), name="backoffice-orders-live"),
    path(
        "<int:pk>/",
        OrderDetailView.as_view(),
        name="backoffice-order-detail",
    ),
    path(
        "<int:pk>/mark-ready/",
        MarkReadyView.as_view(),
        name="backoffice-order-mark-ready",
    ),
    path(
        "<int:pk>/mark-completed/",
        MarkCompletedView.as_view(),
        name="backoffice-order-mark-completed",
    ),
    path(
        "<int:pk>/mark-printed/",
        MarkPrintedView.as_view(),
        name="backoffice-order-mark-printed",
    ),
    path(
        "<int:pk>/cancel/",
        CancelOrderView.as_view(),
        name="backoffice-order-cancel",
    ),
    path(
        "<int:pk>/prep-time/",
        UpdatePrepTimeView.as_view(),
        name="backoffice-order-prep-time",
    ),
    path(
        "<int:pk>/refund/",
        RecordRefundView.as_view(),
        name="backoffice-order-refund",
    ),
]