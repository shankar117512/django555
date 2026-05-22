# conftest.py
import pytest


@pytest.fixture(autouse=True)
def disable_ssl_redirect(settings):
    """
    Production settings enable SECURE_SSL_REDIRECT, which causes the test
    client (plain HTTP) to get a 301 before hitting any view.  Turn it off
    for every test automatically.
    """
    settings.SECURE_SSL_REDIRECT = False


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """Set up public tenant with both localhost and testserver domains."""
    with django_db_blocker.unblock():
        from django_tenants.utils import (
            get_public_schema_name,
            get_tenant_domain_model,
            get_tenant_model,
        )

        TenantModel = get_tenant_model()
        DomainModel = get_tenant_domain_model()

        tenant, _ = TenantModel.objects.get_or_create(
            schema_name=get_public_schema_name(),
            defaults={"name": "Public"},
        )

        for domain_str, is_primary in [
            ("gregarious-purpose-production-98d4.up.railway.app", True),
            ("testserver", False),
            ("localhost", False),
        ]:
            DomainModel.objects.get_or_create(
                domain=domain_str,
                defaults={"tenant": tenant, "is_primary": is_primary},
            )
