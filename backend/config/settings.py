from __future__ import annotations

import json
from pathlib import Path

from decouple import config
from kombu import Queue
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-change-me")
# Development defaults to DEBUG=True; production must set DEBUG=False in the env,
# which activates the security block at the bottom of this file.
DEBUG = config("DEBUG", default=True, cast=bool)

_allowed_hosts = config("ALLOWED_HOSTS", default="127.0.0.1,localhost")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework",
    "drf_spectacular",
    "common",
    "apps.accounts",
    "apps.cms",
    "apps.catalog",
    "apps.orders",
    "apps.payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL is the only supported backend
# ---------------------------------------------------------------------------
# The catalog relies on PostgreSQL-native full-text search and pg_trgm, so there
# is deliberately no SQLite fallback. Every value comes from the environment;
# see .env.example for the defaults used by local development.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="fastfood"),
        "USER": config("POSTGRES_USER", default="fastfood"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="fastfood"),
        "HOST": config("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": config("POSTGRES_PORT", default=5432, cast=int),
        "CONN_MAX_AGE": 60,
    }
}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
# REDIS_URL is declared as a real setting because common/redis_client.py reads
# settings.REDIS_URL. It is also the single source for the Redis cache backend
# and for Celery's default broker URLs.
REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/0")

# Development uses the in-process cache; a non-DEBUG deployment keeps the
# production expectation (Redis) unless explicitly overridden.
if config("CACHE_BACKEND", default="locmem" if DEBUG else "redis") == "redis":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "KEY_PREFIX": "fastfood",
        }
    }
else:
    # Local development default: no external service is required for the API to
    # boot. Set CACHE_BACKEND=redis (and REDIS_URL) to mirror production.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "fastfood-dev",
            "KEY_PREFIX": "fastfood",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.Customer"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exception_handler.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,

    # Intentionally no DEFAULT_AUTHENTICATION_CLASSES.
    #
    # Authentication is chosen explicitly per surface:
    #   * Storefront views use JWTAuthentication only (common.views.StorefrontAPIView).
    #   * Backoffice views use SessionAuthentication only (common.views.BackofficeAPIView).
    # This keeps DRF from running CSRF checks on JWT endpoints and keeps a
    # customer JWT from ever authenticating a staff endpoint.

    "DEFAULT_THROTTLE_RATES": {
        "otp_request": "5/hour",
        "otp_verify": "10/hour",
        "staff_login": "10/hour",
        "catalog_search": "120/min",
        "catalog_suggest": "120/min",
    },
}



SIMPLE_JWT = {

    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_LIFETIME_MINUTES", default=60, cast=int)
    ),

    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_LIFETIME_DAYS", default=7, cast=int)
    ),

    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,   # staff login records last_login explicitly
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
}







SPECTACULAR_SETTINGS = {
    "TITLE": "FastFood Backend API",
    "DESCRIPTION": (
        "Storefront and Backoffice APIs for a single-location fast-food "
        "restaurant. Storefront docs are public. Backoffice docs require "
        "a staff session (login at /api/v1/backoffice/auth/login/)."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # Stable enum component names; several models define a nested ``Status``
    # choice class, which would otherwise collide in the generated schema.
    "ENUM_NAME_OVERRIDES": {
        "ProductStatusEnum": "apps.catalog.models.Product.Status",
        "OrderStatusEnum": "apps.orders.models.Order.Status",
        "OrderPaymentStatusEnum": "apps.orders.models.Order.PaymentStatus",
        "OrderDeliveryTypeEnum": "apps.orders.models.Order.DeliveryType",
        "PaymentStatusEnum": "apps.payments.models.Payment.Status",
    },
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = config(
    "CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/2"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = (
    Queue("default"),
    Queue("high_priority"),
)
CELERY_TASK_ROUTES = {
    "apps.accounts.tasks.send_otp_sms": {"queue": "high_priority"},
    "apps.orders.tasks.send_order_registered_sms": {"queue": "high_priority"},
    "apps.orders.tasks.send_order_ready_sms": {"queue": "high_priority"},
    "apps.orders.tasks.send_prep_time_changed_sms": {"queue": "high_priority"},
}

CELERY_BEAT_SCHEDULE = {
    "cancel-expired-unpaid-orders": {
        "task": "apps.orders.tasks.cancel_expired_unpaid_orders",
        "schedule": 60.0,
    },
    "reverify-pending-payments": {
        "task": "apps.payments.tasks.reverify_pending_payments",
        "schedule": 300.0,  # every 5 minutes
    },

}


# Inline task execution is a development convenience only; it follows DEBUG so a
# deployed environment does not run SMS/HTTP calls inside the web process.
CELERY_TASK_ALWAYS_EAGER = config(
    "CELERY_TASK_ALWAYS_EAGER", default=DEBUG, cast=bool
)
CELERY_TASK_EAGER_PROPAGATES = True


MANAGER_PHONE = config("MANAGER_PHONE", default="")


# Product autocomplete limits (see apps/catalog/apis/storefront/views.py).
# The requested `limit` is clamped to PRODUCT_SUGGESTIONS_MAX_LIMIT.
PRODUCT_SUGGESTIONS_DEFAULT_LIMIT = 5
PRODUCT_SUGGESTIONS_MAX_LIMIT = 10


# ---------------------------------------------------------------------------
# Catalog search
# ---------------------------------------------------------------------------
# Extra synonym pairs/groups, merged with the built-in Persian food synonyms:
#   CATALOG_SEARCH_SYNONYMS={"برگر": ["همبرگر"], "نوشابه": ["کوکاکولا"]}
# Values are read once at startup (apps/catalog/search.py).
_raw_synonyms = config("CATALOG_SEARCH_SYNONYMS", default="").strip()
CATALOG_SEARCH_SYNONYMS: dict[str, list[str]] = (
    json.loads(_raw_synonyms) if _raw_synonyms else {}
)
if not isinstance(CATALOG_SEARCH_SYNONYMS, dict):
    raise ValueError("CATALOG_SEARCH_SYNONYMS must be a JSON object.")

# Minimum pg_trgm similarity for fuzzy matches. Search uses it to keep partial
# matches alongside full-text hits; autocomplete uses it for typo tolerance and
# "did you mean" uses the (slightly stricter) threshold below.
CATALOG_SEARCH_SIMILARITY_THRESHOLD = config(
    "CATALOG_SEARCH_SIMILARITY_THRESHOLD", default=0.2, cast=float
)
CATALOG_DID_YOU_MEAN_THRESHOLD = config(
    "CATALOG_DID_YOU_MEAN_THRESHOLD", default=0.25, cast=float
)

# Cached search/autocomplete responses. Keys include the normalized query, all
# filters, sorting and pagination, plus a catalog generation that is bumped by
# every catalog write (see apps/catalog/cache.py).
CATALOG_SEARCH_CACHE_ENABLED = config(
    "CATALOG_SEARCH_CACHE_ENABLED", default=True, cast=bool
)
CATALOG_SEARCH_CACHE_TTL = config("CATALOG_SEARCH_CACHE_TTL", default=60, cast=int)
CATALOG_SUGGEST_CACHE_ENABLED = config(
    "CATALOG_SUGGEST_CACHE_ENABLED", default=True, cast=bool
)
CATALOG_SUGGEST_CACHE_TTL = config("CATALOG_SUGGEST_CACHE_TTL", default=120, cast=int)



# Zarinpal
ZARINPAL_MERCHANT_ID = config("ZARINPAL_MERCHANT_ID", default="")

ZARINPAL_CALLBACK_URL = config(
    "ZARINPAL_CALLBACK_URL",
    default="http://127.0.0.1:8000/api/v1/storefront/payments/callback/",
)

ZARINPAL_SANDBOX = config("ZARINPAL_SANDBOX", default=True, cast=bool)


# Where the browser lands after callback (frontend URL)
PAYMENT_FRONTEND_RESULT_URL = config(
    "PAYMENT_FRONTEND_RESULT_URL",
    default="http://127.0.0.1:3000/payment/result",
)


SMS_IR_API_KEY = config("SMS_IR_API_KEY", default="")
SMS_IR_SENDER = config("SMS_IR_SENDER", default="")




if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
    CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31_536_000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True





LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
}