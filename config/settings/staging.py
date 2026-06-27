# config/settings/staging.py

import os

from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = config("DEBUG", default=False, cast=bool)

RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")

ALLOWED_HOSTS = [
    "charming-passion-staging.up.railway.app",
    "healthcheck.railway.app",
    "localhost",
    "127.0.0.1",
    ".railway.app",
]

if RAILWAY_DOMAIN and RAILWAY_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RAILWAY_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    "https://charming-passion-staging.up.railway.app",
]
if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_DOMAIN}")

# ─────────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────────
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ─────────────────────────────────────────────────
# DATABASE SSL
# FIX 1: The previous code checked for 'sslmode=disable' in DATABASE_URL but
# dj_database_url had already parsed the URL in base.py. Any sslmode embedded
# in the URL is parsed into OPTIONS automatically by dj_database_url, so we only
# need to add sslmode=require when the URL didn't already set one — i.e. when
# 'sslmode' is absent from the URL entirely. This prevents double-setting OPTIONS
# and avoids overwriting a URL-embedded sslmode=disable with require.
# ─────────────────────────────────────────────────
_db_url = os.environ.get("DATABASE_URL", "")
if DATABASES.get("default"):  # noqa: F405
    if "sslmode=" not in _db_url:
        # URL has no sslmode at all — enforce require for staging
        DATABASES["default"].setdefault("OPTIONS", {})  # noqa: F405
        DATABASES["default"]["OPTIONS"]["sslmode"] = "require"  # noqa: F405
    # If sslmode=disable or any other sslmode is already in the URL,
    # dj_database_url has already set it in OPTIONS — leave it alone.

# ─────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.mailgun.org")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# ─────────────────────────────────────────────────
# THROTTLING
# FIX 2: Instead of mutating the imported REST_FRAMEWORK dict key in-place
# (which modifies the dict object from base.py affecting any other importer),
# replace the entire sub-dict with a new dict. This is safe and explicit.
# ─────────────────────────────────────────────────
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405  — inherit all base keys
    "DEFAULT_THROTTLE_RATES": {
        "anon": "50/day",
        "user": "500/day",
    },
}
