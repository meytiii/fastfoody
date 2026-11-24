from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.models import Product
from apps.catalog.search import (
    ARABIC_KAF,
    ARABIC_YEH,
    MAX_PRICE_FILTER,
    MAX_SEARCH_LENGTH,
    normalize_search_query,
    search_variants,
)

LIST_URL = "/api/v1/storefront/catalog/products/"
SUGGEST_URL = "/api/v1/storefront/catalog/suggestions/"


@pytest.fixture(autouse=True)
def _local_cache(settings):
    """Discovery endpoints are throttled; keep tests independent of Redis."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def _make(
    category,
    name,
    *,
    slug,
    price=100_000,
    status=Product.Status.AVAILABLE,
    is_main_dish=True,
    display_order=0,
    description="",
    prep_time_minutes=5,
):
    return Product.objects.create(
        category=category,
        name=name,
        slug=slug,
        price=price,
        status=status,
        is_main_dish=is_main_dish,
        display_order=display_order,
        description=description,
        prep_time_minutes=prep_time_minutes,
    )


def _payload(response):
    assert response.status_code == 200, response.content
    return response.json()


def _names(response):
    return [row["name"] for row in _payload(response)["results"]]


def _error(response):
    body = response.json()
    assert body["success"] is False
    return body["error"]


class TestSearchNormalization:
    def test_folds_arabic_letters_to_persian(self):
        assert normalize_search_query("پيتزا كباب") == "پیتزا کباب"

    def test_converts_persian_and_arabic_digits(self):
        assert normalize_search_query("پیتزا ۲") == "پیتزا 2"
        assert normalize_search_query("پیتزا \u0662") == "پیتزا 2"

    def test_collapses_and_trims_whitespace(self):
        assert normalize_search_query("  cheese    burger  ") == "cheese burger"

    def test_handles_empty_and_none(self):
        assert normalize_search_query(None) == ""
        assert normalize_search_query("") == ""
        assert normalize_search_query("   \t\n ") == ""

    def test_removes_zero_width_non_joiner(self):
        assert normalize_search_query("هم\u200cبرگر") == "همبرگر"

    def test_truncates_oversized_input(self):
        assert len(normalize_search_query("a" * (MAX_SEARCH_LENGTH + 50))) == (
            MAX_SEARCH_LENGTH
        )

    def test_variants_cover_both_spellings(self):
        variants = set(search_variants("پیتزا"))
        assert "پیتزا" in variants
        assert any(ARABIC_YEH in variant for variant in variants)

        kaf_variants = set(search_variants("کباب"))
        assert any(ARABIC_KAF in variant for variant in kaf_variants)


class TestSearch:
    def test_exact_name_ranks_first(self, api_client, db, category):
        _make(category, "Cheese Burger", slug="cheese-burger", display_order=1)
        _make(category, "Burger", slug="burger", display_order=2)

        assert _names(api_client.get(LIST_URL, {"q": "burger"}))[0] == "Burger"

    def test_partial_match(self, api_client, db, category):
        _make(category, "Cheese Burger", slug="cheese-burger")
        _make(category, "Pizza", slug="pizza")

        assert _names(api_client.get(LIST_URL, {"q": "cheese"})) == ["Cheese Burger"]

    def test_english_is_case_insensitive(self, api_client, db, category):
        _make(category, "Cheese Burger", slug="cheese-burger")

        assert _names(api_client.get(LIST_URL, {"q": "BURGER"})) == ["Cheese Burger"]

    def test_persian_search(self, api_client, db, category):
        _make(category, "پیتزا مخصوص", slug="pizza-special")
        _make(category, "سالاد", slug="salad")

        assert _names(api_client.get(LIST_URL, {"q": "پیتزا"})) == ["پیتزا مخصوص"]

    def test_arabic_stored_data_matches_persian_query(self, api_client, db, category):
        _make(category, "كباب كوبيده", slug="kabab")
        _make(category, "سالاد", slug="salad")

        assert _names(api_client.get(LIST_URL, {"q": "کباب کوبیده"})) == [
            "كباب كوبيده"
        ]

    def test_persian_query_with_arabic_input(self, api_client, db, category):
        _make(category, "پیتزا مخصوص", slug="pizza-special")

        assert _names(api_client.get(LIST_URL, {"q": "پيتزا"})) == ["پیتزا مخصوص"]

    def test_searches_description(self, api_client, db, category):
        _make(
            category,
            "پیتزا مخصوص",
            slug="pizza-special",
            description="با پنیر موزارلا",
        )

        assert _names(api_client.get(LIST_URL, {"q": "موزارلا"})) == ["پیتزا مخصوص"]

    def test_searches_category_name(self, api_client, db, category):
        # conftest `category` is named "Pizzas"
        _make(category, "Margherita", slug="margherita")

        assert _names(api_client.get(LIST_URL, {"q": "Pizzas"})) == ["Margherita"]

    def test_empty_query_returns_all_visible(self, api_client, db, category):
        _make(category, "One", slug="one")
        _make(category, "Two", slug="two")

        assert _payload(api_client.get(LIST_URL, {"q": ""}))["count"] == 2

    def test_no_results(self, api_client, db, category):
        _make(category, "One", slug="one")

        payload = _payload(api_client.get(LIST_URL, {"q": "zzzz"}))
        assert payload["count"] == 0
        assert payload["results"] == []

    def test_hidden_product_never_matches(self, api_client, db, category):
        _make(
            category,
            "Secret Burger",
            slug="secret-burger",
            status=Product.Status.HIDDEN,
        )

        assert _names(api_client.get(LIST_URL, {"q": "Secret"})) == []

    def test_no_duplicate_rows_when_several_fields_match(self, api_client, db):
        from apps.catalog.models import Category

        cat = Category.objects.create(name="Pizza Pizza", slug="pizza-pizza")
        _make(
            cat,
            "Pizza Pizza",
            slug="pizza-pizza-special",
            description="pizza with extra pizza",
        )

        payload = _payload(api_client.get(LIST_URL, {"q": "pizza"}))
        assert payload["count"] == 1

    def test_products_in_inactive_category_are_not_discoverable(
        self, api_client, db
    ):
        from apps.catalog.models import Category

        cat = Category.objects.create(
            name="Hidden Menu", slug="hidden-menu", is_active=False
        )
        _make(cat, "Ghost Product", slug="ghost")

        assert _names(api_client.get(LIST_URL, {"q": "Ghost"})) == []


class TestCategoryFilter:
    def test_filter_by_slug(self, api_client, db, category):
        from apps.catalog.models import Category

        drinks = Category.objects.create(name="Drinks", slug="drinks")
        _make(category, "Pizza", slug="pizza")
        _make(drinks, "Cola", slug="cola")

        assert _names(api_client.get(LIST_URL, {"category": "drinks"})) == ["Cola"]

    def test_filter_by_id(self, api_client, db, category):
        _make(category, "Pizza", slug="pizza")

        assert _names(api_client.get(LIST_URL, {"category_id": category.pk})) == [
            "Pizza"
        ]

    def test_unknown_slug_is_404(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"category": "nope"})

        assert response.status_code == 404
        assert _error(response)["code"] == "CATEGORY_NOT_FOUND"

    def test_unknown_id_is_404(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"category_id": 9999})

        assert response.status_code == 404
        assert _error(response)["code"] == "CATEGORY_NOT_FOUND"

    def test_inactive_category_is_404(self, api_client, db):
        from apps.catalog.models import Category

        Category.objects.create(name="Closed", slug="closed", is_active=False)

        response = api_client.get(LIST_URL, {"category": "closed"})
        assert response.status_code == 404

    def test_non_numeric_id_is_400(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"category_id": "abc"})

        assert response.status_code == 400
        assert "category_id" in _error(response)["details"]

    def test_empty_category_returns_empty_page(self, api_client, db, category):
        payload = _payload(api_client.get(LIST_URL, {"category": "pizzas"}))
        assert payload["count"] == 0

    def test_category_combined_with_search(self, api_client, db, category):
        from apps.catalog.models import Category

        drinks = Category.objects.create(name="Drinks", slug="drinks")
        _make(category, "Cheese Pizza", slug="cheese-pizza")
        _make(drinks, "Cheese Cola", slug="cheese-cola")

        assert _names(
            api_client.get(LIST_URL, {"q": "cheese", "category": "drinks"})
        ) == ["Cheese Cola"]


class TestPriceFilter:
    def test_min_price(self, api_client, db, category):
        _make(category, "Cheap", slug="cheap", price=50_000)
        _make(category, "Pricey", slug="pricey", price=300_000)

        assert _names(api_client.get(LIST_URL, {"min_price": 100_000})) == ["Pricey"]

    def test_max_price(self, api_client, db, category):
        _make(category, "Cheap", slug="cheap", price=50_000)
        _make(category, "Pricey", slug="pricey", price=300_000)

        assert _names(api_client.get(LIST_URL, {"max_price": 100_000})) == ["Cheap"]

    def test_range_is_inclusive(self, api_client, db, category):
        _make(category, "Low", slug="low", price=100_000)
        _make(category, "Mid", slug="mid", price=200_000)
        _make(category, "High", slug="high", price=300_000)

        names = _names(
            api_client.get(LIST_URL, {"min_price": 100_000, "max_price": 200_000})
        )
        assert set(names) == {"Low", "Mid"}

    def test_negative_min_price_is_400(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"min_price": -1})

        assert response.status_code == 400
        assert "min_price" in _error(response)["details"]

    def test_non_numeric_price_is_400(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"max_price": "cheap"})

        assert response.status_code == 400
        assert "max_price" in _error(response)["details"]

    def test_reversed_range_is_400(self, api_client, db, category):
        response = api_client.get(
            LIST_URL, {"min_price": 300_000, "max_price": 100_000}
        )

        assert response.status_code == 400
        assert "max_price" in _error(response)["details"]

    def test_extremely_large_price_is_400(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"max_price": MAX_PRICE_FILTER + 1})

        assert response.status_code == 400

    def test_price_filter_uses_product_price(self, api_client, db, category):
        product = _make(category, "Pizza", slug="pizza", price=150_000)

        payload = _payload(api_client.get(LIST_URL, {"min_price": 150_000}))
        assert payload["results"][0]["price"] == product.price


class TestAvailabilityFilters:
    def test_default_includes_available_and_out_of_stock(
        self, api_client, db, category
    ):
        _make(category, "In Stock", slug="in-stock")
        _make(
            category,
            "Sold Out",
            slug="sold-out",
            status=Product.Status.OUT_OF_STOCK,
        )

        assert _payload(api_client.get(LIST_URL))["count"] == 2

    def test_available_true_excludes_out_of_stock(self, api_client, db, category):
        _make(category, "In Stock", slug="in-stock")
        _make(
            category,
            "Sold Out",
            slug="sold-out",
            status=Product.Status.OUT_OF_STOCK,
        )

        assert _names(api_client.get(LIST_URL, {"available": 1})) == ["In Stock"]

    def test_available_false_returns_only_out_of_stock(self, api_client, db, category):
        _make(category, "In Stock", slug="in-stock")
        _make(
            category,
            "Sold Out",
            slug="sold-out",
            status=Product.Status.OUT_OF_STOCK,
        )

        assert _names(api_client.get(LIST_URL, {"available": 0})) == ["Sold Out"]

    def test_is_main_dish_filter(self, api_client, db, category):
        _make(category, "Main", slug="main", is_main_dish=True)
        _make(category, "Side", slug="side", is_main_dish=False)

        assert _names(api_client.get(LIST_URL, {"is_main_dish": 1})) == ["Main"]
        assert _names(api_client.get(LIST_URL, {"is_main_dish": 0})) == ["Side"]

    def test_invalid_boolean_is_400(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"available": "maybe"})
        assert response.status_code == 400

    def test_discount_filter_is_rejected_explicitly(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"discount": 1})

        assert response.status_code == 400
        assert "discount" in _error(response)["details"]

    def test_filters_combine(self, api_client, db, category):
        _make(category, "Cheap Main", slug="cheap-main", price=80_000)
        _make(
            category,
            "Cheap Side",
            slug="cheap-side",
            price=80_000,
            is_main_dish=False,
        )
        _make(category, "Pricey Main", slug="pricey-main", price=500_000)

        names = _names(
            api_client.get(
                LIST_URL,
                {"available": 1, "is_main_dish": 1, "max_price": 100_000},
            )
        )
        assert names == ["Cheap Main"]


class TestSorting:
    def test_default_order_uses_display_order_then_name(
        self, api_client, db, category
    ):
        _make(category, "B", slug="b", display_order=2)
        _make(category, "A", slug="a", display_order=1)
        _make(category, "C", slug="c", display_order=2)

        assert _names(api_client.get(LIST_URL)) == ["A", "B", "C"]

    def test_newest_and_oldest(self, api_client, db, category):
        old = _make(category, "Old", slug="old")
        new = _make(category, "New", slug="new")
        now = timezone.now()
        Product.objects.filter(pk=old.pk).update(created_at=now - timedelta(days=2))
        Product.objects.filter(pk=new.pk).update(created_at=now - timedelta(days=1))

        assert _names(api_client.get(LIST_URL, {"sort": "newest"}))[0] == "New"
        assert _names(api_client.get(LIST_URL, {"sort": "oldest"}))[0] == "Old"

    def test_price_sorting(self, api_client, db, category):
        _make(category, "Mid", slug="mid", price=200_000)
        _make(category, "Low", slug="low", price=100_000)
        _make(category, "High", slug="high", price=300_000)

        assert _names(api_client.get(LIST_URL, {"sort": "price_asc"})) == [
            "Low",
            "Mid",
            "High",
        ]
        assert _names(api_client.get(LIST_URL, {"sort": "price_desc"})) == [
            "High",
            "Mid",
            "Low",
        ]

    def test_relevance_is_default_when_searching(self, api_client, db, category):
        _make(category, "Spicy Burger Deluxe", slug="spicy-burger", display_order=1)
        _make(category, "Burger", slug="burger", display_order=9)

        assert _names(api_client.get(LIST_URL, {"q": "burger"}))[0] == "Burger"

    def test_relevance_without_query_falls_back_to_default(
        self, api_client, db, category
    ):
        _make(category, "Second", slug="second", display_order=2)
        _make(category, "First", slug="first", display_order=1)

        assert _names(api_client.get(LIST_URL, {"sort": "relevance"})) == [
            "First",
            "Second",
        ]

    def test_unknown_sort_is_400(self, api_client, db, category):
        response = api_client.get(LIST_URL, {"sort": "random"})

        assert response.status_code == 400
        assert "sort" in _error(response)["details"]

    def test_ties_are_deterministic(self, api_client, db, category):
        for index, name in enumerate(["Tie A", "Tie B", "Tie C"], start=1):
            _make(category, name, slug=f"tie-{index}", price=100_000)

        first = _names(api_client.get(LIST_URL, {"sort": "price_asc"}))
        second = _names(api_client.get(LIST_URL, {"sort": "price_asc"}))
        assert first == second == ["Tie A", "Tie B", "Tie C"]


class TestPagination:
    def test_offset_and_limit(self, api_client, db, category):
        for index in range(5):
            _make(
                category,
                f"Item {index}",
                slug=f"item-{index}",
                price=100_000,
                display_order=index,
            )

        payload = _payload(api_client.get(LIST_URL, {"limit": 2, "offset": 2}))
        assert payload["count"] == 5
        assert _names(api_client.get(LIST_URL, {"limit": 2, "offset": 2})) == [
            "Item 2",
            "Item 3",
        ]

    def test_filter_parameters_survive_pagination(self, api_client, db, category):
        for index in range(4):
            _make(
                category,
                f"Burger {index}",
                slug=f"burger-{index}",
                price=150_000,
                display_order=index,
            )

        response = api_client.get(
            LIST_URL, {"q": "Burger", "min_price": 100_000, "limit": 2}
        )
        assert response.status_code == 200
        next_url = response.json()["next"]
        assert next_url is not None
        assert "q=Burger" in next_url
        assert "min_price=100000" in next_url
        assert "limit=2" in next_url

    def test_no_duplicates_across_pages(self, api_client, db, category):
        for index in range(5):
            _make(
                category,
                f"Tie {index}",
                slug=f"tie-{index}",
                price=100_000,
                display_order=0,
            )

        seen: list[int] = []
        for offset in (0, 2, 4):
            payload = _payload(
                api_client.get(LIST_URL, {"sort": "price_asc", "limit": 2, "offset": offset})
            )
            seen.extend(row["id"] for row in payload["results"])

        assert len(seen) == len(set(seen)) == 5

    def test_empty_result_pagination_metadata(self, api_client, db, category):
        payload = _payload(api_client.get(LIST_URL, {"q": "nothing-here"}))
        assert payload["count"] == 0
        assert payload["next"] is None
        assert payload["previous"] is None


class TestSuggestions:
    def test_returns_expected_schema(self, api_client, db, category):
        _make(category, "Cheese Burger", slug="cheese-burger", price=180_000)

        results = _payload(api_client.get(SUGGEST_URL, {"q": "burger"}))["results"]

        assert len(results) == 1
        assert set(results[0]) == {
            "id",
            "name",
            "slug",
            "price",
            "status",
            "image_url",
        }
        assert results[0]["price"] == 180_000
        assert results[0]["slug"] == "cheese-burger"

    def test_empty_query_returns_no_suggestions(self, api_client, db, category):
        _make(category, "Cheese Burger", slug="cheese-burger")

        assert _payload(api_client.get(SUGGEST_URL, {"q": ""}))["results"] == []
        assert _payload(api_client.get(SUGGEST_URL))["results"] == []

    def test_default_limit(self, api_client, db, category):
        for index in range(12):
            _make(category, f"Burger {index}", slug=f"burger-{index}")

        results = _payload(api_client.get(SUGGEST_URL, {"q": "burger"}))["results"]
        assert len(results) == 5

    def test_limit_is_clamped_to_configured_maximum(self, api_client, db, category):
        for index in range(12):
            _make(category, f"Burger {index}", slug=f"burger-{index}")

        results = _payload(
            api_client.get(SUGGEST_URL, {"q": "burger", "limit": 50})
        )["results"]
        assert len(results) == 10

    def test_explicit_limit(self, api_client, db, category):
        for index in range(4):
            _make(category, f"Burger {index}", slug=f"burger-{index}")

        results = _payload(
            api_client.get(SUGGEST_URL, {"q": "burger", "limit": 2})
        )["results"]
        assert len(results) == 2

    def test_invalid_limit_is_400(self, api_client, db, category):
        assert api_client.get(SUGGEST_URL, {"q": "x", "limit": "abc"}).status_code == 400
        assert api_client.get(SUGGEST_URL, {"q": "x", "limit": 0}).status_code == 400

    def test_hidden_and_inactive_products_are_excluded(self, api_client, db, category):
        from apps.catalog.models import Category

        closed = Category.objects.create(
            name="Closed", slug="closed", is_active=False
        )
        _make(category, "Visible Burger", slug="visible-burger")
        _make(
            category,
            "Hidden Burger",
            slug="hidden-burger",
            status=Product.Status.HIDDEN,
        )
        _make(closed, "Closed Burger", slug="closed-burger")

        names = [
            row["name"]
            for row in _payload(api_client.get(SUGGEST_URL, {"q": "burger"}))["results"]
        ]
        assert names == ["Visible Burger"]

    def test_query_is_limited(self, api_client, db, category, django_assert_max_num_queries):
        for index in range(10):
            _make(category, f"Burger {index}", slug=f"burger-{index}")

        with django_assert_max_num_queries(2):
            response = api_client.get(SUGGEST_URL, {"q": "burger"})
        assert response.status_code == 200


class TestListingQueryCount:
    def test_listing_query_count(
        self, api_client, db, category, django_assert_max_num_queries
    ):
        for index in range(5):
            _make(category, f"Burger {index}", slug=f"burger-{index}")

        with django_assert_max_num_queries(3):
            response = api_client.get(LIST_URL, {"q": "burger", "limit": 5})
        assert response.status_code == 200


class TestRegression:
    def test_menu_still_excludes_hidden_products(self, api_client, db, category):
        _make(category, "Visible", slug="visible")
        _make(category, "Hidden", slug="hidden", status=Product.Status.HIDDEN)

        response = api_client.get("/api/v1/storefront/catalog/menu/")
        assert response.status_code == 200

        products = response.json()["categories"][0]["products"]
        assert [p["name"] for p in products] == ["Visible"]

    def test_product_detail_still_works(self, api_client, db, category):
        _make(category, "Margherita", slug="margherita")

        response = api_client.get("/api/v1/storefront/catalog/products/margherita/")
        assert response.status_code == 200
        assert response.json()["slug"] == "margherita"
        assert "addons" in response.json()

    def test_hidden_product_detail_is_still_404(self, api_client, db, category):
        _make(category, "Secret", slug="secret", status=Product.Status.HIDDEN)

        response = api_client.get("/api/v1/storefront/catalog/products/secret/")
        assert response.status_code == 404
        assert _error(response)["code"] == "PRODUCT_NOT_FOUND"

    def test_lucky_wheel_unchanged(self, api_client, db, category):
        _make(category, "Main Dish", slug="main-dish", is_main_dish=True)
        _make(category, "Side", slug="side", is_main_dish=False)

        response = api_client.get("/api/v1/storefront/catalog/lucky-wheel/")
        assert response.status_code == 200
        assert [p["name"] for p in response.json()["products"]] == ["Main Dish"]
