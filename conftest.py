# conftest.py (project root)
import os
from pathlib import Path

import pytest
from decouple import AutoConfig, Config, RepositoryEnv
from rest_framework.test import APIClient

# ── Load envs/.env.staging so decouple can find DJANGO_SECRET_KEY etc. ──
_BASE_DIR = Path(__file__).resolve().parent
_env_file = _BASE_DIR / "envs" / ".env.staging"
if _env_file.exists():
    # AutoConfig with a custom search path reads that specific .env file
    _config = AutoConfig(search_path=str(_BASE_DIR / "envs"))
    # Populate os.environ from the .env.staging file so decouple picks them up
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
            pass  # optional keys may not exist


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """Set up public tenant with both localhost and testserver domains."""
    with django_db_blocker.unblock():
        from django.apps import apps
        from django_tenants.utils import (get_public_schema_name,
                                          get_tenant_model)

        TenantModel = get_tenant_model()
        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )
        DomainModel = apps.get_model("products", "Domain")

        DomainModel.objects.get_or_create(
            domain="localhost",
            defaults={"tenant": tenant, "is_primary": True},
        )
        DomainModel.objects.get_or_create(
            domain="testserver",
            defaults={"tenant": tenant, "is_primary": False},
        )
