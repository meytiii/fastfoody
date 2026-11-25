from __future__ import annotations

from datetime import time

import pytest

from apps.cms import services
from apps.cms.exceptions import InvalidSiteSectionKeyError
from apps.cms.models import RestaurantSettings, SiteSection
from apps.cms.selectors import get_restaurant_status


class TestRestaurantSettings:
    def test_save_forces_pk_one(self, db):
        assert RestaurantSettings.objects.count() == 1
        settings = RestaurantSettings.objects.get(pk=1)
        settings.pk = 42
        settings.is_temporarily_closed = True
        settings.save()
        settings.refresh_from_db()
        assert settings.pk == 1
        assert settings.is_temporarily_closed is True

    def test_is_open_same_day(self, db):
        s = RestaurantSettings.objects.get(pk=1)
        s.open_time = time(9, 0)
        s.close_time = time(22, 0)
        s.save()
        assert s.is_open(time(10, 0)) is True
        assert s.is_open(time(22, 0)) is False
        assert s.is_open(time(8, 0)) is False

    def test_is_open_overnight(self, db):
        s = RestaurantSettings.objects.get(pk=1)
        s.open_time = time(11, 0)
        s.close_time = time(1, 0)
        s.save()
        assert s.is_open(time(23, 0)) is True
        assert s.is_open(time(0, 30)) is True
        assert s.is_open(time(5, 0)) is False

    def test_temporarily_closed(self, db):
        s = RestaurantSettings.objects.get(pk=1)
        s.is_temporarily_closed = True
        s.save()
        assert s.is_open() is False

    def test_storefront_status_exposes_operational_fees(self, api_client, db):
        s = RestaurantSettings.objects.get(pk=1)
        s.min_delivery_order_amount = 250_000
        s.packaging_fee = 15_000
        s.save()

        response = api_client.get("/api/v1/storefront/cms/restaurant-status/")

        assert response.status_code == 200
        assert response.json()["min_delivery_order_amount"] == 250_000
        assert response.json()["packaging_fee"] == 15_000


class TestSiteSections:
    def test_default_content(self, api_client, db):
        response = api_client.get("/api/v1/storefront/cms/site-sections/hero/")
        assert response.status_code == 200
        assert "content" in response.json()

    def test_upsert(self, db):
        services.upsert_site_section(key="hero", content={"title": "Hello"})
        assert SiteSection.objects.get(key="hero").content == {"title": "Hello"}

    def test_invalid_key(self, db):
        with pytest.raises(InvalidSiteSectionKeyError):
            services.upsert_site_section(key="invalid", content={})

    def test_all_endpoint_returns_all_keys(self, api_client, db):
        response = api_client.get("/api/v1/storefront/cms/site-sections/")
        assert set(response.json().keys()) == {
            "hero", "header", "footer", "announcement", "lucky_wheel", "about_us",
        }


class TestCacheInvalidation:
    def test_settings_cache(self, db, django_capture_on_commit_callbacks):
        s = RestaurantSettings.objects.get(pk=1)
        s.is_temporarily_closed = False
        s.save()

        assert get_restaurant_status()["is_temporarily_closed"] is False

        with django_capture_on_commit_callbacks(execute=True):
            services.update_restaurant_settings(data={"is_temporarily_closed": True})

        assert get_restaurant_status()["is_temporarily_closed"] is True

    def test_site_section_cache(self, db, django_capture_on_commit_callbacks):
        from apps.cms.selectors import get_site_section

        assert get_site_section("hero")["title"] == ""
        with django_capture_on_commit_callbacks(execute=True):
            services.upsert_site_section(key="hero", content={"title": "New"})
        assert get_site_section("hero")["title"] == "New"


class TestBackofficeCMS:
    def test_staff_can_update(self, staff_client, db):
        response = staff_client.patch(
            "/api/v1/backoffice/cms/restaurant-settings/",
            {"in_zone_delivery_fee": 60_000},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["in_zone_delivery_fee"] == 60_000

    def test_non_staff_denied(self, authed_client, db):
        response = authed_client.patch(
            "/api/v1/backoffice/cms/restaurant-settings/",
            {"in_zone_delivery_fee": 60_000},
            format="json",
        )
        assert response.status_code == 403

    def test_staff_can_update_delivery_minimum_and_packaging(
        self, staff_client, db
    ):
        response = staff_client.patch(
            "/api/v1/backoffice/cms/restaurant-settings/",
            {"min_delivery_order_amount": 180_000, "packaging_fee": 12_000},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["min_delivery_order_amount"] == 180_000
        assert response.json()["packaging_fee"] == 12_000