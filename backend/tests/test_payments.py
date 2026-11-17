from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.orders import services as order_services
from apps.orders.models import Order
from apps.payments import services as payment_services
from apps.payments.exceptions import PaymentNotVerifiableError
from apps.payments.models import Payment
from common.exceptions import ValidationError


@pytest.fixture
def pending_order(db, customer, product, restaurant_settings):
    return order_services.create_order(
        customer=customer,
        delivery_type=Order.DeliveryType.PICKUP,
        address_id=None,
        items=[{"product_id": product.pk, "quantity": 1, "addons": []}],
    )


@pytest.fixture
def pending_payment(db, pending_order):
    return Payment.objects.create(
        order=pending_order,
        amount=pending_order.total_amount,
        status=Payment.Status.PENDING,
        authority="A00000000000000000000000000000001",
    )


class TestVerify:
    def test_success(self, db, pending_payment):
        with patch(
            "apps.payments.services.ZarinpalClient.verify_payment",
            return_value={"code": 100, "ref_id": "98765"},
        ):
            payment = payment_services.verify_payment(
                authority=pending_payment.authority, status="OK"
            )
        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.ref_id == "98765"
        order = Order.objects.get(pk=pending_payment.order_id)
        assert order.status == Order.Status.PROCESSING
        assert order.payment_status == Order.PaymentStatus.PAID

    def test_idempotent_double_callback(self, db, pending_payment):
        with patch(
            "apps.payments.services.ZarinpalClient.verify_payment",
            return_value={"code": 100, "ref_id": "98765"},
        ):
            payment_services.verify_payment(
                authority=pending_payment.authority, status="OK"
            )
            payment = payment_services.verify_payment(
                authority=pending_payment.authority, status="OK"
            )
        assert payment.status == Payment.Status.SUCCEEDED

    def test_zarinpal_101_treated_as_success(self, db, pending_payment):
        with patch(
            "apps.payments.services.ZarinpalClient.verify_payment",
            return_value={"code": 101, "ref_id": "98765"},
        ):
            payment = payment_services.verify_payment(
                authority=pending_payment.authority, status="OK"
            )
        assert payment.status == Payment.Status.SUCCEEDED

    def test_callback_status_nok(self, db, pending_payment):
        payment = payment_services.verify_payment(
            authority=pending_payment.authority, status="NOK"
        )
        assert payment.status == Payment.Status.FAILED

    def test_failed_cannot_be_verified(self, db, pending_payment):
        payment_services.verify_payment(
            authority=pending_payment.authority, status="NOK"
        )
        with pytest.raises(PaymentNotVerifiableError):
            payment_services.verify_payment(
                authority=pending_payment.authority, status="OK"
            )


class TestStart:
    def test_start_success(self, db, pending_order):
        with patch(
            "apps.payments.services.ZarinpalClient.request_payment",
            return_value={"authority": "S00000000000000000000000000000001"},
        ):
            result = payment_services.start_payment_for_order(order=pending_order)
        assert "payment_url" in result
        assert Payment.objects.filter(order=pending_order).count() == 1

    def test_revalidates_availability(self, db, pending_order, product):
        product.status = "OUT_OF_STOCK"
        product.save()
        with pytest.raises(ValidationError):
            payment_services.start_payment_for_order(order=pending_order)