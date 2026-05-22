# apps/core/tests.py
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

# ─── home view ───────────────────────────────────────────────────────────────


class HomeViewTests(TestCase):
    def setUp(self):
        self.url = reverse("core:home")

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_returns_405(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 405)

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "core/home.html")


# ─── TenantMiddlewareWithHealthCheck ─────────────────────────────────────────


class TenantMiddlewareTests(SimpleTestCase):
    """
    Tests the custom middleware without a real tenant DB.
    The parent's process_request is mocked so no tenant schema is required.
    """

    def setUp(self):
        self.factory = RequestFactory()
        from apps.core.middleware import TenantMiddlewareWithHealthCheck

        self.middleware = TenantMiddlewareWithHealthCheck.__new__(
            TenantMiddlewareWithHealthCheck
        )

    def test_health_path_bypasses_tenant_and_returns_none(self):
        request = self.factory.get("/health/")
        self.middleware.process_request(request)  # ← removed unused `result =`
        self.assertIsNone(request.tenant)

    def test_monitoring_ping_path_bypasses_tenant(self):
        request = self.factory.get("/monitoring/ping/")
        self.middleware.process_request(request)
        self.assertIsNone(request.tenant)

    def test_health_subpath_also_bypasses(self):
        """Any path starting with /health/ is bypassed."""
        request = self.factory.get("/health/ready/")
        self.middleware.process_request(request)
        self.assertIsNone(request.tenant)

    @patch(
        "apps.core.middleware.TenantMainMiddleware.process_request",
        return_value=None,
    )
    def test_regular_path_delegates_to_parent(self, mock_parent):
        request = self.factory.get("/api/protected/")
        self.middleware.process_request(request)
        mock_parent.assert_called_once_with(request)

    @patch(
        "apps.core.middleware.TenantMainMiddleware.process_request",
        return_value=None,
    )
    def test_root_path_delegates_to_parent(self, mock_parent):
        request = self.factory.get("/")
        self.middleware.process_request(request)
        mock_parent.assert_called_once_with(request)
