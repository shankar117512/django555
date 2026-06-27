# conftest.py (project root)
import os
from pathlib import Path

import pytest

# ── Load .env.staging BEFORE Django settings are imported ──────────────────
# Uses python-dotenv directly so the filename (.env.staging) is explicit.
# In CI, variables are injected as real env vars so this is a no-op.

_env_file = Path(__file__).resolve().parent / "envs" / ".env.staging"

if _env_file.exists():
    # python-dotenv: load only vars not already set in the environment
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=str(_env_file), override=False)
    except ImportError:
        # Fallback: manual parse if python-dotenv is not installed
        with open(_env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value


from rest_framework.test import APIClient  # noqa: E402 — must come after env setup


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

        # Resolve Domain model safely
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
