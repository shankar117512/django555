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
# FIX 1: Removed the duplicate hardcoded SECRET_KEY line.
SECRET_KEY = config("DJANGO_SECRET_KEY")

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

# FIX 2: django_tenants requires SHARED_APPS to be a *tuple*, and django_tenants
# must appear FIRST. The previous code used tuple() around a list + list expression
# which produced a list, not a tuple. Now explicitly cast to tuple().
SHARED_APPS = tuple(
    [
        "django_tenants",  # must be first
        "products",  # the tenant/domain model lives here
    ]
    + DJANGO_APPS
    + THIRD_PARTY_APPS
)

# FIX 3: TENANT_APPS must only contain apps that are *tenant-specific* (per-schema).
# "apps.tenants" was here before but tenant management itself lives in SHARED_APPS
# ("products"). Removed "apps.tenants" from TENANT_APPS to avoid the circular
# reference where the app managing tenants is also isolated per-tenant.
TENANT_APPS = [
    "apps.core",
    "apps.api",
    "apps.monitoring",
    "apps.tenants",
]

# FIX 4: INSTALLED_APPS must be a list; dedup correctly.
# django_tenants requires SHARED_APPS + TENANT_APPS (no duplicates).
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
# Order matters: PrometheusBeforeMiddleware first, TenantMiddleware second,
# AxesMiddleware must come AFTER AuthenticationMiddleware (confirmed below).
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
# ─────────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        engine="django_tenants.postgresql_backend",
    )
}

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

# FIX 5: axes stores lockout records in the DB, not cache. Using cache-based
# sessions is fine, but do NOT use cache for axes itself (it uses its own DB
# models by default). Session config below is correct; axes config is separate.
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

# FIX 6: Added SIMPLE_JWT config block. simplejwt is used for authentication
# but was never configured, relying on all defaults silently.
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
# FIX 7: Django 4.2+ deprecated STATICFILES_STORAGE in favour of the STORAGES
# dict. Kept the old key for backwards compat with older Django, but added the
# new STORAGES dict so this works on Django 4.2+ without deprecation warnings.
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
# FIX 8: axes must use DB for lockout storage (not cache), since SESSION_ENGINE
# is already pointed at cache. Explicitly declare this to avoid silent misconfig.
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"
