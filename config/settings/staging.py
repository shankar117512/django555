# config/settings/staging.py
import os

from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

ALLOWED_HOSTS = [
    os.environ.get("charming-passion-staging.up.railway.app", "*"),
    "healthcheck.railway.app",
    "localhost",  # ← Railway internal healthcheck
    "127.0.0.1",  # ← Railway internal healthcheck
]
CSRF_TRUSTED_ORIGINS = ["https://charming-passion-staging.up.railway.app"]

# Security (partially relaxed for staging)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Staging DB enforces SSL
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# Email: use real backend in staging for testing
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.mailgun.org")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# Stricter throttling
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "50/day",
    "user": "500/day",
}
