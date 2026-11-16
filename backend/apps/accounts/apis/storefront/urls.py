from __future__ import annotations

from django.urls import path

from .views import (
    AddressDetailView,
    AddressListCreateView,
    LogoutView,
    MeView,
    OTPRequestView,
    OTPVerifyView,
    csrf_token_view,
)

urlpatterns = [
    path("csrf/", csrf_token_view, name="storefront-auth-csrf"),
    path("otp/request/", OTPRequestView.as_view(), name="storefront-auth-otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="storefront-auth-otp-verify"),
    path("logout/", LogoutView.as_view(), name="storefront-auth-logout"),
    path("me/", MeView.as_view(), name="storefront-auth-me"),
    path("addresses/", AddressListCreateView.as_view(), name="storefront-addresses"),
    path(
        "addresses/<int:pk>/",
        AddressDetailView.as_view(),
        name="storefront-address-detail",
    ),
]