# apps/monitoring/tests/test_models.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class HealthCheckViewTest(TestCase):
    """Tests for the public /health/ endpoint."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("monitoring:health-check")

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_healthy_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_response_is_json(self):
        response = self.client.get(self.url)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_response_has_status_key(self):
        data = self.client.get(self.url).json()
        self.assertIn("status", data)

    def test_response_has_checks_key(self):
        data = self.client.get(self.url).json()
        self.assertIn("checks", data)

    def test_response_has_timestamp_key(self):
        data = self.client.get(self.url).json()
        self.assertIn("timestamp", data)

    def test_response_has_version_key(self):
        data = self.client.get(self.url).json()
        self.assertIn("version", data)

    def test_version_value(self):
        data = self.client.get(self.url).json()
        self.assertEqual(data["version"], "1.0.0")

    def test_database_check_present(self):
        data = self.client.get(self.url).json()
        self.assertIn("database", data["checks"])

    def test_cache_check_present(self):
        data = self.client.get(self.url).json()
        self.assertIn("cache", data["checks"])

    def test_healthy_status_string(self):
        data = self.client.get(self.url).json()
        self.assertIn(data["status"], ["healthy", "degraded"])

    # ── Database failure ─────────────────────────────────────────────────────

    @patch("apps.monitoring.views.connection")
    def test_db_failure_returns_503(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("DB down")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)

    @patch("apps.monitoring.views.connection")
    def test_db_failure_status_unhealthy(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("DB down")
        data = self.client.get(self.url).json()
        self.assertEqual(data["status"], "unhealthy")

    @patch("apps.monitoring.views.connection")
    def test_db_failure_check_reports_unhealthy(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("DB down")
        data = self.client.get(self.url).json()
        self.assertEqual(data["checks"]["database"]["status"], "unhealthy")

    # ── Cache failure ────────────────────────────────────────────────────────

    @patch("apps.monitoring.views.cache")
    def test_cache_failure_still_returns_200(self, mock_cache):
        mock_cache.set.side_effect = Exception("Cache down")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @patch("apps.monitoring.views.cache")
    def test_cache_failure_status_degraded(self, mock_cache):
        mock_cache.set.side_effect = Exception("Cache down")
        data = self.client.get(self.url).json()
        self.assertEqual(data["status"], "degraded")

    @patch("apps.monitoring.views.cache")
    def test_cache_unexpected_value_is_degraded(self, mock_cache):
        mock_cache.set.return_value = None
        mock_cache.get.return_value = "wrong_value"
        data = self.client.get(self.url).json()
        self.assertEqual(data["checks"]["cache"]["status"], "degraded")


class PingViewTest(TestCase):
    """Tests for the bare-minimum liveness /health/ping/ endpoint."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("monitoring:ping")

    def test_ping_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ping_response_json(self):
        response = self.client.get(self.url)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_ping_status_ok(self):
        data = self.client.get(self.url).json()
        self.assertEqual(data["status"], "ok")

    @patch("apps.monitoring.views.connection")
    def test_ping_works_even_when_db_is_down(self, mock_conn):
        """Ping must never touch the DB."""
        mock_conn.cursor.side_effect = Exception("DB down")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class DbMetricsViewTest(TestCase):
    """
    Tests for the /health/db/ endpoint (admin-only).

    FIX: Uses DRF's APIClient with force_authenticate() instead of Django's
    session-based force_login(). DbMetricsView is a DRF APIView, so DRF's
    IsAuthenticated checks DRF's own auth backends — session login via Django's
    test Client is not recognised unless SessionAuthentication is explicitly
    configured in DEFAULT_AUTHENTICATION_CLASSES.
    """

    def setUp(self):
        self.url = reverse("monitoring:db-metrics")

        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="db_admin", password="adminpass123"
        )

        # Use DRF's APIClient and bypass the auth layer entirely.
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_db_metrics_healthy_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_db_metrics_healthy_payload(self):
        data = self.client.get(self.url).json()
        self.assertEqual(data["db"], "ok")

    @patch("apps.monitoring.views.connection")
    def test_db_metrics_failure_returns_500(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("DB error")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)

    @patch("apps.monitoring.views.connection")
    def test_db_metrics_failure_payload(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("DB error")
        data = self.client.get(self.url).json()
        self.assertEqual(data["db"], "error")
        self.assertIn("detail", data)


class ServerMetricsViewTest(TestCase):
    """Tests for the admin-only /health/server/ endpoint."""

    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.url = reverse("monitoring:server-metrics")
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass123"
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="userpass123"
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
