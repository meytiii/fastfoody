"""Rebuild the catalog search inverted index.

Run after bulk product imports/edits that bypass the catalog services:

    python manage.py rebuild_search_index
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.catalog.indexing import rebuild_all_search_indexes


class Command(BaseCommand):
    help = "Rebuild ProductSearchToken rows for every product."

    def handle(self, *args, **options) -> None:
        count = rebuild_all_search_indexes()
        self.stdout.write(
            self.style.SUCCESS(f"Search index rebuilt for {count} products.")
        )
