from __future__ import annotations

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts import otp as otp_service


def _get_tokens(api_client, phone="09120000000"):
    otp_service.store_otp(phone=phone, code="123456")
    response = api_client.post(
        "/api/v1/storefront/auth/otp/verify/",
        {"phone": phone, "code": "123456"},
        format="json",
    )
    assert response.status_code == 200
    return response.json()


class TestOTPVerify:
    def test_returns_tokens_and_user(self, api_client, db):
        body = _get_tokens(api_client)
        assert "access" in body
        assert "refresh" in body
        assert "user" in body
        assert body["user"]["phone"] == "09120000000"

    def test_no_session_is_created(self, api_client, db):
        body = _get_tokens(api_client)
        assert body["access"]
        # No browser session: /me without an Authorization header is rejected.
        response = api_client.get("/api/v1/storefront/auth/me/")
        assert response.status_code == 401

    def test_storefront_session_routes_removed(self, api_client, db):
        assert api_client.get("/api/v1/storefront/auth/csrf/").status_code == 404
        assert api_client.post("/api/v1/storefront/auth/logout/").status_code == 404


class TestJWTAccess:
    def test_access_token_authenticates(self, api_client, db):
        body = _get_tokens(api_client)
        # Reset session, keep only JWT
        api_client.logout()
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access']}")
        response = api_client.get("/api/v1/storefront/auth/me/")
        assert response.status_code == 200
        assert response.json()["phone"] == "09120000000"

    def test_malformed_header_rejected(self, api_client, db):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
        response = api_client.get("/api/v1/storefront/auth/me/")
        assert response.status_code == 401

    def test_missing_auth_rejected(self, api_client, db):
        response = api_client.get("/api/v1/storefront/auth/me/")
        assert response.status_code in (401, 403)

    def test_session_cookie_is_rejected(self, api_client, db, customer):
        api_client.force_login(customer)
        response = api_client.get("/api/v1/storefront/auth/me/")
        assert response.status_code == 401

    def test_blocked_customer_token_rejected(self, api_client, db):
        from apps.accounts.models import Customer

        body = _get_tokens(api_client)
        customer = Customer.objects.get(phone="09120000000")
        customer.is_blocked = True
        customer.save(update_fields=["is_blocked"])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access']}")
        response = api_client.get("/api/v1/storefront/auth/me/")
        assert response.status_code == 403


class TestRefresh:
    def test_refresh_returns_new_access(self, api_client, db):
        body = _get_tokens(api_client)
        response = api_client.post(
            "/api/v1/storefront/auth/token/refresh/",
            {"refresh": body["refresh"]},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        # Rotation is on: a new refresh is returned
        assert "refresh" in data
        assert data["refresh"] != body["refresh"]

    def test_rotation_blacklists_old_refresh(self, api_client, db):
        body = _get_tokens(api_client)
        old_refresh = body["refresh"]
        api_client.post(
            "/api/v1/storefront/auth/token/refresh/",
            {"refresh": old_refresh},
            format="json",
        )
        # Second use of the same refresh must fail
        response = api_client.post(
            "/api/v1/storefront/auth/token/refresh/",
            {"refresh": old_refresh},
            format="json",
        )
        assert response.status_code == 401

    def test_invalid_refresh_rejected(self, api_client, db):
        response = api_client.post(
            "/api/v1/storefront/auth/token/refresh/",
            {"refresh": "garbage"},
            format="json",
        )
        assert response.status_code == 401


class TestLogout:
    def test_blacklists_refresh(self, api_client, db):
        body = _get_tokens(api_client)
        response = api_client.post(
            "/api/v1/storefront/auth/token/logout/",
            {"refresh": body["refresh"]},
            format="json",
        )
        assert response.status_code == 204

        # Refresh is now dead
        response = api_client.post(
            "/api/v1/storefront/auth/token/refresh/",
            {"refresh": body["refresh"]},
            format="json",
        )
        assert response.status_code == 401

    def test_logout_is_public_and_does_not_need_a_session(self, api_client, db):
        body = _get_tokens(api_client)
        response = api_client.post(
            "/api/v1/storefront/auth/token/logout/",
            {"refresh": body["refresh"]},
            format="json",
        )
        assert response.status_code == 204


class TestBackofficeIsolation:
    def test_jwt_rejected_on_backoffice(self, api_client, db, staff_user):
        refresh = RefreshToken.for_user(staff_user)
        access = str(refresh.access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.get("/api/v1/backoffice/orders/")
        # BackofficeAPIView uses SessionAuthentication only → no user → 403
        assert response.status_code in (401, 403)

    def test_session_still_works_on_backoffice(self, staff_client, db):
        response = staff_client.get("/api/v1/backoffice/orders/")
        assert response.status_code == 200