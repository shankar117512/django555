# apps/monitoring/tests.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


# ─── /monitoring/ ────────────────────────────────────────────────────────────


class HealthCheckTests(TestCase):
    def setUp(self):
        self.url = reverse("monitoring:health-check")

    def test_healthy_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertIn("checks", data)

    def test_healthy_db_and_cache_checks_present(self):
        response = self.client.get(self.url)
        checks = response.json()["checks"]
        self.assertIn("database", checks)
        self.assertIn("cache", checks)

    @patch("apps.monitoring.views.connection")
    def test_db_failure_returns_503(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("DB down")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["checks"]["database"]["status"], "unhealthy")

    @patch("apps.monitoring.views.cache")
    def test_cache_wrong_value_marks_degraded(self, mock_cache):
        mock_cache.set.return_value = None
        mock_cache.get.return_value = "wrong"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["checks"]["cache"]["status"], "degraded")

    @patch("apps.monitoring.views.cache")
    def test_cache_exception_marks_degraded(self, mock_cache):
        mock_cache.set.side_effect = Exception("Redis down")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["checks"]["cache"]["status"], "degraded")

    @patch("apps.monitoring.views.cache")
    @patch("apps.monitoring.views.connection")
    def test_db_failure_overrides_degraded_status(self, mock_conn, mock_cache):
        """DB unhealthy takes precedence over cache degraded."""
        mock_conn.cursor.side_effect = Exception("DB down")
        mock_cache.set.side_effect = Exception("Cache down")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "unhealthy")


# ─── /monitoring/ping/ ───────────────────────────────────────────────────────


class PingViewTests(TestCase):
    def setUp(self):
        self.url = reverse("monitoring:ping")

    def test_ping_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ping_returns_ok(self):
        data = self.client.get(self.url).json()
        self.assertEqual(data["status"], "ok")


# ─── /monitoring/db/ ─────────────────────────────────────────────────────────


class DbMetricsViewTests(TestCase):
    def setUp(self):
        self.url = reverse("monitoring:db-metrics")

    def test_db_ok_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["db"], "ok")

    @patch("apps.monitoring.views.connection")
    def test_db_error_returns_500(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("connection refused")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data["db"], "error")
        self.assertIn("detail", data)


# ─── /monitoring/server/ ─────────────────────────────────────────────────────


class ServerMetricsViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("monitoring:server-metrics")
        self.regular_user = User.objects.create_user(
            username="regular", password="pass123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin", password="admin123"
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_returns_403(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_returns_200(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
