from __future__ import annotations

from django.urls import path

from .views import (
    CustomerDetailView,
    CustomerListView,
    CustomerNoteDetailView,
    CustomerNoteListCreateView,
    StaffLoginView,
    StaffLogoutView,
    StaffMeView,
    backoffice_csrf_view,
)

urlpatterns = [
    # Auth
    path("auth/csrf/", backoffice_csrf_view, name="backoffice-auth-csrf"),
    path("auth/login/", StaffLoginView.as_view(), name="backoffice-auth-login"),
    path("auth/logout/", StaffLogoutView.as_view(), name="backoffice-auth-logout"),
    path("auth/me/", StaffMeView.as_view(), name="backoffice-auth-me"),

    # CRM
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