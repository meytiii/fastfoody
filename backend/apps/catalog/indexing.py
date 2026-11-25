"""Maintenance of the ``ProductSearchToken`` inverted index.

The index is derived data. It is refreshed synchronously after every catalog
write that can change a product's searchable text (product create/update and
category rename). Bulk imports should call the ``rebuild_search_index``
management command, or ``rebuild_all_search_indexes`` directly.
"""

from __future__ import annotations

from collections.abc import Iterable

from django.db import transaction

from .models import Product, ProductSearchToken
from .search_index import build_search_tokens


def _token_rows(product: Product) -> list[ProductSearchToken]:
    tokens = build_search_tokens(
        name=product.name,
        slug=product.slug,
        description=product.description,
        category_name=product.category.name,
    )
    return [
        ProductSearchToken(product=product, token=token, weight=weight)
        for token, weight in tokens.items()
    ]


def _refresh_batch(products: list[Product]) -> None:
    if not products:
        return
    product_ids = [product.pk for product in products]
    ProductSearchToken.objects.filter(product_id__in=product_ids).delete()
    rows: list[ProductSearchToken] = []
    for product in products:
        rows.extend(_token_rows(product))
    ProductSearchToken.objects.bulk_create(rows, batch_size=1000)


def refresh_product_search_index(product: Product) -> None:
    """Replace one product's index rows (call inside the write transaction)."""
    _refresh_batch([product])


def refresh_products_search_index(products: Iterable[Product]) -> int:
    """
    Replace the index for several products; returns the number refreshed.

    Work is batched (one delete + one bulk insert per 200 products) so renaming
    a category with a large product set does not issue two queries per row.
    """
    count = 0
    batch: list[Product] = []
    for product in products:
        batch.append(product)
        count += 1
        if len(batch) >= 200:
            _refresh_batch(batch)
            batch.clear()
    _refresh_batch(batch)
    return count


@transaction.atomic
def rebuild_all_search_indexes(*, batch_size: int = 500) -> int:
    """
    Rebuild the whole index. Intended for deployments and bulk imports.

    Existing rows are removed once, then products are processed in batches so
    a large catalog does not have to fit in memory.
    """
    ProductSearchToken.objects.all().delete()
    count = 0
    batch: list[ProductSearchToken] = []

    queryset = Product.objects.select_related("category").iterator(
        chunk_size=batch_size
    )
    for product in queryset:
        batch.extend(_token_rows(product))
        count += 1
        if len(batch) >= 5000:
            ProductSearchToken.objects.bulk_create(batch, batch_size=1000)
            batch.clear()

    if batch:
        ProductSearchToken.objects.bulk_create(batch, batch_size=1000)
    return count
