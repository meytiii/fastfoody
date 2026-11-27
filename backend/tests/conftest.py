from __future__ import annotations

from datetime import time
from unittest.mock import MagicMock

import pytest
from django.core.cache import cache

_TEST_REDIS_URL = "redis://127.0.0.1:6379/15"


@pytest.fixture(autouse=True)
def _isolated_cache(settings):
    settings.REDIS_URL = _TEST_REDIS_URL
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _TEST_REDIS_URL,
            "KEY_PREFIX": "fastfood_test",
        }
    }
    settings.ZARINPAL_MERCHANT_ID = "test-merchant"
    settings.SMS_IR_API_KEY = ""
    settings.SMS_IR_SENDER = ""
    settings.MANAGER_PHONE = ""
    settings.PAYMENT_FRONTEND_RESULT_URL = "http://test/frontend/callback"

    from common.redis_client import get_redis

    get_redis.cache_clear()
    try:
        cache.clear()
        get_redis().flushdb()
    except Exception:
        pass

    yield

    try:
        cache.clear()
        get_redis().flushdb()
    except Exception:
        pass
    get_redis.cache_clear()


@pytest.fixture(autouse=True)
def _silence_external(_isolated_cache, monkeypatch):
    from apps.accounts import services as accounts_services
    from apps.orders import services as orders_services
    from apps.accounts import tasks as accounts_tasks
    from apps.orders import tasks as orders_tasks

    monkeypatch.setattr(accounts_services, "send_otp_sms", MagicMock())
    monkeypatch.setattr(orders_services, "send_order_registered_sms", MagicMock())
    monkeypatch.setattr(orders_services, "send_order_ready_sms", MagicMock())
    monkeypatch.setattr(orders_services, "send_prep_time_changed_sms", MagicMock())
    monkeypatch.setattr(accounts_tasks, "send_sms", lambda **kw: True)
    monkeypatch.setattr(orders_tasks, "send_sms", lambda **kw: True)


@pytest.fixture
def restaurant_settings(db):
    from apps.cms.models import RestaurantSettings

    obj, _ = RestaurantSettings.objects.get_or_create(pk=1)
    # Order tests must not depend on the wall clock. Production/staging seeds
    # 11:00-01:00, which would make the suite fail outside opening hours.
    obj.open_time = time(0, 0)
    obj.close_time = time(23, 59, 59)
    obj.is_temporarily_closed = False
    obj.save(
        update_fields=[
            "open_time",
            "close_time",
            "is_temporarily_closed",
            "updated_at",
        ]
    )
    return obj


@pytest.fixture
def customer(db):
    from apps.accounts.models import Customer

    return Customer.objects.create_user(phone="09120000000")


@pytest.fixture
def staff_user(db):
    from apps.accounts.models import Customer

    return Customer.objects.create_user(
        phone="09121111111", password="testpass123", is_staff=True
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authed_client(api_client, customer):
    api_client.force_authenticate(user=customer)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.fixture
def category(db):
    from apps.catalog.models import Category

    return Category.objects.create(name="Pizzas", slug="pizzas")


@pytest.fixture
def product(db, category):
    from apps.catalog.models import Product

    return Product.objects.create(
        category=category,
        name="Margherita",
        slug="margherita",
        price=150_000,
        prep_time_minutes=10,
        is_main_dish=True,
    )


@pytest.fixture
def addon(db):
    from apps.catalog.models import AddOn

    return AddOn.objects.create(name="Extra Cheese", price=20_000)