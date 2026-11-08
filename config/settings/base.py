"""
Settings shared by every environment.

Environment-specific values live in dev.py and prod.py; secrets and
host-specific values are read from environment variables (or a .env file)
with python-decouple.
"""

from pathlib import Path

from decouple import Csv, config as env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = False

ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Redis stores the short code -> long url mappings
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")


# Application definition

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    # Local
    "shortener",
]

MIDDLEWARE = [
    "core.middleware.RequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
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
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# All data lives in Redis, so no relational database is configured
DATABASES = {}


# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # The API is public: no users, sessions or auth tables
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
}


# OpenAPI 3 schema + Swagger UI (drf-spectacular)

SPECTACULAR_SETTINGS = {
    "TITLE": "URL Shortener API",
    "DESCRIPTION": "Shorten long urls and resolve short codes back to them.",
    "VERSION": "1.0.0",
}


# Logging

LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        # Replace Django's default handlers so each record is printed once
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        # The request logging middleware already logs every request,
        # so Django's own per-request logs only report server errors
        "django.server": {"level": "ERROR"},
        "django.request": {"level": "ERROR"},
    },
}
