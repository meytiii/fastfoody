from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Customer
from apps.catalog.models import ProductAddOn
from apps.orders import services
from apps.orders.models import Order, PromoCode, PromoCodeUsage
from common.exceptions import ValidationError


def _order(customer, product, *, qty=1, promo_code=None):
    return services.create_order(
        customer=customer,
        delivery_type=Order.DeliveryType.PICKUP,
        address_id=None,
        items=[{"product_id": product.pk, "quantity": qty, "addons": []}],
        promo_code=promo_code,
    )


def _promo(**overrides):
    data = {
        "code": "SAVE10",
        "discount_type": PromoCode.DiscountType.PERCENTAGE,
        "discount_value": 10,
    }
    data.update(overrides)
    return PromoCode.objects.create(**data)


class TestPromoCodeModel:
    def test_code_is_normalized(self, db):
        promo = PromoCode.objects.create(
            code="  summer20 ",
            discount_type=PromoCode.DiscountType.PERCENTAGE,
            discount_value=20,
        )
        promo.refresh_from_db()
        assert promo.code == "SUMMER20"


class TestPromoApplication:
    def test_percentage_discount_updates_total(
        self, db, customer, product, restaurant_settings
    ):
        _promo()
        order = _order(customer, product, qty=4, promo_code="save10")

        assert order.subtotal == 600_000
        assert order.discount_amount == 60_000
        assert order.promo_code_snapshot == "SAVE10"
        assert order.total_amount == 540_000
        assert PromoCodeUsage.objects.filter(order=order).count() == 1

    def test_percentage_respects_max_discount_cap(
        self, db, customer, product, restaurant_settings
    ):
        _promo(max_discount_amount=50_000)
        order = _order(customer, product, qty=4, promo_code="SAVE10")

        assert order.discount_amount == 50_000
        assert order.total_amount == order.subtotal - 50_000

    def test_fixed_discount_never_exceeds_subtotal(
        self, db, customer, product, restaurant_settings
    ):
        _promo(
            code="BIG",
            discount_type=PromoCode.DiscountType.FIXED,
            discount_value=999_999,
        )
        order = _order(customer, product, promo_code="BIG")

        assert order.discount_amount == product.price
        assert order.total_amount == 0

    def test_minimum_order_amount_rejected(
        self, db, customer, product, restaurant_settings
    ):
        _promo(min_order_amount=200_000)

        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_MIN_ORDER"
        assert Order.objects.count() == 0

    def test_inactive_code_rejected(self, db, customer, product, restaurant_settings):
        _promo(is_active=False)

        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_INACTIVE"

    def test_not_started_code_rejected(
        self, db, customer, product, restaurant_settings
    ):
        _promo(valid_from=timezone.now() + timedelta(hours=1))

        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_NOT_STARTED"

    def test_expired_code_rejected(self, db, customer, product, restaurant_settings):
        _promo(valid_until=timezone.now() - timedelta(minutes=1))

        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_EXPIRED"

    def test_unknown_code_rejected(self, db, customer, product, restaurant_settings):
        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="MISSING")

        assert exc_info.value.code == "PROMO_CODE_NOT_FOUND"

    def test_total_use_limit(self, db, customer, product, restaurant_settings):
        _promo(max_total_uses=1)
        _order(customer, product, promo_code="SAVE10")

        other = Customer.objects.create_user(phone="09128888888")
        with pytest.raises(ValidationError) as exc_info:
            _order(other, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_TOTAL_LIMIT"

    def test_per_customer_use_limit(self, db, customer, product, restaurant_settings):
        _promo(max_uses_per_customer=1)
        _order(customer, product, promo_code="SAVE10")

        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_CUSTOMER_LIMIT"

    def test_first_order_only(self, db, customer, product, restaurant_settings):
        prior = _order(customer, product)
        services.mark_order_paid(order_id=prior.pk)
        _promo(first_order_only=True, max_uses_per_customer=5)

        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")

        assert exc_info.value.code == "PROMO_CODE_FIRST_ORDER_ONLY"

    def test_auto_cancel_releases_usage(
        self, db, customer, product, restaurant_settings
    ):
        _promo()
        order = _order(customer, product, promo_code="SAVE10")
        order.expires_at = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=["expires_at"])

        assert services.cancel_expired_unpaid_orders() == 1

        assert PromoCodeUsage.objects.filter(order=order).count() == 0
        # The quota is free again: the same customer may reuse the code.
        reused = _order(customer, product, promo_code="SAVE10")
        assert reused.discount_amount > 0

    def test_manager_cancel_releases_unpaid_usage(
        self, db, customer, product, staff_user, restaurant_settings
    ):
        _promo()
        order = _order(customer, product, promo_code="SAVE10")

        services.cancel_order_by_manager(order_id=order.pk, manager=staff_user)

        assert PromoCodeUsage.objects.filter(order=order).count() == 0

    def test_paid_cancel_keeps_usage_and_quota(
        self, db, customer, product, staff_user, restaurant_settings
    ):
        _promo()
        order = _order(customer, product, promo_code="SAVE10")
        services.mark_order_paid(order_id=order.pk)

        services.cancel_order_by_manager(order_id=order.pk, manager=staff_user)

        assert PromoCodeUsage.objects.filter(order=order).count() == 1
        with pytest.raises(ValidationError) as exc_info:
            _order(customer, product, promo_code="SAVE10")
        assert exc_info.value.code == "PROMO_CODE_CUSTOMER_LIMIT"


class TestPromoOnOrderEndpoint:
    def test_order_endpoint_applies_promo(
        self, authed_client, db, customer, product, restaurant_settings
    ):
        _promo()

        response = authed_client.post(
            "/api/v1/storefront/orders/",
            {
                "delivery_type": "PICKUP",
                "promo_code": "save10",
                "items": [
                    {"product_id": product.pk, "quantity": 2, "addons": []}
                ],
            },
            format="json",
        )

        assert response.status_code == 201
        body = response.json()
        assert body["promo_code_snapshot"] == "SAVE10"
        assert body["discount_amount"] == 30_000
        assert body["total_amount"] == 270_000


class TestValidatePromoEndpoint:
    def test_returns_discount(self, authed_client, db, customer, restaurant_settings):
        _promo()

        response = authed_client.post(
            "/api/v1/storefront/orders/validate-promo/",
            {"code": "save10", "subtotal": 200_000},
            format="json",
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "SAVE10"
        assert body["discount_amount"] == 20_000
        assert body["discounted_subtotal"] == 180_000

    def test_ineligible_returns_error_envelope(
        self, authed_client, db, customer, restaurant_settings
    ):
        _promo(min_order_amount=500_000)

        response = authed_client.post(
            "/api/v1/storefront/orders/validate-promo/",
            {"code": "SAVE10", "subtotal": 100_000},
            format="json",
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "PROMO_CODE_MIN_ORDER"

    def test_requires_authentication(self, api_client, db, restaurant_settings):
        response = api_client.post(
            "/api/v1/storefront/orders/validate-promo/",
            {"code": "SAVE10", "subtotal": 100_000},
            format="json",
        )
        assert response.status_code in (401, 403)


class TestBackofficePromoCrud:
    def test_crud_and_usage_count(self, staff_client, db, customer, product, restaurant_settings):
        create = staff_client.post(
            "/api/v1/backoffice/promo-codes/",
            {
                "code": "back10",
                "discount_type": "PERCENTAGE",
                "discount_value": 10,
                "max_uses_per_customer": 2,
            },
            format="json",
        )
        assert create.status_code == 201
        assert create.json()["code"] == "BACK10"
        promo_id = create.json()["id"]

        _order(customer, product, promo_code="BACK10")

        listing = staff_client.get("/api/v1/backoffice/promo-codes/")
        assert listing.status_code == 200
        assert listing.json()["results"][0]["usage_count"] == 1

        detail = staff_client.get(f"/api/v1/backoffice/promo-codes/{promo_id}/")
        assert detail.status_code == 200
        assert detail.json()["code"] == "BACK10"

        update = staff_client.patch(
            f"/api/v1/backoffice/promo-codes/{promo_id}/",
            {"is_active": False},
            format="json",
        )
        assert update.status_code == 200
        assert update.json()["is_active"] is False

        delete = staff_client.delete(
            f"/api/v1/backoffice/promo-codes/{promo_id}/"
        )
        assert delete.status_code == 204
        assert (
            staff_client.get(
                f"/api/v1/backoffice/promo-codes/{promo_id}/"
            ).status_code
            == 404
        )

    def test_search_filter(self, staff_client, db):
        _promo(code="SUMMER20", discount_value=20)
        _promo(code="WINTER10")

        response = staff_client.get(
            "/api/v1/backoffice/promo-codes/",
            {"search": "summer", "is_active": "true"},
        )

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["code"] == "SUMMER20"

    def test_invalid_percentage_rejected(self, staff_client, db):
        response = staff_client.post(
            "/api/v1/backoffice/promo-codes/",
            {
                "code": "BAD",
                "discount_type": "PERCENTAGE",
                "discount_value": 150,
            },
            format="json",
        )
        assert response.status_code == 422

    def test_duplicate_code_rejected(self, staff_client, db):
        _promo(code="DUP")

        response = staff_client.post(
            "/api/v1/backoffice/promo-codes/",
            {
                "code": "dup",
                "discount_type": "FIXED",
                "discount_value": 10_000,
            },
            format="json",
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "PROMO_CODE_DUPLICATE"

    def test_customer_cannot_manage_codes(self, authed_client, db):
        response = authed_client.get("/api/v1/backoffice/promo-codes/")
        assert response.status_code == 403


def test_promo_usage_is_soft_deleted(
    db, customer, product, staff_user, restaurant_settings
):
    _promo()
    order = _order(customer, product, promo_code="SAVE10")
    services.cancel_order_by_manager(order_id=order.pk, manager=staff_user)

    assert PromoCodeUsage.all_objects.filter(order=order).count() == 1
    assert PromoCodeUsage.all_objects.get(order=order).deleted_at is not None
    assert PromoCodeUsage.objects.filter(order=order).count() == 0
    # Unrelated fixtures stay importable for the suite.
    assert ProductAddOn.objects.count() == 0
