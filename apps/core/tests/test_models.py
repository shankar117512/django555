# apps/core/tests/test_models.py
#
# NOTE: These are Django TestCase classes (not pytest classes), so they manage
# their own DB transactions.  The session-scoped django_db_setup in conftest.py
# has already created the public tenant + domains by the time these run.

from django.test import Client, RequestFactory, TestCase
from django.urls import reverse


class HomeViewTest(TestCase):
    """Tests for the public home endpoint."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("core:home")

    def test_home_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_content_type_is_html(self):
        response = self.client.get(self.url)
        self.assertIn("text/html", response["Content-Type"])

    def test_home_contains_expected_heading(self):
        response = self.client.get(self.url)
        self.assertContains(
            response, "Django staging environment deployed successfully"
        )

    def test_home_contains_api_link(self):
        response = self.client.get(self.url)
        self.assertContains(response, "/api/")

    def test_home_contains_health_link(self):
        response = self.client.get(self.url)
        self.assertContains(response, "/health/")

    def test_home_post_not_allowed(self):
        """POST to home should not cause a server error."""
        response = self.client.post(self.url)
        self.assertNotEqual(response.status_code, 500)

    def test_home_is_accessible_without_auth(self):
        """Home page is public — no login required, no redirect."""
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 302)

    def test_home_html_structure(self):
        response = self.client.get(self.url)
        self.assertContains(response, "<html")
        self.assertContains(response, "</html>")
        self.assertContains(response, "<title>")


class TenantMiddlewareWithHealthCheckTest(TestCase):
    """
    Unit-test the custom middleware that bypasses tenant resolution
    for /health/ requests.
    """

    def _make_request(self, path):
        factory = RequestFactory()
        return factory.get(path)

    def test_health_path_returns_none(self):
        from apps.core.middleware import TenantMiddlewareWithHealthCheck

        mw = TenantMiddlewareWithHealthCheck(get_response=lambda r: None)
        request = self._make_request("/health/")
        result = mw.process_request(request)
        self.assertIsNone(result)

    def test_health_sub_path_returns_none(self):
        from apps.core.middleware import TenantMiddlewareWithHealthCheck

        mw = TenantMiddlewareWithHealthCheck(get_response=lambda r: None)
        request = self._make_request("/health/ping/")
        result = mw.process_request(request)
        self.assertIsNone(result)
