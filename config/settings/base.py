"""
Django settings for config project.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────────
# AUTO-LOAD THE CORRECT .env FILE
# ─────────────────────────────────────────────────
_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.base")
_env_map = {
    "config.settings.staging": BASE_DIR / "envs" / ".env.staging",
    "config.settings.test": BASE_DIR / "envs" / ".env.test",
    "config.settings.production": BASE_DIR / "envs" / ".env.production",
}
_env_file = _env_map.get(_settings_module)
if _env_file and _env_file.exists():
    from decouple import Config, RepositoryEnv

    config = Config(RepositoryEnv(str(_env_file)))


SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="django-insecure-^+4yk+i8d=9$l07#tj=+-0au3_pc7t$ft5l=p_+^ydeot_*&-=",
)

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

APPEND_SLASH = True

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

SHARED_APPS = (
    [
        "django_tenants",
        "products",
    ]
    + DJANGO_APPS
    + THIRD_PARTY_APPS
)

TENANT_APPS = [
    "apps.core",
    "apps.api",
    "apps.tenants",
    "apps.monitoring",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = "products.Client"
TENANT_DOMAIN_MODEL = "products.Domain"
TENANT_CACHE_BACKEND = "default"
TENANT_CACHE_SECONDS = 300

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
    "axes.middleware.AxesMiddleware",
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
        default=config("DATABASE_URL", default=""),
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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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

ENVIRONMENT = config("ENVIRONMENT", default="dev")

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="")
CORS_ALLOW_CREDENTIALS = True

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
