# conftest.py
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_test_environment, django_db_blocker):
    """Run migrations then set up public tenant for all tests."""
    with django_db_blocker.unblock():
        # Run all migrations including tenant migrations
        call_command("migrate_schemas", "--shared", verbosity=0)

        from django.apps import apps
        from django_tenants.utils import get_public_schema_name, get_tenant_model

        TenantModel = get_tenant_model()
        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )
        DomainModel = apps.get_model("customers", "Domain")
        DomainModel.objects.get_or_create(
            domain="localhost",
            defaults={"tenant": tenant, "is_primary": True},
        )
