from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_alter_category_options_and_more"),
    ]

    operations = [
        # Required by the gin_trgm_ops GIN indexes and TrigramSimilarity lookups
        # in catalog search. Reversible: the reverse operation drops the extension.
        TrigramExtension(),
    ]
