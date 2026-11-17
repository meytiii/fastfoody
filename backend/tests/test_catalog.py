from __future__ import annotations

import pytest

from apps.catalog import selectors, services
from apps.catalog.exceptions import CategoryHasProductsError, SlugAlreadyExistsError
from apps.catalog.models import AddOn, Category, Product, ProductAddOn


class TestServices:
    def test_create_category(self, db):
        cat = services.create_category(data={"name": "Pizza", "slug": "pizza"})
        assert cat.pk is not None

    def test_slug_unique(self, db):
        services.create_category(data={"name": "Pizza", "slug": "pizza"})
        with pytest.raises(SlugAlreadyExistsError):
            services.create_category(data={"name": "Pizza 2", "slug": "pizza"})

    def test_slug_reusable_after_soft_delete(self, db):
        cat = services.create_category(data={"name": "Pizza", "slug": "pizza"})
        services.delete_category(category_id=cat.pk)
        cat2 = services.create_category(data={"name": "Pizza", "slug": "pizza"})
        assert cat2.pk != cat.pk

    def test_delete_category_with_products_fails(self, db, category, product):
        with pytest.raises(CategoryHasProductsError):
            services.delete_category(category_id=category.pk)

    def test_create_product_with_addons(self, db, category, addon):
        product = services.create_product(
            data={
                "name": "Pizza",
                "slug": "pizza",
                "category_id": category.pk,
                "price": 100_000,
                "is_main_dish": True,
                "prep_time_minutes": 10,
                "addons": [
                    {"addon_id": addon.pk, "min_quantity": 0, "max_quantity": 3}
                ],
            }
        )
        link = ProductAddOn.objects.get(product=product, addon=addon)
        assert link.max_quantity == 3


class TestMenuCache:
    def test_menu_is_cached(self, db, category, product):
        original = product.name
        data1 = selectors.get_storefront_menu()
        assert data1["categories"][0]["products"][0]["name"] == original

        product.name = "New Name"
        product.save()

        data2 = selectors.get_storefront_menu()
        assert data2["categories"][0]["products"][0]["name"] == original

    def test_cache_invalidation_on_update(
        self, db, category, product, django_capture_on_commit_callbacks
    ):
        selectors.get_storefront_menu()
        with django_capture_on_commit_callbacks(execute=True):
            services.update_product(product_id=product.pk, data={"price": 999_999})
        data = selectors.get_storefront_menu()
        assert data["categories"][0]["products"][0]["price"] == 999_999


class TestMenuEndpoint:
    def test_menu(self, api_client, db, category, product):
        response = api_client.get("/api/v1/storefront/catalog/menu/")
        assert response.status_code == 200
        assert len(response.json()["categories"]) == 1

    def test_hidden_excluded(self, api_client, db, category, product):
        product.status = Product.Status.HIDDEN
        product.save()
        response = api_client.get("/api/v1/storefront/catalog/menu/")
        assert response.json()["categories"][0]["products"] == []

    def test_out_of_stock_included(self, api_client, db, category, product):
        product.status = Product.Status.OUT_OF_STOCK
        product.save()
        response = api_client.get("/api/v1/storefront/catalog/menu/")
        products = response.json()["categories"][0]["products"]
        assert len(products) == 1
        assert products[0]["status"] == "OUT_OF_STOCK"


class TestLuckyWheel:
    def test_only_available_main_dishes(self, api_client, db, category, product):
        Product.objects.create(
            category=category,
            name="Coke",
            slug="coke",
            price=20_000,
            is_main_dish=False,
            status=Product.Status.AVAILABLE,
        )
        Product.objects.create(
            category=category,
            name="Burger",
            slug="burger",
            price=200_000,
            is_main_dish=True,
            status=Product.Status.OUT_OF_STOCK,
        )
        response = api_client.get("/api/v1/storefront/catalog/lucky-wheel/")
        products = response.json()["products"]
        assert len(products) == 1
        assert products[0]["slug"] == "margherita"