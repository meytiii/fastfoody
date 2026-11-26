"""Pure Persian/Arabic text normalization shared by catalog search.

This module deliberately has no Django imports so migrations and selectors can
import it safely. Stored data is never rewritten; only the user query is
normalized, while ``search_variants`` supplies the alternative Persian/Arabic
spellings used to build search queries against PostgreSQL full-text indexes.
"""

from __future__ import annotations

import re
import string
from typing import Any

MAX_SEARCH_LENGTH = 100
MAX_SEARCH_TOKENS = 8

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
#: Punctuation trimmed from the edges of a word before matching.
_EDGE_PUNCTUATION = string.punctuation + "،؛؟»«…ـ"


def normalize_search_query(raw: Any) -> str:
    """
    Normalize a user-supplied search term without touching stored data.

    - Arabic Yeh/Kaf are folded to their Persian forms.
    - Arabic-Indic and Persian digits become ASCII digits.
    - Zero-width/invisible characters are removed and whitespace is collapsed.
    - The result is trimmed and truncated to ``MAX_SEARCH_LENGTH``.

    Case is intentionally left as-is here; PostgreSQL full-text search and
    trigram matching are case-insensitive.
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
