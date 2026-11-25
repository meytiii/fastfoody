from __future__ import annotations

import pytest

from apps.accounts import services
from apps.accounts.exceptions import (
    AccountBlockedError,
    OTPExpiredError,
    OTPInvalidError,
)
from apps.accounts.models import Customer, CustomerAddress
from common.exceptions import ValidationError


class TestPhoneNormalization:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("+989121234567", "09121234567"),
            ("989121234567", "09121234567"),
            ("9121234567", "09121234567"),
            ("09121234567", "09121234567"),
        ],
    )
    def test_normalizes(self, raw, expected):
        assert services.normalize_phone(raw) == expected

    @pytest.mark.parametrize("bad", ["", "123", "0912", "0012345678"])
    def test_rejects_invalid(self, bad):
        with pytest.raises(ValidationError):
            services.normalize_phone(bad)


class TestOTPFlow:
    def test_request_stores_in_redis(self, db):
        ttl = services.request_otp(phone="09120000000")
        assert ttl == 120

    def test_verify_creates_customer(self, db):
        from apps.accounts import otp as otp_service

        otp_service.store_otp(phone="09120000000", code="123456")
        customer = services.verify_otp(phone="09120000000", code="123456")
        assert customer.phone == "09120000000"
        assert Customer.objects.filter(phone="09120000000").exists()

    def test_verify_wrong_code(self, db):
        from apps.accounts import otp as otp_service

        otp_service.store_otp(phone="09120000000", code="123456")
        with pytest.raises(OTPInvalidError):
            services.verify_otp(phone="09120000000", code="000000")

    def test_verify_expired(self, db):
        with pytest.raises(OTPExpiredError):
            services.verify_otp(phone="09120000000", code="123456")

    def test_verify_consumes_code(self, db):
        from apps.accounts import otp as otp_service

        otp_service.store_otp(phone="09120000000", code="123456")
        services.verify_otp(phone="09120000000", code="123456")
        with pytest.raises(OTPExpiredError):
            services.verify_otp(phone="09120000000", code="123456")

    def test_verify_blocked_customer(self, db, customer):
        from apps.accounts import otp as otp_service

        customer.is_blocked = True
        customer.save()
        otp_service.store_otp(phone=customer.phone, code="123456")
        with pytest.raises(AccountBlockedError):
            services.verify_otp(phone=customer.phone, code="123456")


class TestOTPEndpoints:
    def test_request_endpoint(self, api_client, db):
        response = api_client.post(
            "/api/v1/storefront/auth/otp/request/",
            {"phone": "09120000000"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["expires_in"] == 120

    def test_verify_returns_jwt_without_session(self, api_client, db):
        from apps.accounts import otp as otp_service

        otp_service.store_otp(phone="09120000000", code="123456")
        response = api_client.post(
            "/api/v1/storefront/auth/otp/verify/",
            {"phone": "09120000000", "code": "123456"},
            format="json",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["phone"] == "09120000000"
        assert body["access"] and body["refresh"]
        assert "_auth_user_id" not in api_client.session


class TestAddresses:
    def test_create_marks_new_address_default(self, authed_client, customer):
        response = authed_client.post(
            "/api/v1/storefront/auth/addresses/",
            {"address_text": "Tehran", "is_out_of_zone": False},
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["is_default"] is True
        assert CustomerAddress.objects.filter(customer=customer).count() == 1

    def test_new_address_becomes_default(self, authed_client, customer):
        a1 = CustomerAddress.objects.create(
            customer=customer, address_text="A1", is_default=True
        )
        response = authed_client.post(
            "/api/v1/storefront/auth/addresses/",
            {"address_text": "A2"},
            format="json",
        )
        a1.refresh_from_db()
        assert a1.is_default is False
        assert response.json()["is_default"] is True

    def test_fifth_address_rejected(self, customer):
        for index in range(4):
            services.create_address(
                customer=customer, data={"address_text": f"A{index}"}
            )

        with pytest.raises(ValidationError) as exc_info:
            services.create_address(customer=customer, data={"address_text": "A5"})

        assert exc_info.value.code == "ADDRESS_LIMIT_REACHED"
        assert CustomerAddress.objects.filter(customer=customer).count() == 4

    def test_replace_address_at_limit(self, customer):
        addresses = [
            CustomerAddress.objects.create(
                customer=customer,
                address_text=f"A{index}",
                is_default=index == 0,
            )
            for index in range(4)
        ]

        replaced = services.create_address(
            customer=customer,
            data={"address_text": "Replaced"},
            replace_address_id=addresses[0].pk,
        )

        assert CustomerAddress.objects.filter(customer=customer).count() == 4
        assert replaced.address_text == "Replaced"
        assert replaced.is_default is True
        addresses[1].refresh_from_db()
        assert addresses[1].is_default is False

    def test_set_default_endpoint(self, authed_client, customer):
        first = CustomerAddress.objects.create(
            customer=customer, address_text="A1", is_default=True
        )
        second = CustomerAddress.objects.create(
            customer=customer, address_text="A2"
        )

        response = authed_client.post(
            f"/api/v1/storefront/auth/addresses/{second.pk}/set-default/"
        )

        assert response.status_code == 200
        assert response.json()["is_default"] is True
        first.refresh_from_db()
        assert first.is_default is False

    def test_soft_deleted_address_frees_a_slot(self, customer):
        for index in range(4):
            services.create_address(
                customer=customer, data={"address_text": f"A{index}"}
            )
        victim = CustomerAddress.objects.filter(customer=customer).first()
        services.delete_address(customer=customer, address_id=victim.pk)

        created = services.create_address(
            customer=customer, data={"address_text": "New"}
        )
        assert created.pk is not None


class TestStaffLogin:
    def test_valid(self, api_client, staff_user):
        response = api_client.post(
            "/api/v1/backoffice/auth/login/",
            {"phone": staff_user.phone, "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["user"]["is_staff"] is True

    def test_wrong_password(self, api_client, staff_user):
        response = api_client.post(
            "/api/v1/backoffice/auth/login/",
            {"phone": staff_user.phone, "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_non_staff_rejected(self, api_client, customer):
        customer.set_password("x")
        customer.save()
        response = api_client.post(
            "/api/v1/backoffice/auth/login/",
            {"phone": customer.phone, "password": "x"},
            format="json",
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "NOT_STAFF"

    def test_blocked_rejected(self, api_client, staff_user):
        staff_user.is_blocked = True
        staff_user.save()
        response = api_client.post(
            "/api/v1/backoffice/auth/login/",
            {"phone": staff_user.phone, "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "ACCOUNT_BLOCKED"