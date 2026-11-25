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

    # CRM (mounted at /api/v1/backoffice/ — see config/api_urls_backoffice.py)
    path(
        "crm/customers/",
        CustomerListView.as_view(),
        name="backoffice-customers",
    ),
    path(
        "crm/customers/<int:pk>/",
        CustomerDetailView.as_view(),
        name="backoffice-customer-detail",
    ),
    path(
        "crm/customers/<int:pk>/notes/",
        CustomerNoteListCreateView.as_view(),
        name="backoffice-customer-notes",
    ),
    path(
        "crm/customers/<int:pk>/notes/<int:note_id>/",
        CustomerNoteDetailView.as_view(),
        name="backoffice-customer-note-detail",
    ),
]