from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.models import Product
from apps.orders import selectors, services
from apps.orders.models import Order, PromoCode
from common.exceptions import ValidationError


def _order(customer, product, *, qty=1, promo_code=None):
    return services.create_order(
        customer=customer,
        delivery_type=Order.DeliveryType.PICKUP,
        address_id=None,
        items=[{"product_id": product.pk, "quantity": qty, "addons": []}],
        promo_code=promo_code,
    )


class TestSalesAnalytics:
    def test_kpis_and_product_performance(
        self, db, customer, staff_user, product, category, restaurant_settings
    ):
        paid = _order(customer, product, qty=2)
        services.mark_order_paid(order_id=paid.pk)

        refunded = _order(customer, product, qty=1)
        services.mark_order_paid(order_id=refunded.pk)
        services.cancel_order_by_manager(
            order_id=refunded.pk, manager=staff_user
        )
        services.record_refund(
            order_id=refunded.pk,
            manager=staff_user,
            card_number="6037xxxx",
            tracking_code="refund-1",
        )

        PromoCode.objects.create(
            code="TEN",
            discount_type=PromoCode.DiscountType.PERCENTAGE,
            discount_value=10,
        )
        discounted = _order(customer, product, qty=2, promo_code="TEN")
        services.mark_order_paid(order_id=discounted.pk)

        Product.objects.create(
            category=category,
            name="Zero seller",
            slug="zero-seller",
            price=10_000,
        )

        data = selectors.get_sales_analytics(period="today")

        assert data["gross_sales"] == 720_000
        assert data["refunded_count"] == 1
        assert data["refunded_amount"] == 150_000
        assert data["net_sales"] == 570_000
        assert data["paid_orders_count"] == 2
        assert data["average_order_value"] == 285_000
        assert data["total_discounts"] == 30_000
        assert data["total_delivery_fees"] == 0
        assert data["total_packaging_fees"] == 0

        assert data["top_products"][0]["product_id"] == product.pk
        assert data["top_products"][0]["quantity"] == 4
        assert data["top_products"][0]["revenue"] == 600_000

        assert data["least_selling_products"][0]["name"] == "Zero seller"
        assert data["least_selling_products"][0]["quantity_sold"] == 0

        assert sum(row["order_count"] for row in data["peak_hours"]) == 3
        assert len(data["daily_trend"]) == 1
        assert data["daily_trend"][0]["order_count"] == 3
        assert data["daily_trend"][0]["revenue"] == 570_000

    def test_empty_range_returns_zeroes(
        self, db, customer, product, restaurant_settings
    ):
        _order(customer, product)  # unpaid: excluded from every KPI

        data = selectors.get_sales_analytics(period="today")

        assert data["gross_sales"] == 0
        assert data["net_sales"] == 0
        assert data["paid_orders_count"] == 0
        assert data["average_order_value"] == 0
        assert data["top_products"] == []

    def test_custom_range_requires_both_dates(
        self, db, restaurant_settings
    ):
        with pytest.raises(ValidationError):
            selectors.get_sales_analytics(
                period="custom", date_from=timezone.localdate()
            )

    def test_custom_range_rejects_reversed_dates(
        self, db, restaurant_settings
    ):
        today = timezone.localdate()

        with pytest.raises(ValidationError):
            selectors.get_sales_analytics(
                period="custom",
                date_from=today,
                date_to=today - timedelta(days=1),
            )

    def test_invalid_period_rejected(self, db, restaurant_settings):
        with pytest.raises(ValidationError):
            selectors.get_sales_analytics(period="90d")


class TestAnalyticsEndpoint:
    def test_staff_can_read(
        self, staff_client, db, customer, product, restaurant_settings
    ):
        order = _order(customer, product)
        services.mark_order_paid(order_id=order.pk)

        response = staff_client.get(
            "/api/v1/backoffice/analytics/sales/",
            {"period": "today"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["gross_sales"] == product.price
        assert body["net_sales"] == product.price
        assert body["paid_orders_count"] == 1
        assert len(body["peak_hours"]) == 24

    def test_customer_denied(self, authed_client, db):
        response = authed_client.get("/api/v1/backoffice/analytics/sales/")
        assert response.status_code == 403

    def test_anonymous_denied(self, api_client, db):
        response = api_client.get("/api/v1/backoffice/analytics/sales/")
        assert response.status_code in (401, 403)

    def test_invalid_custom_range_returns_422(
        self, staff_client, db
    ):
        response = staff_client.get(
            "/api/v1/backoffice/analytics/sales/",
            {"period": "custom"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"
