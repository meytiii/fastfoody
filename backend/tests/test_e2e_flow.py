from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.accounts import otp as otp_service
from apps.orders.models import Order


class TestFullFlow:
    def test_happy_path(self, api_client, db, product, restaurant_settings):
        # 1) OTP request + verify
        with patch("apps.accounts.services.send_otp_sms"):
            api_client.post(
                "/api/v1/storefront/auth/otp/request/",
                {"phone": "09120000000"},
                format="json",
            )
        otp_service.store_otp(phone="09120000000", code="111111")
        response = api_client.post(
            "/api/v1/storefront/auth/otp/verify/",
            {"phone": "09120000000", "code": "111111"},
            format="json",
        )
        assert response.status_code == 200

        # 2) Create order
        response = api_client.post(
            "/api/v1/storefront/orders/",
            {
                "delivery_type": "PICKUP",
                "items": [{"product_id": product.pk, "quantity": 1, "addons": []}],
            },
            format="json",
        )
        assert response.status_code == 201
        order_id = response.json()["id"]

        # 3) Start payment
        with patch(
            "apps.payments.services.ZarinpalClient.request_payment",
            return_value={"authority": "AUTH-1"},
        ):
            response = api_client.post(
                "/api/v1/storefront/payments/request/",
                {"order_id": order_id},
                format="json",
            )
        assert response.status_code == 201

        # 4) Callback
        with patch(
            "apps.payments.services.ZarinpalClient.verify_payment",
            return_value={"code": 100, "ref_id": "REF-1"},
        ):
            response = api_client.get(
                "/api/v1/storefront/payments/callback/",
                {"Authority": "AUTH-1", "Status": "OK", "format": "json"},
            )
        assert response.status_code == 200

        # 5) Assert final state
        order = Order.objects.get(pk=order_id)
        assert order.status == Order.Status.PROCESSING
        assert order.payment_status == Order.PaymentStatus.PAID
        assert order.daily_number == 1