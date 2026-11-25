from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import CustomerAddress, CustomerNote
from apps.catalog.models import Product, ProductAddOn
from apps.orders import services
from apps.orders.exceptions import OrderNotFoundError
from apps.orders.models import Order
from common.exceptions import (
    OrderStateError,
    RestaurantClosedError,
    ValidationError,
)


def _create(customer, product, delivery="PICKUP", address_id=None, qty=1, addons=None):
    return services.create_order(
        customer=customer,
        delivery_type=delivery,
        address_id=address_id,
        items=[
            {"product_id": product.pk, "quantity": qty, "addons": addons or []}
        ],
    )


class TestOrderCreation:
    def test_basic(self, db, customer, product, restaurant_settings):
        order = _create(customer, product, qty=2)
        assert order.status == Order.Status.PENDING_PAYMENT
        assert order.payment_status == Order.PaymentStatus.UNPAID
        assert order.subtotal == product.price * 2
        assert order.delivery_fee == 0
        assert order.total_amount == order.subtotal

    def test_prep_time_with_buffer(self, db, customer, product, restaurant_settings):
        product.prep_time_minutes = 15
        product.save()
        order = _create(customer, product)
        assert order.prep_time_minutes == 20

    def test_out_of_stock_rejected(self, db, customer, product, restaurant_settings):
        product.status = Product.Status.OUT_OF_STOCK
        product.save()
        with pytest.raises(ValidationError):
            _create(customer, product)

    def test_addon_quantity_limit(self, db, customer, product, addon, restaurant_settings):
        ProductAddOn.objects.create(
            product=product, addon=addon, min_quantity=0, max_quantity=2
        )
        with pytest.raises(ValidationError):
            _create(
                customer,
                product,
                addons=[{"addon_id": addon.pk, "quantity": 5}],
            )

    def test_price_snapshot(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        product.price = 999_999
        product.save()
        item = order.items.first()
        assert item.unit_price_snapshot == 150_000
        assert item.product_name_snapshot == "Margherita"

    def test_restaurant_closed(self, db, customer, product, restaurant_settings):
        restaurant_settings.is_temporarily_closed = True
        restaurant_settings.save()
        with pytest.raises(RestaurantClosedError):
            _create(customer, product)

    def test_delivery_requires_address(self, db, customer, product, restaurant_settings):
        with pytest.raises(ValidationError):
            _create(customer, product, delivery="DELIVERY", address_id=None)

    def test_delivery_fee_in_zone(self, db, customer, product, restaurant_settings):
        addr = CustomerAddress.objects.create(
            customer=customer, address_text="x", is_out_of_zone=False
        )
        order = _create(customer, product, delivery="DELIVERY", address_id=addr.pk)
        assert order.delivery_fee == restaurant_settings.in_zone_delivery_fee

    def test_delivery_fee_out_zone(self, db, customer, product, restaurant_settings):
        addr = CustomerAddress.objects.create(
            customer=customer, address_text="x", is_out_of_zone=True
        )
        order = _create(customer, product, delivery="DELIVERY", address_id=addr.pk)
        assert order.delivery_fee == restaurant_settings.out_zone_delivery_fee

    def test_delivery_sets_selected_address_default(
        self, db, customer, product, restaurant_settings
    ):
        first = CustomerAddress.objects.create(
            customer=customer, address_text="A1", is_default=True
        )
        second = CustomerAddress.objects.create(
            customer=customer, address_text="A2"
        )

        _create(customer, product, delivery="DELIVERY", address_id=second.pk)

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.is_default is False
        assert second.is_default is True

    def test_packaging_fee_added_to_total(
        self, db, customer, product, restaurant_settings
    ):
        restaurant_settings.packaging_fee = 15_000
        restaurant_settings.save(update_fields=["packaging_fee"])

        order = _create(customer, product, qty=2)

        assert order.packaging_fee == 15_000
        assert order.total_amount == (
            order.subtotal + order.delivery_fee + order.packaging_fee
        )

    def test_minimum_delivery_amount_enforced(
        self, db, customer, product, restaurant_settings
    ):
        restaurant_settings.min_delivery_order_amount = 200_000
        restaurant_settings.save(update_fields=["min_delivery_order_amount"])
        addr = CustomerAddress.objects.create(customer=customer, address_text="x")

        with pytest.raises(ValidationError) as exc_info:
            _create(customer, product, delivery="DELIVERY", address_id=addr.pk)

        assert exc_info.value.code == "MIN_DELIVERY_ORDER_AMOUNT"
        assert Order.objects.count() == 0

    def test_minimum_delivery_amount_allows_equal_subtotal(
        self, db, customer, product, restaurant_settings
    ):
        restaurant_settings.min_delivery_order_amount = product.price
        restaurant_settings.save(update_fields=["min_delivery_order_amount"])
        addr = CustomerAddress.objects.create(customer=customer, address_text="x")

        order = _create(customer, product, delivery="DELIVERY", address_id=addr.pk)

        assert order.subtotal == product.price


class TestStateTransitions:
    def test_paid_transitions(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        paid = services.mark_order_paid(order_id=order.pk)
        assert paid.status == Order.Status.PROCESSING
        assert paid.payment_status == Order.PaymentStatus.PAID
        assert paid.daily_number == 1
        assert paid.expected_ready_at is not None

    def test_ready(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        order = services.mark_order_ready(order_id=order.pk)
        assert order.status == Order.Status.READY

    def test_completed(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        services.mark_order_ready(order_id=order.pk)
        order = services.mark_order_completed(order_id=order.pk)
        assert order.status == Order.Status.COMPLETED

    def test_cancel_paid_to_awaiting_refund(
        self, db, customer, product, staff_user, restaurant_settings
    ):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        order = services.cancel_order_by_manager(
            order_id=order.pk, manager=staff_user, reason="customer request"
        )
        assert order.status == Order.Status.CANCELED
        assert order.payment_status == Order.PaymentStatus.AWAITING_REFUND

    def test_refund_recording(
        self, db, customer, product, staff_user, restaurant_settings
    ):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        services.cancel_order_by_manager(order_id=order.pk, manager=staff_user)
        order = services.record_refund(
            order_id=order.pk,
            manager=staff_user,
            card_number="6037xxxx",
            tracking_code="123456",
        )
        assert order.payment_status == Order.PaymentStatus.REFUNDED
        assert order.refund_tracking_code == "123456"

    def test_cannot_mark_ready_when_pending(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        with pytest.raises(OrderStateError):
            services.mark_order_ready(order_id=order.pk)

    def test_update_prep_time(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        updated = services.update_prep_time(order_id=order.pk, new_prep_time_minutes=30)
        assert updated.prep_time_minutes == 30

    def test_mark_printed_idempotent(self, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        first = services.mark_order_printed(order_id=order.pk)
        second = services.mark_order_printed(order_id=order.pk)
        assert first.is_printed is True
        assert second.printed_at == first.printed_at


class TestEndpoints:
    def test_create_via_api(self, authed_client, db, product, restaurant_settings):
        response = authed_client.post(
            "/api/v1/storefront/orders/",
            {
                "delivery_type": "PICKUP",
                "items": [{"product_id": product.pk, "quantity": 1, "addons": []}],
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["status"] == "PENDING_PAYMENT"

    def test_live_orders(self, staff_client, db, customer, product, restaurant_settings):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        response = staff_client.get("/api/v1/backoffice/orders/live/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["status"] == "PROCESSING"


class TestCancellationRequests:
    def test_paid_order_can_request_cancellation(
        self, db, customer, product, restaurant_settings
    ):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)

        updated = services.request_cancellation(
            customer=customer, order_id=order.pk, reason="changed my mind"
        )

        assert updated.cancellation_requested is True
        assert updated.cancellation_request_reason == "changed my mind"
        assert updated.cancellation_requested_at is not None
        assert updated.status == Order.Status.PROCESSING
        assert updated.payment_status == Order.PaymentStatus.PAID

    def test_unpaid_order_cannot_request(
        self, db, customer, product, restaurant_settings
    ):
        order = _create(customer, product)

        with pytest.raises(OrderStateError):
            services.request_cancellation(customer=customer, order_id=order.pk)

    def test_duplicate_request_rejected(
        self, db, customer, product, restaurant_settings
    ):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        services.request_cancellation(customer=customer, order_id=order.pk)

        with pytest.raises(OrderStateError):
            services.request_cancellation(customer=customer, order_id=order.pk)

    def test_customer_cannot_request_other_order(
        self, db, customer, product, restaurant_settings
    ):
        from apps.accounts.models import Customer

        other = Customer.objects.create_user(phone="09129999999")
        order = _create(other, product)
        services.mark_order_paid(order_id=order.pk)

        with pytest.raises(OrderNotFoundError):
            services.request_cancellation(customer=customer, order_id=order.pk)

    def test_endpoint(
        self, authed_client, db, customer, product, restaurant_settings
    ):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)

        response = authed_client.post(
            f"/api/v1/storefront/orders/{order.pk}/request-cancellation/",
            {"reason": "too late"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["cancellation_requested"] is True

    def test_backoffice_live_and_detail_expose_request(
        self, staff_client, db, customer, product, restaurant_settings
    ):
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)
        services.request_cancellation(
            customer=customer, order_id=order.pk, reason="too late"
        )

        live = staff_client.get("/api/v1/backoffice/orders/live/")
        detail = staff_client.get(f"/api/v1/backoffice/orders/{order.pk}/")

        assert live.json()[0]["cancellation_requested"] is True
        assert live.json()[0]["cancellation_request_reason"] == "too late"
        assert detail.json()["cancellation_requested"] is True
        assert detail.json()["cancellation_requested_at"] is not None


class TestCustomerNotesOnPos:
    def test_live_and_detail_include_customer_notes(
        self, staff_client, db, customer, staff_user, product, restaurant_settings
    ):
        CustomerNote.objects.create(
            customer=customer, author=staff_user, text="No onions"
        )
        order = _create(customer, product)
        services.mark_order_paid(order_id=order.pk)

        live = staff_client.get("/api/v1/backoffice/orders/live/")
        detail = staff_client.get(f"/api/v1/backoffice/orders/{order.pk}/")

        assert live.status_code == 200
        assert live.json()[0]["customer_notes"][0]["text"] == "No onions"
        assert (
            live.json()[0]["customer_notes"][0]["author_phone"]
            == staff_user.phone
        )
        assert detail.status_code == 200
        assert detail.json()["customer_notes"][0]["text"] == "No onions"


class TestAutoCancel:
    def test_expired_orders_canceled(
        self, db, customer, product, restaurant_settings
    ):
        order = _create(customer, product)
        order.expires_at = timezone.now() - timedelta(minutes=1)
        order.save()
        assert services.cancel_expired_unpaid_orders() == 1
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELED