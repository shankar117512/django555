# apps/monitoring/tests/test_views.py
from unittest.mock import patch

import pytest


def tenant_mock():
    """Context manager to bypass django-tenants middleware DB lookup."""
    return patch(
        "apps.core.middleware.TenantMainMiddleware.process_request",
        return_value=None,
    )


@pytest.mark.django_db
class TestMonitoringViews:
    # ------------------------------------------------------------------ #
    #  Health check — these already pass; keep them unchanged             #
    # ------------------------------------------------------------------ #

    def test_health_check(self, client):
        response = client.get("/health/")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, client):
        with patch("django.db.backends.base.base.DatabaseWrapper.ensure_connection"):
            response = client.get("/health/")
        data = response.json()
        assert data["status"] in ("healthy", "degraded")

    def test_health_check_db_failure_returns_503(self, client):
        with patch(
            "apps.monitoring.views.check_database",
            return_value={"status": "error", "message": "DB down"},
        ):
            response = client.get("/health/")
        assert response.status_code == 503

    def test_health_check_cache_degraded(self, client):
        with patch(
            "apps.monitoring.views.check_cache",
            return_value={"status": "degraded"},
        ):
            response = client.get("/health/")
        assert response.status_code in (200, 207)

    def test_health_check_cache_exception(self, client):
        with patch(
            "apps.monitoring.views.check_cache",
            side_effect=Exception("cache error"),
        ):
            response = client.get("/health/")
        assert response.status_code in (200, 503)

    # ------------------------------------------------------------------ #
    #  Server metrics — require admin; go through tenant middleware        #
    # ------------------------------------------------------------------ #

    def test_server_metrics_requires_admin(self, client):
        with tenant_mock():
            response = client.get("/health/server/")
        assert response.status_code in (401, 403)

    def test_server_metrics_admin_access(self, client, django_user_model):
        admin = django_user_model.objects.create_superuser(
            username="admin", password="adminpass", email="admin@example.com"
        )
        client.force_login(admin)
        with tenant_mock():
            response = client.get("/health/server/")
        assert response.status_code == 200

    # ------------------------------------------------------------------ #
    #  DB metrics — require admin; go through tenant middleware            #
    # ------------------------------------------------------------------ #

    def test_db_metrics_requires_admin(self, client):
        with tenant_mock():
            response = client.get("/health/db/")
        assert response.status_code in (401, 403)

    def test_db_metrics_admin_access(self, client, django_user_model):
        admin = django_user_model.objects.create_superuser(
            username="admin2", password="adminpass", email="admin2@example.com"
        )
        client.force_login(admin)
        with tenant_mock():
            response = client.get("/health/db/")
        assert response.status_code == 200
