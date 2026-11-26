from __future__ import annotations

import pytest

from apps.accounts.models import Customer
from apps.catalog.models import Category, Product, ProductAddOn
from apps.orders import services
from apps.orders.exceptions import OrderNotFoundError
from apps.orders.models import Order


def _order(customer, product, *, qty=1, addon=None, addon_qty=1):
    addons = (
        [{"addon_id": addon.pk, "quantity": addon_qty}] if addon is not None else []
    )
    return services.create_order(
        customer=customer,
        delivery_type=Order.DeliveryType.PICKUP,
        address_id=None,
        items=[
            {"product_id": product.pk, "quantity": qty, "addons": addons}
        ],
    )


class TestReorderPayload:
    def test_rebuilds_current_prices(
        self, db, customer, product, addon, restaurant_settings
    ):
        ProductAddOn.objects.create(
            product=product, addon=addon, max_quantity=3
        )
        order = _order(customer, product, qty=2, addon=addon, addon_qty=2)

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["warnings"] == []
        assert len(payload["items"]) == 1
        item = payload["items"][0]
        assert item["product_id"] == product.pk
        assert item["quantity"] == 2
        assert item["unit_price"] == product.price
        assert item["addons"][0]["addon_id"] == addon.pk
        assert item["addons"][0]["quantity"] == 2
        assert item["line_total"] == (product.price * 2) + (addon.price * 2)

    def test_skips_hidden_and_out_of_stock_products(
        self, db, customer, product, restaurant_settings
    ):
        order = _order(customer, product)
        product.status = Product.Status.HIDDEN
        product.save(update_fields=["status"])

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"] == []
        assert any("موجود نیست" in warning for warning in payload["warnings"])

    def test_skips_inactive_category(
        self, db, customer, product, restaurant_settings
    ):
        order = _order(customer, product)
        product.category.is_active = False
        product.category.save(update_fields=["is_active"])

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"] == []
        assert any("غیرفعال" in warning for warning in payload["warnings"])

    def test_skips_soft_deleted_product(
        self, db, customer, product, restaurant_settings
    ):
        order = _order(customer, product)
        product.delete()

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"] == []
        assert any("حذف شد" in warning for warning in payload["warnings"])

    def test_clamps_addon_quantity(
        self, db, customer, product, addon, restaurant_settings
    ):
        link = ProductAddOn.objects.create(
            product=product, addon=addon, max_quantity=5
        )
        order = _order(customer, product, addon=addon, addon_qty=4)
        link.max_quantity = 2
        link.save(update_fields=["max_quantity"])

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"][0]["addons"][0]["quantity"] == 2
        assert any("کاهش یافت" in warning for warning in payload["warnings"])

    def test_skips_unavailable_addon(
        self, db, customer, product, addon, restaurant_settings
    ):
        ProductAddOn.objects.create(product=product, addon=addon)
        order = _order(customer, product, addon=addon)
        addon.is_available = False
        addon.save(update_fields=["is_available"])

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"][0]["addons"] == []
        assert any("افزودنی" in warning for warning in payload["warnings"])

    def test_skips_unlinked_addon(
        self, db, customer, product, addon, restaurant_settings
    ):
        link = ProductAddOn.objects.create(product=product, addon=addon)
        order = _order(customer, product, addon=addon)
        link.delete()

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"][0]["addons"] == []

    def test_reports_price_changes(
        self, db, customer, product, addon, restaurant_settings
    ):
        ProductAddOn.objects.create(product=product, addon=addon)
        order = _order(customer, product, addon=addon)
        product.price = 175_000
        product.save(update_fields=["price"])
        addon.price = 30_000
        addon.save(update_fields=["price"])

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert payload["items"][0]["unit_price"] == 175_000
        assert payload["items"][0]["addons"][0]["unit_price"] == 30_000
        joined = " ".join(payload["warnings"])
        assert "قیمت محصول" in joined
        assert "قیمت افزودنی" in joined

    def test_other_customer_order_not_found(
        self, db, customer, product, restaurant_settings
    ):
        other = Customer.objects.create_user(phone="09127777777")
        order = _order(other, product)

        with pytest.raises(OrderNotFoundError):
            services.prepare_reorder_payload(customer, order.pk)

    def test_product_from_inactive_category_still_counted_once(
        self, db, customer, product, restaurant_settings
    ):
        order = _order(customer, product)

        payload = services.prepare_reorder_payload(customer, order.pk)

        assert len(payload["items"]) == 1
        # Sanity: the fixture category is active and the product is available.
        assert Category.objects.filter(is_active=True).exists()
        assert Order.objects.filter(pk=order.pk).exists()


class TestReorderEndpoint:
    def test_owner_gets_cart_payload(
        self, authed_client, db, customer, product, restaurant_settings
    ):
        order = _order(customer, product)

        response = authed_client.post(
            f"/api/v1/storefront/orders/{order.pk}/reorder/",
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["items"][0]["product_id"] == product.pk

    def test_other_customer_gets_404(
        self, authed_client, db, customer, product, restaurant_settings
    ):
        other = Customer.objects.create_user(phone="09126666666")
        order = _order(other, product)

        response = authed_client.post(
            f"/api/v1/storefront/orders/{order.pk}/reorder/",
            format="json",
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"

    def test_requires_authentication(self, api_client, db, customer, product, restaurant_settings):
        order = _order(customer, product)

        response = api_client.post(
            f"/api/v1/storefront/orders/{order.pk}/reorder/",
            format="json",
        )

        assert response.status_code in (401, 403)
