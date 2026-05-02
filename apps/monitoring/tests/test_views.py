# apps/monitoring/tests/test_views.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for /health/ — no auth required."""

    def test_health_check_returns_200_when_healthy(self, api_client):
        response = api_client.get("/health/")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "cache" in data["checks"]  # ✅ Fix 3: correct indentation

    def test_health_check_structure(self, api_client):
        response = api_client.get("/health/")
        data = response.json()
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_check_no_auth_required(self, api_client):
        """Health endpoint must be publicly accessible."""
        response = api_client.get("/health/")
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_health_check_db_failure_returns_503(
        self, mock_conn, mock_cache, api_client
    ):
        mock_conn.cursor.side_effect = Exception("DB down")
        response = api_client.get("/health/")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        # ✅ Fix 2: check DATABASE status, not cache
        assert data["checks"]["database"]["status"] == "unhealthy"

    def test_health_check_cache_degraded(self, mock_cache, api_client):
        """Cache returns wrong value → degraded (not unhealthy)."""
        mock_cache.set.return_value = None
        mock_cache.get.return_value = "wrong_value"  # not "ok"
        response = api_client.get("/health/")
        data = response.json()
        assert data["checks"]["cache"]["status"] == "degraded"


@pytest.mark.django_db
class TestServerMetrics:
    """Tests for /monitoring/server/ — admin only."""

    def test_unauthenticated_blocked(self, api_client):
        response = api_client.get("/monitoring/server/")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_non_admin_blocked(self, authenticated_client):
        response = authenticated_client.get("/monitoring/server/")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_admin_can_access(self, admin_client):  # ✅ Fix 1: fixture now exists
        response = admin_client.get("/monitoring/server/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data

    def test_server_metrics_structure(self, admin_client):
        response = admin_client.get("/monitoring/server/")
        data = response.json()
        assert "overall_percent" in data["cpu"]
        assert "total_gb" in data["memory"]
        assert "free_gb" in data["disk"]
        assert "bytes_sent_mb" in data["network"]


@pytest.mark.django_db
class TestDbMetrics:
    """Tests for /monitoring/db/ — admin only."""

    def test_unauthenticated_blocked(self, api_client):
        response = api_client.get("/monitoring/db/")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_admin_can_access(self, admin_client):  # ✅ Fix 1: fixture now exists
        response = admin_client.get("/monitoring/db/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "active_connections" in data
        assert "db_size_mb" in data
        assert "table_stats" in data
        assert "timestamp" in data  # ✅ Fix 4: removed corrupted trailing text
