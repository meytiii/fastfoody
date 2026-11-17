from __future__ import annotations

import pytest

from apps.accounts.models import Customer
from apps.orders import services
from apps.orders.models import Order


BACKOFFICE_URLS = [
    "/api/v1/backoffice/crm/customers/",
    "/api/v1/backoffice/catalog/categories/",
    "/api/v1/backoffice/orders/",
    "/api/v1/backoffice/cms/restaurant-settings/",
]


class TestBackofficeAccess:
    @pytest.mark.parametrize("url", BACKOFFICE_URLS)
    def test_anonymous_denied(self, api_client, db, url):
        response = api_client.get(url)
        assert response.status_code in (401, 403)

    @pytest.mark.parametrize("url", BACKOFFICE_URLS)
    def test_customer_denied(self, authed_client, db, url):
        response = authed_client.get(url)
        assert response.status_code == 403


class TestCustomerIsolation:
    def test_cannot_see_others_order(
        self, authed_client, db, customer, product, restaurant_settings
    ):
        other = Customer.objects.create_user(phone="09129999999")
        order = services.create_order(
            customer=other,
            delivery_type=Order.DeliveryType.PICKUP,
            address_id=None,
            items=[{"product_id": product.pk, "quantity": 1, "addons": []}],
        )
        response = authed_client.get(f"/api/v1/storefront/orders/{order.pk}/")
        assert response.status_code == 404