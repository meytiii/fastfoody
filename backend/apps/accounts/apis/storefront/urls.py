from __future__ import annotations

from django.urls import path

from .views import (
    AddressDetailView,
    AddressListCreateView,
    LogoutView,
    MeView,
    OTPRequestView,
    OTPVerifyView,
    TokenLogoutView,
    TokenRefreshView,
    csrf_token_view,
)

urlpatterns = [
    path("csrf/", csrf_token_view, name="storefront-auth-csrf"),

    # OTP
    path("otp/request/", OTPRequestView.as_view(), name="storefront-auth-otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="storefront-auth-otp-verify"),

    # JWT
    path("token/refresh/", TokenRefreshView.as_view(), name="storefront-auth-token-refresh"),
    path("token/logout/", TokenLogoutView.as_view(), name="storefront-auth-token-logout"),

    # Session logout (kept for browser flow)
    path("logout/", LogoutView.as_view(), name="storefront-auth-logout"),
    path("me/", MeView.as_view(), name="storefront-auth-me"),

    # Addresses
    path("addresses/", AddressListCreateView.as_view(), name="storefront-addresses"),
    path(
        "addresses/<int:pk>/",
        AddressDetailView.as_view(),
        name="storefront-address-detail",
    ),
]