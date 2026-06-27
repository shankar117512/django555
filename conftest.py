# conftest.py (project root)
import os
from pathlib import Path

import pytest
from decouple import Config, RepositoryEnv
from rest_framework.test import APIClient

_BASE_DIR = Path(__file__).resolve().parent

# ── Load .env.test if it exists, else fall back to .env.staging (CI) ────────
_env_file = _BASE_DIR / "envs" / ".env.test"
if not _env_file.exists():
    _env_file = _BASE_DIR / "envs" / ".env.staging"

if _env_file.exists():
    _staging_config = Config(RepositoryEnv(str(_env_file)))
    _keys_to_load = [
        "DJANGO_SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "DEBUG",
        "ENVIRONMENT",
        "CORS_ALLOWED_ORIGINS",
        "SENTRY_DSN",
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
    ]
    for _key in _keys_to_load:
        try:
            if _key not in os.environ:
                os.environ[_key] = _staging_config(_key)
        except Exception:
            pass


# ── Simple fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


# ── Tenant bootstrap — runs ONCE per session ────────────────────────────────


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """
    Ensure the public tenant + required domains exist before any test runs.

    django-tenants requires a public schema row in the tenant table and at
    least one Domain row pointing at it.  Without this every request made
    through the test client fails inside TenantMainMiddleware.
    """
    with django_db_blocker.unblock():
        from django.apps import apps
        from django_tenants.utils import get_public_schema_name, get_tenant_model

        TenantModel = get_tenant_model()

        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )

        DomainModel = apps.get_model("products", "Domain")

        # Django test client uses "testserver"; direct calls use "localhost"
        for domain_name, is_primary in [("localhost", True), ("testserver", False)]:
            DomainModel.objects.get_or_create(
                domain=domain_name,
                defaults={"tenant": tenant, "is_primary": is_primary},
            )
