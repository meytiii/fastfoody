from __future__ import annotations

from django.urls import path

from .views import (
    CustomerDetailView,
    CustomerListView,
    CustomerNoteDetailView,
    CustomerNoteListCreateView,
)

urlpatterns = [
    path("customers/", CustomerListView.as_view(), name="backoffice-customers"),
    path(
        "customers/<int:pk>/",
        CustomerDetailView.as_view(),
        name="backoffice-customer-detail",
    ),
    path(
        "customers/<int:pk>/notes/",
        CustomerNoteListCreateView.as_view(),
        name="backoffice-customer-notes",
    ),
    path(
        "customers/<int:pk>/notes/<int:note_id>/",
        CustomerNoteDetailView.as_view(),
        name="backoffice-customer-note-detail",
    ),
]