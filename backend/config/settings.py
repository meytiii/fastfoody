from __future__ import annotations

from pathlib import Path

from decouple import config
from kombu import Queue

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-change-me")
DEBUG = config("DEBUG", default=False, cast=bool)

_allowed_hosts = config("ALLOWED_HOSTS", default="127.0.0.1,localhost")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "common",
    "apps.accounts",
    "apps.cms",
    "apps.catalog",
    "apps.orders",
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

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
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
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "otp_request": "5/hour",
        "otp_verify": "10/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FastFood Backend API",
    "DESCRIPTION": "Storefront and Backoffice APIs for a single-location fast-food restaurant.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
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
}



MANAGER_PHONE = config("MANAGER_PHONE", default="")



ZARINPAL_MERCHANT_ID = config("ZARINPAL_MERCHANT_ID", default="")
ZARINPAL_CALLBACK_URL = config("ZARINPAL_CALLBACK_URL", default="")
ZARINPAL_SANDBOX = config("ZARINPAL_SANDBOX", default=True, cast=bool)

SMS_IR_API_KEY = config("SMS_IR_API_KEY", default="")
SMS_IR_SENDER = config("SMS_IR_SENDER", default="")

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