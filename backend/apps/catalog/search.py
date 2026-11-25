"""
Reusable search / filtering / sorting helpers for the public product catalog.

This module owns *only* query construction for product discovery. Business
visibility rules (which products are publicly discoverable) live in
``apps.catalog.selectors.get_public_product_queryset``; both the product listing
and the autocomplete endpoint reuse this module so there is a single search
implementation.

Data model notes (verified against ``apps/catalog/models.py``):
- ``Product.price`` is the effective selling price (integer toman) and is the
  value orders snapshot. ``Product.compare_at_price`` is the optional original
  price, so a discount never changes historical order totals.
- Availability is manual: ``Product.status`` is the only source of truth and
  the project intentionally does not track numeric stock quantities.
- Search matching goes through ``ProductSearchToken`` (an indexed inverted
  index) rather than leading-wildcard ``icontains`` scans.
- There are no variant, SKU, tag or ingredient fields. Filters that would need
  them are not offered here.
"""

from __future__ import annotations

import difflib
from functools import lru_cache
from typing import Any, Sequence

from django.conf import settings
from django.db.models import (
    Case,
    F,
    IntegerField,
    Q,
    QuerySet,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from .models import Product, ProductSearchToken
from .search_index import (
    ARABIC_KAF,
    ARABIC_YEH,
    MAX_SEARCH_LENGTH,
    MAX_SEARCH_TOKENS,
    PERSIAN_KAF,
    PERSIAN_YEH,
    TOKEN_MAX_LENGTH,
    normalize_search_query,
    tokenize_search_query,
)

MAX_PRICE_FILTER = 1_000_000_000  # 1e9 toman; guards SQLite integer overflow

#: Default catalog order, mirroring ``Product.Meta.ordering`` plus a deterministic
#: tie-breaker so pagination is stable.
DEFAULT_ORDERING = ("display_order", "name", "pk")

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

# Tolerance for the autocomplete fallback: a query word is replaced only by a
# product-name word that is this similar (difflib ratio, 0..1).
FUZZY_MIN_TOKEN_LENGTH = 3


# ---------------------------------------------------------------------------
# Normalization (re-exported for callers/tests that import it from here)
# ---------------------------------------------------------------------------
__all__ = [
    "MAX_PRICE_FILTER",
    "MAX_SEARCH_LENGTH",
    "SORT_CHOICES",
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
    """All spellings/synonyms of a single word, capped to bound the lookup."""
    expanded: list[str] = []
    for variant in search_variants(token):
        expanded.append(variant)
        expanded.extend(_synonym_map().get(variant.lower(), ()))

    # Preserve order while removing duplicates; 8 candidates per token is plenty.
    seen: set[str] = set()
    result: list[str] = []
    for candidate in expanded:
        candidate = candidate.lower()[:TOKEN_MAX_LENGTH]
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result[:8]


# ---------------------------------------------------------------------------
# Query building
# ---------------------------------------------------------------------------
def build_search_filter(term: str) -> Q:
    """
    Build a token-AND search filter backed by ``ProductSearchToken``.

    Every query word must match at least one indexed token (or a synonym of
    that word). Each word becomes a ``pk__in`` subquery over the token index, so
    the planner starts from ``catalog_search_token_idx`` and reads only the
    matching products instead of scanning the product table with
    ``LIKE '%...%'``. Word subqueries are AND-ed; the inner ``DISTINCT`` keeps
    the id lists duplicate-free.

    A query without words produces an empty ``Q`` (no filtering).
    """
    tokens = tokenize_search_query(term)
    if not tokens:
        return Q()

    combined = Q()
    for token in tokens:
        # Drive the query from the token index (indexed ``token`` lookups) and
        # intersect the resulting product ids, instead of scanning products and
        # probing the index once per row.
        matches = (
            ProductSearchToken.objects.filter(token__in=_expand_token(token))
            .values("product_id")
            .distinct()
        )
        combined &= Q(pk__in=matches)
    return combined


def build_relevance_ordering(term: str) -> list[Any]:
    """
    Rank: exact name > name prefix > name substring > slug/category/description.

    Ties fall back to the default catalog order, so relevance never produces
    unstable pagination.
    """
    exact = Q()
    prefix = Q()
    name_partial = Q()
    related_partial = Q()

    for variant in search_variants(term):
        exact |= Q(name__iexact=variant)
        prefix |= Q(name__istartswith=variant)
        name_partial |= Q(name__icontains=variant)
        related_partial |= (
            Q(slug__icontains=variant)
            | Q(category__name__icontains=variant)
            | Q(description__icontains=variant)
        )

    score = Case(
        When(exact, then=Value(5)),
        When(prefix, then=Value(4)),
        When(name_partial, then=Value(3)),
        When(related_partial, then=Value(2)),
        default=Value(0),
        output_field=IntegerField(),
    )
    return [score.desc(), "display_order", "name", "pk"]


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
            return queryset.order_by(*build_relevance_ordering(term))
        sort = "default"

    if sort == "popularity":
        return annotate_sales_count(queryset).order_by(
            "-sales_count", *DEFAULT_ORDERING
        )

    ordering = SORT_ORDERINGS.get(sort or "default", DEFAULT_ORDERING)
    return queryset.order_by(*ordering)


# ---------------------------------------------------------------------------
# Typo tolerance (bounded, autocomplete-only fallback)
# ---------------------------------------------------------------------------
def correct_search_term(
    term: str,
    vocabulary: Sequence[str],
    *,
    cutoff: float | None = None,
) -> str | None:
    """
    Return ``term`` with misspelled words replaced by close vocabulary words.

    ``difflib`` performs a Levenshtein-like ratio comparison in Python. The
    vocabulary is built from product names only (see
    ``selectors.get_search_vocabulary``) and the caller applies this to at most
    one query, only when the exact search found nothing — so no per-request scan
    of the catalog happens on the normal path.

    Returns ``None`` when no word can be corrected.
    """
    tokens = tokenize_search_query(term)
    if not tokens or not vocabulary:
        return None

    threshold = (
        cutoff
        if cutoff is not None
        else getattr(settings, "CATALOG_SEARCH_FUZZY_CUTOFF", 0.8)
    )
    vocabulary_lower = [word.lower() for word in vocabulary]

    corrected: list[str] = []
    changed = False
    for token in tokens:
        if token.lower() in vocabulary_lower or len(token) < FUZZY_MIN_TOKEN_LENGTH:
            corrected.append(token)
            continue

        matches = difflib.get_close_matches(
            token.lower(), vocabulary_lower, n=1, cutoff=threshold
        )
        if matches:
            corrected.append(matches[0])
            changed = True
        else:
            corrected.append(token)

    return " ".join(corrected) if changed else None
