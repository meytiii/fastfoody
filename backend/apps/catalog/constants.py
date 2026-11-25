from __future__ import annotations

from common.cache import make_cache_key

CACHE_KEY_MENU = make_cache_key("catalog", "storefront_menu")
CACHE_KEY_LUCKY_WHEEL = make_cache_key("catalog", "lucky_wheel")
CACHE_KEY_SEARCH_VOCAB = make_cache_key("catalog", "search_vocab")
CACHE_KEY_UPSELL = make_cache_key("catalog", "upsell")
CACHE_TIMEOUT_SECONDS = 60 * 60