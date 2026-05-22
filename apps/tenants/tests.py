# apps/tenants/tests.py
from django.test import SimpleTestCase


class TenantsAppConfigTests(SimpleTestCase):
    """Smoke-test that the tenants app loads without errors."""

    def test_app_module_importable(self):
        import apps.tenants

        self.assertIsNotNone(apps.tenants)

    def test_models_module_importable(self):
        import apps.tenants.models

        self.assertIsNotNone(apps.tenants.models)
