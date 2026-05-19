# conftest.py (project root)
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """Set up public tenant with both localhost and testserver domains."""
    with django_db_blocker.unblock():
        from django.apps import apps
        from django_tenants.utils import get_public_schema_name, get_tenant_model

        TenantModel = get_tenant_model()
        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )
        DomainModel = apps.get_model("products", "Domain")

        # Used in production / local dev
        DomainModel.objects.get_or_create(
            domain="localhost",
            defaults={"tenant": tenant, "is_primary": True},
        )
        # Django test client always sends HOST=testserver — must be registered
        DomainModel.objects.get_or_create(
            domain="testserver",
            defaults={"tenant": tenant, "is_primary": False},
        )
