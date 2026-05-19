# apps/tenants/tests.py
from django.test import TestCase


class TenantsAppConfigTest(TestCase):
    """Smoke-test: tenants app loads correctly."""

    def test_app_config_name(self):
        from apps.tenants.apps import TenantsConfig

        self.assertEqual(TenantsConfig.name, "apps.tenants")

    def test_app_is_in_installed_apps(self):
        from django.apps import apps

        self.assertTrue(apps.is_installed("apps.tenants"))
