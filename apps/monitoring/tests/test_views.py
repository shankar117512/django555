# apps/monitoring/tests/test_views.py
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestMonitoringViews:
    def test_health_check(self, client):
        response = client.get(reverse("monitoring:health-check"))
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, client):
        response = client.get(reverse("monitoring:health-check"))
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_db_failure_returns_503(self, client):
        with patch("apps.monitoring.views.connection") as mock_conn:
            mock_conn.cursor.side_effect = Exception("DB down")
            response = client.get(reverse("monitoring:health-check"))
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"]["status"] == "unhealthy"

    def test_health_check_cache_degraded(self, client):
        with patch("apps.monitoring.views.cache") as mock_cache:
            mock_cache.set.return_value = None
            mock_cache.get.return_value = "wrong-value"  # unexpected value
            response = client.get(reverse("monitoring:health-check"))
        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["cache"]["status"] == "degraded"

    def test_health_check_cache_exception(self, client):
        with patch("apps.monitoring.views.cache") as mock_cache:
            mock_cache.set.side_effect = Exception("Redis down")
            response = client.get(reverse("monitoring:health-check"))
        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["cache"]["status"] == "unhealthy"

    def test_server_metrics_requires_admin(self, client):
        response = client.get(reverse("monitoring:server-metrics"))
        assert response.status_code in (401, 403)

    def test_server_metrics_admin_access(self, admin_client):
        response = admin_client.get(reverse("monitoring:server-metrics"))
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data

    def test_db_metrics_requires_admin(self, client):
        response = client.get(reverse("monitoring:db-metrics"))
        assert response.status_code in (401, 403)

    def test_db_metrics_admin_access(self, admin_client):
        with patch("apps.monitoring.views.connection") as mock_conn:
            cursor = MagicMock()
            cursor.__enter__ = MagicMock(return_value=cursor)
            cursor.__exit__ = MagicMock(return_value=False)
            cursor.fetchone.side_effect = [
                (5,),  # active_connections
                (1048576,),  # db_size_bytes (1 MB)
            ]
            cursor.fetchall.return_value = [
                ("users", 100, 2),
                ("orders", 50, 0),
            ]
            mock_conn.cursor.return_value = cursor
            response = admin_client.get(reverse("monitoring:db-metrics"))
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "db_size_mb" in data
        assert "table_stats" in data
