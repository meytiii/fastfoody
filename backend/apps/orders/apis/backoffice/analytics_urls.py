from __future__ import annotations

from django.urls import path

from .views import SalesAnalyticsView

urlpatterns = [
    path("sales/", SalesAnalyticsView.as_view(), name="backoffice-analytics-sales"),
]
