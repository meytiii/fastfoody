"""Pure text helpers shared by catalog search and the search index.

This module deliberately has no Django imports: migrations and the
``rebuild_search_index`` command import it, and keeping it dependency-free
avoids importing models during schema construction.

Two representations are produced from the same normalization:

* the user query is normalized and tokenized (max 8 words);
* each product contributes normalized words to ``ProductSearchToken``. Words
  from the product name and its category are also indexed under all prefixes
  (from two characters up to 24), so a partial query such as "پیتز" matches
  "پیتزا" through an exact, indexed token lookup instead of ``LIKE '%...%'``.
"""

from __future__ import annotations

import re
import string
from typing import Any

MAX_SEARCH_LENGTH = 100
MAX_SEARCH_TOKENS = 8

#: Shortest/longest prefix stored for name and category words. Capping the
#: prefix length keeps the number of rows per word bounded for long names.
TOKEN_MIN_PREFIX_LENGTH = 2
TOKEN_MAX_PREFIX_LENGTH = 24
#: Must match ``ProductSearchToken.token`` max_length.
TOKEN_MAX_LENGTH = 48

PERSIAN_YEH = "\u06cc"  # ی
ARABIC_YEH = "\u064a"  # ي
PERSIAN_KAF = "\u06a9"  # ک
ARABIC_KAF = "\u0643"  # ك

_ARABIC_INDIC_DIGITS = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
_EXTENDED_ARABIC_INDIC_DIGITS = (
    "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9"
)
_ASCII_DIGITS = "0123456789"
_DIGIT_TRANSLATION = str.maketrans(
    _ARABIC_INDIC_DIGITS + _EXTENDED_ARABIC_INDIC_DIGITS,
    _ASCII_DIGITS + _ASCII_DIGITS,
)

# Zero-width / directional marks that never carry meaning for matching.
_INVISIBLE_CHARS = (
    "\u200c",  # zero-width non-joiner (Persian half-space)
    "\u200d",  # zero-width joiner
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u0640",  # tatweel / kashida
)

_WHITESPACE_RE = re.compile(r"\s+")
#: Punctuation trimmed from the edges of a word before indexing/matching.
_EDGE_PUNCTUATION = string.punctuation + "،؛؟»«…ـ"


def normalize_search_query(raw: Any) -> str:
    """
    Normalize a user-supplied search term without touching stored data.

    - Arabic Yeh/Kaf are folded to their Persian forms.
    - Arabic-Indic and Persian digits become ASCII digits.
    - Zero-width/invisible characters are removed and whitespace is collapsed.
    - The result is trimmed and truncated to ``MAX_SEARCH_LENGTH``.

    Case is intentionally left as-is here; token storage and matching
    lower-case both sides.
    """
    if raw is None:
        return ""

    text = str(raw).translate(_DIGIT_TRANSLATION)
    text = text.replace(ARABIC_YEH, PERSIAN_YEH).replace(ARABIC_KAF, PERSIAN_KAF)
    for char in _INVISIBLE_CHARS:
        text = text.replace(char, "")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:MAX_SEARCH_LENGTH]


def _clean_word(word: str) -> str:
    """Trim edge punctuation left over after normalization."""
    return word.strip(_EDGE_PUNCTUATION).lower()


def tokenize_search_query(term: str) -> list[str]:
    """Split a normalized term into at most ``MAX_SEARCH_TOKENS`` words."""
    tokens = [_clean_word(token) for token in term.split(" ")]
    return [token for token in tokens if token][:MAX_SEARCH_TOKENS]


def iter_index_tokens(text: str) -> list[str]:
    """Normalized full words of a stored field (no prefixes)."""
    words = (
        _clean_word(word)
        for word in normalize_search_query(text).split(" ")
    )
    return [word[:TOKEN_MAX_LENGTH] for word in words if word]


def _with_prefixes(word: str) -> list[str]:
    """Full word plus every stored prefix (2..24 chars)."""
    word = word[:TOKEN_MAX_LENGTH]
    candidates = {word}
    upper = min(len(word), TOKEN_MAX_PREFIX_LENGTH)
    for length in range(TOKEN_MIN_PREFIX_LENGTH, upper):
        candidates.add(word[:length])
    return list(candidates)


def build_search_tokens(
    *,
    name: str,
    slug: str = "",
    description: str = "",
    category_name: str = "",
) -> dict[str, int]:
    """
    Return ``{token: weight}`` for one product.

    Name and category words are prefix-indexed (weight 3 and 2), while slug and
    description contribute full words only (weight 1). When the same token
    appears in several fields the highest weight wins.
    """
    tokens: dict[str, int] = {}

    def add(word: str, weight: int, *, prefixes: bool) -> None:
        candidates = _with_prefixes(word) if prefixes else [word[:TOKEN_MAX_LENGTH]]
        for candidate in candidates:
            if not candidate:
                continue
            if weight > tokens.get(candidate, 0):
                tokens[candidate] = weight

    for word in iter_index_tokens(name):
        add(word, 3, prefixes=True)

    for word in iter_index_tokens(category_name):
        add(word, 2, prefixes=True)

    # Slugs use hyphens instead of spaces; normalize them into words.
    for word in iter_index_tokens(slug.replace("-", " ").replace("_", " ")):
        add(word, 1, prefixes=False)

    for word in iter_index_tokens(description):
        add(word, 1, prefixes=False)

    return tokens
