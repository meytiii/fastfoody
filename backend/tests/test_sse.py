from __future__ import annotations

import json
from unittest.mock import patch

from rest_framework.response import Response

from apps.orders import services
from apps.orders import sse
from apps.orders.models import Order
from apps.payments import services as payment_services
from apps.payments.models import Payment
from apps.orders.sse import (
    POS_CHANNEL,
    build_order_event,
    event_stream,
    order_channel,
    publish_order_event,
)


class FakePubSub:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.subscribed: tuple[str, ...] = ()
        self.closed = False
        self.unsubscribed: tuple[str, ...] = ()

    def subscribe(self, *channels):
        self.subscribed = tuple(channels)

    def get_message(self, **_kwargs):
        return self.messages.pop(0) if self.messages else None

    def unsubscribe(self, *channels):
        self.unsubscribed = tuple(channels)

    def close(self):
        self.closed = True


class FakeRedis:
    def __init__(self, pubsub=None):
        self.published: list[tuple[str, str]] = []
        self._pubsub = pubsub or FakePubSub()

    def publish(self, channel, payload):
        self.published.append((channel, payload))

    def pubsub(self):
        return self._pubsub


def _order(customer, product):
    return services.create_order(
        customer=customer,
        delivery_type=Order.DeliveryType.PICKUP,
        address_id=None,
        items=[{"product_id": product.pk, "quantity": 1, "addons": []}],
    )


class TestOrderEventPayload:
    def test_payload_fields(self, db, customer, product, restaurant_settings):
        order = _order(customer, product)

        payload = build_order_event(order, "order.status_changed")

        assert payload["event_type"] == "order.status_changed"
        assert payload["order_id"] == order.pk
        assert payload["status"] == Order.Status.PENDING_PAYMENT
        assert payload["payment_status"] == Order.PaymentStatus.UNPAID
        assert payload["cancellation_requested"] is False
        assert payload["timestamp"]

    def test_publishes_to_pos_and_order_channels(
        self, db, customer, product, restaurant_settings, monkeypatch
    ):
        fake = FakeRedis()
        monkeypatch.setattr(sse, "get_redis", lambda: fake)
        order = _order(customer, product)

        publish_order_event(order, "order.created_or_paid")

        channels = [channel for channel, _ in fake.published]
        assert channels == [POS_CHANNEL, order_channel(order.pk)]
        body = json.loads(fake.published[0][1])
        assert body["order_id"] == order.pk
        assert body["event_type"] == "order.created_or_paid"

    def test_redis_failure_is_swallowed(
        self, db, customer, product, restaurant_settings, monkeypatch
    ):
        def broken_redis():
            raise OSError("redis down")

        monkeypatch.setattr(sse, "get_redis", broken_redis)
        order = _order(customer, product)

        # Must not raise: order transitions cannot depend on Redis.
        publish_order_event(order, "order.status_changed")


class TestPublishersOnTransitions:
    def test_verified_payment_publishes_created_or_paid(
        self, db, customer, product, restaurant_settings, monkeypatch,
        django_capture_on_commit_callbacks,
    ):
        order = _order(customer, product)
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            status=Payment.Status.PENDING,
            authority="A00000000000000000000000000000001",
        )
        events: list[tuple[int, str]] = []
        monkeypatch.setattr(
            payment_services,
            "publish_order_event",
            lambda o, event: events.append((o.pk, event)),
        )

        with patch(
            "apps.payments.services.ZarinpalClient.verify_payment",
            return_value={"code": 100, "ref_id": "98765"},
        ):
            with django_capture_on_commit_callbacks(execute=True):
                payment_services.verify_payment(
                    authority=payment.authority, status="OK"
                )

        assert events == [(order.pk, "order.created_or_paid")]

    def test_ready_completed_and_prep_time_publish(
        self, db, customer, product, restaurant_settings, monkeypatch,
        django_capture_on_commit_callbacks,
    ):
        order = _order(customer, product)
        services.mark_order_paid(order_id=order.pk)
        events: list[str] = []
        monkeypatch.setattr(
            services,
            "publish_order_event",
            lambda o, event: events.append(event),
        )

        with django_capture_on_commit_callbacks(execute=True):
            services.mark_order_ready(order_id=order.pk)
        with django_capture_on_commit_callbacks(execute=True):
            services.update_prep_time(
                order_id=order.pk, new_prep_time_minutes=20
            )
        with django_capture_on_commit_callbacks(execute=True):
            services.mark_order_completed(order_id=order.pk)

        assert events == [
            "order.status_changed",
            "order.prep_time_updated",
            "order.status_changed",
        ]

    def test_cancellation_request_publishes(
        self, db, customer, product, restaurant_settings, monkeypatch,
        django_capture_on_commit_callbacks,
    ):
        order = _order(customer, product)
        services.mark_order_paid(order_id=order.pk)
        events: list[str] = []
        monkeypatch.setattr(
            services,
            "publish_order_event",
            lambda o, event: events.append(event),
        )

        with django_capture_on_commit_callbacks(execute=True):
            services.request_cancellation(
                customer=customer, order_id=order.pk, reason="changed"
            )

        assert events == ["order.cancellation_requested"]

    def test_manager_cancel_publishes_status_changed(
        self, db, customer, product, staff_user, restaurant_settings, monkeypatch,
        django_capture_on_commit_callbacks,
    ):
        order = _order(customer, product)
        events: list[str] = []
        monkeypatch.setattr(
            services,
            "publish_order_event",
            lambda o, event: events.append(event),
        )

        with django_capture_on_commit_callbacks(execute=True):
            services.cancel_order_by_manager(
                order_id=order.pk, manager=staff_user
            )

        assert events == ["order.status_changed"]


class TestEventStream:
    def test_formats_frames_and_closes_pubsub(self, monkeypatch):
        payload = json.dumps(
            {
                "event_type": "order.status_changed",
                "order_id": 5,
            }
        )
        pubsub = FakePubSub(
            messages=[{"type": "message", "data": payload}]
        )
        fake = FakeRedis(pubsub=pubsub)
        monkeypatch.setattr(sse, "get_redis", lambda: fake)

        stream = event_stream([POS_CHANNEL])
        frame = next(stream)

        assert frame == f"event: order.status_changed\ndata: {payload}\n\n"
        assert pubsub.subscribed == (POS_CHANNEL,)

        stream.close()

        assert pubsub.closed is True
        assert pubsub.unsubscribed == (POS_CHANNEL,)


class TestStreamEndpoints:
    def test_storefront_owner_stream_uses_order_channel(
        self, authed_client, db, customer, product, restaurant_settings, monkeypatch
    ):
        order = _order(customer, product)
        seen: list[list[str]] = []

        def fake_response(channels):
            seen.append(channels)
            return Response({"channels": channels})

        monkeypatch.setattr(
            "apps.orders.apis.storefront.views.make_sse_response",
            fake_response,
        )

        response = authed_client.get(
            f"/api/v1/storefront/orders/{order.pk}/stream/"
        )

        assert response.status_code == 200
        assert seen == [[order_channel(order.pk)]]

    def test_storefront_other_order_returns_404(
        self, authed_client, db, customer, product, restaurant_settings
    ):
        from apps.accounts.models import Customer

        other = Customer.objects.create_user(phone="09125555555")
        order = _order(other, product)

        response = authed_client.get(
            f"/api/v1/storefront/orders/{order.pk}/stream/"
        )

        assert response.status_code == 404

    def test_backoffice_live_stream_uses_pos_channel(
        self, staff_client, db, monkeypatch
    ):
        seen: list[list[str]] = []

        def fake_response(channels):
            seen.append(channels)
            return Response({"channels": channels})

        monkeypatch.setattr(
            "apps.orders.apis.backoffice.views.make_sse_response",
            fake_response,
        )

        response = staff_client.get(
            "/api/v1/backoffice/orders/live/stream/"
        )

        assert response.status_code == 200
        assert seen == [[POS_CHANNEL]]

    def test_backoffice_stream_customer_denied(self, authed_client, db):
        response = authed_client.get(
            "/api/v1/backoffice/orders/live/stream/"
        )
        assert response.status_code == 403

    def test_storefront_stream_requires_auth(self, api_client, db, customer, product, restaurant_settings):
        order = _order(customer, product)

        response = api_client.get(
            f"/api/v1/storefront/orders/{order.pk}/stream/"
        )

        assert response.status_code in (401, 403)
