from __future__ import annotations

import pytest

from apps.catalog.models import Category
from common.exceptions import (
    BusinessException,
    NotFoundError,
    OrderStateError,
    PaymentError,
    PermissionDeniedError,
    RestaurantClosedError,
    ValidationError,
)


class TestSoftDelete:
    def test_soft_delete_hides_from_default_manager(self, db):
        cat = Category.objects.create(name="X", slug="x")
        cat.delete()
        assert Category.objects.filter(pk=cat.pk).exists() is False
        assert Category.all_objects.filter(pk=cat.pk).exists() is True

    def test_restore(self, db):
        cat = Category.objects.create(name="X", slug="x")
        cat.soft_delete()
        cat.restore()
        assert Category.objects.filter(pk=cat.pk).exists() is True

    def test_hard_delete(self, db):
        cat = Category.objects.create(name="X", slug="x")
        cat.hard_delete()
        assert Category.all_objects.filter(pk=cat.pk).exists() is False

    def test_alive_and_dead(self, db):
        Category.objects.create(name="A", slug="a")
        b = Category.objects.create(name="B", slug="b")
        b.delete()
        assert Category.objects.alive().count() == 1
        assert Category.objects.dead().count() == 1


class TestExceptions:
    def test_codes(self):
        assert OrderStateError().code == "INVALID_ORDER_STATE"
        assert NotFoundError().status_code == 404
        assert ValidationError().status_code == 422
        assert PermissionDeniedError().status_code == 403
        assert RestaurantClosedError().status_code == 409
        assert PaymentError().status_code == 402

    def test_overrides(self):
        exc = BusinessException(
            message="custom", code="C", details={"k": "v"}, status_code=418
        )
        assert exc.message == "custom"
        assert exc.code == "C"
        assert exc.details == {"k": "v"}
        assert exc.status_code == 418


class TestErrorEnvelope:
    def test_404_envelope(self, api_client, db):
        response = api_client.get(
            "/api/v1/storefront/cms/site-sections/bogus/"
        )
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "SITE_SECTION_NOT_FOUND"
        assert "message" in body["error"]