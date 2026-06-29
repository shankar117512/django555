# conftest.py (project root)
import os
from pathlib import Path

import pytest

# ── Load .env.staging BEFORE Django settings are imported ──────────────────
# Uses python-dotenv directly so the filename (.env.staging) is explicit.
# In CI, variables are injected as real env vars so this is a no-op.

_env_file = Path(__file__).resolve().parent / "envs" / ".env.staging"

if _env_file.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=str(_env_file), override=False)
    except ImportError:
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


# ---------------------------------------------------------------------------
# Tenant bootstrap
# ---------------------------------------------------------------------------
# We do NOT override pytest-django's `django_db_setup` fixture by name — doing
# so bypasses migration execution, which is why `products_client` (and every
# other table) was missing.  Instead we hook into `django_db_modify_db_settings`
# (a no-op shim) and do the one-time tenant seed inside a regular
# session-scoped autouse fixture that explicitly requests `django_db_setup`
# so migrations have already run by the time our code executes.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _seed_public_tenant(django_db_setup, django_db_blocker):
    """
    Ensure the public tenant + the two domains Django's test client uses
    ('localhost' and 'testserver') exist in the already-migrated database.

    This fixture runs once per test session, *after* pytest-django has run
    all migrations (because it depends on `django_db_setup`).
    """
    with django_db_blocker.unblock():
        from django.apps import apps
        from django_tenants.utils import get_public_schema_name, get_tenant_model

        TenantModel = get_tenant_model()

        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )

        try:
            DomainModel = apps.get_model("products", "Domain")
        except LookupError:
            DomainModel = apps.get_model("django_tenants", "Domain")

        # 'testserver' is the HOST Django's test client always sends.
        # 'localhost' is used by direct API / browser-style tests.
        for domain, is_primary in [("localhost", True), ("testserver", False)]:
            DomainModel.objects.get_or_create(
                domain=domain,
                defaults={"tenant": tenant, "is_primary": is_primary},
            )
