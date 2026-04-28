# config/settings/dev.py
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Dev-specific installed apps
INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Dev database from environment
DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Debug toolbar
INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]

# CORS: allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Celery in dev: run tasks eagerly (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable axes in dev
AXES_ENABLED = False
