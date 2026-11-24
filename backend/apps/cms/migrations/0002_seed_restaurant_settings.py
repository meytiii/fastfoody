from __future__ import annotations

from django.db import migrations


def seed_restaurant_settings(apps, schema_editor):
    """
    Ensure the pk=1 singleton exists on a fresh database.

    Order creation, payment start and the storefront status endpoint all read
    this row; without it a newly migrated deployment raised DoesNotExist (500).
    ``get_or_create`` keeps the migration safe to run on databases that already
    have the row.
    """
    RestaurantSettings = apps.get_model("cms", "RestaurantSettings")
    RestaurantSettings.objects.get_or_create(pk=1)


def unseed_restaurant_settings(apps, schema_editor):
    # Intentionally keep the row when migrating backwards: removing it would
    # break any existing order/payment code that assumes the singleton.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_restaurant_settings,
            reverse_code=unseed_restaurant_settings,
        ),
    ]
