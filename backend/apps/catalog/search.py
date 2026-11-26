"""
Query building for the public product catalog, backed by PostgreSQL.

This module owns *only* query construction for product discovery. Business
visibility rules (which products are publicly discoverable) live in
``apps.catalog.selectors.get_public_product_queryset``; both the product listing
and the autocomplete endpoint reuse this module so there is a single search
implementation.

Search strategy:
- ``SearchVector`` combines ``Product.name`` (weight A), ``Category.name``
  (weight B) and ``Product.description`` (weight C). Persian/Arabic letter
  variants and the food synonym dictionary expand each query word, so stored
  Arabic spellings still match a Persian query.
- ``TrigramSimilarity`` on the product name adds fuzzy/partial matches;
  autocomplete's prefix match is served by the ``gin_trgm_ops`` GIN index.
- Relevance is the sum of the weighted full-text rank and the trigram
  similarity, so exact keyword and fuzzy matches rank naturally.

Data model notes (verified against ``apps/catalog/models.py``):
- ``Product.price`` is the effective selling price (integer toman) and is the
  value orders snapshot. ``Product.compare_at_price`` is the optional original
  price, so a discount never changes historical order totals.
- Availability is manual: ``Product.status`` is the only source of truth and
  the project intentionally does not track numeric stock quantities.
- There are no variant, SKU, tag or ingredient fields. Filters that would need
  them are not offered here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from django.conf import settings
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db.models import (
    F,
    FloatField,
    IntegerField,
    Q,
    QuerySet,
    Sum,
    Value,
)
from django.db.models.expressions import ExpressionWrapper
from django.db.models.functions import Coalesce

from .models import Product
from .normalization import (
    ARABIC_KAF,
    ARABIC_YEH,
    MAX_SEARCH_LENGTH,
    PERSIAN_KAF,
    PERSIAN_YEH,
    normalize_search_query,
    tokenize_search_query,
)

MAX_PRICE_FILTER = 1_000_000_000  # 1e9 toman; keeps filter values bounded

#: PostgreSQL has no built-in Persian text-search configuration, so the
#: language-agnostic ``simple`` configuration is used for stemming/stopwords.
#: Matching is still exact-word; trigram similarity covers partial spellings.
SEARCH_CONFIG = "simple"

#: Trigram matching is only meaningful once a query has at least two characters.
TRIGRAM_MIN_QUERY_LENGTH = 2

#: Default catalog order, mirroring ``Product.Meta.ordering`` plus a deterministic
#: tie-breaker so pagination is stable.
DEFAULT_ORDERING = ("display_order", "name", "pk")

#: Relevance ordering requires the ``search_score``/``search_similarity``
#: annotations added by ``apply_search``.
RELEVANCE_ORDERING = ("-search_score", "display_order", "name", "pk")

#: Autocomplete ranking: closest name first, then the best-selling products.
AUTOCOMPLETE_ORDERING = (
    "-search_similarity",
    "-sales_count",
    "display_order",
    "name",
    "pk",
)

#: Explicit allowlist — client input never reaches ``order_by`` unfiltered.
SORT_ORDERINGS: dict[str, tuple[str, ...]] = {
    "default": DEFAULT_ORDERING,
    "newest": ("-created_at", "-pk"),
    "oldest": ("created_at", "pk"),
    "price_asc": ("price", "display_order", "pk"),
    "price_desc": ("-price", "display_order", "pk"),
}

SORT_CHOICES = ("relevance", "popularity") + tuple(SORT_ORDERINGS)

#: Only orders whose money was actually captured count as sales. A refunded or
#: canceled order changes ``payment_status``, so it automatically drops out.
POPULARITY_PAYMENT_STATUS = "PAID"
POPULARITY_ORDER_STATUSES = ("PROCESSING", "READY", "COMPLETED")

#: Persian food synonyms. Groups are expanded in both directions, so searching
#: any member of a group also finds products named with the other members.
#: Deliberately small and domain-specific; extend via
#: ``settings.CATALOG_SEARCH_SYNONYMS`` instead of editing the code.
SYNONYM_GROUPS: tuple[tuple[str, ...], ...] = (
    ("برگر", "همبرگر"),
    ("مرغ", "چیکن", "جوجه"),
    ("نوشابه", "نوشیدنی", "کوکاکولا", "کوکا", "پپسی"),
    ("سیبزمینی", "فرای", "فریز"),
    ("سوسیس", "هاتداگ"),
    ("پنیر", "چیز"),
    ("قارچ", "ماشروم"),
    ("میگو", "shrimp"),
)


# ---------------------------------------------------------------------------
# Normalization (re-exported for callers/tests that import it from here)
# ---------------------------------------------------------------------------
__all__ = [
    "AUTOCOMPLETE_ORDERING",
    "MAX_PRICE_FILTER",
    "MAX_SEARCH_LENGTH",
    "RELEVANCE_ORDERING",
    "SEARCH_CONFIG",
    "SORT_CHOICES",
    "apply_autocomplete",
    "apply_filters",
    "apply_ordering",
    "apply_search",
    "build_relevance_ordering",
    "build_search_filter",
    "normalize_search_query",
    "search_variants",
    "tokenize_search_query",
]


def search_variants(term: str) -> list[str]:
    """
    Return the term plus its Arabic-letter spellings.

    Stored product data is never rewritten, so a query using Persian ی/ک must
    still match rows that were entered with Arabic ي/ك (and vice versa).
    """
    if not term:
        return []

    variants = {term}
    if PERSIAN_YEH in term or PERSIAN_KAF in term:
        variants.add(term.replace(PERSIAN_YEH, ARABIC_YEH))
        variants.add(term.replace(PERSIAN_KAF, ARABIC_KAF))
        variants.add(
            term.replace(PERSIAN_YEH, ARABIC_YEH).replace(PERSIAN_KAF, ARABIC_KAF)
        )
    return sorted(variant for variant in variants if variant)


@lru_cache(maxsize=1)
def _synonym_map() -> dict[str, tuple[str, ...]]:
    """Build the bidirectional synonym map (code groups + settings overrides)."""
    mapping: dict[str, set[str]] = {}

    groups: list[Sequence[str]] = list(SYNONYM_GROUPS)
    overrides = getattr(settings, "CATALOG_SEARCH_SYNONYMS", None) or {}
    for key, values in overrides.items():
        groups.append((key, *values))

    for group in groups:
        normalized = {
            normalize_search_query(member).lower()
            for member in group
            if normalize_search_query(member)
        }
        for member in normalized:
            mapping.setdefault(member, set()).update(normalized - {member})

    return {key: tuple(sorted(values)) for key, values in mapping.items()}


def _expand_token(token: str) -> list[str]:
    """All spellings/synonyms of a single word, capped to bound the query."""
    expanded: list[str] = []
    for variant in search_variants(token):
        expanded.append(variant)
        expanded.extend(_synonym_map().get(variant.lower(), ()))

    # Preserve order while removing duplicates; 8 candidates per token is plenty.
    seen: set[str] = set()
    result: list[str] = []
    for candidate in expanded:
        candidate = candidate.lower()
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result[:8]


def _similarity_threshold() -> float:
    return float(getattr(settings, "CATALOG_SEARCH_SIMILARITY_THRESHOLD", 0.2))


# ---------------------------------------------------------------------------
# Query building
# ---------------------------------------------------------------------------
def build_search_vector() -> SearchVector:
    """Weighted full-text vector over product name, category name and description."""
    return (
        SearchVector("name", weight="A", config=SEARCH_CONFIG)
        + SearchVector("category__name", weight="B", config=SEARCH_CONFIG)
        + SearchVector("description", weight="C", config=SEARCH_CONFIG)
    )


def _token_query(token: str) -> Q:
    """OR every spelling/synonym of one query word against the search vector."""
    query = Q()
    for alternative in _expand_token(token):
        query |= Q(search_vector=SearchQuery(alternative, config=SEARCH_CONFIG))
    return query


def build_search_filter(term: str) -> Q:
    """
    Build a word-AND full-text filter over the ``search_vector`` annotation.

    Every query word must match at least one weighted field (or a synonym of
    that word). A query without words produces an empty ``Q`` (no filtering).
    """
    tokens = tokenize_search_query(term)
    if not tokens:
        return Q()

    combined = Q()
    for token in tokens:
        combined &= _token_query(token)
    return combined


def apply_search(queryset: QuerySet[Product], term: str) -> QuerySet[Product]:
    """
    Annotate and filter a queryset with PostgreSQL full-text + trigram search.

    The filter accepts either a weighted full-text match or a product name that
    is trigram-similar to the query (or contains it as a substring), so exact
    words, Persian/Arabic variants, synonyms and partial/fuzzy spellings all
    return rows. ``search_score`` combines both signals for relevance ordering.
    """
    queryset = queryset.annotate(search_vector=build_search_vector())
    queryset = queryset.annotate(
        search_rank=SearchRank(
            F("search_vector"), SearchQuery(term, config=SEARCH_CONFIG)
        ),
        search_similarity=TrigramSimilarity("name", term),
    )
    queryset = queryset.annotate(
        search_score=ExpressionWrapper(
            F("search_rank") + F("search_similarity"),
            output_field=FloatField(),
        )
    )

    match = build_search_filter(term) | Q(name__icontains=term)
    if len(term) >= TRIGRAM_MIN_QUERY_LENGTH:
        match |= Q(search_similarity__gte=_similarity_threshold())
    return queryset.filter(match)


def apply_autocomplete(
    queryset: QuerySet[Product], term: str
) -> QuerySet[Product]:
    """
    Filter/annotate an autocomplete queryset using trigram similarity and prefix.

    ``name__istartswith`` is served by the trigram GIN index, while
    ``TrigramSimilarity`` catches typos. Synonyms of the whole term are also
    accepted as prefixes. ``search_similarity`` drives the ordering.
    """
    queryset = queryset.annotate(search_similarity=TrigramSimilarity("name", term))

    prefix = Q()
    for candidate in search_variants(term):
        prefix |= Q(name__istartswith=candidate)
        for synonym in _synonym_map().get(candidate.lower(), ()):
            prefix |= Q(name__istartswith=synonym)

    match = prefix
    if len(term) >= TRIGRAM_MIN_QUERY_LENGTH:
        match |= Q(search_similarity__gte=_similarity_threshold())
    return queryset.filter(match)


def build_relevance_ordering() -> tuple[str, ...]:
    """Ordering that ranks combined full-text/trigram relevance first."""
    return RELEVANCE_ORDERING


# ---------------------------------------------------------------------------
# Filters & ordering
# ---------------------------------------------------------------------------
def apply_filters(
    queryset: QuerySet[Product],
    *,
    category_slug: str | None = None,
    category_id: int | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    available: bool | None = None,
    discount: bool | None = None,
    is_main_dish: bool | None = None,
) -> QuerySet[Product]:
    """
    Apply the supported catalog filters.

    - ``available`` is the manual status flag (``True`` → AVAILABLE,
      ``False`` → OUT_OF_STOCK).
    - ``discount`` is derived from ``compare_at_price > price``.
    - Categories are flat, so filtering is by one slug or one id.
    """
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    if category_id is not None:
        queryset = queryset.filter(category_id=category_id)

    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)

    if available is True:
        queryset = queryset.filter(status=Product.Status.AVAILABLE)
    elif available is False:
        queryset = queryset.filter(status=Product.Status.OUT_OF_STOCK)

    if discount is True:
        queryset = queryset.filter(compare_at_price__gt=F("price"))
    elif discount is False:
        queryset = queryset.filter(
            Q(compare_at_price__isnull=True) | Q(compare_at_price__lte=F("price"))
        )

    if is_main_dish is not None:
        queryset = queryset.filter(is_main_dish=is_main_dish)

    return queryset


def annotate_sales_count(queryset: QuerySet[Product]) -> QuerySet[Product]:
    """
    Annotate ``sales_count`` from captured (PAID) order items.

    A single LEFT JOIN + GROUP BY on the primary key keeps the queryset
    pageable and avoids N+1 queries. ``Coalesce`` turns products without sales
    into ``0`` so ordering is deterministic.
    """
    sales = Coalesce(
        Sum(
            "order_items__quantity",
            filter=Q(
                order_items__order__payment_status=POPULARITY_PAYMENT_STATUS,
                order_items__order__status__in=POPULARITY_ORDER_STATUSES,
                order_items__order__deleted_at__isnull=True,
            ),
        ),
        Value(0),
        output_field=IntegerField(),
    )
    return queryset.annotate(sales_count=sales)


def apply_ordering(
    queryset: QuerySet[Product],
    *,
    sort: str | None,
    term: str,
) -> QuerySet[Product]:
    """
    Order by an allowlisted strategy.

    When a search term is present and no sort is requested (or ``relevance`` is
    requested), relevance wins. ``sort=relevance`` without a term falls back to
    the default catalog order. Unknown values also fall back to the default;
    API-level validation rejects them before they reach this function.
    """
    if sort == "relevance" or (not sort and term):
        if term:
            return queryset.order_by(*build_relevance_ordering())
        sort = "default"

    if sort == "popularity":
        return annotate_sales_count(queryset).order_by(
            "-sales_count", *DEFAULT_ORDERING
        )

    ordering = SORT_ORDERINGS.get(sort or "default", DEFAULT_ORDERING)
    return queryset.order_by(*ordering)
