# conftest.py (project root)
import os
from pathlib import Path

import pytest

# ── Load .env.staging BEFORE Django settings are imported ──────────────────
# This fixes: "DJANGO_SECRET_KEY not found" when running pytest locally.
# In CI, variables are injected as real env vars so this is a no-op.
from decouple import AutoConfig
from rest_framework.test import APIClient

_env_path = Path(__file__).resolve().parent / "envs"
_config = AutoConfig(search_path=str(_env_path))

_ENV_VARS = [
    "DJANGO_SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "ALLOWED_HOSTS",
    "DEBUG",
    "SECURE_SSL_REDIRECT",
    "LOG_LEVEL",
    "SENTRY_DSN",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "CORS_ALLOWED_ORIGINS",
    "ENVIRONMENT",
    "DJANGO_SETTINGS_MODULE",
]

for _var in _ENV_VARS:
    if _var not in os.environ:
        try:
            os.environ[_var] = _config(_var)
        except Exception:
            pass  # Optional vars that may not exist in all envs


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """
    Set up the public tenant with both 'localhost' and 'testserver' domains.

    'testserver' is the HOST Django's test client always sends — it must be
    registered or every request will 404 at the tenant-routing middleware.
    """
    with django_db_blocker.unblock():
        from django.apps import apps
        from django_tenants.utils import get_public_schema_name, get_tenant_model

        TenantModel = get_tenant_model()

        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )

        # Resolve Domain model safely — adjust app_label if yours differs
        try:
            DomainModel = apps.get_model("products", "Domain")
        except LookupError:
            # Fallback: try the standard django-tenants app label
            DomainModel = apps.get_model("django_tenants", "Domain")

        DomainModel.objects.get_or_create(
            domain="localhost",
            defaults={"tenant": tenant, "is_primary": True},
        )
        DomainModel.objects.get_or_create(
            domain="testserver",
            defaults={"tenant": tenant, "is_primary": False},
        )
