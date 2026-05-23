# apps/api/tests/test_views.py
from unittest.mock import patch

import pytest


@pytest.mark.django_db
class TestProtectedView:
    def test_protected_view_unauthenticated(self, client):
        # Mock tenant middleware so it doesn't try to resolve a tenant from DB
        with patch(
            "apps.core.middleware.TenantMainMiddleware.process_request",
            return_value=None,
        ):
            response = client.get("/api/protected/")
        assert response.status_code == 401

    def test_protected_view_authenticated(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass"
        )
        client.force_login(user)
        with patch(
            "apps.core.middleware.TenantMainMiddleware.process_request",
            return_value=None,
        ):
            response = client.get("/api/protected/")
        assert response.status_code == 200
