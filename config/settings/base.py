"""
Django base settings for config project.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

# ─────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-development-key")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

APPEND_SLASH = True

# ─────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_prometheus",
    "django_celery_results",
    "django_celery_beat",
    "axes",
]

# SHARED_APPS: tables live in the *public* schema and are accessible from every
# tenant schema.  django_tenants itself MUST be first.  The `products` app
# (which owns the Client/Domain models) MUST also be shared so that the tenant
# router can resolve tenants before any per-tenant schema is activated.
#
# apps.tenants (our internal tenants app) belongs here too: it manages tenant
# lifecycle and must be queryable from the public schema.
SHARED_APPS = tuple(
    [
        "django_tenants",  # must be first
        "products",  # owns Client + Domain — must be shared
    ]
    + DJANGO_APPS
    + THIRD_PARTY_APPS
    + [
        "apps.tenants",  # tenant-management app — lives in public schema
    ]
)

# TENANT_APPS: apps whose tables are created *per tenant schema*.
# Do NOT put apps.tenants here — it belongs in SHARED_APPS (see above).
TENANT_APPS = [
    "apps.core",
    "apps.api",
    "apps.monitoring",
]

# INSTALLED_APPS = union of SHARED_APPS + TENANT_APPS (no duplicates).
# List order is preserved; SHARED_APPS entries come first.
INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# ─────────────────────────────────────────────────
# DJANGO-TENANTS
# ─────────────────────────────────────────────────
TENANT_MODEL = "products.Client"
TENANT_DOMAIN_MODEL = "products.Domain"

TENANT_CACHE_BACKEND = "default"
TENANT_CACHE_SECONDS = 300

# ─────────────────────────────────────────────────
# MIDDLEWARE
# Order matters:
#   1. PrometheusBeforeMiddleware  — wraps everything for metrics
#   2. TenantMiddlewareWithHealthCheck — activates tenant schema early;
#      health-check paths bypass tenant resolution so the DB doesn't need to
#      be up for /health/.
#   3. Standard Django middleware stack.
#   4. AxesMiddleware — MUST come after AuthenticationMiddleware.
#   5. PrometheusAfterMiddleware — closes the metrics wrap.
# ─────────────────────────────────────────────────
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "apps.core.middleware.TenantMiddlewareWithHealthCheck",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # must be after AuthenticationMiddleware ✓
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ─────────────────────────────────────────────────
# DATABASE
# django_tenants requires its own postgresql backend.  The public schema is
# used for all SHARED_APPS tables (including products_client / products_domain).
# ─────────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        engine="django_tenants.postgresql_backend",
    )
}

# Explicitly name the public schema so django_tenants knows where shared tables
# live.  This must match get_public_schema_name() (default: "public").
DATABASES["default"]["SCHEMA"] = "public"

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# ─────────────────────────────────────────────────
# CACHE
# ─────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ─────────────────────────────────────────────────
# CELERY
# ─────────────────────────────────────────────────
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ─────────────────────────────────────────────────
# AUTH & PASSWORD VALIDATION
# ─────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────────
# REST FRAMEWORK
# ─────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ─────────────────────────────────────────────────
# INTERNATIONALISATION
# ─────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────
# STATIC & MEDIA
# ─────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─────────────────────────────────────────────────
# DEFAULT PRIMARY KEY
# ─────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "axes": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}

# ─────────────────────────────────────────────────
# ENVIRONMENT
# ─────────────────────────────────────────────────
ENVIRONMENT = config("ENVIRONMENT", default="dev")

# ─────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ─────────────────────────────────────────────────
# DJANGO-AXES (brute force protection)
# ─────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"
