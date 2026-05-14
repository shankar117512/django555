import os

from decouple import config

from .base import *

DEBUG = config("DEBUG", default=False, cast=bool)

RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")

ALLOWED_HOSTS = [
    "charming-passion-staging.up.railway.app",
    "healthcheck.railway.app",
    "localhost",
    "127.0.0.1",
    ".railway.app",  # covers all railway subdomains
]

# Also include the dynamic Railway domain if set
if RAILWAY_DOMAIN and RAILWAY_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RAILWAY_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    "https://charming-passion-staging.up.railway.app",
]
if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_DOMAIN}")

# Security (partially relaxed for staging)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Staging DB enforces SSL
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.mailgun.org")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# Throttling
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "50/day",
    "user": "500/day",
}
