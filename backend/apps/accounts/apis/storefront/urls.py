from __future__ import annotations

from django.urls import path

from .views import (
    AddressDetailView,
    AddressListCreateView,
    MeView,
    OTPRequestView,
    OTPVerifyView,
    SetDefaultAddressView,
    TokenLogoutView,
    TokenRefreshView,
)

urlpatterns = [
    # OTP
    path("otp/request/", OTPRequestView.as_view(), name="storefront-auth-otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="storefront-auth-otp-verify"),

    # JWT
    path("token/refresh/", TokenRefreshView.as_view(), name="storefront-auth-token-refresh"),
    path("token/logout/", TokenLogoutView.as_view(), name="storefront-auth-token-logout"),
    path("me/", MeView.as_view(), name="storefront-auth-me"),

    # Addresses
    path("addresses/", AddressListCreateView.as_view(), name="storefront-addresses"),
    path(
        "addresses/<int:pk>/",
        AddressDetailView.as_view(),
        name="storefront-address-detail",
    ),
    path(
        "addresses/<int:pk>/set-default/",
        SetDefaultAddressView.as_view(),
        name="storefront-address-set-default",
    ),
]