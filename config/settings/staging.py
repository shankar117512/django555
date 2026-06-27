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

# Security
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SSL: only require it when DATABASE_URL doesn't explicitly disable it
# dj_database_url already parsed the URL in base.py, so we patch OPTIONS here.
# Guard against DATABASES not having a 'default' key (e.g. misconfigured base.py).
_db_url = os.environ.get("DATABASE_URL", "")
if DATABASES.get("default"):  # noqa: F405
    if "sslmode=disable" in _db_url:
        DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}  # noqa: F405
    else:
        DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}  # noqa: F405

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.mailgun.org")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# Throttling
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "50/day",
    "user": "500/day",
}
