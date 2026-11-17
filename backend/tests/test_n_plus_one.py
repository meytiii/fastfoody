from __future__ import annotations


class TestQueryCounts:
    def test_menu_query_count(
        self, django_assert_max_num_queries, db, category, product
    ):
        from apps.catalog.selectors import get_storefront_menu

        with django_assert_max_num_queries(3):
            get_storefront_menu()

    def test_order_detail_query_count(
        self, django_assert_max_num_queries, db, customer, product, restaurant_settings
    ):
        from apps.orders import services, selectors

        order = services.create_order(
            customer=customer,
            delivery_type="PICKUP",
            address_id=None,
            items=[{"product_id": product.pk, "quantity": 1, "addons": []}],
        )
        with django_assert_max_num_queries(4):
            o = selectors.get_order_backoffice(order.pk)
            for item in o.items.all():
                list(item.addons.all())