# config/settings/production.py
from .base import *

DEBUG = False

# Security headers (strict)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"

# Production DB with SSL
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# Email: production provider
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = 587
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@yourapp.com")

# Static files on CDN (optional)
STATIC_URL = config("STATIC_URL", default="/static/")

# Production throttling
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "20/day",
    "user": "1000/day",
}

# Axes: strict in production
AXES_FAILURE_LIMIT = 3
AXES_COOLOFF_TIME = 2
